---
type: patch
---

#### Summary

- 自律継続の loop の prompt が、使える `<gdd-stop>` の reason として、`staging-verification-blocked`・`external-review-waiting`・`auth-waiting` も用途を限って挙げる。起動時の表示も、止まる条件を許容値の表で示す
- `/gdd-dev` の sticky 継続は、`done`・`cancelled`・`blocked` の 3 つではなく、loop state を消す reason（`references/output-format.md` の許容値の表。`staging-verification-blocked` を含む）まで続くと書いた
- ビルドループは、reason の用途に当たって止まるときを除いて自律継続すると書き、`clarification-needed` の使いどころを `references/state-machine.md` で引く
- brainstorming の fail-closed の停止（entry intent の `ambiguous` など）は、許容値の表と loop の prompt に合わせて `<gdd-stop reason="blocked">` で止まる（これまではマーカーを使わないと書いていた）
- 自然文から停止を推定しない規定と、`次のアクション` の terminal 状態の一覧は、reason の一覧と読めないように書き直した

#### Affected Files

- `commands/gdd-dev.md`・`references/output-format.md`・`references/stop-hook-structured-markers.md`・`references/subagent-dispatch.md`・`scripts/setup-gdd-loop.sh`・`skills/gdd-brainstorming/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
