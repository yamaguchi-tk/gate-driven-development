---
type: patch
---

#### Summary

`setup-gdd-loop.sh` がロックのメッセージに出す `Existing session last active:` の時刻の読み方を直した。transcript の行を `\n` だけで分ける（U+2028 などを含む記録も読む）。日付として正しくない `timestamp` はその記録だけを飛ばし、全体を `unknown` にしない。同じ秒の中は秒の下の桁で比べる。経過時間は 1 時間未満なら分（`25m ago`）、未来の時刻なら `in the future` と出し、ローカル時刻も添える（`(5h ago; local time 2026-10-15 14:00 JST)`）。transcript から時刻が取れないときは、state の `started_at` を下限として添える。案内の行は、この時刻の行をユーザーに見せるよう求める。`commands/gdd-dev.md` の手動の手順（手順 2）で止まるときも、持ち主の時刻を添えるよう求める（取り方は `docs/TROUBLESHOOTING.md` に書いた。経過時間・ローカル時刻は求めない）。

#### Affected Files

- `plugins/gate-driven-development/scripts/setup-gdd-loop.sh`
- `plugins/gate-driven-development/commands/gdd-dev.md`（手動の手順で止まるときに時刻を添える）
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`（復帰の手順に時刻の行の読み方を足す）
- `plugins/gate-driven-development/docs/SECURITY.md`（信頼境界に、ロックの分岐が別の session の transcript の末尾を読むことを足す）
- `plugins/gate-driven-development/tests/test_setup_gdd_loop_lock_last_active.py`
- `plugins/gate-driven-development/tests/test_setup_gdd_loop_session_lock.py`・`tests/test_setup_gdd_loop_project_root.py`（実際の `~/.claude/projects` を走査しないようにする）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_setup_gdd_loop_lock_last_active.py`（`setup-gdd-loop.sh` を入口にして、行の区切り・正しくない日付・同じ秒・1 時間未満の分・未来の時刻・ローカル時刻・transcript が無いときの started_at・案内の文に加え、1 MiB を超える transcript・dir の読む順・`CLAUDE_CONFIG_DIR` があるときに HOME を読まないこと・入れ子の timestamp の位置を確かめる）
- `tests/test_setup_gdd_loop_session_lock.py`・`tests/test_setup_gdd_loop_project_root.py`（ロックの文と、変えた起動の環境）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
