---
type: minor
---

#### Summary

後続で実装する guard・contract test の要件を定める Decision（ADR・guardrail）について、独立レビューの収束の規則を `references/independent-review.md` の (3-f) に足した。reviewer は Decision への finding を、文字どおりに読むと文自体が違反を許す（fail-open の向き）ときだけ high にし、「列挙の外の経路で抜けられる」型で文字どおりの読みでは違反になる（後続の test が落ちる側に倒れる）ものは medium 以下にし、category に実害クラスを付けず `test-power` にして、後続の test の要件として申し送る（blocking に数えない）。Decision に当たるか、どちらに倒れるかを判定できなければ (3-f) を当てない（§ 常時 High と通常の基準のまま）。main session は reviewer が付けた severity・category を変えずに数える。`references/reviewer-common.md` § finding category の「降格の防止」にも、この扱いを指す文を足した。high は実装仕様の列挙を足さず、守る事実（主体ごと）と「判定できない形は失敗」に書き直して直す。書き直した後の独立レビューは 1 PR あたり 1 回で、前回の high・blocking がすべて Decision への finding なら(3-a) の 1 つ目の条件に当たっても範囲を前回の独立レビューからの差分にし（(3-a) のほかの全量の条件に当たれば全量）、それでも high または blocking が残れば人に戻す（`references/post-completion-pr-flow.md` の昇格処理の順序 3 に、この経路を書き足した）。

`gdd-planning-reviewer`（design phase）と `gdd-security-reviewer`（全 phase）に、Decision が guard・contract test の実装仕様を列挙していたら Medium として報告し、守る事実＋fail-closed の柵への書き直しを修正案にする観点を足した。

#### Affected Files

- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-security-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
