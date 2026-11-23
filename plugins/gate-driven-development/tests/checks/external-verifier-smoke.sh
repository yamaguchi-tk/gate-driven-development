#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

SNYK_PLUGIN_ROOT="$(cd "${SNYK_PLUGIN_ROOT:-/nonexistent}" 2>/dev/null && pwd || true)"
if [[ -n "$SNYK_PLUGIN_ROOT" && -f "$SNYK_PLUGIN_ROOT/hooks/scripts/update-snyk-scan-state.js" && -n "${NODE_BIN:-}" ]]; then
  echo "BLOCK: external-verifier-smoke"
  bash "$ROOT/scripts/external-verifier-smoke.sh" --snyk-plugin-root "$SNYK_PLUGIN_ROOT"
  echo "VERDICT: external-verifier-smoke: OK"
else
  echo "SKIP: external-verifier-smoke (SNYK_PLUGIN_ROOT or node not available)"
  echo "VERDICT: external-verifier-smoke: SKIP"
fi
