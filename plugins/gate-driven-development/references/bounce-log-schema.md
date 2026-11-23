# Bounce Log Schema（正本）

fail-closed gate が同じ blocker で何度も差し戻されて ping-pong する無限ループを防ぐための共通 escape hatch。「N-1 回は通常通り差し戻す / N 回目は人間判断に escalate する」構造を全 gate で共通化する。**この仕様の唯一の正本**。各 skill / hook は inline で仕様を再掲せず、この reference を pointer で参照する。

## Schema（state.md に書く場合）

`state.md` に **専用セクション**（gate ごとに名前を分ける）を持ち、以下の行フォーマットで記録する。

```
## <Gate 名> Bounce Log
- <identifier-key> | bounced_at: <ISO 8601 timestamp> | bounce_count: <N>
```

- **`<identifier-key>`**: 「同じ blocker が繰り返された」と識別できる最小単位。gate ごとに実装が選ぶ（下表参照）
- **`bounced_at`**: 直近の差し戻し時刻
- **`bounce_count`**: 同一 identifier で発生した累計差し戻し回数

1 ラインで 1 identifier を表す。bounce が発生するたびに同じ行を更新（count を +1、timestamp 更新）する。

## 閾値と発動条件

- **skill-level gate**: `bounce_count >= 2`（2 回目の同一 bounce）で escape hatch 発動
- **hook-level gate**: `deny_count >= 3`（3 回連続 deny）で escape hatch 発動
  - hook は軽量な pattern match なので 1 回多く粘る。skill gate は重い reviewer 判定を含むため 2 回目で escalate する

## 発動時の出力テンプレート

```
⛔ 同じ <blocker の種類> での再差し戻しを検出したため <gate 名> を停止し <escalate 先> に委ねます

対象: <identifier-key>
繰り返された blocker: <具体的な欠落 / violation>
過去の bounce: <bounce_count> 回

Next Action: <human_recheck_required | gdd-systematic-debugging | warning-mode>
Reason: <gate 経由では同じ blocker が解消されないため何を見直すべきか>
```

## 発動後の処理

- **前提の点検**: skill-level の escape hatch が発動したら、出力を書く側が、escalate 先によらず、出力を書く前に `references/requirements-gating-steps.md` § レビューループの契約 1 の前提の点検をして `worklog.md` に `前提の点検:` 行を書く（hook-level の Steering Write Deny Counter は除く）
- **counter reset**: escape hatch 発動時点で該当 identifier の bounce_count を 0 に戻し、次回は通常 deny から再スタート
- **状態引き継ぎ**: hook では `STATE_TTL_SECONDS` 経過でも自動リセット

## Architecture Gate（same route 3回）

Superpowers の systematic debugging と同じく、同じ修正 lane で 3 回失敗した場合は「もう 1 回同じ fix を試す」ではなく **アーキテクチャを疑う**。GDD ではこれを state machine の route signal として扱う。

- **発動条件**: 同一 Current Task または同一 root cause で、same route（例: `implementation_fix_only` または `design_detail_only`）が 3 回連続で失敗した
- **見る入力**: `Fix Attempts`、`worklog.md` Error Log、Implementation Gate Bounce Log、PR Review Bounce Log、Refactor Gate Bounce Log
- **出力**: `gdd-systematic-debugging` に戻し、Architecture Gate として `design_detail_only` / `planning_rework_required` / `human_recheck_required` のいずれかを再判定する
- **推奨 route**: 修正のたびに症状が移動する、workaround が積み上がる、同一 root cause が形を変えて再発する場合は `planning_rework_required` を強く検討する
- **禁止**: Architecture Gate 発動後に、根拠なく同じ same route へ再投入しない

## ライフサイクル表（契機別の reset/継続ルール）

単一 gate の escape hatch 発動直後の reset だけでは、多 gate 共存・steering 越境・並列 batch 下での挙動が不定になる。以下の 5 契機 × 4 Bounce Log 軸で挙動を明示する。

| 契機                                                          | Implementation Gate Bounce Log                         | PR Review Bounce Log          | Refactor Gate Bounce Log                                                                | Steering Write Deny Counter                               |
| ------------------------------------------------------------- | ------------------------------------------------------ | ----------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **escape hatch 発動直後**                                     | 該当 identifier を reset to 0                          | 該当 identifier を reset to 0 | 該当 invariant-id を reset to 0                                                         | 該当 `(file_path, category)` を clear_deny（hook 実装済） |
| **`human_recheck_required`（scope delta 承認）**              | **全 identifier を reset to 0**（Fix Attempts と同期。reset 後の Fix Attempts 上限は 2/2 — `state-machine.md` § Remediation Loop Safety。`Gate Rounds` は reset しない。planning 差し戻し後の tasklist の作り直しでは、task と一緒に消える） | reset to 0                    | reset to 0                                                                              | 影響なし（hook state は steering 外）                     |
| **`planning_rework_required` → brainstorming 完了**           | **全 identifier を reset to 0**                        | reset to 0                    | **全 invariant-id を reset to 0**（rescope で invariant 体系が再定義されるため全 wipe） | 影響なし                                                  |
| **通常 fix / 継続（bounce 発火なし）**                        | 継続                                                   | 継続                          | 継続                                                                                    | 継続                                                      |
| **session restart（kernel panic / process kill からの再開）** | 継続（state.md 永続）                                  | 継続                          | 継続                                                                                    | TTL 3600s 経過で回数を 0 と読む（ファイルは残る）、それ以前は継続 |

**reset の責務主体**: reset は **戻り先 phase の入口 skill** が担う。具体的には:

- `planning_rework_required` → `gdd-brainstorming` が再入時点で state.md の 3 Bounce Log セクション（Implementation Gate / PR Review / Refactor Gate）を wipe する
- `human_recheck_required` → `gdd-brainstorming`（境界越え）または `gdd-design-gating`（部分修正）が再入時点で 3 Bounce Log を wipe する
- escape hatch 発動直後 → escape 先 skill（`gdd-systematic-debugging` / `human-check-waiting` 等）は reset しない。**次回該当 gate の入口 skill**（`gdd-completion-check` / `gdd-pr-review` / `gdd-refactor-planning`）が新サイクル開始時に該当行を reset to 0 する

**並列書き込みの直列化**:

- Bounce Log セクションは同じ state.md ファイルに per-task / per-identifier 行で蓄積されるため、並列 batch（`batch_mixed`）下では race リスクがある
- **serialization contract**: state.md への Bounce Log 書き込みは **main session のみが実行** する。subagent は「候補行」を tool 報告で返し、main session が 1 turn 内で順次 apply する
- 同一 identifier への同時書き込みは main session 側で「先着の bounce_count を採用 + 後着は無視」で解決（二重 +1 を防ぐ）
- 詳細は `phase-progression.md` § batch_mixed Serialization Contract を参照

**identifier-key の直交性（明示宣言）**:

以下の Bounce Log / Counter は `(Bounce Log 名, identifier-key)` の単位で直交しており、1 task 内で複数が同時に発火しても **互いに独立にカウント** する（cross-contamination なし）。

- Implementation Gate: `task-id + 欠落項目`
- PR Review: `file_path + missing_keyword`
- PR Review Cause Cluster: `PR + root cause カテゴリ`（所有 `gdd-pr-review-followup`。上の PR Review とは別カウンタ）
- Refactor Gate: `invariant-id`（+ `sha1:<first-8-of-sha1(invariant-text)>` 補助）
- Steering Write Deny: `(file_path, category)` の sha1 hash
- Requirements Gating / Design Gating / Task Breakdown: `Current Task + root causeカテゴリ`（形式は同一だが gate 名で名前空間が分離され別カウンタとして扱う）
- Implementation Gating Reviewer: `task-id + reviewer指摘カテゴリ`（`Fix Attempts` カウンタとは別軸）

Requirements / Design / Task Breakdown は identifier-key 文字列が同一になり得るが、gate 名でカウンタ空間が分離されるため cross-contamination しない。

## 既存実装一覧

| 実装                           | 配置                                                                                     | identifier-key                                                                       | 閾値   | escalate 先                                                                                                             |
| ------------------------------ | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| Implementation Gate Bounce Log | `state.md`（skill: `gdd-completion-check` Step 2a）                                      | `task-id + 欠落項目`                                                                 | `>= 2` | `gdd-systematic-debugging`（route recalibration。policy-level 変更が無い限り human check に戻さない）                   |
| PR Review Bounce Log           | `state.md`（skill: `gdd-pr-review` § 3b Step 7）                                         | `file_path + missing_keyword`                                                        | `>= 2` | `gdd-systematic-debugging`                                                                                              |
| PR Review Cause Cluster Log | `state.md`（skill: `gdd-pr-review-followup` § Design Review Checkpoint） | `PR + root cause カテゴリ`（PR 単位で生存し reset しない） | `hooks/scripts/lib/constants.py` の `PR_CHECKPOINT_CLUSTER_REPEAT_ROUNDS` | checkpoint trigger (c)（3 択の自律選択。(3) パッチ継続は同じループへ戻る例外で、次の 1 巡だけ有効） |
| Refactor Gate Bounce Log       | `state.md`（skill: `gdd-refactor-planning` § Behavior Preservation Invariants Re-check） | `invariant-id`（`design.md` の Behavior Preservation Invariants 行番号または見出し） | `>= 2` | `planning_rework_required`（同一 invariant が 2 回 violated = refactor scope では解決不能 / root feature 再設計が必要） |
| Steering Write Deny Counter    | `~/.claude/.gdd-hook-state/<sha1 の先頭 16 桁>.json`（hook: `validate-steering-write.py`。中身は回数と時刻だけ） | `(file_path, category)` の sha1 hash                                                 | `>= 3` | warning-mode allow                                                                                                      |
| Requirements Gating Bounce Log | `state.md`（skill: `gdd-requirements-gating`）                                          | `Current Task + root causeカテゴリ`（`実コード未読` / `AC仕様不備` / `スコープ不一致` 等）           | `>= 2` | `human_recheck_required`（ユーザー提示escalation）                                                                       |
| Design Gating Bounce Log       | `state.md`（skill: `gdd-design-gating`）                                                | `Current Task + root causeカテゴリ`                                                  | `>= 2` | `human_recheck_required`（ユーザー提示escalation）                                                                       |
| Task Breakdown Bounce Log      | `state.md`（skill: `gdd-task-breakdown`）                                               | `Current Task + root causeカテゴリ`                                                  | `>= 2` | `human_recheck_required`（ユーザー提示escalation）                                                                       |
| Implementation Gating Reviewer Bounce Log | `state.md`（skill: `gdd-implementation-gating`）                                 | `task-id + reviewer指摘カテゴリ`                                                      | `>= 2` | `既存の gdd-systematic-debugging`（`Fix Attempts` カウンタとは別軸）                                                     |
| debug bounce 計測（**escape hatch ではない。report-only 指標**） | `worklog.md` の `## Route Decision` 節（parser: `scripts/collect-gdd-telemetry.py` の `parse_route_decisions()`。受理面の正本は `references/phase-progression.md` § Bounce 計測の受理面） | なし（steering ごとの件数のみ。制御には使わない） | なし | なし（Stop hook 内の記録機構は削除済み。計測の正本は worklog 記録の事後パースに一本化） |

## 設計原則

1. **identifier-key は「同じ blocker」を識別する最小単位**。細かすぎると `count` が伸びず escape が効かず、粗すぎると無関係な差し戻しが混ざって誤発動する
2. **閾値は必ず固定値**。実行中に変えると AI が次回の試行コストを予測できない
3. **escape 先は必ず人間または上位 lane**。同じ gate に再度 routing しない（ループを作らない）
4. **発動時は必ず「何が繰り返されたか」を明示**。log だけ残して silent に通さない
5. **counter は TTL またはルート変更時にリセット**。無期限に蓄積させると別 issue の bounce と混ざる

## 新規 bounce log を追加するときの checklist

新しい fail-closed gate に escape hatch を付ける場合:

- [ ] identifier-key を決め、「同じ blocker の繰り返し」を一意に表現できるか検証
- [ ] 閾値を 2（skill）または 3（hook）で設定。独自値は使わない
- [ ] 発動時の出力テンプレート（上記）に沿ったメッセージを組む
- [ ] escalate 先が元の gate に戻らないルート（=ループしない）であることを確認
- [ ] 既存実装一覧表に 1 行追加する
