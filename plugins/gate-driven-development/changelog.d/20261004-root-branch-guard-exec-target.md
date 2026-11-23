---
type: patch
---

#### Summary

root branch guard（`validate-worktree-command.py`）が、ブランチを作る実行先でも判定するようにした。これまでは payload の cwd だけで判定していたので、linked worktree のセッションから `cd <root> && git checkout -b …` や `git -C <root> switch -c …` で、GDD が active な root checkout にブランチを作る形を通していた。payload の cwd は候補に残したまま、先行するセグメントの先頭にある `cd` と、`git -C` の行き先（変数・コマンド置換を含まないもの。相対パスは前の行き先を基点に解く）を候補に足し、どれか 1 つが「GDD が active で linked worktree でない」なら止める。変数などで決められない行き先は候補にしない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_exec_target.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_root_branch_guard_exec_target.py` を足した
- `bash tests/validate-plugin.sh`
