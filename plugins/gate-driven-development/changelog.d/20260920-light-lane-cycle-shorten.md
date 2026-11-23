---
type: patch
---

#### Summary

- plugin を開発する側の文書 `CONTRIBUTING.md` の規則を変えた（利用者の実行時の挙動は変わらない）。変更断片には利用者から見える変更だけを書き、push の前に 1 回で確定する規則を足した

#### Changed

- `CONTRIBUTING.md` の項 1d とレビュー観点: 断片に書くのは利用者から見える変更だけ。レビューの経緯・巡の記録は書かない

#### Affected Files

- `CONTRIBUTING.md`
- plugin の外: root `CLAUDE.md`（レーン表の L0 の行、軽いレーンの手順 4・6・7、全レーン共通）、`.github/copilot-instructions.md`（PR の前提の 1 項目）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_governance_contract.py`・`tests/test_distribution_readiness_contract.py`・`tests/test_superpowers_differentiation_contract.py`・`tests/test_light_lane_review_routing_contract.py`・`tests/test_independent_review_host_route_contract.py`・`tests/test_always_high_scope_contract.py`（`CONTRIBUTING.md` と root `CLAUDE.md` の固定文字列）
