---
name: gdd-refactor-planning
description: "Use for GDD refactor or cleanup planning when approved behavior should not change."
version: 0.1.0
---

# Refactor Planning Lite

実装後または completion 後に、挙動を変えないリファクタだけを計画する skill。新機能追加や要件変更は担当しない。approved な requirements / design / tasklist を前提に、リファクタ計画だけを切り出してから通常の実装レーンへ戻す。

## Fixed Model

- `Claude Code`: `opus` + `effort=high`
- `Cursor`: `Grok 4.6` + `reasoning.effort=low` / `Codex`: `gpt-5.6-sol` + `reasoning.effort=low`（refactor 計画レーン。一般 heavy として low 固定）
- 重いモデルで固定する

## Use When

- ユーザーが「リファクタしたい」「後で整理したい」「作業完了後に内部整理したい」と言っている
- 既存の挙動、受入条件、approved policy は変えずに構造だけ良くしたい
- 実装は既存の実装モデルと implementation lane に戻したい
- `gdd-implementation-gating` が全タスク完了後に `Next Action=gdd-refactor-planning` で自動 routing した（Refactor Gate モード）

## Do Not Use When

- user-visible behavior が変わる
- requirements / acceptance criteria / implementation policy を動かす
- route / owner / prompt contract / output contract / rollout / rollback の承認済み policy を変える
- **リファクタと機能追加が混在する場合** — 機能追加部分は `/gdd-dev` で `gdd-brainstorming` から始める。リファクタ部分だけこの skill で扱うか、混合の程度によっては全体を `/gdd-dev` 新規タスクとして扱う
- 上記に該当する場合は `design_detail_only` / `human_recheck_required` / `planning_rework_required` を優先して、通常の planning route に戻す。`human_recheck_required` は policy / scope / owner / security boundary の再承認が必要なときだけ使う

## Goal

- リファクタ対象と非対象を明確にする
- 守るべき挙動を `Behavior Preservation Invariants` として固定する
- リファクタで壊してはいけない外部契約を明示する
- 実装前に rollback と verification を短く固める
- planning 後は通常の実装レーンに戻す

## Before Refactor Baseline Review

superpowers `requesting-code-review` の「before refactoring baseline check」を GDD refactor gate に吸収する。refactor は挙動を変えないはずの作業なので、開始前に「何を守るか」と「現状で既に壊れていないか」を明確にする。

以下のいずれかに該当する場合、refactor task を追加する前に companion review または inline baseline review を実施する。

- large refactor: 3 ファイル以上、または shared module / public API / state machine artifact に触る
- security-sensitive / operationally-sensitive な境界に触る
- 同じ invariant / reviewer finding が過去に再発している
- refactor 対象の現状把握に不安がある

記録する baseline packet:

```markdown
### Refactor Baseline Review Packet
- base diff / target files:
- behavior preservation invariants:
- current verification evidence:
- known existing issues:
- reviewer: inline | gdd-requesting-code-review | skipped
- skip reason: <小規模・局所・既存 verification 十分など>
```

companion review を使う場合は `gdd-requesting-code-review` に `reason=before-refactor-baseline` を渡し、返った findings は `gdd-receiving-code-review` で valid / invalid / route required を判定してから refactor scope に入れる。

## Architecture Drift Detection / Re-Architecture Recommendation

refactor gate は「細かい整理」だけでなく、実装が大きくなったことで当初の architecture が合わなくなっていないかも見る。ただし、大規模リアーキを現在の PR に黙って混ぜない。検出したら `Architecture Debt Finding` として記録し、Local Refactor / Boundary Reshape / Runtime / Service Split のどれで扱うかを決める。

Drift signals:

- `mixed responsibilities`: UI / domain / infra / policy / transport が同じ file / module に混在している
- `broad change surface`: approved scope より広い unrelated files に広がっている
- `duplicated validation / policy`: sanitizer / guard / validation / policy が複数箇所に重複している
- `dependency direction inversion`: domain / core が infra / UI / transport へ依存している
- `circular dependency`: module import cycle や runtime coupling が発生している
- `hard tests / excessive mocks`: 外部依存を外せず、テストが重い・脆い・過剰 mock になっている
- `runtime / deploy mismatch`: worker / async / batch / external egress が web process や別 runtime に混ざっている
- `unexplained dependencies`: dependency manifest / lock file に理由不明の追加、lock file だけ更新、または runtime image 変更がある

Recommendation levels:

- `Local Refactor`: behavior を変えず、命名・重複・小さな責務分離で閉じる。この skill の通常 refactor task として扱える
- `Boundary Reshape`: module / layer / adapter boundary を組み替える。approved architecture option、file placement、AC の証明方法が変わるなら `human_recheck_required`
- `Runtime / Service Split`: process、worker、service、deploy、queue、credential boundary を分ける。原則として別 Stage / 別 PR / human recheck

Severity Guide:

- `low: local cleanup`: 1〜2 ファイル程度の局所的な命名・重複・小さな責務混在。approved architecture option、AC、runtime、dependency manifest、CI command は変わらない
- `medium: boundary risk`: shared module / public API / state machine artifact / dependency direction / tests に影響し、境界を少し動かす可能性がある。AC は変わらないが、file placement や証明方法が変わり得る
- `high: approved architecture or runtime boundary changes`: approved architecture option、runtime boundary、service / worker split、package manager、credential boundary、deploy / CI topology、AC の意味が変わる

broad change surface thresholds:
- low: approved scope 内、追加/変更が 1〜2 ファイル程度、または既存 pattern と同じ場所への局所追加
- medium: approved scope 内だが 3〜7 ファイル、shared module / public API / common test fixture を含む、または当初 glob より横に広がる
- high: approved scope 外、8 ファイル以上、複数 runtime / service / deploy unit に跨る、または unrelated files を含む

mixed responsibilities examples:
- low: 小さな adapter 内で mapping と軽い validation が同居しているが、domain / infra / UI へ波及しない
- medium: 1 module に domain rule と transport / persistence / UI state が混在し、test が外部依存を多く mock している
- high: domain / infra / UI / runtime orchestration が同じ変更単位に混ざり、approved architecture option や runtime boundary を維持できない

Handling Decision:

Baseline Compliance Check has priority for hard mismatch: approved baseline と実 diff が明確に不一致なら、まず Baseline Compliance Check の blocker として扱う。Architecture Drift Detection は、その不一致が単なる修正漏れか、構造的な再設計候補かを分類する補助として使う。

highest severity wins: 複数の drift signal が同時に出た場合は、最も重い severity を採用する。ただし Baseline Compliance Check has priority for hard mismatch に該当する場合は、まず blocker として止めてから drift 分類する。

medium escalates to human-recheck-required: medium でも file placement、証明方法、public API、AC evidence interpretation、approved architecture option のいずれかが変わるなら `human-recheck-required` に昇格する。

- `apply-now`: low で behavior-preserving、approved architecture / AC / runtime / dependency baseline を変えない
- `defer-follow-up`: medium だが current PR の価値提供を妨げず、後続で整理できる
- `human-recheck-required`: approved architecture option / file placement / runtime boundary / package manager / CI command / AC evidence interpretation が変わる
- `planning-rework-required`: high で現在の plan の Stage 分解、service boundary、runtime/deploy topology 自体を作り直す必要がある

記録フォーマット:

```markdown
### Architecture Debt Finding
- signal: <mixed responsibilities / dependency direction inversion / circular dependency / runtime / deploy mismatch / unexplained dependencies / ...>
- evidence: <file / diff / test pain / dependency manifest / CI / runtime evidence>
- recommendation: Local Refactor | Boundary Reshape | Runtime / Service Split
- current PR handling: apply-now | defer-follow-up | human-recheck-required | planning-rework-required
- reason: <なぜその扱いにするか>
```

`Boundary Reshape` または `Runtime / Service Split` は、ユーザーが明示的に「リアーキまでこの PR でやる」と承認していない限り、巨大 PR に混ぜない。`Planned Follow-up Stage Lane` に後続 seed を残す。

## Phase Gate Pre-check

この skill の実行前に `state.md` の `Task Size` を確認する。

- **`quick (express)`**: Express パスでは refactor gate を実施しない（`impl-gate → done` で直行するため、この skill に到達すること自体が routing ミス）。`Next Action=done` に修正し、この skill の残りの Steps は実行しない。
- **`standard` / `quick (standard)` / `quick (express → standard)`**: 以下の Steps を通常通り実行する。

## Steps

### Refactor Gate モード（`gdd-implementation-gating` からの自動 routing 時）

0. `tasklist.md` に `Refactor Gate Status=in-progress` を追記する（`Next Action` 行の直後に置く）。
0a. **Bounce Log 検査（同一 invariant 再抽出の検出）**: `state.md` の `Refactor Gate Bounce Log` セクションを読み、`worklog.md` の `## Invariant Violation` エントリを走査する。過去 violated 判定された `Invariant ID` と **同一 invariant**（後述の同一性判定）が今回の改善機会候補に再登場していないかを先に確認する。
   - **判定の正本は state.md の Refactor Gate Bounce Log**（bounce_count の機械判定に使う）。worklog.md の `## Invariant Violation` は監査用 cross-check（自然文記録）として併読するが bounce_count の計算ソースにはしない
   - **判定は invariant-id ごとに独立**して行う。複数 invariant が同時に bounce している場合でも合算しない
   - **欠損時動作（fail-closed）**: `Refactor Gate Bounce Log` セクション自体が state.md に存在しない場合は **新規作成して継続**（初回扱い、bounce_count=0 とみなす）。同一 invariant-id の行が存在しない場合も初回扱い。silent pass（セクション欠損 = skip）を許さず、常に section + 行を materialize する
   - 同一 Invariant ID が **1 回** 過去に violated だった場合: 今回の refactor で触るか外すかを明示的に判断。触るなら「過去の violation が新 scope で再発しないか」を Re-check checklist と同じ観点で事前評価
   - 同一 Invariant ID が **2 回以上** 過去に violated: **Refactor Gate Bounce Log の bounce_count に従い `bounce_count >= 2` で escape hatch 発動**（`references/bounce-log-schema.md` 参照）。`planning_rework_required` に倒し、「refactor scope では解決不能。root feature の再設計が必要」と出力する。refactor-planning の改善機会抽出はこの時点で中断
   - **Bounce Log フォーマット**（sha1 prefix 補助付き）:
     ```
     - <invariant-id> (sha1:<first-8-of-sha1(invariant-text)>) | bounced_at: <ISO 8601> | bounce_count: <N>
     ```
     - `<invariant-id>` は design.md の Behavior Preservation Invariants 見出し推奨（行番号のみは refactor で動くため非推奨）
     - `sha1:<first-8-of-sha1(invariant-text)>` は invariant テキスト（見出し末尾のコロン以降、末尾空白を trim）の sha1 hex の先頭 8 文字。rescope で invariant-id が振り直されても invariant テキストが実質同一なら過去 bounce を継承できる
     - **同一性判定**: 同一 invariant-id の完全一致 **OR** sha1 prefix 一致のいずれかで「同一 invariant」とみなす。後方互換のため sha1 prefix なしの旧形式も読める（その場合は invariant-id 完全一致のみで判定）
   - **counter reset の責務**: `planning_rework_required` 発火後の reset は **戻り先 phase（`gdd-brainstorming`）が担う**。refactor-planning 側では escape hatch 発動行を削除 / 0 化しない（戻り先で Bounce Log ライフサイクル表に従って wipe される、`references/bounce-log-schema.md` § ライフサイクル表参照）
1. `requirements.md` / `design.md` / `tasklist.md` をすべて読む。全タスクの diff 範囲と per-task REFACTOR チェックポイントの証跡を確認する。
2. タスク横断でまだ残っている改善機会を洗い出す（以下の観点で複数ファイルを横断的に確認する）:
   - **タスクをまたいだ重複**: 複数タスクで同じパターンを独立実装した結果、抽出できる共通ロジックが生まれていないか
   - **命名統一**: タスク間で命名が揺れていないか（同じ概念に複数の名前が使われていないか）
   - **過剰な抽象化の除去**: 1 タスク実装時に将来を意識しすぎた abstraction が入っていないか
   - **テストの重複**: 同一ロジックをテストする重複テストが複数タスクで生まれていないか
   - **Architecture Drift Detection**: mixed responsibilities、dependency direction inversion、circular dependency、runtime / deploy mismatch、unexplained dependencies がないか。該当する場合は `Architecture Debt Finding` を記録し、`Re-Architecture Recommendation` として Local Refactor / Boundary Reshape / Runtime / Service Split のどれかに分類する
3. 改善機会が **ない** 場合:
   - `tasklist.md` の `Refactor Gate Status=in-progress` を `Refactor Gate Status=pass-empty` に更新する
   - `Next Action=gdd-completion-check` にする
   - **終了**（以下の step には進まない）
4. 改善機会が **ある** 場合は `design.md` に次を追加または更新する:
   - `Refactor Objective`
   - `Behavior Preservation Invariants`
   - `Refactor Scope / Non-Scope`
   - `Rollback / Safe Revert`
   - `Verification Focus`
5. `tasklist.md` に refactor task を追加し、`Current Task` / `Pending Tasks` / `Completed Tasks` を更新する。`Refactor Gate Status=in-progress` はこのままにしておく（`gdd-implementation-gating` が全タスク完了時に `pass-applied` に更新する）。
6. `Next Action=gdd-test-driven-development` にする。

### 明示呼び出しモード（ユーザーから直接依頼された場合）

1. `requirements.md` / `design.md` / `tasklist.md` を読み、approved behavior と current implementation policy を確認する。
2. 今回の依頼が behavior-preserving refactor に収まるかを判定する。
3. 収まらない場合は、理由を明記して `design_detail_only` / `human_recheck_required` / `planning_rework_required` のどれかへ戻す。
4. 収まる場合は `design.md` に次を追加または更新する。
   - `Refactor Objective`
   - `Behavior Preservation Invariants`
   - `Refactor Scope / Non-Scope`
   - `Rollback / Safe Revert`
   - `Verification Focus`
5. `tasklist.md` に refactor task を追加し、`Current Task` / `Pending Tasks` / `Completed Tasks` を更新する。
6. 実装前の戻り先は `gdd-test-driven-development` または `gdd-subagent-driven-implementation` ではなく、まず `Next Action=gdd-test-driven-development` を既定にする。
7. 実装は既存の実装モデルで行う。implementation lane の契約を変えない。

## Required Writing Rules

- `Behavior Preservation Invariants` は外部から見える挙動を自然文で書く
- 内部語だけで済ませず、どの契約を維持するかを人間が読めるように書く
- `Refactor Scope / Non-Scope` で、今回触らない部分を明示する
- `Verification Focus` には最低でも回帰確認ポイントを書く

## Handoff

- behavior-preserving refactor に収まる場合:
  - `Next Action=gdd-test-driven-development`
  - 実装は通常の implementation lane に戻す
- approved policy を動かす場合:
  - `design_detail_only` / `human_recheck_required` / `planning_rework_required` のいずれかを明示して戻す
- refactor が失敗し回帰が見つかった場合:
  - `Next Action=gdd-systematic-debugging` に戻して原因調査を優先する

## Guardrails

- 新機能追加を混ぜない
- user-visible behavior change を silent に入れない
- approved policy change を refactor と偽装しない
- refactor planning のまま実装に飛ばず、必ず通常の implementation lane に戻す

## Behavior Preservation Invariants Re-check（refactor 中 escalation / fix 後）

Refactor task 実装中に以下のいずれかが発生した場合、**再開時に Behavior Preservation Invariants の再検証 checklist を通す**。scope 変更や bug fix で元 invariant が維持できなくなるケースを silent に許さない。

- `design_detail_only` / `human_recheck_required` / `planning_rework_required` が発火した場合（scope 変更）
- `implementation_fix_only` で bug fix を入れた場合（refactor task 固有 — 通常 task では不要）。bug fix が silent に BPI を壊す経路を塞ぐため、refactor task に限り fix_only でも checklist を通す

### 再検証 checklist

Refactor task の build 再開直前（design-gate 再通過後 or human check 再承認後）に `design.md` の `Behavior Preservation Invariants` 各項目について以下を評価:

1. **Invariant は新 scope でも維持されるか** — yes/no で判定。各 invariant 行に `[retained]` / `[violated]` タグを付与
2. **1 つでも `[violated]` がある場合**:
   - refactor task を **abort** し、`tasklist.md` の `Completed Tasks` / `Pending Tasks` から当該 refactor task を削除（`Completed Tasks` にあるときは先に `Pending Tasks` へ移してから次の書き込みで消す。steering write guard）
   - abort した差分は revert commit を積む（`revert: refactor task aborted due to invariant violation`）
   - 当該 invariant 違反を通常 task として再計画する（`Refactor Gate Status=pending` に戻し、次の `gdd-completion-check` で再度 Refactor Gate を通す）
   - `worklog.md` に以下固定フォーマットで記録:
     ```
     ## Invariant Violation (YYYY-MM-DDTHH:MM:SSZ)
     - Invariant ID: <invariant-id、design.md の Behavior Preservation Invariants 行番号または見出し>
     - Invariant Text: <1 行要約>
     - Judged By: <reviewer 名 or main session>
     - Escalation Route: <design_detail_only | human_recheck_required | planning_rework_required>
     - Aborted Refactor Task: <T-N>
     - Revert Commit: <commit sha>
     - Next Action: Refactor Gate Status=pending → gdd-completion-check が次回 gdd-refactor-planning 再起動
     ```
   - **Refactor Gate Bounce Log 更新**: `state.md` の `## Refactor Gate Bounce Log` セクションで当該 `Invariant ID` の行を更新（`bounce_count` を +1、`bounced_at` を現在時刻に更新）。セクションが無ければ新規作成。新規記録時は sha1 prefix 付き形式を推奨:
     ```
     ## Refactor Gate Bounce Log
     - <invariant-id> (sha1:<first-8-of-sha1(invariant-text)>) | bounced_at: <ISO 8601> | bounce_count: <N>
     ```
     既存行を +1 する場合は既存の形式（sha1 有無）を踏襲する（後方互換）
   - **Bounce Log 閾値判定**: 更新後の `bounce_count >= 2` になった場合は次の `gdd-refactor-planning` 再起動時（Step 0a）で escape hatch が発動し、`planning_rework_required` に倒れる。今回は通常通り通常 task として再計画で進めて良い
3. **全て `[retained]` の場合**: refactor task を通常通り再開。worklog.md に `Invariants Re-checked: all retained / route=<escalation route>` を記録

### Why

Refactor は「挙動を変えない」が前提の自走範囲。escalation で scope が広がった時、元 invariant が silent に壊れると「user-visible behavior change を silent に入れない」guardrail が有名無実化する。escalation 後の再検証を契約化することで、invariant 違反を必ず顕在化させる。
