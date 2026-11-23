#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: pr-review-followup-state-lint"
TMP_PR_FOLLOWUP_OK=$(mktemp -t pr-review-followup-ok.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_PR_FOLLOWUP_OK:-}" "${TMP_PR_FOLLOWUP_BAD:-}" "${TMP_AUTH_PAUSE_BAD:-}"' EXIT
TMP_PR_FOLLOWUP_BAD=$(mktemp -t pr-review-followup-bad.XXXXXX.md)
cat > "$TMP_PR_FOLLOWUP_OK" <<'PR_FOLLOWUP_OK_EOF'
PR Review Follow-up Status: clean
PR Review Follow-up Attempts: 2
PR URL: https://github.com/example/repo/pull/123
PR Head SHA: abc1234
Fresh PR Review Head SHA: abc1234
Fresh PR Checks Head SHA: abc1234
Evidence collected at: 2026-06-07T12:00:00+09:00
Fresh PR Review Evidence: gh pr view 123 --json reviews,reviewThreads,comments at 2026-06-07T12:00:00+09:00
Fresh PR Checks Evidence: gh pr checks 123 at 2026-06-07T12:00:00+09:00 pass

PR Review Follow-up:
- PR URL: https://github.com/example/repo/pull/123
- Iteration: 2
- Collected findings: 0
- Valid actionable findings: 0
- Idempotency keys processed: none
- Fixed findings: none
- Invalid / out-of-scope: none
- CI failure: none
- Verification: python3 -m unittest PASS
- Push: abc1234
- Re-review request: sent
- Next: actionable finding 0件
PR_FOLLOWUP_OK_EOF
cat > "$TMP_PR_FOLLOWUP_BAD" <<'PR_FOLLOWUP_BAD_EOF'
PR Review Follow-up Status: clean
PR Review Follow-up Attempts: 1
PR URL: https://github.com/example/repo/pull/123
Fresh PR Review Evidence: gh pr view 123 --json reviews,reviewThreads,comments at 2026-06-07T12:00:00+09:00
Fresh PR Checks Evidence: gh pr checks 123 at 2026-06-07T12:00:00+09:00 pass

PR Review Follow-up:
- PR URL: https://github.com/example/repo/pull/123
- Iteration: 2
- Collected findings: 0
- Valid actionable findings: 0
- Fixed findings: thread-1
- Verification: python3 -m unittest PASS
- Push: abc1234
- Re-review request: sent
- Next: actionable finding 0件
PR_FOLLOWUP_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-pr-review-followup-state.py" "$TMP_PR_FOLLOWUP_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-pr-review-followup-state.py" "$TMP_PR_FOLLOWUP_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-pr-review-followup-state.py should reject premature clean state"
  exit 1
fi

# S-1: auth-waiting pause の構造化マーカーを release gate に接続する。
# followup SKILL が広告する CLI enforcement point (--skill) を実際に走らせ、
# 不正マーカーを reject することを確認する。
"$PYTHON_BIN" "$ROOT/scripts/lint-pr-review-followup-state.py" \
  --skill "$ROOT/skills/gdd-pr-review-followup/SKILL.md" --quiet
TMP_AUTH_PAUSE_BAD=$(mktemp -t auth-pause-bad.XXXXXX)
cat > "$TMP_AUTH_PAUSE_BAD" <<'AUTH_PAUSE_BAD_EOF'
### auth pause 再開規約
散文だけで構造化ブロック（gdd-auth-pause）が無い。
AUTH_PAUSE_BAD_EOF
if "$PYTHON_BIN" "$ROOT/scripts/lint-pr-review-followup-state.py" \
    --skill "$TMP_AUTH_PAUSE_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-pr-review-followup-state.py --skill should reject a missing gdd-auth-pause marker"
  rm -f "$TMP_AUTH_PAUSE_BAD"
  exit 1
fi

echo "VERDICT: pr-review-followup-state-lint: OK"
