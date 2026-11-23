---
type: patch
---

#### Summary

- 社内の repo 名・サービス名・社内ツールの名前を使わずに読めるように、コメント・references・skills・docs・変更断片の文を書き直した（「GDD を使う別の repo」などの一般的な表現にした。日付・件数などの実測値は残した）
- テストの入力値の repo 名・パスを、架空の名前（`example-org/infra-repo`、`src/review-bot/**` など）にした。テストが見分ける性質（別の owner であること、glob の形）は変えていない
- done guard の block メッセージ（`method=security_evidence:*` 行の回復案内）で、Snyk のスキャン結果を書く verifier plugin の名前と設定ファイル名を挙げていたのを、「verifier plugin」「`.claude/<plugin 名>.local.md`」と書くようにした。`scripts/external-verifier-smoke.sh` と `tests/checks/external-verifier-smoke.sh` は、隣のディレクトリの plugin 名を決め打ちで探さず、`SNYK_PLUGIN_ROOT`（または `--snyk-plugin-root`）で場所を受け取る
- 3 つの manifest の author の email を、GitHub の noreply アドレスにした
- 社内 wiki のサービス名を、出力先の例（「Slack / GitHub / wiki」など）や社内ドキュメントの例（`docs/PROJECT_CLAUDE_MD_TEMPLATE.md`・`docs/SECURITY.md`）で、「wiki」「社内 wiki・チケット管理」と書くようにした。社内の記事番号は消した

#### Affected Files

- `.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`.cursor-plugin/plugin.json`（author.email）
- `references/independent-review.md`、`references/self-review-lanes.md`、`references/subagent-dispatch.md`、`references/dialectic-review.md`、`references/e2e-verification-catalog.md`、`commands/gdd-dev.md`
- `skills/gdd-pr-review/SKILL.md`、`skills/gdd-brainstorming/SKILL.md`、`skills/gdd-design-gating/SKILL.md`、`skills/gdd-requirements-gating/SKILL.md`、`skills/gdd-test-driven-development/SKILL.md`、`skills/root-cause-investigation/references/investigation-hygiene.md`
- `hooks/scripts/lib/ir_merge_carry.py`、`hooks/scripts/lib/merge-gate-binding.sh`（コメントだけ）、`scripts/lint-requirements-duplication.py`（`--help` に出る docstring の 1 文）
- `hooks/scripts/lib/done_block_message.py`（block メッセージ）、`scripts/external-verifier-smoke.sh`、`tests/checks/external-verifier-smoke.sh`
- `references/faq.md`、`references/self-contained-contract.md`、`CHANGELOG-archive-2.md`
- `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`、`docs/SECURITY.md`、`docs/design/2026-08-30-pr-w0-defect-telemetry-adr.md`、`docs/references-archive/` の 4 本、`docs/audits/` の 2 本、`CHANGELOG.md`
- `changelog.d/` の既存断片 8 本
- テスト 16 本と fixture 2 本

#### User Action Required

なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
