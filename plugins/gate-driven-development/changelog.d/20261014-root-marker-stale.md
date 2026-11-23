---
type: patch
---

#### Summary

`setup-gdd-loop.sh` が別の session の `active: true` の state でロックするとき、持ち主の session が最後に動いた時刻と経過時間を `Existing session last active:` の行に出すようにした。時刻は Claude Code の transcript（`$CLAUDE_CONFIG_DIR` か `~/.claude` の `projects/*/<session_id>.jsonl`）の末尾の 1 MiB を 1 行ずつ JSON として読み、記録の top-level の `timestamp` の最大値から取る。session_id が英数字・`-`・`_` 以外を含むとき、transcript が無い・読めない・時刻が無いときは `unknown` と出す。ロックするかどうかは変えない。持ち主が `done` を出さずに止まった（週の上限・放置など）state が `active: true` のまま残ったとき、まだ動いているかをすぐ判断できるようにするため。

#### Affected Files

- `plugins/gate-driven-development/scripts/setup-gdd-loop.sh`（ロックのメッセージに持ち主の最後の記録の時刻を足す）
- `plugins/gate-driven-development/tests/test_setup_gdd_loop_lock_last_active.py`

#### User Action Required

- なし。ロックで止まったら、`Existing session last active:` の時刻を見て、持ち主が動いていなければ state の `active:` を `false` にする（今までと同じ抜け方）

#### Validation / Eval Impact

- `tests/test_setup_gdd_loop_lock_last_active.py`（`setup-gdd-loop.sh` を入口にして、時刻を出すこと、読めない各ケースで `unknown` と出すこと、どの場合もロックのままであることを確かめる）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
