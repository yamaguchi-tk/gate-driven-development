---
type: patch
---

#### Summary

- `gdd-formal-gate-runner` の起動を background に強制する PreToolUse hook（`background_dispatch_gate.py`）が、`run_in_background` を文字列の `"true"` で受けたときも background として通すようにした。2026-11-13、Agent ツールの定義に `run_in_background` が無いセッション（定義の説明は「subagent は background で動く」）で、値が文字列の `"true"` のまま hook に届き、`/gdd-dev` の brainstorming の起動が拒否されて gate-runner を一度も起動できなかった（観測）。定義に引数がある host では、hook に届く前に真偽値へ変換されていると推定している（transcript には文字列の `"true"` が残るが、その起動は通っている）
- 整数の `1` や `"yes"`・`"True"` などは今までどおり拒否する

#### Affected Files

- `hooks/scripts/lib/background_dispatch_gate.py`・`tests/test_background_dispatch_gate.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest tests/test_background_dispatch_gate.py`・`python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
