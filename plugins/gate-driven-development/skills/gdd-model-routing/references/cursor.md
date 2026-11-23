# Cursor Model Routing

Cursor 環境向けのモデル選択補助ルール。共有正本は親の `SKILL.md` と plugin 直下の `references/cursor.md` / `references/fixed-models.md` に置く。

> 2026-08-25 最新化: Grok + Composer 主体へ移行。GPT 系は routing から除外した。

## 既定

- `Grok 4.6` は heavy tier の基本モデルにする。
  - 一般 heavy（debug / refactor / advisory review）: `reasoning.effort=low`
  - formal gate（brainstorming / requirements-gating / design-gating / implementation-gating / completion-check）: `reasoning.effort=medium`
- `Grok 4.5` は light task の標準にする（task-breakdown / TDD / pre-workflow-brainstorming / test-failure-debug-pack / receiving-code-review）。`pr-review` は light ではなく `general_heavy_risk`（`Grok 4.6` + `reasoning.effort=high`）に固定する。
- `Grok 4.5` + `reasoning.effort=low` は leaf task の標準にする（status / metrics / using-git-worktrees などの admin task）。state / routing source を読むため cheap lane には落とさない。
- cheap/read-only lane（短い要約、リンク確認、一覧整形、state 更新なし、routing 判断なし）も `Grok 4.5` + `reasoning.effort=low` を使う（`Grok Code Fast 1` がモデルピッカーに残っていればそちら）。
- Cursor で実装コードを触るときは `Composer 2.5` を標準に固定する。`composer-2-fast` は使わない。
- mini禁止境界として、cheap lane モデル（`Grok Code Fast 1` 等）は HITL生成 / requirements判断 / design判断 / routing判断 / state更新 / worktree判断 / completion判定 / PR可否判断には使わない。
- 旧 GPT 系の組み合わせは使わない。effort は low / medium / high の 3 段階のみ使う。

## Risk Escalation

一般 heavy はコスト最適化のため `Grok 4.6 + low` を標準にする。ただし、次の signal がある場合は `Grok 4.6 + high` へ上げる。

- `undocumented_step`: skill に明示手順が無い、想定外の分岐
- `large_working_set`: 64K 超級の working-set、長い会話継続、広域コード探索
- `security_sensitive`: 認可、secret、IAM、Terraform、運用影響など
- `final_review`: formal gate 外での最終判断・コードレビュー

formal gate は人間承認や gate 判定の読みやすさを優先し、`Grok 4.6 + medium` に固定する。formal gate 内で上記 signal があっても、既定の gate model/effort を正本とする。

## 起動時の固定表（Cursor）

| 役割 | Cursor |
| --- | --- |
| 相談だけの壁打ち | `Grok 4.5` + `reasoning.effort=medium` |
| formal gate | `Grok 4.6` + `reasoning.effort=medium` |
| 一般 heavy | `Grok 4.6` + `reasoning.effort=low` |
| 一般 heavy risk escalation / 最終 diff review | `Grok 4.6` + `reasoning.effort=high` |
| light task | `Grok 4.5` + `reasoning.effort=medium` |
| leaf task | `Grok 4.5` + `reasoning.effort=low` |
| cheap/read-only lane | `Grok 4.5` + `reasoning.effort=low` |
| 実装 | `Composer 2.5` |

## 判断の書き方（Cursor）

```text
model: Grok 4.5 (Cursor, reasoning.effort=medium) - light task の標準
```

```text
model: Grok 4.5 (Cursor, reasoning.effort=low) - leaf task / cheap/read-only lane の標準
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=low) - 一般 heavy の標準
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=medium) - formal gate の標準
```

```text
model: Grok 4.6 (Cursor, reasoning.effort=high) - 一般 heavy の risk escalation
```
