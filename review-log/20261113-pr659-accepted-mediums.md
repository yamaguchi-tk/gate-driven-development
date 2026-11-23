---
lane: L1
pr: 663
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2d4909bd3392c156abb46e2b78c5e8cdeb661dca | 1 | 2 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | eebd828d2eeef2b2af23048eac29af51fee37696 | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | no | inherited | hitl-advisor-append | fixed | 設計: 変える（追記と出し直しの 2 経路をやめ、相談役が返ったら必ず全文を出し直す 1 経路にする）。推奨の行だけの追記は、依頼との差の欄が無く、その後の OK を承認の hook が止めていた。出し直しでは相談役を起動し直さない（I1-5 を含む）。commit: 479e1d28 |
| I1-2 | 独立-1 | medium | no | self-inflicted | request-scope | next-pr | M5 は、再開の境界を見分ける信号を足す別の L1+ の PR で直す（ユーザーの返事で決定） |
| I1-3 | 独立-1 | medium | no | self-inflicted | hitl-length | fixed | 延期・削除でない変換の行を一次表示の具体化の行に 1 行ずつ出し、OK がそれも承認するようにした。commit: 479e1d28 |
| I1-4 | 独立-1 | medium | no | self-inflicted | request-lockin | fixed | 見直しの足し直しも、要件の表と節の両方に番号を振り直して足すようにした。commit: 479e1d28 |
| I1-5 | 独立-1 | low | no | self-inflicted | hitl-advisor-append | fixed | 出し直しでは相談役を起動し直さないと書いた（I1-1 に含む）。commit: 479e1d28 |
| I1-6 | 独立-1 | low | no | self-inflicted | hitl-advisor-append | fixed | subagent-dispatch と rollback-patterns の要約を、返ったら全文を出し直すに揃えた。commit: 479e1d28 |
| I1-7 | 独立-1 | low | no | self-inflicted | planning-time-budget | accepted | 作業中の発言で起点が戻り、委任の経路では戻らない |
| I1-8 | 独立-1 | low | no | inherited | planning-time-budget | accepted | requirements-gating の skill の概要が、処置の前の経過の確認を書いていない |
| I1-9 | 独立-1 | low | no | self-inflicted | approval-record | accepted | completion reviewer が一次表示に出した行を確かめる手段を持たない |
| I1-10 | 独立-1 | low | no | self-inflicted | request-lockin | accepted | 答えから分かれた行の原文の語の欄に何を書くかが決まっていない |
| I1-11 | 独立-1 | low | no | self-inflicted | requirements-template | accepted | ズレ確認の節の置き場所が、Honest Limitations の承認ポイントの直後と食い違い、節一覧にも無い |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 直っていた 3 件の ID と場所を PR 本文に書いた。commit: なし（PR 本文） |
| I1-13 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 限界の行に種類を付けた。commit: なし（PR 本文） |
| I1-14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の具体化の行の記述を、一次表示に出す形に合わせた。commit: 479e1d28 |
| I2-1 | 独立-2 | medium | no | self-inflicted | request-scope | re-reported | I1-2 の再掲（M5 を届けていない。確認待ち） |
| I2-2 | 独立-2 | low | no | self-inflicted | hitl-length | accepted | 具体化の行の注記が完了条件の変換の語を含むと、手で回した lint が落とす |
| I2-3 | 独立-2 | low | no | self-inflicted | hitl-length | accepted | compact の必ず含める一覧が具体化の行を挙げていない |
| I2-4 | 独立-2 | low | no | self-inflicted | hitl-length | accepted | 具体化の行に追加・未解決も入り、扱いが表示から消える |
| I2-5 | 独立-2 | low | no | self-inflicted | hitl-length | accepted | 行数の目安を超えたときに具体化の行を落とすかが決まっていない |
| I2-6 | 独立-2 | low | no | inherited | hitl-advisor-append | accepted | 相談役が 1 本だけ返ったターンの発言が決まっていない |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 未リリースの別の断片が届いたら追記のまま |
| I2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 原則 7 に追記の語が残る |
| I2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片に見直しの後の番号の振り直しが無い |
| I2-10 | 独立-2 | advisory | no | self-inflicted | request-scope | accepted | 推奨案を変えないときも全文を出し直すので、人は確認を 2 回見る |
