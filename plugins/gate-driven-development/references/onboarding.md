# Onboarding

> **所有**: 初回利用向けの最短シナリオと成功条件
> **上位正本**: なし（ユーザー向けガイドの独立文書）
> **参照元**: `commands/gdd-dev.md`、`faq.md`
> **他チーム向け展開ガイド**: `docs/ONBOARDING.md`（30 分導入シナリオと 1 週間チェックリスト）

## 最初の3分でやること

**1. タスクを伝えて実行する**

```
/gdd-dev ユーザー一覧画面にページネーションを追加したい
```

**2. 待つ（AI が自動で進む）**

要件整理 → AI レビュー → 人間確認で止まる

**3. 承認する**

表示された承認ポイントに OK / 別案希望 を答える。各ポイントには **背景** と **変更前 → 変更後** が付いているので、コンテキストを遡らずに判断できる。末尾の **方向性承認** で AI の自走範囲も合意する。承認後は完了まで自動。

以上。初回はここまでできれば成功。

---

## 小さいタスクは小さく終わる

GDD はすべてのタスクにフル工程を要求しない。タスクサイズに応じてセレモニーが自動調整される。

### trivial（〜1分、ゲートなし）

```
/gdd-dev README の typo を修正
```

→ AI が修正してそのまま完了。レビューも承認もなし。

### express（15〜45 分の目安、承認 1 回だけ）

```
/gdd-dev --express ログイン後のリダイレクトバグを修正
```

→ 要件整理 → 要件レビュー → 承認 → テスト + 実装 → レビュー → 完了。設計 gate やタスク分解は省略。

**「GDD は重い」と感じたら、まず trivial / express を試してほしい。** 日常の小さな修正はこれで十分。standard フローが必要なのは複数ファイルにまたがる開発だけ。

---

## 段階的な学習パス

| 段階 | やること | 覚えること | 所要時間 |
|------|---------|-----------|---------|
| **Day 1** | `/gdd-dev <タスク>` で 1 回動かす | human check まで辿れれば成功 | 3 分 |
| **Day 2-3** | trivial / express / quick を使い分ける | タスクサイズと ceremony の関係 | README § 所要時間の目安 |
| **Week 1** | `gdd-status` で現在地確認、中断→再開を試す | state.md / Resume From の仕組み | 適宜 |
| **Week 2+** | `gdd-metrics` で実績を確認、チーム導入を検討 | gate 通過率・差し戻し傾向 | 適宜 |

---

## 詰まったらどこを見るか

| 症状 | 見る場所 |
|------|---------|
| 「新規か再開か」聞かれる | `/gdd-dev 新規開始: <task>` と明示する |
| git / worktree で止まる | git リポジトリ内で実行しているか確認 |
| 同名 asset 衝突で止まる | 別実体の同名 skill/agent を退避・無効化する |
| phase が進まない | hooks が有効か確認。Cursor は manifest 経由で有効化が必要 |
| 何が正本か分からない | `gdd-status` で現在地を確認 |
| superpowers と GDD で迷う | `references/superpowers-overlap.md` の使い分け表を見る（短答: standalone 探索なら superpowers、workflow 完走したいなら GDD） |

詳しくは `references/faq.md` を参照。

---

## よくある失敗と回避方法

### 1. 引数なしで `/gdd-dev` を実行する

```
# NG — 新規か再開か判断できず止まる
/gdd-dev

# OK — タスクを伝える
/gdd-dev 通知設定の CRUD API を追加したい
```

### 2. git リポジトリ外で実行する

GDD は worktree を前提とするため、git リポジトリ外では起動できない。`git init` してから再実行する。

### 3. 人間確認で何を見ればいいか分からない

`承認ポイント` の箇所だけ見ればよい。各ポイントに **背景**（なぜ必要か）と **変更前 → 変更後**（何が変わるか）が付いており、yes/no で判断できる。要件の全文を読む必要はない。末尾の **方向性承認** で、実装中に E2E で発見された問題を AI が自律判断してよい範囲を合意する。

### 4. Cursor で自動継続しない

hooks を manifest 経由で有効化する必要がある。hooks なしでも動くが、phase 間で「次に進めて」と手動指示が必要。

---

## 初回の成功条件

**人間確認（human check）まで辿れること。** 承認後の自動フローは初回以降で慣れればよい。

確認方法:
- active worktree 側 `.steering/.../requirements.md` がある
- active worktree 側 `.steering/.../design.md` がある
- `Resume From=human-check-waiting` まで進んでいる

---

## 3つの入り口

| やりたいこと | 入り口 | 何が起きるか |
|-------------|--------|------------|
| まず相談・壁打ち | 普通に会話する | `gdd-pre-workflow-brainstorming` が自動トリガー。成果物なし |
| 実装まで進める | `/gdd-dev <やりたいこと>` | formal workflow を開始 |
| 状態を確認する | `gdd-status` | 現在のフェーズ・ゲート状態を表示 |

### 相談 → 実装の流れ

相談フェーズで考えを整理してから `/gdd-dev` で formal workflow に入る。

---

## 具体例

### アプリチーム

| やりたいこと | コマンド例 | 想定パス |
|-------------|-----------|---------|
| API エンドポイント追加 | `/gdd-dev 通知設定の CRUD API を追加したい` | standard |
| UI コンポーネント作成 | `/gdd-dev ダッシュボードにグラフウィジェットを追加したい` | quick / standard |
| バグ修正（軽量） | `/gdd-dev --express ログイン後のリダイレクトバグを修正` | express |
| バグ修正（通常） | `/gdd-dev ログイン後にリダイレクトが 2 回走るバグを修正したい` | quick |
| DB マイグレーション | `/gdd-dev users テーブルに phone_number カラムを追加したい` | quick / standard |

### インフラチーム

| やりたいこと | コマンド例 |
|-------------|-----------|
| Terraform 変更 | `/gdd-dev ECS サービスの AutoScaling 設定を追加したい` |
| CI/CD パイプライン | `/gdd-dev GitHub Actions に staging デプロイジョブを追加したい` |
| 監視設定 | `/gdd-dev CloudWatch アラームの閾値を見直したい` |

---

## 調査記録の残し方（findings.md / worklog.md）

planning 中の調査知見やプロセスを残すファイルが 2 つある:

| ファイル | 用途 | 作るタイミング |
|---------|------|--------------|
| `findings.md` | 技術調査の結果、比較検証、外部ドキュメントの要約 | 調査操作を 2 回行ったら書き出す |
| `worklog.md` | 試して捨てた選択肢、検索過程、セッション跨ぎで失われると困る知見 | 任意（session 跨ぎで残したいときに書く） |

- いずれも `.steering/.../` 内に作成する
- gate 条件や routing source にはならない（あくまで補助記録）
- `findings.md` は `Sources` / `Synthesized Findings` / `Comparisons` のセクションで構造化する
- `adr.md`（意思決定記録）とは棲み分ける: `adr.md` は「決まったこと」、`worklog.md` は「過程」

---

## Cursor ユーザー向け

Cursor で使う場合は `references/cursor-guide.md` を確認。主な違い:

- **導入**: `bash scripts/install-cursor-links.sh` で symlink を作る
- **hooks なしの場合**: phase ごとに手動で「次に進めて」と指示する
- **モデル**: Grok 4.6 / Grok 4.5 / Composer 2.5 を使う（`references/cursor.md` 参照）

---

## human check 承認後の流れ

`gdd-brainstorming` で要件を整理した後、承認後は以下が自動的に進む:

1. `gdd-design-gating` — 詳細設計 + AI レビュー
2. `gdd-task-breakdown` — タスク分解
3. `gdd-test-driven-development` — テスト作成（RED）
4. `gdd-subagent-driven-implementation` — 実装（GREEN + REFACTOR）
5. `gdd-implementation-gating` — 実装レビュー
6. `gdd-completion-check` — 完了チェック → PR 作成

---

## セッション復帰

コンテキストがリセットされた場合（`/clear` やセッション再開）:

- SessionStart フックが自動的に状態を復元する
- `/gdd-dev` で続きから再開できる

---

## 正本の見方

| 状態 | 正本 |
|------|------|
| planning 中 | active worktree 側 `state.md` の `Resume From` |
| build 中 | active worktree 側 `tasklist.md` の `Next Action` |
| 停止時 | `参照した正本` / `停止理由` / `次の1アクション` と、`<gdd-stop>` の後の `## 👤 次にすること`（`cancelled` を除く）が返る |

---

## Reviewer 構成（4 agents）

| reviewer | 役割 |
|----------|------|
| `gdd-planning-reviewer` | 要件の完全性・AC 品質・設計の一貫性・実現可能性 |
| `gdd-implementation-reviewer` | バグ・保守性・AC 準拠・契約遵守・信頼性・性能 |
| `gdd-security-reviewer` | セキュリティ・secrets・trust boundary |
| `gdd-completion-reviewer` | 最終横断レビュー・コード品質・cross-cutting リスク |
