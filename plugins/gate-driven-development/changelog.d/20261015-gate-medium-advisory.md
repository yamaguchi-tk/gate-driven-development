---
type: breaking
---

#### Summary

phase gate は、blocking でない medium（実害クラスでない product・test-power など）では差し戻さないようにした。今までの implementation-gating は、blocking が 0 件でも「Round 消費 category」の medium が 1 件あれば `changes_requested` にしていて、実害の無い指摘で Round が増えていた。

- implementation-gating と completion-check は、reviewer の finding で差し戻すのを High と実害クラス（`reviewer-common.md` の `is_blocking`）が残るときだけにした。Task Size（quick (express) を含む）によらず同じ
- それ以外の medium・low は、state.md の `## Advisory Findings (Impl-Gate)` に記録して approved にし、PR 本文に全件を書く。その loop では直さない
- Stage A（AC を満たしていない・承認範囲を超えている・Tech Stack が違う・Human Recheck Boundary に触れている）と Spec Drift は、severity・category によらず差し戻す
- design-gating は、requirements-gating と同じ述語（high・medium のうち、AC の意味・スコープ・承認ポイント・安全境界に影響するものだけ blocking）で差し戻す。ほかは advisory として記録し、最後の Round の後に反映する
- completion-check の testing gap は、AC の Verification の evidence がその AC を示せていないものに限り、category によらず evidence の不足として blocking にする。ほかのテストの指摘は category のとおりに扱う。completion-check で差し戻さない medium・low も、同じ `## Advisory Findings (Impl-Gate)` に記録し、PR 本文に全件を書く
- remediation（systematic-debugging・subagent-driven-implementation）が直すのは、差し戻しの理由になった finding だけにした。Advisory Findings に記録したものは、その loop では直さない
- reviewer の finding で category が付いていない、または 9 値のどれでもないものは、medium 以上なら実害クラスと同じく差し戻し、blocking に数える（今までも product 相当として差し戻していたが、blocking には数えていなかった。9 値の外の値は扱いが決まっていなかった）。inline review の checklist の走査と gate 自身の検査が出す finding にも同じ既定を当て、gate 自身の検査（E2E 一貫性の未実施、scope 外の変更、dead code、空値 return の意図確認）の Medium には、実害クラスでない category を付ける

#### Breaking Contract Changes

- `references/reviewer-common.md` § finding category の表から「Round 消費」の列と `consumes_round` の述語、別名「Round 非消費 category」を外した。`Gate Rounds` は、Round 消費 category の finding の有無によらず、`changes_requested` のたびに +1 する
- state.md の見出し `## Advisory Findings (Express Impl-Gate)` を `## Advisory Findings (Impl-Gate)` に改め、全 Task Size で書く
- reviewer の出力の「approved」の条件を「medium・high が無い」から「High と実害クラスの finding が無い」に変えた
- `references/state-machine.md` § Remediation Loop Safety の「直近 2 Round の差し戻しの finding がすべて Round 非消費なら、Round の上限を待たず approved」の規則を消した
- Stage A と Spec Drift は、今までは Round 非消費 category の finding なら advisory にしていた。今回から category によらず差し戻す

#### Affected Files

- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/evals/evals.json`

#### User Action Required

- 進行中の task の state.md に `## Advisory Findings (Express Impl-Gate)` の節があれば、見出しを `## Advisory Findings (Impl-Gate)` に直す（読む hook は無い。PR 本文への搬送は旧見出しの節も読むので、直さなくても記録は落ちない）

#### Validation / Eval Impact

- `evals/evals.json` の id 27（実害クラスでない medium は Advisory Findings に記録して approved。`waived` は non-applicable の reviewer だけ）、id 28（testing gap を AC の検証の不足に限る）、id 30（実害クラスの medium で差し戻す）を新しい規則に合わせた
- `tests/validate-plugin.sh`
