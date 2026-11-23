---
lane: L1
pr: 404
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 73f80bcb | 0 | 2 | 2 | 2026-10-08T15:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | yes | self-inflicted | approval-path | accepted | commands/gdd-dev.md:188 の返答の分類が Round 上限のメニューだけを名指しし、Pre-PR の上限のメニューへの「OK」が STEP 2 の承認に進んでもう 1 周回る。旧#404 はこれを直さずにマージした（この巡の結果が届く前にマージしたため）。後続 PR（review-log/20261008-pre-pr-limit-fix.md）で直す |
| F2 | 独立-1 | medium | no | self-inflicted | product | next-pr | Pre-PR の上限で止めるときの停止理由と state の組（`blocked`・`Next Action=human_recheck_required`）が Handoff・再開検証と食い違い、4 択が人に届かない |
| F3 | 独立-1 | medium | yes | self-inflicted | approval-path | accepted | autonomy.md の一覧 3・語彙と human-check-template.md:708 に Pre-PR の上限が無く、事前回答の委任先が 4 つ目（限界として受け入れる）を採りうる。旧#404 はこれを直さずにマージした。後続 PR で直す |
| F4 | 独立-1 | medium | no | self-inflicted | product | next-pr | 上限に届いた原因が `missing-evidence` だけでも方式転換しか選べない |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 4 つ目の手順の草案の限界と state の値の文が Pre-PR 向けに読み替えられていない |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 「4 択の中から選ぶ」が、判断役が実際に採れる案より広く読める |
| F7 | 独立-1 | low | no | self-inflicted | style | next-pr | rollback-patterns.md:59 の句点の後に半角空白がある |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Skill RED-GREEN Evidence が材料の抜粋に無い（PR 本文には実測の結果を書いた） |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | next-pr | phase-progression.md:489・:689-692 と gdd-completion-check/SKILL.md:49 の要約が Pre-PR の上限のメニューに触れていない |
| A3 | 独立-1 | advisory | no | inherited | bookkeeping | accepted | 起動時の gitStatus と worktree HEAD から、tip より後の変更の中身が読めた（判断には使っていない） |
