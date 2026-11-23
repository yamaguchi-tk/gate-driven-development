"""root branch guard の中核契約（active state 判定・worktree add・global flag）。

state の持ち主の session の照合（payload の session_id と環境変数 CLAUDE_CODE_SESSION_ID）と、
読めない state で止めることは `test_root_branch_guard_session_owner.py` にある。この file の payload は
session_id を持たないので、state による deny は照合せずに `active: true` の有無で決まる。

分割の経緯と共有 fixture は `tests/_root_branch_guard_support.py` を参照。
名前候補抽出は `test_root_branch_name_candidates.py`、segmentation は
`test_root_branch_guard_segmentation.py`、deny corpus 非回帰は
`test_root_branch_deny_corpus.py`、parser 不在時の fail-closed は
`test_root_branch_guard_fail_closed.py`、実 git oracle は
`test_root_branch_guard_real_git.py` にある。
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import (
    GUARD_HOOK_TIMEOUT_SEC,
    RootBranchGuardFixtureMixin,
)
from _timing_budget import TimingBudget, timing_budget

#: suffix 剥がしの CPU 時間予算（秒）。旧 O(N^2) 実装なら確実に超える値。
PEELING_CPU_BUDGET_SEC = 3.0


class RootBranchGuardContractTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    def test_hook_blocks_root_branch_creation_during_active_gdd(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git switch -c codex/20260611-root-branch",
                "git checkout -b codex/20260611-root-branch",
                "git branch codex/20260611-root-branch",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
                    self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_blocks_dated_codex_task_branch_even_without_root_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_guard(
                repo,
                "git switch -c codex/20260610-example-detection-task",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_allows_worktree_add_branch_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(
                repo,
                "git worktree add /tmp/example-gdd-worktree -b codex/20260611-root-branch origin/main",
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])

    def test_hook_allows_worktree_add_from_recorded_base_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(
                repo,
                f"git worktree add /tmp/example-gdd-worktree -b codex/20260611-root-branch {self._head(repo)}",
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])

    def test_hook_blocks_gdd_worktree_creation_from_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_guard(
                repo,
                "git worktree add /tmp/example-gdd-worktree -b codex/20260611-example-report-task HEAD",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Blocked GDD worktree creation from HEAD", payload["systemMessage"])
            self.assertIn("origin/<default-branch>", payload["systemMessage"])

    def test_hook_blocks_gdd_worktree_creation_from_head_with_case_folded_branch_prefix(self):
        # 独立発見: `GDD_TASK_BRANCH_RE` は `re.IGNORECASE` を持たず、
        # `looks_like_gdd_task_branch` が `Codex/`/`GDD/`/`Claude/`/`Cursor/`
        # のように先頭が大文字始まりのブランチ名で False を返すため、
        # `_worktree_creates_gdd_branch` の入り口ゲートごと HEAD worktree
        # 作成ガードを bypass できていた。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for prefix in ["Codex", "GDD", "Claude", "Cursor", "CODEX"]:
                with self.subTest(prefix=prefix):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b {prefix}/20260906-case-fold HEAD",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD worktree creation from HEAD",
                        payload["systemMessage"],
                    )

    def test_hook_blocks_dated_task_branch_case_folded_prefix_even_without_root_state(self):
        # 同じ `re.IGNORECASE` 欠落は root branch（非 worktree）経路の
        # `_creates_gdd_named_branch` にも波及し、active state が無い
        # dated task branch 判定（`test_hook_blocks_dated_codex_task_branch_even_without_root_state`
        # の大文字小文字違いバリエーション）も bypass できていた。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for prefix in ["Codex", "GDD", "Claude", "Cursor", "CODEX"]:
                with self.subTest(prefix=prefix):
                    result = self._run_guard(
                        repo,
                        f"git switch -c {prefix}/20260906-case-fold",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_gdd_worktree_creation_from_local_default_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for base in ["main", "master", "develop"]:
                with self.subTest(base=base):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/example-gdd-worktree -b codex/20260611-root-branch {base}",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
                    self.assertIn("Blocked GDD worktree creation from a local default branch", payload["systemMessage"])
                    self.assertIn("origin/<default-branch>", payload["systemMessage"])

    def test_hook_blocks_gdd_worktree_creation_from_local_default_branch_with_case_folded_branch_prefix(self):
        # `_worktree_creates_gdd_branch` の入り口ゲートは HEAD 経路 / local-default
        # 経路の双方から共有される。同ゲート依存の case-fold 回帰
        # （`test_hook_blocks_gdd_worktree_creation_from_head_with_case_folded_branch_prefix`）
        # は HEAD 経路のみを固定しており、local-default 経路が将来分岐しても
        # 検出できない gap があったため、同型の回帰をこちらにも固定する
        # （独立セルフレビュー指摘、test-coverage）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for prefix in ["Codex", "GDD", "Claude", "Cursor", "CODEX"]:
                with self.subTest(prefix=prefix):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b {prefix}/20260906-case-fold main",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD worktree creation from a local default branch",
                        payload["systemMessage"],
                    )

    def test_hook_blocks_gdd_worktree_creation_from_head_revision_aliases(self):
        # 独立実装レビュー指摘（PR #34 merge 後）: `command_creates_gdd_worktree_from_head`
        # は base-ref の文字列リテラル一致（"HEAD"）のみで判定しており、`@`/
        # `HEAD~0`/`HEAD^0`/`@{0}` のような HEAD の別名 revision は positionals に
        # そのまま残るため `"HEAD" in positionals` に掛からず、かつ 2 個目の
        # positional として明示されているため `len(positionals) <= 1` にも掛から
        # ず bypass していた（実 git は全て HEAD と同一コミットに解決する。
        # 実測確認済み: git 2.50.1）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for alias in ["@", "HEAD~0", "HEAD^0", "@{0}"]:
                with self.subTest(alias=alias):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b codex/20260906-h {alias}",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD worktree creation from HEAD",
                        payload["systemMessage"],
                    )

    def test_hook_blocks_gdd_worktree_creation_from_local_default_branch_aliases(self):
        # 独立実装レビュー指摘（PR #34 merge 後）: `command_creates_gdd_worktree_from_local_default`
        # も同様に `{"main", "master", "develop"}` との文字列リテラル一致のみで、
        # `refs/heads/main`/`heads/main`/`main@{0}` のような別名 revision は
        # positionals に別の文字列として残るため判定をすり抜けていた（実測確認済み:
        # git 2.50.1、いずれも local main と同一コミットに解決する）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for alias in ["refs/heads/main", "heads/main", "main@{0}"]:
                with self.subTest(alias=alias):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b codex/20260906-l {alias}",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD worktree creation from a local default branch",
                        payload["systemMessage"],
                    )

    def test_hook_blocks_gdd_worktree_creation_from_case_folded_head_alias(self):
        # 独立発見（本 CHANGELOG エントリ前から存在する pre-existing gap）:
        # `_HEAD_REVISION_ALIASES` は `{"HEAD", "@"}` との大文字小文字を区別する
        # 文字列一致で判定しているが、macOS の既定 APFS（大文字小文字を区別しない
        # 設定が既定）や Windows の既定 NTFS 上では git 自身のファイルベースの ref
        # 解決が OS の case-folding の影響を受け、`head`（小文字）でも実際には
        # HEAD と同一コミットに解決してしまう。実測確認済み: git 2.50.1、macOS
        # APFS。`.git/HEAD` は常に loose file のため `git gc` で packed-refs に
        # 固めた後も再現する恒久的な bypass。case-insensitive でない CI
        # （Linux ext4 等）では再現しないため `core.ignorecase` で skip する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            if not self._repo_ignorecase(repo):
                self.skipTest(
                    "test environment filesystem does not fold case "
                    "(core.ignorecase != true)"
                )

            result = self._run_guard(
                repo,
                "git worktree add /tmp/w -b codex/20260906-case head",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from HEAD",
                payload["systemMessage"],
            )

    def test_hook_blocks_gdd_worktree_creation_from_case_folded_local_default_branch_alias(self):
        # 独立発見（本 CHANGELOG エントリ前から存在する pre-existing gap）:
        # `_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES` も同様に大文字小文字を区別する
        # 文字列一致のみで判定している。`git init -b main` の初回 commit 直後のように
        # main が loose ref のままなら `MAIN`（大文字）は HEAD/local main と同一コミットに
        # 解決する（実測確認済み: git 2.50.1、macOS APFS）。`git gc` で packed-refs
        # に固められた後は解決に失敗する（rc=1）ため、この alias は一時的にのみ
        # 有効な bypass だが、`_init_repo` 直後（`git init -b main` の初回 commit
        # 直後）は loose ref の状態にある。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            if not self._repo_ignorecase(repo):
                self.skipTest(
                    "test environment filesystem does not fold case "
                    "(core.ignorecase != true)"
                )

            result = self._run_guard(
                repo,
                "git worktree add /tmp/w -b codex/20260906-case MAIN",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from a local default branch",
                payload["systemMessage"],
            )

    def test_hook_normalizes_non_lowercase_core_ignorecase_config_value(self):
        # 独立セルフレビュー指摘（実測確認済み: git 2.50.1）: `git config --get
        # core.ignorecase` はリポジトリ設定ファイルに書かれた値をそのまま返し、
        # git の boolean 正規化を経由しない。`git config core.ignorecase True`
        # （大文字 T、`git` 自身は boolean true として受理する表記）を設定した
        # リポジトリで `git config --get core.ignorecase` を実行すると `"True"`
        # （大文字のまま）が返り、`== "true"`（小文字リテラル一致）の判定では
        # false と誤認される。`git config --type=bool --get core.ignorecase` を
        # 使えば `"true"`（正規化済み小文字）を返すことを実測確認済み。
        #
        # このテストは `core.ignorecase` を明示的に上書きするため、実行環境の
        # 実際のファイルシステムが大文字小文字を区別するかどうかに依存せず
        # （`_repo_ignorecase` による skip 不要）、case-sensitive な CI
        # （Linux ext4 等）でも常に実行される。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            subprocess.run(
                ["git", "config", "core.ignorecase", "True"],
                cwd=repo,
                check=True,
            )

            result = self._run_guard(
                repo,
                "git worktree add /tmp/w -b codex/20260906-normalize head",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from HEAD",
                payload["systemMessage"],
            )

    def test_hook_blocks_gdd_worktree_creation_from_chained_noop_suffix_revisions(self):
        # 独立セルフレビュー指摘（PR #40 merge 後）: 有限集合との文字列一致は
        # chained no-op suffix（`~0~0`/`^{}`/`~0` の連鎖）を無限に生成できる
        # git revision 構文を塞ぎきれない。実測確認済み: git 2.50.1、
        # `git rev-parse HEAD` / `git rev-parse 'HEAD~0~0'` / `git rev-parse
        # 'HEAD^{}'` はいずれも同一 SHA に解決し、`git worktree add <path> -b
        # <name> 'HEAD~0~0'`（`'HEAD^{}'` も同様）は実際に成功して HEAD と
        # 同一コミットへ checkout する。`main~0` も `git rev-parse main` と
        # 同一 SHA に解決し、`git worktree add <path> -b <name> main~0` も
        # 同様に成功するが、いずれの alias も `_HEAD_REVISION_ALIASES` /
        # `_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES` の有限集合に含まれないため
        # guard は allow (rc=0) を返してしまう。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for alias, expected_message in [
                ("HEAD~0~0", "Blocked GDD worktree creation from HEAD"),
                ("HEAD^{}", "Blocked GDD worktree creation from HEAD"),
                (
                    "main~0",
                    "Blocked GDD worktree creation from a local default branch",
                ),
            ]:
                with self.subTest(alias=alias):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b codex/20260906-chain {alias}",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(expected_message, payload["systemMessage"])

    def test_hook_blocks_gdd_worktree_creation_from_generalized_noop_suffix_forms(self):
        # 独立セルフレビュー Round 2 指摘（altitude 角度 + line-by-line 角度、
        # PR #40 merge 後の `_peel_noop_revision_suffixes` 導入直後に独立発見）:
        # `_NOOP_REVISION_SUFFIX_RE` は `~0`/`^0`/`@{0}` の桁を厳密に 1 文字の
        # `0` のみに固定していたため、git が実際にパースする「0 のみからなる
        # 任意桁の数値」（`~00`/`~000`/`^00`/`@{00}`）をすり抜けていた。また
        # `^{}`（空 brace の再帰的 dereference）のみを no-op として認識しており、
        # `^{commit}`/`^{object}`（commit に対しては no-op、`^{tree}`/`^{tag}`
        # は別オブジェクトになるため対象外）という type-peel 構文の変種を
        # 見落としていた。実測確認済み: git 2.50.1、`git rev-parse HEAD` /
        # `git rev-parse 'HEAD~00'` / `git rev-parse 'HEAD^{commit}'` はいずれも
        # 同一 SHA に解決し、`git worktree add <path> -b <name> 'HEAD~00'`
        # （`'HEAD^{commit}'`/`'main~00'` も同様）は実際に成功して HEAD/local
        # main と同一コミットへ checkout する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for alias, expected_message in [
                ("HEAD~00", "Blocked GDD worktree creation from HEAD"),
                ("HEAD^00", "Blocked GDD worktree creation from HEAD"),
                ("HEAD@{00}", "Blocked GDD worktree creation from HEAD"),
                (
                    "HEAD^{commit}",
                    "Blocked GDD worktree creation from HEAD",
                ),
                (
                    "HEAD^{object}",
                    "Blocked GDD worktree creation from HEAD",
                ),
                (
                    "main~00",
                    "Blocked GDD worktree creation from a local default branch",
                ),
                (
                    "main^{commit}",
                    "Blocked GDD worktree creation from a local default branch",
                ),
            ]:
                with self.subTest(alias=alias):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b codex/20260906-gen {alias}",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(expected_message, payload["systemMessage"])

    def _assert_peeling_within_budget(
        self, timing: TimingBudget, expectation: str
    ) -> None:
        """suffix 剥がしの所要時間が CPU 予算と壁時計 backstop に収まることを検証する。

        なぜ CPU 時間（厳）と壁時計（緩）の二本立てにするか: CPU 時間は
        二次計算量の退行を CPU 律速のまま検出でき（現状閾値を据え置ける）、
        壁時計 backstop は hook timeout 予算の逸脱という別の性質を守る。
        1 本の壁時計だけで両方を担うのが並列負荷下の flaky の構造的原因
        だった（ADR-1）。
        """
        self.assertLess(
            timing.cpu_seconds,
            PEELING_CPU_BUDGET_SEC,
            msg=(
                f"peeling took {timing.cpu_seconds:.2f}s CPU "
                f"(wall {timing.wall_seconds:.2f}s), expected {expectation}"
            ),
        )
        self.assertLess(
            timing.wall_seconds,
            GUARD_HOOK_TIMEOUT_SEC / 2,
            msg=(
                f"peeling took {timing.wall_seconds:.2f}s wall "
                f"(CPU {timing.cpu_seconds:.2f}s), expected well under hook timeout"
            ),
        )

    def test_hook_peels_adversarial_noop_suffix_chain_without_quadratic_slowdown(self):
        # 独立セルフレビュー Round 2 指摘（efficiency 角度 + line-by-line 角度、
        # 2 名の独立エージェントが同一の O(N^2) を実測確認）: 修正前の
        # `_peel_noop_revision_suffixes` は `while True: ... .search(token)`
        # で毎回先頭から再スキャンする実装だったため、`~0` を連鎖させた
        # adversarial token で反復回数 x 各回のスキャン長が O(N^2) になり、
        # このガードは Bash/Shell コマンドごとに同期実行される PreToolUse hook
        # であるにも関わらず、入力が長いと hook の timeout を大きく超えるハングを
        # 引き起こしていた（入力長を変えて測ると、N を 2 倍にすると所要時間が
        # 約 4 倍になり N^2 スケーリングと一致した）。
        # 1 回の正規表現 substitution（`+` 量化子で一括マッチ）に置き換えた
        # 修正後は同じ入力がすぐに完了する。CI 実行環境のばらつきを
        # 考慮し、閾値は生成コストの 1 桁以上小さい 3 秒に設定した
        # （旧実装はこの長さの入力でこの閾値を確実に超える）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            # 入力長 2 倍（AC-8）: 旧実装の記録（入力を 2 倍にすると所要時間が
            # 約 4 倍）から、50000 反復（100004 文字相当）は退行時に閾値 3.0 秒を
            # 大きく超える見込みで、検出の余裕が十分にある。
            adversarial_suffix = "~0" * 50000
            command = (
                "git worktree add /tmp/w -b codex/20260906-dos "
                f"HEAD{adversarial_suffix}"
            )
            with timing_budget() as timing:
                result = self._run_guard(repo, command)

            self._assert_peeling_within_budget(
                timing, "O(N) single-pass regex"
            )
            self.assertEqual(result.returncode, 2)

    def test_hook_peels_adversarial_noop_suffix_chain_ending_in_excluded_keyword_without_quadratic_slowdown(
        self,
    ):
        # 独立レビュー指摘（`@{upstream}` 大文字小文字バグ修正のセルフレビュー中に
        # 追加発見）: `_NOOP_REVISION_SUFFIX_CHAIN_RE`（`atom+\Z`、無アンカー）は、
        # chain の**末尾**が否定先読みで除外される atom（`@{upstream}`/`@{u}`/
        # `@{push}`、大文字小文字を問わず）で終わる token に対して、`\Z` に到達
        # できるマッチが存在しないため、正規表現エンジンが全開始位置から
        # バックトラックを行い O(N^2) になる。これは前回の独立レビューが
        # 「1 回の re.sub で O(N) に修正した」と主張していた対象そのものの
        # 再発である（修正前の case-sensitive な旧パターンでも `@{u}`/
        # `@{upstream}`/`@{push}`（小文字）終端の chain で同じ O(N^2) が既に
        # 存在しており、今回の case-insensitive 化はその引き金になる文字列
        # パターンを広げただけで新規に持ち込んだわけではないが、既存の perf
        # regression test（直前のテスト）は全要素が chain にマッチしきる
        # `~0` のみの入力しか検証しておらず、この失敗モードを検出できない）。
        # 手動パーサー化前の実装で `"HEAD" + "@{0}" * 8000 + "@{U}"` と
        # `"@{0}" * 16000 + "@{U}"` を測ると、どちらも数秒以上かかり、
        # N を 2 倍で時間が約 4 倍になって O(N^2) と一致した。
        # `_peel_noop_revision_suffixes` を正規表現の一括 `re.sub` から、
        # suffix 種別ごとに文字列末尾からの直接インデックス走査で 1 個ずつ
        # 判定する手動パーサーに置き換えることで、剥がす（または剥がせないと
        # 判定する）suffix の長さに比例したコストのみで完了するようにした。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            # 入力長 2 倍（AC-8）: 上の記録（入力を 2 倍にすると所要時間が約 4 倍）
            # から、16000 反復（64,008 文字相当）は退行時に閾値 3.0 秒を大きく
            # 超える見込みで、検出の余裕が十分にある。
            adversarial_suffix = "@{0}" * 16000 + "@{U}"
            command = (
                "git worktree add /tmp/w -b codex/20260906-dos2 "
                f"HEAD{adversarial_suffix}"
            )
            with timing_budget() as timing:
                result = self._run_guard(repo, command)

            self._assert_peeling_within_budget(
                timing, "O(N) suffix-by-suffix peeling"
            )
            # chain の末尾が `@{U}`（upstream の別名、除外対象）で終わるため
            # chain 全体は no-op に還元されず、HEAD の別名としては認識され
            # ない = ブロックされない。
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])

    def test_hook_blocks_gdd_worktree_creation_from_reflog_date_specifiers(self):
        # 独立セルフレビュー Round 3 指摘（マージ前の追加独立検証で発見）:
        # `_NOOP_REVISION_SUFFIX_ATOM` の `@{0+}` は数字のみからなる reflog
        # index を想定していたが、git の `@{<n>}` 構文は日付・相対時刻表現
        # （`@{now}`/`@{yesterday}`/`@{1.second.ago}` 等の approxidate、
        # gitrevisions(7) 参照）も受理し、reflog が変化していなければ
        # 現在値と同一コミットに解決する。実測確認済み: git 2.50.1、
        # `git rev-parse '@{now}'` / `'HEAD@{now}'` / `'main@{now}'` は
        # いずれも HEAD/local main と同一 SHA に解決し、
        # `git worktree add <path> -b <name> '@{now}'` は実際に成功して
        # HEAD と同一コミットへ checkout する。数字のみに限定した
        # `@\{0+\}` はこれらの日付形をすり抜ける。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for alias, expected_message in [
                ("@{now}", "Blocked GDD worktree creation from HEAD"),
                ("HEAD@{now}", "Blocked GDD worktree creation from HEAD"),
                (
                    "main@{now}",
                    "Blocked GDD worktree creation from a local default branch",
                ),
                (
                    "main@{yesterday}",
                    "Blocked GDD worktree creation from a local default branch",
                ),
            ]:
                with self.subTest(alias=alias):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b codex/20260906-reflog {alias}",
                    )
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(expected_message, payload["systemMessage"])

    def test_hook_allows_gdd_worktree_creation_from_upstream_alias_case_insensitively(self):
        # 独立レビュー指摘（マージ後の追加独立検証で発見）: `_NOOP_REVISION_SUFFIX_ATOM`
        # の `@\{(?!upstream\}|u\}|push\})[^{}]*\}` は `@{upstream}`/`@{u}`/
        # `@{push}` を no-op 剥離対象から除外する否定先読みだが、この先読みは
        # 大文字小文字を区別していた。一方 git 自身は `@{...}` のキーワード
        # マッチを大文字小文字を区別せずに行う。実測確認済み: git 2.50.1、
        # `git rev-parse 'main@{upstream}'` / `'main@{UPSTREAM}'` /
        # `'main@{U}'` / `'main@{Upstream}'` はいずれも同一の upstream 側
        # コミット（local `main` とは別コミットになりうる）に解決し、
        # `git worktree add <path> -b <name> 'main@{UPSTREAM}'` は実際に成功して
        # upstream 側のコミットへ checkout する。したがって
        # `main@{UPSTREAM}` のような大文字小文字違いは `main` の別名では
        # なく、修正前は否定先読みが `UPSTREAM`（大文字）にマッチせず除外に
        # 失敗するため、no-op suffix として誤って剥がされ `main` に正規化
        # されてしまい、local default branch 由来として誤って deny されて
        # いた（false positive）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for alias in [
                "main@{upstream}",
                "main@{UPSTREAM}",
                "main@{Upstream}",
                "main@{u}",
                "main@{U}",
                "main@{push}",
                "main@{PUSH}",
            ]:
                with self.subTest(alias=alias):
                    result = self._run_guard(
                        repo,
                        f"git worktree add /tmp/w -b codex/20260906-upstream {alias}",
                    )
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_blocks_root_branch_creation_with_global_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            commands = [
                "git -c core.hooksPath=/dev/null switch -c codex/20260903-a",
                "git --git-dir=/tmp/gddprobe/.git switch -c codex/20260903-b",
                "git -c a=b -C /tmp/gddprobe checkout -b codex/20260903-c",
                "git --no-pager branch codex/20260903-d",
                "git -C /tmp/gddprobe switch -c codex/20260903-e",
                "git --work-tree=/tmp/w switch -c codex/20260903-f",
                "git --namespace=ns switch -c codex/20260903-g",
                "git --bare switch -c codex/20260903-h",
                "git switch --create codex/20260903-i",
                "git switch --force-create codex/20260903-j",
                "git switch --create=codex/20260903-k",
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_root_branch_creation_with_remaining_global_flags(self):
        # AC-1 / AC-9: 16 種の global flag のうち上のテストで未カバーの 10 種を
        # 個別 subTest 化する（Implementation Medium-2 remediation）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            commands = [
                "git --git-dir /tmp/gddprobe/.git switch -c codex/20260903-a",
                "git --config-env=core.hooksPath=/dev/null switch -c codex/20260903-b",
                "git --attr-source=refs/heads/main switch -c codex/20260903-c",
                "git --shallow-file=/tmp/gddprobe.shallow switch -c codex/20260903-d",
                "git -p switch -c codex/20260903-e",
                "git --paginate switch -c codex/20260903-f",
                "git -P switch -c codex/20260903-g",
                "git --no-optional-locks switch -c codex/20260903-h",
                "git --no-replace-objects switch -c codex/20260903-i",
                "git --literal-pathspecs switch -c codex/20260903-j",
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_blocks_root_branch_creation_with_upper_case_create_flags(self):
        # AC-1 / AC-9: `switch -C` / `checkout -B` の個別ケース（M3/M2 と同型）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git switch -C codex/20260903-a",
                "git checkout -B codex/20260903-b",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD root branch creation", payload["systemMessage"]
                    )

    def test_hook_allows_branch_creation_in_linked_worktree(self):
        # AC-6(c) / AC-9: linked worktree 内での branch 作成は allow のまま。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)
            linked = Path(tmp) / "linked-worktree"
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-q",
                    str(linked),
                    "-b",
                    "codex/20260903-linked-setup",
                    "main",
                ],
                cwd=repo,
                check=True,
            )

            result = self._run_guard(linked, "git switch -c codex/20260903-inner")
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])

    def test_hook_allows_non_gdd_branch_creation_without_active_state(self):
        # AC-6(d) / AC-9: active state なし かつ 非 GDD 名の branch 作成は allow。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for command in [
                "git switch -c feature-x",
                "git checkout -b feature-x",
                "git branch feature-x",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)
                    payload = json.loads(result.stdout.strip())
                    self.assertTrue(payload["continue"])

    def test_hook_survives_creation_flag_mutations(self):
        # Implementation Medium-3: mutation-surviving ケース（M8-M12, M16）を固定する。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            deny_commands = [
                # M8: worktree add の短 option 結合形（`-bcodex/...`）から名前抽出
                "git worktree add /tmp/w -bcodex/20260903-a HEAD",
                # M10: branch の copy / force による作成（旧 ADR-6 条件3。R2 で saw_creating による site 収集へ移行。20260906-branch-guard-unknown-flag 参照）
                "git branch -c old codex/20260903-b",
                "git branch -f codex/20260903-c",
                # M11: root branch 判定側は先頭 token に限定せず全走査する
                "sudo git switch -c codex/20260903-d",
                "env FOO=1 git switch -c codex/20260903-e",
            ]
            for command in deny_commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)

            allow_commands = [
                # M9: 削除操作は creating flag 併記でも non-creating が優先（旧 ADR-6 条件1。R2 で saw_unconditional_veto による無条件 veto へ移行。20260906-branch-guard-unknown-flag 参照）
                "git branch -d -f old-branch",
            ]
            for command in allow_commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            # M12: worktree-from-head 判定側も先頭 token に限定せず全走査する
            for command in [
                "sudo git worktree add /tmp/w -b codex/20260903-f HEAD",
                "env FOO=1 git worktree add /tmp/w -b codex/20260903-g HEAD",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD worktree creation from HEAD",
                        payload["systemMessage"],
                    )

            # M16: GDD task branch 名でない通常の branch 名は allow のまま
            # （`looks_like_gdd_task_branch` フィルタの回帰ガード）
            result = self._run_guard(
                repo, "git worktree add /tmp/w -b feature-x HEAD"
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])

    def test_hook_blocks_worktree_add_short_option_cluster_branch_name(self):
        # completion_check.md M-1 remediation: switch/checkout 側の
        # `_segment_creates_switch` / `_segment_creates_checkout` は
        # `_short_cluster_has` で `-f` 等と結合した短 option cluster 形を
        # 正しく扱うが、worktree add の名前抽出側（`_worktree_positionals_and_names`）
        # は `-b`/`-B` 単独形・値結合形のみ対応で cluster 形（`-fb<name>` /
        # `-fb <name>`）を見落としていた（deny すべきが allow されていた）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            # HEAD からの worktree 作成: cluster 形（分離形・値結合形の両方）で deny
            head_deny_commands = [
                "git worktree add /tmp/w -fb codex/20260904-y HEAD",
                "git worktree add /tmp/w -fbcodex/20260904-z HEAD",
            ]
            for command in head_deny_commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertEqual(
                        payload["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(
                        "Blocked GDD worktree creation from HEAD",
                        payload["systemMessage"],
                    )

            # base 省略（implicit HEAD, AC-2 Q-c）でも cluster 形で deny される
            result = self._run_guard(repo, "git worktree add /tmp/w -fb codex/20260904-bb")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from HEAD", payload["systemMessage"]
            )

            # local default branch (main) からの worktree 作成も cluster 形で deny
            result = self._run_guard(
                repo, "git worktree add /tmp/w -fb codex/20260904-cc main"
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from a local default branch",
                payload["systemMessage"],
            )

            # 非 GDD branch 名は cluster 形でも allow のまま
            # （`looks_like_gdd_task_branch` フィルタの回帰ガード）
            result = self._run_guard(repo, "git worktree add /tmp/w -fb feature-x HEAD")
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout.strip())
            self.assertTrue(payload["continue"])

    def test_hook_blocks_unknown_global_flag_fail_closed(self):
        # AC-5: 未知 global option は fail-closed
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for command in [
                "git --future-flag switch -c codex/20260903-x",
                "git --future-flag=v switch -c codex/20260903-y",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)

    def test_hook_blocks_worktree_from_head_with_global_options_and_b_upper(self):
        # AC-2 拡張（Q-a: -B も対象）+ global option 前置
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            commands = [
                "git -c a=b worktree add /tmp/w -b codex/20260903-a HEAD",
                "git -C /tmp/gddprobe worktree add /tmp/w -b codex/20260903-b HEAD",
                "git worktree add /tmp/w -B codex/20260903-c HEAD",
                "git worktree add /tmp/w -b codex/20260903-d 2>&1",  # AC-2 implicit HEAD + redirect
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD worktree creation from HEAD",
                        payload["systemMessage"],
                    )

    def test_hook_blocks_worktree_add_b_value_extraction_across_redirection(self):
        # 独立実装レビュー指摘（PR #34 merge 後）: `_worktree_positionals_and_names`
        # は switch/checkout/branch 側で使う `_skip_redirection` / `_take_flag_value`
        # を再利用せず、`-b` の値抽出・fd 判定を自前の簡易実装（`token.isdigit()` の
        # みで named fd `{name}` 非対応、`-b` の分離値は redirection を読み飛ばさず
        # 次 token を無条件取得）のままにしていた。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            # (1) `-b` の分離値が redirection operator 自体になり候補が壊れる形。
            # 実 shell では `>/dev/null` はリダイレクトとして消費され、git の argv は
            # `-b codex/20260906-x`（start-point 省略 = implicit HEAD）になる。
            result = self._run_guard(
                repo,
                "git worktree add /tmp/w -b >/dev/null codex/20260906-x",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from HEAD", payload["systemMessage"]
            )

            # (2) bash 4.1+ / zsh の named fd（`{name}>...`）が positional に混入し
            # `len(positionals) <= 1` が崩れる形。
            result = self._run_guard(
                repo,
                "git worktree add /tmp/w -b codex/20260906-y {fd}>/dev/null",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn(
                "Blocked GDD worktree creation from HEAD", payload["systemMessage"]
            )

    def test_hook_blocks_worktree_from_local_default_with_global_options(self):
        # AC-3 拡張 + global option 前置
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            for base in ["main", "master", "develop"]:
                command = f"git -c a=b worktree add /tmp/w -b codex/20260903-x {base}"
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2)
                    payload = json.loads(result.stderr.strip())
                    self.assertIn(
                        "Blocked GDD worktree creation from a local default branch",
                        payload["systemMessage"],
                    )

    def test_hook_allows_worktree_regression_cases(self):
        # AC-6(a)(b): 既存 allow ケースの回帰
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)
            head_sha = self._head(repo)

            for command in [
                "git worktree add /tmp/w -b codex/20260903-a origin/main",
                f"git worktree add /tmp/w -b codex/20260903-b {head_sha}",
            ]:
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 0)

    def test_hook_blocks_non_gdd_name_with_active_state(self):
        # AC-6: active state 有りの deny は branch 名に依存しない（従来どおり deny）。
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_guard(repo, "git switch -c feature-x")
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr.strip())
            self.assertIn("Blocked GDD root branch creation", payload["systemMessage"])

    def test_hook_tolerates_non_utf8_state_file(self):
        # R2-1（impl-gate Round 2）: `.claude/gdd-dev.local.md` が非 UTF-8 でも
        # `root_state_blocks` は例外を送出せず、判定は `active: true` の
        # 有無だけで決まる（payload に session_id が無いので、持ち主は照合しない）。
        #
        # 退行検出の要は allow 側（case 1）: 厳格 decode（`errors="replace"`
        # 無し）だと `UnicodeDecodeError`（`OSError` ではなく `ValueError` 系）
        # が `main()` の try に落ちて emit_deny になり、良性コマンドが真因
        # （state ファイル破損）と無関係な「worktree を先に作れ」deny を受ける。
        # deny 側（case 2）は AC-6 の保持を固定する: 破損が `active: true` 以外
        # の箇所にあれば保護は失われない。`except UnicodeDecodeError: return
        # False` のような代替実装では case 2 が allow に倒れて fail-open になる。
        cases = [
            (b"---\nnote: \xff\xfe\n---\n", 0),
            (b"---\nactive: true\nnote: \xff\xfe\n---\n", 2),
        ]
        for state_bytes, expected_rc in cases:
            with self.subTest(state_bytes=state_bytes, expected_rc=expected_rc):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    self._init_repo(repo)
                    state_dir = repo / ".claude"
                    state_dir.mkdir()
                    (state_dir / "gdd-dev.local.md").write_bytes(state_bytes)

                    result = self._run_guard(repo, "git switch -c feature-x")
                    self.assertEqual(result.returncode, expected_rc)
                    if expected_rc == 0:
                        payload = json.loads(result.stdout.strip())
                        self.assertTrue(payload["continue"])
                    else:
                        payload = json.loads(result.stderr.strip())
                        self.assertIn(
                            "Blocked GDD root branch creation", payload["systemMessage"]
                        )
