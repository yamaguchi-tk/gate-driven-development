---
type: patch
---

#### Summary

task の resolver（`scripts/gdd_task_binding.py`）は、`worktree_path` が絶対パスの文字列でない binding（空・欠落・相対パス・`~` 始まり・文字列でない値）を、今の worktree に一致させないようにした。これまでは空や相対の値がプロセスの cwd を基準に解決され、worktree の top で動く hook から見ると今の worktree に一致していた。`worktree_path` の無い旧書式の binding.json を git に commit した repo では、各 worktree に複製された旧書式の binding が一致し、done guard（Stop hook）が conflict になり、worktree に steering が 2 つ以上あるときは warn だけで停止を通していた（steering が 1 つならその 1 つを検査する）。文字列でない値では resolver が例外で落ち、同じく warn に下がっていた。done guard の `steering_path` と merge gate の binding lookup が絶対パスだけを受けるのと同じ規約にそろえた。

あわせて、binding.json 1 件のために resolver 全体が落ちないようにした。正規化できない欄（数値の `steering_path`、NUL や `\ud800` などの孤立サロゲートを含むパス）は空として扱い、Python 3.12 以前で `Path.exists` が投げ直す権限エラーは `missing_worktree_path` として扱う。読めない binding.json（深い入れ子で `json.loads` が RecursionError を投げるものなど）は、その 1 件だけを飛ばす。`resolve` の出力は、非 ASCII の文字も含めて `\uXXXX` に escape するようにした（UTF-8 で符号化できない孤立サロゲートを含む値で print が落ち、`detect-steering.sh`・`gate-ledger.sh` が空出力として fallback に進んでいた）。この 2 つは `json.load` で読むので値は変わらないが、`resolve` の出力を直接読む `gdd-status`・`/gdd-dev resume`・`gdd-next-plan` では、日本語のパスや発言が `\uXXXX` で見える。

#### Affected Files

- `plugins/gate-driven-development/scripts/gdd_task_binding.py`

#### User Action Required

- `worktree_path` の無い旧書式の `.gdd/tasks/*/binding.json` を git に commit している repo では、この版で一致はしなくなる。消してよい（`.gdd/` は gitignore の対象）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_task_binding_worktree_path_absolute.py -q`
