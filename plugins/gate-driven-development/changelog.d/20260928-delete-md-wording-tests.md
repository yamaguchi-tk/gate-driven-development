---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。hook・script・lib を実行せず、文書（references・skills・agents・commands など）に語・文があるか（無いか）だけを assert するテストを消した。文言を 1 語直すだけで落ち、文言の修正のたびに手戻りを生んでいたため。ファイルごと消したのは 43 本で、2 本はコードと文書を突き合わせる部分だけを残した。

消したファイルの名前を挙げていた `CONTRIBUTING.md` の関係するテストの案内、`references/fixed-models.md` の版数付きの名前の検査の案内、`docs/DISTRIBUTION_READINESS.md` の一覧、他のテストのコメントも合わせた。`references/prompt-contract-map.md` の表は、state の正本の 4 文書について、機械の検査が無いことを書いた。

#### Affected Files

- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/prompt-contract-map.md`
- `plugins/gate-driven-development/docs/DISTRIBUTION_READINESS.md`
- `plugins/gate-driven-development/tests/test_always_high_scope_contract.py`
- `plugins/gate-driven-development/tests/test_design_review_checkpoint_contract.py`
- `plugins/gate-driven-development/tests/test_independent_review_host_route_contract.py`
- `plugins/gate-driven-development/tests/test_verification_closed_grammar_release_notes_contract.py`
- `plugins/gate-driven-development/tests/test_requirements_tiering_contract.py`
- `plugins/gate-driven-development/tests/test_adr_guidance_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_adr_origin_producer_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_carry_forward_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_codex_compact_recovery_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_completion_check_loop_safety_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_completion_check_unused_symbol_scan_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_continuation_registry_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_differentiation_core_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_express_advisory_findings_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_fable_removal_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_finding_category_vocabulary_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_gdd_code_simplifier_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_goal_driven_execution_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_governance_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_independent_review_differential_scope_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_japanese_writing_norm_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_model_generation_audit_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_model_names_without_version_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_open_input_handling_template_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_plan_execution_discipline_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_planning_reviewer_ac_closure_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_planning_reviewer_lenses_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_planning_reviewer_open_input_handling_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_planning_reviewer_wiring_table_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_post_merge_local_cleanup_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_pr_creation_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_pr_review_followup_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_pr_review_wiring_cross_model_review_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_pr_size_limit_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_precision_tiering_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_remediation_loop_root_cause_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_repro_test_and_blast_radius_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_requirements_gating_parallel_review_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_reviewer_live_execution_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_state_source_of_truth_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_superpowers_active_gdd_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_superpowers_imported_disciplines_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_superpowers_method_import_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_team_rollout_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_testing_standard_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_wiring_table_authoring_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_x33_worktree_dispatch_binding_contract.py`（削除）
- `plugins/gate-driven-development/tests/test_x64_fable_remnant_cleanup_contract.py`（削除）

#### User Action Required

- なし

#### Validation / Eval Impact

- 消したファイルの名前を、`review-log/`・`changelog.d/`・CHANGELOG を除くリポジトリ全体で grep し、当時の記録である `docs/adr/` を除いて、残る参照を直した
- `tests/test_always_high_scope_contract.py` の変異の確認
- `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
