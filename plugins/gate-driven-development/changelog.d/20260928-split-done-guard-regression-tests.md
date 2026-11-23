---
type: patch
---

#### Summary

利用者から見える変更なし。`tests/test_stop_hook_done_guard_regression_contract.py`（1,600 行）は、1 ファイル 1,500 行の目安を超えていた。そこで、done guard の Check 3（`Route In Progress`）が `state.md` の正準形を読み、散文を拾わないことを測る `RouteInProgressCanonicalFormTests` を、`tests/test_stop_hook_route_in_progress_canonical_form_contract.py` へ分けた。class の本体は変えていない。元のファイルの docstring に、分けた先への参照を 1 文足した。

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_route_in_progress_canonical_form_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 分けた 2 ファイルで収集したテストの件数と、class 名・テスト関数名の一覧が、merge-base の元のファイルと一致することを確かめた
- 移した class と、元のファイルに残した定義の本体が merge-base と一致することを、AST のソース比較で確かめた
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` で起動しても、共有ヘルパの import を解決できることを確かめた
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
