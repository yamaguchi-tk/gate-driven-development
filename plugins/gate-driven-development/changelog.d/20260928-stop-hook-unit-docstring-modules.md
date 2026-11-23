---
type: patch
---

#### Summary

利用者から見える変更なし。Stop hook の単体テスト 4 ファイルの docstring に、テストが名前・パスで直接参照する本体のモジュール（`hooks/scripts/` の下）を書いた。変更したファイルの名前で関係するテストを grep で選ぶ手順で、`lib/guards.py`・`lib/constants.py`・`lib/tasklist_parse.py` などを変えたときにも、そのモジュールを確かめるファイルが選ばれるようにするため。起動した hook の script が `source` する lib（`run-session-start-hook.sh` が読む `lib/detect-steering.sh` など）のように、間接的にだけ届くモジュールは一覧に入れていない。

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_state_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_continuation_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_stop_reason_unit.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 各ファイルが直接使う本体のモジュールを、import・共有 fixture が再公開する名前の定義元・`gdd_stop_hook` 経由の再公開・`hooks/scripts` の下のファイル名の文字列（class の docstring を含み、`#` のコメントは含まない）から割り出し、そのモジュール名の grep で各ファイルが選ばれることを、ファイルごとに確かめた
- 変更したファイルと、それを参照するテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
