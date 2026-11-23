"""Unit tests for scripts/lint-hitl-required-fields.py (declared-field redesign)。

実測: `references/human-check-template-compact.md` の条件付き節
（「〜場合だけ」）は AI の判断に委ねられており、未記録と「該当なし」が
区別できない。また、HITL の大半で Option ラベルが 0 個だった。

方針メモ（2026-09-15、ユーザー確認）: この lint は warn-only で配線する
（`hooks/scripts/lib/hitl_lint_gate.py` の HITL_LINT_WARN_SCRIPTS）。

## 設計変更（このファイルの再設計）

PR #92 の初期実装は、4つの条件付き節が固定句（「該当なし（理由: ...）」等）や
Option ラベルを本文から生テキスト一致で探す raw-text-match 方式だった。
`references/human-check-template-compact.md` の各節 placeholder 自身が、
未編集のまま例示として同じ固定句・Option ラベルを含んでいたため、独立レビュー
1巡目・PR後レビュー1巡目・独立レビュー2巡目の時点で同一クラスタ
（raw-text-match-vs-placeholder）の fail-open が3巡連続で再発した
（review-log/20260915-x60-x57-hitl-required-fields.md の F1/G1/H1 参照）。

「宣言フィールド化」（本文を一切解釈せず、著者が明示的に宣言した閉じた語彙の
タグだけを見る）へ再設計した後も、タグの境界検出（フェンス・HTML コメント・
インデントコードブロックの構文列挙で「例示」を除外する方式）で同クラスタが
PR後レビュー2巡目まで**4巡連続**で再発した（`f1_infostring_closer` 等、
review-log/20260916-x60-hitl-declared-fields.md の I1〜I3 参照）。独立-2 で
合意した「CommonMark のコードブロックは3種で閉じた集合」という打ち切り根拠
自体が誤りだったため（`<pre>`/`<textarea>` 等の HTML block が未列挙）、
構文列挙という手段そのものを放棄し、Opus（claude-opus-5）セカンドオピニオンを
経て**位置契約**（markdown 構文を一切解釈せず、`_HITL_STOP_MARKER` の直前で
空行だけを飛ばした最初の非空行がスタンドアロンなタグ行かどうかだけを見る）に
再設計した。構文の種類を列挙しないため、未列挙の構文で再発する経路が構造的に
無くなる（`AdjacencyContractTests` で固定する）。

本文中に `該当なし` や `Option A` という文字列が何個あっても、
`<gdd-hitl-fields ...>` タグの宣言値が正しくなければ合格しない——逆に本文が
空でも、宣言が正しければ合格する。これにより raw-text-match-vs-placeholder
クラスタは構造的に再発しえなくなる（`BodyContentIrrelevantToVerdictRegressionTests`
で固定する）。

宣言値そのものの真偽（本当に該当なしか、本当に記入したか）は検証しない
——`承認ポイント数: <N>` 宣言フィールドと同じ、他の固定フィールドと
同じ自己申告の信頼境界（`~/.claude/skills 等` ではなく本 plugin の既存設計と
同一の考え方）。

subprocess 経由でスクリプトを起動する（in-process import はしない）。
`scripts/lib/` と `hooks/scripts/lib/` は同名パッケージ `lib` を持つため、
pytest -n auto の同一 worker プロセス内で両方を `sys.path` へ乗せて import
すると片方が sys.modules を汚染する（実測、他 lint contract test と同じ
subprocess 方式に統一する）。

正本: `references/human-check-template-compact.md`、
review-log/20260916-x60-hitl-declared-fields.md。

Run from plugins/gate-driven-development/:
  python3 -m unittest tests.test_lint_hitl_required_fields -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
SCRIPT = PLUGIN_ROOT / "scripts" / "lint-hitl-required-fields.py"
HITL_MARKER = '<gdd-stop reason="human-check-waiting">'

FIELD_SECTIONS = (
    ("options", "選択肢の説明"),
    ("arch", "アーキテクチャ選択"),
    ("zure", "ズレ確認"),
    ("multi-pr", "Multiple PR Strategy Options"),
    ("stage", "段階実装"),
)


def _run(text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "hitl.md"
        path.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            text=True,
            capture_output=True,
            check=False,
        )


def _fields_tag(
    options: str = "none",
    arch: str = "none",
    zure: str = "none",
    multi_pr: str = "none",
    stage: str = "none",
) -> str:
    return (
        f'<gdd-hitl-fields options="{options}" arch="{arch}" '
        f'zure="{zure}" multi-pr="{multi_pr}" stage="{stage}">'
    )


# 宣言タグのみを持つ最小の合格ドキュメント。本文（節見出し・説明文）は
# lint の判定に一切影響しないため、意図的に持たせない
# （`BodyContentIrrelevantToVerdictRegressionTests` 参照）。
COMPLIANT_DOC = f"""\
## 確認

{_fields_tag()}

{HITL_MARKER}
"""


class DeclaredFieldPresenceTests(unittest.TestCase):
    def test_compliant_doc_passes(self):
        result = _run(COMPLIANT_DOC)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_tag_entirely_reports_four_errors(self):
        doc = f"## 確認\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 1)
        for _, label in FIELD_SECTIONS:
            self.assertIn(label, result.stdout, result.stdout)

    def test_missing_one_attribute_reports_only_that_section(self):
        """タグ自体はあるが `zure` 属性だけを欠く場合、ズレ確認だけを指摘し、
        他の3属性は正しく宣言されているので合格側として扱う（他属性のエラーを
        道連れにしない）。"""
        doc = (
            "## 確認\n\n"
            '<gdd-hitl-fields options="none" arch="none" multi-pr="none">\n\n'
            f"{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ズレ確認", result.stdout)
        self.assertNotIn("選択肢の説明", result.stdout)
        self.assertNotIn("アーキテクチャ選択", result.stdout)
        self.assertNotIn("Multiple PR Strategy Options", result.stdout)

    def test_invalid_attribute_value_reports_only_that_section(self):
        doc = COMPLIANT_DOC.replace('arch="none"', 'arch="not-a-real-value"')
        result = _run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("アーキテクチャ選択", result.stdout)
        self.assertNotIn("選択肢の説明", result.stdout)
        self.assertNotIn("ズレ確認", result.stdout)
        self.assertNotIn("Multiple PR Strategy Options", result.stdout)

    def test_empty_attribute_value_is_rejected(self):
        doc = COMPLIANT_DOC.replace('zure="none"', 'zure=""')
        result = _run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ズレ確認", result.stdout)

    def test_all_four_filled_passes_without_any_specific_body_content(self):
        """`filled` 宣言は自己申告であり、本文の内容は一切検証しない
        （`承認ポイント数: <N>` と同じ信頼境界。Known limitations に
        開示済み）。"""
        doc = (
            "## 確認\n\n"
            + _fields_tag(
                options="filled", arch="filled", zure="filled", multi_pr="filled", stage="filled"
            )
            + f"\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class StageAxisDeclaredFieldTests(unittest.TestCase):
    """5 つ目の属性 `stage`（段階実装の節を書いたか）。none は段階が 1 つだけで節を
    書かない、filled は複数段階・後続 PR 前の再承認などで節を書いた。"""

    def test_stage_none_and_filled_both_pass(self):
        for value in ("none", "filled"):
            with self.subTest(value=value):
                result = _run(f"## 確認\n\n{_fields_tag(stage=value)}\n\n{HITL_MARKER}\n")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_stage_attribute_warns_only_about_stage(self):
        doc = (
            "## 確認\n\n"
            '<gdd-hitl-fields options="none" arch="none" zure="none" multi-pr="none">\n\n'
            f"{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("段階実装", result.stdout)
        self.assertIn("`stage`", result.stdout)
        self.assertNotIn("ズレ確認", result.stdout)

    def test_invalid_stage_value_is_rejected(self):
        for value in ("single", "none|filled", ""):
            with self.subTest(value=value):
                result = _run(f"## 確認\n\n{_fields_tag(stage=value)}\n\n{HITL_MARKER}\n")
                self.assertEqual(result.returncode, 1)
                self.assertIn("段階実装", result.stdout)


class AdjacencyContractTests(unittest.TestCase):
    """位置契約（PR後-2 I1〜I4、review-log/20260916-x60-hitl-declared-fields.md
    の「方針メモ」参照、Opus セカンドオピニオンによる再設計）。

    フェンス種別・HTML コメント・インデントコードブロックを列挙する方式は、
    独立-1 → PR後-1 → 独立-2 → PR後-2 と4巡連続で同一クラスタ
    （raw-text-match-vs-placeholder、本文中の"例示"を本物と誤認する）を
    再発させた。未列挙の構文（info string 付き閉じ行、同一行のコメント
    再オープン、`<pre>`/`<textarea>` 等の HTML block）が見つかるたびに
    再発する構造的な問題であることが確定したため、markdown 構文の列挙を
    やめ、「`_HITL_STOP_MARKER` の直前で、空行だけを飛ばした最初の非空行が
    ちょうどスタンドアロンな `<gdd-hitl-fields ...>` 行であること」だけを
    見る位置契約に置き換えた。

    残存する意図的な境界（Known limitations、独立-4/PR後-4 で訂正）:
    フェンス・HTML コメント・`<pre>` 等の中でタグと marker が直接隣接
    する「完結したペア」になっていれば、その構文を閉じているかどうかに
    関わらず合格する
    （`test_tag_and_marker_pair_completed_inside_a_closed_fence_still_passes`
    参照）。位置契約はマーカー直前の非空行だけを見て markdown 構文を一切
    解釈しないため、「閉じているかどうか」は判定に影響しない——旧版の
    本 docstring は「正しく閉じていれば reject する」と誤って記載して
    いた。ただし universal quantification（`hitl_fields.hitl_check_points` が全
    occurrence を列挙）により、この完結ペアが「本物」の代わりになる
    ことはない。`test_tag_inside_a_properly_closed_fence_is_ignored` が
    reject するのは、フェンス内にタグだけを置き marker をフェンス外に
    出しているため——marker 直前の非空行がタグ行ではなくフェンスの
    閉じ行になり、隣接契約そのものに反する別のケースである（構文が
    閉じているから reject されるわけではない）。この場合 hook 自身
    （`gdd_stop_hook.py::_check_stop_markers`）も同じマーカーで実際に
    pause しており、宣言とマーカーの対応は整合しているため実害クラス
    ではない。
    """

    def test_tag_immediately_before_marker_passes(self):
        result = _run(COMPLIANT_DOC)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_multiple_blank_lines_between_tag_and_marker_still_passes(self):
        doc = "## 確認\n\n" + _fields_tag() + f"\n\n\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tag_followed_by_prose_before_marker_is_rejected(self):
        """PR レビュー（PR #94、Medium）由来の逆側: タグの後に説明文が
        続いてからマーカーが来る場合、タグはマーカーに隣接していないため
        無視され reject する（fail-closed）。テンプレートどおりタグを
        マーカー直前に置けば発生しない、位置契約に伴う意図的な制約
        （Known limitations）。"""
        doc = (
            "## 確認\n\n"
            + _fields_tag()
            + f"\n\n実装では `<gdd-hitl-fields>` タグを新設した。\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_last_standalone_line_before_marker_wins_even_if_an_earlier_valid_tag_exists(self):
        """マーカー直前だけを見るため、下書き・修正前の例示タグが先に
        あっても、マーカー直前にある本物（値が不正）が判定対象になる。"""
        doc = (
            "## 確認\n\n"
            "(下書き例: "
            + _fields_tag(options="filled", arch="filled", zure="filled", multi_pr="filled")
            + ")\n\n"
            + _fields_tag(zure="not-a-real-value")
            + f"\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ズレ確認", result.stdout)

    def test_blockquoted_tag_immediately_before_marker_is_never_standalone(self):
        doc = "## 確認\n\n> " + _fields_tag() + f"\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_inline_code_tag_immediately_before_marker_is_never_standalone(self):
        doc = "## 確認\n\n" + f"タグの書式は `{_fields_tag()}` のようになる。\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_tag_outside_a_fenced_code_block_still_counts_even_with_a_fence_present(self):
        doc = (
            "## 確認\n\n"
            "書式の例:\n```\nsome unrelated fenced content\n```\n\n"
            + _fields_tag()
            + f"\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tag_inside_a_properly_closed_fence_is_ignored(self):
        doc = "## 確認\n\n書式の例:\n```\n" + _fields_tag() + f"\n```\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for _, label in FIELD_SECTIONS:
            self.assertIn(label, result.stdout, result.stdout)

    def test_tag_inside_an_unclosed_fence_immediately_before_marker_is_accepted(self):
        """PR後-2 I1 由来の残存境界（Known limitations）。フェンスを閉じ
        忘れたまま、タグの直後にマーカーが続く場合は markdown 構文を見ない
        ため合格する。"""
        doc = "## 確認\n\n書式の例（閉じ忘れ）:\n```\n" + _fields_tag() + f"\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fence_closed_by_a_line_with_trailing_prose_no_longer_matters(self):
        """PR後-2 I1: 旧フェンス状態機械は info string 付きの閉じ行
        （閉じフェンス文字列の後に文字が続く行）を「閉じ」と誤判定して
        いた。新設計はフェンス状態を一切追跡しないため、このバグの
        クラス自体が存在しない——例示タグがマーカーから離れていれば
        （間に他の行があれば）常に無視される。"""
        doc = (
            "## 確認\n\n```\nsome code\n```prose after closer\n"
            + _fields_tag()
            + f"\n\n(この後に説明が続く)\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_tag_inside_a_properly_closed_html_comment_is_ignored(self):
        doc = "## 確認\n\n<!--\n" + _fields_tag() + f"\n-->\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_html_comment_reopened_on_the_same_line_no_longer_matters(self):
        """PR後-2 I2: 旧コメント状態追跡は同一行内で `-->` の後に `<!--`
        が続く「再オープン」を扱えなかった。新設計はコメント状態を一切
        追跡しないため、このバグのクラス自体が存在しない。"""
        doc = (
            "## 確認\n\n<!-- 説明 -->  <!--\n"
            + _fields_tag()
            + f"\n-->\n\n(この後に説明が続く)\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_tag_inside_a_properly_closed_pre_block_is_ignored(self):
        """PR後-2 I3: `<pre>` を正しく閉じていれば閉じタグ行が挟まるため
        reject する。"""
        doc = "## 確認\n\n<pre>\n" + _fields_tag() + f"\n</pre>\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_tag_inside_an_unclosed_pre_block_immediately_before_marker_is_accepted(self):
        """PR後-2 I3 由来の残存境界（Known limitations）: 独立-2 で合意した
        「CommonMark のコードブロックは3種で閉じた集合」という前提自体が
        誤りで、`<pre>`/`<textarea>` 等の HTML block はいずれの3種にも
        該当しなかった。新設計は構文の種類を問わないため、閉じ忘れの
        `<pre>` でも他の未閉じ構文と同じ扱いになる。"""
        doc = "## 確認\n\n<pre>\n" + _fields_tag() + f"\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_indented_tag_immediately_before_marker_is_accepted(self):
        """独立-2 で問題視された4スペースインデントコードブロックも、
        構文を見ない新設計では単に行の前後空白を無視するだけであり、
        隣接していれば合格する（意図的な境界、Known limitations）。"""
        doc = "## 確認\n\n書式の例:\n\n    " + _fields_tag() + f"\n\n{HITL_MARKER}\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tag_and_marker_pair_completed_inside_a_closed_fence_still_passes(self):
        """独立-4 / PR後-4 由来: 「正しく閉じていれば reject する」という
        旧 docstring の誤りをテストで固定する。タグと marker が直接隣接
        する完結したペアであれば、そのペアを含む構文を後で正しく閉じても
        合格する（閉じているかどうかは判定に影響しない）。"""
        doc = "## 確認\n\n```\n" + _fields_tag() + f"\n{HITL_MARKER}\n```\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fieldsets_prefix_line_is_not_a_standalone_tag_line(self):
        """`_STANDALONE_TAG_LINE_RE` の接頭辞境界（PR レビュー指摘由来）を
        位置契約の下で固定する。`<gdd-hitl-fieldsets ...>` はタグ名の
        接頭辞一致に過ぎず、正規表現がこの境界を失うと緑のまま通る。"""
        doc = (
            "## 確認\n\n"
            '<gdd-hitl-fieldsets options="none" arch="none" zure="none" multi-pr="none">\n\n'
            f"{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_tag_line_with_trailing_prose_on_the_same_line_is_not_standalone(self):
        """タグの直後、同じ行内に説明文が続く場合はスタンドアロンなタグ行
        ではないため無視される（`_STANDALONE_TAG_LINE_RE` の行末 `$`
        境界）。"""
        doc = (
            "## 確認\n\n"
            + _fields_tag().rstrip(">")
            + '> このタグを新設した\n\n'
            + f"{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_unquoted_attribute_value_is_rejected_not_silently_accepted(self):
        """タグ行自体はスタンドアロンな形を保っていても、属性値がダブル
        クォートで囲まれていなければ `_HITL_FIELD_ATTR_RE` が抽出せず、
        「属性自体がありません」として reject する（非ダブルクォート値を
        黙って受理しない）。"""
        doc = (
            "## 確認\n\n"
            '<gdd-hitl-fields options=none arch="none" zure="none" multi-pr="none">\n\n'
            f"{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("選択肢の説明", result.stdout)


class ExceptionSafetyTests(unittest.TestCase):
    """L1+ 安全策2: block / allow の判定を変える修正では、(1) block すべき
    入力が allow になる (2) 例外で guard 全体が落ちる (3) 判定できない
    ときに通ってしまう、の3ケースを先に固定する。(1) は
    `AdjacencyContractTests` の `_no_longer_matters` 系で固定済み。ここでは
    (2)(3) を固定する。"""

    def test_empty_document_does_not_raise_and_is_rejected(self):
        result = _run("")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_document_with_only_a_marker_does_not_raise(self):
        result = _run(HITL_MARKER + "\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_document_with_no_marker_at_all_does_not_raise(self):
        """stop marker 自体が無い（本来 lint が呼ばれない状況の防御的
        確認）。`hitl_fields.hitl_check_points` は marker が無ければ文書末尾を1点だけ
        対象にするため、末尾直前の非空行を通常どおり評価する。"""
        result = _run("## 確認\n\n" + _fields_tag() + "\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_malformed_tag_missing_closing_quote_is_rejected_not_crashed(self):
        """属性値の閉じクォートが無い等、壊れた属性構文は正規表現が
        マッチしないため通常の「属性自体がありません」分岐に落ちる
        （クラッシュしない、fail-closed）。"""
        doc = '## 確認\n\n<gdd-hitl-fields options="none arch="none" zure="none" multi-pr="none">\n\n' + HITL_MARKER + "\n"
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


class OptionAxisDeclaredFieldTests(unittest.TestCase):
    """Option 軸も `options` 属性の宣言だけで判定する。`Option A/B` の
    出現回数を本文から数える経路はこの再設計で撤去した（raw-text-match の
    復活を防ぐため、意図的に持たない）。"""

    def test_options_none_passes_without_any_option_label_in_body(self):
        result = _run(COMPLIANT_DOC)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_options_filled_passes_without_actual_option_labels_in_body(self):
        doc = COMPLIANT_DOC.replace('options="none"', 'options="filled"')
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_options_attribute_missing_names_the_selection_section(self):
        doc = (
            "## 確認\n\n"
            '<gdd-hitl-fields arch="none" zure="none" multi-pr="none">\n\n'
            f"{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("選択肢の説明", result.stdout)


def _extract_unedited_template() -> str:
    """`references/human-check-template-compact.md` の ```markdown フェンス
    内（未編集テンプレートそのもの）を抽出する。ハードコードした合成文字列
    ではなく実ファイルから動的に取るのは、テンプレートの placeholder 文言が
    将来変わっても正本とテストが食い違ったまま放置されるのを防ぐため。
    """
    text = (PLUGIN_ROOT / "references" / "human-check-template-compact.md").read_text(
        encoding="utf-8"
    )
    start = text.index("```markdown\n") + len("```markdown\n")
    end = text.index("\n```", start)
    return text[start:end]


class UneditedTemplateRegressionTests(unittest.TestCase):
    """未編集テンプレートは `<gdd-hitl-fields>` の各属性がプレースホルダー値
    （閉じた語彙 `none`/`filled` のどちらでもない）のままのため、4属性すべてが
    reject される（fail-closed）。"""

    def test_completely_unedited_template_is_rejected_on_all_four_fields(self):
        unedited = _extract_unedited_template()
        result = _run(unedited)
        self.assertEqual(
            result.returncode,
            1,
            f"未編集テンプレートは reject されるべき: {result.stdout}{result.stderr}",
        )
        for _, label in FIELD_SECTIONS:
            self.assertIn(
                label,
                result.stdout,
                f"未編集テンプレートは {label} を reject するはずが、していない: {result.stdout}",
            )

    def test_unedited_template_is_rejected_via_the_invalid_value_branch_not_the_missing_tag_branch(self):
        """PR レビュー（gdd-pr-review、PR #94、Medium）: タグ自体は Template に
        存在する（未編集でも欠落ではない）ため、「宣言がありません」（タグ
        欠落）ではなく「値は許容されていません」（タグはあるが値が閉じた
        語彙の外）の分岐で reject されるはずである。この区別が無いと、タグ
        欠落と placeholder 値のどちらでも同じ「4ラベル + rc=1」の出力に潰れ、
        changelog が固定すると書いた性質をテストが検出できない。"""
        unedited = _extract_unedited_template()
        result = _run(unedited)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("は許容されていません", result.stdout, result.stdout)
        self.assertNotIn("の宣言がありません", result.stdout, result.stdout)


class BodyContentIrrelevantToVerdictRegressionTests(unittest.TestCase):
    """raw-text-match-vs-placeholder クラスタ（F3 → G1 → H1/H2 → I1〜I3、
    review-log 参照）の再発防止の要。この再設計では判定材料が `<gdd-hitl-fields>` タグ
    だけであり、本文（節見出し・placeholder の例示文言・Option ラベルの
    地の文言及）が何を含んでいても判定に影響しないことを固定する。

    （Opus 設計レビュー H-3 の再検証）旧設計は `_is_substantial()`
    （12文字以上の可視テキスト）という本文の長さヒューリスティックを持ち、
    placeholder の角括弧だけを取り除いた説明文がこの閾値を超えて誤って
    合格しうる欠陥が残っていた（本PRのスコープでは未解決として開示されて
    いた）。この再設計は本文の長さ・内容を一切見ないため、この経路は
    構造的に閉じている（`test_valid_tag_passes_even_with_untouched_looking_body`
    がこれを固定する）。
    """

    def test_decoy_body_with_old_na_phrases_and_option_labels_does_not_rescue_a_missing_tag(self):
        """旧設計が探していた固定句・Option ラベルを本文にいくら並べても、
        `<gdd-hitl-fields>` タグそのものが無ければ reject する（旧方式への
        先祖返りが無いことの確認）。"""
        doc = (
            "## 確認\n\n"
            "### 選択肢の説明\n選択肢なし（単一案。理由: 対象が1案しかないため）\n\n"
            "### アーキテクチャ選択\n選択肢なし（単一案。理由: 既存 repo 標準をそのまま使うため）\n\n"
            "### ズレ確認\n該当なし（理由: 後戻りが大きい論点が無いため）\n\n"
            "### Multiple PR Strategy Options\n該当なし（単一PRで完結。理由: 変更が1ファイルに閉じるため）\n\n"
            "Option A: 既存実装を再利用する\nOption B: 新規に作り直す\n\n"
            + HITL_MARKER
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for _, label in FIELD_SECTIONS:
            self.assertIn(label, result.stdout, result.stdout)

    def test_valid_tag_passes_even_with_untouched_looking_body(self):
        """タグの宣言さえ正しければ、本文が未編集の placeholder 文言そのもの
        （角括弧だけ取り除いた長い説明文を含む）でも合格する。本文の内容検証を
        一切行わない設計であることの直接証跡（H-3 はこの再設計では検証対象
        自体が無くなるため、再現しえない）。"""
        doc = (
            "## 確認\n\n"
            "### 選択肢の説明\n"
            "Option A / B / C を使うなら 1〜3 行。Option B だけを出さず、各案の"
            "「何をする案か / 良い点 / 弱い点 / AIの仮決定」を書く。単一案なら "
            "選択肢なし（単一案。理由: ...）\n\n"
            + _fields_tag()
            + f"\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class FirstHitlSegmentIsolationRegressionTests(unittest.TestCase):
    """PR #92 後レビュー（5巡目、実機で再現確認済み）で「最初の marker 出現
    だけをアンカーする」設計にしたが、PR #94 再レビュー（PR後-3）は、これが
    「先に compliant な例（別 HITL の引用・下書き等）があると、後ろの
    本物（タグ無し）が無審査で合格する」という新しい fail-open
    （`h1_plain_echo` 等、rc=0 で実機再現確認済み）を生むことを指摘した。
    raw-text-match-vs-placeholder クラスタの派生形——「例示・引用が本物の
    代わりに審査され、本物がすり抜ける」という failure mode 自体は一貫して
    いる。

    L1+ 安全策4 に基づく再検討の結果、「最初の1個だけを見る」existential な
    契約から、「文書中に現れる `_HITL_STOP_MARKER` の**すべての出現**それぞれに
    ついて隣接宣言を要求する」universal な契約へ拡張した（`MultipleMarkerOccurrencesRequireDeclarationRegressionTests`
    参照）。これは同じ入力空間（`_HITL_STOP_MARKER` に隣接する宣言の有無）を
    より広く（fail-closed 方向に）検査するだけであり、markdown 構文の列挙には
    戻らない。
    """

    def test_noncompliant_first_hitl_followed_by_a_compliant_later_one_is_rejected(self):
        """1つ目が非 compliant（タグ無し）なら、その後ろに compliant な内容
        （下書きの清書・別 HITL の引用等）が続いていても reject する
        （universal 契約でも、最初の occurrence 単独で既に reject 対象）。"""
        doc = (
            f"## 確認（本番）\n\n{HITL_MARKER}\n"
            + "\n\n(参考までに、コンプライアントな例を示す)\n\n"
            + COMPLIANT_DOC
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_compliant_first_hitl_followed_by_a_noncompliant_later_one_is_now_rejected(self):
        """（PR後-3 で反転）1つ目が compliant でも、後ろに非 compliant な
        occurrence があれば universal 契約により reject する。以前はここが
        `passes`（rc=0）だったこと自体が fail-open だった。"""
        doc = (
            COMPLIANT_DOC
            + "\n\n(以下は前回の HITL の引用)\n\n"
            + f"## 確認\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


class MultipleMarkerOccurrencesRequireDeclarationRegressionTests(unittest.TestCase):
    """PR #94 再レビュー（PR後-3、High・blocking）: 位置契約が「最初の
    `_HITL_STOP_MARKER` occurrence」だけをアンカーしていたため、先に
    compliant な組（宣言タグ＋marker）があると、それがどんな構文
    （地の文・フェンス・HTML コメント・`<pre>`・チルダフェンス）に包まれて
    いても、後ろにある本物（タグ無し）の HITL が無審査で通っていた
    （`h1_plain_echo` / `h1_fenced_pair` / `h1_comment_pair` / `h1_pre_pair` /
    `h1_tilde_pair`、いずれも rc=0 で実機再現確認済み）。

    位置契約は markdown 構文を一切見ないため、包む構文の違いはそもそも
    判定に影響しない——`_HITL_STOP_MARKER` の**全ての**出現それぞれに隣接
    宣言を要求する universal な契約に変えることで、構文を問わず一括して
    閉じる。
    """

    def _decoy_then_real(self, wrapped_compliant_pair: str) -> str:
        return (
            "## 確認（前回の例）\n\n"
            + wrapped_compliant_pair
            + "\n\n(以下、本当に確認したい本番の内容)\n\n"
            + f"## 確認\n\n{HITL_MARKER}\n"
        )

    def test_h1_plain_echo_decoy_pair_does_not_vouch_for_a_later_undeclared_marker(self):
        doc = self._decoy_then_real(f"{_fields_tag()}\n\n{HITL_MARKER}")
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_h1_fenced_pair_decoy_does_not_vouch_for_a_later_undeclared_marker(self):
        doc = self._decoy_then_real(f"```\n{_fields_tag()}\n\n{HITL_MARKER}\n```")
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_h1_tilde_pair_decoy_does_not_vouch_for_a_later_undeclared_marker(self):
        doc = self._decoy_then_real(f"~~~\n{_fields_tag()}\n\n{HITL_MARKER}\n~~~")
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_h1_comment_pair_decoy_does_not_vouch_for_a_later_undeclared_marker(self):
        doc = self._decoy_then_real(f"<!--\n{_fields_tag()}\n\n{HITL_MARKER}\n-->")
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_h1_pre_pair_decoy_does_not_vouch_for_a_later_undeclared_marker(self):
        doc = self._decoy_then_real(f"<pre>\n{_fields_tag()}\n\n{HITL_MARKER}\n</pre>")
        result = _run(doc)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_two_valid_declarations_for_two_real_markers_both_pass(self):
        """universal 契約は「複数あればすべて正しく宣言せよ」であり、複数
        marker 自体を禁止するわけではない——両方に正しい隣接宣言があれば
        合格する（fail-closed 方向への過剰な締め付けではないことの確認）。"""
        doc = (
            f"## 確認1\n\n{_fields_tag()}\n\n{HITL_MARKER}\n\n"
            f"## 確認2\n\n{_fields_tag()}\n\n{HITL_MARKER}\n"
        )
        result = _run(doc)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ScriptCliTests(unittest.TestCase):
    """CLI 層（exit code / --quiet）は他の lint script と同じ contract を守る。"""

    def test_missing_file_returns_exit_code_2(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "/nonexistent/path.md"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)

    def test_compliant_doc_via_cli_quiet_returns_exit_code_0_and_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hitl.md"
            path.write_text(COMPLIANT_DOC, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--quiet"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")

    def test_noncompliant_doc_via_cli_returns_exit_code_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hitl.md"
            path.write_text(f"## 確認\n\n{HITL_MARKER}\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--quiet"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
