"""root branch guard の segmentation 経路（複合コマンド・コマンド置換・heredoc）。

`split_segments` が分解した各 segment に対する deny 判定と、引用符・heredoc 本文の
false positive 抑止をまとめる。分割の経緯と共有 fixture は
`tests/_root_branch_guard_support.py` を参照。
"""

import json
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import RootBranchGuardFixtureMixin


class RootBranchGuardSegmentationTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    def test_hook_detects_root_branch_creation_after_various_compound_separators(self):
        # AC-4 / AC-9: `&&` 以外の区切り（`;` `||` `|` 改行 `bash -c`）でも
        # 後段が独立に判定される（Implementation Medium-2 remediation）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            commands = [
                "git worktree add /tmp/w -b codex/20260903-a origin/main ; "
                "git switch -c codex/20260903-b",
                "git worktree add /tmp/w -b codex/20260903-c origin/main || "
                "git switch -c codex/20260903-d",
                "git worktree add /tmp/w -b codex/20260903-e origin/main | "
                "git switch -c codex/20260903-f",
                "git worktree add /tmp/w -b codex/20260903-g origin/main\n"
                "git switch -c codex/20260903-h",
                "bash -c 'git switch -c codex/20260903-i'",
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_unquoted_command_substitution_segmentation(self):
        # Implementation High-1 remediation: `$(...)` / バッククォートによる
        # セグメント分断で git token を含むセグメントから引数が漏れる regression。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)
            head_sha = self._head(repo)

            for command in [
                "git worktree add $(mktemp -d) -b codex/20260903-a HEAD",
                "git worktree add `mktemp -d` -b codex/20260903-b HEAD",
                "git -C $(pwd) checkout -b codex/20260903-c",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)

            result = self._run_guard(
                repo,
                "git worktree add $(mktemp -d) -b codex/20260903-d main",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from a local default branch",
                payload["systemMessage"],
            )

            # 回帰確認: command substitution が絡まない既存 allow ケースは維持
            result = self._run_guard(
                repo,
                f"git worktree add /tmp/w -b codex/20260903-e {head_sha}",
            )
            self.assertEqual(result.returncode, 0)

    def test_hook_blocks_double_quoted_command_substitution_segmentation(self):
        # Round 2 finding の対照: bash が **実際に展開する** 形（ダブルクォート内の
        # `$(...)` / バッククォート、クォート外でエスケープ済み `\'` の後ろ）は
        # deny のまま維持する（シングルクォート対応で fail-open に倒さない）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                'git commit -m "example: $(git switch -c codex/20260904-a)"',
                'git commit -m "example: `git switch -c codex/20260904-b`"',
                "echo it\\'s $(git switch -c codex/20260904-c)",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_nested_shell_command_substitution_segmentation(self):
        # `bash -c '...'` の中身はシングルクォート内だが nested shell が展開する。
        # 外側のクォート追跡で見送った `$(...)` / バッククォートも、nested shell
        # 展開時に切り出されて `-b <branch> HEAD` がセグメントから漏れないこと。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "bash -c 'git worktree add $(mktemp -d) -b codex/20260904-d HEAD'",
                "bash -c 'git worktree add `mktemp -d` -b codex/20260904-e HEAD'",
                "bash -c 'git -C $(pwd) checkout -b codex/20260904-f'",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)

    def test_hook_blocks_executed_heredoc_body(self):
        # Security High remediation: heredoc 経由で実際にシェルへ渡され実行される
        # 本文（`bash <<EOF` 等）を guard から不可視にしない。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            commands = [
                "bash <<'EOF'\ngit switch -c codex/20260903-a\nEOF",
                "sh <<EOF\ngit switch -c codex/20260903-b\nEOF",
                "cat <<'EOF' | bash\ngit switch -c codex/20260903-c\nEOF",
                "bash -s <<'EOF'\ngit switch -c codex/20260903-d\nEOF",
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

            # 回帰確認: 非実行系 heredoc（AC-8 で承認済み）は引き続き allow
            result = self._run_guard(
                repo,
                "git commit -F - <<MSG\n"
                "use git switch -c codex/20260903-x instead\n"
                "MSG",
            )
            self.assertEqual(result.returncode, 0)

    def test_hook_blocks_executed_heredoc_body_through_ampersand_redirect(self):
        # PR #28 Copilot review: `_PIPELINE_BOUNDARY_RE` が `|&`/`&>`/`>&` 中の `&`
        # も無条件に境界扱いしていたため、`cat <<EOF |& bash` のような実行される
        # heredoc で interpreter 名（bash）が走査範囲外に落ち、本文が strip されて
        # guard から不可視になっていた regression。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            commands = [
                "cat <<'EOF' |& bash\ngit switch -c codex/20260903-e\nEOF",
                "bash <<'EOF' &> /tmp/gdd-probe.log\ngit switch -c codex/20260903-f\nEOF",
                # PR #28 followup review: `<&`（入力 fd 複製）中の `&` も境界扱いしない。
                "cat <<'EOF' 3<&0 | bash\ngit switch -c codex/20260904-g\nEOF",
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_command_after_false_positive_heredoc_marker(self):
        # Security Medium / Implementation Medium-1 remediation: クォート内文字列
        # 中の `<<WORD` に heredoc marker regex が誤反応し、終端行が見つからない
        # まま残り全行を破棄してしまう regression。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            command = (
                'git commit -m "see <<EOF docs"\n'
                "git switch -c codex/20260903-a"
            )
            result = self._run_guard(repo, command)
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_allows_quoted_string_false_positive(self):
        # AC-8 FP-2: クォート内の文字列に誤爆しない
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(
                repo,
                "git commit -m 'use git switch -c codex/20260903-x instead'",
            )
            self.assertEqual(result.returncode, 0)

    def test_hook_allows_single_quoted_command_substitution_false_positive(self):
        # AC-8 FP-2（Round 2 finding）: bash が展開しないシングルクォート内の
        # `$(...)` / バッククォート、およびダブルクォート内でエスケープされた
        # `\$(` はリテラル文字列であり、独立セグメント化して deny しない。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git commit -m 'example: $(git switch -c codex/20260904-a)'",
                "git commit -m 'example: `git switch -c codex/20260904-b`'",
                "git commit -m 'example: $(git switch -c codex/20260904-c)' && echo done",
                'git commit -m "example: \\$(git switch -c codex/20260904-d)"',
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_allows_heredoc_body_false_positive(self):
        # AC-8 FP-2: heredoc 本文への誤爆を許さない
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            command = (
                "git commit -F - <<MSG\n"
                "use git switch -c codex/20260903-x instead\n"
                "MSG"
            )
            result = self._run_guard(repo, command)
            self.assertEqual(result.returncode, 0)

    def test_hook_detects_root_branch_creation_after_compound_command(self):
        # AC-4: 複合コマンドの後段が独立に判定される
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            command = (
                "git worktree add /tmp/w -b codex/20260903-a origin/main && "
                "git switch -c codex/20260903-b"
            )
            result = self._run_guard(repo, command)
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_allows_segmentation_relief_cases(self):
        # AC-7: セグメント分割の副作用で意図的に deny→allow になるケース
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git worktree add /tmp/w -b codex/20260903-a origin/main && "
                "git -C /tmp/w log -1 HEAD",
                "git worktree add /tmp/w -b codex/20260903-b origin/main && "
                "echo done to main",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_allows_unrelated_string_in_other_segment(self):
        # AC-4: 別 segment の無関係な文字列は候補に混入しない。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_guard(
                repo,
                "git commit -m 'codex/20260903-x' --allow-empty && git switch -c feature-x",
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])
