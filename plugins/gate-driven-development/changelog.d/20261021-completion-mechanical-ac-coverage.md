---
type: minor
---

#### Summary

- `scripts/check-completion-mechanical.py` に 2 つの行を足した。`ac-coverage`（Step 4c）は、requirements.md の AC が tasklist.md・worklog.md の task の範囲（Current Task・Pending Tasks・Completed Tasks の節と task の見出しの下）の `AC:`・`Covers AC:` 欄に無いと invalid。Implementation Sequence Plan で `PR Boundary` が `follow-up-pr`・`post-merge-verification` の Stage にだけ置いた AC は除く。`follow-up-stage`（Step 4d）は、Planned Follow-up Stage Lane の 6 欄が空・`<...>` のまま、`Tracking Destination=none` に理由が無い、表でない、`- [ ]` の項目があるときに invalid（欄の中身は gate が読む）。行は Step の順（2a → 3 → 4 → 4c → 4c-3 → 4d → 5）に出す
- requirements.md の AC か PR Boundary を閉じた形で読めない（受入条件の節が無い、`- AC-n:` の定義が無い、節の AC ID を定義として読めない、Plan の PR Boundary が語彙に無い値）ときは、AC 集合で ok を出さず `ac-source` を invalid で出す。main は dispatch し、gate が読んで判定する
- `--ledger` を付けると、AC Trace Ledger の行（gate 列 `completion-check:ledger` の `ac-ledger`・`ac-source`）だけを出す。AC ごとに、最後の行の status が `verified` でない、検証コマンドが空、行が無いと invalid、Ledger の見出しに欄が欠けると invalid、`ac-ledger.md`（Ledger の専用ファイル）が無いと missing。`ac-ledger.md` に Ledger の表のほかの行（欄の数が合わない行・AC ID の欄が requirements.md の AC でない行・注記・見出し・別の表・fenced code block の行など。`references/ac-trace-ledger.md` § Append-Only Rule）があれば、AC の判定をせず `ac-source` を invalid で出し、gate が読む（読めない行の後に verified の行を追記しても ok には戻らない）。gate が Part B の後に回し、`ac-ledger.md` か AC の行が無ければ、Part B で pass した AC の行を `ac-ledger.md` に追記して回し直す（Checklist E の (iii) の例外。`references/gate-checklists.md`・`references/ac-trace-ledger.md` に書いた）
- main は、`ac-coverage` が invalid なら dispatch せずに止め（`gdd-task-breakdown` での再分割が要ると報告する）、`ac-source` と `follow-up-stage` は gate に任せる

#### Changed

- `scripts/check-completion-mechanical.py`（`ac-coverage`・`follow-up-stage` の行、`--ledger`）
- `hooks/scripts/lib/completion_trace.py`（新規。行の判定）
- `skills/gdd-completion-check/SKILL.md`（Step 4c・4d・AC Trace Ledger Gate を行で判定する）
- `references/subagent-dispatch.md`（§ Completion-Check の前の機械検査の (4a)・(5a)）
- `agents/gdd-completion-reviewer.md`（reviewer が指摘しない機械検査に 3 つを足した）
- `references/gate-checklists.md`・`references/ac-trace-ledger.md`（completion-check が Ledger を追記する例外）

#### Affected Files

- `scripts/check-completion-mechanical.py`
- `hooks/scripts/lib/completion_trace.py`
- `skills/gdd-completion-check/SKILL.md`
- `references/subagent-dispatch.md`
- `agents/gdd-completion-reviewer.md`
- `references/gate-checklists.md`
- `references/ac-trace-ledger.md`
- `tests/test_check_completion_mechanical.py`

#### User Action Required

- なし。動いているセッションの main は、root checkout を pull した後に読む references から新しい手順に従う

#### Validation / Eval Impact

- `tests/test_check_completion_mechanical.py`（新しい行の変異と fail-open のケース）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
