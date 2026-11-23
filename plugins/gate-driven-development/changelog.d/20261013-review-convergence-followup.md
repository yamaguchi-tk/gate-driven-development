---
type: minor
---

#### Summary

`references/independent-review.md` の (3-f)（後で実装する guard・contract test の Decision への finding）を、ほかの規定とかみ合うように直した。

- (3-f) の severity と category の基準は 1 回目のレビューから当て、§ 常時 High と § finding category より先に当たる（正本は (3-f)）。Decision に当たるか、どちらに倒れるかを判定できなければ (3-f) を当てない。`gdd-planning-reviewer`・`gdd-security-reviewer` の category も (3-f) に従う
- 取り直しは gate の Round 上限・`Pre-PR Fix Attempts` とは別に 1 PR あたり 1 回と数え、始めるときに `state.md` § Gate Status に `Decision Retake:` の行を書く。前回の high・blocking がすべて Decision への finding（`decision-only`）なら、(3-a) の 1 つ目の条件に当たっても範囲を差分にする。`mixed`・行を読めない・確かめられないとき、(3-a) のほかの全差分の条件に当たるときは全差分にする。行は `state-field-tiers.md` の Tier 3 に足した
- 取り直しでも high または blocking が残れば人に戻す。PR 作成前は `references/post-completion-pr-flow.md` の昇格処理の順序 3、PR 作成後は `gdd-pr-review-followup` の方式転換で戻す。昇格処理の見出しと順序 2・3 の条件にこの経路を入れ、`state-machine.md` の例外一覧と `gdd-completion-check` にも足し、`rollback-patterns.md`・`autonomy.md`・`self-review-lanes.md`・`pr-review-followup`・`gdd-pr-review-followup` からもこの上限を指した。`commands/gdd-dev.md` #10 STEP 1 では、この上限から着いた 4 択への 4 つ目か案名の無い返答も STEP 2 に通さない
- 経路 P 型と、承認済みの Decision の列挙の形への finding のうち、medium 以下で実害クラスでないものは、`gdd-implementation-gating` の Round の計上では Round を消費せず advisory として記録する（high・実害クラスは差し戻す。design gate では直す）。後続の test の要件として書かれた修正案は Issue に写して申し送りの正本とし、`Medium Disposition` を書くときは `recorded` にその Issue 参照を書く
- `gdd-security-reviewer` の Decision の観点を、Design phase だけでなく全 phase（companion lane を含む）に当てる位置へ移した。2 つの reviewer では、列挙の形そのものは Medium、文字どおりに読むと違反を許すなら high とした
- 規範文を逐語で固定していた `tests/test_diff_scope_out_of_range_blocking_contract.py` を外した

#### Affected Files

- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-security-reviewer.md`
- `plugins/gate-driven-development/tests/test_diff_scope_out_of_range_blocking_contract.py`（削除）
- `plugins/gate-driven-development/changelog.d/20261013-review-convergence-rules.md`（`amends:`。今の (3-f) の規則に合わせ、削除したテストの記述を外した）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
