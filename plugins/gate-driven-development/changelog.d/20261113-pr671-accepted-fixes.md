---
type: patch
---

#### Summary

- `references/output-format.md` の `<gdd-stop reason>` の許容値の表と「次にすること」のマップに、`staging-verification-blocked` を足した（hook が認める値は 8 つ）。`references/state-machine.md` は値を並べず、この表を指す。`clarification-needed` の行に、`TaskStop` で待ちから外れる結果（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`）を書いた
- 突き合わせ agent・completion reviewer・human check の `原文:` は、`request.md` の形によらず、`見直し` で始まる assistant の引用を依頼の原文に数えない。hook が写せなかったときの `request.md` の見出しにも、この引用を除くことを書いた。突き合わせ agent の起動の説明に、express から昇格したタスクで回し直すときを足した
- 要件を固める確認で、既存側をユーザーが決めた規則・方針として仮決定するときの「記録の場所」を、repo の `CLAUDE.md`・`AGENTS.md` の `file:line` か、`request.md` に時刻つきで足したユーザーの発言に限った（steering の main が書いたファイル、ユーザーの global の規則、前のタスクの承認は数えない）。requirements の観点の reviewer の範囲の狭めの検査も、この種類で例外を判断する
- requirements-gating の時間の目安（Step 4b）の `要件ゲート再開:` は、事前回答の委任で一括提示の答えを適用したとき、行き先によらず書く（再入しない行き先を含む）

#### Affected Files

- `references/output-format.md`・`references/brainstorming-steps.md`・`references/requirements-gating-steps.md`・`agents/gdd-request-code-crosscheck.md`・`agents/gdd-completion-reviewer.md`・`agents/gdd-planning-reviewer.md`
- `hooks/scripts/lib/request_capture.py`（写せなかったときの見出しの文）・`references/state-machine.md`（許容値は output-format.md を指す）・`references/human-check-template.md`（原文から `見直し` の引用を除く）
- `changelog.d/20261113-accepted-leftovers-batch.md`（`amends:`。見直しの引用・unavailable のときのリスクの段・planning reviewer の検査の広がり・押し返しの文面の指し先・読めない log での書き込み・相談役が動いているターンの語・express からの昇格・faq の書き先を書き足した）
- `tests/test_stop_hook_validate.py`・`tests/test_stop_hook_resumed_agent_wait.py`・`tests/test_wait_watchdog.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `TaskStop` の成功の JSON が JSON でない block の後にある形と、再開した agent で JSON の id が input と違う成功を待ちに残す形のテストを足した。読めない log のテストは root では skip する
