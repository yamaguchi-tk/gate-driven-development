---
type: patch
---

#### Summary

- pre-PR gate（`gh pr create` などの前に動く hook）が起動する python3 を減らした。コマンドの解析の結果を 1 回の python3 から受け取り、欄ごとに python3 を起動し直さない。PR 作成でないコマンドでは 3 回から 1 回、PR 作成のコマンドでは 18 回から 5 回になる（Task Size が quick (express) の steering のとき）
- PR 本文に対になっていない UTF-16 のサロゲート文字（lone surrogate）があるときも、本文の機密検査と `--head` の照合を行う。これまでは本文が空として扱われ、検査を通っていた
- merge gate（`gh pr merge` の前に動く hook）が origin 以外の remote の set-default を読むループに、here-string（`<<<`）を使わない。here-string は一時ファイルで作られることがあり、作れない環境（ディスクフルなど）では、ループを飛ばして origin の PR として照合し、外れると merge を通していた

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_single_parse.py`
- `plugins/gate-driven-development/tests/test_here_string_read_failure.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 追加: `test_pre_pr_gate_single_parse.py`（python3 の起動回数、NUL・改行をはさんだ機密候補、lone surrogate を含む本文と `--head`、解析が例外で終わる・結果を出さずに終わるときに止まること）
- 追加: `test_here_string_read_failure.py`（2 つの hook のループがリダイレクトを使わないこと、解析の出力が空なら active GDD の中で止まること）
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
