---
type: patch
---

#### Summary

- 後続 Stage に判断の委任の行を写すときの自走上限を、行の値と元の steering の今の自走上限の狭い方で決めるようにした。狭い方は置換値の包含（`実装完了まで` ⊂ ほかの値、`PR 作成まで` ⊂ `PR 作成 + 外部レビュー収束まで`・`マージまで`、`マージまで` ⊂ `マージ・デプロイ・QA まで`）だけで決め、比べられない組と読めないときは `PR 作成まで`（どちらかが `実装完了まで` なら `実装完了まで`）にする。`20261015-limit-row-and-raise-fix` の断片にある「引き上げの記録だけで説明できるか」で決める写し方は、これに置き換わった。履歴で決めていたときは、記録の無い引き下げの後に引き上げると、本人が下げた値より上の値が写ることがあった

#### Affected Files

- `references/human-check-template.md`（§ 事前回答 4）

#### User Action Required

なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
