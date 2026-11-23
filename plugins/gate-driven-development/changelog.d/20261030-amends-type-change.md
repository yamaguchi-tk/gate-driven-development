---
type: patch
---

#### Summary

通常の PR が、review-log の `amends:` で宣言した他の PR の断片の `type:` も書き換えられるようにした。これまでは、宣言しても `type:` を変える書き換えは FAIL だった。

#### Changed

- `tests/checks/version-not-consumed.sh`：`amends:` で宣言した断片の、同じパスでの書き換えを `type:` を問わず通す。宣言の無い書き換え・削除・改名は今までどおり FAIL。断片の書式（`type:` の値など）は今までどおり層 A が見る
- `docs/VERSIONING.md`：上の受理範囲を書き直した。よくある判断の迷いの「既存の agent の定義の model・effort を変えた」に、変えた model に合わせて既にある dispatch gate の固定 model の表・警告・reference を直しただけのときも PATCH と書いた
- 未リリースの断片 `20261030-simplifier-sonnet.md` の `type:` を patch に、`20261013-merge-intent-followup.md` の受理範囲の文を、今の検査に合わせた

#### Affected Files

- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/docs/VERSIONING.md`
- `plugins/gate-driven-development/tests/test_changelog_fragment_amends.py`
- `plugins/gate-driven-development/changelog.d/20261030-simplifier-sonnet.md`
- `plugins/gate-driven-development/changelog.d/20261013-merge-intent-followup.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_changelog_fragment_amends.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
