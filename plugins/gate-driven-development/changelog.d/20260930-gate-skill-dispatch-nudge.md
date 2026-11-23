---
type: minor
---

#### Summary

main が gate の skill（`gdd-implementation-gating`・`gdd-completion-check`）を Skill ツールで直接呼んだとき、`references/subagent-dispatch.md` の Template で `gdd-formal-gate-runner` に dispatch するよう促すようにした。止めはしない。

自由文での再開や compact・resume の後に、main が `Next Action` の名前の skill をそのまま呼び、gate を main で回すことがあった。そのときは runner が書く `handoff/` の記録が残らなかった。

#### Added

- PreToolUse（Skill）の hook `run-gate-skill-dispatch-nudge-hook.sh` を足した。対象の 2 つの skill が Skill ツールで呼ばれると、Template の場所と dispatch 先を `additionalContext` で伝える。GDD の loop が active かは問わない。kill switch（`~/.claude/gdd-hooks-disabled`）で止まる

#### Changed

- 2 つの skill の冒頭の段落に、Claude Code の main セッションで手順を読んでいるとき（Skill ツール・slash コマンド・Read のどれで開いても）は実行せず、Template で runner に dispatch することを書いた。Codex・Cursor は `references/subagent-dispatch.md` § Codex / Cursor Worker Dispatch に従う

#### Affected Files

- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/hooks/scripts/run-gate-skill-dispatch-nudge-hook.sh`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/tests/test_gate_skill_dispatch_nudge_hook.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`

#### User Action Required

- 長く動いているセッションは、resume して hook を読み込み直す

#### Validation / Eval Impact

- `tests/test_gate_skill_dispatch_nudge_hook.py` に、対象の skill 名（prefix の有無、入力のキー 3 種）で案内が出ること、ほかの skill と読めない入力では何も出ないこと、kill switch で止まること、`hooks.json` の登録から起動して案内が出ること、案内が指す Template の見出しと dispatch 先が `references/subagent-dispatch.md` にあることのテストを足した
