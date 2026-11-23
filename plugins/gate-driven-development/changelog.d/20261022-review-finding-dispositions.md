---
type: minor
---

#### Summary

- impl-gating と独立レビューで、reviewer の指摘ごとに ID と行き先（閉じた値）を steering の `review-findings.md` に書くようにした。行き先の欠け・値域の外・high と実害クラスの不正な降格を、スクリプトで機械的に検査する。今までは、指摘ごとの採否を書く欄が無く、誤検知も再報告も数えられなかった。`Independent Review` 行も件数だけで、前回の指摘が解消したかを確かめられなかった

#### Added

- `references/finding-dispositions.md`: `review-findings.md` の書式、行き先の値域（`blocking`・`advisory[:理由]`・`rejected:refuted`・`rejected:duplicate:<id>`・`re-reported:<id>`）、high・実害クラスに付けられない行き先、独立レビューの件数の数え方
- `scripts/check-finding-dispositions.py`（述語は `hooks/scripts/lib/finding_dispositions.py`）: `review-findings.md` の形・連番・値域・行き先の規則を検査する。ok 以外があれば exit 1
- `scripts/check-gate-ledger.sh` の `findings` 行: `Independent Review` 行と同じ sha の `IR` 節があり、件数（high・medium・blocking）が行と一致するかを見る（hook は見ない検算だけの行）
- `agents/gdd-finding-verifier.md`: 指摘の検証役（read-only、Opus・high）

#### Changed

- `skills/gdd-implementation-gating/SKILL.md` Step 8: 判定を決めたら、その Round の全 finding の行き先を書き、検査が ok になるまで直す
- `references/reviewer-common.md`（Implementation 段階）・`references/independent-review.md`（出力フォーマット）: reviewer は finding に通し番号を付け、最後の行に `findings: <数>` を書く
- `rejected:refuted` にする行か、high・実害クラスを `advisory:calibration`・`advisory:unverified_file` に下げる行があるときは、検証役にその巡で 1 回判定させる。`rejected:refuted` と high・実害クラスの `advisory:calibration` は、検証役が `refuted` と判定した行だけ。high・実害クラスの `advisory:unverified_file` は、それに加えて、根拠が `absent@<sha>`（impl-gating Step 1c）の行にも付けられる。`rejected:duplicate` は参照元より軽い行を指せない
- references/ の行数を上限の中に収めるため、重なっていた文を統合した（`dialectic-review.md` の Output Contract の雛形・Host Adapter の表・Anti-Patterns、`subagent-dispatch.md` § Subagent Model Routing の表〔`fixed-models.md` を正本に〕、`reviewer-common.md` の Implementation 段階の出力の欄）
- `references/independent-review.md` § 証跡: `Independent Review` 行を書く前に、その巡の行き先を書く。`rejected:refuted` にした high も件数に残す
- `skills/gdd-completion-check/SKILL.md`（PR 作成の手順 4）: `check-gate-ledger.sh` で直す行に、gate 列が `independent-review` の行（`findings` 行）も入れた

#### Affected Files

- `plugins/gate-driven-development/references/finding-dispositions.md`
- `plugins/gate-driven-development/hooks/scripts/lib/finding_dispositions.py`
- `plugins/gate-driven-development/scripts/check-finding-dispositions.py`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/self-contained-contract.md`
- `plugins/gate-driven-development/agents/gdd-finding-verifier.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/references/dialectic-review.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/tests/test_finding_dispositions.py`
- `plugins/gate-driven-development/tests/test_finding_verifier_agent.py`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`

#### User Action Required

- impl-gating か独立レビューを回す steering では、`review-findings.md` を書く。作業中の steering で `Independent Review` 行がすでにあるなら、push・PR の前の `check-gate-ledger.sh` の `findings` 行が missing になるので、その巡の `IR` 節を足す

#### Validation / Eval Impact

- `tests/test_finding_dispositions.py`（CLI と `check-gate-ledger.sh` の `findings` 行を入口から通す。category の集合と `reviewer-common.md` の表の突き合わせ）
- `tests/test_finding_verifier_agent.py`（検証役の frontmatter の model・effort・tools と、起動の model の gate）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
