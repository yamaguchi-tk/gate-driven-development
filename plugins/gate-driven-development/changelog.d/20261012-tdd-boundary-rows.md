---
type: patch
---

#### Summary

`gdd-test-driven-development` の Contract Surface Coverage で、条件で挙動が分かれる AC の 2 行（止める側・境界）を、`validation / sanitize / fail-closed path` の行を分けるのではなく、どの観点の行に当たるかを問わず AC ごとに足す形にした。止める側は AC が「通さない・起こさない・しない」と定める側（その側の副作用も見る。3 つ以上に分かれる AC では通す側以外の枝ごと）、境界は止めるべき入力のうち通す入力に最も近いもの（閾値の止める側の端、通す形と 1 箇所だけ違う入力）とした。記録の語彙と記入例も 2 行の形にそろえた。

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
