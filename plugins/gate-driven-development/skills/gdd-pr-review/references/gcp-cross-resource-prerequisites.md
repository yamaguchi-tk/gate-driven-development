# GCP Cross-Resource Prerequisite Reference

このファイルは GCP リソースの cross-resource dependency（リソース A が機能するためにリソース B の設定・権限が必要）の参照です。

方針:

- `terraform plan` も `terraform apply` も通るが、実行時に **silent-failure** になるパターンに限定する
- 同一モジュール基本単位で前提の有無を追い、確定できない場合は `要追加確認` に寄せる

---

## 1. 対象

| Trigger resource | チェックセクション |
|---|---|
| `google_logging_project_sink` / `google_logging_folder_sink` / `google_logging_organization_sink` | §2 |
| `google_iam_workload_identity_pool` / `google_iam_workload_identity_pool_provider` | §3 |
| `google_artifact_registry_repository` | §4 |

---

## 2. Cloud Logging Sink

公式: https://cloud.google.com/logging/docs/export/configure_export_v2

前提:

- `google_logging_project_sink` を作成すると `writer_identity` が自動生成される
- この identity に destination への書き込み権限を **明示的に付与** する必要がある

destination 別の必要権限:

- BigQuery: `roles/bigquery.dataEditor` on dataset
- Cloud Storage: `roles/storage.objectCreator` on bucket
- Pub/Sub: `roles/pubsub.publisher` on topic

```hcl
resource "google_logging_project_sink" "audit" {
  name        = "audit-sink"
  destination = "bigquery.googleapis.com/projects/my-project/datasets/audit_logs"
}

resource "google_bigquery_dataset_iam_member" "sink_writer" {
  dataset_id = google_bigquery_dataset.audit_logs.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.audit.writer_identity
}
```

レビューで確認すること:

- `google_logging_project_sink` があるのに `writer_identity` への IAM 付与が同一モジュール内に無い → `[high]` (ログが destination に届かない)
- `unique_writer_identity = false` ではデフォルト service account が使われる。destination が別プロジェクトの場合は権限不足になりやすい

---

## 3. Workload Identity Federation

公式: https://cloud.google.com/iam/docs/workload-identity-federation

前提:

3 つのリソースが揃って初めて機能する:

1. `google_iam_workload_identity_pool` — pool 作成
2. `google_iam_workload_identity_pool_provider` — provider (OIDC / SAML / AWS) を pool に紐付け
3. `google_service_account_iam_binding` (or `_member`) — service account に `roles/iam.workloadIdentityUser` を付与

```hcl
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
}
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  oidc { issuer_uri = "https://token.actions.githubusercontent.com" }
}
resource "google_service_account_iam_member" "github_wif" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/..."
}
```

レビューで確認すること:

- pool があるのに provider が無い → `[high]` (認証できない)
- pool + provider があるのに `roles/iam.workloadIdentityUser` の binding が無い → `[high]` (impersonation で AccessDenied)
- 3 つ揃っていても `attribute_condition` が緩すぎないか → `[medium]`（セキュリティ観点）

---

## 4. Artifact Registry Permissions

公式: https://cloud.google.com/artifact-registry/docs/access-control

前提:

- `google_artifact_registry_repository` を作成しただけでは pull 権限は自動付与されない（デフォルト service account に付いている場合はある）
- **カスタム service account** を使っている Cloud Run / GKE では明示的な IAM 付与が必要

```hcl
resource "google_artifact_registry_repository_iam_member" "reader" {
  repository = google_artifact_registry_repository.app.name
  location   = google_artifact_registry_repository.app.location
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.cloud_run.email}"
}
```

レビューで確認すること:

- 新規 repo + カスタム service account で `artifactregistry.reader` 付与が無い → `[medium]` (runtime で image pull 失敗)
- デフォルト service account 使用の場合は通常問題ない → `要追加確認`
- cross-project の場合は IAM 付与が確実に必要 → `[high]`

---

## 5. 汎化ヒューリスティクス

上の 2〜4 に載っていないパターンでも「載っていないから素通し」にしない。

**cross-resource dependency の疑いが強いサイン:**

- `google_*_iam_member` / `google_*_iam_binding` が無いのに、あるリソースが別リソースの出力先 / 参照先になっている
- `writer_identity` / `service_account` が自動生成されるリソースで、destination 側への権限付与が無い
- 公式ドキュメントに "Grant the service account access to..." / "Before you begin" セクションが存在するサービス

---

## 6. 要追加確認に寄せるケース

- destination / 参照先リソースが別プロジェクト / 別 repo で管理されている
- デフォルト service account の権限で十分か確定できない
- カスタム service account の使用有無が同一モジュール内で確認できない

この場合は:

- `要追加確認: <resource> の前提となる <prerequisite> が対象プロジェクトで設定されているか手動確認してください`
