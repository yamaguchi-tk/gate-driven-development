---
type: patch
---

#### Summary

利用者から見える変更なし。Stop hook の E2E テスト 2 ファイルの docstring を中身に合わせた。

- `tests/test_stop_hook_e2e.py`: 主題の列挙に「worktree の分離」「terminal の除外」を足し、残っている 8 class と一致させた
- `tests/test_stop_hook_e2e_block_content.py`: 「確かめる本体」に、「次の計画」のブロックを実装する `lib/next_plan_check.py`・`lib/post_merge_continuation.py` と、continuation の reason の文言を持つ `lib/constants.py` を足した。変更したファイルの名前で関係するテストを grep で選ぶ手順で、これらのモジュールを変えたときにもこのファイルが選ばれる

#### Affected Files

- `plugins/gate-driven-development/tests/test_stop_hook_e2e.py`
- `plugins/gate-driven-development/tests/test_stop_hook_e2e_block_content.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 足したモジュール名それぞれの grep で `tests/test_stop_hook_e2e_block_content.py` が選ばれることを確かめた
- 変更したファイルと、それを参照するテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
