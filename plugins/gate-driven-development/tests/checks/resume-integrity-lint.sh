#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: resume-integrity-lint"
TMP_RESUME_ROOT=$(mktemp -d -t resume-integrity.XXXXXX)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -rf "${TMP_RESUME_ROOT:-}"' EXIT
TMP_RESUME_OK="$TMP_RESUME_ROOT/repo-ok/.steering/20260605-example-hardening-task"
TMP_RESUME_BAD="$TMP_RESUME_ROOT/repo-bad/.steering/20260601-example-review-task"
mkdir -p "$TMP_RESUME_OK" "$TMP_RESUME_BAD"
cat > "$TMP_RESUME_OK/state.md" <<RESUME_OK_EOF
## Gate Status
- Task ID: 20260605-example-hardening-task
- Active Worktree Path: $TMP_RESUME_ROOT/repo-ok
- Active Branch: codex/20260605-example-hardening-task
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
RESUME_OK_EOF
cat > "$TMP_RESUME_OK/tasklist.md" <<'RESUME_TASKLIST_EOF'
## Current Task
- T-1
RESUME_TASKLIST_EOF
cat > "$TMP_RESUME_BAD/state.md" <<RESUME_BAD_EOF
## Gate Status
- Task ID: 20260601-example-review-task
- Active Worktree Path: $TMP_RESUME_ROOT/repo-bad
- Active Branch: codex/20260605-example-dns-task
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
RESUME_BAD_EOF
cat > "$TMP_RESUME_BAD/tasklist.md" <<'RESUME_TASKLIST_BAD_EOF'
## Current Task
- T-1
RESUME_TASKLIST_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-resume-integrity.py" --steering-dir "$TMP_RESUME_OK" --branch "codex/20260605-example-hardening-task" --worktree-path "$TMP_RESUME_ROOT/repo-ok" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-resume-integrity.py" --steering-dir "$TMP_RESUME_BAD" --branch "codex/20260605-example-dns-task" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-resume-integrity.py should reject branch/task mismatch"
  exit 1
fi

echo "VERDICT: resume-integrity-lint: OK"
