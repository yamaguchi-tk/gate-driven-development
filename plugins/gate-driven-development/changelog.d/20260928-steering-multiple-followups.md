---
type: patch
---

#### Summary

SessionStart で作業中の steering が複数見つかったときの警告（`[gdd:warning]`）の直し方の案内を、pre-push gate の `steering-multiple` の案内にそろえた。以前は「worktree ごと削除するか、tasklist.md の Next Action=cancelled にする」と案内していた。検出は current worktree の `state.md` しか読まないので tasklist.md を変えても解けず、worktree の削除は作業中の checkout ごと消す。今は「使わない steering は削除せず別の場所へ移す」と案内し、pre-push gate も同じ理由で止まることを添える。

pre-PR gate が steering 2 件以上（作業中が 2 件以上、または作業中が無く done が 2 件以上）で `gh pr create` を止めるときの案内も、「completion-check を通してから PR を作成する」から同じ案内に変えた。作業中が 2 件なら、片方を completion-check で done にしても残りの作業中の steering で同じ gate に止まる。done が 2 件なら、completion-check をやり直しても 2 件のまま。どちらも前の案内では解けなかった。steering が 1 件も解決できないときの案内（completion-check を通してから）は変えていない。`docs/TROUBLESHOOTING.md` § active steering が複数検出されて通知が出る の原因と復帰手順も同じ内容に直した。

#### Changed

- `hooks/scripts/run-session-start-hook.sh`: 複数 steering の警告の案内文
- `hooks/scripts/run-pre-pr-gate-hook.sh`: 複数 steering で止めるときの案内文（止める条件は変えていない）。done の steering が 2 件以上のときも、作業中が 2 件以上のときと同じ案内にする
- `docs/TROUBLESHOOTING.md` § active steering が複数検出されて通知が出る

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`
- `plugins/gate-driven-development/tests/test_steering_terminal_pipe_head_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_steering_terminal_pipe_head_contract.py` に、SessionStart の複数 steering の警告と、pre-PR gate の複数 steering（作業中 2 件・done 2 件）の block の案内、steering が解決できないときの案内が変わらないことを確かめるテストを足した（先に失敗を確認した）
- 同じファイルで、全角の注記を active な steering と並べて `steering-multiple` で判別するテストと、merge gate の照合し直しが対象 PR の steering の証跡で判定する（`approval-missing`）ことを確かめるテストに強めた
- 変更したファイルを参照するテストと `bash plugins/gate-driven-development/tests/validate-plugin.sh`
