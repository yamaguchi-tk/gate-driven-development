---
type: patch
---

#### Summary

実装の差し戻しの早期の方式判断で、止まる経路と記録の残りの欠けを直した。

- 判断役が止めるべきと答えた、または答えが読めないときは、事前回答の適用中も人間に止まり、委任先に聞き直さない。`references/human-check-template.md` § 事前回答 3 の「人に戻す条件」に足し、止めるときは § 事前回答 3 の `採った案: 人間に止める` の行を書く
- `references/rollback-patterns.md` の Downstream Human Recheck Handoff で、この停止に着いたら止める行を `worklog.md` に書いてから止まる
- `gdd-implementation-gating` の Step 1・1d・8a の各出口に、handoff（`implementation_gating.md`）の `## Round` の節を Step 9 のとおり書く旨の参照を足した。reviewer が approved でも Step 8a の出口で `Next Action=gdd-systematic-debugging` にしたときを、Template と § Subagent Return Output Contract の条件に入れた
- 早期の方式判断の判断役を起動できなかったときは、`references/autonomy.md` の止まる場面に当たらず、通常どおり判定する。`worklog.md` の `早期方式判断:` の行の `止めるべきか:` に `読めない` の値を足した

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
