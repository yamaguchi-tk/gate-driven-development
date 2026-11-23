---
type: patch
---

#### Summary

停止の手順を書いた skill・command・reference のうち、`<gdd-stop>` マーカーを末尾・最後に置くと書いていた次の 11 か所を、`references/output-format.md` § 停止時の「👤 次にすること」マップの順（本文 → マーカー → `## 👤 次にすること`）に合わせた。これまでは字面どおりに読むと見出しを落とし、Stop hook の見出しの要求で差し戻されうる書き方だった。`subagent-dispatch.md` の「マーカーが無ければ追加」は、見出しの前に足すよう書いた。

#### Affected Files

- `plugins/gate-driven-development/commands/gdd-dev.md`（#9 の 0・3）
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`・`skills/gdd-requirements-gating/SKILL.md`・`skills/gdd-completion-check/SKILL.md`（done の停止）
- `plugins/gate-driven-development/references/subagent-dispatch.md`・`references/requirements-gating-steps.md`・`references/human-check-template.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
