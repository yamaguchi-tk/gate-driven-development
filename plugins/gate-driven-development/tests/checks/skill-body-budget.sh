#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

# Skill body budget: prevent god-skill growth while allowing known oversized
# skills only when they carry a concrete reduction plan. Body lines exclude
# frontmatter so metadata changes do not affect the budget.
MAX_SKILL_BODY_LINES=350

skill_body_reduction_plan() {
  if [[ -n "${SKILL_BODY_TEST_EMPTY_PLAN_REL:-}" && "$1" == "$SKILL_BODY_TEST_EMPTY_PLAN_REL" ]]; then
    echo ""
    return 0
  fi
  # These three were distilled but did not reach <=350 body lines.
  # Their baselines below were ratcheted down to the post-distillation
  # measurements. Reason for not reaching 350: further cuts were judged to lose
  # meaning that the runtime contract depends on, so meaning preservation was
  # prioritized over the line target. The per-target rationale (which sections
  # were cut, which were kept and why) is recorded in the audit sheets under
  # docs/audits/r9-2-<target>-audit-20260729.md, section 7.
  # gdd-brainstorming reached 312 lines and was removed from this list.
  case "$1" in
    "skills/gdd-writing-skills/SKILL.md")
      echo "Move development-only guidance into docs or references and keep the runtime skill body minimal."
      ;;
    "skills/root-cause-investigation/SKILL.md")
      echo "Move duplicated superpowers fork explanation into references and keep the entry skill focused on routing and evidence steps."
      ;;
    "skills/gdd-systematic-debugging/SKILL.md")
      echo "Move detailed debug triage material into references and keep the skill body focused on route decisions."
      ;;
    *)
      return 1
      ;;
  esac
}

skill_body_baseline_lines() {
  case "$1" in
    # Baselines ratcheted down to post-distillation measurements
    # (see the note above skill_body_reduction_plan for why <=350 was not
    # reached). gdd-brainstorming (352 -> 312) cleared the cap and was removed.
    "skills/gdd-writing-skills/SKILL.md")
      echo "423"
      ;;
    "skills/root-cause-investigation/SKILL.md")
      echo "541"
      ;;
    "skills/gdd-systematic-debugging/SKILL.md")
      echo "463"
      ;;
    *)
      return 1
      ;;
  esac
}

skill_body_line_count() {
  "$PYTHON_BIN" - "$1" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines()
start = 0
if lines[:1] == ["---"]:
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            start = index + 1
            break
print(len(lines[start:]))
PY
}

check_skill_body_budget() {
  local scan_root="$1"
  local failures=0

  while IFS= read -r skill; do
    local rel body_lines plan baseline_lines
    rel="${skill#"$scan_root"/}"
    body_lines="$(skill_body_line_count "$skill")"
    if (( body_lines <= MAX_SKILL_BODY_LINES )); then
      continue
    fi
    if ! plan="$(skill_body_reduction_plan "$rel")"; then
      echo "SKILL_BODY_BUDGET_EXCEEDED: ${rel} has ${body_lines} body lines > ${MAX_SKILL_BODY_LINES}"
      echo "Add a reduction plan or split the skill before merging."
      failures=1
      continue
    fi
    if [[ -z "${plan//[[:space:]]/}" ]]; then
      echo "SKILL_BODY_REDUCTION_PLAN_MISSING: ${rel}"
      failures=1
      continue
    fi
    if ! baseline_lines="$(skill_body_baseline_lines "$rel")"; then
      echo "SKILL_BODY_ALLOWLIST_BASELINE_MISSING: ${rel}"
      failures=1
      continue
    fi
    if (( body_lines > baseline_lines )); then
      echo "SKILL_BODY_ALLOWLIST_BASELINE_EXCEEDED: ${rel} has ${body_lines} body lines > baseline ${baseline_lines}"
      echo "Allowlisted over-budget skills must shrink or stay at their recorded baseline."
      failures=1
    fi
  done < <(find "$scan_root/skills" -mindepth 2 -maxdepth 2 -name 'SKILL.md' -type f | sort)

  return "$failures"
}

check_skill_body_budget_self_test() {
  local tmp_root over_budget allowlisted empty_plan empty_plan_output baseline_output
  tmp_root="$(mktemp -d)"
  mkdir -p "$tmp_root/skills/oversized" "$tmp_root/skills/gdd-writing-skills" "$tmp_root/skills/empty-plan-fixture"
  over_budget="$tmp_root/skills/oversized/SKILL.md"
  allowlisted="$tmp_root/skills/gdd-writing-skills/SKILL.md"
  empty_plan="$tmp_root/skills/empty-plan-fixture/SKILL.md"

  write_skill_body_fixture() {
    local path name body_lines
    path="$1"
    name="$2"
    body_lines="${3:-351}"
    {
      printf '%s\n' "---" "name: ${name}" "description: fixture" "---"
      for _ in $(seq 1 "$body_lines"); do
        printf '%s\n' "body"
      done
    } > "$path"
  }

  write_skill_body_fixture "$over_budget" "oversized"
  if check_skill_body_budget "$tmp_root" >/dev/null 2>&1; then
    echo "FAIL: skill body budget self-test should reject unallowlisted oversized skill"
    rm -rf "$tmp_root"
    exit 1
  fi

  write_skill_body_fixture "$empty_plan" "empty-plan-fixture"
  rm -f "$over_budget"
  if empty_plan_output="$(SKILL_BODY_TEST_EMPTY_PLAN_REL="skills/empty-plan-fixture/SKILL.md" check_skill_body_budget "$tmp_root" 2>&1)"; then
    echo "FAIL: skill body budget self-test should reject allowlisted oversized skill without reduction plan"
    rm -rf "$tmp_root"
    exit 1
  fi
  if [[ "$empty_plan_output" != *"SKILL_BODY_REDUCTION_PLAN_MISSING"* ]]; then
    echo "FAIL: skill body budget self-test should exercise missing reduction plan branch"
    rm -rf "$tmp_root"
    exit 1
  fi

  write_skill_body_fixture "$allowlisted" "gdd-writing-skills" 591
  rm -f "$empty_plan"
  if baseline_output="$(check_skill_body_budget "$tmp_root" 2>&1)"; then
    echo "FAIL: skill body budget self-test should reject allowlisted skill above baseline"
    rm -rf "$tmp_root"
    exit 1
  fi
  if [[ "$baseline_output" != *"SKILL_BODY_ALLOWLIST_BASELINE_EXCEEDED"* ]]; then
    echo "FAIL: skill body budget self-test should exercise allowlist baseline branch"
    rm -rf "$tmp_root"
    exit 1
  fi

  write_skill_body_fixture "$allowlisted" "gdd-writing-skills"
  if ! check_skill_body_budget "$tmp_root" >/dev/null 2>&1; then
    echo "FAIL: skill body budget self-test should allow oversized skill with reduction plan"
    rm -rf "$tmp_root"
    exit 1
  fi
  rm -rf "$tmp_root"
}

echo "BLOCK: skill-body-budget"
check_skill_body_budget "$ROOT"
check_skill_body_budget_self_test

required_files=(
  ".claude-plugin/plugin.json"
  ".cursor-plugin/plugin.json"
  ".codex-plugin/plugin.json"
  "README.md"
  "CHANGELOG.md"
  "docs/CI_GUARDS.md"
  "docs/TEAM_ROLLOUT.md"
  "commands/gdd-dev.md"
  "hooks/hooks.json"
  "hooks/scripts/run-gdd-stop-hook.sh"
  "hooks/scripts/run-steering-write-hook.sh"
  "hooks/scripts/validate-steering-write.py"
  "references/faq.md"
  "references/onboarding.md"
  "references/reviewer-selection.md"
  "references/source-of-truth-map.md"
  "references/contract-overview.md"
  "references/self-contained-contract.md"
  "references/human-check-template.md"
  "references/confirmed-text.md"
  "docs/references-archive/hitl-offline-judge.md"
  "references/abandon-and-pause.md"
  "references/autonomy.md"
  "references/post-merge-qa.md"
  "references/adr-vs-design.md"
  "docs/references-archive/benchmark-scenarios.md"
  "references/bounce-log-schema.md"
  "references/debug-triage.md"
  "references/dialectic-review.md"
  "references/gate-status-schema.md"
  "references/rationalization-root-causes.md"
  "references/skill-responsibility-matrix.md"
  "references/subagent-dispatch.md"
  "references/superpowers-overlap.md"
  "references/testing-anti-patterns.md"
  "references/verification-before-completion.md"
  "docs/references-archive/worked-examples.md"
  "references/state-machine.md"
  "references/state-machine-overview.md"
  "references/common-guardrails.md"
  "references/phase-progression.md"
  "references/context-budget.md"
  "references/config-defaults.md"
  "references/output-format.md"
  "references/inline-review-checklists.md"
  "references/independent-review.md"
  "references/task-breakdown-steps.md"
  "references/task-sizing.md"
  "references/entry-intent.md"
  "references/brainstorming-steps.md"
  "references/requirements-template.md"
  "references/requirements-template-express.md"
  "references/human-check-template-compact.md"
  "references/rollback-patterns.md"
  "references/requirements-gating-steps.md"
  "references/cursor.md"
  "references/codex.md"
  "references/operation-levels.md"
  "references/gdd-self-development.md"
  "references/workspace-policy.md"
  "references/reviewer-common.md"
  "references/finding-dispositions.md"
  "references/cursor-guide.md"
  "docs/references-archive/team-onboarding.md"
  "docs/references-archive/gdd-writing-skills-templates.md"
  "references/cross-task-learning.md"
  "references/state-field-tiers.md"
  "references/stop-hook-structured-markers.md"
  "references/parallel-failure-investigation.md"
  "references/fixed-models.md"
  "references/phase-gate-prechecks.md"
  "references/state-schema.json"
  "references/e2e-verification-catalog.md"
  "references/gate-checklists.md"
  "references/reviewer-lineage.md"
  "references/uat-checklist.md"
  "references/post-completion-learning.md"
  "docs/references-archive/autonomous-model-workers.md"
  "references/ac-trace-ledger.md"
  "references/gdd-scenario-evals.md"
  "references/workflow-incident-review.md"
  "references/prompt-contract-map.md"
  "docs/references-archive/infra-accretion-prevention-decision.md"
  "references/post-completion-pr-flow.md"
  "references/japanese-writing-norm.md"
  "references/nfr-viewpoints.md"
  "references/self-review-lanes.md"
  "evals/gdd-scenario-fixtures.json"
  "scripts/lint-approved-direction.py"
  "scripts/gdd-codebase-health.py"
  "scripts/lint-ac.py"
  "scripts/lint-hitl-display-integrity.py"
  "scripts/lint-hitl-complexity.py"
  "scripts/lint-hitl-stage-plan.py"
  "scripts/lint-hitl-outcome-audit.py"
  "scripts/lint-hitl-decision-quality.py"
  "scripts/lint-runtime-budget.py"
  "scripts/lint-clarification-brief.py"
  "scripts/lint-conversation-routing-replay.py"
  "scripts/lint-human-check-language.py"
  "scripts/lint-resume-integrity.py"
  "scripts/lint-worktree-provenance.py"
  "scripts/lint-state-tasklist-continuity.py"
  "scripts/lint-pr-review-followup-state.py"
  "scripts/lint-reviewer-lineage.py"
  "scripts/find-stale-steerings.sh"
  "scripts/run-gdd-scenario-evals.py"
  "evals/evals.json"
  "scripts/grade_evals.py"
  "scripts/external-verifier-smoke.sh"
  "scripts/install-cursor-links.sh"
  "scripts/setup-gdd-loop.sh"
  "scripts/resolve-gdd-model.py"
  "scripts/run-gdd-worker.py"
  "scripts/run-with-plugin.sh"
  "scripts/uninstall-cursor-links.sh"
  "skills/gdd-pre-workflow-brainstorming/SKILL.md"
  "skills/gdd-dev/SKILL.md"
  "skills/gdd-brainstorming/SKILL.md"
  "skills/gdd-status/SKILL.md"
  "skills/gdd-metrics/SKILL.md"
  "skills/gdd-next-plan/SKILL.md"
  "skills/gdd-goal-driven-execution/SKILL.md"
  "skills/gdd-model-routing/SKILL.md"
  "skills/gdd-using-skills/SKILL.md"
  "skills/gdd-writing-skills/SKILL.md"
  "skills/gdd-requirements-gating/SKILL.md"
  "skills/gdd-requirements-amendment/SKILL.md"
  "skills/gdd-design-gating/SKILL.md"
  "skills/gdd-task-breakdown/SKILL.md"
  "skills/gdd-using-git-worktrees/SKILL.md"
  "skills/gdd-test-driven-development/SKILL.md"
  "skills/gdd-subagent-driven-implementation/SKILL.md"
  "skills/gdd-implementation-gating/SKILL.md"
  "skills/gdd-pr-review/SKILL.md"
  "skills/gdd-pr-review-followup/SKILL.md"
  "skills/pr-review-followup/SKILL.md"
  "skills/gdd-ac-verification/SKILL.md"
  "skills/gdd-requesting-code-review/SKILL.md"
  "skills/gdd-receiving-code-review/SKILL.md"
  "skills/gdd-test-failure-debug-pack/SKILL.md"
  "skills/gdd-systematic-debugging/SKILL.md"
  "skills/gdd-completion-check/SKILL.md"
  "skills/gdd-refactor-planning/SKILL.md"
  "skills/root-cause-investigation/SKILL.md"
  "agents/gdd-planning-reviewer.md"
  "agents/gdd-implementation-reviewer.md"
  "agents/gdd-security-reviewer.md"
  "agents/gdd-completion-reviewer.md"
  "agents/gdd-code-simplifier.md"
)

for rel in "${required_files[@]}"; do
  if [[ ! -f "${ROOT}/${rel}" ]]; then
    echo "MISSING: ${rel}"
    exit 1
  fi
done

for rel in "$ROOT"/skills/*/SKILL.md "$ROOT"/references/*; do
  [[ -f "$rel" ]] || continue
  rel="${rel#"$ROOT"/}"
  found=false
  for required in "${required_files[@]}"; do
    if [[ "$required" == "$rel" ]]; then
      found=true
      break
    fi
  done
  if [[ "$found" == "false" ]]; then
    echo "REQUIRED_FILES_MISSING_ASSET: ${rel}"
    exit 1
  fi
done

# Source Budget backstop: this prevents references/ source sprawl, but
# references line budget is not the runtime budget. Runtime Budget is enforced
# by compact HITL / Skill Runtime Read Limits contracts.
# This limit only moves downward; raising it requires removing or
# consolidating equivalent parent text first（subagent-dispatch.md の
# Template 6 本の `## 読む対象` 欄と Typed Agent Resolution 節の追加分 59 行
# （11939 → 11998。旧上限の余裕 19 行を使い、上限は 40 行の引き上げ）のみ、
# ユーザー承認済みで 11958 → 11998。main 取り込みで main 側が 7 行増えた分は
# Template 内の空行を詰めて吸収し、上限は据え置き）。references/autonomy.md の追加分は
# ユーザー承認のうえ上げた（経緯は CHANGELOG）。references/post-merge-qa.md の追加分も
# ユーザー承認のうえ上げた（2026-10-01）。human-check-template.md § 事前回答 の追加分は、
# 重複の統合の後に残った 4 行だけ上げた（2026-10-02。PR でユーザーの承認を求める）。references/confirmed-text.md
# （確定文面の正本。ユーザーの依頼で新設）の追加分も上げた（2026-10-13。PR でユーザーの承認を求める）。task-breakdown-steps.md
# § Judgment Change（impl-gating の review を外す線の正本）の 6 行も上げた（2026-10-22。PR でユーザーの承認を求める）。Ratchet history lives in
# CHANGELOG.md, not here (avoid stale duplicated numbers).
reference_lines=$(find "$ROOT/references" -name '*.md' -type f -print0 | xargs -0 wc -l | tail -n 1 | awk '{print $1}')
if [[ "${reference_lines}" -gt 12155 ]]; then
  echo "REFERENCES_LINE_BUDGET_EXCEEDED: ${reference_lines} > 12155"
  echo "Additions to references/ must remove or consolidate equivalent parent text."
  exit 1
fi

# Runtime Budget backstop: HITL is checked separately by lint-hitl-complexity.
# This check freezes the runtime-facing SKILL body line budget, Runtime template
# budget, express runtime profile, standard runtime profile, and estimated
# runtime tokens so source-only docs can grow without making every workflow
# heavier.
# Limits below are the values measured on the integration target (origin/main
# tip) after the ratchets below, applied in sequence:
# 1) HITL 承認ポイントの固定フィールド受理文法:
#    max-standard-estimated-tokens 45381->45405. 承認ポイントごとの 既定範囲 /
#    狭める根拠 / 判断に影響する前提 固定フィールドを human-check-template-compact.md
#    に追加したため。等価削減を2巡試して888->945トークンまで圧縮した残りをユーザー
#    承認で吸収。他の値は不変。
# 2) 2026-09-15: new skill `pr-review-followup` added 105 body
#    lines. The "6982 -> 7068" step looks like a +86 delta, not +105, because
#    the pre-existing 6982 constant was itself already 19 lines stale vs. the
#    true origin/main total (6963) before this ratchet — a pre-existing,
#    unrelated drift verified via a clean origin/main clone, not something
#    this change introduced. 7068 = true pre-change total (6963) + 105, and
#    matches the measured post-change total exactly. This skill is not
#    covered by the express/standard runtime profiles, so express/standard
#    estimated-token budgets are unaffected by it — only the sum-of-all-skills
#    backstop moves.
# 3) 2026-10-02: max-standard-estimated-tokens 45405->45430. 事前回答の入口
#    （gdd-using-skills の振り分け、gdd-requirements-gating の途中指示）に § 事前回答
#    への指し先を足し、commands/gdd-dev.md #9 を事前回答の行を先に見る順序に書き直したため。足した文を詰めた残りの 25。
#    PR でユーザーの承認を求める。
# 4) 2026-10-02: max-total-skill-body-lines 7068->7073. gdd-pr-review の 3g（配線レビュー）の
#    指摘のまとめ方を、1 行に詰めた文から箇条 5 つに分けたため（1 文に詰めて読み違いが出ていた）。
#    ユーザー承認済み。
# 5) 2026-10-12: max-standard-estimated-tokens 45430->45443、max-express-estimated-tokens
#    30083->30088. 簡易版 human check テンプレートの `判断軸:` に既定の比較の軸の名前を書いたため
#    （増分はどちらも 13。元の余裕は standard 1・express 9）。
#    ユーザー承認済み。
# 6) 2026-10-12: max-standard-estimated-tokens 45443->45454、max-express-estimated-tokens
#    30088->30099. 同じ `判断軸:` の軸の名前を相談役の欄とそろえ（信頼境界・fail-closed）、
#    要件の充足度と信頼境界を書く条件を言い切ったため（増分はどちらも 11）。
#    ユーザー承認済み。
# 7) 2026-10-12: max-standard-estimated-tokens 45454->45472、max-express-estimated-tokens
#    30099->30117. commands/gdd-dev.md #10 に、human check の本人の回答を request.md に
#    足す一文を入れたため（増分はどちらも 19。元の余裕はどちらも 1）。ユーザー承認済み。
# 8) 2026-10-13: max-standard-estimated-tokens 45472->45480、max-express-estimated-tokens
#    30117->30125. skills/gdd-using-skills/SKILL.md の振り分けの前段に、本人の入力を
#    request.md にも足す一句を入れたため（増分はどちらも 8。元の余裕はどちらも 0）。ユーザー承認済み。
# 9) 2026-10-22: max-total-skill-body-lines 7073->7075、max-standard-estimated-tokens 45480->45497.
#    impl-gating の Step 1e（判定の線で review を外す）と、task-breakdown の task の欄
#    `Judgment Change:` とその正本への指し先を足したため（元の余裕は行 0・token 9）。
#    PR でユーザーの承認を求める。
# 10) 2026-10-28: max-standard-estimated-tokens 45497->45552. human check の承認の後に
#    design-gating を飛ばす経路（STEP 2 の route）と、design.md の skeleton に 5a・5b・5d と
#    External Guardrails Inventory を足したため（元の余裕は 0）。PR でユーザーの承認を求める。
# 11) 2026-11-02: max-standard-estimated-tokens 45552->45497. 10) で足した design-gating を
#    飛ばす経路と skeleton の節を外したため（10) の前の値に戻す）。
# 12) 2026-11-10: max-express-estimated-tokens 30125->30141. 簡易版 human check テンプレートの
#    判断ポイントに `依頼との差:` の欄を足し、「OK で承認」が差の無い点だけを承認すると書き、
#    再提示を全点にしたため（増分 16。元の余裕は 0）。PR でユーザーの承認を求める。
# 13) 2026-11-13: max-express-estimated-tokens 30141->30208. 選べる案が実質無い human check で
#    止まり直さないために、gdd-dev.md #10 STEP 1 の「明確な承認」に表示した案の名指しを入れ、
#    全点の再提示を書く 2 つの SKILL に、名指しは変更要求ではないと 1 文ずつ足したため
#    （増分 67。元の余裕は 0）。PR でユーザーの承認を求める。
# They only move downward otherwise. Ratchet history lives in CHANGELOG.md,
# not here (avoid stale duplicated numbers). max-skill-body-lines 570 is the
# per-skill cap and was out of scope for these ratchets (unchanged).
"$PYTHON_BIN" "$ROOT/scripts/lint-runtime-budget.py" "$ROOT" \
  --max-skill-body-lines 570 \
  --max-total-skill-body-lines 7075 \
  --max-express-template-lines 187 \
  --max-standard-template-lines 411 \
  --max-express-estimated-tokens 30208 \
  --max-standard-estimated-tokens 45497 \
  --quiet

echo "VERDICT: skill-body-budget: OK"
