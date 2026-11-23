---
type: patch
---

#### Summary

review-followup の nudge hook は、push 先の branch に UTF-8 で書けない文字（`\ud800` のような lone surrogate）があっても、解析結果を最後まで書き出し、gh に PR の有無を問い合わせるようにした。今までは、書き出しの途中で例外になり、push 先の root が出ないまま何もせずに抜けていた。branch 名は `\uXXXX` に置き換わるので実在の branch には当たらず、提案の有無は変わらない（gh への問い合わせが 1 回増え、`skipped(no-pr)` として記録される）。書き出しは merge gate・pre-push gate と同じ形にした（surrogateescape で符号化し、それでも書けない行は行全体を backslashreplace で書く）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-review-followup-nudge-hook.sh`

#### User Action Required

- なし

#### Validation / Eval Impact

- `plugins/gate-driven-development/tests/test_review_followup_nudge_hook_emit_encoding.py` を足した
