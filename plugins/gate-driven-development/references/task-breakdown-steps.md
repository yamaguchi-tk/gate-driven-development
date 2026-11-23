# Task Breakdown: Steps & Self-Review

> **所有**: `gdd-task-breakdown` の詳細手順
> **参照元**: `skills/gdd-task-breakdown/SKILL.md`

## Steps

1. 承認済み `requirements.md` と `gdd-design-gating` 通過済みの `design.md` を読む。`adr.md` があれば、既に確定した重要判断を task 分解の補助コンテキストとして確認する。`requirements.md` の受入条件（AC）を正本として読む。人間が承認した重要判断は AC として書かれているため、全 AC を task 分割の正本にする。standard または複数段階 quick (standard) では `Implementation Sequence Plan` も正本として読み、Stage ID / PR Boundary / Approval Scope / 生成物 / 後続が consume するもの / 人間に戻す条件 / Follow-up Tracking を tasklist に引き継ぐ。
   - **Health-First Task Ordering**: コードベース健全性調査の foundational finding は feature 前の足場タスクへ。`Non-Goal` / `no-action + 理由` 以外を後回しにしない。
2. `tasklist.md` が無ければ新規作成する。Hotfix Lane の steering で `worklog.md` に `## Origin Findings` があれば、その行を作った task の `Fix Findings:` に写す（写し先は `references/state-machine.md` § tasklist.md の canonical state）。既存の `tasklist.md` を作り直す・初期化するときは、`Route In Progress` の値を問わず（route は task-breakdown の前に `none` へ戻る）、`Completed Tasks` の `Reviewed by:` のあるタスクを消す前に、そのタスクを `Pending Tasks` へ移す書き込みを 1 回挟む（次の書き込みで消すための一時的な移動。1 回で消すと steering write guard が止める）。planning 差し戻し後に再到達した場合は次のとおりにする:
   - **`requirements_amendment`**: 差分 artifact update lane が未解消なので tasklist を確定しない。`requirements_amendment のまま tasklist を生成しない`。`gdd-requirements-gating` に戻し、`human_recheck_required` / `planning_rework_required` / `none` のいずれかへ解消してから task-breakdown を再開する。
   - **planning 差し戻し後の再到達**（`planning_rework_required` / `human_recheck_required` / `design_detail_only` のどれで戻っても。route は `none` に戻っている）: 既存の `tasklist.md` を stale tasklist とみなし、全セクション（`Current Task` / `Pending Tasks` / `Completed Tasks` / `Implementation Reviewer Selection` / `Review Status` / `Verification`）を初期化して再生成する。部分的に stale task を `pending` に戻す運用はしない（手順 2 の冒頭の一時的な移動は除く）。前回の作業成果は git 上に残るため、tasklist metadata のリセットでコードは失われない。再生成が終わるまで `Stage Continuity Source=requirements.md#Implementation-Sequence-Plan` に戻し、古い `tasklist.md#Execution-Plan` を source として参照しない。`Completion Rounds` / `Completion Baseline` / `Completion Reviewed Through` の行は引き継ぎ、task の `Fix Findings:` の行は作り直した task に写す（写し先は `references/state-machine.md` の同節）。並列 batch の例外、作り直しで途切れる数え、`design_detail_only` で残した commit が満たす AC の扱いは `references/state-machine.md` § planning 差し戻し後の tasklist.md リセットに従う。
3. tasklist 冒頭に **Agentic Worker Header** を作る。subagent は前後文脈を持たずに task 単位で実装するため、最初に全体方針を 1 画面で読めるようにする。

   ```markdown
   # <task title> Tasklist

   > **For agentic workers:** Follow this tasklist together with `requirements.md` / `design.md`. Do not change AC, Approved Direction, or Human Recheck Boundary from a leaf task.

   **Goal:** <この tasklist 全体で実現することを 1 文>
   **Architecture:** <設計方針・主要コンポーネント・データフローを 2-3 文>
   **Tech Stack:** <language / runtime、framework / library、test tooling、access method、credential backend の採用内容>
   **Approved Direction:** <human check で承認された自走範囲・自走上限>
   **Stage Continuity Source:** <requirements.md#Implementation-Sequence-Plan、requirements.md#Implementation-Sequence-Plan (N/A - single-stage express)、または tasklist.md#Execution-Plan>
   **Human Recheck Boundary:** <AC / scope / policy / ownership / security boundary / prompt-output contract が変わる場合は human-check-waiting に戻す、など>

   ---
   ```

   - `Tech Stack` は human-check の `実装技術スタック` と一致させる。task-breakdown で新しい技術を発明しない
   - `Stage Continuity Source` は、tasklist がどの `Implementation Sequence Plan` から生成されたかを示す。resume / compact / human_recheck_required 後に段階連続性を復元するための参照であり、routing source にはしない
   - quick (express) で `Implementation Sequence Plan` が `N/A - single-stage express` の場合も、`Stage Continuity Source` は空欄にせず `requirements.md#Implementation-Sequence-Plan (N/A - single-stage express)` と書く
   - `Human Recheck Boundary` は subagent が「この変更は自分で進めてよいか」を判断するための境界であり、曖昧な場合は `gdd-systematic-debugging` に戻す
4. `Current Task` / `Pending Tasks` / `Completed Tasks` の 3 セクションを canonical format として揃える。
5. 各 task に `T-1`, `T-2`, ... の連番 Task ID を付与し、`requirements.md` の AC ID と紐付けて次のテンプレートで書く。

   **見出しの正準形は `### Task: <ID> <name>`**。連番は見出しではなく Task ID 側で表現する。`### Task 1: <name>` のように見出しへ番号を埋め込む形は使わない。
   PreToolUse の plan-reread hook はこの節から task 名を読んで build 中の context 再注入を行うため、
   形式が崩れると **注入が silent に止まる**（`references/state-field-tiers.md` § Tier 1 の
   「読み手だけ厳格にしない」方針に従い hook 側も番号付き・リスト形式を受理するが、
   新規作成では正準形に揃える）。

   ```markdown
   ### Task: T-1 <name>
   - AC: AC-1, AC-3 (primary: T-1)
   - Stage: S-1
   - PR Boundary: current-pr | follow-up-pr | post-merge-verification
   - Approval Scope: このPRで実施許可 | 後続PRの方針のみ承認 | 後続PR着手前に再承認 | 事前回答で後続PRも実施許可
   - Depends on: none
   - Stage Output Contract:
     - Produces: <この task が作る schema / API / policy / fixture / integration contract / terminal artifact 等。無ければ none + 理由>
     - Consumes: <前 task / 前 Stage から使う生成物。無ければ none>
   - Files: src/api/handler.ts, src/api/handler.test.ts
   - Estimated changes: ~30 lines
   - Complexity: standard | complex（決め方は `references/fixed-models.md` の `implementation` tier）
   - Planned RED / E2E: <AC の検証方法から導いた RED test / E2E smoke / executable verification>
   - Verification: test run / manual check

   #### Steps
   1. Write failing test
      - File: `tests/api/handler.test.ts`
      - Code: (テストコード片)
      - Run: `npm test -- tests/api/handler.test.ts`
      - Expected: FAIL — "handler not defined"
   2. Implement
      - File: `src/api/handler.ts`
      - Code: (実装コード片)
      - Run: `npm test -- tests/api/handler.test.ts`
      - Expected: PASS
   ```
   ```
   #### Attempts
   （実装中に自動記録される。タスク作成時は空）
   ```
   - `Attempts`（試行記録）: 実装中にエラーや失敗したアプローチを記録するセクション。タスク作成時は空で、実装フェーズで自動的に追記される。フック経由でコンテキストに再注入されるため、同じミスの繰り返しを防ぐ。記録形式: `- [試行N] <やったこと>: <結果>（<次のアプローチ>）`
     - **AC Owner Migration**: 実装中に AC の primary owner を別 task に移す必要が生じた場合（例: T-1 で実装した AC-2 の検証が T-3 の方が適切と判明した等）、Attempts セクションに以下の形式で記録する:
       ```
       - [AC Owner Migration] AC-2: T-1 → T-3, reason: T-3 のスコープに含まれる API 変更と一体で検証すべきため
       ```
       移行先の task の `AC:` 行に `(primary: T-3)` を付け替え、移行元の `(primary: T-1)` を削除する。移行は同一 diff 内で行い、primary が 0 個または 2 個以上になる状態を作らない
   - `AC`: 対応する受入条件 ID（verification failure 時に再オープンできるよう残す）。1 task に複数 AC を載せてよい（例: `AC-1, AC-3`）。同じ AC が複数 task に現れる場合は `(primary: T-n)` で primary owner を明示する。`gdd-completion-check` 差し戻し時は primary owner の Task ID で reopen 先を決定する
   - `Stage`: `Implementation Sequence Plan` の Stage ID。単一段階 express で plan が `N/A` の場合は `single-stage`
   - `PR Boundary`: `Implementation Sequence Plan` の PR Boundary を写す。`current-pr` 以外の task は、明示承認がない限り `Current Task` に置かず `Planned Follow-up Stage Lane` / 後続 steering seed へ送る
   - `Approval Scope`: human-check で承認された Stage 単位の実施許可。`follow-up-pr` / `post-merge-verification` では、原則 `後続PRの方針のみ承認` または `後続PR着手前に再承認` とし（本人の事前回答の対象の Stage は `事前回答で後続PRも実施許可`。`references/human-check-template.md` § 事前回答 の 4）、この PR の task として実装しない
   - `Depends on`: このタスクが開始できる前に完了している必要があるタスクの ID リスト。依存がなければ `none`。依存関係は並列実行の判定に使う
   - **Stage Output Contract**: `Produces` / `Consumes` で task 間・Stage 間の受け渡しを明示する。`Depends on` だけで済ませない。後続 task が前 task の型定義・API・fixture・policy・schema・外部証跡を使う場合、前 task の `Produces` と後 task の `Consumes` が対応していなければならない
     - quick (express) / single-stage の場合、`Produces` は `terminal artifact: <変更後のファイル・文言・CLI 出力など>` と書く。`後続が依存する生成物` は human-check に出さない（段階が 1 つなら Brief を書かない。`human-check-template.md` 必須ルール 19）が、task 自体が完了時に生成・変更するものは `terminal artifact` として残す
     - `Produces: none` は、task が検証・削除・調査のみで変更後 artifact を持たない場合に限る。README typo 修正のように変更後ファイルが成果物になる場合は `none` にしない
   - `Files`: 変更対象ファイルのパス一覧（正確なパス）。事前に特定することで粒度が可視化される
   - `Estimated changes`: 概算の変更行数。100 行を超える場合は分割を検討する。ただし **task 総数 8 以内を優先**する（機能単位で束ね、行数分割は塊内の Steps で満たす）。**両方（task 総数 8 以内 / 100 行・5 ファイル超での分割）を同時に満たせない見積もりは、task 分割ではなく Stage 分割の signal として `Implementation Sequence Plan` に返す**
   - `Planned RED / E2E`: AC 本文が要求する検証水準（E2E 必須・外部証跡必須の明記があればそれ）から導く。AC が Yes/No で観測できない曖昧なままなら task を確定せず requirements / human check に戻す
   - `Verification`: RED test / manual check / script 等、この task の完了をどう確認するか
   - `Steps`: TDD サイクルに沿った具体的な手順。コード変更を含むステップには必ずコード片を含める。検証コマンドには期待出力を添える
   - **Executable Step Contract**: 各 task の Steps は、Superpowers plan と同じく実行者が迷わない粒度にする。コード変更 step には `Actual code`、RED 検証 step には `Expected RED`、GREEN 検証 step には `Expected GREEN` を書く。`No Placeholder Paraphrase` として、「適切に」「同様に」「必要なら」のような実装者判断へ逃げる言い換えは禁止する
6. 大きすぎる task（`Estimated changes` が 100 行超、または `Files` が 5 ファイル超）は小さな task か小 batch に分割する。優先順位の判断基準は本ファイル § Steps 手順 5 の `Estimated changes` 説明を参照。
7. 実行単位となる task を 1 つ選び、`Current Task` に置く。残りは `Pending Tasks` に置く。
8. `Review Status` は reviewer ごとの初期枠を作る。
   - `gdd-implementation-reviewer`
   - `gdd-security-reviewer`
   - 初期値はすべて `pending | evidence: none | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
9. `Implementation Reviewer Selection` の初期枠を作る。
   - `gdd-implementation-reviewer`
   - `gdd-security-reviewer`
   - 初期値はすべて `pending | reason: none`
   - `selection_change_reason: none | updated_by: gdd-task-breakdown | updated_at: <timestamp>`

9a. **Reviewer Lineage Patterns 参照（推奨）**: `docs/learned-patterns.md` の `Reviewer Lineage Patterns` セクションを読み、今回の task signature（変更ファイル種別 + scope keyword + 関連 AC）に一致する pattern があれば、その `次回適用ヒント` で推奨される reviewer を **最初から** Step 9 で作成した `Implementation Reviewer Selection` の初期枠で `selected` に含める。`次回適用ヒント=強い推奨`（3 回以上記録済み）の pattern は **必ず**初期枠に含める（記録形式と運用は `references/post-completion-learning.md` § Reviewer Lineage Patterns セクション format 参照）。**Why**: build loop 中の事後追加（SMI / Impact Block 由来）を、次回 task では事前追加に進化させ、reviewer evidence の収集タイミングを早めて remediation cycle を削減する
10. `Verification` の初期枠を揃える。各 accepted AC に対し、AC 本文が要求する検証水準と compatible な verification 行が tasklist に作れることを確認する。E2E 必須 / 外部証跡必須の AC は final smoke / external evidence 行を明示し、lower-level RED で先に固定する境界も task に残す。
    - **Existing coverage inspection の証拠条件**: 承認済みの重要判断（AC）を `Existing coverage inspection` で閉じる場合は、task の Verification に以下をすべて書く。1 つでも欠ける場合は `existing-evidence` として扱わず、`new-red-green` または `code-diff` task に戻す。
      - 対象の実装ファイル
      - 対象のテストファイル
      - テスト名または検証コマンド
      - なぜ新規実装なしで十分なのか
      - その判断により OK しても今回は対象外になることがある場合は、その制限事項
11. 初期 `Next Action=gdd-test-driven-development` を設定する。
11a. **Next Exact Step / Current Step Verification**: tasklist には `Next Exact Step` を持たせる。これは先頭の未完了 step を 1 つだけ示す field で、実装者が今何をするかを迷わないためのもの。各 step には `Step Verification` を持たせ、Current Step Verification として実行コマンド・期待結果・証跡保存先を明示する。Execution Status は `pending` / `in_progress` / `verifying` / `completed` / `blocked` のいずれかにする。
12. 計画そのものの組み直しが必要なら、その場で tasklist を確定しない。
13. `planning_rework_required` の場合は次を行う。

- `Requirements Review Status=pending | evidence: <planning-reopen-id> | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Design Review Status=pending | evidence: <planning-reopen-id> | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Human Check Status=pending | evidence: none | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Resume From=gdd-brainstorming`
- `Next Action=gdd-brainstorming`
- 古い `waiver_reason` を残さない

14. 狭い要件・実装方針変更だけで人間判断が必要な場合は、`human_recheck_required` として次を行う。

- `Requirements Review Status=approved | evidence: <requirements-review-id> | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Design Review Status=pending | evidence: <human-recheck-id> | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Human Check Status=pending | evidence: none | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Resume From=human-check-waiting`
- `Next Action=human-check-waiting`
- 古い `waiver_reason` を残さない

15. 要件は変わらないが detailed design の修正が必要なら、`design_detail_only` として次を行う。

- `Requirements Review Status=approved | evidence: <requirements-review-id> | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Design Review Status=changes_requested | evidence: <design-reopen-id> | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Human Check Status=approved | evidence: <元の evidence> | updated_by: gdd-task-breakdown | updated_at: <timestamp>`
- `Resume From=gdd-design-gating`
- `Next Action=gdd-design-gating`
- 古い `waiver_reason` を残さない

16. 要件も detailed design も変わらない場合だけ Self-Review を行ってから `gdd-test-driven-development` に進む。

## Fresh Executor Quality Standard

superpowers `writing-plans` の「fresh executor がそのまま実行できる」品質基準を GDD tasklist に吸収する。各 task は **context-zero executor**（会話履歴を読んでいない実行者）が読んでも迷わない粒度にする。

必須:

- File は absolute or repo-relative path で書く
- Run は exact command で書く
- Expected は expected result として pass / fail / 出力文字列 / exit code のどれかを明示する
- Step は 1 action に分ける
- 「既存に合わせて」「適切に」「必要なら」だけで実装者判断に逃げない

この基準を満たさない tasklist は、TDD / implementation に進めない。task-breakdown 自身が Self-Review で直す。

## Carry Forward（subagent 境界で次段に残す実測値）

> **所有**: `Carry Forward:` の判定基準・保存先・分量の正本
> **参照元**: `context-budget.md` § Carry Forward（Phase Context Manifest の carve-out）、
> `gdd-task-breakdown` SKILL.md（task entry schema）、
> `gdd-subagent-driven-implementation` SKILL.md（Step 12b で記入 / prompt contract で供給）

subagent の実装文脈は task 境界で破棄される。これは意図した設計で、「何が消えるか制御できない compaction」より優れている。ただし**破棄しないもの**が Handoff Summary としか定義されておらず、次段が必要とする実測値がどこにも残らなかった。

### 何を書くか

**次段がそれを知らないとブロックされる、または誤った前提で進んでしまうもの**だけ。
「あると便利」は書かない。

| 種別 | 例 |
|---|---|
| 確定した実測値 | 実装で確定した関数・API シグネチャ、戻り値の形 |
| 名前・場所 | 定数名、環境変数名、生成物のパス（次段が参照するもの） |
| 実行時に判明した制約 | E2E で判明した順序依存・タイムアウト・権限・レート制限 |
| **未解決の申し送り** | 次段の着手前に解消が要る前提、暫定対処のまま残した箇所、踏んだ罠 |

4 番目が「支障なく引き継ぐ」ことに最も効く。事実の共有よりも**次段が詰まる地雷の共有**を優先する。

### どこに書くか（`findings.md` を使わない理由）

保存先は `tasklist.md` の task entry。controller が唯一の writer であり、
`gdd-subagent-driven-implementation` Step 12b（`Completed Tasks` へ移す前）という
**既に必須の手順**の中で書かれる。規律ではなく手順に載せるのが要点。

`findings.md` は使わない。調べると実際に書かれていることはまれで、
同じく「指示するだけ」だった `Last Handoff Summary` がほとんど書かれなかったのと同じ失敗を繰り返すため。

### 分量

1 task あたり 5 行程度を目安とし、参照するのは直近 1〜2 task 分に限る。
ただしこれは書きすぎを検知するための目安であって、**抑制の根拠にしない**。
次段がブロックされる情報は目安を超えても省略しない — 削るのは詳細であって、地雷ではない。
該当が無ければ `なし` と書く（空欄にしない。未記入と「無い」を区別する）。

### Canonical Task Fields

新規 tasklist では `AC:` を canonical field として使う。既存 artifact に `Covers AC:` が残っている場合は legacy alias として読んでよいが、新規追記・修正時は `AC:` に正規化する。fresh executor に渡す task で `AC:` と `Covers AC:` を混在させない。

## タスク粒度ガイドライン

各タスクは **1 つの論理的変更** に対応し、以下の基準に収める:

| 指標 | 目安 | 超えたら分割 |
|------|------|------------|
| 変更行数 | 30〜80 行 | 100 行超 |
| 変更ファイル数 | 1〜3 ファイル | 5 ファイル超 |
| RED テスト数 | 1 つ | 2 つ以上の独立したテストが必要 |

**判定の原則**: 1 つのタスクを説明するのに「〜と〜」（and）が必要なら、分割を検討する。

### アプリケーション開発の粒度例

| タスク種別 | 良い粒度（1 タスク） | 大きすぎる（分割が必要） |
|-----------|-------------------|----------------------|
| API エンドポイント | `GET /api/users` の handler + test | CRUD 全体を 1 タスク |
| React コンポーネント | `UserCard` コンポーネント + Storybook | ページ全体を 1 タスク |
| DB マイグレーション | カラム追加のマイグレーションファイル | マイグレーション + モデル変更 + API 変更 |
| バリデーション | 入力バリデーション + エラーメッセージ | バリデーション + UI + API 全部 |
| バグ修正 | 原因の修正 + 再発防止テスト | 複数の独立したバグを 1 タスク |

### インフラ開発の粒度例

| タスク種別 | 良い粒度（1 タスク） | 大きすぎる（分割が必要） |
|-----------|-------------------|----------------------|
| Terraform | 1 リソースの定義 + plan 検証 | モジュール全体を 1 タスク |
| CI/CD | 1 ジョブの追加 + テスト | パイプライン全体の構築 |
| 監視 | 1 アラーム定義 + threshold テスト | 監視体系全体の設計+実装 |

### 分割パターン

大きなタスクを分割する際の典型パターン:

1. **レイヤー分割**: DB → モデル → サービス → コントローラー → UI
2. **CRUD 分割**: Create → Read → Update → Delete を別タスクに
3. **正常系/異常系分割**: 正常パスの実装 → エラーハンドリング
4. **依存順分割**: 共通部品 → 利用側の実装

## Parallel Execution（並列実行）

タスク間の依存関係を明示し、独立タスクを並列で実行することで実装時間を短縮する。

`Execution Plan` は `requirements.md` の `Implementation Sequence Plan` から生成する。task-breakdown は Stage を新しく発明せず、必要に応じて Stage を task に分割するだけにする。Stage の生成物や consume 関係を変える必要が出た場合は tasklist を確定せず、`human_recheck_required` または `planning_rework_required` に戻す。

### 依存関係の記述ルール

- 各タスクに `Depends on:` フィールドを記述する
- 依存がなければ `none` と書く
- 依存がある場合は Task ID をカンマ区切りで列挙する（例: `Depends on: T-1, T-2`）
- 循環依存は許可しない（検出した場合は分割を再検討する）

### 依存関係の判定基準

| 依存あり（逐次） | 依存なし（並列可能） |
|----------------|-------------------|
| 後続タスクが前タスクの型定義・関数・API を使う | 異なるモジュール・ファイルを変更する |
| 後続タスクのテストが前タスクの実装成果物を import する | 同じモジュールでも変更箇所が独立している |
| DB マイグレーション → マイグレーション後のデータ操作 | UI コンポーネント A と UI コンポーネント B |
| 共通ユーティリティ作成 → 利用側の実装 | バックエンド API と関連しないフロントエンド変更 |

### 並列バッチの構成

依存グラフから並列実行可能なバッチを構成する:

```
Batch 1: T-1, T-2（依存なし → 並列実行）
    ↓ 完了待ち
Batch 2: T-3（Depends on: T-1）, T-4（Depends on: T-2）→ 並列実行
    ↓ 完了待ち
Batch 3: T-5（Depends on: T-3, T-4）
```

- 同一バッチ内のタスクは **変更ファイルが重ならない** ことが前提
- ファイルが重なる場合は逐次に降格する（merge conflict 回避）
- バッチ内の全タスクが impl-gate を通過したら次バッチに進む

### 並列実行の条件（standard タスクのみ）

並列実行は、タスク数が 3 以上・依存グラフから 2 タスク以上の並列バッチが構成できる・並列バッチ内のタスクの変更ファイルに重複がない、をすべて満たす場合に有効化する。quick (express) / quick (standard) では逐次のまま（タスクが少ないため並列化の効果が薄い）。満たさない場合は従来通り逐次実行する。

### tasklist.md への記録

並列実行が有効な場合、tasklist.md に `## Execution Plan` セクションを追加する:

```markdown
## Execution Plan
- Mode: parallel
- Source: requirements.md#Implementation-Sequence-Plan
- Planned Follow-up Stage Lane: requirements.md#Planned-Follow-up-Stage-Lane
- Batch 1: T-1, T-2 (independent)
- Batch 2: T-3 (after T-1), T-4 (after T-2)
- Batch 3: T-5 (after T-3, T-4)
```

逐次実行の場合は `Mode: sequential` と記録する。

### Gate Batch（逐次実行の gate のまとめ）

`Mode: sequential` で、standard（`quick` 系ではまとめない）・task 数が 3 以上・依存順に連続する（間に別の task を挟まない）・最大 3 個・各 task が自分の `Planned RED / E2E` を持つ（他の task の検証に頼らない）、をすべて満たす task は `Gate Batch` にまとめてよい（`Mode: parallel` とは併用しない）。`## Execution Plan` に `- Gate Batch 1: T-1, T-2, T-3` の形で記録する。まとめた task は 1 つずつ RED → GREEN → REFACTOR を終え、最後の task が終わったところで `gdd-implementation-gating` を 1 回だけ実行する（費用の大きい gate を task の数だけ回さないため。2026-09-24〜29 に調べると、task の多い steering は impl-gating を task の数より多く回していた）。impl-gating は batch を 1 つの gate 単位として判定する（どの出口から `changes_requested` を返すときも全 task を差し戻し、`Gate Rounds` を足すときは全 task に同じだけ足す。finding には対象の task id を付け、remediation はその task だけを直す。対象の task を決められない finding と、`Fix Attempts` などを task ごとに数えることは `references/state-machine.md` § Remediation Loop Safety）。実装中の task は `Current Task` の先頭に置く（文脈を注入する hook は task 名を先頭の task から読む。ほかの field の読み方は hook ごとに違う）。条件を満たさない task は従来どおり 1 task ごとに gate する。

### Judgment Change（impl-gating の review を外すか）

task ごとに `- Judgment Change: yes | no` を書く。`yes` は、その task の変更が次のどれかを変えるとき：block / allow の判定（guard・hook）、認可・IAM・権限の付与（トークン・認証情報の扱いを含む）、Ready・承認の判定、費用の上限で止める判定、入力検証（untrusted な入力の扱いを含む）、fail-open の既定。これらの判定のコードの書き換え（挙動を変えない refactor を含む）、runtime が毎回読んで止めさせる手順文、受理する値・固定した入力の変更も `yes`。`worklog.md` の `AI が閉じた:`・`表示した文面を採用:` の行が名指しした AC を実装する task も `yes`（impl-gating で名指しの確かめを外さないため。`references/requirements-gating-steps.md` § AI が閉じる blocking）。どれにも当たらない（テストだけ・文書だけ・確認だけなど）ときだけ `no`、判定できないときは `yes` にする。
- 宣言に数えるのは、1 つの task に `- Judgment Change: no` ちょうど 1 本だけで、装飾・末尾の文・別の値・別の書き方の行・2 本目の行があれば `yes` と同じ。前の gate が差し戻した commit を残す・流用する作り直しでは、その差分を担う task に `no` を書かない。`no` の task には、変えるファイルを Files（1 行の `- Files:` か `#### Files` の `- Create/Modify/Test/Delete:`。パスの後ろの括弧の注記は読まない）にちょうど 1 つ書く。欄が無い task（refactor-planning・completion-check・systematic-debugging が足した task を含む）も `yes` と同じ。`no` を書くのは task-breakdown だけで、ほかは `yes` に上げることだけができる
- impl-gating は、Task Size が `standard` か `quick (standard)` で（Express とその昇格は外さない）、`Current Task` の task が 1 つだけで（Gate Batch・並列の batch は外さない。起点と State Machine Impact block の単位が gate 単位と合わないため。並列の batch は Execution Plan で見分け、節が無いか、`## Execution Plan` の Mode の行がちょうど 1 本で `- Mode: sequential`・`Mode: sequential`・`- sequential` のどれかで、番号つきの Gate Batch の行が無いときだけ逐次と読む）その task が `no` で、`Gate Rounds` の行が無く、gate 単位の差分（`state.md` の `Impl Gate Base` か、無ければ default branch との merge-base からの変更ファイル。未 commit・untracked を含み、この steering を除く）がその task の Files に収まり、Files が空でなければ宣言したファイルが差分に出ていて、`Completed Tasks` の task の数が `state.md` の `Impl Gate Completed`（Step 11 が起点と同じ時点で書く。起点も欄も無ければ 0）と同じときだけ review を外す。`Current Task` が最初の task より前に行を持つ・1 本だけの欄が重なるなど、読めない形のときも外さない（`skills/gdd-implementation-gating/SKILL.md` Step 1e。判定は `scripts/impl-gate-context.py` の `impl-gate-review:` 行）。外した task は `Reviewed by: none (Judgment Change: no)` で完了し、completion-check Step 2a はこの行を宣言のある task でだけ受け付け、completion-reviewer が線に触れていないかを見る。Why: GDD を使う別の repo の正式 GDD のタスクを調べると（2026-10-20）、impl の実害はすべて線の中の batch で起き、線の外の単位では 1 件も起きていなかった。外すと impl-gating の Round が大きく減る

## Step Granularity（task 内の 1 step のサイズ）

各 task の `#### Steps` に並ぶ 1 step は **1 つの action（おおむね 2-5 分で完了）** になるように書く。これは task 全体ではなく、task 内部の step の粒度。

- ✅ 「failing test を書く」 — 1 step
- ✅ 「テストを実行して fail することを確認する」 — 1 step
- ✅ 「test を pass させる最小実装を書く」 — 1 step
- ✅ 「テストを実行して pass することを確認する」 — 1 step
- ✅ 「commit する」 — 1 step
- ❌ 「実装してテストする」 — 2 action を 1 step に詰めない

step レベルで細かく切る理由: subagent が 1 step ずつ進めれば、途中で詰まった場合にどこで詰まったかが明確になる。「実装してテストする」のような複合 step は failure point を隠す。

## WHERE 特定の探索手段（Serena 優先 / fail-open）

`Files:` フィールドの実ファイルパス + 行番号 + シンボルの定義位置・呼び出し元を特定する際、対象が LSP 対応言語（Python/TS/Go 等）かつ Serena プロジェクトが有効なら、grep/sed の総当たりの前に Serena を第一手にする。使い分けは `get_symbols_overview`（ファイル構造把握）→ `find_symbol`（定義位置・行番号の特定）→ `find_referencing_symbols`（呼び出し元の特定）の順。

**fail-open フォールバック（2 トリガー）**:
- (i) LSP 非対応（Markdown/shell 中心）または Serena プロジェクト無効環境では、最初から grep/sed にフォールバックする。
- (ii) Serena のツールが未インデックス / ツール不在でエラーまたは空結果を返した場合は、即座に grep/sed へ切り替える（Serena 呼び出し失敗で停止せず回復する）。

**WHERE 持ち越し点検**: 実ファイルパス + 行番号が前段（brainstorming の調査記録 / `Files` / human check の Decision Packet の WHERE）から持ち越せているかを点検する。task-breakdown で WHERE の再探索が発生している場合は、前段の WHERE 引き継ぎが機能していないプロセス穴の兆候として扱う（Decision Packet 本体は変更しない）。

## No Placeholders パターン（禁止表現の具体例）

> **正本**: `references/common-guardrails.md` § プレースホルダー禁止。ここでは Self-Review 用の具体パターンを補足する。

## Plan Placeholder Failure Gate

tasklist 確定前に、以下の placeholder が残っていないか確認する。残っている場合は tasklist を確定しない。対象外は正本（`references/common-guardrails.md` § プレースホルダー禁止）のとおり。

- TBD
- TODO
- implement later
- Similar to Task
- Add appropriate error handling
- Write tests for the above
- 空の `Code:`

placeholder は subagent に解釈を押し付けるため、実装前に具体化する。

以下のパターンが task に残っている時点で、plan は未完成とみなす。Self-Review でこれらを grep して一掃する。

### 言い訳パターン
- `TBD` / `TODO` / `後で実装` / `後で決める` / `詳細は後で`
- 「適切なエラー処理を追加」（どの error をどう処理するか未定義）
- 「必要なバリデーションを追加」（何を validate するか未定義）
- 「エッジケースをハンドリング」（どの edge case か未定義）

### コピペ回避パターン
- 「Task N と同様」（subagent は他 task を読まない前提。該当コード片を重複して書く）
- 「前のタスクの handler を真似る」（handler の shape を具体コードで示す）

### 抽象化逃避パターン
- 「テストを書く」（テストコード片がない）
- 「関数を実装」（実装コード片がない）
- コード変更を含む step に code block が無い（`Code:` フィールドが空 or 省略）

### 未定義参照
- 定義していない型・関数・メソッドへの参照（`SomeType` / `processX()` を使う step があるのに、どの task でも定義されていない）

## Task Self-Review

`tasklist.md` を確定する前に、以下のチェックを自分で行う（reviewer への dispatch ではない）。問題を見つけたらその場で修正する。再レビューは不要。

1. **設計決定カバレッジ**: `design.md` の設計決定（アーキテクチャ方針・モデル選択・実装戦略・コンポーネント変更・設定値）を列挙し、それぞれに対応するタスクが存在するかを確認する。設計決定が tasklist に落ちていない場合はタスクを追加する。各タスクの `Files:` フィールドに正確なファイルパスが書かれているか、変更内容が「何をどう変えるか」のレベルで具体化されているかも同時に確認する
2. **AC カバレッジ**: `requirements.md` の各 AC ID に対応するタスクがあるか。抜けがあればタスクを追加する
3. **Testability カバレッジ**: 各 accepted AC の検証水準が task の `Planned RED / E2E` と `Verification` に写っているか。AC 本文より弱い検証にすり替わっていないか。Yes/No で観測できない曖昧な AC が残っていたら tasklist を確定せず requirements / human check に戻す
4. **承認判断カバレッジ**: 承認済みの重要判断（AC）を `Existing coverage inspection` で閉じる場合、対象の実装ファイル / 対象のテストファイル / テスト名または検証コマンド / 新規実装なしの理由 / 制限事項が Verification にあるか
5. **AC primary owner の一意性**: 各 AC ID の primary owner (`(primary: T-n)`) が一意か。同じ AC が複数 task に出る場合は必ず 1 つだけ primary を指定する。実装中に移行が発生した場合は `[AC Owner Migration]` 記録が Attempts にあり、移行元と移行先で primary が 1 つだけになっているか確認する
6. **No Placeholders scan**: 上記「No Placeholders パターン」を全 task の Steps に対して grep する。`TBD` / `TODO` / `後で` / `適切に` / `Task N と同様` / 空の `Code:` / 未定義型参照がいずれも残っていないこと。1 箇所でも該当したら具体化して書き直す。対象外（語に触れるだけの記録など）は正本 § プレースホルダー禁止のとおりで、`Actual code` の `// TODO` は対象
7. **Step Granularity**: 各 task の Steps が 1 action = 1 step（2-5 分で完了）の粒度で切れているか。「実装してテストする」のような複合 step を分解する
7a. **Executable Step Contract**: 各 task の Steps に `Actual code` / `Expected RED` / `Expected GREEN` が必要な箇所で具体化されているか。`No Placeholder Paraphrase` として「適切に」「同様に」「必要なら」「既存に合わせて」だけで済ませていないか
8. **型・関数の一貫性**: 後続タスクで使う型名・関数名・プロパティ名が、定義タスクと一致しているか。例: Task 3 で `clearLayers()` を呼び、Task 7 で `clearFullLayers()` を定義 → 不一致。後続で使う名前と定義側の名前を揃える
9. **Task 粒度チェック**: 上記「タスク粒度ガイドライン」の基準に照らして、100 行超のタスクや 5 ファイル超のタスクが残っていないか。1 つの RED テストで検証できない場合は分割する。優先順位の判断基準は § Steps 手順 5 を参照
10. **依存関係チェック**: 全タスクに `Depends on:` フィールドがあるか。循環依存がないか。依存先が存在するタスク ID を指しているか
11. **Stage Output Contract チェック**: `Implementation Sequence Plan` がある場合、全タスクに `Stage` / `Stage Output Contract` / `Produces` / `Consumes` があるか。後続 task の `Consumes` が、依存先 task または前 Stage の `Produces` に対応しているか。`Depends on だけで済ませない`
12. **並列バッチ検証**（`Execution Plan: parallel` の場合）: 同一バッチ内のタスクの変更ファイル（`Files:` フィールド）に重複がないか。重複がある場合は逐次に降格するか、バッチ構成を変更する
13. **Attempts・Complexity**: 全タスクに `#### Attempts` セクションが（空の状態で）存在し、`Complexity:` が `standard` か `complex` のどちらか 1 つか
14. **Agentic Worker Header**: Goal / Architecture / Tech Stack / Approved Direction / Stage Continuity Source / Human Recheck Boundary が冒頭にあり、human-check の `実装技術スタック` と矛盾していないか
