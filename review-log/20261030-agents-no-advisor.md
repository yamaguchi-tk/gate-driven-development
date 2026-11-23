---
lane: L1
pr: 617
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2e762f9d | 0 | 1 | 0 | 2026-10-30T17:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | Sonnet の worker を、依頼の条件（追加の費用だけか）ではなく本文をそろえる契約を理由に止めた。Sonnet ＋ Fable は公式が勧める組なので、止めてよいかをユーザーに確かめた。ユーザーが止めたままにすると決めた（2026-10-30） |
| r1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「advisor は費用だけを足す」が根拠（ぶれの境目の +1.7 点、Opus high の組だけ）より強く、Sonnet・medium の agent にも貼っている（worker 3 本:28、simplifier:43、qa-runner:31） |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「社内の agentic coding のベンチマーク」が誰の社内か分からない（同じ 5 か所） |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「GDD の agent はすべて呼ばない」が、定義を持たない Plan・Explore・general-purpose の起動を含まず、散文で保証しないことも書いていない（断片:7） |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | User Action Required が「なし」だが、動いているセッションは開き直すまで古い定義で動く（断片:24） |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 未リリースの 20261021-worker-final-check-advisor.md の「相談は残す」が、同じ版でこの PR と食い違う |
| r1-7 | 独立-1 | low | no | self-inflicted | style | accepted | 断片の Summary の「1.7 点（ぶれの境目）で」に「上がり」が抜けている（断片:7） |
| r1-8 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Validation に、worker の本文が同じであることを固定するテストの名前が無い |
| r1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 公式の資料の URL が、配る定義と PR 本文の抜粋に無い |
| r1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「advisor を agent ごとに切る設定は無い」の確かめ方が PR 本文の抜粋に無い |
| r1-11 | 独立-1 | advisory | no | self-inflicted | product | accepted | マージ後に advisor の呼び出しが 0 になったかを数える方法と時期が書かれていない |
