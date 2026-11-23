---
lane: L1
pr: 640
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e4d932ea6a7f79af62364f496dbe0eb32a310f02 | 0 | 3 | 0 | 2026-11-06 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 2dee09f82fb1ddbbeee8900cb2eaae6ac0322128 | 0 | 4 | 0 | 2026-11-08 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | rule-copy | accepted | 狭い側を数値の理由で既定にしてよいとする規定が、human-check-template・compact・lint・brainstorming-steps・rollback-patterns・root CLAUDE.md の方針メモに残り、新しい出口と食い違う |
| I1-2 | 独立-1 | medium | no | self-inflicted | rule-copy | accepted | 同じファイルの § 選ぶときの基準 1（と相談役 3 本の写し）が、数値の理由があれば狭い案を推してよいと書いたままで、§ scope の「推奨・既定にしない」と食い違う |
| I1-3 | 独立-1 | medium | no | self-inflicted | limit-condition | accepted | 限界に `依頼より狭い` を書く条件が「縮めたら」から「選択肢に並べたら」に変わり、採らなかった狭い案が限界に載り、ユーザーが自分で狭めたときは載らなくなる |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 相談役への相談が必須の出口から「迷うとき」に下がったことと、限界を書く条件の変化が、断片と PR 本文に書かれていない |
| I1-5 | 独立-1 | low | no | self-inflicted | rule-timing | accepted | 前の「進める前に…どちらもせずに縮めない」が消え、前提を変えた案をいつ誰に示すか、「迷うとき」の条件が観測できない |
| I1-6 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の Validation 欄が「なし（…PR 本文に書いた）」で、再生での比較を検証の種類として書いていない |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の数値がどの版の文で測ったものか、根拠の場所が書かれていない |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 限界の「ユーザーの指示でこの文を入れる」を、決めたことの形に書き換える |
| I1-9 | 独立-1 | advisory | no | self-inflicted | style | accepted | Why の順が、縮める側の新しい経緯・広げる側・縮める側の古い経緯と交互になっている |
| I2-1 | 独立-2 | medium | no | inherited | rule-copy | fixed | root CLAUDE.md の L1+ 方針メモに「狭い側を既定にできるのは数値として示せた場合だけ」が残る。ユーザーの決定（2026-11-09「推奨どおり」）で基準 1 と同じ考え方の文に替えた。commit: 5bcb0427 |
| I2-2 | 独立-2 | medium | no | self-inflicted | limit-condition | fixed | 承認された案にあった「限界の `依頼より狭い` に判断ポイントかユーザーの決定の場所を添える」が入っていない。commit: 7578a507 |
| I2-3 | 独立-2 | medium | no | inherited | rule-copy | fixed | post-completion-pr-flow の事前回答の委任先が採れる案に「AC を削らないスコープ縮小」が残り、改名した 4 択と食い違う。commit: 7578a507 |
| I2-4 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | human-check-template の「8 要素」が、2 欄を外した後も 8 のまま |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 承認された案の `既定範囲` の 3 値化と `前提の問題:` の必須を入れていない。ユーザーの決定（2026-11-09「推奨どおり」）で、欄の撤去のままにする |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | compact の無回答時のデフォルトに「ユーザーが決めた範囲」の除外が無く、full と基準 1 より狭く読める |
| I2-7 | 独立-2 | low | no | self-inflicted | product | accepted | 方式転換の「依頼の範囲を変えるかを人に問う」を選んだ後に何を書き、どこへ戻るかが書かれていない |
| I2-8 | 独立-2 | low | no | self-inflicted | style | accepted | phase-progression の 3 案の切れ目が読めない |
| I2-9 | 独立-2 | low | no | self-inflicted | test-power | accepted | 範囲の欄の文の不在を見る assert が常に真で、撤去した検査を戻しても落ちるテストが無い |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | テストの docstring が撤去した値域の検査を前提にしたまま |
| I2-11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「検査が 1 つ減る」「lint は落とさない」が不正確（外したのは 3 つ。`誤検知実測=` は根拠の母集団の検査に今も当たる） |
| I2-12 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の再生の数値の出典が抜粋の中に無い |
| I2-13 | 独立-2 | advisory | no | inherited | product | accepted | pr-review-followup の選択肢 (2) スコープ縮小は medium を後続に回す後回しで、改名した 4 択と同じ名前が同じ表に残る |
| I2-14 | 独立-2 | advisory | no | inherited | doc-claim | accepted | brainstorming の Pre-option Scope Narrowing の keep が、AI が先に狭める既定とも読める |
