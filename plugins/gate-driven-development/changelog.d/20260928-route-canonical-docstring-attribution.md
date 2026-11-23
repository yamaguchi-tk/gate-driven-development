---
type: patch
---

#### Summary

利用者から見える変更なし。`tests/test_stop_hook_route_in_progress_canonical_form_contract.py` のテスト 2 本の docstring を直した。

- `test_decorated_non_none_route_still_blocks`: 「実データ 228 件で空を返す行は 0 件」という実測は、H5-1 の是正前の `_route_value`（enum として読めない値に空を返していた）で測った値である。今の `tasklist_parse.route_value` と併記し、実測の帰属を戻した
- `test_unclosed_fence_does_not_silence_the_check`: この test の入力は値が non-none なので、fence の閉じ忘れを一律で block するかどうかは判別しない。一律 block を測る `test_done_guard_state_line_break_chars_contract.py` の `test_unclosed_fence_blocks_even_when_route_is_none` への参照を足した

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_route_in_progress_canonical_form_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 変更したファイルのテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
