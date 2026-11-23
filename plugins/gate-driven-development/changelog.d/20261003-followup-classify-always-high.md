---
type: patch
---

#### Summary

- PR 作成後のレビュー対応で、外部レビューの指摘を分けるときにも `reviewer-common.md` § 常時 High を掛けるようにした

#### Changed

- `gdd-pr-review-followup` と `pr-review-followup` の Classify で、§ 常時 High の 4 型に当たり、同節の適用範囲に当たる指摘は、source と reviewer が付けた severity によらず High に分けるようにした

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`

#### User Action Required

- 操作は不要。止まる場面が増える: `gdd-pr-review-followup` では、§ 常時 High に当たる指摘が比較 diff の外にあると `Independent Review` の high に数えたまま `範囲外 blocker` の checkpoint で止まる。`pr-review-followup` では、Low・advisory として merge 前 blocker から外せていた指摘が High になり、loop を続ける対象になる

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
