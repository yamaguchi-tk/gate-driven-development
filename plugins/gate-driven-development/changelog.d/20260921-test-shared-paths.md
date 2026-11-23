---
type: patch
---

#### Summary

利用者から見える変更なし。テストが個別に `Path(__file__)` から組み立てていた plugin・repo のルートパス（`PLUGIN_ROOT` / `ROOT` / `REPO_ROOT`。約 140 箇所・綴り 7 通り）を、共通モジュール `tests/_paths.py` の import に置き換えた。`tests/__init__.py` が `tests/` を sys.path に入れるので、`python3 -m unittest tests.<module>` でもテストを起動できる。assert・入力・既存テストの本数は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/_paths.py`（新規）
- `plugins/gate-driven-development/tests/__init__.py`（新規）
- `plugins/gate-driven-development/tests/test_tests_package_import_contract.py`（新規）
- `plugins/gate-driven-development/tests/_block_reason_support.py`
- `plugins/gate-driven-development/tests/_merge_gate_support.py`
- `plugins/gate-driven-development/tests/_plugin_module_loader.py`
- `plugins/gate-driven-development/tests/_root_branch_guard_support.py`
- `plugins/gate-driven-development/tests/_timing_budget.py`
- `plugins/gate-driven-development/tests/_validate_plugin_reader.py`
- `plugins/gate-driven-development/tests/test_*.py`（132 本。ルートパスの定義行を import に置き換え、使わなくなった `pathlib` の import を消した）

#### User Action Required

- なし

#### Validation / Eval Impact

- 新規 contract test: `tests/test_tests_package_import_contract.py`（`tests/test_*.py` の全モジュールを、1 モジュール 1 subprocess で `tests.<module>` として import できる）
- 置き換えの前後で `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q` の収集一覧が一致すること（新規テストの 1 件を除く）を確認した
- 変更したテストと、変更した helper を import するテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
