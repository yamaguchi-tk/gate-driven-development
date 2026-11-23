---
type: patch
---

#### Summary

`Independent Review` 行を検査する gate として pre-push gate だけを挙げていた `references/self-review-lanes.md`・`references/independent-review.md` § 証跡・`CONTRIBUTING.md` に、pre-PR gate（HEAD と比べる）を足した。`skills/gdd-pr-review/SKILL.md` の quick・trivial の免除に、pre-push gate が複数の steering から push 対象 tip の証跡で 1 件を選んだときは Task Size によらず検査することを書いた。gate の挙動は変えない。

#### Affected Files

- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
