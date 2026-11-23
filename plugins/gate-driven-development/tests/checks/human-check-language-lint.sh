#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: human-check-language-lint"
TMP_HITL_OK=$(mktemp -t human-check-language-ok.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_HITL_OK:-}" "${TMP_HITL_BAD:-}"' EXIT
TMP_HITL_BAD=$(mktemp -t human-check-language-bad.XXXXXX.md)
cat > "$TMP_HITL_OK" <<'HITL_OK_EOF'
評価用に取り分けたサンプル（holdout）を確認します。
人が内容を確認済みにする（human-confirm）作業です。
自動テストやコマンドで実行できる状態（executable）にします。
HITL_OK_EOF
cat > "$TMP_HITL_BAD" <<'HITL_BAD_EOF'
holdout を human-confirm して executable にします。
HITL_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-human-check-language.py" "$TMP_HITL_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-human-check-language.py" "$TMP_HITL_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-human-check-language.py should reject unexplained internal terms"
  exit 1
fi

echo "VERDICT: human-check-language-lint: OK"
