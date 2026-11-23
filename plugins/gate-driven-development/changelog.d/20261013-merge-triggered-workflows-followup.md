---
type: minor
---

#### Summary

- `scripts/list-merge-triggered-workflows.py` に `--merge-with <ref>` を足した。マージの結果の workflow をファイルごとに選んで読む（PR 側だけが変えたものは `--head`、ほかは `<ref>` から。両方が変えたものは `起動しうる`、どちらかが消したものは出さない）。既定ブランチに後から足された workflow も一覧に出る
- `issues` は `types` が無いか `closed` を含むと `起動しうる` にした（PR 本文の `Closes #<n>` で、マージが issue を閉じる）。`merge_group` も `起動しうる` にした。`types` が空の list のときは `起動しうる`（判定できない形）にした
- パス・repo のパス・既定ブランチ名が UTF-8 でなくても、出力で落ちないようにした（パスは元の bytes のまま書く）
- PR 作成前の一覧（completion-check の 11、PR Body Merge-Triggered Workflows Check）と `references/post-merge-qa.md` の 2 の `起動:` は、`git fetch` の後に `--merge-with origin/<既定ブランチ>` で作る
- § Manual Merge Continuation の 1 を次のようにした。旧#450 の断片の「マージの後は `--base <merge commit>^1`」と「マージ後の一覧で script が 0 以外で終わったら止まる」は、ここで置き換える
  - マージ後の一覧の base（`<push の前>`）は、merge commit なら `<merge commit>^1`。親が 1 つで PR の commit が N 個（N≥2）なら、author の日時が PR の commit と順に一致すれば rebase として `<merge commit>~N`、そうでなければ squash として `^1`。`references/post-merge-qa.md` の 3 と 5（revert の仕方）も同じ決め方を使う
  - run は、理由が push の行ではマージ commit で、ほかの行（`pull_request` の closed など）では `--created ">=<mergedAt>"` で探す。出現は `scripts/wait-until.py --timeout 540 --check-timeout 50` を前面で待つ。`起動しうる` の行は現れなければ `起動しなかった:` と書いて進み、`起動する` の行は現れなければ止まる
  - script が 0 以外で終わったら止まらずに、マージ後に作られた run を監視する。gh も失敗したら `マージ後の確認: 未了（gh が失敗。出力: …）` と報告して止まる
- gdd-pr-review-followup の push の後に、PR 本文の影響範囲の節を作り直す
- gdd-using-git-worktrees の Merge Report Cleanup Trigger は、確かめる workflow と「対象外」を Manual Merge Continuation の 1 の一覧（作れなければ監視した run）で決める
- gdd-pr-review から PR を作るときの PR 本文のチェックに Advisory Findings Check を足した

#### Affected Files

- `scripts/list-merge-triggered-workflows.py`
- `tests/test_list_merge_triggered_workflows.py`
- `references/post-completion-pr-flow.md`
- `references/post-merge-qa.md`
- `skills/gdd-completion-check/SKILL.md`
- `skills/gdd-pr-review/SKILL.md`
- `skills/gdd-pr-review-followup/SKILL.md`
- `skills/gdd-using-git-worktrees/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 追加 test: `tests/test_list_merge_triggered_workflows.py` の `FollowupTest`（issues・merge_group・空の types、値の途中の引用符 2 つ、3,000 超の paths-ignore、既定ブランチ不明の branches-ignore、UTF-8 でないパス）と `MergeWithTest`（既定ブランチに足された workflow、片側だけ・両側が変えた workflow、消した workflow、解決できない ref）
