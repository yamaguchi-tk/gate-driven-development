---
type: patch
---

#### Summary

変更断片の有無を検査する `version-not-consumed.sh` は、plugin のツリーに変更が無いブランチを SKIP-B にしている。ところが、統合先（`origin/main`）の最新とツリーを比べていたので、ブランチが分岐した後に統合先が plugin を変えると、plugin に触れていないブランチでも断片を求めて FAIL していた。今後は、統合先との merge-base と比べる。

#### Fixed

- `tests/checks/version-not-consumed.sh` の SKIP-B（「this branch ships nothing」）は、merge-base から HEAD までに plugin のツリーが変わっていないときにだけ出る。統合先が分岐後に plugin を変えても、plugin に触れていないブランチは SKIP-B になる（統合先と criss-cross の merge をしたブランチを除く。merge-base が 2 件以上あると、git が返す 1 件によって結果が変わる）。SKIP-B の理由の文言は `plugin tree is unchanged since the merge-base with <ref>` になる
- 統合先と共通の祖先が無い（merge-base が取れない）ときは、ツリーが統合先と同じでも SKIP-B にせず FAIL にする。分岐点が履歴に無い shallow clone も同じく FAIL になり、`git fetch --unshallow` を案内する
- 統合先の最新と plugin のツリーが同じでも、分岐後に plugin を変えたブランチ（同じ版を上げたリリース分岐など）は SKIP-B にせず、版数と断片を検査する

#### Affected Files

- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/docs/VERSIONING.md`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_changelog_fragments.py` の `VersionCheckTests` に次のテストを足した。plugin に触れないブランチは、分岐後に統合先が plugin を変えても、統合先を取り込んでも SKIP-B になる。plugin を変えて断片の無いブランチは、統合先が plugin を変えた後も、取り込んだ後も FAIL になる。共通の祖先が無いブランチと、統合先と同じツリーのリリース分岐は FAIL になる
  - `test_branch_outside_plugin_skips_after_main_changes_plugin`
  - `test_branch_that_merged_main_without_touching_plugin_skips`
  - `test_branch_changing_plugin_without_fragment_fails_after_main_changes_plugin`
  - `test_branch_changing_plugin_without_fragment_fails_after_merging_main`
  - `test_ref_without_merge_base_fails_not_skips`
  - `test_release_with_the_same_tree_as_main_fails_not_skips`
