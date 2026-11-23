---
type: patch
---

#### Summary

利用者から見える変更なし（GDD を開発する人向け）。文書の表の行数と、テストが生成・収集する母集合の件数を `assertEqual(len(...), N)` で固定していたテストのうち、5 ファイルの分を改めた。表の行を足す・母集合を広げるたびにテストが落ちていたため。件数の固定は外し、ループや differential が空のまま通らないこと（空でない・受理と不受理の両側がある）と、表のキーが重複しないこと（`len(dict) == len(rows)`）だけを見る。本文が数を書いている表（3 レーン定義・効果測定）の行数は、本文の数と同じものなので固定のまま残す。reader が生成集合のうち受理する件数（bash の受理数・共有受理面の受理数）は、reader と生成集合の両方で決まるので固定のまま残す。

#### Affected Files

- `plugins/gate-driven-development/tests/test_root_branch_deny_corpus.py`
- `plugins/gate-driven-development/tests/test_self_review_lanes_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_progress_bind_scope_contract.py`
- `plugins/gate-driven-development/tests/test_tasklist_parse_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 変更した 5 ファイルの pytest と、空の母集合で空でないことの検査が落ちることの確認
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
