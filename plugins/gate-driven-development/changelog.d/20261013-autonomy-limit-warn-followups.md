---
type: patch
---

#### Summary

steering の書き込み hook が自走上限について返す注記（`hooks/scripts/lib/autonomy_value.py`）の、残っていた食い違いを直した。

- 自走上限がマージの値なのに evidence が `human:` で始まらないときの注記は、これまで「`human:<読んだままの自走上限>` にします」と示していた。自走上限が表の外の値（`マージ・検証まで（…）` など）でも、その値をそのまま写すよう示していた。今後、値を示すのは自走上限が表の値のときだけにする。表の外の値なら、自走上限を表の値に直したうえで `human:<直した値>` にするよう示す
- `human:` で始まらない evidence の注記で承認前として除く `pending`・`changes_requested` の理由を正す。正しい理由は、承認前の evidence が `human:` でないのが正規の形だから、である（`pending` に戻すときは `none`、`changes_requested` では review run の id など。`references/gate-status-schema.md`）。同じ版の `20261013-autonomy-limit-warn-and-advisor-launch.md` の「`evidence: none` が正規の形なので除く」は `changes_requested` では成り立たない（挙動は変えていない）
- 自走上限と `human:` の evidence の値が、注記の無い `PR マージ後検証 / 再学習まで`（自走のマージを許さない表の値）か、`マージ` を含まない値だけのときは、行の数・形と不一致の注記を返さないようにした。注記を付けた `PR マージ後検証 / 再学習まで` には、今までどおり知らせる
- 表の外の「マージ…」の値の注記から「どちらとも決められないときも `PR 作成まで`」を外した。`references/human-check-template.md` § 事前回答 5 は、当てはめられない発話を引き上げない
- 同じ注記の範囲を書く `references/human-check-template.md` § 事前回答 2・`scripts/lint-approved-direction.py` の docstring・`references/rollback-patterns.md`・`skills/gdd-systematic-debugging/SKILL.md` を、`post-merge-qa.md` § 入口と手順 2 の形を満たさない理由、という書き方にそろえた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_value.py`・`scripts/lint-approved-direction.py`（docstring）
- `plugins/gate-driven-development/references/human-check-template.md`・`references/rollback-patterns.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_autonomy_value_notes.py plugins/gate-driven-development/tests/test_pre_answer_contract.py -q`
