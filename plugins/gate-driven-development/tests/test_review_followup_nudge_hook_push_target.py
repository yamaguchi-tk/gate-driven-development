"""review-followup nudge hook の push の検知と push 先 branch の解決の契約テスト。

`hooks/scripts/run-review-followup-nudge-hook.sh` が、Bash のコマンドから実際の `git push`
だけを拾い（echo・コメント・`--help`・`--dry-run`・`--delete` では `gh` を呼ばない）、
明示 refspec・`HEAD`・detached HEAD・`-` で始まる branch 名などから push 先 branch を
正しく決めることを測る。`test_review_followup_nudge_hook.py` から分けた。fixture は
`_review_followup_nudge_support.py` の `ReviewFollowupNudgeFixtureMixin` にある。
"""
from __future__ import annotations

import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from _review_followup_nudge_support import (
    _hash8,
    _write_stub_gh,
    ReviewFollowupNudgeFixtureMixin,
)


class ReviewFollowupNudgePushTargetTests(ReviewFollowupNudgeFixtureMixin, unittest.TestCase):
    def test_detached_head_without_explicit_refspec_is_noop(self) -> None:
        """明示 refspec の無い `git push`（暗黙に現在の checked-out branch を指す形）は、
        detached HEAD だと push 対象 branch を解決できないため no-op になる。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            head_sha = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            subprocess.run(["git", "-C", str(repo), "checkout", "-q", head_sha], check=True)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push origin",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists())

    def test_explicit_refspec_target_overrides_current_branch(self) -> None:
        """独立レビューで検出: 旧実装は現在 checked-out branch だけを見ていたため、
        `git push origin <branch>` で現在の branch と異なる branch を明示指定すると
        誤った branch で PR 有無を判定していた。`push_command_parse.classify_refspec`
        の `explicit_ref` を使い、明示された push 対象 branch を優先する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            # 現在の checked-out branch は "other-branch"。
            self._init_repo(repo, branch="other-branch")
            state_dir = Path(tmp) / "hookstate"
            cache_dir = state_dir / "review-followup-pr-cache"
            cache_dir.mkdir(parents=True)
            # hook 内の ROOT は bash の `$(pwd)` （symlink 解決済みの物理パス）。
            # macOS では tempfile が返す論理パス（/var/... 等）と物理パス
            # （/private/var/... 等）が食い違うため、`resolve()` で揃える。
            root_hash = _hash8(str(repo.resolve()))
            # 明示 push 対象 "feature-x" 用のキャッシュは "no"、現在 branch
            # "other-branch" 用のキャッシュは "yes" を事前に仕込む。
            # BRANCH ハッシュ判定に使うのは explicit_ref の解決結果なので、
            # 現在 branch のキャッシュが読まれたら誤り（"yes" が誤注入される）。
            # cached_epoch は「今」に近い値にする（0 のままだと TTL 判定で
            # 即座に expired 扱いになり、常に fresh な gh 呼び出しへフォール
            # バックしてキャッシュ命中を検証できない）。
            now_epoch = int(time.time())
            (cache_dir / f"{root_hash}__{_hash8('feature-x')}").write_text(
                f"{now_epoch}\nno\n", encoding="utf-8"
            )
            (cache_dir / f"{root_hash}__{_hash8('other-branch')}").write_text(
                f"{now_epoch}\nyes\n", encoding="utf-8"
            )
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.strip(), "",
                "明示 refspec 'feature-x' の cache('no') ではなく現在 branch "
                "'other-branch' の cache('yes') を読んでいる（誤注入）",
            )
            self.assertFalse(counter.exists(), "cache 命中時は gh を再呼び出ししない")

    def test_gh_pr_view_receives_target_branch(self) -> None:
        """独立レビュー2巡目で検出: 旧実装は `gh pr view` に branch を渡していな
        かったため、`gh` は current checked-out branch を見ていた（明示 refspec
        の解決結果が無視されていた）。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo, branch="other-branch")
            gh_stub = Path(tmp) / "gh-stub.sh"
            args_file = Path(tmp) / "args.log"
            _write_stub_gh(gh_stub, behavior="has-pr", args_file=args_file)
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(args_file.exists())
            self.assertEqual(
                args_file.read_text(encoding="utf-8").strip(),
                "feature-x",
                "gh pr view に明示 refspec 'feature-x' ではなく現在 branch が渡っている",
            )

    def test_explicit_ref_head_resolves_to_current_branch(self) -> None:
        """独立レビュー2巡目で検出: `git push origin HEAD` / `git push -u origin
        HEAD` は explicit_ref="HEAD" になる常用形。これを branch 名としてそのまま
        使うと全 branch が同一キャッシュキー "HEAD" を共有してしまうため、実際の
        checked-out branch 名へ解決し直す。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo, branch="release-branch")
            state_dir = Path(tmp) / "hookstate"
            cache_dir = state_dir / "review-followup-pr-cache"
            cache_dir.mkdir(parents=True)
            root_hash = _hash8(str(repo.resolve()))
            now_epoch = int(time.time())
            # 誤って "HEAD" をそのまま branch 名として使うと、この "yes" が
            # 読まれて誤注入される。正しい実装は "release-branch" のキャッシュ
            # （未作成 = 必ず fresh 判定）を経由する。
            (cache_dir / f"{root_hash}__{_hash8('HEAD')}").write_text(
                f"{now_epoch}\nyes\n", encoding="utf-8"
            )
            gh_stub = Path(tmp) / "gh-stub.sh"
            args_file = Path(tmp) / "args.log"
            _write_stub_gh(gh_stub, behavior="no-pr", args_file=args_file)
            result = self._run_hook(
                repo,
                "git push origin HEAD",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.strip(), "",
                "\"HEAD\" 用の cache('yes') が誤って使われている（誤注入）",
            )
            self.assertTrue(args_file.exists(), "現在 branch へ解決して fresh に gh を呼ぶはず")
            self.assertEqual(args_file.read_text(encoding="utf-8").strip(), "release-branch")

    def test_all_digit_branch_is_not_misread_as_pr_number(self) -> None:
        """独立レビュー3巡目で検出: `gh pr view <arg>` は <arg> が全桁数字だと
        branch 名ではなく PR 番号として解決する。`git push origin 1234` のような
        数字だけの branch 名を明示 refspec で push すると、無関係な PR #1234 の
        有無に基づいて誤注入されうるため、判定不能として抜ける。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push origin 1234",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists(), "gh を呼ばず判定不能として抜けるはず")

    def test_echo_prefixed_push_does_not_invoke_gh(self) -> None:
        """人間レビュー指摘 High-2: `is_git_push` の広い過検出をそのまま使うと、
        実行されない `echo git push ...` のようなコマンド文面でも認証付き
        `gh` が呼ばれる（PreToolUse は許可ダイアログより前なので、拒否した
        push でも問い合わせが走る）。command-start 限定の狭い判定で、この
        ケースでは `gh` を一切呼ばないことを固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "echo git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists(), "echo 経由の文面で gh を呼んではならない")

    def test_comment_prefixed_push_does_not_invoke_gh(self) -> None:
        """人間レビュー指摘 High-2: `# git push origin x` のようなコメント代わり
        の行でも `gh` を呼んではならない。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "# git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists())

    def test_help_flag_push_does_not_invoke_gh(self) -> None:
        """人間レビュー指摘 High-2: `git push --help` はマニュアルを開くだけで
        push を実行しない。`gh` を呼んではならない。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push --help",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists())

    def test_dry_run_push_does_not_invoke_gh(self) -> None:
        """人間レビュー指摘 Medium: `git push --dry-run` は実際に remote を
        更新しない。`gh` を呼んではならない。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push --dry-run origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists())

    def test_delete_push_does_not_invoke_gh(self) -> None:
        """人間レビュー指摘 Medium: `git push --delete` は削除対象と無関係な
        branch の PR 有無で誤判定しうる（既存の delete-push フォールバック
        限界と同種）。`gh` を呼ばず抜ける。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push --delete origin old-branch",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists())

    def test_finds_real_push_after_earlier_echo_false_match(self) -> None:
        """`echo git push foo && git push origin bar` のように、過検出源の後に
        本物の command-start push が続く場合は見逃してはならない。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            result = self._run_hook(
                repo,
                "echo git push foo && git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("additionalContext", result.stdout)

    def test_dry_run_then_real_push_still_injects(self) -> None:
        """独立レビュー round 4 指摘 Medium: 除外対象（--dry-run）の
        command-start push が先にあり、その後に本物の push が続く形
        （`git push --dry-run origin main && git push origin main`）では、
        1 つ目の一致だけで諦めると 2 つ目の本物の push を見逃す。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push --dry-run origin feature-x && git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("additionalContext", result.stdout)
            self.assertTrue(counter.exists(), "2つ目の本物の push で gh が呼ばれるはず")

    def test_dash_prefixed_branch_is_not_parsed_as_gh_flag(self) -> None:
        """PR #88 人間レビュー round 5 指摘 High: 先頭が `-` の branch 名は
        全桁数字と違って弾いていなかった。`"$BRANCH"` を素のまま渡すと、
        `--repo=attacker/repo` のような branch 名（hostile clone の HEAD が
        この ref 名を指す形）が `gh` 自身のグローバル flag として解釈され、
        認証付き問い合わせの宛先を push 対象 repo の作者が選べてしまう。
        `git branch`/`checkout -b` は check-ref-format でこの名前を拒否する
        が、`update-ref` + `symbolic-ref` で低レベルに作れば実 git でも
        `rev-parse --abbrev-ref HEAD` はこの名前をそのまま返す（実測確認
        済み）。hostile clone の HEAD がまさにこの形を取りうる。明示
        refspec 無しの push（実 branch 名は `git -C "$ROOT" rev-parse
        --abbrev-ref HEAD` から解決される）で、`--` を挟んで常に literal な
        branch 名として渡ることを、stub が受け取った最後の引数で固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            dash_branch = "--repo=attacker/repo"
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
            subprocess.run(
                ["git", "update-ref", f"refs/heads/{dash_branch}", sha],
                cwd=repo, check=True,
            )
            subprocess.run(
                ["git", "symbolic-ref", "HEAD", f"refs/heads/{dash_branch}"],
                cwd=repo, check=True,
            )
            gh_stub = Path(tmp) / "gh-stub.sh"
            args_file = Path(tmp) / "args.log"
            _write_stub_gh(gh_stub, behavior="no-pr", args_file=args_file)
            result = self._run_hook(
                repo,
                "git push origin",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(args_file.exists(), "gh は呼ばれ、branch は literal として渡るはず")
            self.assertEqual(
                args_file.read_text(encoding="utf-8").strip(),
                dash_branch,
                "branch 名が gh の flag として解釈され、素の値のまま渡っていない",
            )

    def test_brace_group_cd_resolves_correct_root(self) -> None:
        """PR #88 人間レビュー round 5 指摘 Medium: push 検出は `{` を
        command-start に含めているのに cd 解決が既定の狭い集合のままだと、
        `{ cd <other-repo>; git push; }` が誤った root（payload/process
        cwd）を候補にし、無関係な repo の PR 有無で `gh` を呼んでしまう。
        `_hash8(other_repo)` を鍵にした cache ファイルができることで、正しい
        root が解決されたことを固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            other_repo = Path(tmp) / "other-repo"
            other_repo.mkdir()
            self._init_repo(other_repo, branch="other-branch")
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                f"{{ cd {other_repo}; git push origin feature-x; }}",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("additionalContext", result.stdout)
            cache_dir = state_dir / "review-followup-pr-cache"
            # ROOT は `cd` の引数（コマンド文字列中の生の token）をそのまま使う
            # ため、`_hash8` の入力も symlink 解決前の literal path で揃える
            # （payload cwd 側の PROCESS_CWD は起動時に `pwd` で解決済みの
            # 実パスになるのと非対称だが、ここでは `cd` 経路の検証が目的）。
            expected_key = f"{_hash8(str(other_repo))}__{_hash8('feature-x')}"
            self.assertTrue(
                (cache_dir / expected_key).exists(),
                "cache key が other-repo ではなく repo/payload cwd で作られている（root 誤解決）",
            )


if __name__ == "__main__":
    unittest.main()
