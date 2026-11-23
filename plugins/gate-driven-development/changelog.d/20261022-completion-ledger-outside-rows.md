---
type: patch
---

#### Summary

- AC Trace Ledger の置き場所を、steering の専用ファイル `.steering/<slug>/ac-ledger.md` にした。`check-completion-mechanical.py --ledger` は、このファイルの全体を許可リストで読む。置ける行は、空行・`AC Trace Ledger` だけの見出し・Ledger の表（見出し・区切り・AC の行）で、それ以外の行（注記・ほかの見出し・箇条書き・別の表・fence の行など）が 1 行でもあれば、`ac-source` を invalid で出して gate に読ませる。行はファイルの末尾に足す
- tasklist.md・worklog.md の見出し（閉じた fence の外）に `AC Trace Ledger` が残っていれば、`ac-ledger.md` があっても `ac-source` を invalid で出す（旧来の置き場所の Ledger を読まずに ok にしない）。`ac-ledger.md` が無ければ missing。`ac-ledger.md` がディレクトリ・指す先の無い symlink・UTF-8 でないときは error
- 挙動の変化: これまで tasklist.md・worklog.md の `## AC Trace Ledger` の節に Ledger を置いていた steering は、`ok` から `ac-source` になり、gate が Ledger を読む。completion-check は、`ac-ledger.md` が無ければ、Part B で pass した AC の行を `ac-ledger.md` に書く。注記・Round の要約は worklog.md に、見出しに `AC Trace Ledger` を含めずに書く
- TDD（`RED-created`）・実装（`GREEN-verified`・`REFACTOR-reverified`）・completion-check の追記先を `ac-ledger.md` にした。`collect-gdd-telemetry.py` の件数は `ac-ledger.md` も数える

#### Changed

- `hooks/scripts/lib/completion_trace.py`（`ledger_errors` が `ac-ledger.md` の全体を読む。`legacy_ledger_headings` を足した）
- `scripts/check-completion-mechanical.py`（`--ledger` の読み先）・`scripts/collect-gdd-telemetry.py`
- `references/ac-trace-ledger.md`（置き場所・置ける行）、Ledger に追記する skill と、復帰正本の列挙

#### Affected Files

- `hooks/scripts/lib/completion_trace.py`
- `scripts/check-completion-mechanical.py`
- `scripts/collect-gdd-telemetry.py`
- `references/ac-trace-ledger.md`・`references/context-budget.md`・`references/gate-checklists.md`・`references/subagent-dispatch.md`
- `skills/gdd-completion-check/SKILL.md`・`skills/gdd-test-driven-development/SKILL.md`・`skills/gdd-subagent-driven-implementation/SKILL.md`・`skills/gdd-status/SKILL.md`
- `tests/test_check_completion_mechanical.py`・`tests/test_p0_p1_operational_hardening_contract.py`

#### User Action Required

- 進行中の steering で tasklist.md・worklog.md に `## AC Trace Ledger` の節があるなら、completion-check の gate がその Ledger を読む（ok にはならない）。新しい行は `ac-ledger.md` に書く

#### Validation / Eval Impact

- `tests/test_check_completion_mechanical.py`（`ac-ledger.md` の末尾に、注記・6 欄の別の表・別の見出しの Ledger の表・区切りが続く行・AC を含む `AC ID` の見出し・引用の中の表・小文字の AC の後に足した failed の行を gate に返す。tasklist.md・worklog.md に残った Ledger の見出し〔階層・前後の語・大文字小文字・字下げ・引用・setext・`##` の後ろの全角スペース・NBSP・改行・閉じていない fence〕を gate に返し、閉じた fence の中の記入例と AC を含むほかの表は見ない。空・見出しだけのファイルは invalid、ディレクトリ・壊れた symlink・UTF-8 でないファイルは error）
- `tests/test_p0_p1_operational_hardening_contract.py`（telemetry が `ac-ledger.md` の Ledger を数える）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
