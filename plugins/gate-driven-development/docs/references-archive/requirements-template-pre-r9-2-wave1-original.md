# Requirements Template

> **所有**: `requirements.md` と lightweight `design.md` skeleton のセクション定義
> **上位正本**: `self-contained-contract.md`
> **参照元**: `gdd-brainstorming`、`gdd-requirements-gating`

`brainstorming` が `requirements.md` と lightweight `design.md` を作成する際のテンプレート定義。

## HITL Outcome Audit

Approved Direction と最終成果物を照合し、この承認をきっかけに AI が自走した結果、期待どおりの結果になったかを確認する。結果は `match / mismatch / unverified` で記録する。mismatch / unverified が残る場合は completion を通さず、必要に応じて `human_recheck_required` または planning route に戻す。

## Size-Specific Template Dispatch

このファイルは full requirements template の詳細正本である。`quick (express)` では、まず `references/requirements-template-express.md` を使う。express template に無い情報が必要になった場合だけ、この full template の quick standard / standard section に昇格する。

- `quick (express)`: `references/requirements-template-express.md`
- `quick (standard)`: このファイルの `Quick Standard Requirements 最小構成`
- `standard`: このファイルの full template

**Why**: express で full template を読み始めると、変更規模に対して ceremony が過剰になり、GDD の軽量性と human check の読みやすさを損なう。サイズ別テンプレートを先に選び、必要になった時だけ昇格する。

## Summary Brief（4 層構造）

`requirements.md` と `design.md` の両方で冒頭に配置する。standard では 4 層すべて、quick では 3 層（Honest Limitations は任意）。

```markdown
## Summary Brief

### 一言
<対象>に対して<目的>を実施する

### 判断材料
- 確定事項: ...
- 未確定事項: ...
- やらないこと: ...
- 外部依存の確認結果: ...
- 設計方針: ...
- 実行・評価環境: <実際に動く host/runtime と、release gate として扱う検証レーン>

### ズレ確認
- 完了条件の変換: <Completion Condition Trace のうち refined / split / deferred / dropped / added / unresolved だけを短く要約。kept は原則省略>
- テスト化確認: <Completion Testability Matrix のうち needs-clarification / e2e-required / external-evidence-required / non-testable-deferred と、後戻りが高い test interpretation だけを短く要約>
- 既存実装の調査状況: <Existing Implementation Survey の complete / partial / not_run、再利用する既存経路、未調査でズレ得る点を短く要約>
- Engineering Baseline: <architecture / code structure / dependency manifest / lock file / runtime / install command / test command / CI command の確認状況。未整備なら、今回どこまで整えるかを短く要約>
- アーキテクチャ提案: <Architecture Recommendation Gate の採用案、却下案、構造上の手戻りリスクだけを短く要約>
- 依存・実行環境: <Dependency / Runtime Baseline のうち、package manager / runtime / install / test / CI の再現性に関わる判断だけを短く要約>
- 技術スタック確認: <Technology Stack Fit Matrix / Adopted Technology Stack Trace のうち vendor official integration / 既存 repo 標準 / MCP・CLI・SDK・API 等の access method / credential backend / multi-tenant 境界がズレると手戻りが大きいものだけを短く要約>
- 段階連続性: <Implementation Sequence Plan のうち Stage 間の受け渡し、依存、後続で消費される生成物がズレると後戻りが大きいものだけを短く要約>
- 作り方の重要判断: <Implementation Approach Trace のうち repo 分割 / import-recreate / 既存再利用 / public-private / CI/CD 方針など後戻りが高い論点だけ>
- Plan Direction LLM Review: <方針を HITL に出す前の LLM レビューで直した点 / 残す判断点だけを短く要約>
- Adversarial Requirements Review: <反対仮説 / ズレリスク / 採用した修正 / 残すリスクのうち、HITL で人間が見るべきものだけを短く要約>

### 承認ポイント
1. **<カテゴリ>**: <判断対象の説明>
   - 背景: <なぜこの判断が必要か — Problem Discovery で得た具体的事実を 1-2 文で>
   - 変更前: <現在の挙動・状態>
   - 変更後: <採用案を適用した場合の挙動・状態>
   - 採用案: <AIが選んだ案とその理由>
   - 代替案: <却下した案とその理由>
   - → OK / 別案希望

2. **<カテゴリ>**: <判断対象の説明>
   - 背景: <なぜこの判断が必要か>
   - 変更前 → 変更後: <1 行で対比できる場合はこの形式でもよい>
   - 内容: <承認してほしい内容>
   - リスク: <承認した場合のリスクと対策>
   - → OK / 修正依頼

### Honest Limitations
<承認ポイントの直後に配置する。standard で必須、quick は任意。詳細は下記「Honest Limitations」節を参照>
- <この設計で確認できないこと / ユニットテストでは担保できない部分 / デプロイしないと分からない部分>
```

- 「一言」は 1 行で何をするかを書く。人間が最初にこれだけ読めば話が分かる粒度にする
- 「判断材料」は確定/未確定/非スコープ/外部依存/設計方針を箇条書きで並べる
- 「ズレ確認」は全文レビューを避けるための圧縮欄。requirements.md 本文には詳細 trace を残し、human check では「思ったんと違う」になりやすい完了条件変換と作り方の重要判断だけを出す
- 「承認ポイント」は human check で判断してほしい事項を番号付きで書く（原則 3〜5 件）
  - 各ポイントは **カテゴリ**（scope / 方針 / リスク / 権限 / データ等）を太字で先頭に置く
  - **背景**: なぜこの判断が必要なのかを具体的事実で示す。「ページネーションの方式」ではなく「全件取得で 1000 件超えると 5 秒以上かかるため、取得方式の変更が必要」のように書く
  - **変更前 → 変更後**: 現状と採用案適用後の対比を示す。人間が「何が変わるか」を一目で把握できるようにする
  - AI が選んだ案・理由・代替案を提示し、人間は「OK / 別案希望 / 修正依頼」で判断する
  - 人間がコンテキストを読み込まなくても、承認ポイントだけ読めば判断できる粒度にする
- 「方向性承認」を承認ポイントの末尾に 1 件追加する（原則必須）:
  ```markdown
N. **方向性**: <この変更の目的を 1 行で>
   - 自走範囲: <この方向性と矛盾しない限り、E2E で発見された問題の修正は AI が自律判断してよい>
   - 自走上限: <今回の承認で AI が進めてよい最大到達点。例: 実装完了まで / PR 作成まで / デプロイ準備まで / デプロイ実行は別承認>
   - Post-PR Completion Scope: <none / マージして再学習まで / post-merge verification / relearning まで。ユーザーが明示した場合は PR 作成までに丸めない>
   - Post-PR 操作承認: <manual merge required / merge approved / deploy approval required / Requires explicit operation approval>
   - 人間に戻す条件: <方向性自体が変わる場合 / AC の根本的な追加・削除 / セキュリティ要件の新規発生>
   - → OK / 自走範囲を制限したい
  ```
  - 人間が「OK」と答えた場合、`state.md` に `Approved Direction` として方向性と自走範囲を記録する
- 人間が自走範囲または自走上限を制限した場合、その制限を `Approved Direction` に記録し、制限を超える変更は human check に戻す
  - **Why:** 途中で E2E 起因の問題が連鎖的に発覚する場合、毎回 human check に戻すと人間確認が爆発する。方向性レベルの承認を先に取ることで、詳細の判断は AI に委ねられる
- 「Honest Limitations（この設計で確認できないこと）」を承認ポイントの直後に 1 セクション追加する（standard で必須、quick は任意）:
  ```markdown
  ### Honest Limitations
  - <この設計で確認できないこと / ユニットテストでは担保できない部分 / デプロイしないと分からない部分>
  - <代替手段で十分に担保できる範囲がある場合はそれも明示>
  - 例:
    - SKILL.md のプロンプト変更の効果は AgentCore Runtime の実行なしには確認できない
    - dev 環境の Claude 動作確認はユニットテストでは担保できない（8 割は担保できるが 2 割は実環境必須）
    - Terraform plan は syntax / 参照整合性は確認できるが、apply 後の実挙動は確認できない
  ```
  - 「できる / できない」の切り分けは率直に書く。「多分できる」「たぶん大丈夫」は `未確定事項` に回す
  - Honest Limitations を読んだ人間が **scope reduction**（範囲を狭める）や **後工程の E2E 計画** を判断できる粒度で書く
  - **Why:** AI が「できることだけ」を提示すると、人間は「できないこと」に気付けず過剰なスコープで承認してしまう。率直な自己制限の明示により、人間は「この設計で本当に十分か / 何を後工程に回すか / scope を縮小すべきか」を先に判断できる。手戻りの最大の原因は「後で気付いた担保不足」なので、最初に明示する（superpowers 観察パターン）

## Trace セクション

brainstorming では、ユーザー入力をそのまま固定せず、要件として解釈・分割・縮小・延期する。そのため requirements.md には、初期入力から承認対象への変換履歴を残す。HITL ではこの詳細を全文表示せず、`human-check-template.md` の `ズレ確認` に高リスク差分だけを載せる。

```markdown
## User-Stated Completion Conditions

- USC-1: <ユーザーが最初に言った完了条件を、できるだけ原文に近く保存する>
- USC-2: <既存実装状態・仮置き・手動設定済みなど、完了判断に影響する初期状態も含める>

## Completion Condition Trace

| ID | User-stated condition | Refined condition | Status | Reason | Maps to |
|---|---|---|---|---|---|
| USC-1 | <原文> | <AI が AC 化できる粒度に解釈した内容> | kept / refined / split / deferred / dropped / added / unresolved | <なぜ変えたか> | AC-1 / Non-Goal / Deferred / Honest Limitations / Open Question |

## Post-PR Completion Scope

| User-stated post-PR condition | Scope decision | Operation approval | Verification / evidence | Stop condition |
|---|---|---|---|---|
| <例: マージして再学習まで> | <post-merge verification / relearning として保持。PR 作成までに丸めない。自走上限を PR 作成までへ自動降格しない> | <merge / deploy / apply / AWS write は Requires explicit operation approval。手動 merge 後の read-only 検証は継続可。1 操作ごとの明示承認を維持> | <何を read-only に確認するか> | <未承認 write が必要なら `<gdd-stop reason="blocked">`> |

## Verification Sanity Check

検証を実行する前に、その検証セットアップが目的の改善を実際に計測できる構造かを確認する。以下をチェックする:

- false pass の防止: 壊れた実装が検証を通過してしまわない設計になっているか（検証が本当に壊れた状態を検出できるか）
- 改善前後で観測値が実際に変わる構造か（不変量を計測しているだけでないか）
- 検証環境 / ハーネス / ツールが本番と同じ前提で動いているか（eval ハーネスの MCP 無効化等の制約を確認済みか）

## Completion Testability Matrix

| AC ID | Source condition | Testable claim | Test level | Planned RED / E2E | Evidence required | Status |
|---|---|---|---|---|---|---|
| AC-1 | USC-1 | <Yes/No で観測できる claim> | unit / contract / integration / e2e / manual-evidence | <先に書く RED test / E2E smoke / executable verification> | <exit code / log / screenshot / external evidence> | testable / needs-clarification / e2e-required / external-evidence-required / non-testable-deferred |

## Implementation Approach Trace

| Issue | User signal / current state | AI provisional approach | Alternatives | Status | Goes to |
|---|---|---|---|---|---|
| <作り方の重要論点> | <ユーザーの希望・既存実装状態・仮置き状態> | <AI の仮決定> | <却下案・未採用案> | accepted / design-gating / human-check / deferred / unresolved | Human Check / design-gating / Non-Goal |

## Existing Implementation Survey

| Area | What was checked | Existing path / pattern found | Reuse decision | Evidence | Completeness |
|---|---|---|---|---|---|
| repo structure | <主要ディレクトリ・関連 package / skill / command / runtime> | <既存実装の場所 or not_found> | reuse / extend / do-not-use / new-required / unknown | <rg / ls / test / doc の要点> | complete / partial / not_run |
| related files | <ユーザーが名指しした対象・語句> | <該当ファイル> | reuse / extend / do-not-use / new-required / unknown | <根拠> | complete / partial / not_run |
| similar implementation | <同種責務・同じ出力先・同じ workflow> | <類似実装> | reuse / extend / do-not-use / new-required / unknown | <根拠> | complete / partial / not_run |
| read/write surface | <read / write / persistence / API / MCP / wrapper / adapter / log / audit> | <既存 wrapper / adapter / policy / client / command> | reuse / extend / do-not-use / new-required / unknown | <検索語・確認ファイル・既存 tests> | complete / partial / not_run |
| tests / contracts | <unit / contract / E2E / fixture / validator> | <既存テスト> | reuse / extend / do-not-use / new-required / unknown | <根拠> | complete / partial / not_run |
| docs / policy boundary | <docs / runbook / ownership / tenant / secret / PII / 外部送信> | <関連 docs / policy module> | reuse / extend / do-not-use / new-required / unknown | <根拠> | complete / partial / not_run |
| knowledge transfer check | 過去セッションの実験結果・技術的制約（失敗アプローチ・環境制約・eval 結果等）が SKILL.md / 要件に反映済みかを棚卸しし、設計前に引き継ぎ漏れを確認したか | <過去 steering の findings.md / worklog.md / SKILL.md 参照先> | reuse / extend / do-not-use / new-required / unknown | <確認した steering ファイルパス・引き継ぎ漏れの有無（引き継ぎ漏れなし: confirmed / 引き継ぎ漏れあり: missing / 過去セッションなし: N/A）> | complete / partial / not_run |
| current state verification | 対象コードパスが既存 PR・既存実装で対応済みでないかを `git log` / `gh pr list` / `grep` で確認したか。タスクが触れうる全実行経路（MCP ラッパー / Bash / subagent / SDK 等）を列挙してから調査範囲を確定したか | <確認した git log / gh pr list コマンド・列挙した実行経路> | reuse / extend / do-not-use / new-required / unknown | <対応済み PR の有無・列挙した実行経路一覧（確認済み: confirmed / 未確認: missing）> | complete / partial / not_run |

Read/Write Surface Survey は、読み書き・保存・投稿・検索・更新・外部連携・wiki / Slack / GitHub / AWS / MCP / API / DB / log / audit を含むタスク、またはユーザーが「既存コードがあるはず」と示したタスクで必須。新規機構を提案する前に、既存の read / write / persistence / API / MCP / wrapper / adapter 経路と tests / contracts を確認する。見つからない場合は `not_found` と検索範囲を Evidence に書く。partial は、必須 surface は確認済みだが任意参考が未完の意味に限定する。必須 surface が未確認なら `not_run` とし、accepted approach にしない。not_run は human-check へ進めない停止理由であり、human-check に表示して承認を取る状態ではない。

## Engineering Baseline Survey

GDD は特定言語に依存せず、最初に architecture / code structure / dependency manifest / lock file / runtime / install / test / CI を確認する。既存 repo は現状を調査し、新規または未整備 repo は最小の再現可能な足場を提案する。

| Area | Detected / proposed baseline | Evidence | Status | Goes to |
|---|---|---|---|---|
| architecture / code structure | <monolith / simple modular / layered / service split / existing pattern 等> | <ディレクトリ構造、類似実装、README、CI、既存 design> | confirmed / missing / needs-human / N/A | Human Check / design-gating / Non-Goal |
| dependency management | <package manager、dependency manifest、lock file の有無> | <package.json / pyproject.toml / go.mod / Gemfile / Terraform lock 等、実際の file> | confirmed / missing / needs-human / N/A | Human Check / design-gating |
| execution environment | <runtime、local dev、container、CI runner、tool versions> | <README / AGENTS / Dockerfile / CI / mise / asdf / Makefile 等> | confirmed / missing / needs-human / N/A | Human Check / design-gating |
| runner / eval harness structure | テストランナー / eval ハーネス / 起動スクリプトの内部構造（実行時に効く設定・MCP/flag・強制無効化など）を設計前に確認したか | <該当ファイルのパス / 設定箇所 / 強制無効化フラグ等> | confirmed / missing / needs-human / N/A | Human Check / design-gating |
| install command | <再現セットアップ command> | <README / Makefile / package script / docs> | confirmed / missing / needs-human / N/A | Project Reproducibility Gate |
| test command | <最小 test / full test / target test command> | <既存 test runner / CI / package script> | confirmed / missing / needs-human / N/A | Project Reproducibility Gate |
| CI command | <CI が実行する build / test / lint / validate> | <workflow / pipeline / docs> | confirmed / missing / needs-human / N/A | Baseline Compliance Check Plan |
Codebase Health Survey: `gdd-codebase-health.py` findings（`large_file` / `missing_lockfile` / test・CI）を Engineering Baseline に統合し、影響分だけ出す。

### Project Reproducibility Gate

以下が 1 つでも missing のまま code-generation / feature implementation に進む場合、human-check に「未整備のまま進む」承認ポイントとして出す。完全未調査なら `human-check に進めない`。

- dependency manifest: 依存関係の正本があるか
- lock file: 同じ依存解決を再現できるか。repo 方針で lock しない場合は理由を明記する
- install command: 初回セットアップを再現できるか
- test command: 変更後に最低限の確認を再現できるか
- CI command: local と CI の期待がずれていないか

## Architecture Recommendation Gate

既存 repo では「既存に従う」が第一候補だが、既存構造が明らかに破綻している場合は小さな整理または再設計を提案する。新規実装では、過剰な抽象化を避けて Simple Modular を既定とし、複雑さの根拠がある場合だけ Layered / Clean-ish や Service / Worker Split を提案する。

### Architecture Option Matrix

アーキテクチャ、CI/CD、IaC policy、runtime、framework、test tooling、access method、credential backend の選定で複数の妥当な選択肢がある場合、AI が勝手に単一案へ丸めない。既存 repo 標準、業界標準 / vendor official、最小の自前実装、現行方式を比較し、標準から外れる案や非標準な自前実装を採る場合は human-check に「人間に確認」する判断として出す。

`業界標準 / vendor official` は 1 つの候補名ではなく、**vendor official が存在するなら vendor official を優先確認し、存在しない/非該当なら ecosystem の標準寄り実装を確認する**という意味で使う。例: OPA/Rego + Conftest は Terraform vendor official そのものではなく、Terraform plan JSON を policy as code で検査する ecosystem standard 寄り候補として扱う。

| Option | What it means | Existing repo standard | 業界標準 / vendor official | DRY / KISS / YAGNI fit | Testability / operability | 採用しない理由 | AI recommendation | Goes to |
|---|---|---|---|---|---|---|---|---|
| <既存 repo 標準> | <既存の置き場所・既存CI・既存toolingに合わせる案> | <合う / 合わない / 未確認> | <公式・標準との関係> | <重複や過剰抽象化を増やさないか> | <test / CI / 運用で扱いやすいか> | <不採用なら理由> | adopt / reject / needs-human | Human Check / design-gating |
| <業界標準 / vendor official> | <公式ツール・標準ツールに寄せる案> | <既存repoとの整合> | <GA / preview / deprecated / unavailable> | <自前実装を減らせるか> | <導入・検証・運用の現実性> | <不採用なら理由> | adopt / reject / needs-human | Human Check / design-gating |
| <最小の自前実装> | <Python / shell / small script 等で狭く作る案> | <既存で同方式が標準か> | <公式標準から逸脱するか> | <KISS か、長期的に重複を増やすか> | <保守・検証・CI の見通し> | <不採用なら理由> | adopt / reject / needs-human | Human Check / design-gating |

Terraform policy / IaC CI の標準例:
- Terraform plan JSON の policy check は、既存 repo 標準が無い限り **OPA/Rego + Conftest** を第一候補にする。policy as code として CI に載せやすく、DRY / KISS / YAGNI の観点でも自前 parser より説明しやすい。
- 既存 repo 標準が Python 等で存在する場合、OPA/Rego + Conftest を黙って優先しない。既存標準を拡張する案と、OPA/Rego + Conftest に移行する案を `needs-human` として比較し、policy が増える見込み、保守できる人、導入コスト、CI 依存追加を判断材料にする。
- **Python 独自チェック**は、policy が一時的で極小、既存 repo 標準が Python、または OPA/Rego + Conftest を導入できない具体的制約がある場合だけ候補にする。採用するなら、なぜ標準方式を使わないかを HITL に出す。
- `terraform validate / tflint / Checkov` は構文・lint・known misconfig の補助であり、plan JSON の組織固有 policy 判定の置き換えとは限らない。何を検出し、何を検出しないかを `検証計画` に分けて書く。
- 上記比較が無いまま CI policy の実装方針を決めた場合は `human-check に進めない`。

### Architecture Drivers

| Driver | Evidence | Impact on architecture |
|---|---|---|
| domain complexity | <単純 CRUD / domain rule 多め / workflow-heavy 等> | <Simple Modular / Layered / Clean-ish 等への影響> |
| integration boundary | <external API / MCP / DB / queue / browser / worker 等> | <adapter / service split / retry boundary 等への影響> |
| data ownership | <single repo / multiple services / shared DB / tenant boundary> | <module boundary / service boundary / migration strategy> |
| operational constraints | <latency / async / deploy / rollback / credentials / security> | <runtime / worker / infra boundary> |
| testability | <unit で足りる / integration 必須 / E2E 必須> | <dependency direction / seam / fixture strategy> |

| Option | What it means | Good fit when | Trade-off | AI recommendation |
|---|---|---|---|---|
| Follow | 既存 architecture / code structure に従って最小変更する | 既存構造が健全で、同種実装がある | 既存の歪みも温存する | adopt / reject / needs-human |
| Fit + Small Refactor | 既存構造に合わせつつ、今回触る範囲だけ責務整理する | 既存構造は使えるが、局所的な重複・肥大化がある | PR が少し大きくなる | adopt / reject / needs-human |
| Reshape | 既存構造の責務境界を見直し、実装前に設計を組み替える | 既存に載せると複雑さ・重複・テスト困難が増える | human recheck と段階実装が必要になりやすい | adopt / reject / needs-human |
| Simple Modular | 新規または小規模で、module / function / adapter 境界を明快に分ける | まだ domain が小さく、service 分割は不要 | 将来大きくなったら再整理が必要 | adopt / reject / needs-human |
| Layered / Clean-ish | domain / application / infrastructure の依存方向を分ける | domain rule が増え、テストで外部依存を外したい | 小規模では抽象化過多になりやすい | adopt / reject / needs-human |
| Service / Worker Split | runtime / deploy / queue / batch / async worker を分ける | latency、非同期、権限、scaling、failure isolation が必要 | deploy / observability / CI が重くなる | adopt / reject / needs-human |

## Dependency / Runtime Baseline

`Technology Stack Fit Matrix` が「何を採用するか」を比較するのに対し、この表は「同じ環境で動かせるか」を確認する。言語・framework にかかわらず必須。

| Ecosystem | Package manager | Dependency manifest | Lock file | Runtime | Install command | Test command | CI command | Status |
|---|---|---|---|---|---|---|---|---|
| <Python / Node / Go / Terraform / multi 等> | <uv / pip / npm / pnpm / go / bundler / terraform 等> | <file path or missing> | <file path / not-used + reason / missing> | <version source> | <command> | <command> | <command> | confirmed / missing / needs-human |

## Baseline Compliance Check Plan

implementation / completion で確認する項目を先に固定する。完了時に `pass` と言うには、少なくとも approved baseline との整合を示す。

| Check | Evidence | Failure handling |
|---|---|---|
| architecture followed | <diff が approved architecture option と file placement に従う> | design_detail_only / human_recheck_required |
| file placement | <新規ファイル・変更ファイルが code structure と一致> | task breakdown / design rework |
| dependency manifest / lock file | <新しい import / provider / image / tool が dependency manifest と lock file に反映、または不要理由あり> | implementation_fix_only / human_recheck_required |
| fresh install | <install command 実行または not_run 理由> | blocker / not verified |
| fresh test | <test command 実行または not_run 理由> | blocker / debug route |
| CI consistency | <CI command と local command の差分> | docs / CI / command alignment |

## Architecture Drift Detection / Re-Architecture Recommendation

実装中または completion 前に、当初の architecture recommendation から逸脱していないかを確認する。逸脱は「悪」ではないが、黙って進めず、リファクタ・段階実装・再承認のどれで扱うかを決める。

| Signal | Evidence | Severity | Recommendation |
|---|---|---|---|
| mixed responsibilities | <1 ファイル / 1 module に UI / domain / infra / policy が混在> | low / medium / high | Local Refactor / Boundary Reshape / Runtime / Service Split |
| broad change surface | <当初 glob より大きい diff / unrelated files> | low / medium / high | Local Refactor / Boundary Reshape |
| duplicated validation / policy | <同じ validation / sanitizer / guard が複数箇所> | low / medium / high | Local Refactor |
| dependency direction inversion | <domain が infra / UI / transport に依存> | medium / high | Boundary Reshape |
| circular dependency | <module import cycle / runtime coupling> | medium / high | Boundary Reshape |
| hard tests / excessive mocks | <外部依存を外せず unit が重い> | medium | Boundary Reshape |
| runtime / deploy mismatch | <worker が必要なのに web process に混在、deploy / CI が不一致> | medium / high | Runtime / Service Split |
| unexplained dependencies | <dependency manifest に理由不明の追加、lock だけ更新等> | low / medium | Local Refactor / human recheck |

### Severity Guide

- `low: local cleanup`: 1〜2 ファイル程度の局所的な命名・重複・小さな責務混在。approved architecture option、AC、runtime、dependency manifest、CI command は変わらない
- `medium: boundary risk`: shared module / public API / state machine artifact / dependency direction / tests に影響し、境界を少し動かす可能性がある。AC は変わらないが、file placement や証明方法が変わり得る
- `high: approved architecture or runtime boundary changes`: approved architecture option、runtime boundary、service / worker split、package manager、credential boundary、deploy / CI topology、AC の意味が変わる

broad change surface thresholds:
- low: approved scope 内、追加/変更が 1〜2 ファイル程度、または既存 pattern と同じ場所への局所追加
- medium: approved scope 内だが 3〜7 ファイル、shared module / public API / common test fixture を含む、または当初 glob より横に広がる
- high: approved scope 外、8 ファイル以上、複数 runtime / service / deploy unit に跨る、または unrelated files を含む

mixed responsibilities examples:
- low: 小さな adapter 内で mapping と軽い validation が同居しているが、domain / infra / UI へ波及しない
- medium: 1 module に domain rule と transport / persistence / UI state が混在し、test が外部依存を多く mock している
- high: domain / infra / UI / runtime orchestration が同じ変更単位に混ざり、approved architecture option や runtime boundary を維持できない

### Handling Decision

Baseline Compliance Check has priority for hard mismatch: approved baseline と実 diff が明確に不一致なら、まず Baseline Compliance Check の blocker として扱う。Architecture Drift Detection は、その不一致が単なる修正漏れか、構造的な再設計候補かを分類する補助として使う。

highest severity wins: 複数の drift signal が同時に出た場合は、最も重い severity を採用する。ただし Baseline Compliance Check has priority for hard mismatch に該当する場合は、まず blocker として止めてから drift 分類する。

medium escalates to human-recheck-required: medium でも file placement、証明方法、public API、AC evidence interpretation、approved architecture option のいずれかが変わるなら `human-recheck-required` に昇格する。

| Handling | Use when | Route |
|---|---|---|
| apply-now | low で behavior-preserving、approved architecture / AC / runtime / dependency baseline を変えない | Local Refactor task |
| defer-follow-up | medium だが current PR の価値提供を妨げず、後続で整理できる | Planned Follow-up Stage Lane / Architecture Debt Finding |
| human-recheck-required | approved architecture option / file placement / runtime boundary / package manager / CI command / AC evidence interpretation が変わる | human-check-waiting |
| planning-rework-required | high で現在の plan の Stage 分解、service boundary、runtime/deploy topology 自体を作り直す必要がある | gdd-brainstorming / design-gating |

Re-Architecture Recommendation は次の 3 段階に絞る:

- `Local Refactor`: 既存 behavior を変えず、命名・重複・小さな責務分離だけを行う
- `Boundary Reshape`: module / layer / adapter の境界を再設計する。AC や file placement に影響する場合は human recheck
- `Runtime / Service Split`: process、worker、service、deploy、queue、credential boundary を分ける。原則として別 Stage / 別 PR / human recheck

## Technology Stack Fit Matrix

| Decision | Candidate stack / access method | Existing repo standard | Official integration | Operational constraints | Multi-tenant / credential boundary | Testability | Fit | Goes to |
|---|---|---|---|---|---|---|---|---|
| <外部サービス・SDK・CLI・MCP・runtime・framework 等の選定> | <MCP / CLI / SDK / API / managed service / framework A 等> | <既存実装・社内標準・既存 dependency との整合> | <vendor official / GA / preview / deprecated / unavailable> | <運用・権限・network・rate limit・host compatibility> | <tenant 切替、secret backend、IAM、credential scope> | <unit / contract / E2E / mockability> | adopt / reject / needs-human / needs-research | Human Check / design-gating / Non-Goal / Open Question |

## Adopted Technology Stack Trace

| Area | Adopted stack / access method | Why this fits | Rejected alternatives | Human-visible risk | Recheck trigger |
|---|---|---|---|---|---|
| <Datadog access / frontend framework / DB / IaC / runtime 等> | <採用する技術スタック> | <既存 repo / Official integration / 運用制約 / testability に合う理由> | <CLI / SDK / API / MCP 等の比較で落とした案> | <ズレると困ること> | <MCP GA 判明 / credential backend 変更 / tenant 境界変更 / official path 変更等> |

## Implementation Sequence Plan

| Stage ID | 目的 | PR Boundary | Approval Scope | 入力 / 前提 | 生成物 | Covers AC | Depends on | 後続が consume するもの | 人間に戻す条件 | Follow-up Tracking |
|---|---|---|---|---|---|---|---|---|---|---|
| S-1 | <最初に固定する schema / contract / foundation> | current-pr / follow-up-pr / post-merge-verification | このPRで実施許可 / 後続PRの方針のみ承認 / 後続PR着手前に再承認 | <既存実装、承認済み方針、技術スタック> | <後続が使う型・API・policy・fixture 等> | AC-1 | none | S-2 / S-3 が使う <artifact> | <生成物の意味・scope・技術スタックが変わる場合> | <current-pr なら none。follow-up-pr なら Planned Follow-up Stage Lane seed / backlog / steering 予定> |

HITL 表示用の `段階実装案` はこの表から生成する。複数 Stage がある場合、human-check では `Stage ID`、この段階でやること、`PR Boundary`、`Approval Scope`、完了確認、次に進む条件 / 人間に戻す条件、`Follow-up Tracking` を stage list summary として出す。`Stage Continuity Brief` は Stage 間の受け渡し説明であり、段階ごとの実装順序・検証・自走範囲を示す `段階実装案` の代替にしない。`Stage Continuity Brief` の代替にしない、という制約を requirements gate / human-check の両方で守る。

## Planned Follow-up Stage Lane

`Implementation Sequence Plan` に `PR Boundary=follow-up-pr` または `post-merge-verification` の Stage がある場合は必須。計画済み後続 Stage が PR merge 後に消えないよう、後続作業の seed を残す。

| Pending Stage ID | Origin Steering | Base Branch | Base Commit | Next Planned Stage | Follow-up Trigger | Tracking Destination | Human Recheck |
|---|---|---|---|---|---|---|---|
| S-2 | <現在の steering path> | <現在の base branch> | <PR 作成時または merge 後の commit> | <次に着手する Stage ID と目的> | post-merge / after-current-pr / manual | <new steering seed / backlog / issue / none + 理由> | required before implementation / not required + 理由 |

## Adversarial Requirements Review

Selection: Dialectic Review Lane=<selected / selected(existing_evidence) / not_applicable> — <理由 1 行>

| 観点 | 内容 | HITL への反映 |
|---|---|---|
| 反対仮説 | <この requirements / completion condition / implementation approach が間違っているとしたら何が原因か> | <承認ポイント / ズレ確認 / Open Question / N/A> |
| ズレリスク | <人間が「思ったんと違う」と言いそうな scope / AC / 技術スタック / access method / credential boundary / Stage continuity / self-run limit> | <human-check に出す欄> |
| 採用した修正 | <敵対的レビューから requirements / design skeleton / human-check に反映した変更> | <反映先> |
| 棄却した指摘 | <採用しない指摘と理由> | <N/A または Honest Limitations> |
| 残すリスク | <HITL で明示確認する残リスク。ない場合は `なし`> | <承認ポイント / Not Verified Yet / 人間に戻す条件> |

## Plan Direction LLM Review

Selection: Plan Direction LLM Review=<selected / selected(main-session) / not_applicable> — <理由 1 行>

| 観点 | レビュー結果 | 反映 |
|---|---|---|
| ユーザー入力との一致 | <ユーザーが求めたことと AI の整理した要件・方針がズレていないか> | <修正先 / N/A> |
| アーキテクチャ / 技術スタック | <採用する作り方、変更ファイル、access method、credential boundary が妥当か> | <修正先 / HITL の判断ポイント> |
| セキュリティ / 制約 | <危険操作、secret、tenant、外部送信、本番相当操作の扱いが妥当か> | <修正先 / 人間に戻す条件> |
| 検証計画 | <AC に対して unit / contract / E2E / external evidence の切り方が妥当か> | <修正先 / Not Verified Yet> |
| 自走範囲 | <この承認をきっかけに AI が自走しても、期待どおりの結果になりそうか> | <自走上限 / stop condition> |
| HITL 表示 | <非エンジニアにも判断できる言葉になっているか。P0/P1 など未定義語を残していないか> | <human-check 修正 / 用語定義> |

## Plan Revision Ledger

| Revision | Reason | Changed AC | Affected Stage | New / Reopened Task | Downstream invalidation | Human recheck |
|---|---|---|---|---|---|---|
| R1 | initial plan | AC-1..AC-N | S-1..S-N | task-breakdown で作成 | none | initial HITL |
```

Adversarial Requirements Review は full debate log ではない。requirements.md には採用判断だけを残し、HITL には `反対仮説` / `ズレリスク` / `採用した修正` / `残すリスク` のうち人間が誤承認しやすいものだけを出す。

Plan Direction LLM Review は、方針を人間に見せる直前の LLM レビュー結果を残す欄。これは full debate log ではなく、HITL 前に直した点と、承認者に残す判断点だけを残す。別 LLM / subagent を使える場合は独立 reviewer として実行し、使えない環境では main-session self-review として `selected(main-session)` を記録する。`not_applicable` にできるのは typo など方針・作り方・検証・自走範囲が存在しない trivial 変更だけ。

Status の意味:
- `kept`: 初期完了条件を意味変更なしで採用した
- `refined`: 抽象的な条件を AC 化できる粒度へ具体化した
- `split`: 1 つの条件を複数 AC / Non-Goal / Deferred に分割した
- `deferred`: 今回は後回しにした
- `dropped`: 今回やらないと明示した
- `added`: AI が安全性・検証・運用上必要と判断して追加した
- `unresolved`: 参照 URL 取得不可、外部事実未確認、人間判断待ちなどで未解決にした

Completion Testability Matrix の Status:
- `testable`: unit / contract / integration test または executable verification を実装前に RED として書ける
- `needs-clarification`: 表現が曖昧で Yes/No の claim になっていない。accepted AC として silent 承認せず、Open Question または HITL のテスト化確認に出す
- `e2e-required`: 実配線・UI・外部配送など E2E でないと最終確認できない。E2E に残す境界と、先に書く unit / contract / integration RED を分けて書く
- `external-evidence-required`: cloud / security / third-party state など外部証跡（plan / describe / CI / screenshot / log）が必要
- `non-testable-deferred`: 現スコープではテスト不能。accepted AC にせず Deferred / Non-Goal / Honest Limitations へ写像する

Status と Maps to の使い分け:
- `Status` は「ユーザーの初期条件をどう変換したか」を表す。`Maps to` は「変換後の置き場所」を表す
- `deferred` は、別承認・別タスク・後工程で扱う可能性を残すときに使う。置き場所は原則 `Deferred`。今回 scope から外すことも同時に伝えたい場合は `Deferred / Non-Goal` のように両方へ写像してよい
- `dropped` は、安全性・目的不一致・ユーザー合意により今回採用しないと決めたときに使う。置き場所は原則 `Non-Goal`
- 「AI の方針は仮決定したが、現物値・外部事実・権限が未確認」の場合は、方針行を `refined` または `human-check` として残し、未確認事実を `unresolved` / `Open Question` として分ける。1 行に混ぜる場合は Reason に「方針は仮決定、現物未確認」と明記する
- 「マージして再学習まで」「merge 後に検証」「post-merge verification / relearning」など、PR 作成後を含む完了条件は標準既定の `PR 作成まで` に丸めない。危険操作が未承認なら、その操作だけを `Requires explicit operation approval` として `Post-PR 操作承認` に分離し、完了条件自体は `Post-PR Completion Scope` として保持する
- 既存実装済み・途中実装・手動設定済みなどの初期状態は、守るべき条件なら `AC`、今回触らない境界なら `Non-Goal`、確認できない制約なら `Honest Limitations` へ写像する。単に「既存状態だから」という理由だけで `Honest Limitations` に逃がさない
- HITL に出す `refined` は、意味・scope・安全境界・作り方が変わるものに絞る。ログ粒度やテスト観点など、requirements.md に残れば十分な細部の具体化は、後戻りが大きくない限り `ズレ確認` に出さない

Trace の運用:
- `User-Stated Completion Conditions` は、ユーザーが言った目的・完了条件・既存実装状態・仮設定・手動設定済み状態を落とさず保存する
- `Completion Condition Trace` の各行は、必ず `AC / Non-Goal / Deferred / Honest Limitations / Open Question` のどれかへ写像する
- accepted AC はすべて `Completion Testability Matrix` に 1 行以上持つ。ユーザー入力時点では曖昧でもよいが、HITL 前には `Testable claim` / `Test level` / `Planned RED / E2E` / `Evidence required` / `Status` を埋める
- `needs-clarification` と `non-testable-deferred` は accepted AC として扱わない。前者は Open Question または HITL のテスト化確認へ、後者は Deferred / Non-Goal / Honest Limitations へ移す
- `e2e-required` は「E2E まで何もテストしない」という意味ではない。E2E に残す境界と、先に unit / contract / integration で固定する境界を分けて `Planned RED / E2E` に書く
- `external-evidence-required` は、どの外部証跡を `Verification` に残すかを `Evidence required` に具体化する
- `Completion Testability Matrix` は task-breakdown / TDD / completion-check が消費する正本であり、tasklist 側で別解釈を作らない
- `Implementation Approach Trace` は作り方の重要判断だけに絞る。ファイル単位の詳細設計や実装タスクは design-gating / task-breakdown に送る
- `Existing Implementation Survey` は HITL 前の既存実装調査の正本。変更対象ファイル単体ではなく、repo 構造、関連ファイル、類似実装、read / write / persistence / API / MCP / wrapper / adapter 経路、tests / contracts、docs、policy 境界を確認する。`partial` は必須 surface 調査済み・任意参考未完、`not_run` は必須 surface 未調査という意味で使い分ける。`not_run` は human-check へ進めない停止理由であり、`partial` で human check に進む場合だけ、何がズレ得るかを `Human Check Questions` と HITL の `既存実装の調査状況` に出す
- 読み書き・保存・投稿・検索・更新・外部連携を含むタスクでは、既存の wrapper / adapter / policy / client / command / tests を探すまで、新規機構を前提にした `Implementation Approach Trace` を accepted にしない。既存経路を使わない場合は `Reuse decision=do-not-use` と理由を明記する
- 外部サービス連携、認証方式、SDK/CLI/MCP/API、runtime/framework、IaC/provider、database、AI/model/eval 基盤の採用がある場合は `Technology Stack Fit Matrix` を必ず置く。候補が 1 つだけに見えても、`Existing repo standard` と `Official integration` を確認し、単一候補の理由を書く
- `Official integration` は vendor 公式の MCP / SDK / managed integration / CLI / API の有無と maturity（GA / preview / deprecated / unavailable）を確認する。公式統合があるのに独自 wrapper / direct API / CLI fallback を採用する場合は、理由を `Adopted Technology Stack Trace` に残し HITL に出す
- `Multi-tenant / credential boundary` は tenant 切替、credential backend（Secrets Manager / SSM / env / OAuth 等）、IAM scope、secret 実値の扱いを比較する。ここが変わる場合は単なる実装詳細ではなく human recheck 候補にする
- `Adopted Technology Stack Trace` の `Recheck trigger` に該当する後続情報が出た場合は、design_detail_only で閉じず `human_recheck_required` を検討する
- MCP に依存する機能を要件化する場合は、MCP 未接続・disabled 環境（別ホスト・他エージェントランタイム・restricted sandbox 等）でのフォールバック手段（標準ツールでの代替経路）を明記する。フォールバックが存在せず機能が MCP 必須である場合は、その旨を明記し `Non-Goals` に含める（session b5af6133: Serena MCP 未接続時に周辺コード探索が行われなかった再発防止）
- HITL には `kept` 行を原則出さず、`refined / split / deferred / dropped / added / unresolved` と、後戻りが高い approach 論点だけを出す
- HITL には全テスト計画を貼らない。`Completion Testability Matrix` のうち、テスト化できない完了条件、E2E/外部証跡必須、解釈差が大きい claim だけを `テスト化確認` に圧縮して出す
- HITL には全 dependency 一覧を貼らない。`Technology Stack Fit Matrix` のうち、採用する技術スタック、公式統合とのズレ、既存標準からの逸脱、credential / multi-tenant / access method の後戻りが高い判断だけを `技術スタック確認` に圧縮して出す
- `Implementation Sequence Plan` は standard または複数段階の quick (standard) で必須。quick (express) は単一ファイル・単一ACに閉じる場合のみ省略可。省略する場合は `N/A - single-stage express` と理由を残す
- `Implementation Sequence Plan` は tasklist 作成前の段階計画の正本。ファイル単位の詳細 task ではなく、Stage 間の入力 / 前提、生成物、後続が consume するもの、人間に戻す条件だけを書く。task-breakdown はここから `Execution Plan` と task の `Stage Output Contract` を作る
- `Depends on` だけで済ませない。後続 Stage が何を consume するかを書かないと、resume / amendment / task 再編時に連続性を復元できない
- HITL には全 Stage 詳細を貼らない。`Implementation Sequence Plan` のうち、生成物の意味がズレると後続全体が変わる Stage 境界だけを `Stage Continuity Brief` / `段階連続性` に圧縮して出す
- 複数 Stage がある場合、HITL には `Stage Continuity Brief` に加えて `段階実装案` を必ず出す。`段階実装案` は、stage ごとの「この段階でやること」「この PR / 後続」「この OK で承認する範囲」「完了確認」「次に進む条件 / 人間に戻す条件」「後続の追跡先」を短く示す。`段階実装にする` と書いているのに `段階実装案` が無い場合は requirements gate で差し戻す
- `Implementation Sequence Plan` が `N/A - single-stage express` でない場合、human-check の `段階実装案` は requirements.md の Stage ID と対応していなければならない。HITL 側で新しい Stage を作らず、requirements.md を正本にする
- `PR Boundary=follow-up-pr` / `post-merge-verification` の Stage は `Approval Scope` と `Follow-up Tracking` を必ず持つ。後続 Stage をこの OK で実装まで自走してよいか、方針承認だけか、着手前に再承認が必要かを曖昧にしない
- `Planned Follow-up Stage Lane` は、計画済み後続 Stage の seed。completion / post-merge では、`Pending Stage ID` が残っているか、`Tracking Destination` が作られたか、`Human Recheck` が必要かを確認する
- `Adversarial Requirements Review` は HITL 前の独立 / 敵対的レビューの採用判断を残す。`Dialectic Review Lane=selected` なら `references/dialectic-review.md` の Short Form を使い、`not_applicable` でも理由を 1 行残す。反対仮説、ズレリスク、採用した修正、残すリスクは human-check の `Adversarial Requirements Review` に圧縮して出す
- `Plan Direction LLM Review` は、HITL に方針を出す前に必ず確認する。ユーザー入力との一致、アーキテクチャ / 技術スタック、セキュリティ / 制約、検証計画、自走範囲、HITL 表示を確認し、修正できるものは HITL 前に反映する。残る判断点だけを human-check に圧縮して出す
- quick (express) で `Implementation Sequence Plan` が `N/A - single-stage express` の場合も、`state.md` の `Stage Continuity Source` は `requirements.md#Implementation-Sequence-Plan (N/A - single-stage express)` と書く。source を空欄にしない
- `Plan Revision Ledger` は active follow-up / amendment / human_recheck_required / planning_rework_required で Stage 計画が変わるたびに追記する。`Affected Stage` と `Downstream invalidation` を必ず書き、既存 tasklist のどこを再生成・再検証するかを明示する

## Express requirements.md テンプレート

`quick (express)` パスでは以下の軽量テンプレートを使う。design.md は作成しない。

```markdown
# [タスク名]

Task Size: quick (express)

## 目的
<なぜこの変更が必要か — Problem Discovery で得た 1-2 文>

## 変更内容
- `<ファイルパス>`: <何をどう変えるか>
- 変更前: <現在の挙動>
- 変更後: <変更後の挙動>

## 受入条件
- AC-1: <Yes/No で判定できる条件>
- AC-2: <Yes/No で判定できる条件>

## Express Minimal Trace
- User-Stated Completion Conditions: <1-2 行。ユーザーが言った完了条件・対象ファイルを原文に近く保存>
- Completion Condition Trace: <kept / refined / dropped 等を 1 行で。例: USC-1 -> AC-1 kept>
- Completion Testability Matrix: <AC-1 の Testable claim / Planned RED or executable verification を 1 行で>
- Implementation Sequence Plan: N/A - single-stage express（<単一ファイル・単一AC・後続 Stage が consume する生成物なし等の根拠>）
- Stage Continuity Source: requirements.md#Implementation-Sequence-Plan (N/A - single-stage express)

## 承認ポイント
1. **<カテゴリ>**: <判断対象>
   - 背景: <なぜこの判断が必要か>
   - 変更前 → 変更後: <1 行で対比>
   - → OK / 別案希望

### 方向性承認
- AI 自走範囲: <変更対象ファイル内の修正に閉じる。他ファイルへの波及が判明した場合は quick (standard) に昇格>
- 自走上限: <実装完了まで / PR 作成まで / デプロイ準備まで / デプロイ実行は別承認>
- → OK / 自走範囲を制限したい
```

Express テンプレートの原則:
- 承認ポイントは 1-3 件に絞る（standard の 3-5 件より少ない）
- 方向性承認は必ず 1 件含める
- Behavior Change Summary / Route / Ownership Matrix / Sensitive Data / Masking Policy / Design Policy Discussion は省略可（見出しも不要）
- `Express Minimal Trace` は省略しない。standard の full trace 表は使わず、1 行ごとの最小 trace / N/A 根拠だけを残す。これにより quick (express) でも初期完了条件・テスト可能性・single-stage 判定が落ちない
- `state.md` の Gate Status は brainstorming 完了時に以下を設定:
  - `Requirements Review Status=approved`（reviewer skip）
  - `Design Review Status=approved`（design.md 不要）
  - `Human Check Status=pending`
  - `Resume From=human-check-waiting`

## requirements.md セクション一覧

`quick (standard)` パスでは Summary Brief + 目的 + スコープ + AC + 実装方針の最小構成でよい。

1. Summary Brief
2. 目的
3. スコープ
4. 非スコープ
5. 受入条件
   - 各条件に `AC-1`, `AC-2`, ... の連番 ID を付与する
   - ID は task breakdown での AC 紐付け、completion での pass/fail 追跡に使う
   - 例: `- AC-1: ユーザーがログインボタンを押すとダッシュボードに遷移する`
   - **機械可読 schema（optional）**: 大規模 / migration / 外部 API 連携タスクでは AC を `requirements.md` 冒頭の YAML frontmatter で並行記述してよい。`category` / `severity` / `boundary` / `verification_hint` 等のメタデータを構造化できる。markdown bullet と並行サポート、両方ある場合は YAML が正本。`lint-ac.py` が YAML を優先抽出し、無ければ markdown bullet にフォールバックする。schema 詳細は `docs/references-archive/ac-machine-readable-schema.md`
6. `User-Stated Completion Conditions`
   - ユーザーが最初に言った完了条件、既存実装状態、仮置き、手動設定済み状態を原文に近く保存する
7. `Completion Condition Trace`
   - 初期完了条件が `kept` / `refined` / `split` / `deferred` / `dropped` / `added` / `unresolved` のどれになったかを記録し、`AC / Non-Goal / Deferred / Honest Limitations / Open Question` に写像する
8. `Completion Testability Matrix`
   - accepted AC ごとに `Testable claim` / `Test level` / `Planned RED / E2E` / `Evidence required` / `Status` を記録する
   - `needs-clarification` / `non-testable-deferred` を accepted AC に残さない。E2E / 外部証跡が必要な条件は HITL の `テスト化確認` に出す
9. `Post-PR Completion Scope`
   - ユーザーが `merge` / `マージ` / `再学習` / `relearning` / `post-merge verification` / `release verification` / `apply 後確認` を完了条件として明示した場合に必須
   - `マージして再学習まで` のような条件を `PR 作成まで` に丸めず、post-merge verification / relearning として何を確認するかを記録する
   - `merge / deploy / apply / AWS write` などの write 操作は、`Post-PR 操作承認` に `Requires explicit operation approval` として分離し、1 操作ごとの明示承認を維持する
10. `Implementation Approach Trace`
   - repo 分割、既存仕組み再利用、新設、import/recreate、public/private、CI/CD 方針など、作り方がズレると後戻りが高い論点を記録する
11. `Technology Stack Fit Matrix`
   - 外部サービス / SDK / CLI / MCP / API / framework / runtime / IaC / DB / AI model 等の採用判断を比較する
   - `Existing repo standard` / `Official integration` / `Operational constraints` / `Multi-tenant / credential boundary` / `Testability` を埋める
12. `Adopted Technology Stack Trace`
   - 採用する技術スタック、採用理由、却下案、HITL に出す risk、後続で再承認が必要になる trigger を記録する
13. `Critical Trace`
    - human check で承認した重要判断のうち、実装完了まで消えてはいけないものを記録する
    - 完了条件、制限事項、技術スタック、作り方の重要判断、HITL で「OKで実装・検証すること / OKしても今回は対象外のこと」と説明した境界を対象にする
    - `kept` の詳細や単なる文言調整は対象外。ズレると手戻り・安全リスク・期待外れにつながるものだけを載せる
    - 証明方法は `new-red-green` / `code-diff` / `existing-evidence` のいずれかにする
      - `new-red-green`: 新しい失敗テストを作り、実装後に通した証跡で証明する
      - `code-diff`: 実装差分そのものが重要判断を満たしていることを diff と reviewer で証明する
      - `existing-evidence`: 新規実装なしで既存実装・既存テストが十分と証明する。この場合は人間に「新規実装なし」と分かるように tasklist / completion に残す
    - 形式:
      ```markdown
      ## Critical Trace

      | ID | 人間が承認した重要判断 | 実装で必ず証明すること | 許される証明方法 | HITL 表示 |
      |---|---|---|---|---|
      | CT-1 | <例: Browser / Playwright / generic HTTP も外部送信面として扱う> | <分類・deny・warn のいずれかで扱われること> | new-red-green / code-diff / existing-evidence | OKで実装・検証すること |
      ```
    - **Why:** HITL で承認された内容が task-breakdown で `Existing coverage inspection` にすり替わると、実装差分が無いまま done になりうる。Critical Trace は「人間が OK した重要判断」を tasklist / completion-check が追跡するための最低限の正本。
14. `Implementation Sequence Plan`
   - 複数段階実装の Stage ID、PR Boundary、Approval Scope、入力 / 前提、生成物、Covers AC、Depends on、後続が consume するもの、人間に戻す条件、Follow-up Tracking を記録する
   - standard または複数段階 quick (standard) では必須。HITL の `Stage Continuity Brief` / `段階実装案` と tasklist の `Stage Output Contract` の正本にする
15. `Planned Follow-up Stage Lane`
   - `PR Boundary=follow-up-pr` / `post-merge-verification` の Stage がある場合に必須
   - Pending Stage ID、Origin Steering、Base Branch、Base Commit、Next Planned Stage、Follow-up Trigger、Tracking Destination、Human Recheck を記録する
16. `Adversarial Requirements Review`
   - HITL 前に独立 / 敵対的レビューを実施したか、または `not_applicable` とした理由を記録する
   - 反対仮説、ズレリスク、採用した修正、棄却した指摘、残すリスクを短く残す
   - human-check には全文ではなく、誤承認につながるズレリスクと残すリスクだけを圧縮して出す
17. `Plan Revision Ledger`
   - active follow-up / amendment / human_recheck_required / planning_rework_required による段階計画の差分を記録する
   - `Affected Stage` / `Downstream invalidation` / `Human recheck` を明示し、追加 task が元のどの Stage を変えたかを追跡できるようにする
15. 制約・前提・依存関係
16. 影響範囲
17. リスク
18. 実装方針
19. 非採用案
20. fail-closed 方針
21. 不完全データ時の扱い
22. operator 手順へ逃がす境界
23. 検証ヒント
24. `Execution / Evaluation Reality`
    - 実際にどの host / runtime / CI / agent / model / toolchain / 権限で動くか
    - local / IDE / CI / production 相当など複数レーンがある場合、どれが release gate でどれが exploratory か
    - benchmark / eval / score / AI review / prompt tuning / skill / plugin / hook / command 変更では、評価対象・評価データ・pass/fail 基準・parity 証跡を明記する
    - Codex / Cursor / Claude Code の複数ホストで使う場合は Host Compatibility Matrix を置き、各ホストの role / 制約 / 代替手段 / release gate 可否を表にする
    - production 相当性を確認できない検証は `探索結果` として扱い、merge / release の合格根拠にしない
25. `Latest Tech Context`（技術、対象 version、確認した最新情報の要点、参照元、checked_at、planning への影響）
26. Open Questions
27. `Behavior Change Summary`
    - 何が変わるか
    - 何が変わらないか
    - user-visible change か internal-only change か
28. `Route / Ownership Matrix`
    - before / after / owner / flag / rollback を 1 表で見せる
    - 例: `before | after | owner | rollout flag | rollback note`
    - route / owner 変更が無い場合でも見出しは残し、`N/A` と根拠 1 行で済ませてよい
29. `Sensitive Data / Masking Policy`
    - どの値が sensitive か
    - prompt に入るか
    - model output や外部配送面に出る可能性があるか
    - どこで mask / reject / sanitize するか
    - 最終責任者は誰か
    - 非該当なら `N/A` と根拠 1 行を残す
30. `Design Policy Discussion`
    - human check 前に人間と先に詰めたい設計方針の候補、簡略化余地、採用しない案、残る判断点を整理する
    - **実装方式の選定**（複数の合理的方式がある場合のみ）: 方向性が決まった上で「どう実装するか」の候補を比較する。以下の形式で記録する:
      ```markdown
      ### 実装方式の選定
      | 観点 | 方式A: <名前> | 方式B: <名前> | 方式C: <名前> |
      |------|-------------|-------------|-------------|
      | 概要 | ... | ... | ... |
      | 実装例 | <事例の有無・参照先> | ... | ... |
      | 複雑さ | ... | ... | ... |
      | 信頼性 | ... | ... | ... |
      | 運用コスト | ... | ... | ... |
      | 制約・前提 | ... | ... | ... |
      
      **推奨**: 方式A — <理由 1-2 文>
      **調査の詳細**: findings.md § <セクション名>
      ```
    - 実装方式が 1 つしかない場合は比較表を省略し、`実装方式: <方式名> — <1 行説明>` のみ記載する
    - 実装方式の選定結果は `Human Check Questions` の承認ポイントに含め、human check で承認を取る
31. `Human Check Questions`
    - Summary Brief の「承認ポイント」と同じ構造化形式を使う
    - 各ポイントは番号付きで、**カテゴリ**（scope / 方針 / リスク / 権限 / データ等）を太字で先頭に置く
    - 各ポイントに **背景**（なぜこの判断が必要か）と **変更前 → 変更後**（何が変わるか）を含める
    - AI が選んだ案・理由・代替案を提示し、人間は「OK / 別案希望 / 修正依頼」で判断する
    - route / ownership / secret handling / masking / rollout / rollback が scope にある場合は、その承認事項を必ず含める
    - 人間がそのまま読んで判断できる短い自然文にする
    - 内部フィールド名や略語だけで済ませず、必要なら括弧で補足する
    - 人間が承認ポイントだけ読めばコンテキスト不要で判断できる粒度にする
    - 原則 3〜5 件に絞る
- `Completion Condition Trace` の `refined` / `split` / `deferred` / `dropped` / `added` / `unresolved`、`Implementation Approach Trace` の `human-check` 行、`Adopted Technology Stack Trace` の high-risk 行は、human-check の `ズレ確認` または承認ポイントに圧縮して含める
    - `Adversarial Requirements Review` の `ズレリスク` / `残すリスク` は、human-check の `Adversarial Requirements Review` または承認ポイントに圧縮して含める

### 写像の目安

新しい固定スキーマを増やす意図ではなく、既存項目への写像の目安:

- `目的` ≒ Why
- `スコープ/非スコープと主要な受入条件` ≒ What
- `品質面の受入条件と検証ヒント` ≒ How well
- `制約・前提・依存関係` ≒ Constraints

### Examples の扱い

`Examples` は独立必須セクションにせず、曖昧な受入条件、境界ケース、失敗時挙動があるときだけ、`受入条件` または `検証ヒント` に入力/出力/期待挙動の代表例として書いて固定する。

## lightweight design.md skeleton セクション一覧

`quick` パスでは Summary Brief + 変更点 + テスト方針の最小構成でよい。

1. Summary Brief（requirements と同じ 4 層構造: 一言 / 判断材料 / 承認ポイント / Honest Limitations。standard で必須、quick は Honest Limitations 任意。テンプレートは上記参照）
2. 変更点の要約
3. `Behavior Change Summary`（requirements と矛盾させず、必要なら requirements を参照する）
4. `Route / Ownership Matrix`（requirements の表をそのまま使うか、implementation boundary が読める粒度に具体化する）
5. `Sensitive Data / Masking Policy`（design では enforcement point を具体化する）
6. `Design Policy Discussion`（human check 前に設計方針の候補、簡略化余地、採用しない案、残る判断点を見える位置に残す）。以下の設計抜けパターンチェックリストを必要に応じて使う:
   - **インターフェース全量カバレッジ**: 既存インターフェースを書き換えるとき、元のインターフェースが扱う全ケース（メッセージ種別・状態・ハンドラ分岐）が新設計に含まれているか
   - **コンポーネント間の対称性ポリシー**: 複数コンポーネントに同じ機能を追加するとき、対称性（または意図的な非対称の理由）が明文化されているか
   - **やらない判断の根拠**: AC または Non-Goal に「やらない」判断の根拠（技術的制約・スコープ外・コスト判断）が記録されているか
7. `Human Check Questions`（requirements の承認事項をそのまま見える位置に残す。非該当なら `N/A` と根拠 1 行）
8. `Implementation Sequence Plan` 参照 / 要約
   - design.md は requirements.md の `Implementation Sequence Plan` を重複コピーしない
   - design 側では requirements の Stage 計画を参照 / 要約し、設計詳細が Stage の生成物・consume 関係と矛盾しないことだけを示す
   - design 詳細化で Stage の生成物・consume 関係を変える必要が出た場合は、requirements 側の `Implementation Sequence Plan` と `Plan Revision Ledger` を更新し、必要に応じて human recheck に戻す
9. 影響範囲
10. Requirements Trace
11. 主要フロー
12. `Latest Tech Context` / `External References`
13. `Execution / Evaluation Reality`
14. テスト方針
15. ロールバック / fail-closed
16. Open Questions

## state.md セクション一覧

Gate Status と Reviewer Selection を `design.md` から分離した state-only ファイル。

1. Gate Status
   - `Entry Intent`（brainstorming 開始時に記録。下記「Entry Intent テンプレート」参照）
   - `Requirements Review Status`
   - `Planning Reviewer Selection`
   - `Design Review Status`
   - `Human Check Status`
   - `Resume From`
   - `Approved Direction`（human check 承認後に記録。以下のテンプレートで `state.md` に追記する）
   - `Plan Revision`（段階計画の最新 revision。`requirements.md` の `Plan Revision Ledger` と一致させる）
   - `Current Stage`（現在実装・再設計・再承認の対象になっている Stage ID。未着手なら `planning`）
   - `Next Stage`（次に進む Stage ID。tasklist 未作成なら `task-breakdown`）
   - `Stage Continuity Source`（段階連続性の正本への参照。例: `requirements.md#Implementation-Sequence-Plan` / `tasklist.md#Execution-Plan`）

`state.md` に書くのは routing / phase 復元に必要な最小 field を優先する。長い reviewer history、Fix Attempts の詳細、scenario eval の全文、HITL で却下された案の長い理由は `worklog.md` / `adr.md` / appendix に移し、`state.md` には参照先と短い要約だけを書く。詳細を移動しても `Resume From` / `Next Action` / `Human Check Status` / `Route In Progress` の Core field は省略しない。

### Entry Intent テンプレート（正本）

```markdown
## Entry Intent
- 判定: new | resume | amendment | ambiguous
- 判定理由: <1 行で。例: "明示的な新規依頼 + active steering なし" / "resume cue + 単一 active steering" / "既存機能の amendment、anchor=<feature name>">
- 参照した正本: `references/entry-intent.md`
- 判定日時: <ISO8601 + TZ 付き、例: 2026-05-12T14:30:00+09:00>
```

- **記載位置**: `state.md` ファイル先頭側に **`## Entry Intent`（H2 見出し）** として独立配置する（`## Gate Status` の前または直後。`Gate Status` 配下の H3 ではない）
- **タイムスタンプ形式**: ISO8601 + タイムゾーン明示。JST なら `+09:00`、UTC なら `Z`
- brainstorming Step 2 で entry intent を判定したら、**必ずこの形式で `state.md` に記録する**
- `ambiguous` の場合は fail-closed 停止するため state.md は作成しない（または判定行のみ記録して停止）
- 後続 phase（completion-check / reviewer / pr-review）が「なぜこの phase 構成か」を再現できるよう、判定理由を 1 行で残す
- amendment 判定時は `anchor`（一意に紐付ける既存 feature / artifact 名）を判定理由に必ず含める

**Why（state machine 一体型 brainstorming としての差別化）**: entry intent の判定は runtime で消費されるだけで永続化されていなかった。後続 reviewer や completion-check が「この task は new か resume か amendment か」を再判定するコストを削減し、`/gdd-dev` の Resume Cue 解析と整合させる。superpowers の brainstorming は単発で完結するが、GDD brainstorming は entry intent → Resume From → Approved Direction という連鎖で state machine と一体化する。

### Approved Direction テンプレート（正本）

```markdown
## Approved Direction
- 方向性: <human check で承認された目的の 1 行要約>
- 自走範囲:
  - 含むディレクトリ / モジュール glob: <例: src/auth/**, src/http/cookie.ts>
  - 含む AC: [AC-1, AC-3]（省略時は全 AC）
  - 明示的に除外する範囲: <例: DB migration, logger 設定。省略時は除外なし>
- 自走上限: <実装完了まで / PR 作成まで / デプロイ準備まで / デプロイ実行は別承認>
- 承認後の到達点: <PR 作成まで / deploy 手前まで / 実装完了まで。terraform apply / AWS write / DB write / Docker push は別途明示承認>
- Post-PR Completion Scope: <none / マージして再学習まで / post-merge verification / relearning まで。ユーザーが明示した場合は PR 作成までに丸めない>
- Post-PR 操作承認: <manual merge required / merge approved / deploy approval required / Requires explicit operation approval>
- 別途明示承認が必要な操作: <terraform apply / AWS write / DB write / Docker push / 本番デプロイ。非該当なら N/A と根拠>
- 人間に戻す条件: <方向性自体の変更 / AC の根本的な追加・削除 / セキュリティ要件の新規発生>
- 事前スキャンファイル数: <N>（Cumulative Changed Files の基準値。brainstorming 時の影響範囲スキャンで取得）
- 事前スキャン対象 glob: <brainstorming 時に実スキャンした glob パターン>
- 承認日: <timestamp>
```

- routing source にはしない（`Resume From` / `Next Action` が正本）
- `gdd-systematic-debugging` が自走範囲の判定に使う補助コンテキスト
- **自走範囲の Scope 判定基準**: `gdd-systematic-debugging` は「含むディレクトリ / モジュール glob」への **glob マッチ** を第一基準とし、glob に含まれないパスに触れた時点で「自走範囲外（= `human_recheck_required` 相当）」と判定する。glob が省略された場合は従来通り自然文判断に従う（glob 化を強く推奨）
- **事前スキャンファイル数の保存**: brainstorming 時に取得した値を `state.md` に `Cumulative Diff Base: <sha>` と合わせて記録する。`human_recheck_required` で新 Approved Direction 承認時は `Cumulative Diff Base` を現 HEAD で更新する

### Stage Continuity State テンプレート（正本）

```markdown
## Stage Continuity
- Plan Revision: R1
- Current Stage: planning | S-1 | S-2 | ...
- Next Stage: workflow-handoff:task-breakdown | S-1 | S-2 | ...
- Stage Continuity Source: requirements.md#Implementation-Sequence-Plan
```

- `Plan Revision` は `requirements.md` の `Plan Revision Ledger` の最新 Revision と一致させる
- `Current Stage` / `Next Stage` は resume / compact / human_recheck_required 後に「複数段階のどこにいるか」を復元するためのアンカーであり、routing source にはしない。routing は引き続き `Resume From` / `Next Action` が正本
- `Next Stage` は Stage ID か、まだ Stage 実行に入っていない場合の `workflow-handoff:<phase>` を使う。例: human-check 前は `workflow-handoff:task-breakdown`、実装中の次 Stage は `S-2`
- `Stage Continuity Source` は、tasklist 作成前は `requirements.md#Implementation-Sequence-Plan`、tasklist 作成後は `tasklist.md#Execution-Plan` を指す。quick (express) で Stage 計画が `N/A - single-stage express` の場合は `Stage Continuity Source: requirements.md#Implementation-Sequence-Plan (N/A - single-stage express)` と書く
