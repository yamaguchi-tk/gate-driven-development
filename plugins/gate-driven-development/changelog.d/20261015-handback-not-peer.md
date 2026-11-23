---
type: patch
---

#### Summary

同じ session の subagent が返した行（`[Subagent hand-back]` の完了報告と、同じ session 内の SendMessage）を、別セッションからのメッセージ（peer）と判定しないようにした。host はこの行にも `origin.kind: "peer"` を付け、user 行では本文も `Another Claude session sent a message:` で始まるため、steering write guard が直前の人間の承認を使えずに承認・マージ承認・中止・完了の write を deny していた（実データで 11 件、本物の peer が原因の件は 0）。送り手が同じ session の task であることは `origin.senderTaskId`（空でない文字列）で決め、本文は読まない。その行は peer にも人間の発話にも数えず読み飛ばし、peer の状態も解除しない。`senderTaskId` が無い・空・文字列でない行は、今までどおり peer として止める。

共有の判定（`lib/transcript.py` の `last_user_turn_is_peer`）を直したので、Stop hook と wait watchdog も、hand-back の user 行の直後に検査を飛ばさなくなる。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`（`_is_same_session_origin` を足し、`_queued_line_is_peer` と `last_user_turn_is_peer` の user 行の分岐で使う）
- `plugins/gate-driven-development/tests/test_handback_not_peer.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_handback_not_peer.py`（steering write guard の入口から、hand-back と SendMessage の後でも承認の write が通ること、別セッションの形と `senderTaskId` が読めない行は止めること、本物の peer の後の hand-back で peer の状態が解けないこと、Stop hook の入口から hand-back の後でも watchdog が止めること）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
