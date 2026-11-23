#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

# Skill count budget: keep the skill count from growing by addition-only PRs.
# If this budget itself changes, the PR must carry an explicit reduction plan.
#
# 28 -> 29（2026-09-15）: `pr-review-followup`（GDD 非依存の PR レビュー
# follow-up skill）を新設した。既存 `gdd-pr-review-followup` は state.md/tasklist.md/
# steering 依存の 18 箇所を持つため、その場での consolidation（統合・削除）は
# GDD 経路の Next Action routing を壊すリスクが高いと判断し見送った。次の skill
# 棚卸し（reference: docs/audits/ 配下の既存棚卸し方針）で consolidation 候補の
# 有無を確認する。
BASELINE_SKILL_COUNT=29
MAX_SKILL_COUNT=29
if [[ "${SKILL_COUNT_BUDGET_CHANGE:-false}" == "true" && -z "${SKILL_COUNT_REDUCTION_PLAN:-}" ]]; then
  echo "MISSING: SKILL_COUNT_REDUCTION_PLAN (required when SKILL_COUNT_BUDGET_CHANGE=true)"
  exit 1
fi
if (( MAX_SKILL_COUNT != BASELINE_SKILL_COUNT )) && [[ -z "${SKILL_COUNT_REDUCTION_PLAN:-}" ]]; then
  echo "MISSING: SKILL_COUNT_REDUCTION_PLAN (required when changing MAX_SKILL_COUNT)"
  exit 1
fi
skill_count=$(find "$ROOT/skills" -mindepth 2 -maxdepth 2 -name 'SKILL.md' -type f | wc -l | tr -d ' ')
if (( skill_count > MAX_SKILL_COUNT )); then
  echo "FAIL: Skill count budget exceeded: $skill_count > $MAX_SKILL_COUNT"
  echo "New skills require existing skill consolidation or an explicit budget update with reduction plan."
  exit 1
fi
codex_manifest_skill_count=$("$PYTHON_BIN" - "$ROOT" "$skill_count" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
actual = int(sys.argv[2])
manifest = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
skills = manifest.get("skills")
if isinstance(skills, str) and skills.rstrip("/") in {"./skills", "skills"}:
    print(actual)
elif isinstance(skills, list):
    print(len(skills))
else:
    print(0)
PY
)
if (( codex_manifest_skill_count != skill_count )); then
  echo "FAIL: manifest skill count mismatch: codex_manifest_skill_count=$codex_manifest_skill_count actual=$skill_count"
  exit 1
fi
echo "VERDICT: skill-count-budget: OK"
