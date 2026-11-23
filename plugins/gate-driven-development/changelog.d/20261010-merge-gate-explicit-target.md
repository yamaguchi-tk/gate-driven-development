---
type: patch
---

#### Summary

merge gate は、対象を repo つきで明示した merge（PR の URL、`-R owner/name <番号>`）を、cd 先や payload の `cwd` が別の repo・marker のある worktree を指すとき、または cd 先を 1 つに決められないときも、それだけでは止めなくなった。`cd <dir> && X=$(…) && gh pr merge -R owner/name 7` や、merge の後ろに cd と `$` が続く形がこれに当たる。gh が操作する PR は実行先に依存しないので、セッションの root の証跡で検査する。root の steering に対象 PR が無いときは GDD の PR 台帳を引き、台帳に載っている GDD worktree の PR なら `repo-root-unresolvable` で止める。台帳を読めないときも止める。cwd が git でないセッション（root を決められない経路）でも、明示した merge は cd の意図・cd 先・payload の `cwd` を見ずに台帳だけで決め、`repo-root-unresolvable` で止めるのは、台帳に載っている PR、台帳を読めないとき、決められる実行先（プロセス cwd・payload の `cwd`・cd 先）の祖先に marker があるとき（git が無い・`git rev-parse` が失敗した GDD worktree）にした。番号だけの merge、引数を省いた merge、host つきの `-R`、`GH_HOST` / `GH_REPO` の前置は、実行先を決められなければ今までどおり止める。`-R` や URL の owner/repo が許可リストの形でない（`$`・`*` を含むなど）ときは明示に当たらず、台帳は番号だけで照合する。`repo-root-unresolvable` の案内に、cd と同じコマンドに `$` を含めないことを足した。

`20261001-merge-gate-same-repo-worktree` と `20261002-merge-gate-cd-after-merge` が「従来どおり止まる」と書く形（別 repo への `cd`、payload の `cwd` で marker のある worktree を指した形、マージより前と後ろで別の repo に `cd` する形）のうち、対象を repo つきで明示した merge は、この変更で上のとおり止まらなくなった。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`（注釈のみ）
- `plugins/gate-driven-development/tests/test_merge_gate_explicit_target.py`
- `plugins/gate-driven-development/tests/test_merge_gate_cd_after_merge.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_merge_gate_explicit_target.py plugins/gate-driven-development/tests/test_merge_gate_cd_after_merge.py`
