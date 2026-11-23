---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。hook・script・lib を実行するテストと同じファイルにある、文書に語・文があるか（無いか）だけを assert するテストを消した（30 ファイル）。使われなくなったテスト用のヘルパー（`tests/_root_branch_guard_support.py` の `read`）も消した。ファイルごとの削除は同じ版の別の変更で行った。文書を読むテストでも、コードが読む値・集合・シンボルと文書を突き合わせるもの、JSON・frontmatter を構造として読むもの、パスの実在を見るもの、行数の予算を見るものは残した。

#### Affected Files

- `plugins/gate-driven-development/tests/_root_branch_guard_support.py`
- `plugins/gate-driven-development/tests/test_auth_waiting_pause_contract.py`
- `plugins/gate-driven-development/tests/test_autonomous_model_worker_contract.py`
- `plugins/gate-driven-development/tests/test_canonical_field_line_anchoring_contract.py`
- `plugins/gate-driven-development/tests/test_changelog_fragments.py`
- `plugins/gate-driven-development/tests/test_cross_session_hitl_contract.py`
- `plugins/gate-driven-development/tests/test_distribution_readiness_contract.py`
- `plugins/gate-driven-development/tests/test_e2e_replay_fixtures.py`
- `plugins/gate-driven-development/tests/test_engineering_baseline_architecture_contract.py`
- `plugins/gate-driven-development/tests/test_gdd_scenario_eval_contract.py`
- `plugins/gate-driven-development/tests/test_hitl_lint_marker_sync_contract.py`
- `plugins/gate-driven-development/tests/test_impl_gate_precision_tiering_contract.py`
- `plugins/gate-driven-development/tests/test_independent_review_host_route_contract.py`
- `plugins/gate-driven-development/tests/test_last_handoff_summary_contract.py`
- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`
- `plugins/gate-driven-development/tests/test_lint_hitl_stage_plan_contract.py`
- `plugins/gate-driven-development/tests/test_merge_gate_followup_findings.py`
- `plugins/gate-driven-development/tests/test_model_routing_contract.py`
- `plugins/gate-driven-development/tests/test_p0_meta_feedback_contract.py`
- `plugins/gate-driven-development/tests/test_p0_p1_operational_hardening_contract.py`
- `plugins/gate-driven-development/tests/test_remediation_loop_model_routing_contract.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_contract.py`
- `plugins/gate-driven-development/tests/test_self_review_lanes_contract.py`
- `plugins/gate-driven-development/tests/test_status_field_ownership_contract.py`
- `plugins/gate-driven-development/tests/test_steering_retention_contract.py`
- `plugins/gate-driven-development/tests/test_steering_size_deny_contract.py`
- `plugins/gate-driven-development/tests/test_superpowers_differentiation_contract.py`
- `plugins/gate-driven-development/tests/test_typed_dispatch_templates_contract.py`
- `plugins/gate-driven-development/tests/test_verification_closed_grammar_release_notes_contract.py`
- `plugins/gate-driven-development/tests/test_verification_grammar_single_source_contract.py`
- `plugins/gate-driven-development/tests/test_x55_hitl_offline_judge_removal_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 消したテストの名前を、`review-log/`・`changelog.d/`・CHANGELOG を除くリポジトリ全体で grep した
- 編集したテストファイルを `python3 -m pytest <ファイル…> -q` で回した
- `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
