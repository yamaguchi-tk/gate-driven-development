---
type: patch
---

#### Summary

利用者から見える変更なし。分けたテストの docstring を、中身と実装に合わせた。

- `tests/test_push_command_parse_push_detection.py`・`_push_target.py`・`_optout.py`: 「確かめる本体」に `hooks/scripts/lib/git_command_parse.py` を足した。`tokenize` などは `git_command_parse` の定義を `push_command_parse` が再公開しているので、変更したファイルの名前で関係するテストを grep で選ぶ手順で、`git_command_parse` を変えたときにもこの 3 ファイルが選ばれる
- `tests/test_push_command_parse.py`: このファイルに置くテストの要約に、実 git を呼ばない `UnknownGlobalFlagPropertyTests`（一覧に無い global flag でも push を検出できること）を足した
- `tests/test_stop_hook_route_in_progress_canonical_form_contract.py`: 「確かめる本体」に、`Route In Progress` 行の読み取りを実装する `hooks/scripts/lib/tasklist_parse.py` を足した。あわせて、テスト 2 本の docstring の古い記述を今の実装に合わせた（fence の閉じ忘れは値を読まずに一律で block する、読み取りの関数は `tasklist_parse.route_value`）

#### Affected Files

- `plugins/gate-driven-development/tests/test_push_command_parse.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_push_detection.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_push_target.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_optout.py`
- `plugins/gate-driven-development/tests/test_stop_hook_route_in_progress_canonical_form_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `grep -rl git_command_parse plugins/gate-driven-development/tests/` が分けた 5 ファイルをすべて選ぶこと、`grep -rl tasklist_parse plugins/gate-driven-development/tests/` が `test_stop_hook_route_in_progress_canonical_form_contract.py` を選ぶことを確かめた
- 変更したファイルのテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
