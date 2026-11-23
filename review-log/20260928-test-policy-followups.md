---
lane: L1
pr: 221
follow_up_of: 220
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b67d0cd9c345b641308b517868189042adaafbf1 | 0 | 0 | 0 | 2026-09-28T21:54+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | dd0fc4ff32b7795d29ce339193737b6886dff81c | 0 | 0 | 0 | 2026-09-28T22:15+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | e409b6fde0a0cd126b238ee58e507abdeaa3fdca | 0 | 1 | 0 | 2026-09-28T22:50+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | inherited | doc-claim | next-pr | test_light_lane_review_routing_contract.py に、CLAUDE.md・AGENTS.md・agent 定義の文言だけを見るメソッドが残る（差分との関係: 無関係、②）。並行している混在ファイルの削除の PR で消す |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | CONTRIBUTING.md の新しい文が対象を限らず、CLAUDE.md の tests/test_*.py への限定と食い違う。同じ限定を書いた（f19c4343） |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | (a) の列挙の正規表現が入れ子の全角括弧で途中で切れ、後ろに足した field を比べない。入れ子を許さない形にし、変異で落ちることを確かめた（b6c61b49） |
| F4 | 独立-1 | low | no | inherited | test-power | fixed | test_status_field_ownership_contract.py が hook 所有の宣言行を読まず Status を固定で置き、同じ宣言を読む 2 本で受理集合が食い違う。宣言行の field を全部取る形にし、変異で落ちることを確かめた（4aab7ebf、断片 59edce73） |
| F5 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | hook 所有の宣言の先頭が Status であることの検査を外したのは assert の緩和に当たる。近道にせず通常の巡で進める |
| G1 | 独立-2 | low | no | self-inflicted | test-power | accepted | hook 所有の宣言を読む 3 本目の test_pre_compact_transcript_offset.py:402-404 が Status を固定で置いたまま。偽の失敗は落ちる側で、Status を外した形は他の 2 本が拾う。follow_up_of がある PR の差分巡の low なので accepted にし、PR 本文の限界に書く |
| G2 | 独立-2 | low | no | inherited | doc-claim | accepted | test_status_field_ownership_contract.py に文書の語だけを見るメソッドが 2 本残る。並行している混在ファイルの削除の PR が消すので、この PR では扱わない。PR 本文の限界に書く |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Summary の CONTRIBUTING の記述に tests/test_*.py の限定が無かった。限定を入れた（249925c1）。断片は後続の PR で書き換えられないので、差分巡の low だがこの PR で直した。changelog.d だけの commit なので巡は無効にならない |
| G4 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | (a) の抽出が最初の (a) に固定されておらず、入れ子のときに落ちる理由が読み取りにくい。落ちる側には倒れる。次に触るときに直す |
| J1 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | skills/gdd-writing-skills/SKILL.md:21・31・36・40 が、見出し・語の有無を見る contract test を書くよう指示したままで、CONTRIBUTING のテストの方針と逆を向く。main の取り込みで巡が無効になった後の差分巡の blocking でない medium で、follow_up_of があるので accepted にし、PR 本文の限界に書く |
| J2 | 独立-3 | medium | no | inherited | doc-claim | next-pr | test_superpowers_differentiation_contract.py ほか 3 ファイルに、文書の語の有無だけを見るメソッドが残る。差分が触っていない側なので、PR 本文の「次の PR」に列挙する |
| J3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | CONTRIBUTING.md:85 が command の契約を tests/test_*.py で固定するとし、「残さない」も無い。accepted にし、PR 本文の限界に書く |
| J4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | CLAUDE.md § テストの「ここでいうテストは tests/test_*.py」が、文書だけの変更の免除の行にも掛かって読める。accepted にし、PR 本文の限界に書く |
| J5 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | (a) の比較は最初の括弧の中だけで、括弧の外に広げた field は比較に入らない。入れ子のときは落ちるが、メッセージが原因を指さない。PR 本文の advisory に書く |
