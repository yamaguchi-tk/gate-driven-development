# State Machine（正本）

> **所有**: state field の意味、phase 遷移表、routing / resume source、更新責任、Autonomous Continuation
> **上位正本**: `self-contained-contract.md`（fail-closed 条件、自己完結条件）
> **参照元**: 全 phase skill、`commands/gdd-dev.md`、`entry-intent.md`、`phase-progression.md`
> **関連**: `state-field-tiers.md`（state field の Tier 分類と phase ごとの Minimum Required Set）

`gate-driven-development` の routing / resume / formal state の正本。契約上の優先順位は `references/self-contained-contract.md` が上位で、このファイルは state field の意味、phase 遷移、routing source、更新責任を具体化する。遷移ルールを変える場合はこのファイルを更新し、各 skill はここを参照する。

Machine-readable constraints are synchronized with `references/state-schema.json`. Build phase prechecks use `Human Check Status=approved`; never use the non-schema `auto_confirmed` status.

state.md の各 field を**「常に必須」「phase に入ったときに必須」「条件付き」**で分類した Tier 表は `state-field-tiers.md` に切り出している。**新規 steering の最小テンプレート**（Express / trivial 用）もそちらに収録。本ファイルは個別 field の意味と状態遷移ルールに集中する。

## 契約境界

- このファイルが正本にするのは次だけ:
  - state field の意味
  - phase 遷移
  - routing / resume source
  - state の更新責任
- 次は `references/self-contained-contract.md` を正本とする:
  - forbidden な root 依存
  - plugin-managed Cursor symlink alias を除く same-name ambient asset 衝突時の fail-closed
  - 許可される外部依存と version 条件
  - `Latest Tech Context` と最新技術情報の確認ルール
  - `Verification` の固定 schema
  - acceptance criteria
- README と各 skill は、routing / resume はこのファイルを、自己完結条件は `references/self-contained-contract.md` を参照する。

## Single Source of Truth（workflow phase）

workflow phase（= session のどこまで進んだか）の正本は **active worktree の `.steering/<task>/state.md` にある `Resume From` フィールドのみ**。他のファイル・他のフィールドに phase を複製しない。

task identity（= どの task を現在対象として扱うか）の正本は **Task Binding Registry `.gdd/tasks/<task_id>/binding.json`**。`state.md` は phase の正本だが、自然文 resume / status で対象 task を決める正本ではない。Task Binding Registry は current worktree / branch / steering path を束ねる identity registry であり、`scripts/gdd_task_binding.py` が作成・解決を担当する。

### 理由

過去、`gdd-dev.local.md` の `workflow_phase` フィールドと `state.md` の `Resume From` が両方 phase を保持していた。メインセッションが片方だけ更新すると 2 箇所が食い違い、Stop hook の判定が不安定化する構造リスクがあった。phase の正本を 1 箇所に固定すれば、この drift は起こり得ない。

### 各ファイルの責務

| ファイル                    | 保持するもの                                                                                                 | phase を持つか        |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------- |
| `.steering/<task>/state.md` | `Resume From`, Review Status 群, Approved Direction, Reviewer Selection, Last Handoff Summary, Blocked Since | **Yes（唯一の正本）** |
| `.claude/gdd-dev.local.md`  | `session_id`, iteration, 前回 continuation prompt, active steering pointer（相対パス）                       | **No**                |
| `.gdd/tasks/<task_id>/binding.json` | `task_id`, `worktree_path`, `branch`, `steering_path`, `state_path`, `canonical_goal`                | **No（identity 正本）** |

`gdd-dev.local.md` の `detected_phase` フィールドは model routing 用のヒント（stop hook が最後に検出した phase を記録）であり、workflow phase の正本ではない。レガシーの `workflow_phase` フィールドが残っている場合は stop hook が自動で `detected_phase` にマイグレーションし、`workflow_phase` を削除する。

### Stop hook の判定順序

1. subagent の tool_result に `<gdd-stop reason="...">` があれば stop
2. active steering の `state.md` の `Resume From` が `human-check-waiting` なら stop（disk Resume From フォールバックで stop するのはこの値のみ）。他の reason（`blocked` / `cancelled` / `done` / `clarification-needed` / `external-review-waiting` / `staging-verification-blocked` / `auth-waiting`）は `<gdd-stop reason="...">` marker 経路（rule 1）で扱われ、rule 2 の disk フォールバック対象ではない。design フェーズは `gdd-task-breakdown` へ直接 handoff するため stop-worthy ではない。design 中に `human_recheck_required` が発動した例外は `Resume From=human-check-waiting` に戻る
3. どちらも該当しなければ autonomous continuation を許可

Allowed stop reasons: `done` / `cancelled` / `human-check-waiting` / `blocked` / `clarification-needed` / `external-review-waiting` / `auth-waiting` / `staging-verification-blocked`。
`clarification-needed` は artifact 作成前の intake 停止専用で、`state.md` の `Resume From` には書かない。requirements readiness を満たすまで複数回発火してよい。

`gdd-dev.local.md` の `detected_phase` は model routing 用ヒントとしてのみ使用（Stop hook の判定順序には含まれない）。

### pre-brainstorming 期間の扱い

`gdd-brainstorming` 実行前は `state.md` が存在しない。通常は brainstorming が同一ターン内で human-check-waiting まで到達するため、`state.md` 不在 = continuation 許可で実害はない。

例外として、Clarification Loop が発火した場合は `state.md` を作らず `<gdd-stop reason="clarification-needed">` で停止する。これは workflow phase ではなく intake の質問待ちなので、ユーザー回答後は回答を元の `$ARGUMENTS` に追記して readiness を再評価する。まだ曖昧なら loop を継続し、ready になった時点で Step 1 から formal workflow を再開する。

### subagent の state 更新契約

planning / review 系 subagent は、return 前に自身で `state.md` の `Resume From` を最終値まで書き切ること。メインセッションは subagent から戻ったあと `Resume From` を read-back して期待値であることを確認し、それから `<gdd-stop>` を出力する。subagent が `Resume From` を更新しないまま return するのは contract 違反。read-back 失敗時は `<gdd-stop reason="blocked">` で停止し、手動修正または subagent 再実行を促す（blocked 出力フォーマットは `references/output-format.md` § 具体例: blocked 参照）。

## state machine の外側

- `gdd-pre-workflow-brainstorming` は相談専用の pre-workflow lane であり、この state machine の対象外
- `gdd-pre-workflow-brainstorming` は `.steering/...`、`.cursor/plans/*.plan.md`、`Resume From`、`Next Action` を所有しない
- `gdd-pre-workflow-brainstorming` から formal workflow に入るときは、常に `/gdd-dev` -> `gdd-brainstorming` から開始する
- active steering の解決は `gdd-pre-workflow-brainstorming` ではなく、formal handoff 後の `gdd-brainstorming` が行う

## 保存場所

- **active worktree 側 `state.md`** の `Gate Status` セクション:
  - `Requirements Review Status`
  - `Planning Reviewer Selection`
  - `Design Review Status`
  - `Human Check Status`
  - `Resume From`
  - `Route In Progress`（差し戻し route の文脈。route 完了で `none` にクリア）
  - `Approved Direction`（human check 承認後に記録。routing source にはしない）
  - `Plan Revision`（段階計画の最新 revision。`requirements.md` の `Plan Revision Ledger` と一致させる。routing source にはしない）
  - `Current Stage`（現在対象の Stage ID。未着手なら `planning`。routing source にはしない）
  - `Next Stage`（次に進む Stage ID または `task-breakdown`。routing source にはしない）
  - `Stage Continuity Source`（段階連続性の正本への参照。`requirements.md#Implementation-Sequence-Plan` または `tasklist.md#Execution-Plan`）
  - `Planned Follow-up Stage Lane`（計画済み後続 Stage の seed 参照。`requirements.md#Planned-Follow-up-Stage-Lane`。routing source にはしない）
  - `Last Handoff Summary`（直近の phase 遷移時に出力された Handoff Summary。session 再開時の context 復元に使う。routing source にはしない）
- **active worktree 側 `tasklist.md`** の `Review Status` セクション:
  - `Implementation Reviewer Selection`
  - `gdd-implementation-reviewer`
  - `gdd-security-reviewer`
  - `Refactor Gate Status`
  - `Next Action`
- **active worktree 側 `tasklist.md`** の `Verification` セクション:
  - completion 判定の正本
- **active worktree 側 `adr.md`**:
  - optional な decision log
  - 重要な意思決定、却下した代替案、その理由、影響を残してよい
  - `Resume From` / `Next Action` の routing source には使わない
- **active worktree 側 `worklog.md`**:
  - optional な全 phase 共通の追記型作業ログ
  - planning 中の調査メモ、試した案、ボツにした理由
  - build 中のデバッグ過程、根本原因分析
  - review 指摘への対応方針
  - `adr.md` は「決まったこと」、`worklog.md` は「過程」
  - `Resume From` / `Next Action` の routing source には使わない
- **project-scoped `.claude/gdd-dev.local.md`**:
  - explicit な `/gdd-dev` run の Stop hook 用 loop state
  - same session に返す continuation prompt と iteration を保持する
  - `Resume From` / `Next Action` の routing source には使わない
- **project-scoped `.gdd/tasks/<task_id>/binding.json`**:
  - natural-language resume / status で現在 task を解決する identity registry
  - `worktree_path` と `branch` と `steering_path` を束ねる
  - `Resume From` / `Next Action` の phase source には使わない
  - `state.md` 更新後は `scripts/gdd_task_binding.py upsert-from-state` で更新する
- 新 contract では tracked な root 側 `.steering` を canonical state の保存場所に使わない
- legacy root steering に `Active Worktree Path` / `Active Branch` が残っていても、新 contract の state field としては更新しない

## state field の意味

- `Requirements Review Status`:
  - human check 前に行う requirements review gate の状態
  - `requirements.md` と lightweight `design.md` skeleton が human check に出せる品質かを表す
- `Planning Reviewer Selection`:
  - `gdd-requirements-gating` と `gdd-design-gating` がどの reviewer を `selected` / `waived` にしたかの累積的な正本
  - requirements gate で `gdd-planning-reviewer` を記録し、design gate で `gdd-security-reviewer` の判断を追記する
  - `references/reviewer-selection.md` に従った applicability 判断と根拠を `state.md` に残す
- `Design Review Status`:
  - `gdd-design-gating` における AI reviewer 群の detailed design gate の状態
  - human check 後に具体化された `design.md` の gate 成否を表す
- `Human Check Status`:
  - `requirements.md` に書かれた要件・受入条件・実装方針に対する人間承認の状態
  - human check は必須 gate なので `waived` を許可しない
  - 実装後の再人間チェックは `human_recheck_required` に限り、常態化させない
  - `changes_requested` は方向性レベルの全面見直しが必要な差し戻しに使う。承認ポイントの一部だけを直して再提示する間は `pending` を維持し、`human-check-waiting` を続ける
- `Approved Direction`:
  - human check 承認後に記録する方向性レベルの承認
  - 方向性の 1 行要約 + 自走範囲 + 人間に戻す条件を保持する
  - `gdd-systematic-debugging` が `design_detail_only` で自走するか `human_recheck_required` に escalate するかの補助判定に使う
  - routing source にはしない（`Resume From` / `Next Action` が正本）
  - human check で再承認された場合は最新の承認内容で上書きする
- `Plan Revision`:
  - `requirements.md` の `Plan Revision Ledger` の最新 revision ID
  - active follow-up / amendment / human_recheck_required / planning_rework_required で段階計画が変わるたびに更新する
  - resume / compact 後に「どの段階計画を前提にしているか」を復元する補助コンテキスト
  - routing source にはしない（`Resume From` / `Next Action` が正本）
- `Current Stage`:
  - `Implementation Sequence Plan` または tasklist `Execution Plan` 上の現在対象 Stage ID
  - planning 中は `planning`、tasklist 作成前は `task-breakdown` を使ってよい
  - routing source にはしない。人間向け status / resume handoff のアンカーとして使う
- `Next Stage`:
  - 次に実施・再計画・再承認する Stage ID
  - まだ Stage 実行に入っていない planning handoff では `workflow-handoff:<phase>` を使う（例: `workflow-handoff:task-breakdown`）。workflow phase 名を裸で書かない
  - `Current Stage` と合わせて、HITL 停止時や再開時に「どこまで出来ていて次に何が残るか」を説明するための補助コンテキスト
  - routing source にはしない
- `Stage Continuity Source`:
  - 段階連続性の正本ファイルへの参照
  - tasklist 作成前は `requirements.md#Implementation-Sequence-Plan`、tasklist 作成後は `tasklist.md#Execution-Plan` を既定にする
  - `human_recheck_required` / `planning_rework_required` で既存 tasklist が stale tasklist になった場合、再 task-breakdown が完了するまでは `Stage Continuity Source=requirements.md#Implementation-Sequence-Plan` に戻す。古い `tasklist.md#Execution-Plan` を source として使わない
  - quick (express) で `Implementation Sequence Plan` が `N/A - single-stage express` の場合は `requirements.md#Implementation-Sequence-Plan (N/A - single-stage express)` と書く
  - source が存在しない場合、standard / 複数段階 quick (standard) では requirements-gating または task-breakdown に戻して補完する
  - routing source にはしない
- `Planned Follow-up Stage Lane`:
  - `requirements.md#Planned-Follow-up-Stage-Lane` への参照
  - `Implementation Sequence Plan` に `PR Boundary=follow-up-pr` / `post-merge-verification` がある場合に記録する
  - 計画済み後続 Stage の `Pending Stage ID` / `Next Planned Stage` / `Tracking Destination` / `Human Recheck` を復元する補助コンテキスト
  - routing source にはしない。後続 Stage を開始するには、ユーザーの明示入力または Manual Merge Continuation 後の新 steering seed が必要
  - `Tracking Destination` が無い場合は completion-check で補完し、`done` の最終説明から後続 Stage を落とさない
- `Route In Progress`:
  - `gdd-systematic-debugging` が route を決定したときに記録する、現在進行中の差し戻し route
  - 値: `design_detail_only` / `implementation_fix_only` / `human_recheck_required` / `planning_rework_required` / `requirements_amendment` / `batch_mixed` / `none`
  - `requirements_amendment` は AC / requirements / lightweight design skeleton の差分 artifact update lane。停止 route ではない
  - `requirements_amendment` は差分作成後に `human_recheck_required` / `planning_rework_required` / `none` のいずれかへ解消する
  - セッション中断後の再開時に「なぜこの phase に戻ったか」を明示的に伝える
  - route の修正が完了し次の phase に進んだ時点で `none` にクリアする
  - routing source にはしない（`Resume From` / `Next Action` が正本）
- `batch_paused_for_hotfix`:
  - `batch_mixed` 進行中にユーザーが緊急 Hotfix Lane 開設を明示した場合のみ `true`。通常時は `false` または未設定
  - 値: `true` / `false`（未設定 = `false` 扱い）
  - `true` の間は subagent 起動禁止。Hotfix 完了後に `false` に戻して保持された `Batch Route Decisions` で batch 再開
  - 詳細は `phase-progression.md` § Batch-Hotfix Bridge Contract / Case 2 を参照
  - routing source にはしない
- `Last Handoff Summary`:
  - 直近の phase 遷移時に出力された Context Handoff Summary のテキスト
  - phase 遷移ごとに上書き更新する（履歴は保持しない。最新 1 件のみ）
  - session 再開時に SessionStart hook が Quick Reboot context に注入し、前セッションの最終決定事項を即座に復元する
  - **Session continuity guard**: SessionStart hook は Task Binding Registry と current worktree / branch が一意に一致するときだけ `[gdd:reboot]` に task 名 / Current Task / Last Handoff を含める。`CLAUDE_CODE_SESSION_ID` や `.claude/gdd-dev.local.md` の `session_id` は soft signal として使ってよいが、一致しても registry / current worktree の解決を上書きしない。registry が無い、不一致、または複数候補の場合は `[gdd:paused]` に格下げし、旧 task 詳細を出さない。これは別セッションの `20260601-example-review-task` のような古い task が、直近の別作業（例: 機密情報アウトプット禁止 / LLM Judge）の判断材料に混入するのを防ぐため。
  - **SessionStart 契約（欠損 fail-safe）**: SessionStart hook は以下の 3 状態を明確に区別する:
    1. **field 欠落**（`Last Handoff Summary=` 行自体が無い）: `Last Handoff Summary` は routing source ではないため、これ単独では `[gdd:blocked]` にしない。Quick Reboot に Last Handoff を含めず、`Resume From` / `Next Action` など canonical field でのみ復帰判断する
    2. **field 存在 + 値が空文字**: `<EXTRACTION_FAILED:<ISO8601>>` の sentinel に書き換え、`tasklist.md` の `Current Task` + `state.md` の `Approved Direction` から最小 Handoff を **自動合成**して Quick Reboot に注入する（抽出失敗の痕跡を残しつつ再開可能性を確保）
    3. **field 存在 + 値あり**: そのまま注入
  - `[gdd:blocked]` は `Resume From` / `Human Check Status` / `Route In Progress` / canonical `tasklist.md` の `Next Action` など、routing source になる canonical field が欠落した場合にだけ使う
  - sentinel 検出は hook の diagnostic log に残し、次 Stop hook で正常な Handoff Summary が書き込まれれば上書きされる
- `Blocked Since`:
  - `gdd-completion-check` が外部前提不足で `blocked` 停止した時刻（ISO 8601）
  - 初回 blocked 時に記録し、既に記録済みなら上書きしない（最初の blocked 時刻を保持）
  - blocker 解消で `blocked` 以外の状態に進んだ時点で削除する
  - SessionStart hook が 24 時間超の blocked を警告する
  - routing source にはしない（`Resume From` / `Next Action` が正本）
  - Handoff Summary が無い初期状態では空文字列または未設定
- `Operation Level`:
  - タスク開始時に確定した運用レベル（`light` / `standard` / `strict`）
  - `gdd-brainstorming` が `references/operation-levels.md` に従って解決し、`state.md` に記録する
  - タスク完了まで変更しない（開始時のレベルで最後まで進む）
  - routing source にはしない（gate / reviewer の適用範囲の判定にのみ使う）
  - 監査時に「このタスクはどの運用レベルで実行されたか」を追跡可能にする
- `Started At`:
  - steering 作成時刻（ISO 8601）
  - same-worktree の active steering 候補が複数あるとき、最新候補の選別に使う
  - **`state.md` では必須**。write hook は canonical field（`Resume From` / `Human Check Status` / `Route In Progress`）を含む `state.md` 更新で `Started At` が無い場合、書き込み自体を deny する
- `Resume From`:
  - planning phase の resume source
  - `tasklist.md` が routing source になる前は、どの planning phase に戻るかを表す
  - build フェーズの戻り先を持つ用途には使わない
  - **active steering では必須**。SessionStart / UserPromptSubmit hook は `state.md` から `Resume From` を抽出できない場合、canonical state 欠落として fail-closed に倒す
- `Human Check Status`:
  - `pending` / `changes_requested` / `approved` の 3 値を持つ review gate 状態
  - planning と build の境界判定（3-field gate check）に使う
  - **active steering では必須**。SessionStart / UserPromptSubmit hook は `state.md` から `Human Check Status` を抽出できない場合、canonical state 欠落として fail-closed に倒す
- `Route In Progress`:
  - 差し戻し route / artifact update lane の文脈 (`implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required` / `requirements_amendment` / `batch_mixed` / `none`)
  - remediation 完了時または terminal 遷移時に `none` に戻す
  - **active steering では必須**。SessionStart / UserPromptSubmit hook は `state.md` から `Route In Progress` を抽出できない場合、canonical state 欠落として fail-closed に倒す
- `Next Action`:
  - `tasklist.md` が routing source になった後の formal な次工程
  - `tasklist.md` が存在しても `Requirements Review Status=approved`、`Design Review Status=approved`、`Human Check Status=approved` の 3 つが揃うまでは draft planning artifact とみなし、routing source にしない
  - draft / stale tasklist の間は planning phase 名を保持してよいが、routing の正本には使わない
  - `Human Check Status=approved` 後は、`human_recheck_required` / `planning_rework_required` / `design_detail_only` または fail-closed 条件が出ない限り、formal workflow は phase ごとの追加人間承認を待たずに `Next Action` に従って進む
  - advisory review lane はこれを所有しない
  - **canonical tasklist では必須**。`Requirements Review Status=approved` / `Design Review Status=approved` / `Human Check Status=approved` が揃った後に `tasklist.md` から `Next Action` を抽出できない場合、SessionStart / UserPromptSubmit hook は fail-closed に倒す
- `Implementation Reviewer Selection`:
  - `gdd-implementation-gating` が current task に対してどの reviewer を `selected` / `waived` にしたかの **per-task 一時状態**
  - task が `Completed Tasks` に移るときに次の task 用に `pending | reason: none` にリセットされる
  - リセット前に、completed task block 末尾に `Reviewed by: <selected reviewer 名>` を 1 行付記して選定履歴を残す
  - 同じ `Current Task` の再レビューでは scope が変わらない限り再利用し、変更時は `selection_change_reason` を残す
  - `gdd-completion-check` では Implementation Reviewer Selection の現在値ではなく、各 completed task の `Reviewed by` 行と全 task が `Completed Tasks` に到達している事実を監査根拠にする
- `Refactor Gate Status`:
  - 全タスク完了後に `gdd-refactor-planning` が横断的リファクタ点検を実行したかの状態
  - `gdd-implementation-gating` が全タスク完了を検出したときに `Refactor Gate Status` の値で次の遷移先を決める
  - `tasklist.md` の `Review Status` セクション内、`Next Action` 行の直前に配置する
  - Express パスでは `Refactor Gate Status` を使わない（completion-check / refactor gate ともにスキップ）
  - routing source にはしない（`Next Action` が正本）。`Refactor Gate Status` は `gdd-implementation-gating` の分岐条件としてのみ使う

## 許容値

- `Requirements Review Status`:
  - `pending`, `in_review`, `changes_requested`, `approved`
  - 必須項目: `status`, `evidence`, `updated_by`, `updated_at`
- `Design Review Status`:
  - `pending`, `in_review`, `changes_requested`, `approved`
  - 必須項目: `status`, `evidence`, `updated_by`, `updated_at`
- formal reviewer status:
  - `pending`, `in_review`, `changes_requested`, `approved`, `waived`
  - 必須項目: `status`, `evidence`, `updated_by`, `updated_at`
  - `waived` のときのみ: `waiver_reason` 必須。他へ遷移するときは古い `waiver_reason` を残さない
- reviewer selection record:
  - `pending`, `selected`, `waived`
  - reviewer ごとに `reason` 必須
  - block 全体として `updated_by`, `updated_at` 必須
  - `Implementation Reviewer Selection` では追加で `selection_change_reason` を持てる
- `Human Check Status`:
  - `pending`, `changes_requested`, `approved`
  - 必須項目: `status`, `evidence`, `updated_by`, `updated_at`
  - human check は必須 gate なので `waived` を許可しない
- `Resume From`:
  - `gdd-brainstorming`, `gdd-requirements-gating`, `human-check-waiting`, `gdd-design-gating`, `gdd-task-breakdown`
- `Refactor Gate Status`:
  - `pending`, `in-progress`, `pass-empty`, `pass-applied`
  - `pending`: 初期状態（`gdd-refactor-planning` 未実行）、または refactor task 実装中に Behavior Preservation Invariants 違反で abort し、通常 task として再計画した場合（`gdd-completion-check` が検知して `gdd-refactor-planning` を再起動する）
  - `in-progress`: `gdd-refactor-planning` が改善機会を検出し、refactor task を追加した
  - `pass-empty`: `gdd-refactor-planning` が改善機会なしと判定した
  - `pass-applied`: refactor task が全て完了し `gdd-implementation-gating` を通過した
  - Express パスでは使用しない（absent のまま）
  - **`pending` 再起動 routing**: `gdd-completion-check` は tasklist.md 先頭で `Refactor Gate Status=pending` を検出したら `Next Action=gdd-refactor-planning` に戻し、invariant 違反で通常 task 化された改善を再度評価する
- `Next Action`:
  - `gdd-brainstorming`, `gdd-requirements-gating`, `human-check-waiting`, `gdd-design-gating`, `gdd-task-breakdown`, `gdd-test-driven-development`, `gdd-subagent-driven-implementation`, `gdd-implementation-gating`, `gdd-systematic-debugging`, `gdd-refactor-planning`, `gdd-completion-check`, `done`, `cancelled`
- `Route In Progress`:
  - `design_detail_only`, `implementation_fix_only`, `human_recheck_required`, `planning_rework_required`, `requirements_amendment`, `none`, `batch_mixed`
  - `requirements_amendment` は active follow-up で AC / requirements / lightweight design skeleton の差分を artifact に反映している途中の artifact update lane。停止 route ではない。差分作成後に `human_recheck_required` / `planning_rework_required` / `none` のいずれかへ解消し、terminal state へ持ち越さない
  - `batch_mixed` は並列 batch 中に複数タスクが異なる route を同時発火した場合専用。per-task の内訳は `tasklist.md` の `Batch Route Decisions` に記録する（詳細は `phase-progression.md` § 並列 batch 複数 route 同時発火）
  - `batch_mixed` 時の `Next Action` は「最 severe な route の遷移先」に従う（`planning_rework_required > human_recheck_required > design_detail_only > implementation_fix_only` の順）
  - `requirements_amendment` は severity ordering には入れない。差分 artifact 更新の作業状態であり、承認待ちに戻す場合は `human_recheck_required`、要件壁打ちへ戻す場合は `planning_rework_required` へ解消してから扱う
  - **`batch_mixed` の消去タイミング**: batch 内の全タスクが resolve（impl-gate 通過 / abort / 次 phase に合流 / **Hotfix Lane へ退避**）した時点で `Route In Progress=none` に戻し、`tasklist.md` の `Batch Route Decisions` ブロックも削除する。「Hotfix Lane へ退避」は当該 task 行を `Batch Route Decisions` から外し、worklog.md に `Hotfix Diverted` エントリを残すことで resolve 扱いとする（詳細は `phase-progression.md` § Batch-Hotfix Bridge Contract）。次 batch 開始時に残存していたら integrity check で fail-closed（`batch_mixed` と新 batch の route 混在は前提崩壊）
  - **Batch Route Decisions の carry-over**: batch pause 後の再開 batch には carry-over しない。再開時は `gdd-task-breakdown` が新しい依存グラフと新 `Batch Route Decisions` ブロックを作る
- `Post-Merge Follow-up Mode`:
  - 値: `none` / `read_only_verification` / `amendment` / `hotfix`
  - PR merge 後に追加実装・確認を始める new steering のみ持つ。元 steering は `done` のまま保持し、この field を後追いで書き込まない
  - `amendment` / `hotfix` の場合、実装場所は latest default branch から作った新 worktree に限定する。merge 済み branch / 元 worktree を再利用している場合は state 不整合として fail-closed
  - `read_only_verification` の場合、実装差分を作らない。差分が必要になった瞬間に `amendment` または `hotfix` として新 worktree を作る
- `Origin PR` / `Origin Branch` / `Origin Merge Commit` / `Base Branch` / `Base Commit`:
  - PR merge 後 follow-up の new amendment / hotfix steering が持つ trace fields
  - `Origin Branch` は先行 PR の branch、`Base Branch` / `Base Commit` は新 worktree 作成時点の default branch を指す
  - `Origin Merge Commit` が不明な場合は `unresolved:<reason>` として HITL に出す。未確認のまま元 branch を再利用しない
- `batch_paused_for_hotfix`:
  - 値: `true` / `false`（未設定は `false`）
  - `true` の間は `Route In Progress=batch_mixed` を保ちつつ subagent 起動禁止
  - Resume 時の整合性検証: `batch_paused_for_hotfix=true` かつ Hotfix Lane 側の state.md が存在しない場合は fail-closed（前提崩壊）
- `Fix Attempts`:
  - `0` 以上の整数。`Current Task` セクション内に保持
  - **Current Task → Pending Tasks 逆戻り時の扱い**（`design_detail_only` の tasklist 差分リセット起因）: Fix Attempts を **継続**（逆戻りは修正失敗ではなく scope 再設計のため、カウントをそのまま保持する）。継続することで「逆戻り後に再び impl_fix_only を連打しても escape hatch に到達する」blind loop 防止機能が維持される。task 再分割（T-N → T-Na/T-Nb）の場合は、分割前のカウントを **分割後の最初の実装 task（T-Na）に継承**し T-Nb は 0 リセット（分割 gaming 防止のため継承は 1 task のみ）
- `Scope Drift Counter`:
  - `0` 以上の整数。`state.md` に保持（steering 単位でカウントする）。`gdd-systematic-debugging` が `design_detail_only` を選択するたびに +1 する。task が `Completed Tasks` に移っても reset しない（steering 全体の累積）
  - **+1 の正本タイミング（クラッシュ耐性）**: `gdd-systematic-debugging` が route を確定した直後ではなく、**`state.md` の `Route In Progress=design_detail_only` 書込みが永続化完了した瞬間** を真の増分コミット点とする。route 決定〜state.md 書込前のクラッシュからの復帰時、integrity check で `Route In Progress` と worklog.md 最新 Route Decision が不一致な場合、**または worklog.md に Route Decision 行自体が存在しない場合**（worklog 書込みもクラッシュで未完了）、いずれも fail-closed（自動加算しない）。「比較対象なし」は「不一致」と同等に扱う。二重 +1 も二重漏れも silent に発生させない
  - **逆戻り時の扱い**（Current Task → Pending Tasks、`design_detail_only` の tasklist 差分リセット起因）: Counter 自体は **継続**（steering 単位累積のため、逆戻りで減算しない）。逆戻り対象 task の `Fix Attempts` は下記 Fix Attempts § 参照
  - `Why:` iteration 2 findings 旧#12 — worklog 自然文の grep 依存だと reliability が低く、Scope Drift Guard の発動判定が安定しない。state field に昇格することで 4 回目以降の判定を機械的に行える
- `Cumulative Changed Files`:
  - `0` 以上の整数。`state.md` に保持。brainstorming 時の「影響範囲の事前スキャン」で想定したファイル数に対する累積実変更ファイル数。`gdd-implementation-gating` 通過時に `git diff --name-only` で再計算して更新
- `Cumulative Diff Base`:
  - `state.md` に保持。Scope Drift Guard の impl-gate「前回の 2 倍以上」判定の分母となる基準値
  - schema: `Cumulative Diff Base: { files: <数>, hash_prefix: <base commit sha 先頭 8>, recorded_at: <ISO8601> }`
  - 書込責務: `gdd-design-gating` が design を `approved` に遷移させる瞬間に記録（詳細は `skills/gdd-design-gating/SKILL.md` Step 7）
  - 初回 approved 時に新規書込。2 回目以降の design approved（`changes_requested` 後の再承認、`human_recheck_required` route 復帰後の再承認）では **上書きせず累積追記**し、履歴として複数行を保持。最新行を最新基準として採用する
  - `human_recheck_required` 再承認時は新 Approved Direction に対して**再計測した値**を追記する（旧基準は stale のため分母に使わない。詳細は `references/rollback-patterns.md` の `human_recheck_required` セクション）
  - field が欠落している場合、「前回の 2 倍以上」判定は fail-open 化するため integrity check で fail-closed に倒す
  - `Why:` iteration 12 finding N12-a — base 書込責務が未定義で silent fail-open が発生していた
- `Root Cause Tag`:
  - 短い識別子文字列（例: `cursor-encoding-boundary`, `oauth-token-validation`）。`Current Task` セクション内に保持。`gdd-systematic-debugging` が route 判定時に直前 failure の root cause を 1 タグで要約する。同一タグが 2 回以上連続したら Escalation Decision Table 2 行目「同一 root cause が 2 回以上再発」の判定根拠として採用する
  - `Why:` iteration 2 findings 旧#1 — 「同一 root cause」判定を worklog 自然文比較ではなくタグ一致で機械的に行えるようにする
- `Origin Steering`:
  - Hotfix Lane として起こされた steering のみ持つ。root feature steering（最初に機能を実装した steering）への参照を `state.md` に保持
  - 多段 hotfix でも常に **root を指す**（直前 hotfix を指さない）。audit 遡行性を 1 ホップで保証するため
  - value grammar は 4 形式: `local:<path>` / `snapshot:<snapshot-id>:<path>` / `git-ref:<tag-or-sha>:<path>` / `unresolved:<last-known-path>`（物理 delete かつ復元不能時、詳細は `phase-progression.md` 参照）
  - root feature steering が archive/discard されていても参照は残し続ける（scrub 禁止）
  - 詳細規約は `phase-progression.md` § Post-PR / Post-Merge Contract 参照
- `Origin Resolution Status`:
  - `Origin Steering` と対で保持し、参照先の解決状態を示す
  - 値: `local`（local tree に存在） / `snapshot`（snapshot / git-ref で解決可能） / `unresolved`（物理 delete かつ復元不能）
  - `unresolved` の場合は hotfix 側 `tasklist.md` で `Origin VH Rehydration: required` フラグを立て VH を self-contain する（詳細は `phase-progression.md` § Post-PR / Post-Merge Contract 参照）
- `Parent Hotfix`:
  - 多段 hotfix（hotfix → hotfix）でのみ持つ。直前 **merge 済 hotfix steering** への相対 path を `state.md` に保持
  - cancelled / unmerged hotfix は `Parent Hotfix` に記録しない。audit 目的で `Abandoned Hotfix Attempts: [<path>, ...]` 配列に別記
  - root hotfix（`Origin Steering` の直接子）の場合は省略可
  - chain depth 計算に使う: `Parent Hotfix` 無 ⇒ depth=1、有 ⇒ 親 depth+1。cancelled hotfix は閾値 5 の上限消費に寄与しない。depth ≥5 で `human_recheck_required` 強制発火
  - routing source にはしない
- `Abandoned Hotfix Attempts`:
  - cancelled / unmerged な hotfix steering への path 配列。audit 目的で保持し、chain depth 計算からは除外
  - Hotfix Lane でのみ持つ（空配列可）
- `Trigger Hotfix`:
  - 多段 hotfix で、起票契機となった **in-flight / cancelled を含む** 親 hotfix への参照を `state.md` に保持する。形式: `<path> (状態: build-in-progress|merged|cancelled)`
  - `Parent Hotfix` が merge 済 hotfix のみを対象とするのに対し、`Trigger Hotfix` は **merge 前の in-flight hotfix も記録**（merge 前の連鎖 hotfix 発火を audit trail に残すため）
  - chain depth 計算には **算入しない**（algorithm の正本は `Parent Hotfix` のまま）
  - `Trigger Hotfix` 記載の親 hotfix が後に `merged` になれば `Parent Hotfix` にも昇格させて両方保持。`cancelled` になれば `Abandoned Hotfix Attempts` 配列に追記して `Trigger Hotfix` の状態を `cancelled` に更新
  - 省略可（root hotfix、および trigger 契機が元 feature steering の場合）
- `Origin VH Rehydration`:
  - hotfix 側 `tasklist.md` にのみ持つフラグ。値: `required` / `unnecessary`（既定 unnecessary）
  - `Origin Resolution Status=unresolved` の場合に `required` となり、hotfix tasklist.md に `## Origin Verification History (rehydrated)` セクションを併置する

### state field のフォーマット検証

state field は `<value> | <key>: <detail> | <key>: <detail> ...` のパイプ区切り形式で書かれる。検証ルール:

- 最初のセグメント（`|` の前）が上記許容値のいずれかに **完全一致** すること。先頭・末尾の空白は trim して比較する
- 許容値に含まれない値（typo、空文字列、未設定）は不正値として扱う
- 不正値を検出した場合、そのフィールドに依存する routing 判定（3-field gate check を含む）は実行せず fail-closed で停止する
- 停止時は不正値の具体的な内容（フィールド名・検出値・許容値リスト）を返す

**3-field gate check の検証**:

- `tasklist.md` が routing source になるかの判定（`Requirements Review Status=approved` + `Design Review Status=approved` + `Human Check Status=approved`）では、3 フィールドすべてが上記フォーマットで `approved` を持つことを確認する
- 1 フィールドでも不正値・未設定・空の場合は `tasklist.md` を routing source にしない（安全側: planning candidate として扱う）

## 状態遷移一覧（quick express）

`quick (express)` は planning gate を省略し、brainstorming → human-check → build → impl-gate → done の最短経路を取る。

| 契機                                                | Requirements Review Status | Design Review Status | Human Check Status | Resume From             | Next Action                        |
| --------------------------------------------------- | -------------------------- | -------------------- | ------------------ | ----------------------- | ---------------------------------- |
| gdd-brainstorming 開始（express）                   | pending                    | pending              | pending            | gdd-brainstorming       | —                                  |
| gdd-brainstorming 完了（express: human check 待ち） | approved                   | approved             | pending            | human-check-waiting     | human-check-waiting                |
| human check 承認（express）                         | approved                   | approved             | approved           | —                       | gdd-test-driven-development        |
| human check 差し戻し（express）                     | pending                    | pending              | changes_requested  | gdd-brainstorming       | gdd-brainstorming                  |
| human check 中止（express）                         | —                          | —                    | —                  | —                       | cancelled                          |
| human check で昇格指示（express → standard）        | pending                    | pending              | —                  | gdd-requirements-gating | gdd-requirements-gating            |
| gdd-test-driven-development 準備完了（express）     | —                          | —                    | —                  | —                       | gdd-subagent-driven-implementation |
| gdd-subagent-driven-implementation 完了（express）  | —                          | —                    | —                  | —                       | gdd-implementation-gating          |
| gdd-implementation-gating 通過（express）           | —                          | —                    | —                  | —                       | done                               |
| gdd-implementation-gating 差し戻し（express）       | —                          | —                    | —                  | —                       | gdd-systematic-debugging           |
| express 昇格（quick standard へ）                   | pending                    | pending              | —                  | gdd-requirements-gating | gdd-requirements-gating            |

Express では `gdd-implementation-gating` 通過後に `gdd-completion-check` を経由せず直接 `done` に遷移する。

### Express 昇格時の state ロールバック規則

Express から quick (standard) への昇格には 2 つの契機がある:

1. **自動昇格（build phase）**: 実装中に昇格条件（変更ファイル 3+、AC 4+、security boundary 影響等）を検出した場合。`task-sizing.md` § Express 昇格条件を参照
2. **手動昇格（human-check-waiting）**: ユーザーが human check 時に「これは Express では足りない」「設計が必要」「standard にしたい」等と判断した場合。Express 特有の判定であり、standard の human check 差し戻し 3 分類（部分修正 / 実装方針変更 / AC 変更）とは別ルート

どちらの契機でも、以下のフィールドを同時に更新する:

| フィールド                          | 更新値                                           | 理由                                                                                                                                                 |
| ----------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Task Size`                         | `quick (express → standard)`                     | 昇格記録                                                                                                                                             |
| `Requirements Review Status`        | `pending`                                        | Express で skip した req-gate を改めて通すため                                                                                                       |
| `Design Review Status`              | `pending`                                        | Express で skip した design-gate を改めて通すため                                                                                                    |
| `Human Check Status`                | **現在値を維持**                                 | 承認済みなら `approved` のまま。Express の human check は要件の方向性確認として有効                                                                  |
| `Resume From`                       | `gdd-requirements-gating`                        | 不足 phase の先頭から再開                                                                                                                            |
| `Approved Direction`                | 末尾に「Express から昇格のため再レビュー」を追記 | 昇格の経緯を記録                                                                                                                                     |
| `Planning Reviewer Selection`       | `pending`                                        | Express で skip した reviewer selection を standard フローで改めて実施するため                                                                       |
| `Implementation Reviewer Selection` | 削除（存在する場合）                             | Express で作成された selection 記録は standard の scope と合わない可能性があるため。`gdd-task-breakdown` で初期枠を再作成する                        |
| `Fix Attempts`                      | **reset to 0**                                   | 新 scope では loop safety カウンタを再カウント。旧 scope の失敗試行数を引き継ぐと即座に `>= 3` 判定に倒れ不当に blocked になる                       |
| `Root Cause Tag`                    | **継続**                                         | 同一 root cause が standard 側でも再発するなら判定に活かす。reset すると escalation table 2 行目の「同一 root cause 2 回以上再発」判定が効かなくなる |
| `Scope Drift Counter`               | **継続**                                         | steering 単位累積のため reset しない。昇格契機が drift 累積の場合 reset すると累積監視そのものが破綻する                                             |
| `Cumulative Changed Files`          | **継続**                                         | 同上。累積監視の一貫性を保つ                                                                                                                         |
| `Drift Review Required`             | **継続**                                         | 昇格自体は flag のクリア契機ではない。standard 側の impl-gate approved で初めて false になる                                                         |

**build phase 昇格時の code artifact 扱い**（`Resume From` が `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `gdd-implementation-gating` / `gdd-systematic-debugging` のいずれかだった場合）:

- Completed Tasks の commit 済み実装: **revert commit を積む**（`revert: express implementation for Task Size upgrade` の prefix で 1 commit にまとめる）。履歴を辿れて working tree はクリーンな状態で req-gate に入る
- Current Task の WIP: **discard** + worklog.md に破棄対象ファイル一覧を記録
- stash に退避した差分: **stash drop は禁止**（design-gating 再通過時に採否判断する）
- `design.md`: express skeleton は standard scope と合わないため、`gdd-brainstorming` 相当の書き換えは不要だが、req-gate 再通過後の design-gating で standard 用に詳細化する
- `adr.md`: 「Express から standard へ昇格した経緯と scope 再定義理由」を ADR として追記

**Why**: 昇格は scope が変わる操作。Express で作った commit 済み実装が新 scope で valid とは限らず、残したまま req-gate に入ると「approved な要件と違う実装が存在する」矛盾 state になる。revert commit で履歴保全しつつ working tree を初期化する。これは planning 差し戻し時の code artifact 扱いと同じ思想（`state-machine.md` § planning 差し戻し時の code artifact 扱い と整合）。

**Human Check Status=approved を維持したまま req-gate を再通過する場合**: 通常 standard の req-gate 通過は state 表で `Human Check Status=pending → human-check-waiting` 遷移となるが、**express 昇格経路では `approved` を維持したまま req-gate を素通し** する（要件方向性は Express の human check で既に承認済みのため）。ただし `Approved Direction` に「Express から昇格のため再レビュー」追記が残っている間は、reviewer が scope 再定義を可視化する契約とする。再 human check が必要になる条件（AC 追加削除・security 新規等）に該当すれば通常の `human_recheck_required` ルートに倒す。

**昇格 × `human_recheck_required` の同時発火**（E2E で AC 境界越えが判明し、かつ human check でユーザーが「standard 昇格」を指示した場合等）:

2 つのルートの state 更新ルールが衝突するため（例: `Drift Review Required` は昇格=継続・human_recheck=false リセット）、**`human_recheck_required` を優先して 2 段階処理** で適用する。

**段階 1（`human_recheck_required` 処理）** — human-check-waiting に戻った時点:

1. Tasklist Reset Policy § `human_recheck_required` に従い全セクション初期化
2. `Drift Review Required=false` リセット（新 Approved Direction 承認時）
3. `Approved Direction` は新承認内容で上書き
4. code artifact 扱いは `state-machine.md` § planning 差し戻し時の code artifact 扱い に従う（revert commit / WIP discard 等）
5. `Route In Progress=human_recheck_required`

**段階 2（昇格処理）** — 段階 1 の再承認完了後、ユーザーが昇格を指示した時点:

1. `Task Size=quick (express → standard)` に更新
2. `Requirements Review Status=pending` / `Design Review Status=pending` / `Planning Reviewer Selection=pending` に戻す
3. `Human Check Status` は `approved` 維持（段階 1 で再承認済み）
4. `Fix Attempts=0` reset
5. `Root Cause Tag` / `Scope Drift Counter` / `Cumulative Changed Files` は継続（段階 1 でこれらは reset されない）
6. `Drift Review Required` は段階 1 で false、段階 2 で値変更なし（継続 false）
7. `Implementation Reviewer Selection` 削除
8. `Resume From=gdd-requirements-gating`
9. `Route In Progress=none`（昇格は route ではなく Task Size 変更のため）
10. `Approved Direction` 末尾に「Express から昇格のため再レビュー」追記
11. code artifact は段階 1 で既に処理済みなので二重 revert しない

**Why**: 境界越え（AC 追加等）は最も保守的に処理すべき contract。昇格はその後の scope 再定義であり、順序を付ければ state 矛盾が解ける。段階 1 で方向性を確定した上で段階 2 の scope 再定義を適用することで、`Drift Review Required` の矛盾も自然に解消される（段階 1 で false → 段階 2 で継続 false）。

**1 段階処理で済むケース**: human check で昇格のみ指示された（`human_recheck_required` 契機ではない手動昇格）場合は従来通り段階 2 のみ適用。code artifact の revert も段階 2 の規定（§ build phase 昇格時の code artifact 扱い）に従う。

**Why**: Express の brainstorming 完了時に `Requirements Review Status=approved`, `Design Review Status=approved` を設定する（reviewer skip のため）。昇格時にこの 2 つを `pending` に戻さないと、「formal な requirements/design review を通っていないのに approved」という矛盾 state が残り、H-4 の Phase Gate Pre-check を誤って通過する。

Express の `tasklist.md` は `gdd-test-driven-development` の最初のステップで作成する。human check 承認後〜`tasklist.md` 作成前にクラッシュした場合は、`tasklist.md` が無いため planning candidate として扱われ、`Resume From` で正しく `gdd-test-driven-development` に復帰する。

### Task Size 再評価マトリクス（再入契機別の持ち越しルール）

Express 昇格以外の再入契機でも、Task Size を再評価するか / state fields を reset するかの規定が必要。**Task Size は `gdd-brainstorming` 時の Complexity Evaluation で初回確定するが、以下の契機では再評価の要否が分岐する**。Express 昇格表と同格のルール表として本表に従う。

| 再入契機                                                                | Task Size の扱い                                                                 | Complexity Evaluation 再実行                                                               | Fix Attempts                      | Scope Drift Counter | Cumulative Changed Files | Refactor Gate Status                                    | Bounce Log（全種）                                       |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------- | ------------------- | ------------------------ | ------------------------------------------------------- | -------------------------------------------------------- |
| `planning_rework_required`                                              | **reset（再評価）**                                                              | **必須**                                                                                   | reset to 0                        | reset to 0          | reset to 0               | `absent`（tasklist 再生成で消える）                     | **reset to 0**（全 gate）                                |
| `human_recheck_required`（境界越え）                                    | **継続 + 新 Approved Direction 承認時に Complexity Evaluation を条件付き再実行** | **条件付き必須**（AC 追加削除 / security 境界新規 / データモデル変更のいずれかを含む場合） | **reset to 0**                    | 継続                | 継続                     | 継続（tasklist を部分保持するため）                     | **reset to 0**（全 gate）                                |
| `Fix Attempts=3` 単独（同一 task 内 escalation）                        | 継続                                                                             | 不要（root cause は route 判断で sizing ではない）                                         | reset to 0（escape hatch 発動時） | 継続                | 継続                     | 継続                                                    | escape hatch 発動行のみ reset to 0、他 identifier は継続 |
| `Scope Drift Guard` 発動（design_detail_only 累積 4 回目）              | **継続 + Express のみ昇格チェック**（昇格条件を満たせば Express 昇格経路へ合流） | 条件付き（Express 昇格時のみ brainstorming 側で再実行）                                    | 継続                              | 継続                | 継続                     | 継続                                                    | 継続                                                     |
| `gdd-refactor-planning` 再計画（`Refactor Gate Status=pending` 再起動） | 継続                                                                             | 不要（refactor scope は task size 変更契機ではない）                                       | 継続                              | 継続                | 継続                     | `pending` → `in-progress`（refactor-planning が進める） | 継続                                                     |
| session restart（kernel panic / process kill からの再開）               | 継続                                                                             | 不要                                                                                       | 継続                              | 継続                | 継続                     | 継続                                                    | 継続（state.md 永続）                                    |

**Complexity Evaluation 再実行の責務主体**:

- `planning_rework_required`: `gdd-brainstorming` が再入時点で Complexity Evaluation を強制再実行する（初回と同じ扱い）
- `human_recheck_required`（境界越え）: 新 Approved Direction 承認後、`gdd-brainstorming` が「AC 追加削除 / security 境界新規 / データモデル変更」の 3 条件のいずれかを検出した場合に Complexity Evaluation を再実行する。該当しない場合は旧 Task Size を継続
- その他の契機: Complexity Evaluation を再実行しない。旧 Task Size を継続

**昇格方向の非対称性（降格禁止の原則）**:

Task Size は **monotonic upgrade-only**。Complexity Evaluation の再実行結果が旧 Task Size より小さい sizing を示唆した場合でも、**降格は行わない**（reviewer を減らす方向の変更は silent リスクのため）。scope が縮小した場合は artifact を簡素化して継続する。

- 例: `standard` → Complexity Evaluation 再実行結果が `quick (standard)` → **`standard` 継続**（降格せず、reviewer は standard 用を維持）

**trivial からの昇格の到達先判定フロー**:

trivial は `requirements.md` / `design.md` を作らないため「mid-design」の概念がない。昇格が必要になった場合は以下のフローで到達先を決定する:

1. `task-sizing.md` § Express 昇格条件を満たす → `quick (express)` から開始
2. `task-sizing.md` § quick 条件を満たす → `quick (standard)` から開始
3. いずれも満たさない → `standard` から開始
4. `requirements.md` を新規作成し、Complexity Evaluation で最終確定

**Why**: Task Size は brainstorming 1 回限定でロックすると、再入契機で scope が動いた場合に旧 sizing のまま進んで reviewer 不足 / Phase Gate skip を silent に許容するリスクがある。再入契機別に「再評価が必要な経路」「継続で十分な経路」を明示することで、scope 変更時の reviewer/phase 要件を fail-closed に保つ。降格禁止は reviewer 軽量化の silent pass 経路を塞ぐための不可逆設計。

## 状態遷移一覧（quick standard / standard）

`—` は、その契機で当該 field を更新しない、または該当値を持たないことを表す。

| 契機                                                                    | Requirements Review Status | Design Review Status | Human Check Status | Resume From             | Next Action（routing source の値。planning 中は draft 記載値） |
| ----------------------------------------------------------------------- | -------------------------- | -------------------- | ------------------ | ----------------------- | -------------------------------------------------------------- |
| gdd-brainstorming 開始                                                  | pending                    | pending              | pending            | gdd-brainstorming       | —                                                              |
| gdd-brainstorming 完了（requirements review 待ち）                      | pending                    | pending              | pending            | gdd-requirements-gating | —                                                              |
| gdd-requirements-gating 開始（tasklist 未作成）                         | in_review                  | pending              | pending            | gdd-requirements-gating | —                                                              |
| gdd-requirements-gating 開始（stale tasklist あり）                     | in_review                  | pending              | pending            | gdd-requirements-gating | gdd-requirements-gating                                        |
| gdd-requirements-gating 差し戻し                                        | changes_requested          | pending              | pending            | gdd-brainstorming       | gdd-brainstorming                                              |
| gdd-requirements-gating 通過                                            | approved                   | pending              | pending            | human-check-waiting     | human-check-waiting                                            |
| human check 差し戻し（方向性レベルの全面やり直し）                      | pending                    | pending              | changes_requested  | gdd-brainstorming       | gdd-brainstorming                                              |
| human check 中止                                                        | —                          | —                    | —                  | —                       | cancelled                                                      |
| human check 承認                                                        | approved                   | pending              | approved           | gdd-design-gating       | gdd-design-gating                                              |
| gdd-design-gating 開始（tasklist 未作成）                               | approved                   | in_review            | approved           | gdd-design-gating       | —                                                              |
| gdd-design-gating 開始（stale tasklist あり）                           | approved                   | in_review            | approved           | gdd-design-gating       | gdd-design-gating                                              |
| gdd-design-gating で `planning_rework_required` を検知                  | pending                    | pending              | pending            | gdd-brainstorming       | gdd-brainstorming                                              |
| gdd-design-gating で `human_recheck_required` を検知                    | approved                   | pending              | pending            | human-check-waiting     | human-check-waiting                                            |
| gdd-design-gating で `design_detail_only` を検知                        | approved                   | changes_requested    | approved           | gdd-design-gating       | gdd-design-gating                                              |
| gdd-design-gating 通過                                                  | approved                   | approved             | approved           | gdd-task-breakdown      | gdd-task-breakdown                                             |
| gdd-task-breakdown 正常終了                                             | —                          | —                    | —                  | —                       | gdd-test-driven-development                                    |
| gdd-task-breakdown で `planning_rework_required` を検知                 | pending                    | pending              | pending            | gdd-brainstorming       | gdd-brainstorming                                              |
| gdd-task-breakdown で `human_recheck_required` を検知                   | approved                   | pending              | pending            | human-check-waiting     | human-check-waiting                                            |
| gdd-task-breakdown で `design_detail_only` を検知                       | approved                   | changes_requested    | approved           | gdd-design-gating       | gdd-design-gating                                              |
| gdd-test-driven-development 準備完了                                    | —                          | —                    | —                  | —                       | gdd-subagent-driven-implementation                             |
| gdd-test-driven-development で `planning_rework_required` を検知        | pending                    | pending              | pending            | gdd-brainstorming       | gdd-brainstorming                                              |
| gdd-test-driven-development で `human_recheck_required` を検知          | approved                   | pending              | pending            | human-check-waiting     | human-check-waiting                                            |
| gdd-test-driven-development で `design_detail_only` を検知              | approved                   | changes_requested    | approved           | gdd-design-gating       | gdd-design-gating                                              |
| gdd-subagent-driven-implementation 完了                                 | —                          | —                    | —                  | —                       | gdd-implementation-gating                                      |
| gdd-subagent-driven-implementation で `planning_rework_required` を検知 | pending                    | pending              | pending            | gdd-brainstorming       | gdd-brainstorming                                              |
| gdd-subagent-driven-implementation で `human_recheck_required` を検知   | approved                   | pending              | pending            | human-check-waiting     | human-check-waiting                                            |
| gdd-subagent-driven-implementation で `design_detail_only` を検知       | approved                   | changes_requested    | approved           | gdd-design-gating       | gdd-design-gating                                              |
| gdd-implementation-gating 開始                                          | —                          | —                    | —                  | —                       | gdd-implementation-gating                                      |
| gdd-implementation-gating 差し戻し                                      | —                          | —                    | —                  | —                       | gdd-systematic-debugging                                       |
| gdd-systematic-debugging でテスト設計不足 / failing test 不足を検知     | —                          | —                    | —                  | —                       | gdd-test-driven-development                                    |
| gdd-systematic-debugging で `implementation_fix_only` を選択            | —                          | —                    | —                  | —                       | gdd-subagent-driven-implementation                             |
| gdd-systematic-debugging で `planning_rework_required` を検知           | pending                    | pending              | pending            | gdd-brainstorming       | gdd-brainstorming                                              |
| gdd-systematic-debugging で `human_recheck_required` を検知             | approved                   | pending              | pending            | human-check-waiting     | human-check-waiting                                            |
| gdd-systematic-debugging で `design_detail_only` を検知                 | approved                   | changes_requested    | approved           | gdd-design-gating       | gdd-design-gating                                              |
| gdd-implementation-gating 通過（未完了 task あり）                      | —                          | —                    | —                  | —                       | gdd-test-driven-development                                    |
| gdd-implementation-gating 通過（全 task 完了、Refactor Gate 通過済み）  | —                          | —                    | —                  | —                       | gdd-completion-check                                           |
| gdd-implementation-gating 通過（全 task 完了、Refactor Gate 未実行）    | —                          | —                    | —                  | —                       | gdd-refactor-planning                                          |
| gdd-refactor-planning 改善機会なし                                      | —                          | —                    | —                  | —                       | gdd-completion-check                                           |
| gdd-refactor-planning 改善機会あり（refactor task 追加）                | —                          | —                    | —                  | —                       | gdd-test-driven-development                                    |
| gdd-completion-check で外部前提不足                                     | —                          | —                    | —                  | —                       | gdd-completion-check                                           |
| gdd-completion-check 差し戻し                                           | —                          | —                    | —                  | —                       | gdd-systematic-debugging                                       |
| gdd-completion-check 完了                                               | —                          | —                    | —                  | —                       | done（※）                                                      |
| gdd-completion-check 中止                                               | —                          | —                    | —                  | —                       | cancelled（※）                                                 |

※ `done` / `cancelled` への遷移時、`Route In Progress` が `none` 以外なら `none` にクリアする（`references/rollback-patterns.md` §ターミナル状態でのクリア 参照）。

### gdd-completion-check の `Next Action` 許容値（fail-closed 制約）

`gdd-completion-check` 通過時に `state.md` へ書き込める `Next Action` の値は次に固定する。これ以外（特に `plan` / `planning` / 空 / harness 側 Plan mode へのマーカー）は state 不整合として fail-closed 停止し、`<gdd-stop reason="blocked">` で止める。

| `Next Action` 値            | 用途                                                                             |
| --------------------------- | -------------------------------------------------------------------------------- |
| `done`                      | 全 AC pass、reviewer approved、Post-Completion PR Flow も完了                    |
| `cancelled`                 | ユーザー明示の中止                                                               |
| `gdd-completion-check`      | 外部前提不足（同一 blocker が継続）。再実行で解消する見込みがある間だけ          |
| `gdd-systematic-debugging`  | AC failure / review blocker / verification evidence insufficiency による差し戻し |
| `gdd-refactor-planning`     | `Refactor Gate Status=pending` 検知で再評価が必要                                |
| `gdd-implementation-gating` | `Reviewed by` 行欠落で対象 task を再 gate にかける                               |

**Why:** completion-check は post-completion PR Flow（merge / PR / keep / discard 4 択）で次アクションを必ず取り切る最終 gate。harness 側 Plan mode への自動遷移は、`/gdd-dev` 自走契約と矛盾し（Plan mode は計画専用で実行・再開・停止条件を持たない）、人間が次アクションを再選択し直す摩擦を生む。許容値を列挙固定し、それ以外は fail-closed で止めることで、harness のデフォルト挙動に流されない構造を作る。

## Remediation Loop Safety

- `gdd-implementation-gating` または `gdd-completion-check` から `gdd-systematic-debugging` に戻った場合、同じ `Current Task` に対する直前の blocker と今回の blocker を比較する
- 同じ `Current Task` で `changes_requested` が 2 回連続した場合は、`worklog.md` に根本原因、前回との差分、今回の route 判断を書く
- 同じ `Current Task` に対する 3 回目の blind `implementation_fix_only` は許可しない。判定は `tasklist.md` の `Fix Attempts` カウンタを正本とし、`worklog.md` の Error Log を補助根拠にする。両者が食い違う場合は大きい方を採用する（安全側に倒す）
- unresolved `High` / `ops-blocking medium` が明確に減っていない、または同一 root cause が再発している場合は、`implementation_fix_only` を繰り返さず route recalibration を行う。policy / scope / ownership / security boundary / prompt-output contract の変更が必要なら `human_recheck_required` / `planning_rework_required` へ、`Reviewed by:` 欠落や verification wording 不整合などの procedural / evidence only なら build loop 内（`gdd-implementation-gating` / `gdd-completion-check` 再実行）で解消する
- 適切な route を正本から決められない場合は fail-closed で停止し、state を変えずに `参照した正本` / `停止理由` / `次の1アクション` を返す

## Planning Loop Safety

- `gdd-brainstorming`、`gdd-requirements-gating`、`gdd-design-gating`、`gdd-task-breakdown` は同じ unresolved `High` / `Medium` や未解決 trade-off を blind に繰り返さない
- 同じ planning blocker が 2 回の review/edit cycle で残る（`>=2`。`gdd-completion-check` 既存閾値・`references/bounce-log-schema.md` 各行と統一）、または `references/reviewer-selection.md` の優先順位だけでは reviewer conflict を解けない場合は、人間判断が必要な状態として停止する。**同一root cause再発の検出粒度**: bounce 時に根本原因カテゴリ（例: `実コード未読` / `AC仕様不備` / `スコープ不一致`）を1行記録し、直近2回一致すれば表面文言が異なっても同一 bounce としてカウントする
- route / ownership / prompt contract / output contract / sensitive data / masking / rollout / rollback に関する `Open Questions` は、human approval が必要な policy question なら blocking とみなし、`human-check-waiting` へ進めない
- requirements / implementation policy の承認や再承認が必要な場合は `human-check-waiting` に戻し、それ以外の人間判断は current phase を保ったまま `blocked` で止める
- planning escalation で止めるときも、少なくとも `参照した正本` / `停止理由` / `次の1アクション` に加えて、未解決の論点と選択肢を返す

## entry intent の決定規則

- `/gdd-dev` は canonical state 解決の前に、今回の明示実行が `new` / `resume` / `ambiguous` のどれかを判定する
- 判定ルールは `references/entry-intent.md` を正本とする
- 判定は明示 cue のみで行い、implicit な推測はしない:
  - `resume`: `$ARGUMENTS` に明示 resume cue（`再開`, `続き`, `続きから`, `resume`）がある
  - `new`: `$ARGUMENTS` に明示 new cue（`新規`, `新規開始`, `別件`, `新しい task`, `新しいタスク`）がある、または resume cue を含まない具体的な新規 task 説明がある
  - `ambiguous`: 上記のどれにも該当しない（`$ARGUMENTS` が空、cue が弱い、cue が衝突する）
- `ambiguous` は fail-closed で停止し、`新規開始` か `再開` かの明示を要求する
- 明示的な resume cue は、明示的な new cue と衝突しない限り、具体的な task 説明より優先する
- `new` では既存 non-terminal steering を resume 候補として解決せず、新しい `.steering/YYYYMMDD-short-title/` を作って `gdd-brainstorming` から開始する
- `resume` のときだけ active steering candidate を集めて 1 つに解決する

## active steering の決定規則

- `gate-driven-development` は `resume` path で 1 つの active steering だけを扱う
- candidate 収集は Task Binding Registry と git worktree の照合を正本にする
- resolver は hard exclude -> hard match -> soft score -> conflict の順で判断する
  - hard exclude: terminal state、current worktree と異なる binding、branch 不一致、registry にない root `.steering`
  - hard match: current worktree と branch と `steering_path` が registry 上で 1 件だけ一致する
  - soft score: `session_id`、自然文 cue、local state pointer は補助表示にだけ使い、hard match を上書きしない
  - conflict: hard match が 0 件または複数件なら current を断定せず停止する
- active candidate は `state.md` を持つ steering に限定する。`design.md` だけの旧 artifact は resume 正本に使わない
- terminal state（`Next Action=done` / `cancelled`、または `Resume From=done` / `cancelled`）の steering は候補から除外する
- PR merge 済みの follow-up は terminal steering の resume ではない。`続き` / `追加実装` などの自然文 cue があっても、元 steering を active candidate に戻さず、Pre-Follow-up Hygiene Gate の後に new amendment / hotfix steering を作る
- candidate の分類は次で固定する
  1. **build candidate**
     - active worktree 側 `tasklist.md` が存在する
     - `Next Action` が `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `gdd-implementation-gating` / `gdd-systematic-debugging` / `gdd-refactor-planning` / `gdd-completion-check` のいずれか
  2. **planning candidate**
     - active worktree 側 `state.md` が存在する
     - `Resume From` が `gdd-brainstorming` / `gdd-requirements-gating` / `human-check-waiting` / `gdd-design-gating` / `gdd-task-breakdown` のいずれか
     - `tasklist.md` が無い、または `Requirements Review Status=approved` / `Design Review Status=approved` / `Human Check Status=approved` の 3 つが揃っていない
  3. **legacy root candidate**
     - current task としては扱わない
     - repo root に旧 contract の `.steering/...` があれば diagnostic / migration source として表示してよい
     - migration はユーザーが明示的に対象を選んだ後にだけ行う
- 同一 worktree で build candidate と planning candidate が競合した場合は state 不整合として fail-closed で停止する
- active steering の優先順位は `build candidate > planning candidate`。legacy root candidate は current task の優先順位に含めない
- 同一 worktree で同一優先順位の candidate が複数ある場合、異なる `steering_slug` が 2 件以上残るなら fail-closed で停止する。`Started At` 最新だけで自動選択しない
- `Started At` は同一 slug の duplicate など、Worktree Identity Tuple が clean で branch も同じ slug を指す場合だけ tie-breaker として使える
- `Started At` が無い / 同率最新 / branch slug と latest candidate がズレる場合は fail-closed で停止し、どの steering を再開するか明示指定を要求する。このとき新しい steering や新しい `.steering/...` を作って曖昧さを吸収しない
- `resume` なのに candidate が 0 件なら fail-closed で停止し、再開対象の指定または新規開始の意図確認を要求する

## Resume 正本の切り替え

- この節は `entry intent=resume` のときだけ適用する
- **build candidate**: active worktree 側 `tasklist.md` の `Next Action` を正本とし、build はその worktree 側 `.steering/...` のみを更新する
- **planning candidate（tasklist 未作成）**: active worktree 側 `state.md` の `Resume From` を正本にする
- **planning candidate（stale tasklist あり）**: `tasklist.md` は draft planning artifact として扱い、routing / resume の正本にせず、`state.md` の `Resume From` を使う。draft の間の `tasklist.md` の `Next Action` は planning phase を表す補助情報としてだけ扱う
- **legacy root candidate**: current task としては自動採用しない。`gdd-status` / resume resolver では diagnostic として表示し、ユーザーが明示的に migration 対象を選んだ後に `gdd-brainstorming` が worktree-first contract への migration を完了してから、worktree 側 artifact を正本として開く。root 側 `.steering/.../adr.md` があれば一緒に移してよいが、無くても routing は変わらない
- 新 contract では tracked な root 側 `tasklist.md` / `design.md` を canonical build source として使わない

## Resume 時の再開ルーティング

- `entry intent=resume` で active steering が解決した後、canonical state に従って再開する
- active steering が **build candidate** の場合:
  - active worktree 側 `tasklist.md` を正本として再開する
  - ユーザーが review 差し戻しや implementation policy 変更を明示した場合は、同じ active worktree のまま `gdd-systematic-debugging` を safe classifier として使い、`implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required` のどれかを確定する
  - ただし対象 PR が default branch へ merge 済みで、ユーザー入力が追加実装・仕様変更・hotfix を求めている場合は、active build candidate として再開しない。Post-Merge Follow-up Worktree Policy に従い、既存 worktree を整理対象にして new amendment / hotfix worktree へ分離する
- active steering が **planning candidate** の場合:
  - active worktree 側 `state.md` の `Resume From` をそのまま正本に使う
- canonical state だけでは reopen 先を一意に決められない場合は fail-closed で停止し、state を変えずに `参照した正本` / `停止理由` / `次の1アクション` を返す

## Resume 時の state 整合性検証

- `entry intent=resume` で active steering を解決した後、再開ルーティングの前に以下の整合性を検証する
- 検証はセッション再開のたびに実行する。クラッシュで `state.md` と `tasklist.md` の更新が中途半端に残った場合を検出する目的

### 検証項目

1. **Route In Progress と Next Action の整合性**:
   - `Route In Progress=implementation_fix_only` なら `Next Action` は `gdd-subagent-driven-implementation` / `gdd-implementation-gating` のいずれかであること
   - `Route In Progress=design_detail_only` なら `Next Action` は `gdd-design-gating` であること
   - `Route In Progress=human_recheck_required` なら `Next Action` は `human-check-waiting` であること
   - `Route In Progress=planning_rework_required` なら `Next Action` は `gdd-brainstorming` であること
   - `Route In Progress=requirements_amendment` なら `Next Action` は `gdd-requirements-gating` / `human-check-waiting` / `gdd-brainstorming` のいずれかであること
   - `Route In Progress=none` なら `Next Action` に制約なし
   - `Route In Progress=batch_mixed` なら `tasklist.md` に `Batch Route Decisions` per-task マップが存在し、`Next Action` は最 severe な route の遷移先に一致すること
2. **Route In Progress とターミナル状態の排他**:
   - `Next Action` が `done` / `cancelled` のとき `Route In Progress` は `none` であること
3. **Fix Attempts カウンタの健全性**（`tasklist.md` に `Fix Attempts` がある場合）:
   - `Fix Attempts` が 3 以上で `Route In Progress=implementation_fix_only` なら不整合（blind loop 違反の可能性）

### 不整合検出時の対応

- 検証に失敗した場合は fail-closed で停止する
- state を自動修復しない（どちらが正しいか判断できないため）
- 停止時に `参照した正本` / `停止理由`（どのフィールドが矛盾しているか具体値を含める）/ `次の1アクション`（人間が `state.md` または `tasklist.md` のどちらを修正すべきかの指針）を返す

## 停止時の返答契約

- fail-closed や mandatory gate で停止するときも、`進めない` だけで終わらせない
- 停止時は、少なくとも次を返す
  - `参照した正本`
  - `停止理由`
  - `次の1アクション`
- current phase が既に決まっており、external prerequisite 不足・metadata 修復・人間入力待ちだけが blocker の場合は、現在 phase の `Next Action` を維持する
- planning phase で `Next Action` が routing source でない場合も同様に、current な `Resume From` を維持し、同じ phase を再試行できるようにする
- `entry intent=ambiguous`、active steering candidate の競合、candidate 0 件の `resume` のように正本そのものを決められない場合は、state を変えずに停止し、候補一覧または明示入力の要求を返す
- `gdd-completion-check` で required external security evidence の external prerequisite が足りない場合は `Next Action=gdd-completion-check` を維持し、不足前提のチェックリストを返す。再実行時に前回と同じ blocker リストが変化なく残っている場合は `blocked` で停止し、human に解消手順を明示通知する。actual な AC failure / review blocker / verification evidence insufficiency だけを `gdd-systematic-debugging` への差し戻し対象とする

## Autonomous Continuation

- explicit な `/gdd-dev` run は `.claude/gdd-dev.local.md` と Stop hook を使い、same session で non-terminal phase を継続してよい
- non-terminal な `Resume From` / `Next Action` は stop 理由ではなく continuation 理由として扱い、current phase や next phase を要約できるだけで assistant turn を閉じない
- stop してよいのは `done` / `cancelled` / `human-check-waiting` / `blocked` / `clarification-needed` / `external-review-waiting` / `auth-waiting` の 7 種類だけとする
- 明示的に stop するときは、最後の assistant text block に `<gdd-stop reason="done|cancelled|human-check-waiting|blocked|clarification-needed|external-review-waiting|auth-waiting">` を 1 つだけ含める。`</gdd-stop>` は任意で、hook 判定には使わない
- phase 遷移時は `<gdd-phase>skill-name</gdd-phase>` マーカーをヘッダーに含める（`references/output-format.md` 参照）。Stop hook はこのマーカーで phase を検出し、model routing に使う
- `blocked` は fail-closed、外部前提不足、ambiguous routing など、人間入力や環境修復が必須な停止に限定する

### Goal-Driven Loop Ownership

不確実な作業で複数の loop 系 skill が候補になる場合、**single owner** を 1 つだけ決める。二重の outer loop を作らない。

| 役割 | owner | 責務 |
|---|---|---|
| outer loop | `gdd-goal-driven-execution` | Goal Contract / Current State / Working Hypothesis / Plan Revision Loop / Stop Conditions を管理する |
| root cause inner loop | `root-cause-investigation` | 原因仮説を最大 3 回まで probe し、confirmed / likely / no_root_cause_yet を返す |
| implementation inner loop | `gdd-subagent-driven-implementation` | 承認済み tasklist の task を実装し、controller に結果を返す |
| routing bridge | `gdd-systematic-debugging` | confirmed root cause や実装失敗を state machine の戻り先へ分類する |
| continuation guard | Stop hook | 非 terminal の継続可否を判定する。Goal / plan / root cause を所有しない |

`gdd-goal-driven-execution` が outer loop のとき、`root-cause-investigation` と `gdd-subagent-driven-implementation` は inner loop として呼ばれる。inner loop は Goal を変更しない。Goal / Done When / Not Changing Without Human を変える必要が出た場合は `human_recheck_required` または `gdd-requirements-amendment` に戻す。

**Outer Loop Boundary**: `gdd-goal-driven-execution` は root cause probe や implementation verification を所有しない。does not run root cause probes directly / does not mark implementation DONE as verified_done。outer loop は「次にどの inner loop を呼ぶか」「観測結果で plan をどう更新するか」「Goal 変更が必要なら人間に戻すか」だけを所有する。

**Inner Loop Handoff Contract**: inner loop は自分の専門領域の status と evidence を返す。`root-cause-investigation` は root cause status / confidence / next probe を、`gdd-subagent-driven-implementation` は implementation status / changed files / verification evidence を返す。どちらも Goal Contract を変更せず、`verified_done` や completion claim を単独で決めない。

root cause が `confirmed` ではない場合、修正実装へ進む前に `gdd-goal-driven-execution` の Working Hypothesis を更新する。3 回 probe しても `confirmed` にならない場合は、盲目的に 4 回目を回さず `blocked` / `needs_human` / `needs_design_rework` のいずれかを選ぶ。

`gdd-subagent-driven-implementation` は実装担当であり、Goal 達成判定の owner ではない。subagent が `DONE` を返しても、outer loop または completion gate が Verification を確認するまで `verified_done` にしない。

## ユーザー起点の中止（Cancel）

- `human-check-waiting` でユーザーが「中止」「cancel」「やめる」「キャンセル」と明示した場合、`Next Action=cancelled` に遷移する
- `cancelled` は terminal state であり、`done` と同様に `Route In Progress` を `none` にクリアする
- 中止後の worktree cleanup は `gdd-using-git-worktrees` の「Cancelled Cleanup」に従う（keep / archive / discard をユーザーに確認）
- build phase（TDD / implementation / impl-gate）での中止は `human-check-waiting` を経由しないため、ユーザーはセッションを終了して steering を放置できる。放置された steering は `detect-steering` で non-terminal candidate として残り、次回 `/gdd-dev resume` 時に候補として表示される。明示的に終了したい場合は `tasklist.md` の `Next Action=cancelled` を手動で書き込むか、worktree を削除する
- `gdd-completion-check` からの中止は既存の `gdd-completion-check 中止` 遷移を使う

## planning 差し戻し後の tasklist.md リセット

- planning phase に差し戻された場合のリセット範囲は `state.md` の `Route In Progress` で決める
- **`design_detail_only`**: 影響を受けるタスクだけをリセットする（差分更新）
  - 既存 `Completed Tasks` を保持する
  - design 変更で影響を受ける AC に紐づくタスクだけを `Pending Tasks` に戻す（または再分割する）
  - 影響のないタスクは `Completed Tasks` / `Pending Tasks` にそのまま残す
  - `Implementation Reviewer Selection` / `Review Status` はリセットする
  - `Verification` は影響 AC のみリセットし、非影響 AC はそのまま残す
- **`human_recheck_required` / `planning_rework_required`**: 全セクション初期化して再生成する
  - `Current Task` / `Pending Tasks` / `Completed Tasks` をすべてリセット
  - `Implementation Reviewer Selection` を `pending | reason: none` に初期化
  - `Review Status` を全 reviewer `pending | evidence: none` に初期化
  - `Verification` を初期枠に戻す
  - `Drift Review Required` は人間再承認で Approved Direction が更新された時点で `false` にリセット（flag の目的である「自走範囲内の累積変更への reviewer 確認」は human check 再承認で代替されるため）
  - 要件自体が変わる可能性があるため差分更新はしない
- 全リセットの目的は、古い task / verification 行が残ることによる false blocker と false pass の両方を防ぐこと
- 前回の `Completed Tasks` にあった task の作業成果（コード変更）は git 上に残っているため、再生成で失われるのは tasklist 上の metadata のみ

## planning 差し戻し時の code artifact 扱い

`human_recheck_required` / `planning_rework_required` で方向転換が起きた場合、`tasklist.md` のリセットだけでは不十分で、git 上の実装差分 / `design.md` / 導入済み依存をどう扱うかを規定する。基本方針: **「履歴は残し、working tree は次方向で再出発できる状態」に戻す**。

### git commit / WIP 差分

| 状態                                 | 扱い                                                                                  | 理由                                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `Completed Tasks` の commit 済み実装 | **revert commit を積む**（`git revert`）                                              | 履歴辿れて working tree はクリーン。new direction で必要なら cherry-pick 流用可       |
| WIP（uncommitted 差分）              | **discard**（`git checkout -- <paths>`）+ worklog.md に「破棄対象ファイル一覧」を記録 | 中途状態は新方向では再設計するため保持価値が薄い。失われた検討痕跡は worklog で追える |
| stash に退避した差分                 | **stash drop は禁止**。新方向確定後に design-gating で採否判断                        | 判断材料を先に捨てない                                                                |

- revert / discard の実行タイミング: 新 `Approved Direction` が human-check で再承認された **直後**。design-gating invoke 前
- revert commit のメッセージ prefix: `revert(gdd): <task-id> - <方向転換理由の 1 行>`

### design.md の扱い

- `human_recheck_required` / `planning_rework_required` では **全面書き換え**（tasklist.md と同じ思想でリセット）
- 却下された設計は `.steering/<task>/adr.md` に **方向転換 ADR として履歴化** する（adr.md が無ければ新規作成）
- ADR 記載内容: 「<旧方向> を検討したが <新方向> に変更。理由: <ユーザー指示要約>。検討時の制約・懸念: <簡潔に>」

### 導入済み library / 依存

- `package.json` / `requirements.txt` / `go.mod` 等で追加済み library 依存の cleanup は **design-gating で新方向が確定した段階** で判断する（再承認直後ではない）
- 理由: 新方向でも流用可能な library は残す判断があり得る（例: OAuth library の一部を JWT 検証に流用）
- 削除判断が確定したら、`task-breakdown` で **Pending Tasks の先頭に `cleanup-<旧方向>` task を自動投入** する

### 適用しない場合

- `design_detail_only`（差分リセット）では本セクションは適用しない。既存 commit / WIP / design.md は保持し、影響 AC 周辺のみ変更する

## tasklist.md の canonical state

- `tasklist.md` は次のセクションで task state を表す
  - `## Execution Plan`（optional: 並列実行が有効な場合のみ。`Mode: parallel | sequential` とバッチ構成を記録）
  - `## Current Task`（逐次実行時は 1 タスク。並列実行時は現在バッチの全タスク）
  - `## Pending Tasks`
  - `## Completed Tasks`
- `Current Task` は 0 または 1 件だけ許可する。空のときは `- なし` を置く
- `Pending Tasks` は未着手 task を 0 件以上置く。空のときは `- なし` を置く
- `Completed Tasks` は完了 task を 0 件以上置く。空のときは `- なし` を置く
- task の status は checkbox ではなく section の位置で決まる
- 各 task は `T-1`, `T-2`, ... の連番 Task ID を持つ
- 各 task の `Current Task` セクション内に `Fix Attempts: <N>` を持つ。初期値は `0`。`gdd-systematic-debugging` が `implementation_fix_only` を選択するたびに +1 する。task が `Completed Tasks` に移るときにリセットされる（次の task は `0` から開始）。`worklog.md` の Error Log と二重化することで、クラッシュによる worklog 書き込み漏れがあっても blind loop を検出できる
- 1 task に複数 AC を紐付けてよい。同じ AC が複数 task に現れる場合は `(primary: T-n)` で primary owner を明示する。`gdd-completion-check` 差し戻し時は primary owner の Task ID で reopen 先を決定する
- gdd-completion-check の差し戻しで複数 task を再オープンする場合は、tasklist 上の元の task 順で並べ、最初の 1 件だけ `Current Task` に戻し、残りを `Pending Tasks` に戻す
- 対応 task が無い failed AC は remediation task を作り、`Current Task` が空なら最初の 1 件を `Current Task`、残りを `Pending Tasks` に置く

## 更新責任

- **gdd-brainstorming**:
  - active worktree を解決する
  - `requirements.md` に要件・受入条件・実装方針を書く
  - `Behavior Change Summary`, `Route / Ownership Matrix`, `Sensitive Data / Masking Policy`, `Human Check Questions` を `requirements.md` に用意する（非該当なら `N/A` と根拠 1 行）
  - human check 前 `design.md` を lightweight design skeleton として整える
  - 上記 4 見出しを `design.md` skeleton に trace できる形で用意する
  - `Requirements Review Status=pending`
  - `Design Review Status=pending`
  - `Human Check Status=pending`
  - `Resume From=gdd-brainstorming` から始め、requirements review 待ちに入るときは `Resume From=gdd-requirements-gating`
- **gdd-requirements-gating**:
  - human check 前の requirements reviewer 群を回す
  - `Requirements Review Status`
  - `Planning Reviewer Selection`
  - `planning_rework_required` の前段として `gdd-brainstorming` へ戻す
  - human check handoff に `承認ポイント` を作る
  - route / ownership / prompt contract / output contract / sensitive data / masking / rollout / rollback に関する blocking `Open Questions` が無いときだけ `Resume From=human-check-waiting`
- **gdd-using-git-worktrees**:
  - formal workflow 開始時または legacy migration 時に dedicated worktree / branch を準備する helper
  - `Next Action` を所有しない
  - tracked root metadata を新 contract の state field として更新しない
- **gdd-design-gating**:
  - approved な `requirements.md` と human check 前 `design.md` skeleton をもとに detailed design を具体化する
  - `Planning Reviewer Selection`（design gate 分を累積追記）
  - `gdd-planning-reviewer` と applicable `gdd-security-reviewer` による detailed design gate を回す
  - `planning_rework_required` なら `gdd-brainstorming`、`human_recheck_required` なら `human-check-waiting`、`design_detail_only` なら `gdd-design-gating` に戻す
- **gdd-task-breakdown**:
  - `Review Status` の初期化
  - `Implementation Reviewer Selection` の初期化
  - 初期 `Next Action=gdd-test-driven-development`
  - `planning_rework_required` なら `gdd-brainstorming`、`human_recheck_required` なら `human-check-waiting`、`design_detail_only` なら `gdd-design-gating` に戻す
- **gdd-test-driven-development**, **gdd-subagent-driven-implementation**:
  - build フェーズの `Next Action`
  - `planning_rework_required` なら `gdd-brainstorming`、`human_recheck_required` なら `human-check-waiting`、`design_detail_only` なら `gdd-design-gating` に戻す
- **gdd-implementation-gating**:
  - `Implementation Reviewer Selection`
  - applicable formal implementation reviewer に関する `Review Status`
  - `Next Action`（次の task または gdd-completion-check / gdd-systematic-debugging）
- **gdd-requesting-code-review**, **gdd-receiving-code-review**:
  - advisory lane のみを扱う
  - formal な `Next Action`、`Review Status`、`Gate Status` は所有しない
- **gdd-systematic-debugging**:
  - 戻り先に応じた `Next Action`
  - テスト設計不足 / failing test 不足なら `gdd-test-driven-development` に戻す
  - `implementation_fix_only` なら build 内で閉じる
  - `planning_rework_required` なら `gdd-brainstorming`、`human_recheck_required` なら `human-check-waiting`、`design_detail_only` なら `gdd-design-gating` に戻す
  - 同じ `Current Task` に対する repeated `changes_requested` では blocker 比較と `worklog.md` を使って blind loop を防ぐ
- **gdd-completion-check**:
  - `Verification`
  - `gdd-completion-reviewer` の `Review Status`
  - reviewer selection record の妥当性確認
  - 差し戻し時の reviewer status リセット
  - 外部前提不足では `Next Action=gdd-completion-check` を維持し、不足前提のチェックリストを返す
  - 最終 `Next Action`（gdd-completion-check / done / cancelled / gdd-systematic-debugging）
