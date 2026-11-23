# State Machine 概要

> **所有**: phase flow の quick index
> **上位正本**: `self-contained-contract.md`
> **詳細**: `state-machine.md`（遷移表） / `state-field-tiers.md`（state field tier・保存先）
> **正本マップ**: `source-of-truth-map.md`

overview docs must not own field meanings。field の意味・許容値・保存先 tier は `state-field-tiers.md`、遷移表は `state-machine.md` を参照する。

`state.md` は routing source と短い context source であり、state.md is not an audit dump。audit source は `worklog.md` / `adr.md` / `findings.md` / appendix に置く。

## Phase Flow

Express Path:

```text
gdd-brainstorming -> gdd-requirements-gating -> human-check-waiting -> gdd-test-driven-development -> gdd-subagent-driven-implementation -> gdd-implementation-gating -> done
```

Standard Path:

```text
gdd-brainstorming -> gdd-requirements-gating -> human-check-waiting -> gdd-design-gating -> gdd-task-breakdown -> gdd-test-driven-development -> gdd-subagent-driven-implementation -> gdd-implementation-gating -> gdd-completion-check -> done/cancelled
```

差し戻し、Resume From、Next Action、Route In Progress の詳細は `state-machine.md`。state field の routing source / context source / audit source の分類は `state-field-tiers.md`。
