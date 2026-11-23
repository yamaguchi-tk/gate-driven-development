---
type: patch
---

#### Summary

- 外部レビューの指摘を分けるときの § 常時 High の扱いを、上限側と判定できないときまで書いた。ほかの skill の文言もそろえた

#### Changed

- `gdd-pr-review-followup` と `pr-review-followup` の Classify: 適用範囲外の部品の 4 型は Medium を上限にする。4 型や適用範囲に当たるかを判定できない指摘も High に分け、誤りなら受け入れ判定で棄却する（advisory の既定より優先する）
- `gdd-pr-review` の 3g の重さと、`gdd-receiving-code-review` のトリアージ表の深刻度に、§ 常時 High の 4 型で適用範囲に当たるものは High にすることを書いた
- `references/reviewer-common.md` の参照元に、節を名指しして参照する skill・reference を入れた（以前は「skill からは直接参照しない」と書いていた）

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-receiving-code-review/SKILL.md`
- `plugins/gate-driven-development/references/reviewer-common.md`

#### User Action Required

- 操作は不要。PR 作成後のレビュー対応で、4 型に当たるかを判定できない外部レビューの指摘も High になり、その周回で直すか受け入れ判定で棄却する対象になる

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
