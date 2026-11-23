## Post-Merge Continuation

PR merge 後の後続作業として扱います。まず read-only verification で PR merge commit、default branch の最新 commit、CI / test の状態を確認します。その後、後続に必要な判断を worktree 外へ persistence し、旧 worktree の cleanup 可否を診断します。最後に latest default branch から new worktree を作って次フェーズを開始します。

標準順序は **read-only verification → persistence → cleanup → new worktree** です。

### Steering Retention

`.steering/<task>/` は raw task steering であり、active branch / active worktree 内だけで使う **branch-only steering** です。main には raw task `.steering/<task>/` を含めないため、PR / main の commit 対象にしない。

作業中の task branch では、別マシン・別ホスト・別人への引き継ぎが必要な場合だけ raw task `.steering/<task>/` を一時 commit / push してよい。ただし raw steering は branch 履歴に残るため、push 前に機密情報チェックを通し、PR 作成前に重要判断を蒸留し、tracked raw task steering は `git rm -r .steering/<task>/` などで除去する。PR / main の diff は raw task steering net-zero にする。raw steering を一時 push した branch は squash merge と merge 後 branch delete を前提にする。

後続に残す判断は raw task steering 全量ではなく、`docs/adr/` への Distill to ADR、PR body、CI / test evidence、または採用済みの repo-level learned-patterns に蒸留します。

repo-level learned-patterns は raw task steering ではない。`docs/learned-patterns.md` を更新してよいかの採用済み判定は、`origin/<default-branch>` で tracked されていること、または `.gdd-config.md` / repo docs に learned-patterns の保存先が明記されていることです。採用済みでない repo では、新規に `docs/learned-patterns.md` を作らない。判断は `docs/adr/` または repo 既定の学習ファイルへ回します。

### Cleanup

cleanup 前に dirty diff、未 push commit、root duplicate steering、ownership、Continuation Registry / ADR の保存先を確認します。cleanup が unsafe な場合、旧 worktree は保持し、削除しません。その場合でも後続実装は旧 worktree を実装場所にせず、latest default branch から作った新しい worktree で進めます。

### Next Action

1. read-only verification を実行する
2. ADR / Continuation Registry / 採用済み repo-level learned-patterns へ persistence する
3. cleanup 可否を診断する
4. cleanup が safe なら旧 worktree を整理し、unsafe なら保持する
5. latest default branch から新しい worktree を作り、次フェーズの GDD artifact を作成する
