---
type: patch
---

#### Summary

Stop hook の押し返し（`hooks/scripts/lib/autonomy_pushback.py`）の判定を締め直した。

- 締め切りは、押し返しに使った時間の合計（3 秒）と、モジュールの読み込みからの上限（6 秒）の小さいほうで決める。HITL lint などの前処理の時間は 3 秒に数えないので、前処理が 6 秒未満なら human check の押し返しが判定まで届く
- 判定は thread で行い、押し返しの記録は締め切りに間に合った後に書く。間に合わなかった判定は記録を残さない。打ち切りと例外は `.gdd/hook-errors.log` に残す
- マージ待ちの押し返しは、Write・Edit・MultiEdit の tool_use でこの worktree の今の宣言を書いたセッションにだけ届く。読んだだけのセッション、別のセッションが書き直した宣言、Bash・ApplyPatch・subagent で書いたセッションには届かない
- checks が無いときは CI を `no-checks` と書き、pending と同じく待たせる。理由文は、マージするかどうかを宣言の原文と repo・タスクのマージ手順で決めるよう書き、hook の側からマージの許可を足さない
- 宣言の `repo`・`then` が null なら、省略と同じに扱う（`false`・`0` などは今までどおり不正な宣言）

#### Changed

- `hooks/scripts/lib/autonomy_pushback.py`、`hooks/scripts/gdd_stop_hook.py`：上の判定
- `references/post-merge-qa.md` 手順 2：宣言は worktree の toplevel の `.claude/` に Write ツールで書くこと、押し返さない条件を書いた
- `references/state-machine.md` § Stop hook の判定順序：マージ待ちと human check の押し返しを足した
- `hooks/hooks.json` の description：human check の押し返しと、締め切りの説明を足した

#### Affected Files

- `hooks/hooks.json`
- `hooks/scripts/gdd_stop_hook.py`
- `hooks/scripts/lib/autonomy_pushback.py`
- `references/post-merge-qa.md`
- `references/state-machine.md`
- `tests/test_stop_hook_autonomy_pushback.py`

#### User Action Required

- マージ待ちの宣言を Bash で書いていたら、Write ツールで書く

#### Validation / Eval Impact

- `tests/test_stop_hook_autonomy_pushback.py`
- 関係する Stop hook のテスト（`scripts/light-lane-related-tests.py`）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
