---
type: patch
---

#### Summary

早期の方式判断（同じ task への `gdd-implementation-gating` の 1 回目の差し戻しで Round 消費 category の high が 3 件以上のとき、`gdd-opus-advisor` に route を 1 回聞く仕組み）を取り除いた。27 件の steering・137 task の実データでは一度も発火しておらず、差し戻しのループは medium が主因の実装ループと、人間が続行を選び続けた completion・要件のループだった。差し戻しの後は、これまでどおり `gdd-systematic-debugging` が route を決める。

- 取り除いたもの: `references/state-machine.md` § Remediation Loop Safety の箇条、`gdd-implementation-gating` の Step 9 の `## Round` の行と判定表の行、`references/subagent-dispatch.md` の Round 行の扱い、`references/phase-progression.md` の route の行、`references/autonomy.md`・`references/fixed-models.md`・`agents/gdd-opus-advisor.md` の参照
- 残したもの: Step 1・1d の出口での `Gate Rounds` の加算、Template の `approved` の扱い、`human-recheck` の値、Downstream Handoff の事前回答、判断役の出力の `止めるべきか:` の欄（自律モードでも使う）

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし（agent 定義の description を変えたので、動いているセッションには開き直した後に効く）

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
