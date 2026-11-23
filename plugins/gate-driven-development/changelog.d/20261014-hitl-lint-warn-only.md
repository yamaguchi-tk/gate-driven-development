---
type: patch
---

#### Summary

`human-check-waiting` の停止で HITL の品質 lint（`lint-hitl-display-integrity`・`lint-human-check-language`・`lint-hitl-complexity`）を通らなかったとき、Stop hook は差し戻さずに停止を通し、通らなかった lint の名前と最初の行・詳細行（3 行まで）を `systemMessage` でユーザーに知らせ、全文を `.gdd/hitl-lint.log` に記録するようにした（故障の記録の `.gdd/hook-errors.log` とは分けた）。これまでは同じ `/gdd-dev` の中で 2 回まで差し戻していたが、display-integrity が求める約 20 の見出しと complexity の行数の上限を同時に満たせず、差し戻すたびにもう片方で落ちて、同じ HITL がユーザーに 2〜3 回並んでいた。差し戻しの予算（`.claude/gdd-dev.local.md` の `hitl_lint_blocks`）は使わなくなったので外した。lint の判定は変えていない。

HITL のテンプレート（`references/human-check-template-compact.md` と `references/human-check-template.md` § 必須ルール）と `references/rollback-patterns.md` の Downstream Human Recheck Handoff に、停止マーカーの後の `## 👤 次にすること` を足した。これまではテンプレートどおりに書くと、この見出しが無いとして Stop hook に差し戻されていた。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/hitl_lint_gate.py`・`hooks/scripts/lib/errors.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`（`try_stop_with_done_guard`・`_stop_for_non_done_reason`）
- `plugins/gate-driven-development/references/human-check-template-compact.md`・`references/human-check-template.md`・`references/rollback-patterns.md`（Downstream Human Recheck Handoff）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_stop_hook_hitl_lint_gate_e2e.py`・`tests/test_hitl_lint_gate_unit.py`・`tests/test_hitl_lint_gate_warn_wiring.py`・`tests/test_hook_python_safe_path.py`
