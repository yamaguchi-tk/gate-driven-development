---
type: patch
---

#### Summary

- AC Trace Ledger の `check-completion-mechanical.py --ledger` の文書を、旧#559 の挙動（Ledger の表のほかの行は `ac-source` で gate に返す）に合わせた。`skills/gdd-completion-check/SKILL.md` の `ac-source` の場合の列挙は、`ac-ledger.md` に置ける行の正本（`references/ac-trace-ledger.md` § Append-Only Rule）を指す形にした。注記の置き場所は worklog.md にした（定義の無い「`worklog.md` の退避の節」を消した。Ledger は専用ファイル `ac-ledger.md` に置く）。`ac-ledger.md` に置ける行に空行を明記した
- 未リリースの変更断片 2 つ（`20261021-completion-mechanical-ac-coverage.md`・`20261021-completion-ledger-ac-glyph.md`）の、撤去した `ac-ledger` invalid の挙動と、fence の行・`\|` の直し方の書き漏れを直した

#### Changed

- `skills/gdd-completion-check/SKILL.md`（AC Trace Ledger Gate の `ac-source` の場合）
- `references/ac-trace-ledger.md`（注記の置き場所）
- `scripts/check-completion-mechanical.py`（先頭の説明に Ledger の `ac-source` を足した。挙動は変えない）

#### Affected Files

- `skills/gdd-completion-check/SKILL.md`
- `references/ac-trace-ledger.md`
- `scripts/check-completion-mechanical.py`
- `changelog.d/20261021-completion-mechanical-ac-coverage.md`
- `changelog.d/20261021-completion-ledger-ac-glyph.md`
- `tests/test_check_completion_mechanical.py`（テスト名とコメントを挙動に合わせた。assert は変えない）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_check_completion_mechanical.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
