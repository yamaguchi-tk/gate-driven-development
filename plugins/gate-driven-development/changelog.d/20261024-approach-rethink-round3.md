---
type: patch
---

#### Summary

- 指摘を直す前に設計に戻る手順を § 直し方 に入れた。`High` か実害クラスの finding を直す前に、その種類の穴を生んだ設計の決定を挙げ、種類ごと消す設計の変更があれば先に採り、`設計: 変える（<決定>）` か `設計: 変えない（<理由>）` を書く
- impl-gate で 3 回差し戻された task では、route を決める前に方針を考え直した結果を、`tasklist.md` の固定の 1 行（`Approach Rethink`）に書くようにした

#### Changed

- `references/self-review-lanes.md` § 直し方 に 0 を足した：`High` か実害クラスの finding を直す前に設計に戻り、結果を規律 C と同じ記録先に `設計: 変える（<決定>）` か `設計: 変えない（<理由>）` で書く。impl-gate で 3 回差し戻された後の route 判断では下の `Approach Rethink` の行に、PR 後のレビュー対応の 3 巡目では既存の Design Review Checkpoint の `checkpoint:` の行に書く
- `references/state-machine.md` § Remediation Loop Safety（`gdd-systematic-debugging` § Loop Safety と、impl-gating の Loop Safety の表の 3/3 の行から指す）：task の `Gate Rounds` が 3 以上になってから最初に route を決めるとき、task ブロックに `- Approach Rethink: changed <design_detail_only | planning_rework_required | human_recheck_required> | <変えた設計の決定>` か `- Approach Rethink: kept | <変えない理由と、前の修正との違い>` を書く。`|` より前の値はこの 4 つに閉じる（後で数えるための固定の形で、機械の検査はしない）

#### Affected Files

- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（行数の予算を含む）
