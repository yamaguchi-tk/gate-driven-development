---
lane: L1+
pr: 602
follow_up_of: 599
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | - | 0 | 0 | 0 | 2026-10-28T12:58+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e2faa426d276b450d147b14bf34a29700e2cc7a6 | 1 | 0 | 1 | 2026-10-28T13:25+09:00 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | - | 0 | 0 | 0 | 2026-10-28T13:45+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2ffd21e1ae3992f28a09941feb408f916b443784 | 0 | 0 | 0 | 2026-10-28T14:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | advisory | no | self-inflicted | design-alternative | accepted | 入口の e2e の見方で Opus（gh の行を厳密に見て、deadline の行だけなら skip）と Fable（どちらかの行で通す）が割れた。Fable の案は負荷で変更前のコードでも通るので Opus の案にした。ユーザーは推奨の進め方でよいと返事 |
| r1-1 | 独立-1 | high | yes | self-inflicted | fifo-log-write | fixed | 設計: 変える（hook の記録をブロックする open で開く）。.gdd/hook-errors.log が FIFO だと、gh の打ち切りの記録（と締め切りの記録）の open が戻らず、Stop hook が timeout まで止まり done guard が走らない。append_log_record を非ブロッキングで開いて通常のファイルにだけ書く形にし、全呼び出し元で閉じた（Opus・Fable とも同じ案。commit: b0e81e97a665e980df0b3850264943790804e037） |
| r1-2 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 依頼の「遅い gh のテストでその行を確かめる」を、既存の test_slow_gh_does_not_starve_done_guard ではなく、新しい入口のテストで確かめている。ユーザーが承認した方針メモの 10（旧#599 が書き換えるテストには触らず、新しいクラスに置く）のとおりで、手順 6 の例外 (a) に当たるので直さない（Opus・Fable とも同じ推奨） |
| r1-3 | 独立-1 | low | no | self-inflicted | test-power | accepted | gh 以外の失敗のテストが、差し替えた subprocess.run が呼ばれたことを確かめていない |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「gdd-status は両方を読む」は、サブディレクトリの .gdd/ を読まないので広い |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「gh の行は出ず deadline の行だけが出る」は、締め切りの後も worker が動くので広い。出ないのは hook が gh の打ち切りより前に終わったときだけ |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 限界の「リスクが低い」の行に、件数も未測も無い |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | GDD の外の repo にも .gdd/hook-errors.log ができる頻度が増えることを、断片も PR 本文も書いていない |
| r1-8 | 独立-1 | advisory | no | self-inflicted | product | accepted | gdd-status の末尾 5 件の故障の診断に、gh の遅さの行が並ぶ。件数はマージ後に測る |
| r1-9 | 独立-1 | advisory | no | self-inflicted | product | accepted | skip の経路で偽の gh の sleep 600 が 10 分残る |
| r1-10 | 独立-1 | advisory | no | inherited | test-power | accepted | RunWithinDeadlineTest が module の値を戻さない（差分前から） |
| r1-11 | 独立-1 | advisory | no | inherited | doc-claim | accepted | docs/SECURITY.md の Stop の行に、押し返しの読み書きと gh pr view が無い（差分前から） |
| pm1-1 | 方針メモ-1 | advisory | no | self-inflicted | design-alternative | accepted | r1-1 の直し方を、gh の記録だけ守る狭い案ではなく、append_log_record を通常のファイルにだけ書く形にする案にした（狭い案は締め切りの記録の経路が main の thread で止まるので直らない）。r1-2 は承認済みの方針メモ 10 のとおり直さない。Opus・Fable とも同じ推奨 |
| r2-1 | 独立-2 | low | no | self-inflicted | windows | accepted | os.open に O_BINARY が無く、Windows では fdopen のテキストモードと CRT の変換で各行が \r\r\n で終わりうる（実機では未確認。PR 本文に Windows は未確認と書いた） |
| r2-2 | 独立-2 | low | no | self-inflicted | fd-leak | accepted | fdopen を種類の確認より先に呼ぶので、lseek の ESPIPE を握らない古い Python では、読み手のいる FIFO で fd が hook の終わりまで閉じられない。書かずに戻る結果は同じ |
| r2-3 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 足したテストの待ち時間が literal の 3 秒・5 秒で、高い負荷では誤って落ちる余地がある |
| r2-4 | 独立-2 | advisory | no | self-inflicted | product | accepted | 遅い gh の exec sleep 600 が、締め切りが先に来たときに 600 秒残る |
