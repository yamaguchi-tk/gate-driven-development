---
type: patch
---

#### Summary

completion-check の reviewer が時間超過・エラーで、入力を変えない再実行を含めて 2 回とも返らなかったときの出口を決めた。design・implementation と同じく、Round と `Completion Rounds` を進めず、`<gdd-stop reason="blocked">` で止めて人間に渡す。`worklog.md` の `gate結果:` 行には `判定: blocked` と書く。completion-check の Step 13 からこの出口を指し、gate runner は `result: review_unavailable` を返す。main はこの result のときと、gate runner を時間上限で止めたときに、不足 evidence ではなく completion review が成立していないことを停止理由として出す。この経路は `Completion Rounds` に数えない（+1 するのは差し戻しのときだけ）。`Completion Rounds` が 0 のとき（差し戻しがまだ無く、停止の後に再実行するとき）は、`Completion Baseline` があっても全量を再検証する。

#### Affected Files

- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/gate-checklists.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
