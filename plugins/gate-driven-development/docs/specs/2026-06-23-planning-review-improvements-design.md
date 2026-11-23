# 設計文書: GDD planning-reviewer 改善 — 保守的設計推奨の多層防御

**日付**: 2026-06-23  
**ステータス**: Draft  
**対象バージョン**: gate-driven-development (local plugin)

---

## 背景・動機

GDD セッション内で planning subagent が以下の問題を起こした:

- ユーザーが「全量移行」を要求したにもかかわらず、「部分移行」を推奨した
- 推奨の根拠がコード確認なしの推測ベースのリスク主張だった
- 結果として設定管理が 2 箇所に分散する DRY 違反設計が提案された

この問題は **3 層の防御**（要件フェーズ / 設計レビュー / dialectic review）で防ぎ得る。

---

## 設計ゴール

1. 設計レビュー (planning-reviewer) が「保守的すぎる設計」を検知できるようにする
2. 設定・状態・所有権の DRY 違反を設計フェーズで検知する
3. コード根拠のないリスク主張を識別しラベリングする
4. 要件フェーズで移行スコープを定量明記させ、upstream から絞り込む
5. planning-reviewer の Medium 以上 finding で dialectic review を自動トリガーする

---

## 変更ファイル一覧

| ファイル | 変更種別 | 目的 |
|---------|---------|------|
| `agents/gdd-planning-reviewer.md` | 追加 | チェック①②③ を追加 |
| `references/dialectic-review.md` | 追加 | Conservative Design Challenge トリガーを追加 |
| `references/requirements-template.md`（実装時に確認） | 追加（**deferred: 別 PR で実施**） | 移行タスクの AC 品質ルールを追加 |

---

## 変更詳細

### 変更1: gdd-planning-reviewer.md — 3 チェックの追加

既存の `YAGNI / MVP スコープ` セクションの直後に追加する。

---

#### チェック①: 設計スコープの整合性 (Scope Alignment)

設計が要件（AC）に対して範囲を縮小している場合、その根拠を検査する。

| 状況 | Severity |
|------|----------|
| AC が部分スコープを明示して許可している | OK |
| 縮小を具体的なコード箇所・ドキュメントで正当化している | OK（根拠を設計文書に記載） |
| 縮小の根拠が推測・慣習のみ | `Scope Narrowing without Evidence` **Medium** |
| 縮小が AC に直接違反している | `Scope Violation` **High** |

reporting 時は「ユーザーの当初要求と設計が乖離している点」を具体的に引用すること。

---

#### チェック②: 真実の情報源の一元性 (Single Source of Truth)

変更後の設定・状態・所有権の管理が複数箇所に分散しないかを検査する。

- 変更後も同種の情報（設定値・パラメータ・auth 情報等）が複数箇所に存在する: 時間軸付き移行計画を要求
- 恒久的なデュアルソース設計（移行計画なし）: `DRY Violation: Dual Source of Truth` **Medium**
- 「後で直す」はあるがスケジュール未定: `Deferred Technical Debt: unscheduled` **Low**

設定ドメイン（env var・SSM・DB・ファイル等）を問わず適用する。

---

#### チェック③: リスク主張の証拠品質 (Risk Claim Evidence Quality)

設計文書内の「X をすると Y が壊れる」「A のリスクがある」等の主張を検査する。

| リスク主張の根拠 | 対応 |
|------|------|
| 具体的なコード箇所（ファイル＋行）あり | OK |
| 公式ドキュメント・ベンチマーク参照あり | OK |
| 推測・慣習・経験則のみ | `Unverified Risk Claim` **Low** — `assumed, not verified` と明記を要求 |
| 推測リスクのみを理由にユーザー要求スコープを縮小 | `Scope Narrowing via Unverified Risk` **Medium** |

「〜の恐れがある」「〜になりかねない」「〜のリスクがある」という表現が出現したら毎回このチェックを走らせる。

---

### 変更2: dialectic-review.md — Conservative Design Challenge トリガー追加

既存のトリガー条件リストに以下のセクションを追加する。

```markdown
## Conservative Design Challenge（過保守設計チャレンジ）

以下のいずれかが planning-reviewer から報告された場合、gdd-design-gating 実行時に planning-reviewer の出力を受け取った直後に dialectic review を起動する（必須）:

1. `Scope Narrowing without Evidence` (Medium 以上)
2. `Scope Narrowing via Unverified Risk` (Medium 以上)
3. `DRY Violation: Dual Source of Truth` (Medium 以上)

dialectic review のチャレンジ観点:
- 縮小されたスコープは要件の AC をすべて満たすか？
- リスク主張の根拠をコードで実際に確認したか？
- 全量対応した場合のコストは partial より著しく高いか？（数値または具体的比較で示す）
- 現在提案されている設計で、ユーザーが将来「全量化」しようとした場合の移行コストは？
```

---

### 変更3: AC 品質ガイドライン — 移行スコープの定量明記

移行・統合・統廃合タスク（migrate / unify / consolidate / remove 等）のACに適用する。

**追加ルール:**

| パターン | AC に必要な記述 |
|---------|---------------|
| 全量移行 | 「N 個すべてを X に移す」対象を定量化 |
| 意図的な部分移行 | 除外対象と除外理由を AC に明示 |
| 段階的移行 | フェーズ境界と各フェーズ完了定義を記載 |
| 範囲があいまいな AC | `AC Ambiguity: migration scope undefined` として gating でブロック |

**AC 記述例:**

```
# 良い例
- 静的 env var N 個を全量 SSM Parameter Store に移行する
- 移行後、関数の環境変数は参照名の変数を含めて 0 個になる

# 悪い例（NG）
- env var を整理する
- SSM に集約する（範囲不明）
```

---

## 防御層の全体像

```
要件フェーズ
  └─ AC に移行スコープを定量明記（変更3）
       ↓ 通り抜けた場合
設計レビュー
  └─ planning-reviewer が Scope/DRY/Risk を検知（変更1）
       ↓ Medium 以上 finding が出た場合
dialectic review
  └─ Conservative Design Challenge でスコープ縮小を二重チェック（変更2）
```

---

## スコープ外

- implementation-reviewer / completion-reviewer への同種チェックの追加（別タスク）
- common-guardrails.md への横断展開（影響範囲が広いため別評価）
- 既存の YAGNI チェックとのマージ（混在を避けるため独立したセクションとして追加）

---

## 受入条件（本 PR のスコープ）

1. planning-reviewer.md に 3 チェックが追加されている
2. dialectic-review.md に Conservative Design Challenge トリガーが追加されている
3. 今回のセッション（ある repo の設定移行タスク）を事後適用した場合、`Scope Narrowing via Unverified Risk` (Medium) が検出されること（手動検証）

> **別 PR 対応**: AC 品質ガイドラインへの移行スコープ明記ルール追加は `references/requirements-template.md` への追記として別 PR で実施する。
