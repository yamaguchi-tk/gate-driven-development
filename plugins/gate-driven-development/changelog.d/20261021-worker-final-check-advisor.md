---
type: patch
---

#### Summary

- 実装 worker 3 本（`gdd-implementation-worker`・`gdd-implementation-worker-heavy`・`gdd-remediation-worker`）に、実装と verification を終えた後（commit の後・return の直前）の最後の確認では advisor ツールを呼ばない規定を足した。散文の指示で、呼ばないことは保証しない
- 2026-10-12〜20 の実行では、最後の確認の後に成果物を実質的に変えた run は 47 本中 1 本だった。後ろには implementation-gating が残る
- 実装の前の方針の相談と、実装の途中の相談は残す（同じ版の `20261030-agents-no-advisor.md` で、実装の worker はどの時点でも advisor ツールを呼ばないようにした）。return の形・model・effort は変えていない

#### Changed

- `agents/gdd-implementation-worker.md`・`agents/gdd-implementation-worker-heavy.md`・`agents/gdd-remediation-worker.md`（`## 契約` の return の行の前に 1 行。3 本の本文は同じに保つ）

#### Affected Files

- `agents/gdd-implementation-worker.md`
- `agents/gdd-implementation-worker-heavy.md`
- `agents/gdd-remediation-worker.md`

#### User Action Required

- 動いているセッションは、開き直すまで古い定義で動く

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
