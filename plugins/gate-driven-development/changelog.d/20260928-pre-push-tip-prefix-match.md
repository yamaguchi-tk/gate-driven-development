---
type: patch
---

#### Summary

pre-push gate が、複数の steering から push 対象の tip の証跡で 1 件を選ぶとき、一致の条件を「証跡の sha（大文字小文字は区別しない）が tip の sha の先頭と一致する」にした。これまでは証跡の sha を commit に解決して tip と比べていたので、tip を指す tag の sha も一致になりえた。先に候補を絞る条件（tip の sha の先頭 7 桁を含む）と受理する集合がずれていた。選んだ steering の証跡の sha は、今までどおり後の検査で tip と照合する。

tip の証跡で選んだ後の block 文すべてに、`Task Size` を standard として検査したことと、どれを終えるかユーザーに確認したうえで使わない steering を終え、作業中または完了済みの steering が 1 件になれば、その steering の `Task Size` で検査されることを添えた。`state.md` の `Task Size` が quick でも standard の要求で止まるので、理由が分かるようにした。

worktree の binding が終端（done・cancelled・stale な brainstorming）の steering を指すとき、pre-push gate と merge gate が使う steering の解決は、binding の無い作業中の steering を数えなかった。cancelled なら push・merge を検査せずに通し、done（または別の done・blocked の steering が 1 件ある）なら、その終端の steering の `Task Size`（trivial なら無検査）で検査していた。binding が無いときと同じ規則で作業中の steering を数え直し、作業中の steering があるときは done・blocked の steering も候補に残す。候補が 1 件ならその steering で検査する。2 件以上なら、pre-push は push 対象の tip の証跡で選んで standard で検査し（決まらなければ `steering-multiple`）、merge gate は対象 PR を記録した steering で選ぶ（対象 PR を省いたか 2 件以上が一致すれば `steering-ambiguous`、対象 PR を記録した steering が無く PR URL の無い steering があれば `pr-url-unrecorded` で止め、全候補が別の PR を記録していて所有 marker が無ければ検査しない）。作業中の steering が無ければ今どおり（done・blocked の steering が 1 件ならそれで検査し、終端と stale な brainstorming だけなら検査しない）。ほかの hook（session-start・pre-PR gate など）が binding を読む挙動は変えていない。

#### Changed

- `hooks/scripts/lib/detect-steering.sh`: `gdd_detect_active_steering` に `--recount-terminal-binding` を足した。binding が終端の steering を指すとき、binding が無いときと同じ規則で作業中の steering を数え（読めない `state.md` は作業中に数える）、作業中の steering があれば done・blocked の steering も候補に残す。引数なしの呼び出しは今どおり
- `hooks/scripts/lib/self-review-evidence.sh`: pre-push gate と merge gate が使う `gdd_pre_push_resolve_steering` が、その引数で呼ぶ
- `hooks/scripts/run-pre-push-gate-hook.sh`: tip の証跡で選ぶときの比較を先頭一致にした。選んだ後の block 文すべて（sha-mismatch・dry・Independent Review など）に注記を添える
- `references/self-review-lanes.md`: 一致の条件の記述を合わせた。binding が終端の steering を指すときの数え方と、pre-PR gate が binding を読むときの性質を書いた。`not_applicable(independent-review)` を standard でだけ受理する規定に、tip で選んだときは pre-push が standard を渡す例外を書いた
- `hooks/scripts/validate-steering-write.py`: Task Size の正規化の正本のコメントに同じ例外を書いた（挙動は変えない）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/detect-steering.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/self-review-evidence.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/tests/test_pre_push_tip_sha_resolution_contract.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`
- `plugins/gate-driven-development/tests/_pre_push_gate_support.py`
- `plugins/gate-driven-development/tests/test_merge_gate_bound_terminal_steering.py`

#### User Action Required

- binding が終端の steering を指す worktree で、作業中の steering の push と merge が、その steering で検査されるようになる。push が止まったら、その steering に Pre-Push Self Review を記録する。merge が止まったら、その steering の承認と証跡を記録するか、使わない steering なら `references/self-review-lanes.md` の「使わないステアリングの終え方」に従って終える
- 複数 steering の checkout で tip を指す tag の sha を証跡に書いていたときは、その steering は選ばれなくなる。commit の sha で書く

#### Validation / Eval Impact

- `tests/test_pre_push_tip_sha_resolution_contract.py`: tip を指す tag の sha の証跡が一致にならないこと（tip の sha がファイルの別の行にあっても）、大文字の sha も一致になること、tip で選んだときだけ block 文（Independent Review・dry）に注記が付き、ユーザーへの確認と手順の参照先を含み、その ASCII の語が AC-18 の許可集合に収まること、binding が cancelled の steering を指す worktree で、作業中の steering が 1 件だけなら binding が無いときと同じくその steering で検査され（trivial なら通り）、2 件以上なら tip の証跡で選ばれ、読めない `state.md` でも検査されずに通らず、終端と stale な brainstorming だけなら今どおり通ること、binding 先の done の steering や別の done の steering と作業中の steering があるときは、作業中の steering の `Task Size`（trivial）でも done の steering の `Task Size`（trivial）でも通さず `steering-multiple` で止め、binding 先の done の steering が tip の証跡を持てばそれが選ばれ、作業中の steering が無ければ binding 先の done の steering で検査されること、引数なしの `gdd_detect_active_steering` は今どおり none を返すこと、tip 以外の証跡を持つ steering が増えても `Pre-Push Self Review` を読む回数が増えないこと
- `tests/test_merge_gate_bound_terminal_steering.py`（新規）: binding が cancelled の steering を指す worktree で、作業中の steering の PR の merge が binding の無いときと同じく承認の証跡で止まり、読めない `state.md` は `state-unreadable`、作業中が 2 件で対象 PR を省くと `steering-ambiguous` で止まり、作業中が無ければ今どおり通ること
- `tests/test_pre_push_gate_contract.py`・`tests/_pre_push_gate_support.py`: AC-18 の許可トークン集合を共有の定数にした（集合は変えていない）
- 変更したファイルを参照するテスト、`bash plugins/gate-driven-development/tests/validate-plugin.sh`
