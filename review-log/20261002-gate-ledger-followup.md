---
lane: L1
pr: 294
follow_up_of: 285
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c7b0c248f463784a24e0b11b45981246940d43c6 | 0 | 1 | 0 | 2026-10-02T21:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | b7b7f316795c03bdbec0e48a90a3f6170648b0d8 | 0 | 1 | 0 | 2026-10-02T21:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| C1 | 独立-1 | medium | no | self-inflicted | product | fixed | 戻す規則が「移した後にだけ現れた行」しか見ず、ok 行が消える 1 タスクの移動・見出し 1 件の崩れ・欠けていたブロックの移動を検出しない commit: de8772d2 |
| C2 | 独立-1 | low | no | self-inflicted | product | fixed | pre-push の解決が multiple で tip の証跡が 1 件に決まらないと hook は止めるのに、steering 行が pre-push を挙げない（限界としてコメント・断片・PR 本文に書いた） commit: de8772d2 |
| C3 | 独立-1 | low | no | self-inflicted | test-power | fixed | pre-push の解決が none のときの gate 列の分岐を固定するテストが無い commit: 86c280ad |
| C4 | 独立-1 | low | no | self-inflicted | test-power | fixed | kill-switch.sh の source と -X utf8 を戻しても落ちるテストが無い（EUC-JP の入口テストと契約テストの対象で固定） commit: 86c280ad |
| C5 | 独立-1 | low | no | inherited | product | fixed | deny 文言が --steering を案内せず、steering が複数あると移す前後の比較が働かない commit: de8772d2 |
| C6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界「解決が食い違うと止まる」が、実際に止まる条件（どちらの解決も 1 件にならない）と違う commit: なし（PR 本文） |
| C7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の「python は -X utf8 で起動する」が、-I の起動 1 か所だけなのに全部と読める |
| C8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の Validation が、足したテストと強めたテストを分けていない |
| C9 | 独立-1 | advisory | no | inherited | doc-claim | accepted | サイズ超過の警告文の state.md の節「理由は 1 行」が「要約しない」と向きが違う |
| C10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 前の PR の未リリース断片（20261002-gate-ledger-check）の記述が、この差分で古くなる（リリースの dry-run で直す） |
| C11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | テンプレート外の記述あり: PR 本文の抜粋に変異の検出結果の断定があった（次の巡の前に抜粋から除いた） |
| D1 | 独立-2 | medium | no | self-inflicted | product | accepted | 移す前の行が移した後に無ければ戻す、は移したことで直った行（前にある古い field の行・閉じていない fence を移した場合）にも戻すよう案内する（向きつきの 2 条件に分ければ閉じる） |
| D2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「移す前から欠けていた行を直す手順ではない」の明記が state-field-tiers.md に無いのに、断片と PR 本文は両方に明記したと書く |
| D3 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 変更断片に、受け入れた限界（steering-multiple を挙げない）を書いている |
| D4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 契約テストに明示した検算スクリプトのパスが無くなっても、下限 2 のままテストが通る |
| D5 | 独立-2 | low | no | self-inflicted | test-power | accepted | EUC-JP のテストは -X utf8 で通り、kill-switch.sh の source を外しても Linux では落ちない見込み |
| D6 | 独立-2 | low | no | self-inflicted | test-power | accepted | none の場合のテストが pre_pr_blocks を assert しない |
| D7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | kill-switch.sh のコメントが挙げる -I の起動の一覧に検算スクリプトが無い |
| D8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文の「python は -X utf8 で起動する」が、-I でない起動にも当たると読める |
| D9 | 独立-2 | low | no | inherited | product | accepted | 読めない steering があると --steering を付けても検算が 2 行で止まり、移す前後の比較が働かない |
| D10 | 独立-2 | advisory | no | inherited | product | accepted | 移す前から上限を超えていたファイルでは、移した行を全部戻す書き込みが size deny に止められる |
