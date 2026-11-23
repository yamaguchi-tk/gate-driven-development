---
type: patch
---

#### Summary

- 期限 watchdog の block の文面は、`TaskStop` が待ちから外れない結果で返ったときの出口を、期限切れの dispatch がいくつあっても 1 回だけ案内する。案内には、`clarification-needed` の停止の書式の在りか（`references/stop-hook-structured-markers.md`）を足した
- `clarification-needed` の用途を定める `references/state-machine.md` に、background の dispatch への `TaskStop` が待ちから外れない結果（拒否など）で返ったときの受け渡しを足した。`scripts/setup-gdd-loop.sh` の停止の一覧と `blocked` を使う場面、`references/output-format.md` の `clarification-needed` の行に、そのときは `clarification-needed` を使うことを足した。`commands/gdd-dev.md` の `clarification-needed` の例外は、`references/state-machine.md` の用途を指す形にした
- `references/subagent-dispatch.md` の再開の手順の条件を「完了通知も、host が動いていないと答えた `TaskStop` の結果も無い dispatch」にし、押し返しを飛ばす条件の在りかを添えた。`references/human-check-template.md` の、相談役の `TaskStop` が待ちから外れない結果（拒否など）で返ったときは、そのまま返事を扱い、loop state を消す停止で止まるときだけ `clarification-needed` にすることを書いた

#### Affected Files

- `hooks/scripts/lib/wait_watchdog.py`（押し返しの文面）・`hooks/scripts/lib/transcript.py`（コメント）
- `references/subagent-dispatch.md`・`references/state-machine.md`・`references/human-check-template.md`・`references/output-format.md`・`commands/gdd-dev.md`・`scripts/setup-gdd-loop.sh`
- `tests/test_wait_watchdog.py`・`tests/test_stop_hook_validate.py`・`tests/test_stop_hook_resumed_agent_wait.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_wait_watchdog.py` に、期限切れが複数のときの出口の案内の回数と、未武装だけのときに案内しないことのテストを足した
- `tests/test_stop_hook_validate.py` の入口のテストで、拒否の後の `clarification-needed` の停止が押し返されずに通り、loop state が残ることを固定した。`tests/test_wait_watchdog.py` で、loop state を消す停止の押し返しの文面に出口の案内があることを確かめる
