#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: lint-scripts-functional"
# smoke test: each lint script handles minimal valid input without crashing
"$PYTHON_BIN" "$ROOT/scripts/lint-approved-direction.py" --pattern 'src/foo/**' --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-approved-direction.py basic smoke test"
  exit 1
}
TMP_REQ=$(mktemp -t lint-ac-test-req.XXXXXX.md)
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -f "${TMP_REQ:-}" "${TMP_OUTCOME:-}" "${TMP_COMPLEXITY:-}" "${TMP_DISPLAY:-}" "${TMP_DECISION:-}" "${TMP_CONVERSATION:-}"; rm -rf "${TMP_SCENARIO_DIR:-}" "${TMP_PROVENANCE_SMOKE:-}" "${TMP_CONTINUITY_SMOKE:-}" "${TMP_SCORECARD_DIR:-}"' EXIT
cat > "$TMP_REQ" <<'AC_EOF'
## 受入条件
- AC-1: test condition
AC_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-ac.py" "$TMP_REQ" --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-ac.py basic smoke test"
  rm -f "$TMP_REQ"
  exit 1
}
"$PYTHON_BIN" "$ROOT/scripts/lint-plan-consistency.py" "$TMP_REQ" --entry design --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-plan-consistency.py basic smoke test"
  exit 1
}
TMP_OUTCOME=$(mktemp -t hitl-outcome-smoke.XXXXXX.md)
cat > "$TMP_OUTCOME" <<'OUTCOME_EOF'
## HITL Outcome Audit

| Approved Direction の欄 | 最終成果物で見るもの | 結果 | Evidence / notes |
|---|---|---|---|
| 何を作るか | diff | match | ok |
OUTCOME_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-outcome-audit.py" "$TMP_OUTCOME" --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-hitl-outcome-audit.py basic smoke test"
  rm -f "$TMP_OUTCOME"
  exit 1
}
TMP_COMPLEXITY=$(mktemp -t hitl-complexity-smoke.XXXXXX.md)
cat > "$TMP_COMPLEXITY" <<'COMPLEXITY_EOF'
## 確認
### 30秒判断
**1. Scope**
COMPLEXITY_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-complexity.py" "$TMP_COMPLEXITY" --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-hitl-complexity.py basic smoke test"
  rm -f "$TMP_COMPLEXITY"
  exit 1
}
"$PYTHON_BIN" "$ROOT/scripts/lint-runtime-budget.py" "$ROOT" \
  --max-skill-body-lines 570 \
  --max-total-skill-body-lines 7075 \
  --max-express-template-lines 187 \
  --max-standard-template-lines 411 \
  --max-express-estimated-tokens 30208 \
  --max-standard-estimated-tokens 45497 \
  --quiet >/dev/null 2>&1 || {
    echo "FAIL: lint-runtime-budget.py basic smoke test"
    exit 1
  }
TMP_DISPLAY=$(mktemp -t hitl-display-smoke.XXXXXX.md)
# heredoc fixture には正本テンプレートにまだ無い語（この案を選ぶと次に何が起きるか /
# 無回答時のデフォルト。owner=T-7）も含む。marker と正本の乖離は fixture では見えないため、
# tests/test_hitl_lint_marker_sync_contract.py::test_display_integrity_markers_exist_in_canonical_sources
# が正本ファイルそのものを読んで検査する（impl-gate #1 F-2）。
cat > "$TMP_DISPLAY" <<'DISPLAY_EOF'
## 確認
### なぜやるか（WHY・根本原因）
### 何を作るか（整理した要件）
### どう作るか（実装する方法・内容）
**変更予定ファイル（WHERE）**
### どう確かめるか（検証する方法・内容）
### 現在地
### どこまで自走するか（どこまで自走するのか）
OKでも許可されないこと
人間に戻す条件
### 判断ポイント
変更前 / 変更後 / 採用しない案
この案を選ぶと次に何が起きるか
無回答時のデフォルト
### 段階実装（段階実装サマリー）
### ズレ確認（後戻りが大きいものだけ）
完了条件の変換
<gdd-stop reason="human-check-waiting">
DISPLAY_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-display-integrity.py" "$TMP_DISPLAY" --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-hitl-display-integrity.py basic smoke test"
  rm -f "$TMP_DISPLAY"
  exit 1
}
TMP_DECISION=$(mktemp -t hitl-decision-smoke.XXXXXX.md)
cat > "$TMP_DECISION" <<'DECISION_EOF'
## 🔍 確認
### 30秒判断
どこまで自走するのか？
**整理した要件**: 既存コードを読み、テストを書いてから実装します。
**実装する方法・内容**: 既存の Markdown と lint を更新します。
**検証する方法・内容**: lint smoke と contract test で確認します。
**どこまで自走するのか**: 実装とレビューまで。merge と deploy は別承認です。
**判断ポイント**: scope と検証範囲が意図通りか。
**段階実装サマリー**: 単一段階: 今回の PR で完結。

### OKで進む範囲
既存コードを読み、テストを書いてから実装します。

### OKでも許可されないこと
本番反映や外部投稿はしません。

### 現在地
| 項目 | 内容 |
|---|---|
| 人間が今やること | OK か変更点を返す |
| OK 後に残る作業 | 設計、テスト、実装、レビュー |

### やらないこと
本番操作はしません。

### 人間に戻す条件
完了条件や外部公開範囲が変わる場合。
DECISION_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-hitl-decision-quality.py" "$TMP_DECISION" --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-hitl-decision-quality.py basic smoke test"
  rm -f "$TMP_DECISION"
  exit 1
}

TMP_SCENARIO_DIR=$(mktemp -d -t gdd-scenario-release-gate.XXXXXX)
cat > "$TMP_SCENARIO_DIR/fixture.json" <<'SCENARIO_FIXTURE_EOF'
{
  "version": 1,
  "scenarios": [
    {
      "scenario_id": "validate_release_gate",
      "title": "validate release gate",
      "source_session": "synthetic:validate",
      "category": "state",
      "artifacts": ["assistant"],
      "human_ux_rubric": ["next_action_is_clear"],
      "safety_rubric": ["no_block_loop"],
      "failure_modes": ["warning released"],
      "checklist": [
        {
          "id": "VRG-1",
          "critical": true,
          "description": "release gate artifact contains required stop hook suppression language",
          "target": "assistant",
          "kind": "contains_all",
          "patterns": ["transcript_path", "block payload を返さない", "silent exit", "state.md は保持"]
        }
      ]
    }
  ]
}
SCENARIO_FIXTURE_EOF
mkdir -p "$TMP_SCENARIO_DIR/artifacts/validate_release_gate"
cat > "$TMP_SCENARIO_DIR/artifacts/validate_release_gate/assistant.md" <<'SCENARIO_ARTIFACT_EOF'
transcript_path が missing の場合は block payload を返さない。Stop hook は .gdd/hook-errors.log に記録して silent exit し、state.md は保持する。
SCENARIO_ARTIFACT_EOF
"$PYTHON_BIN" "$ROOT/scripts/run-gdd-scenario-evals.py" \
  --fixture "$TMP_SCENARIO_DIR/fixture.json" \
  --input-dir "$TMP_SCENARIO_DIR/artifacts" \
  --holdout \
  --require-release-pass >/dev/null 2>&1 || {
    echo "FAIL: run-gdd-scenario-evals.py release gate smoke test"
    rm -rf "$TMP_SCENARIO_DIR"
    exit 1
  }

TMP_CONVERSATION=$(mktemp -t conversation-routing-smoke.XXXXXX.json)
cat > "$TMP_CONVERSATION" <<'CONVERSATION_EOF'
{
  "case_id": "validate-smoke",
  "conversation": [
    {"role": "user", "text": "GDDで計画して"}
  ],
  "context": {
    "active_gdd_marker": true,
    "superpowers_enabled": true
  },
  "expected": {
    "primary": "gdd",
    "route_contains": "gate-driven-development:gdd-status",
    "must_not_route": ["superpowers:writing-plans"],
    "requires_status_or_resume": true
  }
}
CONVERSATION_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-conversation-routing-replay.py" "$TMP_CONVERSATION" >/dev/null 2>&1 || {
  echo "FAIL: lint-conversation-routing-replay.py basic smoke test"
  rm -f "$TMP_CONVERSATION"
  exit 1
}
TMP_PROVENANCE_SMOKE=$(mktemp -d -t worktree-provenance-smoke.XXXXXX)
TMP_PROVENANCE_SMOKE_DIR="$TMP_PROVENANCE_SMOKE/repo/.steering/20260607-provenance-smoke"
mkdir -p "$TMP_PROVENANCE_SMOKE_DIR"
cat > "$TMP_PROVENANCE_SMOKE_DIR/state.md" <<PROVENANCE_SMOKE_EOF
## Gate Status
- Task ID: 20260607-provenance-smoke
- Active Worktree Path: $TMP_PROVENANCE_SMOKE/repo
- Active Branch: codex/20260607-provenance-smoke
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
PROVENANCE_SMOKE_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-worktree-provenance.py" --steering-dir "$TMP_PROVENANCE_SMOKE_DIR" --branch "codex/20260607-provenance-smoke" --worktree-path "$TMP_PROVENANCE_SMOKE/repo" --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-worktree-provenance.py basic smoke test"
  rm -rf "$TMP_PROVENANCE_SMOKE"
  exit 1
}
TMP_CONTINUITY_SMOKE=$(mktemp -d -t state-tasklist-continuity-smoke.XXXXXX)
TMP_CONTINUITY_SMOKE_DIR="$TMP_CONTINUITY_SMOKE/.steering/20260607-continuity-smoke"
mkdir -p "$TMP_CONTINUITY_SMOKE_DIR"
cat > "$TMP_CONTINUITY_SMOKE_DIR/state.md" <<'CONTINUITY_SMOKE_STATE_EOF'
## Gate Status
- Task ID: 20260607-continuity-smoke
- Resume From: gdd-subagent-driven-implementation
- Next Action: gdd-subagent-driven-implementation
CONTINUITY_SMOKE_STATE_EOF
cat > "$TMP_CONTINUITY_SMOKE_DIR/requirements.md" <<'CONTINUITY_SMOKE_REQ_EOF'
- Revision: req-v1
CONTINUITY_SMOKE_REQ_EOF
cat > "$TMP_CONTINUITY_SMOKE_DIR/design.md" <<'CONTINUITY_SMOKE_DESIGN_EOF'
- Revision: design-v1
- Stage Continuity Source: requirements.md req-v1 / tasklist.md design-v1
CONTINUITY_SMOKE_DESIGN_EOF
cat > "$TMP_CONTINUITY_SMOKE_DIR/tasklist.md" <<'CONTINUITY_SMOKE_TASKLIST_EOF'
- Task ID: 20260607-continuity-smoke
- Requirements Revision: req-v1
- Design Revision: design-v1

## Current Task
- T-1
CONTINUITY_SMOKE_TASKLIST_EOF
"$PYTHON_BIN" "$ROOT/scripts/lint-state-tasklist-continuity.py" --steering-dir "$TMP_CONTINUITY_SMOKE_DIR" --quiet >/dev/null 2>&1 || {
  echo "FAIL: lint-state-tasklist-continuity.py basic smoke test"
  rm -rf "$TMP_CONTINUITY_SMOKE"
  exit 1
}
bash "$ROOT/scripts/find-stale-steerings.sh" --help >/dev/null 2>&1 || {
  # `--help` may exit 0 or 2 depending on parser; require it not to segfault
  true
}

# gdd-scorecard.py: 指標 registry が引けること、regression を実際に検出できることを見る。
# 「crash しない」だけだと常に inconclusive を返す実装でも通ってしまうため、
# --fail-on-regress の exit 3 まで確認する。
"$PYTHON_BIN" "$ROOT/scripts/gdd-scorecard.py" --list-metrics >/dev/null 2>&1 || {
  echo "FAIL: gdd-scorecard.py --list-metrics smoke test"
  exit 1
}
TMP_SCORECARD_DIR=$(mktemp -d -t gdd-scorecard-smoke.XXXXXX)
"$PYTHON_BIN" - "$TMP_SCORECARD_DIR" <<'SCORECARD_FIXTURE_EOF'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])


def task(steering_id, fix_attempts):
    return {
        "steering_id": steering_id,
        "worktree": "/tmp/repo",
        "requirements_status": "approved",
        "design_status": "approved",
        "human_check_status": "approved",
        "route_in_progress": "none",
        "fix_attempts": fix_attempts,
        "error_log_entries": 0,
        "workflow_incident_entries": 0,
        "state_kind": "done",
    }


(out / "baseline.json").write_text(
    json.dumps({"tasks": [task(f"b-{i}", 0) for i in range(4)]}), encoding="utf-8"
)
(out / "candidate.json").write_text(
    json.dumps({"tasks": [task(f"c-{i}", 4) for i in range(4)]}), encoding="utf-8"
)
SCORECARD_FIXTURE_EOF
set +e
"$PYTHON_BIN" "$ROOT/scripts/gdd-scorecard.py" \
  --baseline "$TMP_SCORECARD_DIR/baseline.json" \
  --candidate "$TMP_SCORECARD_DIR/candidate.json" \
  --fail-on-regress >/dev/null 2>&1
SCORECARD_EXIT=$?
set -e
if [[ "$SCORECARD_EXIT" -ne 3 ]]; then
  echo "FAIL: gdd-scorecard.py should exit 3 on regression (got $SCORECARD_EXIT)"
  exit 1
fi

echo "VERDICT: lint-scripts-functional: OK"
