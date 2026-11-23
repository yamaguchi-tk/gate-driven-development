---
type: patch
---

#### Summary

- 軽いレーンの独立レビュー（root `CLAUDE.md` 手順 6）で、reviewer に渡す材料（差分・呼び出し元の候補・PR 本文）を prompt に貼るのをやめ、一時ファイルに書き出して絶対パスで渡す形にした。plugin を開発する側の手順の変更で、利用者の実行時の挙動は変わらない

#### Changed

- 手順 6 の材料の渡し方を、リダイレクトで作ったファイルのパスに変えた。貼る方式では main が差分を出力し直すため、書き写しで行が落ちていた（2026-09-21 実測: 照合できた 38 本のうち 12 本で行が欠け、うち 7 本は変更行〔+/-〕が欠けていた。最大は 1,031 行の差分で変更行 558 行）
- reviewer に、材料を最後まで Read することと、出力の冒頭に読み込んだ行数を申告することを求めた。main は 3 つのファイルの `wc -l` と突き合わせ、1 つでも合わなければ巡を無効にして起動し直す
- 材料が読めない・最後まで読めない・パスの欄が空・欄に本文や `$(` しか無いときは、レビューせずに `blocking: diff 未到達` を返す規定にした（fail-closed）
- 呼び出しテンプレートの欄を、差分の本文と候補の一覧から 3 つのファイルのパスに差し替え、リポジトリ（worktree）の絶対パスの欄を足した

#### Affected Files

- root `CLAUDE.md`（軽いレーンの手順 6）
- `.claude/agents/light-lane-independent-reviewer.md`（守ること・呼び出しテンプレート）
- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 関係するテスト: `test_light_lane_review_routing_contract.py`・`test_independent_review_host_route_contract.py`・`test_always_high_scope_contract.py`・`test_review_log_present.py`・`test_testing_standard_contract.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
