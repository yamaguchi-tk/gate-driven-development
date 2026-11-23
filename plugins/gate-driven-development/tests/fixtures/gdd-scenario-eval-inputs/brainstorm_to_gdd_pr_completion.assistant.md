承知しました。ここまでの `gdd-pre-workflow-brainstorming` の壁打ちは相談レーンのままで、`.steering` や worktree は作っていませんでした。「gdd-devで計画して」という指示を **formal Go** として受け取り、ここから `gdd-brainstorming` を正規ルートにして `/gdd-dev` の formal GDD workflow に入ります。

まず `main` 起点の専用 worktree を切り、そこに `requirements.md` / lightweight `design.md` / `state.md` を作成して human check まで出します。**GDD primary** で進めるため、この作業は `superpowers:writing-plans` / `superpowers:executing-plans` には渡さない。相談レーンの結論（reviewer lane を増やすのではなく `contract delta -> consumer simulation -> failure hypothesis -> counter-evidence` を測る構造にする）を requirements の土台として引き継ぎます。

今回の到達点は **PR 作成まで** です。formal GDD の標準順序（`gdd-requirements-gating` → `gdd-design-gating` → `gdd-task-breakdown` → `gdd-test-driven-development` → `gdd-implementation-gating` → `gdd-completion-check`）を通し、`gdd-completion-check` の Post-Completion PR Flow で commit / push / PR 作成まで自律的に進めます。merge / deploy は別承認です。

worktree: `~/.gdd/worktrees/example-repo/20260610-example-ab-test`
branch: `codex/20260610-example-ab-test`
