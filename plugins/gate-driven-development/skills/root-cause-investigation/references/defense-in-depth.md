# Defense in Depth（多層 validation 戦略）

> **所有**: `root-cause-investigation` の補助 reference。同じ悪い値を複数層で阻止する設計の recipe
> **参照元**: `root-cause-investigation` Phase 1 step 5（データソース追跡） / Phase 4（fix を当てる層の選択）

## いつ使うか

- **同じ root cause** が形を変えて何度も再発している
- データの整形 / validation / sanitization を 1 箇所だけで行っていて、別経路から悪い値が入ってきた
- 「source で fix すれば終わる」と思ったが、後で別 source からも同じ悪い値が来た
- security boundary を跨ぐ値（user input / external API / file content）の扱いで侵入経路が複数ある

## Iron Law

> **1 層の validation は壊れる前提で設計せよ。**

防御は **多層** で行う。source 1 層だけに頼ると、source を bypass する経路（直接 DB に書く、新しい API endpoint、cached data の reuse）が出てきたときに全層が崩壊する。

ただし **冗長 = 良い設計ではない**。重複した validation は保守コストを増やし、変更時の同期忘れで「層によって挙動が違う」事故を起こす。**目的の異なる層** を重ねる。

## 5 層モデル

データが入ってから保存 / 出力されるまでに、以下の異なる目的の層を通すと defense-in-depth が成立する:

| 層 | 責務 | 例 |
|---|---|---|
| **1. Boundary validation** | 形 / 型 / 範囲チェック | API gateway / form validator / API spec（OpenAPI / JSON Schema）|
| **2. Sanitization** | 危険文字 / encoding の正規化 | HTML escape / SQL parameter binding / path traversal 除去 |
| **3. Business rule** | ドメイン制約 | 「user X は organization Y のリソースにアクセス可」等の authz |
| **4. Defensive output** | 出力直前の safety | output encoding / CSP header / SSRF block list |
| **5. Audit / detection** | 異常検知 / log | WAF / IDS / 異常 access pattern alarm |

### この層をどう使い分けるか

- **新規実装**: 最低 1 + 3 + 4 の 3 層を入れる。2 と 5 は外部 service / framework に委譲してよい
- **bug fix**: 「症状の場所だけ直す」のではなく、source / 中間 / 出力の 3 ヶ所で同じ悪い値を捕捉する設計に切り替える
- **既存システム監査**: 各データフローで上記層がどこに配置されているかを表にし、抜けがある層を特定

## 典型 anti-pattern

### Anti-Pattern 1: source 1 層だけで sanitize

```javascript
// ❌ Bad — API entry point だけで sanitize
app.post('/api/comments', (req, res) => {
    const safe = sanitize(req.body.text);  // ← ここだけ
    db.insert(safe);
});

// 後で別経路ができたとき:
app.post('/admin/import', (req, res) => {
    db.insert(req.body.text);  // ← sanitize 忘れ → XSS
});
```

```javascript
// ✓ Good — 出力直前にも encode
// 1. entry で sanitize
app.post('/api/comments', (req, res) => {
    const safe = sanitize(req.body.text);
    db.insert(safe);
});
// 4. 出力で encode（source bypass されてもここで止まる）
function renderComment(text) {
    return escapeHtml(text);  // ← 出力時に必ず escape
}
```

### Anti-Pattern 2: middleware で auth、ただし direct DB access で素通り

```python
# ❌ Bad — auth は API middleware のみ
@app.route("/api/users/<id>")
@require_auth
def get_user(id):
    return db.users.get(id)

# 内部 batch job からは middleware を経由しない:
def daily_report():
    for user in db.users.all():  # ← auth check なし
        send_email(user, ...)
```

```python
# ✓ Good — repository 層で authz を再確認
class UserRepo:
    def get(self, user_id, requester):
        u = self.db.users.get(user_id)
        if not requester.can_read(u):
            raise Forbidden(f"{requester.id} cannot read {user_id}")
        return u
```

### Anti-Pattern 3: 防御層を「全部 disable できる feature flag」で囲む

```python
# ❌ Bad
if not config.get("DISABLE_VALIDATION"):
    validate(payload)
if not config.get("DISABLE_AUTHZ"):
    authz(user, resource)
if not config.get("DISABLE_AUDIT"):
    audit_log(action)
```

各層が同じ flag で disable されると defense-in-depth が意味をなさない。disable する場合は **個別 flag + 期限付き + 監査ログ強制** にする。

### Anti-Pattern 4: 「source 直したから middleware の check は冗長」と削除

```diff
- // middleware で type check
- if (typeof req.body.id !== 'number') return res.status(400).end();

  // service で再 validate
  if (typeof input.id !== 'number') throw new ValidationError();
```

source の validate を削除すると、別 source（gRPC / message queue / batch）が直接 service を呼ぶときに防御が消える。**重複している = 削っていい** ではない。**異なる目的の層** なら残す。

## fix を当てる層の選び方

`root-cause-investigation` Phase 1 step 5 でデータソースを source まで遡った後、Phase 4 で fix を当てる場所を決めるとき:

| 状況 | 推奨 fix 層 |
|---|---|
| 悪い値が 1 経路でしか入ってこない | source（層 1） + 出力（層 4）の 2 ヶ所 |
| 複数経路から入る | 中間（層 3 service / repository）に集約して再 validate |
| security boundary 違反（XSS / SQLi / SSRF） | source（層 1） + sanitize（層 2） + output（層 4） + detection（層 5）の 4 層必須 |
| dead code / unreachable | fix ではなく削除 |
| 環境 / 設定 / external | infra fix（GDD context では `design_detail_only` ルート） |

## review との関係

`gdd-implementation-gating` の security reviewer は defense-in-depth の観点を持つ:

- 「ここで sanitize しているから OK」と書かれた fix → reviewer は **他の入口** を確認する
- middleware の validation だけで済ませた fix → reviewer は **bypass 経路** を grep で確認する
- 1 層削除しているなら、削除前後で **別の層に等価防御** が存在するかを確認

これらの観点は `references/inline-review-checklists.md` の security-reviewer checklist でも明示する。

## アンチパターン早見表

| 出てくる思考 | 現実 |
|---|---|
| 「source で fix したから OK」 | 別 source / bypass 経路がある前提で設計する |
| 「3 ヶ所で同じ check を書くと DRY 違反」 | 異なる目的 / 異なる context での validate は重複ではない |
| 「framework が validate してくれるから自分で書かない」 | framework の前提を破る経路（raw SQL / 直接 file I/O / cache）は必ずある |
| 「detection 層は production だけでいい」 | dev / staging で異常検知できない → 本番で初めて気づくループ |
| 「全部 disable flag で囲んでおけば緊急時切れる」 | 1 つの flag で全層が落ちる設計は最初から壊れている |

## 関連

- `common-failure-patterns.md` § 7. Permission denied — auth boundary 違反の典型パターン（逆参照: 本ファイルが多層 fix 設計の正本）
- `multi-layer-probing.md` — debug 時に layer ごとに値を観測する（**監査** 用途。probe で security boundary 違反を発見したら本ファイルの 5 層モデルで fix 設計）
- `call-stack-tracing.md` — 悪い値を source まで遡る詳細手順（trace 完了後、本ファイルで複数 source への fix を設計）
- `condition-based-waiting.md` — timing 系の多層防御（retry + timeout + circuit breaker）
- `references/inline-review-checklists.md` — security-reviewer / impl-reviewer の checklist で参照（本ファイルの 5 層モデルが review 観点として組み込まれる）
