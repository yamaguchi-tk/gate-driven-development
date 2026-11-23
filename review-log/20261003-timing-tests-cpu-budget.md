---
lane: L1
pr: 296
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | dc8798b42e6d3ab48f0a630c2169f82a8302d761 | 0 | 0 | 0 | 2026-10-03T15:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 66270cb2df445b3bd675b070e72d0d9f871c039a | 0 | 0 | 0 | 2026-10-03T16:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| E1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 2 本が ADR X-37 の二本立て（壁時計の backstop は timeout の半分）と違う形になった理由がどこにも無い。テストのコメントに理由を書いた commit: 28367786 |
| E2 | 独立-1 | low | no | inherited | test-power | fixed | CPU の閾値と保険が literal の 10 で、hooks.json の timeout を下げても追随しない。`hook_timeout_seconds()` で読む commit: 28367786 |
| E3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `HOOK_TIMEOUT` のコメントが、長い入力のテストには当てはまらなくなった。当てはまるテストを書き分けた commit: 28367786 |
| E4 | 独立-1 | low | no | self-inflicted | style | fixed | in-process の計測が共通の `timing_budget()` を使わず式を写している。`timing_budget()` にそろえた commit: 28367786 |
| E5 | 独立-1 | low | no | inherited | test-power | next-pr | merge gate のほかの解析時間のテスト（target_grammar・env_split_string・command_parse）が壁時計のまま。次の PR で CPU 時間にそろえる |
| E6 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 壁時計の上限を 10 秒から 60 秒に広げ、assert の許容範囲の拡大に当たる。PR 本文の限界に書く |
| E7 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 「CPU 時間で超えるなら壁時計でも必ず超える」は直列の実行でしか成り立たない。「ほぼ直列なので」と前提を書いた commit: 28367786 |
| E8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の変異の確認の実測（CPU 秒）が抜粋に無い。PR 本文に at sha つきで書く |
| E9 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の Validation に、関係するテストと validate-plugin.sh が無い。書き足した commit: 28367786 |
| F1 | 独立-2 | low | no | inherited | test-power | next-pr | `test_steering_enumeration_unreadable.py` に `HOOK_TIMEOUT = 10` の literal が残り、merge gate と pre-push gate の FIFO テストが hooks.json の timeout に追随しない |
| F2 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 新しいコメントの「待ちを見るテスト（FIFO）」は pre-PR gate の FIFO テストに当てはまらず、`HANG_GUARD` の括弧が比べる値と誤読されうる |
| F3 | 独立-2 | low | no | inherited | test-power | next-pr | pre-PR gate の FIFO テストが、hook の timeout（10 秒）より長い 20 秒で打ち切り、10〜20 秒の有限の待ちを見逃す |
| F4 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | 断片が「利用者から見える変更なし」と書きながら `#### Changed` にテスト内部の変更を並べている（§ Policy から外れる） |
| F5 | 独立-2 | advisory | no | inherited | doc-claim | accepted | ほかのコメントに「10 秒」の数値が残る。PR 本文に書く |
| F6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | ADR X-37 の決定から外れることを ADR 側に記録していない。PR 本文に書く |
| F7 | 独立-2 | advisory | no | inherited | doc-claim | accepted | `_run_hook` の既定の timeout が literal の 10 のまま。PR 本文に書く |
