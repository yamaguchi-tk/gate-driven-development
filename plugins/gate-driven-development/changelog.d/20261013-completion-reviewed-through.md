---
type: patch
---

#### Summary

- `gdd-completion-check` の 2 回目以降の Round の差分の起点を、新しい field `Completion Reviewed Through`（`tasklist.md`）にした。Step 13 の `gdd-completion-reviewer` の出力が返った Round を差し戻すとき（Round 上限超過を含む）に、差し戻しの書き込みを終えた後で、Step 13 で reviewer を起動する直前の `HEAD` で上書きする。Step 19 の停止などの差し戻し以外の出口、時間超過・エラーで返らないとき、書き込みを終える前に止まったときは書かない
- これまでは起点が `Completion Baseline`（差し戻しのたびに進む）だったので、Step 13 より前（Part A・B）で差し戻した Round の後は、Step 13 が一度も見ていない前の Round の修正が起点より前に入り、差分スコープで素通りしていた。今は、どこで差し戻しても、Step 13 が見ていない変更はすべて次の diff に入る
- `Completion Reviewed Through` が無い（Step 13 がまだ判定を返していない）・sha を解決できない・`HEAD` の祖先でない・diff が空のときは全量を再検証する。「`Completion Rounds` が 0 なら全量」の条件は、この条件に置き換えた
- `Completion Rounds` と `Completion Baseline` の書き方（Round 数の fail-closed）は変えていない。done で 3 行とも消し、route reset・tasklist の作り直しでは 3 行とも引き継ぐ

#### Affected Files

- `plugins/gate-driven-development/references/gate-checklists.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`

#### User Action Required

- なし（進行中の `tasklist.md` には `Completion Reviewed Through` が無いので、次の Round は全量の再検証になる）

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
