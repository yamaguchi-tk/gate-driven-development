---
type: patch
---

#### Summary

steering write guard の `completed_reviewed_by`（完了タスクの `Reviewed by:` を落とす `tasklist.md` の書き込み）が、次の書き込みを通していたのを止めるようにした。

- `## Current Task`・`## Pending Tasks` に同じ名前の別のタスクがあるときに、`## Completed Tasks` に残したまま `Reviewed by:` の行を消す・`gdd-implementation-reviewer` を消す書き込み（同じ書き込みで、同名の ok でない完了タスクを消す形を除く）
- 書き込みの前から閉じていない fence があるときに、その先の完了タスクの `Reviewed by:` を落とす書き込み（閉じていない fence の先も、前と後の両方で構造として読む）
- 空の `new_string` の Edit で、`old_string` と改行が続く箇所と続かない箇所が混ざるとき（replace_all や、重なる `old_string`）。Claude Code の Edit と同じく、`old_string` と改行が 1 か所でも続けばそちらだけを置換の対象として投影する

閉じていない fence が 10 本を超える `tasklist.md` への書き込みは、判定できないとして止める（3 回目で降格する）。あわせて、deny 文言の、完了タスクを意図して消す例に gdd-task-breakdown の作り直しを足した。3 回連続の deny で降格したときの警告文は、「以後は止めない」から「この 1 回だけ通し、回数を 0 に戻すので、同じ違反の次の書き込みは再び止める」に直した（実装は前から後者）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/tasklist_parse.py`
- `plugins/gate-driven-development/hooks/scripts/lib/reviewed_by_guard.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/tests/test_completed_tasks_reviewed_by.py`
- `plugins/gate-driven-development/tests/test_completed_reviewed_by_write_guard.py`
- `plugins/gate-driven-development/tests/test_reviewed_by_guard_edited_text.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_completed_tasks_reviewed_by.py` に、同名の open タスク・同名タスクの件数・書き込みの前から閉じていない fence の 9 本を足した
- `tests/test_reviewed_by_guard_edited_text.py` を足した（Edit の投影を入力の列挙で確かめる）
- `tests/test_completed_reviewed_by_write_guard.py` に、UTF-8 で読めない `tasklist.md` と、閉じていない fence が上限を超える `tasklist.md` が止まる 2 本を足し、3 件を一度に落とす書き込みの降格を `HUMAN REVIEW REQUIRED` で確かめるようにした
