# Entry Intent Resolution

> **所有**: entry intent（new / resume / ambiguous）の判定ルールと優先順位
> **上位正本**: `state-machine.md`（active steering 解決、resume 正本切り替え）
> **参照元**: `gdd-brainstorming`

`/gdd-dev` 開始時に `gdd-brainstorming` が最初に解決する entry intent（`new` / `resume` / `amendment` / `ambiguous`）のルール。

## Intent 判定

| 条件                                                                                                                     | Intent      |
| ------------------------------------------------------------------------------------------------------------------------ | ----------- |
| `$ARGUMENTS` に明示 resume cue（`再開`, `続き`, `続きから`, `resume`）がある                                             | `resume`    |
| `$ARGUMENTS` に明示 new cue（`新規`, `新規開始`, `別件`, `新しい task`, `新しいタスク`）があり、resume cue と衝突しない  | `new`       |
| `$ARGUMENTS` が空でない具体的な新規 task 説明で、resume cue を含まない                                                   | `new`       |
| マージ済み / 実装済み機能への追加要件・仕様変更・不具合修正で、対象を一意に anchor できる（下記 amendment 判定条件参照） | `amendment` |
| 上記のどれにも該当しない（`$ARGUMENTS` が空、cue が弱い、cue が衝突する）                                                | `ambiguous` |

## Amendment 判定条件

以下の**すべて**を満たす場合に `amendment` と判定する:

1. 対象がマージ済みまたは実装済みの既存機能である（未マージのタスクへの変更は `resume` の scope）
2. active steering / 既存 artifact / 明示された既存 feature 名などから、変更対象を **一意に anchor** できる
3. 「追加要件」「仕様変更」「出力が違う」「これも対応して」「挙動がおかしい」「修正して」等のキーワード + 既存機能への変更要求がある

`既存コードのバグ修正` というだけでは `amendment` にしない。target を一意に anchor できない場合は、依頼内容が具体的なら `new`、具体性も不足していれば `ambiguous` に倒す。

`amendment` の場合は `gdd-requirements-amendment` に委譲する。

## 弱い継続 cue

以下の語は、単独では `resume` の決定打にしない。

- `続けて`
- `それで続けて`
- `進めて`

active steering を 1 件に一意に anchor できる場合だけ `resume` として扱い、anchor できない場合は `ambiguous` に倒す。

## Codex Remote Compact Failure Cue

Codex で以下の host error が出た直後の `/gdd-dev` / 自然文再開は、ユーザーが明示的に `new` を指定しない限り **resume cue** として扱う。

- `Error running remote compact task`
- `responses/compact`
- `unexpected status 503 Service Unavailable`

これは GDD workflow failure ではなく host-level interruption である。新しい worktree や重複 steering を作らず、既存の `Resume From` / `Next Action` / `worklog.md` を正本として再開候補を解決する。候補 0 件または複数なら fail-closed で人間に選択を求める。

### amendment vs human_recheck_required の違い

| 観点       | `amendment`                                                 | `human_recheck_required`                                      |
| ---------- | ----------------------------------------------------------- | ------------------------------------------------------------- |
| タイミング | `/gdd-dev` の entry intent 判定時                           | 実装中の Spec Change Detection 等で escalate                  |
| 対象       | マージ済み / 実装済み機能への**新しい変更要求**             | 進行中タスクの AC / Approved Direction からの**逸脱**         |
| 起動元     | `gdd-brainstorming` → `gdd-requirements-amendment`          | 各 skill → `rollback-patterns.md` の `human_recheck_required` |
| 結果       | 新しい steering を作って独立した amendment タスクとして進行 | 既存 steering の gate status を巻き戻して人間再チェック       |

## Express Hint

`$ARGUMENTS` に `--express` が含まれる場合、task sizing で `quick (express)` を強制提案する。ただし express 条件を満たさない場合は brainstorming で quick (standard) / standard に昇格する。`--express` は intent（new/resume/ambiguous）の判定には影響しない — intent を解決してから sizing に適用する。`--auto-confirm` は撤去した。含まれていたら無視し、express も human check を 1 回通ることを 1 行で伝える。

## 優先順位

1. 明示的な resume cue は、明示的な new cue と衝突しない限り、具体的な task 説明より優先する
2. 明示的な new cue がある場合は、既存 non-terminal steering があっても新規開始する
3. 既存 non-terminal steering があっても、明示的な新規 task 説明を勝手に resume に吸わせない

## Steering Candidate Hint

`setup-gdd-loop.sh` は `$ARGUMENTS` に明示 resume cue がある場合、または `$ARGUMENTS` が空の場合だけ、全 worktree の resume 候補を列挙して `gdd-dev.local.md` に `steering_candidate_count` を記録する。具体的な新規 task 説明がある場合は、別 worktree の途中タスクを通常チャットに混ぜないため候補列挙を行わない。

候補列挙では `gdd-using-git-worktrees` の **Worktree Identity Tuple** を必ず検証する。path slug / steering slug / state task id / git branch / state active branch の mismatch、同一 worktree の multiple non-terminal steerings、または mixed worktree bases を検出した場合、その candidate は auto-resume 候補から外し、`gdd-dev.local.md` に worktree pollution warning として露出する。

brainstorming は `resume` 判定時、または空プロンプトで `ambiguous` 停止する時にこの値を early-exit ヒントとして使える:

- `steering_candidate_count=0`: candidate 収集を実行しても 0 件になる可能性が高い。git worktree 列挙は実施するが、0 件確定なら即 fail-closed
- `steering_candidate_count>=2`: 候補一覧が `gdd-dev.local.md` のプロンプトに含まれている。brainstorming は一覧をそのまま提示して fail-closed 停止できる（worktree 列挙の再実行は任意）
- `worktree_pollution_warning_count>=1`: 明示 resume cue があっても auto-resume しない。候補表の mismatch reason を提示し、再開対象 / cleanup / 新規作成のどれを行うか人間に確認する

ヒントは setup 時点のスナップショットであり、brainstorming 実行時に状態が変わっている可能性がある。最終判定は git worktree 列挙を正本とする。

## Superseded Steering Handling

新規タスク（`new`）が既存の non-terminal steering（`human-check-waiting` / `requirements-gating` など planning phase 途中）の機能を包含する場合、旧 steering を **superseded** として明示的に記録する。

### 検知条件

- `new` タスクの scope に、既存の non-terminal steering が対象とする機能が含まれる
- 特に `human-check-waiting` で止まっている planning phase の steering が対象になりやすい

### 対処手順

1. 旧 steering の `state.md` を更新する:
   ```
   Status: superseded
   Superseded By: <新 steering の YYYYMMDD-slug>
   Superseded At: <ISO8601>
   Resume From: cancelled
   ```
2. 新 steering の `state.md` に `Superseded Steerings: <旧 slug>` を記録する
3. 旧 steering のファイル群はそのまま保持する（audit trail として）
4. **Reviewer Lineage の抽出**: 旧 steering の `Planning Reviewer Selection` / `Implementation Reviewer Selection` と最終 outcome を、新 steering の `Reviewer Lineage` section に append する。形式と運用は `references/reviewer-lineage.md` を参照（自動継承はせず、新 steering の reviewer selection の判断材料として使う）
5. **Lineage bias lint**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-reviewer-lineage.py --steering-dir <new-steering-dir>` を実行し、3 連続 waived / repeated changes_requested / long chain without rotation の WARN を確認する。WARN がある場合は brainstorming の Open Questions / Human Check Questions に「reviewer 再起動の検討」を追加し、人間判断に委ねる

**Why:** supersede を記録しないと旧 steering が宙ぶらりんのまま残り、後のセッションで `setup-gdd-loop.sh` の resume 候補に誤って混入する。`Resume From: cancelled` に更新することで candidate 列挙から除外される。Reviewer Lineage を引き継ぐと、同じ root feature の reviewer 判定（false positive の繰り返し / 一貫した waived 判断）を人間が把握できる。

## Default-to-New（Lightweight Path）

以下のいずれかを満たす場合、`ambiguous` でも fail-closed せず **`new` を default として進める**（revert 可能と明示する）:

- `$ARGUMENTS` に具体的な task 内容（動詞 + 対象）が含まれる + active resume candidate が **0 件**
- weak cue（`続けて` `進めて` 等）だけだが、active resume candidate が **0 件**

revert option として brainstorming 開始前に 1 行追記する:

> 「`new` task として進めます。既存タスクの再開が目的なら `/gdd-dev resume <slug>` と再入力してください。」

**Why:** 運用上 `ambiguous` の大半は「resume 対象が存在しない / 明確でない」ケース。candidate 0 件で fail-closed しても、ユーザーは結局 `new` で再投入するだけになる。default-to-new は摩擦を下げつつ revert path で誤動作を巻き戻せる。

## Fail-Closed 条件

以下に該当するときだけ fail-closed で停止し、候補一覧と選び方を返す:

- `$ARGUMENTS` が **空** + active candidate が **1 件以上**（どれを再開するか / 新規 task か明示を要求）
- 明示 resume cue（`再開` `続きから` `resume`）があり、candidate が **0 件** または同一優先順位 candidate が **複数**
- 明示 resume cue があり、候補に `worktree_pollution`（`path_slug_mismatch` / `state_task_mismatch` / `branch_slug_mismatch` / `active_branch_mismatch` / `mixed worktree bases` / `multiple non-terminal steerings`）が含まれる
- `$ARGUMENTS` に **conflicting cue**（明示 new cue と明示 resume cue が同時にある）
- 上記 default-to-new に該当しない `ambiguous`（例: `$ARGUMENTS` 空 + candidate 0 件 + weak cue のみ）

それ以外の `ambiguous` ケース（`$ARGUMENTS` 空 + candidate 0 件 など）は default-to-new path に倒し、まず `new` として brainstorming を開始する。task 内容が不足していれば brainstorming 内の Problem Discovery で確認する。
