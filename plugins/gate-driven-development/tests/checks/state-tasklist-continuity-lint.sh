#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: state-tasklist-continuity-lint"
TMP_CONTINUITY_ROOT=$(mktemp -d -t state-tasklist-continuity.XXXXXX)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -rf "${TMP_CONTINUITY_ROOT:-}"' EXIT
TMP_CONTINUITY_OK="$TMP_CONTINUITY_ROOT/.steering/20260607-continuity"
TMP_CONTINUITY_BAD="$TMP_CONTINUITY_ROOT/.steering/20260607-stale"
mkdir -p "$TMP_CONTINUITY_OK" "$TMP_CONTINUITY_BAD"
cat > "$TMP_CONTINUITY_OK/state.md" <<'CONTINUITY_STATE_OK_EOF'
## Gate Status
- Task ID: 20260607-continuity
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_STATE_OK_EOF
cat > "$TMP_CONTINUITY_OK/requirements.md" <<'CONTINUITY_REQ_OK_EOF'
- Revision: req-v2
CONTINUITY_REQ_OK_EOF
cat > "$TMP_CONTINUITY_OK/design.md" <<'CONTINUITY_DESIGN_OK_EOF'
- Revision: design-v2
- Stage Continuity Source: requirements.md req-v2 / tasklist.md design-v2
CONTINUITY_DESIGN_OK_EOF
cat > "$TMP_CONTINUITY_OK/tasklist.md" <<'CONTINUITY_TASKLIST_OK_EOF'
- Task ID: 20260607-continuity
- Requirements Revision: req-v2
- Design Revision: design-v2

## Current Task
- T-1
CONTINUITY_TASKLIST_OK_EOF
cat > "$TMP_CONTINUITY_BAD/state.md" <<'CONTINUITY_STATE_BAD_EOF'
## Gate Status
- Task ID: 20260607-stale
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_STATE_BAD_EOF
cat > "$TMP_CONTINUITY_BAD/requirements.md" <<'CONTINUITY_REQ_BAD_EOF'
- Revision: req-v3
CONTINUITY_REQ_BAD_EOF
cat > "$TMP_CONTINUITY_BAD/design.md" <<'CONTINUITY_DESIGN_BAD_EOF'
- Revision: design-v3
- Stage Continuity Source: old tasklist
CONTINUITY_DESIGN_BAD_EOF
cat > "$TMP_CONTINUITY_BAD/tasklist.md" <<'CONTINUITY_TASKLIST_BAD_EOF'
- Task ID: 20260607-stale
- Requirements Revision: req-v2
- Design Revision: design-v2

## Current Task
- T-1
CONTINUITY_TASKLIST_BAD_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_OK" --quiet
if "$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_BAD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-state-tasklist-continuity.py should reject stale requirements/design revision"
  exit 1
fi

# 実運用の steering 形状（Agentic Worker Header / Revision 無し / per-task Task ID 有り）で
# lint が通ることを固定する。GDD が正規手順で生成する tasklist は
# `Requirements Revision` / `Design Revision` を持たず、`Task ID` は
# `## Implementation Reviewer Selection` の per-task field としてだけ現れる。
TMP_CONTINUITY_REAL="$TMP_CONTINUITY_ROOT/.steering/20260901-realistic"
mkdir -p "$TMP_CONTINUITY_REAL"
cat > "$TMP_CONTINUITY_REAL/state.md" <<'CONTINUITY_STATE_REAL_EOF'
# Steering State

## Entry Intent
- 目的: merge gate を追加する

## Gate Status
- Task ID: 20260901-realistic
- Human Check Status: approved
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation

## Stage Continuity
- Plan Revision: R1
- Current Stage: planning
- Next Stage: workflow-handoff:task-breakdown
- Stage Continuity Source: N/A - single-stage standard
CONTINUITY_STATE_REAL_EOF
cat > "$TMP_CONTINUITY_REAL/requirements.md" <<'CONTINUITY_REQ_REAL_EOF'
# Requirements

## Summary Brief
- 一言: merge gate を追加する
CONTINUITY_REQ_REAL_EOF
cat > "$TMP_CONTINUITY_REAL/design.md" <<'CONTINUITY_DESIGN_REAL_EOF'
# Design

## Architecture
- 既存 lint に BLOCK を 1 本足す
CONTINUITY_DESIGN_REAL_EOF
cat > "$TMP_CONTINUITY_REAL/tasklist.md" <<'CONTINUITY_TASKLIST_REAL_EOF'
# W17 Merge Gate Tasklist

**Goal:** merge gate を追加する
**Stage Continuity Source:** N/A - single-stage standard

---

## Current Task
### Task: T-3 merge gate を追加する
- AC: AC-1

## Implementation Reviewer Selection
- Task ID: **Task D**（gate #16 開始時に Step 3 で再評価。stale 再利用なし）
- gdd-implementation-reviewer: selected | reason: 実装差分あり
- updated_by: gdd-implementation-gating | updated_at: 2026-09-02
CONTINUITY_TASKLIST_REAL_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_REAL" --quiet || {
  echo "FAIL: lint-state-tasklist-continuity.py should pass a realistic steering without Revision labels"
  exit 1
}

# Task ID の照合自体は残す。header で明示された task id が state と食い違う場合は検出する。
TMP_CONTINUITY_TASKID="$TMP_CONTINUITY_ROOT/.steering/20260901-taskid-mismatch"
mkdir -p "$TMP_CONTINUITY_TASKID"
cat > "$TMP_CONTINUITY_TASKID/state.md" <<'CONTINUITY_STATE_TASKID_EOF'
## Gate Status
- Task ID: 20260901-taskid-mismatch
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_STATE_TASKID_EOF
cat > "$TMP_CONTINUITY_TASKID/tasklist.md" <<'CONTINUITY_TASKLIST_TASKID_EOF'
# Task ID Mismatch Tasklist

> **For agentic workers:** Follow this tasklist together with `requirements.md` / `design.md`.

**Goal:** header の task id が state と食い違う形
**Stage Continuity Source:** N/A - single-stage standard
- Task ID: 20260607-some-other-task

---

## Current Task
- T-1
CONTINUITY_TASKLIST_TASKID_EOF
if "$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_TASKID" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-state-tasklist-continuity.py should reject task id mismatch declared in the tasklist header"
  exit 1
fi

# state.md の `Task ID` 位置は contract に固定されていない（`references/state-schema.json` /
# `references/state-field-tiers.md` のいずれにも無い）。lint-resume-integrity.py /
# lint-worktree-provenance.py / gdd_task_binding.py はいずれも全文走査で読むため、
# 本 lint だけが `## Gate Status` 内に限定して黙って照合を飛ばすことがないよう固定する。
TMP_CONTINUITY_STATE_SCOPE="$TMP_CONTINUITY_ROOT/.steering/20260901-state-scope"
mkdir -p "$TMP_CONTINUITY_STATE_SCOPE"
cat > "$TMP_CONTINUITY_STATE_SCOPE/state.md" <<'CONTINUITY_STATE_SCOPE_EOF'
# Steering State
- Task ID: 20260901-state-scope

## Gate Status
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_STATE_SCOPE_EOF
cat > "$TMP_CONTINUITY_STATE_SCOPE/tasklist.md" <<'CONTINUITY_TASKLIST_SCOPE_EOF'
- Task ID: 20260607-completely-different-task

## Current Task
- T-1
CONTINUITY_TASKLIST_SCOPE_EOF
if "$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_STATE_SCOPE" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-state-tasklist-continuity.py should compare a Task ID declared outside ## Gate Status"
  exit 1
fi

# 本 runner が canonical artifact に対して常時強制する唯一の判定
# （`build-like resume requires tasklist.md Current Task`）に判別力を持たせる。
# 他の fixture はすべて `## Current Task` を持つため、この 1 本が無いと
# 当該 guard を消す mutation が suite 全体で生存する。
TMP_CONTINUITY_NO_CURRENT="$TMP_CONTINUITY_ROOT/.steering/20260901-no-current-task"
mkdir -p "$TMP_CONTINUITY_NO_CURRENT"
cat > "$TMP_CONTINUITY_NO_CURRENT/state.md" <<'CONTINUITY_STATE_NO_CURRENT_EOF'
## Gate Status
- Task ID: 20260901-no-current-task
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_STATE_NO_CURRENT_EOF
cat > "$TMP_CONTINUITY_NO_CURRENT/tasklist.md" <<'CONTINUITY_TASKLIST_NO_CURRENT_EOF'
# No Current Task Tasklist

**Stage Continuity Source:** N/A - single-stage standard

## Pending Tasks
### Task: T-1 まだ着手していない
CONTINUITY_TASKLIST_NO_CURRENT_EOF
if "$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_NO_CURRENT" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-state-tasklist-continuity.py should reject a build-like resume without tasklist.md Current Task"
  exit 1
fi

# design の `Stage Continuity Source` 判定の単独形。既存の BAD / e2e fixture は
# Revision mismatch と併記されているため、この分岐だけを無効化する mutation が生存する。
# 併記形を単独形へ分解して判別力を持たせる（`references/self-review-lanes.md` 検査項目 6）。
TMP_CONTINUITY_DESIGN_SOURCE="$TMP_CONTINUITY_ROOT/.steering/20260901-design-source"
mkdir -p "$TMP_CONTINUITY_DESIGN_SOURCE"
cat > "$TMP_CONTINUITY_DESIGN_SOURCE/state.md" <<'CONTINUITY_STATE_DESIGN_EOF'
## Gate Status
- Task ID: 20260901-design-source
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_STATE_DESIGN_EOF
cat > "$TMP_CONTINUITY_DESIGN_SOURCE/design.md" <<'CONTINUITY_DESIGN_DESIGN_EOF'
- Stage Continuity Source: old tasklist
CONTINUITY_DESIGN_DESIGN_EOF
cat > "$TMP_CONTINUITY_DESIGN_SOURCE/tasklist.md" <<'CONTINUITY_TASKLIST_DESIGN_EOF'
- Task ID: 20260901-design-source

## Current Task
- T-1
CONTINUITY_TASKLIST_DESIGN_EOF
if "$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_DESIGN_SOURCE" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-state-tasklist-continuity.py should reject a design Stage Continuity Source that does not point back to requirements"
  exit 1
fi

# Agentic Worker Header の正準記法は `**Field:** value`。tasklist に `Task ID` を
# 記録する場合はこの記法になるため、bullet 記法だけを読んで黙って照合を飛ばさないこと。
TMP_CONTINUITY_BOLD="$TMP_CONTINUITY_ROOT/.steering/20260901-bold-field"
mkdir -p "$TMP_CONTINUITY_BOLD"
cat > "$TMP_CONTINUITY_BOLD/state.md" <<'CONTINUITY_STATE_BOLD_EOF'
## Gate Status
- Task ID: 20260901-bold-field
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_STATE_BOLD_EOF
cat > "$TMP_CONTINUITY_BOLD/tasklist.md" <<'CONTINUITY_TASKLIST_BOLD_EOF'
# Bold Field Tasklist

**Goal:** header の正準記法で task id を記録した形
**Task ID:** 20260607-completely-different-task
**Stage Continuity Source:** N/A - single-stage standard

---

## Current Task
- T-1
CONTINUITY_TASKLIST_BOLD_EOF
if "$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_BOLD" --quiet >/dev/null 2>&1; then
  echo "FAIL: lint-state-tasklist-continuity.py should read the Agentic Worker Header bold field notation"
  exit 1
fi
echo "VERDICT: state-tasklist-continuity-lint: OK"
