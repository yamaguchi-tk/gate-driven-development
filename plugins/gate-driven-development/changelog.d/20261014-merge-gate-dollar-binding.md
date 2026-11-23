---
type: patch
---

#### Summary

`docs/SECURITY.md` の制限事項の、marker の無い git cwd から parser が対象を決められない形で打つ merge の項で、開き直す条件と実データの件数を書き直した。番号と repo を読める merge なら `$` があっても binding を引く案は、実データで判定が変わる merge が 0 件だったので入れていない。開き直すのは、この形の merge のうち、binding が読める steering に対象 PR が記録されたものが見つかったときとした。hook の挙動は変えていない。

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
