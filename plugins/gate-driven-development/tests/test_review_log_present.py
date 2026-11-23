"""軽いレーンの指摘記録（`review-log/`）を強制する `tests/checks/review-log-present.sh` の契約テスト。

固定するもの:
- `changelog.d/` に断片があるのに対の `review-log/<同じファイル名>` が無い、または書式が不正なら FAIL
- 対象は「このブランチが統合先との merge-base 以降に足した断片」だけ（既存の断片は対象外）
- 統合先 ref が解決できない場合は SKIP ではなく FAIL（fail-closed。sibling の
  version-not-consumed.sh とは異なる。理由は review-log-present.sh 本体のコメント参照）
- repo root が本リポジトリ（`.claude-plugin/marketplace.json` の `name` が
  `gate-driven-development` と一致）でない場合は SKIP-B（name 不一致・manifest
  欠落）。manifest が壊れていて `name` を読めない場合は判定不能として FAIL
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

import pytest

from _paths import PLUGIN_ROOT, REPO_ROOT

GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
MARKETPLACE_NAME = "gate-driven-development"


def write_marketplace_json(repo_root: Path, name: str = MARKETPLACE_NAME) -> None:
    write(repo_root / ".claude-plugin" / "marketplace.json", json.dumps({"name": name}) + "\n")

VERSIONING = """# VERSIONING

## リリース手順

- **統合先の定義**: `origin/main`（`GDD_INTEGRATION_REF` で上書き可）
"""

VERSIONING_NO_REF = """# VERSIONING

## リリース手順

本文書には統合先の定義を書いていない。
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fragment(name: str = "20260914-x.md") -> str:
    return (
        "---\ntype: patch\n---\n\n"
        "#### Summary\n\n- 要約\n\n"
        "#### Affected Files\n\n- `skills/a.md`\n\n"
        "#### User Action Required\n\n- なし\n\n"
        "#### Validation / Eval Impact\n\n- `tests/test_review_log_present.py`\n"
    )


def review_log(
    *,
    lane: str = "L1+",
    pr: str = "82",
    jun_rows: str = "| codex-1 | codex adversarial-review | 3f2a1bc | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
    finding_rows: str = "| F1 | codex-1 | high | yes | inherited | shell-parse | fixed | 例 |\n",
) -> str:
    return (
        f"---\nlane: {lane}\npr: {pr}\n---\n\n"
        "## 巡\n\n"
        "| 巡 | reviewer | sha | high | medium | blocking | at |\n"
        "|---|---|---|---|---|---|---|\n"
        f"{jun_rows}\n"
        "## 指摘\n\n"
        "| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |\n"
        "|---|---|---|---|---|---|---|---|\n"
        f"{finding_rows}"
    )


def make_plugin(root: Path, *, versioning: str = VERSIONING) -> Path:
    write(root / "docs" / "VERSIONING.md", versioning)
    for rel in ("scripts/release.py", "scripts/lib/repository_identity.py", "tests/checks/review-log-present.sh"):
        src = PLUGIN_ROOT / rel
        if not src.exists():
            continue
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, root / rel)
    return root


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


def run_check(plugin_root: Path, ref: str = "main", root_override: Path | None = None) -> subprocess.CompletedProcess:
    env = {
        **GIT_ENV,
        "ROOT": str(root_override or plugin_root),
        "PYTHON_BIN": sys.executable,
        "GDD_INTEGRATION_REF": ref,
    }
    return subprocess.run(
        ["bash", str(plugin_root / "tests" / "checks" / "review-log-present.sh")],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class ReviewLogPresentTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q", "-b", "main")
        write_marketplace_json(self.repo)
        self.plugin = make_plugin(self.repo / "plugins" / "gdd")
        commit_all(self.repo, "base")
        # main から分岐した feature ブランチで作業する（main に直接積むと
        # merge-base(main, HEAD) が HEAD 自身になり「新規に足した断片」が
        # 常に空集合になってしまう）。
        result = git(self.repo, "checkout", "-q", "-b", "feature")
        assert result.returncode == 0, result.stderr

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def add_fragment_and_commit(self, name: str, message: str = "add fragment") -> None:
        write(self.plugin / "changelog.d" / name, fragment(name))
        commit_all(self.repo, message)

    def test_pre_existing_fragment_without_review_log_still_passes(self) -> None:
        # 既存（このブランチが main から分岐する前からある）断片は対象外。
        result = git(self.repo, "checkout", "-q", "main")
        assert result.returncode == 0, result.stderr
        write(self.plugin / "changelog.d" / "20260901-old.md", fragment("20260901-old.md"))
        commit_all(self.repo, "pre-existing fragment on main")
        result = git(self.repo, "checkout", "-q", "feature")
        assert result.returncode == 0, result.stderr
        result = git(self.repo, "merge", "-q", "--ff-only", "main")
        assert result.returncode == 0, result.stderr
        # feature 側でも別の変更を積み、実際に分岐した状態で検査する。
        write(self.plugin / "skills" / "unrelated.md", "unrelated\n")
        commit_all(self.repo, "unrelated feature work")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)

    def test_new_fragment_without_review_log_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review-log/20260914-x.md", result.stdout)
        self.assertIn("is missing", result.stdout)

    def test_ordinary_validation_failure_is_not_misdiagnosed_as_dynamic_module_load(self) -> None:
        # Codex レビュー指摘（medium）: die() は通常の入力検証失敗（review-log
        # 欠落・書式不正等）でも SystemExit(1) を送出するため、呼び出し元の
        # except SystemExit ハンドラが動的ロードしたモジュール由来かどうかを
        # 区別しないまま固定文言を出すと、最も一般的な失敗経路（die() 経由）
        # にまで「動的モジュールロード中の異常」という誤った原因を付加して
        # しまう。die() 経由の通常失敗では、この診断文言（"dynamic module
        # load"）が出ないことを固定する。独立レビュー指摘（独立-1・F6・
        # medium）: この否定検査だけでは「文言を言い換えれば通る」列挙型
        # だったため、die() 経路でも新しい固定文言全体が出力に含まれることを
        # 積極的に確認する肯定検査を追加する（主張そのものを測る）。
        self.add_fragment_and_commit("20260914-x.md")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("dynamic module load", result.stdout)
        self.assertIn("FAIL: review-log-present: run() ended via SystemExit without returning a verdict", result.stdout)

    def test_new_fragment_with_valid_review_log_passes(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_follow_up_of_key_is_accepted_with_accepted_low(self) -> None:
        # 後続 PR の宣言（root CLAUDE.md 手順 1 の `follow_up_of:`）と、その PR で ① の非 blocking の low を
        # `accepted` にした行が、検査を通ること（宣言を書いた review-log が検査で落ちると、規定が使えない）
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            lane="L1",
            jun_rows=(
                "| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n"
            ),
            finding_rows=(
                "| F1 | 独立-1 | low | no | self-inflicted | test-power | accepted | 後続 PR なので限界の節に書いた |\n"
            ),
        ).replace("pr: 82\n", "pr: 82\nfollow_up_of: 204\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_lane_key_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log().replace("lane: L1+\n", "")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lane", result.stdout)

    def test_invalid_lane_value_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log(lane="L2"))
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lane", result.stdout)

    def test_missing_pr_key_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log().replace("pr: 82\n", "")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pr", result.stdout)

    def test_empty_pr_value_is_allowed(self) -> None:
        # pr 番号は PR 作成後（push 後）に埋まるため、値が空でもキーさえあれば通す。
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log(pr=""))
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_jun_section_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log()
        text = text.replace("## 巡\n\n", "").split("## 指摘")[0] + "## 指摘" + text.split("## 指摘")[1]
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("## 巡", result.stdout)

    def test_missing_finding_section_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log().split("## 指摘")[0]
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("## 指摘", result.stdout)

    def test_jun_label_missing_from_findings_fails(self) -> None:
        # 巡テーブルに codex-2 があるのに、指摘テーブルに codex-2 の行（なし含む）が無い。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows=(
                "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n"
                "| codex-2 | codex adversarial-review | 9c4e7d0 | 0 | 0 | 0 | 2026-09-14T11:00+09:00 |\n"
            ),
            finding_rows="| F1 | codex-1 | - | - | - | - | - | なし |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("codex-2", result.stdout)

    def test_finding_references_undeclared_jun_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | 独立-9 | high | yes | inherited | shell-parse | fixed | 例 |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("独立-9", result.stdout)

    def test_invalid_severity_value_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | codex-1 | hgih | yes | inherited | shell-parse | fixed | 例 |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("severity", result.stdout)

    def test_duplicate_finding_id_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            finding_rows=(
                "| F1 | codex-1 | high | yes | inherited | shell-parse | fixed | 例1 |\n"
                "| F1 | codex-1 | medium | no | inherited | doc | deferred | 例2 |\n"
            )
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicated", result.stdout)

    def test_nashi_row_with_non_dash_columns_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | codex-1 | high | - | - | - | - | なし |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("なし", result.stdout)

    def test_unresolvable_integration_ref_fails_not_skips(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        result = run_check(self.plugin, ref="origin/does-not-exist")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("SKIP", result.stdout)
        self.assertIn("not resolvable", result.stdout)

    def test_no_declared_ref_and_no_env_fails(self) -> None:
        make_plugin(self.repo / "plugins" / "gdd", versioning=VERSIONING_NO_REF)
        commit_all(self.repo, "drop declared ref")
        self.add_fragment_and_commit("20260914-y.md")
        env = {**GIT_ENV, "ROOT": str(self.plugin), "PYTHON_BIN": sys.executable}
        result = subprocess.run(
            ["bash", str(self.plugin / "tests" / "checks" / "review-log-present.sh")],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no integration ref declared", result.stdout)

    def test_missing_marketplace_json_skips_b(self) -> None:
        # Codex レビュー指摘（H2・high・product）: ONBOARDING.md の手順3「Plugin の
        # 自己検証を走らせる」は plugin 配布先（消費者環境）でも validate-plugin.sh
        # の実行を明記している。plugin cache 配置等では repo root が本リポジトリの
        # checkout ではないことがあり、これを FAIL で die() すると誤 block で
        # validate-plugin.sh 全体（他の全 BLOCK チェック）まで止めてしまう（実害）。
        # sibling の version-not-consumed.sh の SKIP-B と揃え、判定不能を
        # 「無い」と誤認しない形で SKIP にする。
        #
        # 2026-09-15（H4 対応）: SKIP-B の判定は `.claude-plugin/marketplace.json`
        # の `name` フィールドの自己申告だけで行う（git 呼び出し・ディレクトリ
        # レイアウトのどちらにも依存しない）。manifest 自体が無ければ「本リポジトリ
        # ではない」と判定して SKIP-B にする。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "a" / "b"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_corrupted_marketplace_json_fails_not_skips(self) -> None:
        # fail-open の3ケースのうち「判定できないときに通ってしまう」ケース:
        # manifest が存在するのに JSON として壊れていて `name` を読めない場合、
        # 「本リポジトリではない」と推測せず FAIL にする（H4 対応で identity
        # marker に転換した後も維持すべき性質）。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            write(outside / ".claude-plugin" / "marketplace.json", "{not valid json\n")
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
            self.assertIn("cannot parse", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_marketplace_json_name_type_space_fails_not_skips(self) -> None:
        # Codex レビュー指摘（H5・high・fail-open、実機で再現）: `name` は
        # marketplace の主キーであり（`known_marketplaces.json` のキー、
        # `~/.claude/plugins/marketplaces/<name>/` のディレクトリ名がこの値と
        # 一致する）、これを欠く manifest は「別の marketplace」ではなく
        # インストール不能な壊れた manifest である。しかし H4 時点の実装は
        # `.get("name") == MARKETPLACE_NAME` の等価比較だけに頼っており、
        # `name` キー欠落・null・非文字列・空文字列がいずれも例外を投げずに
        # False（別リポジトリ・SKIP-B）に落ちていた。sibling の
        # version-not-consumed.sh が `version` フィールドで既に確立している
        # 「JSON の型空間で洗う」規律（`test_manifest_version_type_space_fails`
        # 参照）を、`repository_identity()` にも適用する。
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
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            manifest = outside / ".claude-plugin" / "marketplace.json"
            for label, text in cases.items():
                with self.subTest(label):
                    write(manifest, text)
                    result = run_check(self.plugin, root_override=fake_plugin)
                    self.assertNotEqual(result.returncode, 0, f"{label}: {result.stdout + result.stderr}")
                    self.assertNotIn("SKIP-B", result.stdout, f"{label}: {result.stdout}")
                    self.assertNotIn("Traceback", result.stderr, f"{label}: {result.stderr}")
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_marketplace_json_as_directory_fails_not_skips(self) -> None:
        # H5 と同じ「読めないものを『無い』にしない」観点: `.claude-plugin/
        # marketplace.json` という名前のパスがディレクトリの場合、`is_file()`
        # は False を返すが、これは「manifest が無い」とは異なる（読めない）。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            manifest = outside / ".claude-plugin" / "marketplace.json"
            manifest.mkdir(parents=True)
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_marketplace_json_broken_symlink_fails_not_skips(self) -> None:
        # H3 の変異が identity marker 方式にも形を変えて残っていないかの回帰:
        # `.claude-plugin/marketplace.json` 自体が壊れた symlink の場合、
        # `is_file()` は False を返すが、これも「manifest が無い」ではない。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            manifest = outside / ".claude-plugin" / "marketplace.json"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.symlink_to(outside / "nonexistent-target")
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_claude_plugin_holder_broken_fails_not_skips(self) -> None:
        # Cursor/Grok レビュー指摘（H6・high・fail-open、実機で再現）: H5 対応は
        # leaf（marketplace.json 自体）の異常だけを `is_symlink()/exists()` で
        # None に倒していたが、親（`.claude-plugin`）自体が壊れている場合は
        # 一切見ていなかった。`.claude-plugin` が壊れた symlink・symlink loop・
        # 通常ファイル・（root 以外では）権限拒否ディレクトリの場合、
        # `manifest.is_file()/is_symlink()/exists()` は全て False を返すため
        # 「manifest が無い」＝ False（SKIP-B）に落ちていた。権限拒否のケースは
        # 特に重大で、本物の開発 checkout（正しい name の manifest が実在）で
        # あっても `.claude-plugin` の読み取り権限が無いだけで検査全体が
        # 黙ってスキップされる。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
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
                        result = run_check(self.plugin, root_override=fake_plugin)
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
        # H6 修正の逆方向ガード: `.claude-plugin` が実在する通常のディレクトリ
        # だが `marketplace.json` を持たない（単体 plugin リポジトリの実際の
        # レイアウト、例: `.claude-plugin/plugin.json` のみ）場合は、これまで
        # 通り SKIP-B のままでなければならない。H6 修正で「親が実在すれば
        # None」という誤った判定に倒すと、実機に複数実在するこの形の消費者
        # 環境を誤って FAIL させる新しい逆方向の穴になる。
        outside = Path(tempfile.mkdtemp())
        try:
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            write(outside / ".claude-plugin" / "plugin.json", json.dumps({"name": "some-single-plugin"}))
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_multiple_new_fragments_each_checked_independently(self) -> None:
        self.add_fragment_and_commit("20260914-a.md")
        self.add_fragment_and_commit("20260914-b.md")
        write(self.repo / "review-log" / "20260914-a.md", review_log())
        # 20260914-b.md には review-log を作らない。
        commit_all(self.repo, "add review-log for a only")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("20260914-b.md", result.stdout)
        self.assertNotIn("review-log/20260914-a.md is missing", result.stdout)

    def test_fenced_example_table_is_not_mistaken_for_the_real_table(self) -> None:
        # 独立レビュー指摘（high・fail-open、当時の実装）: parse_table が見出しと
        # 完全一致する最初の行を無条件に採用していたため、frontmatter 直後に
        # 「書式の例」をコードフェンスで貼るだけで、その例（正しい書式）が検証
        # 対象として採用され、以降にある実際の記録（不正な内容）が一切チェック
        # されなかった。
        #
        # 2026-09-14 時点の現在の実装は、コードフェンスの内外を判定する仕組み
        # 自体を持たない（H1' 対応でホワイトリスト方式に変更。review-log-present.sh
        # の split_sections 参照）。body は空行と `## 巡`/`## 指摘` の見出し配下
        # だけを受理し、それ以外の内容（この「例:」という説明文を含む）は見出しの
        # 前に置かれた時点で即座に FAIL になる。過去の回避手口が形を変えても
        # 通用しないことを固定する回帰テストとして残す。
        self.add_fragment_and_commit("20260914-x.md")
        fenced_example = (
            "例:\n\n```markdown\n"
            "## 巡\n\n"
            "| 巡 | reviewer | sha | high | medium | blocking | at |\n"
            "|---|---|---|---|---|---|---|\n"
            "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n\n"
            "## 指摘\n\n"
            "| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| F1 | codex-1 | - | - | - | - | - | なし |\n"
            "```\n\n"
        )
        # 実際の記録は巡テーブルに codex-2 があるのに指摘テーブルに対応行が無い（FAIL すべき）。
        real_content = review_log(
            jun_rows=(
                "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n"
                "| codex-2 | codex adversarial-review | 9c4e7d0 | 1 | 0 | 0 | 2026-09-14T11:00+09:00 |\n"
            ),
            finding_rows="| F1 | codex-1 | - | - | - | - | - | なし |\n",
        )
        frontmatter, _, body = real_content.partition("\n\n")
        text = f"{frontmatter}\n\n{fenced_example}{body}"
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a fenced example before the real content")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("must contain only blank lines", result.stdout)

    def test_duplicate_heading_outside_fence_is_ambiguous(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log()
        # フェンスの外で "## 巡" を重複させる（曖昧）。
        text = text.replace("## 巡\n\n", "## 巡\n\n## 巡\n\n", 1)
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with duplicated heading")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("## 巡", result.stdout)

    def test_changelog_subdirectory_is_not_treated_as_a_top_level_fragment(self) -> None:
        # release.py の load_fragments はサブディレクトリを断片として拾わない
        # （scripts/release.py:109 相当）。review-log-present.sh も同じ受理集合に
        # 合わせ、changelog.d/ 直下ではないファイルは対象外にする。
        write(self.plugin / "changelog.d" / "nested" / "20260914-nested.md", fragment("20260914-nested.md"))
        commit_all(self.repo, "add nested fragment (not a top-level fragment)")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_finding_row_with_wrong_column_count_fails_cleanly(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log()
        text = text.replace(
            "| F1 | codex-1 | high | yes | inherited | shell-parse | fixed | 例 |\n",
            "| F1 | codex-1 | high | yes | inherited | shell-parse | fixed |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a malformed row")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("column", result.stdout)

    def test_nested_fence_of_different_length_does_not_escape_detection(self) -> None:
        # 独立レビュー2巡目指摘（high・fail-open、当時の実装）: compute_fence_flags が
        # バッククォートの本数を無視して `` ``` `` の出現だけでトグルしていたため、
        # 外側 4 バッククォート・内側 3 バッククォートの入れ子フェンスでトグルの
        # 偶奇がずれ、内側の閉じフェンスで外側のフェンスが終わったと誤判定された。
        # 結果、外側の開始直後にある単独の3バッククォート行1個で早々にトグルが
        # 戻ってしまい（2回目）、続く「書式の説明のつもりの正しい例」がフェンス外
        # ＝本物として読まれる。外側の閉じ `` ```` `` で3回目のトグルが起きるため、
        # その後にある本物の記録（欠陥入り）は逆にフェンス内と誤判定され検査から漏れる。
        #
        # 2026-09-14 時点の現在の実装は、フェンスのトグル判定自体を持たない
        # （H1' 対応でホワイトリスト方式に変更）。入れ子フェンスの長さがどうで
        # あれ、body の見出し前に置かれた説明文はその時点で即座に FAIL になる。
        # 過去の回避手口が形を変えても通用しないことを固定する回帰テストとして残す。
        self.add_fragment_and_commit("20260914-x.md")
        fenced_wrapper = (
            "説明:\n\n"
            "````\n"
            "```\n"
            "## 巡\n\n"
            "| 巡 | reviewer | sha | high | medium | blocking | at |\n"
            "|---|---|---|---|---|---|---|\n"
            "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n\n"
            "## 指摘\n\n"
            "| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| F1 | codex-1 | - | - | - | - | - | なし |\n\n"
            "````\n\n"
        )
        # 本物の記録は巡テーブルに codex-2 があるのに指摘テーブルに対応行が無い（FAIL すべき）。
        real_content = review_log(
            jun_rows=(
                "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n"
                "| codex-2 | codex adversarial-review | 9c4e7d0 | 1 | 0 | 0 | 2026-09-14T11:00+09:00 |\n"
            ),
            finding_rows="| F1 | codex-1 | - | - | - | - | - | なし |\n",
        )
        frontmatter, _, body = real_content.partition("\n\n")
        text = f"{frontmatter}\n\n{fenced_wrapper}{body}"
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a nested fence of a different length")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("must contain only blank lines", result.stdout)

    def test_indented_opening_fence_is_still_recognized_as_a_fence(self) -> None:
        # Codex レビュー指摘（P1・fail-open、当時の実装）: FENCE_START_RE が行頭直後の
        # フェンスしか認識せず、CommonMark が許す 0-3 スペースの字下げを無視していた。
        # 1 スペース字下げの開始フェンスは「フェンス外」として扱われ、内側の
        # ダミー表がフェンス外＝本物として読まれ、続く字下げなしの区切り行が新規の
        # 開始と誤認識されて、フェンスの外にある本物の不正な記録が検査から漏れた。
        #
        # 2026-09-14 時点の現在の実装は、開始フェンスの字下げ判定自体を持たない
        # （H1' 対応でホワイトリスト方式に変更）。字下げの有無にかかわらず、body の
        # 見出し前に置かれた説明文はその時点で即座に FAIL になる。過去の回避手口が
        # 形を変えても通用しないことを固定する回帰テストとして残す。
        self.add_fragment_and_commit("20260914-x.md")
        fenced_example = (
            "例:\n\n"
            " ```markdown\n"  # 1 スペース字下げ + 3 バッククォート（CommonMark 上は有効な開始）
            "## 巡\n\n"
            "| 巡 | reviewer | sha | high | medium | blocking | at |\n"
            "|---|---|---|---|---|---|---|\n"
            "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n\n"
            "## 指摘\n\n"
            "| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| F1 | codex-1 | - | - | - | - | - | なし |\n"
            "```\n\n"  # 字下げなしの閉じフェンス
        )
        # 本物の記録は巡テーブルに codex-2 があるのに指摘テーブルに対応行が無い（FAIL すべき）。
        real_content = review_log(
            jun_rows=(
                "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n"
                "| codex-2 | codex adversarial-review | 9c4e7d0 | 1 | 0 | 0 | 2026-09-14T11:00+09:00 |\n"
            ),
            finding_rows="| F1 | codex-1 | - | - | - | - | - | なし |\n",
        )
        frontmatter, _, body = real_content.partition("\n\n")
        text = f"{frontmatter}\n\n{fenced_example}{body}"
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an indented fenced example")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("must contain only blank lines", result.stdout)

    def test_jun_count_columns_must_be_non_negative_integers(self) -> None:
        # Codex レビュー指摘（P1）: 巡ごとの high/medium/blocking が数値か検証されて
        # おらず、任意の文字列（例: "not-a-number"）が通っていた。軽いレーンの規定はこの3列を
        # 効果測定の入力にするため、非負整数以外は FAIL にする。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review | 3f2a1bc | not-a-number | 999 | bogus | 2026-09-14T10:12+09:00 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with non-numeric jun counts")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not-a-number", result.stdout)

    def test_finding_row_with_all_dash_values_on_a_non_nashi_row_fails(self) -> None:
        # Codex レビュー指摘（P2）: severity/実害/自己起因/対応 の値域に "-" が無条件
        # で含まれており、要約が「なし」ではない実在する指摘行でも全列を "-" に
        # できた。「なし」行以外では固定語彙を必須にする。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | codex-1 | - | - | - | - | - | 実在する指摘 |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with dash values on a non-nashi row")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("severity", result.stdout)

    def test_nashi_only_jun_with_nonzero_counts_fails(self) -> None:
        # Codex レビュー指摘（P1・再レビュー）: 「なし」行だけの巡（実在する指摘が
        # 無い）なのに high/medium/blocking を非ゼロにしても通っていた。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review | 3f2a1bc | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | codex-1 | - | - | - | - | - | なし |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with nonzero counts on a nashi-only jun")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("codex-1", result.stdout)

    def test_jun_high_count_mismatch_with_finding_rows_fails(self) -> None:
        # Codex レビュー指摘（P1・再レビュー）: high=99 のように、指摘表の実際の
        # high 行数と無関係な数値でも通っていた。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review | 3f2a1bc | 99 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | codex-1 | high | yes | inherited | shell-parse | fixed | 例 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a high count mismatch")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("high=99", result.stdout)

    def test_jun_medium_count_mismatch_with_finding_rows_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review | 3f2a1bc | 1 | 5 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | codex-1 | high | yes | inherited | shell-parse | fixed | 例 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a medium count mismatch")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("medium=5", result.stdout)

    def test_invalid_severity_does_not_also_trigger_a_count_mismatch_false_positive(self) -> None:
        # severity 自体が無効な行は既に別の fail で捕捉されるため、それを理由に
        # 巡テーブルの件数照合まで巻き込んでノイズを増やさないことを確認する。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | codex-1 | hgih | yes | inherited | shell-parse | fixed | 例 |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an invalid severity value")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid severity", result.stdout)
        self.assertNotIn("count mismatch", result.stdout)
        self.assertNotIn("has no real finding row", result.stdout)

    def test_invalid_jun_label_fails(self) -> None:
        # Codex レビュー指摘: 軽いレーンの規定が定める巡ラベルの値域（方針メモ / codex-N /
        # 独立-N / PR後-N）外の任意文字列（例: このPR自身が使っていた "Codex"）が
        # 通っていた。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| Codex | codex adversarial-review | 3f2a1bc | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | Codex | high | yes | inherited | shell-parse | fixed | 例 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an out-of-domain jun label")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid 巡 label", result.stdout)

    def test_pr_go_jun_label_is_accepted(self) -> None:
        # 軽いレーンの規定の値域に含まれる PR後-N ラベルは受理される。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| PR後-1 | Codex (PR review) | 3f2a1bc | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | PR後-1 | high | yes | inherited | shell-parse | fixed | 例 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a PR後-N jun label")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_finding_and_nashi_row_mixed_in_same_jun_fails(self) -> None:
        # Codex レビュー指摘（P2・3回目の再レビュー）: 同じ巡に実指摘行と
        # 要約=なし 行を両方置いてもチェックが成功していた。「なし」は0件を示す
        # 排他的なプレースホルダーなので、実指摘がある巡に「なし」行が混在したら
        # FAIL にする。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            finding_rows=(
                "| F1 | codex-1 | high | yes | inherited | shell-parse | fixed | 例 |\n"
                "| F2 | codex-1 | - | - | - | - | - | なし |\n"
            ),
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a real finding and a nashi row mixed")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("なし", result.stdout)

    def test_duplicate_nashi_rows_in_the_same_jun_fails(self) -> None:
        # Codex レビュー指摘（P2・3回目の再レビュー）: 0件の巡に「なし」行を
        # 複数本置けてしまうと、集計時に曖昧になる。ちょうど1本に固定する。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows=(
                "| F1 | codex-1 | - | - | - | - | - | なし |\n"
                "| F2 | codex-1 | - | - | - | - | - | なし |\n"
            ),
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with duplicate nashi rows in the same jun")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly 1", result.stdout)

    def test_empty_reviewer_in_jun_row_fails(self) -> None:
        # Codex レビュー指摘（P1・4回目の再レビュー）: reviewer/sha/at/クラスタ/要約
        # がすべて空でも通っていた。分析に必要な主要列を欠落禁止にする。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 |  | 3f2a1bc | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an empty reviewer")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reviewer", result.stdout)

    def test_empty_at_in_jun_row_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review | 3f2a1bc | 1 | 0 | 0 |  |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an empty at")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at", result.stdout)

    def test_empty_sha_in_jun_row_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review |  | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an empty sha")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sha", result.stdout)

    def test_dash_sha_disallowed_except_for_policy_memo_jun(self) -> None:
        # sha='-' は「まだコミットが無い」ことを表す方針メモ巡だけの例外。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| codex-1 | codex adversarial-review | - | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a dash sha on a non-policy-memo jun")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sha", result.stdout)

    def test_dash_sha_is_allowed_for_policy_memo_jun(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| 方針メモ | opus (second opinion) | - | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | 方針メモ | high | yes | self-inflicted | doc | fixed | 例 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a dash sha on the policy-memo jun")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_cluster_in_real_finding_row_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | codex-1 | high | yes | inherited |  | fixed | 例 |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an empty cluster")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("クラスタ", result.stdout)

    def test_dash_cluster_in_real_finding_row_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | codex-1 | high | yes | inherited | - | fixed | 例 |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a dash cluster on a real finding row")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("クラスタ of '-'", result.stdout)

    def test_missing_shared_identity_module_fails_closed(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        (self.plugin / "scripts" / "lib" / "repository_identity.py").unlink()
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cannot load scripts/lib/repository_identity.py", result.stdout)

    def test_corrupted_shared_identity_module_fails_closed(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        write(self.plugin / "scripts" / "lib" / "repository_identity.py", "def broken(:\n    this is not valid python\n")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cannot load scripts/lib/repository_identity.py", result.stdout)

    def test_shared_identity_module_raising_systemexit_fails_closed(self) -> None:
        # 独立レビュー指摘（PR後-1・high・実害あり）: `except Exception` は
        # `SystemExit`（BaseException 派生）を捕捉できず、モジュールの exec 中に
        # SystemExit が送出されると try/except を素通りしてスクリプト全体が
        # rc=0 で静かに成功してしまう（SKIP-B 行すら出ない）。
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        write(self.plugin / "scripts" / "lib" / "repository_identity.py", "import sys\nsys.exit(0)\n")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cannot load scripts/lib/repository_identity.py", result.stdout)

    def test_shared_release_module_raising_systemexit_fails_closed(self) -> None:
        # 独立レビュー指摘（独立-6・high・実害あり）: release.py のロードにも
        # 同じ `except Exception` パターンが別に書かれており、SystemExit を
        # 送出するモジュールで try/except を素通りしてしまう（release 変数が
        # 未初期化のモジュールオブジェクトのまま後続で参照される実害もある）。
        # exec_module 専用のブートストラップ（load_dynamic_module）に一本化
        # して閉じた。
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        write(self.plugin / "scripts" / "release.py", "import sys\nsys.exit(0)\n")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cannot load scripts/release.py", result.stdout)

    def test_identity_function_call_raising_systemexit_fails_closed(self) -> None:
        # PR #93 の PR 後レビュー3巡目（独立-5・独立-6に続く同クラスタの High）:
        # load_dynamic_module() は exec_module() 呼び出しの SystemExit だけを
        # 守り、ロード自体は成功したモジュールへの「呼び出し」
        # (identity_lib.repository_identity(...)) で SystemExit が送出される
        # と、fail()/die() に到達せず rc=0 で静かに成功していた。run() を
        # 正常return しなかった経路として呼び出し元の except で一律 FAIL に
        # 合流させる構造に変えたことで、この経路も閉じることを固定する。
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        write(
            self.plugin / "scripts" / "lib" / "repository_identity.py",
            "import sys\n\n\ndef repository_identity(base, marketplace_name):\n    sys.exit(0)\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("VERDICT: review-log-present: OK", result.stdout)
        self.assertNotIn("VERDICT: review-log-present: SKIP", result.stdout)

    def test_release_name_re_fullmatch_call_raising_systemexit_fails_closed(self) -> None:
        # 同クラスタ、呼び出し箇所2つ目: release.NAME_RE.fullmatch() の呼び出し
        # 中に SystemExit が送出されるケース。release.py のロード自体は成功
        # するが、その中の NAME_RE オブジェクトへの呼び出しが落ちる。
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        write(
            self.plugin / "scripts" / "release.py",
            "import sys\n\n\nclass _ExitingPattern:\n"
            "    def fullmatch(self, name):\n"
            "        sys.exit(0)\n\n\n"
            "NAME_RE = _ExitingPattern()\n\n\n"
            "def load_fragments(root):\n"
            "    return [], []\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("VERDICT: review-log-present: OK", result.stdout)
        self.assertNotIn("VERDICT: review-log-present: SKIP", result.stdout)

    def test_identity_function_call_raising_systemexit_256_is_not_masked_to_shell_exit_zero(self) -> None:
        # PR #93 の PR 後レビュー（PR後-3、独立-5・独立-6・PR後-2に続く同種の
        # fail-open 指摘）: except SystemExit ハンドラが `error.code` を読み、
        # `code if code != 0 else 1` で 0 だけを 1 に変換していた。しかし
        # `SystemExit(256)`（256 の倍数）は POSIX のシェル終了コードマスク
        # （`exit_code & 0xFF`）でシェル側の実終了コードが 0 になるため、
        # `code != 0` の判定を通過してそのまま `sys.exit(256)` に渡り、結局
        # シェル rc=0 で静かに成功してしまう（VERDICT 行は出ない）。
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        write(
            self.plugin / "scripts" / "lib" / "repository_identity.py",
            "import sys\n\n\ndef repository_identity(base, marketplace_name):\n    sys.exit(256)\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("VERDICT: review-log-present: OK", result.stdout)
        self.assertNotIn("VERDICT: review-log-present: SKIP", result.stdout)

    def test_identity_function_call_raising_systemexit_512_is_not_masked_to_shell_exit_zero(self) -> None:
        # PR #93 マージ直前に届いた指摘1（test-power）: 上の 256 テストは値を
        # 1 つしか固定しないため、「256 という特定値だけを特別扱いする」狭い
        # 実装変異（例: `except SystemExit as exc: ... exc.code ...` への
        # リネーム）を見逃しうる。独立レビューは `SystemExit(512)`（256の別の
        # 倍数）で rc=0・VERDICT なしが復活することを確認したと報告している。
        # 256 と異なる倍数でも同じ経路が閉じていることを別途固定する。
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        commit_all(self.repo, "add review-log")
        write(
            self.plugin / "scripts" / "lib" / "repository_identity.py",
            "import sys\n\n\ndef repository_identity(base, marketplace_name):\n    sys.exit(512)\n",
        )
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("VERDICT: review-log-present: OK", result.stdout)
        self.assertNotIn("VERDICT: review-log-present: SKIP", result.stdout)
        # PR #93 マージ直前に届いた指摘2（product）: except SystemExit 経路は
        # fail-closed だが診断メッセージ（FAIL: 行）が無く、直接実行時になぜ
        # 失敗したか分からない。error.code は読まず、固定文言で理由を出す。
        self.assertIn("FAIL: review-log-present: run() ended via SystemExit without returning a verdict", result.stdout)

    def test_empty_summary_in_real_finding_row_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(finding_rows="| F1 | codex-1 | high | yes | inherited | shell-parse | fixed |  |\n")
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with an empty summary")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("要約", result.stdout)

    def test_uncommitted_new_fragment_is_still_checked(self) -> None:
        # Codex レビュー指摘（P1・5回目の再レビュー、実害あり）: 新規断片の検出を
        # merge-base..HEAD の git diff だけで行っていたため、「変更 → validate-
        # plugin.sh で検証 → コミット」という通常の運用ではコミット前の新規断片が
        # 検査から漏れていた（未コミット状態で returncode=0 を実測で再現）。
        write(self.plugin / "changelog.d" / "20260914-uncommitted.md", fragment("20260914-uncommitted.md"))
        # コミットしない（working tree にのみ存在する）。
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("20260914-uncommitted.md", result.stdout)
        self.assertIn("is missing", result.stdout)

    def test_staged_new_fragment_is_still_checked(self) -> None:
        write(self.plugin / "changelog.d" / "20260914-staged.md", fragment("20260914-staged.md"))
        rel = (self.plugin / "changelog.d" / "20260914-staged.md").relative_to(self.repo)
        result = git(self.repo, "add", str(rel))
        assert result.returncode == 0, result.stderr
        # git add のみでコミットしない。
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("20260914-staged.md", result.stdout)

    def test_uncommitted_fragment_with_uncommitted_review_log_passes(self) -> None:
        write(self.plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
        write(self.repo / "review-log" / "20260914-x.md", review_log())
        # 断片・review-log ともコミットしない。
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_duplicated_jun_label_in_jun_table_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows=(
                "| codex-1 | codex adversarial-review | 3f2a1bc | 0 | 0 | 0 | 2026-09-14T10:12+09:00 |\n"
                "| codex-1 | codex adversarial-review | 9c4e7d0 | 1 | 0 | 0 | 2026-09-14T11:00+09:00 |\n"
            ),
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a duplicated jun label")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicated", result.stdout)
        self.assertIn("codex-1", result.stdout)

    def test_hidden_row_after_blank_line_in_jun_table_fails(self) -> None:
        # Codex レビュー指摘（H1・high・fail-open）: テーブル行収集ループが `|` で
        # 始まらない行（空行含む）に遭遇した時点で打ち切られていたため、テーブルの
        # 先頭数行さえ正しければ、空行を挟んだ先に不正な巡ラベル・重複 id を置いても
        # 「テーブル外」として一切検査されずスルーされていた（実測で再現）。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows=(
                "| codex-1 | codex adversarial-review | 3f2a1bc | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n"
                "\n"
                "| not-a-valid-label | x | y | 0 | 0 | 0 | z |\n"
            ),
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "hide an invalid jun row after a blank line")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not-a-valid-label", result.stdout)

    def test_hidden_row_after_blank_line_in_finding_table_fails(self) -> None:
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            finding_rows=(
                "| F1 | codex-1 | high | yes | inherited | shell-parse | fixed | 例 |\n"
                "\n"
                "| F1 | codex-1 | not-a-severity | yes | inherited | shell-parse | fixed | 重複id |\n"
            ),
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "hide an invalid finding row after a blank line")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not-a-severity", result.stdout)

    def test_unknown_heading_after_valid_jun_table_no_longer_hides_trailing_data(self) -> None:
        # Codex レビュー指摘（H1'・high・fail-open、実測で再現、fence-parsing/隠し
        # 領域クラスタの5回目の再発）: 直前の修正（テーブルの検査範囲を「見出しから
        # 次の `## ` 見出しまたは EOF まで」に固定）は、`## 巡` の正しい表の直後に
        # `## メモ` のような未知の見出しを置くだけで、その下が無条件で検査範囲の
        # 外になった。ホワイトリスト方式（`## 巡`/`## 指摘` 以外の見出しは見出し
        # として扱わずただの非空行として扱う）に変更したことで、`## メモ` の下の
        # 不正な行も `## 巡` セクションの一部として検査されるようになったことを
        # 固定する。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log()
        text = text.replace(
            "## 指摘\n\n",
            "## メモ\n\n| not-a-valid-label | hidden | garbage |\n\n## 指摘\n\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "hide an invalid row behind an unknown heading")
        result = run_check(self.plugin)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("not-a-valid-label", result.stdout)

    def test_git_dir_env_var_does_not_cause_false_skip_b(self) -> None:
        # Codex レビュー指摘（H2'・high・fail-open、実測で再現）: SKIP-B の判定を
        # `git -C <repo_root> rev-parse --is-inside-work-tree` の returncode だけで
        # 行っていたため、呼び出し元の環境に GIT_DIR が残っていると（例:
        # GIT_DIR=/nonexistent/x.git）、実際には通常の git checkout であるにも
        # かかわらず rev-parse が別のリポジトリを見て失敗し、「判定できない」を
        # 「消費者環境の plugin cache 配置」と誤認して SKIP-B になり、review-log/
        # の欠落チェック自体が素通りしていた。全 git 呼び出しから GIT_* 環境変数を
        # 除去して修正した。
        self.add_fragment_and_commit("20260914-x.md")
        env = {
            **GIT_ENV,
            "ROOT": str(self.plugin),
            "PYTHON_BIN": sys.executable,
            "GDD_INTEGRATION_REF": "main",
            "GIT_DIR": "/nonexistent/x.git",
        }
        result = subprocess.run(
            ["bash", str(self.plugin / "tests" / "checks" / "review-log-present.sh")],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("SKIP-B", result.stdout)
        self.assertIn("review-log/20260914-x.md", result.stdout)
        self.assertIn("is missing", result.stdout)

    def test_corrupted_git_marker_fails_not_skips(self) -> None:
        # fail-open の3ケースのうち「判定できないときに通ってしまう」ケース:
        # `.claude-plugin/marketplace.json` の name が本リポジトリと一致して
        # identity が確定しているのに、`.git` が壊れた参照のせいで
        # `git rev-parse` 自体が失敗する場合、「消費者環境で git work tree では
        # ない」とは区別できないため SKIP にせず FAIL にする（H3・H4 対応で
        # identity marker に転換した後も維持すべき性質）。
        outside = Path(tempfile.mkdtemp())
        try:
            write_marketplace_json(outside)
            fake_plugin = outside / "plugins" / "b"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            (outside / ".git").write_text("gitdir: /nonexistent/broken-worktree.git\n", encoding="utf-8")
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_dangling_git_symlink_in_identity_confirmed_checkout_fails_not_skips(self) -> None:
        # Codex レビュー指摘（H3・high・fail-open、実測で再現、当時の実装）:
        # has_git_marker が Path.exists() を使っており、symlink の先を辿る。
        # repo_root/.git が「存在しない先への symlink」だと exists() は False を
        # 返すため、実際には（壊れているとはいえ）通常の checkout であるにも
        # かかわらず「.git マーカーが無い」と誤判定され SKIP-B になっていた
        # （review-log 無しの checkout で本来 rc 1 になるべきところが rc 0 に
        # なることを実測で再現。SKIP-B 述語のクラスタとしては H2→H2'→H3 で3回目）。
        #
        # H3 対応（ディレクトリレイアウト一致判定）はさらに H4（実機で再現、
        # ROOT が別名 symlink 経由だと基準名が一致せず誤 SKIP-B）を再発させた
        # ため、identity marker（`.claude-plugin/marketplace.json` の name）へ
        # 転換した。identity が確定している限り、`.git` が symlink であろうと
        # 壊れていようと、git の失敗はすべて FAIL（fail-closed）になる性質は
        # 維持される。
        outside = Path(tempfile.mkdtemp())
        try:
            write_marketplace_json(outside)
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            (outside / ".git").symlink_to(outside / "nonexistent-target.git")
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_symlinked_root_with_different_basename_does_not_cause_false_skip_b(self) -> None:
        # Codex レビュー指摘（H4・high・fail-open、実機で再現）: 直前の設計
        # （ROOT が <repo_root>/plugins/<ROOT の名前> というディレクトリ
        # レイアウトと一致するかどうか）は、repo_root は `.resolve()` 済みだが
        # 比較対象の basename は未 resolve の ROOT からそのまま取っていたため、
        # ROOT が別名の symlink（例: plugin cache のバージョン番号ディレクトリ
        # `.../gate-driven-development/0.44.0` → 実体は
        # `<repo_root>/plugins/gate-driven-development`）経由だと basename が
        # 一致せず、真の開発 checkout でも SKIP-B になり review-log の欠落
        # チェックが素通りしていた（このマシンの実際の plugin cache
        # `~/.claude/plugins/cache/*/gate-driven-development/<version>/` で
        # 再現確認済み）。
        #
        # identity marker（`.claude-plugin/marketplace.json` の name）は ROOT の
        # basename を一切見ないため、この変異は構造的に再発しない。
        outside = Path(tempfile.mkdtemp())
        try:
            git(outside, "init", "-q", "-b", "main")
            write_marketplace_json(outside)
            real_plugin = outside / "plugins" / "gate-driven-development"
            make_plugin(real_plugin)
            commit_all(outside, "base (no fragment yet)")
            # release.py の load_fragments と同じ受理集合はディレクトリ直下を
            # 直接見る（working tree、コミット不要。PR後-5 の設計と同じ）。
            write(real_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            symlinked_root = outside / "cache" / "versions" / "0.44.0"
            symlinked_root.parent.mkdir(parents=True, exist_ok=True)
            symlinked_root.symlink_to(real_plugin)
            result = run_check(self.plugin, root_override=symlinked_root)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("SKIP-B", result.stdout)
            self.assertIn("review-log/20260914-x.md", result.stdout)
            self.assertIn("is missing", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_layout_match_does_not_skip_ambiguity_when_marketplace_name_differs(self) -> None:
        # Opus のセカンドオピニオンで実機発見された「逆方向の誤判定」: 旧実装
        # （ROOT が <repo_root>/plugins/<name> というディレクトリレイアウトと
        # 一致するかどうか）は、本物の消費者環境（別リポジトリを marketplace
        # clone したもの）が偶然同じレイアウトを満たすと「開発 checkout」と
        # 誤判定していた（実機の `~/.claude/plugins/marketplaces/*/plugins/*`
        # で複数件実測確認）。SKIP-B が守ろうとしていた実害（消費者環境での
        # 誤 block）を、まさに守れていなかった。
        #
        # identity marker はディレクトリレイアウトを一切見ないため、レイアウトが
        # <repo_root>/plugins/<name> と一致していても、marketplace.json の name
        # が本リポジトリと異なれば SKIP-B にする。
        outside = Path(tempfile.mkdtemp())
        try:
            git(outside, "init", "-q", "-b", "main")
            write_marketplace_json(outside, name="some-other-marketplace")
            fake_plugin = outside / "plugins" / "gdd"
            make_plugin(fake_plugin)
            write(fake_plugin / "changelog.d" / "20260914-x.md", fragment("20260914-x.md"))
            commit_all(outside, "unrelated repo with a plugin-shaped subtree")
            result = run_check(self.plugin, root_override=fake_plugin)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP-B", result.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_policy_memo_jun_label_with_suffix_is_accepted(self) -> None:
        # 差し戻し後の再方針メモ（root CLAUDE.md L1+ 安全策1）を記録できるよう、
        # `方針メモ` 単独に加えて `方針メモ-N` も軽いレーンの規定の巡ラベル値域に含める。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| 方針メモ-2 | opus (second opinion) | 3f2a1bc | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | 方針メモ-2 | high | yes | self-inflicted | doc | fixed | 例 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a suffixed policy-memo jun label")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dash_sha_is_allowed_for_policy_memo_jun_with_suffix(self) -> None:
        # 再方針メモもまだコミットが無い段階で書かれうるため、sha='-' の例外は
        # `方針メモ-N` にも及ぶ。
        self.add_fragment_and_commit("20260914-x.md")
        text = review_log(
            jun_rows="| 方針メモ-2 | opus (second opinion) | - | 1 | 0 | 0 | 2026-09-14T10:12+09:00 |\n",
            finding_rows="| F1 | 方針メモ-2 | high | yes | self-inflicted | doc | fixed | 例 |\n",
        )
        write(self.repo / "review-log" / "20260914-x.md", text)
        commit_all(self.repo, "add review-log with a dash sha on a suffixed policy-memo jun")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    # --- 再掲（`対応` = re-reported）: root CLAUDE.md 手順 6。既に Issue・accepted の
    # 指摘の再報告は、`## 指摘` に行を残し、`## 巡` の high・medium に数えない ---

    def check_log(self, jun_rows: str, finding_rows: str) -> subprocess.CompletedProcess:
        self.add_fragment_and_commit("20260914-x.md")
        write(self.repo / "review-log" / "20260914-x.md", review_log(jun_rows=jun_rows, finding_rows=finding_rows))
        commit_all(self.repo, "add review-log")
        return run_check(self.plugin)

    def test_re_reported_rows_are_not_counted_in_jun_high_and_medium(self) -> None:
        result = self.check_log(
            "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 1 | 0 | 1 | 2026-09-19T10:00+09:00 |\n",
            "| F1 | 独立-2 | high | no | inherited | shell-parse | re-reported | #141 の再掲 |\n"
            "| F2 | 独立-2 | medium | no | inherited | doc | re-reported | F0 の再掲 |\n"
            "| F3 | 独立-2 | high | yes | self-inflicted | shell-parse | fixed | 新規 |\n",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_counting_a_re_reported_row_in_jun_high_fails(self) -> None:
        # 再掲を数えた high を宣言すると、指摘表と食い違う（数え方を片側だけ変えない）
        result = self.check_log(
            "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 1 | 0 | 0 | 2026-09-19T10:00+09:00 |\n",
            "| F1 | 独立-2 | high | no | inherited | shell-parse | re-reported | #141 の再掲 |\n",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("high=1", result.stdout)

    def test_jun_with_only_re_reported_rows_must_declare_zero(self) -> None:
        result = self.check_log(
            "| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 0 | 0 | 0 | 2026-09-19T10:00+09:00 |\n",
            "| F1 | 独立-3 | high | no | inherited | shell-parse | re-reported | #141 の再掲 |\n",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_re_reported_row_still_validates_its_other_columns(self) -> None:
        # 再掲の行も実指摘の行として値域を検査する（'-' や不正値で素通りさせない）
        for row in (
            "| F1 | 独立-2 | hgih | no | inherited | shell-parse | re-reported | 例 |\n",
            "| F1 | 独立-2 | high | - | inherited | shell-parse | re-reported | 例 |\n",
            "| F1 | 独立-2 | high | no | inherited | - | re-reported | 例 |\n",
            "| F1 | 独立-2 | high | no | inherited | shell-parse | re-reported | なし |\n",
        ):
            with self.subTest(row=row):
                self.tearDown()
                self.setUp()
                result = self.check_log(
                    "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 0 | 0 | 0 | 2026-09-19T10:00+09:00 |\n",
                    row,
                )
                self.assertNotEqual(result.returncode, 0, row)

    def test_out_of_pr_rows_are_not_counted_in_jun_high_and_medium(self) -> None:
        # ②（next-pr）と ③（out-of-diff）はこの PR で直さないので、巡の件数に入れない。
        # 既存の値（deferred / accepted）は今までどおり数える（後方互換）
        result = self.check_log(
            "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 1 | 1 | 0 | 2026-09-19T10:00+09:00 |\n",
            "| F1 | 独立-2 | high | no | inherited | doc | next-pr | 話題だけ関連 |\n"
            "| F2 | 独立-2 | high | no | inherited | doc | out-of-diff | 差分の外 |\n"
            "| F3 | 独立-2 | medium | no | inherited | doc | out-of-diff | 差分の外 |\n"
            "| F4 | 独立-2 | high | no | inherited | doc | deferred | 旧来の後回し |\n"
            "| F5 | 独立-2 | medium | no | inherited | doc | accepted | 旧来の受け入れ |\n",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_counting_an_out_of_pr_row_in_jun_high_fails(self) -> None:
        for taiou in ("next-pr", "out-of-diff"):
            with self.subTest(taiou=taiou):
                self.tearDown()
                self.setUp()
                result = self.check_log(
                    "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 1 | 0 | 0 | 2026-09-19T10:00+09:00 |\n",
                    f"| F1 | 独立-2 | high | no | inherited | doc | {taiou} | 例 |\n",
                )
                self.assertNotEqual(result.returncode, 0, taiou)
                self.assertIn("high=1", result.stdout)

    def test_harmful_row_cannot_be_left_out_of_the_count(self) -> None:
        # CLAUDE.md 手順 6: 実害クラスは再掲・②③ にできず、この PR で直す。実害=yes に
        # 3 つの値を付けて巡の high から外す（安全策 4 も素通りする）経路を閉じる
        for taiou in ("re-reported", "next-pr", "out-of-diff"):
            with self.subTest(taiou=taiou):
                self.tearDown()
                self.setUp()
                result = self.check_log(
                    "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 0 | 0 | 0 | 2026-09-19T10:00+09:00 |\n",
                    f"| F1 | 独立-2 | high | yes | inherited | shell-parse | {taiou} | 例 |\n",
                )
                self.assertNotEqual(result.returncode, 0, taiou)
                self.assertIn("実害", result.stdout)

    def test_invalid_value_message_lists_the_allowed_values(self) -> None:
        # 使える値が分からず、`open` などで何度も落ちていた。失敗の行に使える値を並べる。
        for column, row, allowed in (
            ("対応", "| F1 | 独立-2 | high | yes | inherited | shell-parse | open | 例 |\n",
             "accepted, deferred, fixed, next-pr, out-of-diff, re-reported"),
            ("severity", "| F1 | 独立-2 | hgih | yes | inherited | shell-parse | fixed | 例 |\n",
             "advisory, high, low, medium"),
            ("実害", "| F1 | 独立-2 | high | maybe | inherited | shell-parse | fixed | 例 |\n", "no, yes"),
            ("自己起因", "| F1 | 独立-2 | high | yes | pre-existing | shell-parse | fixed | 例 |\n",
             "inherited, self-inflicted"),
        ):
            with self.subTest(column=column):
                self.tearDown()
                self.setUp()
                result = self.check_log(
                    "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 1 | 0 | 1 | 2026-09-19T10:00+09:00 |\n",
                    row,
                )
                self.assertNotEqual(result.returncode, 0)
                line = next(l for l in result.stdout.splitlines() if f"invalid {column}" in l)
                self.assertIn(f"(allowed: {allowed})", line)

    def test_unknown_taiou_value_still_fails(self) -> None:
        result = self.check_log(
            "| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3f2a1bc | 0 | 0 | 0 | 2026-09-19T10:00+09:00 |\n",
            "| F1 | 独立-2 | high | yes | inherited | shell-parse | repeat | 例 |\n",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid 対応", result.stdout)


IN_CANONICAL_REPO = (REPO_ROOT / "review-log" / "README.md").is_file() and (
    REPO_ROOT / "plugins" / "gate-driven-development"
).resolve() == PLUGIN_ROOT.resolve()


# 現行の検査が入る前に書かれ、変更前の検査でも通らない review-log（理由は変更と無関係）
PRE_EXISTING_INVALID = {
    "20260914-review-log.md",  # クラスタ '-' の拒否より前の記録
}
# 検査の対象は L1・L1+ の review-log だけ（L0 は検査が lane で落とす。L0 の記録が足されても
# この後方互換のテストを無関係に落とさない）
LANE_RE = re.compile(r"\A---\n(?:.*\n)*?lane: *(L1\+?) *\n", re.M)


def _existing_review_logs() -> list[Path]:
    if not IN_CANONICAL_REPO:
        return []
    return sorted(
        p
        for p in (REPO_ROOT / "review-log").glob("2*.md")
        if p.name not in PRE_EXISTING_INVALID and LANE_RE.match(p.read_text(encoding="utf-8"))
    )


EXISTING_REVIEW_LOGS = _existing_review_logs()


@pytest.fixture(scope="module")
def review_log_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """base の commit と feature branch までは、どの log でも同じなので worker ごとに 1 回だけ作る。
    複製の途中で auto maintenance の lock が消えないよう、base では止めておく。"""
    template = tmp_path_factory.mktemp("review-log-template") / "repo"
    template.mkdir()
    git(template, "init", "-q", "-b", "main")
    git(template, "config", "maintenance.auto", "false")
    write_marketplace_json(template)
    make_plugin(template / "plugins" / "gdd")
    commit_all(template, "base")
    git(template, "checkout", "-q", "-b", "feature")
    return template


def test_existing_review_logs_are_collected() -> None:
    if not IN_CANONICAL_REPO:
        pytest.skip("canonical repo 外では repo root の review-log/ を検査しない")
    assert EXISTING_REVIEW_LOGS


# 後方互換: `対応` に値を足しても、既存の書式（fixed / deferred / accepted だけ）の
# review-log はそのまま通る。main にある review-log を 1 本ずつ新規断片の対として検査する。
# 1 本を 1 テストにして、xdist の worker に分ける（1 テストにまとめると、本数に比例して伸びる
# 1 件が worker 1 つを占め、全量の終わりを遅らせる）。
@pytest.mark.parametrize("log", EXISTING_REVIEW_LOGS, ids=lambda p: p.name)
def test_existing_review_log_passes(log: Path, review_log_template: Path, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(review_log_template, repo, symlinks=True)
    plugin = repo / "plugins" / "gdd"
    write(plugin / "changelog.d" / log.name, fragment(log.name))
    write(repo / "review-log" / log.name, log.read_text(encoding="utf-8"))
    commit_all(repo, "add")
    result = run_check(plugin)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 fragment(s) checked" in result.stdout


if __name__ == "__main__":
    unittest.main()
