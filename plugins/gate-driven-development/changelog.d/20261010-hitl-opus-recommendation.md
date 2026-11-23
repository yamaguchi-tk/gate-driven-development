---
type: minor
---

#### Summary

human check（compact の判断ポイントの `推奨案` の行）と Downstream Human Recheck Handoff を人に表示する前に、main が `gdd-opus-advisor` に 1 回相談し（human check・Handoff を作る subagent は相談しない）、判断ポイントごとに `相談役の推奨: <案> / 食い違い: <なし | 内容>`（main の案との食い違い。済ませた相談が Fable などだけなら Opus にも相談し、その推奨は `相談役の推奨（Fable）:` のように model 名つきで添える）を載せるようにした。人が「Opus の意見を聞きたい」と返して、もう 1 往復待つことを減らす。推奨は材料で、承認の境界・選択肢・`GDD Autonomy: internal` と事前回答の扱いは変えない。相談役を起動できないときは `unavailable（理由）` と書いて表示する。

#### Affected Files

- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
