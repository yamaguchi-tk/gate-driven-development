---
type: patch
---

#### Summary

background の subagent が自分の background の処理を残したまま返ったときの完了通知（`<status>completed</status>` に「This agent stopped with background work of its own still running」の `<note>` が付いたもの）を、dispatch の終わりに数えないようにした。この通知は途中のもので、処理が終わると同じ task-id でもう一度通知が来る。これまでは途中の通知で終わりとみなしていたため、担当役を待っているだけの main に Stop hook が `/gdd-dev` の継続を押し返し続け、期限の見張り（wait watchdog）と、loop state を消す停止の押し返しも外れていた。push 前のレビューの確認でも、途中の通知しか来ていない reviewer を終わったものとして扱っていた。

#### Changed

- 自分の reviewer を待っている `gdd-formal-gate-runner` にも、期限の見張りの上限（起動から 60 分）が当たるようになる。これまでは、reviewer を待つ間に届く途中の通知で終わりとみなし、上限を測っていなかった。60 分を超えた gate-runner は `TaskStop` させられ、`references/subagent-dispatch.md` § Reviewer Input and Time Budget の「超過・無応答のとき」の扱いになる。requirements は `判定: timeout` の Round として人間に一括提示し、design・implementation・completion は Round を進めず `blocked` で人間に渡す（completion は Next Action を変えず、completion review が成立していないことを停止理由として表示する）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`（`_ended_notifications`）
- `plugins/gate-driven-development/hooks/scripts/lib/background_dispatch_gate.py`（deny の案内文）
- `plugins/gate-driven-development/references/subagent-dispatch.md`（§ Typed Agent Resolution の手順 2、§ Reviewer Input and Time Budget）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_interim_task_notification.py`（途中の通知・後の終わりの通知・本文の引用・閉じタグの欠け・push 前のレビュー・Stop hook の入口から）
