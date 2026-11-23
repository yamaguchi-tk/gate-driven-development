---
lane: L1
pr: 452
follow_up_of: 428
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d4a12187 | 0 | 5 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e76b1856 | 0 | 1 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 4d43ebf2 | 0 | 1 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼の「gate・lint」のうち lint を、ユーザーの確認なしに限界へ回した。ユーザーに確かめ（B を選んだ後、件数 0/241 を示して A に切り替え）、回答を review-log/20261013-test-power-followups.request.md に足した。commit: e76b1856 |
| I1-2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | gate は escalation の reviewer だけが行を読み、既定の inline checklist と再実行の経路では読まない。inline-review-checklists.md § AC・契約準拠に項目を足し、再実行でも参照の行を残すようにした。commit: e76b1856 |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | accepted | 対照の変異の規定は、止める分岐がまだ無い（新しい副作用を条件つきで足す）AC には当てられない。PR 本文の限界に書いた |
| I1-4 | 独立-1 | medium | no | self-inflicted | product | accepted | テストはあり退行注入で落ちるのに、行や変異の記録だけが無いときも test-power（Round 消費）になる。PR 本文の限界に書いた |
| I1-5 | 独立-1 | medium | no | self-inflicted | product | accepted | 新しい押し返しの条件の事前の件数とコマンドが PR 本文に無い。測った数（0/241）とコマンドを PR 本文に書いた |
| I1-6 | 独立-1 | low | no | self-inflicted | product | accepted | 変異の戻し方が安全な手順（一時 commit）を指さず、並列バッチの RED と重なりうる。PR 本文の限界に書いた |
| I1-7 | 独立-1 | low | no | self-inflicted | product | fixed | 参照の行のパスが worktree からの相対でなく、Gate Batch の他 task を読まない。パスを .steering/<task>/tasklist.md にし、task ごとに 1 行とした。commit: e76b1856 |
| I1-8 | 独立-1 | low | no | self-inflicted | product | fixed | reviewer は 2 行の有無だけを見て、3 つ以上に分かれる AC の枝ごとの行の欠けを報告しない。「止める側（枝ごと）」にした。commit: e76b1856 |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が報告の条件の 4 つ目と、読む経路を書いていない。断片を直した。commit: e76b1856 |
| I1-A1 | 独立-1 | advisory | no | inherited | style | accepted | category の値をバッククォート付きで書き写している（既存の 2 か所と同じ書き方） |
| I1-A2 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Superpowers Benchmark Summary が抜粋から確かめられない。PR 本文に書いた。commit: なし（PR 本文） |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | accepted | inline の checklist の項目だけ「tasklist.md の各 task」と書き、Current Task（Gate Batch では batch の各 task）に絞っていない。完了済み・未着手の task の行の欠けを test-power にしうる。PR 本文の限界に書いた |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | testing-anti-patterns.md の参照元に inline-review-checklists.md § AC・契約準拠が載っていない。PR 本文の限界に書いた |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の件数が条件ごとに分かれず、コマンドも無い。条件ごとの件数と数えたスクリプトを PR 本文に書いた。commit: なし（PR 本文） |
| I2-A1 | 独立-2 | advisory | no | self-inflicted | style | accepted | category の値をバッククォート付きのリテラルで書いている |
| I2-A2 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 読む側の 2 か所が、行の書式の定義（TDD skill § Contract Surface Coverage）を指していない |
| I2-A3 | 独立-2 | advisory | no | inherited | doc-claim | accepted | Focus 3 の「止める側と境界の行が無い」が、片方だけ無いときに当たるかを読み分けられない |
| I3-1 | 独立-3 | medium | no | self-inflicted | product | accepted | 対照のテストに入れた変異の戻し方が決まっておらず、Steps 1 の一時 commit の制約が当たらない（未 commit の差分の破棄や共有の stash で戻しうる）。PR 本文の限界に書いた |
| I3-2 | 独立-3 | low | no | self-inflicted | product | re-reported | inline の確認の範囲が「tasklist.md の各 task」で、escalation の範囲と食い違う（I2-1 と同じ） |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | reviewer の入力の範囲が「必要なときだけ読む」のままで、Focus 3 は毎回読む前提になった。PR 本文の限界に書いた |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | 正本の参照元の一覧にクラス I の新しい参照元が無い（I2-2 と同じ） |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の件数が、確認が発火する条件と別の量を数えている。条件ごとの件数と正規表現を PR 本文に書いた。commit: なし（PR 本文） |
| I3-6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | クラス I の「見逃す不具合」に、止める側で起こすと定めた副作用が起きない不具合が入っていない。PR 本文の限界に書いた |
| I3-7 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が「項目を足した」と書くが、既存の項目に継ぎ足している。PR 本文を直した（断片は直していない）。commit: なし（PR 本文） |
| I3-A1 | 独立-3 | advisory | no | self-inflicted | product | accepted | 「テストが無い」と「行・記録の欠け」を分けて数えるための記録が無い |
| I3-A2 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | Superpowers Benchmark Summary を断片・抜粋から確かめられない（PR 本文には書いた） |
