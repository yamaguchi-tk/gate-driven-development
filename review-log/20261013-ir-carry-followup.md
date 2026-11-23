---
lane: L1+
pr: 466
follow_up_of: 459
amends: 20261013-ir-merge-carry.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) | d9a3f8e3 | 0 | 0 | 0 | 2026-10-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fa3c2e6e | 0 | 1 | 1 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 0b07d60b | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P-1 | 方針メモ | advisory | no | self-inflicted | product | fixed | 草案の 7 項目に、merge gate で理由を読むときの set -u 対策、autonomy_pushback.py が読む部分の確認、前の断片の amends:、hook の行数を増やさない、pin の追加を許容範囲の拡大として開示、を足した（Opus の推奨を採り、食い違いなし） commit: 3ede7adf |
| I1-1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | completion-check の引き継ぎの例外が、Independent Review の行の sha を merge sha に書き換えてよいと読める。書き換えてよい行を名指しし、Independent Review の行は旧 sha のまま残すと書いた commit: a7958cea |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 正本の引き継ぎの節と ir_merge_carry.py の docstring が、merge gate も independent-review-stale で止めると書いたまま。gate ごとに書き分けた commit: a7958cea |
| I1-3 | 独立-1 | low | no | inherited | doc-claim | fixed | Independent Review の sha を tip・HEAD に合わせる規定（independent-review.md (3-a)・self-review-lanes.md の 2 か所・followup のスコープ縮小）に引き継ぎの例外が無い。例外を足し、(3-a) の pin を合わせた commit: a7958cea |
| I1-4 | 独立-1 | low | no | self-inflicted | intent | fixed | Carry 行が無いときに理由を出さず、依頼より狭い。引き継ぎを試せた場面では Carry 行が無いことも理由として出す commit: a7958cea |
| I1-5 | 独立-1 | low | no | self-inflicted | intent | fixed | 引き継ぎの案内が先頭の reason code の action にしか出ない。案内を観測値に移した commit: a7958cea |
| I1-6 | 独立-1 | low | no | self-inflicted | test-power | fixed | allow のテストが hook の異常終了と区別できない。終了コードと出力の空を見る commit: daaf33a7 |
| I1-7 | 独立-1 | low | no | self-inflicted | test-power | fixed | 案内を出すテストが案内を見ていない。reason に案内があることを見る commit: daaf33a7 |
| I1-8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 秒の切り捨てのテストが - 1 を戻しても通ることがある。python3 の stub で判定を呼んだかを見る（戻すと落ちることを確かめた） commit: daaf33a7 |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Affected Files・Validation・Summary の漏れと重複 commit: a7958cea |
| I1-10 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 文書の文を固定するテストの許す文を広げた。外すかは別に決める |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | コメントの行番号が古い。節名を指した commit: a7958cea |
| I1-12 | 独立-1 | advisory | no | self-inflicted | style | fixed | 2 つの案内の形がそろっていない。案内を観測値の 1 か所にまとめた commit: a7958cea |
| I1-13 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 引き継ぎを使えない場面にも案内が出る。試せた場面だけに出す commit: a7958cea |
| I1-14 | 独立-1 | advisory | no | inherited | product | accepted | 引き継いだ後の (3-a) の絞り込みの起点が取り込み前の sha のまま。PR 本文に advisory として書く |
| I1-15 | 独立-1 | advisory | no | self-inflicted | style | fixed | 検算の文の「は」の重なり。専用の文にした commit: a7958cea |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | self-review-lanes.md:103 の「sha は push 対象 tip」に引き継ぎの例外が無い。follow_up_of のある PR なので限界に書く |
| I2-2 | 独立-2 | low | no | inherited | test-power | accepted | test_merge_gate_ir_carry.py の Medium Disposition の allow がまだ block の不在だけを見る。限界に書く |
| I2-3 | 独立-2 | low | no | self-inflicted | style | accepted | check-gate-ledger.sh:220 が RECOVERY の中身を書き写し、案内が 2 か所になった。限界に書く |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation の括弧が (3-a) の固定文の書き換えを書いていない。限界に書く |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文が依頼の「テストの docstring の数え方」の行を名指ししていない commit: なし（PR 本文） |
| I2-6 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 文書の文を固定するテストが残り、文書を直すたびに書き換えが続く。残すかは別に決める |
