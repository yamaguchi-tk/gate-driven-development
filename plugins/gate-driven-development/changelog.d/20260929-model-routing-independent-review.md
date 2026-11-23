---
type: patch
---

#### Summary

`skills/gdd-model-routing` の tier の用途の表と host 別の写像表に、`independent_review` tier（push 前の独立レビュー）の行を足した。resolver（`scripts/resolve-gdd-model.py`）と `references/fixed-models.md` には既にあった。

#### Changed

- `skills/gdd-model-routing` の tier の用途の表と host 別 tier mapping の表に `independent_review` の行を足した（Claude Code: `opus` + `effort=max` / Cursor: `Grok 4.6` + `reasoning.effort=high` / Codex: `gpt-5.6-sol` + `reasoning.effort=high`）
- host 別 tier mapping の表の Claude Code 列を、resolver の tier ごとの model・effort と突き合わせるテストを足した

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`
- `plugins/gate-driven-development/tests/test_model_routing_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_model_routing_contract.py -q`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
