---
type: patch
---

#### Summary

- 事前回答（`references/human-check-template.md` § 事前回答）の規定を、言い換えている箇所と入口に揃えた。後続 Stage に事前回答で着手できるのは、元の `事前回答:` 行を § 事前回答 2 のとおり確かめられたときだけであることを、着手を定める各箇所に書いた。あわせて、`scripts/lint-approved-direction.py` が glob pattern の無い state.md を usage error にしなくなり、steering の書き込み hook の advisory に毎回出ていた INFO と usage の行が消えた

#### Changed

- `references/post-completion-pr-flow.md`・`references/state-machine.md`・`skills/gdd-next-plan/SKILL.md`：事前回答による後続 Stage の着手に、元の行を確かめる条件を書いた（確かめられなければ着手せず、`### 次の計画` を出して「次に進んで」を待つ）。`gdd-next-plan` の人に戻す条件の指し先を § 事前回答 の 3 に直し、次 Stage の新しい worktree で出す HITL before implementation に、事前回答の Stage は § 事前回答 2 で扱う例外を足した
- `references/phase-progression.md`：Pending Stage の実装開始を禁じる規定に、`事前回答で後続PRも実施許可` の Stage を § 事前回答 4 で着手する例外を足した（確かめの条件は § 4 にある）
- `references/human-check-template.md` § 事前回答：
  - 確かめられないとき（欄が原文から読めないときを含む）は `事前回答の適用: ... / 採った案: 適用しない（原文を確かめられない）` を書き、行が無いときと同じに扱う（`GDD Autonomy: internal` の宣言があれば autonomy.md に従う）。表示するときは、適用できなかったことと、言い直せば記録し直すことを伝える
  - 原文が触れていない欄は、委任先は `なし`、人に戻す条件は 3 の一覧だけと読む
  - evidence の警告は hook の systemMessage で利用者の端末に出て main には届かないので、main は書く前に自分で値を確かめる
  - Codex の subagent 委譲を開くのは、`references/codex.md` の明示委譲ソースか、表示した human check での本人の承認だけと書いた
  - 人に戻す条件の一覧の由来の断定を外した
  - 後続 Stage の実装まで human check の OK で許可できるのは、`事前回答で後続PRも実施許可` と Stage Continuation だけと、段階実装案の説明にも書いた
- Planning Interrupt Decision Menu（`human-check-template.md`・`requirements-gating-steps.md`）の事前回答の例外は、§ 事前回答 3 の人に戻す条件に当たる指示（scope・AC などの変更）には使わず、項目 1 で扱う
- 入口：`commands/gdd-dev.md` #9 は、事前回答の行があるかを `GDD Autonomy` の判定より先に見る形に書き直した。`references/subagent-dispatch.md` の Post-Return Routing（旧#9 と同じ順序）、`skills/gdd-requirements-gating/SKILL.md` の途中指示、`skills/gdd-using-skills/SKILL.md` の振り分けに、§ 事前回答 への指し先を足した
- `references/post-merge-qa.md` § 限界：事前回答の適用を「行がある」から「§ 事前回答 2 のとおり確かめた行」に直した
- `scripts/lint-approved-direction.py`：state.md を渡して glob pattern が無いときは exit 0 にし、`--quiet` では INFO を出さない。exit 2 は、state.md も `--pattern` も無いときと、state.md が無いときだけにした（未リリースの `20261002-pre-answer-delegation` の「WARN が無ければ今までどおり exit 2」を置き換える）。`gdd-systematic-debugging` Step 3c は、`INFO: no Approved Direction patterns found` を合格に数えず、自走範囲の glob を手で確かめてから進む（lint は `## Approved Direction` の見出しの形を読めない）

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/skills/gdd-next-plan/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-requirements-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-using-skills/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`・`tests/checks/lint-scripts-functional.sh`（standard runtime profile の推定 token の上限を 45405 から 45430 に上げた）
- `plugins/gate-driven-development/tests/test_pre_answer_contract.py`

#### User Action Required

- `事前回答:` 行に補足を移しても、その行の原文が今の会話に無ければ § 事前回答 2 の確認を通らず、残りの human check には効かない。効かせたいときは本人が会話で言い直し、main が § 事前回答 1 の形で記録する

#### Validation / Eval Impact

- `tests/test_pre_answer_contract.py`：glob の無い state.md で lint が exit 0・無出力になること、evidence の WARN に INFO と usage が混ざらないこと、state.md が無いときは exit 2 のままであること、steering の書き込み hook の入口から正規の記録では advisory が出ないこと
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
