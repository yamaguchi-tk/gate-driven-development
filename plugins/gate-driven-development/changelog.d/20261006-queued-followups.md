---
type: patch
---

#### Summary

Stop hook が、main が動いている間に届いた入力（`queue-operation` の `remove` の content と、`attachment`〔type: `queued_command`〕の prompt）の本文が content block の list のとき、素の文字列と text block だけを読むようにした。これまでは tool_result block も読んでいたので、その本文だけで background の dispatch を終わりにしたり、Stop hook が停止の目印を探す直前の tool_result の本文を書き換えたりしていた。type:user の行の読み方は変えていない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/tests/test_queued_task_notification.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_queued_task_notification.py` に足した（Stop hook の入口から、queued の本文の tool_result block で上限を過ぎた reviewer を終わりにしないこと、`<gdd-stop>` 入りの tool_result が queued の本文にあっても tool_result の欄が変わらないこと、形の崩れた要素で落ちないこと、Stop hook が queued の peer の行で watchdog を飛ばさないこと）
- `bash tests/validate-plugin.sh`
