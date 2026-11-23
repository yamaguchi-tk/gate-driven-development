---
type: patch
---

#### Summary

- `gdd-test-driven-development` の Contract Surface Coverage で、`実装前から pass（対照）` のテストに入れる変異の入れ方・戻し方を決めた。変える production ファイルを worktree の外の一時ディレクトリへ複製し、変異の後に複製で上書きして戻し、`cmp` で入れる前と同じことと、対照のテストが pass することを確かめる。commit・reset・未 commit の差分を捨てる操作・共有の stash・別の worktree は使わない。並列バッチでは、バッチの全 task の RED を取り終えてから 1 つずつ入れる
- implementation-gating の inline review の止める側・境界の確認を、`tasklist.md` の全 task ではなく Current Task（Gate Batch では各 task）に絞った。escalation の reviewer の範囲と同じにした
- `gdd-implementation-reviewer` の入力の範囲に、Contract Surface Coverage の `参照:` は Review Focus 3 のとおり毎回読むと書いた

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/references/inline-review-checklists.md`
- `plugins/gate-driven-development/agents/gdd-implementation-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
