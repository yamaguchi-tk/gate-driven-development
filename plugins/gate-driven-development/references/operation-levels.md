# 運用レベル（Operation Levels）

> **所有**: チーム・リポジトリ単位の運用レベル定義
> **上位正本**: `self-contained-contract.md`（fail-closed 条件）
> **参照元**: `commands/gdd-dev.md`、`gdd-brainstorming`、`references/task-sizing.md`

GDD の工程をチームの成熟度やリポジトリの特性に合わせて調整するための運用レベル。

## なぜ運用レベルがあるか

GDD は正しさを重視するが、すべてのチームに同じ厳密さを求めると「重いから使わない」が起きやすい。導入初期は軽く、定着後に厳格化できる段階を用意することで、チーム展開の障壁を下げる。

## 3つの運用レベル

| レベル | 想定場面 | 一言 |
|--------|---------|------|
| **light** | 導入初期、個人利用、小規模チーム | まず使ってみる。最小限のゲート |
| **standard** | 通常のチーム開発 | バランス重視。推奨デフォルト |
| **strict** | セキュリティ重要、監査要件あり、大規模チーム | フルゲート。省略なし |

## レベル別の違い

| 項目 | light | standard | strict |
|------|-------|----------|--------|
| **タスクサイズ判定** | 自動（変更可） | 自動（変更可） | 自動（降格不可） |
| **requirements gate** | quick 以上で実施 | quick 以上で実施 | quick 以上で実施 |
| **human check** | quick 以上で実施 | quick 以上で実施 | quick 以上で実施 |
| **design gate** | standard のみ | quick 以上で実施 | quick 以上で実施 |
| **security reviewer** | 明示依頼時のみ | 条件起動（既定） | 常時起動 |
| **completion reviewer** | skip | standard のみ | quick 以上で実施 |
| **worktree** | [workspace-policy.md](./workspace-policy.md) を参照 | [workspace-policy.md](./workspace-policy.md) を参照 | [workspace-policy.md](./workspace-policy.md) を参照 |
| **Verification 記録** | AC pass/fail のみ | method + status + evidence | フル schema（notes 必須） |
| **adr.md** | 任意 | 任意 | standard タスクで推奨 |
| **Post-Completion PR Flow** | 任意 | 自動 | 自動 + セルフレビュー必須 |

## 設定方法

運用レベルは以下の優先順位で決定される:

1. **ユーザー明示**: `/gdd-dev` 実行時に `--level strict` のように指定
2. **リポジトリ設定**: `.gdd-config.md` の `Operation Level` フィールド
3. **デフォルト**: `standard`

### `.gdd-config.md` の例

```markdown
# GDD Configuration

Operation Level: standard
```

リポジトリルートに `.gdd-config.md` を置く。このファイルは GDD の設定のみを保持する軽量ファイル。

`GDD Push Review Exempt Paths:` の宣言は、push review の hook（`hooks/scripts/git_pre_push_review.py`）がほかの宣言より狭く読む。コードフェンス（バッククォート・チルダ 3 つ）か HTML コメントの開始を 1 つでも含むファイルでは読まず、行頭から書いた行（前に空白を付けない）だけを使う。

### PR Auto Review Convergence（外部レビュー収束の自動化）

- 形式: `PR Auto Review Convergence: reviewers=copilot`（カンマ区切り可）。既定 off（キーが無ければ Auto-Arm は発火せず従来挙動。従来の done 停止条件自体は `references/post-completion-pr-flow.md` が正本）
- 解決順: ① `~/.gdd/config.local.md`（ユーザーグローバル・標準の個人設定置き場・優先） ② 作業ツリー直下 `.gdd-config.md`（チーム共有）。worktree 内セッションが読む（`Worktree Base:` は worktree 作成前に root checkout 文脈で読む値で、読み取り文脈が異なる）
- 優先順位: **タスク自走上限 > 設定キー由来の既定**。キーがある場合、HITL の自走上限既定値は「PR 作成 + 外部レビュー収束まで」に seed される（人間はその場で「PR 作成まで」に戻せる）。挙動の正本は `references/post-completion-pr-flow.md` § Auto-Arm と `skills/gdd-pr-review-followup/SKILL.md` § Auto-Arm Entry

## 各レベルの詳細

### light — まず使ってみる

導入初期に「GDD がどう動くか」を体感するためのレベル。ゲートを最小限にし、摩擦を減らす。

**standard から省略されるもの:**
- design gate（quick タスク）— requirements gate + human check だけで設計フェーズに入る
- completion reviewer（全サイズ）— AC の pass/fail 確認は行うが包括レビューは省略
- security reviewer（自動起動なし）— ユーザーが明示的に依頼した場合のみ起動
- worktree 必須制約（trivial のみ）— trivial は Artifact-less light exception として `.steering/` を作らず直接作業してよい。light でも `.steering/` を作成する formal workflow は worktree 必須で、main ブランチ直下の `.steering/` 作成は許可しない（判断軸は [workspace-policy.md](./workspace-policy.md) を参照）
- Verification の evidence / notes 記録 — AC の pass/fail だけ記録すれば通過

**省略しないもの:**
- fail-closed 条件（曖昧な状態では停止）
- AC の明示（受入条件なしに実装に進まない）
- requirements gate + human check（quick 以上）
- TDD（RED → GREEN → REFACTOR）
- implementation reviewer（inline checklist）

**向いている場面**: 初めて GDD を試すチーム、個人利用、プロトタイプ寄りのリポジトリ

### standard — 推奨デフォルト

バランス重視。ほとんどのチームはこのレベルで十分。

- task-sizing.md の既定ルールがそのまま適用される
- security reviewer は条件起動（auth / secrets / PII / untrusted input を含む変更で自動起動）
- completion reviewer は standard タスクのみ
- worktree の要否は [workspace-policy.md](./workspace-policy.md) を参照

**向いている場面**: 通常のチーム開発、複数人でのコードレビューがある環境

### strict — フルゲート

セキュリティ要件が高い、監査対応が必要、大規模チームで品質を統一したい場合。

**standard に追加されるもの:**
- security reviewer を常時起動（条件に関係なく、全タスクで実行）
- completion reviewer を quick 以上で実施（standard では standard タスクのみ）
- Verification 記録のフル schema 強制（notes フィールドも必須。省略不可）
- タスクサイズの降格禁止（standard → quick への変更不可。安全側に倒す）
- adr.md の推奨（standard タスクでは意思決定記録を残すことを推奨）

**向いている場面**: 金融・医療・個人情報を扱うシステム、SOC2/ISO27001 対応が必要な環境

## 運用レベルの変更

- いつでも変更可能。変更は次の `/gdd-dev` 実行から適用
- 進行中のタスクには影響しない（開始時のレベルで完了まで進む）
- strict → standard / light への変更はチーム合意を推奨

## task-sizing.md との関係

task-sizing.md はタスクの「大きさ」を定義する。operation-levels.md は各大きさに対して「どの工程を適用するか」のオーバーライドを定義する。

- task-sizing.md の判定基準（trivial / quick / standard）は運用レベルに関係なく同じ
- 運用レベルが変えるのは、各サイズに対する gate / reviewer / worktree の適用範囲
- task-sizing.md の「パスごとの違い」テーブルは standard レベルの既定値として維持
