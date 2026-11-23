---
lane: L1
pr: 357
follow_up_of: 354
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（旧#346・旧#354 の限界のうち設計の判断が要る 5 項目。実測: tasklist.md 224 本で並列 22、Completion Rounds の行 2、state.md 203 本で差し戻し中の route 0、worklog 100 本で design_detail_only 1。Opus は main の案の誤りとして、Scope Drift Counter が歯止めになるのは planning_rework_required を除く 2 route だけ、5/5 は作り直しで届かない、rollback-patterns.md の Refactor Gate の保存先は tasklist.md で :75 は削除、残した commit の AC は coverage inspection か未カバー分の RED の 2 択、を指摘し、全部採った。作り直しの印を worklog に書いて数えを区切る Opus の案は main と食い違ったので、信号 ① で Fable に 1 回相談した。Fable は仕組みを足さず限界として書く main の案を推奨した〔頻度に比べて過剰、誤りは安全側〕ので、それを採った） | - | 0 | 0 | 0 | 2026-10-04T09:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2cd8d993 | 0 | 3 | 0 | 2026-10-04T09:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | b9bb4008 | 0 | 2 | 0 | 2026-10-04T10:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| N1 | 独立-1 | medium | no | self-inflicted | 文言 | fixed | マトリクスの Scope Drift Guard 行で absent を Refactor Gate Status ではなく Bounce Log の列に入れていた。断片・PR 本文の記述とも合わない。この PR の変更の誤りなので近道でも直した。commit: b9bb4008 |
| N2 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 同じ行の Fix Attempts が「継続」で、作り直しで振り直すという本文と食い違う。commit: b9bb4008 |
| N3 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 断片・PR 本文の Scope Drift Guard 行の記述が差分と合わない（N1 で解消）。commit: b9bb4008 |
| N4 | 独立-1 | medium | no | self-inflicted | 文言 | fixed | gdd-task-breakdown の SKILL.md の作り直しの規定に、引き継ぎと並列 batch の例外が無い。commit: b9bb4008 |
| N5 | 独立-1 | medium | no | self-inflicted | 文言 | fixed | Gate Rounds が引き継ぐもの・途切れるもののどちらにも入っていない（state-field-tiers.md・bounce-log-schema.md は human_recheck では reset しないと書く）。commit: b9bb4008 |
| N6 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 途切れる数えの列挙に 3/3 と、task id を含む Bounce Log の行が無い。commit: b9bb4008 |
| N7 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 「作り直しをまたぐ歯止め」が実際の保証より強く読める（Scope Drift Guard は上限ではない）。commit: b9bb4008 |
| N8 | 独立-1 | advisory | no | inherited | 作り直しの引き継ぎ | accepted | 方向が変わる作り直しでも Completion Baseline を引き継ぐので、新しい方向の最初の completion-check が差分スコープで走る |
| N9 | 独立-1 | advisory | no | self-inflicted | 文言 | fixed | 並列 batch の例外を指す文の「の 4」が 2 通りに読め、親の箇条も例外を受けていない。commit: b9bb4008 |
| P1 | 独立-2 | medium | no | self-inflicted | 文言 | accepted | Gate Rounds の正本（fixed-models.md:41）が、作り直しで task と一緒に消えることに追随していない |
| P2 | 独立-2 | medium | no | self-inflicted | 文言 | accepted | 承認後の 2/2 について、マトリクスの human_recheck 行・bounce-log-schema.md:61 などは効く前提、§ リセットは途切れる前提で割れている |
| P3 | 独立-2 | low | no | self-inflicted | 文言 | accepted | bounce-log-schema.md:61 の追記に主語が無く、Bounce Log の規定と読める |
| P4 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 「作り直しをまたいで数え続けるのは Scope Drift Counter」は言い過ぎ（Completion Rounds・Cumulative Changed Files なども続く） |
| P5 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 途切れる上限の列挙に Architecture Gate が無い |
| P6 | 独立-2 | low | no | self-inflicted | 文言 | accepted | § Remediation Loop Safety の 3/3 と rollback-patterns.md:165 で、「途切れる」と「食い違えば大きい方」が並ぶ |
| P7 | 独立-2 | low | no | self-inflicted | 文言 | accepted | gdd-task-breakdown の SKILL.md の参照が、手順 2 の 3 項目のうち 2 項目だけ |
| P8 | 独立-2 | low | no | self-inflicted | 文言 | accepted | refactor-planning の再検証（pending の書き戻し）と、作り直しでの absent が割れる（遷移先は同じ） |
| P9 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 除外句が Route In Progress の理由の括弧の中にあり、例外を route で分けると読める |
| P10 | 独立-2 | low | no | self-inflicted | 文言 | fixed | PR 本文の「次の 4 点」が 5 項目と合わない。commit: なし（PR 本文） |
| P11 | 独立-2 | low | no | self-inflicted | 文言 | fixed | PR 本文の限界に、task id を含む Bounce Log の行が無い。commit: なし（PR 本文） |
| P12 | 独立-2 | low | no | inherited | 文言 | accepted | Refactor Gate Status の許容値が pending を初期状態と書いている（作り直し後と手順 8 の初期枠は absent） |
| P13 | 独立-2 | low | no | inherited | 文言 | out-of-diff | Refactor Gate Status の置き場所が state-machine.md:217（Next Action の直前）と refactor-planning SKILL.md:139（直後）で違う |
| P14 | 独立-2 | advisory | no | self-inflicted | 文言 | accepted | gdd-task-breakdown の SKILL.md の runtime budget を確かめられない（validate-plugin.sh の skill-body-budget は OK） |
| P15 | 独立-2 | advisory | no | self-inflicted | 作り直しの引き継ぎ | accepted | Completion Baseline を引き継ぐ副作用（方向転換後の最初の Round も差分スコープ）が限界に無い |
