---
type: patch
---

#### Summary

PreCompact hook が要約器へ渡す文の session の判定を、UserPromptSubmit・plan-reread と同じにした（SessionStart の Safe Resume とは、local state が無いとき・今の session id が取れないとき・ブランチの判定が違う）。

- 別 session の steering（local state の `session_id` が今の session と違う、または空）の状態は渡さない。判定は `gdd_session_continuity_ok` で、今の session id が取れない runtime、local state が無い steering、`GDD_STEERING_DIR` を env で渡した起動では今までどおり渡す
- `Resume From` も `Next Action` と同じく、`|` 以降（evidence など）を落として渡す

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-compact-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/kill-switch.sh`（コメントだけ）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_compact_without_auto_resume.py`：別 session の steering では何も出さないこと・同じ session では出すこと、`Resume From` の `|` 以降を落とすこと、固定の文を全文で固定するテストを足した。EUC-JP のロケールのテストは `tests/_locale_support.py` の用意を使い、値に日本語を入れた
- `tests/test_hook_locale_utf8_contract.py`：hook の中のリテラルの `python3 -I` などの起動に `-X utf8` があることを固定した（変数で起動する python は見ない）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
