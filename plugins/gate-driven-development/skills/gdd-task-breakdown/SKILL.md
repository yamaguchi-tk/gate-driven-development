---
name: gdd-task-breakdown
description: "Internal: auto-routed only when Next Action=gdd-task-breakdown. Converts approved design into executable tasks."
version: 0.1.0
---

# Task Breakdown

承認済みの `requirements.md` と AI gate 通過済みの `design.md` を具体 task に落とす。worktree 準備は formal entry 時点で終わっている前提とする。

## Phase Gate Pre-check（必須）

`references/phase-gate-prechecks.md` § Template A（3-Gate Approval Required）+ § task-breakdown 固有追加 check を実行する。

加えて、HITL で承認された重要判断が受入条件（AC）として `requirements.md` に書かれていることを確認する（正本: `references/requirements-template.md` § 精度の第一原則）。承認された判断で AC に無いものを見つけた場合は、承認内容を変えずに AC として追記してから task 分割に進む。

**Express パスではこの skill に到達しない**: `Task Size = quick (express)` の場合は fail-closed で停止し、Express フローの誤 routing として報告する。

## Goal

- `tasklist.md` を作る
- tasklist 冒頭に Agentic Worker Header（Goal / Architecture / Tech Stack / Approved Direction / Human Recheck Boundary）を置く
- task と AC ID を結び付ける（人間が承認した重要判断は AC として書かれているため、AC カバレッジが承認内容のカバレッジを兼ねる）
- task 間の依存関係を `Depends on:` で明示する
- 依存グラフから並列実行可能なバッチを構成する（条件を満たす場合）
- 現在 task と残タスクを区別する
- build 開始時の `Next Action` を確定する
- `/gdd-dev` からは Claude Code: Sonnet subagent として / Cursor・Codex: worker 経由で dispatch される。`Next Action=gdd-test-driven-development` を state.md に設定し、tasklist.md を完成させた後、5行以内（報告行 1 行必須）の結果サマリーを返して終了する。TDD への継続はメインセッションが担う

## Next Exact Step Contract

tasklist には `Next Exact Step` / `Step Verification` / `Current Step Verification` を含める。subagent が leaf task だけを読んでも、先頭の未完了 step、実行する検証、期待結果が分かる状態にする。`Execution Status` は step と task の現在地を示すために使う。

## Fixed Model

- `Claude Code`: `sonnet` + `effort=medium`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light tier）
- 承認済み artifact を task に落とす中間整理なので軽いモデルを既定にする。cheap lane モデルでは task 分割の品質取りこぼしがあったため light tier を維持する

## Task State Rule

- `tasklist.md` は冒頭に **Agentic Worker Header** を持つ。`Goal` / `Architecture` / `Tech Stack` / `Approved Direction` / `Human Recheck Boundary` を 1 画面で読めるようにし、subagent が leaf task だけを読んでも全体方針・承認済み技術スタック・人間再確認境界を外さないようにする。
- `tasklist.md` には次の 3 セクションを作る。
  - `## Current Task`
  - `## Pending Tasks`
  - `## Completed Tasks`
- task の status は checkbox ではなく section の位置で決まる。
- `Current Task` の件数制約:
  - **逐次実行時**: 0 または 1 件までにする。空のときは `- なし` を置く。
  - **Gate Batch がある逐次実行時**（`Execution Plan` に `Gate Batch <N>` がある）: 同じ Gate Batch のうち、実装を終えた task（`Execution Status: completed`）と実装中の task を `Current Task` に置く（最大 3 件。条件は `references/task-breakdown-steps.md` § Gate Batch）。
  - **並列実行時**（`Execution Plan: Mode parallel`）: 初回バッチのタスクをすべて `Current Task` に置く。バッチ内タスクが複数でも構わない。空のときは `- なし` を置く。
- `Pending Tasks` と `Completed Tasks` は 0 件以上を許可し、空のときは `- なし` を置く。
- `Requirements Review Status=approved`、`Design Review Status=approved`、`Human Check Status=approved` の 3 つが揃った状態で `tasklist.md` を作った時点で、resume の build 正本は active worktree 側 `tasklist.md` に切り替える。
- いずれかの gate が未承認のまま `tasklist.md` が既にある場合は stale planning artifact とみなし、routing source にしない。
- planning 差し戻し後に再到達した場合は、差し戻しの route を問わず、全セクション（`Current Task` / `Pending Tasks` / `Completed Tasks` / `Implementation Reviewer Selection` / `Review Status` / `Verification`）を初期化して再生成する（`Reviewed by:` のある完了タスクは、先に `Pending Tasks` へ移す書き込みを挟んでから消す。`references/task-breakdown-steps.md` 手順 2）。`Completion` で始まる 3 つの field の行は引き継ぎ、task の `Fix Findings:` の行は作り直した task に写す。写し先、並列 batch の例外と作り直しで途切れる数えは `references/state-machine.md` § planning 差し戻し後の tasklist.md リセットに従う。差分更新はしない（`Route In Progress` は task-breakdown に handoff する前に `none` へ戻るので、route で範囲を分けられない）。`implementation_fix_only` は task-breakdown に再到達しない（build 内で閉じる）

## Inputs

- `.steering/.../requirements.md`
- `.steering/.../design.md`
- `.steering/.../adr.md`（存在すれば補助コンテキストとして読む）

## File Structure Map

superpowers `writing-plans` の file discipline を GDD tasklist schema に吸収する。task-breakdown は「何を作るか」だけでなく、**exact file paths** と **responsibility** を明示して、subagent / resume / review が同じ構造を見られるようにする。

`tasklist.md` には必要に応じて次の全体表を置く:

| path | action | responsibility | owner task |
|---|---|---|---|
| `src/example.py` | Modify | 入力 validation policy | Task 1 |
| `tests/test_example.py` | Test | policy regression | Task 1 |

各 task entry には `Files:` / `#### Files` block を置き、最低限次を分けて書く:

```markdown
#### Files
- Create: `path/to/new_file`
- Modify: `path/to/existing_file`
- Test: `path/to/test_file`
```

Rules:

- glob や曖昧なディレクトリ指定だけで済ませない。`src/**` ではなく exact file paths を書く。
- まだ存在しない file は `Create:`、既存 file は `Modify:`、検証 file は `Test:` に分ける。
- 「どの責務をどの file が持つか」を書く。責務が説明できない file は task に含めない。
- Files that change together should live together. 同じ責務の実装と test を別 task に分けすぎない。
- code step がある task は `Files:` に Create / Modify / Test のいずれかを必ず含める。
- 1 task が多数 file に広がる場合は、責務単位で task を分割する。
- LSP 対応言語 + Serena 有効時は、シンボル特定に grep より Serena を第一手にする（fail-open の詳細: `references/task-breakdown-steps.md`）。

## No Placeholders ポリシー

各タスクは subagent に渡す作業指示書である。subagent はプロジェクトコンテキストを持たない前提で書く。以下は **plan の欠陥** とみなし、書いてはいけない。詳細なパターンと grep 対象は `references/task-breakdown-steps.md` § No Placeholders パターン を参照。

- "TBD", "TODO", "後で実装", "詳細は後で決める"
- "適切なエラー処理を追加"（具体性なし）
- "Task N と同様"（繰り返しを省略しない — subagent は他のタスクを読まない）
- "テストを書く"（テストコードを示さずに）
- コード変更を含むステップにコード片がない
- 定義していない型・関数・メソッドへの参照

## Step Granularity

各 task の `#### Steps` に並ぶ 1 step は **1 action（2-5 分で完了）** に収める。「実装してテストする」のような複合 step は failure point を隠すので分解する。詳細は `references/task-breakdown-steps.md` § Step Granularity。

## Task Granularity Guide

各タスクは subagent が **1 回の集中作業で完了できる単位** にする。目安:

- **1 タスク = 1 つの論理的変更**（1 つの関数追加、1 つの API エンドポイント、1 つのコンポーネント等）
- **変更ファイル数: 1〜3 ファイル**（実装 + テスト + 型定義程度）
- **変更行数: 30〜80 行**（100 行超は分割を検討）
- **検証が 1 コマンドで完結する**（`npm test -- <file>` 等）

分割の判断基準: 「このタスクの RED テストを 1 つ書けるか？」— 複数の独立した失敗を 1 テストに詰め込む必要がある場合、タスクが大きすぎる。

逆に小さすぎる分割（型定義だけ、import だけ）も避ける。後続タスクが前のタスクの成果物なしにテストできない場合は 1 タスクにまとめる。

## Plan Execution Fields

各 task entry には、実装中の現在地と停止条件が HITL で読めるように以下の field を含める。これは `superpowers:executing-plans` の Todo 進行管理を active GDD の `tasklist.md` に吸収するための schema であり、task の section 位置（Current / Pending / Completed）を置き換えない。

```markdown
### Task: T-N <名前>

- Covers AC: AC-...
- Depends on: Task ... / なし
- Execution Status: not_started
- Complexity: standard | complex
- Judgment Change: yes | no
- Planned Verification: <task 完了前に実行する command / evidence>
- Stop Conditions: blocker / missing dependency / instruction unclear / verification repeatedly fails / なし
- Return Route: default=<implementation_fix_only|design_detail_only|human_recheck_required|planning_rework_required>; 条件別=<condition -> route>
- Carry Forward: <task 完了時に記入。次段が知らないと詰まる実測値のみ / なし>
#### Steps
1. ...
```

`Carry Forward:` は breakdown 時点では `<未記入>` でよく、**task 完了時（`gdd-subagent-driven-implementation` Step 12b）に埋める**。subagent の実装文脈は境界で破棄されるため（`references/context-budget.md` § Carry Forward）、次段が知らないと詰まる実測値だけをここに残す。判定基準・記入例・上限は同 reference が正本。

`Execution Status:` の allowed values:

- `not_started`: task-breakdown 直後、または Pending Tasks にある
- `in_progress`: 実装に着手済み
- `verifying`: 実装後の task-level verification 実行中
- `blocked`: stop condition に該当し、route 判定待ち
- `completed`: `gdd-subagent-driven-implementation` 手順 12b の条件（verification・REFACTOR・Self-Correct Pass・handoff）を満たした後（`gdd-implementation-gating` の前でもよく、Gate Batch では gate 待ちの目印になる）。Completed Tasks へ移すのは gate 通過後

`Complexity:` は `references/fixed-models.md` の `implementation` tier、`Judgment Change:` は `references/task-breakdown-steps.md` の同名の節に従う。`Planned Verification:` は 1 task に最低 1 つ、具体的な command / test 名 / evidence 種別を書く。書けない task は分割不足か AC 不明瞭として再設計する。`Stop Conditions:` は簡潔に書き、詳細は `worklog.md` に残す。

`Return Route:` は単一値にせず、default route と stop condition ごとの条件別 route を書く。default は rollback pattern（`implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required`）から選ぶ。条件別 route では GDD phase route（例: `gdd-systematic-debugging`）を書いてよい。例: `default=implementation_fix_only; 条件別=missing dependency -> design_detail_only, instruction unclear -> human_recheck_required, verification repeatedly fails -> gdd-systematic-debugging, approved stack drift -> human_recheck_required`。`approved stack drift` は `requirements.md` / `design.md` で承認した technology stack / access method / credential backend / external service / policy / scope から外れること。条件別 route が書けない task は、停止時の裁量補完を避けるため分割か設計確認に戻す。

## Subsystem Boundary Check

`gdd-brainstorming` の Subsystem Decomposition Gate を tasklist 化の直前に再確認する。task-breakdown は「大きすぎる requirements を無理やり task に切る」場所ではない。

- `requirements.md` / `design.md` に `Subsystem Decomposition Gate` があり、`first unit` / `deferred units` が指定されている場合: 今回の tasklist は `first unit` だけを Current/Pending に展開する。`deferred units` は task 化しない。
- gate が無いのに、tasklist 化中に独立 subsystem が複数見つかった場合: tasklist を作り切らず `human_recheck_required` または `planning_rework_required` に戻し、brainstorming で scope 分解をやり直す。
- `phased single steering` を使う場合: 各 phase が同一 AC family に属し、前 phase の成果物なしに後 phase が検証不能である理由を `Execution Plan` に記録する。
- 並列化の理由にしない。独立 subsystem は「同時に subagent へ投げる対象」ではなく、原則として別 steering / 別 phase に分ける対象。

## Plan Self-Review Contract

superpowers `writing-plans` の Self-Review を GDD tasklist schema に吸収する。tasklist.md 作成後、TDD に進む前に以下を全て確認し、未達ならその場で tasklist を修正する。

1. **Spec coverage**: `requirements.md` の全 AC が、少なくとも 1 task の `Covers AC:` に対応している（人間が承認した重要判断は AC として書かれているため、これが承認内容のカバレッジを兼ねる）。
2. **No Placeholders scan**: `references/task-breakdown-steps.md` § Task Self-Review 6 のとおり（対象外もそこに書く）。
3. **Type consistency**: later task で使う型名・関数名・field 名が earlier task の定義と一致している。名称が途中で揺れたら、tasklist 作成中に統一する。
4. **Scope decomposition**: Subsystem Boundary Check に違反していない。deferred units が task 化されていない。
5. **Granularity**: 各 step が 1 action（2-5 分）で、各 task が 1 回の RED/GREEN/verification で閉じられる。

この Self-Review は subagent に委譲しない。task-breakdown 自身が実施し、通過後に `Next Action=gdd-test-driven-development` へ進む。

## Migration / Conversion Task AC 継承（必須）

`requirements.md` に `タスク種別: migration/conversion` が記載されている、または AC に `AC-F1` / `AC-F2` / `AC-F3` / `AC-F4`（migration AC family）が 1 つでも含まれている場合、以下を必須で実施する:

1. **全 task を AC-F* に紐付ける**: 分割後のいずれの task（実装 task / 検証 task を問わず）も、AC-F1〜F4 のいずれか 1 つ以上を `Covers AC:` 行に含める。純粋に構造変換 AC（AC-1 等）だけに紐付く task を許さない。構造変換 task であっても対応する原文保全観点（AC-F1）を併記する
2. **検証 task を独立して必ず含める**: 以下 2 つの task を `Pending Tasks` に必ず入れる:
   - **Content-diff verification task**（AC-F3 担当）: `git diff` で変換元ファイルの削除行から URL・注釈記号（`※N`）・Slack チャンネル（`#foo`）・人名（`@user`）・手順リンクを抽出し、変換後ファイルに grep で存在するかを検証する task。evidence として grep コマンドとその結果を `Verification` に記録する
   - **Rendering verification task**（AC-F4 担当）: 変換後の成果物を実レンダリング環境で確認する task。YAML Forms なら feature branch を push して GitHub UI で Issue 作成画面を開きスクリーンショットを取る、UI framework 変更ならブラウザで対象画面を開く、API 変更なら実リクエストを投げて response を確認する。evidence として URL / スクリーンショットパス / 確認コマンド結果を `Verification` に記録する
3. **task-breakdown の Self-Review**: `tasklist.md` 作成後、以下を self-check する。未達なら修正してから TDD に進む:
   - 全 task の `Covers AC:` に AC-F* が 1 つ以上記載されているか
   - Content-diff verification task が存在するか
   - Rendering verification task が存在するか
4. **Why:** requirements.md に AC-F* を書くだけでは、task 分割時に「構造変換を優先」した task に分解され、検証 task が暗黙扱いで落ちる。task-breakdown の段階で明示的に検証 task を独立させておかないと、implementation 後の completion で「まだ確認していない AC」が残ったまま done 判定される経路が残る

## Deploy Task Standard AC（コンテナデプロイを含むタスクの標準受入条件）

コンテナビルド・デプロイを含むタスクでは、以下の AC を標準追加する:

- **AC-deploy-smoke**: コンテナビルド後、ローカルで import smoke が通ること
  - `docker run --rm --entrypoint sh <image> -lc 'python -c "import app"'`
- **AC-deploy-env**: `update-agent-runtime` 後に環境変数が保持されていること
  - update 後すぐに smoke command（`/ping` 等）を実行し、想定モデル ID が返ることを確認
  - 想定外のモデル ID がログに出た場合は直ちに旧 URI で rollback
  - env var を保持する wrapper script を必ず使う
- **AC-deploy-e2e**: E2E テストで最終的な出力が出力先の描画制約を満たすこと
  - Slack: リンクがクリック可能か、mrkdwn が正しくレンダリングされるか

**Why:** ある一覧の投稿機能では 5 回のコンテナデプロイを要した。うち少なくとも 2 回は `update-agent-runtime` が環境変数をサイレントリセットする問題の確認・復旧に費やされた。AC として明示すれば確認漏れを防げる。

## Steps

詳細な手順は `references/task-breakdown-steps.md` を参照。概要:

1. 承認済み `requirements.md` と `design.md` を読む。人間が承認した重要判断は AC として書かれているため、全 AC を task 分割の正本にする
2. `tasklist.md` を作成・更新し、3 セクション（Current / Pending / Completed）を揃える
3. Agentic Worker Header に Goal / Architecture / Tech Stack / Approved Direction / Human Recheck Boundary を記録する。`Tech Stack` は human-check の `実装技術スタック` と一致させ、task-breakdown で新しい技術を発明しない
4. 各 task を AC ID に紐付け、`Depends on:` で依存関係を明示し、テンプレートに従い TDD サイクルの具体手順とコード片を書く。**Executable Step Contract** として、コード変更 step は `Actual code`、RED 検証 step は `Expected RED`、GREEN 検証 step は `Expected GREEN` を持ち、`No Placeholder Paraphrase`（「適切に」「同様に」「必要なら」等）で逃げない
5. 100 行超・5 ファイル超の task は分割する。ただし task 総数は原則 **8 task 以内**（機能単位で束ねる）。超える場合は Stage 分割を提案する — task 数が増えるほど gate 往復と artifact 肥大で 1 task あたりのコストが上がる
6. 依存グラフから並列実行可能なバッチを構成する（`references/task-breakdown-steps.md` § Parallel Execution の条件を参照）。条件を満たす場合は `## Execution Plan` に `Mode: parallel` とバッチ構成を記録する。並列にしないときは、`references/task-breakdown-steps.md` § Gate Batch の条件を満たす task をまとめ、`Mode: sequential` と `Gate Batch <N>: <task id の並び>` を記録する
7. Review Status の初期枠を作る（`gdd-implementation-reviewer` / `gdd-security-reviewer`）。`Implementation Reviewer Selection` / `Verification` の初期枠も揃える
9a. **Reviewer Lineage Patterns 参照（推奨）**: `docs/learned-patterns.md` の `Reviewer Lineage Patterns` セクションを読み、今回の task signature（変更ファイル種別 + scope keyword + 関連 AC）に一致する pattern があれば、その `次回適用ヒント` で推奨される reviewer を **最初から** `Implementation Reviewer Selection` の初期枠に含める。`次回適用ヒント=強い推奨`（3 回以上記録済み）の pattern は **必ず**初期枠に含める。事前追加 entry には **`added_by: lineage_pattern`** と **`source_pattern: <Pattern: 名>`** を必須記録する（`added_by` の allowed values と reviewer 種別の正式 key 名は `references/post-completion-learning.md` § `added_by` field の allowed values / Reviewer 種別の正式 key 名 を参照）。**Why**: build loop 中の事後追加（SMI / Impact Block 由来）を、次回 task では事前追加に進化させ、reviewer evidence の収集タイミングを早めて remediation cycle を削減する
8. active steering の `state.md` に `Next Action=gdd-test-driven-development` を記録する（tasklist.md のコメントではなく state.md への書き込みが必須）
9. 差し戻しが必要なら gate status を永続化する:
   - `planning_rework_required` → `Resume From=gdd-brainstorming` / `Next Action=gdd-brainstorming`
   - `human_recheck_required` → `Resume From=human-check-waiting` / `Next Action=human-check-waiting`
   - `design_detail_only` → `Resume From=gdd-design-gating` / `Next Action=gdd-design-gating`
10. 正常系では Self-Review（AC カバレッジ、No Placeholders、型一貫性、粒度、Agentic Worker Header、Executable Step Contract の整合性）を通してから TDD に進む
   - 承認済みの重要判断（AC）を既存 coverage inspection で閉じる場合は、対象の実装ファイル / 対象のテストファイル / テスト名または検証コマンド / 新規実装なしの理由 / 制限事項を Verification に残す

## Progress Rule

**逐次実行時:**

- `gdd-implementation-gating` 通過時:
  - `Current Task` の task を `Completed Tasks` へ移す
  - `Pending Tasks` の先頭 task があれば `Current Task` に昇格する
  - `Pending Tasks` が空なら `gdd-completion-check` に進む

**並列実行時:**

- バッチ内の全タスクが `gdd-implementation-gating` を通過したら:
  - バッチ内の全 task を `Completed Tasks` へ移す
  - 次バッチの全 task を `Current Task` に昇格する（並列実行時は複数タスクを `Current Task` に置ける）
  - 次バッチが無ければ `gdd-completion-check` に進む
- バッチ内の一部タスクが差し戻しになった場合:
  - 通過したタスクは `Completed Tasks` へ移す
  - 差し戻しタスクは `Current Task` に残し、修正後に再レビュー
  - 差し戻しタスクの解消後に次バッチに進む

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける
- このスキルは subagent として実行される。正常系は `Next Action=gdd-test-driven-development` を設定後、tasklist.md の内容サマリーを返して終了する。メインセッションが TDD phase へ継続する。
- `gdd-task-breakdown` の正常系を説明するときは、`tasklist.md` を更新し、`Current Task` / `Pending Tasks` / `Completed Tasks` を揃え、`Next Action=gdd-test-driven-development` を state.md に設定したことを答える。
- subagent は `gdd-stop` marker を使わない。state.md 更新と tasklist.md 完成後、結果サマリーを返す。差し戻しが必要な場合は state.md に差し戻し先の `Next Action` を設定して終了する。

## Rationalization Check（この skill 固有）

task 分割を飛ばしたくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。全体向けは `references/common-guardrails.md` § 合理化防止テーブル。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「1 タスクで全部やったほうが速い」 | 大きな 1 タスクは RED 証跡が曖昧になり reviewer が差し戻す。小さく切った方が直線で進む | [Planning Fallacy] 大きな task は楽観的見積もりが効きやすい。実測では分割した方が早く完走する |
| 「AC ID に紐付けなくても対応は自明」 | 自明なら紐付けは 1 行で済む。紐付けが無いと completion-check で対応が取れない | [Curse of Knowledge] 書いた本人には自明でも、completion-check / reviewer は紐付けが無いと対応関係を再構築できない |
| 「承認された判断は覚えているから AC 化不要」 | AC に書かれていない承認判断は task に運ばれず、既存 coverage inspection で静かに消える。承認内容を変えずに AC として追記してから分割する | [Premature Closure] 記憶に頼り、承認された制限事項や作り方の重要判断を消してしまう |
| 「Implementation Reviewer Selection は後で選ぶ」 | 初期枠を作らないと reviewer 選定根拠が散逸する。build 開始前に決める | [Bias for Action] 着手したい欲求が、選定の根拠記録より優先される |
| 「依存関係は実装中に判断」 | 依存は Execution Plan に明示。並列実行の機会を逃すと手戻りの原因になる | [Planning Fallacy] 依存判断を後回しにすると、実装中に sequential 走らせて時間損失する |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、planning 差し戻し route、scope の勝手な拡大）。以下はこの skill 固有のルール。

- Bounce Log: `references/bounce-log-schema.md` 準拠、閾値`>= 2`、escalate先`human_recheck_required`（ユーザー提示escalation。`gdd-systematic-debugging`不使用）
- AC ID に紐付かない task を作らない
- 承認済みの重要判断（AC）を既存 coverage inspection だけで閉じる場合、対象実装・対象テスト・検証コマンド・新規実装なしの理由・制限事項のいずれかが欠けていれば `existing-evidence` として扱わない
- migration/conversion タスクで content-diff verification task / rendering verification task を欠いた `tasklist.md` で TDD phase に進めない（上記 § Migration / Conversion Task AC 継承 を参照）
- `Implementation Reviewer Selection` の初期枠を作らずに build を始めない
- dedicated worktree の準備や再利用をこの phase に持ち込まない
- **Context Compaction Resilience**: task 分割の最終確認前に `requirements.md`（AC 一覧）と `design.md`（実装方針）をディスクから re-read する。task-breakdown は AC → task のマッピングが正確であることが前提であり、compaction で AC の詳細が劣化した状態で分割すると AC 漏れが発生する
