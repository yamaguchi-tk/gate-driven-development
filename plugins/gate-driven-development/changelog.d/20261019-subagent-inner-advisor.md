---
type: patch
---

#### Summary

- GDD の reviewer 4 本（`gdd-security-reviewer`・`gdd-completion-reviewer`・`gdd-implementation-reviewer`・`gdd-planning-reviewer`）と runner 2 本（`gdd-formal-gate-runner`・`gdd-light-task-runner`）に、advisor ツールを呼ばない規定を足した。この plugin を使う repo でも、gate と review の中で advisor（Fable 5.1）を呼ばなくなる
- 2026-10-12〜16 の実行の後ろ向き集計で、これらの agent の中で呼んだ advisor の助言を読んで指摘や判定を変えた run は 0〜8% だった。advisor の費用は、呼んだ agent の文脈をすべて読ませる分だけかかる
- 観点・severity・出力の形・model・effort は変えていない

#### Changed

- `agents/gdd-security-reviewer.md`・`agents/gdd-completion-reviewer.md`・`agents/gdd-implementation-reviewer.md`・`agents/gdd-planning-reviewer.md`（`## Mission` の前に 1 段落）
- `agents/gdd-formal-gate-runner.md`・`agents/gdd-light-task-runner.md`（`## 契約` の箇条書き。2 本の本文は同じに保つ）

#### Affected Files

- `agents/gdd-security-reviewer.md`
- `agents/gdd-completion-reviewer.md`
- `agents/gdd-implementation-reviewer.md`
- `agents/gdd-planning-reviewer.md`
- `agents/gdd-formal-gate-runner.md`
- `agents/gdd-light-task-runner.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
