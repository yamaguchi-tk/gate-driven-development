# PROJECT CLAUDE.md TEMPLATE

> **対象**: GDD を導入するプロジェクトの `CLAUDE.md` 雛形
> **使い方**: 「必須項目」を全て取り込み、「推奨フルセット」から自チームの状況に合わせて選ぶ
> **上位正本**: プロジェクト個別の CLAUDE.md（本テンプレはあくまで雛形）
> **この文書の位置付け**: GDD が期待するプロジェクト設定を他チームが迷わず導入できるようにする

---

## 必須項目（これが無いと GDD の安全保証が崩れる）

以下を自プロジェクトの `CLAUDE.md` に最低限含める。既にユーザー個人の `~/.claude/CLAUDE.md` で設定済みの項目はスキップしてよい。

### 1. GDD 導線

```markdown
## GDD 導入プロジェクト共通

- `/gdd-dev <タスク>` で formal workflow を起動する
- 壁打ち・相談だけのときは `/gdd-dev` を使わず通常会話（`gdd-pre-workflow-brainstorming` が自動トリガー）
- `.steering/` 配下は AI エージェントが管理する正本。直接手で編集しない
- 現在地の確認は `gdd-status` skill
```

### 2. Operational Safety（破壊的操作の保護）

```markdown
## Operational Safety

自律継続モード（`/gdd-dev` の auto 実行等）でも、以下は **1 操作ごとに明示的な確認** を取る:

- **Terraform write**: `terraform apply`, `terraform destroy`, `terraform import`, `terraform state rm`
- **AWS CLI write**: `create-*`, `delete-*`, `update-*`, `put-*`, `modify-*`, `terminate-*`, `deregister-*`, `revoke-*`, `stop-*`, `start-*`
- **破壊的ファイル操作**: `rm -rf`, `rm -r`（ワーキングツリー外）
- **Docker push**: `docker push`, ECR push
- **データベース**: `DROP` / `DELETE` / `TRUNCATE` / `ALTER`（本番/共有 DB）

禁止事項:

- `-auto-approve` 系フラグの使用禁止
- 包括的承認の連鎖禁止（「apply して」は直近 1 操作への承認であり、後続の未提示操作への blanket permission ではない）
- deny 後の同一操作再試行禁止
```

### 3. Secrets 保護

```markdown
## 機密情報の取り扱い

以下を含むファイルは commit・push しない。`.steering/` / plugin artifact にも書かない:

- AWS アカウント ID（12 桁の数字）
- 秘密鍵（private key marker を含むもの）
- パスワード・API キー・アクセストークン
- Secrets Manager / SSM パラメータ実値
- `.env` 全般

誤って commit した場合は即座にユーザーに報告し、自分で push や PR 作成を行わない。
```

### 4. ブランチ・PR

```markdown
## 新機能追加時

- `main` からブランチを作成
- PR タイトルと本文は日本語で記載（English プロジェクトなら英語）
- プロジェクトの PR テンプレートに従う
- commit は作業単位で自律的に行ってよい。ただし、差分確認・必要なテスト・機密情報チェックを行い、コミットメッセージは変更内容が分かるものにする
- push は PR 作成または既存 PR 更新に必要な範囲で行ってよい。force push や履歴改変は明示依頼なしに行わない
- PR 作成は自動処理の許容範囲に含める。PR タイトル・本文はプロジェクト規約に従う
- merge / Issue close / release / 本番デプロイ / terraform apply は明示依頼なしに実行しない
- PR 作成前に raw task `.steering/<task>/` が staged / diff に含まれないことを確認する。標準チェックは `python3 scripts/check-no-raw-task-steering.py --staged` と `python3 scripts/check-no-raw-task-steering.py --against origin/main`
```

---

## 推奨フルセット（運用レベルに応じて選択）

以下はチーム運用で明示しておくと摩擦が減る項目。全部入れる必要はないが、対応する状況がある場合は入れる。

### A. 言語・コミュニケーション

```markdown
## Conversation Guidelines

- 常に日本語で会話する（または English）
- 「まとめて」「一括で」「全て」の依頼は番号付きで網羅的に回答する
- 冗長でも良いのでわかりやすく説明する
```

### B. 設計原則（TDD プロジェクト向け）

```markdown
## 設計原則

シンプルさを優先する:

- YAGNI（今必要ないものは作らない）
- KISS（できるだけ単純に）
- DRY（重複を避ける）

後方互換のための互換レイヤーは、cyclomatic complexity を増やすなら追加しない。

### TDD

- 期待される入出力に基づき、まずテストを作成する
- テスト実行で失敗を確認してから実装する
- 実装中はテストを変更しない
```

### C. 社内ドキュメント連携（該当チームのみ）

```markdown
## 社内ドキュメント

- SSO で保護された社内 wiki・チケット管理は、それぞれの MCP 経由で取得・検索・更新する（WebFetch/curl 禁止）
- 共有時はアカウント ID・内部 URL を `***` でマスクする
```

### D. superpowers / 他 plugin との共存

両方インストールしている場合:

```markdown
## Plugin 優先度

- formal workflow は `/gdd-dev` で入る（GDD）
- superpowers は単発タスク・experimental 実行でのみ使う
- `gdd-using-skills` skill がセッション開始時の skill 選択ルールを持つ
- 両 plugin の skill が同名で競合した場合、GDD 側を優先する
```

### E. AI リソース使用量の制限（オプション）

```markdown
## Resource Limits

- subagent の並列数: 最大 3（standard タスク）
- 1 タスクあたりの reviewer 反復: 最大 5 回（超過時は Reviewer Loop Escape Hatch による route recalibration。human recheck は policy-level 変更時のみ）
- 自走継続の時間上限: なし（ユーザーが任意で停止）
```

### F. 監査・観測（strict 運用向け）

```markdown
## 監査ログ

- `gdd-metrics` で gate 通過率・差し戻し率を定期集計
- `.steering/<task>/worklog.md` は session 跨ぎで残る作業ログ
- reviewer findings は `tasklist.md` に記録される（Fix Attempts / Reviewer Calibration）
- metrics を読む前提として、`state.md` に `Resume From` / `Human Check Status` / `Route In Progress`、`tasklist.md` に `Next Action` が常に残る運用にする
```

---

## 完全な `CLAUDE.md` サンプル（中規模 Web アプリチーム向け）

以下を丸ごとコピーして、自チームの要件に合わせて調整する。

```markdown
# CLAUDE.md

## Conversation Guidelines

- 常に日本語で会話する
- 「まとめて」「一括で」の依頼には番号付きで網羅的に回答する

## 設計原則

- YAGNI / KISS / DRY
- 過剰な正しさよりシンプルさを優先する
- TDD: 期待される入出力のテストを先に書く

## GDD 導入プロジェクト共通

- `/gdd-dev <タスク>` で formal workflow を起動する
- `.steering/` 配下は AI エージェントが管理する。手で編集しない
- 現在地の確認は `gdd-status`

## Operational Safety

自律継続モードでも以下は 1 操作ごとに明示的な確認を取る:

- Terraform write: apply / destroy / import / state rm
- AWS CLI write: create-_ / delete-_ / update-_ / put-_ / modify-_ / terminate-_ / deregister-_ / revoke-_ / stop-_ / start-_
- 破壊的ファイル操作: rm -rf / rm -r
- Docker push / ECR push
- DB: DROP / DELETE / TRUNCATE / ALTER（本番/共有）

禁止:

- `-auto-approve` フラグ
- 包括的承認の連鎖
- deny 後の同一操作再試行

## 機密情報

commit・push しない:

- AWS アカウント ID（12 桁）
- 秘密鍵
- パスワード・API キー・アクセストークン
- Secrets Manager / SSM 実値
- `.env`

## 新機能追加時

- `main` からブランチを作成
- PR タイトル・本文は日本語
- プロジェクト PR テンプレートに従う
- commit は作業単位で自律的に行ってよい
- push は PR 作成または既存 PR 更新に必要な範囲で行ってよい
- PR 作成は自動処理の許容範囲に含める
- merge / Issue close / release / 本番デプロイ / terraform apply は明示依頼なしに実行しない
- raw task `.steering/<task>/` は PR / main に含めない。重要判断は `docs/adr/` や PR body に蒸留する

## Plugin 優先度

- formal workflow は `/gdd-dev`
- superpowers は単発 / experimental のみ
- skill 名競合時は GDD 優先
```

---

## 導入時のチェックリスト

```markdown
- [ ] `CLAUDE.md` に必須項目 4 つが入っている
- [ ] 導入先 repo の CI に `docs/CI_GUARDS.md` の raw task steering guard を追加した
- [ ] `.gitignore` に `.steering/` / `.claude/gdd-dev.local.md` を追加するか判断済み（共有したいなら除外しない）
- [ ] `.claude/` を ignore していないなら、`.claude/gdd-merge-intent.json` と `.claude/gdd-autonomy-pushback.json`（Stop hook の押し返しの宣言と記録）を `.gitignore` に追加した
- [ ] git worktree が使える環境である
- [ ] チームメンバー全員が `docs/ONBOARDING.md` を読んだ
- [ ] PM / PO / 非エンジニア承認者には `docs/NON_ENGINEER_APPROVER_HANDOUT.md` を共有した（詳しい読み方は `docs/NON_ENGINEER_HITL_GUIDE.md`）
- [ ] 運用レベル（strict / standard / light）が `.gdd-config.md` に設定されている
- [ ] 破壊的操作（terraform / aws write）の承認フローがチーム内で共有されている
```

---

## 参考リンク

- 運用レベル選定: `references/operation-levels.md`
- チーム導入の段階的手順: `docs/references-archive/team-onboarding.md`
- 非エンジニア承認者向け 1 ページ配布文: `docs/NON_ENGINEER_APPROVER_HANDOUT.md`
- 非エンジニア承認者向け HITL 読み方: `docs/NON_ENGINEER_HITL_GUIDE.md`
- セキュリティ境界: `docs/SECURITY.md`
- トラブルシューティング: `docs/TROUBLESHOOTING.md`
