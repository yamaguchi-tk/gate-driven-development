---
type: patch
---

#### Summary

- `docs/SECURITY.md` と `hooks/scripts/lib/gdd-pr-roots.sh` の PR 台帳の限界に、`cd <GDD worktree> && … git push` の形でも pre-push gate が証跡を検査せずに通すことを足した。pre-PR gate が飛ばすのは marker の判定より後の検査すべてだと書き、raw task steering の検査は base branch を解決できるときだけ走ると書いた。照合で外れた GDD の PR の merge が証跡を見ずに通る場合を、root に marker が無いとき・root を決められず GDD の外と判定できたとき・marker のある root の steering が対象 PR を記録していないときと書いた。「マージの承認は人が持つ」を、GDD はこの経路で承認を検査しないので導入先の運用で担保する、に改めた
- merge gate が台帳で当たった PR を止めるときの案内（reason code `repo-root-unresolvable`）に、台帳に載った GDD worktree に marker が無いと cd しても同じ照合で止まり続けるので、人が merge する、を足した。判定は変えていない
- `docs/SECURITY.md` § 制限事項の block guard の守る範囲の例外に、GDD worktree へ cd して打つ `git push` と pre-push gate を足し、pre-PR gate・pre-push gate がしないのは marker を見る検査だと書いた

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`

#### User Action Required

- 台帳で当たって止まった `gh pr merge` は、GDD の worktree へ cd して実行し直しても、その worktree に marker（`.claude/gdd-dev.local.md`）が無ければ止まり続ける。そのときは人が merge する

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py`）
