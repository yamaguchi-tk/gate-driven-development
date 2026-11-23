---
lane: L1
pr: 596
follow_up_of: 594
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5bb7e40c | 0 | 0 | 0 | 2026-10-28 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1-1 | 独立-1 | low | no | self-inflicted | 文書の記述 | accepted | tests/test_validate_plugin_check_inventory.py の冒頭コメントの検査の件数の計算が 48 のまま（実際は 47） |
| F1-2 | 独立-1 | low | no | self-inflicted | 文書の記述 | accepted | 断片が手順 9 の Existing Code Reading Evidence を requirements.md の節と書いている。実際の記録先は findings.md で、手順 9 の記録を機械で見るものはこの PR の前から無い。PR 本文はこの事実のとおりに書いた |
| F1-3 | 独立-1 | low | no | self-inflicted | 文書の記述 | accepted | DISTRIBUTION_READINESS 項 14・断片・prompt-contract-map が「AC と承認ポイントに 根拠:・計測:」と書く。lint が承認ポイントに求めるのは 根拠: だけ。PR 本文は書き分けた |
| F1-4 | 独立-1 | advisory | no | self-inflicted | 断片 | accepted | 断片の Removed に skill-body-budget の分、Affected Files に PR Bundle 2 の見出しと代表ファイルの変更が無い |
| F1-5 | 独立-1 | advisory | no | self-inflicted | 文書の記述 | accepted | prompt-contract-map の行の Prompt owner に brainstorming-steps.md（手順 9）が無く、Residual risk が読む範囲の広さを機械で見ないことを書いていない |
| F1-6 | 独立-1 | advisory | no | self-inflicted | テンプレート | accepted | テンプレート外の記述あり: PR 本文の抜粋の「Opus と Fable はどちらも撤去を推し」は前の PR の経緯。PR 本文から除いた |
| F1-7 | 独立-1 | advisory | no | self-inflicted | 記録 | accepted | ローカルの pytest のキャッシュに、巡の行を書く前の test_review_log_present の失敗が残る。記録の後に通ることを確かめる |
