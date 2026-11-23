---
name: gdd-model-routing
description: "Use when choosing models or reasoning effort for GDD phases, worker tasks, reviews, cost, or speed tradeoffs."
version: 0.5.0
---

# GDD Model Routing

`gate-driven-development` の中だけでモデル選択を完結させるための skill。`scripts/run-with-plugin.sh` と `scripts/setup-gdd-loop.sh` は、この skill の考え方を起動時の既定値に落とし込む。

`references/cursor.md` は Cursor の詳細ルール。ここでは Claude Code と Cursor の両方で共通に使う model 方針をまとめる。実際の model 名は host ごとに分かれるので、共有するのは policy だけにする。

## Autonomous Model Workers

Codex / Cursor で工程ごとの model / effort を使い分ける場合、メインセッション自身が途中で model 切替されたと主張しない。`references/subagent-dispatch.md` を参照し、`scripts/run-gdd-worker.py` が `worker_runs/<run_id>/result.json` を残したときだけ requested execution として扱う。`Recommended model` は案内であり、実適用の証拠ではない。

## 同じ skill を両環境で使うとき

- この skill の正本は `skills/gdd-model-routing/SKILL.md` に置く。Cursor は `.claude/skills/` を互換読み込みするので、同じ skill をそのまま両環境で使える。
- `Cursor` 側で同名 skill を別途持つ場合は、project / user の優先コピーとして扱う。意図的な上書きでない限り、両方に別内容を置かない。
- `Claude Code` の `sonnet` / `opus`（alias。版は Claude Code が解決する）と `Cursor` の `Grok 4.6` / `Grok 4.5` / `Composer 2.5` / `Opus`（Dialectic Counter。Cursor のモデル一覧にある最新の Opus）、`Codex` の `gpt-5.6-sol` / `gpt-5.6-terra` / `gpt-5.6-luna` は別の名前空間として扱う。片方の model 指示をもう片方へ流用しない。
- dialectic review では model 名ではなく `Primary evaluator` / `Counter evaluator` / `Final synthesizer` の役割を固定する。host ごとの具体 model は下の § Dialectic Review のモデル割当 の表に従う。
- `model` frontmatter と `effort` frontmatter は、その skill や subagent が active の間だけ有効で、session 全体の既定値とは別に効く。
- したがって、共有ポリシーはこの `SKILL.md` に置き、Cursor 固有の差分だけを `references/cursor.md` に逃がす。

## 判断の優先順位

1. ユーザーが model を明示した場合は、その指定を優先する。ただし formal gate（brainstorming / requirements-gating / design-gating / impl-gating / completion-check）へ推奨 tier より軽いモデルのまま進入する場合は、乖離と影響（レビュー・判断の検出力低下）を明示して 1 回だけ確認を取り、選択結果を `state.md` の `Last Handoff Summary` に 1 語（例: `model-ack:sonnet`）残す。同一 workflow 内での再確認はしない。
2. `曖昧さ`
3. `reasoning horizon` の長さ
4. `working-set` の広さ
5. `tool / shell heavy` かどうか
6. `最終判断` や `security-sensitive` かどうか

## 共通 tier 正本

Claude Code / Cursor / Codex は同じ tier 名で判断し、host ごとの実モデルへ mapping する。resolver と文書の正本 tier は以下:

| tier | 用途 |
|---|---|
| `formal_gate` | brainstorming / requirements / design / implementation-gating / completion-check など、人間承認・正式 gate・最終判断に直結する工程 |
| `general_heavy` | systematic-debug / refactor-plan / requesting-code-review など、広めの推論は要るが通常は risk escalation ではない工程 |
| `general_heavy_risk` | undocumented step / large working-set / security-sensitive / final review など、重い推論へ昇格する工程（往復発生時は `remediation_loop` が優先）。`gdd-pr-review`（最終 diff review）はここに固定（2026-08-25 昇格。gate 通過後に残った実害級の欠陥を検出したのは、当時の Opus+high の最終レビューだけだった） |
| `light_task` | task-breakdown / TDD / pre-workflow / test-failure-debug-pack / receiving-code-review |
| `leaf_task` | status / metrics / using-git-worktrees などの admin task。state / routing source を読むため mini には落とさない |
| `cheap_readonly` | 短い要約 / link check / 一覧整形。state 更新なし、routing 判断なし |
| `implementation` | 承認済み AC に対する bounded な実装 |
| `dialectic_counter` | Dialectic Review の反対評価役 |
| `independent_review` | push 前の独立レビュー（実装文脈を渡さない read-only の別コンテキスト。正本は `references/independent-review.md`） |

## Host 別 tier mapping

| tier | Claude Code | Cursor | Codex |
|---|---|---|---|
| `formal_gate` | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=medium` | `gpt-5.6-sol` + `reasoning.effort=medium` |
| `general_heavy` | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=low` | `gpt-5.6-sol` + `reasoning.effort=low` |
| `general_heavy_risk` | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=high` | `gpt-5.6-sol` + `reasoning.effort=high` |
| `light_task` | `sonnet` + `effort=medium` | `Grok 4.5` + `reasoning.effort=medium` | `gpt-5.6-terra` + `reasoning.effort=medium` |
| `leaf_task` | `sonnet` + `effort=low` | `Grok 4.5` + `reasoning.effort=low` | `gpt-5.6-terra` + `reasoning.effort=low` |
| `cheap_readonly` | `haiku` 相当が使える場合のみ | `Grok 4.5` + `reasoning.effort=low`（`Grok Code Fast 1` が使えればそちら） | `gpt-5.6-luna` + `reasoning.effort=high` |
| `implementation` | `sonnet` + `effort=medium`、`Complexity: standard` でない task は `opus` + `effort=high` | `Composer 2.5`（`composer-2-fast` 不使用） | `gpt-5.6-terra` + `reasoning.effort=low` |
| `dialectic_counter` | `opus` + `effort=high` | `Opus` + `reasoning.effort=high` | `gpt-5.6-terra` + `reasoning.effort=high` + reviewer prompt role |
| `remediation_loop`（往復発生時の route 判断・再レビュー・remediation 実装。開始条件は `references/fixed-models.md`） | `opus` + `effort=xhigh` | `Grok 4.6` + `reasoning.effort=high` | `gpt-5.6-sol` + `reasoning.effort=high` |
| `independent_review` | `opus` + `effort=xhigh` | `Grok 4.6` + `reasoning.effort=high` | `gpt-5.6-sol` + `reasoning.effort=high` |

## 既定

- 軽いモデルは `sonnet`。
- 重いモデルは `opus`。
- 調査と既存コードの確認はまず `sonnet` を使う。実装の worker は task の `Complexity:` で決める（未宣言は `opus`）。
- 要件の曖昧さが大きいとき、または最終判断が必要なときだけ `opus` に上げる。

## Claude Code のモデル使い分け

Sonnet（`sonnet`）を通常の実行役、Opus（`opus`）を判断役として使う。

- `sonnet` は `gdd-pre-workflow-brainstorming`、`gdd-task-breakdown`、`gdd-test-driven-development`、leaf task、bounded な実装・要約・確認に使う。
- `opus` は `gdd-brainstorming`（requirements-gating と同一 subagent で完走）、`gdd-requirements-gating`（reviewer subagent）、`gdd-design-gating`（reviewer subagent）、`gdd-implementation-gating`（reviewer subagent）、`gdd-systematic-debugging`、`gdd-completion-check`（reviewer subagent）、`gdd-refactor-planning` に使う。
- `gdd-subagent-driven-implementation` は `implementation` tier とする。worker subagent は task の `Complexity:` と `Gate Rounds` で 3 つの agent 定義から選ぶ（正本: `references/fixed-models.md` の `implementation` tier の段落。往復による昇格は `remediation_loop`）。
- `opus + effort=high` は、正式レビュー・最終確認・デバッグ計画・リファクタ計画の固定値にする。Claude Code の reviewer subagent frontmatter / Agent ツール指定は `model="opus"` alias を使い、実行環境側で最新の Opus に解決される前提にする（既定の設定では、解決先は Claude Code の版で決まる。`references/fixed-models.md` § モデル名の書き方）。
- 新しい版や model family が出たときは、tier 表の alias で表せるかを確かめ、対象 agent frontmatter（`model` / `effort`）の整合も見直す。alias で表せない family なら、本 tier 表も更新する。
- `sonnet + effort=high` は、相談だけの壁打ち（`gdd-pre-workflow-brainstorming`）に使う。
- `sonnet + effort=low` は leaf task 専用にする。
- `sonnet` で進めていても、`曖昧さ`、`working-set` の広さ、`security-sensitive`、`final review` の信号が出たら `opus` に上げる（実装の worker は `gdd-implementation-worker-heavy` に替える）。

## Cursor / Codex のモデル使い分け（2026-08-25 最新化: Cursor は Grok + Composer 主体、Codex は GPT-5.6 系）

`references/cursor.md` / `references/codex.md` を正本として扱う。

- **heavy tier の基本モデル**は Cursor が `Grok 4.6`、Codex が `gpt-5.6-sol`（Codex CLI の既定モデル）
  - 一般 heavy（debug / refactor / advisory review）: `reasoning.effort=low`
  - **formal gate（brainstorming / requirements-gating / design-gating / impl-gating / completion-check）: `reasoning.effort=medium`**
- **light task の標準**は Cursor が `Grok 4.5` + `medium`、Codex が `gpt-5.6-terra` + `medium`（task-breakdown / TDD / pre-workflow-brainstorming / test-failure-debug-pack / receiving-code-review）。`pr-review` は light ではなく `general_heavy_risk`（heavy 基本モデル + `high`）
- **leaf / admin task の標準**は Cursor が `Grok 4.5` + `low`、Codex が `gpt-5.6-terra` + `low`（status / metrics / using-git-worktrees など）。leaf でも state / tasklist / worktree / routing source を読むため、cheap lane（Luna / Grok Code Fast 1 等）には落とさない
- **cheap/read-only lane 専用**モデルは Cursor が `Grok 4.5` + `low`（`Grok Code Fast 1` が使えればそちら）、Codex が `gpt-5.6-luna` + `high`。Haiku 相当の使い所（短い read-only 要約、リンク確認、一覧整形、state 更新なし、routing 判断なし）だけで使う
- **GPT-5.4 系は使わない**（2026-08-31 廃止予定。mini / nano 含む）。**GPT-5.5 も使わない**（Codex は同等性能・低コストの `gpt-5.6-terra` へ、Cursor は Grok 系へ置換済み）
- **`reasoning.effort=xhigh` は使わない**（high で十分、xhigh はコスト過剰）
- Cursor で実装コードを触るときは `Composer 2.5` を標準にする。`composer-2-fast` は使わない
- **mini禁止境界**: cheap lane モデル（`gpt-5.6-luna` / `Grok Code Fast 1` 等）は HITL生成 / requirements判断 / design判断 / routing判断 / state更新 / worktree判断 / completion判定 / PR可否判断に使わない。cheap/read-only lane だけで使う。
- **Dialectic Review の Counter evaluator**:
  - Cursor: `Opus` + `reasoning.effort=high` に固定（cross-system 観点を確保）
  - Codex: Anthropic 不可のため `gpt-5.6-terra` + `high` + `reviewer prompt role` で代替

**モデル選定の根拠（2026-08-25 時点）**:

- Cursor: `Grok 4.6`（2026-08-12 リリースの xAI 旗艦。long-running agent / コーディング向けと公式明記）を heavy に、`Grok 4.5`（前世代旗艦・light 用途に十分）を light / leaf に置く。実装は `Composer 2.5`（Composer 3 は未リリース）
- Codex: GPT-5.6 系（Sol / Terra / Luna）が 2026-07-09 GA、CLI 既定は `gpt-5.6-sol` + `medium`。`gpt-5.6-terra` は GPT-5.5 相当の性能でバランス型・低コストのため、旧 GPT-5.5 枠と旧 GPT-5.4 枠を統合して置き換える
- 旧 GPT-5.4/5.5 体系の判断根拠は CHANGELOG の当時のエントリを参照

## Think モード

- `effort` は通常 `low` / `medium` / `high` / `xhigh` の 4 段階を使い、`max` は下の Opus の `xhigh` の項に挙げた用途に限る。
- `xhigh` は Opus に後から追加された段で、Claude Code の製品既定でもある。GDD の固定値は `high` を維持し、`xhigh` は限定使用（§ Dialectic Review の使い分け参照: 大規模 migration / 長時間 async / security-sensitive final decision）。固定値の `high`→`xhigh` 格上げは gdd-metrics の before/after 実測を取ってから判断する。
- `low` は速さ優先の単純な調査、軽い要約、定型更新で使う。
- `medium` は通常の調査、軽い実装、既存コード確認で使う。
- `high` は要件が少し曖昧なとき、複数案比較、深いデバッグで使う。
- `think` / `think hard` / `think harder` / `ultrathink` は、推論を段階的に強めるトリガーとして扱う。
- `ultrathink` はそのターンだけ強める。常用設定ではない。

## 起動時の固定表

| 役割                            | Claude Code                | Cursor                                    | Codex                                     |
| ------------------------------- | -------------------------- | ----------------------------------------- | ----------------------------------------- |
| 相談だけの壁打ち                | `sonnet` + `effort=high`   | `Grok 4.5` + `reasoning.effort=medium` | `gpt-5.6-terra` + `reasoning.effort=medium` |
| **formal gate（brainstorming / requirements-gating / design-gating / impl-gating / completion-check）** | `opus` + `effort=high` | **`Grok 4.6` + `reasoning.effort=medium`** | **`gpt-5.6-sol` + `reasoning.effort=medium`** |
| 一般 heavy（systematic-debug / refactor-plan / requesting-code-review） | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=low`  | `gpt-5.6-sol` + `reasoning.effort=low`  |
| **Dialectic Counter** | `opus` + `effort=high` | **`Opus` + `reasoning.effort=high`**（cross-system） | **`gpt-5.6-terra` + `reasoning.effort=high`** + reviewer prompt role（Anthropic 不可） |
| 最終 diff review（gdd-pr-review。general_heavy_risk 固定） | `opus` + `effort=high` | `Grok 4.6` + `reasoning.effort=high` | `gpt-5.6-sol` + `reasoning.effort=high` |
| light task（task-breakdown / TDD / pre-workflow / test-failure-debug-pack / receiving-code-review） | `sonnet` + `effort=medium` | `Grok 4.5` + `reasoning.effort=medium` | `gpt-5.6-terra` + `reasoning.effort=medium` |
| leaf task（status / metrics / using-git-worktrees） | `sonnet` + `effort=low`    | `Grok 4.5` + `reasoning.effort=low` | `gpt-5.6-terra` + `reasoning.effort=low` |
| cheap/read-only lane（短い要約 / link check / 一覧整形、state 更新なし） | `haiku` 相当が使える場合のみ | `Grok 4.5` + `reasoning.effort=low` | `gpt-5.6-luna` + `reasoning.effort=high` |
| 実装                            | `sonnet` + `effort=medium`、`Complexity: standard` でない task は `opus` + `effort=high` | `Composer 2.5`（`composer-2-fast` 不使用）  | `gpt-5.6-terra` + `reasoning.effort=low` |

## Dialectic Review のモデル割当

`references/dialectic-review.md` の Trigger に該当する場合だけ使う。毎回 full dialectic を走らせない。

| 役割              | Claude Code                    | Cursor                                                                                                   | Codex                                                                                |
| ----------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Primary evaluator | 現在の実行 model または `sonnet` | 当該 skill の既定 model（多くは `Grok 4.6` + `low`、formal gate なら `Grok 4.6` + `medium`） | 当該 skill の既定 model（多くは `gpt-5.6-sol` + `low`、formal gate なら `gpt-5.6-sol` + `medium`） |
| **Counter evaluator** | `opus` + `effort=high` | **`Opus` + `reasoning.effort=high`**（cross-system 観点固定。利用不可なら別 role prompt の `Grok 4.5` にフォールバック） | **`gpt-5.6-terra` + `reasoning.effort=high`** + reviewer prompt role（Codex は Anthropic 不可。GPT-5.6 の階層を変えて観点多様化） |
| Final synthesizer | `opus` + `effort=high`     | Primary 系（当該 skill の既定 model）に戻す                                                              | Primary 系（当該 skill の既定 model）に戻す                                          |

使い分け:

- `Primary evaluator` は実装可能性、既存制約、具体案に寄せる（`implementer perspective`）
- `Counter evaluator` は blind spot、過剰/不足、severity calibration、読み手の判断しやすさに寄せる（`reviewer perspective`）
- **Cursor では Opus + `high` を Counter に固定使用**: Primary（Grok 系）と異なる Anthropic 系で cross-system 観点を確保
- **Codex では Anthropic にアクセス不可**: 別階層の GPT-5.6（Primary が Sol なら Counter は Terra、その逆も）+ `reviewer prompt role` で観点多様化。同一 model で prompt role だけ切り替えるフォールバックも可（独立 invocation を 2 回行う）
- `Final synthesizer` は「どちらが優秀か」ではなく `Consensus / Adopted / Rejected / Final Decision / Open Risks` に圧縮する
- Cursor では、最終とりまとめは **Primary 系（Grok 4.6 / Grok 4.5）に戻す**。Counter で出た反論を Primary 文脈で消化する
- model が 1 系統しかない場合は、同一 model で role prompt を分ける。独立評価と cross-review を同じ出力に混ぜない
- **Opus の `xhigh` は限定使用**: 大規模 migration / 長時間 async / security-sensitive final decision のみと、往復の `remediation_loop` と `independent_review`、requirements・design gate の reviewer `gdd-planning-reviewer`（どれも Opus + xhigh）。通常の formal gate は `high` 固定。`max` は `gdd-opus-advisor-max` に限る

## 初稿とレビュー

- `gdd-pre-workflow-brainstorming` は `sonnet + effort=high` / `Grok 4.5 + medium`（Cursor）/ `gpt-5.6-terra + medium`（Codex）に固定する（light tier）。
- **Cursor / Codex の formal gate**（`gdd-brainstorming` / `gdd-requirements-gating` / `gdd-design-gating` / `gdd-implementation-gating` / `gdd-completion-check`）は `Grok 4.6 + medium`（Cursor）/ `gpt-5.6-sol + medium`（Codex）に固定する。`gdd-brainstorming` は requirements-gating と同一 subagent で完走する。
- **一般 heavy**（systematic-debug / refactor-plan / requesting-code-review）は `Grok 4.6 + low`（Cursor）/ `gpt-5.6-sol + low`（Codex）を標準にする（コスト最適化）。ただし undocumented step / large working-set / security-sensitive / final review signal がある場合は `reasoning.effort=high` に上げる。
- 初稿は見出し、前提、判断理由、次アクションを落としすぎない。
- レビュー役は、抜け、矛盾、過剰な省略、実行不能な手順を重点確認する。
- Claude Code では `gdd-task-breakdown` / `gdd-test-driven-development` は `sonnet` のまま進めてよい。実装の worker は task の `Complexity:` と `Gate Rounds` で選ぶ（未宣言は `opus`。正本 `references/fixed-models.md` の `implementation` tier）。
- Cursor の実装ステップは `Composer 2.5` を優先（`composer-2-fast` は使わない）。実装方針の決定や差分レビューは `Grok 4.6 + low` または `Grok 4.6 + medium`（formal gate）に戻す。

## 重いモデルを積極的に使うタスク

- 要件が曖昧で、選択肢の整理や意思決定が必要
- 少しでも不確実性がある、または再確認でやり直しコストが高い
- 仕様・設計・実装方針の境界が複雑
- 複数ファイルや複数 phase にまたがる再設計が必要
- 深いデバッグや根本原因の切り分けが必要
- コードレビュー、設計レビュー、Terraform を含む PR レビュー、正式レビュー
- セキュリティや運用影響が大きい判断
- `terminal` / `shell` / `git` / `terraform` / 多数 tool 呼び出しを跨ぐ multi-step 作業
- `working-set` が広い作業。複数モジュール、リポジトリ横断、多ファイル改修、長い会話継続を含むケース
- **スキルに明示的な手順が無いステップ (undocumented step)**

## 軽いモデルで十分なタスク

- `tasklist.md` の軽い整形、リンク確認、差分要約
- テスト実行自体はモデル不要。失敗の切り分けや原因分析は重いモデルに上げる。
- テストの追加・更新は、既存パターンに沿う単純なものなら軽いモデルで十分
- 文章のみの要約、README やコメントの表現確認
- read-only の差分説明、軽い指摘の整理
- `planner/executor split` の executor 側に相当する、対象が明確で狭い step
- やり直し時間の方が高くつくと感じたら、最初から重いモデルで始める。

## 共通

- `Think` は必要なときだけ上げる。常用で固定しない。
- `scripts/resolve-gdd-model.py` は prompt 文字列と `detected_phase`（`gdd-dev.local.md` に stop hook が記録する最後に検出された phase）から近似判定する。実際の `working-set` が 64K を超える、長い会話を引き継ぐ、広いコードベース探索になる、など resolver から見えない事情がある場合は、人間が手動で重いモデルへ override する。
- `detected_phase` は既定 tier を決めるために使う。ただし `gdd-design-gating`、`gdd-completion-check`、`gdd-implementation-gating`、`final review`、`code review`、`security review`、`review feedback` は重い signal として `phase` より優先する。`undocumented step`、`large working-set` も同様。
- `detected_phase` が入っていても、`leaf_task` が明確なら leaf を優先してよい。ただし `detected_phase` が formal gate（brainstorming / requirements-gating / requirements-amendment / design-gating / implementation-gating / completion-check）または一般 heavy 系（systematic-debugging / refactor-planning / requesting-code-review / pr-review）の場合は leaf を優先しない（`scripts/resolve-gdd-model.py` の `classify_tier()` に足した floor と同じ集合。独立レビューの指摘: 本節がこの限定を欠くと、Claude Code 経路では resolver 側の floor が拘束力を持たない）。`recommended_model` は参考値であって強制ではない。
- Cursor / Codex では、leaf task（status / metrics / worktree）用に `Grok 4.5 + low`（Cursor）/ `gpt-5.6-terra + low`（Codex）、cheap/read-only lane（短い要約 / link check / 一覧整形、state 更新なし、routing 判断なし）用に `Grok 4.5 + low`（Cursor）/ `gpt-5.6-luna + high`（Codex）、light task（task-breakdown / TDD 等）用に `Grok 4.5 + medium`（Cursor）/ `gpt-5.6-terra + medium`（Codex）、一般 heavy（debug / refactor / advisory review）用に `Grok 4.6 + low`（Cursor）/ `gpt-5.6-sol + low`（Codex）、risk escalation と最終 diff review（gdd-pr-review）用に同モデルの `high`、formal gate（brainstorming / requirements / design / impl / completion）用に同モデルの `medium`、Cursor の bounded な実装用に `Composer 2.5` を使う（GPT-5.4 系 / GPT-5.5 / `composer-2-fast` は使わない）。

## 判断の書き方

```text
model: opus (Claude Code, effort=high) - 壁打ちと要件整理を重い側で固定するため
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=medium) - formal gate（brainstorming / requirements / design / impl / completion）を重い側で固定するため
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=low) - 一般 heavy（debug / refactor / advisory review）の標準
```

```text
model: Grok 4.5 (Cursor, reasoning.effort=low) - leaf / admin task の標準
```

```text
model: gpt-5.6-luna (Codex, reasoning.effort=high) - cheap/read-only lane（state 更新なし、routing 判断なし）
```
