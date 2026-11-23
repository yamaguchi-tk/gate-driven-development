---
type: patch
---

#### Summary

- 要件を固める確認で、既存側をユーザーが決めた規則・方針として仮決定した `既存とぶつかる` の行は、確認で聞いた行でも human check の一次表示の § ズレ確認 に載せる。本人が OK を返したときは、その返事が completion reviewer の承認の記録に入り、実装の後に依頼からのずれとして止まらない（completion reviewer の承認の記録に、§ ズレ確認 に出したこの仮決定の行を足した。§ ズレ確認 のほかの行は OK では承認しない）。事前回答の委任では承認の記録にならないので、この行があり、本人がまだその行を承認していなければ、委任先によらず human check を表示する
- その仮決定に添える記録の場所は、repo の `CLAUDE.md`・`AGENTS.md` のうち着手前の commit にある行に限る（このタスクの差分で足した・変えた行、`.claude/rules/` などほかの規則のファイルは数えない）。記録の場所が無ければ、依頼の原文どおりになる側に仮決定する
- human check の `原文:` が `request.md` から引く発言に、hook の節の下に時刻つきで足したユーザーの発言を含めた
- `references/state-machine.md` の stop の reason は、ほかの 2 か所でも値を並べず、`references/output-format.md` の許容値の表を指す

#### Affected Files

- `agents/gdd-completion-reviewer.md`・`references/brainstorming-steps.md`・`references/human-check-template.md`・`references/human-check-template-compact.md`・`references/state-machine.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
