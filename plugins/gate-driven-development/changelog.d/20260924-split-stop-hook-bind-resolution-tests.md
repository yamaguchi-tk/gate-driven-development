---
type: patch
---

#### Summary

利用者から見える変更なし。Stop hook の bind 解決の契約テスト `tests/test_stop_hook_bind_resolution_contract.py` が 1 ファイル 1,500 行の目安と関数の数の warn を超えていたので、fence の扱いを `tests/test_stop_hook_tasklist_fence_contract.py` へ、進捗件数・進捗表示・Resume From の bind スコープを `tests/test_stop_hook_progress_bind_scope_contract.py` へ分けた。class と関数の本体は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_bind_resolution_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_tasklist_fence_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_progress_bind_scope_contract.py`
- `plugins/gate-driven-development/tests/_stop_hook_test_base.py`（コメントの参照先だけ）
- `plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py`（docstring の参照先だけ）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q` の件数と、class 名・テスト関数名の一覧が、merge-base と一致することを確認した
- 移した class・関数・定数の本体が merge-base と一致することを、AST のソース比較で確認した
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` の起動でも共有 fixture を解決できることを確認した
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
