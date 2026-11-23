---
type: minor
---

#### Summary

pre-push gate・pre-PR gate・`scripts/check-gate-ledger.sh` と、merge gate の `Bot Review Received` が `received: no` の経路が、`Independent Review` の sha が push 対象の tip（pre-PR・merge gate では HEAD）と一致しないとき、`Independent Review Carry: <merge sha> | from: <旧 sha> | verified: diff-equal | at: <ISO 8601>` の行があれば、レビュー済みの sha に default branch を取り込んだだけの merge commit かを git から確かめ、確かめられたら旧 sha の独立レビューを引き継ぐようにした。条件は、第 1 親がレビュー済みの sha で第 2 親が remote-tracking の default branch の祖先であること、衝突していないファイルが自動 merge の結果と同じで差分も PR の差分と一致すること、衝突したファイルに衝突マーカーが無く、衝突の外の行が自動 merge のとおりに並び、衝突の位置に両側の行が順序どおり残り、両側のどちらでもない行が 5 行以下であること（条件の正本は `references/self-review-lanes.md` § Independent Review の引き継ぎ）。満たさない・時間内に確かめられないときは、今までどおり止める（pre-push gate・pre-PR gate は `independent-review-stale`、merge gate は `review-wait-not-elapsed`・`independent-review-missing`）。pre-push gate・pre-PR gate の止めるときの文に、引き継ぎの行の案内を足した。検算の Independent Review の行は、引き継いだときは ok の行に「（Independent Review Carry で引き継ぎ）」を付け、sha がずれた行には引き継げない理由を付ける。Self Review の sha がずれた行には、引き継ぐときは sha を書き換えてよいことを足した。merge gate では、引き継いだ独立レビューが bot の待機の免除と独立レビューの要求を満たす（`Medium Disposition` の sha は HEAD のまま要求する）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/ir_merge_carry.py`
- `plugins/gate-driven-development/hooks/scripts/lib/gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`

#### User Action Required

- default branch を取り込んだ merge commit で独立レビューを取り直さずに push するときは、`references/self-review-lanes.md` § Independent Review の引き継ぎのとおり `Independent Review Carry` 行を書き、`Pre-Push Self Review` などの sha を merge sha で書き直す。行を書かなければ、今までどおり取り直しを求められる

#### Validation / Eval Impact

- `tests/test_ir_merge_carry.py`（hook の入口から pre-PR gate・pre-push gate・検算の 3 つを走らせる）
- `tests/test_merge_gate_ir_carry.py`（merge gate の hook の入口から `received: no` の経路を走らせる）
- 変異注入の結果は PR 本文に書く
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
