#!/usr/bin/env python3
"""Lint final HITL text for whether a human can make the next decision.

Exit code:
  0: pass
  1: HITL is present but not decision-ready
  2: usage error / file not found
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# hook は lib/kill-switch.sh で python3 を -I で起動し、PYTHONSAFEPATH も設定する。その下では、このファイルの
# ディレクトリが sys.path に入らない
if sys.flags.isolated or getattr(sys.flags, "safe_path", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.hitl_fields import required_words
from lib.lint_base import check_file, report_errors


REQUIRED_DECISION_MARKERS = (
    "整理した要件",
    "実装する方法・内容",
    "検証する方法・内容",
    "どこまで自走するのか",
    "判断ポイント",
    # 各 stop marker 直前のタグがすべて `stage="none"` のときは要求しない（`lib.hitl_fields`）。
    "段階実装サマリー",
    "OKでも許可されないこと",
)
# compact と full で語彙が違う表示要素。どちらの正本でも同じ判断材料を出しているが
# 綴りが一致しないため、flat な必須語にすると「一方の正本にしか無い語」を他方へ要求して
# しまい、正本どおりに書いた HITL が lint に落ちる（display-integrity が
# REQUIRED_MARKER_GROUPS を導入したのと同じ事故）。any-of で受ける。
REQUIRED_DECISION_MARKER_GROUPS = (
    # OK が許可する自走範囲。compact は `OKで進む範囲`、full は必須ルール 10 の
    # `この OK で許可すること`。
    ("OKで進む範囲", "この OK で許可すること"),
    # 現在地の「人間が今やること」。full は `人間が今やること`、compact は 1 行に
    # 圧縮した `今やること:`。**compact 側はコロンまで含める** — 裸の `今やること` は
    # 地の文にも現れるため、欄が無くても散文だけで充足してしまう。
    ("人間が今やること", "今やること:"),
    # 現在地の「OK 後に残る作業」。compact は `OK後:`（空白なし + コロン）。
    # 裸の `OK後` は 4 文字で「OK後に AI が設計へ進む」のような地の文に普通に出現し、
    # 現在地の欄が丸ごと無い HITL でも通ってしまう（実測で確認した保護の純減）。
    ("OK 後に残る作業", "OK後:"),
)
CANONICAL_SOURCES = (
    "references/human-check-template-compact.md",
    "references/human-check-template.md",
)
# 中身が空 / placeholder のままでないかを追加で見る欄。REQUIRED_DECISION_MARKERS または
# REQUIRED_DECISION_MARKER_GROUPS の要素であること（リテラル再掲すると片方だけ改名した
# とき検査が黙って無効化される）。存在する場合にだけ発火するので、片方の正本にしか
# 無い語を挙げても他方を落とさない。
DECISION_SECTION_MARKERS = (
    "OKで進む範囲",
    # `OKで進む範囲` の any-of 相方（full 正本の必須ルール 10 の語彙）。片方だけを空欄検査に
    # 置くと、full 正本どおりに書いた HITL は承認範囲欄が空でも通ってしまう。
    "この OK で許可すること",
    "OKでも許可されないこと",
)
PRIORITY_LABELS = ("P0", "P1", "P2")
PRIORITY_EXPLANATIONS = (
    "まずやること",
    "最初にやること",
    "次にやること",
    "今回は後回し",
    "後回し",
    "優先度",
)
PRIORITY_CONTENT_MARKERS = {
    "P0": ("まずやること（P0）", "最初にやること（P0）"),
    "P1": ("次にやること（P1）",),
    "P2": ("今回は後回し（P2）", "後回し（P2）"),
}
REDUNDANT_SUMMARY_HEADINGS = (
    "### 承認サマリ",
    "### まず確認",
    "### まず見るところ",
)
FORBIDDEN_OPTIONAL_SECTIONS = (
    "### まず確認",
    "OKすると増える保護",
    "OKしてもまだ増えない保護",
    "今回OKすると決まること",
    "OKしても決まらないこと",
    "AIが自走しないこと",
    "変更したいなら言う場所",
    "AIの仮案",
    "OKするとAIがやること",
    "OKだけではやらないこと",
)
AMBIGUOUS_PHRASES = (
    "次に必要な判断はどちらかです",
    "human-confirm",
    "holdout",
    "prod_equivalent",
    "production model env",
    "executable にする",
    "active/new PR",
)
PR_BOUNDARY_PHRASES = (
    "このPRではここまで",
    "この PR ではここまで",
    "PR 作成まで",
    "PR作成まで",
    "PR 検証",
    "PR検証",
)
PR_FOLLOWUP_MARKER = "PR検証後の次の導線"
OPTION_LABELS = ("Option A", "Option B", "Option C")
OPTION_EXPLANATION_MARKERS = ("選択肢の説明", "何をする案か")
OPTION_DETAIL_MARKERS = ("良い点", "弱い点", "AIの仮決定")
MULTI_PR_PHRASES = (
    "複数PR",
    "複数 PR",
    "follow-up-pr",
    "後続PR",
    "後続 PR",
    "post-merge verification",
    "post merge verification",
    "post-merge",
    "post merge",
)
MULTI_PR_STRATEGY_MARKER = "Multiple PR Strategy Options"
# 件数・実測を根拠に出すなら、その N がどの集合から取られたかを併記させる。
# 母集団を書かずに小さい標本から一般化し、HITL が 1 往復増えた実測に基づく。
# 発火語のマッチなので fail-open（該当語を使わない主張は素通りする）。
EVIDENCE_CLAIM_PHRASES = (
    "件の実測",
    "実測",
    "件中",
)
EVIDENCE_POPULATION_MARKER = "根拠の母集団"

# 承認ポイントの固定フィールド受理文法（既定範囲・狭める根拠の検査は撤去した）。
# 正本: references/human-check-template.md § 承認ポイントの固定フィールド受理文法
# （<!-- decision-scope-grammar:begin/end -->）。PR #83（closed, 未マージ）は
# 「広い側を採用したか」「数値根拠が示されたか」を自由文から判定しようとして 7 巡
# 収束しなかった（`gh api .../pulls/83/comments` に実測）。ここでは自由文を一切
# 解釈せず、行の形・隣接性・固定キーだけを見る。
_WS = " \t"
# bold(`**`) は full 正本、無しは compact 正本のスタイル。両方を同じ 1 本の
# regex で受理する（テンプレートごとに別パーサを持たない）。
# 箇条書き記号は `BULLET_PREFIX_RE` と同じ受理集合（`-`/`*`/`+`）にする（独立
# レビュー指摘: `-` だけを受理していたため、承認ポイント全体を `* ` 箇条書きで
# 書く（有効な markdown）だけで `marker_indices` が空になり、新設チェック
# が丸ごと素通りしていた）。
_BULLET_MARK = r"[-*+]"
DEFAULT_ANSWER_LINE_RE = re.compile(rf"^[ \t]*{_BULLET_MARK}[ \t]+\*{{0,2}}無回答時のデフォルト\*{{0,2}}:")
DECISION_PREMISE_LABEL = "判断に影響する前提"
REJECTED_ALTERNATIVE_LABELS = ("却下した代替案", "採用しない案")
DECISION_AREA_ANCHOR_LABELS = ("判断ポイント", "承認ポイント")
# `_decision_area_start_index` は見出し行だけを起点にする。地の文（例: 30秒判断の
# `**判断ポイント**: ...`）に含まれる同名語を拾わないため、見出し記法（`#`）を要求する。
# 行末まで完全一致（ラベル直後は空白のみ許容）にする（独立レビュー指摘: 前方一致だと
# `### 判断ポイント補足` のような見出しが起点になり、直下の地の文が必須欄を充足できて
# いた）。見出しレベルの上限は設けない（`#####` 等の取りこぼしも fail-open 側のため）。
DECISION_AREA_HEADING_RE = re.compile(
    r"^#+[ \t]+(?:" + "|".join(re.escape(label) for label in DECISION_AREA_ANCHOR_LABELS) + r")[ \t]*$"
)
# 承認ポイントの開始行（`**1. <テーマ>**` / `1. <テーマ>`）。1件目のブロックが
# どこから始まるかの位置検出にだけ使う（どの行がどのポイントかを意味解釈しない。
# 番号の値も見ない）。行頭の空白（インデント）は許容する（独立レビュー指摘: 行頭
# 専用だと、2件目のテーマ行をインデントするだけで検出をすり抜けられた）。
#
# 件数の突き合わせにはもう使わない（セルフレビュー2巡目: round3「丸ごと空の
# 2件目」→round4「インデントされた2件目」→「番号の無い2件目」と、このテーマ行の
# 形推定に対する fail-open が3回同型で再発した。CLAUDE.md の L1+ 安全策により、
# これ以上の行形式の継ぎ足しはせず、ユーザー確認の上で件数チェックは
# `DECLARED_POINT_COUNT_RE` の宣言値へ置き換えた）。
THEME_LINE_RE = re.compile(r"^[ \t]*\*{0,2}\d+\.[ \t]+\S")
# 任意の markdown 見出し行（レベル問わず）。承認ポイント節の終端検出に使う（独立
# レビュー指摘・セルフレビュー: 節の走査を文書末尾まで無条件で行っていたため、
# 承認ポイント節より後ろにある無関係な番号リスト（`### 残タスク` の `1. / 2.` 等）
# まで巻き込み、正当な文書が false FAIL していた。節の終端は「次の見出し」に
# 一致させる — 終端マーカーの位置には依存しない。終端マーカーそのものを欠く
# ポイント（このモジュールが検出したい対象）はマーカーより後ろに現れうるため、
# マーカー位置を終端にはできない）。
_ANY_HEADING_RE = re.compile(r"^#{1,6}[ \t]+\S")
# 承認ポイントの件数宣言。件数の突き合わせは行の形から推定するのではなく、著者が
# 明示するこの宣言値で行う（上の THEME_LINE_RE のコメント参照）。
DECLARED_POINT_COUNT_RE = re.compile(r"^[ \t]*\*{0,2}承認ポイント数\*{0,2}:[ \t]*([0-9]+)[ \t]*$")

COMPLETION_TABLE_LABEL = "完了条件の変換"
NONE_DEFERRED_DELETED_FIELD = "延期・削除: なし"
TAKE_NOT_LABEL = "取りに行かない:"
DEFERRED_DELETED_VALUES = ("延期", "削除")
# `扱い` 列（行の 2 番目のセル）が受理する閉じた5値。これ以外（例: 見送り）は reject する。
HANDLING_CLOSED_VALUES = ("具体化", "延期", "削除", "追加", "未解決")
# `取りに行かない:` は「承認してほしい点」列（行の 4 番目のセル）だけを見る。他列への
# 記載は満たしたことにしない（独立レビュー指摘: どのセルでも足りてしまっていた）。
TAKE_NOT_COLUMN_INDEX = 3
# 正本テーブルの列数（初期条件 / 扱い / 変換後 / 承認してほしい点）。ヘッダー・区切り行・
# data 行のいずれも、この列数に一致しない行は skip せず reject する（独立レビュー指摘:
# 列が足りない延期行が無音 skip され「行が無かったこと」にされていた。また、延期行を
# そのまま4セルの header として使い区切り行だけ短くする形も、区切り行の列数をヘッダーと
# 突き合わせていなかったため通っていた）。
COMPLETION_TABLE_COLUMN_COUNT = 4
_TABLE_ROW_RE = re.compile(r"^[ \t]*\|.*\|[ \t]*$")
# `|` で始まる行は「table 行のつもり」とみなす起点（独立レビュー指摘・5巡目: 閉じる
# `|` を欠く行は `_TABLE_ROW_RE` に一致しないため、table がそこで正常終了したことに
# されていた。`|` で始まるのに `_TABLE_ROW_RE` を満たさない行は、legitimate な
# table 終端ではなく壊れた行として reject する）。
_TABLE_ROW_START_RE = re.compile(r"^[ \t]*\|")
_TABLE_SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")

BULLET_PREFIX_RE = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+[*_]{0,2}$")
PLACEHOLDER_LINES = {
    "",
    "-",
    "なし",
    "未定",
    "todo",
    "tbd",
    "要確認",
}


def _section_after(text: str, marker: str) -> str:
    index = text.find(marker)
    if index < 0:
        return ""
    rest = text[index + len(marker) :]
    next_heading = rest.find("\n### ")
    if next_heading >= 0:
        rest = rest[:next_heading]
    return rest.strip()


def _own_section(text: str, marker: str) -> str:
    """marker 自身に属する本文だけを返す。

    見出し形（`### OKで進む範囲`）は次の `### ` までを本文とする。正本 compact のように
    bullet 形（`- OKで進む範囲: ...`）で書かれている場合、次の `### ` までを取ると兄弟 bullet
    （`- 人間に戻す条件: ...` 等）を巻き込んで空欄が検出できないため、その bullet 行と、
    それより深いインデントの続き行だけを本文とする。
    """
    index = text.find(marker)
    if index < 0:
        return ""
    line_start = text.rfind("\n", 0, index) + 1
    prefix = text[line_start:index]
    if not BULLET_PREFIX_RE.match(prefix):
        return _section_after(text, marker)
    indent = len(prefix) - len(prefix.lstrip(" \t"))
    head, _, remainder = text[index + len(marker) :].partition("\n")
    body = [head]
    for line in remainder.splitlines():
        if not line.strip() or len(line) - len(line.lstrip(" \t")) <= indent:
            break
        body.append(line)
    return "\n".join(body).strip()


def _has_substantial_text(text: str, marker: str) -> bool:
    section = _own_section(text, marker)
    if not section:
        return False
    visible = " ".join(line.strip(" -*|") for line in section.splitlines()).strip().lower()
    return visible not in PLACEHOLDER_LINES and len(visible) >= 12


def _priority_labels_in(text: str) -> set[str]:
    return {label for label in PRIORITY_LABELS if label in text}


def _option_labels_in(text: str) -> set[str]:
    return {label for label in OPTION_LABELS if label in text}


def _decision_area_start_index(lines: list[str]) -> int | None:
    """`承認ポイント数:` の宣言を節の中に持つ `判断ポイント` / `承認ポイント` の**見出し行**を起点にする。

    独立レビュー指摘: 旧実装は `label in line`（任意の行への部分一致）だったため、
    30秒判断の `**判断ポイント**: 完了条件と検証範囲が意図通りか。` のような地の文が
    先に一致し、その地の文が承認ポイント本体の必須欄チェックに混入していた。見出し
    記法（`#`）を要求することで地の文を除外する（見出しの綴り違いには依存しない —
    `判断ポイント` / `承認ポイント` のどちらの見出しでも一致する）。

    full の出力テンプレートは宣言の無い `### 判断ポイント` を先に置き、宣言を後ろの
    `### 承認ポイント` に置く（compact は `### 判断ポイント` の直後に宣言を置く）。最初の
    見出しを起点にすると full の並びが「宣言がありません」で落ちるので、宣言を持つ節を
    選ぶ。宣言を持つ節が無ければ最初の見出しを返し、`_decision_item_field_errors` が
    宣言の欠落として reject する。見出しが1件も無ければ None を返す（0 ではない —
    「見出しが見つからない」と「見出しが先頭にある」を区別できるようにする）。
    """
    heading_indices = [i for i, line in enumerate(lines) if DECISION_AREA_HEADING_RE.match(line)]
    for index in heading_indices:
        section_end = _section_end_index(lines, index)
        if any(DECLARED_POINT_COUNT_RE.match(line) for line in lines[index:section_end]):
            return index
    return heading_indices[0] if heading_indices else None


def _section_end_index(lines: list[str], heading_index: int) -> int:
    return next(
        (i for i in range(heading_index + 1, len(lines)) if _ANY_HEADING_RE.match(lines[i])),
        len(lines),
    )


def _label_value_on_line(line: str, label: str) -> str | None:
    """`line` に `label` が現れる箇所の直後の値を返す（無ければ None）。

    コロン（半角/全角）の直後を値とする。太字マーカー `**` は値の前後にあっても
    自由文の解釈をせずそのまま剥がす。
    """
    if label not in line:
        return None
    after = line.split(label, 1)[1].lstrip("*")
    for colon in (":", "："):
        if colon in after:
            return after.split(colon, 1)[1].strip().strip("*").strip()
    return None


def _block_has_field_content(block_lines: list[str], labels: tuple[str, ...]) -> bool:
    for line in block_lines:
        for label in labels:
            value = _label_value_on_line(line, label)
            if value is None:
                continue
            if value and not (value.startswith("<") and value.endswith(">")):
                return True
    return False


def _block_has_field(block_lines: list[str], labels: tuple[str, ...]) -> bool:
    return any(label in line for line in block_lines for label in labels)


def _decision_item_field_errors(lines: list[str]) -> list[str]:
    """承認ポイントごとの `判断に影響する前提` / 却下した代替案・
    採用しない案 の欠落を見る。

    `- 無回答時のデフォルト:` の出現をポイントの終端マーカーとして使う（正本の
    承認ポイントは必ずこのフィールドを最後の方に持つ。見出しの綴り違い・番号書式
    には一切依存しない）。出現が 0 / 1 / 複数のいずれでも同じループで扱う
    （件数による分岐を作らない）。

    独立レビュー指摘: 終端マーカーを丸ごと欠くポイントは、直前ポイントの区間に
    無音で吸収され独立に検出されなかった（例: 2件目が完全に空でも 1件目の区間の
    チェックが通れば errors 0 になる）。境界そのものが取れているかを先に検査する：
    著者が宣言した承認ポイント数（`DECLARED_POINT_COUNT_RE`）と終端マーカーの
    出現数を見出し以降の区間で数え、一致しなければ個別項目のチェックへ進まず
    reject する（境界が取れない文書はチェックしない、が正本の方針）。

    セルフレビュー2巡目: 件数の突き合わせは、かつてテーマ行の形（`THEME_LINE_RE`、
    `\\d+\\.` 行）から推定していたが、round3「丸ごと空の2件目」→round4「インデント
    された2件目」→「番号の無い2件目」と3回同型の fail-open を生んだ（テーマ行が
    宣言の対象でなく行の形だったため、あらゆる隣接形を後追いで塞ぐしかなかった）。
    CLAUDE.md の L1+ 安全策（同種 high が2回続いたら線引きを戻す）に従い、ユーザー
    確認の上で件数チェックを著者の明示宣言に置き換えた。

    独立レビュー指摘（5巡目）: `無回答時のデフォルト` があるのに見出しが 1 件も
    見つからない（`area_start is None`）場合、旧実装は `block_start` を文書先頭
    （0）へフォールバックしていた。見出しが ATX の閉じ `#` 等で完全一致から外れる
    と、この経路で 30 秒判断の地の文が必須欄を充足できてしまっていた。見出しが
    見つからない場合は個別項目のチェックへ進まず reject する（skip→reject の
    統一方針: 隣接形を1つずつ塞ぐのではなく、フォールバックそのものを無くす）。
    """
    marker_indices = [
        index for index, line in enumerate(lines) if DEFAULT_ANSWER_LINE_RE.match(line)
    ]
    if not marker_indices:
        # `無回答時のデフォルト` を一度も使わない簡易な承認ポイント（Yes/No 形式の
        # 番号リストのみ等）は、この関数のチェック対象外のまま据え置く（既存挙動。
        # 誤 FAIL ゼロの実測対象）。この後のチェックはすべて、少なくとも 1 件は
        # `無回答時のデフォルト` を使っている（＝この文書はフル書式を使うつもり
        # がある）ときだけ働かせる。
        return []
    area_start = _decision_area_start_index(lines)
    if area_start is None:
        return [
            f"{DECISION_AREA_ANCHOR_LABELS[0]} / {DECISION_AREA_ANCHOR_LABELS[1]} の"
            "見出しが見つかりません（`### 判断ポイント` または `### 承認ポイント` の"
            "見出しが必要です。見出しが取れないため個別項目のチェックは行わず"
            "reject します）"
        ]
    # 走査は「次の見出し」までに区切る（独立レビュー指摘: 文書末尾までを無条件で
    # 見ていたため、承認ポイント節より後ろにある無関係な番号リスト（例:
    # `### 残タスク` の `1. / 2.` 項目）まで巻き込んでいた。終端マーカーの位置は
    # 使わない — 終端マーカーそのものを欠くポイント（このチェックが検出したい
    # 対象）は最後のマーカーより後ろに現れうるため、マーカー基準の境界では検出
    # できなくなる）。
    section_end = _section_end_index(lines, area_start)
    declared_count_match = next(
        (
            DECLARED_POINT_COUNT_RE.match(line)
            for line in lines[area_start:section_end]
            if DECLARED_POINT_COUNT_RE.match(line)
        ),
        None,
    )
    if declared_count_match is None:
        return [
            "承認ポイント数の宣言がありません。見出しの直後に `承認ポイント数: <N>` を"
            "書いてください（宣言が無いため、個別項目のチェックは行わず reject します）"
        ]
    area_marker_count = sum(1 for index in marker_indices if index >= area_start)
    declared_count = int(declared_count_match.group(1))
    if declared_count != area_marker_count:
        return [
            f"承認ポイント数の宣言（{declared_count}件）と 無回答時のデフォルト の出現数"
            f"（{area_marker_count}件）が一致しません。すべての承認ポイントに"
            "無回答時のデフォルトを書き、宣言した件数と揃えてください（境界が取れない"
            "ため、個別項目のチェックは行わず reject します）"
        ]
    errors: list[str] = []
    # 1件目のブロックは見出し行そのものではなく、最初のテーマ行から始める
    # （独立レビュー指摘: 見出し行を起点にしていたため、見出し直後・最初のテーマ行
    # より前に置いた地の文が1件目の必須欄を充足できてしまっていた）。件数の一致は
    # 宣言値で確認済みだが、それは「テーマ行が何件あるか」を保証しない（宣言方式は
    # テーマ行の形に依存しないため）。1件目の開始位置を安全に取れる保証が無い場合は
    # フォールバックせず reject する（skip→reject 統一）。
    first_theme_index = next(
        (i for i in range(area_start, section_end) if THEME_LINE_RE.match(lines[i])),
        None,
    )
    if first_theme_index is None:
        return [
            "承認ポイントの開始行（`1. <テーマ>` 等の番号付き行）が見つかりません。"
            "1件目の承認ポイントは番号付きの行で始めてください（1件目の境界が取れない"
            "ため、個別項目のチェックは行わず reject します）"
        ]
    block_start = first_theme_index
    for marker_index in marker_indices:
        block = lines[block_start : marker_index + 1]
        if not _block_has_field_content(block, (DECISION_PREMISE_LABEL,)):
            if _block_has_field(block, (DECISION_PREMISE_LABEL,)):
                errors.append(
                    f"判断に影響する前提 が未記入のままです（{marker_index + 1}行目までの承認ポイント）"
                )
            else:
                errors.append(
                    f"判断に影響する前提 がありません（{marker_index + 1}行目までの承認ポイント）"
                )
        if not _block_has_field_content(block, REJECTED_ALTERNATIVE_LABELS):
            errors.append(
                "却下した代替案 / 採用しない案 が欠落しています"
                f"（{marker_index + 1}行目までの承認ポイント）"
            )
        block_start = marker_index + 1
    return errors


def _split_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|") or len(stripped) < 2:
        return None
    inner = stripped[1:-1]
    cells = re.split(r"(?<!\\)\|", inner)
    return [c.strip() for c in cells]


def _completion_table_rows(
    lines: list[str], label_index: int, end_index: int
) -> list[list[str]] | None:
    """`完了条件の変換` 見出しの直後にある markdown table の data row だけを返す。

    見出しの直後が table 行（`|...|`）で始まらない場合は、table を使わない書き方
    （例: 見出しの直後に直接 `延期・削除: なし` を書く）として `[]` を返す。
    見出しの直後が table 行で始まるのに、その次が有効な区切り行（`|---|---|...|`）で
    無い場合は None を返し、壊れた table として扱う（独立レビュー指摘: 区切り行を
    確認せず先頭行を無条件で header として捨てていたため、区切り行の無い 1 行だけの
    table が「data 0 件」に化けて `延期・削除: なし` で素通りしていた）。

    ヘッダー・区切り行・data 行はいずれも `COMPLETION_TABLE_COLUMN_COUNT` 列に一致
    しなければ None を返す（独立レビュー指摘・2巡目: 列数を突き合わせていなかった
    ため、(a) 列が足りない延期行が `len(cells) >= 4` のガードで無音 skip され「行が
    無かったこと」にされる、(b) 延期行をそのまま header として使い区切り行だけ
    `|---|`（1セル）に短縮する、の2つの隣接形が通っていた。列数が合わない行は
    skip ではなく table 全体を不正として reject する）。

    `|` で始まる行はすべて「table 行のつもり」（`_TABLE_ROW_START_RE`）として扱い、
    正しい形（`_TABLE_ROW_RE`、閉じる `|` を持つ）でなければ None を返す（独立
    レビュー指摘・5巡目: 閉じる `|` を欠く行は `_TABLE_ROW_RE` に一致しないため、
    table がそこで legitimate に終わったことにされ、延期行が消えて `延期・削除:
    なし` で素通りしていた。table 行として始まりかけた行を「table の外」と
    誤認しない）。

    `end_index`（次の `完了条件の変換` 見出し、または文書末尾）までの区間に、
    最初の table が終わった後もなお `|` で始まる行が残っていれば None を返す
    （独立レビュー指摘・セルフレビュー: data 行ループは最初の非 `|` 行（空行等）
    で無音終了していたため、空行や地の文を1行挟むだけで、その後ろにある延期行が
    `rows` に入らず「行が無かったこと」にされ、直前の `延期・削除: なし` で
    素通りしていた。同じ入力集合を持つ blockquote 等での折り返しは対象外の
    まま残る既知の限界であり、changelog の「受け入れた限界」に記載する）。
    """
    rows: list[list[str]] = []
    index = label_index + 1
    while index < end_index and lines[index].strip() == "":
        index += 1
    if index >= end_index or not _TABLE_ROW_START_RE.match(lines[index]):
        table_end = index
    else:
        if not _TABLE_ROW_RE.match(lines[index]):
            return None
        header_cells = _split_table_row(lines[index])
        if not header_cells or len(header_cells) != COMPLETION_TABLE_COLUMN_COUNT:
            return None
        index += 1  # header row
        if index >= end_index:
            return None
        separator_cells = _split_table_row(lines[index])
        if (
            not separator_cells
            or len(separator_cells) != COMPLETION_TABLE_COLUMN_COUNT
            or not all(_TABLE_SEPARATOR_CELL_RE.match(cell) for cell in separator_cells)
        ):
            return None
        index += 1
        while index < end_index and _TABLE_ROW_START_RE.match(lines[index]):
            if not _TABLE_ROW_RE.match(lines[index]):
                return None
            cells = _split_table_row(lines[index])
            if not cells or len(cells) != COMPLETION_TABLE_COLUMN_COUNT:
                return None
            rows.append(cells)
            index += 1
        table_end = index
    for residual_index in range(table_end, end_index):
        if _TABLE_ROW_START_RE.match(lines[residual_index]):
            return None
    return rows


def _completion_table_errors(lines: list[str]) -> list[str]:
    """`完了条件の変換` 見出しの欠落と、テーブルの「扱い」列（閉じた5値）を見る。

    見出し自体が 1 件も無い場合、承認ポイント構造（`- 無回答時のデフォルト:`）を持つ
    文書に限って欠落エラーとする（独立レビュー指摘: 見出しごと省略すると D 系チェックが
    丸ごと素通りしていた。変換表がほとんど出ていなかった実測の再現）。
    `無回答時のデフォルト` を持たない簡易 HITL（既存 smoke fixture 相当）は対象外のまま
    据え置く（誤 FAIL ゼロを維持する）。

    延期・削除の行が 1 件でもあれば行ごとに `取りに行かない:` の存在を要求する
    （PR #83 巡2 の指摘: 1 行だけ満たせば全行が通っていた不備の再発防止）。
    0 件なら固定行 `延期・削除: なし` を要求する（未記録と 0 件を区別する）。
    このチェックは出現（occurrence）ごとに、次の出現または文書末尾までの区間だけを見る
    （文書全体への substring 検査だと、複数出現がある場合に他の出現の固定行を誤って
    流用してしまう）。

    table 行の形（`|...|`）で始まるのに区切り行が無い（壊れた table）場合は、
    `延期・削除: なし` の有無を見ずに reject する（独立レビュー指摘: 区切り行の無い
    1 行だけの table が「data 0 件」に化け、`延期・削除: なし` で素通りしていた）。

    `扱い` 列は `HANDLING_CLOSED_VALUES` の5値以外を reject する（独立レビュー指摘:
    閉じた5値を見ると changelog は主張していたが、実装は `延期`/`削除` 以外を検査
    していなかった）。`取りに行かない:` は「承認してほしい点」列（`TAKE_NOT_COLUMN_INDEX`）
    だけを見る（独立レビュー指摘: どのセルに書いても満たしたことになっていた）。
    """
    label_indices = [index for index, line in enumerate(lines) if COMPLETION_TABLE_LABEL in line]
    if not label_indices:
        if any(DEFAULT_ANSWER_LINE_RE.match(line) for line in lines):
            return [f"{COMPLETION_TABLE_LABEL} がありません（無条件必須です）"]
        return []
    errors: list[str] = []
    for position, label_index in enumerate(label_indices):
        next_label_index = (
            label_indices[position + 1] if position + 1 < len(label_indices) else len(lines)
        )
        rows = _completion_table_rows(lines, label_index, next_label_index)
        if rows is None:
            errors.append(
                f"{COMPLETION_TABLE_LABEL} のテーブル形式が不正です"
                "（ヘッダー行の直後に区切り行 `|---|---|---|---|` が必要です）"
            )
            continue
        for row in rows:
            if row[1] not in HANDLING_CLOSED_VALUES:
                errors.append(
                    "扱い の値が閉じた5値（"
                    f"{'/'.join(HANDLING_CLOSED_VALUES)}）のいずれでもありません: "
                    f"{' | '.join(row)}"
                )
        deferred_or_deleted_rows = [row for row in rows if row[1] in DEFERRED_DELETED_VALUES]
        if not deferred_or_deleted_rows:
            section_text = "\n".join(lines[label_index:next_label_index])
            if NONE_DEFERRED_DELETED_FIELD not in section_text:
                errors.append(
                    f"延期・削除した行がありません。固定行「{NONE_DEFERRED_DELETED_FIELD}」を"
                    "書いてください"
                )
            continue
        for row in deferred_or_deleted_rows:
            if TAKE_NOT_LABEL not in row[TAKE_NOT_COLUMN_INDEX]:
                errors.append(
                    f"延期・削除の行に「{TAKE_NOT_LABEL}」がありません: {' | '.join(row)}"
                )
    return errors


def lint_text(text: str) -> list[str]:
    errors: list[str] = []
    for marker in required_words(REQUIRED_DECISION_MARKERS, text):
        if marker not in text:
            errors.append(f"missing decision marker: {marker}")

    for group in REQUIRED_DECISION_MARKER_GROUPS:
        if not any(word in text for word in group):
            errors.append(f"missing decision marker any-of: {' / '.join(group)}")

    for marker in DECISION_SECTION_MARKERS:
        if marker in text and not _has_substantial_text(text, marker):
            errors.append(f"decision section is empty or placeholder: {marker}")

    lowered = text.lower()
    for phrase in AMBIGUOUS_PHRASES:
        if phrase.lower() in lowered:
            errors.append(f"ambiguous internal phrase remains: {phrase}")

    if "OK" in text and "戻す条件" not in text and "人間に戻す条件" not in text:
        errors.append("missing condition for when AI must return to the human")

    if any(label in text for label in PRIORITY_LABELS) and not any(
        explanation in text for explanation in PRIORITY_EXPLANATIONS
    ):
        errors.append("priority labels P0/P1/P2 are unexplained; use human-readable labels first")

    for label in sorted(_priority_labels_in(text)):
        if not any(marker in text for marker in PRIORITY_CONTENT_MARKERS[label]):
            errors.append(f"missing priority content for {label}; show what it contains")

    option_labels = _option_labels_in(text)
    if option_labels and not all(marker in text for marker in OPTION_EXPLANATION_MARKERS):
        errors.append(
            "missing option explanation: Option labels require 選択肢の説明 with 何をする案か"
        )

    if "Option B" in option_labels:
        missing = [label for label in OPTION_LABELS if label not in option_labels]
        if missing:
            errors.append(
                "Option label is undefined: Option B requires Option A / B / C "
                f"in the same HITL; missing {', '.join(missing)}"
            )

    if option_labels and "選択肢の説明" in text:
        explanation_section = _section_after(text, "選択肢の説明")
        for label in sorted(option_labels):
            if label not in explanation_section:
                errors.append(f"Option label is undefined: {label} is not defined in 選択肢の説明")
        if "何をする案か" not in explanation_section:
            errors.append("missing option explanation: 選択肢の説明 must include 何をする案か")
        missing_details = [marker for marker in OPTION_DETAIL_MARKERS if marker not in explanation_section]
        if missing_details:
            errors.append(
                "missing option explanation detail: 選択肢の説明 must include "
                + " / ".join(missing_details)
            )

    redundant_summary_count = sum(1 for heading in REDUNDANT_SUMMARY_HEADINGS if heading in text)
    if redundant_summary_count >= 2:
        errors.append("too many overlapping summary sections; consolidate into 判断ポイント")

    for section in FORBIDDEN_OPTIONAL_SECTIONS:
        if section in text:
            errors.append(f"unnecessary HITL section remains: {section}")

    if any(phrase in text for phrase in PR_BOUNDARY_PHRASES) and PR_FOLLOWUP_MARKER not in text:
        errors.append("missing PR follow-up path after this PR boundary")

    if any(phrase in text for phrase in EVIDENCE_CLAIM_PHRASES) and EVIDENCE_POPULATION_MARKER not in text:
        errors.append(
            "missing 根拠の母集団: name the source set the cited counts came from, "
            "and say whether that sample represents the population being judged"
        )

    if any(phrase in text for phrase in MULTI_PR_PHRASES) and MULTI_PR_STRATEGY_MARKER not in text:
        errors.append(
            "missing Multiple PR Strategy Options: show 単一PR / 複数PR / "
            "後続PR着手前に再承認 before approving a staged plan"
        )

    # 承認ポイントの固定フィールド受理文法（自由文は解釈しない）。
    # 正本: references/human-check-template.md § 承認ポイントの固定フィールド受理文法
    decision_lines = text.splitlines()
    errors.extend(_decision_item_field_errors(decision_lines))
    errors.extend(_completion_table_errors(decision_lines))

    return errors


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
        "ERROR: HITL Decision Quality failed.\nHITL は表示されていますが、人間が何を承認するか判断しづらい内容です。",
        "OK: HITL Decision Quality passed",
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
