# gdd-writing-skills: skill テンプレート集（development-only）

> 移設元: `skills/gdd-writing-skills/SKILL.md`。新規 Phase Gate skill / 新規 Methodology skill を追加するときのテンプレートを、SKILL body budget 圧縮のため本ファイルに分離した。

## 新規 Phase Gate skill テンプレート

```markdown
---
# (Phase Gate skill 用 frontmatter テンプレート)
name: gdd-<name>
version: 0.1.0
description: "Internal: auto-routed when `Next Action=gdd-<name>`. Do not invoke directly — the state machine routes here. Responsibilities: <責務 1> + <責務 2> + <責務 3>."
---

# <Title>

<1-2 行で skill の役割>

## Goal

- <ゴール 1>
- <ゴール 2>

## Fixed Model

- `Claude Code`: `Sonnet` + `effort=medium`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light_task tier）
- skill/agent 執筆の品質確保のため mini は使わない

## Phase Gate Pre-check

開始前に確認する gate 状態:

- `state.md` の `Gate Status: <前 phase>=approved` を確認
- `tasklist.md` の `Next Action=gdd-<name>` を確認
- <他の前提条件>

満たさない場合は fail-closed で停止し、`参照した正本` / `不足条件` / `次の1アクション` を返す。

## Steps

1. <step 1>
2. <step 2>
...

## Output Guidance

phase 完了時の handoff 形式:

```markdown
## <Phase 名> 完了

### 確定事項
- ...

### 次のアクション
- → `Next Action=gdd-<次 phase>` に更新
```

## Rationalization Check（この skill 固有）

<1 行説明>。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「...」 | ... | [Bias Label] ... |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照。以下はこの skill 固有のルール。

- <固有ルール 1>
- <固有ルール 2>
- **Context Compaction Resilience**: <re-read すべきファイル>
```

## 新規 Methodology skill テンプレート

```markdown
---
# (Methodology skill 用 frontmatter テンプレート)
name: <name>  # gdd- prefix なし
version: 0.1.0
description: "Use when <trigger condition>. Provides <methodology の核> for <purpose>. Independent of any workflow — can be invoked standalone, from <GDD skill>, or by any agent."
---

# <Title>

<役割を 2-3 行で>

## なぜこの skill が要るか

<methodology を持たないとどうなるか、コスト構造>

## Iron Law

> **<太字の不可侵ルール>**

<違反すると何が起きるか>

## 適用範囲

使うべき場面:
- ...

使わない場面:
- ...

## <N> Phases / Steps

### Phase 1: <name>
...

### Phase 2: <name>
...

## Red Flags

以下のいずれかが頭をよぎったら止まる:
- 「...」
- 「...」

## 合理化との対決

> Methodology は **2 列**（superpowers 風 `出てくる言い訳 / 現実`）を採用する。GDD 専用 skill（Phase Gate / Specialized Helper / Lookup）の `Rationalization Check（この skill 固有）` § **3 列** とは別形式。詳細は本 skill の `Rationalization Check ルール` セクションを参照。

| 出てくる言い訳 | 現実 |
|---|---|
| 「...」 | ... |

## Quick Reference

| Phase | 何をする | 完了の判定 |
|---|---|---|
| ... | ... | ... |

## 他 skill との関係

- **`<related skill>`** — <関係の説明>
```

