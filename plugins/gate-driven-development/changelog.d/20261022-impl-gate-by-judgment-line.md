---
type: minor
---

#### Summary

- impl-gating の review（Step 2〜10）を、gate 単位の全 task が「判定の線の外」と宣言したときだけ外すようにした。線は、block / allow の判定・認可・IAM・権限の付与・Ready・承認の判定・費用の上限で止める判定・入力検証・fail-open の既定のどれかを変えるか（正本: `references/task-breakdown-steps.md` § Judgment Change）
- task-breakdown が task ごとに `- Judgment Change: yes | no` を書く。外すのは、Task Size が `standard` か `quick (standard)` で、`Current Task` の task が 1 つだけで（Gate Batch・並列の batch は外さない。並列の batch は `## Execution Plan` の Mode の行で見分け、`- Mode: sequential` などの決まった形のときだけ逐次と読む）、その task が `- Judgment Change: no` ちょうど 1 本を持ち、`Gate Rounds` の行が無く、gate 単位の差分（`state.md` の `Impl Gate Base` か default branch との merge-base からの変更ファイル）がその task の Files の宣言に収まり、宣言が空でなければ宣言したファイルが差分に出ていて、`Completed Tasks` の task の数が gate 単位の始まりと同じ（`state.md` の `Impl Gate Completed`）ときだけ。欄が無い・値が違う・最初の task より前に行がある・1 本だけの欄が重なるなど読めないときは、今までどおり review を回す
- 外すときも gate は起動し、scope guard（Step 1）・RED Evidence の確認（1d）・完了処理（Step 11）は行う。gate は差分が線に触れる・State Machine Impact block に ADR 起票などがあるときは、欄を `yes` に上げて通常の review に進む
- impl-gating Step 11 は、task を移した後に `Current Task` が空になったとき（gate 単位を終えたとき）に `state.md` の `Impl Gate Base:` に HEAD の sha を、`Impl Gate Completed:` に `Completed Tasks` の task の数を書く。数が違えば（並列の batch の途中など）review を外さない
- 外した task は `Reviewed by: none (Judgment Change: no)` で完了する。completion-check Step 2a の機械検査（`check-completion-mechanical.py`・`check-gate-ledger.sh` の `reviewed-by` 行）は、この行を同じ task に `no` の宣言があるときだけ ok とする。completion-reviewer が、外した task の差分が線に触れていないかを見て、触れていれば再 gate する
- steering write guard は、外して完了した task の宣言か `Reviewed by` の行を落とす tasklist.md の書き込みも止める

#### Added

- `references/task-breakdown-steps.md` § Judgment Change（線の定義・宣言の形・外す条件）
- `skills/gdd-implementation-gating/SKILL.md` Step 1e
- `scripts/impl-gate-context.py` の固定行 `impl-gate-review: skip <task 名>` / `impl-gate-review: run（<理由>）`
- `hooks/scripts/lib/tasklist_parse.py` の `impl_gate_review`・`judgment_change_no` と、`completed_tasks_reviewed_by` の状態 `skipped`
- `agents/gdd-completion-reviewer.md` の観点 11（review を外した task）

#### Changed

- `skills/gdd-task-breakdown/SKILL.md` の Plan Execution Fields に `Judgment Change:` を足した
- `skills/gdd-completion-check/SKILL.md` Step 2a、`references/state-machine.md` の差し戻し理由の表、`references/gate-checklists.md` Checklist E (ii)、`references/subagent-dispatch.md` の State Update Contract、`references/reviewer-selection.md` の非 waivable 上書き条項（review を回す gate での選び方であることを明記）
- `hooks/scripts/lib/steering_size.py` の退避の案内に `Judgment Change` の行を足した
- `tests/checks/skill-body-budget.sh` の references の行数・skill 本文の合計行数・standard の token の上限を、足した分だけ上げた

#### Affected Files

- `references/task-breakdown-steps.md`
- `references/reviewer-selection.md`
- `references/state-machine.md`
- `references/gate-checklists.md`
- `references/subagent-dispatch.md`
- `skills/gdd-implementation-gating/SKILL.md`
- `skills/gdd-task-breakdown/SKILL.md`
- `skills/gdd-completion-check/SKILL.md`
- `agents/gdd-completion-reviewer.md`
- `hooks/scripts/lib/tasklist_parse.py`
- `hooks/scripts/lib/steering_size.py`
- `scripts/impl-gate-context.py`
- `tests/checks/skill-body-budget.sh`

#### User Action Required

- なし。既存の tasklist には欄が無いので、今までどおり全 batch で review を回す

#### Validation / Eval Impact

- 追加 test: `tests/test_judgment_change.py`（外す判定の fail-open 3 ケース、完了の受理、write guard の退行）
- `tests/test_impl_gate_context.py`・`tests/test_check_gate_ledger.py` に入口のテストを足した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `python3 scripts/light-lane-related-tests.py --run . origin/main`
