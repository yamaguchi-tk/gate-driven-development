---
lane: L1
pr: 430
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | cf1f65b2 | 0 | 2 | 0 | 2026-10-10 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8307af00 | 0 | 3 | 0 | 2026-10-10 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9a62cb51 | 0 | 1 | 0 | 2026-10-10 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 1d033f23 | 0 | 0 | 0 | 2026-10-10 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 98c40797 | 0 | 0 | 0 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| C1-F1 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 規定の置き場所が、gate を実行する runner の読む経路に無い。runner の定義と実装・完了の gate の手順に置いた。commit: 8307af00 |
| C1-F2 | 独立-1 | medium | no | self-inflicted | product | next-pr | `Round <n>` の出どころが無く、task の欄も無い |
| C1-F3 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | gate を subagent が実行したときだけに限っていた。inline 実行と worker 経由の main も書き手にした。commit: 8307af00 |
| C1-F4 | 独立-1 | low | no | self-inflicted | bookkeeping | next-pr | 件数の定義が gate によって変わる |
| C1-F5 | 独立-1 | low | no | self-inflicted | bookkeeping | next-pr | 判定と phase の値の集合が、gate の出口と合わない |
| C1-F6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | `所要` の定義と、計れないときの値が無い。所要の欄を外した。commit: 98c40797 |
| C1-F7 | 独立-1 | low | no | self-inflicted | product | next-pr | worker の経路で、同じファイルの worker の規定と食い違う |
| C1-A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | worklog.md がまだ無いときの扱いが無い |
| C1-A2 | 独立-1 | advisory | no | self-inflicted | request-drift | fixed | 「gate の記録に欄を足す」を worklog.md の別の行で満たした理由が無い。PR 本文の目的に置き場所の理由を書いた。commit: なし（PR 本文） |
| C1-A3 | 独立-1 | advisory | no | self-inflicted | request-drift | fixed | 依頼に無い欄を足した。PR 本文の目的に理由を書いた。commit: なし（PR 本文） |
| C1-A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 書き漏れを行の有無で数えるのは、implementation・completion では steering だけでは成り立たない |
| C1-A5 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 変更断片の検証が、runner が行を書くかを確かめていない |
| C2-F1 | 独立-2 | medium | no | self-inflicted | wiring | fixed | 足した文が、Claude Code の main に「ここで実行しない」と言う段落の中にある。段落の外の行にした。commit: 9a62cb51 |
| C2-F2 | 独立-2 | medium | no | self-inflicted | product | fixed | ポインタの「出口を問わず」が正本に無く、書き込みを禁じる出口まで含む。語を外した。commit: 9a62cb51 |
| C2-F3 | 独立-2 | medium | no | self-inflicted | product | next-pr | 行の `Round <n>` をどのカウンタから取るかが書かれていない |
| C2-F4 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | requirements・design の gate を、確認なしに限界に回していた。レビューループの契約に置いた。commit: 9a62cb51 |
| C2-F5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | runner の文が、どの `## Phase` が gate に当たるかを挙げていない |
| C2-F6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の書き手から「worker 経由なら結果を統合する main」が抜けていた。commit: 9a62cb51 |
| C2-F7 | 独立-2 | low | no | self-inflicted | style | fixed | 足した文の前の余分な空白。commit: 9a62cb51 |
| C2-F8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | light-task-runner には当てはまる場面が無い（2 つの runner の本文の一致のため） |
| C3-F1 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | design-gating には規定が届いていなかった。reviewer を起動するときに読む時間上限の項から指した。commit: 1d033f23 |
| C3-F2 | 独立-3 | low | no | self-inflicted | product | next-pr | 実装・完了の gate の行に書き手が書かれていない |
| C3-F3 | 独立-3 | low | no | self-inflicted | bookkeeping | fixed | `所要` に計れないときの値が無い。所要の欄を外した。commit: 98c40797 |
| C3-A1 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | design・implementation の reviewer の timeout は blocked で止まり、`timeout` の行は requirements でしか出ない |
| C3-A2 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | fail-closed カウンタの項に「カウンタはこの行を読まない」が無い |
| C3-A3 | 独立-3 | advisory | no | self-inflicted | style | accepted | completion-check の本文が行予算 350 行ちょうどになった |
| C4-1 | 独立-4 | low | no | self-inflicted | bookkeeping | fixed | 既定の経路で `所要` を計れないのに、値の欄に「不明」が無い。所要の欄を外した。commit: 98c40797 |
| C4-2 | 独立-4 | low | no | self-inflicted | bookkeeping | next-pr | 時間上限の項の句が「返るごと」の文に付いていて、書き手と書く時点がずれる |
| C4-3 | 独立-4 | low | no | self-inflicted | request-drift | fixed | 依頼の「巡数と high 件数」より欄を広げている。ユーザーが所要だけを外して残すと決め、`.request.md` に足した。commit: 98c40797 |
| C4-4 | 独立-4 | advisory | no | self-inflicted | doc-claim | fixed | design-gating に規定が届く経路の書き方がずれている。断片を直した。commit: 98c40797 |
| C5-1 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 時間上限の項の `gate結果:` の指し先が、所要時間を記録する文の括弧の中に残っている（C4-2 と同じ箇所） |
| C5-2 | 独立-5 | advisory | no | self-inflicted | bookkeeping | fixed | `.request.md` の「PR-C」が何を指すかが書かれていない。指す文を足した。commit: なし（review-log） |
