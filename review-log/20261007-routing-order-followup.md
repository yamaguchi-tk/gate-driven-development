---
lane: L1
pr: 397
follow_up_of: 394
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d6c7d6cf | 0 | 1 | 0 | 2026-10-07T00:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | route の順序 | accepted | Express Guard（SKILL.md:172）は先に評価するものを ADR 2 件以上に限ったままで、3 回連続・承認後の 2/2 が Express では先に評価されない |
| F2 | 独立-1 | low | no | inherited | route の順序 | accepted | Worked Example の判定フロー 1 が「テスト設計不足？」だけで、Step 1 の先頭の判定を示していない |
| F3 | 独立-1 | low | no | inherited | route の順序 | accepted | phase-progression.md:415 の但し書き（procedural は上限でも短絡しない）が、承認後 2/2 で方式転換にする 1 行目と逆の向き |
| F4 | 独立-1 | low | no | inherited | route の順序 | accepted | silent failure・インフラ層の例外で Decision Tree ごと飛ばすと、Step 1 の上限の確認も飛ぶ |
| F5 | 独立-1 | low | no | inherited | compaction | next-pr | Context Compaction Resilience の読み直しに worklog.md の Error Log と adr.md が無い |
| F6 | 独立-1 | low | no | inherited | 参照元 | accepted | autonomy.md の参照元に human-check-template.md § 事前回答と subagent-dispatch.md § Post-Return Routing が無い |
| F7 | 独立-1 | low | no | inherited | 参照元 | next-pr | state-machine.md:291 の「Escalation Decision Table 2 行目」が、行が足されてずれ、今は 3 行目を指すべき |
| A1 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 新しい Step 1 が EDT を行番号で指し、§ Loop Safety の指し先も Escape Hatch の子項目にしか規定が無い |
| A2 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | Step 1 の 1 行に 3 つの問いをつないでいて、Yes/No がどの問いに掛かるか読みにくい |
| A3 | 独立-1 | advisory | no | self-inflicted | 断片 | accepted | 停止条件が変わるのに断片の User Action Required が「なし」 |
