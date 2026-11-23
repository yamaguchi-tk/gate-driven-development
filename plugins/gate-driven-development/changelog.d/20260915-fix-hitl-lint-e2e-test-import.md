---
type: patch
---

#### Summary

- `tests/test_stop_hook_hitl_lint_gate_e2e.py` が `from tests._stop_hook_test_base import (...)` というパッケージ修飾 import を使っており、`tests/` に `__init__.py`・`conftest.py` が無いため `ModuleNotFoundError: No module named 'tests'` でコレクションエラーになっていた問題を修正した。他のテストファイル（例: `test_stop_hook_unit.py`）と同じ慣行（`sys.path.insert` してからパッケージ修飾なしで import）に合わせた。

#### Changed

- `tests/test_stop_hook_hitl_lint_gate_e2e.py` の import を、ファイル冒頭で `sys.path.insert(0, str(Path(__file__).parent))` を実行してから `from _stop_hook_test_base import (...)` する形に変更した

#### Fixed

- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_hitl_lint_gate_e2e.py -q` 単体実行、および `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` フルスイート実行の両方で発生していた `ModuleNotFoundError` を解消した

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_hitl_lint_gate_e2e.py`

#### User Action Required

- なし。テストファイルの import 修正のみで、hook の実装本体・contract には影響しない

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_hitl_lint_gate_e2e.py -q` で単体実行のエラー解消を確認した（5 passed）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` でフルスイートを実行し、全件成功を確認した（2923 passed, 4 skipped, 16694 subtests passed）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` を PR tip（`b89c5b2`）で計 4 回実行し、いずれも exit code 0 を確認した。PR レビュー（gdd-pr-review 0.4.0）で、別環境での実行時に `active-steering-candidate-resolution` チェックが埋め込み Python の `json.loads()` で `JSONDecodeError` を起こし exit code 1 になる事例を指摘された。原因未確定。環境によって exit 0 と `JSONDecodeError` に分かれる。本 PR の変更（テストファイルの import 文修正のみ）とは無関係。レビュアー自身も「main でも同型で落ちる、この PR が壊したわけではない」と判定している（不採用 Finding）。本 PR はこの現象の調査・修正を対象外とする
