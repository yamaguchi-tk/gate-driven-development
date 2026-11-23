---
type: patch
---

#### Summary

worktree の binding が正規の完了の形（`Resume From` は done 以外、`Next Action: done`）の steering を指すとき、pre-push gate と merge gate は binding 先を作業中として扱い、binding の無い作業中の steering を数えなかった。binding 先が trivial なら push を検査せずに通していた。数え直すときに限り、binding 先の `state.md` の `Resume From`・`Next Action` か `tasklist.md` の `Next Action` の先頭の英単語を小文字にして done・cancelled・canceled なら終端とみなし（`Resume From` が done・cancelled と完全一致する binding 先は数え直しの前から終端で、下の扱いから除く。`Done`・`done (merged)`・`done（…）` も含む。`tasklist.md` が読めない・ファイルでないときも done かもしれないものとして扱う）、作業中の steering を数える（binding 先は作業中に数えず、作業中の steering があれば、done・blocked の steering と、終端とみなした binding 先を候補に残す）。作業中の steering が無ければ、終端とみなした binding 先を今どおり検査する（done でも cancel でも、binding 先が `.steering/` の外にあっても。`Resume From: done` の完全一致で `.steering/` の外の binding 先は除く）。merge gate は、対象 PR の照合で見ない `.steering/` の外の候補があれば `steering-ambiguous` で止める。

pre-PR gate も、binding が終端の steering を指すときに同じ規則で作業中の steering を数え直すようにした。これまでは binding が cancelled・stale な brainstorming を指すと作業中の steering を数えず、別の done の steering が 1 件あればそれで completion-check を判定し、作業中の steering を検査しないまま PR を作らせていた。作業中の steering が 1 件ならその steering の completion-check を求め、候補が 2 件以上なら「複数」で止める。作業中の steering が無ければ今どおり（`Next Action` などだけで終端とみなした binding 先は、done でも cancel でも binding 先で判定する）。

ほかの hook（session-start など）は今どおり、followup 中の `Next Action: done` の binding 先を作業中として扱う。

#### Changed

- `hooks/scripts/lib/detect-steering.sh`: `--recount-terminal-binding` のとき、binding 先の `state.md` の `Resume From`・`Next Action` か `tasklist.md` の `Next Action` の先頭の英単語が done・cancelled・canceled でも終端とみなす（`Resume From` の完全一致の done・cancelled は数え直しの前から終端で、候補に残さない。`tasklist.md` が読めない・ファイルでないときは done とみなす）。binding 先は `.steering/` の中でも外でも作業中に数えず、こうして終端とみなしたか done・blocked なら候補に残す。作業中の steering が無ければ、終端とみなした binding 先を返す
- `hooks/scripts/run-merge-gate-hook.sh`: multiple を対象 PR で探し直して見つからないとき、`.steering/` の外の候補（binding 先）があれば `steering-ambiguous` で止める（照合が `.steering/` しか見ないため）
- `hooks/scripts/run-pre-pr-gate-hook.sh`: `gdd_detect_active_steering --recount-terminal-binding` で解決する。解決した steering の `state.md`・`tasklist.md` が読めなければ、理由つきで止める（無出力で終わらない）
- `references/self-review-lanes.md`: 終端に正規の完了の形を含めること、読めない `tasklist.md` を done とみなすこと、`Next Action` などだけで終端とみなした binding 先を候補に残すこと、pre-PR gate も数え直すことを書いた
- `references/abandon-and-pause.md`: worktree の binding が指す steering は、`Next Action=cancelled`（`tasklist.md` を含む）だけでは push・PR・merge の gate から外れず、外すには `Resume From: cancelled` も書くことを書いた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/detect-steering.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/abandon-and-pause.md`
- `plugins/gate-driven-development/tests/test_pre_push_tip_sha_resolution_contract.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`
- `plugins/gate-driven-development/tests/test_merge_gate_bound_terminal_steering.py`

#### User Action Required

- binding 先が完了済み（`Next Action: done`）で、同じ `.steering/` に使っていない作業中の steering が残っていると、push は tip の証跡が無ければ `steering-multiple`、引数なしの merge は `steering-ambiguous`、PR 作成は「複数」で止まる。使わない steering は `references/self-review-lanes.md` の「使わないステアリングの終え方」に従って終える

#### Validation / Eval Impact

- `tests/test_pre_push_tip_sha_resolution_contract.py`: binding 先が `Next Action: done`（`done | evidence: x` を含む）・trivial で作業中の steering があると `steering-multiple` で止まり、`Next Action: cancelled` でも作業中の steering と並べて `steering-multiple` で止まり、`tasklist.md` にだけ done がある形でも検査されずに通らず、binding 先の `state.md` が読めなくても止める側の判定を出し、followup 中の形で作業中が無ければ今どおり通ること。`done（…）`・`done (merged)`・`Done`・`canceled` の binding 先（trivial）も作業中の steering を隠さないこと。作業中が無ければ、別の done の steering があっても、`.steering/` の外にあっても、binding 先を検査すること。binding 先の `tasklist.md` が読めなくても binding 先を検査すること。binding 先（trivial）の `tasklist.md` が読めない・ディレクトリなら、作業中の steering があると `steering-multiple` で止まること。`.steering/` の外の done の binding 先（followup 中の形と `Resume From: done`）と作業中の trivial の steering があると `steering-multiple` で止まること。`done (merged)` の binding 先（trivial）は、作業中が無ければ別の done の steering があっても binding 先で検査されること。`canceled`・`Cancelled`・`cancelled（superseded）` の binding 先（trivial）も作業中の steering を隠さないこと。`Next Action` だけが cancel の binding 先は、作業中が無ければ、別の done の steering（trivial）があっても binding 先で検査されること。`tasklist.md` にだけ cancelled がある binding 先や、`.steering/` の外の cancelled の binding 先も、作業中の trivial の steering と並べて止まること
- `tests/test_pre_pr_gate_contract.py`: binding が cancelled・stale な brainstorming・`Next Action: done` を指し作業中の steering があると PR 作成を止め、binding 先が `Next Action: done` か followup 中の形で作業中が無ければ今どおり通すこと、数え直しで選んだ作業中の steering の `state.md` が読めなければ理由つきで止めること、binding 先が `Next Action: canceled` で作業中が無ければ別の done の steering で判定しないこと
- `tests/test_merge_gate_bound_terminal_steering.py`: binding 先が `Next Action: done` で作業中の steering もあるとき、対象 PR を記録した binding 先で検査されること、対象 PR を省くと `steering-ambiguous` で止まること、binding 先の `Next Action` だけが `Canceled` で作業中が無くても対象 PR の binding 先を承認の証跡なしに merge させないこと、`.steering/` の外の binding 先（`Canceled`・`done`）が対象 PR を記録し作業中の steering もあると `steering-ambiguous` で止まり、binding 先が `.steering/` の中ならどちらでもない PR の merge は今どおり通すこと
- 変更したファイルを参照するテスト、`bash plugins/gate-driven-development/tests/validate-plugin.sh`
