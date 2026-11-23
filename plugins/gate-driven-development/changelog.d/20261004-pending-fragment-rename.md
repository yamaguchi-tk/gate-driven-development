---
type: patch
---

#### Summary

`validate-plugin.sh` が変更断片が無いと失敗したときの「The fragment is not committed yet」の名指しを、commit したら足した断片に数えるかどうかとそろえた。普通の `mv` で他の PR の断片を改名しただけのもの（untracked）は名指ししない。merge-base の断片が元の場所に残っていれば、同じ中身の自分の断片は名指しする。中身は index ではなく作業ツリーで比べる（`git mv` の後に作業ツリーだけ書き換えたものも名指しする）。

#### Affected Files

- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_changelog_fragments.py` の `test_fragment_of_another_pr_moved_without_git_mv_is_not_named`・`test_own_fragment_with_the_same_content_as_a_kept_one_is_named`・`test_only_the_moved_count_is_left_unnamed`・`test_own_fragment_is_named_after_a_committed_rename_takes_the_moved_slot`・`test_restored_fragment_of_another_pr_is_not_named` を足した
- `bash tests/validate-plugin.sh`
