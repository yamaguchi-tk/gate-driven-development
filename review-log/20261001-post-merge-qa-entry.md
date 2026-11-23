---
lane: L1
pr: 旧#261
follow_up_of: 260
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 170d78ad2c44b78a7ffd747ceb4daa6cd08ca2b4 | 1 | 5 | 0 | 2026-10-01T02:25+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | a9f64ce363ea37788cdd708a7f43a89f963ad2e5 | 0 | 0 | 0 | 2026-10-01T02:38+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| E1 | 独立-1 | high | no | self-inflicted | product | fixed | 変更断片に User Action Required と Validation / Eval Impact の節が無く、version-not-consumed が FAIL する。commit: a9f64ce3 |
| E2 | 独立-1 | medium | no | self-inflicted | product | accepted | § 入口 が Scope を state.md の Approved Direction からしか読まず、requirements.md の Post-PR Completion Scope 節を見ない。近道の ① の medium で、follow_up_of があるので PR 本文の限界に書く |
| E3 | 独立-1 | medium | no | self-inflicted | product | accepted | runner と main が「自走上限の中か」を別々に判定し、判定を記録しない。Post-Return は blocked より先に § 入口 を見る。PR 本文の限界に書く |
| E4 | 独立-1 | medium | no | self-inflicted | product | accepted | Post-Return の blocked の分岐が return text に頼り、§ Subagent Return Output Contract（state.md を読み直す）と食い違う。PR 本文の限界に書く |
| E5 | 独立-1 | medium | no | self-inflicted | product | accepted | 再開で読む記録のうちマージ・デプロイ・QA の fail に書式が無く、再開の入口からこの節への参照も無い。PR 本文の限界に書く |
| E6 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | human-check-template の「PR 後の完了条件」行が、自走上限の値で許す操作を除いていない。PR 本文の限界に書く |
| E7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | done の stop を出す条件が completion-check の Re-entry 手順 7 と post-completion-pr-flow Step 4 で食い違う |
| E8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | requirements-gating-steps.md が、Scope の追跡先を Post-PR Scope Continuation だけと書いたまま |
| E9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | compact テンプレートの「OKで進む範囲」にマージ系の値が無い |
| E10 | 独立-1 | low | no | self-inflicted | style | accepted | post-merge-qa 手順 2 で、3 つの条件の後に両方の値に効く箇条が同じ階層で続く |
| E11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Codex・Cursor での QA 計画レビューの「手順 4 と同じ別コンテキスト（read-only）」が、手順 4 の実行用コンテキストと合わない |
| E12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片と PR 本文が Step 4 を Option 1 の中と書き、`マージまで` の絞り込みを落としている |
| E13 | 独立-1 | low | no | inherited | product | accepted | § 入口 が同じ Approved Direction の Post-PR 操作承認（manual merge required）を見ない |
| E14 | 独立-1 | low | no | inherited | doc-claim | accepted | post-merge-qa.md 冒頭の参照元に gdd-completion-check が無い |
| E15 | 独立-1 | advisory | no | self-inflicted | product | accepted | express の推定トークン予算に収まるかを読み取りだけでは確かめられない（validate-plugin.sh の skill-body-budget で確かめる） |
| F1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 前の PR の未リリース断片の dispatch gate の記述と、この PR が直した post-merge-qa.md § 限界 の記述が食い違い、この PR の断片は訂正を書いていない。前の断片はリリースの dry-run で直す（memory release-time-stale-fragment-fixes の 24） |
| F2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation / Eval Impact に Skill RED-GREEN の検証が書かれていない（PR 本文には書く） |
| F3 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | Validation 欄の括弧書き（assert は変えていない）は検証の種類ではない |
