---
type: patch
---

#### Summary

gate の前の RED Evidence の確認（`gdd-subagent-driven-implementation` 手順 17）の周りで、同じ差し戻しが続く経路と、確認が抜ける読み方を直した。

- `gdd-test-driven-development` の Post-Compaction Resume Check は、`#### RED Evidence` がある task を RED 確認済みとして飛ばしていた。`Worktree:` の行が無いか今の値と違う、または `test:` のファイルが差分にも未 commit の分にも無い節（`gdd-implementation-gating` Step 1d が差し戻す形）は、記録済みに数えずに RED を取り直すようにした。これまでは、Step 1d の差し戻しの後に TDD へ戻っても RED を取り直さず、同じ差し戻しが人に戻るまで続いていた
- 手順 17 で、変えていない既存のテストで観測した RED（`test:` のファイルが差分にも未 commit の分にも無い）は書き写さないようにした。書き写すと、Step 1d が必ず差し戻す
- 手順 17 で節を作るときは、`AC:` の行も書くようにした（`Covers AC:` が無い remediation task では、差し戻しの元の finding が指す AC）。これまでは `lint-ac` が `AC:` の無い節を WARN にしていた
- 手順 2a の Conflict Detection と、`gdd-systematic-debugging` の並列修正パスの手順 3 で、確認を conflict の有無を問わずに行うと読めるようにした
- 手順 17 で TDD に戻さない理由のうち、成り立たない「既に実装のある task は TDD が隔離する」を外した

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
