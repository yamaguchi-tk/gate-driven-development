---
type: minor
---

#### Summary

- requirements.md の AC ごとに `根拠:`（AC が前提にする既存のコード・データの事実を書く前に読むか測った `file:line`・コマンドと値、または `未測（理由）`・`なし（理由）`）と `計測:`（何を・どの母集団で・どの値なら合格か）を、承認ポイントの項目（方向性を除く）ごとに `根拠:` を書く形にした。テンプレートに欄を足し、brainstorming の手順 9 の「確認済み（ファイル名:行番号）」をこの欄に寄せた
- `scripts/lint-plan-consistency.py` の `--entry` に `requirements`（requirements の初回）を足し、`--entry` を常に要るものにした（無いと exit 2）。design の起動の値は `design` にし、前の値 `other` は受け付けない（exit 2）。`requirements` と `requirements-reentry` のとき、AC（定義行から次の AC の定義行か見出しまで）と `### 承認ポイント` の番号つき項目（次の項目か見出しまで）に欄が無ければ ERROR にする。AC の定義が 0 件のとき、`### 承認ポイント`（`（…）` の付記は可）の節か番号つき項目（`3a.`・`3-1.` も 1 項目）が無いときも ERROR にする（承認ポイントを Human Check Questions の参照だけにしない）。欄は箇条の先頭か ` / ` の後ろに書いたものだけを数え（`判断根拠:` などは数えない）、値は読まない。再入の処置の欄も同じ位置で数える
- requirements の reviewer は AC と承認ポイントの `根拠:` が指す場所を読み、事実が違えば blocking にする。欄の書き方の浅さは blocking にしない。1 枚の AC 表は `根拠:`・`計測:` を含めて写す
- express（`## Acceptance Criteria`）と design の起動は検査しない

#### Changed

- `scripts/lint-plan-consistency.py`
- `references/requirements-template.md`（§ 精度の第一原則、§ Summary Brief の承認ポイント、§ requirements.md セクション一覧 の受入条件。token の予算に収めるため、同じファイルの説明文をいくつか縮めた）
- `references/brainstorming-steps.md`（9 の外部依存コンポーネントの実動作調査）
- `references/requirements-gating-steps.md`（§ 精度の第一原則）
- `references/subagent-dispatch.md`（§ Reviewer Input and Time Budget）
- `agents/gdd-planning-reviewer.md`（Blocking の接地条件）

#### Added

- `tests/test_lint_plan_consistency_ac_fields.py`

#### Affected Files

- `scripts/lint-plan-consistency.py`
- `references/requirements-template.md`
- `references/brainstorming-steps.md`
- `references/requirements-gating-steps.md`
- `references/subagent-dispatch.md`
- `agents/gdd-planning-reviewer.md`
- `tests/checks/lint-scripts-functional.sh`

#### User Action Required

- requirements・design の reviewer を起動する前の lint の呼び出しに、`--entry requirements`（requirements の初回）・`requirements-reentry`（再入）・`design`（design）のどれかを必ず付ける
- requirements gate の途中にあるタスクは、次の起動の前に AC と承認ポイントの項目に欄を書き足す（値が分からなければ `未測（理由）`）。承認ポイントを Human Check Questions の参照だけにしているなら、項目を承認ポイントに移す。再入の処置で `根拠:`・`伝播:` を `（根拠: …）` のように書いているなら ` / 根拠: …` の形に直す。この書き足しは再入の「変えた節」に数えない

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_lint_plan_consistency_ac_fields.py plugins/gate-driven-development/tests/test_lint_plan_consistency.py plugins/gate-driven-development/tests/test_lint_plan_consistency_treatment_fields.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
