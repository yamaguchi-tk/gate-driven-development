---
type: patch
---

#### Summary

steering の書き込み hook（`hooks/scripts/lib/autonomy_value.py`。`scripts/lint-approved-direction.py` も共有）が state.md の自走上限を知らせる範囲を広げた。これまでは、値が `マージまで`・`マージ・デプロイ・QA まで` で始まるときだけ見ていた。そのため `マージ・検証まで（…）` のような表の外の値では何も知らせず、`references/post-merge-qa.md` § 入口の完全一致を満たさないまま、マージ後の検証へ進まなかった。今後は次の 2 つも、書き込み後の additionalContext で知らせる。

- 値が `マージ` を含むのに § 自走上限の置換値の表の値でないとき。`docs-only PR はマージまで` のような値も知らせる。`PR マージ後検証 / 再学習まで` に注記を付けた値には、注記を worklog.md に移すこと、マージは 1 操作ごとの承認のままであることを知らせる
- 自走上限がマージの値なのに、`Human Check Status` の evidence が `human:` で始まらないとき（承認前の `pending`・`changes_requested` は、`evidence: none` が正規の形なので除く）

読む側（`post-merge-qa.md` の完全一致）は変えていない。括弧の注記や表の外の言い方を自走のマージに入れることはしない。注記には範囲を狭める条件や承認者の代わりが入る実例があるためである。`references/human-check-template.md` § 事前回答 5 の自走上限の引き上げに、「マージして検証まで」を表の値に当てはめる例を足した。

`agents/gdd-fable-advisor.md`・`gdd-opus-advisor.md` の起動の条件に、ユーザーが自分のターンで名指しで意見を求めたとき（「Fable の意見を聞きたい」など）を足した。役・read-only・`model` を渡さないことは変えていない。`gdd-opus-advisor-max` は費用が大きいので、規則が名指ししたときだけのままにした。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_value.py`・`scripts/lint-approved-direction.py`（docstring）
- `plugins/gate-driven-development/references/human-check-template.md`・`references/fixed-models.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`・`agents/gdd-opus-advisor.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_autonomy_value_notes.py plugins/gate-driven-development/tests/test_pre_answer_contract.py plugins/gate-driven-development/tests/test_advisor_agents.py -q`
