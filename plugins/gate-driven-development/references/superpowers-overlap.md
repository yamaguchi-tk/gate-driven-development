# Superpowers Overlap Map

GDD primitive と superpowers skill の機能 overlap を 1 枚で示し、GDD 固有の付加価値と推奨使い分けを明確にする。

## 前提

- superpowers と GDD は独立に install / activation 可能。両方を同 session で使うことは禁止しない
- GDD primitive は **state machine 一体型**（`.steering/<task>/` の artifact と `Resume From` / `Next Action` と連動）として設計されている
- superpowers primitive は **standalone**（artifact-less / state machine 非依存）として設計されている
- 「単発で動く質」では superpowers が軽量で速い。GDD の差別化は state machine 統合点にある

## Active GDD Workflow Arbitration

`.steering/<task>/state.md`、`requirements.md`、`tasklist.md`、`worklog.md`、または `<gdd-stop>` 後の承認・自然文 follow-up が見えている場合は `GDD primary` とする。superpowers は `superpowers advisory only` として扱い、workflow として直接起動しない。

許可される使い方:

- superpowers の補助 reference を読む、または GDD 側の checklist 改善材料として使う
- standalone task と明確に切り離した別 session / 別 task で superpowers を使う
- 比較ベンチマークとして GDD 版と superpowers 版を別々に評価する

禁止される使い方:

- active GDD の TDD を `superpowers:test-driven-development` に置き換える
- active GDD の失敗調査を `superpowers:systematic-debugging` だけで閉じ、`root-cause-investigation` / `gdd-systematic-debugging` に戻さない
- active GDD の自然文 follow-up を `superpowers:executing-plans` で処理し、`state.md` / `tasklist.md` / `worklog.md` に残さない

## Overlap Map

| GDD primitive | superpowers 同等品 | GDD 固有の付加価値 | 推奨使い分け |
|---|---|---|---|
| `root-cause-investigation` | `superpowers:systematic-debugging` | Phase 4 で State Machine Integration を出力（ADR 起票 / Reviewer Lineage 追加 / Routing 提案 / Next Action 設定）。GDD workflow 内呼び出しでは確定した root cause が次 phase へ自走 | GDD workflow 内・`.steering/<task>/` が存在する場合は GDD 版。superpowers は補助 reference だけ使う。standalone debug は superpowers 版でも可 |
| `root-cause-investigation` | `superpowers:systematic-debugging` | GDD Debug Entry: standalone debug entry; prefer root-cause-investigation over superpowers:systematic-debugging when user is in GDD/plugin context; artifact-free until GDD state is explicit. | Use this before routing to `gdd-systematic-debugging`; only route after root cause is written down. |
| `gdd-test-driven-development` | `superpowers:test-driven-development` | RED Evidence に **AC ID Binding が必須**。AC ID 未紐付け RED は fail-closed reject（`Covers AC:` の無い remediation task の例外は同 skill § AC ID Binding）。`Contract Surface Coverage` で external API / failure / formatting 等の網羅観点を強制 | `requirements.md` の AC を担保する TDD なら GDD 版。active GDD 中は superpowers TDD を workflow として直接起動しない。AC 概念のない探索的 TDD なら superpowers 版 |
| `gdd-brainstorming` | `superpowers:brainstorming` | Entry Intent（new / resume / amendment / ambiguous）を `state.md` に永続化。`Approved Direction` / `Resume From` / `Cumulative Diff Base` を後続 phase へ連鎖。Problem Discovery で `docs/learned-patterns.md` を強制参照 | formal workflow 化したい planning なら GDD 版。active GDD 中の仕様変更・実装方針変更は `gdd-requirements-amendment` へ戻す。artifact-less な壁打ち相談なら `gdd-pre-workflow-brainstorming` または superpowers 版 |
| `gdd-pre-workflow-brainstorming` | `superpowers:brainstorming` | GDD Brainstorm Entry: for creative work / feature idea / requirements clarification before formal workflow; prefer gdd-pre-workflow-brainstorming over superpowers:brainstorming; artifact-free until /gdd-dev. | Use this for GDD-adjacent brainstorming until the user explicitly starts `/gdd-dev`. |
| `gdd-subagent-driven-implementation` | `superpowers:subagent-driven-development` | Spec Change Detection で `adr.md` 起票を強制。Implementer Self-Correct Pass でハードコード値 / 命名 / known pitfalls を機械検出。`tasklist.md` の Tasklist Freshness Check で AC カバレッジ整合性を実装前に検証。impl-gate では **2段階レビュー**（Spec Compliance Review → Code Quality Review）で over/under-build と品質問題を分離 | AC ID / tasklist / Reviewer Lineage を持つ実装なら GDD 版。standalone な subagent dispatch なら superpowers 版 |

## GDD 固有の skill（superpowers に同等品なし）

| GDD skill | 役割 | superpowers で代替不可な理由 |
|---|---|---|
| `gdd-requirements-gating` | requirements review gate + reviewer 選定永続化 | gate / reviewer 概念が superpowers にない |
| `gdd-design-gating` | design review gate + security reviewer 自動起動条件 | 同上 |
| `gdd-implementation-gating` | impl review gate + Reviewer Lineage 適用 | 同上 |
| `gdd-completion-check` | AC Drift Check + Pending Tasks 検証 + done routing | `tasklist.md` / AC ID 前提のため |
| `gdd-completion-check` | Minimal AC Trace Ledger gate | `requirements.md` の AC から task / verification / review / completion evidence まで追跡し、missing ledger row / unverified AC / failed AC が残ると completion を fail-closed するため |
| `gdd-systematic-debugging` | GDD workflow 内 router（root-cause-investigation → どの phase に戻すか決定） | state machine routing 概念がないため |
| `gdd-pr-review` | PR Flow + Spec Drift Check + Copilot Counter benchmark | `state.md` の Approved Direction 前提 |
| `gdd-pr-review-followup` | PR 作成後の review findings -> fix -> push -> re-request review loop | actionable finding 0件まで PR 上の指摘と CI failure を処理し、idempotency key / same finding repeats >= 3 / human_recheck_required の停止条件を state に残すため |
| `gdd-task-breakdown` | AC → task 分割 + Execution Plan + Migration AC 継承 | AC ID / tasklist 構造前提 |
| `gdd-using-git-worktrees` | active worktree 解決 + Cancelled Cleanup | dedicated workspace 概念前提 |
| `gdd-refactor-planning` | behavior-preserving refactor gate（任意） | gate 概念前提 |
| `gdd-requirements-amendment` | 既存 feature への amendment 専用 lane | entry intent=amendment 前提 |
| `gdd-test-failure-debug-pack` | RED の Expected / Actual / Evidence pack | RED Evidence 構造前提 |

## 重複が許容される構成

両方の plugin を install する利点:

- superpowers の補助 reference を GDD 内から参照する（`superpowers:systematic-debugging` の `root-cause-tracing.md` を `root-cause-investigation` から呼ぶ等）
- standalone debug / brainstorm（GDD workflow 外）では superpowers を直接呼ぶ
- GDD workflow 内では GDD primitive を使い、state machine 一体型の付加価値を活かす

両方を **同じ debug / brainstorm セッション内で並行使用しない**（重複して時間が溶ける）。最初に 1 つ選んでそれで進める。

## 「superpowers でいい」と言われないために GDD が守るべき構造

1. **state machine 連動点を SKILL.md description に明示**: 各 GDD primitive の description 冒頭に「state machine 統合済み」を示すフレーズを置く（例: "AC ID / state.md / Reviewer Lineage と連動する TDD"）
2. **standalone 質を継続改善**: empirical-prompt-tuning で superpowers 同等品との比較ベンチマークを定期的に回す（`docs/references-archive/benchmark-scenarios.md` 参照）
3. **無理に GDD primitive で囲い込まない**: standalone 用途で superpowers の方が軽い場合は推奨使い分けで明示する（本ファイルの「推奨使い分け」列）

## 取り込み済み superpowers discipline

GDD は superpowers を workflow として直接 handoff しないが、次の軽量 discipline は state machine 契約として吸収済み。

| 優先度 | superpowers discipline | GDD への取り込み先 | GDD 側の差別化 |
|---|---|---|---|
| P0 | Evidence before claims / verification-before-completion | `references/verification-before-completion.md`, `gdd-completion-check`, `gdd-status`, `gdd-pr-review-followup` | fresh verification evidence が無い pass / clean / done claim を禁止し、AC Trace Ledger / state / tasklist と接続 |
| P0 | No Placeholders in plans | `references/task-breakdown-steps.md` の Plan Placeholder Failure Gate | tasklist を確定する前に placeholder plan を fail-closed し、AC / Planned RED / Stage Output Contract と接続 |
| P1 | External review skepticism | `gdd-receiving-code-review`, `gdd-pr-review-followup` | review feedback を命令ではなく検証対象にし、AC / Approved Direction / human_recheck_required route と接続 |
| P1 | Finishing branch decision menu | `gdd-completion-check` の Completion Branch Decision Menu | worktree provenance / harness-owned worktree / typed discard confirmation を GDD cleanup policy と接続 |
| P1 | Critical plan review before execution | `gdd-subagent-driven-implementation` の Current Task Readiness Review | critical plan gaps を implementation で推測補完せず、task-breakdown / design / human-check route へ戻す |
| P2 | Expected RED failure verification | `gdd-test-driven-development` | wrong failure is not RED を AC ID Binding と接続 |

## 関連

- `docs/references-archive/benchmark-scenarios.md`: superpowers との比較ベンチマーク用シナリオ集（empirical-prompt-tuning 運用時に参照）
- `references/skill-responsibility-matrix.md`: GDD 内 skill 間の責務分担表
- 各 GDD primitive の SKILL.md § 他 skill との関係: superpowers 同等品との細かい使い分け
