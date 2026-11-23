---
lane: L1
pr: 旧#207
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 7ac4a8fcc4e49e3320a536da432395baa346cce6 | 0 | 0 | 0 | 2026-09-28T21:05+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 実データ 228 件の実測は当時の `_route_value`（是正前は読めない値に空を返した）で測った値で、今の `tasklist_parse.route_value` に付け替えると測定の帰属が変わる。近道の ① の blocking でない low なので次の PR で当時と今の名前を併記する |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Validation の 2 つ目の grep に探す場所が無い。断片はリリース後に書き換えられないので、この PR で足した（5c8a0eda） |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 一律 block を説明した docstring の test は、値が non-none なので一律 block かどうかを判別しない。一律 block を pin している `test_unclosed_fence_blocks_even_when_route_is_none` への参照を、次の PR で L1 と一緒に足す |
