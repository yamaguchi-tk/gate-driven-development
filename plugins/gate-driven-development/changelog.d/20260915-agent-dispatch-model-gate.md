---
type: minor
---

#### Summary

`references/fixed-models.md` / `references/subagent-dispatch.md` の工程別 model 表は散文でしか強制されておらず、`Agent` 起動 9,852 本の実測（X-61）で `model` 未指定が 42%（requirements 55% / design 23% / review 55%）あった。未指定は host 既定（main セッションの model）に落ちるため、main を軽量モデルにしていると formal gate も軽量モデルで走っていた。本 PR は `X-61 / X-55 / X-54 B`（前提 `X-56`）に基づき、この強制を `PreToolUse`（`matcher: "Agent"`）hook として機械化する（4 判定のうち判定 1 のみ。判定 2〜4 は別 PR）。判定材料は `tool_input.subagent_type` / `tool_input.model` / `.claude/gdd-dev.local.md` の `active` / `state.md` の `Resume From` / `tasklist.md`・`state.md` の `Next Action` という閉じた入力のみで、`description` の自由文は使わない（PR 旧#83 の失敗: 自由文の機械判定は 7 巡しても収束しなかった）。

#### Added

- `hooks/scripts/run-agent-dispatch-model-gate-hook.sh`（新規）: `Agent` 起動時に、工程に対して `model` が未指定、または工程が許容する model 集合に含まれない場合（軽量モデルへの自動ダウングレードを含む）に `additionalContext` で warn する（block はしない）。`Next Action` は 3 gate 承認済み（canonical）の tasklist.md でのみ routing source として使い、draft の仮置き値は使わない。`tool_input` の抽出は stdin 経由で 1 回だけ JSON parse する（既存の pre-push / merge gate hook と同じ方式。大きな prompt を含む起動で argv 経由だと `ARG_MAX` を超えて抽出が失敗しうるため。PR 旧#91 人間レビュー指摘、Medium）
- `hooks/scripts/lib/agent_dispatch_gate.py`（新規）: 判定ロジック本体。phase → tier のマッピングは `scripts/resolve-gdd-model.py` の `PHASE_TO_TIER` / `TIER_TO_MODEL["claude_code"]` を動的ロードで再利用し、新しく重複したマッピングは作らない。`Explore` / `Plan` 等の読み取り専用の汎用調査 agent は `model` の値によらず常に判定対象外。`agents/*.md` の frontmatter で `model` が既に固定されている reviewer subagent（bare 名・plugin prefix 付きのどちらでも）は、起動時に `model` が未指定のときだけ対象外にする——Claude Code の model 解決順は起動時 `model` → frontmatter → 環境変数 → main であり、起動時に `model` を明示指定すると frontmatter の固定 model より優先されるため、明示的なダウングレードは判定する（PR 旧#91 人間レビュー指摘、High）。`model` の許容判定は alias（`opus`/`sonnet`）だけでなく `claude-opus-5` のような full ID も family に正規化してから比較する（同 Medium）
- `hooks/hooks.json`: `PreToolUse` に `matcher: "Agent"` のエントリを追加（`Skill` matcher の後、`Bash` matcher の前）。`timeout` は他の複数 subprocess を伴う同種 hook に揃えて `10`（独立レビュー指摘。本 hook は 1 回の起動で python3 を最大 4 回逐次 spawn するため、実測で `5` 秒に対し最大 5.33 秒かかり超過することがあった）
- `tests/test_agent_dispatch_model_gate_contract.py`（新規）: 単体テスト（`resolve_phase` / `judge` / `is_exempt_from_phase_model_check`）と、bash hook 本体を実行する統合テスト。不正 JSON / `tool_input` が非 dict / `model` が非文字列、の 3 パターンで hook が非 0 終了しない（guard 自体が落ちない）ことを確認する fail-open 系テストを含む

#### Changed

- `references/fixed-models.md`: 工程別 model 表の直後に、この禁止が Claude Code では起動時に機械強制されること・判定材料・既知の限界を追記した
- `references/subagent-dispatch.md`: `## Subagent Model Routing` 節に、この表の遵守が起動時に warn されることを追記した
- `tests/test_hooks_kill_switch.py`: `ALL_HOOKS` に新規 hook script を追加した

#### Known limitations

- `Resume From` / `Next Action` から工程を特定できない起動では判定しない。具体的には、brainstorming / requirements / design の初回 dispatch は steering 作成前（`Resume From` がまだ書かれていない）か `human-check-waiting` 経由の遷移であることが多く、この経路では判定できない（独立レビュー指摘）。3 gate 未承認の間の build-phase 相当 dispatch も、canonical でない tasklist.md の `Next Action` を使わない設計上、同様に判定できない
- warn-only であり block はしない。`additionalContext` を無視して起動を続けることは可能
- Cursor / Codex にこの機械強制は無い（`hooks.json` は Claude Code 専用機構のため）
- payload の JSON parse に失敗した場合、`model` が実際には未指定でなくても「未指定」と同じ扱いになる（`tool_input` を読めないため）。warn-only であるため実害は低いと判断し、本 PR では区別しない

#### Affected Files

- `hooks/hooks.json`
- `hooks/scripts/lib/agent_dispatch_gate.py`（新規）
- `hooks/scripts/run-agent-dispatch-model-gate-hook.sh`（新規）
- `references/fixed-models.md`
- `references/subagent-dispatch.md`
- `tests/test_agent_dispatch_model_gate_contract.py`（新規）
- `tests/test_hooks_kill_switch.py`

#### User Action Required

- **GDD を使う他リポジトリの進行中セッションに影響しうる**: このリポジトリの `gate-driven-development` プラグインを使う他リポジトリで GDD active な session が `Agent` を `model` 未指定または不適切な `model` で起動していた場合、本 PR のマージ後（プラグインの更新取り込み後）はその起動のたびに `additionalContext` で warn が挿入されるようになる。block ではないため既存の継続実行は止まらないが、進行中セッションの出力に新しい警告文が増える。影響を避けたい場合は `~/.claude/gdd-hooks-disabled` を置く kill switch で無効化できる（既存の全 GDD hook 共通の機構）
- ベースライン「Agent 起動の 42% が model 未指定」の再計測手順: GDD active な session の transcript から `Agent` 起動の `tool_input` を集計し、`model` キーが欠落または空文字の割合を出す（X-61 の元計測と同じ集計単位）。本 PR 適用後、同じ集計を一定期間後（例: 2 週間）に取り直し、未指定率の低下を確認する

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`（既存回帰なし。本文には最終実行時の件数を記載）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（全 BLOCK チェック OK）
- 独立レビュー（read-only / diff-only / 経緯非共有、1 巡目）: High 3 件・Medium 4 件・Low 数件を検出。High 2 件（`Next Action` を tasklist.md からしか読んでいない／`BUILD_PHASES` に工程が 4 つ抜けていた）と Medium 4 件（3 gate 未承認 tasklist の `Next Action` を routing source にしていた／`Next Action` の装飾除去が無い／`subagent_type` の bare 名が受理集合と非対称／formal gate 中の読み取り専用調査 agent への誤 warn）はすべて修正した。High 1 件（brainstorming/requirements/design の初回 dispatch は steering 作成前のため判定できない）は構造的な限界として `references/fixed-models.md` に明記し、対応は別スコープとした
- 独立レビュー（read-only / diff-only / 経緯非共有、2 巡目、`git worktree add --detach` での実行込み）: High 0 件・Medium 1 件（`hooks.json` の `timeout: 5` が実測でマージン不足）・Low 2 件（`gdd-task-breakdown` を `PLANNING_PHASES` に含めていない非対称だが開示済みの既知の限界／fail-open 系の例外テストが未整備）を検出。Medium は `timeout: 10` に修正し、Low の例外テスト欠如は fail-open 系の統合テスト 3 本を追加して対応した。残る Low（`PLANNING_PHASES` の非対称）は既知の限界として `references/fixed-models.md` に記載済みのため対応不要と判断した
- PR 旧#91 人間レビュー（`yamaguchi-tk`、commit `5170e96` 対象）: High 1 件・Medium 2 件（すべてインラインコメント）を受領しすべて修正した。High: 固定 reviewer subagent を `subagent_type` だけで免除しており、起動時に `model` を明示ダウングレードされても判定しなかった（Claude Code の model 解決順は起動時 `model` が frontmatter より優先されるため）。Medium: (a) `opus`/`sonnet` の alias としか比較しておらず `claude-opus-5` 等の full ID を誤警告していた、(b) `tool_input` の抽出が payload 全体を argv 経由で渡しており大きな prompt で `ARG_MAX` を超えうるため stdin parse に切り替えた。修正実装中、model 抽出用の python スクリプトの f-string にバックスラッシュ付きエスケープを使ったことによる `SyntaxError`（`2>/dev/null` で無言に握りつぶされ、抽出が常に失敗する退行）を自己レビューの回帰テストで検出し、単一引用符のリテラルに直して修正した（push 前に検出、実運用には出ていない）
