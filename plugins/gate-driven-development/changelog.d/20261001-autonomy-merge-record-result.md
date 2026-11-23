---
type: patch
---

#### Summary

自走上限でマージを選んだタスクで、`worklog.md` に書く宣言と例外の記録を、読んだ行ではなく判定の結果にした。`~/.gdd/config.local.md` に `on` と `off` の 2 行があるときなど、例外が無いと判定した入力でも、問わずにマージへ進めてしまう穴を閉じる。

#### Changed

- `references/post-merge-qa.md` § 宣言: 宣言の判定の結果を `Post-PR Autonomy 判定: <merge | merge-deploy-qa | なし>`、例外の判定の結果を `Post-PR Autonomy 例外: <on | なし>` と書く。§ 宣言の読み方で数えた `GDD QA *` の行だけを読んだまま `Post-PR Autonomy 宣言:` として残し、QA の runner に渡す。`merge` では `マージまで` だけ、`merge-deploy-qa` では両方を選べることを明記した
- `references/post-merge-qa.md` 手順 2: 自走のマージの条件は、`判定`・`例外` の記録がそれぞれ 1 行だけで、値が条件に合うときだけ満たす（満たさなければ 1 問で問う）
- `references/post-merge-qa.md` 手順 1: QA の書き込みを runner に任せるのは、`例外` の記録が 1 行だけで `on` のときだけ（満たさなければ書き込みをしない計画にする）
- `references/post-merge-qa.md` § 入口: 再開で `マージ前` の行だけがあるときは、`gh pr view <PR> --json state,mergeCommit,headRefOid` で分ける。MERGED で head が同じなら、`マージまで` は read-only の確認をして `done`、`マージ・デプロイ・QA まで` は手順 3 へ。OPEN なら自走せず 1 問で問う。CLOSED・head が違う・読めないときは止まる。手順 3〜5 は `マージ・デプロイ・QA まで` のときだけ
- `references/post-merge-qa.md` 手順 3〜5: `デプロイ:`（run がすべて success のときだけ）・`QA 結果:`・`revert PR:` の記録の行を決めた。再開では、これらを書いた後の中断なら QA や revert の PR を 2 回行わない。止まったデプロイや、high・blocking が残った QA 計画レビューの後の再開は、その手順からやり直す
- `references/post-merge-qa.md` § 宣言: `GDD QA Write Targets` に、アカウント ID を含む ARN と絶対パスを書かない（記録が steering の書き込み検査に止められる）
- `references/post-merge-qa.md` 手順 2: merge gate の拒否で待つのは、reason code が `review-wait-not-elapsed` だけのとき。`マージ前` の行にアカウント ID を含む ARN と絶対パスを書かない
- `references/post-merge-qa.md` § 限界: 利用者の規則と例外の行の食い違いを誰も確かめないことを書いた
- `references/human-check-template.md`・`references/human-check-template-compact.md`: 最大到達点に、`マージまで` 以上ならマージで動く CD と環境（本番なら本番）を、`マージ・デプロイ・QA まで` なら QA の書き込み先を並べ、承認が緩む条件をマージと QA の書き込みで分けて書いた
- `references/operation-levels.md`: 例外の行だけは `~/.gdd/config.local.md` から読むことを書いた
- `agents/gdd-qa-runner.md`: prompt に書かれるのは、記録した `GDD QA *` の行とした

#### Affected Files

- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/operation-levels.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/agents/gdd-qa-runner.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_hook_evidence_parsing.py`（`Merge Approval` のひな形を merge gate の parser に通す。ひな形は変えていない）
- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
