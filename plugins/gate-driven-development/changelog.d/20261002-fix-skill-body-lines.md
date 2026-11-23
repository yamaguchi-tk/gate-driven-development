---
type: patch
---

#### Summary

- `skills/gdd-next-plan/SKILL.md` の、事前回答で後続 Stage に着手する項目を、直前の項目（同じチャットで継続する）の末尾にまとめた。文言は変えていない。2 つの変更が同時にマージされ、skill 本文の合計行数が上限（7068）を 1 行超えていた

#### Changed

- `skills/gdd-next-plan/SKILL.md`：2 つの箇条を 1 つにまとめた（内容は同じ）

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-next-plan/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（skill 本文の合計行数の検査）
