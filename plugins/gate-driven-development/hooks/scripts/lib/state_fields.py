"""state.md の canonical field 行を読む共通 reader。

`validate-steering-write.py` から切り出した。理由は挙動ではなく健全性で、
同ファイルが行数上限 1500 に対して余裕 3 行しかなく、R-1（空値行スキップ）を
足すと `gh pr create` を止める Codebase Health Gate に自分で阻まれるため。
挙動は変えていない。
"""
from __future__ import annotations

import re

# `from lib.X import` は使わない（呼び出し元 validate-steering-write.py と同じ理由:
# `sys.modules["lib"]` を hooks 側に固定し scripts/lib の解決を壊す）。
# `state_field_pattern` の正本は tasklist_parse（done guard Check 3 と受理集合を 1 つにするため。独立-2 B2）。
# 呼び出し元（validate-steering-write.py）はここから import するので再 export する。
from tasklist_parse import state_field_pattern, strip_fenced_blocks  # noqa: F401


def _strip_backticks_for_field_match(text: str) -> str:
    """field 行判定の直前にだけ適用する backtick 除去。

    fence 検出（```）は backtick 3 連が印なので、必ず `strip_fenced_blocks()`
    の**後**に適用する（先に全除去すると fence 境界が消え、コード例中の
    field 名らしき文字列まで拾ってしまう）。
    """
    return text.replace("`", "")


def has_state_field_line(text: str, field: str) -> bool:
    """field 行が書かれているかを判定する（値の有無は問わない）。

    「その field に触ったか」を見る trigger 用。充足検査 (has_state_field) と
    条件が違うので別述語にしている。trigger まで値必須にすると、routing field を
    **空値に更新する**書き込みが trigger をすり抜けて検査が走らない。
    """
    normalized = _strip_backticks_for_field_match(strip_fenced_blocks(text))
    return re.search(state_field_pattern(field), normalized, re.MULTILINE) is not None


def state_field_values(text: str, field: str) -> list[str]:
    """同名 field 行の**全出現**の値を、書かれた順に返す。

    下流パーサ（`gdd_extract_doc_field`）は最初の 1 行で `exit` するため、
    security boundary の判定に最初の値だけを使うと、既存値を先頭に残したまま
    別の値の行を後ろへ足すだけで write-once を迂回できる（PR #31 レビュー
    Finding Q）。宛先 field が二重化した時点で「どちらが宛先か」が読み手ごとに
    変わるので、全出現を見る側の判定が要る。backtick 正規化は
    `has_state_field_line()` と同じ（PR #31 独立レビュー Finding F-2）。
    """
    normalized = _strip_backticks_for_field_match(strip_fenced_blocks(text))
    return [
        match.group(1).split("|")[0].strip()
        for match in re.finditer(
            state_field_pattern(field) + r"[ \t]*(.+)$", normalized, re.MULTILINE
        )
    ]


def state_field_value(text: str, field: str) -> str:
    """`- Field: value | evidence: x` の `value`。**空値行は飛ばして次の一致行**を見る
    （最初の値付き一致。最終行採択にはしない）。全出現が要る write-once 判定は
    `state_field_values()`（R-1 非適用。空値行 = 宛先の削除も 1 出現として数える）。
    正本: tests/test_state_field_value_less_line_contract.py。
    """
    normalized = _strip_backticks_for_field_match(strip_fenced_blocks(text))
    for m in re.finditer(state_field_pattern(field) + r"[ \t]*(.+)$", normalized, re.MULTILINE):
        # 打ち切り判定は pipe tail 込み・返す値は pipe の前だけ（既存仕様）。よって
        # `- Field: | evidence: x` は「値付き」と見て走査を止め `""` を返す。
        if m.group(1).strip():
            return m.group(1).split("|")[0].strip()
    return ""
