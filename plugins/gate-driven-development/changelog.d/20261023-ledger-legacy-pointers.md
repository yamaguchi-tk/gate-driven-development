---
type: patch
---

#### Summary

- `## Verification` の schema 違反で done guard が出す回復の案内と、`skills/gdd-ac-verification/SKILL.md`・`references/self-contained-contract.md` の同じ規定が、検証行を移してよい例外を `## AC Trace Ledger` の節ではなく `ac-ledger.md`（AC Trace Ledger）と名指すようにした。Ledger を専用ファイルに移した後も tasklist.md の `## AC Trace Ledger` の節を正規の置き場所として案内し、従うと以後毎回 `check-completion-mechanical.py --ledger` が `ac-source` になっていた

#### Changed

- `hooks/scripts/lib/done_block_message.py`（回復の案内の文。block / allow の判定は変えない）
- `skills/gdd-ac-verification/SKILL.md`（`## Verification` 節の規定の例外）
- `references/self-contained-contract.md`（同上）

#### Affected Files

- `hooks/scripts/lib/done_block_message.py`
- `skills/gdd-ac-verification/SKILL.md`
- `references/self-contained-contract.md`
- `tests/test_verification_block_message_contract.py`
- `tests/test_check_completion_mechanical.py`（Ledger の節を前提にしたテスト名とコメントを `ac-ledger.md` に合わせた。assert は変えない）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_verification_block_message_contract.py`（回復の案内が `ac-ledger.md` を名指し、`## AC Trace Ledger` を案内しない）
- `tests/test_check_completion_mechanical.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
