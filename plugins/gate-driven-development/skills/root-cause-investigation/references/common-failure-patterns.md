# Common Failure Patterns

multi-stage / multi-component なシステムで頻出する failure パターンをカタログ化したもの。`root-cause-investigation` Phase 2「Pattern Analysis」で「似たような壊れ方をどこかで見たことがあるか」を素早く照合する用途。

これらは「root cause を当てるためのチートシート」ではなく、**仮説の発想元**として使う。確定させるには Phase 3 の hypothesis testing が必要。

## 使い方

1. 症状を 1 行で書き出す（例: 「Lambda が prod でだけ AccessDenied で落ちる」）
2. このカタログから「同じ shape の症状」を探す
3. 該当パターンの **typical root cause** を仮説として記録する
4. 該当パターンの **proving probe** を実行して仮説を検証する
5. 該当しなければ Phase 1 の証跡収集に戻る

## カタログ

### 1. Env 変数の伝播ロス

- **症状**: ローカル / dev では動くが、CI / prod で「env var unset」「empty config」エラー。設定したはずの値が読まれていない
- **典型的 root cause**:
  - secret store → CI runner への inject 漏れ（scope / branch 制限）
  - shell 階層で `set -a` / `export` が掛かっていない
  - container 起動時に `--env-file` が読まれていない
  - lambda の env が IaC で deploy 時に上書きされる
- **proving probe**: 各 layer の入口で `env | grep VAR_NAME || echo UNSET` を 1 行ずつ出力（`scripts/verify-env-propagation.sh` を使う）。最初に UNSET になった layer が境界
- **fix の方向**: ロストしている境界に対して `--env` / `secrets` / `env_from` の宣言を追加。masking のため値は出さない

### 2. 認証 token の期限切れ / scope ずれ

- **症状**: 「最初の数分は動くが時間が経つと 401 / 403」「特定の operation だけ deny される」「再実行すると 1 回目だけ通る」
- **典型的 root cause**:
  - OIDC token の expiry（短命 token を long-running job で使い回している）
  - STS AssumeRole の session duration を超えた
  - service account の権限が PR で変更されたが古い token が残っている
  - scope（IAM action / OAuth scope）が想定より狭い
- **proving probe**: 失敗時刻の token 取得時刻を比較。`aws sts get-caller-identity` で現在の identity を確認。403 のレスポンス body に encoded reason があれば `aws sts decode-authorization-message` で復号
- **fix の方向**: refresh / re-assume を入れる、または long-running 処理を分割

### 3. Timing 依存（race condition / eventual consistency）

- **症状**: 「数回再実行すると 1 回成功する」「ローカルでは絶対起きないが CI で散発」「sleep 入れたら直る」
- **典型的 root cause**:
  - eventual consistency（S3, DynamoDB GSI, IAM 更新の伝播遅延）
  - 同時起動 process の DB / file lock 競合
  - 非同期処理の完了待ちが不在
  - test の teardown が前 test の cleanup と被る
- **proving probe**: 再現率を 5/5 / 3/5 / 1/5 で計測。sleep 注入で直るか確認（直る = timing 依存の強い証拠）。「同じ resource を別 process が触っていないか」を access log で確認
- **fix の方向**: sleep ではなく condition-based wait（polling / event subscription）。race の場合は lock or idempotent retry
- **詳細 recipe**: `condition-based-waiting.md`（固定 sleep の 5 anti-pattern + 決定的待機 recipe + timeout 設計 + 100 回連続実行検証）。test の teardown 由来汚染なら `scripts/find-polluter.sh` で polluter 特定

### 4. Quota / rate limit

- **症状**: 「ある時間帯だけ ThrottlingException」「テスト並列度を上げると失敗率が増える」「夜間バッチで散発」
- **典型的 root cause**:
  - service quota（AWS service limit, third-party API rate limit）に到達
  - burst 設定が caller 側で守られていない
  - account 全体で共有しているリソースを他チームが使い切る
- **proving probe**: error response の `Retry-After` / `X-Ratelimit-*` header を確認。AWS なら `aws service-quotas list-service-quotas` で上限値。failure 時刻と request 数の相関グラフ
- **fix の方向**: backoff + jitter + retry。それでも詰まるなら quota 引き上げ申請

### 5. DNS / network 解決失敗

- **症状**: 「Name or service not known」「Connection timed out」「特定リージョン / VPC からだけ失敗」
- **典型的 root cause**:
  - private DNS / private link の設定漏れ
  - security group / NACL で outbound が閉じている
  - VPC endpoint がなく NAT 経由しようとして経路が無い
  - DNS resolver が古い（TTL 過剰）
- **proving probe**: `dig <domain>` / `nslookup <domain>` を各 layer で実行。`curl -v` で connection attempt の詳細。`traceroute` で経路。VPC なら `aws ec2 describe-security-groups` / `describe-network-acls`
- **fix の方向**: 経路設定を直す。一時しのぎで `/etc/hosts` を編集しない（再発する）

### 6. Serialization / schema mismatch

- **症状**: 「producer 側は OK、consumer で deserialization error」「ある fields だけ null として届く」「特定の値だけ encoding 壊れる」
- **典型的 root cause**:
  - producer と consumer の schema version 不一致（一方を deploy したがもう一方が古い）
  - JSON / protobuf / Avro の optional field を required で扱っている
  - encoding（UTF-8 vs Latin-1）の不一致
  - 数値の overflow（int32 vs int64）
- **proving probe**: 失敗 message の raw bytes を hex dump。producer / consumer 双方の schema version を確認。両側の library version を確認
- **fix の方向**: schema を backward compatible に保つ。breaking change は producer / consumer のリリース順序を強制

### 7. Permission denied（IAM / RBAC / file system）

- **症状**: 「AccessDenied」「permission denied」「403 Forbidden」が特定 operation でだけ
- **典型的 root cause**:
  - IAM policy の Resource / Action / Condition が必要なものを許可していない
  - role chain（assume role の連鎖）で session policy が狭めている
  - file system permission が container user と合っていない
  - S3 bucket policy / KMS key policy の二重承認漏れ
- **proving probe**: AWS なら `aws sts decode-authorization-message` で deny 理由を復号。IAM Access Analyzer / policy simulator で同じ principal + action + resource を simulate。`ls -la` で file 権限
- **fix の方向**: 最小権限を意識しつつ、足りない Action / Resource を追加
- **多層防御の設計**: auth boundary に触れる修正は `defense-in-depth.md` § 5 層モデル + fix を当てる層の選び方（security boundary 違反は層 1+2+4+5 必須）を参照

### 8. キャッシュの stale 化

- **症状**: 「ローカルでは新しい挙動、デプロイ後も古いまま」「user A は新、user B は旧」「ブラウザを更新すると直る」
- **典型的 root cause**:
  - CDN cache の TTL が長すぎる / invalidation 漏れ
  - application 内の in-memory cache が deploy 跨ぎで残っている
  - DB query cache / ORM cache
  - browser cache（特に `Cache-Control` の `immutable` 指定）
- **proving probe**: response header の `cache-control` / `x-cache` / `age` を確認。同じ request を curl で複数回投げてレスポンスが変わるか。CDN の hit rate を見る
- **fix の方向**: 該当 cache を invalidate / TTL 短縮 / cache key に version を含める

### 9. Library / runtime version mismatch

- **症状**: 「同じコードがローカル OK、CI / prod で違うエラー」「dependency 更新後に挙動が変わった」「ある関数だけ挙動が違う」
- **典型的 root cause**:
  - lock file（package-lock.json / Pipfile.lock）が同期されていない
  - runtime version（Node / Python / Java）の minor 差で挙動が変わる
  - native binary の glibc / OpenSSL version 差
  - transitive dependency の major bump
- **proving probe**: 各環境で `node -v && npm ls --depth=0` / `python --version && pip freeze` を出力して diff。lock file が commit されているか確認
- **fix の方向**: lock を厳格化。Docker で base image を pin（`:latest` を使わない）

### 10. Silently swallowed error

- **症状**: 「明らかに動いていないのに log に error が無い」「success と返すが後続が空」「test PASS だが副作用が起きない」
- **典型的 root cause**:
  - `try / except: pass` または `catch (e) { /* ignore */ }`
  - logger level が低くて error が出ない
  - fire-and-forget 非同期処理が失敗を握り潰す
  - 戻り値が unused（`Result` / `Error` を ignore）
- **proving probe**: 該当処理に `print` / `log.error` を直接挿入して再現。logger 設定を確認。code 内で `except` / `catch` を grep
- **fix の方向**: ignore せず最低限 log を出す。error を propagate するか handler を明示

### 11. Feature flag / config の不一致

- **症状**: 「user A だけ新機能、user B には来ない」「特定環境でだけ無効化されている」「config 上は true だが挙動が false」
- **典型的 root cause**:
  - flag service の cache（ローカルの flag SDK が更新を pull していない）
  - user segmentation の条件が想定外
  - config の override 階層（env > file > default）で別の値が勝つ
  - flag 評価の typo / spelling 揺れ
- **proving probe**: 該当 user / 該当環境での flag 評価結果を直接 dump（SDK の debug mode）。config の最終的な merged 値を起動時に出力
- **fix の方向**: flag service の audit log を確認。flag 名を一元管理して typo を防ぐ

### 12. Timezone / locale バグ

- **症状**: 「集計値が 1 日ずれる」「夜間にだけ失敗」「特定 user の date 表示が変」「DST 切り替えで挙動が変わる」
- **典型的 root cause**:
  - server / DB / application の TZ 設定不一致（UTC / local / user TZ が混在）
  - naive datetime（tz info 無し）と aware datetime の演算
  - DST の handling 漏れ
  - locale が `C` / `POSIX` で format が想定と違う
- **proving probe**: 各 layer で `date -u` と `date` を両方出力。DB の `SHOW VARIABLES LIKE 'time_zone'`。application の `datetime.now()` vs `datetime.now(tz=UTC)`
- **fix の方向**: 全 layer を UTC に統一。表示 layer でだけ user TZ に変換

### 13. ストレージ満杯 / 一時領域 exhaustion

- **症状**: 「No space left on device」「inode exhausted」「特定 host だけで起きる」
- **典型的 root cause**:
  - `/tmp` に大量ファイルが残る（cleanup 漏れ）
  - container の writable layer が膨らむ
  - log rotation 設定なし
  - lambda の `/tmp` （512MB）を超えるダウンロード
- **proving probe**: `df -h` / `df -i` を各 host / container で実行。`du -sh /tmp/* | sort -h` で大きい file 特定。CloudWatch の disk metric
- **fix の方向**: cleanup を実装。`/tmp` ではなく S3 等の外部 storage を使う

### 14. 静的型 / runtime 型の不一致

- **症状**: 「TypeScript / mypy では通るが runtime で TypeError」「JSON parse 後の値が想定と違う型」「null チェック漏れ」
- **典型的 root cause**:
  - 外部 API の response 型を信用しすぎ（schema 不一致）
  - JSON 数値が string で返ってくる
  - DB driver が `Decimal` で返すが code は `float` 想定
  - optional / nullable の handling 漏れ
- **proving probe**: 失敗箇所で `type(value)` / `typeof value` を log。response の raw を一度保存して再現
- **fix の方向**: 境界で runtime validation（zod / pydantic 等）。API の schema を契約として固定

### 15. Concurrent modification（書き込み競合）

- **症状**: 「複数 worker が同じ resource を更新して内容が消える」「ConditionalCheckFailedException」「Last write wins で履歴が飛ぶ」
- **典型的 root cause**:
  - 楽観的ロック（version / etag）なしで update
  - 同じ key への複数 producer
  - distributed lock の TTL 不足
- **proving probe**: 競合 resource への write を時系列でログ。version mismatch エラーが出ているか確認
- **fix の方向**: 楽観的ロック / 行ロック / event sourcing。merge 戦略を明示

## カタログの拡張ルール

新しいパターンを追加する場合は以下を満たすこと:

1. **症状が再現可能で具体的**: 「動かない」ではなく「特定条件で特定 error」
2. **典型的 root cause を 3-5 個列挙**: 1 つだけは specificity 不足
3. **proving probe が実行可能**: コマンドかコードで書く
4. **fix の方向は方針のみ**: 具体的修正はケースごとに違うので方向だけ

## 関連 references

- `multi-layer-probing.md` — 各 layer での probe コマンド集（パターン 1 / 5 / 7 等の境界証跡）
- `call-stack-tracing.md` — 深い call stack で悪い値の source を遡る（パターン 6 / 10 / 14 の追跡）
- `condition-based-waiting.md` — 固定 sleep の anti-pattern と決定的待機 recipe（パターン 3 の詳細）
- `defense-in-depth.md` — 多層 validation 設計（パターン 7 / 10 の再発防止、security boundary 違反は層 1+2+4+5 必須）
- `scripts/verify-env-propagation.sh` — パターン 1 の最小チェック
- `scripts/find-polluter.sh` — テスト汚染源（test pollution）の特定。パターン 3 の test teardown 由来汚染に使う
