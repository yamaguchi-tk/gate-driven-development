---
type: patch
---

#### Summary

利用者から見える変更なし。`tests/test_engineering_baseline_architecture_contract.py`（1,627 行）は、1 ファイル 1,500 行の目安を超えていた。そこで、`scripts/gdd-codebase-health.py` の baseline を pre-PR ref（merge-base）の実測値で検査する `TestCodebaseHealthPrePrRefMeasurement` を、`tests/test_codebase_health_pre_pr_ref_contract.py` へ分けた。class の本体は変えていない。helper の `git`・`load_codebase_health_module` は元のファイルに置いたまま、新しいファイルから名前だけを import する。

#### Affected Files

- `plugins/gate-driven-development/tests/test_engineering_baseline_architecture_contract.py`
- `plugins/gate-driven-development/tests/test_codebase_health_pre_pr_ref_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 分けた 2 ファイルで収集したテストの件数と、class 名・テスト関数名の一覧が、merge-base の元のファイルと一致することを確かめた
- 移した class の本体が merge-base と一致することを、AST のソース比較で確かめた
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` で起動しても、helper の import を解決できることを確かめた
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
