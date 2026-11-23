"""Contract tests for lint-ac.py の AC ID 文法（定義行の認識 / ID トークン化）。

GDD completion-check（20260904-state-field-reader-unification）で実測した
取りこぼし 2 件を固定する。

1. 定義行の注記位置
   `- **AC-8-2**（DH-1、人間承認済み）: ...` のように ID と `:` の間に注記が
   入る形が定義として認識されず、tasklist 側の `method=ac:AC-8-2` /
   RED Evidence の `- AC: AC-8-2` が「架空 AC」と誤判定されて exit=1 になった。

2. `AC-3-d` 形のトークン化
   `_AC_ID_CORE` の複合サフィックスが数字しか受けないため `AC-3-d` が `AC-3`
   に潰れ、定義側も参照側も同じ ID になるため矛盾が検出されず、エラーも警告も
   出ないまま coverage 検査を素通りした。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする
# （pytest は tests/ を自動で path に入れるが unittest は入れない）。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import PLUGIN_ROOT, load_plugin_module  # noqa: E402

LINT_AC = PLUGIN_ROOT / "scripts" / "lint-ac.py"


def run_lint(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LINT_AC), *args],
        capture_output=True,
        text=True,
    )


class LintAcIdGrammarContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_plugin_module("scripts/lint-ac.py")

    # --- 1. 定義行の注記位置 -------------------------------------------------

    def test_definition_with_annotation_between_id_and_colon_is_recognized(self) -> None:
        """ID と `:` の間に注記が入る定義行も AC 定義として認識する。"""
        text = (
            "## 受入条件\n"
            "- **AC-1**: 注記なし\n"
            "- **AC-8-2**（DH-1、人間承認済み）: 注記あり（全角括弧）\n"
            "- **AC-17**（DM-1、人間承認済み）: 注記あり（全角括弧）\n"
            "- **AC-18** (DM-2, approved): 注記あり（半角括弧）\n"
            "- **AC-19**［補足］: 注記あり（角括弧）\n"
        )
        ids, _all_ids = self.mod.extract_ac_ids_from_requirements(text)
        self.assertEqual(ids, {"AC-1", "AC-8-2", "AC-17", "AC-18", "AC-19"})

    def test_prose_mention_with_parenthetical_is_not_treated_as_definition(self) -> None:
        """本文中の偶発的な `AC-N` 言及を定義と誤認しない。"""
        text = (
            "## 受入条件\n"
            "- **AC-1**: 本物の定義\n"
            "\n"
            "## 補足\n"
            "- AC-2 (前述) は本 task の対象外: 次 task で扱う\n"
            "- AC-3 については AC-1 の派生: 定義ではない\n"
        )
        ids, _all_ids = self.mod.extract_ac_ids_from_requirements(text)
        self.assertEqual(ids, {"AC-1"})

    def test_annotated_definition_is_not_reported_as_orphan_reference(self) -> None:
        """注記つき定義を tasklist / RED Evidence から参照しても exit=0。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-annotated-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "## 受入条件\n"
                "- **AC-8-2**（DH-1、人間承認済み）: state field reader を統一する\n"
                "- **AC-17**（DM-1、人間承認済み）: 回帰テストを追加する\n",
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "### Current Task\n"
                "- Verification: method=ac:AC-8-2\n"
                "- Verification: method=ac:AC-17\n"
                "\n"
                "#### RED Evidence\n"
                "- AC: AC-8-2, AC-17\n"
                "- command: pytest\n",
                encoding="utf-8",
            )
            result = run_lint("--steering-dir", str(steering))

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertNotIn("存在しない AC ID", result.stdout)

    # --- 2. `AC-3-d` 形のトークン化 ------------------------------------------

    def test_letter_compound_suffix_id_is_tokenized_distinctly(self) -> None:
        """`AC-3-d` が `AC-3` に潰れない。"""
        found = self.mod.AC_ID_RE.findall("AC-3-d AC-8-2 AC-17")
        self.assertEqual(found, ["AC-3-d", "AC-8-2", "AC-17"])

    def test_letter_compound_suffix_id_is_recognized_as_definition(self) -> None:
        text = "## 受入条件\n- **AC-3**: 基本挙動\n- **AC-3-d**: 意図的な挙動変化を固定する\n"
        ids, _all_ids = self.mod.extract_ac_ids_from_requirements(text)
        self.assertEqual(ids, {"AC-3", "AC-3-d"})

    def test_letter_compound_suffix_mismatch_is_detected(self) -> None:
        """`AC-3` しか定義されていない状態で `AC-3-d` を参照したら ERROR。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-suffix-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "## 受入条件\n- **AC-3**: 基本挙動\n",
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "### Current Task\n"
                "- Verification: method=ac:AC-3-d\n"
                "\n"
                "#### RED Evidence\n"
                "- AC: AC-3-d\n",
                encoding="utf-8",
            )
            result = run_lint("--steering-dir", str(steering))

        self.assertEqual(
            result.returncode,
            1,
            msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn("AC-3-d", result.stdout)

    def test_letter_compound_suffix_ac_is_covered_by_verification(self) -> None:
        """`AC-3-d` を定義して同じ ID で verify すれば pass（WARN も出さない）。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-suffix-ok-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "## 受入条件\n- **AC-3**: 基本挙動\n- **AC-3-d**: 意図的な挙動変化\n",
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "### Current Task\n"
                "- Verification: method=ac:AC-3\n"
                "- Verification: method=ac:AC-3-d\n"
                "\n"
                "#### RED Evidence\n"
                "- AC: AC-3, AC-3-d\n",
                encoding="utf-8",
            )
            result = run_lint("--steering-dir", str(steering))

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn("OK: AC ID 整合性 pass", result.stdout)

    # --- 3. 既存 ID 形の回帰 -------------------------------------------------

    def test_existing_id_shapes_still_resolve(self) -> None:
        cases = [
            "AC-1",
            "AC-2a",
            "AC-3b",
            "AC-17",
            "AC-F1",
            "AC-8-2",
            "AC-E9-1",
            "AC-E9-1a",
        ]
        for token in cases:
            with self.subTest(token=token):
                self.assertEqual(self.mod.AC_ID_RE.findall(token), [token])

        text = "## 受入条件\n" + "".join(f"- **{t}**: desc\n" for t in cases)
        ids, all_ids = self.mod.extract_ac_ids_from_requirements(text)
        self.assertEqual(all_ids, cases)
        self.assertEqual(ids, set(cases))

    def test_verification_reference_shapes_still_resolve(self) -> None:
        text = (
            "- Verification: method=ac:AC-2a\n"
            "- Verification: method=ac:AC-8-2\n"
            "- Verification: method=ac:AC-E9-1a\n"
            "- Verification: method=ac:AC-3-d\n"
        )
        self.assertEqual(
            self.mod.extract_ac_ids_from_tasklist(text),
            {"AC-2a", "AC-8-2", "AC-E9-1a", "AC-3-d"},
        )

    # --- 4. YAML frontmatter 撤去後の安全側動作 ------------------------

    def test_ac_definition_free_requirements_is_info_not_error_even_under_strict(self) -> None:
        """AC 未定義の requirements.md は --strict でも exit=0・INFO のまま
        （YAML frontmatter 撤去で「判定できないときに通ってしまう」方向へ
        誤って倒れていないことを固定する）。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-empty-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "## 目的\n本文のみで AC 定義なし\n",
                encoding="utf-8",
            )
            result = run_lint("--strict", "--steering-dir", str(steering))

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn("AC 定義が見つかりません", result.stdout)

    def test_yaml_only_ac_frontmatter_does_not_silently_skip_red_evidence_orphan_check(
        self,
    ) -> None:
        """PR #96 レビュー指摘（HIGH・fail-open、実機再現済み）: requirements.md の AC が
        YAML frontmatter（`acceptance_criteria`）のみで markdown bullet が無い場合、
        撤去済みの YAML 抽出により `req_ids` が空集合になり、
        `check_red_evidence_ac_binding` の `if defined_ac_ids:` ガードが素通りして、
        RED Evidence が実在しない AC（架空 AC）を参照していても exit=0 で通っていた
        （main では exit=1 で検出していた退行）。この入力を ERROR にして固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-yaml-orphan-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "---\n"
                "acceptance_criteria:\n"
                "  - id: AC-1\n"
                "    description: yaml backed\n"
                "---\n\n"
                "## 目的\nテスト\n",
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "### Current Task\n"
                "\n"
                "#### RED Evidence\n"
                "- AC: AC-99\n"
                "- command: pytest\n",
                encoding="utf-8",
            )
            result = run_lint("--steering-dir", str(steering))

        self.assertEqual(
            result.returncode,
            1,
            msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn("ERROR", result.stdout)

    def test_red_evidence_orphan_check_fires_even_when_ac_id_format_is_unrecognized(
        self,
    ) -> None:
        """PR #96 レビュー指摘（HIGH・fail-open、2巡目）: `requirements_has_yaml_ac_frontmatter`
        は素キー（`acceptance_criteria:`）しか検出しないため、引用符付きキー
        （`"acceptance_criteria":`）等の別形式では検出されず、`req_ids` が空集合のまま
        `check_red_evidence_ac_binding` の `if defined_ac_ids:` ガードに戻ってしまい、
        架空 AC 参照が再び exit=0 で通っていた。個別の表記パターンを検出リストに
        追加するのではなく、`defined_ac_ids` が空集合でも RED Evidence の参照 AC を
        すべて未定義として扱う（guard を反転）ことで、YAML の表記に依存しない形で
        この fail-open クラスタ自体を閉じる（ユーザー承認: 広い側デフォルト）。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-quoted-key-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "---\n"
                '"acceptance_criteria":\n'
                "  - id: AC-1\n"
                "    description: quoted key yaml\n"
                "---\n\n"
                "## 目的\nテスト\n",
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "### Current Task\n"
                "\n"
                "#### RED Evidence\n"
                "- AC: AC-99\n"
                "- command: pytest\n",
                encoding="utf-8",
            )
            result = run_lint("--steering-dir", str(steering))

        self.assertEqual(
            result.returncode,
            1,
            msg=f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn("ERROR", result.stdout)

    def test_yaml_frontmatter_migration_error_message_has_no_word_concatenation(
        self,
    ) -> None:
        """独立レビュー指摘（medium）: 隣接文字列リテラルの連結時にスペースが抜け、
        `markdown` と `bullet` が結合した `markdownbullet` という1語に見えていた。
        メッセージの語境界を固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-yaml-msg-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "---\n"
                "acceptance_criteria:\n"
                "  - id: AC-1\n"
                "    description: yaml backed\n"
                "---\n\n"
                "## 目的\nテスト\n",
                encoding="utf-8",
            )
            result = run_lint("--steering-dir", str(steering))

        self.assertNotIn("markdownbullet", result.stdout)
        self.assertIn("markdown bullet", result.stdout)

    def test_yaml_frontmatter_detection_ignores_commented_out_field(self) -> None:
        """独立レビュー指摘（low〜medium）: `requirements_has_yaml_ac_frontmatter` は
        `acceptance_criteria:` の単純な部分文字列一致のため、YAML コメント化された
        旧フィールド（実質的な AC 定義ではない）でも True になり、markdown bullet も
        無い early planning 文書が誤って ERROR（fail-closed 方向の誤検知）になる。
        コメント行は無視することを固定する。"""
        text = (
            "---\n"
            "title: 移行中のドキュメント\n"
            "# acceptance_criteria: 旧形式。markdown bulletへ移行済みのため無視すること\n"
            "---\n\n"
            "## 受入条件\n(まだ書いていない。early planning)\n"
        )
        self.assertFalse(self.mod.requirements_has_yaml_ac_frontmatter(text))

    def test_strict_promotes_unverified_ac_warn_to_error(self) -> None:
        """PR #96 レビュー指摘（MEDIUM）: `--strict` の WARN→ERROR 昇格（未verify AC）を
        固定するテストが無かった。既定では WARN（exit=0）、`--strict` では ERROR（exit=1）
        になることを両方固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-strict-unverified-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "## 受入条件\n- AC-1: verifyされないAC\n",
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "### Current Task\n",
                encoding="utf-8",
            )
            default_result = run_lint("--steering-dir", str(steering))
            strict_result = run_lint("--strict", "--steering-dir", str(steering))

        self.assertEqual(
            default_result.returncode,
            0,
            msg=f"stdout={default_result.stdout!r} stderr={default_result.stderr!r}",
        )
        self.assertIn("WARN", default_result.stdout)
        self.assertEqual(
            strict_result.returncode,
            1,
            msg=f"stdout={strict_result.stdout!r} stderr={strict_result.stderr!r}",
        )
        self.assertIn("ERROR (strict)", strict_result.stdout)

    def test_strict_promotes_missing_red_evidence_ac_line_warn_to_error(self) -> None:
        """PR #96 レビュー指摘（MEDIUM）: `--strict` の WARN→ERROR 昇格（RED Evidence の
        `AC:` 行欠落）を固定するテストが無かった。既定では WARN（exit=0）、`--strict` では
        ERROR（exit=1）になることを両方固定する。"""
        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-strict-missing-red-") as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(
                "## 受入条件\n- AC-1: 基本挙動\n",
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "### Current Task\n"
                "- Verification: method=ac:AC-1\n"
                "\n"
                "#### RED Evidence\n"
                "- command: pytest\n",
                encoding="utf-8",
            )
            default_result = run_lint("--steering-dir", str(steering))
            strict_result = run_lint("--strict", "--steering-dir", str(steering))

        self.assertEqual(
            default_result.returncode,
            0,
            msg=f"stdout={default_result.stdout!r} stderr={default_result.stderr!r}",
        )
        self.assertIn("WARN", default_result.stdout)
        self.assertEqual(
            strict_result.returncode,
            1,
            msg=f"stdout={strict_result.stdout!r} stderr={strict_result.stderr!r}",
        )
        self.assertIn("ERROR (strict)", strict_result.stdout)


# ===========================================================================
# AC-10（T-6）: canonical な method セル（`method=ac:<id>` の表形式行）は、
# 必ず lint-ac.py の AC 参照抽出で拾われることを pin する（design.md § 6
# 「lint-ac 整合」/ requirements.md AC-10）。
#
# 現行 `AC_REF_RE` は `method\s*[=:]?\s*ac\s*:\s*<id>` で既に `method=ac:<id>`
# を拾うため、この契約テストは**追加の regex 変更なしで GREEN になる**
# （tasklist.md T-6 Step 1 で実測・確認済み）。RED は無い —
# `gdd-test-driven-development` § Expected RED Failure Verification が言う
# 「test passes immediately なら RED ではない」に該当するため、本テストは
# characterization / regression pin として追加する（本タスクは
# `scripts/lint-ac.py` を Verify のみで Modify しない）。
# ===========================================================================

_AC10_IDS = ["AC-1", "AC-2a", "AC-F1", "AC-3-d", "AC-E9-1", "AC-E9-1a"]


class DoneGuardCanonicalMethodCellIsAlwaysExtractedByLintAcTests(unittest.TestCase):
    """AC-10: canonical method セルが常に lint-ac の参照抽出に乗ることを一方向で pin する。

    `.steering/` 実物は gitignore 対象で CI から見えないため fixture の
    requirements / tasklist ペア（tempdir）で検証する（AC-10 本文）。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_plugin_module("scripts/lint-ac.py")

    def test_canonical_method_cell_is_extracted_for_each_ac_id(self) -> None:
        for ac_id in _AC10_IDS:
            with self.subTest(ac_id=ac_id), tempfile.TemporaryDirectory(
                prefix="gdd-lint-ac-canonical-"
            ) as tmp:
                root = Path(tmp)
                (root / "requirements.md").write_text(
                    f"## 受入条件\n\n- **{ac_id}**: ダミー AC\n", encoding="utf-8"
                )
                (root / "tasklist.md").write_text(
                    "## Verification\n"
                    "| method | status | evidence | notes |\n"
                    "|---|---|---|---|\n"
                    f"| method=ac:{ac_id} | pass | npm test 通過 | - |\n",
                    encoding="utf-8",
                )
                result = run_lint("--steering-dir", str(root))

                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"ac_id={ac_id} stdout={result.stdout!r} stderr={result.stderr!r}",
                )
                self.assertNotIn(
                    "verify されない",
                    result.stdout,
                    msg=f"ac_id={ac_id}: canonical method セルが未 verify 扱いになった",
                )
                # 直接 API でも同じことを pin する（実関数名は `extract_ac_ids_from_tasklist`。
                # tasklist.md Step 2 の下書きが仮定した `extract_ac_refs` は存在しない）。
                refs = self.mod.extract_ac_ids_from_tasklist(
                    f"| method=ac:{ac_id} | pass | npm test 通過 | - |\n"
                )
                self.assertIn(ac_id, refs)


if __name__ == "__main__":
    unittest.main()
