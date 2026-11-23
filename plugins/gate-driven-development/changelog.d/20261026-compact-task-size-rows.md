---
type: patch
---

#### Summary

- human check の一次表示（compact）の「現在地」に、タスクサイズ（判定理由つき）・フロー・通過予定 gate 数の 1 行を足した。今までは full の「やること」にしか無く、brainstorming の 18 が求める、タスクサイズ・フローの行での明示が、最初に人に見せる画面に届いていなかった。値は full の「やること」の同じ行と同じ

#### Changed

- `references/human-check-template-compact.md`（Template の § 現在地。行数の予算に収めるため、§ Primary Surface Budget の文を冒頭の段落に移して節を畳み、§ Option Completeness から Template の placeholder と同じ単一案の書き方を除いた）

#### Affected Files

- `references/human-check-template-compact.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
