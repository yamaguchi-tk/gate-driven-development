# PR Review（bundled）

コード・ドキュメント・Terraform を含む PR を findings-first でレビューする。
Terraform を含む diff は同一ディレクトリへの context 拡張と provider-specific checks を自動適用する。
PR 作成前の review → fix → re-review の反復にも使う。

> このファイルは `pr-review` plugin が未インストール時のフォールバック。
> Terraform provider チェック用の参照ファイル（`google-cloud-naming.md` 等）は同ディレクトリにある。
> **SYNC**: `pr-review` plugin の SKILL.md を更新したら、この bundled コピーも同じ内容に更新すること。

## Model routing

Claude Code では実行中モデルを skill 内から切り替えることはできない。以下は **レビュー冒頭でユーザーへ伝えるべき推奨**:

- docs-only / README / コメント / 差分説明のみ → Sonnet で充分（速度優先）
- プログラムコード・Terraform・混在 PR → より重いモデル（Opus 等）を推奨。現在のモデルがそれより軽い場合は冒頭に一言添える
- Terraform はコードレビューと同等に扱う

## PR の分類

差分を確認し、以下の 4 種に分類してから review 手順を選ぶ:

| 種別 | 条件 |
|------|------|
| docs-only | `.md` / コメント / README のみ |
| code-only | `.tf` `.tfvars` `.tf.json` `.hcl` を含まないコード変更。CI/CD 設定（`.github/workflows/*.yml`、`Makefile` 等）はコード扱い |
| terraform-only | `.tf` `.tfvars` `.tf.json` `.hcl` のみ |
| mixed | 上記の組み合わせ |

## Review focus

1. Correctness and regressions
2. Security and safety
3. Maintainability and readability
4. Test coverage and verification
5. Documentation consistency
6. Terraform: drift, destructive risk, provider-specific prerequisites, default safety

## Review procedure

### docs-only

- 明快さ・前提・抜け・矛盾を確認する
- Findings は High → Medium → Low の順で出す

### code-only

- バグ・エッジケース・安全性・テスト観点を確認する
- セキュリティ観点（injection / auth / secrets / SSRF / LLM固有リスク）を確認する
- Findings は High → Medium → Low の順で出す

### terraform-only / terraform を含む mixed

「Terraform review」節の手順を適用する。

### mixed（コード + docs）

docs-only と code-only の両方の手順を適用する。

## Terraform review

Terraform / OpenTofu の変更（`*.tf` `*.tfvars` `*.tf.json` `*.hcl`）を含む場合は本節を適用する。

### 基本方針

差分 hunk だけを見て断定するとノイズが増える。変更起点から **同一ディレクトリを module 境界の基本単位として関連ファイルまで読み広げ**、次を高シグナルで確認する:

- 正しさ・互換性・セキュリティ・運用性・コスト
- provider 固有 naming constraints
- provider 固有 DNS record conflict
- cross-resource prerequisite（silent-failure につながる依存関係）

### 対象の決め方

1. ユーザーが `target:` / path / module を指定していればそれを優先する
2. 指定がなければ、working tree を `HEAD` と比較した差分を起点にする
3. `base:` が明示されていれば `git diff <base>...HEAD` 相当の diff を優先する
4. `plan:` が提示されていれば補助情報として使う

### 同一ディレクトリを基本に広げる

優先して読む候補:
`main.tf` / `variables.tf` / `outputs.tf` / `locals.tf` / `providers.tf` / `versions.tf` / `terraform.tf` / `terraform.tfvars` / `*.tf.json` / `*.auto.tfvars` / `moved.tf` / `data.tf` / `*.hcl` / `README.md`

広げ方のルール:
- repo 全体へ無差別に広げない
- 同一ディレクトリで完結するか確認する
- 1 hop で意味が確定しないときだけ、直近の local module 参照を追う
- それでも確定しない場合は `要追加確認` とする

### 基本チェック

**正しさ**
- resource / module / data / output が Terraform 的に一貫しているか
- 参照先の local / variable / output と整合しているか
- rename や split に `moved` や state 影響の配慮があるか
- `count` / `for_each` / key 変更で破壊的置換が起きやすくないか

**セキュリティ**
- IAM や policy が広すぎないか
- public exposure・暗号化・secret 混入に問題がないか
- ネットワークや bucket / object access 周りが過剰に開いていないか

**互換性と運用**
- provider / module version の変更が互換性を壊していないか
- `prevent_destroy` / `create_before_destroy` / `ignore_changes` / `depends_on` の使い方が妥当か
- import 済み・既存運用前提の resource に不要な置換が入りそうでないか

**入出力**
- variables の type / default / validation が妥当か
- outputs が利用側に対して安定した契約になっているか
- module input の追加・削除・rename が caller と整合しているか

**コストと性能**
- 高額になりやすい resource サイズ・冗長構成・ログ出力量を増やしていないか
- retention / monitoring / lifecycle 設定が過不足ないか

### Google Cloud provider-specific checks

`google` / `google-beta` provider または `google_*` resource が見える場合は `google-cloud-naming.md`（このファイルと同ディレクトリ）を読む。

v1 明示サポート:
- `google_storage_bucket`: `google` 混入 / `goog` prefix / IP 形式 / 長さ・文字種
- `google_compute_*`: RFC 1035 形式の文字種・先頭末尾・長さ

### AWS Route53 provider-specific checks

`aws_route53_record` が見える場合は `route53-record-conflicts.md`（このファイルと同ディレクトリ）を読む。

- 同一 `hosted_zone_id` 内での CNAME conflict を優先して確認する
- `base:` がある場合は変更で新規導入された衝突か既存問題かを切り分ける

### CloudWatch metric / alarm prerequisite checks

`aws_cloudwatch_metric_alarm` / `aws_cloudwatch_composite_alarm` / `aws_cloudwatch_dashboard` / `aws_cloudwatch_log_metric_filter` が差分に含まれ、`namespace =` / `metric_name =` が新規または変更されている場合は `cloudwatch-metric-prerequisites.md`（このファイルと同ディレクトリ）を読む。

feature-gated メトリクス（Container Insights / RDS Performance Insights 等）が前提未達の場合、アラームが永久に `MISSING` になる silent-failure を early に止めるのが目的。

### AWS / GCP cross-resource prerequisite checks

以下の resource が差分に含まれる場合は `aws-cross-resource-prerequisites.md` または `gcp-cross-resource-prerequisites.md`（いずれもこのファイルと同ディレクトリ）を読む:

- AWS: `aws_s3_bucket_notification` / `aws_cloudfront_distribution` / `aws_api_gateway_stage` / `aws_wafv2_web_acl` / `aws_lambda_event_source_mapping` / `aws_ecs_task_definition` / `aws_ecs_service` / `aws_rds_cluster` / `aws_kms_key` / `aws_flow_log` / `aws_lb_target_group` / `aws_route53_record` (alias) 等
- GCP: `google_logging_project_sink` / `google_iam_workload_identity_pool` / `google_artifact_registry_repository` 等

### `focus:` の扱い

`focus:` はレビュー観点の優先順位を決める補助ヒント。指定観点外でも `high` 相当の問題は省略しない。
受け付ける値: `security` `compatibility` `cost` `google-naming` `route53-dns` `cloudwatch-metric-prereq`

### ノイズを減らすルール

- diff の 1 行だけで断定しない
- 同一モジュールを読めば解消する曖昧さは先に解消してから指摘する
- lint / fmt / type error 相当の細かい一般論は主対象にしない
- `要追加確認` にすべき場面で無理に NG と断定しない

## Pre-PR loop

1. 現在の差分を本 skill でレビューする
2. 指摘を修正する
3. 修正後の差分をもう一度レビューする
4. High finding が消え、Medium finding も修正または明示的に受容できる状態になるまで繰り返す
5. PR 作成前チェックリストを確認する
6. その後に PR を作る

## Stop conditions

- High finding が 0 件になったら Pre-PR loop は終了候補にする
- Medium finding は修正するか、残留リスクとして明示して受容する
- Low finding は残留リスクとして記録すれば PR 作成を妨げない
- 同じ High finding が修正後も再発する場合は PR を作らず追加修正に戻る

## PR 作成前チェックリスト

### 1. 差分 scope の確認

- `git diff <default-branch>...HEAD` で PR に含まれる全変更を確認する
  （default branch: `git symbolic-ref refs/remotes/origin/HEAD` で取得）
- 今回のタスクに無関係な変更が混入していないか確認する
- untracked ファイル（ローカル状態ファイル等）がステージされていないか確認する
- scope 外の変更が見つかった場合は High finding として報告し、PR 作成を止める

### 2. worktree 状態の確認

- 現在のブランチが意図したブランチであることを確認する
- `git status` で未コミットの変更やステージ漏れがないか確認する

### 3. セルフレビュー

- `git diff <default-branch>...HEAD` の全差分を読み、コードの正当性・回帰リスク・セキュリティ・テストカバレッジを確認する
- 機密情報（12 桁 AWS アカウント ID、秘密鍵、`.env`、API キー、アクセストークン、Secrets Manager / SSM 実値）が diff / staged / untracked 候補に含まれていないか確認する
- Dockerfile / container 関連差分がある場合は、`latest` 固定漏れ、不要 layer、multi-stage 未活用、root 実行、secret bake-in、cache 破壊を確認する
- High finding があれば PR 作成を止め、修正してから再実行する

### 4. PR テンプレート・言語の確認と PR 作成

- リポジトリに PR テンプレートが存在するか、`git ls-files | grep -i -E '(^|/)pull_request_template'` で確認する（大文字・小文字と、`.github/`・`docs/`・root・`PULL_REQUEST_TEMPLATE/` の置き場を拾う。グロブで探さない。zsh では一致しないグロブがコマンドごと失敗し、在るテンプレートを見落とした事例が 2 件あった）
- テンプレートが存在する場合はそのフォーマットに従って PR 本文を作成する
- プロジェクトの規約で PR の言語が指定されている場合はタイトル・本文をその言語で記載する
- テンプレート内のコメント（`<!-- ... -->`）は削除しない
- **PR Body WHY Check**: GDD で作成する PR 本文からは、**なぜこの変更が必要か**、誰（利用者 / 運用 / 開発者）が何が困っていたか、放置すると何が起きるかが読めなければならない。WHY のための見出しは足さず、テンプレートがあれば目的・背景を書く欄（`## 背景` / `## 目的` / `## 要件` / `## 概要` など）の冒頭、そういう欄が無ければ最初の欄の冒頭、テンプレートが無ければ本文の最初の段落に書く（本文の型は `references/japanese-writing-norm.md` § PR 本文）。内容は `requirements.md` の `目的` / `Summary Brief` / 受入条件に写したユーザーの完了条件 / `Why` 記録から抽出し、docs-only / prompt-only の小さな PR では 1-2 文、通常 PR では 1-3 文を目安に書く。実装内容の言い換えだけでは不可。WHY が無い、または「何を実装したか」だけで背景・困りごとが読めない場合は High finding として PR 作成を止める。
- **Issue Reference Check**: `Refs #123` / `Closes #123` / 外部のチケット管理の URL などの参照は、WHY の代替として扱わない。PR 本文にはチケット参照と、GDD artifact から抽出した WHY の両方を残す。外部チケット本文を読めない場合でも、`requirements.md` の `目的` / `Summary Brief` / `Why` 記録から WHY を書けるなら PR 作成を止めない。
- **PR Body Boundary / Follow-up Check**: `requirements.md` に Stage 分割、`Planned Follow-up Stage Lane`、または `PR Boundary=follow-up-pr` / `post-merge-verification` がある場合、PR 本文に今回 PR の範囲と、この PR ではまだ解決しない後続 Stage を、残した問題の欄（テンプレートに `## Follow-up` / `## 後続対応` / `## 今回の範囲と後続対応` などの欄があればそこ）で明示する。最低限、`今回含む Stage`、`今回含まない Stage`、`後続 PR の入口` または Tracking Destination を書く。Tracking Destination の合格例: `GitHub Issue #123`、外部チケットの ID（`ABC-123`）、`.steering/YYYYMMDD-next-stage/` seed、再開プロンプト。WHY Check とは別チェックとして扱い、WHY が存在していても boundary / follow-up が読めない場合は High finding として PR 作成を止める。
- **PR Body Confidentiality Check**: WHY はレビュー可能な抽象度で書き、PII、secret 実値、12 桁 AWS アカウント ID、顧客名、社内の検知経路、攻撃や悪用に使える再現手順・詳細条件を PR body に書かない。`requirements.md` / `design.md` / `adr.md` に機密情報が含まれる場合も、そのまま転記しない。必要性・影響・安全境界をマスクまたは抽象化して要約する。PR body 作成後に、12 桁数字（例: `\b[0-9]{12}\b`）、秘密鍵開始ヘッダ、token/key/password 系文字列、顧客名らしき固有名詞、検知経路、再現手順の有無を secret / PII 観点で確認し、含まれる場合は High finding として `gh pr create` を止める。OK 例: 「機密性の高い識別情報が外部公開されるリスクを減らすため」。NG 例: 実値、顧客名、検知経路、再現条件を含む WHY。

## Output format

レビュー本文は GitHub 上で 5 秒以内に次アクションを判断できる形にする。詳細ログではなく、採用判断を圧縮して出す。

```markdown
**対象PR**: <この PR が何を変えるかを 1 行で説明>

## 結論
<✅ 問題なし / ⚠️ 要確認 / ⛔ 修正必須> — <採用 finding 件数と、次にやることを 1 文で書く>

## 採用Findings
🔴 HIGH `<file or module>` — <問題を 1 行>

⚠️ MEDIUM `<file or module>` — <問題を 1 行>

- 修正: <author が次にやることを 1 行>
- 根拠/影響: <根拠と impact を 1-2 文。必要なら関連ファイルも明記>

HIGH は `🔴 HIGH`、MEDIUM は `⚠️ MEDIUM` を使う。`🟡` は `マージ前確認` の優先度ラベル専用で finding severity には使わない。

## マージ前確認
- [ ] 🔴 <merge 前に必須の確認>
- [ ] 🟡 <意図確認・外部前提確認>
- [ ] ℹ️ <任意の補足確認>

## 要件突合 ✅/⚠️/❌
| 要求 | 実装 | 判定 |
|---|---|:-:|
| <要求 or AC> | <実装状況> | ✅ |
| <要求 or AC> | <実装状況> | ⚠️ |

## 不採用Findings (<shown>/<total> 件)
- `<file or module>`: <不採用理由を 1 行。false positive / evidence 不足 / residual risk 移動など>

## Review metadata
- confidence: <high/medium/low> / coverage gap: <未確認事項>
- judgment axis: <今回の優先順位。例: deploy safety > requirements-fit>
- linked context: <full/partial/unavailable> / dialectic: <selected/not_applicable>
- version: <skill or bot version が分かる場合>
```

出力ルール:
- Findings は重大度順（High → Medium → Low）
- 各 finding は原則 2 bullet（`修正`、`根拠/影響`）に収める。複雑な場合だけ 3 bullet まで許可
- `対象PR` は結論の前に置き、PR の目的を 1 行で把握できるようにする
- `結論` は dashboard 風の件数列挙にせず、次アクション 1 つが読める自然文にする
- `マージ前確認` は GitHub checkbox 記法を使う
- `要件突合` は feature / access / Terraform のいずれでも `✅/⚠️/❌` を使う。access assignment など traceability が重要な PR は table を維持し、単純 feature は bullet にしてもよい
- `不採用Findings` は監査性のため残すが、見出しに件数を含め、代表例だけに圧縮する
- `No findings.` のときも `マージ前確認`、`要件突合`、`Review metadata` は残す
- 軽微な補足は Findings に増やしすぎず、`マージ前確認`、`不採用Findings`、`Review metadata` に寄せる
