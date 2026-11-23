---
lane: L1
pr: 703
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b7df7ef230270739650dba7741f38b7d1cda6622 | 0 | 2 | 0 | 2026-11-19 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 822c9b381ef13e7a78236eade71041e8b33d97cd | 0 | 1 | 0 | 2026-11-19 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 設計: 変えない（依頼の手段に合わせるだけ）。依頼は目的を出力の「そもそもどうあるべきか」の欄で求めるのに、基準の箇条だけを変えていた。欄の先頭に目的の引用を求める文を足した。commit: 702f48a9 |
| I1-2 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 設計: 変える（読み直しの規則を main の手順ではなく相談役の出力に載せる）。「2 本が一致していても main が読み直す」が main の手順に届いていなかった。`引いた決定:` がなし以外なら呼び出し側への 1 行を出力に書かせ、spec-autopilot の README の規則の例にも足した。commit: 702f48a9 |
| I1-3 | 独立-1 | low | no | self-inflicted | rule-gap | accepted | 読み直して対象の外と分かったとき・行が無いときの扱いを書いていない |
| I1-4 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の「過去の決定」を「ユーザーの決定」に狭めていた。引用の対象を書かれた文（ユーザーの決定・ADR・規則の文書・要件・前の確認の記録）に広げた。commit: 702f48a9 |
| I1-5 | 独立-1 | low | no | self-inflicted | measurement | fixed | 読む時期に数える `引いた決定:` を残す記録の場所が書かれていない。PR 本文に数える記録（subagent の transcript）を書いた。commit: なし（PR 本文） |
| I1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | copy-sources.tsv の commit がブランチの commit で、script の規定「main の commit」と食い違う |
| I1-7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の限界の「読む時期と撤去の条件」の行に種類が無い。限界の節の外へ移した。commit: なし（PR 本文） |
| I2-1 | 独立-2 | medium | no | self-inflicted | measurement | fixed | 再生の結果は出力の欄を変える前の本文のもので、PR 本文が tip の本文の結果と読める。PR 本文と notes に、修正後の 3 点は未測と書き、読む時期に目的の引用の有無を数える対象を足した。commit: なし（PR 本文） |
| I2-2 | 独立-2 | low | no | self-inflicted | rule-gap | accepted | 「書かれた文」の括弧に「など」が無く 5 種に限ると読める。欄名「引いた決定」と語がずれる |
| I2-3 | 独立-2 | low | no | inherited | rule-gap | accepted | human-check-template.md と autonomy.md の 2 本一致の手順に、読み直しと対象の外のときの扱いが無い |
| I2-4 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 写しの時点の commit がブランチの commit。repo は merge commit だけを許す設定（gh api で確認）なので、マージ後も main から届く |
| I2-5 | 独立-2 | low | no | self-inflicted | measurement | fixed | 発火条件を広げたのに、既存の記録で当たる件数が PR 本文に無い。未測と、記録に残らない入力を PR 本文に書いた。commit: なし（PR 本文） |
| I2-6 | 独立-2 | low | no | inherited | rule-gap | accepted | main の読み直しの条件が「退けていたら」で、出力の「なし以外なら」と食い違う |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 1 本で呼ぶ Fable・max にも「2 本が一致していても」が出る |
