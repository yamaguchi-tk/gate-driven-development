---
type: patch
---

#### Summary

- `references/testing-anti-patterns.md` § テスト判定基準のクラス表に、クラス I（条件で分かれる AC の止める側・境界の穴）を足した。Contract Surface Coverage の止める側・境界の行は、このクラスで選ぶ
- `gdd-test-driven-development` の Contract Surface Coverage で、`実装前から pass（対照）` のテストは、既存の実装に変異（止める分岐を外す、閾値を 1 つ通す側へずらすなど）を入れて落ちることを確かめ、行に `変異: <入れた変異> -> <落ちたテスト名>` と書くようにした
- implementation-gating で Contract Surface Coverage の行を読むようにした。inline review の checklist（`references/inline-review-checklists.md` § AC・契約準拠）に項目を足し、escalation で起動する reviewer の入力（1 枚）にも task ごとの Contract Surface Coverage を `参照:` で渡す（超過の再実行でも残す）。条件で分かれる AC に止める側（枝ごと）・境界の行が無い、`not_applicable` の理由が AC と食い違う、対照のテストに変異の記録が無いか落ちたテストが行のテストと違う、のどれかを `test-power` として扱う

#### Affected Files

- `plugins/gate-driven-development/references/testing-anti-patterns.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/inline-review-checklists.md`
- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-implementation-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
