---
type: patch
---

#### Summary

- 正式 gate の上限（`上限到達:` 行を書く 6 種。requirements・design・completion の Round 上限、`Pre-PR Fix Attempts` の上限、Remediation Loop Safety の上限、followup の 2 回目の設計し直し）で止まる遷移を書く前に、遷移を書く側が依頼の原文（`request.md`）に照らして、残った指摘を生んだ前提を自分で点検する。点検のために巡を重ねず、人にも問わない。結果は `worklog.md` に `前提の点検: <合う | ずれる> | <1 文> | 案: <前提を変える案の名前 | なし>` の 1 行で残す（旧#641 の原因を変える案と分けて数えるため）。`ずれる` なら、その前提を変える案を一括提示の選択肢に入れる。AC か依頼の読み方が変わると分かったときは、判断ポイントにする
- 同じ指摘の繰り返しの合図でも同じ点検をする。skill-level の Bounce Log の escape hatch が発動したとき（正本 `references/bounce-log-schema.md`）、build loop で route を決め直すとき（finding が減っていない・同じ root cause が再発している。completion-check からの戻りを含む）と Approach Rethink を書くとき、PR 後の Design Review Checkpoint が発火したとき
- 事前回答で委任しているとき、上限で止まる提示の前提を変える案は、依頼の読み方か AC を変えるときだけ人に戻す（前は、前提を変える案を採るといつも戻していた。`planning_rework_required` に進むときも同じ。ほかの人に戻す条件は変えない）

#### Affected Files

- `references/requirements-gating-steps.md`、`references/human-check-template.md`、`references/state-machine.md`、`references/bounce-log-schema.md`、`skills/gdd-pr-review-followup/SKILL.md`、`skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `前提の点検:` の行は数えるための記録で、機械の検査はしない。書き漏れても止まらない
