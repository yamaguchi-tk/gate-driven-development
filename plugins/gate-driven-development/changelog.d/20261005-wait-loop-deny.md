---
type: minor
---

#### Summary

PreToolUse（Bash）の hook `run-wait-loop-gate-hook.sh` を足した。background（`run_in_background: true`）の Bash で、待ちのループを書いた command を deny し、`scripts/wait-until.py` で待つよう理由文で案内する。

- deny する形: ループの語（`until`・`while`・`for`）の後ろに `sleep` がある（python の `time.sleep` も含む）、`--watch`、`gh run watch`。上限つきのループも deny する（打ち切りと成立が同じ exit 0 で見分けられないため）
- 通す形: `sleep N` だけの期限 timer、最初のループの語の後ろに `sleep` が無い command（`sleep N; <コマンド>` など）、`wait-until.py` の呼び出し（条件に、ループの語の後ろの `sleep` や `--watch` を含まないもの）、foreground の Bash、型を読めない payload（JSON として読めないものは state dir の `wait-loop-gate.log` に記録する）
- GDD active を問わず、plugin が有効なすべての repo・セッションで動く。subagent の中の Bash も対象にする。止めるのは kill switch（`~/.claude/gdd-hooks-disabled`）だけ
- 理由文は、`wait-until.py` の絶対パスでの呼び出し（`--pr-checks`、`-- bash -c '<条件>'`、run の完了の条件の例）と、終了コードの意味を示す。subagent の中では Monitor か foreground での待ち方を、待ちでない常駐の処理（`--watch` の dev watcher など）には利用者への確認を示す

main からの gdd-formal-gate-runner の同期起動を deny する background-dispatch-gate も、repo（hook の cwd）に `lib/__init__.py`・`lib.py`・`json.py` などがあると判定の module が置き換わり、deny せずに通していた。2 つの hook とも、判定を `python3 -I` で読むようにした。

ほかの hook の `python3 -c`（pre-push gate・pre-PR gate・active-gdd-skill gate とその expansion gate・merge gate・worktree-command-guard など）も、repo の `json.py` などで import が落ちて、block せずに通していた。すべての hook が最初に読む `hooks/scripts/lib/kill-switch.sh` で、hook の中の `python3` を `-I -X utf8` で起動する関数にした。`-I` は cwd・スクリプトのディレクトリ・`PYTHONPATH`・`PYTHONHOME` を読まないので、Python 3.4 以上で、`PYTHONPATH` に空や相対の要素があっても、repo の `.py` を標準ライブラリや plugin の module より先に読まない。python から起動する子の python（HITL lint など）には `-I` が渡らないので、`PYTHONSAFEPATH=1` も設定する（3.11 以上で cwd を入れない。`PYTHONPATH` の要素は止めない）。`exec python3` は関数を通らないので、worktree-command-guard の起動から `exec` を外した。`python`（2 系）で起動する hook は関数を通らない。`-I`・`PYTHONSAFEPATH` の下でも自分のディレクトリの `lib` を読めるよう、`hooks/scripts/gdd_stop_hook.py` と `scripts/lint-*.py` の 11 本は、自分のディレクトリを `sys.path` に入れる（利用者が自分で `PYTHONSAFEPATH` を設定していた環境では、これらが `ModuleNotFoundError` で落ちていた）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-wait-loop-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/wait_loop_gate.py`
- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/hooks/scripts/run-background-dispatch-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/kill-switch.sh`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/run-worktree-command-guard.sh`
- `plugins/gate-driven-development/scripts/lint-*.py`（`lib` を読む 11 本）
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/tests/test_wait_loop_gate.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`
- `plugins/gate-driven-development/tests/test_background_dispatch_gate.py`
- `plugins/gate-driven-development/tests/test_hook_python_safe_path.py`

#### User Action Required

- background の待ちを、ループや `--watch` で書いていたなら、`scripts/wait-until.py` で書き直す（deny の理由文が書き方を示す）。hook を止めたいときは `~/.claude/gdd-hooks-disabled` を置く（GDD の hook がすべて止まる）

#### Validation / Eval Impact

- `tests/test_wait_loop_gate.py`: 待ちのループ（until・while・for と sleep、heredoc の time.sleep、`python3 -c` の time.sleep、`cd X && until`、複数行のループ）と `--watch`・`gh run watch` を、main と subagent の両方で deny すること。`sleep N`（wait_watchdog が認める期限 timer と同じ入力）・`sleep N; <コマンド>`・wait-until.py の呼び出し（条件に sleep を含むもの、パスに until・for を含むもの）・ループでない for を通すこと。run_in_background が bool の true でないもの・型を読めない payload を通すこと。入口のスクリプトから、git の外・`active: false` の repo でも deny し、kill switch で通し、読めない payload は通して repo の外のログ（600）に 1 行書き、HOME が無くても exit 2 にならないこと。hooks.json の Bash matcher に timeout 10 で登録されていること。repo に `lib/__init__.py` と `json.py` があっても deny すること（`tests/test_background_dispatch_gate.py` も同じ）。理由文が示す wait-until.py の呼び出しを、スクリプトが受け付け、この hook も通すこと
- `tests/test_hook_python_safe_path.py`: kill-switch.sh を読んだ後の `python3`（リテラル・変数・`python3 -`）が、`PYTHONPATH` が未設定・`:`・`.`・`:/x` のどれでも cwd の `json.py` を読まないこと（3.11 以上では `sys.path` に cwd が入らないことも）。`hooks/scripts/*.py`・`scripts/*.py` が `-I` と `PYTHONSAFEPATH=1` の下で `ModuleNotFoundError` を出さないこと（`/usr/bin/python3` が 3.11 未満ならその `-I` でも）。Stop hook が `PYTHONSAFEPATH=1` の下でも、きれいな HITL を通し、HITL lint に落ちる HITL を block すること。cwd（repo の toplevel）に `json.py` と `lib/__init__.py` があっても、pre-push gate・pre-PR gate・active-gdd-skill gate・その expansion gate・worktree-command-guard が、`PYTHONPATH=:` のときと、PATH の先頭の `python3` が 3.11 未満のとき（`/usr/bin/python3` があれば）も block すること
- `bash tests/validate-plugin.sh`
