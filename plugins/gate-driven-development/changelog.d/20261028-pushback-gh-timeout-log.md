---
type: patch
---

#### Summary

Stop hook のマージ待ちの押し返し（`hooks/scripts/lib/autonomy_pushback.py`）で、宣言の PR を読む `gh pr view` が 2 秒で打ち切られたら、`.gdd/hook-errors.log` に `gh: timed out after 2s` の行を残すようにした。これまでは何も残らなかった。押し返さないこと、done guard の判定、gh が無い・失敗したとき（記録しない）は変わらない。

あわせて、hook の記録（`.gdd/hook-errors.log`・`.gdd/hitl-lint.log`）の書き込みを、非ブロッキングで開いて通常のファイルにだけ書く形にした。記録先が FIFO だと、これまでは open が戻らず、Stop hook が timeout まで止まって done guard が走らなかった。記録先が通常のファイルなら挙動は変わらない。

#### Fixed

- `hooks/scripts/lib/autonomy_pushback.py`：gh の打ち切り（`subprocess.TimeoutExpired`）を、ほかの失敗と分けて記録する
- `hooks/scripts/lib/errors.py`：`append_log_record` は通常のファイルにだけ追記する。FIFO などの記録先では書かずに戻る

#### Added

- `tests/test_stop_hook_autonomy_pushback.py`：本物の遅い gh で打ち切りの行が 1 行残ること、gh が無い・失敗したときは残さないこと、記録の書き込みが落ちても押し返しの境界が None を返すこと、gh の打ち切りが押し返しの締め切りより短いこと、Stop hook の入口から打ち切りの行が残り done guard が block を出すこと（負荷で締め切りが先に来たときは skip）、記録先が FIFO でも Stop hook と締め切りの記録が止まらないこと
- `tests/test_errors_log_write.py`：`append_log_record` が通常のファイルに追記し、FIFO（読み手の有無とも）には書かずに戻ること

#### Affected Files

- `hooks/scripts/lib/autonomy_pushback.py`
- `hooks/scripts/lib/errors.py`
- `tests/test_errors_log_write.py`
- `tests/test_stop_hook_autonomy_pushback.py`

#### User Action Required

なし。`.gdd/` を ignore していない repo では、gh の打ち切りのたびに `.gdd/hook-errors.log` が現れることがある。

#### Validation / Eval Impact

関係するテスト（`scripts/light-lane-related-tests.py --run`）と `tests/validate-plugin.sh`。eval への影響は無い。
