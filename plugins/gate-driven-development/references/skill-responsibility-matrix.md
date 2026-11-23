# Skill Responsibility Matrix

似た名前・似た trigger を持つ skill 間で「**どっちを使うべきか**」を一覧で示す。曖昧な状況に遭遇したらここを最初に参照する。

新規 skill 追加で重複・近接が発生した場合は、このファイルにも判断行を追加する（`gdd-writing-skills` § 新規 skill 追加チェックリストで参照される）。

## Decision Table（状況 → 使う skill）

| 状況 / 言いたいこと | 使う skill | 使わない skill | 注記 |
|---|---|---|---|
| `/gdd-dev` で formal workflow を始めたい / 再開したい | `gdd-brainstorming` | `gdd-pre-workflow-brainstorming` | artifact あり、entry intent 解決 |
| 「壁打ちしたい」「相談だけ」「まだ実装しない」「要件から整理したい」 | `gdd-pre-workflow-brainstorming` | `gdd-brainstorming` | artifact なし、state machine 外 |
| Pre-workflow 相談中に「正式に進めたい」と決まった | `gdd-brainstorming`（upgrade） | — | 「Transition Rules」参照 |
| Formal workflow 中に「やっぱり相談に戻したい」 | （明示の人間判断が必要、auto-downgrade 禁止） | — | 「Transition Rules」参照 |
| 実装が完了した、formal な gate を通したい | `gdd-implementation-gating` | `gdd-pr-review` | reviewer 起動 + Express path safety net |
| PR を作る直前、最終 diff を確認したい | `gdd-pr-review` | `gdd-implementation-gating` | pr-review skill 全実行 + Spec Drift / Migration / Dialectic |
| PR 作成後にレビュー指摘を収束させたい / PR後の修正指示・CI失敗に対応したい | `gdd-pr-review-followup` | `gdd-pr-review` / `gdd-receiving-code-review` 単独 / `superpowers:receiving-code-review` | PR 作成後。review findings -> fix -> push -> re-request review loop をレビュー指摘がなくなるまで回す |
| マージ前にもう一度差分を見ておきたい | `gdd-pr-review` | `gdd-implementation-gating` | 同上 |
| 「コードレビューして」（曖昧） | **状況による**：実装直後なら impl-gating、PR 前なら pr-review | — | 下記「Pair 1 詳細」参照 |
| 追加で security / final review を別レーンで入れたい | `gdd-requesting-code-review` | `gdd-implementation-gating` / `gdd-pr-review` | companion review lane（formal gate と並列） |
| companion review からのフィードバックを取り込む | `gdd-receiving-code-review` | — | — |
| テストが落ちて triage したい | `gdd-test-failure-debug-pack` | `gdd-systematic-debugging` 直行 | pack → root-cause-investigation → systematic-debugging の順 |
| Root cause を方法論ベースで突き止めたい（GDD 内・外問わず） | `root-cause-investigation` | `gdd-systematic-debugging` | systematic-debugging は routing 専任。Pair 5 参照 |
| Routing を GDD のどの phase に戻すか決めたい | `gdd-systematic-debugging` | `root-cause-investigation` | root cause 確定後に routing。Pair 5 参照 |
| 「bug を直したい」「壊れている」（順序が曖昧） | **状況による**：root cause 未特定なら `root-cause-investigation` → 特定後 `gdd-systematic-debugging` で routing | — | Pair 5 § 呼び出しの流れ を参照 |
| 完了済み機能に追加要件 / 仕様変更を入れたい | `gdd-requirements-amendment` | `gdd-brainstorming` | active workflow からも呼ばれる |
| マージ済み機能のリファクタ / 整理 | `gdd-refactor-planning` | `gdd-brainstorming` | 承認済み挙動を変えない |
| 「今どこ？」「進捗は？」 | `gdd-status` | — | read-only |
| 全 task 完了後の最終 gate（reviewer 監査 + AC Drift + 各種品質チェック + Post-Completion PR Flow） | `gdd-completion-check` | `gdd-ac-verification` 単独 | completion-check が ac-verification を呼ぶ orchestrator |
| 個別 AC の verify / Verification schema の確認 / fresh evidence の判定 | `gdd-ac-verification` | `gdd-completion-check` 全体 | Specialized Helper、state を変えない |

## Pair 1 詳細: `gdd-implementation-gating` vs `gdd-pr-review`

### 役割の違い

| 観点 | gdd-implementation-gating | gdd-pr-review |
|---|---|---|
| **位置** | 実装直後、completion-check の前 | PR 作成の直前、completion-check の後 |
| **主な対象** | コード差分の品質 / scope / security | PR 全体（コード + docs + Terraform） |
| **reviewer 起動** | 必須（implementation reviewer 常時、他は selection） | pr-review skill 内で個別 |
| **Spec Drift** | scope guard（diff vs requirements、forward） | Spec Drift Check（実装 → artifact、reverse） |
| **Migration content-diff** | × | ○ |
| **Dialectic Review** | × | ○ |
| **Express path safety net** | ○（最後の gate） | × |
| **state machine への接続** | あり（`Next Action`） | なし（手動 / completion-check から auto） |

### Trigger phrase の使い分け

| User が言う | 使う skill |
|---|---|
| 「実装レビューして」「コードレビューして」（実装直後の文脈） | impl-gating |
| 「formal gate 通して」「reviewer 走らせて」 | impl-gating |
| 「PR レビューして」「PR 前に見て」「差分チェックして」 | pr-review |
| 「マージ前に確認して」「final diff review」 | pr-review |
| 「review して」だけ（曖昧） | 状況確認。tasklist で `Next Action=gdd-implementation-gating` なら impl-gating、それ以外で PR 作成直前なら pr-review |

### 直列実行の関係

通常フロー: 実装 → **impl-gating** → completion-check → **pr-review** → PR 作成 → **gdd-pr-review-followup** → merge

impl-gating で approve されない限り pr-review に進まない。両者を同じ目的で同時に呼ばない。

### `gdd-pr-review` vs `gdd-pr-review-followup` vs `gdd-receiving-code-review`

| 観点 | gdd-pr-review | gdd-pr-review-followup | gdd-receiving-code-review |
|---|---|---|---|
| 位置 | PR 作成前 / final diff review | PR 作成後 | review finding 受領時の検証 discipline |
| 主な仕事 | PR 作成前に High を潰す | review pending を待機状態として記録し、指摘収集 → 修正 → push → 再度レビュー指示を loop | finding を valid / invalid / route に分類 |
| 終了条件 | PR 作成可 | latest head の no actionable review findings。review pending は `waiting_for_review` | 個別 finding の routing 決定 |
| push | しない | 必要なら `git push` | しない |
| 再レビュー依頼 | しない | する | しない |

## Pair 2 詳細: `gdd-brainstorming` vs `gdd-pre-workflow-brainstorming`

### 役割の違い

| 観点 | gdd-brainstorming | gdd-pre-workflow-brainstorming |
|---|---|---|
| **artifact** | `.steering/<slug>/{requirements.md, design.md, state.md}` を作成 | なし |
| **state machine** | 入る | 入らない |
| **worktree** | 作る or 再利用 | 作らない |
| **出力** | requirements + design skeleton + Summary Brief | Summary Brief（会話の要約） |
| **human check** | 必須 gate（formal workflow に乗る） | 任意（会話の節目で示すだけ） |
| **trigger** | `/gdd-dev` | 「相談だけ」「壁打ち」「要件から整理」 |

### Transition Rules

#### upgrade: pre-workflow → brainstorming（相談 → 正式）

- **契機**: pre-workflow 中にユーザーが「正式に進めたい」「これで進めて」と明示
- **手順**:
  1. pre-workflow の Summary Brief を保存（後の brainstorming の入力にする）
  2. `gdd-brainstorming` を起動（entry intent = new）
  3. brainstorming Step で Summary Brief を `requirements.md` の初期入力に使う
  4. worktree 準備 + artifact 生成 → 通常フローへ

#### downgrade: brainstorming → pre-workflow（正式 → 相談）

- **契機**: brainstorming or 後続 phase 中にユーザーが「やっぱり相談に戻したい」「実装やめて整理しなおしたい」
- **auto-downgrade 禁止**: 既存の artifact があるため、無条件で戻すと state が dirty になる
- **手順**:
  1. **必ず人間に確認**: artifact の扱いを 3 択で問う
     - `discard`: artifact を削除して pre-workflow に戻る
     - `archive`: `.steering/<slug>-archived-YYYYMMDD/` にリネームし、その `state.md` の `Resume From` と `Next Action` をどちらも `cancelled` にして pre-workflow に戻る
     - `continue`: pre-workflow ではなく brainstorming 内で議論を続ける
  2. ユーザー選択に従って artifact を処理
  3. pre-workflow に切り替える場合は state.md を残さない（または archive）
- **gdd-using-git-worktrees の Cancelled Cleanup と整合させる**（既存規約に従う）

### 同時並行の禁止

同じ slug / 同じ worktree で pre-workflow と brainstorming を並行起動しない。fail-closed で停止し、ユーザーにどちらか選んでもらう。

## Pair 3 詳細: `Pre-flight Self-Check` vs `gdd-implementation-gating`

### 役割の違い

| 観点 | Pre-flight Self-Check (Step 14b) | gdd-implementation-gating |
|---|---|---|
| **実行主体** | implementer（subagent or 本体） | reviewer agent |
| **検出方法** | 機械的（grep / pattern match / 名前照合） | 主観（context 理解 + checklist） |
| **検出対象** | ハードコード値 / 環境変数名 / known pitfalls | scope / dead code / security / 設計整合 |
| **修正タイミング** | その場（同セッション） | 差し戻し → 再実装 |
| **目的** | impl-gate の往復削減 | formal gate（合否判定） |
| **escape hatch** | × | ○（changes_requested loop） |

### 判断軸（新規 check をどっちに入れるか）

新しい check を追加するとき、以下で判定:

| 条件 | Pre-flight に入れる | impl-gating に入れる |
|---|---|---|
| grep / regex で機械的に検出できるか | ○ | × |
| AC drift / 設計整合の判断を伴うか | × | ○ |
| security / scope 境界に関わるか | × | ○ |
| context 理解が必要か | × | ○ |
| implementer が自己修正できる範囲か | ○ | × |
| reviewer の独立判断が必要か | × | ○ |

両側に該当する場合は **impl-gating 優先**（独立評価のほうが信頼性が高い）。Pre-flight に同じ check を残すなら「最低限の事前 catch」と位置づけ、impl-gating の同 check は省略しない。

## Pair 4 詳細: `gdd-completion-check` vs `gdd-ac-verification`

### 役割の違い

| 観点 | gdd-completion-check | gdd-ac-verification |
|---|---|---|
| **種別** | Phase Gate skill（state machine auto-routed） | Specialized Helper skill（呼び出される側） |
| **state 更新** | あり（`Next Action` / `Route In Progress` / `Gate Status` / `Blocked Since`） | **なし**（judgment と schema validation を return するのみ） |
| **AC verification** | ac-verification を呼ぶ orchestrator | Verification schema + judgment + fresh evidence の正本 |
| **AC Drift Check（実装 → artifact）** | ○ Step 5a で実行 | × 立ち入らない |
| **Stub Detection** | ○ Step 9b | × |
| **External Dependency Check** | ○ Step 9c | × |
| **Skill / Document Quality Check** | ○ Step 9d | × |
| **Reviewer Selection Audit** | ○ Step 2 | × |
| **Post-Completion PR Flow** | ○ | × |
| **UAT checklist / Learning patterns** | ○ | × |
| **呼び出し主体** | state machine（auto-route） | completion-check / impl-gating Express path / 手動 |
| **trigger phrase** | （internal、auto-route） | 「AC を verify して」「AC-N を判定」「verification を埋めて」「fresh evidence で再 verify」 |

### 責務の境界

**ac-verification が owns（schema + judgment）**:
- Verification 行の受理文法（field 構成 / status 許容値 / AC 行・external security evidence・refactor-checkpoint の使い分け。BNF 正本は `references/self-contained-contract.md`）
- Schema Validation の fail-closed table
- Fresh Verification Rule（毎セッション再実行）
- Speculative Language の拒絶（"should work" / "probably" / "動作確認済み" 等）
- Iron Law: NO COMPLETION WITHOUT FRESH EVIDENCE

**completion-check が owns（orchestration + 他の品質チェック）**:
- どの evidence kind が今回のタスクに必要かの判定
- AC Drift Check（実装 → artifact の逆方向整合）
- Stub Detection（実装がスタブ状態か）
- External Dependency Completeness Check（env / IAM / StackSets）
- Skill / Document Quality Check（記述一貫性 / 具体性 / Why / 重複）
- Reviewer Selection Audit
- Post-Completion PR Flow（merge / PR / keep / discard 4 択）
- state machine への接続全般

### 呼び出しの流れ

```
gdd-completion-check（auto-routed）
  Part A: 事前確認（reviewer audit / impl-gate evidence check 等）
  Part B: Verification 充足判定
    └── gdd-ac-verification を呼ぶ
        ├── Verification schema validation
        ├── 各行の 4 field 判定
        ├── Speculative Language 拒絶
        ├── Fresh Verification Rule の適用
        └── return: judgment + schema violations
  Part B 続き: AC Drift Check / Stub Detection / External Dependency / Skill Quality
  Part C: Post-Completion PR Flow
  state 更新 + `<gdd-stop>` emission
```

### 重複の禁止

Verification schema や fresh evidence rule を completion-check 側に重複定義しない（drift の元）。schema 関連の規約変更は `gdd-ac-verification` のみで行い、completion-check は呼び出し元として参照する。

## Pair 5 詳細: `root-cause-investigation` vs `gdd-systematic-debugging`

### 役割の違い

| 観点 | root-cause-investigation | gdd-systematic-debugging |
|---|---|---|
| **種別** | Methodology skill（GDD 非依存・workflow 非依存） | Phase Gate skill（GDD state machine auto-routed） |
| **入力** | 症状の記述（test output / error / silent failure） | 確定済みの root cause + 症状種別 |
| **出力** | 確定した root cause（言葉で書ける形） | GDD の戻り先 phase + 復帰シーケンス |
| **方法論** | 4 Phases（Root Cause → Pattern → Hypothesis → Implementation handoff） | Routing Decision Tree（implementation_fix_only → design_detail_only → human_recheck_required → planning_rework_required） |
| **state 更新** | なし | あり（`Next Action` / `Resume From` / `Route In Progress`） |
| **GDD 外利用** | ○ 単独起動可 | × GDD workflow 専用 |
| **trigger** | 「bug を直したい」「動かない」「root cause を突き止めたい」 | `Next Action=gdd-systematic-debugging` の auto-route |

### 呼び出しの流れ

```
[症状検知（test fail / silent failure / reviewer changes_requested 等）]
  ↓
gdd-test-failure-debug-pack          (Test RED の場合のみ、Expected/Actual/Evidence 整理)
  ↓ pack だけで root cause 不明
root-cause-investigation             (4 Phases で root cause 確定)
  ↓ root cause を言葉で書ける状態
gdd-systematic-debugging             (確定 root cause を GDD 戻り先に分類)
  ↓ Routing Decision Tree 通過
[戻り先 phase へ handoff]
```

### 責務の境界

- **root cause の特定**: `root-cause-investigation` の専有。`gdd-systematic-debugging` は root cause の特定をしない（routing 専任）
- **GDD 戻り先の決定**: `gdd-systematic-debugging` の専有。`root-cause-investigation` は GDD state を変更しない
- **Silent failure のインフラ層調査**: `root-cause-investigation` の Phase 1（境界証跡収集）で実施。インフラ層で原因確定すれば `gdd-systematic-debugging` の Routing Decision Tree をスキップして直接 `implementation_fix_only` / `design_detail_only` に進んでよい（`gdd-systematic-debugging` Steps § 症状種別分類を参照）

### 直接呼び出しの順序

1. ユーザーが「bug を直したい」と言ったとき: `root-cause-investigation` を先に呼ぶ
2. root cause が確定したら `gdd-systematic-debugging` に handoff
3. `gdd-systematic-debugging` から差し戻し先 phase（subagent-driven-implementation など）に handoff

`gdd-systematic-debugging` を最初に呼んで「root cause 不明のまま routing 試行」は禁止。`gdd-systematic-debugging` 側で root cause が言葉で書けない状態を検知したら、`root-cause-investigation` を先に呼ぶよう redirect する。

## カタログの拡張ルール

新しい曖昧ペアを発見したら以下を追加:

1. **Decision Table に行を追加**: 「状況 → 使う skill」の対応を 1 行で
2. **必要なら詳細セクション**: 役割の違い表 + transition / 直列関係 / 判断軸
3. **両 skill の description / SKILL.md にも参照リンク**: 「曖昧な場合は `references/skill-responsibility-matrix.md` を参照」

新規 skill 追加時は `gdd-writing-skills` § 新規 skill 追加チェックリストで「責務重複チェック」を経て、ここに行を追加するかを判定する。
