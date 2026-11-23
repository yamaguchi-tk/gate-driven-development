# Condition-Based Waiting（timing 依存 anti-pattern と決定的待機）

> **所有**: `root-cause-investigation` の補助 reference。timing 依存バグの典型 anti-pattern と、決定的（deterministic）に待つ recipe 集
> **参照元**: `root-cause-investigation` Phase 1 / Phase 2 で flaky test や timing 依存の症状が出たとき

## いつ使うか

- テストが「たまに失敗」する（flaky）
- production で sporadic に発生する race condition / timing-sensitive bug
- `setTimeout` / `sleep` / `await new Promise(r => setTimeout(r, N))` 等の固定時間待機が混入している
- 「local では通るが CI で落ちる」（リソース速度差で timing がズレる）

## Iron Law

> **固定時間で待つな。条件で待て。**

`sleep(N)` / `setTimeout(N)` で「N ミリ秒待てば終わってるはず」と仮定するコードは、N が短すぎると flaky / 長すぎると遅い、というジレンマに必ず陥る。**観測したい状態の発生** を直接条件として待つこと。

## 典型 anti-pattern

### Anti-Pattern 1: 固定時間 sleep で「処理完了を仮定」

```javascript
// ❌ Bad
async function test() {
    triggerAsyncWork();
    await sleep(500);  // "500ms あれば終わってるはず"
    assert(state === "done");  // CI で 500ms 足りないと FAIL
}
```

```javascript
// ✓ Good — 条件で待つ
async function test() {
    triggerAsyncWork();
    await waitFor(() => state === "done", { timeout: 5000, interval: 50 });
    assert(state === "done");
}

function waitFor(condition, { timeout = 5000, interval = 50 } = {}) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        const check = () => {
            if (condition()) return resolve();
            if (Date.now() - start > timeout) return reject(new Error("waitFor timeout"));
            setTimeout(check, interval);
        };
        check();
    });
}
```

### Anti-Pattern 2: I/O 完了を時間で推定

```python
# ❌ Bad
subprocess.Popen(["heavy_task"])
time.sleep(10)  # "10 秒あれば終わるはず"
result = read_output_file()
```

```python
# ✓ Good — file 存在 / signal で待つ
proc = subprocess.Popen(["heavy_task"])
result = proc.wait(timeout=60)  # process exit を待つ
# または:
wait_for_file(path="output.json", timeout=60, interval=0.5)
```

### Anti-Pattern 3: 並列処理の終了を「最遅推定」で待つ

```go
// ❌ Bad
for i := 0; i < 10; i++ {
    go doWork(i)
}
time.Sleep(2 * time.Second)  // "10 個の goroutine が 2 秒で終わるはず"
```

```go
// ✓ Good — sync.WaitGroup で完了を待つ
var wg sync.WaitGroup
for i := 0; i < 10; i++ {
    wg.Add(1)
    go func(i int) {
        defer wg.Done()
        doWork(i)
    }(i)
}
wg.Wait()  // 全員が Done() を呼ぶまで決定的に待つ
```

### Anti-Pattern 4: retry ループに sleep を入れて「結果整合性」を待つ

```python
# ❌ Bad
time.sleep(5)  # "DynamoDB 書き込みが伝播するのを待つ"
result = read_from_dynamodb()
assert result is not None
```

```python
# ✓ Good — 観測したい状態を polling
def wait_until_visible(read_fn, predicate, timeout=30, interval=0.5):
    start = time.monotonic()
    last_value = None
    while time.monotonic() - start < timeout:
        last_value = read_fn()
        if predicate(last_value):
            return last_value
        time.sleep(interval)
    raise TimeoutError(f"condition not met, last={last_value!r}")

result = wait_until_visible(read_from_dynamodb, lambda v: v is not None)
```

### Anti-Pattern 5: UI test で element 表示を時間で待つ

```typescript
// ❌ Bad (Playwright / Cypress)
await page.goto("/dashboard");
await page.waitForTimeout(3000);  // "3 秒あれば描画されるはず"
await page.click("button.submit");
```

```typescript
// ✓ Good — element の表示を待つ
await page.goto("/dashboard");
await page.waitForSelector("button.submit", { state: "visible" });
await page.click("button.submit");
```

## 決定的待機の recipe

| 状況 | 待つ条件 | 言語別 API |
|---|---|---|
| 子プロセス完了 | exit | `subprocess.wait()` (Python) / `child.on('exit')` (Node) / `cmd.Wait()` (Go) |
| ファイル出現 | ファイル存在 | polling + `os.path.exists()` / `fs.access()` / `inotify` (Linux) |
| 並列タスク全完了 | counter = 0 | `Promise.all` (JS) / `sync.WaitGroup` (Go) / `asyncio.gather` (Python) |
| network ポート開放 | TCP connect 成功 | `nc -z host port` / socket connect retry loop |
| DB 書き込み伝播 | read で見える | polling + 期待条件の predicate |
| UI element 表示 | DOM 状態 | `page.waitForSelector` / `cy.get` の auto-retry |
| log 出力 | log 行マッチ | tail + grep / `expect`（Tcl）|

## 適切な timeout 値の決め方

- **下限**: 実環境で観測された最遅ケース × 1.5
- **上限**: テスト suite 全体の制限時間から逆算（1 test の timeout は suite の 10% 以下）
- **interval**: 通常 50-100ms。短すぎると CPU を食う、長すぎると不要に待つ
- **fail-fast**: timeout に達したら **必ず明確な error message** を出す（`last_value` や 待った条件文を含める）

## Phase 1 〜 Phase 3 での使い方

- **Phase 1（事実収集）**: 固定 sleep を grep して列挙する
  ```sh
  grep -rn "sleep\|setTimeout\|waitForTimeout\|time\.sleep" --include="*.{js,ts,py,go,sh}" .
  ```
- **Phase 2（pattern 比較）**: 動いている類似テストの待機方法と比較
- **Phase 3（仮説検証）**: sleep を waitFor に置き換えて単体テスト 100 回連続実行（flaky の根絶確認）

## flaky test を Phase 4 に進めるかの判定

`root-cause-investigation` Phase 1 の早期切り上げ条件で **「再現性 deterministic」が必須**。flaky のままで Phase 4 へ進むのは Iron Law 違反。flaky なら:

1. 本 reference で固定時間待機 / global state / 並列依存を疑う
2. 100 回連続実行で再現率を測る（10% 未満なら flaky 確定）
3. Phase 4 出力で「root cause 未確定（flaky）」とし、追加データ収集（observability 強化）を最優先アクションにする

## アンチパターン早見表

| 出てくる思考 | 現実 |
|---|---|
| 「sleep の N をもう少し増やせば flaky 解消する」 | 環境差で N をいくらにしても限界がある。条件で待つしかない |
| 「local では再現しないから OK」 | CI / production で再現するなら fix 対象。local 再現は前提でない |
| 「並列実行の影響だから serial で動かせばよい」 | serial 強制は回避策で fix ではない。並列汚染の根本原因を直す |
| 「retry を増やせば成功する」 | retry で隠すと「いつか必ず再現する」状態が残る。条件で待つ方が単純 |

## 関連

- `common-failure-patterns.md` § 3. Timing 依存 — このパターンの fix 詳細レシピが本ファイル（逆参照）
- `multi-layer-probing.md` — layer ごとの timing 観測（probe で「timing 層を特定」した後の fix 設計に本ファイルを使う）
- `call-stack-tracing.md` — async / 並行処理での call stack 遡及（trace で「timing 問題」と特定したら本ファイルへ）
- `defense-in-depth.md` — retry + timeout + circuit breaker の多層防御 fix（timing 系の多層 fix を組む場合）
- `scripts/find-polluter.sh` — 並列汚染ではなく ordering 汚染（A → B で B 失敗）の特定。teardown 由来の test 汚染なら先にこちらで polluter を絞り込む
