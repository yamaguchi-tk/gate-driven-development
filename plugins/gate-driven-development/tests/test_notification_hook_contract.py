"""`run-notification-hook.sh` の契約テスト（AC-18）。

design.md § Sensitive Data / Masking Policy の enforcement point 2（通知本文は
`notification_type` の allowlist に対する**固定文言の対応表**のみ・`message` /
`title` は読まない・`osascript -` + `system attribute` で連結しない）と
enforcement point 4（`terminalSequence` はリテラル定数のみ ＝ payload 由来
文字列を stdout に載せない）を実行可能な形で固定する。

通知センターへの実表示は自動検証しない（requirements AC-18 / Completion
Testability Matrix の `e2e-required（表示のみ）`）。ここで固定するのは
「通知コマンドが 1 回呼ばれる」「allowlist 外は no-op」「payload 由来の
自由文が通知コマンドへ env / argv / stdin のどの経路でも渡らない」まで。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import PLUGIN_ROOT as ROOT
HOOK = ROOT / "hooks" / "scripts" / "run-notification-hook.sh"

# AC-18 の allowlist。hook 内の固定文言対応表のキー集合と一致していなければならない。
ALLOWED_TYPES = ("idle_prompt", "permission_prompt")


def _make_env(home: Path, *, stub_dir: Path | None = None,
              isolated_path: bool = False) -> dict:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
    if stub_dir is not None:
        env["PATH"] = str(stub_dir) if isolated_path else f"{stub_dir}{os.pathsep}{env['PATH']}"
    return env


def _run(payload, home: Path, **kwargs) -> subprocess.CompletedProcess:
    env = _make_env(home, **kwargs)
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        ["bash", str(HOOK)], input=body, capture_output=True, text=True, env=env, timeout=60,
    )


def _bash_interpreters() -> dict[str, str]:
    """PATH 上と既知の場所から**相異なる bash** を集める（`--version` 行で dedupe）。

    T-18 Attempt 1 の MED-T18-A は、hook の測定基盤が bash 3.2.57 / macOS しか
    通っておらず、**環境（bash のバージョン）という入力空間の 1 軸**が振られて
    いなかったことから漏れた。ここで版を跨いで測ることでその軸を塞ぐ。
    macOS の既定 bash は 3.2.57 の 1 本だけなので、この列挙は開発機では 1 本、
    Linux（bash 5 系）や複数版を入れた環境では 2 本以上になる。
    """
    found: dict[str, str] = {}
    candidates = [os.path.join(d, "bash") for d in os.environ.get("PATH", "").split(os.pathsep) if d]
    candidates += ["/bin/bash", "/usr/bin/bash", "/opt/homebrew/bin/bash", "/usr/local/bin/bash"]
    for path in candidates:
        if not (os.path.isfile(path) and os.access(path, os.X_OK)):
            continue
        try:
            out = subprocess.run([path, "--version"], capture_output=True, text=True,
                                 timeout=30).stdout
        except OSError:  # pragma: no cover - 実行可能でも exec できない環境向け
            continue
        version = out.splitlines()[0].strip() if out else ""
        if version and version not in found:
            found[version] = path
    return found


def _install_notify_stub(stub_dir: Path, log: Path, *, exit_code: int = 0) -> Path:
    """`osascript` の stub。env / argv / stdin の 3 経路すべてを記録する。

    通知本文は env（`GDD_NOTIFY_BODY`）で渡す規約なので、stdin だけを見る stub では
    「本文に payload 由来の自由文が載っていない」ことを測れない。3 経路すべてを
    1 ファイルに落とす（`test_stop_failure_hook_contract.py` と同じ形）。
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
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def _install_notify_send_stub(bin_dir: Path, log: Path) -> Path:
    """`notify-send` の stub。argv を 1 引数 1 行で落とす。

    `--` の option 終端（design § enforcement point 2）は argv の**並び**でしか
    測れないため、`$*` に潰さず 1 引数ずつ記録する。
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "notify-send"
    script.write_text(
        "#!/usr/bin/env bash\n"
        "{\n"
        '  printf "CALL\\n"\n'
        '  for _arg in "$@"; do printf "ARG:%s\\n" "$_arg"; done\n'
        f'}} >> "{log}"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


# hook が PATH から引く外部コマンドのうち「無いと動けない」もの。通知コマンド
# （osascript / notify-send）はここに入れない = 不在で no-op になることを測る。
# 依存が増えたらこのリストが更新されない限りテストが落ちる（依存面の pin も兼ねる）。
REQUIRED_COMMANDS = ("bash", "dirname", "cat")


def _bin_path(tmp: Path, name: str, *, with_python: bool) -> Path:
    """必須コマンド（+ 任意で python3）だけが引ける PATH を作る。

    bash も置くのは subprocess が env の PATH から実行ファイルを探すため
    （置かないと hook を起動する前に FileNotFoundError になり、no-op 経路を測れない）。
    """
    bin_dir = tmp / name
    bin_dir.mkdir(parents=True, exist_ok=True)
    if with_python:
        (bin_dir / "python3").symlink_to(sys.executable)
    for cmd in REQUIRED_COMMANDS:
        resolved = shutil.which(cmd)
        if not resolved:
            raise AssertionError(f"{cmd} not found on PATH")
        (bin_dir / cmd).symlink_to(resolved)
    # fixture 不変条件。`assert` は `python -O` で消えるため明示的に送出する
    # （不在のはずのコマンドが混入したまま通すと no-op 経路の検証が空虚になる）。
    absent_names = ["osascript", "notify-send"]
    if not with_python:
        absent_names += ["python3", "python"]
    for absent in absent_names:
        if (bin_dir / absent).exists():
            raise AssertionError(f"PATH に不在であるべき {absent} が存在する: {bin_dir}")
    return bin_dir


class _NotificationHookTestBase(unittest.TestCase):
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

    def _body(self, notification_type: str, **extra) -> str:
        """1 回だけ通知が出ることを確かめ、env 経由で渡った本文を返す。"""
        payload = {"notification_type": notification_type}
        payload.update(extra)
        result = _run(payload, self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        self.assertEqual(captured.count("CALL"), 1, captured)
        line = next(l for l in captured.splitlines() if l.startswith("ENV:"))
        return line[len("ENV:"):]


class NotificationHookTriggerTests(_NotificationHookTestBase):
    """AC-18 前半: allowlist に載った type では通知コマンドが 1 回呼ばれる。"""

    def test_idle_prompt_triggers_notification_exactly_once(self):
        self.assertTrue(self._body("idle_prompt"))

    def test_permission_prompt_triggers_notification_exactly_once(self):
        self.assertTrue(self._body("permission_prompt"))

    def test_each_allowed_type_maps_to_a_distinct_fixed_body(self):
        """対応表が「表」であること。両 type が同一本文なら分岐に判別力が無い。"""
        bodies = []
        for notification_type in ALLOWED_TYPES:
            self.log.unlink(missing_ok=True)
            bodies.append(self._body(notification_type))
        self.assertEqual(len(set(bodies)), len(ALLOWED_TYPES), bodies)

    def test_body_is_a_single_line(self):
        """通知センターは改行を表示せず truncate する。本文は 1 行で固定する。"""
        for notification_type in ALLOWED_TYPES:
            self.log.unlink(missing_ok=True)
            body = self._body(notification_type)
            self.assertNotIn("\n", body)
            self.assertNotIn("\r", body)

    def test_message_and_title_never_reach_notification_command(self):
        """enforcement point 2: 自由文は env / argv / stdin のどの経路でも届かない。"""
        secret = "SECRET-PAYLOAD-MESSAGE-XYZ"
        result = _run(
            {"notification_type": "idle_prompt", "message": secret, "title": secret,
             "cwd": secret, "session_id": secret},
            self.home, stub_dir=self.stub_dir,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        self.assertIn("CALL", captured, "notification stub was not invoked at all")
        self.assertNotIn(secret, captured)
        self.assertNotIn(secret, result.stdout)
        self.assertNotIn(secret, result.stderr)

    def test_applescript_body_is_passed_by_env_not_concatenated(self):
        """本文は env 経由。stdin のスクリプトは payload 由来値を含まないリテラル。"""
        body = self._body("idle_prompt")
        captured = self._calls()
        stdin_part = captured.split("STDIN:", 1)[1]
        self.assertIn('system attribute "GDD_NOTIFY_BODY"', stdin_part)
        self.assertNotIn(body, stdin_part)
        argv_line = next(l for l in captured.splitlines() if l.startswith("ARGV:"))
        self.assertEqual(argv_line, "ARGV:-", "osascript must read the script from stdin")

    def test_notify_send_is_called_with_option_terminator_before_body(self):
        """`notify-send` は argv 渡し + `--` で option 終端（design § enforcement point 2）。

        design が「本文の先頭が `-` でも壊れないことを 1 ケース固定する」と明記した
        項目。Linux 実機は要らない。`osascript` を不在にした PATH に `notify-send`
        の stub を置けば macOS 上で argv を直接測れる。
        """
        bin_dir = _bin_path(self.tmp, "notify-send-bin", with_python=True)
        _install_notify_send_stub(bin_dir, self.log)
        result = _run({"notification_type": "idle_prompt"}, self.home,
                      stub_dir=bin_dir, isolated_path=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self._calls()
        self.assertEqual(captured.count("CALL"), 1)
        args = [line[len("ARG:"):] for line in captured.splitlines() if line.startswith("ARG:")]
        self.assertEqual(args[:2], ["--", "GDD"], "option terminator must precede the title")
        self.assertEqual(len(args), 3, args)
        self.assertTrue(args[2])


class NotificationHookNoopTests(_NotificationHookTestBase):
    """AC-18 後半 + fail-open: allowlist 外・入力不正・依存不在はすべて no-op / exit 0。"""

    def _assert_noop(self, payload, **kwargs) -> subprocess.CompletedProcess:
        result = _run(payload, self.home, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._calls(), "")
        self.assertEqual(result.stdout, "")
        return result

    def test_other_notification_type_is_noop(self):
        self._assert_noop({"notification_type": "some_other_type"}, stub_dir=self.stub_dir)

    def test_missing_notification_type_is_noop(self):
        self._assert_noop({"message": "hello"}, stub_dir=self.stub_dir)

    def test_empty_payload_is_noop(self):
        self._assert_noop("", stub_dir=self.stub_dir)

    def test_invalid_json_payload_is_noop(self):
        self._assert_noop("{not json", stub_dir=self.stub_dir)

    def test_non_object_json_payload_is_noop(self):
        self._assert_noop("[1, 2, 3]", stub_dir=self.stub_dir)

    def test_non_string_notification_type_is_noop(self):
        """型を落とさず文字列化すると `["idle_prompt"]` が allowlist に当たりうる。"""
        self._assert_noop({"notification_type": ["idle_prompt"]}, stub_dir=self.stub_dir)

    def test_lookalike_type_inside_free_text_field_is_noop(self):
        """自由文に allowlist の字面を仕込んでも発火しない（JSON として読む）。"""
        self._assert_noop(
            {"notification_type": "other",
             "message": '{"notification_type": "idle_prompt"}'},
            stub_dir=self.stub_dir,
        )

    def test_kill_switch_suppresses_notification(self):
        (self.home / ".claude").mkdir(parents=True, exist_ok=True)
        (self.home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        self._assert_noop({"notification_type": "idle_prompt"}, stub_dir=self.stub_dir)

    def test_no_notification_command_is_noop(self):
        """`osascript` / `notify-send` の両方が不在なら no-op で exit 0（AC-18）。"""
        bin_dir = _bin_path(self.tmp, "no-notify-bin", with_python=True)
        self._assert_noop({"notification_type": "idle_prompt"},
                          stub_dir=bin_dir, isolated_path=True)

    def test_python_absent_is_a_silent_noop(self):
        """python 不在の扱いの判断を pin する: python 不在は**無音**で exit 0。

        `lib/` の欠落（＝ 本 plugin の配置ミス）は稀で診断の価値があるので
        `run-stop-failure-hook.sh` は stderr に理由を残すが、python 不在は
        「環境の性質」であって配置ミスではない。Notification は idle のたびに
        発火する高頻度 hook なので、環境由来の事実を毎回 stderr に出すと
        ノイズにしかならない。この非対称は意図的で、ここで固定する。
        """
        bin_dir = _bin_path(self.tmp, "no-python-bin", with_python=False)
        _install_notify_stub(bin_dir, self.log)
        result = self._assert_noop({"notification_type": "idle_prompt"},
                                   stub_dir=bin_dir, isolated_path=True)
        self.assertEqual(result.stderr, "")

    def test_notification_command_failure_still_exits_zero(self):
        """通知コマンドが非 0 で落ちても hook はターンを壊さない。"""
        _install_notify_stub(self.stub_dir, self.log, exit_code=3)
        result = _run({"notification_type": "idle_prompt"}, self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._calls().count("CALL"), 1)

    def test_hook_emits_no_stdout(self):
        """enforcement point 4: stdout は空。payload 由来の 1 バイトも載せない。

        `Notification` は `decision` / `systemMessage` / `hookSpecificOutput` を
        破棄するので出力契約は無く、`terminalSequence` に載せてよいのは hook 内の
        リテラル定数だけ。ここでは「payload 由来値は stdout に出ない」ことを、
        ANSI/OSC マーカーを仕込んだ payload で負の assert として固定する。
        """
        marker = "\x1b]0;PWNED\x07"
        for notification_type in ("idle_prompt", "some_other_type"):
            self.log.unlink(missing_ok=True)
            result = _run(
                {"notification_type": notification_type, "message": marker, "title": marker},
                self.home, stub_dir=self.stub_dir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("PWNED", self._calls())

    def test_payload_larger_than_env_limit_is_still_handled(self):
        """payload は env ではなく stdin で python へ渡す（T-17 実測の E2BIG 回避）。

        env 経由にすると巨大 payload で `execve` が E2BIG になり、通知が無症状で
        消える（design § enforcement point 1 の実測: macOS `ARG_MAX` 1,048,576 /
        Linux `MAX_ARG_STRLEN` 131,072）。閾値を跨ぐ 1 件で経路を固定する。
        """
        payload = {"notification_type": "idle_prompt", "message": "x" * 1_100_000}
        result = _run(payload, self.home, stub_dir=self.stub_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._calls().count("CALL"), 1, self._calls())


class NotificationHookFailOpenScopeTests(_NotificationHookTestBase):
    """AC-16 の射程 (S) と、ヘッダが掲げる射程記述そのものを機械検証する。

    T-18 Attempt 1 の ops-blocking Medium（MED-T18-A）の回帰 pin。
    """

    def _run_with_dead_stderr_pipe(self, bash_path: str, payload: bytes) -> int:
        """stderr = 読み手の消えた pipe。rc が負値ならシグナル死。"""
        read_end, write_end = os.pipe()
        os.close(read_end)          # 読み手を先に消す = 以後の fd 2 への write は SIGPIPE
        try:
            proc = subprocess.Popen(
                [bash_path, str(HOOK)],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=write_end,
                env=_make_env(self.home, stub_dir=self.stub_dir),
            )
        finally:
            os.close(write_end)
        try:
            proc.communicate(payload, timeout=60)
        except subprocess.TimeoutExpired:  # pragma: no cover - block したら証跡を残して落とす
            proc.kill()
            proc.communicate()
            raise
        return proc.returncode

    def test_nul_in_payload_with_dead_stderr_pipe_keeps_exit_zero(self):
        """payload に NUL が 1 バイトあるだけで hook が SIGPIPE 死しないこと。

        **hook 自身は fd 2 へ書かないが、解釈器の bash が書く**: bash 5 は NUL を
        含む入力の command substitution で警告を fd 2 に出す（実測 104B。
        `PAYLOAD="$(cat 2>/dev/null || true)"` の `2>/dev/null` は `cat` の stderr
        にしか掛からないので受け止められない）。fd 2 が読み手の消えた pipe だと
        この write が SIGPIPE を起こし、hook は rc 141 で死ぬ ―― 追加の資源制限も
        端末設定も要らないので **AC-16 (S) の射程内**。`trap '' PIPE` が閉じる。

        **環境も入力空間の 1 軸**なので、見つかった bash を版ごとに全部通す。
        判別力の実測（2026-08-26 / `trap '' PIPE` を落とす変異を隔離コピーへ適用）:
          - bash 5.2.37 (docker `python:3.11-slim`) … shipped rc 0 / 変異 **rc -13**
            ＝ 本テストだけが落ち、他の 21 本は通る（この形で KILL できる）
          - bash 5.3.15 (docker `bash:5`) … 同形を shell 経由で測ると 141（128+13）
          - bash 3.2.57 (macOS) … 変異でも rc 0。**この bash では検出力 0**なので、
            本テストの判別力は「bash 5 系が 1 本でも見つかる環境」に依存する
        null control（NUL 抜きの同一 payload）は全環境で stderr 0B / rc 0。
        """
        payload = b'{"notification_type": "idle_prompt", "message": "a\x00b"}'
        interpreters = _bash_interpreters()
        self.assertTrue(interpreters, "no bash interpreter found on this machine")
        for version, path in interpreters.items():
            with self.subTest(bash=version, path=path):
                self.log.unlink(missing_ok=True)
                rc = self._run_with_dead_stderr_pipe(path, payload)
                self.assertGreaterEqual(rc, 0, "a NUL byte in the payload must not kill the hook")
                self.assertEqual(rc, 0, "AC-16 (S) is in scope: it must stay exit 0")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
