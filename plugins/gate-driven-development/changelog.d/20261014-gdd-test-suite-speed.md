---
type: patch
---

#### Summary

- 利用者から見える変更なし。テストの全量の実行時間を縮めるため、テストの組み立てを変えた。lane が L1・L1+ の review-log を 1 本ずつ検査するテストは、1 件のテストの中で全部を検査していたのを、log ごとのテストに分けて xdist の worker に割るようにした。worker 数の上限のテストは、子の pytest で worker を起動せずに、xdist が起動する予定の数を読むようにした。テストの未使用の import を消した

#### Affected Files

- `plugins/gate-driven-development/tests/test_review_log_present.py`
- `plugins/gate-driven-development/tests/test_pytest_worker_cap.py`
- `plugins/gate-driven-development/tests/_merge_gate_support.py`
- `plugins/gate-driven-development/tests/test_compact_suggestion_contract.py`
- `plugins/gate-driven-development/tests/test_gh_line_continuation_tokens.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_contracts.py`
- `plugins/gate-driven-development/tests/test_state_field_value_less_line_contract.py`
- `plugins/gate-driven-development/tests/test_task_binding_resolver.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 変更: `test_review_log_present.py` の `ExistingReviewLogsStayValidTests.test_every_review_log_on_this_checkout_passes` を、`test_existing_review_log_passes`（log ごと）と `test_existing_review_logs_are_collected` に分けた
- 変更: `test_pytest_worker_cap.py` は xdist が決めた worker の一覧の数を比べる。追加: `test_explicit_worker_count_below_the_cap_is_kept`
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
