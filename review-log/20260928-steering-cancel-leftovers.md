---
lane: L1
pr: 旧#214
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4469c08234182d1ba8cdf0c8633939d163a9e6dc | 0 | 0 | 0 | 2026-09-28T21:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | caf02f90a9fdc40c55e9396b70b151d361ca5bda | 0 | 0 | 0 | 2026-09-28T21:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | guidance-scope | accepted | cancel した steering は .steering/ に残り、URL の無いものは merge gate の pr-url-unrecorded を起こしうる。PR 本文の限界に書く（コードは変えない） |
| F2 | 独立-1 | low | no | self-inflicted | test-power | fixed | TROUBLESHOOTING は古い記述が無いことしか確かめていない。新しい記述の assertIn を足した（cc8eceaa） |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | registry のテストの docstring・メッセージが変わった挙動と合わない（cc8eceaa） |
| F4 | 独立-1 | low | no | self-inflicted | style | fixed | 出力のパスに // が入る。${DIR%/} にした（cc8eceaa） |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | task_binding_resolve.py のコメントが helper の旧挙動を fail-open の理由にしている（cc8eceaa） |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | test_stop_hook_bind_resolution_contract の docstring が helper の mv・rm -rf の指示を前提にしている（cc8eceaa） |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの別断片に「git の管理外に落ち」が残る。リリース時に直す一覧に足した |
| F8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「ignore から外れ」は .steering/ を ignore し、worktree の中へ移す前提。PR 本文に列挙 |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「auto delete は禁止」と「Auto-cancel is forbidden」の言い方のずれ。PR 本文に列挙 |
| G1 | 独立-2 | low | no | self-inflicted | test-power | next-pr | test_registry_is_list_only の禁止語が rm -rf・mv だけで、既定モードも出さなくなったので常に通る。Cancel 提案を足す |
| G2 | 独立-2 | low | no | self-inflicted | test-power | next-pr | ${DIR%/} の修正に回帰テストが無い（出力のパスを見ていない） |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「downgrade の discard で削除・移動」は、移動（archive のリネーム）を discard のせいにしている |
| G4 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | 断片の Affected Files に task_binding_resolve.py と test_stop_hook_bind_resolution_contract.py が無い |
| G5 | 独立-2 | advisory | no | inherited | doc-claim | re-reported | 未リリースの別断片の「git の管理外に落ち」（F7 の再掲） |
| G6 | 独立-2 | low | no | inherited | guidance-scope | accepted | cancel した steering が残ると、binding の無い worktree で done guard が warn だけになる。PR 本文の限界に書く |
