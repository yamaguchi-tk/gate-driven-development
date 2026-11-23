---
type: patch
---

#### Summary

`setup-gdd-loop.sh` が別のセッションの `active: true` の state file（`.claude/gdd-dev.local.md`）で止めたとき、抜け方も出すようにした。中身は「先のセッションがまだ動いているかをユーザーに確かめ、動いていなければ `active:` を `false` にして再実行する。session_id は書き換えない」である。`docs/TROUBLESHOOTING.md` の同じ節にも、session_id を書き換えないこととやり直しを足した。止めるかどうかの判定は変えていない。

#### Affected Files

- `plugins/gate-driven-development/scripts/setup-gdd-loop.sh`
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_setup_gdd_loop_session_lock.py -q`
