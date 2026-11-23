#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hitl-outcome-audit-lint"
TMP_HITL_OUTCOME_OK=$(mktemp -t hitl-outcome-ok.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_HITL_OUTCOME_OK:-}" "${TMP_HITL_OUTCOME_BAD:-}"' EXIT
TMP_HITL_OUTCOME_BAD=$(mktemp -t hitl-outcome-bad.XXXXXX.md)
cat > "$TMP_HITL_OUTCOME_OK" <<'HITL_OUTCOME_OK_EOF'
## HITL Outcome Audit

| Approved Direction の欄 | 最終成果物で見るもの | 結果 | Evidence / notes |
|---|---|---|---|
| 何を作るか | diff | match | ok |
| 確認しないこと | unsupported scope | N/A | not applicable |
HITL_OUTCOME_OK_EOF
cat > "$TMP_HITL_OUTCOME_BAD" <<'HITL_OUTCOME_BAD_EOF'
## HITL Outcome Audit

| Approved Direction の欄 | 最終成果物で見るもの | 結果 | Evidence / notes |
|---|---|---|---|
| どう作るか | stack | mismatch | changed silently |
| 確認すること | tests | unverified | missing evidence |
HITL_OUTCOME_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-outcome-audit.py" "$TMP_HITL_OUTCOME_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-hitl-outcome-audit.py" "$TMP_HITL_OUTCOME_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-hitl-outcome-audit.py should reject mismatch / unverified"
  exit 1
fi

echo "VERDICT: hitl-outcome-audit-lint: OK"
