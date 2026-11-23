---
type: patch
---

#### Summary

- `state-machine.md` の terminal state の定義に、外部レビュー待ちの間の例外を書いた。`Next Action=done` が `Resume From=external-review-waiting` と併記されている間は終端ではなく、binding 経由の検出は、数え直さない呼び出し元では `Next Action=done` を終端にしない（数え直す gate は終端として数え直す）。実装（`detect-steering.sh`）と `gdd-pr-review-followup` の state 契約は変えていない

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 文書だけの変更。`validate-plugin.sh` で確認した
