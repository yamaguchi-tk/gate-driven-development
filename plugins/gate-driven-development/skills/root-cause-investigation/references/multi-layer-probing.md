# Multi-Layer Probing

`root-cause-investigation` Phase 1 step 4「境界ごとに証跡を集める」を、具体的な layer 構成ごとに展開したテンプレート集。

multi-component / multi-stage なシステムで「どの境界で値・state が壊れているか」を特定するためのコマンド・ログ出力の雛形を提供する。fix を当てる前に **どこで壊れているか** を確定させるのが目的。

## 基本原則

1. **各層の入口と出口で値を出す** — 入ってくる値、出ていく値、両方
2. **値そのものではなく「存在 / 形」を出す** — secret は masked + length / prefix のみ
3. **一度の実行で全層を観測する** — 何度も走らせると変化する変数は分離できなくなる
4. **layer 名を必ず付ける** — どの行がどの層の出力か後で読めるように

## Layer 構成パターン別テンプレート

### A. CI/CD パイプライン（GitHub Actions / Cloud Build / GitLab CI 等）

層: `Repository event` → `Workflow runner` → `Job step` → `Build script` → `Deploy script`

```bash
# Layer A1: Workflow event
echo "=== [A1] Workflow event ==="
echo "Event: ${GITHUB_EVENT_NAME:-unknown}"
echo "Ref: ${GITHUB_REF:-unset}"
echo "SHA: ${GITHUB_SHA:-unset}"
echo "Actor: ${GITHUB_ACTOR:-unset}"

# Layer A2: Runner environment
echo "=== [A2] Runner env ==="
echo "OS: $(uname -a)"
echo "Working dir: $(pwd)"
echo "User: $(whoami)"
env | grep -E "^(CI|RUNNER|GITHUB_)" | sort

# Layer A3: Secret propagation to job step
echo "=== [A3] Secret propagation (masked) ==="
for var in AWS_ROLE_ARN GITHUB_TOKEN OIDC_TOKEN; do
  if [ -z "${!var+x}" ]; then echo "$var: UNSET"
  elif [ -z "${!var}" ]; then echo "$var: SET_EMPTY"
  else echo "$var: SET (len=${#var})"; fi
done

# Layer A4: Build script env
echo "=== [A4] Build script env ==="
echo "node version: $(node -v 2>/dev/null || echo 'not found')"
echo "npm version: $(npm -v 2>/dev/null || echo 'not found')"
ls -la

# Layer A5: Deploy script artifact
echo "=== [A5] Deploy artifact ==="
ls -la dist/ build/ out/ 2>/dev/null || echo "no build output dirs"
```

### B. AWS Lambda / Cloud Function

層: `Event source` → `Invocation` → `Handler` → `External AWS API call` → `Response`

```python
# Layer B1: Invocation event
import json, os, time
print(f"=== [B1] Invocation ===")
print(f"Function: {context.function_name}")
print(f"Request ID: {context.aws_request_id}")
print(f"Remaining ms: {context.get_remaining_time_in_millis()}")

# Layer B2: Event payload (shape only)
print(f"=== [B2] Event shape ===")
print(f"Type: {type(event).__name__}")
print(f"Keys: {list(event.keys()) if isinstance(event, dict) else 'not a dict'}")
print(f"Size: {len(json.dumps(event))} bytes")

# Layer B3: Env vars (masked)
print(f"=== [B3] Env (masked) ===")
for var in ['DYNAMODB_TABLE', 'S3_BUCKET', 'SECRET_ARN']:
    val = os.environ.get(var)
    if val is None: print(f"  {var}: UNSET")
    elif val == '': print(f"  {var}: EMPTY")
    else: print(f"  {var}: SET (len={len(val)})")

# Layer B4: Outbound AWS API call
print(f"=== [B4] Outbound: {api_name} ===")
print(f"Region: {os.environ.get('AWS_REGION')}")
t0 = time.time()
try:
    response = client.method(...)
    print(f"Response status: {response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")
    print(f"Latency ms: {int((time.time() - t0) * 1000)}")
except Exception as e:
    print(f"Error type: {type(e).__name__}")
    print(f"Error msg: {str(e)[:200]}")
    raise
```

### C. Web リクエスト（client → API gateway → service → DB）

層: `Browser` → `CDN/Edge` → `API Gateway` → `Application server` → `DB`

```bash
# Layer C1: Client side (browser devtools / curl)
curl -v -H "Authorization: Bearer ***" https://api.example.com/foo 2>&1 | head -30

# Layer C2: Edge / CDN logs
# Cloudflare: cf-ray, cf-cache-status headers
# CloudFront: x-amz-cf-id, x-cache headers
# Look for: req received, cache hit/miss, time to origin

# Layer C3: API Gateway access log
# Look for: auth result, throttle status, integration latency
# AWS API Gateway: $context.requestId, $context.authorizer.principalId,
#                  $context.integrationLatency, $context.integrationStatus

# Layer C4: Application server log
# Confirm: request received with same request_id from gateway
#          auth context propagated
#          DB query parameters

# Layer C5: DB query log
# Confirm: query received with parameters
#          query plan / index usage
#          duration
```

### D. Container / ECS / Kubernetes

層: `Image build` → `Image push` → `Task definition` → `Container runtime` → `Application`

```bash
# Layer D1: Image
docker inspect <image>:<tag> | jq '.[] | {Created, Config: .Config | {Env, Entrypoint, Cmd, WorkingDir}}'

# Layer D2: Task definition / Pod spec
aws ecs describe-task-definition --task-definition <name> | jq '.taskDefinition | {family, revision, containerDefinitions: [.containerDefinitions[] | {name, image, environment, secrets}]}'
# k8s: kubectl describe deployment <name> | grep -A 20 "Containers:"

# Layer D3: Runtime task / pod
aws ecs describe-tasks --cluster <c> --tasks <t> | jq '.tasks[] | {lastStatus, healthStatus, stopCode, stoppedReason}'
# k8s: kubectl describe pod <name>

# Layer D4: Container env
# Inside container or via exec:
env | sort
cat /proc/1/cmdline | tr '\0' ' '

# Layer D5: Application boot
# Application log first 50 lines = where env consumed
```

### E. データパイプライン（producer → queue → consumer → sink）

層: `Producer` → `Queue/Stream` → `Consumer` → `Transform` → `Sink`

```python
# Layer E1: Producer
producer_log = {
    "stage": "produce",
    "msg_id": msg_id,
    "size_bytes": len(payload),
    "schema_version": "v3",
    "timestamp": now_iso(),
}
print(json.dumps(producer_log))

# Layer E2: Queue metrics
# SQS: ApproximateNumberOfMessages, ApproximateAgeOfOldestMessage
# Kafka: lag per consumer group
# Look for: messages stuck, age growing

# Layer E3: Consumer receive
print(json.dumps({"stage": "receive", "msg_id": msg_id, "receive_lag_ms": ...}))

# Layer E4: Transform
print(json.dumps({"stage": "transform", "msg_id": msg_id,
                  "input_schema": detect_schema(input),
                  "output_schema": detect_schema(output),
                  "duration_ms": ...}))

# Layer E5: Sink write
print(json.dumps({"stage": "sink", "msg_id": msg_id,
                  "sink_status": status, "duration_ms": ...}))
```

## 共通の落とし穴

- **Secret を生で出す**: log に full token を出すと事故の元。`scripts/verify-env-propagation.sh` を使うか、masked 表記（length + prefix のみ）にする
- **layer 名を付け忘れる**: 後で grep できないと無意味。`[A1]`, `[B3]` のように prefix を付ける
- **時刻ズレ**: layer ごとに UTC で `date -Iseconds` を出力すると、layer 間のレイテンシが見える
- **異常系だけ probe する**: 正常系の baseline も同じ probe で取っておくと、何が異常か比較できる
- **probe を本番に残す**: debug 完了後に削除するか、log level で制御できる形にする

## 関連 references

- `common-failure-patterns.md` — どの layer で壊れやすいかのパターン集
- `call-stack-tracing.md` — 1 layer 内の call stack を深く遡る場合（multi-layer probe で異常 layer 特定後の深掘り）
- `condition-based-waiting.md` — probe で「timing 問題と特定された」layer の fix recipe（固定 sleep ではなく決定的待機）
- `defense-in-depth.md` — probe で「security boundary 違反」を発見した layer の fix 設計（多層 validation）
- `scripts/verify-env-propagation.sh` — env 伝播の最小チェックを 1 コマンドで実行
- `scripts/find-polluter.sh` — probe で「他の test の汚染」と判明した場合の polluter 特定

## probe を入れたあとの読み方

1. 全 layer の output を 1 つのログに集約する
2. layer 名で grep して、各 layer の入口・出口の値を並べる
3. 「正常系で見るはずの値」と「異常系の値」の差分を取る
4. 最初に差が出る layer がその issue の発生境界。そこを Phase 2（pattern 比較）の対象にする
