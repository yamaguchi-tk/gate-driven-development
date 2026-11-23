---
type: patch
---

#### Summary

`validate-plugin.sh` が変更断片が無いと失敗したとき、`git mv` で改名して commit していない断片も、新しい名前で名指しするようにした。merge-base にある他の PR の断片を、`git mv` で（index 上で）中身を変えずに改名しただけのものは、名指ししない。

#### Affected Files

- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_changelog_fragments.py` の `test_staged_new_fragment_is_named_and_staged_edit_of_committed_fragment_is_not`・`test_fragment_renamed_with_git_mv_is_named`・`test_fragment_of_another_pr_renamed_without_changes_is_not_named` を足した
- `bash tests/validate-plugin.sh`
