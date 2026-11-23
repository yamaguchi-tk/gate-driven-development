---
type: patch
---

#### Summary

`independent_review` tier（push 前の独立レビュー）の Claude Code の effort を `max` から `xhigh` に下げた。`scripts/resolve-gdd-model.py` が返す値と、`references/fixed-models.md`・`gdd-model-routing` の tier 表を変えた。Cursor・Codex の列は変わらない。Claude Code には独立レビュー用の agent 定義が無く、起動の経路が effort を固定しないので、実行時の effort は変わらない（下げる前の `max` も強制されておらず、main の effort を継承していた）。

#### Affected Files

- `plugins/gate-driven-development/scripts/resolve-gdd-model.py`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`
- `plugins/gate-driven-development/tests/test_independent_review_host_route_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_independent_review_host_route_contract.py -q`（resolver の値と 3 つの tier 表の行が一致することを固定する）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
