---
type: patch
---

#### Summary

- 契約 md（skills・references・commands・README）の Claude のモデル名を、版数なしの alias（`opus` / `sonnet`）で書くようにした。Claude Code は alias を CLI が知る最新のモデルに解決するので、新しい Opus が出ても契約 md を直さずに済む。版数付きの名前は、Cursor がモデルを名前で選ぶ Dialectic Counter の 2 行だけに残し、`Opus 5.5` に上げた

#### Changed

- `references/fixed-models.md` の tier 表・skill 表の Claude Code 列を `Opus 5` から `opus` に変えた。§ モデル名の書き方を足し、版数を書く場所を `dialectic_counter` の Cursor 列と `references/cursor.md` の tier 表の同じ行の 2 か所に限った
- Cursor の Dialectic Counter を `Opus 5` から `Opus 5.5` に上げた
- `skills/`・`references/`・`commands/`・README の散文の `Opus 5` を、Claude Code の文脈では `opus`、Cursor の文脈では版数なしの Opus と上の 2 行への参照に変えた
- Cursor の Counter を版数なしの `Opus` で指示する表・箇条書き（`references/cursor.md`・`references/cursor-guide.md`・`skills/gdd-model-routing/SKILL.md`）は、すべて版を書いた `dialectic_counter` 行を指すようにした。表だけを読んで Counter を選んでも `Opus 5.5` に届く

#### Affected Files

- `references/fixed-models.md`・`references/cursor.md`・`references/cursor-guide.md`・`references/codex.md`・`references/subagent-dispatch.md`・`references/dialectic-review.md`
- `skills/gdd-model-routing/SKILL.md` ほか `## Fixed Model` 節を持つ skill 10 本
- `commands/gdd-dev.md`・`README.md`・`evals/evals.json`（eval の期待回答）
- `tests/checks/hooks.sh`・`tests/test_model_names_without_version_contract.py`（新規）ほか契約テスト 4 本

#### User Action Required

- Claude Code で subagent を新しい Opus にするには、Claude Code CLI を更新する（`claude update`）。alias の解決先は CLI の版で決まる（2026-09-23 実測: 2.1.261 は `claude-opus-5`、2.1.280 は `claude-opus-5-5`）。更新後に開いたセッションから反映される。環境変数や設定で解決先を固定している環境では、CLI を更新しても変わらない
- Cursor で Dialectic Counter を使う場合は、`Opus 5.5` を選ぶ

#### Validation / Eval Impact

- 関係するテスト: `test_model_names_without_version_contract.py`・`test_remediation_loop_model_routing_contract.py`・`test_x64_fable_remnant_cleanup_contract.py`・`test_independent_review_host_route_contract.py`・`test_agent_dispatch_model_gate_contract.py` ほか、変更したファイル名を参照するテスト
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
