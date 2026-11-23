---
type: patch
---

#### Summary

- implementation-gating の Steps の前に、`scripts/impl-gate-context.py --steering-dir <Steering Dir>` を 1 回回すようにした。script は、Steps が読む steering の節を出す。tasklist.md は、全節の索引（行の範囲）、冒頭の Agentic Worker Header、Current Task・Pending Tasks・Implementation Reviewer Selection・Review Status・Execution Plan・Refactor Gate Status の節、Completed Tasks の task 行と `was_valid: false` の `[Review Calibration]` を行番号つきで出す。ほかに state.md の Task Size・Route In Progress・Active Worktree Path、`<Steering Dir>/learned-patterns.md`（Step 5 の Cross-task と同じ置き場）の Rejected Alternatives、worklog.md の末尾 20 行、handoff の State Machine Impact と前回の gate の出力の見出しと判定の行を出す。runner は tasklist.md を通読せず、出力に無い節が要るときと Edit の前は、索引と出力の行番号の範囲だけを読む
- 節は done guard と同じく `## <名前>` の前方一致で決め、一致した節は全部出す（`## Pending Tasks（再オープン）` も Pending Tasks の節）
- Current Task・Pending Tasks・Implementation Reviewer Selection の節が無い、Current Task・Pending Tasks の task が done guard 側の数え方（`tasklist_parse.open_task_names`）と合わない、tasklist.md が読めない、fence が閉じていないときは、script は何も出さずに exit 1 で理由を出す。runner はそのとき従来どおり自分で読む
- Step 11 の tasklist の re-read は、script をもう 1 回回して `Pending Tasks` を確かめる形にした（exit 1 なら従来どおり tasklist.md を読む）
- learned-patterns.md を書く側（completion-check）は `docs/learned-patterns.md` に書くので、Step 5 と script が読む `<Steering Dir>/learned-patterns.md` は今までどおり見つからないことが多い。置き場はこの変更では揃えていない
- Implementation-Gating Template の `読むファイル:` から tasklist.md を外した
- gate の判定の規定（差し戻しの条件・`Gate Rounds`・Gate Batch）、model・effort、ほかの phase は変えていない。判定の入力の読み方は上のとおり変わる

#### Affected Files

- `scripts/impl-gate-context.py`（新規）
- `skills/gdd-implementation-gating/SKILL.md`（§ Steps の先頭、Step 2、Step 11）
- `references/subagent-dispatch.md`（Implementation-Gating Template）

#### User Action Required

なし

#### Validation / Eval Impact

- `tests/test_impl_gate_context.py`（新規）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
