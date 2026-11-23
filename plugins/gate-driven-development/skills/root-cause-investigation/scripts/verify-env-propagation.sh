#!/bin/bash
# verify-env-propagation.sh
#
# Verify environment variables are present and propagated at the current layer.
# Run this at each layer boundary (workflow → build → deploy → runtime) with
# the same variable list, then diff the outputs to find where a variable is
# lost or empty.
#
# Usage:
#   LAYER_NAME=build ./verify-env-propagation.sh VAR1 VAR2 VAR3
#   LAYER_NAME=deploy ./verify-env-propagation.sh VAR1 VAR2 VAR3
#
# Output is masked: the actual value is never printed. Only existence, length,
# and first/last character are shown — enough to verify a value made it across
# a boundary, without leaking secrets into logs.
#
# Exit codes:
#   0 — all variables present and non-empty
#   1 — usage error
#   2 — at least one variable UNSET or SET_EMPTY (caller decides if fatal)

set -u

if [ $# -eq 0 ]; then
  echo "Usage: $0 VAR1 [VAR2 ...]" >&2
  echo "       LAYER_NAME=<layer> $0 VAR1 [VAR2 ...]" >&2
  exit 1
fi

layer="${LAYER_NAME:-unknown}"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
host="$(hostname 2>/dev/null || echo unknown)"
pid="$$"

echo "=== [env-probe layer=${layer}] ==="
echo "timestamp: ${timestamp}"
echo "host: ${host}"
echo "pid: ${pid}"
echo "shell: ${SHELL:-unknown}"
echo "user: $(whoami 2>/dev/null || echo unknown)"
echo "---"

missing=0
for var in "$@"; do
  if [ -z "${!var+x}" ]; then
    printf "%s: UNSET\n" "$var"
    missing=$((missing + 1))
  elif [ -z "${!var}" ]; then
    printf "%s: SET_EMPTY (len=0)\n" "$var"
    missing=$((missing + 1))
  else
    val="${!var}"
    len="${#val}"
    if [ "$len" -le 2 ]; then
      # Too short to mask meaningfully; just show length
      printf "%s: SET (len=%d)\n" "$var" "$len"
    else
      first="${val:0:1}"
      last="${val: -1}"
      printf "%s: SET (len=%d, first=%s, last=%s)\n" "$var" "$len" "$first" "$last"
    fi
  fi
done

echo "---"
if [ "$missing" -gt 0 ]; then
  echo "result: ${missing} variable(s) missing or empty"
  exit 2
fi
echo "result: all variables present"
exit 0
