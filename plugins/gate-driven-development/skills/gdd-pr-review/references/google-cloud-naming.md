# Google Cloud Naming Reference

このファイルは `google` / `google-beta` provider を含む Terraform review で使う、v1 の provider-specific naming constraints 参照です。

方針:

- Google Cloud 全体に共通する雑な「予約語一覧」は作らない
- 公式ドキュメントで high-signal に定義されている制約だけを扱う
- unsupported な resource family は `公式ドキュメントでの手動確認が必要` と返す

---

## 1. Cloud Storage bucket names

対象:

- `google_storage_bucket`

公式:

- https://docs.cloud.google.com/storage/docs/buckets

レビューで確認すること:

- bucket 名に docs 明記の禁止語が含まれていないか
  - 自動判定するのは `google` と docs 例示の `g00gle` に限定する
  - それ以外の typo 類推は広げず、必要なら `手動確認が必要` に寄せる
- bucket 名が `goog` prefix で始まっていないか
- dotted-decimal IP address 形式になっていないか
- 文字数
  - 通常は 3-63
  - dot を含む場合は最大 222、ただし各 label は 63 以下
- 先頭と末尾が英数字か
- 使用文字が次だけに収まっているか
  - lowercase letters
  - digits
  - `-`
  - `_`
  - `.`

補足:

- dot を含む bucket 名は domain verification が必要
- グローバル一意性はその場で確認できないので、レビュー結果では `手動確認が必要` と補足する
- bucket 名は公開可視になりやすいので、PII や推測しやすい内部情報を含めない方がよい

---

## 2. Compute Engine naming convention

対象:

- v1 の自動判定は `google_compute_*` に限定する
- それ以外の resource family は、名前が似ていても自動では適用しない

公式:

- https://docs.cloud.google.com/compute/docs/naming-resources

レビューで確認すること:

- 正規表現 `^[a-z]([-a-z0-9]*[a-z0-9])?` に沿うか
- 1-63 文字か
- 先頭が lowercase letter か
- 末尾が letter または digit か
- 使用文字が lowercase letters / digits / hyphen に限定されているか

補足:

- 一意性の単位は location within a project が基本
- VM 名は `vmDnsSetting` が `ZonalOnly` でない場合、project 全体の一意性に注意が必要
- resource ごとに個別例外があり得るので、`google_compute_*` でも docs が別指定している場合はそちらを優先する

---

## 3. 運用ルール

- literal name ならその場で検証する
- local / variable / template で構成される name は、同一モジュール内で追える範囲だけ解決する
- resource family が unsupported なら、無理に NG と断定しない
- 迷ったら `この resource の name 制約は個別 docs で手動確認が必要` と返す
