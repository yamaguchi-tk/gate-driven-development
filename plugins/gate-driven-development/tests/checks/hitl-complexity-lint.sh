#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hitl-complexity-lint"
TMP_HITL_COMPLEXITY_OK=$(mktemp -t hitl-complexity-ok.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_HITL_COMPLEXITY_OK:-}" "${TMP_HITL_COMPLEXITY_BAD:-}"' EXIT
TMP_HITL_COMPLEXITY_BAD=$(mktemp -t hitl-complexity-bad.XXXXXX.md)
cat > "$TMP_HITL_COMPLEXITY_OK" <<'HITL_COMPLEXITY_OK_EOF'
## 確認
### 30秒判断
**1. Scope**
短い確認です。
HITL_COMPLEXITY_OK_EOF
cat > "$TMP_HITL_COMPLEXITY_BAD" <<'HITL_COMPLEXITY_BAD_EOF'
## 確認
### 30秒判断
**1. Scope**
**2. Stack**
**3. Test**
**4. Runtime**
**5. Review**
**6. Deploy**
detail 1
detail 2
detail 3
detail 4
detail 5
detail 6
HITL_COMPLEXITY_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-complexity.py" "$TMP_HITL_COMPLEXITY_OK" --max-lines 12 --max-approval-points 5 --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-hitl-complexity.py" "$TMP_HITL_COMPLEXITY_BAD" --max-lines 12 --max-approval-points 5 --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-hitl-complexity.py should reject over-budget HITL"
  exit 1
fi

echo "VERDICT: hitl-complexity-lint: OK"
