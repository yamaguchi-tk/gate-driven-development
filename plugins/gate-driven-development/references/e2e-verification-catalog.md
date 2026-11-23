# E2E Verification Catalog

> **所有**: 構造化データを外部出力する skill に共通する E2E 検証パターン（Output Consistency / Delivery Channel Rendering / Multi-Run Comparison）の正本
> **上位正本**: `verification-before-completion.md`（Fresh Verification Rule、Iron Law、言語制限）
> **参照元**: `gdd-design-gating`（設計段階で記録）、`gdd-implementation-gating`（実装後に検証）、`gdd-completion-check`（最終 evidence 確認）

外部サービス（Slack / GitHub / wiki / メール / レポート）に構造化データを出力する skill では、LLM の非決定性とレンダリング制約により「1 回 E2E 成功 = 検証完了」と扱えない。本 reference は phase ごとの検証パターンを catalogue 化する。

## Pattern 1: Output Consistency Check（決定性・網羅性検証）

### 適用条件

- AC に「全件列挙」「決定性」「件数が変動しない」等が含まれる
- 構造化データ（list / table / JSON）を外部に投稿する
- データ件数が可変かつ 20 件超の可能性がある

### 検証手順

- 同じ入力で **2 回以上** E2E を実行する
- 出力の件数・項目・通し番号・分割数が全実行で一致するか比較する
- 比較方法を verification evidence に記録する（例: Slack スレッドの読み取り結果を並べて差異なしを確認）

### Severity

- 検証未実施 → Medium finding（impl-gate）
- 検証実施したが不一致 → High finding（実装の非決定性疑い）
- evidence が verification field に記録されていない → `status=fail`（completion-check）

### 設計時の対策（高 risk pattern の予防）

スクリプトが `--json` を返して LLM がフォーマット投稿する設計は **High risk**:

- データ件数が可変かつ 20 件超の可能性 + 全件忠実再現が必要 → スクリプト側で最終テキスト生成（`--slack-mrkdwn` パターン）に変更
- LLM が省略・要約しないよう「省略禁止」と書いても従わない（一覧の投稿機能で大半の行がドロップした事例）

LLM の判断が必要な出力（要約・ナラティブ・調査報告）は決定性不要のため許容する。

## Pattern 2: Delivery Channel Rendering Check

### 適用条件

外部サービス（Slack / GitHub / wiki 等）に出力する設計の場合、設計段階で `design.md` に以下を記録する:

- 出力先のマークアップ仕様（Slack mrkdwn / GitHub Markdown / wiki の Markdown）
- AgentCore ツール結果経由の場合のエスケープ処理影響（Slack: `<url|text>` 形式は HTML エスケープされ壊れるため plain URL 使用）
- 出力フォーマットのサンプル（期待される描画結果）

### Severity

- 設計時に記録なし → Medium finding（design-gating）
- E2E で実際の描画が破損 → High finding（impl-gate / completion-check）

### Why

AgentCore 経由の Slack 出力で `<url|text>` が `&lt;url|text&gt;` にエスケープされリンクが壊れた事例。設計段階でレンダリング制約を確認すれば E2E での発見を待たずに防げる。

## Pattern 3: Multi-Run Comparison（Output Consistency Evidence）

### 適用条件

`verification` field の AC 行が「決定性」「網羅性」「全件」を含む場合、completion-check の evidence に複数回実行の比較結果を要求する。

### Evidence 要件

- 2 回以上の E2E 実行結果の差異なし確認
- 比較方法の記録（diff command、Slack 読み取り、JSON snapshot 等）
- 1 回の成功だけでは `status=pass` にしない

### Severity

- evidence 不足 → `status=fail`、追加 E2E 実行を要求

## Phase ごとの責務

| Phase | Skill | 担う pattern | 役割 |
|---|---|---|---|
| 設計 | `gdd-design-gating` Step 5b | Pattern 2 (Delivery Channel) + Pattern 1 高 risk pattern の予防 | レンダリング制約と高 risk フォーマット pattern を `design.md` に記録 |
| 実装 | `gdd-implementation-gating` Step 1a | Pattern 1 (Output Consistency) | 2 回以上 E2E 実行を確認、未実施なら Medium finding |
| 完了 | `gdd-completion-check` Part A-2 | Pattern 3 (Multi-Run Comparison) | 複数回実行 evidence を verification に要求、不足なら `status=fail` |

各 phase は本 reference を pointer 参照する。inline で同じ手順を繰り返さない。

## 各 skill の SKILL.md での参照方法

```markdown
# 例: gdd-implementation-gating 内
1a. **E2E 一貫性検証**: `references/e2e-verification-catalog.md` § Pattern 1 を適用する。2 回以上の実行確認が未実施なら Medium finding。
```

```markdown
# 例: gdd-design-gating 内
5b. **Delivery Channel Rendering Check**: `references/e2e-verification-catalog.md` § Pattern 2 を適用する。出力先のマークアップ仕様 / エスケープ影響 / フォーマットサンプルを `design.md` に記録。
```

inline 再記載は避け、skill 固有の context（評価結果 / 戻し先 route）だけを残す。

## Why（このパターンの根拠）

- E2E 検証パターンが 3 skill にまたがって inline 記載され、一覧の投稿機能の事例の同じ Why を 3 回繰り返している
- catalogue 化により phase 横断で「同じ pattern を異なる役割で実行している」ことが visible になる
- Fresh Verification Rule や Iron Law は `verification-before-completion.md` が正本。本 reference は「外部出力に特化した patterns」に絞る
