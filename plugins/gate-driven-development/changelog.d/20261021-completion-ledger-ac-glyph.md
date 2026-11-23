---
type: patch
---

#### Summary

- `check-completion-mechanical.py --ledger` は、AC Trace Ledger（`ac-ledger.md`）で受け付ける行を、空行・表の区切り・Ledger の見出し・Ledger の行（AC ID の欄が requirements.md の AC で、ほかの欄に別の AC ID が無い行）だけにした。それ以外の行（`>` の注記・見出し・箇条書き・別の表・fenced code block の行・欄の数が合わない行など）があれば、`ac-source` を invalid で出して gate に読ませる。これまで読み飛ばしていた、AC を含まない注記・見出し・別の表と、AC の有無によらず fenced code block の行も gate に回る。読めない行の後に verified の行を追記しても ok には戻らない（欄の中の逃がし忘れた `|` を `\|` に直すのは、結果の書き換えではないので、その行を直して読める行に戻してよい）
- `references/ac-trace-ledger.md` に、`ac-ledger.md` に置ける行と、注記の置き場所・欄の中の `|` の逃がし方を書いた

#### Changed

- `hooks/scripts/lib/completion_trace.py`（`ledger_errors` が受け付ける行を許可リストにした）
- `scripts/check-completion-mechanical.py`（`ledger_errors` に境界なしの AC ID の式を渡す）
- `references/ac-trace-ledger.md`・`skills/gdd-completion-check/SKILL.md`（`ac-ledger.md` に置ける行）

#### Affected Files

- `hooks/scripts/lib/completion_trace.py`
- `scripts/check-completion-mechanical.py`
- `references/ac-trace-ledger.md`
- `skills/gdd-completion-check/SKILL.md`
- `tests/test_check_completion_mechanical.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_check_completion_mechanical.py`（注記・見出し・別の表・ほかの欄の別の AC・ASCII でない数字の AC・fence の行・壊れた形の行を gate に返す）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
