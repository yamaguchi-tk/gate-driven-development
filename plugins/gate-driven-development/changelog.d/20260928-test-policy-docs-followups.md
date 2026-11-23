---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。`gdd-writing-skills` の Process Documentation TDD と Skill Type Testing Matrix は、見出し・判断語の有無を test に入れるよう指示していた。文書の語・見出しの有無だけを見る test を書くかは、対象 repo のテストの基準（`references/testing-anti-patterns.md` § テスト判定基準が探す先）に従う（この plugin の repo では `tests/test_*.py` に書かない）、見出しと判断語が効くことは pressure scenario・eval・review scenario で確かめる、に改めた。`CONTRIBUTING.md` のテストの方針は、command・agent の frontmatter をコードが読む値の側に置き、command の本文を含む文書の語・文だけを見るテストは書かず、残さない、に改めた。

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-writing-skills/SKILL.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `Skill RED-GREEN Evidence`（PR 本文）: 見出しと判断語を足した skill の変更に対して、変更前の skill では見出し・判断語の有無を見る test を足すか、変更後では足さないかを pressure scenario で比べた
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
