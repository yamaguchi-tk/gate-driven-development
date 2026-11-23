---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。同じ版で足した `--durations=30`（遅いテストの上位 30 行を毎回出す）を絞り、plugin 直下の `pytest.ini` の `addopts` に `--durations-min=1.0` を足した。遅いテストの一覧には 1 秒以上かかったものだけを出す。1 秒未満も見るときは `--durations-min=0` を付ける。手元で速いテストだけを回したときは行を出さないので、出力が膨らまない。`CONTRIBUTING.md` の説明に、一覧の 1 行の単位（1 テストの setup・call・teardown のどれか）と位置（最後の集計行の手前）を書いた。

#### Affected Files

- `plugins/gate-driven-development/pytest.ini`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/tests/test_pytest_ini_durations_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_pytest_ini_durations_contract.py` に、速いテストだけを回したときは一覧に行が出ないことを確かめるテストを先に足し、失敗することを確かめてから `pytest.ini` を変えた
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
