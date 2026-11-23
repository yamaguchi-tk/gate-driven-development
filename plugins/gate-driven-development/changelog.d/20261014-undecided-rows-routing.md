---
type: patch
---

#### Summary

着手前の突き合わせ（`request-crosscheck.md`）で `原文だけでは決まらない` と判定した行は、1 行ずつ行き先（human check で聞く質問、「完了条件の変換」表の `具体化` の行、延期・削除・追加の行のどれか）を決め、human check の § ズレ確認 に固定行 `原文だけでは決まらない: <n> 行 / 質問: #a, … / 具体化: #b→AC-n, …（変換表の具体化 <m> 行） / 延期・削除・追加: #c, …` として `#` を全部並べるようにした。`<m>` は「完了条件の変換」表で、初期条件の先頭に crosscheck の `#` を書いた `具体化` の行の数で、`具体化:` の `#` の数より少なければ表に落ちた行がある。`質問` にした行は質問の文を `#` つきで固定行の下に載せ、`Human Check Questions` の 2 個の上限に数える。0 件なら `原文だけでは決まらない: なし`。同じ固定行を `worklog.md` にも書く。これまでは、AI が仮決定したときに `具体化` の行を書くとだけ決めていて、質問にも表にも載らずに main が決めた行がユーザーから見えなかった（10-09〜10-13 の 7 タスクの 49 行のうち 25 行）。

#### Affected Files

- `plugins/gate-driven-development/references/brainstorming-steps.md`（9 の「依頼と既存コードの突き合わせ」の (5)）
- `plugins/gate-driven-development/references/human-check-template.md`・`references/human-check-template-compact.md`（§ ズレ確認）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
