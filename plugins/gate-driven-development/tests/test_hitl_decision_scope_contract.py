"""Contract tests for HITL 承認ポイントの固定フィールド受理文法。

PR #83（branch `20260914-x53-hitl-hitl-narrowing-guard`。closed のまま main 未マージ）は、
「広い側を採用したか」「数値根拠が示されたか」を日本語の自由文から判定しようとして 7 巡
収束しなかった（`gh api repos/.../pulls/83/comments` に実測が残る）。本 PR はその自由文判定を
全廃し、`- 既定範囲: 広い側 | 狭い側` / `- 狭める根拠: <key>=<数値>` という固定フィールドの
行の形だけを見る受理文法に置き換える。

正本: `references/human-check-template.md` § 承認ポイントの固定フィールド受理文法。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
SCRIPT = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"


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


def _point(
    *,
    premise: str = "判断に影響する前提: なし",
    rejected: str = "却下した代替案: 他案なし（単一候補のため）",
    theme: str = "1. <判断テーマ>",
) -> str:
    """`## 確認` の承認ポイント 1 件分の完全な固定フィールドブロックを組み立てる。

    フィールド順は `references/human-check-template.md` § 承認ポイント の
    実物と一致させる（AI の仮決定 → 根拠 → 却下した代替案 → 判断に影響する前提 →
    この案を選ぶと次に何が起きるか → 無回答時のデフォルト）。
    """
    return "\n".join(
        [
            f"{theme}",
            "- AI の仮決定: 案Aを採用する",
            "- 根拠: 既存実装を再利用できるため",
            f"- {rejected}",
            f"- {premise}",
            "- この案を選ぶと次に何が起きるか: 実装がAパターンに揃う",
            "- 無回答時のデフォルト: 案Aを既定採用する",
        ]
    )


def _doc(*points: str) -> str:
    """既存必須マーカーを全て満たした、新チェックだけを単離できる最小 HITL。

    `承認ポイント数: <N>` は `points` の件数から自動算出する（呼び出し側が
    毎回書かずに済むようにする。件数をわざと崩したいテストは `_doc` を使わず
    生の文字列を組み立てる）。
    """
    body = "\n\n".join(points)
    return "\n".join(
        [
            "## 確認",
            "",
            "### 30秒判断",
            "**整理した要件**: 既存コード読解を先に行い、完了条件に沿ってテストを書きます。",
            "**実装する方法・内容**: 既存の HITL contract と lint を更新します。",
            "**検証する方法・内容**: lint smoke と contract test で確認します。",
            "**どこまで自走するのか**: PR 作成まで。merge と deploy は別承認です。",
            "**判断ポイント**: 完了条件と検証範囲が意図通りか。",
            "**段階実装サマリー**: 単一段階: 今回の PR で完結。",
            "",
            "### OKで進む範囲",
            "既存コード読解を先に行い、HITLで見えた完了条件に沿ってテストを書きます。",
            "",
            "### OKでも許可されないこと",
            "本番反映、外部投稿、追加の仕様変更は承認しません。",
            "",
            "### 現在地",
            "| 項目 | 内容 |",
            "|---|---|",
            "| 人間が今やること | 上の内容が意図どおりか確認して OK と返す |",
            "| OK 後に残る作業 | 設計、テスト、実装、PRレビュー後ループ |",
            "",
            "### PR検証後の次の導線",
            "| PR検証後の状態 | 次にやること | 同じチャットで続けるか / 新しいチャットか |",
            "|---|---|---|",
            "| PR の検証・レビューが通った | merge は人間判断 | 新しいチャット推奨 |",
            "",
            "### 人間に戻す条件",
            "完了条件、技術スタック、外部公開範囲が変わる場合。",
            "",
            "### 承認ポイント",
            "",
            f"承認ポイント数: {len(points)}",
            "",
            body,
            "",
            "### ズレ確認",
            "**完了条件の変換**（変換・延期・削除した条件だけ）",
            "延期・削除: なし",
        ]
    )


class HitlDecisionScopeContractTests(unittest.TestCase):
    # --- 既定範囲・狭める根拠の欄は撤去した（数値を示せば狭い側を既定にできる道を残さない） ---

    def test_point_without_scope_fields_is_accepted(self) -> None:
        result = _run(_doc(_point()))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("既定範囲", result.stdout)

    def test_each_of_several_points_without_scope_fields_is_accepted(self) -> None:
        points = [_point(theme=f"{n}. <判断テーマ{n}>") for n in (1, 2)]
        result = _run(_doc(*points))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    # --- 件数による分岐を作らない（1件でも複数件でも同じ経路） ---


    def test_three_points_all_valid_is_accepted(self) -> None:
        points = [
            _point(theme=f"{n}. <判断テーマ{n}>")
            for n in (1, 2, 3)
        ]
        result = _run(_doc(*points))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    # --- 自由文からは一切判定しない（免疫の確認） ---

    def test_free_text_mentioning_broad_and_narrow_does_not_trigger_scope_check(self) -> None:
        """固定フィールド行にマッチしない地の文は、既定範囲チェックの対象外。

        旧設計（PR #83）はこの手の文を自由文解析で誤判定していた。新設計は
        `- 既定範囲: ` という行の形にしかマッチしないため、地の文は無視されるだけで
        良くも悪くも判定に一切影響しない。
        """
        text = _doc(
            "\n".join(
                [
                    "1. <判断テーマ>",
                    "- 無回答時のデフォルト: 案Aを既定採用する",
                    "広い側は採用せず、ASCIIだけに限定する。既定範囲: 狭い側。",
                ]
            )
        )
        result = _run(text)
        # 既定範囲: フィールドの行が無いので scope チェックはそもそも発火しない。
        # 判断に影響する前提 / 却下した代替案 のチェックだけが働き、reject される。
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("既定範囲の値が不正", result.stdout)

    # --- 例外で guard 全体が落ちない（fail-open 安全策） ---


    def test_empty_document_does_not_crash(self) -> None:
        result = _run("")
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    # --- C: 判断に影響する前提 / 却下した代替案（採用しない案） ---

    def test_missing_premise_field_is_rejected(self) -> None:
        text = _doc(
            "\n".join(
                [
                    "1. <判断テーマ>",
                    "- 却下した代替案: 他案なし（単一候補のため）",
                    "- 無回答時のデフォルト: 案Aを既定採用する",
                ]
            )
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("判断に影響する前提", result.stdout)

    def test_premise_field_with_naught_value_is_accepted(self) -> None:
        """`なし` は正当な値（欠落禁止であって、非空必須ではない）。誤って placeholder 扱いしない。"""
        result = _run(_doc(_point(premise="判断に影響する前提: なし")))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_premise_field_with_unfilled_placeholder_is_rejected(self) -> None:
        result = _run(_doc(_point(premise="判断に影響する前提: <この前提が崩れたら結論が変わる条件を1行>")))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_missing_rejected_alternative_field_is_rejected(self) -> None:
        text = _doc(
            "\n".join(
                [
                    "1. <判断テーマ>",
                    "- 判断に影響する前提: なし",
                    "- 無回答時のデフォルト: 案Aを既定採用する",
                ]
            )
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("却下した代替案", result.stdout)

    def test_compact_style_adopted_alternative_label_is_accepted(self) -> None:
        """compact 正本は `採用しない案:` を使う（full の `却下した代替案:` の同義ラベル）。"""
        result = _run(_doc(_point(rejected="採用しない案: 案Bは見送り（保守コストが高いため）")))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def test_document_without_default_answer_marker_skips_new_checks(self) -> None:
        """`無回答時のデフォルト` が一度も無い簡易 HITL（既存 smoke fixture 相当）は、
        新チェックが発火せず既存挙動のまま通る（誤 FAIL ゼロの実測対象）。
        """
        text = "\n".join(
            [
                "## 確認",
                "### 30秒判断",
                "**整理した要件**: x",
                "**実装する方法・内容**: x",
                "**検証する方法・内容**: x",
                "**どこまで自走するのか**: PR作成まで",
                "**判断ポイント**: 完了条件と検証範囲が意図通りか。",
                "**段階実装サマリー**: 単一段階",
                "### OKで進む範囲",
                "x",
                "### OKでも許可されないこと",
                "merge",
            ]
        )
        result = _run(text)
        # 既存の必須マーカー不足（人間に戻す条件 等）で reject され得るが、新チェック
        # （既定範囲 / 判断に影響する前提）由来のメッセージは出ないことだけを確認する。
        self.assertNotIn("既定範囲", result.stdout)
        self.assertNotIn("判断に影響する前提が欠落", result.stdout)
        self.assertNotIn("却下した代替案 / 採用しない案 が欠落", result.stdout)

    # --- D: 完了条件の変換テーブル（延期・削除の固定フィールド） ---

    def _table_doc(self, table_lines: list[str]) -> str:
        table_block = "\n".join(
            [
                "### ズレ確認",
                "**完了条件の変換**（変換・延期・削除した条件だけ）",
                *table_lines,
            ]
        )
        return _doc(_point()) + "\n\n" + table_block

    def test_completion_table_heading_entirely_missing_is_rejected(self) -> None:
        """独立レビュー指摘: `完了条件の変換` 見出し自体を書かないと素通りしていた。

        `_completion_table_errors` は見出しが 0 件なら即座に空リストを返す設計
        だったため、変換表がほとんど出ていなかった実測と同じ失敗を
        再生産していた。承認ポイント構造（`無回答時のデフォルト`）を持つ文書では
        見出し自体の欠落も検出する。
        """
        text = "\n".join(
            [
                "## 確認",
                "",
                "### 30秒判断",
                "**整理した要件**: 既存コード読解を先に行い、完了条件に沿ってテストを書きます。",
                "**実装する方法・内容**: 既存の HITL contract と lint を更新します。",
                "**検証する方法・内容**: lint smoke と contract test で確認します。",
                "**どこまで自走するのか**: PR 作成まで。merge と deploy は別承認です。",
                "**判断ポイント**: 完了条件と検証範囲が意図通りか。",
                "**段階実装サマリー**: 単一段階: 今回の PR で完結。",
                "",
                "### OKで進む範囲",
                "既存コード読解を先に行い、HITLで見えた完了条件に沿ってテストを書きます。",
                "",
                "### OKでも許可されないこと",
                "本番反映、外部投稿、追加の仕様変更は承認しません。",
                "",
                "### 現在地",
                "| 項目 | 内容 |",
                "|---|---|",
                "| 人間が今やること | 上の内容が意図どおりか確認して OK と返す |",
                "| OK 後に残る作業 | 設計、テスト、実装、PRレビュー後ループ |",
                "",
                "### PR検証後の次の導線",
                "| PR検証後の状態 | 次にやること | 同じチャットで続けるか / 新しいチャットか |",
                "|---|---|---|",
                "| PR の検証・レビューが通った | merge は人間判断 | 新しいチャット推奨 |",
                "",
                "### 人間に戻す条件",
                "完了条件、技術スタック、外部公開範囲が変わる場合。",
                "",
                "### 承認ポイント",
                "",
                _point(),
            ]
        )
        self.assertNotIn("完了条件の変換", text)
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("完了条件の変換", result.stdout)

    def test_completion_table_with_no_deferred_or_deleted_rows_requires_none_marker(self) -> None:
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件A | 具体化 | AC-1 | 影響なし |",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("延期・削除: なし", result.stdout)

    def test_completion_table_with_none_marker_present_is_accepted(self) -> None:
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件A | 具体化 | AC-1 | 影響なし |",
                "",
                "延期・削除: なし",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_deferred_row_without_take_not_field_is_rejected(self) -> None:
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件B | 延期 | Open Questions | 次タスクで再検討 |",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("取りに行かない", result.stdout)

    def test_deleted_row_without_take_not_field_is_rejected(self) -> None:
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件C | 削除 | 非スコープ | 特に無し |",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("取りに行かない", result.stdout)

    def test_deferred_row_with_take_not_field_is_accepted(self) -> None:
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件B | 延期 | Open Questions | 取りに行かない: U+00A0/U+3000 prefix 面 |",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_only_one_of_multiple_rows_satisfying_take_not_is_still_rejected(self) -> None:
        """PR #83 巡2 の再現ケース: 複数の延期・削除行のうち1行だけ満たせば全行が通っていた。"""
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件B | 延期 | Open Questions | 取りに行かない: 面Aの取りこぼし |",
                "| 元の条件C | 削除 | 非スコープ | 特に無し |",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_completion_table_with_unknown_handling_value_is_rejected(self) -> None:
        """PR #86 レビュー指摘 finding 3 (残): `扱い` 列は閉じた5値

        （具体化/延期/削除/追加/未解決）以外を reject する。changelog は
        「閉じた5値を見る」と主張していたが、実装は `延期`/`削除` 以外を
        検査していなかった（未知の値、例: 見送り、を素通りさせていた）。
        """
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件A | 見送り | Open Questions | 特に無し |",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("扱い", result.stdout)

    def test_take_not_field_in_wrong_column_is_still_rejected(self) -> None:
        """PR #86 レビュー指摘 finding 3 (残): `取りに行かない:` は

        `承認してほしい点` 列（指定列）だけを見る。他の列（例: 変換後）に
        書いても満たしたことにしない（「取りに行かない はどのセルでも足りる」
        という指摘の再現）。
        """
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件B | 延期 | 取りに行かない: Open Questions | 次タスクで再検討 |",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("取りに行かない", result.stdout)

    # --- PR #86 レビュー指摘: 終端マーカーを丸ごと欠くポイントの無音吸収 ---

    def test_second_point_with_zero_fields_is_rejected(self) -> None:
        """PR #86 レビュー指摘 finding 1: 2件目が全フィールドを欠くと、1件目の

        区間に無音で吸収され独立に検出されなかった（`- 無回答時のデフォルト:` が
        無いため marker_indices に載らず、既定範囲の行も無いため値域チェックにも
        引っかからない）。承認ポイントの数と終端マーカーの出現数が一致しないことを
        見て reject する。
        """
        good = _point(theme="1. <判断テーマ1>")
        empty_point = "2. <判断テーマ2>"
        result = _run(_doc(good, empty_point))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("一致しません", result.stdout)

    def test_prose_before_real_heading_cannot_satisfy_required_fields(self) -> None:
        """PR #86 レビュー指摘 finding 2: `_decision_area_start_index` が

        `label in line`（任意の行への部分一致）だったため、30秒判断の
        `**判断ポイント**: ...` という地の文に `判断に影響する前提:` /
        `却下した代替案:` を書くと、承認ポイント本体が両方欠いても通っていた。
        見出し行（`#` 記法）だけを起点にすることで地の文を除外する。
        """
        deficient_point = "\n".join(
            [
                "1. <判断テーマ>",
                "- 無回答時のデフォルト: 案Aを既定採用する",
            ]
        )
        text = _doc(deficient_point).replace(
            "**判断ポイント**: 完了条件と検証範囲が意図通りか。",
            "**判断ポイント**: 完了条件と検証範囲が意図通りか。"
            "判断に影響する前提: なし。却下した代替案: 他案なし。",
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("判断に影響する前提 がありません", result.stdout)
        self.assertIn("却下した代替案", result.stdout)

    def test_malformed_completion_table_without_separator_row_is_rejected(self) -> None:
        """PR #86 レビュー指摘 finding 3: 区切り行の無い 1 行だけの table は、

        先頭行が無条件で header として捨てられるため data 0 件に化け、直後に
        `延期・削除: なし` を書くだけで素通りしていた（実際には延期行が 1 件ある）。
        """
        text = _doc(_point()) + "\n\n" + "\n".join(
            [
                "### ズレ確認",
                "**完了条件の変換**（変換・延期・削除した条件だけ）",
                "| 元の条件A | 延期 | Open Questions | 承認事項 |",
                "延期・削除: なし",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("テーブル形式が不正です", result.stdout)

    def test_well_formed_completion_table_is_still_accepted(self) -> None:
        """区切り行を正しく持つ table は、独立レビュー対応後も従来どおり通る（回帰防止）。"""
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件A | 具体化 | AC-1 | 影響なし |",
                "",
                "延期・削除: なし",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    # --- PR #86 レビュー指摘（3巡目）: 1巡目で閉じた3クラスの隣接形 ---
    # レビュー指摘: 同じ種類の High が2巡続いたため、個別 fixture を1つずつ塞ぐのでは
    # なく、各チェックの「認識できない行を黙って無視する（skip）」という共通の穴を
    # 「reject」に統一した（CLAUDE.md の L1+ 安全策: 同種 high が2回続いたら線引きを
    # 戻す。Opus への advisory で「受理集合の定義の書き換え」を確認した上で対応）。

    def test_indented_second_theme_line_still_counts_toward_balance_check(self) -> None:
        """`THEME_LINE_RE` が行頭専用だったため、2件目のテーマ行をインデントすると

        件数バランスチェックをすり抜けていた（インデントされたテーマ行は数えられず、
        1件目だけの件数と偶然一致し、2件目のフィールド欠落が個別チェックに回らな
        かった）。テーマ行の判定はインデントの有無に依存しない（番号の値は見ない、
        という既存方針のまま）。
        """
        good = _point(theme="1. <判断テーマ1>")
        indented_empty_point = "  2. <判断テーマ2>"
        result = _run(_doc(good, indented_empty_point))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("一致しません", result.stdout)

    def test_heading_with_trailing_text_is_not_a_valid_decision_area_start(self) -> None:
        """見出しの前方一致だと `### 判断ポイント補足` のような見出しが起点になり、

        その直下の地の文が承認ポイント本体の必須欄を充足できてしまっていた。見出しは
        行末まで完全一致（ラベルの直後は行末か空白のみ）を要求する。
        """
        deficient_point = "\n".join(
            [
                "1. <判断テーマ>",
                "- 無回答時のデフォルト: 案Aを既定採用する",
            ]
        )
        decoy_section = "\n".join(
            [
                "### 判断ポイント補足",
                "判断に影響する前提: なし。却下した代替案: 他案なし。",
                "",
            ]
        )
        text = _doc(deficient_point).replace(
            "### 承認ポイント", decoy_section + "### 承認ポイント", 1
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("判断に影響する前提 がありません", result.stdout)

    def test_short_data_row_is_rejected_instead_of_silently_skipped(self) -> None:
        """4列ヘッダーの table に3セルの延期行が混ざると、`len(cells) >= 4` の

        ガードで無音 skip され、行が無かったことにされて `延期・削除: なし` の
        固定行だけで通っていた。列数がヘッダーと一致しない行は skip ではなく
        テーブル全体を不正として reject する。
        """
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件B | 延期 | Open Questions |",
                "",
                "延期・削除: なし",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("テーブル形式が不正です", result.stdout)

    def test_disguised_deferred_row_as_header_with_short_separator_is_rejected(self) -> None:
        """延期行をそのまま4セルの header 行として使い、区切り行だけ `|---|`

        （1セル）に短縮すると、区切り行のセル数をヘッダーと突き合わせていな
        かったため通っていた（隠れた延期行が `取りに行かない:` の検査対象から
        丸ごと外れる）。区切り行のセル数はヘッダーと一致しなければ reject する。
        """
        text = self._table_doc(
            [
                "| 元の条件B | 延期 | Open Questions | 次タスクで再検討 |",
                "|---|",
                "",
                "延期・削除: なし",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("テーブル形式が不正です", result.stdout)

    # --- PR #86 レビュー指摘（5巡目）: skip→reject 統一の残り2箇所 ---
    # レビュー指摘: 4巡目で列数チェックは入ったが、見出し 0 件時のフォールバックと
    # 表の途中終了（閉じ `|` 欠落など）はまだ skip のままだった。新しい隣接形の
    # 列挙はせず、この2箇所を reject へ統一する。

    def test_atx_closing_hashes_leave_heading_unmatched_and_must_reject(self) -> None:
        """見出しが完全一致から外れる形（ATX の閉じ `#`、例: `### 承認ポイント ###`）

        だと `_decision_area_start_index` が None を返し、`無回答時のデフォルト`
        を持つ文書でも `block_start` が文書先頭（0）へフォールバックしていた。
        その結果、30秒判断の地の文が承認ポイント本体の必須欄を充足できてしまう
        （前巡までに閉じた「地の文流用」と同型だが、経路が異なる）。見出しが
        見つからない場合は個別項目のチェックへ進まず reject する。
        """
        deficient_point = "\n".join(
            [
                "1. <判断テーマ>",
                "- 無回答時のデフォルト: 案Aを既定採用する",
            ]
        )
        text = (
            _doc(deficient_point)
            .replace(
                "**判断ポイント**: 完了条件と検証範囲が意図通りか。",
                "**判断ポイント**: 完了条件と検証範囲が意図通りか。"
                "判断に影響する前提: なし。却下した代替案: 他案なし。",
            )
            .replace("### 承認ポイント", "### 承認ポイント ###", 1)
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("見出しが見つかりません", result.stdout)

    def test_table_row_missing_closing_pipe_ends_table_silently_and_must_reject(self) -> None:
        """閉じる `|` を欠く行は `_TABLE_ROW_RE` に一致せず、table がそこで

        正常終了したことにされていた（延期行が消え、直後の `延期・削除: なし`
        で通ってしまう）。`|` で始まるのに正しく閉じない行は skip ではなく
        table 全体を不正として reject する。
        """
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件B | 延期 | Open Questions | 次タスクで再検討",
                "",
                "延期・削除: なし",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("テーブル形式が不正です", result.stdout)

    # --- セルフレビュー（実装文脈を渡さない独立レビュー、read-only）で見つかった fail-open ---
    # 5 巡目までの PR レビューはユーザー自身によるものだったため、push 前に自分でも
    # 独立レビュー契約（`references/independent-review.md`）に従い fresh agent へ委託した。

    def test_asterisk_bullets_still_trigger_the_same_checks_as_hyphen(self) -> None:
        """`既定範囲` / `狭める根拠` / `無回答時のデフォルト` の行頭記号が `-` に

        固定されていたため、承認ポイント全体を `* ` 箇条書きで書くだけで（有効な
        markdown）`marker_indices` が空になり、新設チェックが丸ごと
        素通りしていた。`BULLET_PREFIX_RE` と同じ受理集合（`-`/`*`/`+`）に揃える。
        """
        deficient = "\n".join(
            [
                "1. <判断テーマ>",
                "* 無回答時のデフォルト: 案Aを既定採用する",
            ]
        )
        result = _run(_doc(deficient))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_theme_count_scan_is_bounded_and_does_not_count_unrelated_numbered_lists(
        self,
    ) -> None:
        """`theme_count` が `lines[area_start:]` を文書末尾まで走査していたため、

        承認ポイント節より後ろにある無関係な番号リスト（例: `### 残タスク` の
        `1. / 2.` 項目）まで数えてしまい、正当な文書が false FAIL していた。
        """
        text = _doc(_point()) + "\n\n### 残タスク\n1. 設計を書く\n2. テストを書く\n"
        result = _run(text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_deferred_row_separated_by_blank_line_is_not_silently_dropped(self) -> None:
        """table の data 行ループが最初の非 `|` 行（空行）で無音終了していたため、

        空行を挟んだ後ろにある延期行が `rows` に入らず、直前の `延期・削除: なし`
        で素通りしていた。区間内に残る `|` 始まりの行は skip ではなく reject する。
        """
        text = self._table_doc(
            [
                "| 初期条件 | 扱い | 変換後 | 承認してほしい点 |",
                "|---|---|---|---|",
                "| 元の条件A | 具体化 | AC-1 | 影響なし |",
                "",
                "| 元の条件B | 延期 | Open Questions | 特になし |",
                "",
                "延期・削除: なし",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_prose_between_heading_and_first_theme_line_cannot_satisfy_required_fields(
        self,
    ) -> None:
        """1件目のブロックが見出し行そのものから始まっていたため、見出し直後

        （最初のテーマ行より前）に置いた地の文が、1件目の必須欄を充足できて
        しまっていた。block の開始は見出し行ではなく最初のテーマ行にする。
        """
        deficient_point = "\n".join(
            [
                "1. <判断テーマ>",
                "- 無回答時のデフォルト: 案Aを既定採用する",
            ]
        )
        text = _doc(deficient_point).replace(
            "### 承認ポイント",
            "### 承認ポイント\n判断に影響する前提: なし。却下した代替案: 他案なし。",
            1,
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("判断に影響する前提 がありません", result.stdout)

    # --- セルフレビュー2巡目: テーマ行の番号有無に依存しない件数チェックへ ---
    # `THEME_LINE_RE`（`\d+\.` 行）で件数を数える設計は、round3(丸ごと空の2件目)→
    # round4(インデントされた2件目)→ここ(番号の無い2件目) と3回同じ形の fail-open を
    # 生んだ（CLAUDE.md の L1+ 安全策: 同種 high が2回続いたら線引きを戻す）。ユーザー
    # 確認の上、件数の突き合わせをテーマ行の形推定から著者の明示宣言（`承認ポイント数:`）
    # へ置き換える。

    def test_unnumbered_second_theme_line_is_still_caught_by_declared_point_count(
        self,
    ) -> None:
        """2件目のテーマ行を `THEME_LINE_RE`（`\\d+\\.` 行）に一致しない書式（番号を

        使わない）で書くと、テーマ行の形から件数を数える旧実装は2件目を1件も
        数えられず、1件目だけの件数（1件）と偶然一致して2件目のフィールド欠落が
        個別チェックに回らなかった。件数の突き合わせはテーマ行の形に依存しない
        `承認ポイント数:` の宣言値と 無回答時のデフォルト の出現数で行う。
        """
        good = _point(theme="1. <判断テーマ1>")
        unnumbered_empty_point = "**判断テーマ2（番号なし）**"
        result = _run(_doc(good, unnumbered_empty_point))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("一致しません", result.stdout)

    def test_missing_declared_point_count_is_rejected(self) -> None:
        """`承認ポイント数:` の宣言行そのものが無ければ reject する

        （skip→reject 統一: 件数チェックは宣言が無ければフォールバックせず止める）。
        """
        text = "\n".join(
            [
                "## 確認",
                "### 判断ポイント",
                "1. x",
                "",
                "### 承認ポイント",
                "",
                "1. <判断テーマ>",
                "- 無回答時のデフォルト: 案Aを既定採用する",
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("承認ポイント数の宣言がありません", result.stdout)

    def test_declared_point_count_matching_marker_count_with_unnumbered_theme_is_accepted(
        self,
    ) -> None:
        """2件目のテーマ行が番号無しでも、宣言件数とマーカー数が一致し、必須欄が

        すべて揃っていれば通る（回帰防止: 宣言方式への置き換えでテーマ行の形式
        そのものを禁止したわけではない）。
        """
        good = _point(theme="1. <判断テーマ1>")
        unnumbered_full_point = _point(
            theme="**判断テーマ2（番号なし）**"
        )
        result = _run(_doc(good, unnumbered_full_point))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    # --- full テンプレートの並び（判断ポイント → … → 承認ポイント） ---
    # full の出力テンプレート（references/human-check-template.md）は、宣言の無い
    # `### 判断ポイント` を先に置き、`承認ポイント数:` を後ろの `### 承認ポイント` に置く。
    # 起点は「宣言を持つ最初の見出しの節」にする。

    def test_full_template_order_with_declaration_in_later_heading_is_accepted(self) -> None:
        text = _doc(_point()).replace(
            "### OKで進む範囲", _FULL_ORDER_DECISION_SECTION + "### OKで進む範囲", 1
        )
        result = _run(text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_full_template_order_still_checks_fields_from_the_declared_section(self) -> None:
        """宣言の節を起点にしても、前の `### 判断ポイント` の地の文で必須欄を満たせない。"""
        deficient_point = "\n".join(
            [
                "1. <判断テーマ>",
                "- 無回答時のデフォルト: 案Aを既定採用する",
            ]
        )
        decoy = _FULL_ORDER_DECISION_SECTION.replace(
            "1. CI 成功の判定基準",
            "1. 判断に影響する前提: なし。却下した代替案: 他案なし",
        )
        text = _doc(deficient_point).replace(
            "### OKで進む範囲", decoy + "### OKで進む範囲", 1
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("判断に影響する前提 がありません", result.stdout)

    def test_declaration_only_in_a_non_decision_heading_is_rejected(self) -> None:
        text = "\n".join(
            [
                "## 確認",
                "### やること",
                "承認ポイント数: 1",
                "",
                "### 承認ポイント",
                "",
                _point(),
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("承認ポイント数の宣言がありません", result.stdout)

    def test_default_answer_marker_before_the_declared_section_is_rejected(self) -> None:
        """宣言の節より前にある `無回答時のデフォルト` は、どの承認ポイントにも入らず通さない。"""
        text = "\n".join(
            [
                "## 確認",
                "### 判断ポイント",
                "1. <判断テーマ0>",
                "- 無回答時のデフォルト: 案Aを既定採用する",
                "",
                "### 承認ポイント",
                "承認ポイント数: 1",
                "",
                _point(),
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_complete_points_before_the_declared_section_are_not_skipped(self) -> None:
        """宣言の無い前の節に完全な承認ポイントを置き、後ろの節で 1 件だけ宣言しても通さない。

        起点が後ろへ動いても、起点より前の `無回答時のデフォルト` は空のブロックとして
        必須欄の欠落になる。
        """
        text = "\n".join(
            [
                "## 確認",
                "### 判断ポイント",
                _point(theme="1. <判断テーマ0>"),
                "",
                _point(theme="2. <判断テーマ1>"),
                "",
                "### 承認ポイント",
                "承認ポイント数: 1",
                "",
                _point(),
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("判断に影響する前提 がありません", result.stdout)

    def test_two_declared_sections_are_rejected(self) -> None:
        text = "\n".join(
            [
                "## 確認",
                "### 判断ポイント",
                "承認ポイント数: 1",
                "",
                _point(),
                "",
                "### 承認ポイント",
                "承認ポイント数: 1",
                "",
                _point(),
            ]
        )
        result = _run(text)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("一致しません", result.stdout)

    def test_decision_heading_on_the_last_line_does_not_crash(self) -> None:
        for text in ("", "- 無回答時のデフォルト: x\n### 判断ポイント", "### 承認ポイント"):
            with self.subTest(text=text):
                result = _run(text)
                self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)


_FULL_ORDER_DECISION_SECTION = "\n".join(
    [
        "### 判断ポイント",
        "**OKで実装・検証すること**: 共通契約と修復の上限",
        "**OKしても今回は対象外のこと**: branch protection の変更",
        "**人間に決めてほしいこと**",
        "1. CI 成功の判定基準: おすすめは required checks。",
        "2. 自動修復の上限: おすすめは 2 回。",
        "",
        "### やること",
        "CI が通るまで Draft で待つ。",
        "",
        "### 承認サマリ",
        "- **人間が今だけ判断すること**: 判断ポイント 1・2",
        "",
        "",
    ]
)


if __name__ == "__main__":
    unittest.main()
