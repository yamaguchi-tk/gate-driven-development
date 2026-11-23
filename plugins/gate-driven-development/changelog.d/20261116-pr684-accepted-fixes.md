---
type: patch
---

#### Summary

- `記録の場所: なし` の行を完了の報告に書くかは、行に付けた印で決める。この行を一次表示に出した human check に本人が返事をしたら、返事を受けた main が `requirements.md` の同じ行の末尾に ` / 表示: 済み` を足し、行を書き直したら外す（一次表示の文面を作る subagent は足さない。表示せずに事前回答を当てたときと、main がその行を一次表示に出したと確かめられないときも足さない）。完了の報告には、印の無い行を書く。`worklog.md` の事前回答の行や今の承認の記録から、表示したかを推し量らない
- compact の一次表示でも、`記録の場所: なし` の行は行数の目安を超えても落とさない
- completion-check の `done` の最終出力にも、`記録の場所: なし` の行を含める
- fail-closed の停止を `参照した正本` / `停止理由` / `次の1アクション` だけで書いていた残りの箇所（`commands/gdd-dev.md` の worktree の検証と 2 系統の検証、TDD の AC ID の無い RED、README・TROUBLESHOOTING・onboarding の説明、evals の期待出力）に、`<gdd-stop>` の後の `## 👤 次にすること` を書いた
- `commands/gdd-dev.md` の entry intent の短縮ルールから、正本の `references/entry-intent.md` に同じ規則がある 2 文を消した

#### Affected Files

- `README.md`・`commands/gdd-dev.md`・`docs/TROUBLESHOOTING.md`・`evals/evals.json`・`references/human-check-template-compact.md`・`references/human-check-template.md`・`references/onboarding.md`・`references/post-completion-pr-flow.md`・`references/subagent-dispatch.md`・`skills/gdd-completion-check/SKILL.md`・`skills/gdd-test-driven-development/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
