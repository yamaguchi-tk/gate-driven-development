---
lane: L1
pr: 284
follow_up_of: 281
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a8676641c8bb9c22800a545b699b1b945796ea48 | 0 | 0 | 0 | 2026-10-02T19:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| C1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | planning reviewer の行は「正規表現・上限値・抽出位置」で閉じ、5d は「正規表現・上限値など」で開いていて、範囲の書き方が違う。PR 本文の限界に書く |
| C2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | skill の 8a に express の欄名（`外部依存`）の注記が無い（references の § 8a にだけある）。PR 本文の限界に書く |
| C3 | 独立-1 | low | no | self-inflicted | product | accepted | 5d で、fixture はあるが一部の値の形が無く、実データも取れないときの出口が無い。PR 本文の限界に書く |
| C4 | 独立-1 | low | no | self-inflicted | product | accepted | ③ の「テストで使う fixture は」の限定が理由より狭く、AC の根拠用の fixture が `.steering/` に置かれうる。PR 本文の限界に書く |
| C5 | 独立-1 | low | no | self-inflicted | product | accepted | テストの fixture 置き場は steering write guard の外なので、合成値への置き換えが漏れた実値は書き込み時に止まらない。PR 本文の限界に書く |
| C6 | 独立-1 | low | no | self-inflicted | product | accepted | planning reviewer の行は記録の有無だけを見て、落ちた件数が 0 でないのに修正も理由も無い状態を通す。PR 本文の限界に書く |
| C7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「12 桁の数字などを deny」は guard の条件（同じ行に account・role・arn:aws など）より広い。PR 本文に列挙 |
| C8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | skill の 8a は「通知」、§ 8a と requirements-gating は「通知 payload」。PR 本文に列挙 |
| C9 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の「文を短くした（内容は変えていない）」は Policy では書かない項目。PR 本文に列挙 |
| C10 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 未リリースの先行断片（20261002-external-format-sampling-first.md）が古い挙動を書いたまま。リリースの dry-run で版の節をそろえる。PR 本文に列挙 |
| C11 | 独立-1 | advisory | no | inherited | doc-claim | accepted | external-format-sampling-tokens.sh の冒頭コメントの範囲に Webhook が無い。PR 本文に列挙 |
| C12 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の推定 token の値に `at <sha>` が無い。PR 本文に書く commit: なし（PR 本文） |
| C13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence と Superpowers Benchmark Summary が抜粋では確かめられない。PR 本文に書く commit: なし（PR 本文） |
