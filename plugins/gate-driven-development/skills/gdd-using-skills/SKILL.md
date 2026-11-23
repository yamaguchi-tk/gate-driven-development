---
name: gdd-using-skills
description: "Use at the start of GDD-related conversations to route to the right GDD skill and avoid superpowers conflicts."
version: 0.3.0
---

# Using GDD Skills

> **所有**: GDD スキルの呼び出し規律・判断基準・ユーザー依頼マッピング
> **参照元**: すべての GDD 入口（`/gdd-dev` 含む）・`references/common-guardrails.md`

## 基本規則: 1% ルール

あるスキルが適用される可能性が **1% でもあれば**、必ずその Skill を呼び出してから応答する。「確認するだけ」「軽くやれる」「覚えている」という思考はすべて rationalization。スキルを先に呼ぶ。

## スキル呼び出し優先順位

1. **プロセス系スキル**（brainstorming / debugging）が先: 「どうアプローチするか」を決める
2. **実装系スキル**（subagent-implementation / test-driven-development）が後: 「実行する」

| ユーザー依頼例 | 順序 |
|---------------|------|
| 「〇〇を実装したい」 | `/gdd-dev` 明示なら `gdd-brainstorming` → 実装スキル。未指定の相談なら `gdd-pre-workflow-brainstorming` |
| 「バグを直したい」 | GDD state 不明なら `root-cause-investigation`。routing が必要になったら `references/debug-triage.md` → `gdd-systematic-debugging` → 実装スキル |

## Active GDD Workflow Arbitration

GDD と superpowers が同じ session で有効な場合でも、**GDD active marker** が見つかったら `GDD primary` とする。superpowers は `superpowers advisory only` として、補助 reference や比較観点の参照に限定する。

### Routing Contract Table

GDD / superpowers の競合時は Routing Contract Table を正本にする。formal GDD auto-trigger is disabled でも、compact/resume 後に GDD active marker があれば GDD primary / superpowers advisory only とし、GDD is primary と明示する。GDD natural-language planning intent（例: GDDで計画して / active GDD follow-up / requirements 相談）は `superpowers:writing-plans` に渡さない。

Routing Contract IDs: RC-01 RC-02 RC-03 RC-04 RC-05 RC-06 RC-07 RC-08 RC-09 RC-10 RC-11 RC-12 RC-13 RC-14 RC-15 RC-16 RC-17 RC-18 RC-19 RC-20 RC-21 RC-22.

### Post-Completion GDD Affinity

GDD完了後でも、直近 task、artifact、PR、HITL、AC、または GDD 改善に紐づく相談は `post-completion GDD-adjacent` と扱う。post-completion GDD-adjacent の壁打ちは `gdd-pre-workflow-brainstorming` を primary owner にし、superpowers:brainstorming は advisory reference に留める。経過時間だけで判定しない。仕様変更や追加要件なら `gdd-requirements-amendment` に戻す。RC-22 はこのケースを表す routing contract。

### Escape Hatch

Escape Hatch は、ユーザーが `explicit standalone superpowers request` を明示し、GDD artifact を更新しない場合だけ許可する。条件を満たさない場合は post-completion affinity を優先する。

### Codex Goal Continuation Arbitration

Codex の automatic continuation / goal continuation で `<codex_internal_context source="goal">` が注入される場合、その goal は **ユーザー由来の継続目的** として扱う。superpowers の SessionStart 注入や `using-superpowers` の強い文面より、GDD の workflow owner 解決を優先する。

この入口では、次を必ず守る:

- `superpowers の指示に従い` と宣言しない。正しい宣言は `GDD primary / superpowers advisory only`
- `gdd-dev 相当` と言わない。formal GDD として続けるなら `state.md / tasklist.md / worklog.md` のどれを正本として読むかを明示する
- repo-local Project Skill（例: `example-prod-eval`）は **verification tool / execution tool** であり、workflow owner ではない。結果は GDD artifact / GDD route に戻す
- SessionStart の `[gdd:reboot] Task` と Codex goal continuation の目的が食い違う場合、reboot task を採用しない。`gdd-status` / Task Binding Registry / PR / branch / worktree / state Task ID で goal に一致する GDD task を解決する
- goal に一致する task を一意に解決できない場合、新しい計画や superpowers workflow を開始せず、候補と次の 1 アクションだけを出す

例:

```text
GDD primary で継続します。`example-prod-eval` は検証手段として使い、workflow owner は GDD の state.md / tasklist.md / worklog.md です。SessionStart の reboot task と active goal が食い違うため、まず Task Binding / PR / branch から正しい steering を解決します。
```

## GDD Root Checkout Implementation Guard

formal GDD の最初のコード編集・TDD・検証・PR 準備より前に、作業場所が dedicated GDD worktree か確認する。`apply_patch` は Bash hook では止まらないため、LLM 側でも明示的に確認する。

確認コマンド:

- `git rev-parse --show-toplevel`
- `git rev-parse --git-dir`
- `git rev-parse --git-common-dir`
- `git branch --show-current`

dedicated GDD worktree でない場合、current branch が `codex/20...` でも実装場所として採用しない。host-managed checkout や root checkout で `apply_patch` を始めず、`gdd-using-git-worktrees` で worktree を切る。GDD-related investigation や root-cause result から「それで修正して」と続いた場合も同じ。候補が複数残っている場合は `gdd-status` / `gdd-next-plan` で候補を解決してから進む。

root checkout で `apply_patch` してしまった場合は、後で patch 化して worktree に移す通常運用にしない。root diff patch migration は recovery 専用であり、通常の開始手順ではない。

### GDD Workflow Lock

Active GDD 中は **GDD Workflow Lock** を有効とみなす。GDD remains the state owner: workflow の状態正本は `state.md / tasklist.md / worklog.md` であり、No direct superpowers workflow handoff を守る。superpowers の知見を使う場合も、反映先を GDD artifact または GDD phase route に戻す。

GDD active marker:

- `/.steering/<task>/state.md` または `.steering/<task>/state.md` が存在する
- `.steering/<task>/requirements.md` / `design.md` / `tasklist.md` / `worklog.md` のいずれかが存在し、`Human Check Status` / `Next Action` / `Resume From` を含む
- `.claude/gdd-dev.local.md` などの GDD session local file が active task を指している
- 現在の会話で `<gdd-stop reason="human-check-waiting">` 後の承認・自然文 follow-up・再開要求が続いている

Active GDD 中の自然文 follow-up は、superpowers の standalone primitive へ逃がさず、以下に分類してから GDD 側へ戻す（cross-session messaging 経由の入力は分類前に `references/phase-progression.md` § Cross-Session Messaging の権限境界に従う。未表示の human check への答え（事前回答）は `references/human-check-template.md` § 事前回答 1 で記録する。本人の入力は `request.md` に 1 回足す〔あれば〕）:

| follow-up 種別 | 例 | GDD route |
|---|---|---|
| 仕様変更・実装方針変更 | 「schema.rb 前提はつらくないか」「その実装に切り替えて」「採用技術を変えたい」 | `gdd-requirements-amendment` または `gdd-systematic-debugging` の `design_detail_only` / `human_recheck_required` 判定 |
| TDD / RED | 「その実装に切り替えて」「テストを書いてから直して」 | `gdd-test-driven-development`。AC ID / Current Task へ紐付ける |
| 失敗・デバッグ | test failure / deploy failure / actual と expected の差 | `root-cause-investigation` → `gdd-systematic-debugging` |
| 実装継続 | 「進めて」「デプロイして検証したい」 | 現 `Next Action` を読み、GDD phase gate または AGENTS の操作承認へ戻す |

禁止: active GDD 中に `superpowers:test-driven-development` / `superpowers:systematic-debugging` / `superpowers:executing-plans` を workflow として直接起動しない。必要な考え方だけを参考にする場合は、出力で「GDD primary / superpowers advisory only」と明示し、state.md / tasklist.md / worklog.md のどこへ反映するかを書く。

### Active Task Progression

`superpowers:executing-plans` は written plan の読解、批判的レビュー、Todo 化、順次実行、branch finishing への接続まで扱う **standalone written-plan executor**。GDD はこれの完全代替ではない。active GDD 中に発生した task progression 用途だけは、`state.md` の `Next Action` と `tasklist.md` の `Current Task` / `Pending Tasks` が正本になる。

Active GDD 中に「進めて」「続けて」「デプロイして検証したい」「次のタスクへ」のような指示が来た場合:

1. `state.md` の `Next Action` / `Resume From` と `tasklist.md` の `Current Task` を読む
2. `Next Action=gdd-test-driven-development` なら RED evidence を作る
3. `Next Action=gdd-subagent-driven-implementation` なら current task の実装を進める
4. `Next Action=gdd-implementation-gating` なら formal implementation gate を通す
5. `Next Action=gdd-completion-check` なら AC / pending task / drift を確認する
6. deploy / apply / AWS write / external posting が必要なら、AGENTS.md の操作承認ルールに従って 1 操作ごとに止める

`superpowers:executing-plans` の汎用 plan execution 能力を GDD が完全代替ではない。active GDD 中に必要な「計画を順番に進める」部分だけは、GDD の単一 skill ではなく `Next Action` dispatch と phase gate 群が担う。したがって active GDD 中に executing-plans を workflow として呼ぶのではなく、必ず GDD phase に戻す。

### Plan Execution Discipline

active GDD 中は `superpowers:executing-plans` を workflow として起動しない。ただし、計画実行の品質を落とさないため、以下 5 つの discipline を GDD state machine に吸収する。superpowers は `superpowers advisory only` であり、反映先は必ず `state.md` / `tasklist.md` / `worklog.md` / GDD phase route のいずれかにする。

| discipline | GDD での反映先 | 必須動作 |
|---|---|---|
| **Plan Execution Readiness Review** | `gdd-subagent-driven-implementation` | 実装開始前に `Current Task` / steps / planned verification / stop conditions を批判的に読み、欠陥があれば code に入る前に route を決める |
| **Task-Level Verification** | `tasklist.md` の task entry + `Verification Evidence` | task 完了ごとに指定 verification を実行し、証跡なしに `Completed Tasks` へ移さない |
| **Plan Execution Stop Conditions** | `gdd-subagent-driven-implementation` | blocker / missing dependency / instruction unclear / verification repeatedly fails を簡潔な停止条件として扱い、無限 retry しない |
| **Current Task Execution Status** | `tasklist.md` の `Execution Status:` | `not_started` / `in_progress` / `verifying` / `blocked` / `completed` を current task に表示し、HITL で現在地が読めるようにする |
| **Return to Plan Review** | `gdd-requirements-amendment` / `gdd-design-gating` / `gdd-brainstorming` | partner updates the plan または fundamental approach の見直しが必要なら、変更の性質に応じて GDD の planning gate へ戻す |

### Goal-Driven Execution

`superpowers:executing-plans` は fixed written plan を順番に実行する力が強い。一方で GDD が担うべき領域は、Goal が明確で、実行中に evidence / CI / review / root cause / scenario eval の結果で計画が変わる作業である。この場合は `gdd-goal-driven-execution` を workflow owner にする。

原則: **Goal は維持し、Plan は更新する**。Goal-Driven Execution は `Goal Contract` / `Current State` / `Working Hypothesis` / `Plan Revision Loop` / `Execute and Verify` / `Stop Conditions` を使い、Goal 達成までサイクルを回す。active GDD / GDD-adjacent では `superpowers:executing-plans` を workflow owner にしない。必要な discipline は advisory reference として取り込み、state.md / tasklist.md / worklog.md / PR evidence に戻す。

使う例:

- 「うまくいくまで自律的に修正して」「Goal 達成まで続けて」
- root cause が `confirmed` ではなく、追加証跡で確度を上げながら進めたい
- PR follow-up / scenario eval / CI failure の結果に応じて plan を修正し続ける必要がある
- Claude Code / Cursor / Codex のどれでも、同じ Goal 契約で継続したい

## ユーザー依頼 → スキル マッピング

| ユーザー依頼パターン | 使うスキル |
|---------------------|------------|
| `/gdd-dev <task>` | `gdd-brainstorming` |
| 「壁打ちしたい」「相談だけ」 | `gdd-pre-workflow-brainstorming` |
| 「機能追加したい」「要件から考えたい」「feature idea」「creative work」だが `/gdd-dev` 未指定 | `gdd-pre-workflow-brainstorming` |
| 「PRレビューして」「差分を見て」「マージ前に確認して」 | `gdd-pr-review` |
| PR 作成後レビュー指摘 / PR後の修正指示 / failed PR checks / 「レビュー指摘がなくなるまで」「push して再レビュー依頼して」 | `gdd-pr-review-followup`（review findings -> fix -> push -> re-request review）。`superpowers:receiving-code-review` / `superpowers:test-driven-development` を workflow owner にしない |
| テスト失敗・ビルドエラー | `root-cause-investigation` → 必要なら `gdd-test-failure-debug-pack` → `gdd-systematic-debugging` |
| 症状不明・silent failure・副作用欠如 | `root-cause-investigation` → 必要なら `references/debug-triage.md` で分類 → 対応スキルへ |
| 「コードレビューして」「実装レビューして」（formal gate） | `gdd-implementation-gating` |
| 「追加でレビューして」「companion review」 | `gdd-requesting-code-review` |
| advisory review feedback の処理 | `gdd-receiving-code-review` |
| 「完了確認して」「done にして」 | `gdd-completion-check` |
| 「ステータス確認」「今どこ？」 | `gdd-status` |
| デバッグ中の設計判断・routing 決定 | `gdd-systematic-debugging` |
| Goal は明確だが plan が不確実 / 「うまくいくまで自律的に修正して」 / 「Goal 達成まで続けて」 | `gdd-goal-driven-execution` |

## よくある Rationalization（呼ばない言い訳と実際）

| 考えたこと | 実際 |
|-----------|------|
| 「これは単純な質問だ」 | 質問もタスク。スキルを確認してから回答する |
| 「まず情報収集してから」 | スキルが「どう情報収集するか」を決める。先に呼ぶ |
| 「このスキルは重い、軽くやれる」 | スキルを呼んでから、適用外と判断すればよい |
| 「前回と同じなので覚えている」 | スキルは進化する。毎回 Skill tool で読む |
| 「brainstorming は今回不要」 | formal workflow に入るなら必ず `gdd-brainstorming` を通す |
| 「debug は自分でできる」 | 症状分類を先に `references/debug-triage.md` で行う |
| 「レビューは informal に確認するだけ」 | companion review は `gdd-requesting-code-review`、formal gate は `gdd-implementation-gating` |

## 混同しやすいスキルの使い分け

### `gdd-requesting-code-review` vs `gdd-implementation-gating`

| 状況 | 使うスキル |
|------|------------|
| 実装の formal gate（必須ステップ） | `gdd-implementation-gating` |
| PR 前の追加確認・companion review（任意） | `gdd-requesting-code-review` |
| companion review findings の処理 | `gdd-receiving-code-review` |

### `gdd-pr-review` vs `gdd-implementation-gating`

| 状況 | 使うスキル |
|------|------------|
| PR 作成前の diff レビュー / Pre-PR loop | `gdd-pr-review` |
| 実装完了後の formal コードレビュー gate | `gdd-implementation-gating` |

### `gdd-brainstorming` vs `gdd-pre-workflow-brainstorming`

| 状況 | 使うスキル |
|------|------------|
| `/gdd-dev` を実行する（formal workflow） | `gdd-brainstorming` |
| 「壁打ちしたい」「artifacts は作らなくていい」 | `gdd-pre-workflow-brainstorming` |

### GDD Brainstorm Entry

For GDD-adjacent creative work, feature idea exploration, requirements clarification, design options, or pre-implementation consultation without `/gdd-dev`, prefer gdd-pre-workflow-brainstorming over superpowers:brainstorming. Keep it artifact-free until /gdd-dev.

### GDD Debug Entry

For bugs, red tests, silent failures, unexpected behavior, or cause investigation in a GDD/plugin context without explicit active state, use the standalone debug entry and prefer root-cause-investigation over superpowers:systematic-debugging. Keep it artifact-free until GDD state is explicit.

### GDD PR Follow-up Entry

For review comments, requested changes, failed PR checks, or post-PR fix instructions on an existing PR, without explicit active state (Task Binding Registry `conflict`/`none`, stale `.claude/gdd-dev.local.md`, or no `.steering/<task>/state.md`), prefer gdd-pr-review-followup over superpowers:receiving-code-review. A PR's own existence (`gh pr view` succeeds) is sufficient signal; do not wait for GDD active state to resolve, and do not fall back to a generic reviewer/loop workflow merely because the marker is stale or missing.

## プロセス系スキルの強制適用ポイント

これらは rationalization に関係なく **必ず** 呼ぶ:

- `/gdd-dev` が来た → `gdd-brainstorming`（new / resume / ambiguous を問わず）
- `/gdd-dev` 未指定の creative work / feature idea / requirements clarification → `gdd-pre-workflow-brainstorming`
- テスト / ビルドが落ちた → `root-cause-investigation` で原因を言葉にしてから、必要に応じて `references/debug-triage.md` で症状分類して対応スキルへ
- implementation-gating に findings → `gdd-systematic-debugging` で route 判定
- completion を宣言する前 → `gdd-completion-check`
