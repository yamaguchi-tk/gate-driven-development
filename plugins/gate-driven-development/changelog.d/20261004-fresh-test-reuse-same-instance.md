---
type: patch
---

#### Summary

テストの結果を fresh として使ってよい場面を 1 つ足した（`references/verification-before-completion.md` § Fresh の粒度）。

- 同じ起動（subagent の 1 回の起動、または main の 1 ターン）の中で、テストを回した worktree（subagent では prompt の `## Worktree`）を cwd にして回したテストの結果は、テストを始める直前と使う前の 2 回とも、その worktree を `git -C` で指して確かめたコマンドが成功し、HEAD が同じで、`.steering/` 以外の作業ツリーが clean（変更も untracked も無い）なら、証跡に使い、同じテストを回し直さなくてよい。確かめられないとき、requirements.md・design.md が変わったときは回し直す
- 主に gate の Step の間で効く（gate は worker の commit の後に、`.steering/` だけを書きながら進む）。commit 前の作業中は使い回さない
- 使ってよいのはテストの結果だけ。状態確認・E2E・lint、`.steering/` を読むテスト、同じ入力で繰り返して比べる手順（E2E の一貫性確認、flaky の再現率、再現性の確認）、別の起動の結果（subagent の報告、前のセッション）は対象外
- gate runner・light task runner は、SKILL.md の Step が fresh な実行を求めるときも、この扱いを優先する

同じ規定を書いていた completion-check・ac-verification・reference 内の記述も、この例外に揃えた。実装 worker の agent 定義からも同じ節を参照する。これまでは gate の Step ごとに、同じテストの全量を回し直すことがあった。

#### Affected Files

- `plugins/gate-driven-development/references/verification-before-completion.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-ac-verification/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-formal-gate-runner.md`
- `plugins/gate-driven-development/agents/gdd-light-task-runner.md`
- `plugins/gate-driven-development/agents/gdd-implementation-worker.md`
- `plugins/gate-driven-development/agents/gdd-implementation-worker-heavy.md`
- `plugins/gate-driven-development/agents/gdd-remediation-worker.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- Skill RED-GREEN Evidence（gate runner の圧力シナリオ 3 つを、変更前と変更後の規定で比べた）
- `bash tests/validate-plugin.sh`
