# Task Sizing: quick / standard

> **micro レベルのタスク**: 1 ファイルの設定値変更・typo 修正（behavior change なし）は GDD の gate を通す必要がない。Plan モードまたは直接作業で対応を推奨する。GDD を使う場合は quick として扱う。

> **所有**: quick / standard の判定基準、パスごとの artifact / reviewer / gate 省略ルール
> **上位正本**: `self-contained-contract.md`（fail-closed 条件、Verification schema）
> **参照元**: `gdd-brainstorming`、`phase-progression.md`、`reviewer-selection.md`

`gdd-brainstorming` で entry intent 解決後に判定する。ユーザーが明示した場合はそれに従う。

## 判定基準

**trivial** の条件（すべて満たす場合）:
- コード変更なし（`.md`、`.txt`、コメント行、設定値の文言変更のみ）、またはコード変更が 1 行以下かつ typo 修正
- ロジック・条件分岐の追加/変更なし
- behavior change なし
- テスト影響なし
- route / ownership の変更なし
- sensitive data / masking の変更なし
- セキュリティ境界に影響しない

**quick** の条件（すべて満たす場合）:
- 変更対象が 1〜5 ファイル程度
- route / ownership の変更なし
- sensitive data / masking の変更なし
- 外部 API / サービスとの新規接続なし
- セキュリティ境界に影響しない

quick はさらに **express** と **standard** に分岐する:

**quick (express)** の条件（すべて満たす場合）:
- 実装コードが 1-2 ファイル（テスト・ドキュメント・skill 設定の付随更新は数に含めない）
- 方針の選択肢が明白（1 案で十分、Options Exploration 不要）
- AC が 1-3 個
- design.md の詳細化が不要（requirements.md 内の実装方針で十分）

**quick (standard)** の条件:
- quick だが express 条件を 1 つでも満たさない

**Why express を分離した:** quick でもフル 8 phase を通すと 1-2 ファイルのバグ修正には ceremony が重い。express は最短経路（要件レビュー → human check → 実装 → impl-gate → done）を取りつつ steering 記録は残す。「trivial ほど軽くないが quick-standard ほど重くない」中間地帯を埋める。**express の WHERE 調査深さ**: 対象ファイルが自明な場合のみ即答可。自明でなければ事前調査か「N/A + 根拠1行」を明示し、WHERE を空欄・仮パスにしない

**standard** の条件（quick の条件を 1 つでも満たさない場合）:
- 変更対象が 6 ファイル以上、または
- route / ownership の変更あり、または
- sensitive data / masking の変更あり、または
- 外部 API / サービスとの新規接続あり、または
- セキュリティ境界に影響する

**Why quick を広げた:** 旧条件は user-visible change だけで standard に昇格させていたが、ボタン追加等の単純な機能追加は route/ownership/security に影響しないことが多い。waived ばかりの specialist reviewer を回すより quick の必須 reviewer だけで足りるため、重要な safety boundary だけを standard 条件に集約した。

## PR 規模上限

- 上限: **production 差分 2,000 行 / 25 ファイル**（テスト・artifact は別枠）
- production 差分の計測は **repo root で実行する**（`-- .` が cwd 相対のため、worktree 内のサブディレクトリで実行すると値が変わる）:
  ```
  cd "$(git rev-parse --show-toplevel)" && git diff --numstat <base>...HEAD -- . \
    ':(exclude).steering/**' ':(exclude)**/tests/**' ':(exclude)**/docs/**' ':(exclude)**/CHANGELOG.md'
  ```
  行数は追加 + 削除の合計、ファイル数は出力行に現れた path の件数
- 超過見込みが design-gating 時点で判明した場合、`Implementation Sequence Plan` の Stage 分割案を**必須提案**とする（提案なしで task-breakdown に進まない）

## パスの分岐フロー

```
ユーザー入力
    │
    ├─ trivial 条件をすべて満たす？
    │   └─ Yes → trivial（commit → done）
    │
    ├─ quick 条件をすべて満たす？
    │   ├─ express 条件もすべて満たす？
    │   │   ├─ Yes → quick (express)
    │   │   │   └─ Direct Intent 3点以上？ → Express + Direct Intent（最速パス）
    │   │   └─ No → quick (standard)
    │   └─ No → standard
    │
    └─ standard
```

### Direct Intent スコアの計算例

算出例（3 パターン）は `docs/references-archive/worked-examples.md` § Direct Intent スコアの計算例 を参照。算出ルール自体は `references/brainstorming-steps.md` § 7b が正本。

## パスごとの違い

以下は **standard 運用レベル**（デフォルト）の表。運用レベル（light / standard / strict）によるオーバーライドは `references/operation-levels.md` を参照。worktree 要否の判断軸は `references/workspace-policy.md` を参照。

| 項目 | trivial | quick (express) | quick (standard) | standard |
|------|---------|----------------|-----------------|----------|
| requirements.md | 不要 | Express テンプレート（`requirements-template-express.md`） | Summary Brief + 目的 + スコープ + AC + 実装方針（最小） | フル構成 |
| design.md | 不要 | 不要（requirements.md に方針を含める） | 詳細設計の粒度（`requirements-template.md`） | フル構成 |
| tasklist.md | 不要 | 不要（タスクが 1 つ） | 必要 | 必要 |
| gdd-requirements-gating | skip | `gdd-planning-reviewer`（design の観点の組は無し。非 waivable 条項該当時は `gdd-security-reviewer` も） | `gdd-planning-reviewer`＋下の行の組 | `gdd-planning-reviewer`＋下の行の組 |
| gdd-design-gating | skip | skip | `gdd-planning-reviewer` のみ（security skip。非 waivable 条項該当時は起動） | `gdd-planning-reviewer` + 該当 `gdd-security-reviewer` |
| gdd-task-breakdown | skip | skip | 必要 | 必要 |
| gdd-implementation-gating | skip | `gdd-implementation-reviewer` inline checklist only | `gdd-implementation-reviewer` inline checklist only（security skip・subagent escalation なし。非 waivable 条項該当時は起動） | `gdd-implementation-reviewer` + 該当 `gdd-security-reviewer` |
| worktree | 不要（`.steering/` 作成なし） | 必須 | 必須 | 必須 |
| security evidence | 不要 | skip（security boundary 変更なし前提） | `self-contained-contract.md` § Required Evidence Kind 判定 | `self-contained-contract.md` § Required Evidence Kind 判定 |
| human check | 不要 | 1 回（0-2 承認ポイント + 方向性承認） | 1 回（軽量） | 1 回 |
| Route / Ownership Matrix | 省略可 | 省略可 | 省略可 | 必須 |
| Sensitive Data / Masking | 省略可 | 省略可 | 省略可 | 必須 |
| Design Policy Discussion | 省略可 | 省略可 | optional（見出しは残し `N/A` と根拠 1 行） | 必須 |
| gdd-completion-check | skip | skip | `gdd-completion-reviewer` のみ | フル |

### 運用レベルによる主な差分

| 項目 | light での変更 | strict での変更 |
|------|---------------|----------------|
| requirements-gating | quick のみ（standard と同じ） | quick 以上で実施 |
| human check | quick 以上で実施 | quick 以上で実施（standard と同じ） |
| design-gating | quick を skip | quick で実施（standard と同じ） |
| security reviewer | 明示依頼時のみ | 常時起動 |
| completion reviewer | skip | quick 以上で実施 |
| worktree | [workspace-policy.md](./workspace-policy.md) を参照 | [workspace-policy.md](./workspace-policy.md) を参照 |

詳細は `references/operation-levels.md` を参照。

## Quick Standard Design Gate Optional

`quick (standard)` は原則として詳細設計の粒度で `design.md` を作成する。ただし、以下を **すべて満たす** 場合は詳細な design-gating を optional にしてよい。

**optional 条件（すべて必須）**:
- 変更対象が 1〜3 ファイルで、既存の類似実装が明確
- 新しい architecture / package manager / runtime / external service を導入しない
- auth / security / secret / PII / IAM / network egress / data migration に触れない
- public API、DB schema、ジョブ実行順序、永続データ形式を変えない
- codebase survey pack で関連ファイル、類似実装、テスト、ドキュメントを確認済み
- HITL に「設計 gate を軽量化する理由」と「検証方法」が明示されている

**optional にしてはいけない complexity signals**:
- 技術スタック選定、アーキテクチャ選定、依存管理、実行環境の変更
- frontend UI / E2E / Playwright でユーザー体験を確認する必要がある変更
- 影響範囲が不明、または `git grep` / test discovery で複数 module にまたがる可能性がある変更
- 監査、セキュリティ、外部公開、LLM 出力契約、PR review policy に関わる変更

**HITL 表示契約**:
- `設計 gate`: `light` / `full` / `not optional` のいずれかで出す
- `light` の場合は、なぜ light でよいかを 1〜3 行で書く
- optional 条件に迷いがある場合は `not optional` に倒し、通常の design-gating を実行する

## trivial パスのフロー

`trivial` は GDD の gate を一切通さない最短フローで進む:

1. `gdd-brainstorming`: trivial 判定を行い、ユーザーに確認する
2. trivial は `.steering/` を作成しない。作業履歴は commit message と会話ログに残す
3. 直接変更を実施する（typo 修正、コメント修正、設定値の文言変更）
4. commit message に変更理由を記載して完了

`requirements.md`、`design.md`、`tasklist.md`、`state.md` は作成しない。gate / reviewer / human check / security evidence / completion check はすべて省略する。trivial は `.steering/` を作成しないため、root checkout に未追跡 GDD artifact を残さない。worktree を使わず root のまま作業する判断根拠は [workspace-policy.md](./workspace-policy.md) を参照。

**Why**: typo 修正や README の文言変更に human check や artifact 生成を通すのは、タスク自体より overhead が大きい。superpowers と planning-with-files の設計に倣い、trivial な変更は planning system の対象外とする。

**昇格条件**: 作業中に以下が判明した場合は quick 以上に昇格する:
- コード変更が 2 行以上になる
- ロジック変更が含まれる
- テストへの影響がある
- behavior change がある

## Express Path のフロー

`quick (express)` は以下の最短経路を取る:

```
gdd-brainstorming（軽量: Express テンプレートで requirements.md を作成）
    ↓
gdd-requirements-gating（requirements の観点の planning reviewer）
    ↓
human-check-waiting（0-2 承認ポイント + 方向性承認）
    ↓（承認）
gdd-test-driven-development（RED）
    ↓
gdd-subagent-driven-implementation（GREEN + REFACTOR）
    ↓
gdd-implementation-gating（inline checklist only）
    ↓
done
```

**省略される工程と理由:**
- design-gating: design.md 自体が不要。実装方針は requirements.md に含まれる
- task-breakdown: タスクが 1 つだけなので分割不要。AC が直接 test target になる
- completion-check: impl-gate 通過で完結。包括レビューは省略

**Express も brainstorming の後に requirements-gating を通る。** 通過で `Requirements Review Status=approved` と、同じ evidence で `Design Review Status=approved` にする（design.md が無いので design の審査は無い。`references/requirements-gating-steps.md` § Express）。

### Express 昇格条件

Express 中に以下が判明した場合は quick (standard) に昇格する:

- 実装コードのファイルが 3 つ以上になった（テスト・ドキュメント・skill 設定の付随更新は数えない）
- 設計の選択肢が複数出てきた（Options Exploration が必要）
- AC が 4 つ以上に増えた
- security boundary への影響が見つかった
- route / ownership の変更が見つかった

昇格時は:
1. `Task Size` を `quick (express → standard)` に更新する
2. `design.md` を作成し、詳細設計の粒度で埋める
3. `Requirements Review Status=pending` に戻す
4. `Design Review Status=pending` に戻す
5. `Human Check Status` は現在値を維持する（承認済みなら `approved` のまま。突き合わせの例外は state-machine § Express 昇格）
6. `Approved Direction` 末尾に「Express から昇格のため再レビュー」を追記する
7. `Planning Reviewer Selection=pending` に初期化する
8. `Implementation Reviewer Selection` が存在する場合は削除する（`gdd-task-breakdown` で再作成）
9. `Resume From=gdd-requirements-gating` に更新する
10. 不足 phase（requirements-gating → design-gating → task-breakdown）を挿入する（着手の後に `request.md` に入力が足されていれば、先に brainstorming-steps § 9 の突き合わせを回し直す）

**Why（Step 3-4）**: Express の requirements-gating 通過時に Requirements / Design を `approved` に設定している（Design は design.md が無いままの `approved`）。昇格時に両方を `pending` に戻さないと「design の審査を通っていないのに approved」という矛盾 state が残る。
**Why（Step 7-8）**: Express の reviewer selection は design の観点の組を外しているため、昇格後に stale な selection 記録が残ると standard フローの reviewer 判定が狂う。詳細は state-machine § Express 昇格。

**降格は許可しない。** quick (standard) → quick (express) への変更はリスクが高い（reviewer を減らす方向の変更）。

## セルフレビューのリスク比例発火

push / PR 作成前のセルフレビュー（3 レーン・`dry` 収束条件）の Task Size 別発火条件は `references/self-review-lanes.md` § リスク比例発火表 を正本とする。ここでは重複記載しない。

## パスごとの並列実行可否

並列実行は standard タスク（タスク数 3+ かつ依存グラフから並列バッチが構成できる場合）でのみ有効化される。quick (express / standard) では並列化の効果が薄いため逐次実行のまま。

| パス | 並列実行 | 理由 |
|------|---------|------|
| trivial | 不可 | タスク分割自体がない |
| quick (express) | 不可 | タスクが 1 つ |
| quick (standard) | 不可 | タスクが少なく効果が薄い |
| standard | 可（条件付き） | タスク 3+ かつ並列バッチが構成できる場合 |

詳細は `references/task-breakdown-steps.md` § Parallel Execution と `references/phase-progression.md` § Parallel Execution を参照。

## すべてのパスで省略しないもの（trivial を除く）

- human check（必ず 1 回）
- AC の明示（`AC-1`, `AC-2`, ... の連番 ID 付き）
- fail-closed 条件
- `Verification` セクションへの結果記録
- worktree（判断軸は [workspace-policy.md](./workspace-policy.md) を参照）
- security evidence（`self-contained-contract.md` § Required Evidence Kind 判定に従う）

**trivial の例外**: trivial は上記すべてを省略できる。ただし fail-closed 条件（trivial 判定が誤りで昇格が必要な場合）は適用する。

## 判定の記録

- `requirements.md` の冒頭に `Task Size: trivial` / `Task Size: quick` / `Task Size: standard` を記録する（trivial の場合は `requirements.md` を作らないため、commit message に `[trivial]` を付記する）
- 途中で standard に昇格する場合は `Task Size: standard (upgraded from quick)` に更新し、不足セクションを追加する
- trivial から quick 以上への昇格時は `requirements.md` を新規作成する
- standard から quick/trivial への降格は許可しない（reviewer を減らす方向の変更はリスクが高い）

## 正式判定: Complexity Evaluation

Step 7 の暫定判定はユーザーの説明文から推測するだけであり、requirements を書く前にファイル数や AC 数は正確に分からない。**Complexity Evaluation は sizing の正式決定を「requirements.md の初稿を書いた後」に移す。** requirements.md の実際の内容から複雑さを 5 次元で評価し、最適な ceremony を選択する。

### 評価軸（5 次元）

requirements.md の内容から以下の 5 次元を評価する。各次元は **低 / 中 / 高** の 3 段階。

#### 1. Scope Breadth（影響範囲の広さ）

| レベル | 基準 |
|--------|------|
| 低 | 実装コード 1-2 ファイル（テスト・ドキュメント・skill 設定の付随更新は数えない）、単一モジュール内 |
| 中 | 変更ファイル 3-5、2-3 モジュール跨ぎ |
| 高 | 変更ファイル 6+、または 4+ モジュール跨ぎ |

**評価元**: `影響範囲` セクション、Problem Discovery の影響範囲スキャン結果

#### 2. AC Complexity（受入条件の複雑さ）

AC の**数**だけでなく**質**を見る。

| レベル | 基準 |
|--------|------|
| 低 | AC 1-3 個、全て単純な状態確認（「〜が表示される」「〜が返る」） |
| 中 | AC 4-6 個、または条件分岐を含む AC がある（「〜の場合は A、そうでなければ B」） |
| 高 | AC 7+ 個、またはエッジケース・並行処理・タイミング依存の AC がある |

**評価元**: `受入条件` セクション

#### 3. Integration Depth（外部連携の深さ）

| レベル | 基準 |
|--------|------|
| 低 | 既存 API レスポンスの解釈・表示変更のみ（新規呼び出しなし）、内部コードの refactor、単一モジュール内の変更 |
| 中 | 既存 API の呼び出し箇所追加、既存サービスへのクエリ変更、複数モジュール間の interface 変更 |
| 高 | 新規外部サービス接続、認証方式変更、IAM ポリシー追加、スキーマ変更 |

**評価元**: `制約・前提・依存関係` セクション、`外部依存の確認結果`

#### 4. Safety Surface（安全面の広さ）

| レベル | 基準 |
|--------|------|
| 低 | route/ownership 変更なし、sensitive data なし、セキュリティ境界に影響なし |
| 中 | 既存の認証/認可フローの軽微な変更、または internal-only の data handling 変更 |
| 高 | 新規の auth/secrets/PII 処理、public-facing API の変更、route/ownership 変更 |

**評価元**: `Route / Ownership Matrix`、`Sensitive Data / Masking Policy`

#### 5. Uncertainty（不確実性）

| レベル | 基準 |
|--------|------|
| 低 | Open Questions なし、設計方針が 1 案で確定 |
| 中 | Open Questions 1-2 件（実装詳細レベル）、または Design Policy Discussion で 2 案比較 |
| 高 | Open Questions 3+ 件、またはスコープ・方針レベルの未確定事項がある |

**評価元**: `Open Questions`、`Design Policy Discussion`、`Human Check Questions`

### 判定ルール

```
全て「低」                    → quick (express)
高が 0 個                     → quick (standard)（中が何個あっても quick のまま）
高が 1 個以上（Safety 以外）  → standard
Safety Surface が「高」       → standard（他の次元に関係なく）
```

**Why**: 「中」は既存の reviewer / gate で十分捕捉できるレベルの複雑さ。standard に昇格させる根拠は「高」が 1 個以上、または Safety Surface 高のみ。中が 3+ あっても standard に倒さない。これで過剰な standard 化を防ぐ。

### 写像表

| パターン例 | 結果 | 理由 |
|-----------|------|------|
| Scope低, AC低, Integration低, Safety低, Uncertainty低 | express | 全て低。最短経路で十分 |
| Scope低, AC中, Integration低, Safety低, Uncertainty低 | quick (standard) | AC が条件分岐を含む。reviewer チェックが有効 |
| Scope中, AC低, Integration低, Safety低, Uncertainty低 | quick (standard) | 複数モジュール。design review が有効 |
| Scope低, AC低, Integration低, Safety高, Uncertainty低 | standard | Safety が高い時点で standard 確定 |
| Scope中, AC中, Integration中, Safety低, Uncertainty中 | quick (standard) | 高が 0 個。中が複数でも quick のまま |
| Scope高, AC高, Integration高, Safety高, Uncertainty高 | standard | 全て高。フルゲート必須 |

### 暫定判定との比較

暫定 sizing（Step 7 の推測）と Complexity Evaluation の結果が異なる場合:
- **一致**: そのまま進む
- **推奨が重い方向**: 昇格を提案し理由を表示。ユーザーが承認すれば昇格
- **推奨が軽い方向**: 降格は提案しない（既に重い方の artifact 構成で作業しているため）

ユーザーの明示指定は Complexity Evaluation より常に優先する。

### 表示例

**暫定と一致:**
```
タスクサイズ: quick (express)
複雑さ評価: Scope低 / AC低 / Integration低 / Safety低 / Uncertainty低
→ 暫定判定と一致。express で進めます
```

**昇格提案:**
```
タスクサイズ: quick (standard) ← express から昇格
複雑さ評価: Scope低 / AC中 / Integration低 / Safety低 / Uncertainty低
理由: AC-3 に条件分岐（「管理者の場合は全件表示、一般ユーザーは自分のみ」）を含む。
      AI reviewer による AC 品質チェックが有効
→ express のまま進めたい場合は「express で」と指定してください
```

### 評価結果の記録

評価結果は `requirements.md` の `Task Size` 行の直後にコメントとして記録する:
```markdown
Task Size: quick (standard)
<!-- Complexity: Scope低 / AC中 / Integration低 / Safety低 / Uncertainty低 -->
```

## 判定の具体例

**quick (express) の例**:
- 既存関数にバリデーション追加（実装 1 + テスト）
- 1 画面のテキスト表示変更（UI 1 + テスト）
- 設定値の追加（config 1 + テスト）

**quick (standard) の例**:
- スキルの出力フォーマット拡張（実装 1-2 + テスト + ドキュメント・skill 設定）
- 既存エンドポイントへのクエリパラメータ追加（実装 2 + テスト + スキーマ）
- 既存 API のレスポンス解釈拡張（新規呼び出しなし）
- 複数ファイルの表示ロジック統一

**standard の例**:
- 新規外部 API 統合（認証 + IAM + 実装 + テスト）
- スキーマ変更を伴う機能追加（マイグレーション + モデル + API + UI）
- 認証フローの変更
- route / ownership の変更を伴う機能追加
- sensitive data の新規取り扱い

## ユーザー明示

- ユーザーが「typo 修正」「コメント修正」「文言変更」などと言った場合は trivial を提案してよい
- ユーザーが「設定値変更」「1 行だけ」などと言った場合は trivial を提案し、コード変更があるなら quick を提案してよい
- ユーザーが「軽い変更」「ちょっとした修正」「1 ファイルだけ」などと言った場合は quick を提案してよい
- ユーザーが「しっかりやりたい」「フルで」などと言った場合は standard にする
- 判定が微妙な場合はユーザーに確認する
