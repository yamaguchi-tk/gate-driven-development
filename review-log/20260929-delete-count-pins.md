---
lane: L1
pr: 228
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 18b01c4d23621e66c9e03e4fc6cfefab76795a53 | 0 | 1 | 0 | 2026-09-29T00:24+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 278f025eb0917608ecb0bc277f5b49955a5feafa | 0 | 0 | 0 | 2026-09-29T00:38+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| N1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 3 レーン定義・効果測定の表は本文が数（3）を書いていて、行数の固定を外しても行を足すと本文の検査で落ち、表だけを増減させた不整合だけが通るようになっていた。2 表の行数の固定を戻した（1a03f36b） |
| N2 | 独立-1 | low | no | self-inflicted | test-power | fixed | progress bind の hollow check が scope の中の不受理側を見ておらず、scope が受理行だけになっても通る。共有受理面が受理しない行があることの検査を足した（1262085d） |
| N3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | SessionStart の出力点の数の固定を外したが、docstring は 4 番目の出力点を足すと落ちることを理由に書いたまま。新しい出力点に動的テストを足させる固定なので戻した（1a03f36b、断片 f30a1727） |
| N4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 残した受理数の固定を「reader の挙動」としていたが、受理数は生成集合にも依存し、受理される次元を広げると落ちる。断片と PR 本文をそう書き、限界に足した（f30a1727） |
| N5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の目的と限界が、同じ種類の件数の固定（self_review_lanes の記入例、verification_grammar の例表）を対象か対象外か示していなかった。PR 本文の限界に名前で挙げた（PR 本文） |
| N6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 総数 149 の固定を外したので、AC-11 の case の件数を書いた docstring（98 件中 90 件・43 件・35 件・149 case）がどの assert にも縛られなくなった。PR 本文の advisory に書く |
| N7 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | corpus の件数の固定は、以前の外部レビューで下限の緩さを指摘されて入れたもの。空でないことだけの検査はそれより緩く、同じ指摘が出やすい。PR 本文の限界に開示済み |
| P1 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Validation が「6 ファイル」のままで、Summary・Affected Files の 5 件と合わない。5 に直した（a32cee0f）。断片は後続の PR で書き換えられないので、差分巡の low だがこの PR で直した |
| P2 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 変更断片の Summary に、受け入れた限界（受理される次元を広げたら実測し直す）を書き足していた。Summary から外し、PR 本文の限界に残した（a32cee0f） |
| P3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | progress bind の assert のメッセージが、生成した `## ` 行を「次の test の入力」と呼ぶが、次の test はリテラル 1 行を入力にしている。PR 本文の「次の PR」に列挙する |
| P4 | 独立-2 | advisory | no | inherited | doc-claim | accepted | PR 本文の限界が 1500（名前が空白のみの乖離数）を受理数と呼んでいた。PR 本文を直した |
