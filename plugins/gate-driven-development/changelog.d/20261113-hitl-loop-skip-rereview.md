---
type: minor
---

#### Summary

- requirements-gating・design-gating で、Round 上限か時間の目安に当たって残った blocking のうち、計測の締め直し（同じ AC の `計測:` だけを厳しくする）と、要件を固める確認で推奨に任された具体化を細かくするだけのものは、人に一括提示せず AI が閉じるようにした。閉じた後は提出前の照合（Sonnet）を 1 回だけ回し、閉じた AC を次の gate で名指しで確かめる（design-gating では reviewer の入力に載せ、implementation-gating では inline checklist で、実装を壊して計測のテストが落ちることを確かめ、落ちなければ High で差し戻す。名指しの AC を実装する task は review を外さない）。照合が ok を返さなければ、閉じずに人に出す。design-gating で承認済みの AC に出た計測の締め直しだけの blocking も、`human_recheck_required` で人に戻さない。任された具体化は、`worklog.md` の固定行の行き先に `具体化（任された）` と印を付けた行だけに当てる
- 一括提示への返答で、提示に書いた直した後の文面をそのまま採る返事（推奨の案の名指し）は、AC が変わっても brainstorming に戻さず、要件の再レビューも human check の出し直しもせずに承認として次へ進むようにした（提出前の照合を 1 回だけ回し、`request.md` に引用した表示の文面と反映先の字句を突き合わせる。照合が ok を返さなければ、承認に進まず人に見せて待つ）。採った AC も次の gate で名指しで確かめる。一括提示の修正の案には、直した後の文面を書く。1 つの返事で blocking ごとに行き先が分かれたら、最も止める側に進む
- スコープ・承認ポイント・安全境界の blocking、計測を緩める直し、AC の本文を変える直しは、今どおり人に出す

#### Affected Files

- `references/requirements-gating-steps.md`・`references/subagent-dispatch.md`・`references/brainstorming-steps.md`・`references/inline-review-checklists.md`・`commands/gdd-dev.md`・`skills/gdd-requirements-gating/SKILL.md`・`skills/gdd-design-gating/SKILL.md`・`skills/gdd-requirements-amendment/SKILL.md`・`agents/gdd-requirements-precheck.md`・`agents/gdd-planning-reviewer.md`・`agents/gdd-implementation-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- Skill RED-GREEN Evidence（上限に当たった直後と一括提示への返事の 2 つの場面を、変更前と変更後の規則で解かせた）・`python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
