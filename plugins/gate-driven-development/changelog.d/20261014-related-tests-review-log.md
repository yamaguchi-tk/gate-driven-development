---
type: patch
---

#### Summary

- 利用者から見える変更なし。GDD の配布物は変えていない。repo root の `scripts/light-lane-related-tests.py`（この repo の軽いレーンで、関係するテストを選ぶ script）が、`review-log/` か `changelog.d/` の変更で `tests/test_review_log_present.py` を選ぶようにし、その契約テストを足した

#### Changed

- `tests/test_light_lane_related_tests.py`: `review-log/`・`changelog.d/` の変更で `test_review_log_present.py` が選ばれることを確かめるテストを 2 本足した

#### Affected Files

- `tests/test_light_lane_related_tests.py`
- `scripts/light-lane-related-tests.py`（repo root）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 追加 test: `test_review_log_or_changelog_fragment_brings_in_the_record_check`・`test_review_log_change_alone_lists_the_record_check`
