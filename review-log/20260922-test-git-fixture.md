---
lane: L1
pr: 旧#170
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4b01a502324d7b5bb0853f66fb9292b1b7884db8 | 0 | 0 | 0 | 2026-09-22T20:05+09:00 |
| PR後-1 | user | 2824d706af2aad464eb2be38391aeaa1ed16060a | 0 | 1 | 1 | 2026-09-22T22:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | aggregation-leftover | next-pr | `test_pre_push_gate_contract.py:58` の `_init_repo` は、変換した `test_pre_pr_gate_contract._init_repo` から末尾の `git switch` を除いたものと行単位で同一なのに未変換。PR 本文の限界が挙げる対象外 3 件はいずれも形の違うもので、同型の残りが列挙されていない。近道の巡の ① の blocking でない medium なので `next-pr`。PR 本文の限界と「次の PR」に列挙する |
| F2 | 独立-1 | low | no | self-inflicted | stale-comment | next-pr | `test_root_branch_guard_contract.py:279,283` のコメントが `git branch -M main` 直後を根拠にしているが、変換後は `git init -b main` になり当該コマンドが消える。結論（loose ref）は変わらない。近道の ① の low なので `next-pr` |
| F3 | 独立-1 | low | no | self-inflicted | aggregation-leftover | next-pr | `test_state_field_value_less_line_contract.py:653` の inline 6 行が、変換した `test_task_binding_resolve_security_contract._init_repo` の変換前と同一。限界の列挙が inline 形にも及んでいるのに、この 1 件が挙がっていない。近道の ① の low なので `next-pr`。PR 本文の限界と「次の PR」に列挙する |
| F4 | 独立-1 | low | no | self-inflicted | helper-arg-style | next-pr | `_git_fixture.init_repo` が `init_cmd` に `"git"` を入れてから `[1:]` で捨てており、`_git()` の呼び出し規約と食い違う。近道の ① の low なので `next-pr` |
| F5 | 独立-1 | low | no | self-inflicted | test-power | next-pr | `test_without_branch_the_host_default_is_kept` は両辺ともホストの `init.defaultBranch` に依存するため、`init.defaultBranch=main` の開発機では `-b main` 常時付与への退行を検出できない。CI（ubuntu、既定 `master`）では判別力がある。近道の ① の low なので `next-pr` |
| A1 | 独立-1 | advisory | no | inherited | name-collision | accepted | `test_changelog_fragments.py:139` に別契約の `init_repo` がある（モジュールローカルで今は衝突しない）。将来そのファイルへ共有 import を足すと後勝ちで黙って上書きされる。PR 本文の advisory に書く |
| P1 | PR後-1 | medium | yes | self-inflicted | ci-flake-maintenance-lock | fixed | ユーザーのレビューは採用 finding 0 件で、マージ前確認として `gdd-plugin` の success だけを求めた。その CI が `test_root_branch_guard_real_git.py` の `shutil.copytree(base/".git", ...)` で `.git/objects/maintenance.lock` を掴めずに 2 件落ちた。`init_git_repo` の最終コマンドが `git branch -M main` から `git commit` に変わり、detached な `git maintenance run --auto` との窓が狭まったため（`GIT_TRACE2_EVENT` で子プロセスの起動を確認。本 PR 後に初めて観測で、過去の失敗 run 7 件には無い）。`init_repo` に `git config maintenance.auto false` を足し、contract test で固定した |
| A2 | 独立-1 | advisory | no | self-inflicted | prompt-template | accepted | 独立レビューの prompt の `## PR 本文` 欄に、テンプレート外の `### 検証` 節（実行結果の断定）を入れていた。reviewer は根拠に採用せず独立に確認した。次回以降は目的・変更内容・限界の 3 節だけを貼る。PR 本文の advisory に書く |
