---
type: patch
---

#### Summary

`validate-plugin.sh` の変更断片の検査で、merge-base にある他の PR の断片を、中身を変えずに改名して commit しただけのものを、このブランチが足した断片に数えないようにした。数えなかった改名先は、断片が無いときの FAIL に名指しする。元の場所から消えた・書き換わった断片と同じ中身のものだけを、その個数の分だけ外すので、他の PR の断片と同じ中身の自分の断片は、元の断片が残っていれば今までどおり数える。

#### Affected Files

- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_changelog_fragments.py` の `test_fragment_of_another_pr_renamed_and_committed_does_not_count_as_added`・`test_own_fragment_still_counts_when_another_pr_fragment_is_renamed`・`test_own_fragment_with_the_same_content_as_a_renamed_one_counts_once` を足し、`test_fragment_similar_to_a_deleted_one_counts_as_added` を、消した断片と中身の違う断片を足し、消した断片の FAIL だけが出ることを見る形に変えた
- `bash tests/validate-plugin.sh`
