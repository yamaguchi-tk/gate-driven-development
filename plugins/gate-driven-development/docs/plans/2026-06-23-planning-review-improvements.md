# GDD planning-reviewer 改善 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** planning-reviewer に「保守的すぎる設計推奨」を検知する 3 チェックを追加し、dialectic review の自動トリガーと要件フェーズの AC 品質ルールで多層防御する。

**Architecture:** markdown ファイル 3 件への追記のみ。コードは変更しない。各タスクは独立して実施可能。

**Tech Stack:** gate-driven-development local plugin (markdown)

## Global Constraints

- ファイルパスはすべて `~/.claude/plugins/local/gate-driven-development/` 配下
- 既存セクション・既存 severity 体系・既存フォーマットを踏み外さない
- 追加のみ（既存行の削除・書き換えなし）
- コミットは1タスク完結後に1回（Task 1〜3 をまとめて 1 コミットでも可）

---

## Task 1: gdd-planning-reviewer.md に 3 チェックを追加

**Files:**
- Modify: `agents/gdd-planning-reviewer.md`

**Interfaces:**
- Consumes: なし
- Produces: 以下の 3 finding を planning-reviewer が出力できるようになる
  - `Scope Narrowing without Evidence` (Medium)
  - `Scope Violation` (High)
  - `DRY Violation: Dual Source of Truth` (Medium)
  - `Deferred Technical Debt: unscheduled` (Low)
  - `Unverified Risk Claim` (Low)
  - `Scope Narrowing via Unverified Risk` (Medium)

- [ ] **Step 1: 挿入箇所が現在存在しないことを確認（RED）**

```bash
grep -n "Scope Alignment\|Single Source of Truth\|Risk Claim Evidence" \
  ~/.claude/plugins/local/gate-driven-development/agents/gdd-planning-reviewer.md
```

期待結果: 出力なし（チェックがまだ存在しない）

- [ ] **Step 2: 挿入箇所の正確な anchor text を確認**

```bash
grep -n "Execution / Evaluation Reality" \
  ~/.claude/plugins/local/gate-driven-development/agents/gdd-planning-reviewer.md
```

期待結果: `57:### Execution / Evaluation Reality ギャップチェック` のような行番号が返る。
この行の直前（2行前付近）がブランク行になっているはず。以下で確認する:

```bash
sed -n '54,58p' ~/.claude/plugins/local/gate-driven-development/agents/gdd-planning-reviewer.md
```

- [ ] **Step 3: 3チェックを `### Execution / Evaluation Reality ギャップチェック` の直前に挿入**

ファイル `agents/gdd-planning-reviewer.md` を Edit ツールで編集する。

`old_string` に `\n### Execution / Evaluation Reality ギャップチェック` を含むブロックの先頭を使い、
`new_string` で 3 チェックを挿入してから同行を続ける。

以下が追加するテキストの全体（`### Execution / Evaluation Reality ギャップチェック` の直前に挿入）:

```markdown

---

### 設計スコープの整合性（Scope Alignment）

設計が要件（AC）に対して範囲を縮小している場合、その根拠を検査する。

| 状況 | Severity |
|------|----------|
| AC が部分スコープを明示して許可している | OK（報告不要） |
| 縮小を具体的なコード箇所・ドキュメントで正当化している | OK（根拠を設計文書に記載） |
| 縮小の根拠が推測・慣習のみ | `Scope Narrowing without Evidence` **Medium** |
| 縮小が AC に直接違反している | `Scope Violation` **High** |

reporting 時は「ユーザーの当初要求と設計が乖離している点」を具体的に引用すること。

---

### 真実の情報源の一元性（Single Source of Truth）

変更後の設定・状態・所有権の管理が複数箇所に分散しないかを検査する。設定ドメイン（env var・SSM・DB・ファイル等）を問わず適用する。

- 変更後も同種の情報が複数箇所に存在し、時間軸付き移行計画がない: `DRY Violation: Dual Source of Truth` **Medium**
- 「後で直す」という言及があるがスケジュールが未定: `Deferred Technical Debt: unscheduled` **Low**

---

### リスク主張の証拠品質（Risk Claim Evidence Quality）

設計文書内の「X をすると Y が壊れる」「このアプローチは Z のリスクがある」等の主張を検査する。「〜の恐れがある」「〜になりかねない」「〜のリスクがある」という表現が出現したら毎回このチェックを走らせる。

| リスク主張の根拠 | 対応 |
|------|------|
| 具体的なコード箇所（ファイル＋行）あり | OK |
| 公式ドキュメント・ベンチマーク参照あり | OK |
| 推測・慣習・経験則のみ | `Unverified Risk Claim` **Low** — `assumed, not verified` と明記を要求 |
| 推測リスクのみを理由にユーザー要求スコープを縮小 | `Scope Narrowing via Unverified Risk` **Medium** |

```

- [ ] **Step 4: 挿入されたことを確認（GREEN）**

```bash
grep -n "Scope Alignment\|Single Source of Truth\|Risk Claim Evidence" \
  ~/.claude/plugins/local/gate-driven-development/agents/gdd-planning-reviewer.md
```

期待結果: 3行が返る（各セクションヘッダー）

---

## Task 2: dialectic-review.md に Conservative Design Challenge トリガーを追加

**Files:**
- Modify: `references/dialectic-review.md`

**Interfaces:**
- Consumes: Task 1 で定義された finding ID（`Scope Narrowing without Evidence` 等）
- Produces: gdd-design-gating 時に planning-reviewer の Medium 以上 finding があれば dialectic review が自動起動する

- [ ] **Step 1: 挿入箇所が現在存在しないことを確認（RED）**

```bash
grep -n "Conservative Design Challenge\|Scope Narrowing without Evidence" \
  ~/.claude/plugins/local/gate-driven-development/references/dialectic-review.md
```

期待結果: 出力なし

- [ ] **Step 2: 挿入箇所の anchor text を確認**

```bash
grep -n "独立レビュー\|敵対的レビュー" \
  ~/.claude/plugins/local/gate-driven-development/references/dialectic-review.md
```

期待結果: `28:- ユーザーが「独立レビュー」「敵対的レビュー」...` のような行番号が返る。
この行が現在の最後のトリガー条件。この行の直後に新しいトリガーを追加する。

- [ ] **Step 3: 最後のトリガー条件の後に新しいトリガーを挿入**

ファイル `references/dialectic-review.md` を Edit ツールで編集する。
`old_string` に上記 grep で見つかった最後のトリガー行を使う。
`new_string` でその行を残しつつ、その直後に以下を追加する:

```markdown
- planning-reviewer が `Scope Narrowing without Evidence`、`Scope Narrowing via Unverified Risk`、または `DRY Violation: Dual Source of Truth` を **Medium 以上**で報告した（Conservative Design Challenge）
  - gdd-design-gating 実行時に planning-reviewer の出力を受け取った直後に dialectic review を起動する
  - チャレンジ観点: ① 縮小スコープは全 AC を満たすか ② リスク主張をコードで確認したか ③ 全量対応コストを定量比較したか ④ 将来の全量化コストを試算したか
```

- [ ] **Step 4: 挿入されたことを確認（GREEN）**

```bash
grep -n "Conservative Design Challenge" \
  ~/.claude/plugins/local/gate-driven-development/references/dialectic-review.md
```

期待結果: 1行が返る

---

## Task 3: requirements-template.md に移行スコープ明記ルールを追加（**deferred: 別 PR で実施**）

> **ステータス: 未実装（本 PR 対象外）** — 別タスクで対応予定。

**Files:**
- Modify: `references/requirements-template.md`（本 PR には含まれない）

**Interfaces:**
- Consumes: なし
- Produces: 移行系タスクの requirements 作成時に、AC のスコープ明記が必須化される

- [ ] **Step 1: 挿入箇所が現在存在しないことを確認（RED）**

```bash
grep -n "AC Ambiguity.*migration\|移行スコープ\|migrate.*unify.*consolidat" \
  ~/.claude/plugins/local/gate-driven-development/references/requirements-template.md
```

期待結果: 出力なし

- [ ] **Step 2: USC Trace テーブルの定義行を確認**

```bash
grep -n "USC-1.*原文\|refined.*added.*unresolved" \
  ~/.claude/plugins/local/gate-driven-development/references/requirements-template.md | head -5
```

期待結果: USC Trace テーブルの行が返る（例: `124:| USC-1 | <原文> | ...`）

- [ ] **Step 3: USC Trace テーブルの直後に移行スコープ AC 品質ルールを挿入**

ファイル `references/requirements-template.md` を Edit ツールで編集する。
grep で見つかった USC Trace テーブルの最終行（`| USC-1 | <原文> | ... | Non-Goal / ...`行）の直後に以下を追加する:

```markdown

> **移行・統合・統廃合タスクの AC スコープ品質ルール**
> USC に `migrate` / `unify` / `consolidate` / `remove` 等を含む場合に適用:
>
> | パターン | AC に必要な記述 |
> |---------|---------------|
> | 全量移行 | 「N 個すべてを X に移す」と対象を定量化 |
> | 意図的な部分移行 | 除外対象と除外理由を AC に明示 |
> | 段階的移行 | フェーズ境界と各フェーズ完了定義を記載 |
> | 範囲があいまい | Status を `unresolved` にする（`AC Ambiguity: migration scope undefined`） |
>
> 悪い例: 「env var を整理する」「SSM に集約する」（範囲不明）
> 良い例: 「静的 env var N 個すべてを SSM Parameter Store に移行し、移行後の env var 数は 0 個になる」
```

- [ ] **Step 4: 挿入されたことを確認（GREEN）**

```bash
grep -n "移行・統合・統廃合タスク\|AC.*migration scope" \
  ~/.claude/plugins/local/gate-driven-development/references/requirements-template.md
```

期待結果: 追加した行が返る

---

## Task 4: コミットと事後検証

**Files:**
- 変更なし（Task 1〜2 で修正済みの 2 ファイルをコミット。Task 3 は別 PR に defer）

- [ ] **Step 1: 変更差分を確認**

```bash
git -C ~/.claude/plugins/local/gate-driven-development diff --stat
```

期待結果: 2 ファイルの変更が表示される（requirements-template は別 PR）

- [ ] **Step 2: 内容を確認**

```bash
git -C ~/.claude/plugins/local/gate-driven-development diff
```

期待結果: 追加行（`+`）のみで、削除行（`-`）は既存行の anchor として使われた分のみ

- [ ] **Step 3: コミット**

```bash
git -C ~/.claude/plugins/local/gate-driven-development add \
  agents/gdd-planning-reviewer.md \
  references/dialectic-review.md

git -C ~/.claude/plugins/local/gate-driven-development commit -m \
  "feat(reviewer): 保守的設計推奨の多層防御チェックを追加

- planning-reviewer: Scope Alignment / Single Source of Truth / Risk Claim Evidence Quality の3チェックを追加
- dialectic-review: Conservative Design Challenge トリガーを追加

背景: ある repo の設定移行タスクで planning subagent が根拠なくスコープを縮小した事例への対処
注: requirements-template への移行スコープ AC 品質ルール追加は別 PR に defer"
```

- [ ] **Step 4: 事後検証 — 設定移行タスクのセッション事例への手動適用**

今回の問題となったセッション（ある repo の設定移行タスク）のシナリオ:
「設定ストアへの移行を静的値だけに限定し、参照名の変数は env var に残す（コード確認なしの推測リスクが理由）」

3チェックで以下が検出されるはずかを確認する（人間が判断）:

| Finding | 期待 | 根拠 |
|---------|------|------|
| `Scope Narrowing via Unverified Risk` Medium | ✅ 検出されるべき | 参照名の変数を env var に残す根拠がコード未確認の推測 |
| `DRY Violation: Dual Source of Truth` Medium | ✅ 検出されるべき | 静的値は設定ストア、参照名の変数は env var に分散 |
| dialectic review トリガー | ✅ 起動されるべき | Medium finding が 2 件 |

---

## 受入確認

- [ ] `Scope Alignment` セクションが planning-reviewer.md に存在する
- [ ] `Single Source of Truth` セクションが planning-reviewer.md に存在する
- [ ] `Risk Claim Evidence Quality` セクションが planning-reviewer.md に存在する
- [ ] `Conservative Design Challenge` トリガーが dialectic-review.md に存在する
- [ ] 2 ファイルがコミットされている
- ※ 移行スコープ AC 品質ルールの requirements-template.md 追加は **別 PR で実施**
