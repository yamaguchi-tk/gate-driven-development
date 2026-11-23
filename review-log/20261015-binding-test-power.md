---
lane: L1
pr: 508
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ca2dbe87 | 0 | 2 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | test-power | accepted | resolver を差し替えるテストが、差し替えが効いたこと（resolve_task が呼ばれたこと）を assert していない。resolve_bind が _import_gdd_task_binding を通らなくなると、空の registry の conflict で同じ答えになり空洞に戻る（近道の blocking でない medium） |
| I1-2 | 独立-1 | medium | no | self-inflicted | test-power | accepted | Path.exists を差し替えるテストが、差し替えが発火したことを assert していない。locked/wt は存在しないので、_invalid_bindings が Path.exists 以外の呼び出しに替わると空洞に戻る（近道の blocking でない medium） |
| I1-3 | 独立-1 | low | no | self-inflicted | test-power | accepted | except の分岐の効果（missing_worktree_path と stale_binding_missing_worktree）を固定していない |
| I1-4 | 独立-1 | low | no | inherited | doc-claim | accepted | test_conflict_for_hostile_steering_paths の docstring が存在しない test_pins_are_not_hollow を指す（正しくは test_containment_pins_are_not_hollow） |
| I1-5 | 独立-1 | low | no | inherited | doc-claim | accepted | test_conflict_for_malformed_task_id のコメント（:197-198）の「型ガードを外すと TypeError が resolve_bind の外へ抜ける」は、_validate_binding を包む except があるので今は成り立たない |
| I1-6 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 投げる例外が組み込みの RuntimeError なので、except を組み込みの型の列挙に狭める変更は検出できない |
| I1-7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の「分岐を外すと落ちることを確かめた」に sha・当てた変更・落ち方が無い。PR 本文に書いた commit: なし（PR 本文） |
| I1-8 | 独立-1 | advisory | no | inherited | test-power | accepted | resolve_bind の _validate_binding を包む 3 つ目の except を外しても、どのテストも落ちない |
| I1-9 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | request.md に、発言が指す案 2・3 の文が無い。足した commit: 6511049d |
