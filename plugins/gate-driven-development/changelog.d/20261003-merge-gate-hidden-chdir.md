---
type: patch
---

#### Summary

merge gate は、cwd を変える語として `cd`・`pushd`・`popd` だけを見ていた。そのため、zsh の `chdir` で cwd を変える形を「cwd を変えない」として扱い、実行先を確かめずに通していた。今後は `chdir` を `cd` と同じく扱う。また、marker の無い repo の cwd から、実行先の repo を決められない番号形のマージ（`-R` 無し）をしたときは、GDD の PR 台帳と番号だけで照合し、台帳の PR と番号が一致すれば止める。

#### Fixed

- `hooks/scripts/lib/gh_command_parse.py` は、`chdir` を `cd` と同じく cwd を変える語として数える
- `hooks/scripts/run-merge-gate-hook.sh` は、marker の無い git の cwd の経路で、cwd を変える語があり実行先の repo を決められない番号形のマージを、台帳のどれかの PR と番号だけで照合する。一致すれば止め、一致しなければ今までどおり通す。`-R` 付き・URL 形は今までどおり repo と番号の組で照合する。block の文面に、`chdir` を別のコマンドに分けることと、GDD の外の PR なら `-R`・URL で明示することを足した

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/tests/test_merge_gate_hidden_chdir.py`

#### User Action Required

- marker の無い repo から、実行先を決められない形（`cd "$PWD" && gh pr merge 7` など）で、GDD の PR 台帳にある PR と同じ番号の別 repo の PR をマージすると止まる。`gh pr merge -R <owner/repo> <番号>` か URL 形で打ち直す

#### Validation / Eval Impact

- `tests/test_merge_gate_hidden_chdir.py` を足した。`chdir`・`builtin chdir` が cwd を変える語になる。`.`・`source`・`alias` は今までどおり見ず、`cd /W && source …` でも `/W` を実行先にする。marker の無い git の cwd で、台帳の PR と同じ番号の、実行先を決められないマージは止まり、別の番号・`-R`・URL 形は通る。GDD の worktree へ `cd` した後に読み込みの語があるマージも、worktree の証跡で判定する
