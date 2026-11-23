---
type: patch
---

#### Summary

- `docs/SECURITY.md` の制限事項に、shell 文字列を解析する block guard（merge gate・pre-push gate・pre-PR gate）が守る範囲を書いた。agent が事故で打つ形から守り、敵対的に作った形は止めない

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
