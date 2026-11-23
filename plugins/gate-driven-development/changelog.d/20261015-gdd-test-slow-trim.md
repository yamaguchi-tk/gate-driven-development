---
type: patch
---

#### Summary

- 利用者から見える変更なし。テストの全量にかかる時間を縮めた。別のファイルから名前で import したテストのクラスが 2 回集められていたのを 1 回にし、ほかのテストと同じ入力・同じ期待を見ていたテスト 2 本を消した。hook を何度も起動していた表のテストは、判定の関数を直接呼ぶ形、hook に同じ入力が渡る行は 1 回だけ起動する形、fixture を組み直さない形に替えた

#### Affected Files

- `plugins/gate-driven-development/tests/_merge_gate_input_classes.py`
- `plugins/gate-driven-development/tests/test_merge_gate_input_classes.py`
- `plugins/gate-driven-development/tests/test_merge_gate_explicit_target.py`
- `plugins/gate-driven-development/tests/test_merge_gate_target_grammar.py`
- `plugins/gate-driven-development/tests/test_merge_gate_cd_after_merge.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_quoted_operator.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_gate_regressions.py`
- `plugins/gate-driven-development/tests/test_merge_gate_ir_carry.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py`
- `plugins/gate-driven-development/tests/test_hooks_toplevel_trailing_newline.py`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`
- `plugins/gate-driven-development/tests/test_confirmed_text.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 書き換えたテストのファイルを、変更の前と後で `python3 -m pytest <ファイル> -q -n 0` で回して CPU 時間を比べた。`bash plugins/gate-driven-development/tests/validate-plugin.sh` を回した
