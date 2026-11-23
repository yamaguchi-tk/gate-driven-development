---
type: patch
---

#### Summary

`gdd-test-driven-development` の Contract Surface Coverage（RED 作成前の確認）で、条件で挙動が分かれる AC（すべて。例: 入力を受け入れるか止めるか、副作用を起こすか起こさないか、retry・状態遷移をするかしないか）では、`validation / sanitize / fail-closed path` を `止める側（通さない入力・起こさない側）`・`境界（閾値ちょうど・空・形が 1 箇所だけ違う入力）` の 2 行に分けて書くようにした。各行は `references/testing-anti-patterns.md` § テスト判定基準 で選び、言えない行は `not_applicable（理由）` にする。実装前から通るテストはこの行に `実装前から pass（対照）` と書き、RED Evidence には入れない。利用者の `/gdd-dev` の TDD が書くテストが、条件で挙動が分かれる AC で増えることがある。

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
