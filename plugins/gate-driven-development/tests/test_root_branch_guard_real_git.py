"""AC-12: 実 git を oracle にした allow / deny 双方向検証。

guard の判定と「実 git が実際に作る ref」を突き合わせ、allow 側で GDD 命名の ref が
できないこと・deny 側で実際に GDD 命名の ref ができることを確認する。分割の経緯と
共有 fixture は `tests/_root_branch_guard_support.py` を参照。
"""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import init_git_repo, run_root_branch_guard


GDD_TASK_BRANCH_RE_FOR_TEST = re.compile(
    r"\b(?:codex|gdd|claude|cursor)/20[0-9]{6}[A-Za-z0-9._/\-]*\b"
)


GIT_BINARY = shutil.which("git")



@unittest.skipUnless(GIT_BINARY, "git binary not available")
class RealGitOracleTests(unittest.TestCase):
    """AC-12: 実 git を oracle にした双方向の narrowing 非回帰検証。

    vacuous pass を避けるため、`git init` + 1 commit だけの repo ではなく
    start-point / copy 元を先に seed した repo で実行し、(1) コマンド自体の
    成功、(2) 実行前後の ref 集合の差分に GDD 名が現れないこと、を確認する。
    """

    def _make_base_repo(self, tmp: Path) -> Path:
        base = tmp / "base"
        base.mkdir()
        init_git_repo(base)
        return base

    def _fresh_seeded_copy(
        self, tmp: Path, base: Path, seed_branches: tuple[str, ...]
    ) -> Path:
        work = tmp / f"work-{len(list(tmp.iterdir()))}"
        shutil.copytree(base / ".git", work / ".git")
        subprocess.run(["git", "checkout", "-q", "main"], cwd=work, check=True)
        for branch in seed_branches:
            subprocess.run(["git", "branch", "-q", branch], cwd=work, check=True)
        return work

    def _refs(self, repo: Path) -> set[str]:
        result = subprocess.run(
            ["git", "for-each-ref", "refs/heads", "--format=%(refname:short)"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return set(result.stdout.split())

    def _run_shell(self, repo: Path, command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "-c", command], cwd=repo, capture_output=True, text=True, check=False
        )

    def _run_guard(self, repo: Path, command: str) -> subprocess.CompletedProcess[str]:
        return run_root_branch_guard(repo, command)

    def test_allow_side_creates_only_the_expected_new_branch(self):
        # AC-12a: 承認ポイント2の allow 行 (a)(c) + AC-1 branch 非 copy/copy +
        # R2 unconditional veto long flag 10形（creating flag併用形。
        # design.md D-3 / ADR-6）。
        # 実測（git 2.50.1）: いずれも rc=0 で、新規 ref は意図した名前のみ。
        # `--edit-description`/`--set-upstream-to`/`--unset-upstream` の3形は
        # 対象branch（`codex/20260903-old`）の事前存在をgit側が要求するため、
        # このtableのdiffベースassertion（new_refs集合）は「対象名以外のref
        # が増えないこと」のみを固定する（対象名自体の非作成はunconditional
        # veto一覧との対応で担保）。`--points-at`/`--no-contains`/
        # `--no-merged`はpattern filterで事前存在を要求しないため
        # `seeds=()` + 未使用名で「対象名も含め一切ref非作成」を直接固定する。
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base = self._make_base_repo(tmp_path)
            table = [
                (
                    ("codex/20260903-x",),
                    "git checkout -b feature-x codex/20260903-x",
                    {"feature-x"},
                ),
                (
                    (),
                    "git commit -m 'codex/20260903-x' --allow-empty && "
                    "git switch -c feature-x",
                    {"feature-x"},
                ),
                (
                    ("codex/20260903-x",),
                    "git branch feature-x codex/20260903-x",
                    {"feature-x"},
                ),
                (
                    ("codex/20260903-old",),
                    "git branch -c codex/20260903-old new-name",
                    {"new-name"},
                ),
                (
                    (),
                    "git branch --contains main -f feature-contains",
                    set(),
                ),
                (
                    (),
                    "git branch -f --list feature-list",
                    set(),
                ),
                (
                    (),
                    "git branch -f --show-current feature-show-current",
                    set(),
                ),
                (
                    (),
                    "git branch -f --merged main feature-merged",
                    set(),
                ),
                (
                    ("codex/20260903-old",),
                    "GIT_EDITOR=true git branch --edit-description -f "
                    "codex/20260903-old",
                    set(),
                ),
                (
                    ("codex/20260903-old",),
                    "git branch -f --set-upstream-to=main codex/20260903-old",
                    set(),
                ),
                (
                    ("codex/20260903-old",),
                    # --unset-upstream は upstream 設定済みの branch を要求する
                    # ため（未設定だと rc=128 "has no upstream information"、
                    # 実測: git 2.50.1）、--set-upstream-to を前提コマンドと
                    # して連鎖させる。
                    "git branch -f --set-upstream-to=main codex/20260903-old && "
                    "git branch -f --unset-upstream codex/20260903-old",
                    set(),
                ),
                (
                    (),
                    "git branch -f --points-at main codex/20260903-points",
                    set(),
                ),
                (
                    (),
                    "git branch --no-contains main -f codex/20260903-nocontains",
                    set(),
                ),
                (
                    (),
                    "git branch --no-merged main -f codex/20260903-nomerged",
                    set(),
                ),
            ]
            for seeds, command, expected_new_refs in table:
                with self.subTest(command=command):
                    work = self._fresh_seeded_copy(tmp_path, base, seeds)
                    before = self._refs(work)
                    result = self._run_shell(work, command)
                    after = self._refs(work)
                    new_refs = after - before
                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    self.assertEqual(new_refs, expected_new_refs)
                    self.assertFalse(
                        any(GDD_TASK_BRANCH_RE_FOR_TEST.search(ref) for ref in new_refs)
                    )

    def test_allow_side_origin_default_branch_matching_local_content_is_not_blocked(self):
        # 設計判断のロック: HEAD/local default branch の base-ref 判定は SHA
        # コンテンツ一致ではなく、no-op suffix を剥がした後の参照の構造的
        # 同一性（bare alias 集合との一致）で行う。フレッシュクローン直後は
        # `origin/main` と local `main` が同一コミットに解決する（実測確認済み:
        # git 2.50.1）ため、もし SHA コンテンツ一致で判定すると、このガード自身が
        # 推奨する安全な base-ref である `origin/<default-branch>`
        # （skills/gdd-using-git-worktrees/SKILL.md 参照）まで誤って deny して
        # しまう。この回帰を固定化する。
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base = self._make_base_repo(tmp_path)
            clone = tmp_path / "clone"
            subprocess.run(
                ["git", "clone", "-q", str(base), str(clone)], check=True
            )
            local_main = subprocess.run(
                ["git", "rev-parse", "main"],
                cwd=clone,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            origin_main = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                cwd=clone,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            self.assertEqual(
                local_main, origin_main, "fixture assumption: fresh clone is up to date"
            )

            result = self._run_guard(
                clone,
                "git worktree add /tmp/w -b codex/20260906-origin origin/main",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_allow_side_git_itself_rejects_pathspec_form(self):
        # AC-12a (b): `git checkout -b feature-x -- codex/...` は seed 済みでも
        # git 自身が拒否する形（実測: rc=128, fatal: 'codex/...' is not a commit）。
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base = self._make_base_repo(tmp_path)
            work = self._fresh_seeded_copy(tmp_path, base, ("codex/20260903-x",))
            before = self._refs(work)
            result = self._run_shell(
                work, "git checkout -b feature-x -- codex/20260903-x"
            )
            after = self._refs(work)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(after, before)

    def test_deny_side_when_real_git_creates_gdd_ref(self):
        # AC-12b: 実 git が GDD ref を作った場合に限り hook が deny することを
        # 条件付きで assert する（git のバージョン差で作成可否が変わる形があるため）。
        commands = [
            "git branch -f --sort committerdate codex/20260903-x",
            "git branch -f --format '%(refname)' codex/20260903-x",
            "git branch --force --sort refname codex/20260903-x",
            "git checkout -b 2>/dev/null codex/20260903-x",
            "git switch -c 2>&1 codex/20260903-x",
            "git switch -c >/dev/null 2>&1 codex/20260903-x",
            # 独立実装レビュー指摘: --color/--column/--abbrev は optional
            # argument（`=` 必須、空白区切りの次 token は値として消費しない）
            # であるため、この唯一の positional が branch 名になる
            # （実測: git 2.50.1）。--sort/--format は必須値だが、値の後ろに
            # さらに token があれば同様に branch を作成する。
            "git branch --color codex/20260903-x",
            "git branch --column codex/20260903-x",
            "git branch --abbrev codex/20260903-x",
            "git branch --sort committerdate codex/20260903-x",
            "git branch --format '%(refname)' codex/20260903-x",
            # 独立セルフレビュー指摘: --sort/--format の値 token が -d/-D/-m/-M
            # の見た目をしていても、実 git はその値として消費し（delete/move
            # 操作とは解釈しない）残りの token から branch を作成する
            # （実測: git 2.50.1）。
            "git branch --sort -d codex/20260903-x",
            "git branch --format -m codex/20260903-x",
            # 独立セルフレビュー指摘: --sort/--color の直後に `--` が続いても
            # 実 git は branch を作成する（実測: git 2.50.1）。
            "git branch --sort committerdate -- codex/20260903-x",
            "git branch --color -- codex/20260903-x",
            "git branch -v codex/20260906-x",
            "git branch -i codex/20260906-x",
            "git branch --quiet codex/20260906-x",
            "git branch --no-column codex/20260906-x",
            "git branch -tdirect codex/20260906-x",
            "git branch --no-color codex/20260906-x",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base = self._make_base_repo(tmp_path)
            verified_any_command = False
            for command in commands:
                with self.subTest(command=command):
                    probe = self._fresh_seeded_copy(tmp_path, base, ())
                    before = self._refs(probe)
                    result = self._run_shell(probe, command)
                    after = self._refs(probe)
                    new_refs = after - before
                    git_created_gdd_ref = result.returncode == 0 and any(
                        GDD_TASK_BRANCH_RE_FOR_TEST.search(ref) for ref in new_refs
                    )
                    if not git_created_gdd_ref:
                        # `skipTest()` は subTest 単位ではなくテストメソッド
                        # 全体を即終了させるため、ここで呼ぶと git 版差で
                        # 先頭コマンドが ref を作らないだけで残りのコマンドが
                        # 一切検証されない（PR #34 Copilot review 指摘
                        # Round 6）。この 1 件だけ `continue` で見送る。
                        continue

                    verified_any_command = True
                    guard_repo = self._fresh_seeded_copy(tmp_path, base, ())
                    guard_result = self._run_guard(guard_repo, command)
                    self.assertEqual(
                        guard_result.returncode,
                        2,
                        msg=f"real git created {new_refs} but the guard did not deny",
                    )
            if not verified_any_command:
                self.skipTest(
                    "installed git did not create a GDD-named ref for any command in this list"
                )

    def test_deny_side_redirection_with_separate_output_target(self):
        # AC-12b (redirection 連続、出力先を per-test tempfile にして衝突を避ける)。
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base = self._make_base_repo(tmp_path)
            log_path = tmp_path / "gdd-oracle-redirect.log"
            command = f"git switch -c 2>/dev/null >{log_path} codex/20260903-x"
            probe = self._fresh_seeded_copy(tmp_path, base, ())
            before = self._refs(probe)
            result = self._run_shell(probe, command)
            after = self._refs(probe)
            new_refs = after - before
            git_created_gdd_ref = result.returncode == 0 and any(
                GDD_TASK_BRANCH_RE_FOR_TEST.search(ref) for ref in new_refs
            )
            if not git_created_gdd_ref:
                self.skipTest("installed git did not create a GDD-named ref for this form")

            guard_repo = self._fresh_seeded_copy(tmp_path, base, ())
            guard_result = self._run_guard(guard_repo, command)
            self.assertEqual(guard_result.returncode, 2)
