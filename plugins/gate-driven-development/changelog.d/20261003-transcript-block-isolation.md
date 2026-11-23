---
type: patch
---

#### Summary

Stop hook が transcript を読むとき、中身の型が変な block（文字列でない `tool_use_id` など）を、行ごとではなく block ごとに読み飛ばすようにした。これまでは同じ record の人間の発話も一緒に捨てたので、その前の `/gdd-dev continue` などの古い継続意図で継続の block が出た。行として読めない行（桁の多い整数、深い入れ子）は、これまでどおりその行だけを読み飛ばす。例外で読み飛ばした block・行の数と最初の例外は `.gdd/hook-errors.log` に記録する（Stop のたびに 1 件。JSON として読めない行は数えない）。直近の人間のターンが peer かを判定できないとき（例外のとき）は、これまでどおり peer と同じく自動継続を抑止し、新たに例外を `.gdd/hook-errors.log` に記録する。stderr の文は「peer であるか、それを判定できないため」にした。post-merge の事前判定が例外になったときも記録する。終わりの `<task-notification>` は、user の record の最後の text block だけでなく、全部の text block から読む。通知のブロックを開始タグから丸ごと本文に引用したときは、それも 1 つの通知として読む（ヘッダの外に id のタグだけを引用したときは終わりにしない）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/references/stop-hook-structured-markers.md`
- `plugins/gate-driven-development/tests/test_stop_hook_validate.py`
- `plugins/gate-driven-development/tests/test_stop_hook_e2e.py`
- `plugins/gate-driven-development/tests/test_stop_hook_stop_reason_unit.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_stop_hook_validate.py` に `TestParseTranscriptBlockIsolation` を足した
- `tests/test_stop_hook_e2e.py` に `test_human_text_with_malformed_sibling_block_does_not_revive_continuation` を足した
- `bash tests/validate-plugin.sh`
