---
type: patch
---

#### Summary

- 利用者から見える変更なし。hook を起動するテストの打ち切りを `hang_guard_seconds`（hooks.json の timeout の 6 倍）にした後も、古い規定や広すぎる書き方のまま残っていた文書を直した

#### Fixed

- `docs/learned-patterns.md`（repo 直下）: 「本番と同じ timeout で起動する」の項の更新の注記を見出しの直後に移した。見出しの原則がもう今の規定ではないことと、打ち切りを延ばしたテストは打ち切りでは本番の timeout に収まるかを見なくなることを書いた。どのテストが何秒で打ち切るかは書き写さず、正本をコード（`hang_guard_seconds` とその呼び出し元、各 helper の既定）にした
- `tests/test_timing_budget_contract.py` の docstring の 1 行目に `hang_guard_seconds()` を足した
- `docs/adr/2026-09-12-x37-test-timing-flakiness.md`（repo 直下）: Decision 5 の参照先を「Consequences の『2026-10-27 の変更』」に直した
- `docs/adr/2026-09-11-merge-gate-quoted-operator.md`（repo 直下）と `tests/test_merge_gate_hook_quoted_operator.py` の docstring: 「本番と同じ 10 秒」を当時のこととし、今の既定の打ち切りが `HANG_GUARD` であることを書いた

#### Affected Files

- `docs/learned-patterns.md`（repo 直下）
- `tests/test_timing_budget_contract.py`
- `docs/adr/2026-09-12-x37-test-timing-flakiness.md`（repo 直下）
- `docs/adr/2026-09-11-merge-gate-quoted-operator.md`（repo 直下）
- `tests/test_merge_gate_hook_quoted_operator.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_timing_budget_contract.py`
- `tests/test_merge_gate_hook_quoted_operator.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
