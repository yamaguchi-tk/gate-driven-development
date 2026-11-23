---
type: patch
---

#### Summary

- 利用者から見える変更なし。merge gate の python3 の呼び出しをまとめたときに足したテストが、merge gate を止めずに実行後に通知する形に変わった後の main で落ちていたのを直した。`"decision": "block"` を見ていた assert を、通知に出る reason code（`approval-stale`・`pr-target-unresolvable`・`parse-error`）を見る assert に替えた

#### Affected Files

- `plugins/gate-driven-development/tests/test_merge_gate_python_batch.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_merge_gate_python_batch.py -q -n auto` と `bash plugins/gate-driven-development/tests/validate-plugin.sh` を回した
