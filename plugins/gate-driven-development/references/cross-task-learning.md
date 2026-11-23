# Cross-Task Learning

> **所有**: steering 横断のパターン蓄積メカニズム
> **参照元**: `gdd-completion-check`（書き込み）、`gdd-brainstorming`（読み取り）、`gdd-subagent-driven-implementation`（読み取り）、`gdd-implementation-gating`（読み取り）

同一プロジェクトで複数の GDD タスクを実行するとき、過去の設計判断やコードパターンを次のタスクに活かす仕組み。

## Why

毎回の GDD run がゼロから始まると:
- 同じ設計議論（「cursor vs offset pagination」）を繰り返す
- 同じコードパターンを毎回発見し直す
- 過去に却下した代替案を再度検討してしまう

過去の判断を蓄積・参照することで、brainstorming の議論時間と reviewer 差し戻しを削減する。

## learned-patterns.md

完了した steering の成果から抽出したパターンを repo-level learned-patterns に蓄積する。既に GDD cross-task learning を採用している repo では `docs/learned-patterns.md`（worktree のルート直下の `docs/`。`docs/adr/` と同階層）を使う。branch-only の raw task steering `.steering/<task>/` とは明確に分離し、main へ通常に tracked される持続的ドキュメントとして扱う（`.steering/` 配下には置かない）。採用済み判定は、`origin/<default-branch>` で `docs/learned-patterns.md` が tracked、または `.gdd-config.md` / repo docs に learned-patterns の保存先が明記されていること。repo にこの規約が無い場合は、新規に `docs/learned-patterns.md` を作らず、`docs/adr/` または repo 既定の学習ファイルへ蒸留する。

### フォーマット

```markdown
# Learned Patterns

## Adopted Patterns
- **cursor-based pagination**: `src/api/` の GET エンドポイントは cursor-based で統一（2026-04-08, pagination-task）
- **Repository パターン**: DB アクセスは `src/repositories/` 経由（2026-04-05, user-crud-task）

## Rejected Alternatives
- **offset pagination**: 大量データでパフォーマンス劣化のため却下（2026-04-08, pagination-task）
- **直接 SQL**: Repository を経由せず SQL を書く案、テスト困難のため却下（2026-04-05, user-crud-task）

## Code Conventions Discovered
- エラーレスポンスは `{ error: string, code: string }` 形式（src/api/errors.ts で定義）
- テストは `*.test.ts` で co-locate（`__tests__/` ディレクトリは使わない）
```

### branch-only steering / Distill to ADR

standard 運用では raw task steering `.steering/<task>/` は branch-only steering として active branch / worktree 内でだけ使う。main には raw task `.steering/<task>/` を含めない。`learned-patterns.md` は raw task steering ではない。merge 後の cross-task learning は `docs/adr/` の Distill to ADR と repo-level learned-patterns だけを読む。raw task steering は次回 task の正本・検索対象にしない。

`docs/adr/` には、Approved Direction、採用した設計方針、却下した代替案、後続 task が守るべき制約だけを残す。tasklist 進捗、Handoff Summary、個別 Verification evidence は ADR に残さない。

### ルール

- **書き込みタイミング**: `gdd-completion-check` が `done` を出す直前に、`adr.md` と実装の diff から抽出する
- **書き込み内容**: 5 種類
  - Adopted Patterns: 採用した設計パターン・技術選択（パターン名 + 理由 + 日付 + steering 名）
  - Rejected Alternatives: 検討して却下した代替案（代替案名 + 却下理由 + 日付 + steering 名）
  - Code Conventions Discovered: 実装中に発見したプロジェクト固有の規約（規約 + 根拠ファイル）
  - Migration Patterns（migration / conversion task のみ）: AC-F\* の検証手段 + 失敗モード + 再発防止ヒント
  - **Reviewer Lineage Patterns**: SMI / Impact Block で build loop 中に追加された reviewer の履歴を task signature 単位で集約。次回同種 task の `gdd-task-breakdown` で事前追加できるようヒントを残す（format は `post-completion-learning.md` § Reviewer Lineage Patterns セクション format 参照）
- **読み取りタイミング**:
  - `gdd-brainstorming` Step 9（Problem Discovery）で参照。類似の過去判断があれば Options Exploration を短縮できる
  - `gdd-subagent-driven-implementation` Step 1a（Implementation Guidance）で参照。既存パターンに合わせて実装する。`gdd-implementation-gating` Step 5（Reviewer Calibration 参照）も `Rejected Alternatives` を参照する（`scripts/impl-gate-context.py` が同じ置き場を読む）
- **上書きルール**: 同じパターン名で新しい判断が出た場合は、古いエントリを更新する（日付と steering 名を新しくする）
- **削除**: パターンが不適切と判明した場合は削除してよい。canonical state ではないため gate 条件にしない
- **Reviewer Calibration 反映**: `gdd-completion-check` の Post-Completion Learning で、`tasklist.md` の `[Review Calibration]` エントリから `was_valid=false` が 2 回以上の checklist 項目を `Rejected Alternatives` に追記する。次回の `gdd-implementation-gating` が severity 調整に参照する（`references/inline-review-checklists.md` § Reviewer Calibration 参照）
- **Reviewer Lineage Patterns 反映**: `gdd-completion-check` の Post-Completion Learning で、`tasklist.md` の `Implementation Reviewer Selection` から `added_by: smi_block` / `added_by: impact_block` の entry を抽出し、`Reviewer Lineage Patterns` セクションに task signature 別に集約する。次回 `gdd-task-breakdown` Step 6a が初期枠選定に参照する（`references/post-completion-learning.md` § Reviewer Lineage Patterns セクション format 参照）
- **routing source にしない**: `learned-patterns.md` は参考情報であり、routing や gate の判定根拠にしない
