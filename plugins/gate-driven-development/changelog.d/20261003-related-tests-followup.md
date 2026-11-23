---
type: patch
---

#### Summary

利用者から見える変更なし。この repo の開発手順で使う `scripts/light-lane-related-tests.py` が、GDD の helper（`tests/_*.py`）経由で部品を名指しするテストも選び、`--run` の `--` で足したテストを、選んだテストが 0 件のときも回すようにした。スクリプト自身の終了コードは、pytest の終了コードと重ならない値にした。

#### Affected Files

- `plugins/gate-driven-development/CONTRIBUTING.md`（項 1 の「関係するテスト」に helper の規則を足した）
- `plugins/gate-driven-development/tests/test_light_lane_related_tests.py`
- plugin の外: `scripts/light-lane-related-tests.py`、root `CLAUDE.md`（手順 3・手順 6）、`.github/copilot-instructions.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_light_lane_related_tests.py` に、helper 経由のテスト・`--` で足すテスト・終了コード・`__pycache__`・subdirectory のテストを足した
- `bash tests/validate-plugin.sh`
