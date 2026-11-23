---
type: patch
---

#### Summary

merge gate は、コマンドに UTF-8 で書けない文字（`\ud800` のような lone surrogate）があっても、GDD の PR 台帳と照合するようにした。今までは、hook が解析結果を書き出す途中で例外になり、照合する番号が空のまま残ったので、marker の無い checkout（root checkout など）から打った台帳の PR の merge が通っていた。書き出しは pre-push gate と同じ形にした（surrogateescape で符号化し、それでも書けない行は行全体を backslashreplace で書く）。

- payload の `cwd`（`workdir`）欄を書き出す処理も同じ形にした
- payload の `cwd` が解決できない（存在しない・書けない文字を含むなど）merge は、`-R` の無い番号を番号だけで台帳と照合する。今までは marker の無い checkout の経路で照合から落ち、台帳の PR でも通っていた
- marker のある worktree では、こうしたコマンドを今まで `parse-error` で止めていた。今後は通常の判定に回り、たとえば書けない文字を含む cd 先は `pr-target-unresolvable` で止まる

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`

#### User Action Required

- なし

#### Validation / Eval Impact

- `plugins/gate-driven-development/tests/test_merge_gate_emit_encoding.py` を足した
