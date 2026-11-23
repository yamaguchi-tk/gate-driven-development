---
type: patch
---

#### Summary

GDD の回帰テストを回すときの xdist の worker 数を 8 で頭打ちにした。これまでは `-n auto` が論理 CPU 数ぶん（16 コアの Mac なら 16）の worker を起動し、複数のセッションが同時に回すとマシンが詰まっていた。上限は `pytest.ini` に置くので、`-n auto` をコマンドラインで渡す CI・手順の実行にも効く。一時的に変えるなら `--maxprocesses=N` を渡す。

#### Affected Files

- `plugins/gate-driven-development/pytest.ini`
- `plugins/gate-driven-development/tests/test_pytest_worker_cap.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_pytest_worker_cap.py` を足した（32 コアを模した環境で、ini の既定と `-n auto` の両方の worker 数が 8 以下になることを、実際の pytest の起動で確かめる）
- `bash tests/validate-plugin.sh`
