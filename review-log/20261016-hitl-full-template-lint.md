---
lane: L1+
pr: 536
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 84cda5c8 | 0 | 3 | 0 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 4a277825 | 0 | 0 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 断片が「両方を置いた HITL は重複した要約の検査に落ちなくなる」と書くが、lint の判定は変えていない。commit: 4a277825 |
| F2 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 出力テンプレートの承認サマリの欄名を元に戻しても、どのテストも落ちない（案内文に同じ語があり、出ないことを見る文の陽性の対照も無い）。commit: 4a277825 |
| F3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 新しい reject の分岐（宣言の節の外）に当たる件数とコマンドが PR 本文に無い。数えると 0 件だったので、規定どおり分岐を外した。commit: 4a277825 |
| F4 | 独立-1 | low | no | self-inflicted | test-power | accepted | 宣言の節より前のマーカーのテストが returncode だけを見ていて、常に通る |
| F5 | 独立-1 | low | no | self-inflicted | test-power | accepted | 具体例には無回答時のデフォルトが無く、宣言の検査が具体例の側では走らない |
| F6 | 独立-1 | low | no | inherited | test-power | accepted | 最後の承認ポイントの既定範囲の検査だけが、宣言の節の外まで伸びる |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | _decision_item_field_errors の docstring と受理文法の文が、新しい起点に追随していない |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 外した節が持っていた冒頭の除外の欄が骨組みから無くなり、断片の「承認サマリと中身が同じ」は事実より広い |
| F9 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files に、変えたテスト 2 本が無い |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 限界の PR検証後の次の導線の行の種類が依頼より狭いでなく、行き先も無い |
| F11 | 独立-1 | low | no | inherited | doc-claim | accepted | 具体例の承認ポイントが 8 要素のうち 4 つを欠き、lint の固定欄の検査を全部すり抜ける |
| F12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 欄名の改名は、Stop hook につながる display-integrity にも効く |
| F13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | docs/METRICS_BASELINE.md に改名前の綴りが残る |
| F14 | 独立-1 | advisory | no | self-inflicted | product | accepted | 全量テストをローカルで回したことの届け先が材料に無い |
| G1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 限界の「借りる形は変更の前から残る」は compact の並びだけ正しい。full の並びは前は宣言の検査で落ちていたので、この PR で届くようになった（PR 本文で書き直した） |
| G2 | 独立-2 | low | no | self-inflicted | product | accepted | 宣言の節より前のマーカーは reject されるが、出る文が「判断に影響する前提 がありません」で実態と合わない |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 受理文法の文と lint のコメントが、マーカーを起点から文書末尾まで数えることと、区間が見出しをまたぐことを書いていない |
| G4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 具体例には無回答時のデフォルトが無く、具体例の側の宣言の検査の assert は常に成り立つ |
| G5 | 独立-2 | low | no | self-inflicted | test-power | accepted | 宣言の節が 2 つのテスト名は一般に落とすと読めるが、落ちるのは件数が合わないときだけで、2 つ目以降の宣言は読まない |
| G6 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 実測の数に、測ったコマンドとどの版の lint で測ったかが無い（PR 本文に書いた） |
| G7 | 独立-2 | advisory | no | inherited | product | accepted | 具体例の承認ポイントが 8 要素の 4 つを欠き、X-53 の検査を丸ごと素通りする |
| G8 | 独立-2 | advisory | no | inherited | product | accepted | 承認ポイント数の宣言の桁数に上限が無く、4,300 桁を超えると int() が例外を投げる（exit 1 で reject 側） |
| G9 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 全量テストを回した tip と結果の記録が材料に無い |
