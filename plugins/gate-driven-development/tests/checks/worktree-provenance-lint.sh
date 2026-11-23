#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: worktree-provenance-lint"
TMP_PROVENANCE_ROOT=$(mktemp -d -t worktree-provenance.XXXXXX)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -rf "${TMP_PROVENANCE_ROOT:-}"' EXIT
TMP_PROVENANCE_OK="$TMP_PROVENANCE_ROOT/repo-ok/.steering/20260607-gdd-provenance"
TMP_PROVENANCE_BAD="$TMP_PROVENANCE_ROOT/repo-bad/.steering/20260601-old-task"
mkdir -p "$TMP_PROVENANCE_OK" "$TMP_PROVENANCE_BAD"
cat > "$TMP_PROVENANCE_OK/state.md" <<PROVENANCE_OK_EOF
## Gate Status
- Task ID: 20260607-gdd-provenance
- Active Worktree Path: $TMP_PROVENANCE_ROOT/repo-ok
- Active Branch: codex/20260607-gdd-provenance
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
PROVENANCE_OK_EOF
cat > "$TMP_PROVENANCE_BAD/state.md" <<PROVENANCE_BAD_EOF
## Gate Status
- Task ID: 20260601-old-task
- Active Worktree Path: $TMP_PROVENANCE_ROOT/repo-bad
- Active Branch: codex/20260607-new-topic
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
PROVENANCE_BAD_EOF
cat > "$TMP_PROVENANCE_ROOT/diff-files.txt" <<'PROVENANCE_DIFF_EOF'
.steering/20260607-new-topic/state.md
plugins/gate-driven-development/skills/gdd-dev/SKILL.md
PROVENANCE_DIFF_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-worktree-provenance.py" --steering-dir "$TMP_PROVENANCE_OK" --branch "codex/20260607-gdd-provenance" --worktree-path "$TMP_PROVENANCE_ROOT/repo-ok" --pr-head-branch "codex/20260607-gdd-provenance" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-worktree-provenance.py" --steering-dir "$TMP_PROVENANCE_BAD" --branch "codex/20260607-new-topic" --worktree-path "$TMP_PROVENANCE_ROOT/repo-bad" --pr-head-branch "codex/20260607-new-topic" --diff-files "$TMP_PROVENANCE_ROOT/diff-files.txt" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-worktree-provenance.py should reject task / branch / diff mismatch"
  exit 1
fi

echo "VERDICT: worktree-provenance-lint: OK"
