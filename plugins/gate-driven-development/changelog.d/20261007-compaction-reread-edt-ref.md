---
type: patch
---

#### Summary

`gdd-systematic-debugging` の Context Compaction Resilience で、route を決める前にディスクから読み直すものに、`worklog.md` の Error Log（同一 root cause カテゴリの連続）と `adr.md`（remediation 由来 ADR entry の件数）を足した。どちらも Routing Decision Tree 1 が方式転換を判定するときに数えるもので、compaction の後に会話に残った古い値で数えると、方式転換を出し損ねるか、余計に出す。

あわせて、Escalation Decision Table を行番号（「1 行目」「2 行目」）で指していた 2 か所を、route で指すようにした。`references/state-machine.md` の `Root Cause Tag` は、表に行が足されてずれ、今の 2 行目（`implementation_fix_only`）を指していた。

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/references/state-machine.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
