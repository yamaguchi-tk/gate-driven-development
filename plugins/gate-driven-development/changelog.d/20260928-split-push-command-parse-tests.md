---
type: patch
---

#### Summary

利用者から見える変更なし。`hooks/scripts/lib/push_command_parse.py` の単体テスト `tests/test_push_command_parse.py`（1,703 行・関数 154）は、1 ファイル 1,500 行の目安と関数の数の fail 上限（80）を超えていた。そこで主題ごとに次の 4 ファイルへ分けた。

- 字句・分割: `tests/test_push_command_parse_lexing.py`
- `git push` の検出: `tests/test_push_command_parse_push_detection.py`
- push 対象の解決: `tests/test_push_command_parse_push_target.py`
- opt-out と副作用の無い push: `tests/test_push_command_parse_optout.py`

git global option と `git push` option の一覧を実 git・実 bash と突き合わせるテストは、`hooks/scripts/lib/git_command_parse.py`・`push_command_parse.py` のコメントがこのファイルを名指ししているので、元のファイルに残した。class と関数の本体は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/test_push_command_parse.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_lexing.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_push_detection.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_push_target.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_optout.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 分けた 5 ファイルで収集したテストの件数と、class 名・テスト関数名の一覧が、merge-base の元のファイルと一致することを確かめた
- 移した class・関数・定数の本体が merge-base と一致することを、AST のソース比較で確かめた
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` で起動しても、共有 fixture を解決できることを確かめた
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
