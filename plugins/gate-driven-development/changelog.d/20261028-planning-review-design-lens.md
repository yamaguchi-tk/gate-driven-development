---
type: minor
---

#### Summary

- requirements-gating が、design-gating を通るタスク（`Broad Requirement: true` を除く）で、design の観点の reviewer の組も同じ Round に並行に起動するようになった。組は design-gating と同じで、`gdd-planning-reviewer` を design phase の文脈で 1 本と、条件に当たる `gdd-security-reviewer` である。設計の欠陥が human check の前に見つかる
- design-gating は今までどおり回る。この版では計画のレビューの時間と費用が増える（design の観点のレビューが human check の前と後の 2 回になる）。design-gating を通常の経路から外すのは、この版の後のタスクで、design-gating の 1 巡目が新しく出す指摘を数えてから決める
- `reviews.md` の requirements の Round は、reviewer と所要を観点ごとに書き、指摘の先頭に出した観点（`[requirements]`・`[design]`・`[security]`）を書く。再入で起動するのは、前回 blocking を出した reviewer と、処置で変えた文書の観点の planning reviewer だけである
- design の観点の reviewer が時間超過で 2 回とも返らないときは、その reviewer を `timeout` と書き、Round の判定は残りの reviewer で決める（gate runner の中では reviewer に期限を置かないので、当たるのは reviewer がエラーで返ったときだけで、時間超過は runner の停止として Round 全体が timeout になる）。design の観点の reviewer は、影響範囲の grep の記録と配線表が無ければ指摘する（実値検算の記録は指摘しない）

#### Changed

- requirements-gating の reviewer の組（`references/reviewer-selection.md` § Gate Rules・§ Record Format、`references/task-sizing.md` § パスごとの違い、`skills/gdd-requirements-gating/SKILL.md` § Review Set、`references/self-contained-contract.md`）
- requirements-gating の起動と Round の記録（`references/requirements-gating-steps.md`）と、時間超過の扱い（`references/subagent-dispatch.md` § Reviewer Input and Time Budget の「超過・無応答のとき」）
- design の観点の reviewer に渡す 1 枚（`references/subagent-dispatch.md` § Reviewer Input and Time Budget。ファイル名 `requirements-round-<N>-design.md`、`- Phase: design（gdd-requirements-gating から。human check の前）` の行）
- `agents/gdd-planning-reviewer.md`・`agents/gdd-security-reviewer.md` の design phase の節（requirements-gating から起動されたときの扱い）

#### Affected Files

- `references/reviewer-selection.md`
- `references/requirements-gating-steps.md`
- `references/subagent-dispatch.md`
- `references/task-sizing.md`
- `references/self-contained-contract.md`
- `skills/gdd-requirements-gating/SKILL.md`
- `agents/gdd-planning-reviewer.md`
- `agents/gdd-security-reviewer.md`

#### User Action Required

- なし。進行中のタスクで requirements-gating の Round 1 を既に済ませたものは、そのまま進めてよい（design-gating が今までどおり見る）

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
