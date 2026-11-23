---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。`references/testing-anti-patterns.md` の冒頭の参照元に、§ テスト判定基準を参照している `skills/gdd-writing-skills/SKILL.md`（Process Documentation TDD）を足した。`tests/test_stop_hook_progress_bind_scope_contract.py` の assert のメッセージが、生成した `## ` 行を次の test の入力と呼んでいたので直した。

#### Affected Files

- `plugins/gate-driven-development/references/testing-anti-patterns.md`
- `plugins/gate-driven-development/tests/test_stop_hook_progress_bind_scope_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_progress_bind_scope_contract.py -q`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
