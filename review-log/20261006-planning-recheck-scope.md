---
lane: L1
pr: 388
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 9e2a957d | 0 | 0 | 0 | 2026-10-06T19:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | next-pr | 再入で読む範囲（処置箇所と変えた節）が、同じ規定の「差分と影響節」と食い違い、修正が生んだ影響節の食い違いを見なくなる。security reviewer の定義とも食い違う |
| F2 | 独立-1 | medium | no | self-inflicted | 配線 | next-pr | subagent-dispatch の 1 枚の書き方で「再入は」が requirements の文にだけ掛かり、design の再入で前回 Round の blocking の一覧が載らない |
| F3 | 独立-1 | medium | no | self-inflicted | 配線 | next-pr | design-gating の処置の手順（step 12）が blocking だけの処置に変わっておらず、advisory の high の時機も決まっていない |
| F4 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | next-pr | 再入を「2 回目の Round」で定義しており、design の Round 3 以降や build から戻った Round の扱いが決まらない |
| F5 | 独立-1 | low | no | self-inflicted | 範囲の定義 | next-pr | agent 定義に「一覧が無いときは Round 1 と同じ範囲」が無い |
| F6 | 独立-1 | low | no | self-inflicted | 文言 | next-pr | Why の数字が「時間は呼び出しの回数に比例する」を支えていない |
| F7 | 独立-1 | low | no | self-inflicted | 文言 | next-pr | 断片が Attempts への記録と agent 定義の読む範囲の追加を書いていない |
| F8 | 独立-1 | low | no | self-inflicted | 計測 | next-pr | tool_uses の取り方が gate-runner の中で未確認で、reviews.md の形式に置き場所が無い |
| F9 | 独立-1 | low | no | inherited | 計測 | out-of-diff | implementation の記録の行が hook から直近のエラーとして注入される（記録の行を Attempts に書かせる規定は前から） |
| F10 | 独立-1 | low | no | self-inflicted | 範囲の定義 | next-pr | 再入の範囲が、処置した gate の自己申告だけで決まる |
| F11 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | RED-GREEN の比較の結果が PR 本文の抜粋に無い（PR 本文の Skill RED-GREEN Evidence に書く） |
