---
type: patch
---

#### Summary

SessionStart hook の `[gdd:shadow-marker]` が、各 worktree の中にあるテスト用 fixture（`tests/fixtures/e2e-replay/**/.steering/*/state.md`）を「同一リポジトリの GDD steering 候補」として拾っていた。候補の root ごとに `find "$root" -path '*/.steering/*/state.md'` を再帰で実行していたためである。その結果、このリポジトリのすべてのセッションに「GDD を primary に」「`/gdd-dev resume`」という誤った案内が注入されていた。さらに、候補の上限 5 件が fixture で埋まり、本物の放置 steering が表示されていなかった。探索範囲を、steering を実際に置く場所に限定した。

#### Fixed

- `detect_shadow_gdd_markers` の探索を、worktree root 直下の `.steering/<id>/state.md` に限定した。深さは、同じ入力を読む `lib/detect-steering.sh`・pre-PR gate・merge gate の `find "<wt>/.steering" -mindepth 2 -maxdepth 2 -name state.md` に揃えた
- worktree の置き場（`~/.gdd/worktrees/<repo>` と `<current>/.worktrees`）では、直下の各 task dir を worktree root として扱う。受理するのは `<base>/<task>/.steering/<id>/state.md` の形だけである
- `~/.gdd/worktrees/<repo>/<task>` は `git worktree list` にも出るため、同じ steering が二重に数えられ、5 件の枠を消費していた。候補の steering dir を物理パスで重複除去してから上限を数えるようにした
- 置き場の task 列挙が、現 worktree 自身（`~/.gdd/worktrees/<repo>/<task>` から起動したセッション）を候補 root に戻し、自分の steering を「outside this workspace」と案内していた（`GDD_STEERING_STATUS=none` になる stale brainstorming 等と重なったときだけ。変更前の再帰 find でも起き得た）。`git worktree list` 側と置き場側の両方で、現 worktree を物理パス（`pwd -P`）で比較して除くようにした
- 候補の root が 0 件のとき（他の worktree も置き場も無いとき）、bash 3.2 の `set -u` で空配列の展開が失敗しないようにした（今回の変更で置き場の root を無条件に足さなくなり、この経路が生じたため）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/tests/test_session_start_shadow_marker_scope.py`（新規）

#### User Action Required

- なし

#### Validation / Eval Impact

- 新規 contract test: `tests/test_session_start_shadow_marker_scope.py`（入口は SessionStart hook の実行。fixture だけがある worktree では警告を出さない／worktree root 直下と 2 種の置き場にある本物の非終端 steering は警告に出す／fixture が 6 件あっても本物の候補が隠れない／`git worktree list` にも出る置き場の task は 1 回だけ数える／置き場にある現 worktree 自身の steering は外部候補に出さず、他の候補は出す／終端の steering は従来どおり除外する）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
