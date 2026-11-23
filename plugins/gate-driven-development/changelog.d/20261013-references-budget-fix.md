---
type: patch
---

#### Summary

利用者から見える変更なし。`references/` の行数が行予算（12149 行）を 3 行超え、`validate-plugin.sh` の `skill-body-budget` が落ちていたのを戻した。`references/task-breakdown-steps.md` の、改行で折り返していただけの 1 段落を 1 行にまとめた。文面は変えていない（段落の中の改行を除いただけ）。

#### Affected Files

- `plugins/gate-driven-development/references/task-breakdown-steps.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
