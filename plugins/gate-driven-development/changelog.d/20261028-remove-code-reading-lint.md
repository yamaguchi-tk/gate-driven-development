---
type: minor
---

#### Summary

- gate から呼ばれていなかった `scripts/lint-existing-code-reading.py`（requirements.md の `## Existing Code Reading Evidence` の表の列を検査する lint）を撤去した。requirements の既存コードの事実は、AC と承認ポイントの `根拠:` の欄と、reviewer を起動する前の `scripts/lint-plan-consistency.py --entry requirements` の欄の検査で扱う
- requirements.md の `Existing Code Reading Evidence` の節を書く手順（brainstorming の手順 9）は変えていない。この節を機械で検査するものが無くなるだけである

#### Removed

- `scripts/lint-existing-code-reading.py`
- `validate-plugin.sh` の `existing-code-reading-lint` の検査と、`lint-scripts-functional`・`lint-scripts-syntax` の同じ script の分
- replay の fixture `tests/fixtures/e2e-replay/shallow-code-reading`・`tests/fixtures/e2e-replay/existing-capability-missed`

#### Affected Files

- `scripts/lint-existing-code-reading.py`（削除）
- `tests/checks/existing-code-reading-lint.sh`（削除）
- `tests/checks/manifest.tsv`
- `tests/checks/lint-scripts-functional.sh`
- `tests/checks/lint-scripts-syntax.sh`
- `tests/checks/skill-body-budget.sh`
- `tests/fixtures/e2e-replay/shallow-code-reading/`（削除）
- `tests/fixtures/e2e-replay/existing-capability-missed/`（削除）
- `tests/test_e2e_replay_fixtures.py`
- `tests/test_p0_meta_feedback_contract.py`
- `tests/test_validate_plugin_check_inventory.py`
- `references/prompt-contract-map.md`（既存コードの読みが浅い事故の行を、`根拠:` の欄と `lint-plan-consistency.py` に向け直した）
- `docs/DISTRIBUTION_READINESS.md`（PR 前の確認の項 14 を `lint-plan-consistency.py --entry requirements` に替え、runner の表から外した）

#### User Action Required

- `scripts/lint-existing-code-reading.py` を手で呼んでいた場合は、`scripts/lint-plan-consistency.py --entry requirements <requirements.md>` に替える。見るものは違い、こちらは AC と承認ポイントの項目に `根拠:`・`計測:` の欄があるかを見る

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
