"""AC-20 / AC-25: `hooks.json` を正本とする配線・一覧の契約（T-22 / T-25）。

- **AC-20**（T-22）: `StopFailure` / `Notification` の**配線**が競合せず block しないこと
- **AC-25**（T-25）: `README.md` / `CONTRIBUTING.md` / `docs/VERSIONING.md` の
  **手書きの event 一覧**が `hooks.json` と一致すること

`PrePushGateWiringContractTests` と同型 —— `hooks/hooks.json` を実際に開いて
配線面そのものを固定する。加えて **AC-20 の「block しない」を字面ではなく
実挙動で測る**。

計画（T-22 `#### Steps` 1）の 4 test は T-19 完了後は無条件に緑になり、
現実的な退行を軒並み素通しする。**その形と件数の正本は
`tasklist.md` の T-22 `#### Attempts` の表**（ここに件数を書かない ―― 同じ数を
複数箇所に書くと片方だけ直して残りが stale 化する）。要点だけ述べる:

- 計画の `_wired(event, script)` は**自イベントしか見ない**ので、
  `PreToolUse`/`Bash` への二重配線を素通しする（AC-20 の「配線が競合しない」を直接破る）
- 計画の `assertNotIn('"decision":', text)` は**1 ファイルの字面しか見ない**ので、
  `source` 先が出す場合と記法違い（スペース入り）の両方を素通しする

**AC-19 はこのファイルの担当ではない**。AC-19 の 2 節（kill switch で no-op /
`ALL_HOOKS` に全 hook が入る）の owner は `tests/test_hooks_kill_switch.py`（T-21）。
本ファイルの `test_every_script_on_disk_is_wired` が見るのは
「ディスク ↔ `hooks.json`」で、AC-19 が要求する「ディスク ↔ `ALL_HOOKS`」とは
**別の不変条件**である。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
SCRIPTS_DIR = ROOT / "hooks" / "scripts"

#: 新しいイベントに追加した hook と、その配線先イベント。
NEW_WIRING = (
    ("StopFailure", "run-stop-failure-hook.sh"),
    ("Notification", "run-notification-hook.sh"),
)

#: AC-20「配線が競合しない」相手（同時期に足した 3 本はいずれも `PreToolUse` の `Bash`）。
CONFLICTING_EVENT = "PreToolUse"

#: `timeout` の下限。縮めると遅い環境で fail-open する（`PrePushGateWiringContractTests` と同趣旨）。
MIN_HOOK_TIMEOUT_SECONDS = 5

#: 既存 `Stop` hook の `timeout`。この追加が触っていないことを固定するための pin（下限ではなく等値）。
STOP_HOOK_TIMEOUT_SECONDS = 10

#: `command` は 2 形ある —— `bash "<path>"` と、**bash 前置なしの直接実行**（`Stop`）。
#: 後者は shebang と**実行ビットに依存する**ので、書式を絞ったうえで exec 権限を別途 assert する。
#: **開き / 閉じ引用符は交替でグループ化して対応を強制する** ―― 独立した `"?` にすると
#: 片側だけの `bash "<path>`（起動時に shell 構文エラー）や、
#: `bash <unquoted path>`（plugin root に空白が入ると word splitting で壊れる）を受理してしまう。
_PATH_RE = r'\$\{CLAUDE_PLUGIN_ROOT\}/hooks/scripts/(run-[a-z0-9-]+\.sh)'
_COMMAND_RE = re.compile(rf'^(?:bash "{_PATH_RE}"|{_PATH_RE})$')


def _parse_command(command: str):
    """`(script_name, needs_exec_bit)` を返す。書式外なら `None`。"""
    match = _COMMAND_RE.match(command)
    if match is None:
        return None
    quoted, direct = match.group(1), match.group(2)
    return (quoted, False) if quoted is not None else (direct, True)


def _iter_wired(config: dict):
    """`(event, matcher, hook)` を全イベント横断で列挙する。"""
    for event, entries in config["hooks"].items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                yield event, entry.get("matcher"), hook


README = ROOT / "README.md"

#: `hooks.json` の event を**手書きで列挙している**配布物。ここに載っていないと黙ってずれる。
#: 初版は README だけを見ており、`CONTRIBUTING.md`（4/8 で stale）と
#: `docs/VERSIONING.md`（「hook 4 種類」）が取り残されていた（T-25 Attempt 1 / SC-M2）。
HAND_WRITTEN_EVENT_LISTS = (
    ("CONTRIBUTING.md", r"hook 定義（(.+?)）"),
    ("docs/VERSIONING.md", r"\*\*hook (\d+) 種類\*\*（(.+?)）"),
)


class ReadmeHookListContractTests(unittest.TestCase):
    """AC-25: `README.md` の hook 一覧が `hooks.json` の登録イベントと一致すること。

    **`hooks.json` を正本にして機械導出する**。手書きの一覧は黙ってずれる ——
    本 PR では `tests/test_hooks_kill_switch.py` の `ALL_HOOKS` が 12 対 15 でずれ（T-21）、
    `README.md` の hook 表が 4 対 8 でずれていた（T-25）。どちらも
    「足し忘れても誰も落ちない」形だったのが原因。

    件数はここに書かない（規約 2）。**期待値は `hooks.json` から取る**。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        cls.readme = README.read_text(encoding="utf-8")

    def _events(self) -> set[str]:
        events = set(self.config["hooks"])
        self.assertTrue(events, "hooks.json に event が 1 つも無い（検査が空虚になる）")
        return events

    def _hook_table_rows(self) -> set[str]:
        """`## Hooks` 節の表から event 名を抜く。節を跨がないよう範囲を絞る。"""
        start = self.readme.index("\n## Hooks\n")
        end = self.readme.index("\n## ", start + 1)
        section = self.readme[start:end]
        return set(re.findall(r"^\| \*\*([A-Za-z]+)\*\*", section, re.M))

    def test_readme_hook_table_matches_hooks_json(self) -> None:
        events = self._events()
        rows = self._hook_table_rows()
        self.assertEqual(rows - events, set(), "README の表にあるが hooks.json に無い event")
        self.assertEqual(events - rows, set(), "hooks.json にあるが README の表に無い event")

    def test_readme_states_the_count_that_hooks_json_actually_has(self) -> None:
        """説明文の「N 種類」が実際の event 数と一致すること。"""
        match = re.search(r"以下の (\d+) 種類の hook を定義", self.readme)
        self.assertIsNotNone(match, "hook 数を述べる説明文が見つからない")
        self.assertEqual(int(match.group(1)), len(self._events()))

    def test_other_hand_written_event_lists_stay_in_sync(self) -> None:
        """`hooks.json` の event を手書き列挙している**他の配布物**も同期対象。

        AC-25 が名指しするのは `README.md` だけだが、本 task 自身の正当化
        （「手書きの一覧は黙ってずれる」）がそのまま当てはまる。README を直しても
        **同じ stale が 2 箇所生き残っていた**（T-25 Attempt 1 / SC-M2）。
        """
        events = self._events()
        for relative, pattern in HAND_WRITTEN_EVENT_LISTS:
            with self.subTest(path=relative):
                path = ROOT / relative
                self.assertTrue(path.exists(), f"存在しない: {relative}")
                # 列挙は折り返されうる（`CONTRIBUTING.md` は 2 行）。改行と
                # ツリーの装飾（`│` / `#` / 連続空白）を潰してから照合する。
                raw = path.read_text(encoding="utf-8")
                flat = re.sub(r"[\s│#]+", " ", raw)
                match = re.search(pattern, flat)
                self.assertIsNotNone(match, f"{relative} の event 列挙が見つからない")
                groups = match.groups()
                listed = groups[-1]
                names = {part.strip() for part in listed.split("/") if part.strip()}
                self.assertEqual(events - names, set(), f"{relative} に無い event")
                self.assertEqual(names - events, set(), f"{relative} にあるが hooks.json に無い名前")
                if len(groups) == 2:  # 「hook N 種類」の N も導出する
                    self.assertEqual(int(groups[0]), len(events),
                                     f"{relative} の件数が hooks.json と不一致")

    def test_directory_diagram_comment_lists_every_event(self) -> None:
        """ディレクトリ図の `hooks.json` コメントも同期対象（AC-25 の字句）。

        2 つの穴を実測で見つけて塞いだ（T-25 Attempt 1 / CQ-M1・CQ-M2）:

        - **部分文字列照合では `Stop` ⊂ `StopFailure` の対が抜ける**。
          図から `Stop / ` だけ落としても `"Stop" in block` は True のまま。
          初出の変異は前置語でない event（`PreCompact`）を選んでいたため通っていた ——
          「正の対照を足したら同形の負変異も足す」の裏返しで、
          **前置語ケースだけが母集団から漏れていた**。**集合の両方向一致**にして構造的に塞ぐ
        - **継続行の判定が緩く、図の後続コメント行を 9 行飲み込んでいた**
          （`"#" not in line` で break）。結果として固定できていたのは
          「図の**どこかの**コメントに 8 つの名前が出てくる」で、
          「**`hooks.json` のコメントが列挙している**」ではなかった。
          継続行を「ツリーのエントリ記号を持たないコメント行」に限定する
        """
        lines = self.readme.splitlines()
        anchor = next(i for i, line in enumerate(lines)
                      if "hooks.json" in line and "hook 定義" in line)
        block = [lines[anchor]]
        for line in lines[anchor + 1:]:
            # 継続行 = 新しいツリーエントリ（`──`）を持たないコメント行だけ
            if "#" not in line or "──" in line:
                break
            block.append(line)
        comment = " ".join(part.split("#", 1)[1] for part in block)
        # 列挙は `hook 定義（… / … / …）` の括弧内。見出し語（`hook 定義`）まで拾わない。
        listed = re.search(r"（(.+?)）", comment)
        self.assertIsNotNone(listed, f"hooks.json のコメントに列挙が無い: {comment!r}")
        names = {part.strip() for part in listed.group(1).split("/") if part.strip()}
        events = self._events()
        self.assertEqual(events - names, set(), "ディレクトリ図のコメントに無い event")
        self.assertEqual(names - events, set(), "ディレクトリ図のコメントにあるが hooks.json に無い名前")


class NewEventWiringContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))

    def _wired_anywhere(self, script_name: str) -> list[tuple[str, object, dict]]:
        return [(e, m, h) for e, m, h in _iter_wired(self.config)
                if script_name in h.get("command", "")]

    # --- 配線そのもの ------------------------------------------------

    def test_each_new_hook_is_wired_exactly_once_across_all_events(self) -> None:
        """自イベント内だけでなく **全イベント横断で 1 度だけ**であること。

        計画の `_wired(event, script)` は自イベントしか見ないため、
        `PreToolUse`/`Bash` への二重配線を素通しする（実測 SURVIVED）。
        それは AC-20 の「同時期に足した 3 本と別イベントで配線が競合しない」を
        直接破る形なので、ここで落とす。
        """
        for event, script in NEW_WIRING:
            with self.subTest(script=script):
                wired = self._wired_anywhere(script)
                self.assertEqual(
                    [(e, m) for e, m, _ in wired],
                    [(event, "*")],
                    f"{script} は {event} の matcher='*' に 1 度だけ配線されている必要がある",
                )

    def test_new_hooks_never_appear_under_the_conflicting_event(self) -> None:
        """AC-20 の相手側からも見る（正の対照を兼ねた二方向の assert）。"""
        commands = " ".join(
            h.get("command", "")
            for e, _, h in _iter_wired(self.config) if e == CONFLICTING_EVENT
        )
        self.assertTrue(commands, f"{CONFLICTING_EVENT} の配線が 0 件（検査が空虚になる）")
        for _, script in NEW_WIRING:
            with self.subTest(script=script):
                self.assertNotIn(script, commands)

    def test_wired_timeout_has_headroom(self) -> None:
        for _, script in NEW_WIRING:
            for event, matcher, hook in self._wired_anywhere(script):
                with self.subTest(script=script, event=event, matcher=matcher):
                    self.assertGreaterEqual(hook.get("timeout", 0), MIN_HOOK_TIMEOUT_SECONDS)

    def test_every_command_resolves_to_a_script_that_exists(self) -> None:
        """`command` の書式を固定し、実体の無い script / 余分な引数を落とす。"""
        seen = 0
        for event, matcher, hook in _iter_wired(self.config):
            with self.subTest(event=event, matcher=matcher):
                self.assertEqual(hook.get("type"), "command")
                parsed = _parse_command(hook.get("command", ""))
                self.assertIsNotNone(parsed, f"command の書式が想定外: {hook.get('command')!r}")
                name, needs_exec_bit = parsed
                script = SCRIPTS_DIR / name
                self.assertTrue(script.is_file(), f"実体の無い script を配線している: {script}")
                if needs_exec_bit:
                    # 直接実行の配線は exec 権限が落ちた時点で**無言で起動しなくなる**。
                    self.assertTrue(
                        os.access(script, os.X_OK),
                        f"{script.name} は bash 前置なしで配線されているので実行ビットが要る",
                    )
                seen += 1
        self.assertGreater(seen, 0, "配線が 0 件（検査が空虚になる）")

    def test_every_script_on_disk_is_wired(self) -> None:
        """ディスクと `hooks.json` の drift を落とす。

        新設した hook を配線し忘れると、**その hook は一度も起動しない**まま
        テストも lint も緑になる（実測 SURVIVED）。
        """
        on_disk = {p.name for p in SCRIPTS_DIR.glob("run-*.sh")}
        wired = {parsed[0] for _, _, h in _iter_wired(self.config)
                 if (parsed := _parse_command(h.get("command", "")))}
        self.assertTrue(on_disk, "SCRIPTS_DIR に run-*.sh が 1 本も無い（検査が空虚になる）")
        self.assertEqual(on_disk - wired, set(), "実体はあるが hooks.json に配線が無い")
        self.assertEqual(wired - on_disk, set(), "配線はあるが実体が無い")

    def test_stop_event_wiring_is_unchanged(self) -> None:
        """AC-20 節 3「既存 `Stop` の block 経路に影響しない」。

        `(event, matcher)` の同一性だけでは足りない ―― 実測で 2 形が漏れた:
        `Stop` hook の `timeout` を縮める形（**ワークフローを実際に止めている
        hook が遅い環境で fail-open する**）と、`Stop` イベントへ**別 hook を
        追加配線する**形（追加分が `decision: block` を返せば block 経路は変わる）。
        本数と `timeout` も併せて固定する。
        """
        wired = self._wired_anywhere("run-gdd-stop-hook.sh")
        self.assertEqual([(e, m) for e, m, _ in wired], [("Stop", "*")],
                         "既存の Stop 配線を新しいイベントの追加が触ってはならない")
        entries = self.config["hooks"]["Stop"]
        hooks = [h for entry in entries for h in entry.get("hooks", [])]
        # 依頼との差の hook は、欄の形が崩れた確認だけを block する（条件と上限は test_request_diff_hook.py が実行で確かめる）。
        # 印の付け忘れの hook は知らせだけを出す（test_display_marker_hook.py が実行で確かめる）。
        # main のモデルの通知の hook は知らせだけを出す（test_main_model_gate.py の test_stop_notice_once_per_session_when_sonnet が実行で確かめる）。
        # timeout の固定は、ワークフローの停止を決める run-gdd-stop-hook.sh だけに当てる。
        others = ("run-request-diff-hook.sh", "run-display-marker-hook.sh", "run-main-model-gate-hook.sh")
        blocking = [h for h in hooks if not any(name in h.get("command", "") for name in others)]
        self.assertEqual(
            len(blocking), 1,
            f"Stop に配線されている hook は run-gdd-stop-hook.sh と依頼との差の表示と印の付け忘れの知らせと main のモデルの通知だけのはず: "
            f"{[h.get('command') for h in hooks]}",
        )
        self.assertEqual(
            blocking[0].get("timeout"), STOP_HOOK_TIMEOUT_SECONDS,
            "Stop hook の timeout を変えると block 判定が遅い環境で fail-open する",
        )

    # --- 「block しない」を実挙動で ----------------------------------

    def test_new_hooks_emit_no_decision_control_at_runtime(self) -> None:
        """AC-20「decision control を使わない」を**実際に起動して**確かめる。

        字面 `assertNotIn('"decision":', text)` では `source` 先が出す場合と
        記法違いの両方を見逃す。ここでは stdout そのものを見る ――
        両 hook とも「**stdout は空**」を自ら宣言している（各 script のヘッダ）ので、
        空であることを assert すれば decision control は構造的に出しえない。

        **payload は実働パスに届く形でなければ意味がない** ―― 初版は
        `Notification` に `message` を渡していたが、hook が読むのは
        `notification_type` で、allowlist 判定の最初期分岐で no-op 終了しており
        **本体を 1 度も実行していなかった**（T-22 Attempt 1 / M-1）。
        到達したことは **通知コマンドの stub が呼ばれたか**で確かめる（正の対照）。

        通知コマンドは **stub に差し替える** ―― 素の PATH で走らせると
        `osascript` が実機のデスクトップ通知を出す（同 M-4）。
        sibling の `test_stop_failure_hook_contract.py` /
        `test_notification_hook_contract.py` と同じ規約。
        """
        payloads = {
            "run-stop-failure-hook.sh": {
                "cwd": str(ROOT),
                "session_id": "t22-contract",
                "transcript_path": "/nonexistent/transcript.jsonl",
                "error": "test-error",
                "stop_hook_active": False,
            },
            "run-notification-hook.sh": {
                "cwd": str(ROOT),
                "session_id": "t22-contract",
                "notification_type": "idle_prompt",
            },
        }
        for _, script in NEW_WIRING:
            with self.subTest(script=script), tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                log = tmp_path / "notify.log"
                stub_dir = tmp_path / "stub-bin"
                stub_dir.mkdir()
                for name in ("osascript", "notify-send"):
                    stub = stub_dir / name
                    stub.write_text(
                        "#!/usr/bin/env bash\n"
                        f'printf "CALL:{name}\\n" >> "{log}"\n'
                        "cat >/dev/null 2>&1 || true\n"
                        "exit 0\n",
                        encoding="utf-8",
                    )
                    stub.chmod(0o755)

                env = dict(os.environ)
                env["HOME"] = str(tmp_path / "home")
                env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
                env["PATH"] = f"{stub_dir}{os.pathsep}{env['PATH']}"
                result = subprocess.run(
                    ["bash", str(SCRIPTS_DIR / script)],
                    input=json.dumps(payloads[script]),
                    capture_output=True, text=True, env=env, timeout=60,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                # 正の対照: 通知まで到達していなければ、この test は何も測っていない。
                self.assertTrue(
                    log.exists() and "CALL:" in log.read_text(encoding="utf-8"),
                    f"{script} が通知まで到達していない（payload が実働パスに届いていない）",
                )
                self.assertEqual(
                    result.stdout, "",
                    f"{script} の stdout は空でなければならない（AC-20）: {result.stdout!r}",
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
