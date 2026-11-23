# GDD UX 改善 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 停止時の次ステップ案内不足・スコープ変更未告知・調査中間報告なし・状態ロストの4問題を2ファイルへの追記で修正する。

**Architecture:** markdown ファイル 2 件への追記のみ。コードは変更しない。Task 1 と Task 2 は独立して実施可能。

**Tech Stack:** gate-driven-development local plugin (markdown)

## Global Constraints

- ファイルパスはすべて `~/.claude/plugins/local/gate-driven-development/` 配下
- 追加のみ（既存行の削除・変更なし）
- 既存のフォーマット・スタイル（見出しレベル、箇条書き形式）を踏み外さない
- git リポジトリが存在する場合はコミット可（存在しない場合はコミット不要）

---

## Task 1: output-format.md にカテゴリA+B の追加

**Files:**
- Modify: `references/output-format.md`（489行）

**Interfaces:**
- Consumes: なし
- Produces: 以下の2つのルールが output-format.md に存在する
  - proactivity 注記（カテゴリA）: `### 停止時の「👤 次にすること」マップ` の直前
  - スコープ変更通知ルール（カテゴリB）: ファイル末尾

- [ ] **Step 1: 挿入箇所が現在存在しないことを確認（RED）**

```bash
grep -n "proactive\|スコープ変更通知\|スコープ外になった項目" \
  ~/.claude/plugins/local/gate-driven-development/references/output-format.md
```

期待結果: 出力なし

- [ ] **Step 2: カテゴリA — proactivity 注記の挿入箇所を確認**

```bash
grep -n "停止時の.*👤.*マップ" \
  ~/.claude/plugins/local/gate-driven-development/references/output-format.md
```

期待結果: `346:### 停止時の「👤 次にすること」マップ（必須 trailing block）`

- [ ] **Step 3: カテゴリA — proactivity 注記を `### 停止時の「👤 次にすること」マップ` の直前に挿入**

ファイル `references/output-format.md` を Edit ツールで編集する。

old_string: `### 停止時の「👤 次にすること」マップ（必須 trailing block）`

new_string（以下のテキストを old_string の前に挿入し、old_string も残す）:

```markdown
> **MUST: proactive に書くこと**
> このブロックは stop hook が出力後に検査するが、**hook に頼らず最初から書くこと**。
> hook に指摘されてから追加するのは reactive 修正であり、不要なコンテキストを消費するため禁止。
> subagent をバックグラウンド起動して停止する場面でも必ず書く。

### 停止時の「👤 次にすること」マップ（必須 trailing block）
```

- [ ] **Step 4: カテゴリA — 挿入確認（GREEN）**

```bash
grep -n "proactive に書くこと\|hook に頼らず" \
  ~/.claude/plugins/local/gate-driven-development/references/output-format.md
```

期待結果: 1〜2行が返る

- [ ] **Step 5: カテゴリB — スコープ変更通知ルールをファイル末尾に追加**

ファイル末尾（最後の ` ``` ` 行の後）に以下を追記する。
現在の末尾付近は `- → 準備ができたら \`/gdd-dev 再開\` で completion check を再実行` で終わっている。

ファイル末尾の ` ``` ` の直後に以下を追加する:

```markdown

---

### スコープ変更通知

セッション中にタスクの対象・範囲が変わった場合（別サブタスクへの移行・問題の切り分け・意図的な絞り込みを含む）、
以下を停止出力または作業完了報告の末尾に **必ず** 追加する:

> **スコープ外になった項目**
> - <元のタスクや要求で、今回対応しなかった項目>
> - 理由: <スコープ外にした理由>
> - 対処が必要な場合: <ユーザーが次にすべき操作>

スコープ変更に気づかず省略した場合、ユーザーは「対応済みか未対応か」を判断できない。

**スコープ変更の例**:
- 「Aバグ調査」で始まり「Bバグ修正の PR 作成」で完了した場合 → 「Aバグへの対処は今回スコープ外」を明記
- 「全 env var の SSM 移行」を依頼されて「静的値のみ」を移行した場合 → 「PARAM_NAME / SECRET は今回未対応」を明記
```

- [ ] **Step 6: カテゴリB — 挿入確認（GREEN）**

```bash
grep -n "スコープ変更通知\|スコープ外になった項目" \
  ~/.claude/plugins/local/gate-driven-development/references/output-format.md
```

期待結果: 2行が返る

---

## Task 2: root-cause-investigation/SKILL.md にカテゴリC+D の追加

**Files:**
- Modify: `skills/root-cause-investigation/SKILL.md`（596行）

**Interfaces:**
- Consumes: なし
- Produces: 以下の4つのルールが SKILL.md に存在する
  - 中間報告ルール（10ツール呼び出しごと）
  - 仮説→検証→結論サイクル
  - 調査完了後の遷移案内
  - `.gdd/rci-findings.md` へのレジャー記録

- [ ] **Step 1: 挿入箇所が現在存在しないことを確認（RED）**

```bash
grep -n "中間報告\|仮説.*検証.*結論\|rci-findings\|10ツール" \
  ~/.claude/plugins/local/gate-driven-development/skills/root-cause-investigation/SKILL.md
```

期待結果: 出力なし

- [ ] **Step 2: ファイル末尾の anchor を確認**

```bash
tail -5 ~/.claude/plugins/local/gate-driven-development/skills/root-cause-investigation/SKILL.md
```

期待結果: `worklog.md` の Error Log や `gdd-systematic-debugging` に関する行で終わっている

- [ ] **Step 3: カテゴリC+D のセクションをファイル末尾に追加**

ファイル末尾の最終行の後に以下を追記する（Edit ツールで末尾の anchor 行を old_string に使う）。

追加するテキスト:

~~~~markdown

---

## 中間報告・調査サイクル・状態永続化

### 中間報告ルール（10ツール呼び出しごと）

10ツール呼び出しごとに、以下の形式で中間サマリーをユーザーに向けてテキスト出力する:

> **調査中間報告**（ツール呼び出し N 回目）
> - 確認済みの事実: <箇条書き>
> - 現在の仮説: <1-2行>
> - 次に検証すること: <1-2行>
> - 残り不明な点: <箇条書き>

### 仮説→検証→結論サイクルの遵守

調査は以下のサイクルで進める。サイクルを飛ばして深掘りしない:

1. **仮説を立てる**: 証拠から根本原因の候補を 1-3 個絞る
2. **検証する**: 仮説を確認/反証できる最小のツール呼び出しを行う
3. **結論を更新する**: 証拠が仮説を支持するか判断し、次の仮説に移る
4. **収束判定**: 仮説が 1 つに絞られ、確認証拠が揃ったら調査完了

### 調査完了後の遷移案内

調査が完了したら（`<gdd-stop reason="done">` 出力時）、`👤 次にすること` に以下を含める:

- 根本原因のサマリー（1-3行）
- 修正が必要な場合: 「修正を進めるには『修正して』と指示してください」
- GDD フローで進める場合: 「`/gdd-dev` で修正フェーズを開始できます」

### 調査発見事項のレジャー記録

重要な発見（根本原因の特定・確認証拠・除外した仮説）は都度、以下のファイルに記録する:

ファイル: `.gdd/rci-findings.md`（なければ作成）

```markdown
# Root Cause Investigation Findings

## <タスク名> (<日付>)
- **確認済み**: <発見事項>
- **除外**: <除外した仮説と理由>
- **現在の仮説**: <最新の仮説>
```

このファイルはコンテキストが切れても残るため、再開時に Read することで調査状態を復元できる。
長時間調査（ツール呼び出し 20 回超）では必ず記録すること。
~~~~

- [ ] **Step 4: 挿入確認（GREEN）**

```bash
grep -n "中間報告ルール\|仮説.*検証.*結論\|rci-findings\|遷移案内" \
  ~/.claude/plugins/local/gate-driven-development/skills/root-cause-investigation/SKILL.md
```

期待結果: 4行が返る（各セクションヘッダー）

---

## 受入確認

- [ ] `grep -n "proactive に書くこと" output-format.md` が返る
- [ ] `grep -n "スコープ変更通知" output-format.md` が返る
- [ ] `grep -n "中間報告ルール" root-cause-investigation/SKILL.md` が返る
- [ ] `grep -n "仮説.*検証.*結論" root-cause-investigation/SKILL.md` が返る
- [ ] `grep -n "遷移案内" root-cause-investigation/SKILL.md` が返る
- [ ] `grep -n "rci-findings" root-cause-investigation/SKILL.md` が返る
