---
name: gdd-status
description: "Use when the user asks where the GDD workflow is, what is done, or what remains."
version: 0.3.0
---

# GDD Status

現在の GDD の状態を 1 画面で可視化する。

## Goal

- ユーザーが「今どこにいるか」を即座に把握できるようにする
- 次に何をすべきかを明確にする
- gate の通過状況を一覧で見せる

## Evidence before claims

status 表示でも **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE** を守る。ステータス表示で pass / clean / done と言う場合、fresh verification evidence を `state.md / tasklist.md / worklog.md / ac-ledger.md`（AC Trace Ledger） から読み直す。会話履歴が欠落していても、`state.md / tasklist.md / worklog.md / ac-ledger.md`（AC Trace Ledger） を復帰正本として扱い、AC Trace Ledger が欠ける、または unverified / failed が残るなら done を断定しない。

## Fixed Model

- `Claude Code`: `sonnet` + `effort=low`
- `Cursor`: `Grok 4.5` + `reasoning.effort=low` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=low`
- 状態表示でも state / tasklist / routing source を読むため、mini には落とさない

## Steps

1. repo root / current working directory / current branch を確認する。
2. `scripts/gdd_task_binding.py resolve` と同じ deterministic resolver を使い、Task Binding Registry（`.gdd/tasks/<task_id>/binding.json`）から現在 task を解決する。
   - 実行できる環境では次を使う: `python3 <plugin-root>/scripts/gdd_task_binding.py resolve --repo-root <repo-root> --cwd <cwd> --current-branch <branch> --local-state-path .claude/gdd-dev.local.md --latest-user-text "<user text>"`
   - 自然文の「今どこ？」「続き」「再開して」は entry cue であり、task identity の根拠にはしない。
   - `codex_session_id` / `CLAUDE_CODE_SESSION_ID` / `.claude/gdd-dev.local.md` は soft signal。registry と current worktree が一致しない task を current として採用しない。
   - root 側 `.steering/...` は legacy diagnostic / migration source のみ。status の current task として自動採用しない。
3. resolver が `conflict` / `not_found` を返す場合は、state を読まずに「active workflow を一意に解決できません」と返す。候補、無視した legacy root steering、次の1アクションを表示し、古い task の phase を current として提示しない。
4. registry から active steering が一意に解決できた場合、binding の `steering_path` 配下から以下を読む:
   - `requirements.md` の冒頭（Task Size）と `Summary Brief` の「一言」
   - `state.md` の `Gate Status` セクション（`Resume From`, review status 群）
   - `tasklist.md` の `Current Task` / `Pending Tasks` / `Completed Tasks`（存在する場合）
   - `tasklist.md` の `Next Action`（存在する場合）
   - `findings.md` の要約（存在する場合、最初の 3〜5 件の発見）
   - hook error log（存在する場合、`.gdd/hook-errors.log` または `<worktree>/.gdd/hook-errors.log` の末尾 5 件）
4b. **Integrity Check（整合性チェック）**: state.md を読んだ後、以下のチェックを実行する。問題があれば後述の `⚠ Integrity Issues` セクションに出力する。

   **Compact Failure Reboot Mode**: ユーザー入力に `Error running remote compact task` / `responses/compact` / `503 Service Unavailable` が含まれる場合、これは Codex host の compact 503 からの復帰であり workflow failure ではない。loop state を消す停止（`done` / `cancelled` / `blocked` など）に進めず、以下を status 出力に追加する:
   - 観測事実: Codex compact 503
   - 復帰正本: planning 中は `state.md` の `Resume From`、build 中は `tasklist.md` の `Next Action`
   - 次の1アクション: `/gdd-dev resume <slug>` または現在 phase の skill 再実行
   - 注意: 同じ task の新規 worktree / steering を作らない

   **チェック1: Resume From 不正値**
   - `Resume From` の許容値: `gdd-brainstorming`, `gdd-requirements-gating`, `human-check-waiting`, `gdd-design-gating`, `gdd-task-breakdown`, `gdd-test-driven-development`（express 専用。`references/state-machine.md` § `Resume From` 参照）
   - `done`, `cancelled` または許容値外の値が設定されている場合は不正値として記録する
   - **Why:** `done` は `Next Action` の許容値であって `Resume From` ではない。不正値はセッション再開時に「完了済み」として誤解釈される

   **チェック2: gate status と Resume From の矛盾**
   - `Design Review Status: pending` かつ `Resume From` が `gdd-task-breakdown` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `gdd-implementation-gating` / `gdd-completion-check` の場合は矛盾として記録する（ただし `Task Size=quick (express)` かつ `Resume From=gdd-test-driven-development` の組み合わせだけ対象外。`human_recheck_required` 再承認時は `Design Review Status` が pending のまま（`references/state-machine.md` § 状態遷移一覧（quick standard / standard）の `human_recheck_required` を検知 行）、STEP 2 が `Task Size=quick (express)` なら `Resume From=gdd-test-driven-development` を記録する（同節の表直後の注記）ため、この組み合わせだけが正常系となる）
   - `Human Check Status: pending` かつ `Resume From` が `gdd-design-gating` 以降の場合は矛盾として記録する
   - **Why:** 前フェーズの gate が未承認なのに後続フェーズを Resume From に持つのは state の不整合

   **チェック3: tasklist.md の存在チェック**
   - `Next Action` が `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `gdd-implementation-gating` / `gdd-refactor-planning` / `gdd-completion-check` / `done` なのに `tasklist.md` が存在しない場合は記録する
   - **Why:** build フェーズは tasklist.md を正本として routing するため、存在しない場合は実装が行われていない可能性が高い

   **チェック4: 完了宣言と証跡の不整合**
   - `Next Action: done` または `Resume From: done`（不正値だが実際に存在する場合）なのに、`tasklist.md` の `Verification` セクションがないまたは `status=pending` が残っている場合は記録する
   - **Why:** completion-check を経由せずに done になった可能性を示す

5. 以下のフォーマットで出力する:

```
## Workflow Status

**Goal**: <Summary Brief の「一言」から取得>
**Task**: <steering ディレクトリ名から推定したタスク名>
**Size**: quick | standard
**Worktree**: <worktree パス>

### Task Identity
| Field | Value |
|-------|-------|
| task_id | <binding.task_id> |
| branch | <binding.branch> |
| steering | <binding.steering_path> |
| resolver | Task Binding Registry |

### Progress
phase: <current-phase> | tasks: N/M done | current: <current-task-name>
```

この 1 行は Stop hook が systemMessage に注入する形式と同一。ユーザーが自律実行中に見る情報と `gdd-status` で見る情報を一致させる。tasklist.md がない場合は `tasks:` と `current:` を省略する。

```

### Quick Reboot
| 質問 | 回答 |
|------|------|
| Where am I? | <現在の phase 名> |
| Where am I going? | <次の skill 名 or terminal state> |
| What's the goal? | <Summary Brief の一言> |
| What have I learned? | <findings.md の要約 or 「findings なし」> |
| What's blocked? | <Open Questions / blocking issues or 「なし」> |

### Gates
| Gate | Status |
|------|--------|
| Requirements Review | ✅ approved / 🔄 in_review / ⬜ pending / ❌ changes_requested |
| Human Check | ✅ approved / ⬜ pending / ❌ changes_requested |
| Design Review | ✅ approved / 🔄 in_review / ⬜ pending / ❌ changes_requested |

### Phase
**現在**: <phase 名>
**次のアクション**: <次の skill 名 or terminal state>

### Tasks (build phase のみ)
| # | Task | Status |
|---|------|--------|
| 1 | <task name> | ✅ completed |
| 2 | <task name> | 🔄 current |
| 3 | <task name> | ⬜ pending |

### ⚠ Integrity Issues（不整合あり時のみ表示）
| # | 種別 | 内容 | 推奨アクション |
|---|------|------|----------------|
| 1 | 不正値 | Resume From: done（許容値外） | `state.md` の `Resume From` を適切な値（例: `human-check-waiting`）に手動修正 → `/gdd-dev 再開` |
| 2 | 矛盾 | Design Review: pending なのに Resume From: gdd-task-breakdown | `state.md` の `Resume From` を `gdd-design-gating` に修正 → `/gdd-dev 再開` |
| 3 | 欠落 | Next Action: done なのに tasklist.md が存在しない | 実装が行われていない可能性。`/gdd-dev 再開` で completion-check を再実行し、不足分を補完 |
| 4 | 不整合 | Next Action: done なのに Verification に pending が残存 | completion-check 未通過の可能性。`/gdd-dev 再開` で AC 検証をやり直す |

### Hook Errors（hook error log がある時のみ表示）
| 時刻 | Hook | 内容 | 次の1アクション |
|------|------|------|----------------|
| <timestamp> | <hook name> | <error summary> | 状態を変更せず、該当 hook log と current steering を確認する |
```

整合性チェックで問題がない場合は `⚠ Integrity Issues` セクションを省略する。
Hook Errors は「GDD が壊れているかもしれない」診断情報であり、表示だけを行う。`gdd-status` は hook error log を消さない、state を修復しない、done / blocked に進めない。

6. active steering が複数ある場合は、すべてを一覧表示する。ただし、どれか 1 件を current として断定しない。

### Conflict Output

resolver が task を一意に解決できない場合は、通常の Workflow Status ではなく次の形式を使う:

```
## Workflow Status

active workflow を一意に解決できません。

### Resolver Result
| Field | Value |
|-------|-------|
| status | conflict |
| reason | <resolver の warning / reason> |
| current worktree | <cwd> |
| current branch | <branch> |

### Candidates / Diagnostics
| 種別 | task_id | branch | worktree | steering |
|------|---------|--------|----------|----------|
| registry | <task_id> | <branch> | <worktree> | <steering> |
| legacy root ignored | - | - | - | <root .steering path> |

### 次の1アクション
`/gdd-dev resume <task_id>` のように再開対象を明示するか、現在 worktree の task であれば Task Binding Registry を再生成してください。
```

## Output Rules

- ヘッダーやフォーマットの decoration は上記テンプレートに従う
- gate status のアイコンは ✅ / 🔄 / ⬜ / ❌ を使う
- tasklist が無い場合は Tasks セクションを省略する
- `gdd-stop` タグは使わない（状態表示は terminal action ではない）

## Workflow Control Hints

status 出力の末尾に、状況に応じたヒントを 1 行だけ付ける:

- active workflow あり → `ワークフローの中断・キャンセル・離脱は references/abandon-and-pause.md を参照`
- active workflow なし → ヒント省略

## Guardrails

- 状態の表示だけを行い、state を変更しない
- `Resume From` / `Next Action` を更新しない
- reviewer を起動しない
- artifact を作成・更新しない
- 自然文・session id・root `.steering` だけで task identity を決めない
