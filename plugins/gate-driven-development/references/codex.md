# Codex Model Routing

Codex CLI 環境向けのモデル選択ルール。Claude Code / Cursor 環境では参照不要。

> **2026-08-25 最新化**: GPT-5.4 / GPT-5.5 体系から **GPT-5.6 系（Sol / Terra / Luna）**へ移行した。
> GPT-5.4 は ChatGPT サインイン利用の Codex で 2026-08-31 に廃止予定のため使わない。
> GPT-5.5 も一世代前となったため、同等性能で低コストの Terra に置き換える。
> 旧体系の判断根拠は CHANGELOG の当時のエントリを参照。

**方針: GPT-5.6 の階層（Sol / Terra / Luna）+ effort 差別化**を採用する。ただし **Codex CLI は Anthropic Claude 系（Opus 等）にアクセスできない** ため、Cursor と異なり Dialectic Counter には Anthropic を使えず、**別階層の GPT-5.6 + 別 prompt role** で観点多様化を確保する。

## Codex Subagent Delegation Permission

Codex の subagent ツールは **ユーザーが明示的に委譲を依頼した場合のみ**使う。GDD はこれを「Codex では subagent が使えない」とは扱わず、明示委譲ソースを workflow contract に入れる。

- **明示委譲ソース**: ユーザーの自然文（例: `承認しなくてもsubagentを使ってほしい` / `subagent も使ってよい` / `サブエージェントに委譲してよい`）、project policy、または `/gdd-dev` 引数に明示の委譲許可がある場合は、`explicit_delegation_source=<source>` として扱う。
- **明示委譲ソースあり**: `state.md` の `Approved Direction` に `Codex Subagent Delegation Permission: approved_by_explicit_delegation` と `explicit_delegation_source` を記録する。HITL で改めて承認を求めない。human-check には「すでに許可済みの場合」として表示し、判断点にしない。
- **明示委譲ソースなし**: HITL で subagent 委譲可否を露出する。human-check には `subagent 委譲` の判断点を出し、許可する場合 / 許可しない場合の作業速度・検証境界・並列可否を短く説明する。
- **承認後**: `state.md` の `Approved Direction` に `Codex Subagent Delegation Permission: approved_by_explicit_delegation | approved | denied | not_applicable` を記録する。approved 系の場合だけ実装バッチや reviewer lane で subagent を使える。
- **許可なし**: Codex では許可が無いまま subagent を起動しない。代替は main session inline execution + sequential execution とし、parallel batch は sequential に落として進める。
- **許可を取り直す条件**: task 粒度・委譲範囲・subagent が触る file scope が HITL の説明から変わる場合は、`human_recheck_required` として再確認する。

この permission は危険操作の承認ではない。merge / deploy / terraform apply / AWS write / DB write / Docker push は、引き続き operation safety の 1 操作ごとの明示承認が必要。

## 方針（GPT-5.6 階層 + effort 差別化）

- **`gpt-5.6-sol` を heavy tier の基本**にする（GPT-5.6 最上位。複雑なコーディング / research 向け。Codex CLI の既定モデルでもある）
  - 一般 heavy（debug / refactor / advisory review）: `reasoning.effort=low`
  - 一般 heavy の risk escalation（undocumented step / large working-set / security-sensitive / final review）: `reasoning.effort=high`
  - formal gate（brainstorming / requirements-gating / design-gating / impl-gating / completion-check）: `reasoning.effort=medium`（Codex CLI 既定の `gpt-5.6-sol` + `medium` と同じ）
- **実装は `gpt-5.6-terra` + `reasoning.effort=low`**（GPT-5.5 相当の性能でバランス型・低コスト。旧 `GPT-5.5 + low` の実装枠を引き継ぐ）
- **light は `gpt-5.6-terra` + `reasoning.effort=medium`**（task-breakdown / TDD / pre-workflow-brainstorming / test-failure-debug-pack / receiving-code-review）。`gdd-pr-review` は light ではなく `general_heavy_risk`（`gpt-5.6-sol` + `reasoning.effort=high`）に固定する
- **leaf は `gpt-5.6-terra` + `reasoning.effort=low`**（status / metrics / worktree）。state / routing source を読むため Luna には落とさない
- **`gpt-5.6-luna` + `reasoning.effort=high` は cheap/read-only lane 専用**（最速・最安の階層。短い要約、リンク確認、一覧整形、state 更新なし、routing 判断なし）
- **使わないもの**: `GPT-5.4` 系全般（2026-08-31 廃止予定。mini / nano 含む）、`GPT-5.5`（Terra が同等性能・低コストで置き換え）、`reasoning.effort=xhigh`（Sol 系のみ対応との情報だが公式一次確認が不完全でコスト過剰）、`reasoning.effort=minimal`
- **Dialectic Review の Counter evaluator は Anthropic を使えない**: Codex CLI は OpenAI 系専用のため、Cursor のような Opus + `high` の Counter は不可。代わりに**別階層の `gpt-5.6-terra`** + **別 prompt role**で観点多様化を確保
- **独立レビュー**は `references/fixed-models.md` の `independent_review` tier の Codex 列（`gpt-5.6-sol` + `reasoning.effort=high`）で起動する。起動するのは上の § Codex Subagent Delegation Permission の許可（明示委譲ソースを含む）があるときだけで、許可が無いときは inline で代替しない（実装文脈を渡さない契約を満たさない）。unavailable（委譲許可なし）と記録してユーザーに渡す。agent 定義を直接起動しない（Codex では agent 定義による起動を前提にしない。frontmatter の `model: opus` は Anthropic 不可で解決できない。起動の失敗は Cursor で実測し、Codex では未実測）。会話を引き継がない read-only の別コンテキストを、列のモデルと effort を明示して起動し、定義の本文（frontmatter を除く）と埋めたテンプレートを prompt に貼る。frontmatter を除くと `tools: Read, Grep, Glob` の制限が落ちるので、起動側で使えるツールを Read・Grep・Glob 相当に絞る（Codex は read-only の sandbox）。絞れないときは、read-only が散文だけの規定になったことを記録に書く。明示できないときだけ inherit にし、main が列と同じモデル・effort であることを確かめる。記録にはモデルと effort の両方を書く。列のモデルと effort で走ったときは、独立レビューのモデル条件を満たしたものとする。届かない、または確かめられないときは満たしたとせず、unavailable（model 条件未達: 実際のモデル・effort）と記録する。起動に失敗しても、この経路を 1 回試すまでは unavailable と記録しない。GDD の `agents/*.md` の reviewer は、上の § Codex Subagent Delegation Permission の許可があるときだけ本文を貼る同じ経路で起動し（モデルはその工程の tier に従う。ツールと sandbox は定義どおりにし、read-only に絞らない。Read・Grep・Glob への制限は独立レビューだけ）、許可が無ければ main session inline execution で実行する
- **mini禁止境界**: `gpt-5.6-luna` は HITL生成 / requirements判断 / design判断 / routing判断 / state更新 / worktree判断 / completion判定 / PR可否判断に使わない

## 共通 tier mapping（Codex）

| tier | Codex model | effort |
|---|---|---|
| `formal_gate` | `gpt-5.6-sol` | `medium` |
| `general_heavy` | `gpt-5.6-sol` | `low` |
| `general_heavy_risk` | `gpt-5.6-sol` | `high` |
| `light_task` | `gpt-5.6-terra` | `medium` |
| `leaf_task` | `gpt-5.6-terra` | `low` |
| `cheap_readonly` | `gpt-5.6-luna` | `high` |
| `implementation` | `gpt-5.6-terra` | `low` |
| `dialectic_counter` | `gpt-5.6-terra` + reviewer prompt role | `high` |
| `remediation_loop` | `gpt-5.6-sol` | `high` |
| `independent_review` | `gpt-5.6-sol` | `high` |

## 工程別の使い分け

| Skill | Codex model | effort | 備考 |
|---|---|---|---|
| `gdd-pre-workflow-brainstorming` | `gpt-5.6-terra` | `medium` | 壁打ち（light tier） |
| **`gdd-brainstorming`** | **`gpt-5.6-sol`** | **`medium`** | 要件整理・初稿（formal gate 扱い） |
| **`gdd-requirements-gating`** | **`gpt-5.6-sol`** | **`medium`** | brainstorming と同一 subagent で完走 |
| **`gdd-design-gating`** | **`gpt-5.6-sol`** | **`medium`** | detailed design + security boundary |
| `gdd-task-breakdown` | `gpt-5.6-terra` | `medium` | light tier |
| `gdd-test-driven-development` | `gpt-5.6-terra` | `medium` | light tier |
| `gdd-subagent-driven-implementation` | `gpt-5.6-terra` | `low` | 実装（GPT-5.5 相当・低コスト） |
| **`gdd-implementation-gating`** | **`gpt-5.6-sol`** | **`medium`** | formal impl gate + reviewer dispatch |
| `gdd-systematic-debugging` | `gpt-5.6-sol` | `low` | route 判定（一般 heavy。`remediation_loop` 中は `high`） |
| **`gdd-completion-check`** | **`gpt-5.6-sol`** | **`medium`** | 最終 gate + comprehensive review |
| `gdd-refactor-planning` | `gpt-5.6-sol` | `low` | refactor 計画（一般 heavy） |
| `gdd-requesting-code-review` | `gpt-5.6-sol` | `low` | advisory review（一般 heavy） |
| `gdd-pr-review` | `gpt-5.6-sol` | `high` | general_heavy_risk 固定（最終 diff review） |
| `gdd-test-failure-debug-pack` | `gpt-5.6-terra` | `medium` | light tier |
| `gdd-receiving-code-review` | `gpt-5.6-terra` | `medium` | light tier |
| `gdd-status` / `gdd-metrics` / `gdd-using-git-worktrees` | `gpt-5.6-terra` | `low` | leaf tier（admin task。state / routing source を読むため Luna 不使用） |
| cheap/read-only lane | `gpt-5.6-luna` | `high` | 短い要約 / link check / 一覧整形。state 更新なし、routing 判断なし |

## Dialectic Review Lane の役割割当

`references/dialectic-review.md` の Trigger に該当する変更で起動。**Codex は Anthropic にアクセスできないため、prompt role + 別階層 model で観点多様化を確保する**:

| Role | Codex model | 理由 |
|---|---|---|
| Primary evaluator | 当該 skill の既定 model（多くは `gpt-5.6-sol` + `low`、formal gate なら `gpt-5.6-sol` + `medium`） | 通常の workflow を進める model。`implementer perspective` の prompt role |
| **Counter evaluator** | **`gpt-5.6-terra` + `reasoning.effort=high`** + `reviewer perspective` prompt role | **別階層の GPT-5.6** + `blind spot finder / reviewer perspective` の prompt role で観点多様化 |
| Cross-review | 当該 skill の既定 model に戻す | Primary の context で synthesize |
| Final synthesis | 当該 skill の既定 model | Primary 系に戻して最終判断 |

**Counter prompt role の規約**:

- Primary は `implementer perspective`（「実装可能か」「既存制約と合うか」「具体案を構築できるか」）
- Counter は `reviewer perspective`（「blind spot は何か」「過剰 / 不足はどこか」「severity calibration が緩いか」「読み手にとって判断しやすいか」）
- 同じ会話 / role に **両方を混ぜない**。独立 invocation を 2 回行う

**Counter で別階層 GPT-5.6 を使う理由**:

- 同一 model + 同一 prompt では観点が同質化しやすい（confirmation bias）
- 別階層（Sol ↔ Terra）+ 別 prompt role の組み合わせで、最低限の「異なる視点」を確保
- Cursor のような cross-system（Grok vs Anthropic）には及ばないが、Codex 環境で取れる最善の多様化策

最終とりまとめは Primary 系統に戻す。Counter で出た反論を Primary 文脈で消化する。

## Think モード

- `reasoning.effort` は `low` / `medium` / `high` の **3 段階**で扱う（Codex CLI 自体は `minimal`〜`xhigh` の 5 段階を持つが、`minimal` と `xhigh` は使わない）
- `low`: gpt-5.6-sol 一般 heavy の標準（コスト最適化）/ gpt-5.6-terra 実装・leaf の標準
- `medium`: gpt-5.6-sol formal gate の標準（Codex CLI の既定と同じ）/ gpt-5.6-terra light tier の標準
- `high`: gpt-5.6-luna cheap/read-only lane、一般 heavy の risk escalation、Dialectic Counter（gpt-5.6-terra + reviewer prompt role）

## 起動時の固定表（Codex）

| 役割 | Codex model | effort |
|---|---|---|
| **要件整理・初稿（brainstorming / requirements-gating）** | **`gpt-5.6-sol`** | **`medium`** |
| 通常レビュー / 一般 heavy（systematic-debug / refactor-plan / requesting-code-review） | `gpt-5.6-sol` | `low` |
| 一般 heavy risk escalation（undocumented step / large working-set / security-sensitive / final review） | `gpt-5.6-sol` | `high` |
| **formal gate（design / impl / completion）** | **`gpt-5.6-sol`** | **`medium`** |
| **Dialectic Counter** | **`gpt-5.6-terra`** + `reviewer prompt role` | `high` |
| 実装 | `gpt-5.6-terra` | `low` |
| **light task**（task-breakdown / TDD / pre-workflow / test-failure-debug-pack / receiving-code-review） | **`gpt-5.6-terra`** | **`medium`** |
| **leaf task**（status / metrics / using-git-worktrees） | **`gpt-5.6-terra`** | **`low`** |
| cheap/read-only lane（短い要約 / link check / 一覧整形） | `gpt-5.6-luna` | `high` |

## Codex 固有モデルの扱い

過去には `gpt-5.1-codex-max` / `gpt-5.2-codex` / `gpt-5.3-codex` のような `-codex` 接尾辞の派生モデルが存在したが、いずれも廃止済みで、GPT-5.6 世代では Sol / Terra / Luna の階層名が Codex CLI でもそのまま使われている。新しい Codex 専用モデルが提供された場合は、本 reference と `scripts/resolve-gdd-model.py` の `TIER_TO_MODEL["codex"]` を update する。

## 判断の書き方（Codex）

```text
model: gpt-5.6-terra (Codex, reasoning.effort=medium) - light task（task-breakdown / TDD 等）の標準
```

```text
model: gpt-5.6-terra (Codex, reasoning.effort=low) - leaf task（status / metrics / worktree）と実装の標準
```

```text
model: gpt-5.6-luna (Codex, reasoning.effort=high) - cheap/read-only lane（state 更新なし、routing 判断なし）
```

```text
model: gpt-5.6-sol (Codex, reasoning.effort=low) - 一般 heavy（debug / refactor / advisory review）の標準
```

```text
model: gpt-5.6-sol (Codex, reasoning.effort=high) - 一般 heavy の risk escalation / 最終 diff review
```

```text
model: gpt-5.6-sol (Codex, reasoning.effort=medium) - formal gate（brainstorming / requirements-gating / design-gating / implementation-gating / completion-check）の標準
```

```text
model: gpt-5.6-terra (Codex, reasoning.effort=high, prompt_role=reviewer) - Dialectic Counter として別階層 GPT-5.6 + reviewer perspective で観点多様化（Anthropic 不可のため）
```
