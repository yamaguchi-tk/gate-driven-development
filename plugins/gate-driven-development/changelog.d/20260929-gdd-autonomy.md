---
type: minor
---

#### Summary

作業ツリー直下の `.gdd-config.md` に `GDD Autonomy: internal` の 1 行を書いたプロジェクトでは、GDD が人間の確認で止まる箇所のうち、閉じた一覧に載せたものだけを Opus に判断させて続けるようにした。一覧は、その steering で初めての human check（`worklog.md` に `自律判断: human-check` の行がまだ無く、`state.md` に `Approved Direction` も無いもの。一覧に着いた後は止まるときも、`Approved Direction` の無い human check にユーザー本人が返答したときも行を書く）、`human_recheck_required`、上限に当たったときの方式転換（同じ種類の 2 回目を除く）である。止まる案と止まる場面は一覧より優先し、どれに当たるか判定できないときも止まる。AC を削る・弱める、task を撤回する、中止する、`planning_rework_required` に進む案と、`clarification-needed`・AC の曖昧さ・ユーザー本人の返答を受けた場面・判断役を起動できないときは、今までどおり人間に止まる。main の案と Opus の推奨が食い違ったときだけ、Fable に 1 回（1 steering あたり）アドバイザリとして相談する（Claude Code だけ。Codex・Cursor は `general_heavy_risk` tier で判断し、Fable には相談しない）。自律の承認は `Human Check Status` の evidence を `autonomy:<箇所>` にして人間の承認と区別し、`worklog.md` の `自律判断:` の行に残し、PR 本文の `## 自律で判断した箇所` 節に列挙する。merge・release・本番デプロイなどの承認の境界は変えない。宣言が無いプロジェクトの動きは変わらない。

#### Added

- `references/autonomy.md`：自律モードの宣言・自律で決めてよい停止・判断の手順・限界の正本
- `commands/gdd-dev.md` Instructions 旧#9 に、宣言があれば human check の前に `references/autonomy.md` で判定する 1 行と、旧#10 に、宣言があれば provenance 先行判定の後に `references/autonomy.md` 手順 5 に従う一文
- `references/subagent-dispatch.md` § HITL Pending Hard Invariant に、宣言があればユーザー本人の入力を扱う前に `references/autonomy.md` 手順 5 に従う一文
- `references/post-completion-pr-flow.md` の PR 本文の手順に、`自律判断:` の行を列挙する Autonomy Decisions Check

#### Changed

- references 全体の行予算（`tests/checks/skill-body-budget.sh`）を 11998 から 12032 に上げた（新しい正本の分。既存の親テキストで統合できるものは無かった）。同じ検査の必須ファイルの一覧に `references/autonomy.md` を足した

#### Fixed

- `references/rollback-patterns.md` § Downstream Human Recheck Handoff が、存在しない `references/human-check-template.md` の節を読ませていた。参照を消し、同じ節の出力項目だけに従うようにした

#### Affected Files

- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`

#### User Action Required

- 自律モードを使うプロジェクトでは、ユーザーが作業ツリー直下の `.gdd-config.md` に `GDD Autonomy: internal` の 1 行を、steering を始める前に書く（途中で書くと、宣言より前に差し戻した human check が数えられない）。使わないなら何もしない

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 宣言あり・なし、止まる条件に当たる場面・当たらない場面を手順書だけで判断させ、止まるか・Opus に判断させるかを比べた（PR 本文の Skill RED-GREEN Evidence）
