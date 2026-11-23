"""S-2: worktree 横断レジストリ（`find-stale-steerings.sh --registry`）の契約テスト。

背景:
実測で `~/.gdd/worktrees` には、origin/main にマージ済みのまま残る worktree が多く、
途中停止のものや未コミット変更のあるものもあった。既存の stale 検出は 2 点足りなかった:

1. 判定が「`Started At` が N 日超 **かつ** `Resume From` が `gdd-brainstorming`」＝
   planning 序盤で放棄されたものしか拾わない。実測の途中停止は `gdd-completion-check` /
   `human-check-waiting` ＝ 完了間際で検出対象外
2. スコープが current worktree / 同一 repo 止まり。実測は複数のリポジトリに分散

走査は **`.git` の存在**で判定する。`~/.gdd/worktrees/*/*` の深さ固定にすると、
branch 名に `/` を含む worktree（実データに `fix/...` がある）を取りこぼす。

`--registry` は **list only**。既存モードが出す片付けの提案（cancel）は付けない。
完了間際の worktree に片付けを勧めるのは有害なため。
"""
from __future__ import annotations

import datetime
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
from _git_fixture import init_repo
SCRIPT = ROOT / "scripts" / "find-stale-steerings.sh"


def _make_worktree(root: Path, repo: str, slug: str, *, next_action: str = "gdd-completion-check",
                   resume_from: str = "gdd-completion-check", dirty: int = 0) -> Path:
    """`.git` を持つ疑似 worktree を作る（branch 名に `/` を含む slug も可）"""
    wt = root / repo / slug
    (wt / ".steering" / "20260601-task").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=wt, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=wt, check=True)
    (wt / ".steering" / "20260601-task" / "state.md").write_text(
        f"Started At: 2026-06-01T00:00:00Z\n"
        f"Resume From: {resume_from}\n"
        f"Human Check Status: approved\n"
        f"Route In Progress: none\n"
        f"Next Action: {next_action}\n",
        encoding="utf-8",
    )
    (wt / "README.md").write_text("x\n", encoding="utf-8")
    # `.steering/` は追跡しない。実運用の GDD steering は branch-only で untracked
    # であり、`git add -A` で巻き込むと AC-14（git tracked 除外）で候補から消える。
    # `.gitignore` に入れて untracked かつ status クリーンな状態を作る。
    (wt / ".gitignore").write_text(".steering/\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=wt, check=True)
    for i in range(dirty):
        (wt / f"dirty{i}.txt").write_text("y\n", encoding="utf-8")
    return wt


def _run_registry(root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GDD_WORKTREES_ROOT"] = str(root)
    return subprocess.run(["bash", str(SCRIPT), "--registry"],
                          capture_output=True, text=True, env=env)


class RegistryDiscoveryTests(unittest.TestCase):
    def test_finds_worktrees_by_git_presence(self) -> None:
        """深さ固定ではなく `.git` の存在で検出する（`fix/...` を取りこぼさない）"""
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            root = Path(tmp)
            _make_worktree(root, "repoA", "20260601-normal")
            _make_worktree(root, "repoB", "fix/nested-branch-name")
            r = _run_registry(root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("20260601-normal", r.stdout)
            self.assertIn(
                "fix/nested-branch-name", r.stdout,
                "depth-fixed globbing would miss slash-containing worktrees "
                f"(4 such worktrees exist in real data): {r.stdout}",
            )

    def test_skips_non_worktree_directories(self) -> None:
        """`.git` の無い中間ディレクトリは worktree として数えない"""
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            root = Path(tmp)
            (root / "repoC" / "not-a-worktree").mkdir(parents=True)
            _make_worktree(root, "repoA", "20260601-real")
            r = _run_registry(root)
            self.assertNotIn("not-a-worktree", r.stdout)


class RegistryOutputTests(unittest.TestCase):
    def test_reports_stopped_task_beyond_brainstorming(self) -> None:
        """完了間際で停止した task を拾う（既存条件は brainstorming 限定で見逃していた）"""
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            root = Path(tmp)
            _make_worktree(root, "repoA", "20260601-stopped",
                           next_action="gdd-completion-check",
                           resume_from="gdd-completion-check")
            r = _run_registry(root)
            self.assertIn("20260601-stopped", r.stdout)
            self.assertIn("gdd-completion-check", r.stdout,
                          "Next Action must appear so the user can judge the stage")

    def test_reports_dirty_and_merged_columns(self) -> None:
        """未コミット件数と merged 判定が列として出る"""
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            root = Path(tmp)
            _make_worktree(root, "repoA", "20260601-dirty", dirty=3)
            r = _run_registry(root)
            self.assertRegex(r.stdout, r"dirty", "dirty column must be present")
            self.assertRegex(r.stdout, r"merged", "merged column must be present")
            self.assertIn("3", r.stdout, "the uncommitted file count must be shown")

    def test_registry_is_list_only(self) -> None:
        """破壊的な提案を出さない（完了間際 + dirty に rm を勧めない）"""
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            root = Path(tmp)
            _make_worktree(root, "repoA", "20260601-stopped", dirty=2)
            r = _run_registry(root)
            for forbidden in ("rm -rf", "mv "):
                with self.subTest(cmd=forbidden):
                    self.assertNotIn(
                        forbidden, r.stdout,
                        f"--registry must not suggest {forbidden!r}; it lists only",
                    )


class NonRegressionTests(unittest.TestCase):
    def test_default_mode_unchanged(self) -> None:
        """既定モードは brainstorming 限定で、候補ごとに cancel を提案する"""
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            wt = _make_worktree(Path(tmp), "repoA", "20260601-brainstorm",
                                resume_from="gdd-brainstorming",
                                next_action="gdd-brainstorming")
            r = subprocess.run(["bash", str(SCRIPT)], cwd=wt, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Cancel 提案", r.stdout,
                          "default mode must print its cancel suggestion")

    def test_help_still_works(self) -> None:
        r = subprocess.run(["bash", str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("registry", r.stdout.lower(),
                      "the new mode must be documented in --help")


class CrossPlatformStatTests(unittest.TestCase):
    """`stat` のオプション差による環境依存を固定する。

    GNU stat (Linux) の `-f` は `--file-system` で、`stat -f %m <file>` は mtime ではなく
    ファイルシステム情報を返す。BSD 形式を先に試す実装は macOS では動くが Linux CI で
    `File: unbound variable` を起こした（実際に CI が落ちた）。
    ローカルが macOS のため通常のテストでは検出できないので、順序を静的に固定する。
    """

    @staticmethod
    def _code_only(text: str) -> str:
        """コメント行を除いた実行部分だけを返す（説明文中の例示を拾わないため）"""
        return "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )

    def test_gnu_stat_is_tried_before_bsd(self) -> None:
        code = self._code_only(SCRIPT.read_text(encoding="utf-8"))
        self.assertIn("stat -c %Y", code)
        self.assertIn("stat -f %m", code)
        self.assertLess(
            code.index("stat -c %Y"), code.index("stat -f %m"),
            "GNU form (-c) must be tried first; GNU's -f means --file-system "
            "and silently returns non-mtime output",
        )

    def test_mtime_output_is_validated_as_numeric(self) -> None:
        """stat の出力が想定外でも算術比較でクラッシュしない"""
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            '[[ "$M" =~ ^[0-9]+$ ]]', text,
            "the mtime value must be validated before arithmetic comparison",
        )


class DepthIndependentDiscoveryTests(unittest.TestCase):
    """走査が深さ上限に依存しないこと（PR #191 レビュー指摘）。

    `-maxdepth 4` 固定では `feature/foo/bar` のようにスラッシュが 2 つ以上ある
    branch 名の worktree を取りこぼす。「深さ固定にすると取りこぼす」と説明しながら
    実装が固定深さでは意図と一致しない。

    ただし素の `-prune` にすると、worktree 配下にネストした無関係な git リポジトリ
    （実データでは terraform module の `.terraform/modules/*/.git`）まで拾ってしまう。
    そのため prune で探索を打ち切りつつ、GDD worktree の判定は別途行う。
    """

    def test_finds_deeply_nested_branch_name(self) -> None:
        """スラッシュ 2 つの branch 名（深さ 5）でも検出する"""
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            root = Path(tmp)
            _make_worktree(root, "repoA", "feature/foo/bar")
            r = _run_registry(root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(
                "feature/foo/bar", r.stdout,
                f"depth-limited discovery misses multi-slash branch names: {r.stdout}",
            )

    def test_skips_nested_git_repos_inside_a_worktree(self) -> None:
        """worktree 配下にネストした無関係な git は拾わない

        実データに `.terraform/modules/<name>/.git` が存在する。
        これを worktree として一覧すると、実体のない行がノイズになる。
        """
        with tempfile.TemporaryDirectory(prefix="gdd-wt-") as tmp:
            root = Path(tmp)
            wt = _make_worktree(root, "repoA", "20260601-normal")
            nested = wt / ".terraform" / "modules" / "vendored"
            nested.mkdir(parents=True)
            subprocess.run(["git", "init", "-q"], cwd=nested, check=True)
            r = _run_registry(root)
            self.assertIn("20260601-normal", r.stdout)
            self.assertNotIn(
                "vendored", r.stdout,
                f"a git repo nested inside a worktree must not be listed: {r.stdout}",
            )


class StaleScanDedupeTests(unittest.TestCase):
    """stale scan（default / `--all-worktrees`）の dedupe と git tracked 除外。

    fixture は**実 `git worktree add`** を使う。`git worktree list --porcelain` の
    並び順が「代表の決まり方」そのものなので、疑似ディレクトリでは契約を測れない。

    実行 shell は macOS 既定の `bash 3.2` になりうる（実測: `GNU bash, version
    3.2.57`）。連想配列（`declare -A`）と `set -u` 下の空配列展開は 3.2 で落ちるため、
    本クラスの behavioral test はその両方を素通りさせない。
    """

    def _init_repo_with_worktrees(self, tmp: Path) -> tuple[Path, Path, Path]:
        """main + wt1 + wt2 の実 worktree を作る（`worktree list` の順 = main, wt1, wt2）"""
        main = tmp / "main"
        main.mkdir()

        def run(*argv: str) -> None:
            subprocess.run(list(argv), cwd=main, check=True,
                           capture_output=True, text=True)
        init_repo(main)
        wt1, wt2 = tmp / "wt1", tmp / "wt2"
        run("git", "worktree", "add", "-q", "-b", "b1", str(wt1))
        run("git", "worktree", "add", "-q", "-b", "b2", str(wt2))
        return main, wt1, wt2

    def _write_steering(self, wt: Path, slug: str, *, days_ago: int = 20) -> Path:
        """stale 判定を満たす steering を置く（`Resume From=gdd-brainstorming` + 閾値超）"""
        started = (datetime.datetime.now(datetime.timezone.utc)
                   - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
        steering = wt / ".steering" / slug
        steering.mkdir(parents=True)
        (steering / "state.md").write_text(
            f"Started At: {started}\n"
            f"Resume From: gdd-brainstorming\n"
            f"Next Action: gdd-brainstorming\n",
            encoding="utf-8",
        )
        return steering

    def _track(self, wt: Path, steering: Path) -> None:
        for args in (["git", "add", str(steering / "state.md")],
                     ["git", "commit", "-q", "-m", "track steering"]):
            subprocess.run(args, cwd=wt, check=True, capture_output=True, text=True)

    def _run(self, wt: Path, *args: str,
             env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", str(SCRIPT), *args], cwd=wt,
                              capture_output=True, text=True, env=env)

    @staticmethod
    def _candidate_slugs(stdout: str) -> list[str]:
        return re.findall(r"^slug:\s+(\S+)$", stdout, flags=re.MULTILINE)

    # --- dedupe (AC-13) ---

    def test_same_slug_in_two_worktrees_yields_one_candidate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-dedupe-") as tmp:
            _main, wt1, wt2 = self._init_repo_with_worktrees(Path(tmp))
            self._write_steering(wt1, "20260601-dup")
            self._write_steering(wt2, "20260601-dup")
            r = self._run(wt1, "--all-worktrees")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(
                self._candidate_slugs(r.stdout), ["20260601-dup"],
                f"the same slug in 2 worktrees must collapse to 1 candidate: {r.stdout}",
            )
            self.assertIn(str(wt1), r.stdout,
                          "the representative is the first worktree in `git worktree list` order")
            self.assertIn("除外（重複）", r.stdout, "AC-13: the excluded duplicate must stay visible")
            self.assertIn(str(wt2), r.stdout,
                          "AC-13: the *location* of the excluded duplicate must stay visible")
            self.assertIn("合計 1 件の stale 候補を検出", r.stdout)

    def test_distinct_slugs_are_not_collapsed(self) -> None:
        """dedupe が「常に 1 件」に潰す実装でないことを固定する（null control）"""
        with tempfile.TemporaryDirectory(prefix="gdd-dedupe-") as tmp:
            _main, wt1, wt2 = self._init_repo_with_worktrees(Path(tmp))
            self._write_steering(wt1, "20260601-a")
            self._write_steering(wt2, "20260601-b")
            r = self._run(wt1, "--all-worktrees")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sorted(self._candidate_slugs(r.stdout)),
                             ["20260601-a", "20260601-b"], r.stdout)
            self.assertNotIn("除外（重複）", r.stdout,
                             "no duplicate exists, so no duplicate-exclusion section")

    # --- git tracked 除外 (AC-14) ---

    def test_git_tracked_steering_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-tracked-") as tmp:
            _main, wt1, _wt2 = self._init_repo_with_worktrees(Path(tmp))
            steering = self._write_steering(wt1, "20260601-tracked")
            self._track(wt1, steering)
            r = self._run(wt1, "--all-worktrees")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(self._candidate_slugs(r.stdout), [],
                             f"a git tracked steering must not be a stale candidate: {r.stdout}")
            self.assertIn("除外（git tracked）: 1 件", r.stdout,
                          "AC-14: the excluded count must stay in the output")
            self.assertIn(str(wt1), r.stdout)

    def test_untracked_copy_survives_when_the_first_worktree_is_tracked(self) -> None:
        """tracked 除外は dedupe の代表選出より先に効く。

        先頭 worktree の copy が tracked のとき、それが slug を占有してしまうと
        後続 worktree の**追跡されていない本物**まで消える。
        """
        with tempfile.TemporaryDirectory(prefix="gdd-order-") as tmp:
            _main, wt1, wt2 = self._init_repo_with_worktrees(Path(tmp))
            steering = self._write_steering(wt1, "20260601-both")
            self._track(wt1, steering)
            self._write_steering(wt2, "20260601-both")
            r = self._run(wt1, "--all-worktrees")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(self._candidate_slugs(r.stdout), ["20260601-both"],
                             f"the untracked copy must remain a candidate: {r.stdout}")
            self.assertIn(str(wt2), r.stdout,
                          "the untracked copy in the 2nd worktree is the representative")

    def test_ls_files_failure_keeps_the_candidate(self) -> None:
        """`git ls-files` が失敗する環境では fail-open（従来どおり候補に残す）"""
        with tempfile.TemporaryDirectory(prefix="gdd-failopen-") as tmp:
            root = Path(tmp)
            _main, wt1, _wt2 = self._init_repo_with_worktrees(root)
            steering = self._write_steering(wt1, "20260601-failopen")
            self._track(wt1, steering)
            bindir = root / "bin"
            bindir.mkdir()
            real_git = shutil.which("git")
            assert real_git, "git is required to run these tests"
            shim = bindir / "git"
            shim.write_text(textwrap.dedent(f"""\
                #!/bin/sh
                for a in "$@"; do
                  [ "$a" = "ls-files" ] && exit 128
                done
                exec {real_git} "$@"
                """), encoding="utf-8")
            shim.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
            r = self._run(wt1, "--all-worktrees", env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(self._candidate_slugs(r.stdout), ["20260601-failopen"],
                             f"an ls-files failure must not drop the candidate: {r.stdout}")
            self.assertNotIn("除外（git tracked）", r.stdout)

    def test_glob_metacharacter_slug_is_not_excluded_by_a_tracked_sibling(self) -> None:
        """tracked 判定の pathspec は literal。`?` を含む slug が別 steering に glob 一致しない。

        `ls-files --error-unmatch <path>` は pathspec としてワイルドカード解釈されるため、
        `20260601-rea?` が tracked な `20260601-real/state.md` に一致し、
        **追跡されていない別 steering** が「git tracked」として黙って落ちる
        （over-exclusion = silent false negative）。
        """
        with tempfile.TemporaryDirectory(prefix="gdd-literal-") as tmp:
            _main, wt1, _wt2 = self._init_repo_with_worktrees(Path(tmp))
            tracked = self._write_steering(wt1, "20260601-real")
            self._track(wt1, tracked)
            self._write_steering(wt1, "20260601-rea?")
            r = self._run(wt1)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(
                self._candidate_slugs(r.stdout), ["20260601-rea?"],
                f"an untracked slug containing `?` must stay a candidate: {r.stdout}",
            )
            self.assertIn(
                "除外（git tracked）: 1 件", r.stdout,
                f"only the genuinely tracked steering may be excluded: {r.stdout}",
            )

    # --- no-op / 既定モード ---

    def test_default_mode_prints_no_exclusion_sections(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-noop-") as tmp:
            _main, wt1, _wt2 = self._init_repo_with_worktrees(Path(tmp))
            self._write_steering(wt1, "20260601-plain")
            r = self._run(wt1)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(self._candidate_slugs(r.stdout), ["20260601-plain"])
            self.assertIn("Cancel 提案", r.stdout)
            self.assertNotIn("除外", r.stdout,
                             "nothing was excluded, so no exclusion noise")


class RegistryUnaffectedByStaleScanTests(unittest.TestCase):
    """AC-15: `--registry` は dedupe / tracked 除外の影響を受けない。"""

    def test_registry_keeps_its_columns_and_gains_no_exclusion_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-reg-") as tmp:
            root = Path(tmp)
            _make_worktree(root, "repoA", "20260601-same")
            _make_worktree(root, "repoB", "20260601-same")
            r = _run_registry(root)
            self.assertEqual(r.returncode, 0, r.stderr)
            header = r.stdout.splitlines()[0]
            self.assertEqual(
                header.split(),
                ["worktree", "branch", "next_action", "updated", "merged", "dirty"],
                "the 6-column header is part of the registry contract",
            )
            self.assertEqual(r.stdout.count("20260601-same"), 2,
                             "registry lists worktrees, not stale candidates: no dedupe")
            self.assertNotIn("除外", r.stdout,
                             "--registry must not gain dedupe / tracked exclusion output")

    def test_registry_is_unreachable_from_the_stale_scan(self) -> None:
        """構造的支配: registry ブロックは stale scan 到達前に `exit 0` する"""
        code = "\n".join(
            line for line in SCRIPT.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        )
        # `index()` は最初の一致を返すので、アンカーが一意でないと別の構文を指しうる。
        # 測る述語（registry ブロックの出口）と書く述語を一致させるため一意性も固定する。
        self.assertEqual(code.count("exit 0\nfi"), 1,
                         "the exit anchor must be unique, otherwise index() may point elsewhere")
        self.assertLess(code.index("exit 0\nfi"), code.index("STALE_COUNT=0"),
                        "the registry branch must exit before the stale scan loop")


class HelpOutputTests(unittest.TestCase):
    def test_help_documents_the_tracked_exclusion_side_effect(self) -> None:
        r = subprocess.run(["bash", str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tracked", r.stdout.lower(),
                      "AC-14 の副作用（tracked 運用 repo は検出対象外）を --help に残す")

    def test_help_prints_only_the_header_comment(self) -> None:
        """`--help` が実行コードを漏らさない（行番号 literal による範囲指定の副作用）"""
        r = subprocess.run(["bash", str(SCRIPT), "--help"], capture_output=True, text=True)
        leaked = [ln for ln in r.stdout.splitlines()
                  if ln.strip() and not ln.lstrip().startswith("#")]
        self.assertEqual(leaked, [], f"--help leaked non-comment lines: {leaked}")


if __name__ == "__main__":
    unittest.main()
