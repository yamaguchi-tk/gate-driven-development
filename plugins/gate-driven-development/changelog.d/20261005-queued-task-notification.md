---
type: patch
---

#### Summary

Stop hook が background の Agent・Bash の完了を判定するときに、main が動いている間に届いた完了通知も読むようにした。この通知は transcript に `type: "user"` の行として残らず、`queue-operation` の `remove` の content か、`attachment`（type: `queued_command`）の prompt にだけ残ることがある。これまではその通知を読まず、終わった dispatch を実行中とみなしていた。そのため wait watchdog が、終わった reviewer・gate-runner に期限切れ・未武装の block を出したり、loop state を消す停止を押し返したりしていた。`queue-operation` の `enqueue` だけの通知は配達待ちなので、今までどおり実行中として扱う。本文が content block の list のときも、type:user の行と同じく text block と素の文字列を読む。queued の行は last_user_text に使わない。

steering write guard の peer 境界（peer のメッセージの直後の承認・中止・完了・`Origin Session` の書き込みを止める）は、turn の途中に queued の形（attachment の queued_command）だけで届いた peer の文も、peer として扱うようにした。peer かどうかは host が書く `attachment.origin.kind` で決め、`human`・`task-notification`・`auto-continuation` と origin の無い行だけを peer でないとし、ほかの値は peer として止める。queued の人間の文は、これまでどおり peer 状態を解除しない。Stop hook と wait watchdog の peer 判定は変えていない。

この変更で、次の場面では新しく block が出る。queued の形だけで完了通知が届いた dispatch を待っていた Stop は、これまで in-flight として黙って通していたが、継続の block を出すようになる。期限 timer の完了が queued の形で届いた後は、まだ動いている reviewer・gate-runner に「期限 timer が無い」の block を出すようになる。turn の途中に queued の形で届いた自分の subagent の hand-back（`attachment.origin.kind` が `peer`）の後も、人間が発話するまで、steering write guard が承認・完了・中止・`Origin Session` の書き込みを止める（type:user の形で届く hand-back の後は今までも止めていた）。Stop hook 側は queued の peer を読まないので、継続の block と食い違い、連続 block の上限まで進みうる（直近 30 日の transcript では、該当する書き込みは 0 件）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/lib/constants.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/references/stop-hook-structured-markers.md`
- `plugins/gate-driven-development/tests/test_queued_task_notification.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_queued_task_notification.py` を足した（Stop hook の入口から、remove・enqueue+remove・attachment と、その本文が list の形で完了とすること、enqueue だけでは押し返し、上限を過ぎた reviewer に block すること、変な形の行で落ちないこと、queued の行で last_user_text と Stop hook 側の peer 判定が変わらないこと、validate-steering-write.py の入口から queued の peer の後の承認を止め、判定できない origin を peer に倒すこと）
- `bash tests/validate-plugin.sh`
