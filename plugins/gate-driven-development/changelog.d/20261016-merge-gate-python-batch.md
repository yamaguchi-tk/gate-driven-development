---
type: patch
---

#### Summary

- merge gate の hook が 1 回の起動で python3 を起こす回数を減らした。判定（block・allow、理由、exit code）は変えていない
  - 証跡の時刻は、`gdd_parse_merge_gate_field` が検証のときに変換した epoch（`GDD_MG_AT_EPOCH`・`GDD_MG_APPROVED_AT_EPOCH`）を使い回す。承認の鮮度と、Recheck・待機の経過の判定で、同じ時刻を python3 で変換し直さない。経過は `date -u +%s` との引き算にした
  - `tool_input` の cwd は、コマンドの解析と同じ埋め込みの python が渡す。payload を読む python3 は 1 回になった

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/merge-gate-evidence.sh`
- `plugins/gate-driven-development/tests/_merge_gate_input_classes.py`
- `plugins/gate-driven-development/tests/test_merge_gate_input_classes.py`
- `plugins/gate-driven-development/tests/test_merge_gate_python_batch.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- merge gate のテスト（`tests/test_merge_gate_*.py`）を、python3 の起動を記録する shim を PATH に置いて、変更の前と後で回した。`python3 scripts/light-lane-related-tests.py --run . origin/main` と `bash plugins/gate-driven-development/tests/validate-plugin.sh` を回した
