---
type: minor
---

#### Summary

完了前の最終レビュー（`gdd-completion-reviewer`）と PR 前のレビュー（`gdd-pr-review` の 3a）が、steering の依頼の原文（`request.md`）を読み、依頼の語ごとに差分が届けるものと突き合わせるようにした。依頼の要件を届けていない、語を狭めた・広げた・読み替えた、合格の条件を替えた、確認なしに対象外・後回し・限界にした、頼まれた手段を別の手段で代えた、の型を探し、どれも High（`Request Drift`）にする。承認の記録に数えるのは `request.md` に写したユーザーの発言だけで、`Approved Direction` や非スコープは数えない。このずれは AC・非スコープの追記では閉じず、依頼に合わせて実装を直すか、`human_recheck_required` に戻してユーザーに確かめる。`request.md` は quick (standard)・standard だけにあり、無いときは行わない。完了前の最終レビューには `request.md` のパスを渡す。

照合の材料が足りるように、ユーザーの本人の発言（human check への返答と、作業中の指示）も、cross-session 経由のものを除いて、route の分類によらず `request.md` に言い換えずに時刻つきで足すようにした。human check への返答には、承認した承認ポイントと「完了条件の変換」表の行を引用して添える。2026-10-08〜10-12 に GDD を使う別の repo では、`request.md` があったタスクで、完了前の最終レビュー 9 回・PR 前のレビュー 6 回のどれも `request.md` を読んでいなかった。また、4 タスクのうち確かめた 2 つで、途中の回答が `request.md` に写されていなかった。

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-completion-reviewer.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/references/brainstorming-steps.md`・`references/human-check-template.md`・`references/phase-progression.md`・`references/subagent-dispatch.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`・`tests/checks/lint-scripts-functional.sh`（runtime profile の推定 token の上限を、standard は 45454 から 45472 に、express は 30099 から 30117 に上げた）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
