---
type: patch
---

#### Summary

hook の steering 検出で、pipe の注記がついた state field の値（`- Next Action: done | evidence: x` など）を、先頭セグメントで比べるようにした。state field の文法（`references/state-machine.md` § state field のフォーマット検証）で比べるのは `|` より前である。hook は注記ごと `== "done"` と比べていたので、注記つきの terminal 値を active と数えていた。そのため active な steering と同じ checkout にあると候補 2 件の `multiple` になり、pre-push gate が検査せずに push を通していた（fail-open）。

あわせて、同じ解決の結果を使う gate の素通りを閉じた。

- pre-push gate: 検査する steering を 1 件に決められない（候補が 2 件以上の）ときは、通さずに block する（reason code: `steering-multiple`）。active な steering が 2 件以上のときも、終端（done・blocked）の steering だけが 2 件以上並ぶときも同じ。以前は `multiple` として検査せずに通していた（pre-PR gate は以前から block していた）
- pre-push gate・merge gate: `Next Action: blocked` の steering も、`Resume From: blocked` と同じく検査の対象にする
- merge gate: 検出が active な steering 1 件を返しても、コマンドが対象 PR を明示していて、その steering の PR URL が違う（または未記録の）ときは、対象 PR を記録した steering を探し直す。1 件ならその steering で検査し、2 件以上なら `steering-ambiguous`、見つからず PR URL 未記録の steering があれば `pr-url-unrecorded` で止める（候補が複数のときの扱いと同じ）

#### Changed

- `hooks/scripts/lib/detect-steering.sh`: `gdd_value_head` を足した（ASCII `|` より前を取り出して前後の空白を落とす）。`gdd_detect_active_steering` の terminal 判定と、古い brainstorming の判定をこれで比べる
- `hooks/scripts/lib/self-review-evidence.sh`: `gdd_pre_push_resolve_steering` の union も同じ切り出しで比べ、`Next Action: blocked` を候補に足した。候補が 2 件以上のときの reason を `multiple-terminal` にして、active が 2 件の `multiple` と分けた
- `hooks/scripts/run-pre-push-gate-hook.sh`: 解決の結果が `multiple` のときに block する
- `hooks/scripts/run-pre-pr-gate-hook.sh`: steering の解決と completion-check の確認（`Next Action` が done か）を同じ切り出しで比べる。空かどうかの判定と block の文面には、切り出す前の値を使う
- `hooks/scripts/run-merge-gate-hook.sh`: 上の「対象 PR の steering を探し直す」処理を足した
- `hooks/scripts/gdd_stop_hook.py`: markerless の human-check fallback も、`Resume From` を先頭セグメントで比べる
- `hooks/scripts/run-session-start-hook.sh`: ローカル関数 `_gdd_strip_pipe_tail` を `gdd_value_head` に置き換えた（挙動は同じ）

全角の `｜`・`（` は文法の外なので区切りとして扱わない。これらで注記した値は、今までどおり active として数える。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/detect-steering.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/self-review-evidence.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/tasklist_parse.py`（コメントだけ）
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/tests/test_steering_terminal_pipe_head_contract.py`（新規）
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`
- `plugins/gate-driven-development/tests/test_self_review_evidence.sh`
- `plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py`（コメントだけ）
- `plugins/gate-driven-development/tests/test_state_field_value_less_line_contract.py`（docstring だけ）
- `plugins/gate-driven-development/references/self-review-lanes.md`（§ blocked steering の扱い）

#### User Action Required

- active な GDD セッションで push するとき、同じ checkout で検査する steering が 1 件に決まらない（作業中の steering が 2 件以上ある、または作業中が無く done・blocked の steering が 2 件以上ある）と、pre-push gate が `steering-multiple` で止める。使わない steering は削除せず別の場所へ移す（git で追跡している steering なら、その repo で commit する）。緊急時は `GDD_SKIP_PRE_PUSH_GATE=1 git push ...` で通す
- merge gate: 所有する marker が無く、検出された steering の PR URL が対象 PR と違うとき、対象 PR を記録した steering が 2 件以上なら `steering-ambiguous`、1 件も無く PR URL 未記録の steering（cancelled のものを含む）があれば `pr-url-unrecorded` で止める。steering に PR URL を記録するか、使わない steering を移す。緊急時は kill-switch を使う
- `Resume From: cancelled | …` の steering は、素の `cancelled` と同じく検査の対象から外れる（今までは active として数えていた）

#### Validation / Eval Impact

- 契約テストを先に書き、失敗を確認してから実装した（pre-push の fail-open、steering が複数の場合（active・終端とも）、`Next Action: blocked`、全角の注記、空の先頭セグメント、古い brainstorming、pre-PR の空判定の経路、merge gate の照合し直し、stop hook の fallback）
- union 側だけ・merge gate 側だけ修正を外すと、それぞれのテストが落ちることを確認した
- 変更したファイルを参照するテストと `bash plugins/gate-driven-development/tests/validate-plugin.sh`
