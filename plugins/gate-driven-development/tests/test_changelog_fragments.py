"""変更断片（`changelog.d/`）とリリーススクリプトの契約テスト。

通常の PR は版数系のファイル（3 manifest・`CHANGELOG.md` の版見出し・`docs/VERSIONING.md` の現状）に
触れず、`changelog.d/` に断片を 1 つ足す。版数上げと CHANGELOG への集約は `scripts/release.py` が
リリース時にまとめて行う。並行する PR が版数系のファイルで互いに衝突しないことが目的。

固定するもの:
- 版数の決め方: 断片の種別の最大値（breaking > minor > patch）。v0.x の breaking は minor を上げる
- `scripts/release.py`: 断片 0 件なら何もしない / 既定は dry-run / `--apply` で 4 箇所を更新して断片を消す
- `tests/checks/version-not-consumed.sh`: 断片の要求・リリースのコミットの判定・版数の後退・入力の型違い
- 2 本の PR がそれぞれ断片を 1 つ足しても、互いに衝突しない
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _plugin_module_loader import PLUGIN_ROOT, load_plugin_module

release = load_plugin_module("scripts/release.py")

MANIFESTS = (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json", ".codex-plugin/plugin.json")
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

CHANGELOG = """# Changelog

## Policy

- 断片は `changelog.d/` に書く

## Current Release Notes

### [{version}] - 2026-09-11

#### Summary

- 前の版
"""

VERSIONING = """# VERSIONING

## 現状

- **現行バージョン**: v{version}（3 manifest）

## リリース手順

- **統合先の定義**: `origin/main`（`GDD_INTEGRATION_REF` で上書き可）
"""


def fragment(kind: str = "patch", summary: str = "- 要約", extra: str = "") -> str:
    return (
        f"---\ntype: {kind}\n---\n\n"
        f"#### Summary\n\n{summary}\n\n"
        f"{extra}"
        "#### Affected Files\n\n- `skills/a.md`\n\n"
        "#### User Action Required\n\n- なし\n\n"
        "#### Validation / Eval Impact\n\n- `tests/test_changelog_fragments.py`\n"
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


MARKETPLACE_NAME = "gate-driven-development"


def write_marketplace_json(repo_root: Path, name: str = MARKETPLACE_NAME) -> None:
    write(repo_root / ".claude-plugin" / "marketplace.json", json.dumps({"name": name}) + "\n")


def make_plugin(root: Path, version: str = "0.43.0") -> Path:
    for manifest in MANIFESTS:
        write(root / manifest, json.dumps({"name": "gdd", "version": version, "description": "d"}, indent=2) + "\n")
    write(root / "CHANGELOG.md", CHANGELOG.format(version=version))
    write(root / "docs" / "VERSIONING.md", VERSIONING.format(version=version))
    write(root / "skills" / "a.md", "a\n")
    write(root / "skills" / "b.md", "b\n")
    for rel in ("scripts/release.py", "scripts/lib/repository_identity.py", "tests/checks/version-not-consumed.sh"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PLUGIN_ROOT / rel, root / rel)
    return root


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def run_release(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "release.py"), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def run_check(root: Path, ref: str = "main") -> subprocess.CompletedProcess:
    # 検査は GIT_* を落とすので、GIT_CONFIG_GLOBAL の代わりに HOME を外して開発者の ~/.gitconfig を読ませない。
    env = {
        **GIT_ENV, "ROOT": str(root), "PYTHON_BIN": sys.executable, "GDD_INTEGRATION_REF": ref,
        "HOME": os.devnull, "XDG_CONFIG_HOME": os.devnull,
    }
    return subprocess.run(
        ["bash", str(root / "tests" / "checks" / "version-not-consumed.sh")],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        capture_output=True,
        text=True,
        env=GIT_ENV,
        check=False,
    )


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    result = git(repo, "commit", "-q", "-m", message)
    assert result.returncode == 0, result.stderr


def init_repo(repo: Path) -> Path:
    """plugin を `plugins/gdd/` に置いた合成 repo を作り、main に 1 commit 積む。plugin の root を返す。"""
    git(repo, "init", "-q", "-b", "main")
    write_marketplace_json(repo)
    plugin = make_plugin(repo / "plugins" / "gdd")
    commit_all(repo, "base")
    return plugin


class NextVersionTests(unittest.TestCase):
    def test_bump_follows_the_largest_kind(self) -> None:
        cases = [
            ("0.43.0", ["patch"], "0.43.1"),
            ("0.43.2", ["patch", "minor", "patch"], "0.44.0"),
            ("0.43.2", ["minor", "breaking"], "0.44.0"),  # v0.x の breaking は minor を上げる
            ("1.2.3", ["patch"], "1.2.4"),
            ("1.2.3", ["minor", "patch"], "1.3.0"),
            ("1.2.3", ["patch", "breaking"], "2.0.0"),
        ]
        for current, kinds, expected in cases:
            with self.subTest(current=current, kinds=kinds):
                self.assertEqual(release.next_version(current, kinds), expected)


class ReleaseScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_plugin(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def add_fragment(self, name: str, text: str) -> None:
        write(self.root / "changelog.d" / name, text)

    def plan(self) -> tuple[list, dict[Path, str]]:
        """`main()` と同じ手順で fragments と writes を作る（apply_writes を直接呼ぶテスト用）。"""
        fragments, errors = release.load_fragments(self.root)
        self.assertFalse(errors, errors)
        current, errors = release.read_current_version(self.root)
        self.assertFalse(errors, errors)
        new = release.next_version(current, [f.kind for f in fragments])
        section = release.render_section(new, "2026-09-12", fragments)
        writes, errors = release.plan_writes(self.root, current, new, section)
        self.assertFalse(errors, errors)
        return fragments, writes

    def test_no_fragments_is_a_noop(self) -> None:
        for make_dir in (False, True):
            with self.subTest(changelog_d_exists=make_dir):
                if make_dir:
                    (self.root / "changelog.d").mkdir(exist_ok=True)
                before = snapshot(self.root)
                result = run_release(self.root, "--apply")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("nothing to release", result.stdout)
                self.assertEqual(snapshot(self.root), before)

    def test_dry_run_is_the_default_and_writes_nothing(self) -> None:
        self.add_fragment("20260912-a.md", fragment("patch"))
        self.add_fragment("20260913-b.md", fragment("minor"))
        before = snapshot(self.root)
        result = run_release(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("dry-run", result.stdout)
        self.assertIn("### [0.44.0] - ", result.stdout)
        self.assertEqual(snapshot(self.root), before)

    def test_apply_updates_version_files_and_collects_fragments(self) -> None:
        self.add_fragment(
            "20260912-a.md",
            fragment(
                "patch",
                summary="- 要約 A",
                extra="#### Fixed\n\n- 修正 A\n\n#### Known limitations\n\n- 限界 A\n\n",
            ).replace(
                "- `tests/test_changelog_fragments.py`\n",
                "- `tests/test_changelog_fragments.py`\n\n```bash\n# コメントは見出しではない\n#### これも見出しではない\n```\n",
            ),
        )
        self.add_fragment("20260913-b.md", fragment("minor", summary="- 要約 B", extra="#### Added\n\n- 追加 B\n\n"))
        manifest_before = (self.root / MANIFESTS[0]).read_text(encoding="utf-8")

        result = run_release(self.root, "--apply", "--date", "2026-09-20")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        for manifest in MANIFESTS:
            self.assertEqual(json.loads((self.root / manifest).read_text(encoding="utf-8"))["version"], "0.44.0")
        # version 行以外は書き換えない
        self.assertEqual(
            (self.root / MANIFESTS[0]).read_text(encoding="utf-8"),
            manifest_before.replace('"0.43.0"', '"0.44.0"'),
        )
        self.assertIn("**現行バージョン**: v0.44.0（", (self.root / "docs" / "VERSIONING.md").read_text(encoding="utf-8"))
        self.assertEqual(list((self.root / "changelog.d").glob("*.md")), [])

        changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        new_section, previous = changelog.split("## Current Release Notes\n\n", 1)[1].split("### [0.43.0]", 1)
        self.assertTrue(new_section.startswith("### [0.44.0] - 2026-09-20\n"), new_section)
        self.assertIn("#### Summary", previous)  # 前の版の節は残る
        headings = [line for line in new_section.splitlines() if line.startswith("#### ") and "見出しではない" not in line]
        self.assertEqual(
            headings,
            [
                "#### Summary",
                "#### Added",
                "#### Fixed",
                "#### Known limitations",
                "#### Affected Files",
                "#### User Action Required",
                "#### Validation / Eval Impact",
            ],
        )
        summary = new_section.split("#### Summary", 1)[1].split("#### Added", 1)[0]
        self.assertLess(summary.index("要約 A"), summary.index("要約 B"))  # 断片はファイル名の順
        self.assertIn("# コメントは見出しではない", new_section)

        again = run_release(self.root, "--apply")
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertIn("nothing to release", again.stdout)

    def test_invalid_fragment_fails_without_writing(self) -> None:
        cases = {
            "unknown type": ("20260912-a.md", fragment("huge")),
            "no frontmatter": ("20260912-a.md", fragment("patch").split("---\n\n", 1)[1]),
            "missing required section": ("20260912-a.md", fragment("patch").replace("#### Affected Files", "#### Files")),
            "version heading inside": ("20260912-a.md", fragment("patch") + "\n### [9.9.9] - 2026-01-01\n"),
            "text before first section": ("20260912-a.md", fragment("patch").replace("---\n\n#### Summary", "---\n\n前置き\n\n#### Summary")),
            "breaking without breaking section": ("20260912-a.md", fragment("breaking")),
            "bad file name": ("notes.md", fragment("patch")),
        }
        for label, (name, text) in cases.items():
            with self.subTest(label):
                shutil.rmtree(self.root / "changelog.d", ignore_errors=True)
                self.add_fragment(name, text)
                before = snapshot(self.root)
                result = run_release(self.root, "--apply")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(name, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(snapshot(self.root), before)

    def test_breaking_fragment_with_breaking_section_is_accepted(self) -> None:
        self.add_fragment("20260912-a.md", fragment("breaking", extra="#### Breaking Contract Changes\n\n- 破壊的変更\n\n"))
        result = run_release(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("### [0.44.0] - ", result.stdout)

    def test_manifest_mismatch_fails_without_writing(self) -> None:
        self.add_fragment("20260912-a.md", fragment("patch"))
        write(self.root / MANIFESTS[1], json.dumps({"name": "gdd", "version": "0.42.0"}, indent=2) + "\n")
        before = snapshot(self.root)
        result = run_release(self.root, "--apply")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_apply_failure_leaves_everything_unchanged(self) -> None:
        """途中の書き込み失敗で、manifest・VERSIONING・CHANGELOG・断片のどれも書き換わらない
        （一時ファイルへ書いてから置換するので、失敗時点でまだ本体には触れていない）。"""
        self.add_fragment("20260912-a.md", fragment("patch"))
        before = snapshot(self.root)
        docs_dir = self.root / "docs"
        original_mode = docs_dir.stat().st_mode
        docs_dir.chmod(0o500)  # 書き込み不可にして VERSIONING.md の一時ファイル作成を失敗させる
        try:
            result = run_release(self.root, "--apply")
        finally:
            docs_dir.chmod(original_mode)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_replace_failure_partway_restores_the_already_replaced_files(self) -> None:
        """新しい内容への置換が一部の対象で終わった後に失敗しても、その分も含めて全て元に戻る
        （バックアップは退避フェーズで全対象分すでにあるので、置換済みの対象もバックアップから戻せる）。
        `writes` は 5 件（manifest 3・VERSIONING・CHANGELOG）で、os.replace は退避フェーズに 5 回・
        置換フェーズに 5 回呼ばれる。7 回目（置換フェーズの 2 回目、1 件はすでに新しい内容に置換済み）
        で失敗させることで、単なる退避フェーズの失敗ではなく「置換済みの取り消し」を検証する。"""
        self.add_fragment("20260912-a.md", fragment("patch"))
        fragments, writes = self.plan()
        self.assertEqual(len(writes), 5)
        before = snapshot(self.root)

        real_replace = os.replace
        calls = {"n": 0}

        def flaky_replace(src, dst):
            calls["n"] += 1
            if calls["n"] == 7:
                raise OSError("injected failure")
            return real_replace(src, dst)

        with mock.patch("os.replace", side_effect=flaky_replace):
            with self.assertRaises(OSError):
                release.apply_writes(writes, [f.path for f in fragments])

        self.assertGreaterEqual(calls["n"], 7)  # 退避フェーズ(5 回)を過ぎ、置換フェーズの途中で失敗した
        self.assertEqual(snapshot(self.root), before)

    def test_fragment_deletion_failure_restores_the_already_replaced_files(self) -> None:
        """断片の削除が失敗しても、既に置換した manifest・VERSIONING・CHANGELOG まで含めて全て元に戻る
        （断片削除は置換より後に行うので、置換済みの本体だけが更新されたまま残ることはない）。"""
        self.add_fragment("20260912-a.md", fragment("patch"))
        self.add_fragment("20260913-b.md", fragment("minor"))
        fragments, writes = self.plan()
        before = snapshot(self.root)

        real_unlink = Path.unlink
        calls = {"n": 0}

        def flaky_unlink(path, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise OSError("injected failure")
            return real_unlink(path, *args, **kwargs)

        with mock.patch.object(Path, "unlink", flaky_unlink):
            with self.assertRaises(OSError):
                release.apply_writes(writes, [f.path for f in fragments])

        self.assertEqual(snapshot(self.root), before)


class VersionCheckTests(unittest.TestCase):
    """`tests/checks/version-not-consumed.sh` を合成 git repo の上で実行する。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.plugin = init_repo(self.repo)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def branch(self, name: str) -> None:
        self.assertEqual(git(self.repo, "switch", "-q", "-c", name, "main").returncode, 0)

    def bump_by_hand(self, version: str) -> None:
        for manifest in MANIFESTS:
            path = self.plugin / manifest
            path.write_text(path.read_text(encoding="utf-8").replace('"0.43.0"', f'"{version}"'), encoding="utf-8")
        changelog = self.plugin / "CHANGELOG.md"
        changelog.write_text(
            changelog.read_text(encoding="utf-8").replace(
                "## Current Release Notes\n\n",
                f"## Current Release Notes\n\n### [{version}] - 2026-09-12\n\n#### Summary\n\n- x\n\n",
            ),
            encoding="utf-8",
        )

    def test_pr_without_fragment_fails(self) -> None:
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)

    def test_uncommitted_fragment_is_named_in_the_failure(self) -> None:
        # 断片を書いたが commit していないと、「断片が無い」とだけ出て原因が分からなかった。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        write(self.plugin / "changelog.d" / "20260912-feat.md", "---\ntype: patch\n---\n")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertIn("not committed yet: changelog.d/20260912-feat.md", result.stdout)

    def test_files_that_are_not_new_fragments_are_not_named(self) -> None:
        # 名指しするのは、changelog.d/ 直下に新しく足した .md（ドットファイルを除く）だけ。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        write(self.plugin / "changelog.d" / ".draft.md", "x\n")
        write(self.plugin / "changelog.d" / "notes.txt", "x\n")
        write(self.plugin / "changelog.d" / "sub" / "20260912-x.md", "x\n")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertNotIn("not committed yet", result.stdout)

    def test_committed_fragment_edited_in_the_working_tree_is_not_named(self) -> None:
        # commit 済みの断片を作業ツリーで書き換えた（` M`）だけなら、「commit していない」とは言わない。
        self.branch("feat")
        write(self.plugin / "changelog.d" / "20260912-feat.md", "---\ntype: patch\n---\n")
        commit_all(self.repo, "add a broken fragment")
        write(self.plugin / "changelog.d" / "20260912-feat.md", "---\ntype: patch\n---\n\nx\n")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertNotIn("not committed yet", result.stdout)

    def test_staged_new_fragment_is_named_and_staged_edit_of_committed_fragment_is_not(self) -> None:
        # index に足しただけ（`A `）の新しい断片は名指しする。commit 済みの断片の書き換えを index に載せた（`M `）だけなら名指ししない。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        write(self.plugin / "changelog.d" / "20260912-feat.md", "---\ntype: patch\n---\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, capture_output=True)
        result = run_check(self.plugin)
        self.assertIn("not committed yet: changelog.d/20260912-feat.md", result.stdout)

        commit_all(self.repo, "add a broken fragment")
        write(self.plugin / "changelog.d" / "20260912-feat.md", "---\ntype: patch\n---\n\nx\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, capture_output=True)
        result = run_check(self.plugin)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertNotIn("not committed yet", result.stdout)

    def test_fragment_renamed_with_git_mv_is_named(self) -> None:
        # `git mv` で改名した断片は index で rename（`R`）と出る。新しい名前を名指しする。
        self.branch("feat")
        write(self.plugin / "changelog.d" / "20260912-a.md", "---\ntype: patch\n---\n")
        commit_all(self.repo, "add a broken fragment")
        subprocess.run(
            ["git", "-C", str(self.repo), "mv", str(self.plugin / "changelog.d" / "20260912-a.md"), str(self.plugin / "changelog.d" / "20260912-b.md")],
            check=True, capture_output=True,
        )
        result = run_check(self.plugin)
        self.assertIn("not committed yet: changelog.d/20260912-b.md", result.stdout)

    def test_fragment_of_another_pr_renamed_without_changes_is_not_named(self) -> None:
        # merge-base にある他の PR の断片を、中身を変えずに `git mv` しただけなら、自分の断片として名指ししない。
        write(self.plugin / "changelog.d" / "20260911-old.md", "---\ntype: patch\n---\n")
        commit_all(self.repo, "another PR's fragment")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        subprocess.run(
            ["git", "-C", str(self.repo), "mv", str(self.plugin / "changelog.d" / "20260911-old.md"), str(self.plugin / "changelog.d" / "20260912-new.md")],
            check=True, capture_output=True,
        )
        result = run_check(self.plugin)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertNotIn("not committed yet", result.stdout)

    def test_fragment_of_another_pr_moved_without_git_mv_is_not_named(self) -> None:
        # `git mv` ではなく普通の mv で改名して commit していない（`??`）ものも、commit 後に数えないので名指ししない。
        write(self.plugin / "changelog.d" / "20260911-old.md", "---\ntype: patch\n---\n")
        commit_all(self.repo, "another PR's fragment")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        (self.plugin / "changelog.d" / "20260911-old.md").rename(self.plugin / "changelog.d" / "20260912-new.md")
        result = run_check(self.plugin)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertNotIn("not committed yet", result.stdout)

    def test_own_fragment_with_the_same_content_as_a_kept_one_is_named(self) -> None:
        # merge-base の断片が元の場所に残っていれば、同じ中身の自分の断片は commit 後に数えるので、名指しする。
        write(self.plugin / "changelog.d" / "20260911-old.md", "---\ntype: patch\n---\n")
        commit_all(self.repo, "another PR's fragment")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        write(self.plugin / "changelog.d" / "20260912-own.md", "---\ntype: patch\n---\n")
        self.assertEqual(git(self.repo, "add", "-A").returncode, 0)
        result = run_check(self.plugin)
        self.assertIn("not committed yet: changelog.d/20260912-own.md", result.stdout)

    def test_only_the_moved_count_is_left_unnamed(self) -> None:
        # 改名した 1 つと、同じ中身の自分の断片 1 つ。commit 後に数えるのは 1 つなので、1 つだけ名指しする。
        write(self.plugin / "changelog.d" / "20260911-old.md", "---\ntype: patch\n---\n")
        commit_all(self.repo, "another PR's fragment")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        (self.plugin / "changelog.d" / "20260911-old.md").rename(self.plugin / "changelog.d" / "20260912-a-new.md")
        write(self.plugin / "changelog.d" / "20260912-b-own.md", "---\ntype: patch\n---\n")
        result = run_check(self.plugin)
        self.assertIn("not committed yet: changelog.d/20260912-b-own.md", result.stdout)
        self.assertNotIn("20260912-a-new.md", result.stdout.split("not committed yet")[1].split("Not counted")[0])

    def test_own_fragment_is_named_after_a_committed_rename_takes_the_moved_slot(self) -> None:
        # commit 済みの改名が、消えた断片の分を先に取る。同じ中身の自分の断片は、名前の順に関係なく名指しする。
        for own, renamed in (("20260912-a-own.md", "20260913-renamed.md"), ("20260913-own.md", "20260912-a-renamed.md")):
            with self.subTest(own=own):
                self.setUp()
                write(self.plugin / "changelog.d" / "20260911-old.md", fragment())
                commit_all(self.repo, "another PR's fragment")
                self.branch("feat")
                write(self.plugin / "skills" / "a.md", "changed\n")
                self.assertEqual(
                    git(self.repo, "mv", str(self.plugin / "changelog.d" / "20260911-old.md"), str(self.plugin / "changelog.d" / renamed)).returncode,
                    0,
                )
                commit_all(self.repo, "rename another PR's fragment")
                write(self.plugin / "changelog.d" / own, fragment())
                result = run_check(self.plugin)
                self.assertIn(f"not committed yet: changelog.d/{own}", result.stdout)
                self.tearDown()

    def test_restored_fragment_of_another_pr_is_not_named(self) -> None:
        # commit で消した merge-base の断片を index に戻しても、自分の断片として名指ししない。
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment())
        commit_all(self.repo, "another PR's fragment")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        (self.plugin / "changelog.d" / "20260911-old.md").unlink()
        commit_all(self.repo, "delete another PR's fragment")
        self.assertEqual(git(self.repo, "checkout", "main", "--", str(self.plugin / "changelog.d" / "20260911-old.md")).returncode, 0)
        result = run_check(self.plugin)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertNotIn("not committed yet", result.stdout)

    def test_ordinary_validation_failure_is_not_misdiagnosed_as_dynamic_module_load(self) -> None:
        # Codex レビュー指摘（medium）: die() は通常の入力検証失敗（断片
        # 未追加等）でも SystemExit(1) を送出するため、呼び出し元の
        # except SystemExit ハンドラが動的ロードしたモジュール由来かどうかを
        # 区別しないまま固定文言を出すと、最も一般的な失敗経路（die() 経由）
        # にまで「動的モジュールロード中の異常」という誤った原因を付加して
        # しまう。die() 経由の通常失敗では、この診断文言（"dynamic module
        # load"）が出ないことを固定する。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertNotIn("dynamic module load", result.stdout)
        # 独立レビュー指摘（独立-1・F6・medium）: 否定検査だけでは「文言を
        # 言い換えれば通る」列挙型だったため、die() 経路でも新しい固定文言
        # 全体が出力に含まれることを積極的に確認する肯定検査を追加する。
        self.assertIn("FAIL: version-not-consumed: run() ended via SystemExit without returning a verdict", result.stdout)

    def test_pr_with_fragment_passes(self) -> None:
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_pr_with_invalid_fragment_fails(self) -> None:
        self.branch("feat")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment("huge"))
        commit_all(self.repo, "change")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("20260912-a.md", result.stdout)

    def test_fragment_carried_over_from_main_does_not_count(self) -> None:
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)

    def test_bump_with_fragments_left_fails(self) -> None:
        self.branch("feat")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        self.bump_by_hand("0.43.1")
        commit_all(self.repo, "old-style bump")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("release commit", result.stdout)

    def test_release_commit_passes(self) -> None:
        write(self.plugin / "changelog.d" / "20260911-a.md", fragment("minor"))
        commit_all(self.repo, "merged PR")
        self.branch("release")
        applied = run_release(self.plugin, "--apply", "--date", "2026-09-12")
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        commit_all(self.repo, "release")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("0.44.0", result.stdout)

    def test_version_regression_fails(self) -> None:
        self.branch("feat")
        self.bump_by_hand("0.42.9")
        commit_all(self.repo, "regress")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("lower than", result.stdout)

    def test_missing_shared_identity_module_fails_closed(self) -> None:
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        (self.plugin / "scripts" / "lib" / "repository_identity.py").unlink()
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("cannot load scripts/lib/repository_identity.py", result.stdout)

    def test_corrupted_shared_identity_module_fails_closed(self) -> None:
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        write(self.plugin / "scripts" / "lib" / "repository_identity.py", "def broken(:\n    this is not valid python\n")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("cannot load scripts/lib/repository_identity.py", result.stdout)

    def test_shared_identity_module_raising_systemexit_fails_closed(self) -> None:
        # 独立レビュー指摘（PR後-1・high・実害あり）: `except Exception` は
        # `SystemExit`（BaseException 派生）を捕捉できず、モジュールの exec 中に
        # SystemExit が送出されると try/except を素通りしてスクリプト全体が
        # rc=0 で静かに成功してしまう。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        write(self.plugin / "scripts" / "lib" / "repository_identity.py", "import sys\nsys.exit(0)\n")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("cannot load scripts/lib/repository_identity.py", result.stdout)

    def test_shared_release_module_raising_systemexit_fails_closed(self) -> None:
        # 独立レビュー指摘（独立-6・high・実害あり）: release.py のロードにも
        # 同じ `except Exception` パターンが別に書かれており、SystemExit を
        # 送出するモジュールで try/except を素通りしてしまう。exec_module
        # 専用のブートストラップ（load_dynamic_module）に一本化して閉じた。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        write(self.plugin / "scripts" / "release.py", "import sys\nsys.exit(0)\n")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("cannot load scripts/release.py", result.stdout)

    def test_identity_function_call_raising_systemexit_fails_closed(self) -> None:
        # PR #93 の PR 後レビュー3巡目（独立-5・独立-6に続く同クラスタの High）:
        # load_dynamic_module() は exec_module() 呼び出しの SystemExit だけを
        # 守り、ロード自体は成功したモジュールへの「呼び出し」
        # (identity_lib.repository_identity(...)) で SystemExit が送出される
        # と、fail()/die() に到達せず rc=0 で静かに成功していた。run() を
        # 正常return しなかった経路として呼び出し元の except で一律 FAIL に
        # 合流させる構造に変えたことで、この経路も閉じることを固定する。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        write(
            self.plugin / "scripts" / "lib" / "repository_identity.py",
            "import sys\n\n\ndef repository_identity(base, marketplace_name):\n    sys.exit(0)\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: OK", result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: SKIP", result.stdout)

    def test_load_fragments_call_raising_systemexit_fails_closed(self) -> None:
        # 同クラスタ、呼び出し箇所2つ目: release.load_fragments() の呼び出し中に
        # SystemExit が送出されるケース（changelog.d/20260916-...md の Known
        # limitations で「現時点では到達不能」と開示していたが、release.py の
        # 将来の変更で到達可能になった場合の同型 fail-open として、独立-7・
        # PR #93 の新レビューで再指摘された）。NAME_RE は他の入力検査
        # （断片名パターン）で使われるため、通常の正規表現のままにする。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        write(
            self.plugin / "scripts" / "release.py",
            "import re\nimport sys\n\n\nNAME_RE = re.compile(r'.*')\n\n\n"
            "def load_fragments(root):\n    sys.exit(0)\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: OK", result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: SKIP", result.stdout)

    def test_identity_function_call_raising_systemexit_256_is_not_masked_to_shell_exit_zero(self) -> None:
        # PR #93 の PR 後レビュー（PR後-3、独立-5・独立-6・PR後-2に続く同種の
        # fail-open 指摘）: except SystemExit ハンドラが `error.code` を読み、
        # `code if code != 0 else 1` で 0 だけを 1 に変換していた。しかし
        # `SystemExit(256)`（256 の倍数）は POSIX のシェル終了コードマスク
        # （`exit_code & 0xFF`）でシェル側の実終了コードが 0 になるため、
        # `code != 0` の判定を通過してそのまま `sys.exit(256)` に渡り、結局
        # シェル rc=0 で静かに成功してしまう（VERDICT 行は出ない）。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        write(
            self.plugin / "scripts" / "lib" / "repository_identity.py",
            "import sys\n\n\ndef repository_identity(base, marketplace_name):\n    sys.exit(256)\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: OK", result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: SKIP", result.stdout)

    def test_identity_function_call_raising_systemexit_512_is_not_masked_to_shell_exit_zero(self) -> None:
        # PR #93 マージ直前に届いた指摘1（test-power）: 上の 256 テストは値を
        # 1 つしか固定しないため、「256 という特定値だけを特別扱いする」狭い
        # 実装変異（例: `except SystemExit as exc: ... exc.code ...` への
        # リネーム）を見逃しうる。独立レビューは `SystemExit(512)`（256の別の
        # 倍数）で rc=0・VERDICT なしが復活することを確認したと報告している。
        # 256 と異なる倍数でも同じ経路が閉じていることを別途固定する。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-a.md", fragment())
        commit_all(self.repo, "change")
        write(
            self.plugin / "scripts" / "lib" / "repository_identity.py",
            "import sys\n\n\ndef repository_identity(base, marketplace_name):\n    sys.exit(512)\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: OK", result.stdout)
        self.assertNotIn("VERDICT: version-not-consumed: SKIP", result.stdout)
        # PR #93 マージ直前に届いた指摘2（product、origin: pre-existing）:
        # except SystemExit 経路は fail-closed だが診断メッセージ（FAIL: 行）
        # が無く、直接実行時になぜ失敗したか分からない。error.code は読まず、
        # 固定文言で理由を出す（review-log-present.sh と対称に適用する）。
        self.assertIn("FAIL: version-not-consumed: run() ended via SystemExit without returning a verdict", result.stdout)

    def test_file_that_release_would_not_collect_does_not_count(self) -> None:
        """書式検査も集約もされないファイル（ドットファイル・サブディレクトリ）で断片の要求を満たせない。"""
        for name in (".20260912-x.md", "sub/20260912-x.md", ".hidden/anything.md"):
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                plugin = init_repo(repo)
                git(repo, "switch", "-q", "-c", "feat")
                write(plugin / "skills" / "a.md", "changed\n")
                write(plugin / "changelog.d" / name, fragment())
                commit_all(repo, "change")
                result = run_check(plugin)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("no changelog fragment", result.stdout)

    def test_fragment_similar_to_a_deleted_one_counts_as_added(self) -> None:
        """git のリネーム・コピー検出で、足した断片が「追加」から外れない（`--no-renames` を固定する）。
        消した断片は、merge-base の断片の削除として別に FAIL になる。"""
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        (self.plugin / "changelog.d" / "20260911-old.md").unlink()
        write(self.plugin / "changelog.d" / "20260912-new.md", fragment(summary="- 要約（新）"))
        commit_all(self.repo, "replace")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("20260911-old.md", result.stdout)
        self.assertNotIn("no changelog fragment", result.stdout)

    def test_fragment_of_another_pr_renamed_and_committed_does_not_count_as_added(self) -> None:
        """merge-base の断片を中身を変えずに改名して commit しただけでは、断片を足したことにならない。"""
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        self.assertEqual(
            git(self.repo, "mv", str(self.plugin / "changelog.d" / "20260911-old.md"), str(self.plugin / "changelog.d" / "20260912-new.md")).returncode,
            0,
        )
        commit_all(self.repo, "rename another PR's fragment")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)
        self.assertIn("Not counted (same content as a fragment at the merge-base", result.stdout)
        self.assertIn("20260912-new.md", result.stdout)

    def test_fragment_counts_when_the_repo_sets_diff_relative(self) -> None:
        """利用者の git 設定（diff.relative=true）で、足した断片のパスが変わって数え落とさない。"""
        self.assertEqual(git(self.repo, "config", "diff.relative", "true").returncode, 0)
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-own.md", fragment())
        commit_all(self.repo, "change with fragment")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1 fragment(s) added", result.stdout)

    def test_own_fragment_still_counts_when_another_pr_fragment_is_renamed(self) -> None:
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        self.assertEqual(
            git(self.repo, "mv", str(self.plugin / "changelog.d" / "20260911-old.md"), str(self.plugin / "changelog.d" / "20260912-new.md")).returncode,
            0,
        )
        write(self.plugin / "changelog.d" / "20260912-own.md", fragment(summary="- 自分の変更"))
        commit_all(self.repo, "rename and add own")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1 fragment(s) added", result.stdout)

    def test_own_fragment_with_the_same_content_as_a_renamed_one_counts_once(self) -> None:
        """改名で外すのは、元の場所から消えた断片の個数の分だけ。"""
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        self.assertEqual(
            git(self.repo, "mv", str(self.plugin / "changelog.d" / "20260911-old.md"), str(self.plugin / "changelog.d" / "20260912-new.md")).returncode,
            0,
        )
        write(self.plugin / "changelog.d" / "20260912-own.md", fragment())
        commit_all(self.repo, "rename and add own with the same content")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1 fragment(s) added", result.stdout)

    def test_fragment_removed_since_merge_base_fails(self) -> None:
        """merge-base にあった別の断片を消して自分の断片だけ足しても、削除は素通りしない。"""
        write(
            self.plugin / "changelog.d" / "20260911-old.md",
            fragment("breaking", extra="#### Breaking Contract Changes\n\n- 破壊的変更\n\n"),
        )
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        (self.plugin / "changelog.d" / "20260911-old.md").unlink()
        write(self.plugin / "changelog.d" / "20260912-new.md", fragment("patch", summary="- 別の要約"))
        commit_all(self.repo, "drop existing fragment, add unrelated one")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("20260911-old.md", result.stdout)

    def test_fragment_rewritten_since_merge_base_fails(self) -> None:
        """merge-base にあった断片の中身だけ書き換えても、書き換えは素通りしない。"""
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment("patch", summary="- 元の要約"))
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        write(self.plugin / "changelog.d" / "20260911-old.md", fragment("patch", summary="- 書き換えた要約"))
        write(self.plugin / "changelog.d" / "20260912-new.md", fragment("patch", summary="- 追加の要約"))
        commit_all(self.repo, "rewrite existing fragment, add another")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("20260911-old.md", result.stdout)

    def test_duplicate_content_fragment_removed_since_merge_base_fails(self) -> None:
        """merge-base に同じ内容の断片が 2 件あっても、1 件だけ消せば検出する
        （blob の集合ではなく個数で比べるので、別ファイルの同じ内容に隠れて素通りしない）。"""
        write(self.plugin / "changelog.d" / "20260911-a.md", fragment("patch", summary="- 同じ要約"))
        write(self.plugin / "changelog.d" / "20260911-b.md", fragment("patch", summary="- 同じ要約"))
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        (self.plugin / "changelog.d" / "20260911-a.md").unlink()
        write(self.plugin / "changelog.d" / "20260912-new.md", fragment("patch", summary="- 別の要約"))
        commit_all(self.repo, "drop one of the duplicate fragments, add unrelated one")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("20260911-a.md", result.stdout)

    def test_open_pr_stays_ok_after_a_release_lands_on_main(self) -> None:
        """統合先が先にリリースしても、版数に触れていない PR に main の取り込みを強いない。"""
        write(self.plugin / "changelog.d" / "20260911-m.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        write(self.plugin / "changelog.d" / "20260912-f.md", fragment())
        commit_all(self.repo, "change")
        git(self.repo, "switch", "-q", "main")
        applied = run_release(self.plugin, "--apply", "--date", "2026-09-12")
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        commit_all(self.repo, "release 0.43.1")
        git(self.repo, "switch", "-q", "feat")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_release_branch_missing_a_later_main_fragment_fails(self) -> None:
        """リリース分岐後に main へ別の断片が積まれたら、それを取り込まないリリース分岐は通らない。"""
        write(self.plugin / "changelog.d" / "20260911-m.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("release")
        applied = run_release(self.plugin, "--apply", "--date", "2026-09-12")
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        commit_all(self.repo, "release 0.44.0")
        git(self.repo, "switch", "-q", "main")
        write(self.plugin / "changelog.d" / "20260912-later.md", fragment())
        commit_all(self.repo, "later PR merged onto main")
        git(self.repo, "switch", "-q", "release")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("does not include the latest", result.stdout)

    def test_release_that_reuses_the_version_on_main_fails(self) -> None:
        write(self.plugin / "changelog.d" / "20260911-m.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("release")
        self.assertEqual(run_release(self.plugin, "--apply", "--date", "2026-09-12").returncode, 0)
        commit_all(self.repo, "release 0.43.1")
        git(self.repo, "switch", "-q", "main")
        self.assertEqual(run_release(self.plugin, "--apply", "--date", "2026-09-13").returncode, 0)
        commit_all(self.repo, "another release 0.43.1")
        git(self.repo, "switch", "-q", "release")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("already", result.stdout)

    def test_release_with_the_same_tree_as_main_fails_not_skips(self) -> None:
        """統合先の tip と plugin ツリーが同じでも、分岐後に版数を上げたブランチは SKIP-B にしない。"""
        write(self.plugin / "changelog.d" / "20260911-m.md", fragment())
        commit_all(self.repo, "merged PR")
        self.branch("release")
        self.assertEqual(run_release(self.plugin, "--apply", "--date", "2026-09-12").returncode, 0)
        commit_all(self.repo, "release 0.43.1")
        git(self.repo, "switch", "-q", "main")
        self.assertEqual(run_release(self.plugin, "--apply", "--date", "2026-09-12").returncode, 0)
        commit_all(self.repo, "same release 0.43.1 on main")
        git(self.repo, "switch", "-q", "release")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("already", result.stdout)

    def test_head_contained_in_ref_skips_branch_layer(self) -> None:
        write(self.plugin / "changelog.d" / "20260911-a.md", fragment())
        commit_all(self.repo, "merged PR")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("SKIP-B", result.stdout)

    def test_branch_outside_plugin_skips_after_main_changes_plugin(self) -> None:
        """plugin に触れないブランチは、分岐後に main が plugin を変えても断片を求められない（PR #269）。"""
        self.branch("feat")
        write(self.repo / "other" / "x.md", "x\n")
        commit_all(self.repo, "outside plugin")
        git(self.repo, "switch", "-q", "main")
        write(self.plugin / "skills" / "b.md", "main changed\n")
        write(self.plugin / "changelog.d" / "20260911-m.md", fragment())
        commit_all(self.repo, "merged PR on main")
        git(self.repo, "switch", "-q", "feat")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("SKIP-B", result.stdout)
        self.assertIn("plugin tree is unchanged since the merge-base", result.stdout)

    def test_branch_that_merged_main_without_touching_plugin_skips(self) -> None:
        self.branch("feat")
        write(self.repo / "other" / "x.md", "x\n")
        commit_all(self.repo, "outside plugin")
        git(self.repo, "switch", "-q", "main")
        write(self.plugin / "skills" / "b.md", "main changed\n")
        commit_all(self.repo, "merged PR on main")
        git(self.repo, "switch", "-q", "feat")
        self.assertEqual(git(self.repo, "merge", "-q", "--no-edit", "main").returncode, 0)
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("SKIP-B", result.stdout)
        self.assertIn("plugin tree is unchanged since the merge-base", result.stdout)

    def test_branch_changing_plugin_without_fragment_fails_after_main_changes_plugin(self) -> None:
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        git(self.repo, "switch", "-q", "main")
        write(self.plugin / "skills" / "b.md", "main changed\n")
        commit_all(self.repo, "merged PR on main")
        git(self.repo, "switch", "-q", "feat")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)

    def test_branch_changing_plugin_without_fragment_fails_after_merging_main(self) -> None:
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        git(self.repo, "switch", "-q", "main")
        write(self.plugin / "skills" / "b.md", "main changed\n")
        commit_all(self.repo, "merged PR on main")
        git(self.repo, "switch", "-q", "feat")
        self.assertEqual(git(self.repo, "merge", "-q", "--no-edit", "main").returncode, 0)
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("no changelog fragment", result.stdout)

    def test_ref_without_merge_base_fails_not_skips(self) -> None:
        """統合先と共通の祖先が無い（判定できない）ときは、SKIP-B にせず FAIL にする。"""
        self.assertEqual(git(self.repo, "checkout", "-q", "--orphan", "other").returncode, 0)
        commit_all(self.repo, "unrelated history")
        result = run_check(self.plugin, ref="main")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertNotIn("SKIP-B", result.stdout)
        self.assertIn("cannot find the merge-base", result.stdout)

    def test_git_dir_env_var_does_not_cause_false_skip_b(self) -> None:
        # sibling の review-log-present.sh の H2' 対応と揃える（2026-09-15、
        # Opus へのセカンドオピニオンに基づき両スクリプトへ同時適用）: GIT_DIR 等の
        # GIT_* 環境変数が子プロセスにそのまま継承されると、実際には通常の
        # checkout であるにもかかわらず `git -C <root>` が別のリポジトリを見て
        # 失敗し、「判定できない」を「消費者環境」と誤認して SKIP-B になり、断片
        # チェック自体が素通りしてしまう。全 git 呼び出しから GIT_* を除去して
        # 修正した。
        self.branch("feat")
        write(self.plugin / "skills" / "a.md", "changed\n")
        commit_all(self.repo, "change")
        env = {
            **GIT_ENV,
            "ROOT": str(self.plugin),
            "PYTHON_BIN": sys.executable,
            "GDD_INTEGRATION_REF": "main",
            "GIT_DIR": "/nonexistent/x.git",
            "HOME": os.devnull,
            "XDG_CONFIG_HOME": os.devnull,
        }
        result = subprocess.run(
            ["bash", str(self.plugin / "tests" / "checks" / "version-not-consumed.sh")],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("SKIP-B", result.stdout)
        self.assertIn("no changelog fragment", result.stdout)

    def test_missing_marketplace_json_skips_b(self) -> None:
        # sibling の review-log-present.sh と揃える（2026-09-15、H4 対応）:
        # `.claude-plugin/marketplace.json` が無いディレクトリは「本リポジトリ
        # ではない」として SKIP-B にする。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "a" / "b"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            result = run_check(fake_plugin)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_corrupted_marketplace_json_fails_not_skips(self) -> None:
        # 判定不能を「無い」と誤認しない（H4 対応で identity marker に転換した
        # 後も維持すべき性質）: manifest が存在するのに JSON として壊れていて
        # `name` を読めない場合は SKIP にせず FAIL にする。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            write(outside / ".claude-plugin" / "marketplace.json", "{not valid json\n")
            result = run_check(fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
            self.assertIn("cannot parse", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_marketplace_json_name_type_space_fails_not_skips(self) -> None:
        # sibling の review-log-present.sh と揃える（2026-09-15、H5 対応）:
        # `name` は marketplace の主キーであり、これを欠く manifest は「別の
        # marketplace」ではなくインストール不能な壊れた manifest である。H4
        # 時点の実装は `.get("name") == MARKETPLACE_NAME` の等価比較だけに
        # 頼っており、`name` キー欠落・null・非文字列・空文字列がいずれも
        # 例外を投げずに False（SKIP-B）に落ちていた。
        cases = {
            "missing key": "{}",
            "null": '{"name": null}',
            "int": '{"name": 123}',
            "bool": '{"name": true}',
            "array": '{"name": ["gate-driven-development"]}',
            "object": '{"name": {"v": "gate-driven-development"}}',
            "empty string": '{"name": ""}',
            "top-level array": '["gate-driven-development"]',
        }
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            manifest = outside / ".claude-plugin" / "marketplace.json"
            for label, text in cases.items():
                with self.subTest(label):
                    write(manifest, text)
                    result = run_check(fake_plugin)
                    self.assertNotEqual(result.returncode, 0, f"{label}: {result.stdout + result.stderr}")
                    self.assertNotIn("SKIP-B", result.stdout, f"{label}: {result.stdout}")
                    self.assertNotIn("Traceback", result.stderr, f"{label}: {result.stderr}")
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_marketplace_json_as_directory_fails_not_skips(self) -> None:
        # H5 と同じ「読めないものを『無い』にしない」観点: manifest という名前
        # のパスがディレクトリの場合、`is_file()` は False を返すが、これは
        # 「manifest が無い」とは異なる（読めない）。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            manifest = outside / ".claude-plugin" / "marketplace.json"
            manifest.mkdir(parents=True)
            result = run_check(fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_marketplace_json_broken_symlink_fails_not_skips(self) -> None:
        # H3 の変異が identity marker 方式にも形を変えて残っていないかの回帰:
        # marketplace.json 自体が壊れた symlink の場合、`is_file()` は False を
        # 返すが、これも「manifest が無い」ではない。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            manifest = outside / ".claude-plugin" / "marketplace.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.symlink_to(outside / "nonexistent-target")
            result = run_check(fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_claude_plugin_holder_broken_fails_not_skips(self) -> None:
        # sibling の review-log-present.sh と揃える（2026-09-15、H6 対応、
        # Cursor/Grok レビュー指摘・high・fail-open、実機で再現）: H5 対応は
        # leaf（marketplace.json 自体）の異常だけを見ており、親（`.claude-plugin`）
        # 自体が壊れた symlink・symlink loop・通常ファイル・（root 以外では）
        # 権限拒否ディレクトリの場合を見ていなかった。この場合 `is_file()/
        # is_symlink()/exists()` は全て False を返すため「manifest が無い」＝
        # False（SKIP-B）に落ちる。権限拒否のケースは、正しい name の manifest
        # が実在する本物の開発 checkout でも検査全体が黙ってスキップされる。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            holder = outside / ".claude-plugin"

            def reset_holder() -> None:
                if holder.is_symlink() or holder.exists():
                    if holder.is_dir() and not holder.is_symlink():
                        os.chmod(holder, 0o755)
                        shutil.rmtree(holder)
                    else:
                        holder.unlink()

            cases = ["broken symlink", "regular file", "symlink loop"]
            if os.geteuid() != 0:
                cases.append("permission denied dir")
            for label in cases:
                with self.subTest(label):
                    reset_holder()
                    if label == "broken symlink":
                        holder.symlink_to(outside / "nonexistent-target")
                    elif label == "regular file":
                        holder.write_text("not a directory")
                    elif label == "symlink loop":
                        holder.symlink_to(holder)
                    elif label == "permission denied dir":
                        write_marketplace_json(outside)
                        os.chmod(holder, 0o000)
                    try:
                        result = run_check(fake_plugin)
                        self.assertNotEqual(result.returncode, 0, f"{label}: {result.stdout + result.stderr}")
                        self.assertNotIn("SKIP-B", result.stdout, f"{label}: {result.stdout}")
                        self.assertNotIn("Traceback", result.stderr, f"{label}: {result.stderr}")
                    finally:
                        if label == "permission denied dir":
                            os.chmod(holder, 0o755)
            reset_holder()
        finally:
            if (outside / ".claude-plugin").exists():
                os.chmod(outside / ".claude-plugin", 0o755)
            shutil.rmtree(outside, ignore_errors=True)

    def test_claude_plugin_dir_without_marketplace_json_still_skips_b(self) -> None:
        # H6 修正の逆方向ガード（sibling の review-log-present.sh と揃える）:
        # `.claude-plugin` が実在する通常のディレクトリだが `marketplace.json`
        # を持たない（単体 plugin リポジトリの実際のレイアウト、例:
        # `.claude-plugin/plugin.json` のみ）場合は、これまで通り SKIP-B の
        # ままでなければならない。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            write(outside / ".claude-plugin" / "plugin.json", json.dumps({"name": "some-single-plugin"}))
            result = run_check(fake_plugin)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_dangling_git_symlink_in_identity_confirmed_checkout_fails_not_skips(self) -> None:
        # Codex レビュー指摘クラスタ（H2→H2'→H3→H4・high・fail-open）を sibling の
        # review-log-present.sh と同時に踏まえた対応: `.claude-plugin/marketplace.json`
        # の name が本リポジトリと一致して identity が確定しているのに、`.git`
        # が壊れた symlink のせいで git 呼び出し自体が失敗する場合、「消費者環境
        # で git work tree ではない」とは区別できないため SKIP にせず FAIL にする。
        outside = Path(tempfile.mkdtemp())
        try:
            write_marketplace_json(outside)
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            (outside / ".git").symlink_to(outside / "nonexistent-target.git")
            result = run_check(fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_symlinked_root_with_different_basename_does_not_cause_false_skip_b(self) -> None:
        # Codex レビュー指摘（H4・high・fail-open、実機で再現）: 直前の設計
        # （root が <repo_root>/plugins/<root の名前> というディレクトリ
        # レイアウトと一致するかどうか）は、root が別名の symlink（例: plugin
        # cache のバージョン番号ディレクトリ `.../gate-driven-development/0.44.0`
        # → 実体は `<repo_root>/plugins/gate-driven-development`）経由だと
        # basename が一致せず、真の開発 checkout でも SKIP-B になり版数チェック
        # が素通りしていた（このマシンの実際の plugin cache
        # `~/.claude/plugins/cache/*/gate-driven-development/<version>/` で
        # 再現確認済み）。identity marker は root の basename を一切見ないため、
        # この変異は構造的に再発しない。
        outside = Path(tempfile.mkdtemp())
        try:
            git(outside, "init", "-q", "-b", "main")
            write_marketplace_json(outside)
            real_plugin = outside / "plugins" / "gate-driven-development"
            make_plugin(real_plugin)
            commit_all(outside, "base")
            git(outside, "switch", "-q", "-c", "feat")
            write(real_plugin / "skills" / "a.md", "changed\n")
            commit_all(outside, "change without a fragment")
            symlinked_root = outside / "cache" / "versions" / "0.44.0"
            symlinked_root.parent.mkdir(parents=True, exist_ok=True)
            symlinked_root.symlink_to(real_plugin)
            result = run_check(symlinked_root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
            self.assertIn("no changelog fragment", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_layout_match_does_not_skip_ambiguity_when_marketplace_name_differs(self) -> None:
        # Opus へのセカンドオピニオンで実機発見された逆方向の実害: レイアウトが
        # <repo_root>/plugins/<name> と一致していても、marketplace.json の name
        # が本リポジトリと異なる（本物の消費者環境・別リポジトリの marketplace
        # clone）なら SKIP-B にする（統合先 ref が解決できないことによる誤 FAIL
        # を避ける。実機の `~/.claude/plugins/marketplaces/*/plugins/*` で
        # 複数件実測確認）。
        outside = Path(tempfile.mkdtemp())
        try:
            git(outside, "init", "-q", "-b", "main")
            write_marketplace_json(outside, name="some-other-marketplace")
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            commit_all(outside, "base")
            # main に直接積むと HEAD が ref 自身になり、"HEAD is contained in
            # ref" という別の SKIP-B 理由で偶然パスしてしまう（層 A のみ enforced
            # という別経路）。identity 不一致による SKIP-B を検証するには、ref
            # より先に進んだブランチが必要。
            git(outside, "switch", "-q", "-c", "feat")
            write(fake_plugin / "changelog.d" / "20260915-x.md", fragment())
            commit_all(outside, "unrelated repo with a plugin-shaped subtree")
            result = run_check(fake_plugin)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP-B", result.stdout)
            self.assertIn("does not look like a checkout of", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_unreadable_manifest_on_ref_fails(self) -> None:
        for label, text in {"null": '{"version": null}\n', "invalid json": "{\n"}.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                plugin = init_repo(repo)
                write(plugin / MANIFESTS[0], text)
                commit_all(repo, "broken main")
                git(repo, "switch", "-q", "-c", "feat")
                write(plugin / MANIFESTS[0], json.dumps({"name": "gdd", "version": "0.43.0"}, indent=2) + "\n")
                write(plugin / "changelog.d" / "20260912-a.md", fragment())
                commit_all(repo, "fix")
                result = run_check(plugin)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("FAIL: version-not-consumed", result.stdout)
                self.assertIn("at main", result.stdout)

    def test_manifest_version_type_space_fails(self) -> None:
        """manifest の `version` が semver 文字列以外なら、どの JSON 型でも FAIL（無言 PASS にしない）。"""
        cases = {
            "null": '{"version": null}',
            "int": '{"version": 1}',
            "float": '{"version": 0.43}',
            "bool": '{"version": true}',
            "array": '{"version": ["0.43.0"]}',
            "object": '{"version": {"v": "0.43.0"}}',
            "empty string": '{"version": ""}',
            "non semver": '{"version": "0.43"}',
            "missing key": '{"name": "gdd"}',
            "top-level array": '["0.43.0"]',
            "invalid json": "{",
            "empty file": "",
        }
        with tempfile.TemporaryDirectory() as tmp:
            plugin = make_plugin(Path(tmp))
            path = plugin / MANIFESTS[0]
            for label, text in cases.items():
                with self.subTest(label):
                    path.write_text(text, encoding="utf-8")
                    result = run_check(plugin)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn("FAIL: version-not-consumed", result.stdout)
                    self.assertNotIn("Traceback", result.stderr)
            with self.subTest("non utf-8"):
                path.write_bytes(b'{"version": "\xff"}')
                result = run_check(plugin)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertNotIn("Traceback", result.stderr)
            with self.subTest("file absent"):
                path.unlink()
                result = run_check(plugin)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertNotIn("Traceback", result.stderr)


class ParallelPullRequestTests(unittest.TestCase):
    """2 本の PR がそれぞれ断片を 1 つ足しても、版数系のファイルで衝突しない。"""

    def test_two_branches_with_one_fragment_each_merge_without_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plugin = init_repo(repo)

            for name, source in (("a", "skills/a.md"), ("b", "skills/b.md")):
                self.assertEqual(git(repo, "switch", "-q", "-c", f"pr-{name}", "main").returncode, 0)
                write(plugin / source, f"changed by {name}\n")
                write(plugin / "changelog.d" / f"20260912-{name}.md", fragment())
                commit_all(repo, f"pr {name}")
                check = run_check(plugin)
                self.assertEqual(check.returncode, 0, check.stdout)
                git(repo, "switch", "-q", "main")

            git(repo, "switch", "-q", "main")
            for name in ("a", "b"):
                merged = git(repo, "merge", "--no-ff", "-q", "-m", f"merge pr-{name}", f"pr-{name}")
                self.assertEqual(merged.returncode, 0, merged.stdout + merged.stderr)

            self.assertEqual(sorted(p.name for p in (plugin / "changelog.d").glob("*.md")), ["20260912-a.md", "20260912-b.md"])
            for manifest in MANIFESTS:
                self.assertEqual(json.loads((plugin / manifest).read_text(encoding="utf-8"))["version"], "0.43.0")
            check = run_check(plugin)
            self.assertEqual(check.returncode, 0, check.stdout)


if __name__ == "__main__":
    unittest.main()
