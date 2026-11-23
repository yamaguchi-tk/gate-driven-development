---
type: patch
---

#### Summary

`scripts/check-gate-ledger.sh` の `reviewed-by` 行を完了タスクごとに出すようにし、サイズ上限で `worklog.md` へ移すときの「戻す」規則を、移す前の出力の行が移した後にも全部あるかで決める形にした。今までは、完了タスクを丸ごと移したとき・要約で見出しの形が崩れたとき・既に 1 タスク欠けている tasklist で別のタスクの `Reviewed by:` を落としたときに、戻す規則が働かなかった。

#### Changed

- `reviewed-by` 行を完了タスクごとに 1 行出す（`ok` / `missing` / `invalid`）。completion-check の Step 2a を通る Task Size で `## Completed Tasks` に完了タスクが 0 件なら、`n/a` ではなく `missing` にする
- サイズ上限の deny 文言（`SIZE_DENY_SUFFIX`）と `references/state-field-tiers.md` は、移す前と後に検算スクリプトを `--steering <その steering>` つきで走らせて出力を比べ、移す前の行が 1 行でも移した後に無ければ（ok の行が消えた、`missing` / `invalid` / `n/a` になった）移した行を戻すよう案内する。戻す手順は移した行を戻すだけで、移す前から欠けていた行を直す手順ではないことを明記した
- `steering` 行の gate 列には、解決がそろわない gate だけを入れる（pre-push の解決が `none`・`multiple` のときは pre-push を入れない。hook はそれぞれ検査せずに通す・tip の証跡で選ぶ）。`multiple` で tip の証跡を持つ steering が 1 件に決まらないときは hook が止めるが、この行は pre-push を挙げない（hook の選び方を写していない）
- 検算スクリプトは hook と同じく `LC_ALL=C.UTF-8`・`PYTHONUTF8=1` で走り、python は `-X utf8` で起動する
- サイズ超過の警告文と WHY 行の「圧縮」を、書き換えずに worklog / adr へ移す案内にそろえた
- `references/state-field-tiers.md` の、残す行（field の現在値）と移す行（置き換わった古い値・履歴）の書き分けをそろえた。`references/self-review-lanes.md` の、`gh pr create` の前に解消する行の範囲を completion-check と同じ（gate 列が `pre-PR` か `completion-check`）にした
- `lib/tasklist_parse.py` の `completed_tasks_missing_reviewed_by` を、タスクごとの状態を返す `completed_tasks_reviewed_by` に置き換えた

#### Affected Files

- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/tasklist_parse.py`
- `plugins/gate-driven-development/hooks/scripts/lib/steering_size.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`
- `plugins/gate-driven-development/tests/test_completed_tasks_reviewed_by.py`
- `plugins/gate-driven-development/tests/test_hook_locale_utf8_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_check_gate_ledger.py` に、完了タスク 0 件が `missing` になること、既に 1 タスク欠けている tasklist で別のタスクの行を落とすと移した後にだけ現れる行が出ること、`steering` 行の gate 列が止まる gate だけを挙げること、`--base` の短い名前を `origin/` の側から解くこと、symlink を通した `--steering` が実体のパスで一致すること、`Independent Review` の書式不正の行が理由を出すこと、pre-push の解決が `none` のとき gate 列に pre-push を挙げないこと、1 タスクのブロックを移すとその ok 行が消えること、EUC-JP のロケールでも行を UTF-8 で出すことのテストを足した
- `tests/test_hook_locale_utf8_contract.py` の、`-I` の python に `-X utf8` を付ける検査の対象に `scripts/check-gate-ledger.sh` を足した
