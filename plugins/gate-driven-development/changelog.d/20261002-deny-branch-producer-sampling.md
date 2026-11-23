---
type: patch
---

#### Summary

- reviewer の指摘を直すときに guard へ deny の分岐（拒否する条件・上限・受理する集合の縮小）を足すなら、実装の前に、新しく deny になる入力を本番で誰が何件出すかを測るようにした。測らずに足した上限が正当な入力を止め、次の指摘を生むのを防ぐ

#### Added

- `references/self-review-lanes.md` § 修正時規律 に規律 C（deny 分岐の入力者実測）を足した。測る先・読み取り専用の操作・記録先（`findings.md` か followup の証跡）、正当な入力が当たったときに別の直し方を比べること、測れないときに「未測」と限界を書くことを決めた

#### Changed

- 修正の手順（`gdd-subagent-driven-implementation` の差し戻し時の修正、`pr-review-followup` と `gdd-pr-review-followup` の ①直す）から、規律 C を指すようにした

#### Affected Files

- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/tests/test_self_review_lanes_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_self_review_lanes_contract.py`
- `tests/validate-plugin.sh`
