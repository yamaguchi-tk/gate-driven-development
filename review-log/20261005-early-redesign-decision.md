---
lane: L1
pr: 377
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 08d004ed8df785753d6eff948cdbb2420e5d3c31 | 0 | 0 | 0 | 2026-10-05T03:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | product | next-pr | design_detail_only で tasklist を作り直すと上限の数えが途切れ、新しい task の 1 回目でまた早期の方式判断が発火して自走する。「上限はそのまま数える」は state-machine.md の作り直しのリセットと食い違う |
| F2 | 独立-1 | medium | no | self-inflicted | product | next-pr | 判断役の `止めるべきか: yes` と、4 つの route のどれでもない推奨の扱いが無い。skill の括弧書きは起動できないときを書いていない |
| F3 | 独立-1 | low | no | self-inflicted | product | next-pr | worklog 行の `採った route:` が telemetry の `route: ` に当たり bounce を 2 重に数えうる。model なし・effort 継承・task id の欄が無い |
| F4 | 独立-1 | low | no | self-inflicted | product | next-pr | 判断が Step 2 の括弧書きにあり、Step 1 のテスト設計不足で TDD に戻ると発火しない |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | Gate Batch での数える単位・起動の単位・推奨の合わせ方が書かれていない |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | phase-progression.md の Escalation Decision Table に早期の方式判断の行が無い |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | gdd-opus-advisor の起動点の列挙（agent 定義・fixed-models.md・autonomy.md の参照元・agent_dispatch_gate.py のコメント）に今回の起動点が無い |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 閾値の根拠の本数（66 と 67）、判定の基準、high < 3 の群の率が無い。配布物で「このリポジトリ」と書いている |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 変更断片が「推奨が」人間に止まる条件と書き、自走範囲の検査で human_recheck_required になる経路を外している |
| F10 | 独立-1 | advisory | no | self-inflicted | product | accepted | systematic-debugging の subagent から gdd-opus-advisor を起動できるかを確かめていない。呼べなければ判断は発火せず、worklog の行でしか分からない。次の PR で確かめる |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Codex・Cursor で判断役をどう起動するかが書かれていない |
| F12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の目的が変更前の決定木より強い言い方で、Gate Batch と上限の扱いが変更内容に無い。PR 本文で直す |
