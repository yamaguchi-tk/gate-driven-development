---
type: patch
---

#### Summary

利用者から見える変更なし。pre-push gate の契約テスト `tests/test_pre_push_gate_contract.py` が 1 ファイル 1,500 行の目安を超えていたので、共有 fixture の mixin `tests/_pre_push_gate_support.py` と、関心ごとの 3 ファイル（起動の短絡と active の判定 / opt-out とその記録 / steering の解決から証跡の照合・block reason・配線）に分けた。テスト関数の本体は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/_pre_push_gate_support.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_activation_contract.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_optout_contract.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`（docstring の参照先だけ）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q` の件数とテスト関数名の一覧が、merge-base と一致することを確認した
- 移したテスト関数・helper の本体が merge-base と一致することを、AST のソース比較で確認した
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` の起動でも共有 fixture を解決できることを確認した
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
