---
type: patch
---

#### Summary

`Independent Review` 行の検査の書き漏れを 5 か所直した。`references/independent-review.md`・`references/self-review-lanes.md`・`skills/gdd-pr-review/SKILL.md` の Task Size ごとの免除（独立レビュー・`dry: yes`）に、pre-push gate が複数の steering から push 対象 tip の証跡で 1 件を選んだときは Task Size によらず standard として検査することを書いた。発火表の sha に「PR 作成時は HEAD」を足し、契約 3 (3-a) の sha 一致検査に pre-PR gate を足した。§ 証跡 の merge gate の一致の検査は、`Bot Review Received: received: no` の経路だけと書き直した。gate の挙動は変えない。

#### Affected Files

- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
