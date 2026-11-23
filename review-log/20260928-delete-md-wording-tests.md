---
lane: L1
pr: 220
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8deeb56a6d5425da6f9e004d61af2c2162c13589 | 0 | 2 | 0 | 2026-09-28T20:51+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | e25862eb6db9aea539b57fd6ae514a38cc974fa4 | 0 | 0 | 0 | 2026-09-28T21:12+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 消したテストに、コードと文書を突き合わせる検査（常時 High の (a) の再開 field と hook・tiers の集合の一致、checkpoint の定数の実在）が含まれていた。この 2 つだけを残す形でファイルを戻した（b7ac4633）。断片の説明も合わせた（6bd0a235） |
| F2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | testing-anti-patterns.md の「クラス E の文単位のテストは残す」と、消した範囲が食い違う。規定は利用者の repo にも効く製品の規則なので変えず、同じ節が正とする対象 repo の CLAUDE.md のテストの節に、この repo の決定（文書の語・文だけを見るテストは書かない・残さない）を書いた（1ea31f37） |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | prompt-contract-map.md の state の正本の行が、ずれを検出しないテストを guard として挙げていた。guard 欄を None にし、Residual risk に機械の検査が無いことを書いた（441d2deb） |
| F4 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 断片に限界の段落があり、参照を直した範囲の書き方が docs/adr を残したことと合わなかった。段落を外し、docs/adr を除いたと書いた（6bd0a235） |
| G1 | 独立-2 | medium | no | self-inflicted | doc-claim | next-pr | 新しいテストの節が、手順 2（TDD）と「指摘を直すとき」の先に書くテストと食い違う。文書だけの変更で先に書けるテストが無くなったのに例外が無い。次の PR で例外を書く |
| G2 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | test_light_lane_review_routing_contract.py の MaterialsByFileTests・PrBodyFieldTests・FollowUpChainTests は文書の文だけを固定していて、新しい節に反する。混在ファイルの語の検査を消す次の PR で消す（RoutingVocabularyTests は残す） |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | prompt-contract-map.md の state の正本の行の guard を None にしたが、codebase-health-smoke.sh の overview 2 文書の 30 行上限が一部に効いている。次の PR で guard 欄に書く |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 戻した test_always_high_scope_contract.py に、コードと突き合わせない文字列の固定（hook 所有の宣言の先頭が Status）が 1 つ残る。次の PR で集合の包含に直す |
| G5 | 独立-2 | low | no | self-inflicted | test-power | next-pr | test_resume_fields_are_in_scope は (a) の列挙との一致ではなく、節全体への片方向の包含になっている。次の PR で (a) の括弧の中を取り出して集合の一致にする |
| G6 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 断片に利用者から見えない変更の段落と実測を書き足していた。段落と実測を外した（edbc76fa）。断片は後続の PR で書き換えられないので、差分巡の low だがこの PR で直した。changelog.d だけの commit なので巡は無効にならない |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | CONTRIBUTING.md:85 が「skill / reference の契約は tests/test_*.py で固定する」のままで、新しい方針と逆向き。次の PR で直す |
| G8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 新しい節の「テスト」に tests/checks/*.sh の文言検査が含まれるかが書かれていない。次の PR で範囲を 1 文書く |
