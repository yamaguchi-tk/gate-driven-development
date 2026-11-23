---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。文書の語だけを見るテストを消したときに一緒に消えていた、tier の表の照合を戻した。`references/fixed-models.md` の `formal_gate`・`light_task`・`remediation_loop` の行（Claude Code 列）と、`references/cursor.md`・`references/codex.md` の `independent_review` の行（model と effort）を、期待値をテストに直書きせず `scripts/resolve-gdd-model.py` の `TIER_TO_MODEL`・`resolve_effort` の値と突き合わせる。あわせて、消したテストの契約を書いたままだった docstring・コメントを残るテストの中身に合わせ、中身と合わないテストのクラス名・メソッド名を改名した。

#### Affected Files

- `plugins/gate-driven-development/tests/test_gdd_scenario_eval_contract.py`
- `plugins/gate-driven-development/tests/test_independent_review_host_route_contract.py`
- `plugins/gate-driven-development/tests/test_last_handoff_summary_contract.py`
- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`
- `plugins/gate-driven-development/tests/test_merge_gate_followup_findings.py`
- `plugins/gate-driven-development/tests/test_remediation_loop_model_routing_contract.py`
- `plugins/gate-driven-development/tests/test_typed_dispatch_templates_contract.py`
- `plugins/gate-driven-development/tests/test_verification_closed_grammar_release_notes_contract.py`
- `plugins/gate-driven-development/tests/test_verification_grammar_single_source_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 足したテストごとに、文書の該当行の model・effort を一時的に書き換えて落ちること、`scripts/resolve-gdd-model.py` の effort を一時的に書き換えて落ちることを確かめ、戻した
- 改名したクラス名・メソッド名を、リポジトリ全体で grep した
- 変更したテストファイルと、その名前を参照するテストを `python3 -m pytest <ファイル…> -q -n auto` で回した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
