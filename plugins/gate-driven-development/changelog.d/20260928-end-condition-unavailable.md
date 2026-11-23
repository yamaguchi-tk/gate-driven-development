---
type: patch
---

#### Summary

利用者から見える変更なし。このリポジトリの軽いレーンの終了条件（root `CLAUDE.md` 手順 6、配布物ではない）で、「PR 本文には、巡については…巡の sha と結果だけを書き」の「だけ」が、「Claude Code 以外で読むとき」と安全策 1 が PR 本文に書かせる `unavailable` の行を禁じないように、その行は別に書くと足した。

#### Affected Files

- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_light_lane_review_routing_contract.py` の `test_end_condition_limits_only_the_round_record` に、`unavailable` の行を別に書く句の assert を足した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
