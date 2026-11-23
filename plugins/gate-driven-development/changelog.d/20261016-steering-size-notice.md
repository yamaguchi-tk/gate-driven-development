---
type: minor
---

#### Summary

steering write guard は、`.steering/` の `state.md` / `tasklist.md` / `design.md` への書き込みが size の上限（20,000 / 80,000 / 60,000 バイト）を超えて増えても、止めずに通知するようにした。今までは deny し、92% は subagent の書き込みだった。止められた後に Bash で同じファイルを書き換えた回避もあった。

- 通知は `[steering size] <ファイル名> is <バイト数> bytes after this write, over the <上限> byte limit.` に続けて、worklog.md への退避の手順を書く。agent に届く `additionalContext`（subagent にも届く）と、利用者の端末の `systemMessage` の両方に出す
- ほかの category（email・秘密情報など）の deny と、3 回続いて警告付きで通す回にも、同じ通知を本文に付ける。size は deny の理由にならず、降格の判定にも関わらない
- 減る書き込み・上限以下・算出できない書き込み（ApplyPatch など）には出さない。post-write サイズの算出は変えていない
- kill switch `GDD_STEERING_SIZE_DENY` は無くなった（設定しても読まない）。size の連続 deny の counter、無効化の告知、今までの advisory の `[artifact size]`（利用者の端末にだけ出ていた）も無くなった

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/steering_size.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/hooks/scripts/run-steering-write-hook.sh`（コメント）
- `plugins/gate-driven-development/docs/SECURITY.md`、`references/common-guardrails.md`・`config-defaults.md`・`reviewer-selection.md`・`inline-review-checklists.md`
- `docs/adr/2026-09-06-w36-task-ceremony-cost.md` と `plugins/gate-driven-development/docs/design/2026-09-06-w36-task-ceremony-cost-adr.md`（冒頭に追記）
- `plugins/gate-driven-development/changelog.d/20261004-autonomy-value-notes-followup.md`（kill switch の記述）

#### User Action Required

- `GDD_STEERING_SIZE_DENY` を設定しているなら、外してよい（読まれない）

#### Validation / Eval Impact

- `tests/test_steering_size_deny_contract.py`（入口から: 上限を超えて増える Write・Edit・MultiEdit は exit 0 で、additionalContext と systemMessage に通知が出る。ほかの category の deny と降格した allow の本文にも通知が付く。超えない・減る・算出できない書き込みには出ない。`[artifact size]` と kill switch の告知は出ない。算出の各ケースは超過かどうかを通知で確かめる）
- `tests/test_steering_deny_counter_contents.py`（size の counter を作らない）、`tests/test_impl_gate_precision_tiering_contract.py`、`tests/test_autonomy_value_notes.py`
- 効かなくなった `GDD_STEERING_SIZE_DENY` の設定を、テストから外した
