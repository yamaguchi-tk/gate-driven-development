---
type: patch
---

#### Summary

- human check の判断ポイントの `依頼との差:` の値を、`なし` か、推奨が満たさない依頼の原文の項目を宣言する `あり: <その項目>` の 2 形に閉じた。ほか（`なし | <項目>`・`なし。`・`ありません。` など）は「欄の形が読めない」になる。今までは `なし` 以外は何でも「なし以外の点がある」で、`なし | <項目>` と書いた確認も、差のある正しい提示と区別できなかった
- 確認を出した Stop で、人の発言の後で最後のマーカー付きの発言の欄が読めないか、マーカーの直前のタグ（`request-diff`）が無い・読めないなら、request-diff の hook が block し、ユーザーが答える前に確認の全文を出し直させる（読み手の `claude -p` は起動しない）。同じ人の発言のターンで 2 回まで block し、その後は止めずに `systemMessage` で知らせる。例外・読めない transcript では止めない。今までは、ユーザーが OK した後に承認の書き込みで止まり、OK を言い直させていた。`あり:`（タグは `differs`）の点がある確認は、Stop では止めない（OK は要件の変更の経路に送られる）
- 提示の時点の lint（`scripts/lint-hitl-decision-fields.py`）は欄の形だけを見る。`あり:` で宣言した差は通す
- 承認の書き込みの拒否の文とテンプレートで、欄の形の行を `- 依頼との差: なし` だけにした（今までの `なし | <項目>` は、並べて書く形と読まれていた）。拒否の文に、出し直しの説明の文にも欄の名前を書かない、追記・回答にマーカーを付けない、同じ提示のまま承認の書き込みを繰り返さない、を足した

#### Affected Files

- `hooks/scripts/lib/request_diff_field.py`（値の 2 形・`format_problem`）・`hooks/scripts/lib/request_diff.py`（Stop の block）・`hooks/scripts/lib/request_diff_approval.py`（拒否の文）・`hooks/scripts/run-request-diff-hook.sh`・`hooks/hooks.json`（description）・`scripts/lint-hitl-decision-fields.py`
- `references/human-check-template.md`・`references/human-check-template-compact.md`・`references/requirements-gating-steps.md`・`references/rollback-patterns.md`・`README.md`
- `tests/test_request_diff_hook.py`・`tests/test_request_diff_approval_gate.py`・`tests/test_lint_hitl_decision_fields.py`・`tests/test_hooks_wiring_new_events_contract.py`

#### User Action Required

- なし。差のある点を書くときは、値を `あり: <依頼の原文の項目>` にする

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 欄の値の 2 形と読めない値、Stop の block（欄が読めない・タグが無い・タグが読めない・説明の文に名前・追記にマーカー）、最後のマーカー付きの発言を読むこと、前のターンの提示を読まないこと、上限と人の発言での数え直し、block の記録を見たことにしないこと、例外で止めないことのテストを足した
