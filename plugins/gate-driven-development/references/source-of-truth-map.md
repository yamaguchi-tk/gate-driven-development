# Source of Truth Map

> **所有**: GDD 内の正本マップ。どの文書が何を決めるかの index, not override
> **上位正本**: なし。この文書は優先順位を上書きせず、正本の所在だけを示す
> **参照元**: README、overview docs、phase skill、contract test

この文書は、GDD のルールが複数の overview / template / skill に散らばって見えることを防ぐための正本マップ。ここに書くのは「どこを見れば決まるか」であり、詳細ルールは各正本文書に置く。

## 使い方

1. ルールを変更するときは、まずこの表で担当文書を確認する。
2. overview docs must not own field meanings。概要文書は短い説明とリンクに留める。
3. owner 以外の文書に同内容の本文を書くこと禁止。必要な場合は要約 + 正本リンクだけにし、詳細 table / 手順 / 許容値は owner 文書へ戻す。
4. 新しい文書を足す場合は、同じ内容を持つ親文書から本文を削除する。追加だけで終わる変更は drift risk として review blocker。

## 正本マップ

| 領域 | 正本 | overview / 補助 | メモ |
|---|---|---|---|
| 自己完結契約 / fail-closed | `self-contained-contract.md` | `contract-overview.md` | overview は要約だけ。優先順位は `self-contained-contract.md` が上 |
| phase 遷移 / state machine | `state-machine.md` | `state-machine-overview.md` | overview は phase flow と quick reference だけ |
| state field の tier / 保存先 | `state-field-tiers.md` | `state-machine-overview.md` | `state.md` は routing source と短い context source。state.md is not an audit dump |
| gate status schema | `gate-status-schema.md` | `state-machine.md` | status の許容値は schema 側を優先 |
| human check 表示 | `human-check-template.md` / `human-check-template-compact.md` | — | compact first |
| 確定文面（承認した文の digest・照合・再確認） | `confirmed-text.md` | `human-check-template.md` § 確定文面の再確認 | 道具は `scripts/confirmed-text.py` |
| 要件テンプレート | `requirements-template.md` / `requirements-template-express.md` | `requirements-gating-steps.md` | task size ごとに使い分ける |
| task sizing | `task-sizing.md` | README | README は入口説明だけ |
| worktree 判断ルール | `workspace-policy.md` | `common-guardrails.md` / `state-machine.md` | worktree 判断ルールの正本は `workspace-policy.md`。worktree の enforcement / state 遷移は `common-guardrails.md` / `state-machine.md` が補助正本として残る |
| routing guard | `common-guardrails.md` / `state-machine.md` | `TROUBLESHOOTING.md` | troubleshooting は復旧案内であり、routing 正本ではない |
| scenario evaluation | `gdd-scenario-evals.md` | `evals/gdd-scenario-fixtures.json` | fixture は事故例と期待挙動。契約本文は reference 側 |
| 機能仕様 | `docs/specs/<capability>.md` | `post-completion-pr-flow.md`（Distill to Spec 手順） | OpenSpec 型（Purpose / Requirements / Scenarios）。main に置く例外は蒸留物（ADR / spec）のみで、raw task `.steering/<task>/` は含めない |

## State Artifact Ownership

`state.md` は workflow の現在地を戻すための routing source であり、長い判断履歴を保存する場所ではない。

| 分類 | 保存先 | 例 |
|---|---|---|
| routing source | `state.md` / build 中は `tasklist.md` | `Resume From`, `Human Check Status`, `Route In Progress`, `Next Action` |
| context source | `state.md` の短い要約、詳細は artifact link | `Approved Direction`, `Stage Continuity`, `Last Handoff Summary` |
| audit source | `worklog.md`, `adr.md`, `findings.md`, appendix | reviewer findings, rejected options, long evidence |

詳細な field tier、許容値、軽量テンプレートは `state-field-tiers.md` を参照する。

## 変更時のチェック

- overview に field の意味を追加したくなったら、先に `state-field-tiers.md` か `state-machine.md` に置けないか確認する。
- `state.md` に長文・履歴・全 reviewer 出力を入れたくなったら、`worklog.md` / `adr.md` / `findings.md` に逃がす。
- skill が overview だけを読んで routing 判断する場合でも、field 意味の判断は `state-field-tiers.md` / `state-machine.md` を参照する。
