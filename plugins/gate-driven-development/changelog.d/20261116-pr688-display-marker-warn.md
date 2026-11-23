---
type: minor
---

#### Summary

- human check の返事を受けたターンの Stop で、一次表示に出した `記録の場所: なし` の行を `requirements.md` の § ズレ確認 の同じ行と 1 行ずつ突き合わせ、印（` / 表示: 済み`）が無い行か、同じ行が見つからない行があれば、新しい Stop hook（`hooks/scripts/run-display-marker-hook.sh`）が systemMessage で知らせる。一次表示に出していない行は数えない。止めはしない。見るのは、本人の返事の直前のマーカー付きの一次表示だけで、cross-session の返事、一次表示と返事の間の compaction、返事のターンで確認を出し直したときは知らせない
- 知らせた回も知らせなかった回も、一次表示の行数・一致して印の無い行数・同じ行が見つからない行数を、hook の state dir の `display-marker.log` に残す（行の本文は残さない）

#### Affected Files

- `hooks/hooks.json`・`hooks/scripts/run-display-marker-hook.sh`・`hooks/scripts/lib/display_marker.py`・`references/human-check-template.md`・`tests/test_display_marker_hook.py`・`tests/test_hooks_kill_switch.py`・`tests/test_hooks_wiring_new_events_contract.py`

#### User Action Required

- 長く動いているセッションは、開き直すと新しい Stop hook が効く

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
