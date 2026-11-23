---
type: patch
---

#### Summary

- 上限での方式転換で止まるときの `上限到達:` 行は、止まる遷移を書いた側（gate runner などの subagent か main）が、遷移と同じ手順で 1 回だけ書くようにした。resume・compaction の後に同じ選択肢を表示し直すときは書かない。委任先に聞く前に同じ語の行が 0 本なら（書き落とし）、main が行を書いてから人に止まる。これまでは書く側と時機が 4 か所で違い、委任した 1 回目で人に止まるか、2 回目を数え落とすことがあった
- 判断の委任を human check で選んだ行と、会話で「相談しながら進めて」と言って書いた行は、自走上限を行の値ではなく今の `Approved Direction` の値で読むようにした。これまでは、委任の後に自走上限を引き上げると、行の値と一致せず委任が効かなくなっていた。後続 Stage に写すときは、行の値と元の steering の今の自走上限が同じならその値で写す。違うときは、その差が引き上げの記録（`自走上限の引き上げ:` 行）だけで説明できるときだけ行の値で写し、それ以外（引き下げ・記録の無い差・読めない）は `PR 作成まで` で写す。どちらかが `実装完了まで` なら `実装完了まで` で写す（元の steering の中の引き上げは後続 Stage に届かず、それ以外の差は止まる側に倒す）

#### Affected Files

- `references/human-check-template.md`（§ 事前回答 2・3・4）
- `references/rollback-patterns.md`
- `references/state-machine.md`
- `skills/gdd-pr-review-followup/SKILL.md`
- `agents/gdd-formal-gate-runner.md`・`agents/gdd-light-task-runner.md`（本文が同じ 2 つの runner）
- `skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 関係するテスト（`python3 scripts/light-lane-related-tests.py --run . origin/main`）
