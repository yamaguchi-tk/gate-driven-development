"""parser / lib が利用できないとき、および実行時例外の fail-closed 契約（AC-10 / AC-11）。

`lib/git_command_parse.py` の欠落・構文エラー・API 欠落・例外・再帰上限と、state を読む
`lib/regular_file.py` の欠落のいずれでも deny へ倒れることを、scripts ツリーの複製に対して検証する。分割の経緯と共有 fixture は
`tests/_root_branch_guard_support.py` を参照。
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import ROOT


class ParserUnavailableFailClosedTests(unittest.TestCase):
    """AC-10（parser・regular_file の import 失敗）/ AC-11（実行時例外）が無言で allow へ倒れない。"""

    def _copy_scripts_tree(self, dest: Path) -> Path:
        src = ROOT / "hooks" / "scripts"
        copied = dest / "scripts"
        shutil.copytree(src, copied)
        return copied

    def _run_guard_from(self, scripts_dir: Path, repo: Path, command: str):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command, "cwd": str(repo)},
        }
        return subprocess.run(
            ["python3", str(scripts_dir / "validate-worktree-command.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_deny_when_regular_file_missing(self):
        # state を読む lib/regular_file.py が欠けても止め、回復手順がそのファイルを名指しする
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)
            (scripts_dir / "lib" / "regular_file.py").unlink()

            result = self._run_guard_from(scripts_dir, repo, "git checkout -b feature-x")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("lib/regular_file.py", payload["systemMessage"])

    def test_deny_when_git_command_parse_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)
            (scripts_dir / "lib" / "git_command_parse.py").unlink()

            result = self._run_guard_from(
                scripts_dir,
                repo,
                "git worktree add /tmp/example-gdd-worktree -b codex/20260903-x origin/main",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_deny_when_git_command_parse_has_syntax_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)
            (scripts_dir / "lib" / "git_command_parse.py").write_text(
                "def broken(:\n", encoding="utf-8"
            )

            result = self._run_guard_from(
                scripts_dir,
                repo,
                "git worktree add /tmp/example-gdd-worktree -b codex/20260903-x origin/main",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_allow_when_command_has_no_git_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)
            (scripts_dir / "lib" / "git_command_parse.py").unlink()

            result = self._run_guard_from(scripts_dir, repo, "echo hello")
            self.assertEqual(result.returncode, 0)

    def test_deny_when_lib_missing_command_substitution_placeholder(self):
        """AC-10: lib が古い版のまま COMMAND_SUBSTITUTION_PLACEHOLDER が無い場合も deny。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)
            lib_path = scripts_dir / "lib" / "git_command_parse.py"
            text = lib_path.read_text(encoding="utf-8")
            original = text
            text = text.replace(
                'COMMAND_SUBSTITUTION_PLACEHOLDER = "__gdd_cmd_subst__"',
                "",
            )
            self.assertNotEqual(
                original,
                text,
                "public constant definition not found; update this test if it moved",
            )
            lib_path.write_text(text, encoding="utf-8")

            result = self._run_guard_from(
                scripts_dir,
                repo,
                "git switch -c codex/20260903-x",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )
            # 機序の識別: import 失敗経路（emit_deny_parser_unavailable）であることを
            # assert する。通常の deny（emit_deny）は "failed to import" を含まないため、
            # 定数を import せず literal で複製する実装（ADR-2 が却下した形）では
            # このテストが FAIL する。
            self.assertIn("failed to import", payload["systemMessage"])

    def test_deny_when_root_branch_name_candidates_raises(self):
        """AC-11: split_segments 以降の実行時例外は emit_deny（rc=2）に倒れる。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)
            hook_path = scripts_dir / "validate-worktree-command.py"
            text = hook_path.read_text(encoding="utf-8")
            marker = "def root_branch_name_candidates(segments: list[list[str]]) -> tuple[set[str], bool]:"
            self.assertIn(marker, text, "marker not found; update this test if the signature changed")
            injected = marker + '\n    raise RuntimeError("injected")\n'
            text = text.replace(marker, injected, 1)
            hook_path.write_text(text, encoding="utf-8")

            result = self._run_guard_from(
                scripts_dir,
                repo,
                "git switch -c codex/20260903-x",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_deny_when_split_segments_exhausts_recursion(self):
        """AC-11 / ADR-5: `split_segments` 自体の例外も deny に倒れる。

        深くネストした `$(` は `git_command_parse` の再帰下降で RecursionError を
        送出する。ADR-5 が `main()` の try を `split_segments` の直前まで広げた
        根拠がこの経路で、try が `root_state_blocks` 直前から始まる
        （ADR-5 以前の狭い範囲）実装では例外が捕捉されず rc=1 = PreToolUse
        非ブロッキング＝コマンド実行の fail-open になる。注入は不要で、
        本番コードのまま rc=2 を固定できる。
        """
        depth = 1500
        command = "git switch -c " + "$(" * depth + "x" + ")" * depth
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)

            # 前提の固定: この入力が実際に split_segments で例外になること。
            sys.path.insert(0, str(scripts_dir / "lib"))
            try:
                import git_command_parse

                with self.assertRaises(RecursionError):
                    git_command_parse.split_segments(command)
            finally:
                sys.path.remove(str(scripts_dir / "lib"))
                sys.modules.pop("git_command_parse", None)

            result = self._run_guard_from(scripts_dir, repo, command)
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_deny_when_is_linked_worktree_raises(self):
        """AC-11: `is_linked_worktree` の例外も deny に倒れる（PR #34 Copilot review 指摘）。

        **修正前の挙動**（commit `fd1a5b9` で是正済み。本テストはその回帰テスト）:
        `main()` の `try` ブロックは `split_segments` から
        `root_state_blocks` / `_creates_gdd_named_branch` までを覆っていたが、
        その直後に呼ばれる `is_linked_worktree(cwd)` は同じ try の外にあった。
        `is_linked_worktree` は内部で `git_output()`（`subprocess.run(...,
        text=True)`）を呼ぶため、`git rev-parse` の出力が非 UTF-8 の場合
        `UnicodeDecodeError` を送出しうる。この例外が try の外で発生すると
        `main()` の呼び出し元にまで伝播し、Python が未捕捉例外で終了して
        returncode 1（PreToolUse の非ブロッキングエラー = fail-open）になっていた。

        **現行実装**: `is_linked_worktree(cwd)` は同じ `try` 内へ移動済みで、
        本テストは修正が今後も維持されることを固定する回帰テスト。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            dest = Path(tmp) / "copy"
            dest.mkdir()
            scripts_dir = self._copy_scripts_tree(dest)
            hook_path = scripts_dir / "validate-worktree-command.py"
            text = hook_path.read_text(encoding="utf-8")
            marker = "def is_linked_worktree(cwd: Path) -> bool:"
            self.assertIn(marker, text, "marker not found; update this test if the signature changed")
            injected = marker + '\n    raise UnicodeDecodeError("utf-8", b"\\xff", 0, 1, "injected")\n'
            text = text.replace(marker, injected, 1)
            hook_path.write_text(text, encoding="utf-8")

            result = self._run_guard_from(
                scripts_dir,
                repo,
                "git switch -c codex/20260903-x",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )
