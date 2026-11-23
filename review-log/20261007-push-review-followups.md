---
lane: L1
pr: 401
follow_up_of: 400
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f882501ebb27d73935fd129e1491d061db980e6d | 0 | 1 | 0 | 2026-10-07T13:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6057edc9676d5131674f12f47ab562054eb2a171 | 0 | 1 | 0 | 2026-10-07T14:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| R1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | 起動応答が読めない background の reviewer が、完了の通知の後も reviewer-incomplete のまま。通知の tool-use-id で判定する。commit: 6057edc9 |
| R1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の起動応答の記述が実装と合わない。commit: 6057edc9 |
| R1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | push review の宣言の読み方が autonomy.md の読み方と違うことが書かれていない。operation-levels.md と断片に書いた。commit: 6057edc9 |
| R1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | _exempt_paths の docstring の保証が実装より広い（details などを区別しない）。commit: 6057edc9 |
| R1-5 | 独立-1 | low | no | self-inflicted | test-power | fixed | pushurl と url の優先を固定するテストが無い。commit: 6057edc9 |
| R1-6 | 独立-1 | low | no | self-inflicted | test-power | fixed | not-installed の session の値を固定していない。commit: 6057edc9 |
| R1-7 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | ref ごとの error の行に repo と branch が無い。commit: 6057edc9 |
| R1-8 | 独立-1 | low | no | self-inflicted | product | fixed | UTF-8 でない gh の出力が gh-unknown でなく error になる。commit: 6057edc9 |
| R1-9 | 独立-1 | low | no | self-inflicted | product | fixed | UTF-8 でない .gdd-config.md が error になる。commit: 6057edc9 |
| R1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | SECURITY.md の not-installed の記述が compact の扱いに追随していない。commit: 6057edc9 |
| R1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の判定の外の例外の記述が広い（script の読み込みの失敗を含まない）。commit: 6057edc9 |
| R1-12 | 独立-1 | low | no | self-inflicted | product | fixed | pushurl があるのに url で GitHub と判定する。commit: 6057edc9 |
| R1-13 | 独立-1 | advisory | no | self-inflicted | product | accepted | ref 名が 1 本でも UTF-8 でないと、同じ push のほかの ref の判定も消える。PR 本文に列挙 |
| R1-14 | 独立-1 | advisory | no | self-inflicted | product | accepted | not-installed の行は compact だけを抑え、resume では重複しうる。PR 本文に列挙 |
| R1-15 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | docstring の reviewer-incomplete に、通知の無い background の起動を含むことを書く。commit: 6057edc9 |
| R2-1 | 独立-2 | medium | no | self-inflicted | product | accepted | UTF-8 でない .gdd-config.md でも、宣言の行が ASCII なら宣言が読まれる。断片の記述を実装に合わせ、PR 本文の限界に書いた |
| R2-2 | 独立-2 | low | no | self-inflicted | test-power | accepted | test_pushurl_wins_over_url は pushurl があれば url を見ない変更を判別しない（判別は別のテストが担う）。PR 本文の限界に書いた |
| R2-3 | 独立-2 | low | no | self-inflicted | test-power | accepted | 読めない起動応答のテストが、別の dispatch の completed の通知で reviewed にならないことを固定していない。PR 本文の限界に書いた |
| R2-4 | 独立-2 | low | no | self-inflicted | product | accepted | pushurl が複数あると、GitHub でない URL への push も GitHub として記録する。PR 本文の限界に書いた |
| R2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | operation-levels.md に、宣言が 2 行以上あると読まない条件が無い。PR 本文の限界に書いた |
| R2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | UTF-8 でない出力の扱いが locale に左右される（encoding 未指定）。PR 本文の限界に書いた |
| R2-7 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | ref ごとの error 行の repo・branch にテストと説明が無い。PR 本文に列挙 |
| R2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 断片に SessionStart の not-installed の条件の修正が書かれていない。commit: cd832fdf |
