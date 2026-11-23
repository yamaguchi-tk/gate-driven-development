#!/usr/bin/env python3
"""Lint whether a final HITL explicitly declares its 5 conditional axes via a
closed-vocabulary `<gdd-hitl-fields>` tag（宣言フィールド化）。

過去の human-check-waiting の HITL を調べると、`human-check-template-compact.md`
の条件付き節（「〜場合だけ」の見出し）は AI が「該当しない」と判断すれば
書かなくてよい構造になっており、未記録と「該当なし 0 件」が区別されない。
また、Option ラベルが 0 個の HITL が大半だった。

## 設計（PR #92 からの再設計、PR #94 で位置契約へ再々設計）

初期実装（PR #92）は、4つの条件付き節が固定句（「該当なし（理由: ...）」等）や
Option ラベルを本文から**生テキスト一致**で探す raw-text-match 方式だった。
`references/human-check-template-compact.md` の各節 placeholder 自身が、未編集
のまま例示としてこれと同じ固定句・Option ラベルを含んでいたため、独立レビュー・
PR後レビューを通じて3巡連続で同一クラスタ（raw-text-match-vs-placeholder）の
fail-open が再発した（review-log/20260915-x60-x57-hitl-required-fields.md の
F1/G1/H1 参照）。本文を一切解釈しない宣言フィールド方式（`<gdd-hitl-fields ...>`
タグ）へ再設計した後も、タグの境界検出をフェンス・HTML コメント・インデント
コードブロックの**構文列挙**で行う方式が、独立-2 → PR後-2 と未列挙の構文
（info string 付き閉じ行、同一行のコメント再オープン、`<pre>`/`<textarea>` 等の
HTML block）のたびに同クラスタを再発させ、通算**4巡連続**に達した
（review-log/20260916-x60-hitl-declared-fields.md の I1〜I3 参照）。L1+ 安全策
#4 に基づき Opus（claude-opus-5）のセカンドオピニオンを経て、markdown 構文の
列挙をやめ、**位置契約**（`HITL_STOP_MARKER` の直前で、空行だけを飛ばした
最初の非空行がちょうどスタンドアロンな `<gdd-hitl-fields ...>` 行であることだけ
を見る）へ再設計した（同ファイル「方針メモ」参照）。

位置契約を「**最初**の `HITL_STOP_MARKER` 出現だけ」を見る形で実装したところ、
PR後-3 レビューが、先に compliant な組（宣言＋marker）があると後ろの本物
（宣言なし）が無審査で合格する fail-open（同クラスタの5巡目の再発）を指摘した。
`HITL_STOP_MARKER` の**全ての**出現それぞれについて隣接宣言を要求する
（existential → universal）よう修正し、marker が複数現れても、どの occurrence
も無審査で素通りしないようにした。

本 script が見るのは `<gdd-hitl-fields options="..." arch="..." zure="..."
multi-pr="..." stage="...">` タグの5属性だけで、本文（節見出し・placeholder の例示文言・
Option ラベルの地の文言及）は一切読まない。各属性の値は閉じた語彙
（`none` = 該当なし / `filled` = 記入済み）のどちらかでなければならない。
宣言値そのものの真偽（本当に該当なしか、本当に記入したか）は検証しない
——`承認ポイント数: <N>` 宣言フィールドと同じ、他の固定フィールドと
同じ自己申告の信頼境界（Known limitations 参照）。

Known limitations（位置契約の意図的な境界）: フェンス・HTML コメント・
`<pre>` 等の中に**タグと marker のペアが完結して**いる場合、そのペア自体は
構文を見ないため合格しうる（閉じているかどうかは無関係）。ただし universal
quantification（全 occurrence を検査）により、それが「本物」の代わりに
なることはない——文書中の**別の** `HITL_STOP_MARKER` occurrence（例えば
実際にテンプレートどおり出力の末尾にある本物）は、そのペアとは独立に
それぞれ検査される。逆にタグが対応する marker に隣接していない（間に他の
行がある）場合は、本物の宣言であっても無視される——
`references/human-check-template-compact.md` のテンプレートどおりタグを
マーカー直前行に置けば発生しない。

また、地の文・インラインコード中に `HITL_STOP_MARKER` と同一の文字列が
（機能する marker としてではなく）言及・引用される場合も、位置契約は markdown
文脈を判別しないため1つの occurrence として数え、直前に宣言タグが無ければ
warn 対象になる（fail-closed 方向の誤検知、warn-only のため実害は計測ノイズ
のみ。PR後-3 レビューでも「後続でも可」として受け入れた）。

正本: `references/human-check-template-compact.md` の Template 内タグ、
`references/human-check-template.md` § 選択肢の説明・§ Multiple PR Strategy
Options・§ ズレ確認。

`stage`（2026-11-11）は段階実装の節を書いたか（`none` = 段階が 1 つだけで節を
書かない / `filled` = 複数段階・後続 PR 前の再承認などで節を書いた）。
display-integrity・human-check-language・decision-quality は、同じ位置契約で
各 stop marker 直前のタグがすべて `stage="none"` のときだけ段階実装の語を
要求しない（`scripts/lib/hitl_fields.py` を共有する）。

位置契約の実装（`hitl_check_points`・`parse_hitl_fields_at`）は
`scripts/lib/hitl_fields.py` にある。

方針メモ（2026-09-15、ユーザー確認）: この lint は warn-only で配線する
（`hooks/scripts/lib/hitl_lint_gate.py` の HITL_LINT_WARN_SCRIPTS）。CLI 自体の
exit code 契約（0=pass/1=fail/2=usage error）は他の lint script と同じ。

Exit code:
  0: pass
  1: HITL is present but the declared-field tag is missing entirely, or one
     or more of its 5 attributes is missing / not one of the closed values
  2: usage error / file not found
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# hook は lib/kill-switch.sh で python3 を -I で起動し、PYTHONSAFEPATH も設定する。その下では、このファイルの
# ディレクトリが sys.path に入らない
if sys.flags.isolated or getattr(sys.flags, "safe_path", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.hitl_fields import hitl_check_points, parse_hitl_fields_at
from lib.lint_base import check_file, report_errors

FIELD_VALUE_NONE = "none"
FIELD_VALUE_FILLED = "filled"
ALLOWED_FIELD_VALUES = (FIELD_VALUE_NONE, FIELD_VALUE_FILLED)

# (<gdd-hitl-fields> の属性名, エラーメッセージで使う節ラベル)。
# 正本: `references/human-check-template-compact.md` の Template 内タグと
# CONDITIONAL_SECTIONS の対応。
FIELD_SECTIONS: tuple[tuple[str, str], ...] = (
    ("options", "選択肢の説明"),
    ("arch", "アーキテクチャ選択"),
    ("zure", "ズレ確認"),
    ("multi-pr", "Multiple PR Strategy Options"),
    ("stage", "段階実装"),
)


def _field_errors_for(fields: dict[str, str] | None) -> list[str]:
    if fields is None:
        return [
            f"{label} の宣言がありません。<gdd-hitl-fields ...> タグの `{attr}` 属性に "
            f"`{FIELD_VALUE_NONE}`（該当なし）または `{FIELD_VALUE_FILLED}`（記入済み）を"
            "明記してください（未記録と該当なしを区別するため）"
            for attr, label in FIELD_SECTIONS
        ]
    errors: list[str] = []
    for attr, label in FIELD_SECTIONS:
        value = fields.get(attr)
        if value in ALLOWED_FIELD_VALUES:
            continue
        if value is None:
            detail = "属性自体がありません"
        else:
            detail = f"値 `{value}` は許容されていません"
        errors.append(
            f"{label} の宣言（<gdd-hitl-fields> の `{attr}` 属性）が不正です（{detail}）。"
            f"`{FIELD_VALUE_NONE}`（該当なし）または `{FIELD_VALUE_FILLED}`（記入済み）の"
            "いずれかにしてください"
        )
    return errors


def _declared_field_errors(text: str) -> list[str]:
    """`text` 中の stop marker の全ての occurrence について隣接
    宣言を検査し、最初に不正だった occurrence のエラーを返す（universal
    quantification。PR後-3 対策）。全て正しければ空リストを返す。
    """
    for position in hitl_check_points(text):
        fields = parse_hitl_fields_at(text, position)
        errors = _field_errors_for(fields)
        if errors:
            return errors
    return []


def lint_text(text: str) -> list[str]:
    return _declared_field_errors(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="final HITL markdown sample path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    path = Path(args.path)
    if (rc := check_file(path)) is not None:
        return rc

    errors = lint_text(path.read_text(encoding="utf-8", errors="replace"))
    return report_errors(
        errors,
        "ERROR: HITL Required Fields failed.\n"
        "<gdd-hitl-fields> タグの宣言が欠落しているか、値が不正です。",
        "OK: HITL Required Fields passed",
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
