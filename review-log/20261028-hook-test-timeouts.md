---
lane: L1
pr: 599
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 03f6089ef1a60359c2515c9abc891f27bab14d4f | 0 | 1 | 0 | 2026-10-28T12:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 決着（2026-10-28T12:58+09:00、ユーザーは 2 本に分ける推奨の案でよいと返事）: 依頼の C（autonomy_pushback.py の gh の時間切れの記録）が差分に無く、限界の節に回している。C は hooks/scripts/lib を変える L1+ の変更で、手順 6 の例外 (c)（別のファイル群に広がる）に当たるので、直後の PR に分け、1 本にしたいかを PR 本文で問う（Opus は 1 本、Fable は 2 本を推奨。main は Fable と同じ） |
| r1-2 | 独立-1 | low | no | self-inflicted | test-order | accepted | test_pushback_time_limit_fits_the_hook_timeout が、RunWithinDeadlineTest が戻さずに書き換える module の定数を読み、worksteal の走る順で落ちうる |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary が、直した範囲（literal の 10 秒など）より広く「そろえた」と書いている |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「打ち切りが効かない退行は 60 秒で落ちる」は、gh の打ち切りと締め切りの両方が効かないときだけ当たる（docstring・断片・PR 本文） |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docstring の「本番の timeout に収まること」は、定数の比較が示す押し返しの分より広い |
| r1-6 | 独立-1 | low | no | self-inflicted | test-power | accepted | 壁時計の上限を外した後は、押し返しの thread の外で 10〜60 秒待つ退行をどのテストも落とさない（PR 本文の限界に開示） |
| r1-7 | 独立-1 | low | no | self-inflicted | style | accepted | Stop hook の打ち切りの導出を 3 か所に足し、_stop_hook_test_base._run_hook の既定は literal の 60 のまま |
| r1-8 | 独立-1 | low | no | inherited | test-power | accepted | test_ir_merge_carry.py:600 に壁時計 3.0 秒の上限が残り、打ち切りの変更では負荷の偽の失敗が減らない |
| r1-9 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 大きな transcript のテストの CPU 時間に、テストの側の fixture づくりが入っている |
| r1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 共有の lib（ir_merge_carry・regular_file）のテストを 1 つの hook の lib と書き、その hook の hang guard から導いている |
