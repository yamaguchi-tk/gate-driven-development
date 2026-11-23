# Gate Status Schema（正本）

`state.md` / `tasklist.md` に書く gate status・reviewer status の **共通フォーマットの唯一の正本**。各 gate skill は inline で schema を再掲せず、この reference を pointer で参照する。機械可読な許容値・precheck 最小条件は `references/state-schema.json` にも同期しており、文書と hook / test の drift を防ぐ。

> **関連**: `state.md` に出てくる**全 field の Tier 分類**（Core / Phase-Specific / Audit）と phase ごとの **Minimum Required Set** は `state-field-tiers.md` を参照。本 reference は gate / reviewer 系 field の status 値・更新フォーマットに集中し、field の lifecycle 全体は state-field-tiers.md が正本。

## Phase-level gate status

対象フィールド（`state.md`）:

- `Requirements Review Status`
- `Design Review Status`
- `Human Check Status`

### 許容値

| フィールド | 許容値 |
|-----------|--------|
| `Requirements Review Status` | `pending` / `in_review` / `changes_requested` / `approved` |
| `Design Review Status` | `pending` / `in_review` / `changes_requested` / `approved` |
| `Human Check Status` | `pending` / `changes_requested` / `approved` |

- **`waived` はいずれの phase-level status でも使わない**。必須 gate なので skip は許さない
- **人の承認は `Human Check Status=approved` だけを使う**（独自 status は許可しない）。ユーザー本人のターンの承認は `evidence: human:<承認した自走上限の値>` にする。本人の事前回答を適用した承認も同じ形にし、値に補足を付けない（事前回答であることは `worklog.md` の行で区別する。`references/human-check-template.md` § 事前回答）（`references/post-merge-qa.md` 手順 2 が本人の承認をこの形で判定する）。`risk-low:`（リスクの段が低のときの承認）は、`request-crosscheck.md` のリスクの段が `低` と読め、依頼の原文がある（`request.md` が hook の節で始まる通常のファイルである。Codex・Cursor の steering は当たらない）steering の state.md にだけ書ける（`hooks/scripts/lib/risk_tier.py`。表記の揺れを含め、それ以外の steering の state.md に触れる書き込みが `risk-low` を足せば、steering の書き込み hook が止める）。`requirements.md` の § ズレ確認 に、ユーザーの決めた規則・方針の側に仮決定した `既存とぶつかる` の行があり、その行を引用した本人の承認が `request.md` に無い steering では、`risk-low:` を使わず本人の承認を待つ（`references/human-check-template.md` § 事前回答 3 と同じ条件。risk-low では一次表示を出さないので `requirements.md` で読む。risk-low は承認の記録にならないため。hook はこれを検査しない）。`記録の場所: なし` の行の扱いは、`references/post-completion-pr-flow.md` の Step 4 と Autonomy Decisions Check に従う。`approved` のまま書き直すとき（design-gating・task-breakdown・design_detail_only など）は、元の evidence をそのまま写す。
- 各 status の意味:
  - `pending`: まだ着手していない
  - `in_review`: reviewer 起動中 / 人間確認中
  - `changes_requested`: 差し戻し中（自律 remediation ループの開始点として扱う）
  - `approved`: 通過

### 更新フォーマット

以下の 4 要素を `|` で連結した 1 行で更新する:

```
<status> | evidence: <id> | updated_by: <skill-name> | updated_at: <ISO 8601 timestamp>
```

- **`<status>`**: 上記の許容値のいずれか
- **`evidence`**: 根拠となる id
  - `in_review` 遷移時: `review-start:<reviewer-or-task-id>` または `<review-start-id>`
  - `approved` / `changes_requested` 遷移時: 対応する review run の id か、本人の差し戻しの approval id（例: `<requirements-review-id>`）。`Human Check Status` の `approved` は上の `human:<自走上限の値>`・`risk-low:<記録のファイル>`（リスクの段が `低` と読める steering だけ）のどれか
  - `pending` に戻す時: `none`
- **`updated_by`**: 更新を実行した skill 名（例: `gdd-requirements-gating`, `gdd-design-gating`, `gdd-implementation-gating`, `gdd-completion-check`）
- **`updated_at`**: 更新時刻（ISO 8601）

### 関連フィールド

- `Resume From=<next-skill>`: 次に実行する skill
- `Next Action=<skill-or-state>`: state machine が次に routing する先

## `Status`（廃止した hook の印）

`Status` は gate status でも進捗表現でもない。compact 自動復帰（2026-09-28 に廃止）のときに PreCompact hook が `paused` を書き、SessionStart hook が読んでいた印で、今は hook が書きも読みもしない。同じ往復の `CompactSessionId` / `CompactSource` / `AutoCycleCount` / `PausedAt` / `CompactTranscriptOffset` も同じ扱い。

- **skill / LLM はこの field に書かない**。進捗は `Resume From` / `Next Action` で表現する
- 既存の state.md に残っていても害は無く、消してもよい
- 機械可読な一覧は `references/state-schema.json` § `retired_hook_fields` と同期する

**Why**: compaction の hook は、main の compaction か subagent の compaction かを入力から見分けられず（Claude Code 2.1.280）、自動復帰の文が subagent に届いていた。compaction の前後で「再開せよ」「再開するな」のどちらも注入しないことにし、印を廃した。

## Reviewer-level status

対象: `Review Status`（`tasklist.md` に書く per-reviewer state）

### フィールド構造

reviewer ごとに以下を持つ:

- `<reviewer>.status`: `pending` / `in_review` / `approved` / `changes_requested` / `waived`
- `<reviewer>.evidence`
- `<reviewer>.updated_by`
- `<reviewer>.updated_at`
- `<reviewer>.waiver_reason`（`status=waived` のときのみ必須）

### Waived の扱い

- reviewer-level status は `waived` を許す（phase-level とは異なる）
- `waived` は「その reviewer 観点が current task に本当に非該当」な場合のみ使用可能
- real issue の受容には使わない（受容する場合は `approved` にせず `changes_requested` のまま差し戻すか、`human_recheck_required` に escalate）
- 遷移で `waived` から離れる時（`pending` / `in_review` / `approved` / `changes_requested` に戻す時）は古い `waiver_reason` を必ずクリアする

### 対象 reviewer（例）

- `gdd-planning-reviewer`（requirements / design gate）
- `gdd-security-reviewer`（design / implementation gate の条件付き）
- `gdd-implementation-reviewer`（implementation gate）
- `gdd-completion-reviewer`（completion gate）

## 選択肢記録（Reviewer Selection）

対象:

- `Planning Reviewer Selection`（`state.md`）
- `Implementation Reviewer Selection`（`tasklist.md` の per-task 一時状態）

### フィールド

- reviewer ごとに `pending` / `selected` / `waived` と `reason`
- `selection_change_reason`, `updated_by`, `updated_at` を残す
- selection rule の正本: `references/reviewer-selection.md`

## 永続化のタイミング

- **reviewer 起動前**: selected reviewer を `in_review` に更新し、`evidence=review-start:<id>` を設定
- **reviewer 完了直後**: 判定結果を `approved` / `changes_requested` に遷移し、`evidence` を review run id に更新
- **phase 遷移時**: 関連する phase-level status を一括で永続化（`Resume From` も同時に更新）
- **rollback pattern 適用時**: `references/rollback-patterns.md` のパターンに従う

## Why

- gate status の schema が skill ごとに微妙にズレると、`state.md` の parse 側（SessionStart hook / `gdd-status` / `gdd-systematic-debugging`）が壊れる
- `waived` を phase-level で許すと必須 gate が silent skip されるリスクがある
- evidence / updated_by / updated_at を省略すると、どの skill が何時点で何を根拠に更新したかが追えず、監査と rollback が成立しない

## 新規 gate を追加するときの checklist

新しい phase-level gate を導入する場合:

- [ ] 上記 4 要素（status / evidence / updated_by / updated_at）を固定で使う
- [ ] `waived` を許すかを決める（`Human Check Status` 同様、必須 gate なら不許可）
- [ ] `references/rollback-patterns.md` に差し戻しパターンを追加する
- [ ] この reference の「対象フィールド」表に 1 行追加する
