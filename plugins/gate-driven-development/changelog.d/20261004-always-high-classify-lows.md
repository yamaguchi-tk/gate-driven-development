---
type: patch
---

#### Summary

- 外部レビューの指摘を分ける Classify で、判定できない指摘を High にした後に戻す条件・戻し先・根拠の残し方と、部品の決め方を書いた

#### Changed

- `gdd-pr-review-followup` と `pr-review-followup` の Classify: 戻す条件を「4 型に当たらない、または適用範囲外の部品だと確かめたら」とし、受け入れ判定の「範囲外」（pr-review-followup では手順 3 の out-of-scope）とは別だと書いた
- 同じ Classify: 戻し先を「この規定を掛けずに分けた severity」にした。reviewer が付けた値は High / Medium / Low / advisory に読み替え、読み替えられなければ main が分けた値にする。確かめた根拠は PR コメントに残す
- 同じ Classify: どの部品かの決め方と、判定できないときに適用範囲内とすることは、言い換えずに `reviewer-common.md` § 常時 High を指す形にした。Medium の上限の例外も category の値を並べず、同節を指す形にした
- `gdd-receiving-code-review` のトリアージ表の深刻度: 選択肢に Low と advisory を入れ、呼び出し元に Classify が無いときも § 常時 High に従うようにした

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-receiving-code-review/SKILL.md`

#### User Action Required

- 操作は不要。判定できないことを理由に High にした外部レビューの指摘は、確かめて戻すときに、その根拠を PR コメントに残すことになる

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
