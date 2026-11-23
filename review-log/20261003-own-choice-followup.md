---
lane: L1
pr: 338
follow_up_of: 267
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 67a9564a64d5bd3107626c9e053492003a2131c3 | 0 | 4 | 0 | 2026-10-03T15:30+09:00 |
| 方針メモ | user（近道の巡で、この PR が足した文の medium 3 件を直すかをユーザーに確認した。規則では後続 PR の medium は accepted だが、直すのはユーザーの指示のときだけのため。回答: この PR で直す） | - | 0 | 0 | 0 | 2026-10-03T15:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c9eb9c64eca04b64fe65e3d2e3c6a00930b79cff | 0 | 0 | 0 | 2026-10-03T16:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | aca8bfb27a5eb06605736bc36c257c6ac158e23b | 0 | 0 | 0 | 2026-10-03T17:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（ユーザーの回答: この PR で直す） |
| R1 | 独立-1 | medium | no | self-inflicted | product | fixed | § 入口の値の読み方「`:` の後の文字列全体」が state field の文法と食い違い、4 部分の行・`=` の形で `approved` に一致しない。state-machine.md の文法（最初のパイプ区切りの前を trim）にそろえ、evidence の取り方も書いた commit: 63f5b019 |
| R2 | 独立-1 | medium | no | self-inflicted | product | fixed | `自走上限:` の数え方が狭く、全角コロン・`*`・括弧注記・`**` で書いた 2 行目を数えない。数える形を広げ、使うのは `- 自走上限: <値>` の形の 1 行だけにした commit: 63f5b019 |
| R3 | 独立-1 | medium | no | self-inflicted | product | fixed | completion-check に足した確かめ方の材料（worklog の承認の行）を既定の経路が書かない。編集を元に戻した（J4 は限界） commit: 63f5b019 |
| R4 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 狭める根拠の「根拠を要しない」例外が、同じファイルの受理文法と lint の両方に拒否される。例外の文を消した（compact の既定範囲の注記は残す） commit: 63f5b019 |
| R5 | 独立-1 | low | no | inherited | test-power | accepted | lint-approved-direction.py の自走上限の読み方（最初の 1 行、行数を数えない）が新しい正本と違う（warn-only）。PR 本文の限界に書く |
| R6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が、compact に書いていない例外を書いたとしている commit: c9eb9c64 |
| R7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が `<approval-id>` の削除を書いていない commit: c9eb9c64 |
| R8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | § 限界の同じ行の前半「steering の書き込み検査が止める」に Bash の除外が無い commit: 63f5b019 |
| R9 | 独立-1 | low | no | inherited | doc-claim | accepted | phase-progression.md:31 も書き込み検査が Edit・Write だけを見ることを書いていない。PR 本文の限界に書く |
| R10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | STEP 2 の evidence の書き分けに事前回答の適用が無く、code span の中のバッククォートで span が切れる commit: 63f5b019 |
| R11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | gate-status-schema の evidence の例から approval id を除き、Human Check Status の changes_requested に当てはまる形が無くなった commit: 63f5b019 |
| R12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | § 入口の条件（Approved Direction の自走上限）と読み方（state.md 全体）で読む範囲が違う。条件から読み方を指した commit: 63f5b019 |
| R13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence の有無を確かめる。PR 本文に節を書く |
| S1 | 独立-2 | low | no | self-inflicted | product | accepted | lint-approved-direction.py の読み方（行末までを値にする・数えない形も受理する）が新しい正本とずれ、WARN が実際と逆になりうる（warn-only）。PR 本文の限界に書く |
| S2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「state-machine.md のとおり」と書いた値の区切りが空白付きのパイプで、文法の縦棒と一致しない（受理は狭い側）。PR 本文の限界に書く |
| S3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「2 行以上なら 1 問で問う」は実際には文書に入らず PR 作成で done になる。PR 本文の限界に書く |
| S4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片が数える形と使う形を混ぜ、数える形からバッククォートが漏れる。PR 本文の限界に書く |
| S5 | 独立-2 | low | no | self-inflicted | product | accepted | 数える形が列挙で、番号付き・引用・見出しなどの形を数えない。Human Check Status は前方一致より狭くなった（発火には古い行を残す別の事故が要る。入力者: 未測）。PR 本文の限界に書く |
| S6 | 独立-2 | low | no | inherited | product | accepted | 戻した completion-check の整合の判定は、書き直しの updated_at で誤って通る（main と同じ文）。PR 本文の限界に書く |
| S7 | 独立-2 | low | no | inherited | doc-claim | accepted | 自走上限の判断ポイントで「既定にしない」と「狭い側なら数値必須」が両立しない（main と同じ文。lint は Stop hook に配線されていない）。PR 本文の限界に書く |
| S8 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 「本人の差し戻しの approval id」が定義されておらず、design reopen の id も列挙に無い。PR 本文に列挙 |
| S9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 使う形 `- 自走上限: <値>` に先頭の空白を許すかが書かれていない（どちらに読んでも自走しない側）。PR 本文に列挙 |
| S10 | 独立-2 | advisory | no | inherited | doc-claim | accepted | Approved Direction が上書きか累積かが文書間で食い違い、累積なら再承認で自走上限が 2 行になる。PR 本文に列挙 |
| S11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 条件は Approved Direction の自走上限だが、読み方は state.md 全体を数える。PR 本文に列挙 |
| T1 | 独立-3 | low | no | inherited | doc-claim | accepted | compact の既定範囲の欄に「マージまで以上は既定にしない」の注記が無く、上位正本と書き方がずれる（compact は main と同じ。OKで進む範囲の欄に同じ規定がある）。PR 本文の限界に書く |
| T2 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 予算に収めたことの計測値が無い。PR 本文に express・standard の推定トークンを書く |
| T3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | STEP 2 の「OK の後に再度止まらない」が確認の停止に限らず読め、requirements-gating-steps.md の書き方とずれる（文脈からは承認直後の確認の停止）。PR 本文の限界に書く |
| T4 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | 断片の Summary が数える形のバッククォートと使う形の条件を書き落とす（S4 の再掲） |
