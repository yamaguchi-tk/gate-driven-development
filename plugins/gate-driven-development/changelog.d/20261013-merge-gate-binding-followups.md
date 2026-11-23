---
type: patch
---

#### Summary

- merge gate の binding の照合で、同じ state.md を指す binding が複数あるとき、検査に落ちる binding（相対の `worktree_path`、出力できない値）や state.md を `.steering/` の下に持たない worktree の binding が先に並んでも、正しい binding を採る。今までは対象 PR の steering を見つけられず、今までの判定（PR 台帳など）に戻ることがあった
- root の steering に対象 PR が無いときの切り替えは、binding の state.md が worktree の `.steering/<slug>/state.md`（名前も `state.md`）のときだけ行い、切り替えた後に新しい root で steering を求め直す
- binding が 2 件以上で止まるときの文を、ユーザーに確認して binding を整理する案内から始める
- `repo-root-unresolvable` の案内を、repo の中を cwd にしたセッションから対象 PR を URL か `-R owner/repo <番号>` で明示して打つ形から始める。`cd <worktree> && gh pr merge` の形は、GDD の worktree に marker があるときだけ勧める（cwd が git の外のセッションからは、marker の無い GDD worktree へ cd しても root が決まらず binding を引かない）。binding の説明は、binding を引く条件（hook が root を決められ、対象 PR を番号か URL で明示した merge）つきにする
- `.steering/` の外の steering を指す binding で止まるときの文も、ユーザーに確認して binding を付け直す案内から始める

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/merge-gate-binding.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/tests/test_merge_gate_binding_steering.py`
- `plugins/gate-driven-development/changelog.d/20261013-merge-gate-binding-steering.md`（`amends:`。binding を引く条件・UTF-8 でない binding.json・2 件以上のときの出口を書き足した）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_binding_steering.py` に、binding の並び・値・対象の読み方・payload の cwd の分岐のテストを足した
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
