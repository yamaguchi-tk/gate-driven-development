---
type: minor
---

#### Summary

実装の差し戻しで、作り直すかどうかを早く判断するようにした。同じ task への `gdd-implementation-gating` の 1 回目の差し戻しで、Round 消費 category の high が 3 件以上あるときは、`gdd-systematic-debugging` が局所の修正（`implementation_fix_only`）を選ぶ前に、`gdd-opus-advisor` に route を 1 回聞いて推奨の route を採る（早期の方式判断）。

- 作り直し（`design_detail_only`）で進めるなら、人間に戻さずに進む（自走範囲の検査は通常どおり行う）
- 人間に止まるのは、推奨が Approved Direction の外（`human_recheck_required`）か前提の組み直し（`planning_rework_required`）のときだけ。自律モードでは `references/autonomy.md` に従う
- 判断役を起動できないときは止まらず、今までどおりの判定に戻る
- `worklog.md` に `早期方式判断:` の 1 行を書く
- 3/3・5/5・同一 root cause カテゴリの連続・ADR ≥ 2 の上限は、今までどおり数える

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（変更前と変更後の手順で、1 回目の差し戻しで high 4 件の場面の route の決め方を比べる）は PR 本文に書く
