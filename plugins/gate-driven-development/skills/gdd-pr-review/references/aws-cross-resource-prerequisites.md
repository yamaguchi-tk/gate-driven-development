# AWS Cross-Resource Prerequisite Reference

このファイルは AWS リソースの cross-resource dependency（リソース A が機能するためにリソース B の設定・権限が必要）の参照です。

方針:

- `terraform plan` も `terraform apply` も通るが、実行時に **silent-failure**（ログが出ない / 通知が飛ばない / 接続できない / 機能しない）になるパターンに限定する
- 同一モジュール基本単位で前提の有無を追い、確定できない場合は `要追加確認` に寄せる
- permission / policy / IAM 系の resource が対になっているかを優先して確認する

---

## 1. 対象

差分に以下の resource type が含まれる場合、該当セクションの前提をチェックする:

| Trigger resource | チェックセクション |
|---|---|
| `aws_s3_bucket_replication_configuration` | §2a |
| `aws_s3_bucket_notification` | §2b |
| `aws_cloudfront_distribution` (S3 origin) | §3 |
| `aws_api_gateway_stage` (access_log_settings) | §4 |
| `aws_db_instance` / `aws_rds_cluster` (`backup_retention_period`) | §5 |
| `aws_flow_log` | §6 |
| `aws_wafv2_web_acl` | §7 |
| `aws_lambda_event_source_mapping` / `aws_sns_topic_subscription` (Lambda) / `aws_cloudwatch_event_target` (Lambda) | §8a |
| `aws_lambda_function` (`dead_letter_config`) | §8b |
| `aws_lambda_function_event_invoke_config` | §8c |
| `aws_ecs_task_definition` (`secrets`) | §9 |
| `aws_ecs_service` (`enable_execute_command`) | §10 |
| `aws_rds_cluster` | §11 |
| `aws_kms_key` (explicit `policy`) | §12 |
| `aws_route53_record` (`alias`) | §13 |
| `aws_lb_target_group` (`health_check`) | §14 |

---

## 2. S3 Cross-Resource Prerequisites

### 2a. Replication

公式: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html

前提:

- source bucket と destination bucket の **両方** に `aws_s3_bucket_versioning` (`status = "Enabled"`) が必要
- `aws_iam_role` に replication 用の policy が必要

```hcl
resource "aws_s3_bucket_versioning" "source" {
  bucket = aws_s3_bucket.source.id
  versioning_configuration { status = "Enabled" }
}
```

レビューで確認すること:

- `aws_s3_bucket_replication_configuration` があるのに source / destination に `aws_s3_bucket_versioning` が無い → `[high]`
- versioning が `Suspended` → `[high]`（replication が停止する）

### 2b. S3 Bucket Notification → Lambda / SNS / SQS

公式: https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html

前提:

- Lambda 宛: `aws_lambda_permission` で `principal = "s3.amazonaws.com"` を許可
- SNS 宛: `aws_sns_topic_policy` で S3 の Publish を許可
- SQS 宛: `aws_sqs_queue_policy` で S3 の SendMessage を許可

```hcl
resource "aws_lambda_permission" "s3" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data.arn
}
```

レビューで確認すること:

- `aws_s3_bucket_notification` の destination に Lambda / SNS / SQS が指定されているのに、対応する permission resource が同一モジュール内に無い → `[high]`
- `source_arn` が bucket ARN と一致しているか確認

---

## 3. CloudFront S3 Origin

公式: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

前提:

- OAC 使用時: `aws_cloudfront_origin_access_control` + `aws_s3_bucket_policy` で CloudFront service principal の GetObject を許可
- OAI（レガシー）使用時: `aws_cloudfront_origin_access_identity` + `aws_s3_bucket_policy`

```hcl
resource "aws_s3_bucket_policy" "cf" {
  bucket = aws_s3_bucket.web.id
  policy = jsonencode({
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.web.arn}/*"
      Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.web.arn } }
    }]
  })
}
```

レビューで確認すること:

- `aws_cloudfront_distribution` の origin が S3 で `origin_access_control_id` を指定しているのに bucket policy が無い → `[high]` (403 エラー)
- OAI / OAC の混在（同一 origin に両方）→ `[medium]`

---

## 4. API Gateway → CloudWatch Logs

公式: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-logging.html

前提 (REST API / v1):

- **アカウント単位** で `aws_api_gateway_account.cloudwatch_role_arn` に CloudWatch Logs 書き込み権限を持つ IAM Role が必要

```hcl
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gw_cloudwatch.arn
}
```

前提 (HTTP API / v2):

- v2 は `access_log_settings.destination_arn` だけで動く（account-level role 不要）
- ただし destination の CloudWatch Log Group が存在すること

レビューで確認すること:

- REST API の `aws_api_gateway_stage.access_log_settings` が設定されているのに `aws_api_gateway_account` が無い → `[high]` (ログが silent に出ない)
- v2 API の場合はこのチェック不要（v1 / v2 の区別に注意）
- `aws_api_gateway_account` は AWS アカウント全体で 1 つ。別モジュールで管理されている可能性があるので、見つからない場合は `要追加確認`

---

## 5. RDS Automated Backup

公式: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html

前提:

- `backup_retention_period` のデフォルトは `1`（自動バックアップ有効）
- `backup_retention_period = 0` で明示的に無効化

レビューで確認すること:

- 本番 / ステージング DB で `backup_retention_period = 0` → `[high]` (point-in-time recovery 不可)
- `aws_db_snapshot_copy` や `aws_backup_selection` と `backup_retention_period = 0` の組み合わせ → `[high]`
- 開発環境で明示的に 0 はコスト節約の意図がありうるので環境を確認

---

## 6. VPC Flow Logs

公式: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html

前提:

- `log_destination_type = "cloud-watch-logs"`: `iam_role_arn` に CloudWatch Logs 書き込み権限が必要
- `log_destination_type = "s3"`: destination bucket に書き込み許可 bucket policy が必要

レビューで確認すること:

- CloudWatch Logs 宛なのに `iam_role_arn` が未設定 / 対応 IAM Role に権限が無い → `[high]`
- S3 宛で bucket policy が無い → `要追加確認`（AWS は自動で policy 付与を試みるが、明示 policy がある bucket では上書きされない）

---

## 7. WAF v2 Logging

公式: https://docs.aws.amazon.com/waf/latest/developerguide/logging.html

前提:

- `aws_wafv2_web_acl` 単体ではログが出ない。**別リソース** `aws_wafv2_web_acl_logging_configuration` が必要
- Kinesis Firehose 宛の場合、delivery stream 名は `aws-waf-logs-` prefix が必須

```hcl
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
  resource_arn            = aws_wafv2_web_acl.main.arn
}
```

レビューで確認すること:

- `aws_wafv2_web_acl` が新規追加されているのに `aws_wafv2_web_acl_logging_configuration` が無い → `[medium]`（ログ無しが意図的な場合もある。セキュリティ・監査要件がある環境なら `[high]`）
- Kinesis Firehose 宛で stream 名が `aws-waf-logs-` prefix を持たない → `[high]`

---

## 8. Lambda Permission Prerequisites

### 8a. Event Source Trigger → Lambda Permission

公式: https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html

前提:

- **Push 型** trigger（SNS / S3 / EventBridge / Cognito 等）: `aws_lambda_permission` で呼び出し元 principal を許可
- **Pull 型** trigger（SQS / DynamoDB Streams / Kinesis）: Lambda execution role にソース読み取り権限が必要（`aws_lambda_permission` は不要）

```hcl
# Push 型: SNS → Lambda
resource "aws_lambda_permission" "sns" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.events.arn
}
```

レビューで確認すること:

- Push 型で `aws_lambda_permission` が無い → `[high]`
- Pull 型で execution role に `sqs:ReceiveMessage` / `dynamodb:GetRecords` 等が無い → `[high]`
- Push / Pull の区別を間違えない（SQS は Pull、SNS は Push）

### 8b. Lambda DLQ Permission

公式: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html

前提:

- `dead_letter_config.target_arn` に SNS / SQS を指定する場合、Lambda **execution role** に `sns:Publish` / `sqs:SendMessage` が必要

レビューで確認すること:

- `dead_letter_config` が設定されているのに execution role に送信権限が無い → `[high]` (失敗メッセージが silent に消失)

### 8c. Lambda Async Destinations

前提:

- `aws_lambda_function` だけでは async invocation の destination は設定されない
- `aws_lambda_function_event_invoke_config` の `destination_config` が必要
- destination への送信権限が execution role に必要

レビューで確認すること:

- `destination_config` があるのに execution role に destination への送信権限が無い → `[high]`
- async failure routing が必要なのに `aws_lambda_function_event_invoke_config` が無い → `[medium]`

---

## 9. ECS Task Role vs Execution Role

公式: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html

前提:

- **Task execution role** (`execution_role_arn`): ECS agent がコンテナ起動時に使う。ECR pull, CloudWatch Logs, **Secrets Manager / SSM Parameter Store からの secret 取得**
- **Task role** (`task_role_arn`): コンテナ内アプリが実行中に使う

```hcl
resource "aws_ecs_task_definition" "app" {
  execution_role_arn = aws_iam_role.ecs_execution.arn
  container_definitions = jsonencode([{
    secrets = [{ name = "DB_PASSWORD", valueFrom = "arn:aws:secretsmanager:..." }]
  }])
}
```

レビューで確認すること:

- `secrets` に Secrets Manager / SSM ARN が含まれるのに `execution_role_arn` 未設定 / 対応 role に `secretsmanager:GetSecretValue` / `ssm:GetParameters` が無い → `[high]` (タスク起動失敗)
- `task_role_arn` と `execution_role_arn` が混同されていないか（secrets は execution role 側）

---

## 10. ECS Exec

公式: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html

前提:

- `aws_ecs_service.enable_execute_command = true`
- **Task role** に SSM permissions が必要:

```json
{
  "Action": [
    "ssmmessages:CreateControlChannel",
    "ssmmessages:CreateDataChannel",
    "ssmmessages:OpenControlChannel",
    "ssmmessages:OpenDataChannel"
  ],
  "Resource": "*"
}
```

- task definition の `linuxParameters.initProcessEnabled = true`（推奨）

レビューで確認すること:

- `enable_execute_command = true` なのに task role に `ssmmessages:*` が無い → `[high]`
- `initProcessEnabled` 未設定 → `[medium]` (zombie プロセス蓄積リスク)
- 必要なのは task role（execution role ではない）

---

## 11. Aurora Cluster + Instance

公式: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.CreateInstance.html

前提:

- `aws_rds_cluster` だけでは DB エンドポイントは機能しない
- 少なくとも 1 つの `aws_rds_cluster_instance` が必要

レビューで確認すること:

- `aws_rds_cluster` が新規作成されているのに `aws_rds_cluster_instance` が同一モジュール内に無い → `[high]`
- 既存 cluster への変更で instance が別ファイル / 別モジュールにある可能性 → `要追加確認`

---

## 12. KMS Key Policy

公式: https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html

前提:

- `aws_kms_key` に明示的 `policy` を書いた場合、key を使う IAM entity の Principal が含まれていないと `AccessDenied`
- `policy` 未指定（デフォルト）は root account に全権限委譲するため IAM policy 側で制御可能

レビューで確認すること:

- 明示的 `policy` で key を使う IAM Role / User の Principal が含まれていない → `[high]`
- cross-account / cross-service のケースで不足が多い
- `policy` 未指定（デフォルト）ならこのチェック不要

---

## 13. Route53 ALIAS Record

公式: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html

前提:

- `alias.zone_id` は target resource の **サービス固有 hosted zone ID**（Route53 hosted zone ID ではない）
- 主な値:
  - CloudFront: 常に `Z2FDTNDATAQYW2`
  - ALB/NLB: リージョンごとに異なる（例: `ap-northeast-1` = `Z14GRHDCWA56QT`）
  - S3 website: リージョンごとに異なる

レビューで確認すること:

- `alias.zone_id` が Route53 hosted zone ID と同じ値になっている → `[high]` (DNS 解決されない)
- Terraform 属性参照（`aws_lb.main.zone_id` 等）を使っていれば OK
- ハードコード zone ID が target service / region と一致するか確定できない → `要追加確認`

---

## 14. ALB Target Group Health Check

公式: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html

前提:

- `health_check.path` が HTTP 200-399 を返すこと
- `health_check.port` がアプリの listen port と一致すること

レビューで確認すること:

- `health_check.port` が `"traffic-port"` 以外で、container / instance の listen port と不一致 → `[high]`
- `health_check.path` がカスタムで、アプリ仕様と整合性が確認できない → `要追加確認`
- Terraform レベルでは確定が難しいことが多い。アプリ仕様との突合が必要な場合は `要追加確認`

---

## 15. 汎化ヒューリスティクス

上の 2〜14 に載っていないパターンを見ても「載っていないから素通し」にしない。

**cross-resource dependency の疑いが強いサイン:**

- ある resource が別 resource の ARN / ID を参照しているが、参照先に **permission / policy** 系の resource が存在しない
- 「ログ出力先」「通知先」「destination」系の attribute が設定されているのに、宛先への書き込み権限 resource が無い
- `enable_*` / `*_enabled` 系 attribute が `true` なのに、対応する IAM / policy resource が同一モジュール内に無い
- AWS ドキュメントで "prerequisites" / "required permissions" / "before you begin" セクションが存在するサービス

**手順:**

1. `AWS <Service> <Feature> prerequisites terraform` を Web 検索し、公式ドキュメントで前提の有無を確認する
2. 前提が確認できた場合は、本 reference にパターンとして追記する
3. 確定できない場合は `要追加確認` に寄せる

---

## 16. 要追加確認に寄せるケース

- 参照先リソースが別 repo / 別 terraform state / 手作業管理で、current repo 内に定義が無い
- IAM Role / Policy が module 外で管理されており、権限の有無を確定できない
- `aws_api_gateway_account` のようにアカウント全体で 1 つの設定が別モジュールにある可能性
- アプリケーション仕様との突合が必要（health check path / port 等）
- 環境差（dev / stg / prd）で設定が異なる可能性がある

この場合は:

- `要追加確認: <resource> の前提となる <prerequisite> が対象環境で設定されているか手動確認してください`
