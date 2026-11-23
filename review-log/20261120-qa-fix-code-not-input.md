---
lane: L1
pr: 718
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d38a001f | 0 | 2 | 0 | 2026-11-20 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 83574b40 | 0 | 0 | 0 | 2026-11-20 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| 独立-1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 観点 0（依頼の原文から外れた）。規則を QA の報告と人に戻るときの 2 か所だけに置き、普通の会話に届かないことを確かめずに限界にしていた。main と相談役が全部の推奨に当てる § 選ぶときの基準 に 8 として足し、写しもそろえた。commit: d378fd2a |
| 独立-1-2 | 独立-1 | medium | no | self-inflicted | rule-conflict | fixed | 原因に挙げた global のフォールバックの原則との関係を規則が扱っていない。基準 8 に、読み方を決める直しはフォールバックに当たらないと書いた。commit: d378fd2a |
| 独立-1-3 | 独立-1 | low | no | self-inflicted | coverage | accepted | 列挙: QA の報告の規則が fail だけで、inconclusive と手順 3 のデプロイの失敗の報告に当たらない（基準 8 は main と相談役の推奨全体に当たる） |
| 独立-1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 列挙: 入れ直しを推奨にしないが言い切りすぎ。基準 8 に、コードを直せないときは読み手と理由を添えて入れ直しを推してよいと書いた。commit: d378fd2a |
| 独立-1-5 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 新しい発火条件に当たるなら、件数を目的の節に書く |
| 独立-2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | QA の報告と人に戻るときの文が「入れ直させる案を推奨にしない」と無条件で、基準 8 の例外（コードを直せないとき）より狭い |
| 独立-2-2 | 独立-2 | low | no | self-inflicted | coverage | accepted | 列挙: 基準 8 は、同じ値がほかの環境で今の形で入っている場面と、利用者の規則が形を名指しで決めている場面を扱わない |
| 独立-2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | autopilot.md の「相談役の定義」に場所が無く、何を推すかが本文から消えた |
| 独立-2-4 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文に、件数の置き場と、読む時期・撤去の条件が無い |
| 独立-2-5 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | copy-sources.tsv の commit が据え置きで、写しの報告に基準 8 の分が出続ける |
| 独立-2-6 | 独立-2 | advisory | no | inherited | doc-claim | out-of-diff | spec-autopilot の README が /autopilot から相談役を呼ばないと書いたまま |
