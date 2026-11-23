# Phase Progression

> **所有**: phase 進行順序、remediation / completion のルール
> **上位正本**: `self-contained-contract.md`（fail-closed 条件）、`state-machine.md`（遷移表）
> **参照元**: 全 phase skill、`commands/gdd-dev.md`

`/gdd-dev` の phase 進行ルール。各 phase の詳細は対応する skill を参照。
タスク規模（`quick` / `standard`）による reviewer / phase 省略は `references/task-sizing.md` を参照。

## Autonomous Continuation

自走継続・stop 条件・`<gdd-stop>` マーカーのルールは `state-machine.md` の「Autonomous Continuation」を正本とする。
human check 承認後は**追加の人間承認なしで自走継続**する。

## Post-Merge Same-Chat Boundary

マージ後のローカル整理案内は、次 stage の実装計画より先に表示する。方針は **同じチャット継続 + stageごとに新 worktree**。cleanup 前に worktree 外へ保存されているかを確認し、worktree remove で消える artifact / continuation / 未 push 成果物がないかを見る。実行は `gdd-using-git-worktrees` に戻し、`worktree remove` と `branch delete` は候補提示後に行う。旧 worktree では後続実装しない。

### Merge Report Cleanup Trigger

ユーザーが `マージした` / `mergeした` / `merged` と報告した場合、それは cleanup cue かつ deployment/status verification cue でもある。safe cleanup ready の判定条件は `skills/gdd-using-git-worktrees/SKILL.md` の Post-Merge Cleanup に従う。safe cleanup ready なら、追加の cleanup 指示を待たず旧 worktree / branch を整理する。条件が揃わない場合は cleanup 候補とブロッカーを出し、後続実装は latest default branch から作る新 worktree に分離する。deploy/apply は既存 workflow の read-only 監視であり、手動 write 操作は別承認。

## Active Session Follow-up Classification

`.claude/gdd-dev.local.md` が `active: true` の間、後続のユーザー入力は GDD state machine の一部として扱う。host Plan mode や generic Agent process へ分岐せず、実装・修正・確認の前に次の表で route を分類する。

| User follow-up                                                                   | Route                                                                                                                                       | Human check                |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| 既存 AC 内の不具合修正 / テスト失敗修正                                          | `implementation_fix_only` / `gdd-systematic-debugging`                                                                                      | 不要                       |
| reviewer 指摘対応（既承認 AC 内）                                                | `gdd-pr-review-followup`                                                                                                                    | 不要                       |
| AC は同じで実装方式・設計詳細だけ変わる                                          | `design_detail_only`                                                                                                                        | 原則不要。判断根拠を記録   |
| AC の追加・削除・条件変更・意味変更                                              | `requirements_amendment`                                                                                                                    | 責任境界が変わる場合は必要 |
| policy / scope / ownership / security boundary / prompt-output contract が変わる | requirements/design 差分があるなら `requirements_amendment + human_recheck_required`。差分がなく再承認だけ必要なら `human_recheck_required` | 必要                       |
| 「Plan にして」「計画して」等の host planning 要求                               | この表で分類し GDD 内で処理                                                                                                                 | それ自体では不要           |
| 中止 / cancel / やめる                                                           | `cancelled`                                                                                                                                 | 不要                       |

`requirements_amendment` と `human_recheck_required` が同時に見える場合は、まず `requirements_amendment` として AC / requirements / design の差分を既存 steering に反映し、その差分が policy / scope / ownership / security boundary / prompt-output contract を変えるなら `human_recheck_required` として `human-check-waiting` に戻す。active session 中の `requirements_amendment` は「差分を作る処理 route」であり、`human_recheck_required` は「再承認が必要な停止 route」。この組み合わせを単純な `implementation_fix_only` に落としてはならない。

`requirements_amendment + human_recheck_required` では、task size / reviewer selection / model routing / ADR 起票要否 / tasklist reset を必ず再評価する。特に Dockerfile / container build / deploy boundary / ownership boundary が増えた場合は「実装詳細の追加」に倒さず、承認済み AC と設計への差分として記録してから再 gate に戻す。

### Same-Session Correction Rule

実装後、PR 作成後、deploy / E2E 後、または merge 直前までは、同じチャットセッション内でユーザーが「気になる」「ずれている」「これを直して」「追加で修正して」と言及した場合、まず **same-session correction** として扱う。新しい Plan / 新しい steering / 新しい worktree を作る前に、この表で現在の成果物への correction route を分類する。

PR が default branch へ merge 済みの場合は例外。自然文では「続きで」「追加で」と言われても、実装場所として元 worktree / 元 branch を再利用しない。まず `gdd-using-git-worktrees` の **Pre-Follow-up Hygiene Gate** で既存 worktree を整理し、その結果を HITL に出してから、latest default branch から新しい amendment / hotfix worktree を作る。

優先順位:

1. `<gdd-stop reason="done">` 前、または PR がまだ修正可能な同一ブランチ上にある → same-session correction を優先する
2. PR 作成後 / deploy / E2E 後で、同じ PR / branch に追加 commit できる → same-session correction を優先する
3. default branch へ merge 済みで、追加要件・仕様変更・受入条件変更・非緊急 follow-up → Pre-Follow-up Hygiene Gate の後、new amendment worktree を latest default branch から作る
4. default branch へ merge 済みで、production bug / 緊急 hotfix / 既に閉じたリリースへの修正として扱うべき場合 → Pre-Follow-up Hygiene Gate の後、Post-PR/Post-Merge Contract の Hotfix Lane を優先する
5. ユーザーが「別件」「新規」「新しい task」「新しい Plan」を明示した場合 → `new` intent を許可する

- 既存 AC の範囲内の実装修正、E2E で見つかった bug → `implementation_fix_only` / `gdd-systematic-debugging`
- reviewer 指摘（PR レビューコメント対応）→ `gdd-pr-review-followup`
- 承認済み挙動を変えない構造整理 → `gdd-refactor-planning`
- 当初目的の未達（例: 「シンプルにしたい」のに追加コード中心で削除が少ない）→ まず `requirements_amendment + human_recheck_required` として **現在の session / current steering / current PR** に追記・巻き戻し、別 Plan にしない
- 完全に別機能、別リポジトリ、またはユーザーが「別件」「新規」と明示した場合だけ `new` intent を許可する

**Why:** GDD は state machine を持つため、実装後の違和感を新規 Plan に逃がすと、元の Approved Direction と実装差分の対応が切れる。一方で merge 済み PR の branch / worktree に追加実装を載せると、完了済み steering と新テーマの branch が混線する。merge 前は same-session correction、merge 後は hygiene 済みの follow-up worktree に分けることで、原因追跡と worktree 分離を両立する。

#### Post-Merge Follow-up Worktree Policy

PR merge 後の追加実装は、同一セッション継続であっても元 worktree を実装場所にしない。元 steering は `done` の完了履歴として固定し、追加実装は new amendment / Hotfix Lane の新 steering として扱う。

標準フロー:

1. `gdd-using-git-worktrees` の Pre-Follow-up Hygiene Gate を実行し、既存 worktree の task id / branch / state / dirty diff / root bleed / multi-steering contamination を診断する
2. 整理結果を HITL に出し、「元 worktree は整理対象であり実装場所ではない」「新規 worktree の base は latest default branch」と明示する
3. 非緊急の追加要件・仕様変更は `.steering/YYYYMMDD-amendment-<slug>/` を作り、`Amendment of` / `Origin PR` / `Origin Branch` / `Origin Merge Commit` / `Base Branch` を記録する
4. production bug / urgent regression は Hotfix Lane として `.steering/YYYYMMDD-hotfix-<slug>/` を作り、`Origin Steering` / `Trigger Hotfix` / `Parent Hotfix` 規約に従う
5. 元 worktree は cleanup / archive / keep の対象として扱う。cleanup が完了していなくても、追加実装を元 branch に載せない

HITL には最低限、次を出す:

- `マージ後 follow-up 判定`: amendment / hotfix / read-only verification
- `既存 worktree 整理結果`: clean / dirty / polluted / host-managed / cleanup blocked
- `実装場所`: 新 worktree path と branch、base branch / base commit
- `先行成果物`: origin steering / PR / merge commit
- `人間が今やること`: cleanup 方針確認、または新 worktree 作成承認

#### Post-Done Correction Default

`<gdd-stop reason="done">` 発火後の修正依頼（same-session correction 対象）に Active Session Follow-up Classification を適用する際は、以下を default とする:

| 修正の性質                                                       | デフォルト分類                  |
| ---------------------------------------------------------------- | ------------------------------- |
| ユーザー向け挙動が変わる / 新しい条件・境界値が加わる            | `requirements_amendment`        |
| 実装が壊れているだけ（既存テスト fail、新挙動なし、AC 変更なし） | `implementation_fix_only` 許容  |
| 実装アプローチが変わるが、ユーザー向け挙動は変わらない           | `design_detail_only` 許容       |
| 上記どちらか判断できない                                         | `requirements_amendment` に倒す |

この表の適用は `done` 状態からの same-session correction 限定。`done` 前（実装途中）の follow-up には通常の Active Session Follow-up Classification テーブルを使う。

**Why**: `done` 状態は「承認済み要件を完全に実装した」状態を意味する。以降の修正依頼は定義上「承認外の変更」を含む可能性が高く、`implementation_fix_only` は例外（純粋バグ修正）としてのみ許容する。

分類結果は、human check に戻さない場合でも state.md / tasklist.md / worklog.md のいずれかに短く記録する:

```markdown
Follow-up Classification:

- route: implementation_fix_only
- reason: within AC-<id>, no scope/policy/security boundary change
```

## Express Path（quick express）

`quick (express)` は planning phase を大幅に省略する最短経路。

### Express フロー

```
gdd-brainstorming → human-check-waiting → gdd-test-driven-development →
gdd-subagent-driven-implementation → gdd-implementation-gating → done
```

### Express の遷移ルール

- `gdd-brainstorming` が Express テンプレートで `requirements.md` を作成し、`Requirements Review Status=approved` / `Design Review Status=approved` / `Human Check Status=pending` / `Resume From=human-check-waiting` を設定する
- requirements-gating / design-gating / task-breakdown / completion-check は skip する
- human check 承認後は `gdd-test-driven-development` に直接進む（`gdd-design-gating` を経由しない）
- `tasklist.md` は作成しない。`Next Action` は `state.md` の `Resume From` で管理する（build phase に入るまで）
- build phase に入ったら `tasklist.md` を最小構成で作成する:
  - `Current Task` に AC を直接紐付けた 1 タスクだけ配置
  - `Pending Tasks` / `Completed Tasks` は `- なし`
  - `Next Action=gdd-test-driven-development`
  - `Fix Attempts: 0`
  - `tasklist.md` の作成は `gdd-test-driven-development` の最初のステップとして実行する。作成前にクラッシュした場合は `state.md` の `Resume From` が復帰正本となり、`tasklist.md` 不在のまま planning candidate として再開される。再開後に `gdd-test-driven-development` が `tasklist.md` を再作成する
- impl-gate は `gdd-implementation-reviewer` の inline checklist を 1 回のみ実行し advisory 化する（High + ops-blocking medium のみ fail-closed で停止、それ以外の medium/low は remediation に入らず `state.md` の `## Advisory Findings (Express Impl-Gate)` へ記録し、post-completion PR flow がそこから PR 本文の `## Advisory Findings` 節へ搬送する）
- impl-gate 通過後は `done` に直接遷移する（completion-check skip、refactor gate もスキップ）

### Express → standard 昇格

Express 中に昇格条件（`references/task-sizing.md` § Express 昇格条件）を満たした場合:

- `Task Size` を `quick (express → standard)` に更新し、不足 phase を挿入する
- `Requirements Review Status=pending` に戻す
- `Design Review Status=pending` に戻す
- `Human Check Status` は現在値を維持する（承認済みなら `approved` のまま）
- `Planning Reviewer Selection=pending` に初期化する
- `Implementation Reviewer Selection` が存在する場合は削除する
- `Resume From=gdd-requirements-gating` に更新し、req-gate から再開する
- 昇格後は通常の quick (standard) フローに従う
- 詳細は `state-machine.md` § Express 昇格時の state ロールバック規則を参照

## Planning Phase

### gdd-brainstorming

- entry intent を解決後、dedicated worktree を canonical workspace とし `requirements.md` と `design.md` の draft を作る
- version-sensitive な利用技術は `tech-docs-searcher` などで最新情報を確認し、`Latest Tech Context` / `Open Questions` に残す
- 重要な途中判断は任意で `.steering/.../adr.md` に記録してよい

### gdd-requirements-gating

- `gdd-planning-reviewer` は常時必須
- selection は `Planning Reviewer Selection` として `state.md` に残す

### human check

- `gdd-requirements-gating` 通過後に 1 回実施。`requirements.md` の要件・受入条件・実装方針を承認対象とする
- `Human Check Status` に `waived` は使わない
- 承認後は `human_recheck_required` のときだけ再実施
- 旧 `Go1` / `Go2` の二段人間承認はこの command の契約に含めない

### gdd-design-gating

- `Human Check Status=approved` 後は、追加人間承認を待たずに AI が継続する
- approved な `requirements.md` と lightweight `design.md` skeleton をもとに detailed design を AI が具体化する
- 対象技術の最新情報を再確認し、`Latest Tech Context` と設計影響を `design.md` に残す
- `gdd-planning-reviewer` は常時必須。`gdd-security-reviewer` は `references/reviewer-selection.md` に従う
- selection は `Planning Reviewer Selection` として `state.md` に残す
- high 指摘は必ず解消。unresolved な medium が残る間は `gdd-task-breakdown` に進まない

## Build Phase

design gate 通過後は次の順に進める:

1. `gdd-task-breakdown`（依存グラフを構築し、並列実行の可否を判定）
2. `gdd-test-driven-development`
3. `gdd-subagent-driven-implementation`（mandatory refactor checkpoint を含む — 正本はこの skill。`gdd-implementation-gating` と `gdd-completion-check` は証跡確認のみ）
4. `gdd-implementation-gating`（必須レビュー）
5. 指摘が出た場合: `gdd-systematic-debugging` → リファクタ修正 → `gdd-implementation-gating`（再レビュー）
   5.5. `gdd-refactor-planning`（**Refactor Gate** — 全タスク完了後に一度だけ実行。タスクをまたいだ重複排除・命名統一などを点検し、改善機会があれば TDD → 実装 → impl-gate を 1 サイクル回してから completion-check へ。何もなければ即 completion-check へ。Express パスはスキップ）
6. `gdd-completion-check`

### External Guardrails Inventory（W-5）

design-gating の合否に関わらず、**deploy を伴う task（本番環境へのリリース / PR merge が含まれる）では `gdd-design-gating` の最終 step で `External Guardrails Inventory` を生成する**。

目的: SKILL.md ↔ hook ↔ runtime ↔ API gateway などの **inter-artifact 契約整合性** を事前に一覧化し、impl-gate / completion-check の reviewer が参照できるようにする。単一 artifact 内の correctness（unit test で検出可能）は対象外。

```markdown
## External Guardrails Inventory

生成日: <ISO 8601>

| #   | Artifact A       | Artifact B                 | 契約内容                                                     | 検証方法                        | 検証責任者    |
| --- | ---------------- | -------------------------- | ------------------------------------------------------------ | ------------------------------- | ------------- |
| 1   | SKILL.md         | PreToolUse hook allowlist  | 使用する tool name × body fields が allowlist に含まれること | hook 実行時ログ確認             | impl-reviewer |
| 2   | SKILL.md         | API gateway / external API | 呼び出す endpoint × required body fields が API spec と一致  | integration test or staging E2E | impl-reviewer |
| 3   | `build_prompt()` | skill 起動規約             | prompt 先頭に skill 起動指示が含まれること                   | prompt log 確認                 | impl-reviewer |
```

- `gdd-implementation-gating` の reviewer はこの表を参照し、未検証の行が残っていれば `changes_requested` を返す
- 表の行数が 0 の場合は「deploy 伴わない task と判定 / 不要」と明記する

### Staging Verification（W-6）

**deploy を伴う task では `gdd-completion-check` 内で `Staging Verification` を mandatory 化する**。

- `completion-check → done` への遷移は staging E2E が全 AC pass した後にのみ許可する
- staging E2E を実行できない環境（CI 未整備等）の場合は `gdd-completion-check` で `<gdd-stop reason="staging-verification-blocked">` を出し、ユーザーに手動確認を明示依頼してから `done` に進む
- Express パスでも deploy を伴う場合は同様に mandatory（Express の "completion-check skip" 規則は non-deploy task 限定）

### Parallel Execution（並列実行）

standard タスクでタスク数 3+ かつ依存グラフから並列バッチが構成できる場合、Build Phase は以下のフローを取る:

```
gdd-task-breakdown（Execution Plan: parallel + バッチ構成）
    ↓
Batch 1: RED（T-1, T-2 を並行） → GREEN+REFACTOR（T-1, T-2 を subagent で並列）
    ↓ 全タスク完了
Batch 1: impl-gate（T-1, T-2 をそれぞれレビュー）
    ↓ 全タスク通過
Batch 2: RED（T-3, T-4）→ GREEN+REFACTOR（並列）→ impl-gate
    ↓
... → gdd-completion-check
```

**並列実行のルール:**

- 同一バッチ内のタスクの変更ファイルが重なる場合は逐次に降格する
- バッチ内の 1 タスクが impl-gate で差し戻しになっても、他タスクはそのまま通過できる
- 差し戻しタスクは次バッチに先送りせず、同バッチ内で retry する
- 全バッチが完了したら `gdd-completion-check` に進む
- quick (express / standard) では並列実行しない（タスク数が少なく効果が薄い）

**In-flight overlap 発覚時のルール**（実装中に変更ファイル予定が重なったと分かった場合）:

task-breakdown 時の独立性確認は起動「前」1 回限り。実装中に設計変更等で ファイル overlap が発覚した場合は以下の手順で解決する。

1. 発覚時点で subagent は **main session に即報告する契約**（変更ファイル予定が増えたら tool 報告経由で main session に通知）
2. main session は **後発タスク（設計変更が後に起きた方 = 事後的に overlap を生んだ方）を abort し、次バッチへ先送り**
3. 先行タスクの WIP は **保持**（先行着手優先。既に投入された労力を捨てない）
4. abort されたタスクの差分は **discard**、worklog に以下を記録: `Abort Reason: in-flight overlap / Overlapping File: <path> / Preserved Task: <id>`
5. impl-gate は **タスク単位で部分通過可**。バッチ同期（全通過待ち）は必須ではない。先行タスクを先に通して後発タスクは次バッチで再計画する
6. abort 後、main session は `gdd-task-breakdown` を呼び出して残タスクと abort タスクの依存グラフを再構築する（overlap 解消後の新バッチ編成）

**判定優先順位**: 「どちらが後発か」は **変更ファイル予定が増えた時点が遅い方**。同時判定の場合は `tasklist.md` の `Current Task` 登録順で若い方を先行として扱う。

**Why**: 並列実行中の overlap は merge conflict・race condition の温床。後発 abort + 先行保持で既に投じた労力を守りつつ、再計画の契機を worklog に残すことで後追い可能にする。

**並列 batch 中に `human_recheck_required` が発火した場合のルール**（AC 境界越え等で 1 タスクが人間再承認に戻る必要が出た場合）:

並列 batch の 1 タスクで `human_recheck_required` が発火したら、**batch 全体を pause** する（in-flight overlap と違い、先送り単独 abort では済まない。境界越えは batch 前提が変わる可能性があるため）。

1. **通過済タスク（impl-gate approved）の commit**: **一旦保持**（revert しない）。再承認後の新 AC に対して valid か `gdd-task-breakdown` 再実行時に evaluate する。invalid と判断されたら cleanup task に降格して revert 対象に回す
2. **WIP タスク（実装中、未 impl-gate）の差分**: **discard**（再承認で前提が変わる可能性があり、WIP は信頼できない）。worklog.md に `Discarded WIP: <task-id> / Reason: parallel batch pause on human_recheck_required` を記録
3. **`human_recheck_required` 発火タスク自体**: 通常の全リセット経路に従う（Tasklist Reset Policy）
4. **再承認後の再開**: `gdd-task-breakdown` を必ず再呼び出す。既存通過分の Completed Tasks を carry-over するかは reviewer 判断 —— 新 AC と整合するなら残し、整合しないなら cleanup task に降格
5. **batch 組み直し**: 再承認後は元の batch 構成を復元せず、新 AC に基づいて依存グラフを再計算する

**Why**: 並列実行は「独立性前提」の下で投機的に進める。境界越え（= 前提崩れ）が起きたら投機分は保守的に扱う。ただし通過済 commit は「事実」として残し、後続で evaluate 対象にすることで無駄な再実装を避ける。この例外は並列文脈に閉じる（逐次実行時の `human_recheck_required` は通常通り Tasklist Reset Policy に従い全 revert 対象）。

**並列 batch で複数タスクが同時に異なる route を発火した場合のルール**:

1 turn 内で batch 内の複数タスクが `implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required` の異なる route を発火することがある。この場合の扱い:

1. **Batch Route Decisions の per-task 記録**: `state.md` の `Route In Progress` は並列 batch 中 `batch_mixed` を記録し、併せて `tasklist.md` の Current Task セクションに per-task マップを残す:
   ```
   Batch Route Decisions (2026-04-19T12:34:00Z):
   - T-1: implementation_fix_only
   - T-2: human_recheck_required
   - T-3: design_detail_only
   ```
2. **Batch 全体の遷移先は最も severe な route に倒す**: `planning_rework_required > human_recheck_required > express_promotion_required > design_detail_only > implementation_fix_only` の順（Escalation Decision Table の「下ほど安全側」と一致）。batch 全体の `Next Action` はこの優先順位で決まる
   - `express_promotion_required` は Express 中の 1 タスクが昇格条件（`references/task-sizing.md` § Express 昇格条件）を満たした場合の独立 route として扱い、`human_recheck_required` と **同等の batch pause 条件** を持つ（下記 Rule 3 参照）。severity 順では `human_recheck_required` より弱いが `design_detail_only` より強い
   - **2 task 同時 Express 昇格時の直列化**: 同一 batch 内で 2 task が同 turn に `express_promotion_required` を発火した場合、**小さい T-id を持つ task から順に直列で昇格処理**する（例: T-1 と T-3 が同時発火なら T-1 を先に処理し、T-3 は T-1 昇格完了後に再評価）。並列昇格は state.md の Requirements/Design Review Status の一斉 `pending` 戻しが race するため禁止
3. **Batch Pause 発動条件**: `human_recheck_required` / `planning_rework_required` / `express_promotion_required` が 1 つでも発火したら batch 全体 pause（既存並列 human_recheck ルールの拡張）
4. **`design_detail_only` 単独発火（severe route なし）**: batch pause せず、**当該タスクのみ `gdd-design-gating` に戻す**。他タスクは継続。design-gating 通過後に当該タスクは次バッチへ繰り越すか同バッチに再合流するかは reviewer 判断（整合性が取れれば同バッチ、崩れれば次バッチ）
5. **`implementation_fix_only` のみ複数発火**: batch pause せず、各タスクで fix_only ループを並列継続。WIP は discard しない
6. **Pause 中の `implementation_fix_only` WIP 扱い**: batch 全体 pause でも `implementation_fix_only` で remediation 中のタスクの WIP は **discard せず保留**（fix_only は自走範囲内のため、再開時に引き続き修正を続けられる）。ただし pause 契機が `human_recheck_required` で新 AC が承認されたら discard 対象に合流させる（新 AC で前提が変わるため）

**Worklog フォーマット**: 複数 route 同時発火時は `worklog.md` に以下で記録:

```
## Batch Route Decisions (YYYY-MM-DDTHH:MM:SSZ)
- Batch Pause: true (triggered by human_recheck_required)
- T-1: implementation_fix_only (WIP 保留)
- T-2: human_recheck_required (全リセット対象)
- T-3: design_detail_only (gdd-design-gating へ)
- Batch-wide Next Action: human-check-waiting
- 参照した正本: phase-progression.md § 並列 batch 複数 route 同時発火
```

**Why**: 並列 batch の本質は「タスクが独立している」前提。独立性が崩れた瞬間（= route がバラバラに発火）は、最も保守的な route に batch 全体を揃えて前提を再確認する。severe でない route（fix_only / design_detail_only 単独）は当該タスクだけで閉じて並列性を保つことで、不要な pause を避ける。

### batch_mixed Serialization Contract（state.md 並列書き込みの直列化）

`batch_mixed` 下では subagent が並列に各タスクを処理するため、`state.md` の `Batch Route Decisions` / `Bounce Log` / `Fix Attempts` 等を複数 writer が同時に touch する race リスクがある。以下の serialization contract で保護する。

1. **state.md 書き込みは main session のみ**: subagent は state.md を直接 edit しない。タスク処理結果（route 判定 / Bounce Log 更新候補行 / Fix Attempts 増分等）を tool 報告経由で main session に返す
2. **main session は 1 turn 内で順次 apply**: 全 subagent の結果を受信後、main session が 1 turn 内で `state.md` を atomic に更新する（複数 `Edit` ツール呼び出しを同一 turn にまとめる）
3. **同一 identifier への競合解決**: 同一 identifier-key（例: Bounce Log 行）への同時書き込みが発生した場合は「**先着の bounce_count を採用 + 後着は無視**」で決着する（二重 +1 を防ぐ）。「先着」の判定基準は **task-id 辞書順**（T-1, T-2, T-3 ...）で固定する（timestamp は精度不足、subagent 起動順は非決定的のため採用しない）。競合採用が発生した場合は main session が worklog.md に `## Bounce Log Conflict Resolution (ISO8601)` ブロックで「identifier-key / 採用 task-id / 無視 task-id / 各 subagent の bounce_count」を記録する（audit trail）
4. **Batch Route Decisions の per-task 順序**: `Batch Route Decisions` ブロック内の行順序は task-id の辞書順で固定（T-1, T-2, T-3 ...）。subagent 報告順に依存しない
   4a. **Approved Direction 末尾 per-task annotation の追記保護**: `state.md` の `Approved Direction` 末尾への per-task annotation 追記（Express 昇格時の境界記録、drift 発覚時の注記など）も **main session 単独 writer** 契約に含める。subagent は annotation を直接 edit せず main session に報告する。annotation フォーマットは固定で以下を使う:

   ```
   - [<ISO 8601>] [T-<id>] <body>
   ```

   - `<ISO 8601>` は書込み時刻（UTC）、`<id>` は task-id（`1`, `2a` 等）、`<body>` は 1 行要約
   - Approved Direction 末尾に時系列 append-only。既存行の改変は禁止
   - 複数 subagent の annotation が同 turn に集まった場合は task-id 辞書順でシリアル追記（Rule 3 の同一 identifier 解決方式を再利用）

5. **violation 検知時の fail-closed**: identifier-key 衝突・順序逆転・parse 失敗・**行欠落（partial write — subagent 報告数と apply 行数の差）** 等を検知した場合は state.md を変更せず停止し、`<gdd-stop reason="human-check-waiting">` で報告する
6. **partial write 検知時の Rollback 提示**: Rule 5 発火時は main session が以下 3 択をユーザーに提示する。(A) **discard all**: 当該 turn の全 apply 候補を破棄し state.md を apply 前状態に戻す（最も保守的）。(B) **apply verified subset**: parse 成功 + identifier 衝突なし + 報告完全な subagent 分のみ apply し、残りは worklog に未 apply 候補として記録。(C) **human review**: state.md を触らずユーザーが手動で state.md を編集する（非常口）。既定は (A)。選択後 worklog.md に `## Rollback Decision (ISO8601)` で記録

**Why**: 並列 writer による state.md race は「silent に片方の Bounce が消える」「Fix Attempts 増分が合算されず escape hatch 発動が遅れる」等の fail-open 経路を生む。main session 単独 writer + 先着採用ポリシーで deterministic な収束を保証する。

### Batch-Hotfix Bridge Contract（batch 中の Hotfix Lane 退避と手動 Hotfix 起動）

`batch_mixed` 進行中に `<gdd-stop reason="done">` 発行後の Hotfix 契機（PR CI High finding / production bug）が発火するケース、および active batch 中にユーザーが手動で Hotfix Lane を要求するケースは、既存の Post-PR/Post-Merge Contract §2 では扱えない。以下の bridge contract で補完する。

**Case 1: batch 途中で Hotfix Lane 退避が発生した場合**（例: T-1 done / T-2 fix_only 中 / T-3 が PR CI High で Hotfix Lane 行き）

1. **退避対象 task を `Batch Route Decisions` から外す**: 当該 task の行を削除し、worklog.md に以下を記録:
   ```
   ## Hotfix Diverted (YYYY-MM-DDTHH:MM:SSZ)
   - Task: T-3
   - Reason: PR CI High finding post done marker
   - Linked Steering: .steering/hotfix-null-ref-2026-04-19/
   ```
2. **残 task は batch 継続**: T-1 done 保持、T-2 fix_only ループ継続。`Route In Progress=batch_mixed` は維持
3. **batch_mixed clear 条件の第 4 項**: `state-machine.md` L208 の clear 条件に「**Hotfix Lane へ退避**」を追加済み（3 条件「impl-gate 通過 / abort / 次 phase に合流」に並ぶ第 4 項）
4. **Hotfix Lane 新規 steering**: 通常の Post-PR/Post-Merge Contract §2 に従い、`Origin Steering: local:<current-steering-path>` / `Origin Resolution Status: local` で hotfix steering を開設

**Case 2: active batch 中にユーザーが手動で Hotfix Lane を要求した場合**

既定は **queue**（現 batch 完了後に開始）。ただしユーザーが「緊急」を明示した場合のみ `batch_paused_for_hotfix` モードに入る:

1. **既定動作（queue）**: `batch_paused_for_hotfix=false` のまま。ユーザーに「現 batch 完了後に Hotfix Lane を開始します。緊急な場合は明示してください」と確認し、継続
2. **緊急明示時**: `state.md` に `batch_paused_for_hotfix: true` を立て、以下を実行:
   - 全 in-flight subagent 処理を graceful stop（既に完了した subagent 結果は state.md に apply）
   - 当該 batch の `Batch Route Decisions` / WIP / `Fix Attempts` はすべて **保持**（discard しない）
   - 別 worktree で Hotfix Lane 新規 steering を開設（`gdd-using-git-worktrees` § Hotfix Worktree に従う）
3. **Hotfix 完了後の batch 再開**: `batch_paused_for_hotfix=false` に戻し、保持された `Batch Route Decisions` を復元して batch 継続。`gdd-task-breakdown` 再呼び出しは不要（batch 前提は変わっていないため）
4. **緊急 Hotfix が batch 前提を変える場合**: Hotfix 内で `human_recheck_required` / `planning_rework_required` が発火したら、batch 側も `Batch Route Decisions` を discard して再計画に合流する。discard 時は main session が worklog.md に以下 schema で記録する:

   ```
   ## Batch WIP Discard (ISO8601)
   - Trigger: <hotfix human_recheck_required / hotfix planning_rework_required>
   - Route In Progress: batch_mixed → human_recheck_required
   - Discarded tasks:
     - T-2: <route=implementation_fix_only, Fix Attempts=N, WIP summary>
     - T-4: <route=impl-gate pending, WIP summary>
   - Preserved artifacts: <参照 path — worklog.md / tasklist.md Completed section>
   - Re-plan trigger: <gdd-brainstorming 再入 / gdd-design-gating 再入>
   - 参照した正本: phase-progression.md § Case 2 step 4
   ```

   Fix Attempts は discard 対象 task では reset to 0（新 scope で再カウント。`human_recheck_required` 経路の既存規約と整合）

   **discard 実行時の batch 側 state.md 書換規約（Resume 時 phase 判定の一意化）**:
   - batch 側 state.md の `Route In Progress` は `batch_mixed` から **`human_recheck_required` に書換**（`batch_mixed` のまま残さない）
   - 同時に `Batch Route Decisions` ブロックは **削除**（stale 情報として残さない）
   - 上記 `## Batch WIP Discard` worklog エントリの `Route In Progress: batch_mixed → human_recheck_required` 行で書換の audit trail を残す
   - Resume 時は `human_recheck_required` 経路で一意に phase 判定される（`batch_mixed` / `human_recheck_required` の曖昧さを排除）

**Why**: Hotfix Lane は `<gdd-stop reason="done">` 発行後の設計だが、「done 発行後に batch が別 task で継続中」という現実的経路が存在する。batch 途中退避を明示的に state machine に組み込むことで、batch stuck（`Route In Progress=batch_mixed` が Hotfix Lane 退避で clear できない）を防ぐ。手動 Hotfix は既定 queue で並列性を守りつつ、緊急時のみ batch pause を許容する。

補助:

- `gdd-using-git-worktrees` は worktree の preparation / guard / post-merge cleanup を担う helper
- `gdd-refactor-planning` は completion 後やレビュー後に挙動を変えないリファクタ計画を行う

## Implementation Review

- `gdd-implementation-reviewer` を常時必須にし、`gdd-security-reviewer` は `references/reviewer-selection.md` に従う
- selection は `Implementation Reviewer Selection` として `tasklist.md` に残す

## Remediation

- `changes_requested` はユーザー確認待ちの停止点ではなく、自律 remediation ループの開始点
- 優先順位、`ops-blocking medium` の定義、blind loop 防止ルール（3 回制限・escalation 条件）は `state-machine.md` の「Remediation Loop Safety」を正本とする
- `design_detail_only` / `human_recheck_required` / `planning_rework_required` は non-local な意思決定が必要な場合だけ使う
- stopped workflow の review / re-entry cue では、新しい worktree を作らず同じ active worktree の `gdd-systematic-debugging` で route を確定する

### Escalation Decision Table

`gdd-systematic-debugging` が route を確定する際の判定テーブル。上から順に評価し、最初に一致した条件の route を採用する。

| 条件                                                                                            | Route                      | 復帰先                                                                                                                                                                            |
| ----------------------------------------------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fix Attempts < 3 かつ High 減少中（root cause が異なる or 前回修正の波及）                      | `implementation_fix_only`  | 同 task build 継続                                                                                                                                                                |
| 同一 root cause が 2 回以上再発 + Approved Direction の自走範囲内                               | `design_detail_only`       | `gdd-design-gating`                                                                                                                                                               |
| Approved Direction の境界超過（AC 追加・削除、security 新規、認可・route 変更、外部依存変更、technology stack / access method / credential backend / multi-tenant boundary / official integration adoption 変更等） | `human_recheck_required`   | `human-check-waiting`                                                                                                                                                             |
| 初回試行で前提が崩れた失敗（structural mismatch）— eval ハーネスが MCP を強制無効化する等、設計前提そのものが崩れており refinement では解消できない場合。**リトライ回数を待たず attempt 1 で中断する** | `planning_rework_required` | `gdd-brainstorming`（refinement との区別: refinement = 実装修正で解消できる失敗 / structural mismatch = 前提 / 環境 / 設計方針そのものが崩れている失敗） |
| AC の全面やり直し / 前提崩壊（Problem Discovery からやり直し要）                                | `planning_rework_required` | `gdd-brainstorming`                                                                                                                                                               |
| **Fix Attempts ≥ 3 到達**                                                                       | route recalibration        | procedural / evidence only なら failing gate を再実行する build loop 継続、policy / scope / ownership / security boundary / prompt-output contract 変更なら `human-check-waiting` |
| 上記いずれも決めきれない / 判定情報不足                                                         | fail-closed `blocked`      | —                                                                                                                                                                                 |

**判定の優先順位**: 迷ったら **安全側に倒す**（上の行より下の行を選ぶ）。ユーザーが「もう 1 回 implementation_fix_only で」と明示しても、Fix Attempts ≧ 3 や Approved Direction 境界超過を override できない（`commands/gdd-dev.md` Instructions § Contract override 不可 を参照）。ただし **procedural / evidence only** の反復は policy-level 変更ではないため、Fix Attempts ≧ 3 でも自動で `human_recheck_required` に短絡しない。

**記録義務**: route を確定した瞬間に `worklog.md` へ「選んだ route / 該当条件 / 参照した正本」を残す。`Fix Attempts >= 2` で route 判断記録が無ければ fail-closed。

**複数境界が同時発火した場合の記録粒度**: `human_recheck_required` で複数の境界を同時に越えた場合（例: 「AC 追加」かつ「認可要件変更」）、主要因 1 つではなく **全ての境界をリスト形式で残す**。worklog.md に以下フォーマットで記録:

```
## Route Decision (YYYY-MM-DDTHH:MM:SSZ)
- Route: human_recheck_required
- Triggered Boundaries:
  - AC 追加: 「管理者ロールは全件取得できる」
  - 認可要件変更: 管理者ロール分岐の新規発生
- 参照した正本: phase-progression.md § Escalation Decision Table
```

再承認時は全境界に対する人間判断が必要。1 つでも未対応なら `human-check-waiting` を継続する。

### E2E Discovery Loop（E2E 発見ループ）

E2E / 本番確認で新しい問題が見つかった場合の自走ルール。`Approved Direction` が `state.md` に記録されている（= human check 承認済み）ことが前提。

- **自走できる条件**（すべて満たす場合、human check に戻さず AI が自走する）:
  1. 元の AC を壊さない（既存の pass 済み AC が fail に変わらない）
  2. `Approved Direction` の自走範囲と矛盾しない
  3. セキュリティ要件の新規発生ではない
  4. AC の根本的な追加・削除ではない（既存 AC の詳細化・修正は許容）
- **自走中のゲート**:
  - `implementation_fix_only`: reviewer なしで自走
  - `design_detail_only`: reviewer は通すが human check には戻さない
  - 修正後は通常通り `gdd-implementation-gating` を再通過する
- **human check に戻す条件**:
  - 上記 4 条件のいずれかを満たさない
  - `Approved Direction` に人間が設定した制限を超える
  - Scope Drift Guard が発動した（下記）
- **Scope Drift Guard**:
  - 発動条件は以下 2 つの **OR**（どちらかを満たしたら発動）:
    1. `state.md` の `Scope Drift Counter`（= `design_detail_only` 発動回数）が **3 を超えた**（= 4 回目以降）
    2. `state.md` の `Cumulative Changed Files` が brainstorming 時の「影響範囲の事前スキャン」ファイル数の **3 倍を超えた**
  - 判定は state field の数値で機械的に行う。worklog の自然文 grep は使わない（信頼性が低いため）
  - Guard 発動 = 即座に human check ではなく、「方向性と矛盾しないか」を再確認する契機
  - **発動時の必須手順**:
    1. 自走 4 条件（AC 不破壊 / Approved Direction 範囲内 / security 新規なし / AC 根本追加削除なし）を再評価し、結果を worklog に記録する
    2. 再評価結果が全 yes なら `Drift Review Required=true` フラグを立てて自走継続。次の `gdd-implementation-gating` で reviewer に可視化する
    3. 1 つでも no があれば `human_recheck_required` に倒して human-check-waiting に戻る
  - **`Drift Review Required` のクリア条件**:
    - 次の `gdd-implementation-gating` を `approved` で通過した瞬間に **`false` にリセット**
    - reviewer が Drift flag を見て「累積変更が Approved Direction と整合している」ことを明示的に確認する（reviewer checklist に追加項目として扱う）
    - impl-gate が `changes_requested` を返した場合は flag を維持したまま remediation へ進む
    - flag が累積して意味を失うことを防ぐため、**同時に true であるのは常に最新 1 世代のみ**（次 Drift Guard 発動時に上書きされる）
    - `human_recheck_required` に倒れて human-check-waiting に戻った場合、**新 Approved Direction が承認された時点で `false` リセット**（flag の目的である「自走範囲内の累積変更への reviewer 確認」は human check 再承認で代替されるため）
    - 世代交代時（Drift Guard 再発動で flag 上書き）に前回発動時の reviewer 未確認が累積している場合は、worklog.md に `Carried Drift Review: <前回 Drift Guard 発動時刻>` を記録。次の impl-gate reviewer が checklist で累積分も含めて確認する
  - 閾値（回数 3・倍率 3）は task size 別調整の余地あり（`references/task-sizing.md` 参照）。現在は全 size 共通値
- **Why:** 実際の開発では「作ってみたら分かること」が多い。E2E で env 未反映 → 契約変更 → packaging 不備 → runtime 設計変更と問題が連鎖する場合、毎回 human check に戻すと人間確認が爆発する。方向性が同じなら AI が自律的に吸収し、方向性が変わるときだけ人間に戻す

## Completion

- 未完了 task が残っている間は `gdd-completion-check` に進まない
- `tasklist.md` の `Verification` セクションへ AC ごとの結果と external security evidence を固定 schema で残す
  - field: `method` / `status` / `evidence` / `notes`
  - `status`: `pending` / `pass` / `fail` / `N/A` / `unsupported`
  - **AC 行では `pending` / `pass` / `fail` のみ**（`N/A` / `unsupported` は AC 行では禁止 — AC は測定可能でなければならない）
  - **`method` は非空必須**。`TBD` / `unknown` 等の未確定値は禁止 — method 未確定は方向性判断のため `human_recheck_required` に短絡する
  - **`status=pass` は `evidence` 非空必須**
  - schema 違反（AC 行での unsupported / method 空 / pass で evidence 空 / security pass で prod 未検証）は `gdd-completion-check` で fail-closed。詳細は `skills/gdd-completion-check/SKILL.md` § Schema Validation を参照
- `gdd-completion-reviewer` による包括レビューで横断的な漏れと reviewer selection の妥当性を確認
- 結果: `done` / `cancelled` / `gdd-systematic-debugging` への差し戻し
- required external security evidence の外部前提不足だけは例外で、`gdd-completion-check` のまま不足前提のチェックリストを返す
- `done` 到達後、`<gdd-stop>` を出す前に Post-Completion PR Flow を自動実行する:
  - `gdd-pr-review` の Pre-PR loop（PR 作成前チェックリスト含む）を呼び出す
  - 差分 scope 確認・worktree 状態確認・セルフレビュー・PR テンプレート/言語規約確認・PR 作成は `gdd-pr-review` が正本
  - High finding があれば `blocked` で停止、なければ PR 作成後に `done` で停止
  - ユーザーが「PR不要」と明示した場合だけスキップ
  - PR 作成後にレビュアー（Copilot 等）からコメントが届いた場合は `gdd-pr-review-followup` を呼び出す

### Post-PR / Post-Merge Contract

PR 作成後 / merge 後に発覚した finding の扱い（SRE フローで必ず起きる経路を明文化）:

**Manual merge continuation**:

- ユーザーが PR 作成後に手動で merge する運用では、`mergeした` / `マージした` / `merged` を「merge 後の read-only 監視・検証を再開する cue」として扱う。
- 直前の会話・worklog・assistant output のいずれかに「apply 完了を待つ」「deploy 後に続行」「merge 後に確認」「後続作業を実施」などの継続意図が残っている場合、追加の「続行して」を待たずに、merge 後 workflow 監視 → post-merge / post-apply verification → state/tasklist re-read → Approved Direction / 自走上限確認 → 残タスク確認 → `Planned Follow-up Stage Lane` の未着手 Stage 確認まで進める。
- `Planned Follow-up Stage Lane` に `Pending Stage ID` が残る場合は、後続 Stage をその場で勝手に実装開始しない。`Tracking Destination` が未作成なら新 steering seed / backlog / issue のどれに残すかを示し、`Human Recheck=required before implementation` なら次の `/gdd-dev` 入口プロンプトを出して停止する。
- `mergeした` は新たな write 操作の包括承認ではない。merge / apply / AWS write / production 操作は既存の approval gate を維持し、承認済みでない write が必要になった時点で停止して対象・影響・ロールバックを提示する。自走上限が `PR 作成まで` や `デプロイ準備まで` の場合でも、ユーザーが手動 merge した後の read-only 監視・検証は継続可。ただし deploy / apply / write 実行は別承認を維持する。
- apply / deploy が失敗して follow-up PR が作られた場合は、その PR を修正・監視する。follow-up PR も手動 merge されたら同じ continuation rule を再適用する。多段 follow-up でも、成功した apply と post-merge verification まで自走する。

**Why:** 手動 merge は GDD の自律 loop 外で起きるが、SRE / Terraform task では merge 後 apply が実質的な完了条件になる。`mergeした` のたびに「続行して」を要求すると、apply 成功後の実環境確認や残タスク照合が抜けやすい。manual merge を gate release として扱うことで、安全な read-only 後続作業だけを継続できる。

1. **PR 作成後 CI で High severity finding（`done` marker 発行前）**:
   - Post-Completion PR Flow は PR 作成後に **CI 完了まで待機**（最長 `PR CI Wait Timeout` で打ち切り）
   - CI fail で High severity があれば `<gdd-stop reason="blocked">` で停止。`Resume From=gdd-completion-check` を維持し、CI ログと finding 詳細を worklog に記録
   - CI pass で初めて `<gdd-stop reason="done">` 発行
   - CI timeout 到達時は `blocked` で停止（人間判断待ち）

   **CI Wait semantics（詳細契約）**:

   Post-PR CI の扱いは次の 3 状態に排他分類する。分類は以下の順で評価し、最初に一致した行の処理に倒す。

   | #   | 状態                  | 判定条件                                                                                                                             | 処理                                |
   | --- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- |
   | 1   | **CI 到達不能**       | `gh` バイナリ不在 / network error / 401/403 auth failure                                                                             | 原則 `blocked` 停止（詳細は下記 a） |
   | 2   | **CI 設定不明**       | `gh` 到達成功 + required checks API 応答成功 + required 配列が空 + `ci_required_overrides` も未設定                                  | `blocked` 停止（silent pass 禁止）  |
   | 3   | **CI 明示的に未設定** | `.github/` や `ci.yml` 系設定ファイルが repo に存在しない（確証あり） or ユーザーが `settings.json` で `ci_configured: false` を明示 | AC Verification fallback（下記 f）  |

   上記に該当しないパス（CI 正常動作）では通常の待機・判定（下記 b〜e）を行う。

   a. **CI 到達不能の下位分類**（状態 1 の詳細）:
   - **`gh` バイナリ不在**: fail-closed `blocked`（AC Verification fallback には倒さない — CI がある可能性を否定できないため）
   - **auth 401/403**: retry せず **即 `blocked`**（credential 破損・token 期限切れは待機で回復しない）
   - **network error（timeout / 5xx / DNS failure）**: exponential backoff で **3 回 / 最大 60 秒** 再試行。超過で `blocked`
   - いずれの blocked でも worklog に `CI Unreachable: <reason> / last-error: <文言>` を記録

   b. **required check の判定ソース**（状態 3 以外の通常パス）:
   - GitHub required checks API（`gh api repos/<owner>/<repo>/branches/<branch>/protection/required_status_checks`）を **一次ソース** とする
   - **API 応答取得成功時は API が絶対優先**。`ci_required_overrides` は **ignore**（API と override の merge / union / intersection は行わない）
   - API 到達不能（状態 1）または API 応答が空配列 + override 設定あり、の場合のみ `ci_required_overrides: [<check-name>, ...]` を採用
   - **override validation 必須**: override に含まれる check 名が PR の check run リスト（`gh pr checks`）に 1 つも存在しない場合は typo / stale と判断し fail-closed `blocked`（silent pass 防止）

   c. **partial pass の扱い**: required check が全 pass なら **partial pass も done marker 発行可**。ただし required 以外の check で fail があれば worklog に以下を記録:

   ```
   ## CI Partial Pass (YYYY-MM-DDTHH:MM:SSZ)
   - PR: <url>
   - Required Checks: all pass
   - Non-required Failed: <check-name-1>, <check-name-2>
   - Decision: done marker 発行（required 全 pass のため）
   ```

   required check 自体が fail なら full fail と同じ扱い（High severity 判定へ）

   d. **PR CI Wait Timeout override precedence**:
   - 既定値 1800 秒
   - `settings.json`（project root の `.claude/settings.json` 固定。sub-dir の settings.json は無視）の `pr_ci_wait_timeout_seconds: <秒>` で project-level override
   - steering 単位の override は `state.md` に `CI Wait Timeout Override: <秒> / Reason: <理由>` で記録
   - **優先順位**: `state.md override` > `settings.json override` > `既定値 1800`（steering の方が scope が狭く、意図が新しいため強い）

   e. **Idempotency**: 同一 commit SHA に対する CI 再 check 成功時、直前の Verification History エントリと **status が同じなら追記しない**（重複 log の防止）。status が変わった場合だけ新 entry を追加。これにより push なしの再 check で VH が肥大化しない

   f. **AC Verification fallback**（状態 3）: CI が明示的に未設定の確証が取れた場合のみ、`Verification` の AC 検証 evidence を最後の safety net とする（既存 completion-check § Step 1 と一致）。worklog に `CI Not Configured: AC Verification をもって done 判定 / 確証: <ci.yml 不在 or settings.json 明示>` を記録

   g. **Manual skip 禁止**: reviewer 判断で CI fail を無視して done marker を発行することは **不可**。CI 回避が必要なら必ず `human_recheck_required` 経路に倒し、人間再承認として記録する。PR 本文への「CI skip 理由」記載も done marker 発行の根拠にしない

   **Why**: CI 不在 / auth 失敗 / 空配列 / override 衝突はいずれも silent pass の温床となる。「到達不能 / 設定不明 / 明示未設定」の 3 状態で排他分類し、前 2 つは `blocked` に倒すことで done marker の silent 発行経路を塞ぐ。override は API fallback 専用と明確化し、typo 検出を fail-closed にすることで「override を追加したら silent pass が起きた」事故を防ぐ。

2. **PR 作成後 CI で High severity finding（`done` marker 発行**後**に後追いで fail した場合）** / **merge 後 production bug**:
   - `<gdd-stop reason="done">` 発行後に後追いで問題が見つかったら、**Hotfix Lane** として新規 `/gdd-dev` task を起こす
   - 元 steering との紐付けは新 steering の `state.md` に `Origin Steering: <root feature steering path>` フィールドを記録
   - **多段 hotfix（hotfix → hotfix）の紐付け規約**:
     - `Origin Steering:` は常に **root feature steering**（最初に機能を実装した steering）を指す。多段 hotfix でも root を絶対基準にすることで audit trail の遡行性を 1 ホップで保証する
     - 直前 hotfix を指すために `Parent Hotfix: <直前 hotfix steering path>` を併記する（root hotfix の場合は省略可）
     - 例: feat-A → hotfix-1 → hotfix-2 の場合、hotfix-2 の `state.md`:
       ```
       Origin Steering: .steering/20260301-feat-A/
       Parent Hotfix: .steering/hotfix-1-2026-04-15/
       ```
     - root feature steering が archive / discard されている場合も `Origin Steering:` の参照先は root を指し続ける（archive 前の scrub 禁止 — audit 遡行性を保つため path は残す）
     - **`Origin Steering:` value grammar（root が物理的に消えたケース対応）**: 参照先 root が **物理 delete** されて path 解決できない場合に備え、4 形式を許容する。`state.md` には `Origin Steering:` と対になる `Origin Resolution Status:` フィールドを併記する:
       - `local:<path>` — 通常の local path。root が local tree に存在する場合（`Origin Resolution Status: local`）
       - `snapshot:<snapshot-id>:<path>` — root が archive / tarball で scrub 対象外 snapshot に退避されている場合（`Origin Resolution Status: snapshot`）。snapshot-id は `snapshots/<ISO 8601>-<root-name>.tar.gz` 等の retrievable identifier
       - `git-ref:<tag-or-sha>:<path>` — root が git tag / commit sha で参照できる場合（`Origin Resolution Status: snapshot`）
       - `unresolved:<last-known-path>` — 物理 delete かつ snapshot / git-ref でも解決不能な場合（`Origin Resolution Status: unresolved`）。`<last-known-path>` は最後に観測された root の local path（audit 用に形だけ残す）。この形式のときは後述の VH Rehydration を **必須化** する
   - **Origin VH Rehydration（root が discard され VH が消失した場合の再水和）**:
     - 通常は root feature steering の `Verification History` に追記することで監査連鎖を保つが、root が **物理 delete** されて VH 追記先が存在しない場合、hotfix 側 steering の `tasklist.md` に `Origin VH Rehydration: required` フラグを立て、hotfix 側が VH を **self-contain** する
     - self-contain 時の hotfix `tasklist.md` には以下を含める:
       - `## Origin Verification History (rehydrated)` セクション: root で記録されていた AC 単位の pass/fail 履歴（入手可能な範囲で `snapshot:` / `git-ref:` から復元し、入手不能な分は `unknown (rehydrated)` と明示）。このセクションは rehydration 完了時点で **凍結**（root 由来の履歴の書き足しは禁止）。後から snapshot / git-ref で追加情報が取れた場合は `## Origin Verification History (rehydrated, extended YYYY-MM-DDTHH:MM:SSZ)` という別セクションを **新設** して追加する（既存行は改竄しない）
       - `## Verification History`（通常セクション）: hotfix 自身の AC 検証記録。root 由来の履歴と混ぜない（2 セクション並置）
     - rehydration が必須（`Origin Resolution Status: unresolved`）かつ VH 復元材料が全く無い場合は、`<gdd-stop reason="human-check-waiting">` で「root feature の VH が物理失失している。hotfix 続行には root の AC 再宣言が必要」と提示して `human_recheck_required` に倒す
     - **snapshot 退避された root の VH 追記先決定**（`Origin Resolution Status: snapshot`）: tarball / git-ref への書き戻しは非現実的なため、**hotfix 側の `## Origin Verification History (rehydrated)` に追記** する（すなわち `unresolved` と同じく self-contain に倒す）。`Origin VH Rehydration: required` を立てる点も同じ。差は rehydration 時の復元材料が snapshot / git-ref から取得可能である点のみ。tarball 本体は touch しない（audit 用 read-only artifact として保持）
   - **Parent Hotfix の cancelled / unmerged 扱い（chain depth の正確化）**:
     - `Parent Hotfix:` に記録する対象は **merge 済 hotfix steering のみ**。cancelled / unmerged（PR close 放棄、`blocked` のまま abandon）の hotfix は chain に含めない
     - cancelled な試行は audit 目的で `Abandoned Hotfix Attempts: [<path1>, <path2>, ...]` 配列として state.md に併記する（chain depth 計算からは除外）
     - 例: feat-A → hotfix-1（cancelled）→ hotfix-2（merged）→ hotfix-3 を起こす場合、hotfix-3 の `state.md`:
       ```
       Origin Steering: local:.steering/20260301-feat-A/
       Origin Resolution Status: local
       Parent Hotfix: .steering/hotfix-2-2026-05-02/
       Abandoned Hotfix Attempts: [.steering/hotfix-1-2026-04-15/]
       ```
     - chain depth は `Parent Hotfix` のみを辿って計算するため、cancelled hotfix は閾値 5 の上限消費に寄与しない（realistic な連鎖のみを数える）
   - **cancelled 化した trigger hotfix の Abandoned Hotfix Attempts 引き取り契約**:
     - `Trigger Hotfix`（state-machine.md § Hotfix Lane スキーマ参照）として記録した親 hotfix が後に `cancelled` 化した場合、子 hotfix 側は **stub.md 経由で Abandoned Hotfix Attempts 配列を引き取る**
     - 引き取り時は子 hotfix の `state.md` に `Abandoned Hotfix Attempts` に追記し、各エントリに `Inherited From: <cancelled trigger hotfix path>` を付記する:
       ```
       Abandoned Hotfix Attempts:
         - .steering/hotfix-x-2026-04-10/ | Inherited From: .steering/hotfix-trigger-2026-04-08/
       ```
     - stub.md § Abandoned Hotfix Attempts の single source of truth はそのまま維持（root archive 時は stub.md、未 archive 時は root state.md）。子側は「引き取ったことを示す annotation 付きで複写」し、stub.md 側の値を改竄しない
     - 引き取り実施は cancelled を検知した hotfix 起票 skill が担う（起票最初の step で `Trigger Hotfix` 状態を再評価するタイミング）。引き取り後は `Abandoned Hotfix Attempts` 件数閾値（3 件）の評価対象になる
     - **`Abandoned Hotfix Attempts` 件数閾値（cancel 連打の escape hatch）**: 同一 root に対する `Abandoned Hotfix Attempts` 配列の **要素数が 3 以上** になった時点で、次の hotfix 起票は `human_recheck_required` を強制発火する。理由: chain depth は cancelled を除外するため、cancel を繰り返せば閾値 5 を形式的に回避できてしまう。3 回連続で hotfix 試行が放棄された = root feature 側の再設計が必要、と判定して gate する。human_recheck 通過後に `Abandoned Hotfix Attempts` を 0 件に wipe する責務は戻り先 skill（`gdd-brainstorming` または `gdd-design-gating`）が担う（戻り先で root を再設計した前提で counter をクリア）
   - 元 steering の `tasklist.md` に `Verification History` サブセクションを追加し、後追い fail を audit trail として残す。元 steering が discard/archive の場合は **root feature steering の Verification History に追記**（root が archive 済でも VH の書き込みは許可、scrub 対象外）:
     ```
     ## Verification History
     - 2026-04-19T14:30:00Z: AC-2 status pass → fail
       Reason: production で null ref が発覚
       Linked Steering: .steering/hotfix-null-ref-2026-04-19/
     - 2026-04-22T09:15:00Z: AC-2 status fail → pass
       Reason: hotfix-null-ref で patch 適用
       Linked Steering: .steering/hotfix-null-ref-2026-04-19/
     - 2026-05-10T16:00:00Z: AC-2 status pass → fail
       Reason: 二次 regression が発覚
       Linked Steering: .steering/hotfix-null-ref-v2-2026-05-10/
     ```
     **VH schema（複数エントリ）**:
     - 時系列で **append only**（既存 entry は上書きしない）
     - 1 行目: `<ISO 8601>: <AC-ID> status <old> → <new>`
     - 2 行目以降: `Reason:` / `Linked Steering:` をインデント 2
     - `<old>` / `<new>` は `pending` / `pass` / `fail` / `N/A` / `unsupported` のいずれか
     - 同一 AC の pass → fail → pass → fail の繰り返しも時系列で全て残す
   - **Hotfix 世代数閾値（chain depth bounded guard）**:
     - `Parent Hotfix:` を辿った chain depth が **5 以上** で `human_recheck_required` を強制発火する（connection steering を作る前に人間判断に戻す）
     - chain depth は新 steering 作成時に計算: `Parent Hotfix` が無ければ depth=1、あれば親の depth+1
     - depth 5 到達時は新 hotfix steering の作成を中断し、`<gdd-stop reason="human-check-waiting">` で「連鎖 hotfix が 5 世代に達しました。root feature の再設計が必要な可能性があります」と提示
   - 元 steering 自体は done のまま再 open しない（reopening は state machine を複雑化させるため避ける）。hotfix lane の新 steering で独立して修正する

   ### Steering Archive / Scrub / 機密削除の規約（Fix X）

   #### X-1: Scrub 許可範囲マトリクス（N2-d）

   steering を scrub（機密情報削除）する際の対象スコープ:

   | 対象                                          | scrub 可否                              | 代替措置                                                                                                                                                                               |
   | --------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `Origin Steering:` の path 文字列             | **禁止**（audit 遡行性を保つ）          | —                                                                                                                                                                                      |
   | state field 値（Origin Resolution Status 等） | **禁止**                                | —                                                                                                                                                                                      |
   | AC 自然文本文                                 | **可**（情報粒度を落とす最小限に）      | scrub 箇所を `<redacted by security on ISO8601>` で置換し、AC-ID は維持する                                                                                                            |
   | `Behavior Preservation Invariants` テキスト   | **可（注意）**                          | scrub するとその invariant の sha1 prefix が変わり Bounce Log 継続性が切れる。sha1 変更前に `scrub_rev: old_sha1=<旧 8hex>, new_sha1=<新 8hex>` を Bounce Log 行に付記する（後述 X-3） |
   | `VH Reason:` 欄                               | **可**                                  | scrub 後の文言を記録し、append-only 原則は維持（行削除ではなく `<redacted>` 置換）                                                                                                     |
   | `worklog.md` 本文                             | **可**                                  | 機密行を `<redacted by security>` で置換                                                                                                                                               |
   | design.md / requirements.md 本文              | **可**                                  | 上記 AC scrub に準ずる                                                                                                                                                                 |
   | Root Cause Tag                                | **禁止**（escalation 判定の正本のため） | 機密固有名詞を含む場合は generic tag に変更（例: `prod-db-01-error` → `db-connection-error`）し worklog に変更記録を残す                                                               |

   #### X-2: Origin Resolution Status の mutability 規約（N2-g）

   `Origin Resolution Status` はホットフィックス起票時に **1 度だけ評価・記録**し、その後 snapshot → unresolved など実体が変化した場合は **hotfix 起票 skill が起票開始 step で必ず再評価**する:
   1. hotfix 起票の最初の step で `Origin Steering` が示すパスを検証する（local 存在確認 / tarball 存在確認 / git-ref 解決）
   2. 検証失敗（tarball が消えた等）なら `Origin Resolution Status` を一段階 downgrade して書き直す:
      - `local` → `snapshot` → `unresolved` の順（飛び越し可）
      - downgrade 時は worklog に `## Origin Resolution Downgrade (ISO8601) / From: <old> / To: <new> / Reason: <物理削除・tarball 欠損等>` を記録
   3. 責任主体は「次の hotfix を起票する主体（AI）」。定期 integrity check は補助。

   #### X-3: Scrub 由来の sha1 prefix 変化への対応（N2-j）

   invariant テキストが scrub で変更された場合、Bounce Log の sha1 補助 key との継続性が切れる。以下を必須化:
   1. scrub 実施者は scrub 前後の sha1 prefix 8 hex を計算し、Bounce Log 行の末尾に `| scrub_rev: old=<旧 8hex>, new=<新 8hex>` を追記する
   2. 以降の Refactor Gate Bounce Log の同一性判定は **旧 sha1 OR 新 sha1 のいずれかと一致すれば同一 invariant** と判定する（継承維持）
   3. `scrub_rev` を追記せずに scrub した場合は **bounce_count が 0 に見える silent reset** が発生する危険がある。scrub 後の最初の refactor 起動時に Step 0a の fail-closed 処理で不整合を検出し `human_recheck_required` に倒す

   #### X-4: Root Archive 時の Root Stub 保持（N2-m）

   root feature steering を archive（tarball 退避 + local 削除）する際、以下の **root stub** を local に残す:

   ```
   .steering/<root-name>-stub/
   └── stub.md
       # Root Stub for <root-name>
       - Original path: .steering/<root-name>/
       - Archive: <snapshot-id>
       - Archived at: <ISO 8601>
       - Active hotfix chains: [<path1>, <path2>]   # archive 時点の進行中 hotfix 一覧
       - VH merge manifest: 複数 chain の rehydrated VH を time-sort で結合した場合の canonical 順序
         - <ISO 8601>: <AC-ID> <chain-path> <status>
         - ...
   ```

   - stub は物理削除禁止（audit 用 read-only artifact）
   - `Abandoned Hotfix Attempts` の single source of truth は stub.md に集約する（root state.md が archive 済の場合）
   - stub が存在する場合、`Origin Resolution Status` は `local` ではなく `snapshot`（stub は local だが root 本体は archive）
   - **archive 実行 gate**: 進行中の hotfix chain が 1 つでも残っている場合、archive を中断し `<gdd-stop reason="human-check-waiting">` で「進行中 hotfix があるため archive 保留」と提示する

3. **PR reviewer が AC 未達を指摘（`done` marker 発行後）**:
   - `gdd-systematic-debugging` 経由で route を確定: AC 追加・削除なら `human_recheck_required`、AC 解釈違いなら `design_detail_only`、実装バグなら `implementation_fix_only`
   - 同一 steering を再 open するか Hotfix Lane を使うかは route に従う:
     - `implementation_fix_only` / `design_detail_only`: 同一 steering で再開（Verification History に `pass → fail` 記録）
     - `human_recheck_required` / `planning_rework_required`: Hotfix Lane として新規 steering

4. **PR Flow 中の High finding（`done` marker 発行前）**:
   - 既存ルール通り `blocked` 停止
   - `Completed Tasks` / `Verification` は **保持**（revert しない）。finding 解消後に Pre-PR loop を再実行する
   - finding が AC 変更を要求する場合だけ `human_recheck_required` に格上げする

**Why**: PR 作成後・merge 後の問題発覚は実務で避けられない経路。`<gdd-stop reason="done">` を契機に state machine を閉じる設計は保つが、hotfix lane を別 steering として扱うことで「done の不可逆性」と「現実の問題対応」を両立する。元 steering の Verification History は audit trail として残し、単体テスト合格時点の記録を改竄しない。

## Diff Routing（差し戻し先）

- `planning_rework_required` → `gdd-brainstorming`
- `human_recheck_required` → `human-check-waiting`
- `design_detail_only` → `gdd-design-gating`
- `implementation_fix_only` → build 内で閉じる

## External Verifier との共存

- external verifier hook の実装詳細や command surface は `gate-driven-development` 側で固定しない
