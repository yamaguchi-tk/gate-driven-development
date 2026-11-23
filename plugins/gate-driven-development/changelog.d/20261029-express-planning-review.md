---
type: breaking
---

#### Summary

- `quick (express)` も requirements-gating を通る。brainstorming の後、同じターンで `gdd-planning-reviewer`（requirements の観点）と、選定条件に当たる `gdd-security-reviewer` を起動してから human check で止まる。design の観点の組は起動しない。Round 上限・時間上限・再入・`reviews.md` の記録は standard と同じ（`references/requirements-gating-steps.md` § Express）
- express でも、着手の時点で依頼と既存コードの突き合わせ（`gdd-request-code-crosscheck`）を 1 回回す。`request.md`・`request-crosscheck.md` ができ、human check にリスクの段の行と `原文:` が出る
- planning reviewer は、express の計画に design phase の実装可能性の机上追跡（名指しした既存のシンボルの実在）を当てる。express の条件（`references/task-sizing.md` の 4 条件と、express テンプレートの Promotion Rules）を外れた計画を blocking にし、処置に昇格を挙げる。昇格の後の requirements-gating は再入として数える
- express の human check で「一部変更」が AC・範囲・Files を変えたら、再提示の前に requirements-gating を再入として回す
- express の Auto-Confirm モード（`/gdd-dev --auto-confirm` で human check を省く経路）を撤去した。express も human check を必ず 1 回通る
- express の requirements.md のテンプレートは、`## Acceptance Criteria` を `## 受入条件` にし、AC に `根拠:`・`計測:`、承認ポイントに `根拠:` の欄を足した。reviewer の起動の前の `lint-plan-consistency.py --entry requirements` が express にも当たる。Promotion Rules の AC の線は、task-sizing の昇格条件にそろえて 4 件以上にした
- build に入る前の条件（`references/state-schema.json` § `prechecks.build_phase`）は、express でも Requirements・Design・Human Check の 3 つとも approved になった。express の Design Review Status は、requirements-gating の通過のときに同じ evidence で approved になる

#### Breaking Contract Changes

- `/gdd-dev --auto-confirm` を撤去した。`references/task-sizing.md` § Express Auto-Confirm モード、`references/state-schema.json` の `auto_confirm`、`Human Check Status` の evidence の `auto-confirm:<condition-id>` が無くなった
- express の gate の順序が変わった（brainstorming → requirements-gating → human check）

#### Changed

- express の経路（`references/task-sizing.md`、`references/phase-progression.md`、`references/state-machine.md`、`references/state-field-tiers.md`、`references/phase-gate-prechecks.md`、`references/state-schema.json`、`references/gate-status-schema.md`、`commands/gdd-dev.md`、`README.md`）
- requirements-gating の手順（`references/requirements-gating-steps.md` § Express・§ 承認後の即時継続、`skills/gdd-requirements-gating/SKILL.md`）
- brainstorming の手順（`skills/gdd-brainstorming/SKILL.md`、`references/brainstorming-steps.md`）
- reviewer と突き合わせ（`agents/gdd-planning-reviewer.md`、`agents/gdd-request-code-crosscheck.md`）
- human check と入力の 1 枚（`references/human-check-template.md`、`references/human-check-template-compact.md`、`references/subagent-dispatch.md`）
- express のテンプレート（`references/requirements-template-express.md`、`references/requirements-template.md`）
- 説明（`references/output-format.md`、`references/onboarding.md`、`references/faq.md`、`skills/gdd-systematic-debugging/SKILL.md`）

#### Affected Files

- `references/requirements-gating-steps.md`
- `references/task-sizing.md`
- `references/state-machine.md`
- `references/state-schema.json`
- `references/gate-status-schema.md`
- `references/requirements-template-express.md`
- `agents/gdd-planning-reviewer.md`
- `agents/gdd-request-code-crosscheck.md`
- `skills/gdd-brainstorming/SKILL.md`
- `skills/gdd-requirements-gating/SKILL.md`
- `commands/gdd-dev.md`
- `README.md`

#### User Action Required

- `/gdd-dev --auto-confirm` は使えなくなった。express も human check で 1 回承認する
- 進行中の express の steering: human-check-waiting で `Requirements Review Status` / `Design Review Status` の行が無いものは、build の前の確認で requirements-gating に戻される。その場合は requirements-gating を 1 回通してから human check に進む
- express のタスクでも planning reviewer（最大 30 分）と突き合わせが回るので、express の human check までの時間が延びる

#### Validation / Eval Impact

- `tests/test_express_planning_review.py`（express のテンプレートが lint を通る、express でも requirements-gating の承認が無ければ build に進まない）
- `tests/test_p0_p1_operational_hardening_contract.py`（`state-schema.json` に `auto_confirm` が無い。express の build の前の条件）
- `evals/gdd-scenario-fixtures.json` の README の所要時間のケースから auto-confirm の語を外した
- `bash tests/validate-plugin.sh`
