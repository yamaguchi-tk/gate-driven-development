---
type: patch
---

#### Summary

- 利用者から見える変更なし。未リリースの変更で足した、human check の承認の後に design-gating を飛ばす経路（`scripts/design-gate-route.py`）と、brainstorming が書く tasklist.md の下書きを、リリースの前に外した。承認の後は、今のリリースと同じく必ず design-gating → task-breakdown に進む
- requirements-gating で design の観点の reviewer の組を並行に起動する変更（`20261028-planning-review-design-lens.md`）と、その出力で Dialectic review を起動する変更は残る
- human check の前の design.md に design-gating Step 5a・5b・5d の記録と External Guardrails Inventory を書く規定も外した。これらは今のリリースと同じく design-gating で書く

#### Affected Files

- `plugins/gate-driven-development/changelog.d/20261028-design-gating-off-default.md`（`amends:`。飛ばす経路と design.md の節の記述を外し、Dialectic review の起動の場所だけを残した）
- `plugins/gate-driven-development/changelog.d/20261029-task-breakdown-into-stage1.md`（`amends:`。全項を外し、type を patch にした）
- `plugins/gate-driven-development/changelog.d/20261029-express-planning-review.md`（`amends:`。Validation から、外したテストの記述を外した）

#### User Action Required

- なし。進行中の steering の state.md に残った `design-lens-reviewing:` の token と、tasklist.md の `Tasklist Basis:` の行は読まれず、承認の後は design-gating に進む

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
