# ADR: PR レビューループに「設計見直し checkpoint」を新設し、同一原因判定を root cause カテゴリへ統一する

- **日付**: 2026-09-11（決定・PR 作成時に蒸留）
- **状態**: Accepted
- **関連**: `plugins/gate-driven-development/CHANGELOG.md` の `[0.43.0]` entry / `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md` / `plugins/gate-driven-development/references/state-machine.md` / `.steering/20260910-design-review-checkpoint/design.md`

## Context

PR-W8 の T-2 が 10 時間・12 finding で発散した実測（同一 root cause の finding が形を変えて再発し、1 件ずつのパッチを積み続けても収束しなかった）を受け、PR 後レビューループ（`gdd-pr-review-followup`）に「パッチを続けるべきか、設計を見直すべきかを機械的に判定する」仕組みが欠けていた。既存の `PR Review Follow-up Attempts`（上限 12）はレビュー待ちの polling wake 数を数えるカウンタで、実際にレビュー結果を受け取った巡数（設計品質の劣化を測る単位）とは別物であり、巡数そのものを上限管理する field が無かった。

また、同一原因の再発判定（`references/state-machine.md` § Remediation Loop Safety、`skills/gdd-implementation-gating/SKILL.md`）は finding の位置（`file:function`）の一致で行っていた（W-27）。同じ根本原因が別ファイル・別関数に現れる場合（本セッションの T-1〜T-3 自身で 4 回連続発生した「test-power」欠陥が好例）を検出できず、再発の実態を過小評価していた。

## Decision

1. **設計見直し checkpoint の新設**（`skills/gdd-pr-review-followup/SKILL.md` § Design Review Checkpoint）。4 トリガー（(a) 巡数 `PR Review Rounds` ≥ `PR_CHECKPOINT_ROUNDS_THRESHOLD`、(b) 自傷率 `fix_origin: self-inflicted` の割合、(c) クラスタ再発 `PR Review Cause Cluster Log`、(d) commit 比率）で発火し、AI が「(1) 設計し直し / (2) スコープ縮小 / (3) パッチ継続」の3択を自律選択する（人間へは事後報告。AC / scope / policy / security boundary が変わるときと同一 PR で2回目の (1) だけ人間へ戻す）。判定不能な入力は非発火ではなく**強制発火**に倒す（fail-closed）。
2. **新規カウンタ `PR Review Rounds`**（`hooks/scripts/lib/constants.py` の `PR_REVIEW_ROUNDS_MAX=5`）を新設し、既存 `PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS=12`（polling wake 数）とは別軸で管理する。
3. **レビュー対応プロトコルを4段へ再構成**（Step 3〜5）: (a) 受け入れ判定 → (b) 原因クラスタリング（root cause カテゴリで束ね、`fix_origin: self-inflicted | inherited` を付与）→ (c) クラスタ判定（パッチ可 / 設計し直し）→ (d) 1巡の修正範囲（merge を止めるものと同じクラスタの medium だけを直す）。
4. **W-27: 同一原因判定を `file:function` から root cause カテゴリへ統一**（`references/state-machine.md` § Remediation Loop Safety、`skills/gdd-implementation-gating/SKILL.md`、`skills/gdd-systematic-debugging/SKILL.md`、`references/phase-progression.md` の4ファイル）。あわせて新規 ADR 発行 ≥2（同一 Current Task の remediation が `adr.md` に entry を2件追記）を、root cause 一致を待たない独立トリガーとして追加した。
5. **スコープ縮小**: 当初案にあった「pre-push / pre-PR / merge gate の人間承認済み非退行 high 受理経路」（AC-23〜AC-27）は、本 PR の受入条件（`references/self-review-lanes.md` § followup 周回時のレーン要求 の既存契約、`hooks/scripts/lib/merge-gate-evidence.sh` の受理述語）を変える必要があり、設計レビューで指摘された契約の穴（2件）を埋めるための追加検討が必要と判明したため、別 PR（S-2）へ切り出した。本 PR は checkpoint 本体・対応プロトコル・巡数カウンタ・W-27 の4点に閉じる。

### 却下した代替案（Rejected Alternatives）

- **判定不能を非発火（安全側 silent skip）に倒す案**: 却下。記録喪失や parse 失敗を「発火しない」側に倒すと、収束しない PR が checkpoint を一度も経由せず放置される fail-open になる。判定不能は強制発火に固定した。
- **`PR Review Rounds` を `PR Review Follow-up Attempts` に統合する案**: 却下。前者は「レビュー結果を受け取った巡数」、後者は「レビュー待ちの polling wake 数」で単位が異なる（CI 再実行や polling wake だけでは巡数は進まない）。混在させると上限判定が意味を失う。
- **checkpoint の3択を人間が毎回選ぶ案**: 却下。ユーザー承認（2026-09-10「Option B」判断ポイント2）により、AI が自律選択し人間へは事後報告する方式を採用した（AC / scope / policy / security boundary の変更を伴うときだけ人間へ戻す）。

## Why

同一原因の再発を「finding の位置」で数える設計は、原因が形を変えて再発するケース（本セッション自身で4回実測）を見逃す。checkpoint が無い状態では、収束しない PR レビューループは `PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS`（polling wake 上限）に達するまで気づかれず、その間ずっと 1 件ずつのパッチが積まれ続ける。巡数・自傷率・クラスタ再発・commit 比率という4つの独立したシグナルで機械的に検知し、AI が自律的に方式転換を判断できるようにすることで、PR-W8 T-2 のような発散を PR 作成後の早い段階で止める。

## Consequences

**新規の状態フィールド**: `state.md` に `PR Review Rounds` / `checkpoint:` 行 / `PR Review Cause Cluster Log` を追加した。既存 PR で followup 対応中（`Iteration` 行が既にある PR）に本バージョンへ upgrade した場合、`PR Review Rounds` は自動初期化されず、次回 followup で (a) 判定不能として checkpoint が強制発火する（設計し直し / スコープ縮小の2択。詳細は CHANGELOG `[0.43.0]` § User Action Required）。

**既知の限界（独立セルフレビューで検出、non-blocking のため本 PR では未対応）**:

- `fix_origin` の算出が reviewer 由来の `origin: this-diff`（PR 全体 scope）と当巡の比較 diff を OR しており、自傷率トリガー (b) が退化しうる
- `- **Origin**: remediation / <Current Task>` の `<Current Task>` がプレースホルダのまま置換規則が未確定で、実タスク名に置換するかリテラルのまま書くかで計数の正しさが変わる。また1 remediation ラウンド内で複数 producer が同時に ADR を起票すると、発散していなくても閾値 2 件に誤って到達しうる（PR 旧#68 レビュー対応で producer・route 確定側・成功経路・handoff は実装済みだが、この2点は未対応）
- `PR Review Cause Cluster Log` の `bounce_count` の加算契機（巡単位）と実装（クラスタ確定のたび）が厳密には一致せず、同一巡での過加算・恒久 latch のリスクがある
- 「同一 finding 3 回 → blocked」の重複定義4箇所中3箇所が Escape Hatches の優先順位追記に追随していない
- root cause カテゴリ統一により、既存 `Implementation Gating Reviewer Bounce Log` と新ルールが同一シグナルを別軸で二重計測する形になっている

いずれも measurement-design の refinement であり、checkpoint の中核契約（判定不能→強制発火の fail-closed、merge gate の受理述語 `high 0 / blocking 0` は不変）を損なわない。follow-up task で対応する。

**参照**: `.steering/20260910-design-review-checkpoint/design.md`、`.steering/20260910-design-review-checkpoint/adr.md`（ADR-1〜22、詳細な設計判断の正本）、`.steering/20260910-design-review-checkpoint/handoff/followup-seed-ac23-27.md`（S-2 の seed）。
