---
type: patch
---

#### Summary

- 利用者から見える変更なし。並列の全量テストの負荷対策（`hang_guard_seconds`）の後に、古いまま残っていた文書を今の動きにそろえた

#### Fixed

- `changelog.d/20261027-parallel-suite-load-flakes.md`: `MergeIntentAfterMergeDenialTest` で入口から起動するテストの本数を、陽性対照を含めた 4 本に直した。Summary の review-followup nudge の書き方（打ち切りを「替えた」）を、Changed の節（「足した」）にそろえた
- `tests/test_timing_budget_contract.py` の冒頭の説明: 固定する契約の一覧と Contract Surface Coverage に `hang_guard_seconds()` を足した
- `docs/learned-patterns.md`（repo 直下）: 「hook のテストは本番と同じ timeout で起動する」の項に、今は打ち切りを `hang_guard_seconds` にしていることを追記した
- `docs/adr/2026-09-12-x37-test-timing-flakiness.md`（repo 直下）: Decision 5 の「既定は 10 秒」に 2026-10-27 の変更を添え、既知の穴「`timeout=` は固定されていない」を `HangGuardSecondsTests` で閉じたと書いた

#### Affected Files

- `changelog.d/20261027-parallel-suite-load-flakes.md`
- `tests/test_timing_budget_contract.py`
- `docs/learned-patterns.md`（repo 直下）
- `docs/adr/2026-09-12-x37-test-timing-flakiness.md`（repo 直下）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_timing_budget_contract.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
