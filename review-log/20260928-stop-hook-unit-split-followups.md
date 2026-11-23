---
lane: L1
pr: 旧#194
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | da7fffe1cb755d9b4071202367d50acb81d562cc | 0 | 0 | 0 | 2026-09-28T15:32+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 独立-1 | low | no | self-inflicted | related-test-selection | next-pr | 足した「確かめる本体」に `lib/guards.py`・`lib/tasklist_parse.py` などが無く、continuation には行自体が無い。`lib/guards.py` を変えても continuation・stop_reason の単体テストが grep で選ばれない。各ファイルが直接使う `hooks/scripts` のモジュール名を機械的に数えて docstring に書く |
| K2 | 独立-1 | low | no | inherited | related-test-selection | next-pr | 分割の後、`test_stop_hook_unit.py` から "constants" の語が消え、`lib/constants.py` の `HANDOFF_PATTERN` を変えても `TestHandoffPattern` を持つこのファイルが選ばれない。「いずれかのファイルで拾える」という検証はファイルの集合で判定するので、ファイルごとの取りこぼしを検出できない。K1 と同じ PR で、ファイルごとの判定にして直す |
| K3 | 独立-1 | advisory | no | inherited | test-copy-of-predicate | accepted | `_should_skip_continuation_check()` はテスト側の写しで、本体の `_load_active_state()` の述語を呼ばない。本体を通るのは e2e の `active: "false"` の 1 ケースだけ。分割前からの状態で、PR 本文に advisory として書く |
