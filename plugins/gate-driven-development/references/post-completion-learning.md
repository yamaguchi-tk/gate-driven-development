# Post-Completion Learning

> **所有**: `gdd-completion-check` Post-Completion Learning step の手順詳細
> **上位正本**: `cross-task-learning.md`（learned-patterns.md の format / lifecycle）
> **参照元**: `gdd-completion-check` § Post-Completion Learning

`Next Action=done` 確定後、PR Flow の前に、今回のタスクから得られた知見を蓄積する。standard 運用では raw task steering `.steering/<task>/` は **branch-only steering** として扱い、main には raw task `.steering/<task>/` を含めない。merge 後に読ませる判断材料は `docs/adr/` への **Distill to ADR** と repo-level learned-patterns に蒸留する。**Why**: 次のタスクの brainstorming で過去判断を参照でき、同じ議論の繰り返しを防ぐ。実装 skill が ADR / learned-patterns を読むことで reviewer 差し戻しも減る。

repo-level learned-patterns（例: `docs/learned-patterns.md`）は raw task steering ではない。repo が既に `docs/learned-patterns.md` を cross-task learning file として採用している場合だけ更新する。採用済み判定は、`origin/<default-branch>` で `docs/learned-patterns.md` が tracked、または `.gdd-config.md` / repo docs に learned-patterns の保存先が明記されていること。この規約が無い repo では、新規作成せず `docs/adr/` または repo 既定の学習ファイルに蒸留する。

## 手順

1. `adr.md` があれば読み、採用した設計パターンと却下した代替案を抽出する。**`adr.md` が無い場合**は、今回の task に重要な意思決定（採用した設計方針 / 却下した代替案 / やらないと決めたこと）があったかを確認し、あれば `.steering/<task>/adr.md` に `Context` / `Decision` / `Why` / `Consequences` で残してから抽出する。重要判断が無ければそのまま次へ進む（`adr.md` は optional な補助 artifact であり、不在では**停止しない**）。重要判断がある standard task では、PR Flow 前に `docs/adr/<YYYYMMDD>-<task>.md` へ Distill to ADR する。既存 repo に ADR の慣習がある場合はその場所に従う
   - **Why**: `state.md` は routing source であり audit dump ではない（`source-of-truth-map.md`）。却下した代替案や長い根拠の逃がし先が実在しないと、行き場を失った内容が `state.md` に溜まる。実運用の task を調べると、`adr.md` は使われず、`state.md` は大きく肥大化し schema 外の値が混入していた
2. 実装の diff から、プロジェクト固有のコード規約（命名規則、ディレクトリ構成、エラーハンドリングパターン等）で他のタスクにも適用できるものを抽出する
3. **Reviewer Calibration の反映**: `tasklist.md` の `Completed Tasks` 内の `#### Attempts` セクションから `[Review Calibration]` エントリを収集する。`was_valid=false` が 2 回以上記録されている checklist 項目があれば、`learned-patterns.md` の `Rejected Alternatives` に「この checklist 項目はこのプロジェクトで false positive が多い（具体例: ...）」と記録する。次回の `gdd-implementation-gating` が severity 調整に参照する（`references/inline-review-checklists.md` § Reviewer Calibration 参照）
4. **Migration / Conversion Failure Pattern の記録**: `requirements.md` に `タスク種別: migration/conversion` が含まれていた場合、以下を `learned-patterns.md` の `Migration Patterns` セクション（無ければ新規作成）に記録する:
   - **今回 pass した AC-F\***: どの検証手段（grep コマンド / スクリーンショット / 実環境確認）で pass に至ったか
   - **今回発覚した失敗モード**: content-loss / ネイティブ機能非活用 / レンダリング未検証 のうち、どれが implementation-gating / completion-check / pr-review のどの段階で検出されたか（検出が遅れた場合は「どの gate で先に検出すべきだったか」も記録）
   - **再発防止の示唆**: 次回同種タスクの requirements.md 初稿で最初から入れるべき AC / verification task のヒント
5. **Reviewer Lineage Pattern の自動 capture**: `tasklist.md` の `Implementation Reviewer Selection` から `added_by: smi_block` または `added_by: impact_block` の entry を全て抽出し（**`added_by: lineage_pattern` や `added_by: task-breakdown` の entry は capture 対象外** — それらは既に過去の pattern 由来 / 標準枠であり、二重 capture を防ぐ）、以下を `learned-patterns.md` の `Reviewer Lineage Patterns` セクション（無ければ新規作成）に記録する:
   - **task signature**: 今回 task の特徴（変更ファイル種別 / scope keyword / requirements の関連 AC ID）。例: `terraform/modules/lambda/*.tf` + `IAM policy 追加`
   - **追加 reviewer**: `gdd-security-reviewer` / `terraform checklist reviewer` 等
   - **trigger source**: `smi_block`（root-cause-investigation 由来）/ `impact_block`（gdd-subagent-driven-implementation 由来）
   - **source_signal**: 追加の決め手となった原因 / 仕様変更の 1 行要約
   - **outcome**: 追加 reviewer が `approved` / `changes_requested` のどちらで判定したか（次回 calibration の手がかり）
   - **再発予測**: 次回同じ task signature が来たら同じ reviewer を **最初から** selection に含めるべきヒント
   - **抽出 skip 条件**: `added_by` 行が無い entry（manual selection 由来）は capture 対象外。`added_by: smi_block | impact_block` のみが対象
6. **Workflow Incident Review の capture**: `references/workflow-incident-review.md` に従い、GDD の進め方そのものの事故があれば `docs/learned-patterns.md` に記録する。対象 type は `hitl_readability` / `resume_mixup` / `worktree_contamination` / `skill_arbitration` / `context_loss` / `code_reading_gap` / `pr_review_followup_early_clean`。実装成果ではなく workflow の再発防止を残す欄なので、`何が起きたか` / `影響` / `検出した gate` / `再発防止` / `反映先` を短く書く
7. repo-level learned-patterns が採用済みなら `docs/learned-patterns.md` に追記する。既存エントリと重複する場合は更新する。採用済みでない repo では、新規作成ではなく ADR / repo 既定の学習ファイルに回す
8. 抽出するパターンがない場合はスキップする（空の追記はしない）

## Distill to ADR

branch-only steering を main に残さない代わりに、次回の人間と AI が読むべき判断だけを `docs/adr/` に残す。ADR は read-optimized な共有資産、raw task steering は write-optimized な作業ファイルである。

ADR に残す:

- Approved Direction
- 採用した設計方針と理由
- 却下した代替案と理由
- 「やらない」と決めたこと
- 後続 task が守るべき制約

ADR に残さない:

- tasklist の進捗
- Handoff Summary
- 個別 Verification evidence（PR / CI / test が証跡）
- 生ログ、会話の逐語、機密値

completion-check は `ADR distilled: yes | not_applicable` を確認する。`not_applicable` は trivial / quick express / 重要判断なしに限り、理由を 1 行で残す（`references/independent-review.md` の (3-f) で後続の test の要件を申し送った Decision があれば、Task Size によらず `not_applicable` にしない。`ADR distilled: not_applicable` で `state.md` に `Decision Handoff` の行があれば、pre-PR gate は `adr-na-with-decision-handoff` を不足として実行後に通知する）。strict 運用で main に raw steering を残す場合は human check の明示承認と ADR への理由記録が必要。

## Reviewer Lineage Patterns セクション format

```markdown
## Reviewer Lineage Patterns

### Pattern: <task signature の 1 行要約>
- task_signature: <変更ファイル種別 + scope keyword + 関連 AC>
- added_reviewer: <reviewer 名>
- trigger_source: smi_block | impact_block
- source_signal: <原因 or 仕様変更の 1 行要約>
- outcome: approved | changes_requested(N rounds)
- 次回適用ヒント: <task_signature 一致時に最初から含めるべき reviewer 選定>
- 記録日: <ISO8601 + TZ>
- 起源 task: <task id>
```

## `added_by` field の allowed values（Implementation Reviewer Selection）

`tasklist.md` の `Implementation Reviewer Selection` の各 entry に付ける `added_by` field は以下のいずれかを使う:

| value | 意味 | 設定する skill |
|---|---|---|
| `task-breakdown` | 標準必須 reviewer として初期枠で `selected`（`gdd-implementation-reviewer` / `gdd-security-reviewer` 等） | `gdd-task-breakdown` Step 8 |
| `lineage_pattern` | `learned-patterns.md` の Reviewer Lineage Patterns から **事前選定**された（次回適用ヒント=強い推奨 etc.）| `gdd-task-breakdown` Step 9a |
| `smi_block` | build loop 中に `root-cause-investigation` の Phase 4 SMI block で追加された | `gdd-systematic-debugging` § SMI Block Handoff |
| `impact_block` | build loop 中に `gdd-subagent-driven-implementation` の Spec Change Detection で追加された | `gdd-subagent-driven-implementation` § Spec Change Detection |

**capture 対象**: Reviewer Lineage Patterns への記録対象は **`smi_block` / `impact_block` のみ**（build loop 中の事後追加 = 学習材料）。`task-breakdown` / `lineage_pattern` は既に既知 pattern なので二重 capture しない。

**trace の対称性**: 事前追加（`task-breakdown` / `lineage_pattern`）でも事後追加（`smi_block` / `impact_block`）でも、entry 構造は同じ（reviewer 名 / status / reason / added_by / source_signal or source_pattern / added_at）。これにより `tasklist.md` 上で「いつ・なぜ追加されたか」を一意に追跡できる。

## Reviewer 種別の正式 key 名（参照導線）

`Implementation Reviewer Selection` で使う reviewer の正式 key 名は `references/reviewer-selection.md` を正本とする:

- `gdd-implementation-reviewer`: 標準必須
- `gdd-security-reviewer`: auth / secrets / untrusted input / shell / filesystem / permissions / LLM 呼び出し / エージェント実装 で `selected`
- `gdd-terraform-checklist-reviewer`: `.tf` / `.tfvars` / `.tf.json` 変更を含む場合に `selected`（`references/inline-review-checklists.md` § terraform 追加チェックを `gdd-implementation-reviewer` checklist 内で走査する形と等価）

key 名を SKILL.md / tasklist.md で記述する際は上記正式名を使う。略称（"terraform reviewer" 等）は避ける。

複数 task で同じ task_signature が記録された場合は entry を統合し `outcome` を「過去 N 回中 approved=M / changes_requested=K」のように頻度集計する。同 signature が **3 回以上記録された場合**、`次回適用ヒント` を「**強い推奨**」として強調する（task-breakdown / brainstorming の reviewer 初期枠選定で参照）。

## Why（詳細根拠）

- **Reviewer Calibration を明示的に learned-patterns に反映する**: false positive の検出 → 記録 → 次回調整の閉ループが成立する。これがないと同じ false positive が何度も remediation cycle を消費する
- **Migration Patterns を独立セクションにする**: この種のタスクが組織内で繰り返し発生する（各サービスの旧フォーマットを新フォーマットに移行する波が定期的に来る）。検知ヒント・AC テンプレート・失敗モードを残せば次回の brainstorming で同じ議論を省略できる
- **Reviewer Lineage Patterns で SMI / Impact Block の reviewer 追加履歴を蓄積する**: 「この種の task では security-reviewer が build loop 中に追加された」という履歴を残せば、次回同種 task の `gdd-task-breakdown` で **最初から** reviewer selection に含められる。build loop 中の事後追加 → 次回の事前追加に進化させることで、reviewer evidence の収集タイミングが早まり remediation cycle を削減できる
- **Workflow Incident Review で GDD 自体の事故を学習する**: HITL が読みにくい、resume が混線する、worktree が汚染される、skill arbitration が揺れる、context_loss で AC を読み落とす、code_reading_gap で設計がズレる、PR review follow-up が早く clean 扱いになる、といった問題は実装パターンではなく workflow 改善の材料である。`hitl_readability` / `resume_mixup` / `worktree_contamination` / `skill_arbitration` / `context_loss` / `code_reading_gap` / `pr_review_followup_early_clean` として分類し、再発防止を残す
- **空の追記はしない**: learned-patterns.md が noise で肥大化しないよう、本当にパターンとして残るもののみ記録する

## 関連 reference

- `cross-task-learning.md`: learned-patterns.md の format / lifecycle / lookup ルール
- `inline-review-checklists.md` § Reviewer Calibration: false positive 記録の field 構造
