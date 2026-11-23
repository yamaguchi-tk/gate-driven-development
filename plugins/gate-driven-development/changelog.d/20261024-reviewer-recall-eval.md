---
type: minor
---

#### Summary

- reviewer を、過去に実際に出た欠陥（独立レビューが見つけた 11 巡と、PR 作成後の外部レビューで見つかった 35 ケースの、high・実害の指摘）に当て直して、見逃しを数える評価を足した。reviewer の定義を変える前と後に回して比べるための道具で、gate には組み込んでいない

#### Added

- `scripts/run-reviewer-recall-eval.py`: ケースごとに tip の木（`review-log/` を除く）と差分を用意し、reviewer（既定 `gdd-implementation-reviewer`）を headless の claude で回す。出力を `review-findings.md` と同じ形の表に写して、既知の指摘ごとに hit・weak・miss を数える。費用の上限（`--max-cost-usd`）を超えそうな実行は始めない。終わった実行は使い直す
- `evals/reviewer-recall-cases.json`: 46 ケース（既知の指摘 84 件）
- `docs/reviewer-recall-eval.md`: 回し方・採点・読み方・基準の実行の結果・限界

#### Affected Files

- `plugins/gate-driven-development/scripts/run-reviewer-recall-eval.py`
- `plugins/gate-driven-development/evals/reviewer-recall-cases.json`
- `plugins/gate-driven-development/docs/reviewer-recall-eval.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/tests/test_run_reviewer_recall_eval.py`

#### User Action Required

- なし。reviewer の定義を変える PR では、変える前と後に `python3 scripts/run-reviewer-recall-eval.py --out <dir>` を回して比べる（CONTRIBUTING の「reviewer agent を追加・改修する」）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_run_reviewer_recall_eval.py -q`
- 基準の実行（46 ケース × 2 回）。結果は `docs/reviewer-recall-eval.md` § 基準の実行
