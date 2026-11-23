# チーム導入ガイド

> **所有**: GDD をチームに導入するための手順・チェックリスト・サンプル
> **上位正本**: なし（チーム向けガイドの独立文書）
> **参照元**: `README.md`
> **関連**: 他チーム向け雛形は `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` / 30 分導入シナリオは `docs/ONBOARDING.md`

GDD を個人ツールからチーム標準に引き上げるためのガイド。

## 導入ステップ

### Step 1: 試す（1人、1タスク）

1. 開発者 1 人が GDD をインストールする
2. 小さいタスク（quick サイズ）で `/gdd-dev` を 1 回通す
3. 「人間確認まで辿れたか」「承認後に完了まで進んだか」を確認する

**判断基準**: 1 タスクを完了できれば Step 2 へ。

### Step 2: 運用レベルを決める

チームの状況に合わせて運用レベルを選ぶ（`references/operation-levels.md`）。

| チームの状態 | 推奨レベル |
|-------------|-----------|
| AI コーディング初めて | light |
| 普通の開発チーム | standard |
| セキュリティ要件が高い | strict |

リポジトリルートに `.gdd-config.md` を置く:

```markdown
# GDD Configuration

Operation Level: standard
```

### Step 3: チームに展開する

1. リポジトリに GDD を設定する（下記「リポジトリ設定チェックリスト」参照）
2. チームメンバーに以下を共有:
   - `README.md` の「3分クイックスタート」セクション
   - `references/onboarding.md` の「最初の3分でやること」
3. 最初の 1 週間は light または standard で運用し、慣れてから必要に応じて strict に上げる

### Step 4: 定着を確認する

導入効果を測る指標（任意）:

| 指標 | 測り方 | 期待される変化 |
|------|--------|---------------|
| 差し戻し回数 | PR レビューでの changes_requested 数 | 減少（AI reviewer が先にキャッチ） |
| 中断からの復帰時間 | session 再開から build 再開までの時間 | 短縮（state machine が状態を保持） |
| レビュー修正回数 | implementation gate での remediation loop 数 | 安定（TDD で品質を事前担保） |

---

## リポジトリ設定チェックリスト

チームリポジトリに GDD を導入する際の確認事項:

- [ ] git リポジトリである
- [ ] `git worktree` が使える（bare clone でないこと）
- [ ] GDD プラグインがインストールされている
- [ ] `.gdd-config.md` で運用レベルが設定されている（任意、デフォルトは standard）
- [ ] チームメンバーが Claude Code または Cursor をセットアップ済み
- [ ] PR テンプレートがある場合、GDD の PR Flow と矛盾しないことを確認

---

## 役割別の最初の 1 歩

### 開発者

```
/gdd-dev <自分の担当タスクを書く>
```

人間確認まで進んだら OK と答える。以降は自動。

### レビュワー

AI reviewer が先にチェック済みの PR が来る。`gdd-pr-review` で差分チェックも依頼可能。

### テックリード

1. `.gdd-config.md` で運用レベルを設定する
2. 最初は light で試し、チームが慣れたら standard に上げる
3. `evals/evals.json` でトリガー精度を確認する

### PM

人間確認ポイント（human check）で要件を承認する。初回配布時は `docs/NON_ENGINEER_APPROVER_HANDOUT.md` を共有し、必要に応じて `docs/NON_ENGINEER_HITL_GUIDE.md` も読む。HITL 出力では `判断ポイント` / `ズレ確認` / `OKでも許可されないこと` を中心に確認する。判断材料が足りない場合は `判断材料が足りない` と返し、無理に OK しない。

---

サンプル（requirements.md / design.md、quick サイズ）は `docs/references-archive/worked-examples.md` § quick サイズのサンプル を参照。

---

## 同一リポジトリでの並行開発

チーム内で複数の開発者が同時に `/gdd-dev` を実行する場合のガイド。

### なぜ安全か

GDD は worktree-first で設計されている。各タスクは専用の git worktree で作業するため:

- **ファイルシステムが分離**: 各 worktree は独立したディレクトリ。実装が互いに干渉しない
- **steering が分離**: `.steering/<task-name>/` はタスク名ごとにディレクトリが別れるため、state.md / tasklist.md が衝突しない
- **ブランチが分離**: 各 worktree は専用ブランチを持つため、git の競合が起きない

### 注意点

| 状況 | 対応 |
|------|------|
| 同じファイルを変更する 2 タスクが並行する | PR マージ時にコンフリクトが発生する可能性あり。先にマージされた PR に対して後続 PR をリベースする |
| `learned-patterns.md` の同時更新 | worktree ルートの `docs/learned-patterns.md` は共有リソース。後からマージする側がコンフリクトを解消する |
| DB マイグレーションが並行する | マイグレーション番号の衝突に注意。チーム内で番号帯を割り当てるか、タイムスタンプベースの命名を採用する |

### 推奨プラクティス

1. **タスクの粒度を小さくする**: 変更ファイルの重複を減らすために、タスクのスコープを小さく保つ
2. **main への早期マージ**: 長期間ブランチを分離すると、マージコンフリクトが大きくなる。完了したら早めにマージする
3. **`gdd-status` で互いの状況を確認**: 他のメンバーが同じ領域で作業していないか確認する

---

## よくある質問（チーム導入時）

### Q: 全員が同じ運用レベルを使う必要がある？

A: リポジトリ単位で `.gdd-config.md` に設定するのが推奨。個人で `/gdd-dev --level light` のようにオーバーライドも可能。

### Q: 既存の PR レビュープロセスと競合しない？

A: GDD の AI reviewer は PR 作成前に品質チェックを行う。既存の PR レビューは引き続き有効で、AI reviewer が事前にキャッチした分だけ人間レビューの負荷が減る。

### Q: light で始めて途中で standard に上げられる？

A: いつでも変更可能。`.gdd-config.md` を更新すれば次の `/gdd-dev` から適用される。進行中のタスクには影響しない。

### Q: Cursor と Claude Code が混在するチームでも使える？

A: 使える。同じ契約・同じゲートがどちらの環境でも再現される。Cursor は hooks の有効化に追加手順が必要（`references/cursor-guide.md` 参照）。
