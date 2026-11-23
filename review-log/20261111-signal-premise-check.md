---
lane: L1
pr: 657
follow_up_of: 653
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 6a87c6c45242eef98cd1ce0f11f3d35adac53153 | 0 | 3 | 0 | 2026-11-11 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 825a0f7080cf7689b85c81ab4ca7edc0d375a3a2 | 0 | 2 | 0 | 2026-11-11 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 69b0dc0e6d0c20fa03df0d0cf1ff8e1a75a76007 | 0 | 3 | 0 | 2026-11-11 |
| 方針メモ-1 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-11-11 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 59e89b072fe7731185e38e1d3fc4ea7b6685993a | 0 | 1 | 0 | 2026-11-11 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | d59ba8c82aafd1a740f901d85593c45255445f55 | 0 | 2 | 0 | 2026-11-11 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | 範囲 | fixed | 設計: 変える（点検を契約 1 だけに置いた。§ 事前回答 3 の `上限到達:` 行の規定に置き、6 種の上限すべてに届ける）。依頼の「正式 gate の上限の一括提示」より狭く配線していた。commit: 825a0f7 |
| I1-2 | 独立-1 | medium | no | self-inflicted | 範囲 | accepted | 上限で止まる提示を写した別のファイル（runner の定義・rollback-patterns など）に点検の句が無い（写しはどれも § 事前回答 3 の `上限到達:` の手順を参照する） |
| I1-3 | 独立-1 | medium | no | self-inflicted | 記録 | fixed | PR 本文に印を読む時期と撤去する条件が無い。commit: なし（PR 本文） |
| I1-4 | 独立-1 | low | no | self-inflicted | 範囲 | fixed | state-machine の挿入位置で「ときだけ」「書かない」の限定が点検にかかって読める。I1-1 で文を消した。commit: 825a0f7 |
| I1-5 | 独立-1 | low | no | self-inflicted | 記録 | fixed | `ずれる` の案が 旧#641 の変える案に混ざり、分けて数えられない。行に `案:` の欄を足した。commit: 825a0f7 |
| I1-6 | 独立-1 | low | no | self-inflicted | 記録 | accepted | `前提の点検:` 行の形が、合う・原文なし・時間超過のときの書き方を決めていない |
| I1-7 | 独立-1 | low | no | self-inflicted | 軽いレーン | accepted | 軽いレーンで、点検の結果と相談役の推奨のどちらが先かが決まっていない |
| I1-8 | 独立-1 | low | no | self-inflicted | 軽いレーン | accepted | 軽いレーンの (b) の確かめ方（accepted と 確認待ち:）と、行き詰まりでは accepted にしない規定がぶつかる |
| I1-9 | 独立-1 | low | no | self-inflicted | 範囲 | fixed | 断片と PR 本文が適用範囲を実際より広く書いていた。I1-1 で配線し、断片を 6 種の列挙に直した。commit: 825a0f7 |
| I1-10 | 独立-1 | low | no | self-inflicted | 記録 | accepted | 断片の Validation / Eval Impact が CHANGELOG の Policy の形でない |
| I1-11 | 独立-1 | advisory | no | self-inflicted | 記録 | fixed | PR 本文の「足した分より多く消した」に物差しが無い。commit: なし（PR 本文） |
| I1-12 | 独立-1 | advisory | no | inherited | 範囲 | fixed | 委任中は、AC や依頼の読み方を変えない前提の変更でも人に戻る。依頼の「人に戻すのは AC か依頼の読み方が変わるときだけ」に合わせて § 事前回答 3 の条件を直した。commit: 825a0f7 |
| I1-13 | 独立-1 | advisory | no | self-inflicted | 記録 | accepted | 2 つのレーンで印の形が違う |
| I1-14 | 独立-1 | advisory | no | self-inflicted | 記録 | fixed | PR 本文の「損失の多くは」に数が無い。commit: なし（PR 本文） |
| I2-1 | 独立-2 | medium | no | self-inflicted | 範囲 | fixed | 設計: 変えない（人に戻す条件の一覧に、前提の変更で planning_rework_required に進むときの除外を 1 つ足す）。requirements・design の上限では、前提を変える案が planning_rework_required を通って人に戻り、依頼の「AC か依頼の読み方が変わるときだけ」に届いていなかった。commit: 69b0dc0 |
| I2-2 | 独立-2 | medium | no | self-inflicted | 範囲 | fixed | 依頼の「同じ指摘の繰り返し」に、方式転換に至らない繰り返しの合図（followup の Design Review Checkpoint、Approach Rethink、同じ root cause の再発）が入っていなかった。広い側で読み、3 か所に点検を足した。commit: 69b0dc0 |
| I2-3 | 独立-2 | low | no | self-inflicted | 記録 | fixed | 断片の「…ときだけにした」が、ほかの人に戻す条件を落として読める。I2-1 と同じ文を直した。commit: 69b0dc0 |
| I2-4 | 独立-2 | low | no | self-inflicted | 記録 | re-reported | `前提の点検:` の 1 欄目に、点検できない場面の値が無い（I1-6 の再掲） |
| I2-5 | 独立-2 | low | no | self-inflicted | 範囲 | accepted | 6 種のうち 4 種で、点検の指示が § 事前回答 3 の括弧の中にしか無い |
| I2-6 | 独立-2 | low | no | self-inflicted | 記録 | fixed | 物差しの「案: の案が採られた数」を、本人が答えた停止では何で数えるかが PR 本文に無い。commit: なし（PR 本文） |
| I2-7 | 独立-2 | advisory | no | self-inflicted | 記録 | accepted | 点検を載せる範囲の書き方が 2 か所で違い、AC の語が一覧の先頭と重なる |
| I3-1 | 独立-3 | medium | no | self-inflicted | 範囲 | accepted | 実行側の gdd-systematic-debugging の SKILL が、同じ規定を点検なしで書いている |
| I3-2 | 独立-3 | medium | no | self-inflicted | 範囲 | accepted | 一括提示の無い合図で、`ずれる` の結果が route・選択にどう効くかが決まっていない |
| I3-3 | 独立-3 | medium | no | self-inflicted | 範囲 | accepted | 決着（ユーザーが (b) を選んだ）: 委任中の `planning_rework_required` の除外は、依頼の「人に戻すのは…ときだけ」を既存の条件にも当てる読み。Opus 2 本とも、その読み (b) を推した。PR 本文の限界の節に問いを書く |
| I3-4 | 独立-3 | low | no | self-inflicted | 範囲 | fixed | 設計: 変える（発火点を 1 つずつ足す形をやめ、Bounce Log の正本と、2 回目以降の route の決定の 1 か所に寄せた。方針メモ-1 の推奨）。「同じ指摘の繰り返し」の Bounce Log に点検が載っていなかった。commit: 59e89b0 |
| I3-5 | 独立-3 | low | no | self-inflicted | 記録 | accepted | 同じ出来事で `前提の点検:` 行が重なり、合図の種類で区別できない |
| I3-6 | 独立-3 | low | no | self-inflicted | 記録 | fixed | 「High が減らない」でも点検が発火するのに、断片は root cause の再発だけを書いていた。2 回目以降の route の決定にまとめ、断片を直した。commit: 59e89b0 |
| I3-7 | 独立-3 | low | no | self-inflicted | 記録 | re-reported | request.md が無い・写せていない steering で点検の値が無い（I1-6 の再掲） |
| I3-8 | 独立-3 | advisory | no | self-inflicted | 記録 | fixed | 断片が、委任中に planning_rework_required へ人に見せずに進みうることを書いていなかった。commit: 59e89b0 |
| P1-1 | 方針メモ-1 | advisory | no | self-inflicted | 範囲 | accepted | 2 本とも、問い 1 は (b)、問い 2 は Bounce Log の正本と 2 回目以降の route の決定に寄せる案を推し、人に止めて聞く必要は無いと答えた |
| I4-1 | 独立-4 | medium | no | self-inflicted | 範囲 | fixed | 設計: 変える（点検の条件を counter ではなく、直前 blocker と同じ root cause かで決める）。`Gate Rounds` ≥ 2 にまとめたため、completion-check から同じ root cause で戻る経路が落ちていた。commit: d59ba8c |
| I4-2 | 独立-4 | medium | no | self-inflicted | 範囲 | re-reported | route を決める gdd-systematic-debugging の SKILL 本文に点検が無い（I3-1 の再掲） |
| I4-3 | 独立-4 | low | no | self-inflicted | 範囲 | fixed | `Gate Rounds` ≥ 2 は同じ指摘の繰り返しより広かった。I4-1 と同じ文で直した。commit: d59ba8c |
| I4-4 | 独立-4 | low | no | self-inflicted | 記録 | fixed | 重複した行を「同じ時刻」で 1 本に数えると PR 本文に書いたが、行に時刻の欄が無い。PR 本文を「重複は除けない」に直した。commit: なし（PR 本文） |
| I4-5 | 独立-4 | low | no | self-inflicted | 範囲 | re-reported | 一括提示の無い発火点で、`ずれる` のときに何をするかが決まっていない（I3-2 の再掲） |
| I4-6 | 独立-4 | low | no | self-inflicted | 記録 | accepted | Bounce Log の正本で、「出力を書く前に」の指示が出力テンプレートの後の節にある |
| I4-7 | 独立-4 | low | no | self-inflicted | 記録 | re-reported | 依頼の原文が無い steering で点検の値が書けない（I1-6 の再掲） |
| I4-8 | 独立-4 | low | no | self-inflicted | 記録 | accepted | followup の SKILL で、趣旨の違う 2 つの規定を 1 つの箇条にまとめた |
| I4-9 | 独立-4 | advisory | no | self-inflicted | 記録 | fixed | 発火点ごとの当たる件数が PR 本文に無い。commit: なし（PR 本文） |
| I5-1 | 独立-5 | medium | no | self-inflicted | 範囲 | fixed | 設計: 変える（新しい述語を作らず、既存の発火点 route recalibration と Approach Rethink の名前に結ぶ）。「直前と同じ root cause」は依頼の「同じ指摘の繰り返し」より狭かった。5/5 の hard cap は一括提示ではないので載せない。commit: 28ecd8c |
| I5-2 | 独立-5 | medium | no | inherited | 範囲 | fixed | route を決める gdd-systematic-debugging の SKILL 本文から点検に届かない。既存の行に state-machine への参照の句を足した。commit: 28ecd8c |
| I5-3 | 独立-5 | low | no | self-inflicted | 記録 | accepted | 「同じ root cause」の判定の元と、判定できないときの側が書かれていない |
| I5-4 | 独立-5 | low | no | self-inflicted | 記録 | accepted | build loop の発火条件に当たる件数が PR 本文に無い |
| I5-5 | 独立-5 | low | no | inherited | 範囲 | re-reported | 委任中の既存の人に戻す条件を緩めたのは、依頼の語を広げた読み（I3-3 の再掲。確認待ち） |
| I5-6 | 独立-5 | advisory | no | self-inflicted | 記録 | fixed | 528 行目の括弧で field 名のバッククォートがそろっていない。文を書き直して消えた。commit: 28ecd8c |
| I5-7 | 独立-5 | advisory | no | inherited | 記録 | accepted | `前提の点検:` 行に、どの合図で書いたかの欄が無い |
