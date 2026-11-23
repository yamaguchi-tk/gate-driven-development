"""root branch guard が、payload の cwd を解けないときに git コマンドを通さないこと。

cwd を解く処理が main() の try の外にあると、`~-`・NUL・lone surrogate の cwd で例外になり、
hook が exit 1（PreToolUse の非 block）で終わって通してしまう。cwd を解けない git コマンドは止め、
git を含まないコマンドと、コマンドを取り出せない壊れた payload は今までどおり通す。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import run_root_branch_guard_raw as run_guard


def payload(command: str, cwd: str, key: str = "cwd") -> bytes:
    # payload の cwd は tool_input.cwd、Codex は tool_input.workdir。guard はどちらも読む。
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": command, key: cwd}}).encode()


UNRESOLVABLE_CWDS = ("~-/x", "/tmp/a\x00b", "/tmp/\ud800")


class PayloadCwdTests(unittest.TestCase):
    def test_unresolvable_cwd_denies_branch_creation(self) -> None:
        for key in ("cwd", "workdir"):
            for cwd in UNRESOLVABLE_CWDS:
                with self.subTest(key=key, cwd=cwd):
                    result = run_guard(payload("git checkout -b feat", cwd, key))
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    output = json.loads(result.stderr.decode(errors="surrogateescape"))
                    self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
                    self.assertIn("could not resolve the working directory", output["systemMessage"])

    def test_unresolvable_cwd_allows_commands_without_the_git_word(self) -> None:
        # 止める範囲は parser が無いときと同じく `git` の語に当たるコマンドだけ。
        for command in ("ls", "ls .gitignore", "open https://github.com/x"):
            for cwd in UNRESOLVABLE_CWDS:
                with self.subTest(command=command, cwd=cwd):
                    result = run_guard(payload(command, cwd))
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_removed_hook_cwd_blocks_only_branch_creation(self) -> None:
        # payload の tool_input に cwd が無く（Claude Code）、hook 自身の cwd が消えているとき。
        # ブランチ・GDD 名の worktree を作るコマンドだけを止め、消えた worktree の後始末は通す。
        # python3 が消えた cwd で起動できない環境（hook のコードに届かない）では skip する。
        with tempfile.TemporaryDirectory() as base:
            gone = Path(base) / "gone"
            gone.mkdir()
            probe = run_guard(b"", removed_cwd=gone)
            if b"failed to make path absolute" in probe.stderr:
                self.skipTest("python3 cannot start in a removed cwd on this platform")
        cases = (
            ("git checkout -b feat", 2),
            ("echo .gitignore; g''it checkout -b feat", 2),
            ("git worktree add ../wt -b codex/20261003-x origin/main", 2),
            ("git worktree prune", 0),
            ("git -C /tmp status", 0),
        )
        for command, expected in cases:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as base:
                gone = Path(base) / "gone"
                gone.mkdir()
                stdin = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}).encode()
                result = run_guard(stdin, removed_cwd=gone)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                if expected == 2:
                    output = json.loads(result.stderr.decode(errors="surrogateescape"))
                    self.assertIn("could not resolve the working directory", output["systemMessage"])

    def test_broken_payload_is_allowed_like_invalid_json(self) -> None:
        for stdin in (b"not json", b'["git checkout -b feat"]', b'"git checkout -b feat"'):
            with self.subTest(stdin=stdin):
                result = run_guard(stdin)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_payload_not_decodable_as_utf8_is_allowed(self) -> None:
        # UTF-8 mode を切り、strict に読ませて UnicodeDecodeError の経路を通す。
        result = run_guard(b"\xff\xfe", extra_env={"PYTHONUTF8": "0", "PYTHONIOENCODING": "utf-8:strict"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
