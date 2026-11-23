state.md 確認：
- **系統 A**: `Resume From=human-check-waiting` ✓
- **系統 B**: subagent output に human-check テンプレート + `<gdd-stop reason="human-check-waiting">` ✓

---

## 🔍 確認をお願いします

### 30秒判断（まず見るところ）

**なぜやるか（WHY・根本原因）**: STG の画像変換ジョブの出力先が EC2 のローカルディスクのままだと、インスタンスの入れ替えで出力が消え、後段の配信処理が参照できない。S3 バケットへ出力先を移し、配信処理から同じパスで参照できる状態にする。

**整理した要件**: 対象は STG 環境のみ。出力先を `local`（ローカルディスク）→ `s3`（S3 バケット）に切り替えることが必須要件で、変換ジョブのスクリプト本体（別 repo）の変更は今回のスコープに含めない前提で整理した。

**実装する方法・内容**: 対象 repo は `example-app-infra`（Terraform）。既存 module `image_convert_job` を流用し、出力先の設定（`output_conf`）を `type=local` → `type=s3` + prefix=`s3://stg-example-image-output/converted` へ差し替える。新 module は作らない（KISS・rollback 容易）。

**変更予定ファイル（WHERE）**:
- `example-app-infra/modules/image_convert_job/main.tf`: `output_conf` の `type=local` → `type=s3` 切替、prefix 追加
- `example-app-infra/modules/image_convert_job/variables.tf`: 新バケット名の変数追加
- `example-app-infra/envs/stg/image_output.tf`: 新規 S3 バケット追加、ジョブ実行ロールへの S3 権限付与、不要なローカルボリューム権限の削除
- 対応 AC: AC-1（出力先切替）/ AC-3（IAM 最小化）

**検証する方法・内容**: 設計面（新 bucket/IAM/conf）はコード diff + `terraform plan`（apply 前）で確認する。動作面（初回の再変換/増分/配信処理からの参照）は apply 後にジョブを実行し、ジョブのログ・S3 のオブジェクト件数・配信処理の応答で確認する（post-merge verification）。本 repo にユニットテスト基盤は無いため external evidence で検証する。

**どこまで自走するのか**: OK で進む範囲は Terraform 変更（module + env/stg）、`terraform plan` 作成・差分提示、PR 作成までです。`terraform apply` / ジョブ実行（再変換）/ S3 への実書き込み等の AWS write は 1 操作ごとに別途明示承認が必要で、merge / PRD 適用も対象外です。cross-repo の script 変更が必須と判明した場合、PRD への波及が生じた場合、旧ローカルディスクの撤去が必要になった場合、新たな機密データが発生した場合は人間に戻します。

### 判断ポイント（OK / 別案希望 で回答してください）

**Q1. scope（cross-repo 分解）**
本 GDD を Terraform repo の変更に限定し、変換ジョブのスクリプト（`example-app-worker`）は無変更で実行検証→必要時のみ別 steering、で良いか？

**Q2. 方針（旧リソース残置）**
旧ローカルディスクのボリューム（`aws_ebs_volume`）は destroy せず残置（切り戻し先）で良いか？

### 段階実装
- **S-1**（今回 PR）: Terraform 変更（新 bucket/conf/IAM）+ `terraform plan` 差分提示
- **S-2**（post-merge、都度承認）: apply 後の初回の再変換 + オブジェクト件数の検証

<gdd-stop reason="human-check-waiting">
