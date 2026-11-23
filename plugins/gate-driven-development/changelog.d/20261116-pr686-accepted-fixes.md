---
type: patch
---

#### Summary

- human check の返事を受けた main が足す印の文字列（` / 表示: 済み`）と足す行（一次表示に出した `記録の場所: なし` の行）を、`commands/gdd-dev.md` の human check 承認後の手順にも書いた。返事のたびに full 版の template を開かなくても印を足せる
- 完了の報告に書く `記録の場所: なし` の行は、印の無い行である。一次表示で見せたが、返事をしたと main が確かめられなかった行も書くと明記した
- Stage Continuation で新しい steering を作るときに、継続元の `requirements.md` の、印の無い `記録の場所: なし` の行を新しい steering に写す。写せないときは継続せずに止まる。継続で作った steering の `done` では、どの経路で出すかを問わず、その steering の `requirements.md` だけを読む。Origin の steering は別の worktree にあり、継続先からは読めないため
- README・TROUBLESHOOTING・onboarding の停止時の出力の説明で、`## 👤 次にすること` が `cancelled` の停止には付かないことを書いた

#### Affected Files

- `README.md`・`commands/gdd-dev.md`・`docs/TROUBLESHOOTING.md`・`references/onboarding.md`・`references/post-completion-pr-flow.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
