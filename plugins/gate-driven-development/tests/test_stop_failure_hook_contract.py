"""`run-stop-failure-hook.sh` の契約テスト（AC-16 / AC-17）。

design.md § Sensitive Data / Masking Policy の enforcement point 1（永続化直前の
whitelist + 200 文字切り詰め）/ enforcement point 2（通知本文は固定文言のみ・
`osascript -` + `system attribute` で連結しない）/ § 論点 3（置き場所・1 件保持・
mode 0600 / 0700・`project_root` キー・fail-open）を実行可能な形で固定する。

通知センターへの実表示は自動検証しない（requirements AC-16 の「分類済み未検証」）。
ここで固定するのは「通知コマンドが 1 回呼ばれる」ことと「payload 由来の自由文が
通知コマンドへ 1 バイトも渡らない」ことまで。
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import PLUGIN_ROOT as ROOT
from test_notification_hook_contract import _install_notify_send_stub
HOOK = ROOT / "hooks" / "scripts" / "run-stop-failure-hook.sh"

RECORD_NAME = "last-turn-failure.json"
# 記録に載ってよいキーの全集合（design § 論点 3 + project キー）。
EXPECTED_KEYS = {"error", "error_details", "session_id", "timestamp", "project_root"}


def _make_env(home: Path, *, stub_dir: Path | None = None, state_dir: Path | None = None,
              isolated_path: bool = False) -> dict:
    env = os.environ.copy()
    env.pop("GDD_HOOK_STATE_DIR", None)
    env["HOME"] = str(home)
    env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
    if state_dir is not None:
        env["GDD_HOOK_STATE_DIR"] = str(state_dir)
    if stub_dir is not None:
        env["PATH"] = str(stub_dir) if isolated_path else f"{stub_dir}{os.pathsep}{env['PATH']}"
    return env


def _run(payload, home: Path, **kwargs) -> subprocess.CompletedProcess:
    env = _make_env(home, **kwargs)
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        ["bash", str(HOOK)], input=body, capture_output=True, text=True, env=env, timeout=60,
    )


def _install_notify_stub(stub_dir: Path, log: Path) -> Path:
    """`osascript` の stub。env / argv / stdin の 3 経路すべてを記録する。

    通知本文は env（`GDD_NOTIFY_BODY`）で渡す規約なので、stdin だけを見る stub では
    「本文に自由文が載っていない」ことを測れない。3 経路すべてを 1 ファイルに落とす。
    """
    stub_dir.mkdir(parents=True, exist_ok=True)
    script = stub_dir / "osascript"
    script.write_text(
        "#!/usr/bin/env bash\n"
        "{\n"
        '  printf "CALL\\n"\n'
        '  printf "ENV:%s\\n" "${GDD_NOTIFY_BODY-<unset>}"\n'
        '  printf "ARGV:%s\\n" "$*"\n'
        '  printf "STDIN:"\n'
        "  cat\n"
        '  printf "\\n"\n'
        f'}} >> "{log}"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script



# hook が PATH から引く外部コマンドのうち「無いと動けない」もの。通知コマンド
# （osascript / notify-send）と git はここに入れない = 不在で動くことを測る。
# 依存が増えたらこのリストが更新されない限りテストが落ちる（依存面の pin も兼ねる）。
REQUIRED_COMMANDS = ("bash", "dirname", "cat")


def _minimal_bin_path(tmp: Path) -> Path:
    """必須コマンドと python3 だけが引ける PATH（osascript / notify-send / git は不在）。

    bash も置くのは subprocess が env の PATH から実行ファイルを探すため
    （置かないと hook を起動する前に FileNotFoundError になり、no-op 経路を測れない）。
    """
    bin_dir = tmp / "minimal-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "python3").symlink_to(sys.executable)
    for name in REQUIRED_COMMANDS:
        resolved = shutil.which(name)
        if not resolved:
            raise AssertionError(f"{name} not found on PATH")
        (bin_dir / name).symlink_to(resolved)
    # fixture 不変条件。`assert` は `python -O` で消えるため明示的に送出する
    for absent in ("osascript", "notify-send", "git"):
        if (bin_dir / absent).exists():
            raise AssertionError(f"PATH に不在であるべき {absent} が存在する: {bin_dir}")
    return bin_dir


class StopFailureHookRecordTests(unittest.TestCase):
    """enforcement point 1 + § 論点 3: 何を書くか / どこに書くか / どう書くか。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.log = self.tmp / "notify.log"
        self.stub_dir = self.tmp / "stub"
        _install_notify_stub(self.stub_dir, self.log)
        self.addCleanup(self._tmp.cleanup)

    @property
    def record(self) -> Path:
        return self.home / ".claude" / ".gdd-hook-state" / RECORD_NAME

    def _run_ok(self, payload, **kwargs):
        result = _run(payload, self.home, stub_dir=self.stub_dir, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_record_holds_whitelisted_keys_only(self):
        """payload の他フィールドは 1 つも記録に載らない（whitelist が実効）。"""
        self._run_ok({
            "error": "api_error",
            "error_details": "upstream 500",
            "session_id": "abc123ef",
            "cwd": str(self.tmp),
            "transcript_path": "/private/var/transcript.jsonl",
            "hook_event_name": "StopFailure",
            "attacker_controlled": "SHOULD-NOT-BE-PERSISTED",
        })
        self.assertTrue(self.record.is_file(), "record file was not created")
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(set(data.keys()), EXPECTED_KEYS)
        self.assertNotIn("SHOULD-NOT-BE-PERSISTED", self.record.read_text(encoding="utf-8"))
        for key, value in data.items():
            self.assertIsInstance(value, str, f"{key} must be str (consumer shape check)")
        self.assertEqual(data["error"], "api_error")
        self.assertEqual(data["error_details"], "upstream 500")
        self.assertEqual(data["session_id"], "abc123ef")

    def test_timestamp_is_generated_by_hook_not_taken_from_payload(self):
        """timestamp は payload 由来ではなく hook 生成値（enforcement point 1）。"""
        self._run_ok({
            "error": "api_error", "error_details": "x", "session_id": "a",
            "timestamp": "1999-01-01T00:00:00Z",
        })
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertNotEqual(data["timestamp"], "1999-01-01T00:00:00Z")
        self.assertRegex(data["timestamp"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_error_details_truncated_to_200_chars(self):
        self._run_ok({"error": "api_error", "error_details": "x" * 500, "session_id": "a"})
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(len(data["error_details"]), 200)

    def test_error_details_truncation_is_character_based(self):
        """多バイト文字を byte 単位で割らない（`${var:0:N}` 禁止の実質を測る）。

        'あ' は UTF-8 3 バイト。byte 切りだと 200 バイト目が継続バイトの途中に落ちて
        JSON が壊れるか、文字数が 200 に満たない。
        """
        self._run_ok({"error": "api_error", "error_details": "あ" * 300, "session_id": "a"})
        raw = self.record.read_bytes()
        data = json.loads(raw.decode("utf-8"))  # 壊れた UTF-8 ならここで例外
        self.assertEqual(data["error_details"], "あ" * 200)

    def test_non_string_payload_values_are_dropped_not_stringified(self):
        """str 以外は空文字に落とす（消費側 shape 検証の「各値が str」を書き手側で保証）。"""
        self._run_ok({"error": {"kind": "api_error"}, "error_details": ["a", "b"], "session_id": 42})
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(data["error"], "")
        self.assertEqual(data["error_details"], "")
        self.assertEqual(data["session_id"], "")

    def test_record_mode_is_0600_and_state_dir_mode_is_0700(self):
        self._run_ok({"error": "api_error", "error_details": "x", "session_id": "a"})
        self.assertEqual(stat.S_IMODE(self.record.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.record.parent.stat().st_mode), 0o700)

    def test_no_temp_file_is_left_behind(self):
        """atomic write の tmp が state dir に残らない（消費側が拾う余地を作らない）。"""
        self._run_ok({"error": "api_error", "error_details": "x", "session_id": "a"})
        leftovers = sorted(p.name for p in self.record.parent.iterdir() if p.name != RECORD_NAME)
        self.assertEqual(leftovers, [])

    def test_consecutive_failures_keep_only_the_last_record(self):
        """連続 StopFailure は last-write-wins の 1 件保持（§ 論点 3 / duplicate surface）。"""
        self._run_ok({"error": "api_error", "error_details": "first", "session_id": "a"})
        self._run_ok({"error": "overloaded_error", "error_details": "second", "session_id": "b"})
        siblings = sorted(p.name for p in self.record.parent.iterdir())
        self.assertEqual(siblings, [RECORD_NAME])
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(data["error_details"], "second")

    def test_state_dir_env_override_is_honored(self):
        """`GDD_HOOK_STATE_DIR` を既存 2 実装と同じく尊重する（§ 論点 3 env override）。"""
        override = self.tmp / "override-state"
        self._run_ok({"error": "api_error", "error_details": "x", "session_id": "a"},
                     state_dir=override)
        self.assertTrue((override / RECORD_NAME).is_file())
        self.assertFalse(self.record.exists())

    def test_project_root_is_git_toplevel_of_payload_cwd(self):
        repo = self.tmp / "repo"
        nested = repo / "pkg" / "sub"
        nested.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
        self._run_ok({"error": "api_error", "error_details": "x", "session_id": "a",
                      "cwd": str(nested)})
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(Path(data["project_root"]).resolve(), repo.resolve())

    def test_project_root_keeps_trailing_whitespace_of_toplevel(self):
        # 名前が空白・タブ・改行・CR で終わる repo でも、toplevel をそのまま記録する
        # （`.strip()` で落とすと SessionStart の照合と一致しない）。
        for suffix in (" ", "\t", "\n", "\r"):
            with self.subTest(suffix=repr(suffix)):
                repo = self.tmp / f"repo{len(list(self.tmp.iterdir()))}{suffix}"
                nested = repo / "sub"
                nested.mkdir(parents=True)
                subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
                self._run_ok({"error": "api_error", "error_details": "x", "session_id": "a",
                              "cwd": str(nested)})
                data = json.loads(self.record.read_text(encoding="utf-8"))
                self.assertEqual(data["project_root"], str(repo.resolve()))

    def test_project_root_falls_back_to_cwd_outside_git(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        self._run_ok({"error": "api_error", "error_details": "x", "session_id": "a",
                      "cwd": str(plain)})
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(data["project_root"], str(plain))

    def test_existing_loose_state_dir_is_tightened_to_0700(self):
        """既存ディレクトリにも chmod(0o700) を適用する（design § 論点 3 permission）。

        この hook が初めて走るとき state dir は既に他コンポーネント
        （validate-steering-write.py は umask 依存で 0755 を作る）が置いている
        可能性が高い。`mkdir(exist_ok=True)` は既存 dir の mode を変えないので、
        締め直しの唯一の点が chmod。0755 の既存 dir を入力にしないと測れない。
        """
        state_dir = self.tmp / "loose-state"
        state_dir.mkdir()
        state_dir.chmod(0o755)
        self.assertEqual(stat.S_IMODE(state_dir.stat().st_mode), 0o755)
        self._run_ok({"error": "api_error", "error_details": "x", "session_id": "a"},
                     state_dir=state_dir)
        self.assertEqual(stat.S_IMODE(state_dir.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((state_dir / RECORD_NAME).stat().st_mode), 0o600)

    def test_unpaired_surrogate_payload_is_recorded_and_leaves_no_temp_file(self):
        """JSON の単独サロゲートで記録が silent に消えない（tmp も残さない）。

        payload は JSON なので `"\\ud800"` が正当に届く（API エラー本文が絵文字の
        途中で切られると自然に起きる）。UnicodeEncodeError は OSError ではなく
        ValueError 系なので、受理面が `except OSError` だと書き込み途中で
        プロセスが落ち、ドットファイルの部分書き込みだけが溜まる。
        3 回投入で leftovers 0 / record 有り を固定する。
        """
        state_dir = self.tmp / "surrogate-state"
        payload = ('{"error":"api_error","error_details":"lead-\\ud800-tail",'
                   '"session_id":"a"}')
        for _ in range(3):
            self._run_ok(payload, state_dir=state_dir)
        record = state_dir / RECORD_NAME
        self.assertTrue(record.is_file(), "record must survive an unpaired surrogate")
        leftovers = sorted(p.name for p in state_dir.iterdir() if p.name != RECORD_NAME)
        self.assertEqual(leftovers, [])
        data = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(data["error_details"], "lead-?-tail")
        # 記録が残る以上、通知も 3 回とも出ている（AC-16 / AC-17 の両立）
        self.assertEqual(self.log.read_text(encoding="utf-8").count("CALL"), 3)

    def test_failed_replace_leaves_no_temp_file_behind(self):
        """tmp 作成後に書き込みが失敗しても hidden tmp を残さない。

        `test_no_temp_file_is_left_behind` は成功経路しか通らないため、
        後始末そのものには判別力が無い。record 名がディレクトリとして先に存在すると
        `os.replace` が IsADirectoryError で落ち、**tmp を作った後**に失敗する経路へ入る。
        後始末が無いと `.last-turn-failure.*` が実行のたびに単調増加する（ドットファイル
        なので `ls` にも出ず、GC も TTL も無い）。
        """
        state_dir = self.tmp / "occupied-state"
        state_dir.mkdir()
        (state_dir / RECORD_NAME).mkdir()
        for _ in range(3):
            result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                          self.home, stub_dir=self.stub_dir, state_dir=state_dir)
            self.assertEqual(result.returncode, 0)
        leftovers = sorted(p.name for p in state_dir.iterdir() if p.name != RECORD_NAME)
        self.assertEqual(leftovers, [])
        self.assertIn("record not written", result.stderr)

    def test_payload_larger_than_env_limit_is_still_recorded(self):
        """env のサイズ上限を超える payload でも記録が消えない（stdin 渡し）。

        payload を env で渡すと execve が E2BIG で失敗し、記録も通知も無症状で
        消える（実測: macOS ARG_MAX 1,048,576 で payload 1,100,080 バイトが
        exit 0 / record 無し。Linux の単一 env 文字列上限 MAX_ARG_STRLEN は
        131,072 とさらに低い）。1.2MB は両方を超える。
        """
        state_dir = self.tmp / "large-state"
        self._run_ok({"error": "api_error", "error_details": "x" * 1_200_000,
                      "session_id": "a"}, state_dir=state_dir)
        data = json.loads((state_dir / RECORD_NAME).read_text(encoding="utf-8"))
        self.assertEqual(len(data["error_details"]), 200)

    def test_symlinked_state_dir_is_refused_without_following_it(self):
        """state dir が symlink なら書かない（追従先の mode を書き換えない）。

        書き手は `os.replace` なのでファイルが symlink の場合は安全だが、
        **ディレクトリ自体が symlink** だと chmod と書き込みが追従先に及ぶ。
        design § 論点 3 / 消費側の契約 が「同一ユーザ権限の任意プロセス」を
        攻撃者モデルに含めている以上、読み手側と同型の拒否を書き手側にも課す。
        """
        victim = self.tmp / "victim"
        victim.mkdir()
        victim.chmod(0o755)
        linked = self.tmp / "linked-state"
        linked.symlink_to(victim, target_is_directory=True)
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir, state_dir=linked)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(stat.S_IMODE(victim.stat().st_mode), 0o755)
        self.assertEqual(sorted(p.name for p in victim.iterdir()), [])
        # silent に落とさない: 理由が観測できること
        self.assertIn("state_dir_is_symlink", result.stderr)
        # 記録できなくても通知は出る（AC-16 は AC-17 に従属しない）
        self.assertEqual(self.log.read_text(encoding="utf-8").count("CALL"), 1)


class StopFailureHookNotificationTests(unittest.TestCase):
    """enforcement point 2: 通知は固定文言のみ・1 回・不在なら no-op。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.log = self.tmp / "notify.log"
        self.stub_dir = self.tmp / "stub"
        _install_notify_stub(self.stub_dir, self.log)
        self.addCleanup(self._tmp.cleanup)

    def _calls(self) -> str:
        return self.log.read_text(encoding="utf-8") if self.log.exists() else ""

    def test_notification_command_called_exactly_once(self):
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._calls().count("CALL"), 1)

    def test_error_details_never_reaches_notification_command(self):
        """自由文は env / argv / stdin のどの経路でも通知コマンドに届かない。"""
        secret = "SECRET-PROMPT-FRAGMENT-XYZ"
        result = _run({"error": "api_error", "error_details": secret, "session_id": "a"},
                      self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        self.assertIn("CALL", captured, "notification stub was not invoked at all")
        self.assertNotIn(secret, captured)
        self.assertNotIn(secret, result.stdout)
        self.assertNotIn(secret, result.stderr)

    def test_applescript_body_is_passed_by_env_not_concatenated(self):
        """本文は env 経由。stdin のスクリプトは payload 由来値を含まないリテラル。"""
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        env_line = next(line for line in captured.splitlines() if line.startswith("ENV:"))
        stdin_part = captured.split("STDIN:", 1)[1]
        self.assertIn("api_error", env_line)
        self.assertIn('system attribute "GDD_NOTIFY_BODY"', stdin_part)
        self.assertNotIn("api_error", stdin_part)

    def test_hostile_error_token_is_normalized_before_notification(self):
        """`error` は種別として保証されていない。token 正規化して本文へ載せる。"""
        hostile = 'api_error" & (do shell script "id") & "'
        result = _run({"error": hostile, "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        self.assertNotIn("do shell script", captured)
        env_line = next(line for line in captured.splitlines() if line.startswith("ENV:"))
        self.assertIn("unknown", env_line)
        # 記録側は正規化しない（消費側 = SessionStart が自前で正規化する契約）
        record = self.home / ".claude" / ".gdd-hook-state" / RECORD_NAME
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["error"], hostile)

    def test_record_is_written_when_no_notification_command_exists(self):
        """通知コマンド不在でも記録は残り exit 0（AC-16 no-op / AC-17 は独立）。"""
        bin_dir = _minimal_bin_path(self.tmp)
        state_dir = self.tmp / "state"
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=bin_dir, state_dir=state_dir, isolated_path=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((state_dir / RECORD_NAME).is_file())
        self.assertEqual(self._calls(), "")

    def test_notify_send_is_called_with_option_terminator_before_body(self):
        """`notify-send` は argv 渡し + `--` で option 終端（design § enforcement point 2）。

        design が「本文の先頭が `-` でも壊れないことを 1 ケース固定する」と明記した
        項目。Linux 実機は要らない。`osascript` を不在にした PATH に
        `notify-send` の stub を置けば macOS 上で argv を直接測れる。
        """
        bin_dir = _minimal_bin_path(self.tmp)
        _install_notify_send_stub(bin_dir, self.log)
        state_dir = self.tmp / "state"
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=bin_dir, state_dir=state_dir, isolated_path=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        self.assertEqual(captured.count("CALL"), 1)
        args = [line[len("ARG:"):] for line in captured.splitlines()
                if line.startswith("ARG:")]
        self.assertEqual(args[:2], ["--", "GDD"],
                         "option terminator must precede the title")
        self.assertEqual(len(args), 3, args)
        self.assertTrue(args[2].endswith("(api_error)"), args[2])

    def test_error_with_trailing_newline_is_not_a_valid_token(self):
        """token 正規表現は末尾改行を許さない（`\\Z` は `$` と違い fullmatch 等価）。

        `$` に弱めると `api_error\\n` がそのまま通知本文へ載り、本文が 1 行である
        前提（通知センターは改行を表示せず truncate する）も崩れる。
        """
        result = _run({"error": "api_error\n", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        self.assertIn("CALL", captured, "notification stub was not invoked at all")
        self.assertIn("unknown", captured)
        self.assertNotIn("api_error", captured)
        # 記録側は正規化せず原文を残す（正規化は消費側の契約）
        record = self.home / ".claude" / ".gdd-hook-state" / RECORD_NAME
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["error"],
                         "api_error\n")


class StopFailureHookNoopTests(unittest.TestCase):
    """no-op / fail-open path: 何があっても hook はターンを壊さない。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.log = self.tmp / "notify.log"
        self.stub_dir = self.tmp / "stub"
        _install_notify_stub(self.stub_dir, self.log)
        self.addCleanup(self._tmp.cleanup)

    @property
    def record(self) -> Path:
        return self.home / ".claude" / ".gdd-hook-state" / RECORD_NAME

    def _assert_silent_noop(self, payload):
        result = _run(payload, self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.record.exists(), "no-op path must not write a record")
        self.assertFalse(self.log.exists(), "no-op path must not notify")
        return result

    def test_empty_payload_is_noop(self):
        self._assert_silent_noop("")

    def test_invalid_json_payload_is_noop(self):
        self._assert_silent_noop("not json at all")

    def test_non_object_json_payload_is_noop(self):
        self._assert_silent_noop("[1, 2, 3]")

    def test_kill_switch_suppresses_record_and_notification(self):
        (self.home / ".claude").mkdir(parents=True, exist_ok=True)
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.record.exists())
        self.assertFalse(self.log.exists())

    def test_unwritable_state_dir_fails_open_but_still_notifies(self):
        """書き込み不可でも exit 0。記録は残らないが**通知は出る**。

        AC-16 の no-op 条件は「通知コマンドが存在しない環境」だけで、記録の成否は
        条件に入っていない（requirements AC-16）。design § 論点 3 の fail-open は
        永続ファイルについての規定であり、通知の抑制まで広げると、ディスクフルや
        read-only な $HOME といった記録と無関係な事象で、人間が異常終了に気づく
        唯一の即時シグナルが無症状で消える。AC-16 と AC-17 は独立。
        """
        blocked = self.tmp / "blocked"
        blocked.mkdir(mode=0o500)
        self.addCleanup(blocked.chmod, 0o700)
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir, state_dir=blocked / "state")
        self.assertEqual(result.returncode, 0)
        self.assertFalse((blocked / "state" / RECORD_NAME).exists())
        self.assertTrue(self.log.exists(),
                        "record failure must not suppress the notification (AC-16)")
        self.assertEqual(self.log.read_text(encoding="utf-8").count("CALL"), 1)
        # 記録が落ちたことを silent にしない（理由の型名だけを stderr に出す）
        self.assertIn("record not written", result.stderr)
        self.assertNotIn("error_details", result.stderr)

    def test_missing_record_script_reports_the_reason_instead_of_silence(self):
        """記録スクリプトが欠落しても exit 0。ただし **silent には消さない**。

        記録本体を外部ファイルへ出した結果、「配置が不完全なら記録も通知も起きない」
        経路ができた。guard が理由を出さないと、この経路だけ stderr が 0 バイトになり、
        AC-16（通知）と AC-17（記録）が同時に無症状で失われる。guard を外せば python
        自身が診断を出す以上、guard は唯一の signal を握り潰していることになる。
        """
        scripts = self.tmp / "scripts"
        shutil.copytree(HOOK.parent, scripts)
        record_script = scripts / "lib" / "stop-failure-record.py"
        self.assertTrue(record_script.exists(), "fixture precondition")
        record_script.unlink()

        result = subprocess.run(
            ["bash", str(scripts / HOOK.name)],
            input=json.dumps({"error": "api_error", "error_details": "SECRET", "session_id": "a"}),
            capture_output=True, text=True,
            env=_make_env(self.home, stub_dir=self.stub_dir), timeout=60,
        )

        self.assertEqual(result.returncode, 0, "hook must never break the turn")
        self.assertFalse(self.record.exists())
        self.assertFalse(self.log.exists())
        self.assertNotEqual(result.stderr, "", "missing record script must not be silent")
        self.assertIn("record script missing", result.stderr)
        # 診断は stderr だけに出す。hook 出力契約（stdout は空）はこの経路でも侵さない。
        self.assertEqual(result.stdout, "")
        # 理由は配置の話。payload 由来の断片は 1 バイトも載せない。
        self.assertNotIn("SECRET", result.stderr)

    def _run_with_dead_pipe(self, which: str, *, missing_record: bool) -> int:
        """読み手が既に消えた pipe を stdout / stderr に渡して hook を起動する。

        `|| true` は終了ステータスの話なので、**シグナルによる自プロセスの死**は
        捕まえられない。読み手の消えた pipe への write は SIGPIPE を起こし、既定処理
        では shell 自身が死ぬ（`returncode` が負値になる ＝ `exit 0` に到達しない）。
        """
        scripts = self.tmp / f"scripts-{which}-{int(missing_record)}"
        shutil.copytree(HOOK.parent, scripts)
        if missing_record:
            (scripts / "lib" / "stop-failure-record.py").unlink()

        read_end, write_end = os.pipe()
        os.close(read_end)          # 読み手を先に消す = 以後の write は SIGPIPE
        try:
            proc = subprocess.Popen(
                ["bash", str(scripts / HOOK.name)],
                stdin=subprocess.PIPE,
                stdout=write_end if which in ("stdout", "both") else subprocess.DEVNULL,
                stderr=write_end if which in ("stderr", "both") else subprocess.DEVNULL,
                env=_make_env(self.home, stub_dir=self.stub_dir),
            )
        finally:
            os.close(write_end)
        # hang したときに子と stdin を残さない（子が残ると後続 subtest の fd と
        # プロセスが積み上がる。到達するのは hook が block したときだけ）。
        try:
            proc.communicate(
                json.dumps({"error": "api_error", "session_id": "a"}).encode(), timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise
        return proc.returncode

    def test_full_install_survives_a_stderr_pipe_with_no_reader(self):
        """SIGPIPE を無視に倒しても正常系（記録 + 通知 1 回）が壊れないこと。"""
        returncode = self._run_with_dead_pipe("stderr", missing_record=False)
        self.assertEqual(returncode, 0)
        self.assertTrue(self.record.exists(), "the happy path must still record")
        self.assertEqual(self.log.read_text(encoding="utf-8").count("CALL"), 1)

    def test_full_install_survives_a_stdout_pipe_with_no_reader(self):
        """stderr 1 形ではなく fd の class として閉じていること。"""
        returncode = self._run_with_dead_pipe("stdout", missing_record=False)
        self.assertGreaterEqual(returncode, 0, "hook must not be killed by a signal")
        self.assertEqual(returncode, 0)
        self.assertTrue(self.record.exists())

    # --- requirements AC-16（R1.4）「exit 0 の射程」の**射程内**を面で固定する ---
    #
    # 射程内 = (E) hook が扱う**データ**の I/O（stdin の payload read / stdout・stderr
    # への write / 記録先への write）が errno で失敗する経路 + (S) 追加の資源制限・
    # 端末設定なしの既定環境で成立しうる trap 可能シグナル（実測で SIGPIPE のみ）。
    # ここで測るのはその内側だけで、**射程外は測らない**（trap 不能シグナル / 既定
    # 無効の設定を要するシグナル / 外部起因シグナル / 終了コードが返らない形 /
    # プログラム本体の読み込み失敗 = NEW-1）。射程外の列挙と実測値は requirements
    # § Correction Log: AC-16 の fail-open 射程を実測で限定（2026-08-26）が正本で、
    # **ここには複写しない**。テストを射程外へ広げると、達成不能な全称を
    # テストへ書き写すことになる。
    IN_SCOPE_OUTPUT_FAILURES = ("closed", "dead_pipe", "pty_hangup")

    def _scripts_copy(self, name: str, *, missing_record: bool) -> Path:
        scripts = self.tmp / name
        if not scripts.exists():
            shutil.copytree(HOOK.parent, scripts)
            if missing_record:
                (scripts / "lib" / "stop-failure-record.py").unlink()
        return scripts

    def _run_with_broken_output(self, scripts: Path, form: str, which: str) -> int:
        """stdout / stderr / 両方を「壊れた書き先」にして hook を 1 回起動する。"""
        argv = ["bash", str(scripts / HOOK.name)]
        target = subprocess.DEVNULL
        opened: list[int] = []
        if form == "closed":
            # 子の中で fd を閉じてから exec する（以後の write は EBADF）
            pre = []
            if which in ("stdout", "both"):
                pre.append("exec 1>&-")
            if which in ("stderr", "both"):
                pre.append("exec 2>&-")
            argv = ["bash", "-c", "; ".join(pre) + '; exec bash "$0"',
                    str(scripts / HOOK.name)]
        elif form == "dead_pipe":
            read_end, write_end = os.pipe()
            os.close(read_end)      # 読み手を先に消す = 以後の write は SIGPIPE
            target, opened = write_end, [write_end]
        else:                       # pty_hangup: master を閉じた slave への write = EIO
            master, slave = os.openpty()
            target, opened = slave, [slave, master]

        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if which in ("stdout", "both"):
            kwargs["stdout"] = target
        if which in ("stderr", "both"):
            kwargs["stderr"] = target
        try:
            proc = subprocess.Popen(
                argv, stdin=subprocess.PIPE,
                env=_make_env(self.home, stub_dir=self.stub_dir), **kwargs)
        finally:
            for fd in opened:
                os.close(fd)
        try:
            proc.communicate(
                json.dumps({"error": "api_error", "session_id": "a"}).encode(), timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise
        return proc.returncode

    def test_in_scope_output_failures_all_exit_zero(self):
        """射程内 18 形すべてで rc 0（AC-16 / R1.4 の射程内の機械検証）。

        射程を限定した以上、内側は 1 形ずつではなく**面で**測る。2 変位（記録
        script 欠落 ＝ 診断が出る形 / 完全な配置 ＝ 正常系）× 3 失敗形（fd 閉塞 ＝
        EBADF / 読み手の消えた pipe ＝ SIGPIPE -> EPIPE / master を閉じた pty ＝
        EIO）× 3 fd（stdout / stderr / 両方）。

        判別力: `trap '' PIPE` を落とすと「記録 script 欠落 × dead_pipe ×
        {stderr, both}」が rc -13 に落ちる（親 `c9f3621` の実測と同値）ので、この面は
        空の pin ではない。
        """
        for missing_record in (True, False):
            scripts = self._scripts_copy(f"scope-{int(missing_record)}",
                                         missing_record=missing_record)
            for form in self.IN_SCOPE_OUTPUT_FAILURES:
                for which in ("stdout", "stderr", "both"):
                    with self.subTest(missing_record=missing_record, form=form, fd=which):
                        rc = self._run_with_broken_output(scripts, form, which)
                        self.assertGreaterEqual(
                            rc, 0, "an in-scope path must not kill the hook by a signal")
                        self.assertEqual(
                            rc, 0, "an in-scope output failure must keep exit 0")

    def test_home_unset_without_override_is_noop(self):
        env = os.environ.copy()
        env.pop("HOME", None)
        env.pop("GDD_HOOK_STATE_DIR", None)
        env["PATH"] = f"{self.stub_dir}{os.pathsep}{env['PATH']}"
        result = subprocess.run(
            ["bash", str(HOOK)],
            input=json.dumps({"error": "api_error", "error_details": "x", "session_id": "a"}),
            capture_output=True, text=True, env=env, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists())

    def test_hook_emits_no_stdout(self):
        """StopFailure は hook 出力契約を使わない（副作用のみ / design § hook API）。"""
        result = _run({"error": "api_error", "error_details": "x", "session_id": "a"},
                      self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
