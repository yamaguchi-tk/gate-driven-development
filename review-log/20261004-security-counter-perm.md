---
lane: L1
pr: 347
follow_up_of: 344
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fe7616bca70bb14127127b632e81bee4e06b8081 | 0 | 0 | 0 | 2026-10-04T10:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| N1 | 独立-1 | medium | no | inherited | product | next-pr | counter（validate-steering-write.py の record_deny）が、書き込み先の steering ファイルの絶対パスを平文で 0644 で書き、同じ state dir の秘匿水準を下回る（実装側）。次の PR |
| N2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | counter の消える条件が実装より強い（TTL では消えない、文字列を足さない書き込みでは消えない）。限界に書いた |
| N3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片が state dir を「chmod せず」と書き、本文の「last-turn-failure.json を書くときだけ chmod 700」と食い違う。限界に書いた |
| N4 | 独立-1 | low | no | inherited | doc-claim | accepted | § 4 の表の Write/Edit の行に counter の読み書きが無く、StopFailure の行も無い。限界に書いた |
| N5 | 独立-1 | low | no | inherited | doc-claim | next-pr | last-turn-failure.json は、同じ project の SessionStart か壊れた記録のときだけ消え、別の project のセッションでは残る。文書の「次の SessionStart が読んで消す」は強すぎる。次の PR |
| N6 | 独立-1 | advisory | no | inherited | doc-claim | accepted | bounce-log-schema.md の「TTL 3600s 経過で自動消滅」と置き場所 <sha1>.json が、実装（回数を 0 と読むだけ、先頭 16 桁）と SECURITY.md にそろっていない。PR 本文に列挙 |
