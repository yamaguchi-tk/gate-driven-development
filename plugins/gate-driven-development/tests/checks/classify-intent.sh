#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: classify-intent"
bash "$ROOT/tests/test_classify_intent.sh"

echo "VERDICT: classify-intent: OK"
