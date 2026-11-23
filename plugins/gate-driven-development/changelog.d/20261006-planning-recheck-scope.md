---
type: patch
---

#### Summary

planning reviewer の再入レビュー（requirements-gating・design-gating の同じエピソードの 2 回目の Round）で読む範囲を、前回 Round の blocking ごとの処置箇所と変えた節、それらが名指しする実コード（変える関数・その呼び出し元・同じ入力を読む別の実装・それを固定するテストと文書）に限った。これまでは観点レーンの「レーンごとに最低 1 回は実測」が再入にも掛かっていた。そのため、差分だけを見るはずの再入レビューが Round 1 とほぼ同じ量の探索をしていた。advisory も、この範囲の中で見つけたものだけを報告する。human check をまたいだ `Round 1（re-entry: …）` は今までどおり Round 1 として全体を見る。

gate の側では、再入の前に処置するのを blocking だけにし、advisory の反映は最後の Round の後にまとめる。再入の 1 枚には、前回 Round の blocking の一覧（ID・要約・処置した場所）を載せる。reviewer が返ったときに `reviews.md` へ書く行には、所要時間に加えてツール呼び出しの回数（完了通知の `tool_uses`）も書く。

#### Changed

- `references/requirements-gating-steps.md` § レビューループの契約 3: 再入で読む範囲と、再入の前の処置は blocking だけ、を足した
- `agents/gdd-planning-reviewer.md`: 再入レビューでは観点レーンの実測の義務を当てない
- `references/subagent-dispatch.md` § Reviewer Input and Time Budget: 再入の 1 枚に前回 Round の blocking の一覧を載せる。`reviews.md` に呼び出しの回数を書く
- `skills/gdd-requirements-amendment/SKILL.md`・`skills/gdd-design-gating/SKILL.md`: advisory の反映は最後の Round の後

#### Affected Files

- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-requirements-amendment/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py --run`）
- Skill RED-GREEN Evidence: 同じ再入レビューの入力を、変更前と変更後の reviewer 定義で走らせ、呼び出しの回数・所要時間・判定を比べた（PR 本文）
