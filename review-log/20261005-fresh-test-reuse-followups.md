---
lane: L1
pr: 372
follow_up_of: 369
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d1fd11c1e09fc24677cbf5b11e26d4dd4fd97ee0 | 0 | 3 | 0 | 2026-10-05T13:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | Common Failures の表の「テストが通る」の不十分なものの括弧（HEAD が同じ・clean などを 2 回）が、使い回しの条件なのに直接回した実行にも掛かり、:32 の「直前の tool 実行は fresh」と食い違う（締めすぎ）。PR 本文の限界に書く |
| F2 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 例のコマンド列にテストの cwd を <wt> にする手順と show-toplevel が無く、shasum の引数と (3) の起点（<wt> か cwd か）が読み取れない。本文は確かめられなければ回し直す形。PR 本文の限界に書く |
| F3 | 独立-1 | medium | no | self-inflicted | product | accepted | (3) は 2 回とも両方のファイルが無いときしか省けず、design.md を作らない quick (express) では shasum が失敗して使い回しが起きない（回し直す側）。PR 本文の限界に書く |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Iron Law の「同じ起動の外」の括弧が main の区切りだけで、別の subagent の起動を含まない。テスト以外の結果を使えないことも Iron Law だけでは読めない。PR 本文の限界に書く |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | completion-check:337 の「前のターン」が限定の無いまま残り、Iron Law の言い換えと揃っていない。PR 本文の限界に書く |
| F6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | completion-check:78 と reference:42 の RUN の括弧に「条件を満たす」が無い。PR 本文に書く |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の揃えた箇所の一覧に § Fresh の粒度の最初の箇条が無い。PR 本文に書く |
| F8 | 独立-1 | advisory | no | self-inflicted | product | accepted | agent 定義 5 本に、テストを回す時点で確認のコマンドを先に付けることが書かれていない（回し直す側。限界に開示済み）。PR 本文に書く |
