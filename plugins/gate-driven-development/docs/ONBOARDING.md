# ONBOARDING（他チーム導入ガイド）

> GDD hook が想定外に動作する場合は `mkdir -p ~/.claude && touch ~/.claude/gdd-hooks-disabled` で全 hook を即時停止できる（詳細: `docs/TROUBLESHOOTING.md#緊急停止kill-switch`）。復帰は `rm -f ~/.claude/gdd-hooks-disabled`。

> **対象**: GDD plugin を自チームに試験導入したい導入担当エンジニア / テックリード
> **ゴール**: 30 分以内に `/gdd-dev` 1 サイクルを完走できる状態を作る
> **上位正本**: `README.md`（機能紹介）、`references/onboarding.md`（個人向け初回シナリオ）、`docs/references-archive/team-onboarding.md`（チーム定着）
> **この文書の位置付け**: 「他チームが初めて触るときの 30 分の道のり」だけを扱う。深い契約仕様は `references/` を参照
> **チーム外展開の入口**: `docs/TEAM_ROLLOUT.md` を最初に読み、導入可否・HITL・worktree / resume・superpowers 共存・成功指標を確認する

---

## 前提条件

導入前に以下を満たしていることを確認する。満たしていない場合は導入を一旦見送り、事前準備だけ済ませる。PM / PO などの非エンジニア承認者には、操作手順ではなく `docs/NON_ENGINEER_APPROVER_HANDOUT.md` を先に共有し、詳しい読み方が必要な場合だけ `docs/NON_ENGINEER_HITL_GUIDE.md` を案内する。

最初に使う host を決める。Claude Code / Cursor / Codex は同じ GDD 契約を使うが、導入手順と自動継続の確認点が違う。

| host | 最初に確認すること | 導入メモ |
|---|---|---|
| Claude Code | `claude --version` と plugin / symlink のどちらで有効化するか | 初回 pilot の推奨 host。hooks が自動有効になる構成で始める |
| Cursor | `scripts/install-cursor-links.sh` と manifest 経由の hooks 有効化 | hooks が無い場合は phase 間を手動で指示する。詳細は `references/cursor-guide.md` |
| Codex | `.codex-plugin/plugin.json` と `references/codex.md` の host-level interruption 境界 | compact 503 など host 側中断時は state 正本から再開する。導入前に model routing も確認する |

この 30 分シナリオは Claude Code を例に書く。Cursor / Codex で始める場合も、同じ `/gdd-dev` サイクルを使い、host 固有の制約だけ上の表で読み替える。

| #   | 前提                            | 確認コマンド                                         | 不足時の対応                                                           |
| --- | ------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| 1   | 利用 host が決まっている        | 上の host 表                                         | Claude Code pilot から始めるか、Cursor / Codex の制約を先に確認する    |
| 2   | 導入対象が git リポジトリ       | `git rev-parse --git-dir`                            | `git init` してから継続                                                |
| 3   | git worktree が使える           | `git worktree list`                                  | bare clone だと不可。通常の clone を使う                               |
| 4   | プロジェクトに CLAUDE.md または AGENTS.md がある | `ls CLAUDE.md AGENTS.md`                    | `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` から雛形を取り込む                |
| 5   | Plugin を取得                   | `ls <path>/gate-driven-development/plugin.json` 相当 | 配布先から取得                                                         |

---

## 30 分導入シナリオ

### 0. 作業ディレクトリを決める（1 分）

他チームに紹介するときは**本番リポジトリではなく試験用リポジトリ**から始める。State Machine・Hook・worktree 生成の挙動を観察するためにも、軽量な clone を使う。

```bash
cd ~/work
git clone <your-repo>.git gdd-trial
cd gdd-trial
```

### 1. Plugin を有効化する（3 分）

Claude Code の plugin として配置する方法が 2 通りある。**はじめて試すなら B（symlink）を推奨**。

**A. Plugin manifest 経由（推奨・hooks 自動有効）**

```bash
# ~/.claude/plugins/local/ に配置
cp -r /path/to/gate-driven-development ~/.claude/plugins/local/
```

**B. Symlink（機能検証用）**

```bash
bash /path/to/gate-driven-development/scripts/install-claude-code-links.sh
```

> Cursor ユーザーは `scripts/install-cursor-links.sh` を使う。hooks の有効化には別途手順が必要。詳細: `references/cursor-guide.md`

### 2. プロジェクト CLAUDE.md を整える（5 分）

`docs/PROJECT_CLAUDE_MD_TEMPLATE.md` を開いて、必須項目を導入プロジェクトの `CLAUDE.md` に追記する。最低限これだけあれば動く:

```markdown
## GDD 導入プロジェクト共通

- `/gdd-dev <タスク>` で formal workflow を起動する
- `.steering/` 配下は AI エージェントが管理する正本。直接手で編集しない
- 破壊的操作（terraform apply / aws \* create|delete|update / rm -rf 等）は 1 操作ごとに人間の明示承認を取る
- secrets・認証情報・PII は `.steering/` や plugin artifact に書かない
```

詳細項目は `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` の「推奨フルセット」セクション参照。

### 3. Plugin の自己検証を走らせる（1 分）

```bash
bash /path/to/gate-driven-development/tests/validate-plugin.sh
```

すべての BLOCK が `OK` で終了することを確認する。失敗がある場合は plugin のバージョンを確認し、配布元に問い合わせる。

### 3b. 導入先 repo の CI guard を入れる（3 分）

standard 運用では raw task `.steering/<task>/` を main に残さない。導入先 repo の PR CI に `docs/CI_GUARDS.md` の snippet を追加し、`scripts/check-no-raw-task-steering.py --against origin/main` 相当が走ることを確認する。

CI をまだ追加できない場合でも、PR 作成前に同じコマンドをローカルで実行する。CI / local guard が fail したら、重要判断を `docs/adr/` や PR body に蒸留してから raw task steering を除去する。

### 4. 初回サイクルを通す（10 分）

Claude Code セッションを開いて以下を実行:

```
/gdd-dev README に導入セクションを 1 つ追加したい
```

観察すべき挙動:

1. `gdd-brainstorming` が起動する（`▶ gdd-brainstorming: …` の skill アナウンス）
2. 要件整理 → `gdd-requirements-gating` で AI reviewer が走る
3. **human check で停止する**（`Resume From=human-check-waiting` / 承認ポイントがターミナルに出る）
4. `OK` と返すと自動で設計 → TDD → 実装 → レビュー → 完了まで進む

**初回の成功条件**: human check まで辿れること。承認後の自動フローで失敗しても、それは次の 1 週間で慣れれば解消する。

### 5. 中断と再開を試す（5 分）

`/clear` でセッションをリセットしてから:

```
/gdd-dev 再開
```

`SessionStart` hook が直前の state を復元するのを確認する。`Last Handoff Summary` が出力されれば成功。

### 6. `gdd-status` で現在地を確認する（2 分）

```
gdd-status
```

以下が表示されれば state machine が正しく動作している:

- 現在の phase
- `Resume From` / `Next Action` / `Route In Progress`
- 進捗（task N/M done）

### 7. 撤去手順を確認する（3 分）

導入試験なので、撤去経路も確認する:

```bash
# Symlink 方式で入れた場合
bash /path/to/gate-driven-development/scripts/uninstall-claude-code-links.sh

# steering は残る（必要なら git で除去）
git worktree list  # 生成された worktree の確認
git worktree remove <path>  # 不要なら削除
```

---

## 導入後の 1 週間で確認すること

| Day     | やること                                     | 成功条件                |
| ------- | -------------------------------------------- | ----------------------- |
| Day 1   | quick タスクで 1 サイクル完走                | PR が作成される         |
| Day 2   | trivial / express を試す                     | 小タスクには小ゲート    |
| Day 3   | 中断→再開を 2 回以上繰り返す                 | 毎回正しく復帰          |
| Day 4   | 差し戻しシナリオを観察（AI reviewer の指摘） | remediation loop が動く |
| Day 5   | `gdd-pr-review` で差分チェックを依頼         | Spec Drift Check が通る |
| Day 6-7 | チームの他メンバー 1-2 人を誘って並行実行    | worktree 分離が動く     |

---

## 試験導入中の判断ポイント

以下 3 点で判断すると、運用チームへの展開可否が見える:

1. **再開できているか**: session をまたいで迷わず続きに戻れる（`Resume From` の機能）
2. **reviewer の指摘が妥当か**: AI reviewer の false positive が許容範囲（チーム毎に定義）
3. **停止出力で迷わないか**: 停止ポイントの出力だけで次のアクションが判断できる

1 つでも「難しい」なら導入を一時停止し、`docs/TROUBLESHOOTING.md` を読んでから再試行する。

---

## 展開フェーズへの移行

試験導入が成功したら、次のステップは以下:

1. **運用レベルの決定**: `references/operation-levels.md` で strict / standard / light を選ぶ
2. **チーム全員への展開**: `docs/references-archive/team-onboarding.md` の Step 3 を実行
3. **監視項目の設定**: `gdd-metrics` で gate 通過率・差し戻し率を記録開始
4. **障害時の復旧手順**: `docs/TROUBLESHOOTING.md` を熟読

---

## 参考リンク

- 機能概要: `README.md`
- チーム外展開キット: `docs/TEAM_ROLLOUT.md`
- 個人向け初回シナリオ: `references/onboarding.md`
- チーム定着ガイド: `docs/references-archive/team-onboarding.md`
- 非エンジニア承認者向け 1 ページ配布文: `docs/NON_ENGINEER_APPROVER_HANDOUT.md`
- 非エンジニア承認者向け HITL 読み方: `docs/NON_ENGINEER_HITL_GUIDE.md`
- 詰まりどころ Q&A: `docs/TROUBLESHOOTING.md`（新しい体系化版）/ `references/faq.md`（契約正本）
- CLAUDE.md テンプレ: `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`
- CI guard: `docs/CI_GUARDS.md`
- セキュリティ境界: `docs/SECURITY.md`
