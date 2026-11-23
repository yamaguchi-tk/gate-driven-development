---
type: patch
---

#### Summary

- `gdd-subagent-driven-implementation` の worker には、§ 直し方 5 の材料として `worklog.md` の § Error Log の行をすべて渡す。同じ部品の修正が続いたかは worker が判定し、行が無ければ `材料なし` と返す
- 差し戻しの finding を、`tasklist.md` の対象の task の `Fix Findings:` の行（今回の差し戻しの finding。前の行は残さない）に書く。completion-check の差し戻しでは `gdd-completion-check` が、再オープン・作成した task のすべて（`Pending Tasks` に置いたものも含む）に書く。それ以外の差し戻しでは `gdd-systematic-debugging` が、route によらずに書く。行は task が承認されて `Completed Tasks` に移るときに消す
- `gdd-test-driven-development` Step 1 は、`Fix Findings:` の行がある task を指摘を直すために戻った task とし、その finding を再現するテストを足す。RED Evidence の節が無い task では Step 2〜4 の RED の対象に含め、今の worktree で再現しない finding は RED に数えず、RED Evidence の節に `再現せず` と書く
- `gdd-test-driven-development` の AC ID の例外に、Step 1 で `Covers AC:` の無い remediation task の節に追記するエントリを足した
- `references/rollback-patterns.md` § implementation_fix_only で、2. で修正の分岐が変わったら 1. に戻ってテストを足す。修正の前から通るテストは RED に数えない
- `gdd-subagent-driven-implementation` の Codex Subagent Delegation Permission の節を、Subagent Prompt Contract の箇条の後に移した

#### Changed

- `skills/gdd-subagent-driven-implementation/SKILL.md`（Subagent Prompt Contract の Constraints と Expected output、Codex Subagent Delegation Permission の位置）
- `skills/gdd-test-driven-development/SKILL.md`（Step 1、AC ID Binding の例外）
- `references/subagent-dispatch.md`（TDD Template の読むファイル、Implementation-Gating Template の State Update Contract 1）
- `references/self-review-lanes.md`（§ 直し方 2、参照元の行と理由の文）
- `references/rollback-patterns.md`（§ implementation_fix_only）
- `skills/gdd-systematic-debugging/SKILL.md`（§ Failure Routing の復帰と `Fix Findings:` の書き込み）
- `skills/gdd-completion-check/SKILL.md`（手順 17 の `Fix Findings:` の書き込み）
- `skills/gdd-implementation-gating/SKILL.md`（Step 11 で `Fix Findings:` の行を消す）
- `references/state-field-tiers.md`（Tier 3 の `Fix Findings`）

#### Affected Files

- `skills/gdd-subagent-driven-implementation/SKILL.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `references/subagent-dispatch.md`
- `references/self-review-lanes.md`
- `references/rollback-patterns.md`
- `skills/gdd-systematic-debugging/SKILL.md`
- `skills/gdd-completion-check/SKILL.md`
- `skills/gdd-implementation-gating/SKILL.md`
- `references/state-field-tiers.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
