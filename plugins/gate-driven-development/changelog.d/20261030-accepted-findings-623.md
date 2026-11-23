---
type: patch
---

#### Summary

- quick (express) の要件レビューまわりで、前の変更が書いた規定とまわりの規定が食い違っていた箇所をそろえた

#### Fixed

- express の human check の「一部変更」で範囲か Files が変わったときに回す Round を、初回と同じ扱いにした（lint は `--entry requirements`、reviewer は全範囲を読む）。前の Round が approved でも lint で止まらない。Round の上限に当たっていたら、回さずに人へ一括提示する。AC が変わる返答は、`commands/gdd-dev.md` の返答の分類どおり brainstorming に戻す（`references/requirements-gating-steps.md` § Express・§ 承認後の即時継続、`references/brainstorming-steps.md`、`skills/gdd-brainstorming/SKILL.md`、`references/subagent-dispatch.md`）
- express の要件レビューで security reviewer を起動するとき、design の観点と同じ 1 枚に `- Phase: design（gdd-requirements-gating から。human check の前）` の行を付けて渡し、選定の記録にも書くようにした。昇格の後の再入では design の観点の組を `not_applicable` と記録する（`references/reviewer-selection.md`）
- `references/state-machine.md` と `references/faq.md` の自動昇格の条件の写しを、`references/task-sizing.md` § Express 昇格条件 の参照にした。実装 2・テスト 1 の express は昇格しない
- Complexity Evaluation の Scope Breadth の「低」と、express テンプレートの目的・自走範囲・Files の欄を、実装コードで数える形にそろえた（`references/task-sizing.md`、`references/requirements-template-express.md`）。`references/brainstorming-steps.md` の、もう無い Step 7a-4 への参照を直した
- express の human check で「実装方針変更」の返答が来たら、express に無い design-gating ではなく、`## Implementation Policy` を直して requirements-gating をもう 1 Round 回すようにした（設計が要るなら Express 手動昇格。`commands/gdd-dev.md`、`references/human-check-template.md`、`references/common-guardrails.md`、`references/requirements-gating-steps.md` § Express）
- `agents/gdd-planning-reviewer.md`、`references/human-check-template-compact.md`、`README.md`、archive の例、予算の検査のコメントの古い言い回しを直した

#### Affected Files

- `references/requirements-gating-steps.md`
- `references/brainstorming-steps.md`
- `references/subagent-dispatch.md`
- `references/reviewer-selection.md`
- `references/state-machine.md`
- `references/faq.md`
- `references/task-sizing.md`
- `references/requirements-template-express.md`
- `references/human-check-template-compact.md`
- `references/human-check-template.md`
- `references/common-guardrails.md`
- `agents/gdd-planning-reviewer.md`
- `commands/gdd-dev.md`
- `skills/gdd-brainstorming/SKILL.md`
- `README.md`
- `docs/references-archive/worked-examples.md`
- `tests/checks/skill-body-budget.sh`（コメントだけ）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
