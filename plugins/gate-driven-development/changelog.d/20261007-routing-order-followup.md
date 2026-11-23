---
type: patch
---

#### Summary

`gdd-systematic-debugging` の Routing Decision Tree 1 で、テスト設計の不足（TDD）を問う前に、同一 root cause カテゴリ 3 回連続と承認後の 2/2 に当たるかを確かめるようにした。当たれば方式転換の選択肢提示（`human_recheck_required`）にする。`references/phase-progression.md` § Escalation Decision Table の 1 行目と同じ順序になる。これまでは、2/2 に達した task でも RED の不足があれば先に TDD へ進んでいた。

あわせて、`references/autonomy.md` の参照元の一覧に、実際に参照している `references/state-machine.md`・`references/post-merge-qa.md`・`references/gate-status-schema.md` を足した。

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/references/autonomy.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
