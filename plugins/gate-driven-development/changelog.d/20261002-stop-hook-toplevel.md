---
type: patch
---

#### Summary

Stop hook の done guard は、worktree の toplevel から bind 済みの steering（無ければその worktree の `.steering`）を見つけ、tasklist が未完了なら done を止める。ところが toplevel を text モードの `.strip()` で読んでいたので、名前が空白・タブ・改行・CR で終わる worktree では toplevel が別のパスになり、検査対象を見失って warn だけで done を通していた。今後は、git の出力を bytes で読み、最後の改行だけを落とす。

名前（パス）に制御文字・書式文字（タブ・改行・CR・ZWJ など）を含む worktree では、toplevel を正しく読めた後に steering の containment 検査が拒否するので、`.steering/` の下に steering が 1 つでもあれば、tasklist の状態と steering の数にかかわらず done を止める（`containment rejected`）。名前を変えるまで解除できない。

#### Fixed

- `hooks/scripts/gdd_stop_hook.py` の `_worktree_toplevel` は、`git rev-parse --show-toplevel` の出力を bytes で読み、最後の改行 1 つだけを落とす。Stop hook が steering を見る経路（done guard・進捗表示・resume-from の fallback・follow-up の検査・compact の提案・phase 遷移の handoff の warning・bind-unresolved の warn）が、同じ toplevel を使う
- `hooks/scripts/lib/task_binding_resolve.py` の `resolve_guard_tasklist` は、worktree のパスに注入面のある文字があり steering が 2 つ以上あるときも、検査対象なしで通さずに containment で止める（binding は同じ文字で捨てられるので、今までは未完了の tasklist のまま done を通していた）
- `hooks/scripts/lib/stop-failure-record.py` も、StopFailure の記録の `project_root` を同じ読み方で求める。名前が空白・タブ・CR で終わる worktree でも、SessionStart が前のターンの異常終了を通知する

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/lib/stop-failure-record.py`
- `plugins/gate-driven-development/hooks/scripts/lib/task_binding_resolve.py`
- `plugins/gate-driven-development/tests/test_stop_hook_toplevel_trailing_whitespace.py`
- `plugins/gate-driven-development/tests/test_stop_failure_hook_contract.py`

#### User Action Required

- 名前（パス）に制御文字・書式文字（タブ・改行・CR・ZWJ など）を含む worktree で GDD を使っているなら、名前を変える。そのままでは done が毎回止まる

#### Validation / Eval Impact

- `tests/test_stop_hook_toplevel_trailing_whitespace.py` を足した。名前が空白で終わる worktree で、未完了の tasklist は tasklist の検査で block になり（binding がある形・無い形）、完了済みの tasklist は通る（binding がある形）。名前がタブ・改行・CR で終わる worktree は、tasklist の状態と steering の数（1 つ・2 つ）にかかわらず containment で block になり、steering が無ければ通る
- `tests/test_stop_failure_hook_contract.py` に、名前が空白・タブ・改行・CR で終わる repo で `project_root` が toplevel と一致するテストを足した
