---
lane: L1
pr: 旧#197
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 528032ff7ef8b1deadd9d87c9486b5871c192fac | 0 | 0 | 0 | 2026-09-28T15:57+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | low | no | self-inflicted | related-test-selection | accepted | `test_stop_hook_unit.py` の一覧に、起動した `run-session-start-hook.sh` が source する `lib/detect-steering.sh` が無く、「どのモジュールを変えても選ばれる」「漏れなく」が成り立たない。hook の script は多くの lib を source するので、間接的に届くモジュールまで列挙すると入力が閉じない。限界として開示して止める。断片の主張を「テストが名前・パスで直接参照するモジュール」に狭め、間接的にだけ届くモジュールを入れていないことを書いた（断片は規則の文書でないので巡は無効にならない） |
| L2 | 独立-1 | advisory | no | self-inflicted | doc-claim-mechanical | fixed | 断片の「機械的に割り出した」と実際の一覧が合わない（コメントで触れているだけの `lib/handoff_summary.py` などを除いていた）。拾う基準（文字列は docstring を含めて拾い、`#` のコメントは拾わない）を断片に書き足した |
