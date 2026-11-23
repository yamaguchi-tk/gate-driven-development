---
type: patch
---

#### Summary

stale steering の片付けの helper（`scripts/find-stale-steerings.sh`）は、候補ごとに `.steering-archive/` への移動（`mv`）と削除（`rm -rf`）を提案していた。使わない steering を終える手順（`state.md` の `Resume From` と `Next Action` をどちらも `cancelled` にする。移動・削除はしない）と食い違っていたので、cancel と resume の提案に変えた。終えてよいかはユーザーに確認するよう添える。

移動した steering についての記述も直した。「git の管理外に落ちる」と書いていたが、実際は向きが逆である。`.steering/` の外へ移すと、`.steering/` の ignore から外れて、git に見える未追跡ファイルになる。

#### Changed

- `scripts/find-stale-steerings.sh`: 既定モードと `--all-worktrees` の候補ごとの提案を、Archive・Discard から Cancel に変えた（Resume はそのまま）
- `skills/gdd-using-git-worktrees/SKILL.md`: helper の説明を cancel / resume に合わせた
- `references/self-review-lanes.md`・`docs/TROUBLESHOOTING.md`: `.steering/` の外へ移したときの記述を直した

#### Affected Files

- `plugins/gate-driven-development/scripts/find-stale-steerings.sh`
- `plugins/gate-driven-development/skills/gdd-using-git-worktrees/SKILL.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`
- `plugins/gate-driven-development/tests/test_steering_cancel_guidance_contract.py`
- `plugins/gate-driven-development/tests/test_worktree_registry_contract.py`

#### User Action Required

- なし。`find-stale-steerings.sh` の出力に `mv`・`rm -rf` の提案は出なくなる。stale の候補を終えるときは、ユーザーに確認したうえで、`state.md` の両 field を `cancelled` にする

#### Validation / Eval Impact

- `tests/test_steering_cancel_guidance_contract.py`: helper が Cancel を提案し、`mv`・`rm -rf`・`.steering-archive` を出さないこと、worktree の skill の説明、移したときの記述、`Route In Progress` を `none` にする指示が節にあること
- `tests/test_worktree_registry_contract.py`: 既定モードの提案の期待を Cancel に変えた
- 変更したファイルを参照するテスト、`bash plugins/gate-driven-development/tests/validate-plugin.sh`
