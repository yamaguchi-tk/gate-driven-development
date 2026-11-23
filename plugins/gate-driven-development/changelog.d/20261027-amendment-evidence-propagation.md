---
type: minor
---

#### Summary

- requirements の再入の前に書く `reviews.md` の `処置:` を、`- 処置:` の見出しの下の 1 件 1 行の項目にし、1 件ごとに `根拠:`（処置の文が新しく書く事実を確かめた `file:line` か、コマンドと値か、`未測（理由）`）と `伝播:`（処置で変えた語を requirements.md・design.md に grep して直した節か、`なし`）の欄を持つ形にした。書き方は `gdd-requirements-amendment` の § レビュー指摘の処置に足した。`未測` にした事実は Honest Limitations か Human Check Questions に出す
- `scripts/lint-plan-consistency.py` に `--entry requirements-reentry` を足した（`--entry` の値の一覧と、無いときの扱いは `20261027-requirements-fact-evidence.md` の断片のとおり）。`requirements-reentry` のときは、reviews.md の最新 Round に処置が無い・見出しが `- 処置:`（`（注記）` 可）の形でない・`処置` で始まる別の行がある・項目が 1 件 1 行の形でない・処置の見出しの後ろ（ファイルの終わりまで。fence の中も）に処置の項目でない行がある・欄が無い（値は解析しない）・reviews.md を読めないなら ERROR にする。ほかの値は処置を見ない。位置引数で呼んだときも、requirements.md と同じディレクトリの reviews.md を読む
- requirements の再入の 1 枚に処置の `根拠:` と `伝播:` を写し、planning reviewer は再入で `根拠:` の場所を読んで処置の文と合うかを確かめる。`伝播:` に挙げた節は再入の「変えた節」に含む
- design の再入の処置は検査しない

#### Changed

- `scripts/lint-plan-consistency.py`
- `skills/gdd-requirements-amendment/SKILL.md`
- `references/requirements-gating-steps.md`（§ reviews.md の形式、§ レビューループの契約 3）
- `references/subagent-dispatch.md`（§ Reviewer Input and Time Budget）
- `agents/gdd-planning-reviewer.md`（再入で読む範囲）

#### Added

- `tests/test_lint_plan_consistency_treatment_fields.py`

#### Affected Files

- `scripts/lint-plan-consistency.py`
- `skills/gdd-requirements-amendment/SKILL.md`
- `references/requirements-gating-steps.md`
- `references/subagent-dispatch.md`
- `agents/gdd-planning-reviewer.md`

#### User Action Required

- requirements・design の reviewer を起動する前の lint の呼び出しに `--entry` を付ける（値は `20261027-requirements-fact-evidence.md` の断片のとおり）
- 進行中のタスクで、requirements の再入の前に最新 Round の `処置:` が前の形なら、1 件 1 行にして `根拠:` と `伝播:` を足し、処置より後ろの行を処置の前か worklog.md に移してから reviewer を起動する

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_lint_plan_consistency_treatment_fields.py plugins/gate-driven-development/tests/test_lint_plan_consistency.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
