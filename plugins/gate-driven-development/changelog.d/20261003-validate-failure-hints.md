---
type: patch
---

#### Summary

`validate-plugin.sh` の 2 つの失敗が、直し方を出すようになった。review-log の欄の値が不正なときは使える値を並べ、変更断片が無いときは、新しく書いて commit していない断片（untracked か、index に足しただけのもの）を名指しする。判定（何を FAIL にするか）は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/checks/review-log-present.sh`
- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/tests/test_review_log_present.py`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_review_log_present.py` の `test_invalid_value_message_lists_the_allowed_values` と、`tests/test_changelog_fragments.py` の `test_uncommitted_fragment_is_named_in_the_failure`・`test_files_that_are_not_new_fragments_are_not_named`・`test_committed_fragment_edited_in_the_working_tree_is_not_named` を足した
- `bash tests/validate-plugin.sh`
