---
type: patch
---

#### Summary

PR 旧#89（X-64: Cursor `remediation_loop` の Opus 5 残留修正）の独立レビュー round 2 で、範囲外の advisory 指摘として `skills/gdd-model-routing/SKILL.md` の「Autonomous Model Workers」節が、退避済みの `docs/references-archive/autonomous-model-workers.md` を現役の参照先（`references/subagent-dispatch.md` と並列）として案内していたことが見つかった。同 PR で対応した X-55（`references/source-of-truth-map.md` が退避済み `docs/references-archive/hitl-offline-judge.md` を補助正本として引用していた問題）と同型のパターン。現役の worker dispatch 契約は `references/subagent-dispatch.md` 側に統合済みのため、退避済みファイルへの案内を削除した。

#### Fixed

- `skills/gdd-model-routing/SKILL.md`: 「Autonomous Model Workers」節から `docs/references-archive/autonomous-model-workers.md` への案内を削除し、現役の `references/subagent-dispatch.md` のみを参照させる
- `tests/test_x64_fable_remnant_cleanup_contract.py`: `test_model_routing_skill_does_not_cite_archived_references` を追加し、同 skill が退避済み参照を再度案内しないことを検査する再発防止契約とした

#### Affected Files

- `skills/gdd-model-routing/SKILL.md`
- `tests/test_x64_fable_remnant_cleanup_contract.py`

#### User Action Required

なし。参照先の記述を修正しただけで、挙動や利用者の手順は変わらない。

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_x64_fable_remnant_cleanup_contract.py`
- `python3 -m pytest plugins/gate-driven-development/tests/test_autonomous_model_worker_contract.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
