---
lane: L1+
pr: 267
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (Plan, model: opus)（memory の 2026-09-28 の決定で、ユーザーへの確認は内部の相談で代えた。Opus の推奨〔evidence は 1 行だけ・evidence がある・接頭辞で判定、書き直しで接頭辞を消さない、2 値を既定値・推奨値にしない、判定できない workflow は `不明`、限界に 3 点〕を採った。前の断片の書き換えだけは、未リリースの断片を通常の PR で直さない運用に従い、この断片の User Action Required で代えた。Fable は呼んでいない） | - | 0 | 0 | 0 | 2026-10-01T18:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5e036e4053ce7006ebd810a4899cbd2db540144d | 2 | 1 | 2 | 2026-10-01T19:05+09:00 |
| 方針メモ-2 | Fable アドバイザリ (Plan, model: fable)（独立-1 の high の直し方で、main の案〔肯定形 `human:<値>`〕と方針メモの Opus の推奨〔否定形〕が食い違ったため 1 回相談。Fable は肯定形を推奨し、採った） | - | 0 | 0 | 0 | 2026-10-01T19:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 828b1d12ad38f30daeaefca85a9d6292a6c698cd | 0 | 1 | 0 | 2026-10-01T19:55+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 06e0db53b5db0f8c991fa7b82d4a4edcc6819fd2 | 0 | 0 | 0 | 2026-10-01T20:25+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| G1 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | 本人の承認の判定が否定形（autonomy:・auto-confirm: で始まらなければ本人）で、形の決まっていない evidence・節の外の行・自走上限だけの書き換えを通す。human:<自走上限の値> と自走上限の完全一致の肯定形にした commit: 828b1d12 |
| G2 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | 接頭辞を消さない規定が、evidence を書き直す 4 か所（design-gating・task-breakdown・rollback-patterns）のひな形に入っていない。ひな形を <元の evidence> にした commit: 828b1d12 |
| G3 | 独立-1 | medium | no | self-inflicted | product | fixed | compact テンプレートと承認ポイントの「既定は広い側」に、2 値を既定にしない・判定できなければ 不明 が入っていない commit: 828b1d12 |
| G4 | 独立-1 | low | no | self-inflicted | product | fixed | 判定が ## Gate Status の節だけを数え、ひな形の state.md では満たせない。state.md 全体にした commit: 828b1d12 |
| G5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 同じ版の未リリース断片に古い記述が例外の行以外にも残る。PR 本文の限界に file:line で並べた commit: なし（PR 本文） |
| G6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | User Action が利用者の規則を条件のように書くが手順は読まない。限界と User Action を直した commit: 828b1d12 |
| G7 | 独立-1 | low | no | self-inflicted | product | fixed | 変更前に承認された進行中の steering も問わずにマージする。human: の肯定形で問う側に倒れ、User Action に書いた commit: 828b1d12 |
| G8 | 独立-1 | advisory | no | self-inflicted | product | accepted | repo の側から自走のマージを禁じる宣言が無い。限界に branch protection を書いた（宣言は設けない） |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| H1 | 独立-2 | medium | no | self-inflicted | product | fixed | design-gating 手順 8 の書き直しのひな形が <approval-id> のままで、標準の経路で human: が消える（独立-1 の G2 の直し残し） commit: 06e0db53 |
| H2 | 独立-2 | low | no | self-inflicted | product | next-pr | 比べる相手の Approved Direction の 自走上限 の行数が決まっておらず、§ 入口と手順 2 が別の行を読みうる |
| H3 | 独立-2 | low | no | self-inflicted | product | next-pr | 完全一致と「1 行だけ」が前提にする入力の形（注記付きの自走上限の値、フィールドの行の定義）が決まっていない |
| H4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | gate-status-schema の approved 遷移時の evidence の例が <approval-id> のまま |
| H5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | STEP 2 と共通の承認後処理が evidence を無条件に human: と書き、判断役の承認でも同じ手順を使う autonomy.md と食い違う |
| H6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | § 限界の「peer turn の書き込み検査が止める」が Bash での書き込みを含まず、実装の保証より広い |
| H7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 既定範囲の例外が、対になる「狭める根拠」の規定と lint・compact の既定範囲の行に入っていない |
| H8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | evidence が記録するのは置かれた値への承認で、本人がその値を選んだことではない（PR 本文の advisory に書いた） |
| J1 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋の「標準のトークン予算に収めるため。意味は変えていない」）。PR 本文から除いた |
| J2 | 独立-3 | low | no | inherited | doc-claim | next-pr | gate-status-schema の approved 遷移時の evidence の例 <approval-id> が、24 行の規定とずれたまま 1 か所だけ残る |
| J3 | 独立-3 | low | no | inherited | doc-claim | next-pr | § 限界の「human: の evidence を書くのは本人のターンの承認の記録だけ」が、書き直しで写す規定とぶつかる（新しく書くのは、に直す） |
| J4 | 独立-3 | low | no | inherited | doc-claim | next-pr | completion-check が human check を通ったかを、書き直しでも変わる updated_at で見ている |
| J5 | 独立-3 | advisory | no | inherited | doc-claim | accepted | Express から standard への昇格で human check を取り直すかの規定が食い違い、自走上限の引き継ぎが決まらない（PR 本文の限界に書いた） |
| J6 | 独立-3 | advisory | no | inherited | doc-claim | accepted | design-gating 手順 8 は元の値が approved でなくても approved を書く（差分の前からの形） |
