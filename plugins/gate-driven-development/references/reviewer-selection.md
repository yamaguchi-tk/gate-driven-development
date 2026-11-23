# Reviewer Selection

> **所有**: reviewer 選定ルール、自動選定表、record format、gate rules
> **上位正本**: `self-contained-contract.md`（review 契約）
> **参照元**: `gdd-requirements-gating`、`gdd-design-gating`、`gdd-implementation-gating`、`gdd-completion-check`

`gate-driven-development` の formal reviewer を「毎回フルセット起動」ではなく「必要な reviewer だけ起動」に切り替えるときの正本。

## レビュー関連 Skill の責務分類

GDD には4つのレビュー関連 skill がある。役割が混同されやすいため、分類を明確にする。

| 分類 | Skill | 役割 | gate 状態を変更するか |
|------|-------|------|---------------------|
| **Formal Gate** | `gdd-implementation-gating` | state machine が自動 route する必須レビュー。pass/fail が次の phase 遷移を決定する | Yes（Review Status を更新） |
| **Companion** | `gdd-requesting-code-review` | ユーザーが明示的に依頼する追加 advisory review。formal gate とは別レーン | No（advisory のみ） |
| **Triage** | `gdd-receiving-code-review` | companion review の指摘を検証し、valid な指摘だけを debugging / design-gating に route する | No（route 先の skill が更新） |
| **PR Review** | `gdd-pr-review` | PR 作成前後の generic review。completion 後の Post-Completion PR Flow からも呼ばれる | No（advisory のみ） |
| **Dialectic Lane** | `references/dialectic-review.md` | prompt / skill / review policy / 人間向け出力など、採否・severity・表示品質が揺れやすい論点を独立評価→相互レビュー→最終統合で収束させる補助 lane | No（補助証跡のみ） |

## Consolidated Reviewers (4種)

| reviewer | 概要 | 起動 |
|----------|------|------|
| `gdd-planning-reviewer` | 要件の完全性・明確性・AC 品質・より良い実装パターン・設計の整合性・実現可能性・運用リスク | 常時 |
| `gdd-implementation-reviewer` | バグ・保守性・AC 準拠・契約遵守・信頼性・性能・可観測性・rollout/rollback 安全性。Terraform ファイルが変更対象に含まれる場合は追加の terraform checklist も走査 | 常時 |
| `gdd-security-reviewer` | セキュリティ・プライバシー・secrets・trust boundary | 条件 |
| `gdd-completion-reviewer` | 最終横断レビュー・コード品質・cross-cutting リスク | 常時 |

## Reviewer Responsibility Matrix

「誰が・いつ・何を見るか」の交差表。スコープの重複は意図的（異なるフェーズで異なる artifact を検査するため）。

| 観点 | planning-reviewer | implementation-reviewer | security-reviewer | completion-reviewer |
|------|:-:|:-:|:-:|:-:|
| **起動フェーズ** | req-gate, design-gate | impl-gate | design-gate, impl-gate (条件), req-gate (express の非 waivable 時) | completion-check |
| **AC 完全性・測定可能性** | **Primary** (要件段階) | Secondary (コード vs AC) | - | Final check (AC Drift) |
| **設計の整合性・実現可能性** | **Primary** | - | - | - |
| **より良い実装パターン** | **Primary** (設計段階) | - | - | - |
| **バグ・ロジック正当性** | - | **Primary** | - | - |
| **保守性・コード品質** | - | **Primary** | - | Advisory |
| **AC 準拠（コード実装）** | - | **Primary** | - | Cross-check |
| **信頼性・性能・可観測性** | - | **Primary** | - | - |
| **Rollout / Rollback 安全性** | - | **Primary** | - | - |
| **認証・認可** | - | - | **Primary** | - |
| **Secrets / PII / trust boundary** | - | - | **Primary** | - |
| **入力検証・injection 防止** | - | - | **Primary** | - |
| **Cross-task 横断リスク** | - | - | - | **Primary** |
| **Verification 証跡の完全性** | - | - | - | **Primary** |
| **Terraform 追加チェック** | - | **Primary** (.tf 変更時) | - | - |

**読み方**:
- **Primary**: その観点の主責任者。finding を report する義務がある
- **Secondary**: Primary が見た上で、別 artifact/フェーズの視点から補完する
- **Cross-check / Final check**: 後段で drift や漏れを検出する最終防衛線
- **Advisory**: 必須ではないが、発見した場合は report する
- `-`: その reviewer の責務外

## Lazy Loading

reviewer agent の定義（`agents/*.md`）はコンテキストに常時ロードしない。以下の手順で必要時だけ読む。

1. gate skill が本ドキュメントの Gate Rules に基づいて `selected` / `waived` を決定する
2. `selected` になった reviewer の agent 定義だけを `agents/` から読み込む
3. `waived` の reviewer は agent 定義を読まない

## Security Reviewer 非該当リスト

design-gate / impl-gate（と express の req-gate）で `gdd-security-reviewer` を条件起動する際、diff の形が以下のいずれかに一致すれば `waived` にしてよい。ただし次の非 waivable 上書き条項のいずれかに該当する場合は、diff の形に関わらず `selected` にする。**本節が正本であり、§ Quick Selection Table / § Gate Rules は本節を参照するだけで複写しない**。

### 非該当リスト（waived 候補）

- `test_only`: 本番コード変更を含まないテスト専用の追加・変更。ただし security guard の非回帰検出器（deny/allow 境界を固定するテスト）を追加・変更・削除する場合は該当しない
- `docs_only`: ドキュメント・CHANGELOG のみの変更
- `config_only`: 設定値のみの変更 / `generated_only`: 生成物のみの変更（lockfile 等）

### 非 waivable 上書き条項（非該当リストより優先。1 つでも該当すれば `selected`。review を回す gate での選び方で、impl-gating で review を回すかは `task-breakdown-steps.md` § Judgment Change が決める）

1. **対象物ベース**: 変更対象が security guard / 認証 / 認可 / 秘匿 / 権限境界 / deny・allow 境界 / guard 定数・閾値そのものである
2. **パスベース**: `hooks/` 配下、または hook / gate が実行時に呼び出すスクリプトとその lib（`hooks/scripts/`、`hooks/scripts/lib/`、`scripts/`、`scripts/lib/`、`tests/checks/` を含むが列挙は exhaustive ではない）を触る。無効化用 env（例: `GDD_SKIP_PRE_PUSH_GATE`）を `.claude/settings.json` の `env` やシェル profile へ設定する差分も含む
3. **契約文ベース（規則。ファイル列挙ではない）**: agent / hook が実行時に読む指示文・契約文（reviewer agent 定義、gate skill 本体、deny・allow / fail-closed 契約を定義する `references/*.md`、および reviewer 選定契約そのもの — どの reviewer をいつ起動・waive するかを定める記述）を触る変更は `docs_only` / `config_only` に該当しない。**`references/reviewer-selection.md` 自身**（本節・§ Quick Selection Table・§ Gate Rules）と `references/task-sizing.md` の reviewer 省略表を含む（列挙は exhaustive ではない）
4. **既存節との優先順位**: § Gate Rules の「必ず selected」節が最優先。非該当リストはそれを覆さない。本条項は `task-sizing.md` の quick / express の security skip にも優先する
5. **「テスト専用」の限定**: 上記非該当リストの `test_only` の限定と同じ（重複記載しない）

### Untrusted-Input 語彙リスト（design-gate / impl-gate 共通正本）

以下のいずれかが requirements / design、または current task の diff / AC に登場する場合、`gdd-security-reviewer` を必ず `selected` にする（requirements §5「セキュリティ影響: 低」等の自己申告だけでは `waived` にできない。impl-gate で waive するには代替の trust boundary 証明を reason に書く）: webhook body / payload / signature 検証（GitHub / GitLab / Slack / 任意の external service）、PR body / PR title / PR description / issue body / issue title / issue comment / review comment、GitHub App / GitLab App の event payload・installation event / installation token の取り扱い、外部 API（REST / GraphQL / gRPC）経由の任意ユーザー入力とその parsing / validation / sanitize / 照合、email 本文 / subject / attachment・chat 本文・フォーム入力、外部ファイル取り込み（upload / import / fetch したファイルの本文・ファイル名・metadata）、regex / pattern matching を外部入力に適用するロジック、allowlist / denylist / keyword filter の実装。

`waived` と記録するときの `reason` 書式は § Record Format を参照。

## Quick Selection Table

| Gate | reviewer |
|------|----------|
| Requirements Gate | `gdd-planning-reviewer`（常時）。design-gating を通るタスクでは、design の観点の組（`gdd-planning-reviewer` を design phase の文脈で 1 本、`gdd-security-reviewer` は条件）も同じ Round に並行に起動する。quick (express) では security だけを非 waivable 時に起動する（詳細は `## Gate Rules` § `gdd-requirements-gating`） |
| Design Gate | `gdd-planning-reviewer`（常時）、`gdd-security-reviewer`（条件。詳細は `## Gate Rules` § `gdd-design-gating`）、`dialectic review lane`（prompt/skill/policy/表示品質、補助 lane） |
| Implementation Gate | `gdd-implementation-reviewer`（常時。`.tf` / `.tfvars` / `.tf.json` 変更時は terraform 追加チェックも走査）、`gdd-security-reviewer`（条件。詳細は `## Gate Rules` § `gdd-implementation-gating`） |

Task Size ごとの reviewer 省略ルールは `references/task-sizing.md` の「パスごとの違い」テーブルを正本とする。要約: quick は常時必須 reviewer のみ（security skip）、standard はフル適用。

## Core Rules

- reviewer を減らす前に、必ず selection を canonical artifact に記録する
- 迷ったら reviewer を減らすより追加する。ただし本原則は `## Security Reviewer 非該当リスト` の非該当リスト・非 waivable 上書き条項のどちらにも当たらず、security-sensitive の判定が本当に割れる場合にのみ適用する
- `waived` は「current scope に非該当」を意味する。real issue の受容には使わない
- gate は reviewer selection が空のまま開始しない
- 同じ `Current Task`（Gate Batch では同じ batch）を再レビューするときは、scope が変わらない限り前回の `Implementation Reviewer Selection` を再利用する
- 同じ `Current Task` で selection を変える場合は `selection_change_reason` を残す
- reviewer の指摘が競合するときは、まず correctness / security / operational feasibility / rollback safety を優先する
- 優先順位だけで解けない trade-off は局所最適で潰さず、人間判断へ戻す
- **Cross-steering lineage**: 同一 root feature 系統（supersede / hotfix / amendment）の過去 reviewer 判定は `references/reviewer-lineage.md` の optional `Reviewer Lineage` section に記録し、新 steering の reviewer selection で判断材料として参照する。自動継承はしない

## Record Format

### `state.md`

`Gate Status` 付近に次を残す。

- `Planning Reviewer Selection`
  - `gdd-planning-reviewer`: `selected` または `waived`（requirements gate では、design の観点の 1 本も `gdd-planning-reviewer（design の観点）`: `selected` または `not_applicable` として別に記録し、`not_applicable` の reason には § Gate Rules § `gdd-requirements-gating` の (1)・(2) のどちらに当たらないかを書く）
  - `gdd-security-reviewer`: `selected` または `waived`（requirements gate では design の観点の組を起動するとき、または quick (express) で非 waivable 上書き条項に当たるときだけ記録する）
  - 各 reviewer の reason
  - `updated_by`
  - `updated_at`

### `tasklist.md`

`Review Status` 付近に次を残す。

- `Implementation Reviewer Selection`
  - `gdd-implementation-reviewer`: `pending` / `selected` / `waived`
  - `gdd-security-reviewer`: `pending` / `selected` / `waived`
  - 各 reviewer の reason
  - `selection_change_reason`
  - `updated_by`
  - `updated_at`

### waived 記録時の `reason` 書式

`state.md` の `Planning Reviewer Selection` と `tasklist.md` の `Implementation Reviewer Selection` のどちらも、`gdd-security-reviewer` を `waived` にする場合は `reason` に次の 2 要素を含める。

1. 該当した非該当リストの項目名（`test_only` / `docs_only` / `config_only` / `generated_only`）
2. 非 waivable 上書き条項 1〜5 のいずれにも当たらないことを確認した旨

## Gate Rules

### `gdd-requirements-gating`

- always:
  - `gdd-planning-reviewer`（requirements の観点）
- design の観点の組（そのタスクの design-gating が起動する組と同じ。`gdd-planning-reviewer` を design phase の文脈でもう 1 本と、下の § `gdd-design-gating` の条件に当たる `gdd-security-reviewer`。quick (standard) の security は、`references/task-sizing.md` § パスごとの違い のとおり非 waivable 条項に当たるときだけ）を、次の 2 つをどちらも満たすときに同じ Round に並行に起動する（満たすかを決めきれないときは起動する）。(1) タスクの経路に design-gating がある（同じ表で skip でなく、§ Quick Standard Design Gate Optional で外していない）。(2) `requirements.md` に `Broad Requirement: true` が無い（広い要件の設計は、human check で scope を選んだ後に design-gating の Step 5 で書く）。design-gating は今までどおり回す（requirements の時点の design.md を見る。human check の後の書き換えは design-gating が見る）
- quick (express) では design の観点の組を起動しない。`gdd-security-reviewer` は、§ Security Reviewer 非該当リスト の「非 waivable 上書き条項」に当たるときだけ同じ Round に起動する（quick (standard) の design-gating と同じ線。`references/requirements-gating-steps.md` § Express）。security には design の観点の組と同じ 1 枚を、`- Phase: design（gdd-requirements-gating から。human check の前）` の行を付けて渡す。昇格の後の再入でも design の観点の組は起動しない（Round 1 で起動していない）ので、`Planning Reviewer Selection` には `not_applicable` と記録する

### `gdd-design-gating`

- always:
  - `gdd-planning-reviewer`
- select `gdd-security-reviewer` when:
  - security boundary, secret handling, auth/authz, untrusted input, external exposure, data sensitivity, PII, compliance が設計論点になる
  - prompt contract / output contract の変更、masking policy の enforcement point が設計論点になる
  - `## Security Reviewer 非該当リスト` § Untrusted-Input 語彙リストのいずれかが requirements / design に登場する場合は必ず `selected`
  - 非該当リストと非 waivable 上書き条項も同節を参照する

### `gdd-implementation-gating`

- always:
  - `gdd-implementation-reviewer`
- select `gdd-security-reviewer` when（Gate Batch では current task を batch のどれかの task と読む）:
  - auth/authz, secrets, untrusted input, filesystem, shell, network, permissions, data exposure, least privilege が current task にある
  - prompt への sensitive value 投入、model output の sanitize / redact / reject、masking policy の変更が current task にある
  - `## Security Reviewer 非該当リスト` § Untrusted-Input 語彙リストのいずれかが current task の diff / AC / requirements にある場合は必ず `selected`
  - 非該当リストと非 waivable 上書き条項も同節を参照する
- terraform checklist（`gdd-implementation-reviewer` の追加走査、独立 reviewer ではない）:
  - current task の変更対象に `.tf` / `.tfvars` / `.tf.json` ファイルが含まれる場合に走査する
  - 詳細は `references/inline-review-checklists.md` § terraform 追加チェックを参照

## Completion Rule

- `gdd-completion-reviewer` は standard・quick (standard)・quick (express → standard) で常時必須。quick (express) では completion-check 自体をスキップするため起動しない
- `gdd-completion-check` では、`Planning Reviewer Selection` が `state.md` に残っていることを確認する
- `Implementation Reviewer Selection` は per-task 一時状態であり、全 task が `Completed Tasks` に到達していること（= 各 task が `gdd-implementation-gating` を通過した事実）を監査根拠とする
- `Planning Reviewer Selection` で record が無い、reason が曖昧、scope と selection が食い違う場合は少なくとも `Medium` 扱いにし、未解決のまま `done` に進めない
- prompt / skill / review policy / 人間向け出力 / severity calibration を変更した standard タスクでは、`gdd-completion-check` が `Dialectic Review Summary` の有無と final decision の反映を確認する。これは formal reviewer 追加ではなく evidence check として扱う
