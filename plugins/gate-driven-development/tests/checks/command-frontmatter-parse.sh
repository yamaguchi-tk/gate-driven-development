#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: command-frontmatter-parse"
"$PYTHON_BIN" - "$ROOT" <<'PYEOF'
"""frontmatter が YAML として壊れていないことを検査する。

`claude plugin validate` は壊れた frontmatter を検出するが CI では走らないため、
`commands/gdd-resume.md` の `argument-hint` がクォート漏れで parse 不能なまま
出荷された（`allowed-tools` を含む全フィールドが実行時に黙って捨てられていた）。
追加前の 37 check はどれもこれを見ていなかった。

ここではクォートされていないプレーンスカラーのうち、**実 YAML parser が拒否する形を
実測で選んで**弾く（ruby/psych との差分テストで確認した形だけを入れる）:

1. `: `（コロン + 空白）を含む — YAML はこの並びをキーの区切りと解釈する。実際に壊れた形
2. **末尾がコロン** — `description: 使い方:` も同じく mapping value と解釈されて壊れる。
   本 repo の frontmatter は日本語なので、説明がコロンで終わる形は十分あり得る
3. **`*` で始まる** — alias 参照と解釈され、対応する anchor が無いので壊れる

**この 3 形以外にも壊れる形はある**（`` `backtick` `` / `%directive` / `- dash` /
`? question` / `, comma` / 未終端クォート）。python 標準ライブラリに YAML parser が無く
本物の parse ができないための限界であり、**担保しているのは上の 3 形だけ**で、
その外側については主張しない。
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
targets = sorted(
    list(root.glob("commands/*.md"))
    + list(root.glob("skills/*/SKILL.md"))
    + list(root.glob("agents/*.md"))
)
if not targets:
    raise SystemExit("FAIL: no frontmatter targets found (glob broke?)")

KEY_VALUE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
# 値がこれらで始まる場合は YAML の引用符 / flow / ブロックスカラーなので対象外
QUOTED_OR_STRUCTURED = "\"'[{|>"
# インラインコメントの開始。YAML では **空白に続く** `#` 以降がコメントで、
# 空白を伴わない `#` はスカラーの一部（実測: `foo#notacomment: bar` は parse エラー）。
# 単純に `#` 以降を捨てると後者を見逃すため、空白付きのみを落とす。
INLINE_COMMENT = re.compile(r"\s#.*$")


def strip_inline_comment(value: str) -> str:
    """プレーンスカラーからインラインコメントを取り除く。

    コメント内の `: ` まで値として検査すると、`description: foo # example: bar` の
    ような**正しい frontmatter を CI が拒否する**（PR #9 の review 指摘）。
    """
    if value.startswith("#"):
        return ""  # 値がコメントだけ（実測: 実 parser は pass）
    return INLINE_COMMENT.sub("", value).rstrip()

failures = []
for path in targets:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if match is None:
        continue
    for lineno, line in enumerate(match.group(1).splitlines(), start=2):
        parsed = KEY_VALUE.match(line)
        if parsed is None:
            continue
        value = strip_inline_comment(parsed.group(2))
        if not value or value[0] in QUOTED_OR_STRUCTURED:
            continue
        reason = ""
        if ": " in value:
            reason = "`: `（コロン + 空白）を含む"
        elif value.endswith(":"):
            reason = "末尾がコロン"
        elif value.startswith("*"):
            reason = "`*` で始まる（YAML の alias 参照になる）"
        if reason:
            failures.append(
                f"{path.relative_to(root)}:{lineno}: "
                f"`{parsed.group(1)}` の値がクォートされておらず {reason} -> {value!r}"
            )

if failures:
    print("FAIL: frontmatter が YAML として parse できない")
    for item in failures:
        print(f"  - {item}")
    print("  値を \" \" で囲むこと。parse に失敗すると全フィールドが実行時に黙って捨てられる")
    raise SystemExit(1)

print(f"command-frontmatter-parse: OK ({len(targets)} files checked)")
PYEOF
echo "VERDICT: command-frontmatter-parse: OK"
