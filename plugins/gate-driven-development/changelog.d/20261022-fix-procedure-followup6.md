---
type: patch
---

#### Summary

- `gdd-systematic-debugging` が `Fix Findings:` を書く task が `Completed Tasks` にしか無いとき（Pre-PR loop・PR 後のレビューなど、全 task が完了した後の差し戻し）は、同じ steering で直す route なら、書く前にその task を再オープンする。置き方は completion-check の差し戻しと同じで、元の task 順で最初の 1 件を `Current Task`、残りを `Pending Tasks` に置く。対象の task は、finding の `file:line` のファイルを `Files:` に持つ task（AC を名指す finding はその AC の primary owner）で、決められない finding には remediation task を作り、再オープンした task の後に置く。Hotfix Lane に回す route では、元の steering を再オープンせず、`Fix Findings:` も書かない。再オープンした task の `Execution Status:` は `in_progress` に戻す（completion-check の差し戻しの再オープンも同じ）
- planning 差し戻し（PR 後のレビューの `design_detail_only` など）で task-breakdown が tasklist を作り直すときも、task の `Fix Findings:` の行を消さず、作り直した task に写す。写し先は再オープンと同じ規則で決め、決められない行は remediation task に書く。これで、PR 後のレビューから TDD に戻す経路（直接の TDD route と、作り直しを通る route）で、TDD Step 1 が `Fix Findings:` を読む
- remediation task（completion-check が作るものも含む）に書く欄を決めた。`Files:`・`Planned RED / E2E:`（`Fix Findings:` の各行を再現するテスト）・`Planned Verification:`・`Steps`・`Stop Conditions:`・`Return Route:` を書き、`Covers AC:` は finding が AC を名指すときだけ書く
- `gdd-test-driven-development` は、`Fix Findings:` の行がある remediation task を、`Covers AC:` が無くても task-breakdown に戻さない。その task の RED Evidence は、AC ID Binding の例外として `AC:` を推定で書かない
- `gdd-pr-review-followup` の Fix で TDD に戻すときは、`gdd-systematic-debugging` を通して `Fix Findings:` を書く
- Pre-PR loop の `Completed Tasks` を保持する規定（revert しない）に、`Fix Findings:` を書くための再オープンは revert に数えないと添えた

#### Changed

- `skills/gdd-systematic-debugging/SKILL.md`（§ Failure Routing の前置き）
- `references/state-machine.md`（§ tasklist.md の canonical state の再オープンと remediation task の欄）
- `references/state-field-tiers.md`（Tier 3 の `Fix Findings`）
- `skills/gdd-pr-review-followup/SKILL.md`（Fix の ①直す）
- `skills/gdd-test-driven-development/SKILL.md`（AC ID Binding の例外、Step 1・2）
- `references/phase-progression.md`（§ Post-PR / Post-Merge Contract の 4）
- `references/task-breakdown-steps.md`（作り直しで引き継ぐ行）
- `skills/gdd-completion-check/SKILL.md`（手順 16 の remediation task）

#### Affected Files

- `skills/gdd-systematic-debugging/SKILL.md`
- `references/state-machine.md`
- `references/state-field-tiers.md`
- `skills/gdd-pr-review-followup/SKILL.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `references/phase-progression.md`
- `references/task-breakdown-steps.md`
- `skills/gdd-completion-check/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
