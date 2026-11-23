---
type: patch
---

#### Summary

- 待ちのループを deny するときの subagent への理由文は、待機スクリプトを foreground で、`--timeout` を Bash の timeout（省くと 120 秒、最大 600 秒）より短くして起動する案内にした。background で起動して完了通知を待つ案内は出さず、自分が起動した background の処理だけを Monitor で待たせる（subagent が background の完了通知や Monitor のイベントを受け取れるかは確かめていない）。`references/subagent-dispatch.md` と background-dispatch-gate の docstring も、subagent が通知を受けられないと言い切らず「確かめていない」にそろえた
- `docs/SECURITY.md` の hook 表の Agent の行に、background-dispatch-gate の deny と、それが読む `run_in_background`・`agent_id`・git の toplevel・`.claude/gdd-dev.local.md`、`.gdd/hook-errors.log` への記録を足した。「hook は失敗時 fail-closed」を原則とし、通す例外を書いた（型を読めない payload と判定の例外で通す wait-loop-gate・background-dispatch-gate、command や skill の名前を解析できないと通す pre-push・pre-PR・active-gdd-skill の gate、python が無いと通す worktree-command-guard。網羅ではない）。escape hatch の文は `validate-steering-write.py` の箇条に分けた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/wait_loop_gate.py`
- `plugins/gate-driven-development/hooks/scripts/lib/kill-switch.sh`（コメントだけ）
- `plugins/gate-driven-development/hooks/scripts/lib/background_dispatch_gate.py`（docstring だけ）
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/tests/test_wait_loop_gate.py`
- `plugins/gate-driven-development/tests/test_hook_python_safe_path.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_wait_loop_gate.py`: subagent への理由文で、foreground の案内が Monitor の案内より先にあり、`run_in_background: true` と「完了通知を待つ」を含まず、Bash の timeout の既定値（120 秒）を示し、600 秒以上の `--timeout` を例に出さないこと。subagent への理由文の呼び出しも、wait-until.py が受け付け、gate が通すこと
- `tests/test_hook_python_safe_path.py`: `/usr/bin/python3` が 3.11 未満のときの `-I` と block gate のケースを別のテストにし、無ければ skip として結果に残す。Stop hook の HITL lint を PYTHONSAFEPATH の下で確かめるテストの skip を、PATH の `python3` が PYTHONSAFEPATH を読むかで決める。hook がファイルとして起動する `hooks/scripts/lib/*.py`（`run-*.sh` のコメントでない行から拾う）も `-I` で import できること。`run-gdd-stop-hook.sh` から、cwd に `json.py` と `lib/` があり `PYTHONPATH=:` でも、Stop hook 本体が落ちずに、HITL lint に落ちる HITL を block し、きれいな HITL を通すこと（HITL lint が起動する子の python が `-I` かは見分けない）。hook の `.sh` に、正規表現で並べた形（`exec`・`timeout`・`env`・`nohup`・`xargs`・`command` の後ろ、引用符の無い絶対パス）で起動する python が無いこと（引用符つきの絶対パス、名前に python を含まない変数、オプションや行継続を挟む形は拾わない）
- `bash tests/validate-plugin.sh`
