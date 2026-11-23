---
lane: L1
pr: 407
follow_up_of: 404
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus)（材料: 旧#404 の独立-1 の出力と main の直し方の草案。Opus は草案の大筋を採り、次の 4 点を変えるよう推奨した。証跡だけの差し戻しを上限に数えない分岐は入れずに限界にする〔カウント定義の行はテストが固定し、手順 1 が先に +1 するので「数えない」は値を戻すことになる〕。subagent-dispatch.md の post-return routing に、`Resume From=human-check-waiting` なら HITL の表示を先にして debugging を起動しない 1 句を足す。state-machine.md の Round 上限の項は広げず、procedural 降格対象外の句だけを広げる。phase-progression.md と completion-check の要約の直しを必須にする。main は 4 点とも採ったので、食い違いは残らず max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-08T16:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | aa6f56f5 | 0 | 1 | 0 | 2026-10-08T17:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c6bdd28b | 0 | 0 | 0 | 2026-10-08T18:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 断片の「人は修正指示で証跡の書き直しを指示できる」は、#10 STEP 1 で修正指示より先にメニューへの返答の分類が判定されるので成り立たない。断片から外し、PR 本文の限界は「軽い出口は無い」と書く commit: c6bdd28b |
| F2 | 独立-1 | low | no | self-inflicted | product | accepted | subagent-dispatch.md:421 の但し書きが、`<gdd-stop reason="human-check-waiting">` の出力と、表示の前の事前回答・自律モードの判定を書いていない（兄弟の routing の形と違う） |
| F3 | 独立-1 | low | no | self-inflicted | product | accepted | display-integrity の HITL lint は Handoff の形を受け付けず、/gdd-dev 1 回あたり最大 2 回押し戻される（Round 上限の経路も同じ）。lint 側の変更は block gate なので別 PR |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | phase-progression.md:489・:690 の主節「`blocked` で停止」が残り、上限未満の差し戻し（`<gdd-stop>` を出さない）と食い違う |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd-completion-check SKILL.md:137 の PR 作成不可時の `blocked` 停止が、Pre-PR の上限の `human-check-waiting` と食い違う |
| F6 | 独立-1 | low | no | inherited | product | accepted | Round 上限・Pre-PR の上限の state の組は、/gdd-dev resume の build candidate と planning candidate の両方に当たり、競合か build として扱われうる |
| F7 | 独立-1 | low | no | inherited | doc-claim | accepted | human-check-template.md § 即再承認の短絡形から、方式転換メニューへの返答が除かれていない |
| F8 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 受け入れた限界を断片に書いていた（CHANGELOG.md § Policy に反する） commit: c6bdd28b |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 委任先・判断役が採れる案の括弧の列挙を、正本（§ 事前回答 3・autonomy.md の止まる案）を指す形にした方が誤読しにくい |
| A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | 事前回答の経路には同じ上限の 2 回目で止まる規定が無い（PR 本文の限界に開示済み） |
| A3 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が PR 本文にあるかを push の前に確かめる |
| A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 旧い規定で上限に止まった steering（`Next Action=human_recheck_required`）は、更新後に再開すると fail-closed になりうる |
| A5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | gdd-dev.md:188 の「Round 上限」が requirements-gating の Round 上限にも読める |
| B1 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 断片の Summary が PR 本文の変更内容 7 項目のうち 3 つ（procedural 降格の対象外、4 つ目の草案の読み替え、要約からの指し先）に触れていない。§ Policy は全部を書くことを求めていない |
