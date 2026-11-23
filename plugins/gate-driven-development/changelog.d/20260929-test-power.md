---
type: patch
---

#### Summary

利用者から見える変更なし。検査の力を上げた: hook の入口の一覧が `.sh` でない command を黙って落とさず失敗する。EUC-JP のロケールの用意が、python が encoding の別名（`eucJP`・`ujis`）を返しても EUC-JP と読む（防御）。廃止した印を見つける正規表現を、選んだ前の文脈 16 通りと後ろの文脈 12 通りのすべての組み合わせで固定した。

#### Affected Files

- `plugins/gate-driven-development/tests/test_hook_locale_utf8_contract.py`
- `plugins/gate-driven-development/tests/_locale_support.py`
- `plugins/gate-driven-development/tests/test_locale_support.py`
- `plugins/gate-driven-development/tests/test_always_high_scope_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_hook_locale_utf8_contract.py`（`.sh` でない command で落ちる）、`tests/test_locale_support.py`（`is_euc_jp` の別名と近い codec）、`tests/test_always_high_scope_contract.py`（廃止した印の正規表現の全組み合わせ）
