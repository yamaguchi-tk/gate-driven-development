---
type: patch
---

#### Summary

利用者から見える変更なし。`tests/test_review_followup_nudge_hook.py`（1,534 行・関数 49）は、1 ファイル 1,500 行の目安と関数の数の warn（40）を超えていた。そこで、1 つの class にあったテストを主題ごとに 3 ファイルへ分けた。

- `tests/test_review_followup_nudge_hook.py`: 基本の流れ・opt-out・記録・注入の文言・`hooks.json` への配線
- `tests/test_review_followup_nudge_hook_push_target.py`（新規）: push の検知と push 先 branch の解決
- `tests/test_review_followup_nudge_hook_gh.py`（新規）: `gh` の呼び出し・結果の分類・cache
- `tests/_review_followup_nudge_support.py`（新規）: 3 ファイルが共有する fixture（一時 repo・hook 起動・`gh` の stub）。`setUpClass`・`_init_repo`・`_run_hook` は `ReviewFollowupNudgeFixtureMixin` に移し、各ファイルの class が `unittest.TestCase` と一緒に継承する（`_pre_push_gate_support.py` と同じ形）

テスト関数・helper の本体は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/test_review_followup_nudge_hook.py`
- `plugins/gate-driven-development/tests/test_review_followup_nudge_hook_push_target.py`
- `plugins/gate-driven-development/tests/test_review_followup_nudge_hook_gh.py`
- `plugins/gate-driven-development/tests/_review_followup_nudge_support.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 分けた 3 ファイルで収集したテスト関数名の一覧と件数が、merge-base の元のファイルと一致することを確かめた
- 移したメソッド・関数・定数の本体が merge-base と一致することを、AST のソース比較で確かめた
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` で起動しても、共有 fixture の import を解決できることを確かめた
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
