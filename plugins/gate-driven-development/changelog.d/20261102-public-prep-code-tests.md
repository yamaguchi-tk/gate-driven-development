---
type: patch
---

#### Summary

- 公開に向けて、`hooks/`・`scripts/`・`tests/` のコメントと docstring、`CONTRIBUTING.md` と `pytest.ini` のコメントから、repo の外の計画書の項目番号（`X-NN`・`W-NN`）、手元の文書へのパス（`~/work/...`）、実測の値（運用の記録〔transcript・session・steering・worktree・Agent 起動〕の件数や比率と、コードの性能・時間の計測値）を外し、その項目や計測が示した意味の文に書き直した。あわせて、`G-NN`（計画書の項目の札と、同じ形のレビューの指摘番号）・`R9-N`・計画書のファイル名・セッション ID も外した。同じ文にあった過去のタスクの AC 番号・レビューの指摘の番号・計画書の task の ID（`PR-W7` など）も外した
- 判定・閾値・上限・hook が出す文は変えていない。閾値・設定値・テストの入力の大きさ、PR 番号、計画書の札と同じ文に無い、過去のタスクの AC 番号・task 番号・レビューの指摘の番号（`G-NN` の形のものを除く）、テストの fixture の中身、実在するファイル名・branch 名に入る小文字の番号は残した

#### Affected Files

- `hooks/scripts/` の 12 本と `hooks/scripts/lib/` の 21 本（コメントと docstring）
- `scripts/` の 10 本と `scripts/lib/repository_identity.py`（コメントと docstring。`lint-hitl-required-fields.py` と `lint-requirements-duplication.py` の module docstring は `--help` の説明文にも出る）
- `tests/` の 100 本と `tests/checks/` の 8 本（コメントと docstring。`test_hooks_wiring_new_events_contract.py` と `test_pre_push_gate_contract.py` は assert の失敗時の msg 1 か所ずつも）
- `CONTRIBUTING.md`、`pytest.ini`（コメント）

#### User Action Required

なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`（変えたファイルを参照するテスト）、`bash tests/validate-plugin.sh`
