---
lane: L1
pr: 367
follow_up_of: 360
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2fac0c462c1d6892a11482ce52753dfeaa9cf5f1 | 0 | 1 | 0 | 2026-10-04T22:59+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 7810c6286bba0d7c0c712503a80c1fbd78b3e313 | 0 | 0 | 0 | 2026-10-04T23:11+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | Classify の部品の決め方の言い換えが正本より狭く、block しない hook のうち再開経路 (a)(b) に届く欠陥の例外を落とし、「ファイルの場所」という正本に無い基準を足していた。言い換えをやめて同節を指す形にした（ユーザーの「修正可能なら修正して」で取り込み）。commit: 7810c6286bba0d7c0c712503a80c1fbd78b3e313 |
| L1 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 根拠を `Findings:` 行に残せと書いたが、書式（:208）に欄が無い。PR コメントだけにした。commit: 7810c6286bba0d7c0c712503a80c1fbd78b3e313 |
| L2 | 独立-1 | low | no | inherited | doc-claim | fixed | 戻し先「reviewer が付けていればその値」が、Minor・P2 など尺度の外の値を扱っていない。読み替えと、読み替えられないときの値を書いた。commit: 7810c6286bba0d7c0c712503a80c1fbd78b3e313 |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「比較 diff の外を指す受け入れ判定の『範囲外』」が実際の使われ方より狭い。中身に触れず「受け入れ判定の『範囲外』とは別」にした。commit: 7810c6286bba0d7c0c712503a80c1fbd78b3e313 |
| L4 | 独立-1 | low | no | inherited | doc-claim | fixed | トリアージ表の深刻度の選択肢に advisory が無い。足した。commit: 7810c6286bba0d7c0c712503a80c1fbd78b3e313 |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 20261004-always-high-undecided.md:11・:12・:24 が、この差分で書き換えた戻し先・上限の書き方を説明したまま残る。リリースの dry-run で直す |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の「（pr-review-followup では out-of-scope）」が比較 diff の外を指すように読める。手順 3 の out-of-scope と書いた。commit: 7810c6286bba0d7c0c712503a80c1fbd78b3e313 |
| Q1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | gdd-receiving-code-review:135 に足した advisory は、単独で使うとき参照先の reviewer-common.md の尺度（High/Medium/Low）に定義が無く、レーン名の advisory とも重なる。follow_up_of のため PR 本文の限界に書いた |
| Q2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Summary が「部品の決め方を書いた」のままで、実際は § 常時 High を指す形。Changed の「言い換えずに」も main との差ではない。follow_up_of のため PR 本文の限界に書いた |
| Q3 | 独立-2 | low | no | self-inflicted | product | accepted | reviewer の値を High / Medium / Low / advisory に読み替えるとき、Minor・P2 など間に読めるラベルの迷ったときの向きが無い。follow_up_of のため PR 本文の限界に書いた |
| Q4 | 独立-2 | advisory | no | self-inflicted | style | accepted | 「main が分けた値」の main が両 skill で定義されていない（subagent が Classify を実行することもある）。PR 本文に列挙 |
| Q5 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 根拠の記録先から `Findings:` 行を外したので、PR コメントを投稿できないとき（gh が使えない）の置き場が無い。PR 本文に列挙 |
| Q6 | 独立-2 | advisory | no | inherited | doc-claim | accepted | gdd-pr-review 3g（SKILL.md:215）に、判定できないときと戻すときの扱いが無く、PR の前後で同じ指摘の扱いが揃わない。PR 本文に列挙 |
