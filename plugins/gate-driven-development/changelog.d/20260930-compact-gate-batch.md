---
type: patch
---

#### Summary

Stop hook の compact の提案（`[gdd:compact]`）で、impl-gate の Round 3 の区切りを Gate Batch では batch で 1 回にした。Gate Batch は batch の全 task に同じだけ `Gate Rounds` を足すので、これまでは同じ区切りの提案が task の数だけ（最大 3 回）出ていた。

`tasklist.md` の `## Execution Plan` の `- Gate Batch <N>: T-1, T-2, T-3` に入る task は、batch の番号で 1 つの記録にまとめる。batch に入らない task（並列バッチを含む）は、これまでどおり task ごとに 1 回出す。

#### Changed

- `hooks/scripts/lib/compact_suggestion.py` が `## Execution Plan` の `Gate Batch` の行を読み、Round 3 の記録キーを batch 単位にした

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/compact_suggestion.py`
- `plugins/gate-driven-development/tests/test_compact_suggestion_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_compact_suggestion_contract.py` に、Gate Batch の task を 1 つのキーにまとめること、batch の外の task と fence の中の例は task ごとのままであること、Stop hook の入口から 3 回止めても提案が 1 回だけ出ることのテストを足した
