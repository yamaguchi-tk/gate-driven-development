---
lane: L1
pr: 101
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| codex-1 | Codex adversarial-review（codex-companion 1.0.4, --base origin/main --scope branch, 観点: 配線） | 508b4ed | 0 | 2 | 0 | 2026-09-17T15:30+09:00 |
| 独立-1 | general-purpose subagent (model: opus, read-only, diff-only, 経緯非共有; independent-review.md (a)〜(h) 込み) | 077621e | 0 | 0 | 0 | 2026-09-17T16:00+09:00 |
| PR後-1 | GitHub PR 旧#101 レビューコメント（yamaguchi-tk、採用 1 件・不採用 5 件） | 5297069 | 0 | 1 | 0 | 2026-09-17T18:00+09:00 |
| 独立-2 | general-purpose subagent (model: opus, read-only, 077621e..HEAD の差分と影響先, 経緯非共有; independent-review.md (a)〜(h) 込み) | 96a88b6 | 0 | 0 | 0 | 2026-09-17T18:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | codex-1 | medium | no | inherited | candidate-cap-duplication | fixed | ~/.gdd/worktrees/<repo>/<task> が git worktree list と置き場の両方から候補 root に入り、同じ steering が二重に数えられて 5 件の枠を消費し、置き場にしか無い候補を隠していた |
| F2 | codex-1 | medium | no | inherited | worktree-base-resolution | deferred | .gdd-config.md の Worktree Base: で設定した置き場を SessionStart が探索しない（変更前から固定 2 か所のみ。hook 側に Worktree Base の resolver が無いため後続課題） |
| F3 | 独立-1 | low | no | self-inflicted | shadow-base-depth | deferred | 置き場の探索が <base>/<task> の 1 階層固定のため、git worktree list に未登録で 2 階層以上深い worktree（branch 名のスラッシュ等）を拾わなくなった（実測では ~/.gdd/worktrees 配下 249 件すべてが 1 階層） |
| F4 | 独立-1 | low | no | inherited | shadow-symlink-base | deferred | 置き場や .steering 自体が symlink だと BSD find が -H なしで辿らず候補を拾わない（lib/detect-steering.sh も同じ書き方で対称） |
| F5 | PR後-1 | medium | no | inherited | shadow-current-wt-leak | fixed | 置き場（~/.gdd/worktrees/<repo>/<task>）の task 列挙が git worktree list 側と違い現 worktree を除かず、GDD_STEERING_STATUS=none（stale brainstorming 等）と重なると自分の steering を outside this workspace と案内していた。両側を pwd -P で比較して除外 |
| F6 | 独立-2 | advisory | no | self-inflicted | shadow-current-wt-leak | accepted | git worktree list 側の物理パス比較は、git が list/show-toplevel とも実パスを返すため実質挙動を変えず、テストでも固定されていない（防御的な対称化として受け入れ） |
