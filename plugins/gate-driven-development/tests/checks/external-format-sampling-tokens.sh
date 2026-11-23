#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}"

echo "BLOCK: external-format-sampling-tokens"

# 外部の形式（API 応答・通知 payload・ログ書式）に依存する AC を、実データの実測より
# 先に書かないための発火点を pin する。2026-10-02、GDD を使う別の repo のタスクで、
# 組み立て直した fixture から欄の位置を推測して AC と design を書き、requirements
# レビュー 2 回・design レビュー 2 回の後に生 JSON で推測違いが分かった。design の
# 値の形の規則も、実値に当てると大半を捨てていた。
# 発火点は、各 phase で実際に読まれる手順の行（brainstorming の 8a、requirements-gating
# の Spec Self-Review Checklist、design-gating の Step 5d）。文言ではなく見出しと
# 手順の鍵だけを pin する。

fail=0

req() { # $1=relative file, $2=token
  local f="$ROOT/$1"
  if [[ ! -f "$f" ]]; then
    echo "MISSING FILE: $1"
    fail=1
    return
  fi
  if ! grep -qF -- "$2" "$f"; then
    echo "MISSING: $1 : $2"
    fail=1
  fi
}

# --- brainstorming: 実測を AC より先に置く（skill 本文が発火点、手順の正本は references） ---
req "skills/gdd-brainstorming/SKILL.md" "外部形式の実測"
req "references/brainstorming-steps.md" "外部形式の実測（External Format Sampling）"
req "references/brainstorming-steps.md" "読み取り専用"
req "references/brainstorming-steps.md" "worktree の外"
req "references/brainstorming-steps.md" "合成値"

# --- requirements-gating: human check の前に実測の有無を見る ---
req "references/requirements-gating-steps.md" "外部形式に依存する AC"

# --- design-gating: 規則を実値に当てて落ちる件数を記録する ---
req "skills/gdd-design-gating/SKILL.md" "5d. **規則の実値検算"
req "skills/gdd-design-gating/SKILL.md" "落ちた件数"

if (( fail != 0 )); then
  echo "FAIL: external-format-sampling-tokens"
  exit 1
fi

echo "VERDICT: external-format-sampling-tokens: OK"
