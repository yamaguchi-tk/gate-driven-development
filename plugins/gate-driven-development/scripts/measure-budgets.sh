#!/usr/bin/env bash
# GDD 自己開発時の budget 残枠を 1 コマンドで実測する。
#
# 背景（2026-08-31 実測）: ある task の planning subagent は budget・行数の実測に
# Bash を何十本も費やした。同じ測定は毎回同型なので、5 系統の実測と上限との差を
# 1 回で出す。上限値の正本は tests/checks/skill-body-budget.sh（この script は
# 読み取り専用の集約 view であり、判定はしない。判定は check 側が担う）。
#
# 使い方: bash plugins/gate-driven-development/scripts/measure-budgets.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK="$ROOT/tests/checks/skill-body-budget.sh"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# 上限は skill-body-budget.sh の**実行行**（バックスラッシュ継続の呼び出しブロック）から
# 読む。コメント行にも旧値の `--max-...` 表記があるため、行頭が `  --max-` の
# 実引数行に限定する（二重正本を作らない）
ref_limit=$(grep -oE 'REFERENCES_LINE_BUDGET_EXCEEDED: \$\{reference_lines\} > [0-9]+' "$CHECK" | grep -oE '[0-9]+$')
lint_args=$(grep -E '^[[:space:]]+--max-[a-z-]+ [0-9]+' "$CHECK" | grep -oE -- '--max-[a-z-]+ [0-9]+' | tr '\n' ' ')
express_limit=$(printf '%s' "$lint_args" | grep -oE -- '--max-express-estimated-tokens [0-9]+' | grep -oE '[0-9]+$')
standard_limit=$(printf '%s' "$lint_args" | grep -oE -- '--max-standard-estimated-tokens [0-9]+' | grep -oE '[0-9]+$')

ref_lines=$(find "$ROOT/references" -name '*.md' -type f -print0 | xargs -0 wc -l | tail -n 1 | awk '{print $1}')
# shellcheck disable=SC2086
profile_out=$("$PYTHON_BIN" "$ROOT/scripts/lint-runtime-budget.py" "$ROOT" $lint_args 2>/dev/null || true)
express_actual=$(printf '%s\n' "$profile_out" | grep -oE 'express runtime profile: lines=[0-9]+, estimated runtime tokens=[0-9]+' | grep -oE '[0-9]+$' | head -1)
standard_actual=$(printf '%s\n' "$profile_out" | grep -oE 'standard runtime profile: lines=[0-9]+, estimated runtime tokens=[0-9]+' | grep -oE '[0-9]+$' | head -1)

printf '%-34s %10s %10s %10s\n' "budget" "limit" "actual" "headroom"
printf '%-34s %10s %10s %10s\n' "references/*.md lines (ratchet)" "$ref_limit" "$ref_lines" "$((ref_limit - ref_lines))"
if [[ -n "${express_actual:-}" ]]; then
  printf '%-34s %10s %10s %10s\n' "express runtime tokens" "$express_limit" "$express_actual" "$((express_limit - express_actual))"
  printf '%-34s %10s %10s %10s\n' "standard runtime tokens" "$standard_limit" "$standard_actual" "$((standard_limit - standard_actual))"
else
  echo "runtime profile: lint-runtime-budget.py の出力形式が想定と異なる。直接実行して確認: $PYTHON_BIN $ROOT/scripts/lint-runtime-budget.py"
fi
echo
echo "判定（block するのは check 側）: bash $CHECK"
