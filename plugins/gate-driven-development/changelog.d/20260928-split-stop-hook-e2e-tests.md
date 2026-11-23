---
type: patch
---

#### Summary

利用者から見える変更なし。Stop hook の E2E テスト `tests/test_stop_hook_e2e.py`（1,835 行）は、1 ファイル 1,500 行の目安を超えていた。そこで、hook が出す continuation block と「次にすること」「次の計画」のブロックの中身を確かめる 5 class を、`tests/test_stop_hook_e2e_block_content.py` へ分けた。class と関数の本体は変えていない。移したテストを名指ししていた参照先（`tests/test_stop_hook_progress_bind_scope_contract.py`・`docs/design/2026-08-30-pr-w0-defect-telemetry-adr.md`）は新しいファイルに向け、Stop hook のテストを列挙している箇所（`CONTRIBUTING.md`・`references/stop-hook-structured-markers.md`・`tests/_stop_hook_test_base.py`）には新しいファイルを足した。

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_e2e.py`
- `plugins/gate-driven-development/tests/test_stop_hook_e2e_block_content.py`
- `plugins/gate-driven-development/tests/_stop_hook_test_base.py`（docstring の実行例だけ）
- `plugins/gate-driven-development/tests/test_stop_hook_progress_bind_scope_contract.py`（docstring の参照先だけ）
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/references/stop-hook-structured-markers.md`
- `plugins/gate-driven-development/docs/design/2026-08-30-pr-w0-defect-telemetry-adr.md`（参照先だけ）

#### User Action Required

- なし

#### Validation / Eval Impact

- 分けた 2 ファイルで収集したテストの件数と、class 名・テスト関数名の一覧が、merge-base の元のファイルと一致することを確かめた
- 移した class の本体が merge-base と一致することを、AST のソース比較で確かめた
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` で起動しても、共有 fixture を解決できることを確かめた
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
