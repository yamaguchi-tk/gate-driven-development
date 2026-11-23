---
type: patch
---

#### Summary

Plan mode・EnterWorktree・skill gate・skill expansion gate の 4 つの block hook と Stop hook の bash 入口は、repo の toplevel を `$(pwd)`・`$(git rev-parse --show-toplevel)` で読み、そこにある marker（`.claude/gdd-dev.local.md`）で GDD が active かを決めていた。`$()` は末尾の改行を全部落とすので、名前が改行で終わる repo（`<repo>\n`）では、別のパス（`<repo>`）の marker で判定していた。今後は、toplevel を末尾の改行まで正しく取り（`hooks/scripts/lib/exact-path.sh`）、改行で終わるなら marker で判定できないものとして、active として扱う（止める側に倒す。merge gate と同じ）。

SessionStart も同じ関数で toplevel を取る。名前が改行で終わる repo でも、前のターンの異常終了の記録（StopFailure の記録）を注入する。

#### Fixed

- 4 つの block hook は、名前が改行で終わる repo（git の外のディレクトリ、サブディレクトリからの起動を含む）では、marker の有無・値にかかわらず block する
- Stop hook の bash 入口（python が無いときの active 判定 `gdd_local_state_active`）も、同じ repo では active として扱う
- SessionStart は、名前が改行で終わる repo でも StopFailure の記録を注入する（記録の書き手は改行を残す）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/exact-path.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-active-check.sh`
- `plugins/gate-driven-development/hooks/scripts/run-block-plan-mode-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-block-enter-worktree-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-active-gdd-skill-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-active-gdd-skill-expansion-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-agent-dispatch-model-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/tests/test_hooks_toplevel_trailing_newline.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_hooks_toplevel_trailing_newline.py` を足した。名前が改行で終わる repo（marker が active・inactive・無い形、末尾を落とした同名の repo がある形・無い形、サブディレクトリからの起動、git の外のディレクトリ）で 4 つの block hook が block し、名前が改行で終わらない repo では marker で決める。Stop hook の bash 入口の active 判定と、StopFailure の記録の SessionStart での注入も、同じ repo で確かめる
