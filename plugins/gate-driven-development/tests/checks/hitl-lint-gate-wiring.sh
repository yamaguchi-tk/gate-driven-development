#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hitl-lint-gate-wiring"
# HITL品質lintの判定ロジックは正しく動くが、呼び出し手順がどこにも
# 無いため実運用でほぼ実行されなかった（実測）。
# 「reference に手順を書き足しただけ」への回帰を防ぐため、実際に
# gdd_stop_hook.py から lib.hitl_lint_gate が呼ばれていること、かつ
# lib.hitl_lint_gate が配線対象3本のscriptを実際に参照していることを
# 機械的に検査する（散文の手順ではなく、hookからの到達可能性そのものを見る）。

STOP_HOOK="$ROOT/hooks/scripts/gdd_stop_hook.py"
GATE_MODULE="$ROOT/hooks/scripts/lib/hitl_lint_gate.py"

if [[ ! -f "$STOP_HOOK" ]]; then
  echo "FAIL: hitl-lint-gate-wiring: $STOP_HOOK not found"
  exit 1
fi
if [[ ! -f "$GATE_MODULE" ]]; then
  echo "FAIL: hitl-lint-gate-wiring: $GATE_MODULE not found"
  exit 1
fi

if ! grep -q "from lib.hitl_lint_gate import" "$STOP_HOOK"; then
  echo "FAIL: hitl-lint-gate-wiring: gdd_stop_hook.py does not import lib.hitl_lint_gate"
  exit 1
fi
if ! grep -q "enforce_hitl_lint_gate(" "$STOP_HOOK"; then
  echo "FAIL: hitl-lint-gate-wiring: gdd_stop_hook.py does not call enforce_hitl_lint_gate()"
  exit 1
fi

# v1で配線する3本。判定ロジックの追加はしない —— この3本以外を足すなら
# CHANGELOG に実測根拠を残した上でこのlistを更新すること。
REQUIRED_LINTS=(
  "lint-hitl-display-integrity.py"
  "lint-human-check-language.py"
  "lint-hitl-complexity.py"
)

for lint in "${REQUIRED_LINTS[@]}"; do
  if [[ ! -f "$ROOT/scripts/$lint" ]]; then
    echo "FAIL: hitl-lint-gate-wiring: referenced lint script missing: scripts/$lint"
    exit 1
  fi
  # report名とファイル名が同じタプル行に対になっていることを見る（独立レビュー
  # finding 8）。report名の文字列存在だけを見ると、HITL_LINT_SCRIPTSの
  # ファイル名側がtypoで壊れていても（＝実行時はfail-openで静かに素通り）
  # この契約テストは気づけない。
  if ! grep -q "\"${lint%.py}\".*\"${lint}\"" "$GATE_MODULE"; then
    echo "FAIL: hitl-lint-gate-wiring: lib/hitl_lint_gate.py does not pair report name with filename for $lint (HITL_LINT_SCRIPTS entry missing or filename mismatched)"
    exit 1
  fi
done

# 意図的に対象外の2本（decision-quality / stage-plan）が誤って足されていないか
# の逆検査は行わない —— 追加自体は判断であって配線契約の対象ではないため。
# ここで見るのは「配線済みと主張する3本が実際にhookから到達可能か」だけ。

echo "hitl-lint-gate-wiring: OK (3 lints wired: ${REQUIRED_LINTS[*]})"
echo "VERDICT: hitl-lint-gate-wiring: OK"
