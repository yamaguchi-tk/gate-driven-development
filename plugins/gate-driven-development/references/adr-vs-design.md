# ADR vs design.md: 責務の境界

> **所有**: artifact 間の書き分けルール
> **参照元**: `gdd-design-gating`、`gdd-subagent-driven-implementation`、`gdd-completion-check`、`gdd-pr-review`

## Why this reference exists

`design.md` と `adr.md` の役割が曖昧なまま運用されると、同じ情報が両方に書かれたり、どちらにも書かれなかったりする。特に Spec Change Detection で「どこに何を書くか」の判断が skill ごとにブレると、後続の Drift Check が検出漏れを起こす。

## 責務の定義

| Artifact | 役割 | 書くもの | 書かないもの |
|----------|------|---------|------------|
| `design.md` | **現在の正しい設計**（What） | 変更点の要約、影響範囲、主要フロー、テスト方針、ロールバック手順、Route/Ownership Matrix、Sensitive Data Policy | 却下した代替案の詳細な理由、過去の判断の経緯 |
| `adr.md` | **意思決定の履歴**（Why + 却下案） | Context、Decision、Why、Consequences、却下した代替案とその理由 | 現在の設計の詳細仕様（フロー図、API schema 等） |
| repo ADR（例: `docs/adr/NNNN-<slug>.md`） | **merge 後に残す意思決定の正本** | GDD の `adr.md` から蒸留した Context、Decision、Why、Consequences、Rejected Alternatives、Source | raw task steering 全文、作業ログ、テスト実行結果、詳細仕様 |

## 判断基準

**「今の設計を理解するために読むか？」**
- Yes → `design.md` に書く
- No、ただし「なぜこの設計にしたか」を知るために読む → `adr.md` に書く
- 両方に該当する → `design.md` に現在の仕様を書き、`adr.md` に判断理由と却下案を書く

## 典型パターン

### パターン 1: 新しい設計判断

1. `design.md` の該当セクションに採用した設計を記述する
2. `adr.md` に `Context` / `Decision` / `Why` / `Consequences` を追記する
3. 検討したが却下した代替案は `adr.md` にのみ書く

### パターン 2: 実装中の仕様変更（Spec Change Detection）

1. `adr.md` に変更の Context（何が判明したか）と Decision（何を変えたか）を追記する
2. `design.md` の該当セクションを**現在の正しい設計に上書き更新**する（差分は git で見る）
3. `requirements.md` の AC に影響がある場合は AC も同じ diff で更新する

### パターン 3: E2E Discovery で判明した制約

1. `adr.md` に「E2E で判明した事実 / 採用した設計変更 / 却下した代替案」を追記する
2. `design.md` の該当セクションに制約を直接反映する
3. AC の前提に影響する場合は `human_recheck_required` に escalate する

## アンチパターン

| やりがち | 正しい対応 |
|---------|-----------|
| `adr.md` だけ書いて `design.md` を更新しない | `design.md` は常に「現在の正しい設計」を反映する。adr を書いたら design も必ず同期する |
| `design.md` に却下理由を長文で書く | 却下理由は `adr.md` の Consequences セクションに書く。design.md には採用した設計だけを残す |
| 「些細な変更だから adr は不要」と判断する | Spec Change Detection の 4 条件に該当すれば adr は必須。些細かどうかは判断基準にしない |
| `adr.md` に現在の API schema 全体をコピーする | adr には判断の根拠に必要な最小限の技術情報だけを書く。詳細仕様は design.md を参照する |

## adr.md の構造

```markdown
## ADR-N: <判断タイトル>

- **Origin**: remediation / <Current Task>（remediation ループ由来のエントリのみ必須。通常の planning 判断では省略）
### Context
（何が起きたか、何が判明したか）

### Decision
（何を決めたか）

### Why
（なぜこの判断をしたか — 却下した代替案との比較を含む）

### Consequences
（この判断の結果、何が変わるか — 良い影響と悪い影響の両方）
```

- ADR 番号は steering ディレクトリ内で連番にする（`ADR-1`, `ADR-2`, ...）。1 つの判断 = 1 つの ADR エントリとし、複数の判断を 1 エントリにまとめない
- E2E Discovery Loop や Spec Change Detection で追記する場合もこの構造に従う。`Origin` 行（remediation 由来のエントリは見出し直後に必須。`references/state-machine.md` § Remediation Loop Safety の ADR ≥2 独立トリガーが数える）も同じ構造に含める

## repo ADR への Distill

standard 運用では raw task `.steering/<task>/` は branch-only artifact であり、main に長期保存しない。merge 後も参照する必要がある判断は、PR 作成前または merge 前に repo の ADR 置き場（例: `docs/adr/`）へ蒸留する。

### Distill 対象

repo ADR にする:

- process contract / responsibility boundary / security boundary / prompt-output contract を変えた
- technology stack / access method / credential backend / multi-tenant boundary / official integration adoption を決めた
- repo 構造、module 境界、build / deploy / test contract、運用 guardrail を固定した
- contract test、runbook、guardrail、将来の reviewer 判断がこの決定に依存する（`references/independent-review.md` の (3-f) で後続の test の要件を Issue に申し送った Decision は、Task Size によらずここに入る）

repo ADR にしない:

- 単発の実装手順、作業ログ、調査ログ、テスト実行結果
- PR 内で完結する小さなバグ修正
- 現在の詳細仕様そのもの。詳細は実装、`design.md`、runbook、または該当 docs を正本にする

### repo ADR の推奨構造

repo に既存 ADR 形式がある場合はそれを優先し、GDD 由来の判断では次の情報を欠落させない。

```markdown
# ADR-NNNN: <判断タイトル>

## Status

Accepted (YYYY-MM-DD, PR #xxx)

## Context

<何が起きたか、何が判明したか。GDD の requirements/design/adr から要約する>

## Decision

<何を決めたか。現在の詳細仕様ではなく、判断として残す内容を書く>

## Why

<なぜこの判断にしたか。却下した代替案との比較を含める>

## Rejected Alternatives

- <案>: <採用しなかった理由>

## Consequences

<この判断の結果、何が良くなり、どんな制約や再検討条件が残るか>

## Source

- Derived from `.steering/YYYYMMDD-<slug>/`
- Related PR: #xxx
```

PR / cleanup 時に ADR 化しない場合は、PR body、completion summary、または state/worklog のいずれかに `ADR distilled: not_applicable | reason: ...` を残す。理由なしに raw steering だけを削除しない。
