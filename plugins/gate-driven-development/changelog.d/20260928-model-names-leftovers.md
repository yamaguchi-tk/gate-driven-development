---
type: patch
---

#### Summary

- `gdd-model-routing` の Dialectic Review の説明で、Cursor の Primary を Grok 系と書くようにした。`subagent-dispatch.md` のフェーズ別の表で、モデル列の Claude Code 向けの名前を alias にした

#### Changed

- `skills/gdd-model-routing/SKILL.md` の Cursor の Counter の説明で、Primary を「GPT 系」から「Grok 系」に直した（Cursor の Primary は Grok 4.6 / Grok 4.5）
- `references/subagent-dispatch.md` のフェーズ別の表で、`light_task`・`implementation` の Claude Code 向けの名前を `sonnet`・`opus` にした

#### Affected Files

- `skills/gdd-model-routing/SKILL.md`・`references/subagent-dispatch.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 関係するテスト: 変更したファイル名を参照するテスト
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
