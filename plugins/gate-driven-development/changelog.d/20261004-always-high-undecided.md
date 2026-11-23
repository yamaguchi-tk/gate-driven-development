---
type: patch
---

#### Summary

- 外部レビューの指摘を分けるときの「判定できない指摘も High」を、掛ける範囲と、判定がついた後の戻し方まで書いた

#### Changed

- `gdd-pr-review-followup` と `pr-review-followup` の Classify: 4 型に当たるかを判定できない指摘を High に分けるのは、適用範囲内の部品（どの部品か判定できないときは適用範囲内）に限り、適用範囲外と判定できた部品には掛けない。受け入れ判定（pr-review-followup では手順 3 の Verify）で 4 型・適用範囲に当たらないと確かめたら reviewer の severity に戻し、指摘そのものが誤りなら棄却する（pr-review-followup では invalid）
- 同じ Classify の Medium 上限に、`data-loss`・`security-boundary` を付けたものを除くことを書いた
- `pr-review-followup` の Classify から、その skill に無い「受け入れ判定」「下の advisory の既定」の語を除いた
- `gdd-receiving-code-review` のトリアージ表の深刻度は、呼び出し元の Classify に従い、単独で使うときは `reviewer-common.md` § 常時 High に従うようにした

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-receiving-code-review/SKILL.md`

#### User Action Required

- 操作は不要。適用範囲外の部品（warn-only の lint、開発者が実行する検査など）への外部レビューの指摘は、4 型に当たるかを判定できなくても High にならない。High に分けた指摘も、4 型・適用範囲に当たらないと確かめた時点で reviewer の severity に戻る

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
