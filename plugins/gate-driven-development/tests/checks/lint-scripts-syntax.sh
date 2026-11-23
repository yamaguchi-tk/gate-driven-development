#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: lint-scripts-syntax"
LINT_SCRIPTS_PY=(
  "$ROOT/scripts/lint-approved-direction.py"
  "$ROOT/scripts/lint-ac.py"
  "$ROOT/scripts/lint-plan-consistency.py"
  "$ROOT/scripts/lint-hitl-display-integrity.py"
  "$ROOT/scripts/lint-hitl-complexity.py"
  "$ROOT/scripts/lint-hitl-stage-plan.py"
  "$ROOT/scripts/lint-hitl-outcome-audit.py"
  "$ROOT/scripts/lint-hitl-decision-quality.py"
  "$ROOT/scripts/lint-runtime-budget.py"
  "$ROOT/scripts/gdd-codebase-health.py"
  "$ROOT/scripts/lint-clarification-brief.py"
  "$ROOT/scripts/lint-conversation-routing-replay.py"
  "$ROOT/scripts/lint-human-check-language.py"
  "$ROOT/scripts/lint-resume-integrity.py"
  "$ROOT/scripts/lint-worktree-provenance.py"
  "$ROOT/scripts/lint-state-tasklist-continuity.py"
  "$ROOT/scripts/lint-pr-review-followup-state.py"
  "$ROOT/scripts/lint-reviewer-lineage.py"
  "$ROOT/scripts/list-merge-triggered-workflows.py"
)
# scripts/*.sh は全数を対象にする。個別列挙にしていた頃、setup-gdd-loop.sh の
# heredoc 内 backtick が奇数個になって command substitution のパースが壊れる
# 事故がこの BLOCK をすり抜け、後段の遅い e2e check でしか落ちなかった。
LINT_SCRIPTS_SH=()
while IFS= read -r script; do
  LINT_SCRIPTS_SH+=("$script")
done < <(find "$ROOT/scripts" -maxdepth 1 -name '*.sh' | sort)
if [[ ${#LINT_SCRIPTS_SH[@]} -eq 0 ]]; then
  echo "MISSING: no shell scripts found under $ROOT/scripts"
  exit 1
fi
for script in "${LINT_SCRIPTS_PY[@]}"; do
  if [[ ! -f "$script" ]]; then
    echo "MISSING: $script"
    exit 1
  fi
  if ! "$PYTHON_BIN" - "$script" 2>/dev/null <<'PY'; then
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
compile(path.read_text(encoding="utf-8"), str(path), "exec")
PY
    echo "SYNTAX FAIL: $script"
    "$PYTHON_BIN" - "$script" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
compile(path.read_text(encoding="utf-8"), str(path), "exec")
PY
    exit 1
  fi
done
for script in "${LINT_SCRIPTS_SH[@]}"; do
  if [[ ! -f "$script" ]]; then
    echo "MISSING: $script"
    exit 1
  fi
  if ! bash -n "$script" 2>/dev/null; then
    echo "SYNTAX FAIL: $script"
    bash -n "$script"
    exit 1
  fi
done

echo "VERDICT: lint-scripts-syntax: OK"
