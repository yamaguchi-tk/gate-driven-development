---
type: patch
---

#### Summary

hook の中の文字の扱いを UTF-8 にそろえた。これまで hook は利用者のロケールを受け継いでいた。UTF-8 以外のロケール（`ja_JP.eucJP` など）では、payload・state.md・tasklist.md の日本語を読めず、次のことが起きていた。

- pre-push gate：payload の読み取りの例外を握って push を通していた
- pre-PR gate：Linux では `python3 -c` の本文を decode できずに落ちて通し、macOS では awk・sed が日本語で落ちて壊れた理由で block していた
- worktree guard：例外で落ちて guard 全体が通っていた

どの hook も最初に source する `hooks/scripts/lib/kill-switch.sh` の末尾で `LC_ALL=C.UTF-8` と `PYTHONUTF8=1` を export し、hook の中の python を UTF-8 mode で、awk・sed・grep を `LC_ALL=C.UTF-8` で動かす。hook の外で使う `scripts/` の CLI は、この変更の対象外である。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/kill-switch.sh`
- `plugins/gate-driven-development/tests/_locale_support.py`
- `plugins/gate-driven-development/tests/test_hook_locale_utf8_contract.py`
- `plugins/gate-driven-development/tests/test_hook_multibyte_truncation_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_hook_locale_utf8_contract.py`：kill-switch.sh が 2 つの変数を export すること、`hooks.json` の入口がすべて python・awk・sed・grep より前に kill-switch.sh を source することを固定した。EUC-JP のロケールで入口（pre-push gate・pre-PR gate・worktree guard）を起動し、日本語の payload・state.md で block すべき操作が block されることを見るテストを足した。EUC-JP のロケールが無い環境では localedef で作り、CI では用意できなければ skip せずに落とす
- `tests/test_hook_multibyte_truncation_contract.py`：入口では kill-switch.sh がロケールを上書きするので、C ロケールでの切り詰めは lib を直接 source して見るテストと、自由記述を注入する 2 つの hook が `${var:0:N}` で切り詰めていないことを固定するテストを足した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
