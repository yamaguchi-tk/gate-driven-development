---
lane: L1+
pr: 353
follow_up_of: 347
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（counter の JSON から path・category を外す案。Opus は、読む実装が無いので外すことに賛成し、chmod と自動削除は足さない、テストはキー集合の一致とファイルが 1 個あることで確かめる、を推した。食い違いは last-turn-failure.json の文言を別の PR にするかだけで、ユーザーの指示でこの PR に入れた） | - | 0 | 0 | 0 | 2026-10-04T11:40+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 10de79db2f4bb2c0503fc64f02da1be9b38f8506 | 0 | 0 | 0 | 2026-10-04T12:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 692591e3fb0cc524384c47a87b9ffdabe41ed6c7 | 0 | 1 | 0 | 2026-10-04T12:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P0 | 方針メモ | advisory | no | self-inflicted | scope | accepted | Opus は last-turn-failure.json の文言修正を別の PR にすることを推した。ユーザーの指示でこの PR に入れた |
| Q1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | last-turn-failure.json の消える条件が実装より狭い（compaction の直後は残す、symlink はリンクだけ消す）。commit: 692591e3 |
| Q2 | 独立-1 | low | no | inherited | doc-claim | fixed | counter の「deny されずに通ると消す」が実装より広い（行を消すだけの Edit では消さない、size の counter は size で deny されない書き込みのたびに消す）。commit: 692591e3 |
| Q3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 20261004-security-counter-perm.md の「counter がパスを平文で持つ」が、この PR で古くなる。リリースのときに版の節を直す。PR 本文に列挙 |
| Q4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | テストの docstring の「実際の入口」は、登録された wrapper ではなく Python 本体の直接起動。PR 本文に列挙 |
| R1 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | last-turn-failure.json の消える・残る条件を散文で列挙し、正本の表（test_session_start_last_turn_failure_contract.py の _TABLE）にある「state dir が symlink なら読まず消さない」などが落ちた。変更断片も同じ規則を書き直している。限界に書いた |
| R2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | counter を消す契機の文が実装と 3 点で食い違う（peer_turn_state_write・steering_line_break は消さない、completed_reviewed_by はもっと広く消える、size で deny されても category の counter は消える）。限界に書いた |
| R3 | 独立-2 | low | no | inherited | doc-claim | accepted | bounce-log-schema.md（counter の仕様の正本）が、違反の無い書き込みで counter を消すことを書いていない。限界に書いた |
| R4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋が、足した消える・残る条件と counter を消す契機を書いていない。commit: なし（PR 本文） |
| R5 | 独立-2 | low | no | inherited | doc-claim | accepted | SECURITY.md の表の SessionStart の読み取り範囲が実装と合わない（learned-patterns.md は読まない、source・requirements.md などが無い）。限界に書いた |
| R6 | 独立-2 | low | no | inherited | doc-claim | accepted | last-turn-failure.json の中身の記述が、API エラー本文の断片を含みうる error_details を名指ししていない。限界に書いた |
| R7 | 独立-2 | advisory | no | inherited | doc-claim | accepted | Hook の表に StopFailure などの行が無く、見出しの「4 種類」も合わない。PR 本文に列挙 |
