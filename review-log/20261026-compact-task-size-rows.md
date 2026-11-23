---
lane: L1
pr: 580
follow_up_of: 576
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2a4771df846d6a25730bdbab5112cf7b7b040747 | 0 | 0 | 0 | 2026-10-26T11:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | aafd108b5be0ae32a9f2c014da99e78d028cd986 | 0 | 0 | 0 | 2026-10-26T12:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| c1-1 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認済み（2026-10-26、推奨の案）: 依頼は「行」が compact に無いことを挙げるが、差分は独立した行を足さず、現在地の 1 行目の末尾に 3 つの欄をつないだ。Opus・Fable の推奨（独立した 1 行）で直した（commit: 73aedd28） |
| c1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 列挙: 3 つの欄の値の書式と出典（full の § やること・§ 通過予定 gate 数の置換値・brainstorming-steps 18）を compact が指さず、「値は full と同じ」もどの規定にも無い |
| c1-3 | 独立-1 | low | no | inherited | doc-claim | accepted | quick (standard) のフローの値（設計レビュー・タスク分割なし）と通過予定 gate 数（design-gate あり）・task-sizing.md・運用レベルの表が食い違い、それが一次表示の 1 行に並ぶ（origin: pre-existing） |
| c1-4 | 独立-1 | low | no | self-inflicted | changelog | accepted | 変更断片の Summary は「1 行を足した」と書くが、差分は既存の行に欄をつないだ。かぎ括弧の文が原文の引用でない（c1-1 の修正で Summary は事実に合い、引用も直した。commit: 73aedd28） |
| c1-5 | 独立-1 | advisory | no | self-inflicted | changelog | accepted | 変更断片の Changed が、§ Primary Surface Budget・§ Option Completeness の文の削除を挙げていない |
| c1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「相殺」は事実と違い、推定トークンは差し引き +2。PR 本文を直す（commit: なし（PR 本文）） |
| c1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「数値は再掲しない」は Template と重ならず、test が守る規定。PR 本文の根拠を直す（commit: なし（PR 本文）） |
| c1-8 | 独立-1 | advisory | no | inherited | product | accepted | 置換値の gate 名（req-gate など内部の名前）が、説明なしで一次表示に出るようになる（origin: pre-existing） |
| c2-1 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | 列挙: 足した行のフロー・通過予定 gate 数に書式も値の出どころも無く、compact だけを読む書き手が full と違う形の値を書ける（c1-2 の再掲） |
| c2-2 | 独立-2 | low | no | self-inflicted | changelog | accepted | 変更断片の Changed が、§ Option Completeness の文の削除も「行数の予算のため」と書くが、行数は変わらずトークンの予算のためである |
| c2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | § Primary Surface Budget を冒頭へ移すときに「数値は再掲しない」の句が落ち、full の同じ規定と文がそろわない（契約テストは検査を続けている） |
| c2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | evals の scenario hitl-decision-packet-ac2-where-compact の must_preserve が「Primary Surface Budget」の語で compact の節を指すが、その節を畳んだので compact に語が無くなった |
| c2-5 | 独立-2 | advisory | no | inherited | doc-claim | accepted | references/ の合計行数がマージ後は上限より 3 行少なくなり、skill-body-budget.sh のコメント「余裕は 0」と合わない |
| c2-6 | 独立-2 | advisory | no | inherited | doc-claim | accepted | brainstorming-steps.md 18 の指し先が full だけで、compact の現在地の行を指していない（origin: pre-existing） |
