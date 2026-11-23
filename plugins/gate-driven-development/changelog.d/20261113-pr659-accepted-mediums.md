---
type: patch
---

#### Summary

- human check の相談役の推奨が表示の後に届いたら、推奨の行だけを追記せず、確認の全文を出し直すようにした（推奨案を変えないときも同じ。相談役は起動し直さない）。追記の発言には `依頼との差:` の欄が無く、その後の OK を承認の書き込みの検査が止めていた
- requirements-gating の時間の目安（Step 4b）を、着手・要件確認の返事・`request.md` に足した最後のユーザーの発言のうち、いちばん遅い時刻から測るようにした。human check の後に戻った Round が、人の返事を待った時間で必ず打ち切られることが無くなる。経過は、blocking を処置する前にも確かめ、超えていたら処置せずに一括提示に進む
- 要件を固める確認の答えから新しく分かれた点を、`request-crosscheck.md` の要件の表にも続きの `#` で足し、`worklog.md` の固定行の行数と行き先に入るようにした。見直しで上書きした後の足し直しも、要件の表と節の両方に、新しい出力の最後の `#` に続く番号で足す
- `requirements.md` のテンプレート（standard・express）に `### ズレ確認` の節を足した
- human check の一次表示の「どこまで自走するか」に `具体化:` の行を足し、「完了条件の変換」表の延期・削除でない行（`具体化`・`追加` など）を 1 行ずつ出すようにした。OK はこの行も承認し、返答の写しには一次表示に出した行だけを引用する（completion reviewer の承認の記録も同じ）
- 判断の委任で、相談役が確認に並んでいない案（案に足す・変える推奨を含む）を推したら、委任で決めずに人に戻すようにした

#### Affected Files

- `references/human-check-template.md`・`references/requirements-gating-steps.md`・`references/brainstorming-steps.md`・`references/autonomy.md`・`references/human-check-template-compact.md`・`references/subagent-dispatch.md`・`references/rollback-patterns.md`・`references/requirements-template.md`・`references/requirements-template-express.md`・`agents/gdd-completion-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 文書だけの変更。`python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
