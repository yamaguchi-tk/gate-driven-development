# CloudWatch Metric / Alarm Prerequisite Reference

このファイルは `aws_cloudwatch_metric_alarm` / `aws_cloudwatch_composite_alarm` / `aws_cloudwatch_dashboard` / `aws_cloudwatch_log_metric_filter` を含む Terraform review で使う、v1 の CloudWatch metric prerequisite 参照です。

方針:

- CloudWatch 全体の雑な制約を広く持たず、**対象 AWS 側リソースで明示有効化しないと publish されない feature-gated メトリクス** に絞る
- `treat_missing_data = "notBreaching"` と組み合わさると、本番で silent-failure（一度も発報しない）を起こす点を重く見る
- dimension から対象リソース定義を同一モジュール基本単位で追い、確定できない場合は `要追加確認` に寄せる

---

## 1. 対象

- `aws_cloudwatch_metric_alarm` の `metric_name` / `namespace`、または `metric_query` 内の `metric { namespace metric_name }`
- `aws_cloudwatch_composite_alarm` の参照先アラーム（間接的に feature-gated メトリクスを踏んでいないか）
- `aws_cloudwatch_dashboard` の JSON body に含まれる `namespace` / `metric`
- `aws_cloudwatch_log_metric_filter`（前提 log group が対象機能の出力先になっているか）

優先して確認すること:

- 差分内に現れる `namespace = "..."` / `metric_name = "..."` のうち、下の 2〜6 の分類に該当するもの
- 該当した場合の dimension の識別子（`ClusterName` / `DBInstanceIdentifier` / `InstanceId` 等）
- その識別子が指す先の Terraform リソース定義（同一モジュール基本、必要なら 1 hop）

---

## 2. ECS Container Insights

公式:

- https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-ECS-cluster.html

Namespace: `ECS/ContainerInsights`
代表メトリクス: `RunningTaskCount`, `DesiredTaskCount`, `PendingTaskCount`, `TaskCount`, `CpuUtilized`, `MemoryUtilized`, `EphemeralStorageUtilized`, `NetworkRxBytes`, `StorageReadBytes` 等

前提 Terraform 設定:

```hcl
resource "aws_ecs_cluster" "foo" {
  setting {
    name  = "containerInsights"
    value = "enabled"  # または "enhanced"
  }
}
```

レビューで確認すること:

- 対象クラスターの `setting` が `disabled` / 未設定なら `[high]` finding
- `enabled` / `enhanced` なら OK
- Task レベル詳細メトリクス（`EphemeralStorageUtilized` 等）は `enhanced` が要る
- `AWS/ECS` namespace の `CPUUtilization` / `MemoryUtilization`（Service 単位）は Container Insights 無しでも publish されるので混同しない。namespace ごと確認する

---

## 3. RDS Performance Insights

公式:

- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.html

Namespace: `AWS/RDS`
代表メトリクス: `DBLoad`, `DBLoadCPU`, `DBLoadNonCPU`, `DBLoadRelativeToNumVCPUs`

前提 Terraform 設定:

```hcl
resource "aws_db_instance" "foo" {
  performance_insights_enabled          = true
  performance_insights_retention_period = 7    # 7 または 731
}
```

レビューで確認すること:

- `performance_insights_enabled` が `false` / 未設定（= default false）なら `[high]` finding
- Aurora は `aws_rds_cluster` 側に同じ属性がある
- Performance Insights と Enhanced Monitoring は別物。`DBLoad*` 以外の DB 標準メトリクスは Performance Insights 無しでも publish される

---

## 4. RDS Enhanced Monitoring

公式:

- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html

対象: OS レベルメトリクス（`RDSOSMetrics` ロググループに JSON で送信。CloudWatch Metrics として直接参照するには `aws_cloudwatch_log_metric_filter` で metric 化する必要がある）

前提 Terraform 設定:

```hcl
resource "aws_db_instance" "foo" {
  monitoring_interval = 60   # > 0
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
}
```

レビューで確認すること:

- `aws_cloudwatch_log_metric_filter` が `RDSOSMetrics` ロググループを参照しているのに `monitoring_interval = 0` / 未設定なら `[high]` finding
- `monitoring_interval > 0` なのに `monitoring_role_arn` が空なら Terraform 自体のバリデーションで落ちる想定だが、一応確認する

---

## 5. EC2 Detailed Monitoring

公式:

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-cloudwatch-new.html

Namespace: `AWS/EC2`
対象: 1 分粒度メトリクス（デフォルトは 5 分粒度）

前提 Terraform 設定:

```hcl
resource "aws_instance" "foo" { monitoring = true }
# または Launch Template 側
resource "aws_launch_template" "foo" {
  monitoring { enabled = true }
}
```

レビューで確認すること:

- `AWS/EC2` namespace のアラームで `period < 300` を指定しているのに、対象インスタンスで Detailed Monitoring が有効化されていない場合は `[high]` finding。MISSING / INSUFFICIENT_DATA が頻発する
- `period = 300` 以上なら Detailed Monitoring 不要

---

## 6. API Gateway Detailed / Execution Metrics

公式:

- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-metrics-and-dimensions.html

Namespace: `AWS/ApiGateway`
前提付きメトリクス: method 単位の詳細メトリクス（`IntegrationLatency` などを Method dimension で取るケース）、`CacheHitCount` / `CacheMissCount`、`ExecutionError` の method 粒度

前提 Terraform 設定:

```hcl
resource "aws_api_gateway_method_settings" "foo" {
  rest_api_id = aws_api_gateway_rest_api.foo.id
  stage_name  = aws_api_gateway_stage.foo.stage_name
  method_path = "*/*"
  settings {
    metrics_enabled    = true
    data_trace_enabled = true
  }
}
```

`aws_apigatewayv2_stage`（HTTP/WebSocket API）側は `default_route_settings { detailed_metrics_enabled = true }`。

レビューで確認すること:

- Method / Resource dimension を取るアラームで `metrics_enabled` / `detailed_metrics_enabled` が有効化されていなければ `[high]` finding
- キャッシュメトリクスを参照しているなら `aws_api_gateway_method_settings.settings.caching_enabled = true` も必要

---

## 7. WAF (v2) CloudWatch metrics

公式:

- https://docs.aws.amazon.com/waf/latest/developerguide/monitoring-cloudwatch.html

Namespace: `AWS/WAFV2`
代表メトリクス: `BlockedRequests`, `AllowedRequests`, `CountedRequests`, `PassedRequests`

前提 Terraform 設定:

```hcl
resource "aws_wafv2_web_acl" "foo" {
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "foo-web-acl"
    sampled_requests_enabled   = true
  }
  rule {
    # 各 rule 側にも visibility_config が要る
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "foo-rule"
      sampled_requests_enabled   = true
    }
  }
}
```

レビューで確認すること:

- `AWS/WAFV2` のアラームで対象 WebACL または rule 側で `cloudwatch_metrics_enabled = false` / 未設定なら `[high]` finding
- rule ごとにも `visibility_config` が要る点を忘れがち

---

## 8. S3 Request Metrics

公式:

- https://docs.aws.amazon.com/AmazonS3/latest/userguide/metrics-dimensions.html

Namespace: `AWS/S3`
対象: Request Metrics（`AllRequests`, `GetRequests`, `PutRequests`, `4xxErrors`, `5xxErrors` 等）はオプトイン。Storage Metrics（`BucketSizeBytes`, `NumberOfObjects`）はデフォルトで publish される

前提 Terraform 設定:

```hcl
resource "aws_s3_bucket_metric" "foo_requests" {
  bucket = aws_s3_bucket.foo.id
  name   = "EntireBucket"   # filter 無しなら bucket 全体
}
```

レビューで確認すること:

- `AWS/S3` の Request 系メトリクス（`AllRequests` など）を参照するアラームで、対象バケットに `aws_s3_bucket_metric` が無ければ `[high]` finding
- Storage Metrics（`BucketSizeBytes` 等）には前提不要なので `[high]` にしない

---

## 9. Lambda Insights

公式:

- https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Lambda-Insights.html

Namespace: `LambdaInsights`
代表メトリクス: `cpu_total_time`, `memory_utilization`, `rx_bytes`, `tx_bytes`, `init_duration`

前提 Terraform 設定:

- 対象 Lambda の `layers` に Lambda Insights Extension Layer ARN（`arn:aws:lambda:<region>:<lambda-insights-public-account-id>:layer:LambdaInsightsExtension:<ver>`）
- `role` に `CloudWatchLambdaInsightsExecutionRolePolicy` がアタッチされている

レビューで確認すること:

- `LambdaInsights` namespace のアラームで、対象関数に Insights extension layer も IAM も無ければ `[high]` finding

---

## 10. ALB / NLB Access Log 由来メトリクス

公式:

- https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html

対象: Access Log を `aws_cloudwatch_log_metric_filter` でメトリクス化するケース（ALB/NLB 自体の標準メトリクス `TargetResponseTime` 等は前提不要）

前提 Terraform 設定:

```hcl
resource "aws_lb" "foo" {
  access_logs {
    bucket  = aws_s3_bucket.access_logs.id
    enabled = true
  }
}
```

レビューで確認すること:

- `aws_cloudwatch_log_metric_filter` が ALB/NLB access log を参照しているのに `access_logs.enabled = false` なら `[high]` finding

---

## 11. CloudWatch Agent / カスタムメトリクス

Namespace: `CWAgent`（デフォルト。`metrics_namespace` で変更可）または任意のカスタム namespace
代表メトリクス: `mem_used_percent`, `disk_used_percent`, `procstat_*` 等

前提:
対象 EC2 / ECS / オンプレに CloudWatch Agent 相当がデプロイされ、収集設定が入っていること。Terraform 外のことが多い。

レビューで確認すること:

- `CWAgent` namespace または AWS SDK に存在しない custom metric を参照しているアラームを見たら、CloudWatch Agent / サイドカー / ユーザー側 publisher のデプロイ状況を `要追加確認` に寄せて Medium finding にする
- Terraform 側で SSM Association / Launch Template user_data などでエージェント導入している痕跡が同一モジュール基本で見つかれば OK

---

## 12. v1 未掲載パターンの扱い（汎化ヒューリスティクス）

上の 2〜11 に載っていない metric / namespace を見ても、「載っていないから素通し」にしない。同じクラスの silent-failure は今後も新しい AWS サービスで増え続けるため、次のヒューリスティクスで feature-gated かどうかを判定する。

**feature-gated の疑いが強いサイン:**

- namespace が `AWS/<Service>` ではなく、サービス名スラッシュ派生（`ECS/ContainerInsights`, `AWS/States/<Type>`, `LambdaInsights`, `Route53Resolver/<...>` 等）になっている
- metric 名に `Insights` / `Enhanced` / `Detailed` / `Advanced` / `Request*` のような「オプション機能っぽい」語が入っている
- 公式 doc で metric 一覧が「基本 (always on)」と「オプション機能時のみ」に分割して記載されている
- dimension が通常の Service / Resource だけでなく、`FeatureName` / `ConfigurationId` 等のオプション前提のものを取っている
- AWS Console 上で該当メトリクスを有効化するためのトグル・オプション設定が存在する（= Terraform でも対応する属性があるはず）

**手順:**

1. `AWS <Service> <MetricName> prerequisite` / `enable` / `optional` を Web 検索し、公式ドキュメントで前提の有無を確認する
2. 前提が確認できた場合は、そのメトリクスとその前提設定を本 reference にパターンとして追記する（`case-studies` 運用と同じで、見逃し予防は蓄積してこそ働く）
3. 公式で前提が明示されていない / 確定できない場合は、無理に NG と断定せず `要追加確認` に寄せる

**よくある落とし穴:**

- 「`AWS/<Service>` namespace だから前提不要」と短絡しないこと。API Gateway や WAF のように、同 namespace でも一部メトリクスだけオプション、ということがある
- 「STG で動いているから PRD でも動くはず」と環境横展開を素通ししないこと。feature 有効化状態が env 間で違うことは実際にある（case-studies 参照）

---

## 13. `treat_missing_data` の扱い

前提条件未達が疑われるアラームでは `treat_missing_data` の値をセットで見る。

- `notBreaching` — 「正常扱い」される。**silent-failure を隠す最悪の組み合わせ**。前提未達 + `notBreaching` は必ず `[high]` finding で強調する
- `breaching` — 「アラーム扱い」される。誤発報は多いが気付く
- `ignore` — 直前状態を保つ。初期が OK 判定だと発報しない
- `missing` — INSUFFICIENT_DATA に落ちる。ダッシュボードで視認できる

---

## 14. `要追加確認` に寄せるケース

- dimension の識別子（`ClusterName` / `DBInstanceIdentifier` 等）が動的に組み立てられ、同一モジュール基本単位で最終値を確定できない
- 対象リソースが別 repo / 別 terraform state / 手作業管理で、current repo 内に定義が無い
- CloudWatch Agent / 外部 publisher のデプロイ状況が Terraform の守備範囲外
- メトリクス名 / namespace が v1 でサポートしていない新機能（AWS 新サービス等）に由来する

この場合は、無理に NG と断定せず次のように返す:

- `要追加確認: <namespace>/<metric_name> の publish 元（<feature>）が対象リソースで有効化されているか手動確認してください`
