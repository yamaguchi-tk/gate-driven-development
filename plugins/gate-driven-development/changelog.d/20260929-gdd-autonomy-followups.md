---
type: patch
---

#### Summary

自律モード（`references/autonomy.md`）の判定と記録を詰めた。Codex で明示の委譲があっても最初の human check を判断役に回せるようにし、`worklog.md` が無い最初の human check も判断役に回す。止まる側は、Auto-Confirm で進んだ steering と行を書く前に中断した steering の上限、Round 上限で残った blocking を受け入れる案、判断役か Fable のどちらかが止めるべきと答えたときに広げた。Handoff・2 回目の設計し直し・返答分類・Workflow Lock から自律モードの手順を指すようにした。

#### Changed

- `references/autonomy.md`
  - `Approved Direction` が「有る」とは、節に Codex の委譲の記録（`Codex Subagent Delegation Permission`・`explicit_delegation_source` の行）と Express 昇格の追記のほかに行が 1 つでもあることとした
  - 一覧 3 で止まる steering を、`Approved Direction` があるのに行が無いものから、`worklog.md` に `自律判断: human-check` の行が無いものに広げた。新たに、Auto-Confirm で進み、その後 human check を経ていない steering も止まる
  - 「一覧に着く」を、一覧の条件を問わずその停止点に達したことと定めた
  - 止まる案に「Round 上限で残った blocking を accept as known risk にする」を足し、ラベル「ほかに止まるもの」を「止まる場面」にした
  - `worklog.md` が無いときは、行が無いものとして扱う
  - 判断役か Fable のどちらかが人間に止めるべきと答えたら止まる（判断役が止めるべきと答えたときは Fable を呼ばない）。Fable の推奨は行の `Fable: 使った（推奨: <案>）` に残す。判断役を起動しなかった行の欄の値を決めた
  - 宣言の行を数えない場所に、インデントコードと HTML コメントを足した
- `references/rollback-patterns.md` § Downstream Human Recheck Handoff、`skills/gdd-pr-review-followup`（2 回目の設計し直し）、`references/human-check-template.md` § 返答分類の判定基準、`skills/gdd-using-skills` の Workflow Lock から、宣言があれば `references/autonomy.md` を指すようにした
- `references/post-completion-pr-flow.md` の Autonomy Decisions Check で、人間に止めた行と人間の返答の行を「人間に戻した箇所」として分けて書く
- `skills/gdd-pr-review` の PR 本文チェックの列挙に Autonomy Decisions Check を足した
- `references/gate-status-schema.md` に、自律の承認の evidence `autonomy:<箇所>` を書いた

#### Affected Files

- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/gate-status-schema.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-using-skills/SKILL.md`

#### User Action Required

- なし。宣言の書き方（`.gdd-config.md` に `GDD Autonomy: internal`）は変わらない。インデントしたコードや HTML コメントの中に書いた宣言は数えなくなった。そこに宣言を書いていたら、行頭に出す。宣言は steering を始める前に書く

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 宣言ありの 4 場面（Codex の明示委譲、Workflow Lock からの返答、`worklog.md` の無い最初の human check、Auto-Confirm の後の上限）を main の手順書と比べた（PR 本文の Skill RED-GREEN Evidence）
