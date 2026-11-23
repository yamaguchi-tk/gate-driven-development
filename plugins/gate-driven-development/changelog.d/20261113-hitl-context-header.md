---
type: patch
---

#### Summary

- human check の一次表示の冒頭に、前置き 3 行（`**依頼**:` に依頼の原文の引用、`**なぜやるか**:` に解決する問題と根本原因、`**現在地**:` に済んだ工程とこの返事で次に始まること）を置くようにした。前の版で一次表示を判断ポイントと OK の範囲だけにしたため、何のために何を決めるかが確認だけでは分からなかった。確認の出し直し・経過報告の末尾の問い・完了報告の問いでも前置きを毎回書き、「内容は前回と同じ」のように前の発言を指して中身を省かない。停止の出力（`## 停止しました`）と、実装の途中で人に戻す Downstream Human Recheck Handoff も、停止の種類によらず冒頭に前置きを書く。返事を待たない停止の `**現在地**:` には、次に何を待っているかを書く
- 判断の材料にレビューの指摘などを使うときは、件数と場所の 1 行にし、案の選び方を分ける点は各案で何が残るかの文の中に書く。相談役の推奨の追記にも前置き 3 行を書き、判断ポイントは番号や案の名前だけでなく何を決める点かを書く。Clarification Loop で返事が無いときも「回答待ち」だけで止めず、前置きと待っている問いを出し直す
- `steering write guard` は、承認の記録を通すかを、マーカーの直前の `<gdd-hitl-fields ...>` タグに足した `request-diff`（判断ポイントの順に `none`/`differs` をカンマで）だけで決め、本文の `承認ポイント数:` と欄の数は読まない。タグが無い・`request-diff` が読めない・`differs` がある提示と、本文の `依頼との差:` の欄が読めない形か `なし` 以外の値の提示は、承認の記録を止める。本文の欄が欠けていても止めない。本文の欄の行は先頭から順に読むようにし、空白の長い行で長さの二乗の時間がかかって hook の上限を超え、guard 全体が走らずに書き込みが通る穴を塞いだ。以前は件数を本文の `承認ポイント数:` から読んでいたので、語を書き換えた宣言や `:` の無い宣言は照合を抜け、依頼の複数行の引用にある欄の形の行が欠けた本物の欄の代わりに数えられていた。タグを書いていない提示は、承認の前に一度止まり、タグを足して出し直すことになる。依頼の引用は `**依頼**:` の 1 行に収め、`依頼との差` の語を含むときは「…」で切る
- `steering write guard` は、起動したら 8 秒の時限を掛け、超えたら止める（deny）。guard の中の処理が遅い入力（Python 3.12 以前の NFKC は、結合文字の長い連なりで 17 秒台かかる）で hook の上限 10 秒を超えると、guard 全体が走らずに書き込みが通っていた。bash・Python の起動と import は時限の外なので、hook の上限を 10 秒から 30 秒に上げた（止まった guard を待つ時間は 8 秒のまま）。時限は既定の動作の SIGALRM で、`signal.setitimer` の無い環境（Windows の Python）では張れない。bash・Python の起動と import は時限の外なので、そこに 22 秒を超えてかかると、今までどおり guard が走らずに通る

#### Affected Files

- `references/human-check-template.md`、`references/human-check-template-compact.md`、`references/output-format.md`、`references/rollback-patterns.md`、`skills/gdd-brainstorming/SKILL.md`、`skills/gdd-requirements-gating/SKILL.md`、`references/requirements-gating-steps.md`、`hooks/hooks.json`、`hooks/scripts/lib/request_diff_field.py`、`hooks/scripts/lib/request_diff_approval.py`、`hooks/scripts/validate-steering-write.py`、`references/phase-gate-prechecks.md`（重なった空行を 1 つ詰めた）

#### User Action Required

- なし

#### Validation / Eval Impact

- 前置きの有無を見る lint は足していない。`field_problem` を呼ぶ記録だけの lint（`lint-hitl-decision-fields`）と `request-diff.log` の `field_problem` の値は、guard と同じくタグの読み方で変わる（タグの無い提示は「タグが無い」になる）。`なぜやるか`・`現在地` の語は、これまで `詳細:` の行で満たされていたが、今後は前置きの行で満たされる
