---
type: patch
---

#### Summary

利用者から見える変更なし。state への書き込み境界の契約テスト `tests/test_peer_turn_write_boundary_contract.py` は、1 ファイル 1,500 行の目安と関数の数の fail 上限（80）を超えていた。そこで、`Origin Session` の write-once を `tests/test_origin_session_write_once_contract.py` へ分けた。実 hook の stdin 経路で配線を確かめる 3 class は、`tests/test_peer_turn_write_boundary_e2e_contract.py` へ分けた。class と関数の本体は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/test_peer_turn_write_boundary_contract.py`
- `plugins/gate-driven-development/tests/test_origin_session_write_once_contract.py`
- `plugins/gate-driven-development/tests/test_peer_turn_write_boundary_e2e_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 分けた 3 ファイルで収集したテストの件数と、class 名・テスト関数名の一覧が、merge-base の元のファイルと一致することを確かめた
- 移した class・関数・定数の本体が merge-base と一致することを、AST のソース比較で確かめた
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` で起動しても、共有 fixture を解決できることを確かめた
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
