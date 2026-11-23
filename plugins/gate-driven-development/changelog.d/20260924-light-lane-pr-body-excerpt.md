---
type: patch
---

#### Summary

利用者から見える変更なし。このリポジトリの軽いレーンの独立レビューで、reviewer に渡す PR 本文の抜粋の規定を詰めた（配布物ではない root `CLAUDE.md` と `.claude/agents/light-lane-independent-reviewer.md` の変更）。抜粋に書かないものに誘導と抑制の文を足し、GitHub の PR 本文とは名前を分けた。規定を固定する契約テストを強めた。

#### Affected Files

- `plugins/gate-driven-development/tests/test_light_lane_review_routing_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_light_lane_review_routing_contract.py` の `PrBodyFieldTests` を書き直した（手順 6 の冒頭が契約 1 を挙げる／抜粋の行が緩める範囲・書くもの・書かないものの禁止の向き・手順 7 との区別を持つ／テンプレートの欄が同じ制約を持つ／reviewer の規定が報告・判断に使わない・場所・照合先を持つ）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
