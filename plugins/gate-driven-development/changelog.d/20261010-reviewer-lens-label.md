---
type: patch
---

#### Summary

reviewer と相談役の出力に、観点の欄を足した。正式 GDD の reviewer（`references/reviewer-common.md` の Output Format）は finding ごとに `観点: <定義の観点・チェック項目の見出し名 | 観点外>`、相談役（`gdd-opus-advisor`・`gdd-opus-advisor-max`・`gdd-fable-advisor`）は `推奨:` の行に `観点: <要否 | 閉じ方 | 止めるか | 人の選択の代わり | その他>` を書く。観点ごとの効きを後から数えるための欄で、gate と routing は読まない。

#### Affected Files

- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
