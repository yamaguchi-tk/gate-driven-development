# Debug Triage

デバッグの第 1 ステップ。症状の種別を特定し、正しいデバッグ入口へ振り分ける。
テスト RED だけを対象にしない — 症状のレイヤーが違えば根本原因も入口も変わる。

## 症状別 分岐表

| 症状 | 特徴 | 最初にやること | 入口 |
|------|------|---------------|------|
| **Test RED** | 実行可能なテストが失敗。Expected / Actual が取れる | テスト再現・stack trace 確認 | `gdd-test-failure-debug-pack` → `gdd-systematic-debugging` |
| **Silent failure（無反応）** | サービス / bot が一切応答しない。テストが「応答なし」「timeout」で fail | [インフラ層チェック](#インフラ層チェック) を先に実施 | `gdd-systematic-debugging` 直行 |
| **Wrong output（出力異常）** | 応答はあるが内容が期待と違う | contract / prompt 期待値の確認 | `gdd-systematic-debugging` |
| **Expected side effect missing** | テストが PASS に見えたが期待する副作用（PR 作成・open 等）が起きていない | [副作用実態確認](#副作用実態確認) を先に実施 | `gdd-systematic-debugging` |
| **Partial response（途中停止）** | 応答が来た後に止まる。timeout / polling で詰まっている疑い | タイムアウト設定・ポーリング上限の確認 | `gdd-systematic-debugging` |

## インフラ層チェック

**silent failure（無反応）の場合に最初に確認する。**

1. **共通 control path で確認**: `/ping` など最も単純な command を別途実行し、同じ無反応なら共通インフラの問題。route 固有ではなくインフラ層が壊れている可能性が高い
2. **最新デプロイ状態の確認**: コンテナ / Lambda の packaging・デプロイ時刻・ヘルスステータスを確認する
3. **実行時ログの確認**: CloudWatch Logs / Lambda 実行ログで `ImportModuleError`、`Runtime.ExitError`、packaging 不備がないかを確認する
4. **前回の変更を特定**: 最後に変更・デプロイしたコンポーネントをデプロイ前後で比較する

インフラ層で根本原因が特定できた場合: そのまま修正・再デプロイして確認する。artifact 変更が不要なら `gdd-systematic-debugging` の routing decision tree はスキップしてよい。

## 副作用実態確認

**テストが PASS でも期待する副作用が起きていない場合に確認する。**

1. テストが実際に何を検証しているかを確認する（例: `isDraft=false` だけを見ていて CI checks の完了は検証していない）
2. 期待する副作用の実態を直接確認する（PR の state、artifact の存在、コメントの内容など）
3. テスト不足が原因 → テストを強化してから `gdd-test-failure-debug-pack` へ
4. bot / service の logic 不足が原因 → 直接 `gdd-systematic-debugging` へ

## Runtime Silent Timeout 切り分け（LLM agent runtime 特有）

**LLM 系の runtime（AgentCore / Claude CLI / Lambda + agent / Bedrock 系）で「処理が止まった / 何も返ってこない」場合**、上記「インフラ層チェック」の前に以下の 5 階層を切り分ける。`Runtime.ExitError` のような明示的失敗ではなく、stream event すら出ないまま timeout で終わる症状が対象。

### timeout の階層（外側から内側へ）

1. **caller timeout**（API Gateway / Slack webhook / GitHub webhook 等の入口）: 30s や 3min など短めの上限がある。caller 側 timeout なら runtime はまだ走っている可能性。caller 側の retry 設定も確認する
2. **Lambda / 上位コンテナ timeout**（Lambda の `Configuration.Timeout`、AgentCore の `maxLifetime`）: 上位プロセスが落とされていれば runtime ログは途中で切れる
3. **Agent runtime timeout**（AgentCore の `idleRuntimeSessionTimeout`、独自 polling 上限）: idle 判定でセッションが閉じられるパターン
4. **Claude CLI / LLM call timeout**（CLI の `--timeout`、内部 retry、API 側 timeout）: tool call 連鎖が長すぎて API 側で打ち切られている可能性
5. **Tool 個別 timeout**（Bash の `timeout` 引数、subagent dispatch の duration_ms 上限）: 1 つの tool call が詰まって全体が止まる

調査は **caller → Lambda → AgentCore → Claude CLI → tool** の順に外側から潰す。内側から見ると、外側が先に死んでいる場合に時間を浪費する。

### 確認チェックリスト（順に実施、症状が再現しない場合は次へ）

1. **CloudWatch Logs での進行確認**: 該当ロググループの直近 1 時間を時系列で取得し、最後の log event のタイムスタンプと内容を確認する。最後のメッセージが「tool call 開始」「prompt 送信直後」「特定 subagent の dispatch」等のどこで止まっているかで階層が絞れる
2. **stream-json progress event の有無**: Claude CLI が `--output-format=stream-json` モードか確認。stream モードでなければ最終 tool call まで一切出力されないため observability ゼロ。stream モードで起動しているのに event が止まっている場合は API 側 / 内部 retry を疑う
3. **hook timeout の確認**: PreToolUse / PostToolUse / Stop hook が長時間 block していないか。`hooks.json` の該当 hook の実装を読み、外部コマンド実行や API 呼び出しが含まれていないか確認する
4. **subagent dispatch の duration_ms**: subagent が timeout していないか、Task tool の戻り値メタを確認する。subagent の中でさらに subagent を呼ぶ多段 dispatch だと累積で上位 timeout に当たりやすい
5. **caller 側の retry**: webhook 受信後にすでに retry されていないか（同一 job_id が複数回 intake に到達する症状）。retry 競合で同じ runtime が複数走り、片方が idle 判定で閉じられるパターンがある

### 切り分け結果別の対応

| 観測パターン | 推定階層 | 次アクション |
|------|---------|------|
| caller 側 timeout エラーログあり、runtime は動き続けている | 1 caller | caller 側 timeout 延長 or async 化を検討。runtime 自体は無罪 |
| Lambda が `Task timed out after Ns` で死亡 | 2 Lambda | Lambda の `Timeout` を延ばすか、処理を非同期化（SQS / Step Functions）する |
| AgentCore で session が READY → IDLE で消えた | 3 AgentCore | `idleRuntimeSessionTimeout` の延長か、heartbeat 送信を runtime 側で実装 |
| stream event が prompt 送信直後で停止、最終 tool call なし | 4 Claude CLI | `--output-format=stream-json` を有効化済みなら API 側 retry を疑い、CloudWatch / API ログで確認。未有効化なら先に有効化して再現性を上げる |
| 特定 tool call で stream が止まる、duration_ms が異常に長い | 5 Tool | 該当 tool（Bash の長時間コマンド、subagent の多段 dispatch、外部 API 呼び出し）に individual timeout を追加 |

### Why

- LLM runtime の silent timeout は「何も出力されないまま終わる」のが特徴で、`Runtime.ExitError` 系の明示的失敗とは原因の階層が違う。インフラ層チェックだけでは Claude CLI / API / hook 側の問題を見逃す
- 切り分けを階層化しないと、内側だけ深掘りして外側 timeout を見落とすか、逆に外側だけ見て tool 個別 timeout に気づかない両方向の罠がある
- `stream-json` 化 PR 旧#117 のように、observability を上げる施策は切り分けの成功率を直接上げる。stream event が見える状態で再現させてから調査する方が、見えない状態で原因を推測するより圧倒的に早い

## 分類の判断基準

- 「テストが落ちた」と言われたら、まず **Test RED** か **Expected side effect missing** かを区別する
- テストに「応答なし」「timeout」が含まれる → **Silent failure** の可能性が高い。Test RED として扱わずインフラ層チェックを先に行う
- テストが PASS だが想定の動作をしていない → **Expected side effect missing** として扱う
- 「なんか動いていない」系の曖昧な症状 → Silent failure のチェックリストから始める

## 仮説候補チェックリスト

症状のレイヤーを特定したら、以下のカテゴリで「どのパターンに近いか」を仮絞りする。仮説が絞れると調査が短くなる。

### Null / Undefined アクセス
- 未初期化の変数・フィールドへのアクセス
- None / null チェック漏れ（Optional な返り値を必須として扱う）
- 空配列 / 空リストに対する `[0]` / `.first` アクセス

### Import / Module エラー
- 相対パスの誤り（`../` の階層ミス）
- パッケージ名と import 名の不一致、インストール漏れ
- 循環 import、バージョン不整合

### 型不一致
- string と number の比較（`"1" === 1`）
- 非同期関数の返り値を同期的に使用（await 漏れ）
- JSON.parse 後の型保証がない

### Off-by-One / 境界値
- ループの `<` vs `<=` の誤り
- 配列インデックスの 0-based / 1-based 混在
- ページネーションの offset 計算ミス

### Async / Timing
- race condition（複数の非同期操作が共有状態を変更）
- Promise を await せず次の処理が先に進む
- タイムアウト値がテスト環境で短すぎる
- `setTimeout` / `sleep` に依存したテスト（フレーキー）

### 設定 / 環境変数
- 環境変数が未設定（undefined のまま使用）
- test / prod の設定値の取り違え
- `.env` ファイルが読み込まれていない

### 状態の汚染（テスト間 / グローバル）
- テスト間で共有された mutable state
- グローバル変数 / シングルトンのリセット漏れ
- DB / キャッシュのテスト後クリーンアップ漏れ

### テスト設計の問題
- テストが実装の詳細をテストしている（動作ではなく実装）
- mock が実際の API と乖離している
- テストが PASS でも副作用を検証していない → **Expected side effect missing** で再分類
