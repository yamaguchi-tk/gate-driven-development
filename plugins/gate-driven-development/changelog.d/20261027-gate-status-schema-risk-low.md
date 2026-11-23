---
type: patch
---

#### Summary

- `references/gate-status-schema.md` の `evidence` の説明で、`Human Check Status` の `approved` に使える evidence の一覧に `risk-low:<記録のファイル>`（リスクの段が `低` と読める steering だけ）を足した。同じファイルの `risk-low:` の段落と、steering の書き込み hook（`hooks/scripts/lib/risk_tier.py`）がすでに認めている形で、一覧だけが `human:`・`auto-confirm:` の 2 つになっていた。挙動は変わらない

#### Changed

- `references/gate-status-schema.md`（`evidence` の `approved` の行）

#### Affected Files

- `references/gate-status-schema.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
