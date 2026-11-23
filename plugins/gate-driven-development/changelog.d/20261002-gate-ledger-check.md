---
type: minor
---

#### Summary

push・PR の前に、pre-PR gate・pre-push gate・completion-check Step 2a が要求する帳簿の行（`state.md`・`tasklist.md`）がそろっているかを一度に一覧する `scripts/check-gate-ledger.sh` を足した。今までは、hook が最初に欠けた 1 行で止まるので、どの行が欠けているかは止められて初めてわかった。読むだけで、何も書かない。あわせて、サイズ上限で `worklog.md` へ移すときの手順を、要約せず、gate が読む行を移さない形に直した。

#### Added

- `scripts/check-gate-ledger.sh`（`--root`・`--steering`・`--tip`・`--base`）。要求ごとに `状態<TAB>要求<TAB>gate<TAB>詳細` を 1 行出す。状態は `ok`・`missing`（行が無い）・`invalid`（値が条件を満たさない。例: sha が HEAD・push 対象の tip と違う、high・blocking が 0 でない）・`n/a`（Task Size で要求されない、active な marker が無い、完了タスクが無い）。`missing`・`invalid` があれば exit 1
  - 見る行: active marker、steering の解決（pre-PR と pre-push の解決が同じ 1 件にそろうか）、raw steering の除外、`Next Action=done`、`ADR distilled`、Task Size、`Pre-PR Self Review`、`Pre-Push Self Review`、`Independent Review`、完了タスクごとの `Reviewed by:`（`gdd-implementation-reviewer` を含むか）
  - 見ない行: Codebase Health・PR 本文の機密検査・`--head` の検査（帳簿の行ではない）、done guard の検査、`Reviewed by:` の judgment と conditional reviewer
- `hooks/scripts/lib/gate-ledger.sh`。pre-PR gate・pre-push gate の判定の述語（Task Size の正規化、`Next Action`、base ref の解決、`ADR distilled`、証跡の sha の一致、`Independent Review` の high・blocking、PR を作る steering の解決）を集めた。両方の hook と検算スクリプトがここを呼ぶ。hook の block / allow と block 文言は変わらない
- `lib/tasklist_parse.py` の `completed_tasks_missing_reviewed_by`

#### Changed

- サイズ上限の deny 文言（`lib/steering_size.py` の `SIZE_DENY_SUFFIX`）は、`state.md` の現在の field の行を全部残し、置き換わった古い値と履歴の行だけを書き換えずに移す（追記のみ・要約しない）よう求める。`tasklist.md` では `Next Action` と完了タスクの見出し・AC の対応・`Reviewed by`・結論を残す。`state.md`・`tasklist.md` では移す前と後に `check-gate-ledger.sh` を走らせ、移す前に ok だった行が missing / invalid になったら、移した行をそのまま戻すよう案内する
- `gdd-completion-check` の PR 作成の前と Step 2a、`references/self-review-lanes.md`（push・PR の前）、`references/state-field-tiers.md`（worklog へ移すとき）に、検算スクリプトの実行を足した

#### Affected Files

- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/tasklist_parse.py`
- `plugins/gate-driven-development/hooks/scripts/lib/steering_size.py`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`
- `plugins/gate-driven-development/tests/test_completed_tasks_reviewed_by.py`

#### User Action Required

- なし。push・PR の前に `bash <plugin>/scripts/check-gate-ledger.sh` を走らせると、hook に止められる前に欠けた行がわかる

#### Validation / Eval Impact

- `tests/test_check_gate_ledger.py` を足した。帳簿に変異（行の削除、sha を古い commit・解決できない sha・HEAD の短縮 sha にする、high・blocking を 1 にする、`dry: no`、`Next Action` を done 以外にする、`ADR distilled` の削除・diff に ADR の無い `yes`、`Reviewed by` の削除・`gdd-implementation-reviewer` の無い行、quick (express)、未知の Task Size）を入れ、pre-PR・pre-push の hook の block / allow と、検算スクリプトの gate ごとの行の状態が一致することを確かめる。`--tip`・`--steering` の扱い、何も書かないこと、deny 文言が検算スクリプトの読む field を全部挙げることも確かめる
- `tests/test_completed_tasks_reviewed_by.py` を足した
- 述語を lib へ移した後の回帰は、既存の `tests/test_pre_pr_gate_contract.py`・`tests/test_pre_push_*.py` で見る
