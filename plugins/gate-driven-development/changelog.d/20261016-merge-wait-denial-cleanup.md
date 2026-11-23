---
type: patch
---

#### Summary

- マージ待ちの宣言（`.claude/gdd-merge-intent.json`）を書いた後の押し返し（Stop hook）から、merge gate の `review-wait-not-elapsed` だけの拒否を「待つ場面」として拒否に数えない例外を消した。merge gate は拒否せず実行後に通知するだけになったので、この例外に当たる入力は届かない。同じ文が届いたときは、ほかの拒否と同じく押し返さずに止まる
- 押し返しの文から、merge gate に拒否されたときの案内を外した（hook・auto mode classifier の拒否の案内は残る）
- merge gate の通知（`block()`）と suppression の記録（`_mg_log_suppressed`）を、pre-push gate・pre-PR gate と同じ `hooks/scripts/lib/gate-notice.sh` に移した。通知の文と `merge-gate-suppressed.log` の行の形は変わらない（HOME も `GDD_HOOK_STATE_DIR` も無いときは記録を書かない）
- hooks.json の説明の (7) pre-PR gate・(9) pre-push gate・(10) merge gate を、止めずに実行後に通知する形に直した
- references・`README.md`・`docs/TROUBLESHOOTING.md`・`docs/SECURITY.md`・`CONTRIBUTING.md`・`scripts/check-gate-ledger.sh` のコメントで、pre-push gate・pre-PR gate・merge gate が止める・拒むと書いていた箇所を、実行後に通知する形に直した。`references/post-completion-pr-flow.md` の `dry: yes` 未到達の差し戻しは、通知を受けた時点で PR がもう作られている前提にした（証跡を後から書き足さず、reason code と不足をユーザーに報告し、直した差分は同じ PR に push する）
- SessionStart の、steering が複数あるときの案内文を「pre-push gate も steering-multiple で止まります」から「pre-push gate も steering-multiple を不足として実行後に通知します」に直した
- skills（`gdd-completion-check`・`gdd-pr-review-followup`）、`docs/learned-patterns.md`、hooks とテストのコメント・docstring・hooks.json の (11) でも、3 つの gate が止める・拒むと書いていた箇所を、実行後に通知する形に直した。コードの判定は変えていない
- `docs/TROUBLESHOOTING.md` の 2 つの見出しを「active steering が複数検出されて通知が出る」「ステアリングが読めないとして push・merge の後に通知が出る」に変えた
- 3 つの gate が止めると書いた ADR（repo 直下の `docs/adr/`）と設計文書（`plugins/gate-driven-development/docs/design/`）の冒頭に、今は止めずに通知することを 1 行追記した。本文のうち、今も止めると読める現在形の文には「（当時）」などの時点を添えた。Context の当時の実測と経緯は直していない

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_pushback.py`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/hooks.json`（description）
- `plugins/gate-driven-development/references/post-merge-qa.md`・`state-machine.md`・`post-completion-pr-flow.md`・`independent-review.md`・`state-field-tiers.md`・`post-completion-learning.md`・`rollback-patterns.md`・`self-review-lanes.md`
- `plugins/gate-driven-development/README.md`・`docs/TROUBLESHOOTING.md`・`docs/SECURITY.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`（コメント）
- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`（案内文）と、hooks・tests のコメント
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`・`skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/docs/design/`、`docs/adr/`、`docs/learned-patterns.md`
- `plugins/gate-driven-development/changelog.d/20260928-steering-multiple-followups.md`（見出しの参照）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_stop_hook_autonomy_pushback.py`: 待つ場面の merge gate の文を、押し返さずに止まる側の入力に移した。merge gate の文と押し返しの判定の一致を固定していた 2 本を外した
