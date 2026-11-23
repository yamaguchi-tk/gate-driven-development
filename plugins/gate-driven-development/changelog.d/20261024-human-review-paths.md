---
type: minor
---

#### Summary

- 自走上限を `マージまで`・`マージ・デプロイ・QA まで` にしたタスクでも、差分が必ず人が見るファイル（CI の workflow、CODEOWNERS が指すパスなど）に触れたら、GDD は自走でマージせず、マージを 1 問で人に問うようにした

#### Added

- `scripts/list-human-review-files.py --base origin/<既定ブランチ> --head <head>`：差分が必ず人が見るファイルに触れるかを判定する（exit 0 は触れない、1 は触れる、2 は判定できない）。集合は、組み込み（`.github/workflows/**`・`.github/actions/**`・`CODEOWNERS`・`.github/CODEOWNERS`・`docs/CODEOWNERS`・`.gdd-config.md`・`.claude/settings.json`）、既定ブランチの CODEOWNERS のパターン、`.gdd-config.md` の宣言の和である
- `.gdd-config.md` の任意の宣言 `GDD Human Review Paths: <パターン>, ...`：必ず人が見るファイルを repo ごとに足す。パターンは CODEOWNERS と同じ gitignore の書き方で、区切りはカンマか空白（`dir/` は中身に当たる）。宣言が無くても、組み込みの集合と CODEOWNERS で効く

#### Changed

- 自走のマージの条件（`references/post-merge-qa.md` 手順 2）の「差分が `.gdd-config.md` を変えない」を、「上の script が exit 0」に置き換えた。1 か 2 なら、問いの先頭に `必ず人が見るファイル: <n> 件` の行と当たったファイルを並べて問う。本人がマージを承認した後のデプロイの完了確認と QA は、自走上限のとおり続ける
- マージは、自走でも人に問う経路でも、判定に使った PR の head（`gh pr view --json headRefOid`）に固定し、`gh pr merge --match-head-commit <sha>` で行う（判定の後に head が動いたら GitHub が断る）
- `GDD Human Review Paths` は自走を制限する行なので、ほかの宣言と逆に、読めないとき（2 行以上・値の形が違う・コードフェンスの中など）は止める側に倒す（`references/autonomy.md` § 宣言の行の読み方）

#### Affected Files

- `plugins/gate-driven-development/scripts/list-human-review-files.py`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/tests/test_list_human_review_files.py`
- `plugins/gate-driven-development/tests/checks/lint-scripts-syntax.sh`

#### User Action Required

- なし。必ず人が見るファイルを足したい repo は、既定ブランチの `.gdd-config.md` に `GDD Human Review Paths: terraform/**, scripts/deploy-*.sh` のように書く（エージェントは書かない）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_list_human_review_files.py -q`
