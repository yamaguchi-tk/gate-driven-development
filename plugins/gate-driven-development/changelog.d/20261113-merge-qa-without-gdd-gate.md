---
type: breaking
---

#### Summary

- 自走上限 `マージ・デプロイ・QA まで` を、どの repo でも選べるようにした。今までは既定ブランチの `.gdd-config.md` に `GDD Post-PR Autonomy: merge-deploy-qa` と `GDD QA *` の行がある repo でしか選べなかった
- マージしてよいかを止めるのは GitHub（branch protection・ruleset・必須レビュー・CODEOWNERS）に任せる。GDD の側の「必ず人が見るファイル」の判定（`GDD Human Review Paths`・組み込みの集合・CODEOWNERS）と、差分が `GDD QA Deploy Paths` に収まる条件を外した
- GitHub にマージを断られたら、`--admin`・`--auto`・`gh api` でのマージ・既定ブランチへの直接 push で回避せず、理由と人がマージするときのコマンドを報告して止まる
- QA の環境・デプロイの workflow・書き込み先は、repo の宣言の代わりに、自走上限を選ぶ human check に並べて本人が承認したもの（`worklog.md` の `QA の範囲:` の 3 行）にした。QA 計画はその中だけで書き、範囲の外が要るとき・値が `不明` のときは、自走でマージせずに 1 問で問う

#### Breaking Contract Changes

- `.gdd-config.md` の `GDD Post-PR Autonomy`・`GDD QA *`・`GDD Human Review Paths` の行を読まなくなった。宣言で選べるようにしていた `マージ・デプロイ・QA まで` はどの repo でも選べ、QA の範囲はタスクごとの human check で決める。宣言で人に回していたファイルは、GitHub の必須レビューが無ければ自走でマージされる

#### Removed

- `scripts/list-human-review-files.py` とそのテスト
- `.gdd-config.md` の `GDD Post-PR Autonomy`・`GDD QA Environment`・`GDD QA Deploy Paths`・`GDD QA Deploy Workflows`・`GDD QA Write Targets`・`GDD Human Review Paths` の行の読み取り

#### Affected Files

- `references/post-merge-qa.md`・`references/human-check-template.md`・`references/operation-levels.md`・`references/autonomy.md`・`agents/gdd-qa-runner.md`・`tests/checks/lint-scripts-syntax.sh`

#### User Action Required

- `.gdd-config.md` に上の行を書いていた repo は、行を消してよい（残っていても読まない）。QA の環境と書き込み先は、タスクごとの human check で選ぶ
- 人のレビューを必ず通したい repo は、branch protection か ruleset で必須レビューを設定する。保護の無い repo では、workflow や `.claude/settings.json` を変える PR も、自走上限を選べば自走でマージされる
- global の `CLAUDE.md` などに「`.gdd-config.md` が宣言した環境」「`GDD QA Write Targets`」を前提にした規則があれば、「human check で承認した QA の範囲」に読み替える

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
