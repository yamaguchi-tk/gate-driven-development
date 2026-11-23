---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。plugin 直下の `pytest.ini` の `addopts` に `--durations=30` を足した。テストを回すたびに、遅いテストの上位 30 件の実行時間が出る。CI の全量のログにも残るので、テストの実行時間を削るときの前後比較に使う。`CONTRIBUTING.md` の `pytest.ini` の説明も合わせた。

#### Affected Files

- `plugins/gate-driven-development/pytest.ini`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/tests/test_pytest_ini_durations_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_pytest_ini_durations_contract.py`（pytest を起動して、遅いテストの一覧が出ることを確かめる）を先に書き、失敗することを確かめてから `pytest.ini` を変えた
- repo root から plugin のテストを指定して起動しても、`pytest.ini` が読まれて一覧が出ることを確かめた
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
