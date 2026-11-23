# Testing Standard and Anti-Patterns

> **所有**: テストを書く・残す・消す判定基準（§ テスト判定基準）と、mock 設計の禁止パターン集
> **参照元**: `skills/gdd-test-driven-development/SKILL.md`（Guardrails）、`skills/gdd-subagent-driven-implementation/SKILL.md` Step 1a、`skills/gdd-design-gating/SKILL.md`（テスト方針）、`agents/gdd-implementation-reviewer.md` Focus 3、`agents/gdd-completion-reviewer.md` Focus 6、`agents/gdd-planning-reviewer.md`（Design phase）、`references/inline-review-checklists.md` § テスト品質、`skills/gdd-writing-skills/SKILL.md`（Process Documentation TDD）

## テスト判定基準

対象 repo に次のどれかがあれば、それを正とし、そこに無い項目だけを本節で判定する: `docs/testing-standard.md`、`AGENTS.md` のテストの節、`CLAUDE.md` のテストの節。探す先はこの 3 つに限る。

消したら、どのクラス（下表）の、現実にありうるどの不具合を見逃すかを 1 文で言えないテストは書かない。既存のテストなら消す。「念のため」「将来変わるかもしれない」は理由にならない。テストの本数や網羅は、守られていることを意味しない。

| クラス | 見逃す不具合 | 書くテスト |
|---|---|---|
| A | 本番だけが通る配線（decorator の登録先、facade の引数転送、Handler・entrypoint の指す先、パッケージングに含まれるファイル、値の所有境界） | 登録先の identity と signature、impl が実際に受け取った引数、指す先のシンボルの実在 |
| B | 本番の実データ形状との乖離（絶対パス、key 順、CRLF、非 UTF-8、再送、既定値と同値の明示指定） | 本番で観測した入力を、手で整形せずに 1 件以上通す |
| C | 無音失敗（early return・skip、呼ばなかった側の None を成功と解釈、warning の無い fallback） | skip の理由コードや、ログ・warning の痕跡を assert する |
| D | fail-closed 境界の穴（未知入力が許可経路へ、署名の欠落・不一致、許可集合と schema の不一致） | 拒否経路に到達して後続が呼ばれないこと、2 箇所で持つ集合の一致 |
| E | runtime が読む文書と実装のずれ | runtime が読む文書（skill・reference・agent 定義・hook の allowlist）だけを、行と動詞まで含めて見る |
| F | guard の空洞化（guard が壊れても green） | synthetic な違反を注入して guard が落ちる自己テスト |
| G | LLM 出力の品質 | unit test の対象外。eval で扱う |
| H | 分割・pure-move の回帰 | 移行中だけ置き、移行が終わったら消す |
| I | 条件で分かれる AC の止める側・境界の穴（AC が通さない・起こさないと定めた側で通る・起こる。止めるべき入力のうち通す入力に最も近いもの〔閾値の止める側の端、通す形と 1 箇所だけ違う入力〕が通る） | 止める側の入力で、AC が起こさないと定めた処理・副作用が起きないこと（止める側で起こすと定めた副作用は起きること）。境界の入力が止まること |

テストのダブル（fake app・mock・`lambda **kwargs`）で置き換えた本番の継ぎ目ごとに、実物を通すテストを 1 本置く。ダブルは継ぎ目を捨てるので、ダブルだけを通るテストは A を検出しない。

### 書かない・消すテスト

- 固定値 pin（リテラル・行数・文言・SHA・配置の写し）は、次のどれかに当たり、docstring に ADR か PR を引用できる場合だけ残す: (a) 外部契約の実値 (b) セキュリティ境界の集合一致 (c) 本番障害の再発防止で、他に検出手段が無いもの
- 人間向け文書（ADR 本文・runbook・計画 doc）の文言 guard は書かない。runtime が読む文書（クラス E）の規範文を行と動詞まで含めて見るテストは残し、上の固定値 pin に当たらない。語の存在・見出しの存在・最初の一致で見るものは消す。節・文書を丸ごと写すものは E に含めず、固定値 pin として判定する
- 本番ファイルの SHA 固定は原則として消す。次の 3 つをすべて満たすものだけ残す: (1) 対象が、runtime・hook・resolver が実行時に読む規範文書か、セキュリティ境界の実装（hook の allowlist、Gateway の schema など）である (2) わざと壊して試し、「この pin でしか検出できない改変」があると確かめてある (3) 更新は「新しいハッシュ＋理由」を履歴に 1 件足す方式で、ハッシュの値だけを差し替えることはできない
- (3) を満たしていない既存の pin は、変更の多いファイルを対象から外したうえで、この方式に移す
- mock しか検証しないテスト（mock の戻り値をそのまま assert する）は書かない。`assert_called_once_with` で引数契約を見るテストや、実戻り値の配線を見るテストは残す
- ライブラリの仕様の再検証、実装と同じ式で期待値を作るテスト、一度きりの移行確認は書かない
- 2 本で 1 契約のもの（振る舞いと signature の比較、guard とその自己テスト）は片方だけ消さない。消す前に、テスト名が他から参照されていないか確かめる

### 新しいテストの受入条件

1. docstring の 1 行目に、クラスと根拠（AC・ADR・PR・障害）を書く
2. 変異注入で検出力を実測する。配線を外す、引数を落とす、分岐を入れ替える、規範文を弱める、のうち該当する変異で失敗することを、失敗したテスト名で確かめる。テストが通ることは守れている証拠にならない
3. guard を足すなら、同じ変更で F の自己テストを足す

## Core Principle

テストは「実コードの振る舞い」を検証する。mock は **隔離の道具** であり、**テスト対象そのものではない**。

TDD を忠実に守ると、以下の anti-pattern は自然に避けられる。逆に、以下の anti-pattern が出ている時点で、RED を省略した・mock を先に書いた・テスト対象を理解せずに書き始めた、いずれかの TDD 違反が起きている。テストは実装の一部であり、後付けの task にしない（RED → GREEN → REFACTOR を崩さない）。

## Iron Laws（守るべき 3 原則）

```
1. mock の振る舞いをテストしない
2. production class にテスト専用メソッドを追加しない
3. mock の依存関係を理解しないまま mock しない
```

## Anti-Pattern 1: Mock の振る舞いを検証する

**違反例（TypeScript）:**

```typescript
// ❌ BAD: mock が存在することを検証している
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**何が問題か:**
- mock の存在を検証しているだけで、コンポーネントの振る舞いは検証していない
- mock があれば pass、無ければ fail — 実コードの正しさと無関係
- レビュー時の典型的な質問: 「これは mock の振る舞いをテストしていませんか？」

**修正例:**

```typescript
// ✅ GOOD: 実コンポーネントをそのまま使うか、mock を外す
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

### Gate Function

```
mock 要素にアサーションする前に:
  問い: 「実コンポーネントの振る舞いをテストしているか？ それとも mock の存在だけか？」

  mock の存在だけをテストしている場合:
    STOP — アサーションを消すか、コンポーネントを unmock する
```

## Anti-Pattern 2: Production class にテスト専用メソッドを追加する

**違反例:**

```typescript
// ❌ BAD: destroy() はテストでしか呼ばれない
class Session {
  async destroy() {  // production API のように見える
    await this._workspaceManager?.destroyWorkspace(this.id);
  }
}

afterEach(() => session.destroy());
```

**何が問題か:**
- production class がテスト専用コードで汚染される
- 本番で誤って呼ばれると破壊的
- YAGNI / 責務分離に違反
- object の lifecycle と entity の lifecycle を混同している

**修正例:**

```typescript
// ✅ GOOD: テストユーティリティに逃がす
// Session は production では stateless のまま destroy() を持たない

// test-utils/
export async function cleanupSession(session: Session) {
  const workspace = session.getWorkspaceInfo();
  if (workspace) {
    await workspaceManager.destroyWorkspace(workspace.id);
  }
}

afterEach(() => cleanupSession(session));
```

### Gate Function

```
production class にメソッドを追加する前に:
  問い 1: 「このメソッドはテストからしか呼ばれないか？」
    YES → STOP — production に置かない。test-utils に移す

  問い 2: 「このクラスがこの resource の lifecycle を所有しているか？」
    NO → STOP — 置き場所が間違っている
```

## Anti-Pattern 3: 依存関係を理解しないまま mock する

**違反例:**

```typescript
// ❌ BAD: mock がテストの前提（config 書き込み）を破壊する
test('detects duplicate server', () => {
  vi.mock('ToolCatalog', () => ({
    discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
  }));

  await addServer(config);
  await addServer(config);  // duplicate を検出するはずなのに検出されない
});
```

**何が問題か:**
- mock した method に副作用（config 書き込み）があり、テストはその副作用に依存していた
- 「念のため」の過剰 mock が実際の振る舞いを壊している
- テストが誤った理由で pass / fail する

**修正例:**

```typescript
// ✅ GOOD: 必要な部分だけ mock する
test('detects duplicate server', () => {
  vi.mock('MCPServerManager');  // 遅い server 起動だけを mock

  await addServer(config);  // config は書き込まれる
  await addServer(config);  // duplicate が検出される ✓
});
```

### Gate Function

```
method を mock する前に:
  STOP — まだ mock しない

  問い 1: 「実 method にどんな副作用があるか？」
  問い 2: 「テストがその副作用に依存しているか？」
  問い 3: 「このテストが必要とする依存を完全に理解しているか？」

  副作用に依存している場合:
    → 低いレイヤー（実際に遅い / external な呼び出し）を mock する
    → 高レベル method ごと mock しない

  依存が不明な場合:
    → まず実実装でテストを走らせる
    → 必要な副作用を観察してから最小限の mock を入れる

  Red flags:
    - 「念のため mock しておく」
    - 「遅そうだから mock」
    - 依存チェーンを理解せずに mock
```

## Anti-Pattern 4: 不完全な mock（Partial Mock）

**違反例:**

```typescript
// ❌ BAD: 自分が使うと思ったフィールドだけ mock
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' }
  // metadata が抜けている — 下流コードは metadata.requestId を使う
};

// 結果: 実行時に response.metadata.requestId でクラッシュ
```

**何が問題か:**
- partial mock は「構造上の前提」を隠蔽する
- 下流コードが参照する未 mock フィールドで silent に壊れる
- ユニットテストは pass するが、integration で fail する（false confidence）
- mock が real API の shape と一致していないのに、テストは pass と主張する

**Iron Rule:** mock は **real API の完全な構造を反映する**。テスト自身が使うフィールドだけで切り出さない。

**修正例:**

```typescript
// ✅ GOOD: real API と同じ完全な shape を mock
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: { requestId: 'req-789', timestamp: 1234567890 }
  // real API が返す全フィールド
};
```

### Gate Function

```
mock response を作る前に:
  確認: 「real API は実際に何を返すか？」

  手順:
    1. API ドキュメント / 実際のレスポンス例から完全な shape を確認
    2. 下流コードが参照し得る全フィールドを含める
    3. mock が real response schema と一致しているか検証

  不確実な場合: documented な全フィールドを含める
```

## Anti-Pattern 5: Intent 列挙の登録漏れ（Registration Gap）

**違反例（Python）:**

```python
# intent を判定する関数が複数存在する
def _should_use_stream_json(intent: str) -> bool:
    return intent in ("pr_review", "pr_review_heavy")  # ❌ pr_review_light が抜けている

def is_pr_review_route(intent: str) -> bool:
    return intent in ("pr_review", "pr_review_heavy", "pr_review_light")  # ✓ こちらは正しい

# 新しい intent を追加したが、_should_use_stream_json だけ更新を忘れた
```

**何が問題か:**
- 新しい `intent` 値を 1 箇所に追加しただけで、それを参照する全関数が網羅されていると思い込む
- 単体テストは新 intent の正常系だけカバーし、各消費関数への登録漏れを検出しない
- ユニットテストは pass するが E2E smoke で初めて発覚する（T-3 → T-9 のラグ）

**修正例:**

```python
# RED: 追加した時点で各消費関数向けテストを書く
def test_pr_review_light_uses_stream_json():
    assert _should_use_stream_json("pr_review_light") is True  # 最初は FAIL

def test_pr_review_light_is_pr_review_route():
    assert is_pr_review_route("pr_review_light") is True

# GREEN: 全消費関数に登録してから実装する
def _should_use_stream_json(intent: str) -> bool:
    return intent in ("pr_review", "pr_review_heavy", "pr_review_light")  # ✓ 追加
```

**Why:** 新 intent を追加する際、コードを grep して消費関数を列挙してからテストを書かないと、登録漏れを実装後の E2E で初めて発見することになる。

### Gate Function

```
新しい intent / enum / action type を追加する前に:
  Step 1: grep -r 'intent.*<existing_value>\|is_<type>_route\|_should_.*intent' . で
          消費関数の一覧を列挙する
  Step 2: 各消費関数について「新しい intent がここで正しく扱われるか」の
          RED テストを書く（テストが FAIL することを確認する）
  Step 3: 全 RED テストを GREEN にしてから intent 値を追加する

  RED なしで追加した場合:
    STOP — 追加した intent で各消費関数を直接呼ぶ単体テストを先に書く
```

## Mock が複雑になったときのサイン

以下が出始めたら mock 設計を疑う:

- mock の setup がテストロジックより長い
- テストを pass させるために次々 mock を足している
- mock が real コンポーネントにあるメソッドを欠いている
- mock を変えるとテストが壊れる（= mock の振る舞いをテストしている）

判断の補助質問: **「本当に mock が必要か？ integration test の方が簡単では？」**

mock が過剰になっているときは、real コンポーネントで組む integration test の方が結果的にシンプルなことが多い。
