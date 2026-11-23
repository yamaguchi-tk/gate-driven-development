#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: codebase-health-smoke"
TMP_CODEBASE_HEALTH=$(mktemp -d -t gdd-codebase-health.XXXXXX)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -rf "${TMP_CODEBASE_HEALTH:-}"' EXIT
mkdir -p "$TMP_CODEBASE_HEALTH/src"
printf "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n" > "$TMP_CODEBASE_HEALTH/pyproject.toml"
printf "a\nb\nc\nd\n" > "$TMP_CODEBASE_HEALTH/src/large.py"
CODEBASE_HEALTH_JSON=$("$PYTHON_BIN" "$ROOT/scripts/gdd-codebase-health.py" --repo-root "$TMP_CODEBASE_HEALTH" --max-file-lines 3 --format json)
"$PYTHON_BIN" - "$CODEBASE_HEALTH_JSON" <<'PY'
import json
import sys

report = json.loads(sys.argv[1])
categories = {finding["category"] for finding in report["findings"]}
if "large_file" not in categories or "missing_lockfile" not in categories:
    raise SystemExit(f"missing expected categories: {categories}")
PY
if "$PYTHON_BIN" "$ROOT/scripts/gdd-codebase-health.py" --repo-root "$TMP_CODEBASE_HEALTH" --max-file-lines 3 --fail-on high >/dev/null 2>&1; then
  echo "FAIL: gdd-codebase-health.py should fail on high findings"
  rm -rf "$TMP_CODEBASE_HEALTH"
  exit 1
fi

for rel in "references/state-machine-overview.md" "references/contract-overview.md"; do
  lines=$(wc -l < "${ROOT}/${rel}" | tr -d ' ')
  if [[ "${lines}" -gt 30 ]]; then
    echo "OVERVIEW_LINE_BUDGET_EXCEEDED: ${rel} has ${lines} lines > 30"
    exit 1
  fi
done

for rel in \
  "agents/plan-reviewer.md" \
  "agents/plan-reviewer-feasibility-strict.md" \
  "agents/code-reviewer.md" \
  "agents/security-reviewer.md" \
  "agents/gdd-requirements-reviewer.md" \
  "agents/gdd-requirements-solution-reviewer.md" \
  "agents/gdd-design-reviewer.md" \
  "agents/gdd-spec-reviewer.md" \
  "agents/gdd-quality-reviewer.md" \
  "agents/gdd-comprehensive-reviewer.md" \
  "agents/gdd-code-reviewer.md" \
  "agents/gdd-nfr-reviewer.md" \
  "agents/gdd-feasibility-reviewer.md" \
  "skills/requesting-code-review/SKILL.md" \
  "skills/receiving-code-review/SKILL.md"
do
  if [[ -e "${ROOT}/${rel}" ]]; then
    echo "LEGACY FILE SHOULD NOT EXIST: ${rel}"
    exit 1
  fi
done
echo "VERDICT: codebase-health-smoke: OK"
