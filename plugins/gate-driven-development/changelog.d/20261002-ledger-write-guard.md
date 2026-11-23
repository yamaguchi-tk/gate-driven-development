---
type: minor
---

#### Summary

steering write guard（PreToolUse）が、完了タスクの `Reviewed by:` を落とす `tasklist.md` の書き込みを止めるようにした。`Reviewed by:` は completion-check の Step 2a だけが読み、それまでの hook は読まなかったので、要約や worklog への移動で落ちても、completion-check で差し戻されるまで気づけなかった（2026-10-01 の S-0）。あわせて、サイズ上限で worklog へ移すときの「戻す」規則を、移したことで直った行には戻させない形にした。

#### Added

- steering write guard の deny category `completed_reviewed_by`。書き込みの前に `## Completed Tasks` で `Reviewed by:`（`gdd-implementation-reviewer` を含む）がそろっていたタスクが、書き込みの後に次のどれかになると止める
  - `Reviewed by:` の行が無くなる、または `gdd-implementation-reviewer` が無くなる
  - `## Completed Tasks` にも `## Current Task`・`## Pending Tasks` にもタスクとして無くなる（ブロックを丸ごと消す、要約で見出しの形が崩れる、節の見出しを変える、別の節へ移す）。同じ名前のタスクは件数で比べる
  - Edit の `old_string` がファイルに無く、書き込みの後を判定できない
- Edit は、Claude Code の Edit と同じく、空の `new_string` が続く改行ごと消すものとして判定する（`replace_all` では、ツールの結果と違うことがある）
- 止めないもの: `## Current Task` か `## Pending Tasks` へ移したタスク（再オープン）、書き込みの前から欠けていたタスク、新しいファイル、書き込み後の全文を投影できない `ApplyPatch`。書き込みの前のファイルを読めないなど判定中の例外は止める
- 完了タスクを意図して消す・分け直すとき（gdd-task-breakdown の作り直し、refactor の abort など）は、先に `## Pending Tasks` へ移してから消すよう deny 文言で案内する
- 連続 3 回の deny で警告付きの allow に降格する（既存の escape hatch）。落とすタスクが何件でも、書き込み 1 回で 1 回と数える。この検査で止めない書き込みを挟むと回数は戻る

#### Changed

- サイズ上限の deny 文言（`SIZE_DENY_SUFFIX`）と `references/state-field-tiers.md` の戻す規則を「移す前の ok の行が移した後に無いか、移した後にだけ missing / invalid / n/a の行が現れたら戻す」にした。移したことで直った行（前にある古い field の行、閉じていない fence）には戻させない

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/hooks/scripts/lib/tasklist_parse.py`
- `plugins/gate-driven-development/hooks/scripts/lib/reviewed_by_guard.py`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/steering_size.py`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/tests/test_completed_reviewed_by_write_guard.py`
- `plugins/gate-driven-development/tests/test_completed_tasks_reviewed_by.py`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`

#### User Action Required

- なし。完了タスクを再オープンするときは、`Reviewed by:` をその場で書き換えず、タスクを `## Current Task` か `## Pending Tasks` へ移す

#### Validation / Eval Impact

- `tests/test_completed_reviewed_by_write_guard.py` を足した。hook の入口（`run-steering-write-hook.sh`）で、要約の Write・`Reviewed by` 行だけを消す Edit・ブロックを丸ごと消す Edit・別の節へ移す Write・行をつなげる Edit・`old_string` が無い Edit が止まること、`Route In Progress` の値で検査を外さないこと、1 回の書き込みで 3 件落としても初回で降格しないこと、止めない書き込みを挟むと回数が戻ること、再オープンの MultiEdit・2 回の書き込みでの再オープン・詳細の行を消す Edit・新しいファイル・ApplyPatch が通ること、書き込みの前を読めないと止まること、3 回目の deny が降格することを確かめる
- `tests/test_completed_tasks_reviewed_by.py` に `reviewed_by_regressions` のテストを足した
