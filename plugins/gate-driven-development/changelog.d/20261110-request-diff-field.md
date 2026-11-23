---
type: minor
---

#### Summary

- human check の判断ポイントごとに `- 依頼との差: なし | <推奨が満たさない依頼の原文の項目>` の欄を足した（full と compact。承認ポイント数の宣言の無い簡易な確認は先頭に 1 行。Downstream Human Recheck Handoff は判断ポイントごとに、おすすめの案について 1 行）。理由を書く場所は無い。ユーザーが自分で狭めると決めた点は、その発言を `根拠` の行に引き、欄は `なし` にする。`依頼との差` の語は欄の行だけに使う
- 再提示は全部の点を載せる（変えていない点と、ユーザーが取り下げた点は、1 行と `依頼との差:` の行だけでよい）
- `Human Check Status` を approved にする Write・Edit を、steering の書き込みの検査が直前の提示と照らして止める。止めるのは、`依頼との差` を含む行が `<記号> 依頼との差: <値>` の形でない、値がちょうど `なし` でない点がある、欄が無い、件数が `承認ポイント数` と合わないとき。前の提示とは比べない。依頼から外れる点は、承認ではなく要件の変更の経路（`gdd-requirements-amendment`。計画の途中なら `planning_rework_required`）に送る
- 新しい Bash の PreToolUse hook は、コマンドに `Human Check Status` と `approved` の両方があれば、提示を読まずに Edit・Write へ付け替える（python は起動しない。kill-switch.sh を読めないときも止める）
- 返答ガイドの「OK」は、差が `なし` の点だけを承認する意味に変えた
- 判断ポイントの固定フィールド（前提・採用しない案・無回答時のデフォルトと件数、完了条件の変換、依頼との差）を見る lint を、Stop hook の記録だけの lint に配線した（止めない。警告文にも載らない）
- `request-diff.log` に、各提示の `依頼との差:` の値と欄の問題を残す。承認の記録を止めるたびに、`request-diff-approval.log` に 1 行残す。直前の提示があって Write・Edit の承認を通したときも、時刻・セッション・state.md・提示の transcript の uuid と sha を 1 行残す（読む時期に、通した承認を数える）。Bash の付け替えの deny は残さない
- express の実行時のトークンの予算を 30125 から 30141 に上げた

#### Affected Files

- `hooks/hooks.json`、`hooks/scripts/run-request-diff-approval-gate-hook.sh`、`hooks/scripts/lib/request_diff_approval.py`、`hooks/scripts/lib/request_diff_field.py`、`hooks/scripts/validate-steering-write.py`、`hooks/scripts/lib/request_diff.py`、`hooks/scripts/lib/hitl_lint_gate.py`、`scripts/lint-hitl-decision-fields.py`、`tests/checks/skill-body-budget.sh`
- `references/human-check-template.md`、`references/human-check-template-compact.md`、`references/requirements-gating-steps.md`、`references/rollback-patterns.md`、`commands/gdd-dev.md`、`skills/gdd-brainstorming/SKILL.md`、`skills/gdd-requirements-gating/SKILL.md`

#### User Action Required

- なし。この版より前に出した human check の提示の後で承認を記録すると、1 回止まる（欄が無い）。欄を足して提示し直す。Bash（sed など）で承認を書いていたら、Edit で書く

#### Validation / Eval Impact

- 欄の値は書き手の自己申告で、正しさは見ない。書き手が差に気づかずに `なし` と書けば通る
- 承認を `Human Check Status` と `approved` の語を含まない Bash のコマンド（変数や別のスクリプト）で書くと、どの検査も通らずに記録される
- 変えた点だけを再提示し、`なし` 以外の点が直前の提示から消えると、その点は承認として記録される（前の提示とは比べない）
