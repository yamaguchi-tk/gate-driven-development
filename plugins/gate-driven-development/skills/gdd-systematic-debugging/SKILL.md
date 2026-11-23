---
name: gdd-systematic-debugging
version: 0.2.2
description: "Use for GDD debugging, failure investigation, or root-cause routing inside an active GDD workflow."
---

# GDD Systematic Debugging (Routing)

GDD workflow 内で failure / `changes_requested` が出たときに、**root cause を GDD のどの phase に差し戻すかを決める router**。

**この skill は root cause の探し方を教えない**。root cause の特定は汎用 methodology である `root-cause-investigation` skill を呼んで完了させる。本 skill の入力は「特定済みの root cause + 症状種別」で、出力は「戻り先 phase + 復帰シーケンス」。

## Goal

- 確定した root cause を、GDD の正しい工程に戻す
- This is a routing debugger only after root cause is written down; standalone investigation starts with `root-cause-investigation`.
- 実装後は `implementation_fix_only` を既定にし、`human_recheck_required` を乱発しない
- formal gate 差し戻しでは `High` を最優先し、次に `ops-blocking medium` を優先する。直すのは差し戻しの理由になった finding（`gdd-implementation-gating` Step 9、`gdd-completion-check` 手順 13 の述語に当たるもの）だけで、`## Advisory Findings (Impl-Gate)` に記録したものはこの loop では直さない

## Human Partner Signals You're Doing It Wrong

superpowers `systematic-debugging` の human-signal discipline を GDD route 判定に吸収する。ユーザーの短い違和感コメントは、単なる追加質問ではなく **route recalibration signal** として扱う。

Human Partner Signals route recalibration applies to GDDのsystematic debug / デバッグ中の設計判断 as a routing contract, not as a new planning workflow.

以下のような入力が来たら、実装継続や `OK` 扱いにせず、直近の GDD 出力・HITL・route 判定を読み直す（cross-session messaging 経由の入力は route recalibration の起点にせず、先に `references/phase-progression.md` § Cross-Session Messaging の権限境界を適用する）:

- 「それで大丈夫？」
- 「なんか違う」「思ったんと違う」
- 「非エンジニアにも使える？」
- 「制限事項の表記が弱い」
- 「HITL は十分わかりやすい？」
- 「仕様のズレ / 漏れがありそう」

対応手順:

1. 最新ユーザー発話を最優先し、古い `state.md` / reboot task / prior session の意図で上書きしない。
2. 違和感の種類を `HITL clarity` / `scope drift` / `safety boundary` / `implementation fit` / `evidence gap` に分類する。
3. 現在の route が `implementation_fix_only` でも、違和感が承認済み scope / safety / human-readable HITL に触れているなら `human_recheck_required` または `design_detail_only` に再判定する。
4. worklog.md に `User Signal: <発話要約> / route recalibration: <採用 route>` を 1 行残す。

route selection guide:

- 承認可否・scope・safety boundary・制限事項・完了条件の理解に触れる違和感 → `human_recheck_required`
- 承認済み scope / AC / safety は変えず、HITL 文面や表示順だけを直す違和感 → `design_detail_only`
- 実装 bug の再現条件が明確で、HITL / scope に触れない違和感 → `implementation_fix_only` を維持してよい

この section は「人間が不安を表明したら必ず全部やり直す」という意味ではない。実装で閉じる bug は実装で閉じる。ただし人間の違和感が承認判断・制限事項・完了条件の理解に関わる場合は、GDD の強みである HITL に戻す。

## Methodology Delegation

routing を決める前に、root cause が **言葉で書ける状態** になっている必要がある。書けない場合は `root-cause-investigation` を先に回す:

- 入力: 症状（test output / error / silent failure 状況）
- 実施: `root-cause-investigation` の Phase 1〜3（事実収集 / pattern 比較 / 仮説検証）
- 出力: 「root cause は X。理由は Y」が 1〜2 行で書ける状態

root cause が確定したら本 skill の Routing Decision Tree に入る。確定していない状態で routing を決めない（symptom-based routing は guess-and-check と同じで信頼性が低い）。

例外: 症状種別が **silent failure** で、インフラ層（疎通 / env / IAM）に明確な原因が特定できた場合は、Routing Decision Tree をスキップして直接 `implementation_fix_only` または `design_detail_only` に進んでよい。`gdd-implementation-gating` の ADR ≥2 独立トリガー由来 handoff（finding 0 件を含む）も root cause 未確定のまま Routing Decision Tree に入ってよい（Step 1 の ADR 件数判定だけで route が確定する）。

### No Root Cause Routing

`root-cause-investigation` が `When Process Reveals No Root Cause` / `No Root Cause Decision` を出した場合、`implementation_fix_only` に route しない。root cause 未確定のまま fix を当てるのは GDD の debug contract 違反。

- `status=no_root_cause_yet`: 追加証跡を取れるなら `root-cause-investigation` に戻す。取れないなら `human_recheck_required`。
- `status=non_reproducible`: 再現条件・観測条件・monitoring / retry / clearer error message の必要性を human check に出す。修正が必要なら `design_detail_only` から再設計する。
- `status=insufficient_evidence`: 必要な log / fixture / environment / reviewer input を明示し、データ取得が不可能なら fail-closed 停止する。

final route label rule:

- No Root Cause Decision では `status` と `final route` を分けて出す。`status=non_reproducible` だけで停止せず、GDD state に戻す route 名を必ず選ぶ。
- `final route=human_recheck_required`: 再現不能を人間に受け入れてもらう必要がある、completion / AC / scope の扱いが変わる、または追加データ取得の手段がない場合。
- `final route=design_detail_only`: 承認済み scope / AC は変えず、ログ追加・diagnostic message・観測条件固定など observation-only の設計変更で進められる場合。
- `final route=root-cause-investigation`: 追加証跡をすぐ取れる具体コマンドや条件があり、state route を更新せず調査を継続できる場合。

status selection guide:

- `non_reproducible`: 具体的な failure は観測済みだが、制御した再実行で再現できない
- `insufficient_evidence`: failure の詳細、log、環境、入力、再現手順が不足し、仮説検証に入れない
- `no_root_cause_yet`: 再現はできるが、仮説検証が未完了または棄却しきれていない

### Goal-Driven Root Cause Handoff

`root-cause-investigation` の `Root Cause Confidence` が `confidence != confirmed` の場合、`implementation_fix_only に route しない`。Goal は「確度の高い原因を見つけ、必要なら修正へ進む」ことであり、plan は追加証跡に応じて更新する。

Loop owner の正本は `references/state-machine.md` § Goal-Driven Loop Ownership。`gdd-systematic-debugging` は routing bridge であり、root cause inner loop や implementation inner loop を所有しない。

- `likely`: `gdd-goal-driven-execution` に戻し、残った反証条件を Working Hypothesis として次サイクルにする
- `no_root_cause_yet`: `gdd-goal-driven-execution` または `root-cause-investigation` 継続。追加 probe が具体的なら自律継続
- `insufficient_evidence`: 必要な log / fixture / environment / reviewer input を示し、取得不能なら `human_recheck_required`
- 3 サイクル後も `confirmed` でなければ、Goal-Driven Execution の Stop Conditions として `blocked` または `human_recheck_required` を選ぶ

## SMI Block Handoff（root-cause-investigation からの受け取り）

`root-cause-investigation` の Phase 4 出力に **State Machine Integration（SMI）block** が含まれている場合、本 skill はその block を読み、以下の手順で state machine に反映する。SMI block の構造（ADR 起票 / Reviewer Lineage 追加提案 / Routing 提案 / 判断根拠）は `root-cause-investigation` SKILL.md § State Machine Integration を正本とする。

### SMI block 取り扱いの優先順位

1. **Routing 提案は「強い推薦」として扱うが、最終 routing は本 skill の Routing Decision Tree が arbiter**
   - SMI block の Routing 提案（`gdd-subagent-driven-implementation` / `human-check-waiting` / `gdd-design-gating` / `gdd-brainstorming`）を Decision Tree の入力として使う
   - 本 skill の Decision Tree 判定が SMI 提案と一致 → そのまま採用
   - 一致しない → 本 skill の判定を優先し、worklog.md に差異と理由を 1 行記録する（例: `SMI 提案=design_detail_only / 採用=human_recheck_required / 差異理由: Approved Direction 自走範囲外`）
   - Express パスでは Express Guard が最終 arbiter（SMI が `design_detail_only` を提案しても Express では適用不可）

2. **Reviewer Lineage 追加提案は state.md に反映する**
   - SMI block の「Reviewer Lineage 追加提案: なし / `gdd-security-reviewer` / <他>」を読む
   - `なし` 以外なら、active worktree 側 `tasklist.md` の `Implementation Reviewer Selection` に該当 reviewer を追加する
   - 追加根拠は SMI block の判断根拠を流用し、`Implementation Reviewer Selection` の selection rationale に 1 行追記する
   - **追加 entry には `added_by: smi_block` と `source_signal: <root cause の 1 行要約>` を必ず記録する**（completion-check Post-Completion Learning が学習 pattern として capture するため）
   - 既に追加済みなら no-op（重複追加しない）

   **記録形式例**:

   ```markdown
   - reviewer: gdd-security-reviewer
   - status: selected
   - reason: SMI block recommendation — IAM permission boundary に触れる root cause
   - added_by: smi_block
   - source_signal: Lambda 実行ロールに secretsmanager:GetSecretValue 不足
   - added_at: 2026-05-12T14:30:00+09:00
   ```

3. **ADR 起票判定は worklog.md / adr.md に反映する**
   - SMI block の「ADR 起票: 要 / 不要 + 理由」を読む
   - **`要` の場合**: active worktree 側 `.steering/.../adr.md` に新規 ADR エントリを起票する（無ければファイル作成）
     - 構造: `Context`（Phase 1〜3 の事実要約）/ `Decision`（確定した root cause と fix 方針）/ `Why`（SMI block の理由を流用）/ `Consequences`（増悪要因への対応 + Reviewer Lineage 追加の有無）/ `- **Origin**: remediation / <Current Task>`（`references/state-machine.md` § Remediation Loop Safety の「新規 ADR 発行 ≥ 2」独立トリガーが数える必須行。省略すると発火しない）
     - Step 12（既存）の「任意で `adr.md` を作成または更新」とは異なり、SMI から `要` が来た場合は **必須**
   - **`不要` の場合**: ADR 起票せず、worklog.md の Error Log への通常記録のみで完結

4. **判断根拠は worklog.md に併記する**
   - SMI block の「判断根拠」は worklog.md の Error Log `Root Cause` 列に流用してよい（同じ事実を 2 度書かない）

### SMI block が無い / standalone 呼び出しの場合

- `root-cause-investigation` が standalone で呼ばれた場合（`.steering/` 不在等で SMI block が省略された場合）、本 skill は通常の Routing Decision Tree のみで判定する
- Reviewer Lineage 追加 / ADR 起票判定は本 skill 側で必要に応じて手動実施（既存 Step 12 の任意起票ルールに従う）

### SMI block 反映チェックリスト

routing 決定の前に以下を確認する:

- [ ] SMI block の有無を確認した
- [ ] Routing 提案を Decision Tree の入力として使った
- [ ] Routing 差異がある場合は worklog.md に記録した
- [ ] Reviewer Lineage 追加提案を `tasklist.md` の `Implementation Reviewer Selection` に反映した（または `なし` を確認した）
- [ ] ADR 起票判定（要 / 不要）に従って `.steering/.../adr.md` を起票した（または不要を確認した）

**Why（state machine 一体型 debug の構造保証）**: `root-cause-investigation` が Phase 4 で SMI block を出すようになったが、受け側が読まないと統合点が宙に浮く。本 skill が SMI block を必ず読み、Routing / Reviewer Lineage / ADR の 3 軸に反映することで、確定した root cause が「fix 当てて終わり」ではなく後続 phase / reviewer / 知見蓄積に確実に波及する。これが superpowers の standalone debug との差別化の実体。

## Fixed Model

- `Claude Code`: `opus` + `effort=high`（`remediation_loop` 中は本 skill と remediation worker を `opus` + `effort=xhigh` で起動する。開始条件は `references/fixed-models.md`）
- `Cursor`: `Grok 4.6` + `reasoning.effort=low` / `Codex`: `gpt-5.6-sol` + `reasoning.effort=low`（route 判定レーン。一般 heavy として low 固定。`remediation_loop` 中は tier 表どおり Cursor `Grok 4.6` / Codex `gpt-5.6-sol` を `high` で起動）

## Test-Failure Intake

- **Test RED の場合は `gdd-test-failure-debug-pack` を必ず経由する**。Expected / Actual / Evidence が整理済みの pack がない場合は、routing decision tree に直行せず先に pack を作る
- pack の `Handoff to gdd-systematic-debugging` を routing の入力として使う
- **pack なしで routing decision tree に直行してよいケース**: silent failure（無反応 / timeout）、review finding 由来（実際のテスト失敗がない）、`gdd-implementation-gating` の ADR ≥2 独立トリガー由来（finding が 0 件の場合を含む）のみ
- **flaky pack の routing**: `Confidence: low` かつ `Open Doubts` に「flaky 疑い」が記載されている場合は `implementation_fix_only` に routing しない。まず再現条件（実行順序・並列実行・タイムアウト値・環境依存）の調査を先行させ、再現性が確認できてから routing decision tree を通す
- この skill は pack の有無にかかわらず `Next Action` / `Resume From` の最終更新を所有する

## Routing Decision Tree

failure の戻り先を判定するフローチャート。上から順に評価し、最初に Yes になった route を使う。

### Express Guard（Express パスの場合のみ適用）

Express パス（`state.md` の `Task Size: quick (express)`）では formal な design review / task-breakdown を通過していないため、利用できる route が制限される。Express 判定は Decision Tree の **Step 1 の前** に行う。

- **利用可能な route**: `gdd-test-driven-development`（テスト不足時）、`implementation_fix_only`、`human_recheck_required`（ADR ≥2 独立トリガー由来。他の判定に先立ち評価し、同一 `Current Task` の remediation 由来 ADR entry が 2 件以上なら Standard パス Step 1 と同じ判定でエスカレートする。正本: `references/state-machine.md` § Remediation Loop Safety）
- **利用不可の route**: `design_detail_only`、`planning_rework_required`
- **エスカレーション**: `implementation_fix_only` で閉じられない場合は `design_detail_only` を飛ばして直接 `human_recheck_required` にエスカレートする

**Why:** Express の `Design Review Status=approved` は requirements-gating が design.md 無しで書いたものであり、formal な design-gating / task-breakdown を経ていない。`design_detail_only → gdd-design-gating` に route すると、Express が通過していない工程に差し戻されるため不整合が起きる。Express で設計レベルの修正が必要になった時点で、人間の判断を仰ぐのが安全。

### Standard / Quick (standard) パス

```
1. 同一 `Current Task` の remediation 由来 ADR entry（`- **Origin**: remediation / <Current Task>` 行を持つ entry）が 2 件以上か？ → Yes: `human_recheck_required`（方式転換の選択肢提示）。No: 同一 root cause カテゴリ 3 回連続・承認後の 2/2（§ Loop Safety）に当たるか？ → Yes: 同じく `human_recheck_required`（方式転換の選択肢提示。`references/phase-progression.md` § Escalation Decision Table の方式転換の選択肢提示の行）。No: テスト設計が不足しているか？（RED が無い / 不十分）
   → Yes: gdd-test-driven-development
   → No: 次へ

2. 承認済み design.md の範囲内でコード/テスト修正だけで直せるか？
   → Yes: implementation_fix_only（ただし以下のアーキテクチャ問題の兆候が 1 つでも当てはまる場合は即 design_detail_only へ）
     ⚠️ アーキテクチャ問題の兆候:
     - 修正するたびに別の場所で新たな問題が現れる（症状が移動する）
     - 修正に mock / workaround / 条件分岐の積み上げが必要
     - 同一 root cause が形を変えて再発している
   → No: 次へ

2b. Architecture Gate（same route 3 回）
   → `Fix Attempts` / `worklog.md` / Bounce Log を読み、同一 Current Task または同一 root cause で same route（`implementation_fix_only` または `design_detail_only`）が 3 回連続して失敗しているか？
   → Yes: **アーキテクチャを疑う**。もう一度同じ route に戻さず、修正のたびに症状が移動する・workaround が積み上がる・同一 root cause が形を変えて再発する場合は `planning_rework_required` を強く検討する。scope / policy / ownership / security boundary の人間判断が必要なら `human_recheck_required`、要件は同じで構造だけ直すなら `design_detail_only`
   → No: 次へ
   ※ 正本は `references/bounce-log-schema.md` § Architecture Gate（same route 3回）

3. 要件（requirements.md の AC / scope）は変わらないが、
   design の detail（実装手段 / API 設計 / データ構造）を変える必要があるか？
   → Yes: design_detail_only → gdd-design-gating
   → No: 次へ

3b. [design_detail_only の場合] Approved Direction の自走範囲内か？
   → Yes: human check に戻さず gdd-design-gating で自走（E2E Discovery Loop）
   → No: 次へ（Step 4 で human_recheck_required を検討）
   ※ Approved Direction が state.md に無い場合は従来通り design_detail_only で進む

3c. [design_detail_only に倒す前の必須 lint] Approved Direction の glob 粒度を自動検査する：
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-approved-direction.py <state.md path>`
   → exit=1（**ERROR: single-file-fixed glob 検出**）: Approved Direction を最低限ディレクトリ単位（`src/foo/**`）に **修正してから** design_detail_only に進む。修正なしの design_detail_only は silent scope creep を起こすため禁止
   → exit=0 + **WARN: global glob × security-sensitive marker** が出力された: `**/auth/**` 等の交差なら `human_recheck_required` への昇格を検討する。`gdd-systematic-debugging` 内で吸収する判断にせず、人間判断を仰ぐ
   → exit=0 + 出力なし、または `INFO: global glob` だけ: design_detail_only で自走可（security-sensitive path に触れる変更は `human_recheck_required` に昇格する。正本の § 全域 glob × security-sensitive path の交差昇格）。`INFO: no Approved Direction patterns found` と `WARN: glob field not read` は glob を検査していない（見出しの形では `含むディレクトリ / モジュール glob:` の欄と続きの箇条だけを読み、glob の形〔`/` を含み `*` などを含む語か、`src/foo.ts` のような単一ファイル〕でない語が 1 つでもあれば欄を読まない。自由文の `自走範囲` は読まない）ので、自走範囲を上の 2 つに手で照らしてから進む（`WARN: human-evidence`〔自走上限と承認の evidence が `references/post-merge-qa.md` § 入口と手順 2 の形を満たさない理由〕は route 判定に使わない）
   ※ 正本ルール: `references/rollback-patterns.md` § Approved Direction glob 粒度 guard

4. 要件自体の変更が必要だが、scope は大きく変わらないか？
   → Yes かつ Approved Direction の自走範囲内: design_detail_only で吸収（AC 詳細化レベル）
   → Yes かつ 自走範囲外 or 方向性変更: human_recheck_required → human-check-waiting
   → No: 次へ

5. 前提や計画の組み直しが必要か？
   → Yes: planning_rework_required → gdd-brainstorming
   → No: fail-closed（判断できない → state を変えず停止）
```

### 並列修正パス（3+ 独立 failure の場合）

同一タスクで **3 件以上の独立した failure** がある場合（同一 root cause ではなく、異なるファイル / 異なるテスト対象に分散している場合）は、並列修正を検討する:

1. **独立性確認（起動前）**: 各 failure の修正ファイルが重複しないか、共有 resource（DB schema / 同一 API / 共有 config ファイル）への競合がないかを確認する。競合がある failure は sequential 修正に移行する
2. **独立している場合**: 各 failure を独立した subagent に割り当てる。各 subagent には失敗テスト / エラーメッセージ / 対象ファイルの focused context だけを渡す
3. **全 subagent 完了後の Conflict Detection**: `git status` / `git diff` で merge conflict を確認し、conflict があれば手動解消する。そのうえで、conflict の有無を問わず `gdd-subagent-driven-implementation` 手順 17 の「gate の前の RED Evidence の確認」をしてから `gdd-implementation-gating` に進む

### 並列調査パス（root cause が未確定で hypothesis 複数）

「並列修正」は root cause が判明済み・修正先が分かっているケースを対象とする。**root cause がまだ確定していない**段階で hypothesis が 2-4 件残っているときは、別パターンとして **failure-domain 並列調査** を検討する。詳細手順・発火条件・loop safety は `references/parallel-failure-investigation.md` を参照。

- **Independent Failure Domain Dispatch**: 並列調査は one agent per independent problem domain に限定する。同一 root cause から派生した related failures、同じ file / API / state field / external resource を触る仮説は並列化せず sequential に戻す。
- 発火条件: root cause 未確定 + hypothesis 2-4 件 + 各 hypothesis が独立検証可能 + 検証コストがそれぞれ重い
- 最大 2 ラウンド。確定しない場合は `human_recheck_required` に escalate
- Express パスでは使わない（sizing 昇格を提案する）

### 判定の具体的な目安

| route                               | 典型的な症状                                                                                          | 判断基準                                                                                             |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `implementation_fix_only`           | テスト失敗（ロジックバグ）、型エラー、import 漏れ、off-by-one                                         | design.md に書いてある方針通りに直せるか？ → Yes                                                     |
| `design_detail_only`                | 選定ライブラリの API が想定と違う、DB スキーマの追加カラムが必要、レスポンス型の変更                  | 要件は同じだが「どう作るか」を変える必要があるか？ → Yes                                             |
| `design_detail_only`（自走）        | E2E で env 未反映、packaging 不備、契約変更が必要と判明。方向性は同じ                                 | Approved Direction の自走範囲内で、AC を壊さない変更か？ → Yes                                       |
| `human_recheck_required`            | AC の解釈が曖昧で実装判断できない、要件間の矛盾が発覚、セキュリティ要件の追加が必要、方向性自体の変更 | 人間の policy 判断なしに scope を決められないか？ → Yes                                              |
| `human_recheck_required`（Express） | Express で `implementation_fix_only` では閉じられず、設計変更が必要と判明                             | Express Guard により `design_detail_only` / `planning_rework_required` が利用不可 → 直接エスカレート |
| `planning_rework_required`          | そもそも要件が現実的でない、技術的に実現不可能と判明、外部依存の前提崩壊                              | requirements.md の前提自体が崩れているか？ → Yes                                                     |

**Why:** 判定基準が主観だと、モデルは保守的に `human_recheck_required` を乱発するか、楽観的に `implementation_fix_only` で回し続ける。フローチャートにすることで、「承認済み design の範囲内か」を最初に確認する習慣をつける。

## Failure Routing

各 route には「戻り先」と「修正後にゴールまで自動的に進む復帰シーケンス」がある。どの route でも、レビューの指摘を直す段（テストを書く段を含む）は `references/self-review-lanes.md` § 直し方 に従う。route を決めたら、route によらず、受け取った差し戻しの finding を対象の task の `Fix Findings:` に書き直す（completion-check の差し戻しは completion-check が書くので書かない。書き方は `references/state-field-tiers.md` の `Fix Findings` の行）。対象の task が `Current Task`・`Pending Tasks` に無いとき（Pre-PR loop・PR 後のレビューなど、全 task が `Completed Tasks` に移った後の差し戻し）は、同じ steering で直す route なら、書く前に `references/state-machine.md` § tasklist.md の canonical state のとおり再オープンする（Hotfix Lane に回す route では再オープンせず、`Fix Findings:` の代わりに同じ形の行を、差し戻しを受けた steering の `worklog.md` の `## Hotfix Findings` に書く。戻り先は同じ steering の復帰シーケンスではなく Hotfix Lane の新しい steering。新しい steering への渡し方は同節）。active な `/gdd-dev` run では、各 phase が完了したら次の phase に自動 handoff し、途中で止まらない。

### Standard / Quick (standard) の復帰シーケンス

- テスト設計不足 / failing test 不足:
  - 戻り先: `gdd-test-driven-development`
  - 復帰: TDD RED → GREEN → impl-gate → （次タスク or completion）
- `implementation_fix_only`:
  - 戻り先: `gdd-subagent-driven-implementation`
  - 復帰: 実害クラス / `High` の finding（文言・帳簿の指摘は除く）は RED 再現テスト（§ 直し方 2 のテストもこの段で書く）→ 実装修正 → impl-gate → （次タスク or completion）。それ以外は § 直し方（コードの挙動を変える修正なら再現テスト）→ 実装修正 → impl-gate → （次タスク or completion）。詳細手順・commit 規律は `references/rollback-patterns.md` § implementation_fix_only
- 修正後の再審査:
  - 戻り先: `gdd-implementation-gating`
- `design_detail_only`:
  - 戻り先: `gdd-design-gating`
  - 復帰: design gate 通過 → task-breakdown（全セクションを作り直す。`references/state-machine.md` § planning 差し戻し後の tasklist.md リセット）→ TDD → 実装 → impl-gate → completion
- `human_recheck_required`:
  - 戻り先: `human-check-waiting`
  - 復帰: 人間承認 → design-gating → task-breakdown → TDD → 実装 → impl-gate → completion
- `planning_rework_required`:
  - 戻り先: `gdd-brainstorming`
  - 復帰: brainstorming（自律解決ループ）→ requirements-gating → human check → design-gating → task-breakdown → TDD → 実装 → impl-gate → completion

上記 4 route（`implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required`）の永続化は `references/rollback-patterns.md` の同名パターンに従う。

### Express パスの復帰シーケンス

Express では task-breakdown / design-gating を経由しないため、復帰シーケンスが短い。

- テスト設計不足 / failing test 不足:
  - 戻り先: `gdd-test-driven-development`
  - 復帰: TDD RED → GREEN → impl-gate → done
- `implementation_fix_only`:
  - 戻り先: `gdd-subagent-driven-implementation`
  - 復帰: 実害クラス / `High` の finding（文言・帳簿の指摘は除く）は RED 再現テスト（§ 直し方 2 のテストもこの段で書く）→ 実装修正 → impl-gate → done。それ以外は § 直し方（コードの挙動を変える修正なら再現テスト）→ 実装修正 → impl-gate → done（詳細: `references/rollback-patterns.md` § implementation_fix_only）
- `human_recheck_required`（Express のエスカレーション先）:
  - 戻り先: `human-check-waiting`
  - 復帰: 人間承認 → 実装修正 → impl-gate → done
  - Express Guard により `design_detail_only` / `planning_rework_required` はスキップされ、ここに直接到達する

## Review-Finding Priority

- 優先順位は `High` -> `ops-blocking medium` -> その他 `Medium`。並べるのは差し戻しの理由になった finding だけで、Advisory Findings に記録したものは `ops impact` によらず並べない
- `ops-blocking medium`:
  - `Medium` のうち、本番挙動、セキュリティ境界、データ整合性、customer-visible regression、resume / gate correctness（範囲は `references/reviewer-common.md` § 常時 High の適用範囲に従う）、rollout / rollback / recovery、observability、required verification evidence、operator safety に影響するもの
- reviewer 出力に `ops impact: yes|no` があればそれを優先して使う
- `ops impact` が無い場合は、issue の `impact` 記述と reviewer 種別から推論する
  - `gdd-security-reviewer` の `Medium` は、明確に cosmetic でない限り `ops-blocking medium` 寄りに扱う
  - `gdd-implementation-reviewer` の `Medium` は、user-visible behavior、reliability、rollback、observability、required evidence、operator safety に触れていれば `ops-blocking medium` とみなす

## Error Log（worklog.md への構造化記録）

routing 完了後、`worklog.md` に以下のテーブル形式でエラーを追記する。テーブルが無ければ `## Error Log` 見出しごと作る。既にあれば行を追加する。

```markdown
## Error Log

| #   | Phase | Error | Root Cause | Resolution | Attempt |
| --- | ----- | ----- | ---------- | ---------- | ------- |
```

- `#`: 連番
- `Phase`: エラーが発生した phase 表示名（`TDD:RED`, `TDD:GREEN+REFACTOR`, `impl-gate` など）
- `Error`: エラーメッセージまたは症状（1 行に収める）
- `Root Cause`: 根本原因の要約
- `Resolution`: 修正内容または routing 先
- `Attempt`: 同一タスクでの試行回数を分数形式で記録（例: `1/3`, `2/3`, `3/3` — 分母 3 は Loop Safety の blind fix 上限。`human_recheck_required` 後は分母 2。上限到達で escalate 必須）

### 記録条件

- `changes_requested` による差し戻し → **常に記録**（remediation の追跡に必須）
- planning 差し戻し（`design_detail_only` / `human_recheck_required` / `planning_rework_required`）→ **常に記録**（重い判断のため記録は必須）
- `implementation_fix_only` で 1 回で解消 → **記録任意**（単純な修正は記録の overhead が大きい）
- テスト設計不足で `gdd-test-driven-development` に戻す → **記録任意**

## Loop Safety

- `implementation_fix_only` を選択するたびに `tasklist.md` の `Current Task` セクション内の `Fix Attempts` を +1 する（Gate Batch では finding の対象の task に足す。カウンタが無ければ `Fix Attempts: 1/3` を追加する）。**表記は分数形式に固定**（`<試行回数>/<上限 3>`、例: `1/3`, `2/3`, `3/3`）。worklog.md の Error Log の `Attempt` 列も同じ分数形式を使う（例: `1/3`, `2/3`, `3/3`）。単独数字（`1`, `2`）の表記は使わない。**`human_recheck_required` 後は reset to 0 のうえ分母を 2 にする**（`1/2`, `2/2`。承認後の再ループ上限。上限が無いと、承認後も試行が続いた事例がある）
- 同じ `Current Task` に対する 3 回目の blind `implementation_fix_only` は許可しない（Gate Batch では task ごとに数える。正本: `references/state-machine.md` § Remediation Loop Safety）。判定は `tasklist.md` の `Fix Attempts` カウンタを正本とし、`worklog.md` の Error Log を補助根拠にする。両者が食い違う場合は大きい方を採用する（安全側に倒す）
- unresolved `High` / 実害クラスの finding が明確に減っていない、または同一 root cause が再発している場合は、`implementation_fix_only` を繰り返さず `design_detail_only` / `human_recheck_required` / `planning_rework_required` へエスカレートする（route を書く前に、`references/state-machine.md` § Remediation Loop Safety の前提の点検をする。下の Approach Rethink も同じ）。task の `Gate Rounds` が 3 以上になってから最初に route を決めるときは、route を書く前に方針を考え直し（`references/self-review-lanes.md` § 直し方 の 0）、その task ブロックに `Approach Rethink` の 1 行を書く（値域・書き方の正本: `references/state-machine.md` § Remediation Loop Safety）
- 適切な route を正本から決められない場合は fail-closed で停止し、state を変えずにユーザーへ `参照した正本` / `停止理由` / `次の1アクション` と `## 👤 次にすること` を返す。方式転換の選択肢で止まる遷移（Decision Tree 1 と Express Guard の ADR ≥ 2・同一 root cause カテゴリの 3 回連続・承認後の 2/2、Step 8 の ADR ≥ 2。5/5 の Escape Hatch と、方式転換でない `human_recheck_required` では書かない）を書いたときは、同じ手順で `worklog.md` に `上限到達:` 行を語 `remediation-loop-limit` で書く（正本: `references/human-check-template.md` § 事前回答 3）
- **Reviewer Loop Escape Hatch**: 同じ `Current Task` に対して `changes_requested` が **5 回連続** で返された場合（route に関係なく、`implementation_fix_only` + `design_detail_only` の合計カウント。Gate Batch では finding の対象になった task ごとに数え、batch の全 task を `changes_requested` にした回数では数えない）、route 判定を無視して **route recalibration checkpoint** を実行する。カウントは `tasklist.md` の `Fix Attempts` + `worklog.md` の Error Log を照合する。
  - blocker が **policy / scope / ownership / security boundary / prompt-output contract** の変更を要求するなら `human_recheck_required`
  - blocker が `Reviewed by:` 欠落、verification wording 不整合、reviewer evidence 整形ミスなどの **procedural / evidence only** なら `human_recheck_required` に上げず、`implementation_fix_only` として failing gate の再実行条件を整える。戻り先は `gdd-implementation-gating` または `gdd-completion-check` を優先し、route を確定できないときだけ fail-closed `blocked`。**再ループ上限**: 承認後の `2/2` 到達、または同一 root cause カテゴリ 3 回連続 finding では、修正を続けず方式転換の選択肢を人間へ一括提示する（正本: `references/state-machine.md` § Remediation Loop Safety）

### なぜ 3 回か / Architecture Problem の兆候

2 回目の修正で新しい問題が別の場所で現れる場合、それは isolated bug ではなく shared state / coupling / leaky abstraction が根本原因の可能性が高い。3 回目の盲目的な修正は問題を移動させるだけであり、根本解決にならない。

以下の兆候が 1 つでも当てはまる場合は `implementation_fix_only` を選ばず、即 `design_detail_only` または `planning_rework_required` へエスカレートする:

- 各修正が異なる場所で新たな問題を露出させる（症状が移動する）
- 「どこにバグがあるか」ではなく「なぜそこに伝播したか」の説明が必要になる
- mock / workaround / 条件分岐を積み上げないと修正できない
- 同一 root cause が形を変えて再発している

## Steps

1. **SMI Block 受け取り確認**: `root-cause-investigation` から handoff されている場合、Phase 4 出力に State Machine Integration block があるか確認する。あれば「SMI Block Handoff」セクションのチェックリストに従って Routing 提案 / Reviewer Lineage / ADR 起票を取り扱う。無ければ standalone 呼び出しとみなして通常 Decision Tree に進む

2. **症状の種別を分類し、root cause を確定させる**（`references/debug-triage.md` を参照）。種別によって入口と methodology の使い方が違う:
   - **Silent failure（無反応 / 応答なし / timeout）**: テスト RED の前にインフラ層チェックを先に行う。`root-cause-investigation` の Phase 1（特に「境界ごとに証跡を集める」）を境界順に回し、どの境界で壊れているかを特定する。インフラ層で root cause が特定できれば Routing Decision Tree をスキップしてよい
   - **Expected side effect missing**: テスト PASS だが副作用（PR open 等）が起きていない場合。テストが実際に何を検証しているか確認し、副作用の実態を直接確認する。`root-cause-investigation` の Phase 1〜2 を使い、テスト assertion と副作用の差分を埋める
   - **Test RED**: 実行可能なテストが失敗。再現条件・`Expected` / `Actual` / `Evidence` が未整理なら先に `gdd-test-failure-debug-pack` を作る。pack だけで root cause が確定しない場合は `root-cause-investigation` の Phase 1〜3 を続けて回してから本 skill に戻る
   - いずれの種別でも、Routing Decision Tree に入る時点で **「root cause は X。理由は Y」が言葉で書ける** 状態にしておく
   - active worktree 側 `.steering/.../adr.md` があれば、既に確定した重要判断も補助コンテキストとして確認する
   - stopped workflow の再開文脈で、single active build candidate に対して review / re-entry cue（例: `レビューで`, `差し戻し`, `実装方針変更`, `設計見直し`, `planning_rework_required`, `human_recheck_required`, `design_detail_only`）が来た場合は、新しい worktree / `.steering/...` を作らず、同じ active worktree の `tasklist.md` / `design.md` / reviewer evidence を入力に route を切り分ける。host 側の一般的な **Plan mode** に逃がさない
3. advisory review 由来の指摘なら、先に `gdd-receiving-code-review` で妥当性を確認してからここへ戻す。
4. formal gate の `changes_requested` 由来なら、差し戻しの理由になった findings を `High`、`ops-blocking medium`、その他 `Medium` に並べ替える。Advisory Findings に記録した finding は並べず、直さない。
5. approved な要件・実装方針の範囲で閉じる issue は、まず `implementation_fix_only` として `gdd-subagent-driven-implementation` に戻す。
6. `High` と `ops-blocking medium` は、未着手のままユーザー確認待ちにせず、scope 内で閉じるかぎり自律 remediation を優先する。
7. その他 `Medium` のうち差し戻しの理由になったもの（実害クラス、category 未付与、Stage A の fail、Spec Drift）も unresolved blocker なので、local かつ deterministic に直せる限り同じ loop で解消を続ける。
8. 同じ `Current Task` で `changes_requested` が 2 回連続した場合は、`worklog.md` に根本原因、前回との差分、今回の route 判断を書く。**route 確定前**に active worktree 側 `.steering/.../adr.md` で `- **Origin**: remediation / <Current Task>` 行を持つ entry も数え（ADR ≥2 独立トリガー）、2 件以上なら `Fix Attempts` や root cause カテゴリ一致を待たず `references/phase-progression.md` § Escalation Decision Table の該当条件に従い方式転換の選択肢を提示する。
9. 同じ `Current Task` で unresolved `High` / 実害クラスの finding が明確に減っていない、または同一 root cause が再発している場合は、3 回目の blind `implementation_fix_only` を選ばない。
10. `design_detail_only`、`human_recheck_required`、`planning_rework_required` は、approved scope では閉じられないことが根拠付きで示せた場合だけ使う。
11. 適切な route を正本から決められない場合は fail-closed で停止し、state を変えずに `参照した正本` / `停止理由` / `次の1アクション` と `## 👤 次にすること` を返す。
12. `worklog.md` の `## Error Log` テーブルにエラー行を追記する（テーブルが無ければ作る）。原因・根拠・回避策も必要に応じて記述する。
13. remediation の過程で重要な意思決定、却下した代替案、今後の実装や運用に影響する判断が確定した場合は、active worktree 側 `.steering/.../adr.md` を作成または更新し、`Context` / `Decision` / `Why` / `Consequences` に加えて `- **Origin**: remediation / <Current Task>` 行を追記する（省略すると `references/state-machine.md` § Remediation Loop Safety の ADR ≥2 独立トリガーが発火しない）。SMI block で `ADR 起票: 要` が来ていた場合は必須、それ以外は任意。
14. 実装修正や再審査だけで閉じる場合は、active worktree 側 `tasklist.md` の `Next Action` だけを戻り先に更新する。
15. planning へ差し戻す場合の永続化先は `references/state-machine.md` の保存場所定義に従う。

- `Gate Status` / `Resume From` / `Route In Progress`: active worktree 側 `state.md`
- `Next Action`: active worktree 側 `tasklist.md`

16. `Resume From` を更新するのは planning へ差し戻す場合だけにする。
17. route を決定したら `state.md` の `Route In Progress` を該当 route 名に更新する（`references/rollback-patterns.md` 参照）。route の修正が完了し次の phase に正常遷移した時点で、遷移先の skill が `none` にクリアする。
18. コードやテストを修正した場合は、修正後に必ず `gdd-implementation-gating` を再通過する。
19. `gdd-completion-check` に進めるのは reviewer 通過後だけにする。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける
- routing 決定後は以下のテンプレートでターミナルに出力する。route 名だけで止めない。

```markdown
## デバッグ routing 決定

### 症状

<failure の 1 行要約>

### 根本原因

<root cause の 1 行要約（判定根拠付き）>

### 選択した route: `<route 名>`

- **理由**: <Routing Decision Tree のどの判定で決まったか>
- **戻り先**: <具体的な skill 名>
- **復帰シーケンス**: <route 完了後のゴールまでの流れ>

### 優先 findings（差し戻しの場合）

| #   | 深刻度              | 内容      | 対応方針   |
| --- | ------------------- | --------- | ---------- |
| 1   | High                | <finding> | <修正方針> |
| 2   | ops-blocking Medium | <finding> | <修正方針> |

### 次のアクション

- → <何をするか具体的に>
```

- `human_recheck_required` の場合は、人間に何を判断してほしいかを承認ポイント形式で明記する
- `implementation_fix_only` で自律修復する場合は、修正方針を 1-2 行で示してから実行に移る
- fail-closed 停止の場合は `references/output-format.md` の停止出力テンプレートに従う

## Worked Example

### 例: implementation-gating で changes_requested → routing 判定

**状況**: `gdd-implementation-gating` が `changes_requested` を返した。findings:

- High: `handler.ts` で未認証ユーザーが admin API にアクセス可能
- Medium (ops impact: yes): エラー時に 500 を返すが、原因がログに残らない

**判定フロー**:

1. テスト設計不足？ → No（テストは存在し、PASS している）
2. 承認済み design の範囲内で直せるか？
   - High: design.md に「認証ミドルウェアを通す」と書いてある → design の範囲内 → Yes
   - Medium: design.md に「エラーログを出す」と書いてある → design の範囲内 → Yes
3. → `implementation_fix_only` → `gdd-subagent-driven-implementation` に戻す

**もし High が「admin API 自体を廃止すべき」だったら**:

1. → 2 で No（design の範囲を超える）
2. → 3: 要件は変わらないが API 設計を変える → `design_detail_only` → `gdd-design-gating`

## Rationalization Check（この skill 固有）

debugging で guess-and-check に流れたくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。全体向けは `references/common-guardrails.md` § 合理化防止テーブル。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「原因は明らか、すぐ直せる」 | 「明らか」な原因の 3 割は症状で、真因は別にある。systematic diagnosis が guess-and-check より速い | [Confirmation Bias] 最初の仮説を支持する証拠だけ見て、反証を試みないと症状で fix を当ててしまう |
| 「とりあえず動かしてみて様子を見る」 | 仮説なしの試行は失敗データが蓄積しない。Decision Tree で経路を決めてから手を動かす | [Bias for Action] 進捗の見えなさを嫌い、仮説より行動を優先する |
| 「High だけど impl 修正で閉じられそう、design 触らなくていい」 | impl で閉じられるか確認してから判断。確認なしの blind `implementation_fix_only` は 3 回目で禁止される | [Premature Closure] 早く閉じたい欲求が、設計レベルの問題を impl で握り潰そうとする |
| 「3 回目の impl fix でなんとか通す」 | 3 回失敗は route の誤り。`design_detail_only` や `planning_rework_required` への昇格が必要 | [Sunk Cost Fallacy] 既に 2 回 fix した投資を惜しんで撤退できない |
| 「advisory review だから従わなくていい」 | advisory は `Next Action` を直接変えないが、worklog に記録して次の remediation で参照する対象 | [Authority Substitution] formal でない指摘を「権威ではない」と読み替えて無視する |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、planning 差し戻し route、fail-closed 応答）。以下はこの skill 固有のルール。

- 実装後の差し戻しは、まず `implementation_fix_only` か `design_detail_only` で閉じられないかを確認する
- `High` と `ops-blocking medium` を未着手のままユーザー確認待ちにしない
- 同じ `Current Task` に対する 3 回目の blind `implementation_fix_only` を許可しない
- review / re-entry cue だけで `Resume From` / `Next Action` を飛び越えて決め打ちしない
- `worklog.md` には機密を書かない
- advisory review の findings だけで `Next Action` を直接変えない
- **Context Compaction Resilience**: route 決定前に `state.md`（現在の Gate Status / Route In Progress）と `tasklist.md`（Current Task / Fix Attempts）に加え、Routing Decision Tree 1 が数える `worklog.md` の Error Log（同一 root cause カテゴリの連続）と `adr.md`（remediation 由来 ADR entry の件数）をディスクから re-read する。debug cycle が複数回繰り返される場合、compaction により前回の route 判定結果や Fix Attempts カウンタが劣化し、Loop Safety の 3 回制限が正しく機能しなくなるリスクがある
