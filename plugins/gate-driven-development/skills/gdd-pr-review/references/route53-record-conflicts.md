# AWS Route53 Record Conflict Reference

このファイルは `aws_route53_record` を含む Terraform review で使う、v1 の Route53 record conflict 参照です。

方針:

- Route53 全体の制約を広く持たず、誤検知しにくい高シグナルな `CNAME` conflict に絞る
- current branch の最終状態を見るだけでなく、`base:` がある場合は base 側の元コードも使って、今回の変更で持ち込んだ問題かを切り分ける
- zone や record 名を確定できない場合は断定せず `要追加確認` に寄せる

---

## 1. 対象

- `aws_route53_record`

優先して確認すること:

- 同一 `hosted_zone_id` 相当の範囲で、正規化後の `name` が一致する record
- そのうち `type = "CNAME"` を含む組み合わせ

正規化ルール:

- record `name` は末尾の `.` を取り除いて比較する
- `name` が local / variable / template から構成される場合は、同一モジュール内で追える範囲だけ解決する

---

## 2. CNAME conflict

公式:

- https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ResourceRecordTypes.html#CNAMEFormat

レビューで確認すること:

- 同じ zone 内に、同じ `name` の `CNAME` が複数ないか
- 同じ zone 内に、同じ `name` の `CNAME` と別 type が同居していないか

解釈:

- 新しい `CNAME` を追加する変更なら、同名の既存 record がないかを見る
- 新しい非 `CNAME` record を追加する変更でも、同名の既存 `CNAME` があれば conflict とみなす

---

## 3. PR / `base:` 文脈

`base:` がある場合のルール:

- current branch の最終状態だけで断定しない
- base 側の元コードも見て、衝突が今回の変更で新規導入されたか、既存問題かを切り分ける
- base 側にすでに同じ conflict があり、今回の変更が悪化させていないなら current PR の `high` finding にはしない
- base 側に record が 1 件だけあり、current branch で同名 `CNAME` や同名別 type を追加しているなら `high` finding

---

## 4. `要追加確認` に寄せるケース

- `hosted_zone_id` の最終値を確定できない
- `name` の最終形を同一モジュール内で解決できない
- module / `for_each` / map key などの展開結果をその場で確定できない
- zone をまたいだ record 集約の仕組みがあり、repo 内の 1 hop では全体像が見えない

この場合は、無理に NG と断定せず次のように返す:

- `要追加確認: hosted zone と record 名の最終形を手動確認してください`
