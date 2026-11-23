---
type: patch
---

#### Summary

merge gate が、同じ repo の別 worktree や root checkout へ `cd` してからの merge を、別 repo への merge と見なして `pr-target-unresolvable` で止めていたのを直した。実行先（`cd` 先、または Codex などが payload で渡す `cwd` / `workdir`）と root の toplevel が違っても、git の共通ディレクトリが同じなら、通常は `gh` の対象 repo も同じである。そのため、対象 PR を番号か URL で明示した merge は、実行先が marker（`.claude/gdd-dev.local.md`）を持たなければ通す。このとき、セッションの steering に対象 PR が無ければ、GDD の PR 台帳を照合し、台帳に載った PR と照合できない場合は `repo-root-unresolvable` で止める。

`cd` 先が同じ repo で marker を持つ worktree（GDD の専用 worktree）なら、`gh` が実際に走るその worktree を root にし、そこの steering の証跡で判定する。セッションの worktree が marker を持つとき、payload の `cwd` / `workdir` で marker を持つ別の worktree を指した merge は、従来どおり止まる。

#### Fixed

- `hooks/scripts/run-merge-gate-hook.sh` の AC-18（root と `gh` の実行先の照合）は、toplevel が違っても、git の共通ディレクトリが同じで、対象 PR を明示し、実行先が marker を持たなければ通す。共通ディレクトリを読めないとき（git 2.31 未満、パスの途中に改行を含むなど）は、従来どおり止める
- 上の条件で通した merge で、セッションの steering に対象 PR が無い（steering が無い・別の PR を記録している）ときは、GDD の PR 台帳を照合する。台帳に載った PR と、照合できない場合（unknown・unreadable）は `repo-root-unresolvable` で止める
- 同じ repo で marker を持つ `cd` 先は、対象 PR を明示したときだけ root にする。そこで steering が解決しない・対象 PR が一致しない形は `untrusted-root-unverified` で止まる

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/tests/test_merge_gate_same_repo_worktree.py`

#### User Action Required

- なし。別 repo への `cd` と、対象 PR を省いた merge は、従来どおり止まる

#### Validation / Eval Impact

- `tests/test_merge_gate_same_repo_worktree.py` を足した。hook の入口から次を確かめる
  - root checkout・marker の無い別 worktree への `cd`（payload の `cwd` を含む）は通る
  - 別 repo への `cd`・対象 PR を省いた merge は止まる
  - 専用 worktree への `cd` はその worktree の証跡で判定され、`&` 形・`-R` の別 repo は止まる
  - payload の `cwd` で marker のある worktree を指す形・改行を含む toplevel・共通ディレクトリを読めない git（古い出力・失敗）では止まる
  - 共通ディレクトリで通した merge は、台帳に載った PR なら止まり（セッションの steering が無い・別の PR を 1 件・複数件記録している形）、セッションの steering に対象 PR があれば台帳に載っていても通る
