---
type: patch
---

#### Summary

gate の skill（`gdd-implementation-gating`・`gdd-completion-check`）の冒頭の段落で、runner に dispatch する条件を「Claude Code の main セッションで、この gate を回すために手順を読んでいるとき」に絞った。参照のために開いたときは dispatch しない。Codex・Cursor にはこの段落は当てはまらず、これまでどおり skill の手順に従う。

#### Changed

- 2 つの skill の冒頭の段落の条件に「この gate を回すために」を足した。Codex・Cursor について、`references/subagent-dispatch.md` § Codex / Cursor Worker Dispatch に従う、という飛び先を消し、この段落は当てはまらない、とした
- `README.md` の PreToolUse の block するゲートの列挙に、`.steering/` への書き込みと merge gate を足した

#### Affected Files

- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/tests/test_gate_skill_dispatch_nudge_hook.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_gate_skill_dispatch_nudge_hook.py` の出力の検査を、top-level のキーが `hookSpecificOutput` だけであることまで広げた
