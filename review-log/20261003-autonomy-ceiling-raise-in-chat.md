---
lane: L1
pr: 341
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (Plan, model: opus) + Fable (信号 ①, model: fable) + user | - | 0 | 0 | 0 | 2026-10-03T01:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d47734f25feacd3a53a9b6754df8b7f416ee8cb8 | 1 | 1 | 2 | 2026-10-03T02:05+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | aafa4ecd8443f1061d641ec8c7a4e3f566f436e9 | 1 | 1 | 2 | 2026-10-03T02:40+09:00 |
| 方針メモ-1 | Opus 設計レビュー (Plan, model: opus) | - | 0 | 0 | 0 | 2026-10-03T02:55+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 3ace2cc1bd4d5790a6f8a124fd6ef6e1fc807574 | 3 | 2 | 5 | 2026-10-03T03:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | advisory | no | inherited | autonomy-ceiling-raise | fixed | 承認済みの自走上限を会話で引き上げる経路が規則に無く、マージ待ちで止まる主因だった。user が「会話の発話で直接引き上げる」を選んだ。commit: (本 PR) |
| pm-2 | 方針メモ | advisory | no | inherited | autonomy-ceiling-value | fixed | 自走上限の値が注記つきで post-merge-qa 手順 2 の完全一致に当たらない（実測 7/7）。表の値だけを書く規定を足した。commit: (本 PR) |
| J1 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | 5 の例「マージしたら次に進んで」など、誰がマージするか読めない発話で自走上限がマージの値に上がり、Merge Approval を問わずにマージに進む。エージェントにマージさせる指示・許可のときだけ上げ、読めなければマージ時に Merge Approval を問う形にした。commit: aafa4ecd8443f1061d641ec8c7a4e3f566f436e9 |
| J2 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 引き上げを `事前回答:` 行で書くので、本人が答えていない以後の human check と後続 Stage の human check の表示まで省く。引き上げ・着手・委任を分け、`事前回答:` 行は委任のときだけにした。commit: aafa4ecd8443f1061d641ec8c7a4e3f566f436e9 |
| J3 | 独立-1 | medium | no | self-inflicted | autonomy-ceiling-value | next-pr | 同じファイルの具体例（:626・:691）が、注記つきの自走上限のまま |
| J4 | 独立-1 | medium | no | self-inflicted | approval-path | next-pr | 5 の例が 2 の照合規則（欄が原文から読めること）を通らない |
| J5 | 独立-1 | medium | no | self-inflicted | routing | next-pr | phase-progression.md と gdd-using-skills の承認後の follow-up の振り分けに、5 への入口が無い |
| J6 | 独立-1 | low | no | self-inflicted | bookkeeping | next-pr | 5 の記録の形が 1・2 の定義（対象の択一、適用の値の 2 つ）と合わない |
| J7 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 3 の「適用中に本人から新しい入力を受けた」と 5 の優先が決まっていない |
| J8 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | gate-status-schema.md:24 の evidence を写す規定に、5 の書き換えの例外が無い |
| J9 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | post-merge-qa.md § 限界の `human:` を書く場面の列挙に 5 が無い |
| J10 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 着手を許した Stage の Human Recheck・Approval Scope の記録値を書き換えるかが書かれていない |
| J11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary が発話ごとの効果を取り違えている。J1・J2 の修正で書き直した。commit: aafa4ecd8443f1061d641ec8c7a4e3f566f436e9 |
| J12 | 独立-1 | low | no | self-inflicted | product | next-pr | done で止まった後に引き上げたとき、post-merge-qa のどこから続けるかが書かれていない |
| J13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence を巡で確かめていない。PR 本文に列挙 |
| J14 | 独立-1 | advisory | no | self-inflicted | product | accepted | evidence と自走上限を別々の Edit で書くと lint の WARN が出る。1 回の書き込みと J1 の修正で書いた。PR 本文に列挙 |
| J15 | 独立-1 | advisory | no | inherited | doc-claim | accepted | lint が注記を検査するのはマージの 2 値だけ。PR 本文に列挙 |
| J16 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 限界が指す Stop hook の文言は systemMessage 側にある。PR 本文に列挙 |
| K1 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | 条件付きの許可（「明日の朝マージして」「A さんが approve したらマージして」）を条件の無い自走上限に変え、Merge Approval を省く。閉じ方: 列挙。方針メモ-1 で Opus の推奨（経路が確かめる条件だけ引き上げる）を採り、暗黙の条件は限界に書いた。commit: 3ace2cc1bd4d5790a6f8a124fd6ef6e1fc807574 |
| K2 | 独立-2 | medium | yes | inherited | approval-path | fixed | 承認の後に許可を取り消す・下げる発話を state.md に反映する規定が無い。閉じ方: 列挙。方針メモ-1 で Opus の推奨（引き下げ・取り消しの項）を採り、下げる語を含まない保留は限界に書いた。commit: 3ace2cc1bd4d5790a6f8a124fd6ef6e1fc807574 |
| K3 | 独立-2 | medium | no | self-inflicted | approval-path | next-pr | 委任の行は 1・2 の条件（自走上限の欄が原文から読める）を満たさず適用されない（止める側） |
| K4 | 独立-2 | medium | no | self-inflicted | approval-path | next-pr | 着手と委任を同じ発話で受けても、新しい steering の human check を 2 で扱えない（止める側） |
| K5 | 独立-2 | medium | no | self-inflicted | approval-path | next-pr | 括弧書きを削ったため、既存の `事前回答:` 行が引き上げを元に戻す（止める側） |
| K6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 後続 Stage の例外を列挙する phase-progression ほか 4 か所が、5 の着手と委任の経路を含まない |
| K7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | post-merge-qa.md § 限界の `human:` の書き手の列挙に、引き上げの記録が無い |
| K8 | 独立-2 | low | no | inherited | doc-claim | re-reported | gate-status-schema.md:24 の evidence を写す規定と食い違う（J8 と同じ） |
| K9 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | 後続 Stage の着手の合図を、受けた時点で原文つきで記録しない |
| K10 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 断片の Summary が引き上げ先と例外を言い過ぎている |
| K11 | 独立-2 | advisory | no | self-inflicted | style | accepted | 「1 回の書き込みで」が 5 にだけある。PR 本文に列挙 |
| K12 | 独立-2 | advisory | no | self-inflicted | style | accepted | 5 の見出しが中身より狭い。PR 本文に列挙 |
| K13 | 独立-2 | advisory | no | inherited | doc-claim | accepted | Stop hook の継続の案内と食い違う（限界に開示済み）。PR 本文に列挙 |
| K14 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に、引き上げない条件と原文の確かめが無い。commit: なし（PR 本文） |
| pm1-1 | 方針メモ-1 | advisory | no | self-inflicted | approval-path | fixed | K1・K2 の閉じ方: 列挙 について、実測（マージに触れた本人の発話 681 件中、経路が確かめない条件 1 件・取り消し 0 件）を添えて Opus に相談し、散文の修正と限界の開示を推奨された。commit: 3ace2cc1bd4d5790a6f8a124fd6ef6e1fc807574 |
| F1 | 独立-3 | high | yes | self-inflicted | approval-path | accepted | 引き下げが事前回答の行と後続 Stage への写しに効かず、次の human check・次の Stage で自走上限が戻る。閉じ方: 列挙。巡の上限で限界の先頭に書いた |
| F2 | 独立-3 | high | yes | self-inflicted | approval-path | accepted | 引き下げが記録済みの自走の Merge Approval を消さず、待機明けに merge gate を通る。閉じ方: 列挙。巡の上限で限界の先頭に書いた |
| F3 | 独立-3 | high | yes | self-inflicted | fail-open | accepted | 下げた後の値が変更前の値で縛られず、デプロイを外してもマージで CD が出て、広がることもある（照合なしの書き込み）。閉じ方: 列挙。巡の上限で限界の先頭に書いた |
| F4 | 独立-3 | medium | yes | self-inflicted | approval-path | accepted | 「CI が通る」「指摘が無い」が、経路が確かめる範囲（required checks・未解決の actionable な指摘）より広い。閉じ方: 列挙。限界の先頭に書いた |
| F5 | 独立-3 | medium | yes | inherited | approval-path | accepted | 同じ入力を読む 1（事前回答の記録）に、条件つき許可の扱いが無い。閉じ方: 列挙。限界の先頭に書いた |
| L1 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 変更断片に、引き下げ・取り消しと条件つき許可の扱いが無い |
| L2 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | `human:` の evidence の書き手の列挙に 5 が無い（J9・K7 と同じ） |
| L3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が、Stop hook との食い違いを引き上げの分しか書いていない。commit: なし（PR 本文） |
| L4 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | 5 の見出しと正本の宣言が「引き上げ」のまま（K12 と同じ） |
| L5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋が、差分に無い既定（暗黙の条件は引き上げる）を挙動として書いている。commit: なし（PR 本文） |
