---
type: minor
---

#### Summary

- merge gate は、対象 PR を番号か URL で明示した `gh pr merge` で、`gh` の実行先の repo の binding（root checkout と各 worktree の `.gdd/tasks/*/binding.json`）が指す state.md の `PR URL` が対象 PR に 1 件だけ当たれば、その GDD worktree の steering の証跡（承認・再 fetch・push・bot レビュー・独立レビュー）と HEAD で判定する。binding を引くのは、hook が root を決められ（セッションの cwd が repo の中、または cd 先に marker がある）、実行先の git repo を決められ、下の条件（番号だけの merge・cd の形・対象の書き方）に当たらないときで、そのとき root checkout・GDD worktree・同じ repo の別 worktree のどこから打っても同じ binding を引く。実行先が git の外か決められないとき（cwd が git の外のセッション〔marker の無い GDD worktree へ cd しても同じ〕、`cd "$X"` など）は binding を引かず、今までどおり PR 台帳で判定する（marker のある root からの、対象を repo つきで明示した merge だけは root の repo の binding を引く）
- root checkout に別のセッションの marker が残っているとき、`cd <root checkout> && gh pr merge <n> -R <owner/repo>` が `untrusted-root-unverified` で止まらなくなる（証跡が揃っていれば通り、欠けていれば `approval-missing` などで止まる）
- 自セッションの marker がある root checkout でも、root の steering が対象 PR を記録していない（steering が無い、または別の PR を記録している）ときは、binding の worktree の証跡で判定する。別の PR を記録しているときは今まで止まっていたが、binding の worktree の証跡が揃えば通る
- marker の無い GDD worktree や root checkout で打った merge は、今までは PR 台帳の照合が外れると証跡を見ずに通っていた。binding が対象 PR の steering を指すときは、証跡を検査して止めるようになる
- binding が同じ PR を記録した steering を 2 件以上指すときは `steering-ambiguous` で止める（同じ state.md を指す binding は 1 件に数える）。ユーザーに確認して、使わない steering の binding を消すか、その state.md の `PR URL` を直してから再実行する。binding が読めない・通常のファイルでない・当たらない・root の steering が読めないか `PR URL` を記録していないときは、今までの判定のまま。root の steering に対象 PR が無いときの切り替えは、binding の state.md が worktree の `.steering/<slug>/state.md` のときだけ行う
- steering の解決（pre-push・pre-PR・merge gate など、binding から steering を引く hook）は、通常のファイルでない `binding.json`（FIFO など）を読まずに飛ばす。UTF-8 として読めない `binding.json` は、その 1 件だけを飛ばす（今までは解決全体が失敗していた）。今までは FIFO があると hook が止まり、timeout で素通りしていた。binding で GDD worktree へ切り替えた merge gate も、実行先の marker が通常のファイルでないときに止まらない
- 別の repo へ `cd` した番号だけの merge（`cd X && gh pr merge 7`・`cd X & gh pr merge 7` など）は binding を引かず、今までどおり PR 台帳で判定する（`&` やパイプでは `gh` が元の cwd で走り、番号は元の repo の PR を指すので、cd 先の証跡では通さない）。対象を repo つきで明示した merge は、cd 先の repo の binding で判定する
- 対象 PR を省いた merge・対象を決められない merge・`GH_REPO`／`GH_HOST` を設定した merge は binding を引かず、今までどおり PR 台帳で判定する
- 番号だけの merge は、`gh` が origin の repo を選ぶと決まるとき（remote が origin だけで `gh repo set-default` が無い、または origin が set-default）だけ binding を引く

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/merge-gate-binding.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/scripts/gdd_task_binding.py`

#### User Action Required

- GDD worktree の steering に merge gate の証跡（`Merge Approval` など）を記録せずに `gh pr merge` していた運用では、merge が止まるようになる。記録してから merge する

#### Validation / Eval Impact

- `tests/test_merge_gate_binding_steering.py` を追加（root checkout・GDD worktree・同じ repo の別 worktree・別の repo からの判定、承認の証跡が無い PR を通さないこと）
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
