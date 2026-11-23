---
type: patch
---

#### Summary

- 修正時規律 C（deny 分岐の入力者実測）の記録の項目と記録先を、実際に書かれて確かめられる形にし、修正のコードを書く worker にも届くようにした

#### Changed

- 規律 C の記録の項目を、取得元・範囲・`新しく deny になる件数 / 総件数`・そのうち正当な入力の件数・比べた直し方と採った理由にした
- 規律 C の記録先を、formal gate の修正では `tasklist.md` の該当 task の `Verification Evidence`（controller が書く）、followup では証跡の `Verification:` 行（無いテンプレートでは `Fixed findings` の id とは分けて書く）にした。design-gating を通る修正では 5d（規則の実値検算）の記録で代えてよい
- 規律 C の secret と実値の扱いを、外部形式の実測の ① と ④ に絞って書き、実値を PR コメントにも書かないことを明記した
- `gdd-subagent-driven-implementation` の Subagent Prompt Contract の Constraints で、差し戻しの修正で deny の分岐を足すなら controller が規律 C の実測の結果を worker に渡し、worker が自分の判断で足すなら先に `NEEDS_CONTEXT` で返させるようにした
- `references/self-review-lanes.md` の参照元の理由と、規律 A〜C の位置づけの文を、規律 C を足した後の形に合わせた

#### Affected Files

- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
