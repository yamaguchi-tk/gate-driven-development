---
lane: L1
pr: 392
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a51fd0e0048d20b4edf0da6d1181ef4a4991e458 | 0 | 1 | 0 | 2026-10-07T00:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 全差分, model: opus | 9c09adfd15cc17c1adf983e93ed5513aa4992609 | 1 | 0 | 1 | 2026-10-07T01:30+09:00 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 9c09adfd15cc17c1adf983e93ed5513aa4992609 | 0 | 0 | 0 | 2026-10-07T01:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | product | fixed | 観測した RED が無い task を TDD に戻すと、Gate Batch の completed の task や見出しだけある RED Evidence は TDD の対象に入らず、手順 17 との間で上限なく回る。既に実装のある task では Pre-existing Implementation の隔離や planned_red_missing に落ちる commit: 9c09adf |
| L1 | 独立-1 | low | no | self-inflicted | product | fixed | systematic-debugging の並列修正パス・修正後の再審査など、この skill を通らずに impl gate に入る経路では確認が走らない commit: 9c09adf |
| L2 | 独立-1 | low | no | self-inflicted | product | fixed | 確認は行の有無だけを見て、Step 1d が見る Worktree の値の一致と test: のファイルが差分にあるかを見ない。既存のテストを RED 再現テストに使うと確認を通っても 1d が差し戻す commit: 9c09adf |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「Step 1d は test: か verification: が欠けると High で差し戻す」と読めるが、1d が High にするのは Worktree: の欠落・不一致・ファイル未掲載・コマンド失敗だけ commit: 9c09adf |
| A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 書き写した Worktree: が gate の時点の値であることが記録から分からない |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の実測（6 本で 10 回、値の不一致 0 件）に出所が無い。数え方と steering を書いた commit: なし（PR 本文） |
| A3 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 変更断片の Validation に関係するテストの実行と RED-GREEN の場面が書かれていない |
| H1 | 独立-2 | high | yes | self-inflicted | fail-open | accepted | 列挙: 欠けた Worktree: を gate の時点の観測値で足すので、Step 1d の値の一致は必ず成り立つ。verification: だけの形式では 1d の検査がこれだけなので素通りする。方針メモ-1 で手順 6 の既定 (b) を採り、限界に書いた（入力者: 値の不一致は gate 記録で 0 件、書き漏れの 10 件は観測した worktree が記録に無く未測） |
| M2 | 独立-2 | medium | no | self-inflicted | product | next-pr | 変えていない既存のテストを RED 再現テストに書き写すと 1d で差し戻され、TDD は節があるので RED を取り直さず、同じ差し戻しが人に戻るまで続く。既にある Worktree: が違う task も同じ |
| L4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | TDD に戻さない理由のうち「既に実装のある task は TDD が隔離する」は、差し戻しの後に systematic-debugging が TDD に戻すので成り立たない |
| L5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 20261006 の断片が最終の規定と逆（TDD に戻す）を書き、20261007 の断片が途中の経緯を書いていた。断片を 1 つにまとめた commit: 5254a7b |
| L6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 手順 2a の Conflict Detection の行（gate に進む文）が確認に触れていない |
| L7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | systematic-debugging の並列修正パスの手順 3 で、確認が「conflict があれば」の内側に読める |
| L8 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | 新しく作った節の AC: の行の扱いが無く、Covers AC: の無い remediation task では lint-ac と食い違う |
| A4 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | 20261007 の断片に対応する review-log が無い。断片を 20261006 にまとめた commit: 5254a7b |
| A5 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋が差分の規定の本体を説明していない。PR を 1 本にまとめて本文を書き直した commit: なし（PR 本文） |
| P1 | 方針メモ-1 | advisory | no | self-inflicted | product | accepted | H1 の相談。main の案は (a) RED を観測した時点の値でだけ足す。Opus の推奨は (d) test: のパスがある項目だけ足す。Fable（信号 ①）の推奨は (e) 今の形のまま手順 6 の既定 (b) で限界にする。値の不一致の実例が 0 件なので既定の (e) を採った。旧#392 は単独でマージせず 1 本にまとめる（Opus・Fable とも同じ） |
