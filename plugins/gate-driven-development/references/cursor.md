# Cursor Model Routing

Cursor 環境向けのモデル選択ルール。Claude Code 環境では参照不要。

> **2026-08-25 最新化**: GPT-5.4 / GPT-5.5 体系から **Grok + Composer 主体**へ移行した。
> GPT-5.4 は 2026-08-31 に廃止予定であり、GPT 系は本 routing から除外する。
> 旧体系の判断根拠は CHANGELOG の当時のエントリを参照。

## 方針（Grok 4.6 + effort 差別化、実装は Composer）

- **`Grok 4.6` を heavy tier の基本**にする（2026-08 時点の xAI 旗艦。long-running agent / コーディング向け）
  - 一般 heavy（debug / refactor / advisory review）: `reasoning.effort=low`
  - 一般 heavy の risk escalation（undocumented step / large working-set / security-sensitive / final review）: `reasoning.effort=high`
  - formal gate（brainstorming / requirements-gating / design-gating / impl-gating / completion-check）: `reasoning.effort=medium`
- **leaf は `Grok 4.5` + `reasoning.effort=low`**（status / metrics / worktree）。state / routing source を読むため cheap lane には落とさない
- **light は `Grok 4.5` + `reasoning.effort=medium`**（task-breakdown / TDD / pre-workflow-brainstorming / test-failure-debug-pack / receiving-code-review）。`pr-review` は light ではなく `general_heavy_risk`（`Grok 4.6` + `reasoning.effort=high`）に固定する
- **cheap/read-only lane は `Grok 4.5` + `reasoning.effort=low` 専用**（短い要約、リンク確認、一覧整形、state 更新なし、routing 判断なし）。`Grok Code Fast 1` がモデルピッカーに残っていればそちらを使ってよい（2026-08-25 時点で提供継続は未確認）
- **実装は `Composer 2.5` に固定**: `composer-2-fast` は使わない（Composer 3 は未リリース。リリースされたら本 reference を更新）
- **Dialectic Review の Counter evaluator** は `Opus`（Cursor のモデル一覧にある最新の Opus）+ `reasoning.effort=high` に固定（cross-system 観点を確保。Grok/Composer 主体の唯一の例外）
- **使わないもの**: GPT 系全般（GPT-5.4 は 2026-08-31 廃止予定、GPT-5.5 も本 routing から除外。混在させない）、`reasoning.effort=xhigh`（Grok 4.6 は API 上対応だが Cursor UI での露出は未確認・コスト過剰）、`reasoning.effort=none`
- **mini禁止境界**: cheap lane モデル（`Grok Code Fast 1` 等の軽量特化モデル）は HITL生成 / requirements判断 / design判断 / routing判断 / state更新 / worktree判断 / completion判定 / PR可否判断に使わない

## 共通 tier mapping（Cursor）

| tier | Cursor model | effort |
|---|---|---|
| `formal_gate` | `Grok 4.6` | `medium` |
| `general_heavy` | `Grok 4.6` | `low` |
| `general_heavy_risk` | `Grok 4.6` | `high` |
| `light_task` | `Grok 4.5` | `medium` |
| `leaf_task` | `Grok 4.5` | `low` |
| `cheap_readonly` | `Grok 4.5`（`Grok Code Fast 1` が使えればそちら） | `low` |
| `implementation` | `Composer 2.5` | — |
| `dialectic_counter` | `Opus`（一覧の最新） | `high` |
| `remediation_loop` | `Grok 4.6` | `high` |
| `independent_review` | `Grok 4.6` | `high` |

## なぜ Grok 4.6 / 4.5 の 2 段構成か

- **Grok 4.6**（2026-08-12 リリース）: xAI 現行旗艦。500K コンテキスト、reasoning effort 4 段階、long-running agent・コーディング向けと公式が明記。heavy 側をここに寄せる
- **Grok 4.5**（2026-07 リリース）: 前世代旗艦。20 万トークン以下の価格は 4.6 と同額だが、light / leaf 用途には十分で応答も軽い。旧 GPT-5.4 の位置づけを引き継ぐ
- effort 差別化の考え方（gate=medium / heavy=low / risk=high）は旧 GPT-5.5 体系から変更しない。モデル名だけ差し替える

## 工程別の使い分け

| Skill | Cursor model | effort | 備考 |
|---|---|---|---|
| `gdd-pre-workflow-brainstorming` | `Grok 4.5` | `medium` | 壁打ち（light tier） |
| **`gdd-brainstorming`** | **`Grok 4.6`** | **`medium`** | 要件整理・初稿（formal gate 扱い） |
| **`gdd-requirements-gating`** | **`Grok 4.6`** | **`medium`** | brainstorming と同一 subagent で完走 |
| **`gdd-design-gating`** | **`Grok 4.6`** | **`medium`** | detailed design + security boundary |
| `gdd-task-breakdown` | `Grok 4.5` | `medium` | light tier |
| `gdd-test-driven-development` | `Grok 4.5` | `medium` | light tier |
| `gdd-subagent-driven-implementation` | `Composer 2.5` | — | `composer-2-fast` 不使用 |
| **`gdd-implementation-gating`** | **`Grok 4.6`** | **`medium`** | formal impl gate + reviewer dispatch |
| `gdd-systematic-debugging` | `Grok 4.6` | `low` | route 判定（一般 heavy） |
| `gdd-systematic-debugging` / `gdd-refactor-planning` / `gdd-requesting-code-review` の risk escalation | `Grok 4.6` | `high` | undocumented step / large working-set / security-sensitive / final review |
| **`gdd-completion-check`** | **`Grok 4.6`** | **`medium`** | 最終 gate + comprehensive review |
| `gdd-refactor-planning` | `Grok 4.6` | `low` | refactor 計画（一般 heavy） |
| `gdd-requesting-code-review` | `Grok 4.6` | `low` | advisory review（一般 heavy） |
| `gdd-pr-review` | `Grok 4.6` | `high` | general_heavy_risk 固定（最終 diff review） |
| `gdd-test-failure-debug-pack` | `Grok 4.5` | `medium` | light tier |
| `gdd-receiving-code-review` | `Grok 4.5` | `medium` | light tier |
| `gdd-status` / `gdd-metrics` / `gdd-using-git-worktrees` | `Grok 4.5` | `low` | leaf tier（admin task。state / routing source を読むため cheap lane 不使用） |
| cheap/read-only lane | `Grok 4.5`（`Grok Code Fast 1` が使えればそちら） | `low` | 短い要約 / link check / 一覧整形。state 更新なし、routing 判断なし |

## Dialectic Review Lane の役割割当

`references/dialectic-review.md` の Trigger に該当する変更で起動。**Cross-system 観点を確保するため、Primary（Grok 系）と Counter（Anthropic 系）を分離する**:

| Role | Cursor model | 理由 |
|---|---|---|
| Primary evaluator | 当該 skill の既定 model（多くは `Grok 4.6` + `low`、formal gate なら `Grok 4.6` + `medium`） | 通常の workflow を進める model |
| **Counter evaluator** | **`Opus` + `reasoning.effort=high`** | Grok 系と異なる Anthropic 系を使い、観点の同質化を避ける |
| Cross-review | 当該 skill の既定 model に戻す | Primary の context で synthesize |
| Final synthesis | 当該 skill の既定 model | Primary 系に戻して最終判断 |

- 通常の Counter には Opus + `high` を使う。`max` は使わない
- Counter で Opus が利用不可な環境では、Primary とは別の prompt role で `Grok 4.5` を使う fallback とする
- 最終とりまとめは Primary 系統に戻す。Counter で出た反論を Primary 文脈で消化する

## Think モード

- `reasoning.effort` は `low` / `medium` / `high` の **3 段階**で扱う（Grok 4.6 の `xhigh` は Cursor UI での露出未確認のため使わない、`none` は実質不使用）
- `low`: Grok 4.6 一般 heavy の標準（コスト最適化）/ Grok 4.5 leaf・cheap lane の標準
- `medium`: Grok 4.6 formal gate の標準（精度優先）/ Grok 4.5 light tier の標準
- `high`: 一般 heavy の risk escalation・最終 diff review（Grok 4.6）、Dialectic Counter（Opus）

## 起動時の固定表（Cursor）

| 役割 | Cursor model | effort |
|---|---|---|
| **要件整理・初稿（brainstorming / requirements-gating）** | **`Grok 4.6`** | **`medium`** |
| 通常レビュー / 一般 heavy（systematic-debug / refactor-plan / requesting-code-review） | `Grok 4.6` | `low` |
| 一般 heavy risk escalation（undocumented step / large working-set / security-sensitive / final review） | `Grok 4.6` | `high` |
| **formal gate（design / impl / completion）** | **`Grok 4.6`** | **`medium`** |
| **Dialectic Counter** | **`Opus`** | **`high`** |
| 実装 | `Composer 2.5` | — |
| **light task**（task-breakdown / TDD / pre-workflow-brainstorming / test-failure-debug-pack / receiving-code-review） | **`Grok 4.5`** | **`medium`** |
| **leaf task**（status / metrics / using-git-worktrees） | **`Grok 4.5`** | **`low`** |
| cheap/read-only lane（短い要約 / link check / 一覧整形） | `Grok 4.5` | `low` |

## 初稿とレビュー（Cursor）

- `gdd-pre-workflow-brainstorming` は `Grok 4.5` + `effort=medium` に固定（light tier）
- 要件整理 / formal gate（brainstorming / requirements / design / impl / completion）は `Grok 4.6` + `effort=medium` に固定
- 一般 heavy（debug / refactor / advisory review）は `Grok 4.6` + `effort=low` を標準にし、undocumented step / large working-set / security-sensitive / final review では `effort=high` に上げる
- **light task**（task-breakdown / TDD / test-failure-debug-pack 等）は `Grok 4.5` + `effort=medium` に統一
- **leaf task**（status / metrics / using-git-worktrees）は `Grok 4.5` + `effort=low` に統一（admin タスクでも state / routing source を読むため cheap lane には落とさない）
- **cheap/read-only lane**（短い要約 / link check / 一覧整形、state 更新なし、routing 判断なし）だけ `Grok 4.5` + `effort=low`（`Grok Code Fast 1` が使えればそちら）を使う
- mini禁止境界: cheap lane モデルは HITL生成、requirements判断、design判断、routing判断、state更新、worktree判断、completion判定、PR可否判断には使わない
- **独立レビュー**は `references/fixed-models.md` の `independent_review` tier の Cursor 列（`Grok 4.6` + `reasoning.effort=high`）で起動する。agent 定義を直接起動しない（frontmatter の `model: opus` は Cursor の Task では解決できずに起動が落ちる。2026-09-18 実測、inherit なら起動できた）。会話を引き継がない read-only の別コンテキストを、列のモデルと effort を明示して起動し、定義の本文（frontmatter を除く）と埋めたテンプレートを prompt に貼る。frontmatter を除くと `tools: Read, Grep, Glob` の制限が落ちるので、起動側で使えるツールを Read・Grep・Glob 相当に絞る（Cursor は Task の readonly 指定。指定の有無は未確認）。絞れないときは、read-only が散文だけの規定になったことを記録に書く。明示できないときだけ inherit にし、main が列と同じモデル・effort であることを確かめる。記録にはモデルと effort の両方を書く。列のモデルと effort で走ったときは、独立レビューのモデル条件を満たしたものとする。届かない、または確かめられないときは満たしたとせず、unavailable（model 条件未達: 実際のモデル・effort）と記録する。起動に失敗しても、この経路を 1 回試すまでは unavailable と記録しない。GDD の `agents/*.md` の reviewer も、定義のままでは起動できないときは本文を貼る同じ経路で起動し（モデルはその工程の tier に従う。ツールと sandbox は定義どおりにし、read-only に絞らない。Read・Grep・Glob への制限は独立レビューだけ）、それでも起動できないときだけ inline review（`references/inline-review-checklists.md`）にフォールバックする
- Dialectic Review の Counter は **Opus + `reasoning.effort=high`** で cross-system 観点を確保

## 判断の書き方（Cursor）

```text
model: Grok 4.5 (Cursor, reasoning.effort=medium) - light task（task-breakdown / TDD 等）の標準
```

```text
model: Grok 4.5 (Cursor, reasoning.effort=low) - leaf task（status / metrics / worktree）と cheap/read-only lane（state 更新なし、routing 判断なし）の標準
```

```text
model: Composer 2.5 (Cursor) - Cursor で標準実装を行うため。composer-2-fast は使わない
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=low) - 一般 heavy（debug / refactor / advisory review）の標準
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=high) - 一般 heavy の risk escalation / 最終 diff review
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=medium) - formal gate（brainstorming / requirements-gating / design-gating / implementation-gating / completion-check）の標準
```

```text
model: Opus (Cursor, reasoning.effort=high) - Dialectic Review の Counter evaluator として cross-system 観点を確保するため
```
