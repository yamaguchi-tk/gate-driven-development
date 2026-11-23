---
type: patch
---

#### Summary

- GDD を別のリポジトリ（同じ `plugins/gate-driven-development` の配置で、root に独自の `docs/adr/` を持つもの）へ同期したときに、`test_verification_closed_grammar_release_notes_contract.py` の `SupersedingAdrContractTests::test_new_adr_file_exists` が落ちなくなった。repo root の `docs/adr/` を検査するかを、`docs/adr/` の有無ではなく、`review-log-present.sh`・`version-not-consumed.sh` と同じ `scripts/lib/repository_identity.py`（`.claude-plugin/marketplace.json` の name が `gate-driven-development` か）で決める。manifest が読めないときは skip せずに落ちる

#### Affected Files

- `plugins/gate-driven-development/tests/test_verification_closed_grammar_release_notes_contract.py`

#### User Action Required

- なし（同期先で ADR を写して回避していたなら、その ADR は不要になる）

#### Validation / Eval Impact

- 追加: `CanonicalRepoRootTests`（判定の関数の 5 本〔name が一致・別の marketplace で `docs/adr/` あり・manifest なし・配置が違う・manifest が読めない〕と、`SupersedingAdrContractTests` を通して skip・失敗・error になる 3 本）
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
