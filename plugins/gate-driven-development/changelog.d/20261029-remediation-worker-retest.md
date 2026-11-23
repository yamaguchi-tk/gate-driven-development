---
type: patch
---

#### Summary

`references/fixed-models.md` の `remediation_loop` tier の段落に、remediation worker を xhigh と max で当て直して比べた結果を書いた。これまでは「比べた実測は無い」と書いていた。effort は `xhigh` のまま変えない。max に戻すかを見直す条件（worker の後の gate が `approved` になる率が、max で走った 61 本より下がったとき）も書いた。

#### Changed

- `references/fixed-models.md`：`remediation_loop` tier の段落の、xhigh と max の比較の記述を当て直しの結果に替えた
- `changelog.d/20261028-remediation-worker-xhigh.md`：同じ記述を当て直しの結果に替えた

#### Affected Files

- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/changelog.d/20261028-remediation-worker-xhigh.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
