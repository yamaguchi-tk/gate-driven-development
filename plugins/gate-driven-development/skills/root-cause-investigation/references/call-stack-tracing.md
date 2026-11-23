# Call Stack Tracing

`root-cause-investigation` Phase 1 step 5「データフローを source まで遡る」を、深い call stack で詰まったときに使う具体テクニック集。

bug は **「悪い値が観測された場所」と「悪い値が生まれた場所」が違う** ことが多い。観測点で fix を当てると、別の経路から同じ悪い値が来たときに再発する。本書は **source まで遡る** ための実用テクニックをまとめる。

## いつ使うか

以下のいずれかに当てはまるとき、本書のテクニックを使う:

- error が stack trace の深いところで出ている
- 「`null` が渡されているが、誰が `null` を渡したか分からない」
- file が予期しない場所に作られた / DB が予期しないパスで開かれた
- 空文字列 / `undefined` / 0 / 不正な enum 値が深い層で観測された
- 「この関数を呼び出した呼び出し元の呼び出し元」を辿りたい

逆に、以下のときは本書は使わない:

- error が entry point で出ている（stack trace が浅い）
- 値の出所が 1-2 hop で明らか
- multi-component / multi-layer の境界問題 → `multi-layer-probing.md` を先に使う
- パターン的な失敗 → `common-failure-patterns.md` で照合

## トレース手順

### 1. 症状を文章で書く

例:

```
git init が ~/project/packages/core で失敗した
（ホームディレクトリを期待していたのに）
```

「どの値が、どこで、どう間違っていたか」を 1 文で固定する。曖昧なまま遡らない。

### 2. 直接の原因を特定する

その症状を **直接引き起こしているコード行** を見つける:

```typescript
await execFileAsync('git', ['init'], { cwd: projectDir });
```

ここで「`projectDir` の値はどうだったか」を確認する。stack trace のいちばん深い行から始める。

### 3. 1 hop 上を遡る

その関数を呼んだのは誰か:

```typescript
WorktreeManager.createSessionWorktree(projectDir, sessionId)
  ← Session.initializeWorkspace() が呼んでいる
```

呼び出し元で `projectDir` がどう渡されたかを確認する。

### 4. 値が変質した点を見つける

各 hop で「値が前の hop と同じか」を確認する:

```typescript
Session.create(name, projectDir)
  → Session.initializeWorkspace()    // projectDir = ''  ← 既に空文字列
  → WorktreeManager.createSessionWorktree(projectDir, sessionId)  // ここでも空文字列
  → execFileAsync('git', ['init'], { cwd: projectDir })  // 空文字列が cwd になる
```

値が変質した hop を見つけたら、そこより上を遡る。

### 5. 元の trigger に到達する

```typescript
const context = setupCoreTest();        // context = { tempDir: '' } を返した
Project.create('name', context.tempDir); // 空文字列を渡した
                                          //  ↑ beforeEach の前に呼んだのが原因
```

ここが **original trigger**。fix はここに当てる。

## instrumentation での自動トレース

手動で遡れない場合は、コードに stack trace を仕込んで自動取得する:

### JavaScript / TypeScript

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  console.error('DEBUG git init:', {
    directory,
    cwd: process.cwd(),
    pid: process.pid,
    stack,
  });
  await execFileAsync('git', ['init'], { cwd: directory });
}
```

### Python

```python
import traceback
import logging

def git_init(directory: str):
    logging.error(
        "DEBUG git init: directory=%r cwd=%r stack=%s",
        directory,
        os.getcwd(),
        ''.join(traceback.format_stack()),
    )
    subprocess.run(['git', 'init'], cwd=directory, check=True)
```

### Go

```go
func gitInit(directory string) error {
    buf := make([]byte, 4096)
    n := runtime.Stack(buf, false)
    log.Printf("DEBUG git init: directory=%q cwd=%s\nstack:\n%s",
        directory, mustGetwd(), buf[:n])
    return exec.Command("git", "init").Run()
}
```

### Shell

```bash
git_init() {
  echo "DEBUG git init: directory=$1 cwd=$PWD pid=$$" >&2
  caller 0 >&2  # 直近の呼び出し元（bash）
  # zsh: print -P "%N:%i" >&2
  git -C "$1" init
}
```

## 各 hop で何を出力するか

辿る hop で記録すべき情報:

| 項目 | 何のため |
|---|---|
| **観測した値** | 値そのもの。masking が必要なら length + prefix |
| **呼び出し元の関数名 + 行** | stack trace で 1 hop 上を確定する |
| **その時点での外部状態** | `cwd` / 主要 env / 関連 global 変数 |
| **timestamp（ms 精度）** | 並行処理の場合の前後関係 |
| **trace id / request id** | 複数 request が混ざる場合の絞り込み |

masking が要る場合は `scripts/verify-env-propagation.sh` の masking ロジックを参考にする（length + first/last char）。

## fix を当てる場所の判定

source まで遡れたら、どこに fix を当てるかを決める:

### A. source で fix（推奨）

source の関数で値を検証 / 補正する。**全ての経路に効く**。

```typescript
function setupCoreTest(): { tempDir: string } {
  const tempDir = fs.mkdtempSync('/tmp/test-');
  if (!tempDir) throw new Error('mkdtemp failed');  // ← source で検証
  return { tempDir };
}
```

### B. 中間で fix（やむを得ない場合）

source を変えられない場合（外部ライブラリ等）、最も上流の自分のコードで検証する:

```typescript
class Session {
  static create(name: string, projectDir: string) {
    if (!projectDir) {                              // ← 中間で検証
      throw new Error('Session.create: projectDir is empty');
    }
    // ...
  }
}
```

中間 fix は「source は別」と認識して、後で source を直すための TODO を残す。

### C. defense-in-depth（推奨追加策）

source + 中間の両方で検証する。冗長だが、後で source が壊れたときに中間が catch する:

```typescript
// source 側
function setupCoreTest() {
  const tempDir = fs.mkdtempSync('/tmp/test-');
  if (!tempDir) throw new Error('mkdtemp failed');
  return { tempDir };
}

// 中間側
class Session {
  static create(name: string, projectDir: string) {
    if (!projectDir) throw new Error('Session.create: projectDir is empty');
    // ...
  }
}
```

この pattern は superpowers の `defense-in-depth.md` に詳しい（GDD では本書だけで完結）。

## アンチパターン

以下は **やってはいけない fix**:

### ❌ 観測点で握りつぶす

```typescript
await execFileAsync('git', ['init'], {
  cwd: projectDir || process.cwd()  // 空文字列を黙って補完
});
```

これは「悪い値が来ても何とかなる」ように見えるが:
- source の bug が放置される
- 別の場所で同じ source の悪い値が違う症状で出る
- log や error にも残らないので再発時に再調査が必要

### ❌ try/catch で握りつぶす

```typescript
try {
  await gitInit(projectDir);
} catch (e) {
  // 無視（次の処理に進めばいいから）
}
```

これは **Common Failure Pattern 10（Silently swallowed error）** に該当する。`common-failure-patterns.md` 参照。

### ❌ symptom の場所だけで fix

「`projectDir` が空のときは defaultDir を使う」のような条件分岐を観測点に入れる。source の `setupCoreTest` の bug は残ったまま。

## トレース完了の判定

以下のいずれかに到達したら遡るのを止める:

- **コードを書いた本人の意図に起因する箇所**: 「ここで空文字列を返している」ことが意図的か未意図かを判定できる場所
- **外部入力 / 環境変数 / ファイル読み込みの境界**: source は GDD 内のコードではなく、外部の何か
- **テストの setup / fixture**: テスト環境固有の問題
- **library / framework の境界**: 第三者コード。その先は遡れない

外部入力 / fixture / library が source の場合は、観測点に近い場所で defense-in-depth を入れる。

## GDD workflow との接続

call-stack tracing で root cause が確定したら:

1. 確定した root cause を **言葉で書く**（1-2 行）: 「`setupCoreTest` が `tempDir=''` を返している。理由は `mkdtempSync` の失敗を無視している」
2. `root-cause-investigation` Phase 4 で failing test を書く（root cause を assert する最小のテスト）
3. `gdd-systematic-debugging` に handoff し、Routing Decision Tree で戻り先を決める

trace 経路自体を `worklog.md` に残しておくと、同じ系統の bug が再発したときに高速に解決できる。

## 関連 references

- `multi-layer-probing.md` — multi-component 境界での値の伝播確認（call stack の前段階）
- `common-failure-patterns.md` — 15 パターン（特に 6: Serialization mismatch / 10: Silent swallowed error / 14: 型不一致）
- `condition-based-waiting.md` — call stack tracing で「async / 並行処理での timing 問題」と特定された場合の決定的待機 recipe
- `defense-in-depth.md` — source まで遡って fix を当てる層を決める判定表（複数経路 / security boundary の場合）
- `scripts/verify-env-propagation.sh` — env / 値の masking 出力
- `scripts/find-polluter.sh` — call stack に test 由来の汚染が混入している場合の polluter 特定
