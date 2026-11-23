---
lane: L1
pr: 319
follow_up_of: 294
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable) + user（旧#294 の「次の PR」の、pre-push gate の step 8b を lib に切り出して検算の steering 行から呼ぶ案について。実測: 直近 30 日で steering-multiple の block 文が出た transcript は、このリポジトリの開発以外では 2 本。Opus は、検算は止めない道具で、まれな入力のために block gate を L1+ で動かす費用は見合わず、案の AC（gate 列の pre-push と hook の block の一致）は tip で選んだ steering が期待と違うと成り立たないとして、切り出さないことを推した。main の案と食い違ったので信号 ① で Fable を呼んだ。Fable も切り出さないことを推し、multiple のとき検算は今でも steering 行が invalid で exit 1 になり、変わるのは gate 列のラベルだけであることを実コードで確かめ、詳細文で知らせることと再検討の発火点を書くことを足した。ユーザーは、切り出さずに文言だけ足す案を選んだ） | - | 0 | 0 | 0 | 2026-10-03T00:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4d076a95be47d1dc52931ee3b7634195d1046550 | 0 | 1 | 0 | 2026-10-03T00:50+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 440156b7d5730cc59a87abf0364025ddf76303b2 | 0 | 0 | 0 | 2026-10-03T00:56+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| M1 | 独立-1 | medium | no | self-inflicted | product | fixed | 注記が載る steering 行は、push の前の読み方（gate 列に pre-push を含む行だけ）では読まれない。header と self-review-lanes.md に、詳細が pre-push=multiple なら読むことを足した commit: 440156b7 |
| M2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 注記を条件なしに足す変異がどのテストでも落ちず、確かめる語が reason code でない commit: c444c2df |
| M3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 注記と断片が、valid な証跡だけを数えること・cancelled を含むことを書いていない commit: 440156b7 |
| M4 | 独立-1 | low | no | self-inflicted | style | fixed | invalid 行で注記の後ろに pre-PR の括弧が続き、「この行は判定しない」が何を判定しないのか曖昧 commit: 440156b7 |
| M5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 実測の対象と出典が無く、写す条件の 1 つ目は hook が記録しないので気づく仕組みが無い commit: 440156b7 |
| M6 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり。PR 本文の抜粋に、採らなかった案（lib への切り出し）の記述がある |
| N1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 注記が sha の一致の向きを「tip の sha で始まる」と逆に書き、大文字小文字を区別しないことも書いていない |
| N2 | 独立-2 | low | no | self-inflicted | test-power | accepted | ok 行（pre-PR は found、pre-push は blocked の兄弟で multiple）の注記と、注記が詳細の最後にあることをテストが確かめていない |
| N3 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 写す条件の 2 つ目は hook が記録しない事象に依り、根拠の実測のコマンドが書かれていない |
| N4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 詳細を読んだ後に確かめることと、1 件に決まらないときの出口（使わないステアリングの終え方）への導線が検算の出力に無い |
