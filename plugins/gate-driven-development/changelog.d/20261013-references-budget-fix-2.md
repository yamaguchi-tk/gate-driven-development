---
type: patch
---

#### Summary

- 利用者から見える変更なし。`references/` の合計行数が `tests/checks/skill-body-budget.sh` の上限（12149）を 3 行超えていたので、`references/gate-status-schema.md` § `Status` の、改行で折り返していた 2 つの段落を 1 行ずつにつないだ。文言は変えていない

#### Affected Files

- `plugins/gate-driven-development/references/gate-status-schema.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
