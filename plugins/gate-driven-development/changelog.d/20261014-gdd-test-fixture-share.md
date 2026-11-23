---
type: patch
---

#### Summary

- 利用者から見える変更なし。テストの全量の実行時間を縮めるため、テスト用の共有 fixture `init_repo` を変えた。同じ引数・同じ git の環境での 2 回目以降は、プロセスごとに 1 回だけ作った repo を複製し、日時を渡さないときは複製の後に commit の日時を呼んだ時刻にそろえる

#### Affected Files

- `plugins/gate-driven-development/tests/_git_fixture.py`
- `plugins/gate-driven-development/tests/test_git_fixture_template.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 追加: `test_git_fixture_template.py` の `InitRepoTemplateTests`（2 回目の git の起動回数、複製後の commit の日時、日時の指定、ホストの初期ブランチ名の差し替え、空でないディレクトリ）
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
