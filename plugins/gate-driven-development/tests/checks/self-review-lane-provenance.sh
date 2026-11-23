#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

# AC-21 / CT-5: 分類根拠に社内識別子（社内 repo 名・課題番号・製品名）を持ち込ませない。
# 判定は allow-list 文法（design.md § Sensitive Data / Masking Policy）。denylist を採らない理由は
# 「社内 repo 名は小文字ハイフン連結で一般英単語と区別できず、製品名はカタカナで語境界も無い」ため、
# 著者が思いついた違反しか落とせない検査（= 常に成功する検証）になること。
echo "BLOCK: self-review-lane-provenance"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import re
import sys

root = sys.argv[1]

# 検査対象 1: 分類根拠セクション（正本）。見出しから次の `## ` 見出しの手前まで。
LANES_DOC = "references/self-review-lanes.md"
LANES_HEADING = "## 検出漏れ分類 v1"
# 検査対象 2: 3f の分類根拠ブロック（マーカー間のみ）。既存 3f 本文（`#201` 等の出典表記を含む）は対象外。
SKILL_DOC = "skills/gdd-pr-review/SKILL.md"
START_MARKER = "<!-- self-review-lane-provenance:start -->"
END_MARKER = "<!-- self-review-lane-provenance:end -->"

# allow-list（定義済み分類 ID / 数字 / レーン名 / 定義済み型名 / 定義済み固定語彙）。
# ここは対象ファイルから導出しない。導出すると対象に何を書いても通る「常に成功する検証」になる。
ALLOWED_ASCII = {"A", "B", "C", "D", "E", "ID", "3f", "v1"}
ALLOWED_KATAKANA = {"レーン", "レビュー", "コマンド", "ガード", "データ", "ベース", "ロールバック"}
# 固有名詞の担体になる token 種別だけを取り出す。漢字・ひらがなの一般語は token 化しない
# （残余リスクとして受容。design.md が挙げる担体は小文字ハイフン連結 / カタカナ / `#<数字>`）。
# 残余は 2 種類ある（いずれも AC-21 / design.md の scope 内で、spec 違反ではない）:
#   L-96 対象範囲: 検査するのは上の 2 対象だけで、同 file の
#     § 実装差分レビューの検査項目（由来実例の蓄積先）は**対象節の外**なので検査しない
#   L-97 担体の形: 全角の英数字・カタカナ（`＃201` / `ｋａｉｐｏｋｅ`）は上の正規表現に
#     掛からないため無検出。半角へ正規化してから token 化すれば閉じられる
ASCII_TOKEN = re.compile(r"#?[A-Za-z0-9][A-Za-z0-9._/-]*")
KATAKANA_TOKEN = re.compile(r"[ァ-ヶヷ-ヺー]+")
DIGITS_ONLY = re.compile(r"\d+$")

failures = []


def read(rel):
    try:
        with open(f"{root}/{rel}", encoding="utf-8") as f:
            return f.read()
    except OSError:
        # fail-closed: 対象ファイルを消せば検査が消える形を作らない
        failures.append(f"{rel}: 検査対象ファイルが存在しません")
        return None


def scan(rel, first_line, block):
    for offset, line in enumerate(block.split("\n")):
        for token in ASCII_TOKEN.findall(line):
            token = token.rstrip("._/-")
            if DIGITS_ONLY.match(token) or token in ALLOWED_ASCII:
                continue
            failures.append(f"{rel}:{first_line + offset}: allow-list 外の語 '{token}'")
        for token in KATAKANA_TOKEN.findall(line):
            if token in ALLOWED_KATAKANA:
                continue
            failures.append(f"{rel}:{first_line + offset}: allow-list 外の語 '{token}'")


text = read(LANES_DOC)
if text is not None:
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith(LANES_HEADING)]
    if not starts:
        failures.append(f"{LANES_DOC}: 分類根拠セクション '{LANES_HEADING}' が見つかりません")
    for start in starts:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        section = lines[start:end]
        # 空洞化アンカー: 見出しだけ残して中身を消せば通る形を塞ぐ。
        # `any(...)` では header 行と区切り行の 2 本だけを残して本文 10 行を消す形が
        # 素通りする（L-94 = 実測 SURVIVOR）ため、contract test と同じ述語（>= 3 行）にする。
        if sum(1 for line in section[1:] if line.startswith("|")) < 3:
            failures.append(f"{LANES_DOC}:{start + 1}: 分類根拠セクションに分類表の行がありません")
        scan(LANES_DOC, start + 1, "\n".join(section))

text = read(SKILL_DOC)
if text is not None:
    blocks, cursor = [], 0
    while True:
        start = text.find(START_MARKER, cursor)
        if start == -1:
            break
        end = text.find(END_MARKER, start)
        if end == -1:
            break
        blocks.append((start + len(START_MARKER), text[start + len(START_MARKER):end]))
        cursor = end + len(END_MARKER)
    if not blocks:
        # fail-closed: マーカーを消すだけで violation ループが 1 度も回らない形を塞ぐ
        failures.append(f"{SKILL_DOC}: provenance マーカーブロックが 1 個も存在しません")
    for pos, block in blocks:
        first_line = text.count("\n", 0, pos) + 1
        if not block.strip():
            failures.append(f"{SKILL_DOC}:{first_line}: マーカー間の分類根拠ブロックが空です")
        scan(SKILL_DOC, first_line, block)

if failures:
    for failure in failures:
        print(f"FAIL: self-review-lane-provenance: {failure}")
    sys.exit(1)
print("self-review-lane-provenance: OK (分類根拠は allow-list 語彙のみ)")
PY
echo "VERDICT: self-review-lane-provenance: OK"
