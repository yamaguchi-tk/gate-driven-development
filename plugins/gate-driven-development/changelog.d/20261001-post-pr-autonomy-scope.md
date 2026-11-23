---
type: minor
---

#### Summary

human check の自走上限に「マージまで」「マージ・デプロイ・QA まで」を足した。選べるのは、既定ブランチの `.gdd-config.md` に `GDD Post-PR Autonomy:` の宣言がある repo だけである。「マージ・デプロイ・QA まで」では、PR の後に QA 計画を書いてレビューに通し、マージ、宣言した環境へのデプロイの完了確認、Opus high の `gdd-qa-runner` による QA まで進む。QA が失敗したら revert の PR を作って止まる。

#### Added

- `references/post-merge-qa.md`: repo の宣言（`GDD Post-PR Autonomy`・`GDD QA Environment`・`GDD QA Deploy Paths`・`GDD QA Deploy Workflows`・`GDD QA Write Targets`）、QA 計画、マージ後の QA の手順
- `agents/gdd-qa-runner.md`: QA 計画どおりに QA を 1 回実行する agent（`model: opus`・`effort: high`。repo のファイルは書き換えない）

#### Changed

- `references/human-check-template.md` § 自走上限の置換値に 2 行を足した。宣言が無い repo では選択肢に出さない
- `references/post-completion-pr-flow.md` Option 1 手順 7 と `skills/gdd-completion-check/SKILL.md` で、自走上限が上の 2 値なら completion-check は PR 作成の後に `done` で戻る。`references/subagent-dispatch.md` § Completion-Check Post-Return Routing で、main が完了サマリーの代わりに `references/post-merge-qa.md` を続ける
- マージは `gdd-pr-review-followup` のマージの経路（merge gate の証跡と `Merge Approval`）で行う。`Merge Approval` を問う 1 問に、マージで起動する workflow と環境、QA の書き込みの全件を並べる
- `skills/gdd-brainstorming/SKILL.md` の自走上限の値の列挙をやめ、`references/human-check-template.md` § 自走上限の置換値を指すようにした
- human check の返答例から「自走上限はデプロイ準備まで」を削り、`references/requirements-gating-steps.md` から自走上限の値ごとの停止点の行を削った（どちらも § 自走上限の置換値の表と同じ内容）
- `references/operation-levels.md` に `.gdd-config.md` のキーの入口を足した
- references の行数の上限を 12,032 から 12,076 に上げた（ユーザー承認。同じ意味の既存の文を 2 行削った残り）

#### Affected Files

- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/agents/gdd-qa-runner.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/operation-levels.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`
- `plugins/gate-driven-development/tests/test_agent_dispatch_model_gate_contract.py`

#### User Action Required

- 使うときは、repo の既定ブランチの `.gdd-config.md` に宣言を書く（書式は `references/post-merge-qa.md` § 宣言）。書かなければ今までどおり
- merge gate は今も人間の承認ターンで書いた `Merge Approval` を求めるので、マージの前に 1 回止まる

#### Validation / Eval Impact

- `agent-effort-schema`・agent の許可ツールの契約・dispatch gate の model 固定の表に `gdd-qa-runner` を足した。QA を起動する時点（`Next Action=done`）では dispatch gate は判定しないので、QA を Opus で行うことを保証するのは agent 定義の frontmatter だけである
