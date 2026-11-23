---
type: patch
---

#### Summary

- wait-loop-gate の deny の文も、待機スクリプトのパスに制御文字・surrogate があるときは、Stop hook の押し返しの文と同じく `…/scripts/wait-until.py` と書く。これまでは、パスをクォートの中にそのまま載せていた。判定は `hooks/scripts/lib/wait_script.py` の 1 つの関数で行う
- Stop hook の押し返しの文で、PR の head を読めないときの run の確かめ方を、`--commit <head>` の代わりに `gh pr view` で head を引く形にした（`<head>` は shell に貼るとリダイレクトになる）
- `docs/VERSIONING.md` の層 B の表と `tests/checks/version-not-consumed.sh` の冒頭に、分岐点の断片を消す・書き換えるのは FAIL で、review-log の `amends:` で宣言した書き換えだけを通すことを書いた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/wait_script.py`（新規）
- `plugins/gate-driven-development/hooks/scripts/lib/wait_loop_gate.py`
- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_pushback.py`
- `plugins/gate-driven-development/docs/VERSIONING.md`
- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`（コメント）
- `plugins/gate-driven-development/changelog.d/20261013-merge-intent-followup.md`（`amends:` で書き換え）
- `plugins/gate-driven-development/tests/test_wait_loop_gate.py`・`tests/test_stop_hook_autonomy_pushback.py`・`tests/test_changelog_fragment_amends.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_wait_loop_gate.py plugins/gate-driven-development/tests/test_stop_hook_autonomy_pushback.py plugins/gate-driven-development/tests/test_changelog_fragment_amends.py -q`
