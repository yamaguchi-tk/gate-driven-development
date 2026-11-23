#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: mcp-retry-token"

# AC-21 は**機械強制ではない**。LLM が実際に指示へ従うかは決定論的に検証できず、
# ここで担保できるのは「この文言が配布物に存在すること」まで。
# LLM が従うかはテスト不能（non-testable）なため、文言の存在確認が静的な下限。

f="$ROOT/references/common-guardrails.md"
if [[ ! -f "$f" ]]; then
  echo "MISSING FILE: references/common-guardrails.md"
  echo "FAIL: mcp-retry-token"
  exit 1
fi
if ! grep -qF -- "1 回だけ再試行" "$f"; then
  echo "MISSING: references/common-guardrails.md : MCP 再試行1回の文言"
  echo "FAIL: mcp-retry-token"
  exit 1
fi
# 文言だけあって Honest Limitations が落ちると、機械強制だと誤読される。
#
# 検査語は **`Honest Limitations` ではなく AC-21 固有の断り文**にする ——
# 前者は同ファイルの別節（`## Honest Limitations（率直な自己制限の明示）`）にも
# 現れるため、AC-21 の断りを丸ごと消しても**無関係な出現で検査が満たされてしまう**
# （T-23 の判別力測定で実際に SURVIVED した）。
# AC-21 は「**1 回だけ再試行してから停止する**」の 2 要素。上限だけを検査すると
# 動作を規定する後半（停止・報告）が落ちても緑のままになる。`references/` は
# 残枠 0 で圧縮圧力が最大なので、後半は真っ先に削られる位置にある。
if ! grep -qF -- "停止して人間に報告する" "$f"; then
  echo "MISSING: references/common-guardrails.md : AC-21 の停止・報告の指示"
  echo "FAIL: mcp-retry-token"
  exit 1
fi
if ! grep -qF -- "これは機械強制ではない" "$f"; then
  echo "MISSING: references/common-guardrails.md : AC-21 の Honest Limitations（機械強制ではない旨）"
  echo "FAIL: mcp-retry-token"
  exit 1
fi

# 受理面の表明（T-30 の方針）—— 合格が何を保証し、何を保証しないかを合格時に併記する。
# これを書いていなかったため、**配布ギャップ（ADV-T23-4）がこの検査の緑では見えない**ことが
# 記録側でしか捕まらなかった。
echo "mcp-retry-token: OK"
echo "  scanned: 次の 3 文字列が references/common-guardrails.md の**どこかに**存在すること"
echo "           —— 1 回だけ再試行 / 停止して人間に報告する / これは機械強制ではない"
echo "           （独立した grep 3 本。行・節・文脈は問わない）"
echo "  NOT scanned:"
echo "    - 3 要素が AC-21 という**1 本のルールとして同居**していること。実測: ルール行を丸ごと消して"
echo "      3 トークンを HTML コメント 1 行へ散らすと**この検査は SURVIVED する**（exit 0）"
echo "    - 断りが**ルール本文のインラインラベル**として置かれていること（AC-21 が指定する配置。"
echo "      同名節への配置は AC-21 が明示的に却下している）。実測: インラインラベルを同名節へ移設しても"
echo "      **この検査は SURVIVED する**（exit 0）"
echo "    - この文言が実際に LLM に届くか（配布）。common-guardrails.md を参照しない skill には届かず、"
echo "      未参照側には自律継続の導線が含まれる。件数の正本は carry-forward ADV-T23-4 で、導出は"
echo "      grep -rl common-guardrails skills/ | wc -l と skills/*/SKILL.md の総数の比"
echo "      （ここに件数を書かない —— 同じ数値が複数箇所で別々に古くなるため）"
echo "    - LLM が指示に従うか（AC-21 は機械強制ではない）"
echo "VERDICT: mcp-retry-token: OK"
