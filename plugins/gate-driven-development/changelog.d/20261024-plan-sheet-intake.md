---
type: minor
---

#### Summary

- design-gating を通る `quick (standard)` と `standard` では、brainstorming の 12 で、design.md の骨組みの影響範囲・主要フロー・テスト方針・ロールバック・配線表と条件付きの節を、design-gating の Step 5 の粒度で書くようにした。human check の前に詳細設計が steering にそろう。`Broad Requirement: true` のタスクは例外で、human check で scope を選んだ後に design-gating の Step 5 で書く。design-gating の Step 5 は、書いてある分を確かめ、足りない分を足す。最小構成（Summary Brief + 変更点 + テスト方針）でよいのは、design gate を通らない運用レベル light の `quick (standard)` だけになる。Quick Standard Design Gate Optional で design-gating を軽くするタスクも、詳細設計の粒度で書く。`quick (express)` は今までどおり design.md を作らない
- human check の「やること」（full）と「現在地」（compact）に、リスクの段の行を足した。`request-crosscheck.md` の `### リスクの段` の 1 行目を写し、読めないときは `高` と書く。`quick (express)` は記録が無いので行ごと省く。どの gate・遷移も、まだこの段を読まない

#### Changed

- `references/requirements-template.md`（§ lightweight design.md skeleton セクション一覧）
- `references/brainstorming-steps.md`（12）
- `references/human-check-template.md`（§ やること）
- `references/human-check-template-compact.md`（§ 現在地）
- `references/self-contained-contract.md`（human check 前の design.md の粒度）
- `references/task-sizing.md`（quick (standard) の design.md の行、§ Quick Standard Design Gate Optional、express の昇格の手順）
- `skills/gdd-brainstorming/SKILL.md`（Artifact Rule、11 の design.md skeleton の節）
- `skills/gdd-design-gating/SKILL.md`（Step 5）
- `agents/gdd-request-code-crosscheck.md`（§ リスクの段 の、段を読む側の説明）

#### Affected Files

- `references/requirements-template.md`
- `references/brainstorming-steps.md`
- `references/human-check-template.md`
- `references/human-check-template-compact.md`
- `references/self-contained-contract.md`
- `references/task-sizing.md`
- `skills/gdd-brainstorming/SKILL.md`
- `skills/gdd-design-gating/SKILL.md`
- `agents/gdd-request-code-crosscheck.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
