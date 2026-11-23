---
type: minor
---

#### Summary

自律モードの判断役を、repo の宣言から、タスクごとに「どこまで自走するか」と並べて選ぶ判断の委任に作り直した。

- `.gdd-config.md` の `GDD Autonomy: internal`・`GDD Autonomy Advisor` を廃止した。この行があっても読まない
- human check の「どこまで自走するか」に `判断の委任` の行を足した。値は `人に止める`（既定）／`相談役に任せる`／`Opus に任せる`／`Fable に任せる`。人に止める以外を選ぶと、その human check の承認の時点で § 事前回答の行に記録し、以後の human check を委任先が判断する（その human check 自体は本人の返事で承認する）
- 事前回答の委任先に `並行` を足した。本人が model を名指しせずに任せたときの値で、Opus と Fable に並行で相談し、2 本の推奨が割れたら人に止まる。名指しは `並行` に替えない
- 上限での方式転換（Round 上限、`Pre-PR Fix Attempts` の上限、Remediation Loop Safety の上限、同じ PR での 2 回目の設計し直し）も委任先が判断できる。同じ steering で同じ種類の上限に 2 回目に当たったら人に止まる。数えるために、main は上限に着くたびに、委任の有無を問わず `worklog.md` に `上限到達:` の行を書く
- Stop hook の押し返しは、最後の `事前回答:` 行の委任先が `fable`・`opus`・`並行`・`なし` のどれかのときだけにした。欄が無い・重複する・値が集合の外なら押し返さない
- 判断役の承認の印 `evidence: autonomy:<箇所>` と、`worklog.md` の `自律判断:` の行を使わなくなった。PR 本文の「自律で判断した箇所」は `事前回答の適用:` の行から作る
- `references/autonomy.md` は、委任先の相談役が判断する手順、宣言の行の読み方、比較の軸の正本として残した

#### Affected Files

- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_pushback.py`
- `plugins/gate-driven-development/references/gate-status-schema.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-using-skills/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/agents/gdd-completion-reviewer.md`

#### User Action Required

- `.gdd-config.md` に `GDD Autonomy: internal`・`GDD Autonomy Advisor` を書いていた repo は、行を消してよい（読まなくなった）。判断を任せるときは、human check の `判断の委任` で選ぶか、会話で「Fable に相談しながら進めて」のように言う

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_stop_hook_autonomy_pushback.py` が、委任先の値ごとの押し返しと、集合の外・欄の欠けや重複で押し返さないことを固定する
- `tests/test_pre_answer_contract.py` が、hook の委任先の集合と template の記録の形の値の一致を固定する
