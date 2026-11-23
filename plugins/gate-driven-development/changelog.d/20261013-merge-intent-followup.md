---
type: patch
---

#### Summary

マージ待ちの宣言（`.claude/gdd-merge-intent.json`）の押し返しで、残っていた形を直した。

- 宣言を書いた後の、同じ PR の `gh pr merge` の最後の試行が、本文の空の is_error の結果で終わっていたときも、走る前に止められたとみなして押し返さない。これまでは本文が空だと押し返していた（`hooks/scripts/lib/autonomy_pushback.py`）
- 押し返しの文に載せる待機スクリプトのパスに制御文字・surrogate があるときは、`…/scripts/wait-until.py` と書く。これまでは、そのまま載せるか（制御文字）、押し返し自体が出なかった（surrogate）（`hooks/scripts/lib/autonomy_pushback.py`）
- 通常の PR が、他の PR の断片を書き換えられるようにした。この branch で足した断片と対になる `review-log/<slug>.md`（repo root。merge-base に無いもの）の front matter に `amends: <断片のファイル名>, ...` と書いた断片だけ、同じパスでの書き換えを `tests/checks/version-not-consumed.sh` が通す。削除・改名は今までどおり FAIL にする。読めない宣言（空・パスを含む・名前の形でない・merge-base に無い名前・2 行・front matter が読めない）も FAIL にする
- `references/post-merge-qa.md` 手順 2、`references/state-machine.md` の Stop hook の判定順序、`hooks/hooks.json` の description を、上の受理範囲に合わせた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_pushback.py`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/hooks/hooks.json`（description）
- `plugins/gate-driven-development/tests/checks/version-not-consumed.sh`
- `plugins/gate-driven-development/changelog.d/20261013-merge-intent-vs-merge-gate.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_autonomy_pushback.py plugins/gate-driven-development/tests/test_changelog_fragment_amends.py -q`
