---
lane: L1
pr: 686
amends: 20261116-pr681-accepted-fixes.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3cff6c0385d41ba8f6d57f915f04e321aafecef2 | 0 | 1 | 0 | 2026-11-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 3dd4f7b500988fc88829d56628f7f018a293e584 | 0 | 0 | 0 | 2026-11-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | approval-path | fixed | 設計: 変えない（印で決める設計のまま、足す主体と場面を 1 か所に決める）。印を足す主体と時点が無く、subagent が足すと委任の経路で行が届かず、誰も足さないと表示した steering でも書かれる。依頼の「書く条件がずれる」に当たるので直した。commit: 27099d65 |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | compact の「行に」がどのファイルの行か書いていない。compact から印の文を外し、印は main が足す形にした。commit: 27099d65 |
| I1-3 | 独立-1 | low | no | self-inflicted | approval-path | accepted | 「Stage Continuation の最後の Stage」が、継続が途中で止まって Step 4 で done する steering を含むか読めない |
| I1-4 | 独立-1 | low | no | self-inflicted | approval-path | accepted | 途中の Stage の steering の場所が Lane に無く、読めないときの扱いも無い |
| I1-5 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 未リリースの断片（pr675・pr679・pr681）に、置き換えた書く条件の記述が残る |
| I1-6 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の 13 件のうち I1-10（PR 684 の本文の書き漏れ）の扱いが見えない。マージ済みの PR 684 の本文は書き換えず、この PR の本文で開示した。commit: なし（PR 本文） |
| I1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | README・TROUBLESHOOTING・onboarding が、cancelled も含めて必ず `## 👤 次にすること` を返すと読める |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | gdd-dev.md から消した 1 文は残りの行と重なりきっておらず、正本の entry-intent.md に同じ規則がある。PR 本文の書き方を直した |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | Step 4 の括弧が、印の無い行を「一次表示で本人に見せていない行」と言い換え、見せたが確かめられない行を含まないと読める |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片が、印を足さない場合を 2 つしか書いていない（確かめられないときが無い） |
| I2-3 | 独立-2 | low | no | self-inflicted | product | accepted | runtime budget の上限に収まるかが差分からは示せない（tip の見積もりは 30207 で上限 30208 の中） |
| I2-4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 印の文字列と条件が full 版にしか無く、main は返事のたびに full 版を開く必要がある |
| I2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 消した 2 文の理由が、変更断片と PR 本文で違う |
