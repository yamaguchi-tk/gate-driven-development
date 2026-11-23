# Inline Review Checklists

> **所有**: implementation-gating のインラインレビュー用チェックリスト
> **上位正本**: `reviewer-common.md`（severity / route hints / output format）
> **参照元**: `gdd-implementation-gating`
> **Why**: subagent review loop をインラインチェックリストに置き換え、review 時間を大幅短縮しつつ品質を維持する

## 使い方

1. `reviewer-selection.md` で `selected` になった reviewer のチェックリストを使う
2. gate skill 自身がチェックリストを順に走査し、該当する issue を `reviewer-common.md` の severity と output format で報告する
   - **severity 判定の必須参照**: 各 finding の High / Medium / advisory 判定は、本 file 冒頭で宣言されている通り `reviewer-common.md` が **上位正本**。checklist 項目名だけから severity を推定せず、必ず `reviewer-common.md` の severity 定義を Read して適用する（特に Medium vs High の境界判定で根拠が弱くならないため）
   - **常時 High**: `reviewer-common.md` § 常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）の適用範囲に当たる finding は High とし、「false positive 実績のある項目は severity を 1 段階下げる」規定の適用対象外とする（適用範囲外の扱いの正本は同節。ここは参照であり定義しない）
3. チェックリストで判断がつかない場合だけ `agents/*.md` の subagent に escalation する

## implementation-reviewer checklist (always)

### 品質・正確性
- [ ] 壊れた command / skill / agent のリンクがないか
- [ ] 矛盾する state 遷移、resume / worktree で user が詰まるパスがないか
- [ ] 過度に複雑な指示、重複ロジック、紛らわしい命名がないか
- [ ] approval / review gate をバイパスするパスがないか
- [ ] 曖昧な完了条件がないか

### AC・契約準拠
- [ ] 変更が AC を満たしているか（AC ID ごとに確認）。**止める側・境界のテスト**: `tasklist.md` の Current Task の（Gate Batch では各 task の）Contract Surface Coverage で、条件で挙動が分かれる AC に止める側（枝ごと）と境界の行があるか、`not_applicable` の理由が AC と食い違わないか、`実装前から pass（対照）` の行に `変異:` の記録があり、落ちたテストが行のテストと同じか。当たれば `test-power`（`references/testing-anti-patterns.md` § テスト判定基準 のクラス I）。**名指しの AC**: `worklog.md` の `AI が閉じた:`・`表示した文面を採用:` の行が名指しした AC は、実装を壊してその `計測:` のテストが落ちることを実際に確かめる。落ちなければ High の finding（AC の意味）にして差し戻す（`references/requirements-gating-steps.md` § AI が閉じる blocking）
- [ ] **実装 → artifact の逆方向整合**: 実装 diff に含まれる外部観測可能な挙動（新規エンドポイント / 新規 field / 新規 CLI オプション / 新規 UI 要素 / 新規エラーメッセージ / 境界値変更等）が、すべて `requirements.md`（AC）・`design.md`・`adr.md` のいずれかに記載されているか。記載のない挙動がある場合は Spec Drift として Medium finding 以上で報告し、`gdd-subagent-driven-implementation` Step 11 の Spec Change Detection に従って artifact を更新してから再レビューする（AC の根本追加/削除なら `human_recheck_required` に昇格）
- [ ] **design → 実装の順方向整合**: `design.md` が名指しした既存部品・関数・ファイル（「X を使う」「Y を再利用」等）を実装が実際に使っているか。使っていない場合、理由が `worklog.md` に記録されていなければ finding
- [ ] `Next Action` / `Resume From` / gate 遷移が steering docs と一致するか
- [ ] scope が silent に拡大・縮小していないか
- [ ] workflow 契約ファイルの変更が contract-overview / state-machine と整合するか

### 非機能
- [ ] failure mode に対する recovery / rollback が明示されているか
- [ ] ログ / smoke check / troubleshooting hook が必要な箇所にあるか
- [ ] hot path / 繰り返し高コスト処理がないか
- [ ] retry / timeout の設定が適切か

### パフォーマンス（非機能の補助。該当がなければスキップ）
- [ ] N+1 クエリ: ループ内で DB / API を個別呼び出ししていないか（batch / join / eager load で解決可能か）
- [ ] 全件取得: `SELECT *` / `findAll()` / filter なしの list 呼び出しで、大量レコードを無制限にメモリに載せていないか（pagination / streaming / limit が必要か）
- [ ] O(n²) 以上のループ: ネストされたループや配列内の線形検索がデータ量に対して問題にならないか（Map / Set / index による改善が可能か）
- [ ] 不要な再計算: ループ外に出せる計算やキャッシュ可能な値がループ内で毎回計算されていないか
- [ ] 大量データの同期処理: 大きなファイル読み込み・API 呼び出しが同期的にブロックしていないか（streaming / async / worker が必要か）

### パターンマッチ・外部入力照合（regex / allowlist / denylist。該当がなければスキップ）
- [ ] 正規表現の flag 漏れ（`re.IGNORECASE` / `i` flag 等）で大文字小文字 bypass にならないか（external input に対する keyword filter / allowlist は特に要確認）
- [ ] allowlist と denylist の選択が妥当か（external input は allowlist を既定、denylist は bypass されやすい）
- [ ] regex の anchor (`^` / `$` / `\A` / `\z`) が欠落して部分一致で意図外 match しないか
- [ ] regex の catastrophic backtracking（ReDoS）リスクがないか（ネストした量詞、`.*.*` 等）
- [ ] 外部 API / webhook payload の型・schema が期待通りか（実際の payload shape と乖離した field アクセスがないか）
- [ ] 外部 API 応答の null / missing field / 型不一致で silent に分岐が変わらないか

### Dead code / 到達不能分岐（該当がなければスキップ）
- [ ] 先行 `return` / `raise` / `continue` の後に到達不能な処理が残っていないか
- [ ] 常に truthy / falsy な条件で片方の分岐が死んでいないか
- [ ] 使用されない変数 / import / 関数引数が残っていないか（silent な意図逸脱の兆候）
- [ ] 早期 return の後に defensive fallback を書いて実質 dead return にしていないか

### 非同期・時間依存（該当がなければスキップ）
- [ ] Promise / async 関数の rejection が catch されているか（未処理 rejection で silent failure にならないか）
- [ ] タイムアウト設定: 外部呼び出し・DB クエリ・ファイル I/O にタイムアウトが設定されているか（ハングの可能性がないか）
- [ ] 部分的成功: 複数ステップの非同期処理で、途中失敗時にロールバックまたは補償処理があるか
- [ ] タイムゾーン・日付境界: 日付比較やスケジュール処理で UTC / ローカル時間の混在がないか
- [ ] リトライの冪等性: リトライ対象の操作が冪等であるか、または冪等キーが設定されているか

### 運用可能性
- [ ] 提案が host capability の制約内で実行可能か
- [ ] install / resume / upgrade / state migration で user が詰まらないか
- [ ] rollback 手順が具体的で実行可能か
- [ ] 不要な抽象化 / 互換レイヤーが増えていないか

### 実起動検証（hook / CLI / スクリプトが変更対象の場合のみ）
- [ ] 実行可能な entry point を fixture（`mktemp -d` の git repo + 最小 state）で実起動し、正常系 1 + **対象外と宣言していない迂回形 3 以上**（例: 別 shell 経由での起動、引数順の入れ替え、環境変数での分岐、想定外の入力形式）を試したか。finding の evidence に実行コマンドと exit code / 出力を書く
- [ ] **起動しない（対象外と宣言する）entry point**（fixture 内に副作用が閉じないもの — 外部ネットワーク書き込み / 認証情報を要求する / deploy・apply・push・課金を伴う / 共有リソースを変更する）について、「対象外」と理由を finding に明記したか
- [ ] 実起動できない場合は escalation 条件に該当する（subagent へ上げる）

### テスト品質（テストファイル変更がある場合のみ。判定は `references/testing-anti-patterns.md` § テスト判定基準）
- [ ] 各テストについて、消したら見逃す不具合をクラスと 1 文にできるか（できないものと、同節の「書かない・消すテスト」に当たるものは削除を求める）
- [ ] mock / stub 要素そのものに assert していないか（`*-mock` の test ID / mock object の method call 回数検証のみ等は mock の振る舞いテスト）
- [ ] production class にテスト専用メソッドが追加されていないか（`destroy()` / `reset()` 等がテストからしか呼ばれない場合は test-utils に移す）
- [ ] partial mock になっていないか（real API の shape と乖離した最小 field だけの mock は下流で silent failure を引き起こす）
- [ ] mock が過剰ではないか（mock setup がテスト本体より長い / mock を外すとテストが全滅する場合は integration test を検討）
- [ ] environment 起因の失敗を RED とみなしていないか（`ConnectionRefused` / `Module not found` は RED 証跡ではなく環境不備）

### 推論型（分岐と経路を追って初めて見える型。checklist 走査時に必ず 4 項目とも当てる）

- [ ] **既存機構との分岐相互作用**: 新設した deny / guard / counter が、既存の escape hatch・降格・counter・TTL・早期 return と同時に成立する入力で、どちらが勝つかを分岐ごとに追ったか（分類6）— 実例（size の上限が deny した当時）: 既存カテゴリの違反と同時に書くと新設の size decision が record されず、既存 escape hatch の 3 回目 allow で size deny を迂回できた
- [ ] **受理集合の対称性・列挙型判定の検出**: 同じ入力を読む関数が複数あるとき（parser と判定、top-level と nested、単数形と複数形）、受理するキー・別名・型の集合が一致するか。片方だけが受理する入力で「片方は判定・片方は素通り」にならないか（分類6）— 実例: chunk 抽出側の edits ループに別名キーが無く、判定側が deny を算出するのに抽出が空になって無言 allow へ落ちた。また、判定が既知の異常パターンを列挙して弾く型になっていないか。列挙型なら受理文法のホワイトリスト化・既定の反転を検討する
- [ ] **例外で guard 全体が落ちる経路**: 新規コードが既存 deny より前に実行される場合、例外（encode / parse / resolve / stat / 型違い）が捕捉されずに hook が非 block 終了し、既存 deny が 1 件も走らない経路が無いか。**lone surrogate・NUL・非 dict payload・相対パスを 1 形ずつ実際に当てる**（分類6）— 実例（size の上限が deny した当時）: 新設 size 判定の `encode("utf-8")` が lone surrogate で例外になり、hook ごと落ちて既存の deny category が素通りした（rc=1 の fail-open）
- [ ] **正規化と判定の順序**: パスや文字列を正規化する前に判定していないか、正規化後に対象集合から外れる入力が無いか（分類6）— 実例: `resolve()` 前の文字列で対象判定したため `/x/.steering/../state.md` が対象に入り、無関係ファイルが deny された

### 照合型（記録・注釈・テストの穴。diff の外の実態と突き合わせる）

- [ ] **記録 vs 統合先実態**: 版数・消費済み版数・baseline・行数上限等の記録が、統合先（`origin/main`）の**実測**と一致するか（分類3）— 実例: 消費済み版数の記録が分岐前の値のまま残り、統合先を起点にした検査が失敗した
- [ ] **注釈・ADR の主張 vs 実装**: 「閉包が成立」「揃えた」「不変」「唯一」等の断定を、実装のリテラル・集合と 1 件ずつ突合したか（分類8）— 実例: 別名キー集合の注釈と ADR が「閉包は実態と一致」と述べていたが、edits 内の集合だけが不一致だった
- [ ] **テストマトリクスの欠けセル**: 入力の直積（ツール × キー別名 × ファイル形）を列挙し、テストが踏んでいないセルのうち**実装が分岐するもの**を挙げたか（分類2）— 実例: 別名マトリクスのテストが、唯一失敗するセル（別ツール × 別名キー）だけを欠いていた
- [ ] **契約 vs 契約の優先順位**: 新設した条項・上書き規則が、既存の省略規則（Task Size / express / inline-only）や参照側 skill の手順と衝突しないか、優先順位が両側に書かれているかを突合したか（分類8）— 実例: 非 waivable 条項を新設したが quick の security skip 規則と gate skill の手順が旧文言のままで、task size で条項を迂回できた

## security-reviewer checklist

> **スコープ**: LLM が diff の文脈を読んで判断できる脆弱性に集中する（B 層）。
> パターンマッチで検出可能な脆弱性（SQLi, XSS, Command Injection 等の A 層）は SAST ツールの責務。
> ビジネスロジック依存の認可不備（C 層）は requirements gate で認可モデルを AC に明示させることで対応する。

### 基本（常に確認）
- [ ] auth / authorization チェックの欠落、バイパス可能な前提がないか
- [ ] hard-coded credentials / unsafe logging / token・secret の露出がないか
- [ ] 未検証入力 / injection リスク / unsafe shell・file 操作がないか
- [ ] least privilege が維持されているか

### 実起動検証（hook / CLI / スクリプトが変更対象の場合のみ）
- [ ] 実行可能な entry point を fixture（`mktemp -d` の git repo + 最小 state）で実起動したか。正常系・迂回形の下限は implementation-reviewer checklist § 実起動検証 と同じ（正本はそちら）。security 側は **認証・権限・入力検証の迂回**（署名 / トークン検証を経ない経路、権限昇格経路、fail-closed の前段を飛ばす経路）を優先して試す。finding の evidence に実行コマンドと exit code / 出力を書く
- [ ] **fixture 内に副作用が閉じない** entry point（例: 外部ネットワーク書き込み / 認証情報を要求する / deploy・apply・push・課金を伴う / 共有リソースを変更する / ローカル環境を破壊的に変更する）は起動せず「対象外」と理由を明記したか
- [ ] 実起動できない場合は escalation 条件に該当する

### 文脈推論（diff を読んで判断。該当がなければスキップ）
- [ ] ユーザー入力がファイルパス構築に使われていないか（`../` 等の Path Traversal。sanitize / allowlist の有無を確認）
- [ ] 状態変更エンドポイント（POST/PUT/DELETE）に CSRF 保護があるか（フレームワークのミドルウェア / トークン検証の有無）
- [ ] NULL / undefined / error を返しうる関数の戻り値が未チェックのまま使用されていないか
- [ ] 整数演算でオーバーフロー / アンダーフローの可能性がないか（特に型キャスト、配列サイズ計算、金額計算）
- [ ] ファイル / リソース作成時のデフォルトパーミッションが必要最小限か（`0777` / public-read 等の過剰な設定がないか）
- [ ] check-then-act パターンで TOCTOU（Time of Check to Time of Use）の競合がないか（ファイル存在チェック後のオープン、権限チェック後の操作等）
- [ ] 信頼できないデータのデシリアライズがないか（`pickle.loads`, `yaml.load`, `JSON.parse` + `eval` 等。入力ソースが外部の場合は High）
- [ ] リソースアクセス時に、セッション由来の信頼できる値（org_id, user_id 等）で絞り込んでいるか（AC に認可要件がある場合のみ。連番 ID / UUID だけでのアクセス制御は不十分）
- [ ] untrusted input（webhook body / PR body / issue body / GitHub App payload / 外部 API 応答 / email 本文 / chat 本文）に対する照合ロジックが大文字小文字・空白・ゼロ幅文字・Unicode 正規化 bypass に耐えるか（正規化→照合の順序、NFKC 等の適用を確認）
- [ ] untrusted input の keyword filter / allowlist / denylist で regex flag（IGNORECASE 等）や anchor が正しく設定されているか
- [ ] untrusted input を元にした外部 API 呼び出し / shell 実行 / file 参照で、sanitize せずに渡している経路がないか
- [ ] ユーザー入力 URL / 外部取得 URL をそのままサーバーサイドでリクエストしていないか（SSRF。allowlist またはプライベート IP レンジ拒否の有無を確認）
- [ ] webhook signature / HMAC / token 検証が、ルーティング / 判定ロジックの**前段**で fail-closed に実行されているか（後段 bypass 不能）

### AI 固有リスク（LLM 呼び出し / エージェントを扱う diff がある場合のみ）

> **Why**: LLM を使うコードは入出力の信頼境界が曖昧になりやすい。通常の injection / eval リスクが LLM 経由で入り込む経路と、コスト爆発リスクを確認する。

- [ ] ユーザー入力がシステムプロンプトまたはユーザーメッセージに直接連結されていないか（プロンプトインジェクション。システムプロンプトへの埋め込みだけでなく、user ロールへの無検証連結も対象。role 分離・入力サニタイズの有無を確認）
- [ ] LLM の出力をそのまま HTML 埋め込み / SQL / shell に渡していないか（出力を untrusted input として扱っているか）
- [ ] LLM の出力を `eval` / `exec` 等で実行していないか（任意コード実行）
- [ ] エージェントが削除・送信・課金等の破壊的操作をユーザー確認なしで実行できないか（Excessive Agency）
- [ ] ループ内の LLM API 呼び出しに上限・レートリミットがあるか（コスト爆発。`max_tokens` の設定、イテレーション上限の有無を確認）

### 外部 API 入力型検証（外部 API / webhook payload を扱う diff がある場合のみ）

> **Why**: 外部 API に型・形式が不正な値を渡すと 422 等の silent failure で機能が死ぬ。逆に外部から受け取った payload を検証せずに処理すると injection / 認可 bypass の起点になる。field ごとに型・enum・regex・範囲のいずれかの明示検証があるかを確認する。

- [ ] 外部 API に `commit_id` / `sha` / `revision` 系を渡す経路では `[0-9a-f]{7,40}` の形式検証があるか（Git SHA は hex short 7〜full 40 字、それ以外は拒否）
- [ ] GitHub API の `side` には `LEFT|RIGHT` の enum 検証があるか（自由文字列を渡すと 422）
- [ ] `path` / `file` / `filename` に path traversal 検証（`..` / 絶対パス / NUL 文字 / シンボリックリンクの拒否）があるか
- [ ] `line` / `position` / `start_line` 等は integer 型で API に渡されるか（string を渡すと GitHub / GitLab 系 API で 422 になる）
- [ ] 数値系 field に範囲検証（負値拒否、上限）があるか
- [ ] 一般化: 外部 API / webhook payload の各 field に対し、**型・enum・regex・範囲のいずれか**の明示検証があるか。検証が無い field は finding として列挙する

### Design Schema Consistency（設計ドキュメント / スキーマ変更を含む diff がある場合のみ）

> **Why**: JSON payload や DB schema の duplicate field、SKILL.md の API 例示と実 API の型乖離は、実装後に silent failure として顕在化する。設計段階で見つければ実装を捨てずに済む。

- [ ] JSON payload / DB schema に同一情報の重複格納がないか（例: `pr_action` が top-level と `github.pr_action` の両方に存在、`user_id` が root と `actor.id` の両方）
- [ ] SKILL.md / design.md の API 例示と実 API の型が整合しているか（特に `"line": "42"` のような文字列 vs API integer の型不一致、`true`/`"true"` の boolean vs string 混在）
- [ ] Schema の field 追加 / 削除 / 型変更が `references/rollback-patterns.md` のどの route（`implementation_fix_only` / `design_detail_only` / `planning_rework_required`）に該当するか設計側で明示されているか
- [ ] 設計の field 名と実装の field 名が一致するか（snake_case / camelCase の揺れ含む）

### terraform 追加チェック（.tf / .tfvars / .tf.json が変更対象に含まれる場合のみ）

implementation-reviewer が追加で走査する。security-reviewer の担当（IAM 最小権限、secrets 混入、公開設定）とは重複しない。

- [ ] stateful リソース（DB、EBS、S3）に `prevent_destroy` が設定されているか
- [ ] `count` / `for_each` の変更で意図しない大量 destroy が発生しないか
- [ ] `moved` block が必要な rename / refactor で欠落していないか
- [ ] `lifecycle` block（`create_before_destroy`、`ignore_changes`）が適切か
- [ ] `ignore_changes` の過剰使用で drift を隠していないか
- [ ] provider / module のバージョンが固定（`~>` constraint）されているか
- [ ] 変数の型・デフォルト値・validation rule が妥当か
- [ ] outputs が呼び出し元の期待と整合しているか
- [ ] コスト影響の大きい変更（インスタンスタイプ、ストレージサイズ）が明示されているか
- [ ] backend / state 設定の変更で既存 state がロストするリスクがないか
- [ ] plan 結果（add/change/destroy）が確認されているか

## Escalation to subagent

以下のいずれかに該当する場合、該当 reviewer の `agents/*.md` を読んで subagent として起動する:

### 定量的な escalation 基準

| 条件 | escalation 先 | 理由 |
|------|-------------|------|
| 1 つの checklist 項目で issue が **3 箇所以上**に波及する | implementation-reviewer subagent | 局所判断では影響範囲を見落とす |
| security checklist で **Medium 以上の疑い**がある（確信が持てない） | security-reviewer subagent | 安全側に倒す。security は severity 調整しない |
| 複数の checklist 項目が **同じファイル/関数で交差**する | 該当 reviewer subagent | 相互作用の深掘りが必要 |
| user が明示的に **deep review** を要求した | 全該当 reviewer subagent | user intent を尊重 |

### escalation しないケース

- checklist 項目の判断が「該当なし」で完結する場合（スキップで十分）
- 単一箇所の明確な issue（Medium で report して終了）
- evidence が diff から直接引用できる場合（subagent に渡す必要がない）

## Reviewer Calibration（レビュー精度の記録）

差し戻し → 修正 → 再通過のサイクルから、チェックリストの精度を追跡する仕組み。

### 記録タイミング

`gdd-implementation-gating` が `changes_requested` → remediation → 再 review で `approved` に遷移したとき、`tasklist.md` の該当タスクの `#### Attempts` セクションに以下を追記する:

```
- [Review Calibration] <checklist 項目名>: <結果> (<詳細>)
  - finding: <元の指摘内容>
  - actual fix: <実際に行った修正>
  - was_valid: true/false
```

- `was_valid=true`: 指摘が正当で、修正が必要だった
- `was_valid=false`: 指摘が false positive で、修正不要だった（または別の理由で解消した）

### 活用方法（Reviewer Learning Loop）

蓄積された Calibration データは直接的にチェックリストを自動変更しない。次の 2 段階で活用する:

**Stage 1: 記録（completion 時）**
- `gdd-completion-check` が `done` 時に、false positive 率が高いパターンがあれば `docs/learned-patterns.md` の `Rejected Alternatives` に「この checklist 項目はこのプロジェクトで false positive が多い」と記録する

**Stage 2: 参照（次回 review 時）** — 手順は skills/gdd-implementation-gating/SKILL.md Step 5 を正本とする（重複定義しない）。

**Stage 3: 改善（手動）**
- チェックリスト自体の改善は、Calibration データの蓄積を見てプラグインメンテナが手動で行う

**Why:** reviewer の false positive が多いと、差し戻しループが増え、ユーザーの「AI が良い感じにやってくれる」体験が損なわれる。指摘の正当性を記録することで、プロジェクト固有の調整とチェックリスト自体の改善の両方に活かせる
