#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hitl-required-fields-lint"
# 条件付き節（「〜場合だけ」）は省略と「該当なし」が区別できず、
# Option ラベルも大半で0個だった（実測）。宣言フィールド化（review-log/
# 20260916-x60-hitl-declared-fields.md）後は `<gdd-hitl-fields options="..."
# arch="..." zure="..." multi-pr="..." stage="...">` タグの5属性だけを見る（本文は一切
# 解釈しない）。warn-only で配線するため exit code 自体は他の lint script と
# 同じ contract（0=pass/1=fail/2=usage error）。
TMP_HITL_REQUIRED_OK=$(mktemp -t hitl-required-fields-ok.XXXXXX.md)
trap 'rm -f "${TMP_HITL_REQUIRED_OK:-}" "${TMP_HITL_REQUIRED_BAD:-}"' EXIT
TMP_HITL_REQUIRED_BAD=$(mktemp -t hitl-required-fields-bad.XXXXXX.md)

cat > "$TMP_HITL_REQUIRED_OK" <<'HITL_REQUIRED_OK_EOF'
## 確認

<gdd-hitl-fields options="none" arch="none" zure="none" multi-pr="none" stage="none">

<gdd-stop reason="human-check-waiting">
HITL_REQUIRED_OK_EOF

cat > "$TMP_HITL_REQUIRED_BAD" <<'HITL_REQUIRED_BAD_EOF'
## 確認

<gdd-hitl-fields> タグの宣言が無い自由文だけの HITL です。

<gdd-stop reason="human-check-waiting">
HITL_REQUIRED_BAD_EOF

"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-required-fields.py" "$TMP_HITL_REQUIRED_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-hitl-required-fields.py" "$TMP_HITL_REQUIRED_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-hitl-required-fields.py should reject a HITL missing the <gdd-hitl-fields> declaration"
  exit 1
fi
# 後片付けは EXIT trap が行う
echo "VERDICT: hitl-required-fields-lint: OK"
