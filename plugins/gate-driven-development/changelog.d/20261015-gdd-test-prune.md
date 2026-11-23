---
type: patch
---

#### Summary

- 利用者から見える変更なし。テスト判定基準（`references/testing-anti-patterns.md` § テスト判定基準）に当たるテストを消した。文書に語・文があるかだけを見るもの、hook・script・lib のソースの値や文言を写すだけのもの、移行・撤去が済んだことを確かめるだけのもの、ライブラリの仕様を確かめ直すもの、実装と同じ式で期待値を作るもの、ほかのテストや検査が同じことを見ているもの。hook のコメントからは、射程外の列挙の写しと、消したテストの名前を外した

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/task_binding_resolve.py`
- `plugins/gate-driven-development/hooks/scripts/run-notification-hook.sh`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`
- `plugins/gate-driven-development/tests/test_auth_waiting_pause_contract.py`
- `plugins/gate-driven-development/tests/test_complexity_flag_formal_gate_guard_contract.py`
- `plugins/gate-driven-development/tests/test_cross_session_handoff_contract.py`
- `plugins/gate-driven-development/tests/test_cross_session_hitl_contract.py`
- `plugins/gate-driven-development/tests/test_done_guard_closed_grammar_contract.py`
- `plugins/gate-driven-development/tests/test_done_guard_state_line_break_chars_contract.py`
- `plugins/gate-driven-development/tests/test_gdd_scenario_eval_contract.py`
- `plugins/gate-driven-development/tests/test_hitl_lint_gate_unit.py`
- `plugins/gate-driven-development/tests/test_hitl_lint_gate_warn_wiring.py`
- `plugins/gate-driven-development/tests/test_hitl_lint_marker_sync_contract.py`
- `plugins/gate-driven-development/tests/test_impl_gate_precision_tiering_contract.py`
- `plugins/gate-driven-development/tests/test_last_handoff_summary_contract.py`
- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`
- `plugins/gate-driven-development/tests/test_lint_hitl_stage_plan_contract.py`
- `plugins/gate-driven-development/tests/test_merge_gate_followup_findings.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_evidence_parsing.py`
- `plugins/gate-driven-development/tests/test_notification_hook_contract.py`
- `plugins/gate-driven-development/tests/test_p0_p1_operational_hardening_contract.py`
- `plugins/gate-driven-development/tests/test_peer_turn_write_boundary_e2e_contract.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`
- `plugins/gate-driven-development/tests/test_pre_push_tip_sha_resolution_contract.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_lexing.py`
- `plugins/gate-driven-development/tests/test_reference_integrity_contract.py`
- `plugins/gate-driven-development/tests/test_repository_identity.py`
- `plugins/gate-driven-development/tests/test_requirements_tiering_contract.py`
- `plugins/gate-driven-development/tests/test_self_review_lanes_contract.py`
- `plugins/gate-driven-development/tests/test_session_start_last_turn_failure_contract.py`
- `plugins/gate-driven-development/tests/test_state_field_value_less_line_contract.py`
- `plugins/gate-driven-development/tests/test_status_field_ownership_contract.py`
- `plugins/gate-driven-development/tests/test_steering_cancel_guidance_contract.py`
- `plugins/gate-driven-development/tests/test_steering_retention_contract.py`
- `plugins/gate-driven-development/tests/test_stop_failure_hook_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_bounce_containment_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_continuation_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_state_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_unit.py`
- `plugins/gate-driven-development/tests/test_superpowers_differentiation_contract.py`
- `plugins/gate-driven-development/tests/test_t8_final_verification_contract.py`
- `plugins/gate-driven-development/tests/test_task_binding_resolve_security_contract.py`
- `plugins/gate-driven-development/tests/test_typed_dispatch_templates_contract.py`
- `plugins/gate-driven-development/tests/test_validate_plugin_check_inventory.py`
- `plugins/gate-driven-development/tests/test_verification_block_message_contract.py`
- `plugins/gate-driven-development/tests/test_verification_closed_grammar_release_notes_contract.py`
- `plugins/gate-driven-development/tests/test_verification_grammar_single_source_contract.py`
- `plugins/gate-driven-development/tests/test_worktree_pollution_contract.py`
- `plugins/gate-driven-development/tests/test_worktree_registry_contract.py`
- `plugins/gate-driven-development/tests/test_x55_hitl_offline_judge_removal_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
