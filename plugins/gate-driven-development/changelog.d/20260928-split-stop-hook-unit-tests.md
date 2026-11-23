---
type: patch
---

#### Summary

利用者から見える変更なし。Stop hook の単体テスト `tests/test_stop_hook_unit.py` は、1 ファイル 1,500 行の目安と関数の数の fail 上限（80）を超えていた。そこで次の 3 つを別ファイルへ分けた。class と関数の本体は変えていない。

- state の parse・write と Resume From への fallback: `tests/test_stop_hook_state_unit.py`
- 継続の判定: `tests/test_stop_hook_continuation_unit.py`
- stop 理由・marker・post-merge 継続の誤検知: `tests/test_stop_hook_stop_reason_unit.py`

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_state_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_continuation_unit.py`
- `plugins/gate-driven-development/tests/test_stop_hook_stop_reason_unit.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 分けた 4 ファイルで収集したテストの件数と、class 名・テスト関数名の一覧が、merge-base の元のファイルと一致することを確かめた
- 移した class・関数・定数の本体が merge-base と一致することを、AST のソース比較で確かめた
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` で起動しても、共有 fixture を解決できることを確かめた
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
