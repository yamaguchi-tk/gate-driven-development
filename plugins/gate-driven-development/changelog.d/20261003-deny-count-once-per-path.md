---
type: patch
---

#### Summary

steering write guard の連続 deny の回数を、counter（path と category の組。path は `\` と `/` の違いだけを同じとみなす）ごとに、書き込み 1 回で 1 回だけ進めるようにした。同じ綴りの path を `file_path` と `path` の 2 つの key で渡す書き込みは、今まで 1 回で 2 回と数えられ、2 回目の書き込みで警告付きの allow に降格していた。`completed_reviewed_by` は path ごとに reason が出るので、同じ綴りなら 1 回目、綴り違いの 2 つの key でも 2 回目に降格していた。大小文字・`./`・`..`・symlink など、ほかの綴り違いは今までどおり別の counter になる（降格はそれぞれ 3 回目。ある綴りで違反の無い書き込みをしても、別の綴りの回数は戻らない）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/tests/test_completed_reviewed_by_write_guard.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_completed_reviewed_by_write_guard.py` の `test_same_file_named_by_two_keys_counts_as_one_deny` と `test_keys_differing_only_in_separators_share_one_counter` を足した（同じ綴り・`./` の綴り・`\` の綴りの 2 つの key で、1・2 回目は deny、3 回目で降格）
