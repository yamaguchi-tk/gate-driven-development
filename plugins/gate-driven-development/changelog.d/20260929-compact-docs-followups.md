---
type: patch
---

#### Summary

- worktree に紐づいた steering（binding）の先が `Next Action: cancelled` だけで中止されている（human check・completion-check の中止の規定の形）とき、SessionStart・UserPromptSubmit・PreCompact・plan-reread など数え直さない呼び出し元は、その steering を作業中として扱わないようにした。これまでは、中止した steering の状態を案内・注入していた。pre-push・pre-PR・merge gate は今どおり、binding 先を候補に残して検査する（外すには `Resume From: cancelled` も書く）。`Next Action: done` は今どおり終端にしない（`gdd-pr-review-followup` の外部レビュー待ちの間の値）
- merge gate は、作業中の steering が無く終端の steering だけが残る checkout でも、対象 PR を記録した steering（中止した steering を含む）を検査するようにした。これまでは候補 0 件として、承認の証跡を見ずに merge を通していた。PR を記録した steering がある checkout で、対象 PR を決められない merge（引数なし・ブランチ名）は `steering-ambiguous` で止める
- merge gate の台帳の経路（marker の無い checkout や git の外の cwd から、GDD の PR を merge する経路）は、記録した PR URL から repo を取り出せないときも照合したものとして止めるようにした。これまでは repo の比較が一致しないとして照合から外れ、承認の証跡を見ずに通っていた
- steering write guard の peer turn の境界（直近のターンが別セッションからのメッセージのとき、承認・中止の記録を deny する）が、`Resume From: cancelled` の書き込みも deny するようにした。検出は `Resume From` の cancelled だけでも中止とみなすのに、境界は `Next Action: cancelled` だけを見ていた
- `gdd-brainstorming` の discard（Exit Decision）は、state.md を `Resume From: cancelled` / `Next Action: cancelled` に書き換えるようにした（これまでは、hook が読まない廃止した印の `Status: Discarded` と `Resume From: -` を書かせていた）
- `references/phase-gate-prechecks.md` と README の PreCompact・session の照合の説明を実装に合わせた（PreCompact が渡すのは state.md の場所と Resume From・Next Action。session が違えば渡さない。local state が無いときと、session id が取れない runtime では照合しない）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/detect-steering.sh`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`
- `plugins/gate-driven-development/references/phase-gate-prechecks.md`
- `plugins/gate-driven-development/README.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_pre_push_tip_sha_resolution_contract.py`：binding 先が `Next Action: cancelled` だけ（`|` 以降の注記つきを含む）のとき、数え直さない検出は none、数え直す検出は found を返すことを固定した。brainstorming の discard が書かせる値の binding 先で、終端の binding の既存のケースを全部回すこと、binding 先の state.md が読めない・`Next Action` が無いときは検査を続けることを、pre-push の入口から固定した
- `tests/test_peer_turn_write_boundary_e2e_contract.py`：peer turn の `Resume From: cancelled` の書き込み（追加の形・値だけの Edit・不正な UTF-8 を含む state.md）を deny し、人のターンと無関係な Edit は通すことを、hook の入口から固定した
- `tests/test_merge_gate_bound_terminal_steering.py`：対象 PR を記録した中止の steering（binding の有無、`Next Action` だけの中止を含む）の PR を承認の証跡なしに merge すると止まること、対象 PR を省いた merge が止まること、state.md が読めないと止まること、別の PR の merge は通ることを、hook の入口から固定した
- `tests/test_merge_gate_hook_gate_regressions.py`：URL と番号が両方見える merge を番号でも照合して止めること、正準形でない PR URL を記録した steering でも別の repo の同じ番号は通すことを固定した
- `tests/test_merge_gate_ledger_fail_closed.py`：台帳の経路で、repo を取り出せない PR URL の記録を止めること、marker の無い checkout から台帳の PR を URL で指し番号も見える merge を止めることを固定した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
