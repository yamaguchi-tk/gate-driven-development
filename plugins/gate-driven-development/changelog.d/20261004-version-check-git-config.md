---
type: patch
---

#### Summary

`validate-plugin.sh` の変更断片の検査が、利用者の git 設定 `diff.relative=true` のもとで、足した断片を数え落として「no changelog fragment」で失敗していたのを直した。検査の git は `diff.relative=false` で動く。

#### Affected Files

- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_changelog_fragments.py` の `test_fragment_counts_when_the_repo_sets_diff_relative` を足した
- `bash tests/validate-plugin.sh`
