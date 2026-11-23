#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

# 分類5 の下位型「限定・全称の未測定断定」の出荷文書側の機械検査。
# 規律の正本は references/self-review-lanes.md § 分類5 の下位型: 限定・全称の未測定断定。
#
# 述語: 限定宣言マーカーを 1 つ以上含む出荷文書は、同一文書内に実測記録マーカーを持つこと。
# 語彙は検査側に literal を置かず、正本節の 2 行から機械導出する（片側だけ書き換えると
# 検査が空回りする形を作らないため）。導出が空になる形は独立に FAIL にする（空洞化アンカー）。
#
# 対象範囲を出荷文書に限る理由（実測に基づく）:
#   - 語彙を却下語彙（下の REJECTED_VOCAB）まで広げると hits が桁違いに増えて運用不能に
#     なり、既存出荷内容が FAIL する。断定の強さが構文で判るマーカーだけに絞ると
#     偽陽性 0 になる。**この段落が扱う量（却下語彙の hits / 該当文書数 / 走査文書数）は
#     すべて本 check の成功時出力が正本**。コメントには件数 literal も導出コマンドも
#     置かない — 手書きで量を書く形を残すと、走査範囲を変えたときに黙って陳腐化し、
#     その陳腐化を検出する検査が存在しない経路をコメント側に作ってしまうため
#   - `.steering/` は出荷されないため統合先では対象 0 件になり、fail-open 経路になる
#
# 両側 pin: 語彙・宣言形・走査範囲・走査除外は正本の宣言行から機械導出し、下の literal と
# 一致することを assert する。正本側だけを書き換えても検査側 literal だけを書き換えても
# FAIL になる（片側だけの改変で走査範囲や述語が黙って変わる経路を塞ぐ）。
echo "BLOCK: bounded-claim-evidence"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import os
import re
import sys

root = sys.argv[1]

LANES_DOC = "references/self-review-lanes.md"
# 宣言行の見出し語。検査側が持つのはこのラベルだけで、値そのものは正本から導出する。
CLAIM_LABEL = "**限定宣言マーカー**"
EVIDENCE_LABEL = "**実測記録マーカー**"
DECLARATION_LABEL = "**実測記録の宣言形**"
SCAN_LABEL = "**走査範囲**"
EXCLUDE_LABEL = "**走査除外**"
# 以下 3 つは正本の宣言行と突き合わせる対向側 literal（両側 pin）。単独では権威を持たない。
# 走査対象。正本節が宣言する出荷文書の範囲と同じ。`CHANGELOG.md` は他文書の断定を
# 引用する release log であり、断定の契約面は引用元の文書側にあるため対象外にする
# （release log は追記され続けるため、該当行の件数・帰属をここに書かない）。
SCAN_DIRS = ("references", "skills", "docs")
# 末尾 "/" のエントリはディレクトリ接頭辞として扱う。日付付きの過去 PR アーカイブを外す理由は
# 「決定・計画・監査の時点記録で後から追記しないため、新規則の遡及適用が閉じた記録の改変になる」こと
# （除外集合にマーカー該当の文書が出た場合、それが欠陥類型の呼称なのか自文書の限定宣言
#  なのかは当該文書を開いて判定する。件数はここに書かない）。`docs/references-archive/` は残す。
EXCLUDED = (LANES_DOC, "CHANGELOG.md", "docs/design/", "docs/plans/", "docs/audits/")
BACKTICKED = re.compile(r"`([^`]+)`")
# 却下した広い語彙。これは「測った値」ではなく却下案の**定義**なのでここに置く。
# この語彙の hits は成功時出力に載せ、件数の正本を機械側に一本化する。
REJECTED_VOCAB = ("のみ", "だけ", "すべて", "必ず")
# 実測記録は「散文で言及した」ではなく「節として宣言した」ことを要求する。
# 参照だけ残して実測記録の中身を消す形（B2）を KILL するための構造述語。
EVIDENCE_DECLARATION = "**{}**"

failures = []


def read(rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError) as exc:
        # fail-closed: 対象ファイルを消せば検査が消える形を作らない。
        # L-108: 非 UTF-8 を traceback で終わらせない（T-29 の version-not-consumed と同じ担保）。
        failures.append(f"{rel}: 検査対象ファイルを読めません ({exc})")
        return None


def derive(text, label):
    """正本節の宣言行から backtick 括りの語彙を機械導出する。"""
    if text is None:
        return []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- " + label):
            return BACKTICKED.findall(stripped)
    failures.append(f"{LANES_DOC}: 語彙宣言行 '{label}' が見つかりません")
    return []


lanes = read(LANES_DOC)
claim_markers = derive(lanes, CLAIM_LABEL)
evidence_markers = derive(lanes, EVIDENCE_LABEL)

# 空洞化アンカー: 語彙を空にすれば全文書が素通りする形を塞ぐ。
if not claim_markers:
    failures.append(f"{LANES_DOC}: 限定宣言マーカーの導出結果が空です")
if not evidence_markers:
    failures.append(f"{LANES_DOC}: 実測記録マーカーの導出結果が空です")


def pin(label, derived, literal):
    """正本の宣言行から導出した値と検査側 literal の一致を両側から assert する。"""
    if not derived:
        failures.append(f"{LANES_DOC}: {label} の導出結果が空です")
        return
    # 宣言は集合として比較する（並び順は述語に影響しない）。
    if sorted(derived) != sorted(literal):
        failures.append(
            f"{LANES_DOC}: {label} の宣言 {sorted(derived)} が検査側の {sorted(literal)} と"
            "一致しません（正本と検査のどちらか一方だけを変更した）"
        )


pin(SCAN_LABEL, [d.rstrip("/") for d in derive(lanes, SCAN_LABEL)], SCAN_DIRS)
pin(EXCLUDE_LABEL, derive(lanes, EXCLUDE_LABEL), EXCLUDED)
pin(DECLARATION_LABEL, derive(lanes, DECLARATION_LABEL), (EVIDENCE_DECLARATION,))

# 走査除外（`EXCLUDED`）を適用する。正本節そのものを外す理由は、語彙宣言行が限定宣言
# マーカーと実測記録マーカーの両方を必ず含むため、対象に残すと matched が常に 1 以上に
# なり、下の空洞化アンカー（実集合 0 件 = 語彙が実体から乖離）が一度も発火しない
# 自己充足の fail-open になること。
targets = []
for base in SCAN_DIRS:
    for dirpath, _dirnames, filenames in os.walk(os.path.join(root, base)):
        for name in sorted(filenames):
            if name.endswith(".md"):
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                if rel in EXCLUDED:
                    continue
                if any(e.endswith("/") and rel.startswith(e) for e in EXCLUDED):
                    continue
                targets.append(rel)
targets.sort()

if not targets:
    # 空洞化アンカー: 走査対象が 0 件なら「常に成功する検証」になる
    failures.append("走査対象の出荷文書が 0 件です")

matched = 0
rejected_hits = 0
if claim_markers and evidence_markers:
    for rel in targets:
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                body = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            # L-108: 非 UTF-8 の走査対象も traceback ではなく FAIL 行で落とす。
            failures.append(f"{rel}: 読めません ({exc})")
            continue
        rejected_hits += sum(body.count(v) for v in REJECTED_VOCAB)
        hits = [m for m in claim_markers if m in body]
        if not hits:
            continue
        matched += 1
        declarations = [EVIDENCE_DECLARATION.format(m) for m in evidence_markers]
        if not any(d in body for d in declarations):
            failures.append(
                f"{rel}: 限定宣言 {hits} を書いているが実測記録の宣言 "
                f"{declarations} が同一文書に無い"
            )
    # 空洞化アンカー: 実集合 0 件は「マーカー語彙が実体から外れた」ことしか意味しない。
    # 0 件で PASS すると、語彙を実在しない語に差し替えるだけで検査が消える。
    if matched == 0:
        failures.append(
            f"限定宣言マーカー {claim_markers} に該当する出荷文書が 0 件です"
            "（語彙が実体から乖離している）"
        )

if failures:
    for failure in failures:
        print(f"FAIL: bounded-claim-evidence: {failure}")
    sys.exit(1)
print(
    f"bounded-claim-evidence: OK (限定宣言 {matched} 文書すべてに実測記録あり / "
    f"走査 {len(targets)} 文書 / 却下語彙 {list(REJECTED_VOCAB)} の hits {rejected_hits})"
)
PY
echo "VERDICT: bounded-claim-evidence: OK"
