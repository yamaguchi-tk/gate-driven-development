# AC Trace Ledger

GDD の差別化軸である **要件 -> AC -> task -> verification -> review -> completion** の追跡正本。superpowers の standalone discipline と異なり、GDD は AC の状態を workflow artifact として保持し、completion / resume / PR follow-up で再利用する。

## Minimal AC Trace Ledger

最初の実装では、重い台帳にしない。以下の最小項目だけを必須にする。置き場所は steering の専用ファイル `.steering/<slug>/ac-ledger.md` にする。このファイルには Ledger だけを置き、tasklist.md・worklog.md には Ledger の節を作らない。行を足すときは、ファイルの末尾に足す。

| Field | Meaning |
|---|---|
| `AC ID` | `requirements.md` の accepted AC ID |
| `対応タスク` | `tasklist.md` の task ID または `not_started` |
| `検証コマンド/結果` | fresh command / reviewer evidence / external evidence と pass/fail |
| `status` | `unverified` / `verified` / `failed` / `blocked` / `deferred-human` |
| `last verified at/phase` | 最後に検証した phase と時刻。例: `gdd-completion-check @ 2026-06-06T00:00:00Z` |
| `未解決リスク` | なし / external pending / human decision / flaky / scope drift など |

推奨フォーマット（`ac-ledger.md` の中身）:

```markdown
## AC Trace Ledger

| AC ID | 対応タスク | 検証コマンド/結果 | status | last verified at/phase | 未解決リスク |
|---|---|---|---|---|---|
| AC-01 | T-1 | `pytest tests/test_api.py::test_cursor` -> pass | verified | gdd-completion-check @ 2026-06-06T00:00:00Z | なし |
```

## In-Progress AC Trace Updates

AC Trace Ledger は completion でまとめて埋める資料ではなく、TDD / implementation loop の途中から更新する。completion の時点で `ac-ledger.md` か AC の行が無いときだけ、completion-check が Part B の fresh verification の結果から追記する（下の compact / resume の段落と `skills/gdd-completion-check/SKILL.md` § AC Trace Ledger Gate）。更新は **append-only** とし、古い row を silent に上書きしない。

必須更新ポイント:

- `RED-created`: `gdd-test-driven-development` で RED Evidence を作成した時点で追記する。まだ実装後検証ではないため `status=unverified` とし、`検証コマンド/結果` には failing test / executable verification と期待 failure を記録する
- `GREEN-verified`: `gdd-subagent-driven-implementation` で RED が GREEN になった時点で追記する。fresh command が pass なら `status=verified`、失敗なら `status=failed`
- `REFACTOR-reverified`: REFACTOR チェックポイント後に同じ AC の verification を再実行し、結果を追記する。pass なら `status=verified`、回帰なら `status=failed`

追記例:

```markdown
| AC-01 | T-1 | RED-created: `pytest tests/test_api.py::test_cursor` -> expected fail | status=unverified | gdd-test-driven-development @ 2026-06-06T00:00:00Z | GREEN 未確認 |
| AC-01 | T-1 | GREEN-verified: `pytest tests/test_api.py::test_cursor` -> pass | verified | gdd-subagent-driven-implementation @ 2026-06-06T00:05:00Z | なし |
| AC-01 | T-1 | REFACTOR-reverified: `pytest tests/test_api.py::test_cursor` -> pass | verified | gdd-subagent-driven-implementation/refactor @ 2026-06-06T00:07:00Z | なし |
```

## Append-Only Rule

AC Trace Ledger は append-only を基本にする。修正が必要な場合は古い行を silent に書き換えず、同じ AC ID の新しい行を `ac-ledger.md` の末尾に追記し、`last verified at/phase` を更新する。履歴を圧縮する場合は completion 時に要約してよいが、検証根拠を失わない（`ac-ledger.md` には Ledger の行の形で書き、散文の要約や Round の注記は worklog.md に置く）。`ac-ledger.md` に置ける行は、空行・`AC Trace Ledger` だけの見出し（行頭から書く。`#` の数は問わないが、字下げ・ほかの語・大文字小文字の違いは読めない行になる）・Ledger の表（見出し・区切り・AC の行）だけにする。行の AC は `AC ID` の欄だけで決まるので、別の AC の結果をその行のほかの欄に書かない（`AC-1〜AC-7 は同値` のような参照も書かない）。欄の中の `|` は `\|` で逃がす。`ac-ledger.md` にこれ以外の行（注記・ほかの見出し・箇条書き・別の表・fence の行など）が 1 行でもあると、`check-completion-mechanical.py --ledger` は AC の判定をせず `ac-source` を invalid で出し、completion-check の gate が Ledger を読む。append-only なので、置いてしまった行は後から追記しても消えない（逃がし忘れた `|` を `\|` に直すのは、結果の書き換えではない）。tasklist.md・worklog.md の見出し（閉じた fence の外）に `AC Trace Ledger` があると、`ac-ledger.md` があっても `ac-source` を invalid で出す（旧来の置き場所の Ledger を読まずに ok にしないため）。worklog.md に注記を書くときも、見出しに `AC Trace Ledger` を含めない。

## Completion Gate Rule

completion gate MUST fail-closed in these cases:

- `requirements.md` に accepted AC があるが、AC Trace Ledger に missing ledger row がある
- `status=unverified` が残っている
- `status=failed` が残っている
- `status=blocked` / `deferred-human` が残っており、人間判断または外部前提が未解消
- `検証コマンド/結果` が空、または fresh evidence ではない
- AC drift があり、実装された外部観測可能な挙動が accepted AC に存在しない

停止時は `Next Action=gdd-completion-check` のままにし、未検証 AC と必要 evidence を列挙する。実装修正が必要な場合だけ `gdd-systematic-debugging` に戻す。

## Resume / Compact Recovery

会話履歴が欠落しても、`state.md / tasklist.md / worklog.md / ac-ledger.md`（AC Trace Ledger）から以下を復元する。

- どの AC が verified / unverified / failed か
- どの task が AC を担当しているか
- 次に実行すべき verification
- completion に進めない blocker

compact / resume 後に AC Trace Ledger が無い場合、done 判定を信用しない。`gdd-status` は ledger 欠落を integrity issue として出し、completion-check は ledger の作成または再検証を要求する。
