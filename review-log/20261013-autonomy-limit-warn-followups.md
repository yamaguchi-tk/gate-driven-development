---
lane: L1+
pr: 460
follow_up_of: 453
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d5e172c3 | 0 | 1 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e6a71597 | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | product | accepted | 依頼 7 行目の断片の誤った理由を直さず、この PR の断片で代えていた。PR 旧#453 の断片を直すと version-not-consumed の層 B が FAIL にするので戻し、この PR の断片に正しい理由と、前の断片の文が成り立たないことを書いた。前の断片の文はリリースの dry-run で直す（memory release-time-stale-fragment-fixes に足す） |
| I1-2 | 独立-1 | low | no | self-inflicted | product | fixed | test_pre_answer_contract.py の docstring の前半が古い入口のままだった commit: 92378bbc |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「注記の無い PR マージ後検証では行の数・形の注記を返さない」が広すぎ、不一致の注記も返さなくなったことを書いていなかった commit: 92378bbc |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | この PR の断片が、差分が変えていない承認前の除外を書いていた。行を消した commit: 92378bbc |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | § 事前回答 2 の括弧が hook の範囲より広く、「承認後の evidence」が承認前でない status と範囲が違った commit: 92378bbc |
| I1-6 | 独立-1 | low | no | self-inflicted | test-power | fixed | 表の値のときだけ値を示すテストが、注記付きの表の値を当てていなかった commit: 92378bbc |
| I1-7 | 独立-1 | low | no | self-inflicted | test-power | fixed | 注記付きの PR マージ後検証の hook の入口のテストが、evidence の human:マージまで で入口が開いて通っていた commit: 92378bbc |
| I1-8 | 独立-1 | low | no | self-inflicted | test-power | fixed | _BEFORE_APPROVAL を state-schema.json の Human Check Status の allowed と突き合わせるテストが無かった commit: 92378bbc |
| I1-9 | 独立-1 | low | no | inherited | doc-claim | fixed | lint-approved-direction.py の docstring に、警告する入口と evidence を見る条件が無かった commit: 92378bbc |
| I1-10 | 独立-1 | low | no | inherited | product | accepted | 列挙: PR マージ後検証/再学習まで のような表の値の言い換えに、表の外の注記が マージまで への当てはめを示す。言い換えは開いた入力なので限界に書く |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | § 事前回答 2 の括弧が、evidence を見るのは自走上限が自走のマージを指しうる値のときだけ、という限定を欠き、注記付きの PR マージ後検証を「自走のマージを指しうる」に入れて読める |
| I2-2 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files に scripts/lint-approved-direction.py（docstring）が無い commit: df573b26 |
| I2-3 | 独立-2 | low | no | inherited | doc-claim | accepted | autonomy_value.py の module docstring に、注記を見る入口の限定が無い |
