# Workflow Incident Review

> **所有**: GDD workflow 自体の事故分類と再発防止記録
> **参照元**: `gdd-completion-check` / `post-completion-learning`

GDD の実装成果ではなく、GDD の進め方そのものが人間の期待や state machine 契約からズレた場合に記録する。目的は blame ではなく、同じ種類の workflow 事故を次回減らすこと。

## 記録するタイミング

- HITL が分かりにくく、人間が何を承認したか分からない状態で進みかけた
- resume / compact / worktree 解決で別 task の state を見た、または見そうになった
- superpowers / GDD の skill arbitration が曖昧で、workflow の正本が揺れた
- context loss により AC / Approved Direction / tasklist の読み直しが不足した
- 既存コード読解が浅く、作り方・技術スタック・影響範囲がズレた
- PR 作成後レビュー指摘の修正・push・再レビュー依頼・fresh 再確認ループが早く終わった扱いになった
- HITL Outcome Audit / GDD Complexity Budget / lint で mismatch / unverified / over-budget が見つかった

## Incident Type

| type | 意味 | 典型的な再発防止 |
|---|---|---|
| `hitl_readability` | HITL が読みにくい、承認範囲や制限事項が分からない | 30秒判断 / easy summary / 用語説明 / Complexity Budget を強化 |
| `resume_mixup` | resume / compact 後に別 task や古い task を参照した | active steering 解決、worktree slug / branch / state の一致確認を強化 |
| `worktree_contamination` | worktree / branch / steering の対応が崩れた | Worktree Provenance Gate、cleanup、supersede 記録を強化 |
| `skill_arbitration` | GDD と superpowers、または GDD skill 間の責務が混ざった | GDD Workflow Lock / skill responsibility matrix / trigger description を修正 |
| `context_loss` | compaction や長時間作業で AC / task / Approved Direction を読み落とした | phase entry reread、AC Trace Ledger、Current Task reread を強化 |
| `code_reading_gap` | 既存コード・呼び出し元・consumer の読み込み不足で設計がズレた | Existing Code Reading Evidence / caller / consumer / test gap を強化 |
| `pr_review_followup_early_clean` | PR 作成後レビュー指摘が残っているのに clean / 完了扱いにした | push / re-review request / fresh PR reviews / checks evidence を state に残す |

## 記録形式

`worklog.md` または `learned-patterns.md` に以下の形で残す。

```markdown
## Workflow Incident Review

| field | value |
|---|---|
| incident_type | hitl_readability / resume_mixup / worktree_contamination / skill_arbitration / context_loss / code_reading_gap / pr_review_followup_early_clean |
| 何が起きたか | <観測事実。推測だけで書かない> |
| 影響 | <HITL / AC / implementation / review / PR への影響> |
| 検出した gate | <HITL Outcome Audit / completion-check / pr-review / human feedback 等> |
| 検出 lint / fixture | <scripts/... / tests/fixtures/e2e-replay/... / なし> |
| 再発防止 | <次回から変える rule / lint / reference / checklist> |
| 反映先 | <requirements-template / human-check-template / state-machine / learned-patterns 等> |
| 残るリスク | <deterministic に検出できない判断、外部条件、host 差分など> |
```

## Completion での扱い

- incident が起きたが再発防止が未記録なら `Workflow Incident Review` を completion output に含める
- incident が `scope / AC / policy / security boundary / prompt-output contract` を変える場合は `human_recheck_required`
- procedural / evidence only の incident は build loop 内で直し、再発防止を記録してから completion を続ける
- 再発防止が `なし` のままなら「なぜ再発しないと言えるか」が必要。根拠がなければ completion を通さない
- 新しい事故型を追加した場合は `references/prompt-contract-map.md` に Prompt owner / Executable guard / Good sample / Residual risk を追記する

## 再発防止

Workflow Incident Review は、同じ失敗を繰り返さないための学習材料である。Post-Completion Learning では、実装パターンだけでなく workflow incident の再発防止も `docs/learned-patterns.md` に残す。
