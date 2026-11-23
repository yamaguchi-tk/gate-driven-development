---
type: minor
---

#### Summary

- マージで起動する workflow の一覧を出す `scripts/list-merge-triggered-workflows.py` を足した。`git diff --name-only --no-renames -z <base>...<head>` の変更ファイルと、`<head>`（既定は `HEAD`）の `.github/workflows/*.yml`・`*.yaml` の `on` を突き合わせ、workflow ごとに `起動する`・`起動しうる`・`起動しない` と理由をタブ区切りで出す。引数は `--repo`・`--base`・`--head`・`--default-branch`。マージの後は `--base <merge commit>^1 --head <merge commit>` で、マージ commit の差分を見る
  - `on.push` は filter（branches・branches-ignore・tags・tags-ignore・paths・paths-ignore）で判定する。glob は GitHub Actions の filter pattern に合わせる（`*` は `/` をまたがず `**` はまたぐ、`?`・`+`・`[]`、`!` は順に評価して後勝ち）
  - push 以外の event は、マージで起動しないと分かっているもの（`workflow_dispatch`・`schedule`、`closed` を含まない `pull_request` など）だけを `起動しない` にし、ほか（`workflow_run`・`closed` を含む `pull_request` など）は `起動しうる` にする
  - 判定できない形（読めない YAML、paths と paths-ignore の併用、既定ブランチが分からないときの branches、差分が空、差分が 3,000 ファイルを超えるときの paths など）は `起動しうる` にする。一覧を作れないときは exit 2
- completion-check の Part B の 11 で、毎 Round この一覧を `worklog.md` に写す。script が 0 以外で終わると、一覧ができるまで `done` に進まない
- PR 作成手順の 4 に PR Body Merge-Triggered Workflows Check を足した。PR を作る直前と、PR 作成後の push のたびに一覧を作り直し、PR 本文の影響範囲の節（無ければ `## 影響範囲`）に `起動する`・`起動しうる` の行を書く（0 件なら `マージで起動する workflow: なし`）。script が 0 以外で終わると PR を作らない。一覧にデプロイ系の workflow があれば、マージ後の確認にその run の完了（success）を入れる
- マージの後に確かめる workflow は、マージ commit から作り直した一覧で選ぶ（§ Manual Merge Continuation の 1、`references/post-merge-qa.md` の 3、`references/phase-progression.md` の manual merge continuation）。post-merge-qa の 3 は、宣言した workflow に加えて、一覧のうちデプロイ系の workflow の完了も確かめる。宣言に無い `起動しうる` の workflow の run が 10 分たっても現れなければ、`起動しなかった:` と書いて進む。post-merge-qa の 2 の `起動:` も、マージする head の一覧から書く。マージの後の一覧は `git fetch` の後に作り、script が 0 以外で終わったら止まる
- gdd-pr-review から PR を作るときに適用する PR 本文のチェックに、PR Body Merge-Triggered Workflows Check を足した

#### Affected Files

- `scripts/list-merge-triggered-workflows.py`（新規）
- `tests/test_list_merge_triggered_workflows.py`（新規）
- `tests/checks/lint-scripts-syntax.sh`
- `skills/gdd-completion-check/SKILL.md`
- `references/post-completion-pr-flow.md`
- `references/post-merge-qa.md`
- `references/phase-progression.md`
- `skills/gdd-pr-review/SKILL.md`

#### User Action Required

- なし。`.github/workflows/` が無い repo では一覧が空になり、PR 本文には `マージで起動する workflow: なし` と書く

#### Validation / Eval Impact

- 追加 test: `tests/test_list_merge_triggered_workflows.py`（paths だけ・paths-ignore だけ・否定パターン・`workflow_dispatch` だけ・push 以外の event・`on: push` の短縮形・branches の filter・pattern の `+`・`[]`・`\`・非 ASCII のパス・空の差分・マージ commit の指定・判定できない形）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（`lint-scripts-syntax` の対象に新しい script を足した）
