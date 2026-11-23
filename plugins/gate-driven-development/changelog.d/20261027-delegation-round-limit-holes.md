---
type: patch
---

#### Summary

- 判断を相談役に委任したタスクで、requirements・design の Round 上限に同じ steering で 2 回目に当たったら人に戻すようにした。今までは「同じ上限に 2 回目」で数える種類が completion・pre-pr・remediation・followup の 4 つだけで、何度も上限に当たる収束しない設計も、相談役が決め続けた
- 委任したタスクで、承認した human check で `Approved Direction` に記録した人間に戻す条件に当たったら、相談役の推奨によらず人に戻すようにした。今までは人に戻す条件の閉じた一覧に入っておらず、本人が決めた止める条件が委任の判断で読まれなかった。委任先の承認では、この条件の前の項目を消さず・書き換えず、足すだけにする。後続 Stage の steering にも写す

#### Changed

- `references/human-check-template.md`（§ 事前回答 2 の `事前回答の適用:` 行の 1 欄目に `requirements-round-limit`・`design-round-limit` を足した。§ 事前回答 3 の `上限到達:` 行の種類を 6 つにし、Round 上限の一括提示の遷移でも書かせる。人に戻す条件に `Approved Direction` の人間に戻す条件を足した）
- `references/requirements-gating-steps.md`（§ レビューループの契約 1。一括提示の遷移で `上限到達:` 行を書く）
- `agents/gdd-formal-gate-runner.md`・`agents/gdd-light-task-runner.md`（`上限到達:` 行を足す遷移に Round 上限の一括提示を含めた）

#### Affected Files

- `references/human-check-template.md`
- `references/requirements-gating-steps.md`
- `agents/gdd-formal-gate-runner.md`
- `agents/gdd-light-task-runner.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
