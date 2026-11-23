---
name: gdd-dev
description: 'やりたいことを伝えるだけ。要件整理→人間確認→設計→TDD→実装→レビュー→PRを自動ゲート付きで完走する'
argument-hint: 'やりたいこと（例: ユーザー一覧にページネーションを追加したい）'
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-gdd-loop.sh:*)"]
---

# Gate-Driven Development

`gate-driven-development` の steering-first workflow entrypoint。contract と state の正本は以下を参照。

## 30 秒で分かる GDD（人間向けメンタルモデル）

GDD で人間が覚えることは 3 つだけ:

1. **伝える**: `/gdd-dev やりたいこと` — AI が要件を整理する
2. **承認する**: 初回 human check で OK / 修正 を答える（3 分程度）。承認後の再 human check は policy / scope / ownership / security boundary / technology stack / access method / credential backend が変わるときだけ
3. **待つ**: 承認後は原則すべて自動（テスト → 実装 → レビュー → PR 作成）。`human_recheck_required` が出たときだけ再度確認する

裏側の skill / reference / reviewer agent / hook は AI が参照する。**人間が中身を覚える必要はない**。

### タスクの大きさで自動調整

正式な分類は `trivial` / `quick` / `standard` の 3 段階。`quick` はさらに `express` と `standard` に分岐する（分類の正本は `references/task-sizing.md`）。

| サイズ           | 例                                                   | 何が起きるか                                        |
| ---------------- | ---------------------------------------------------- | --------------------------------------------------- |
| trivial          | typo / 設定値の文言修正                              | 即完了。承認もレビューもなし                        |
| quick (express)  | 1-2 ファイルの明白なバグ修正（方針 1 案・AC 1-3 個） | 要件レビュー → 承認 1 回 → テスト + 実装 → レビュー → 完了 |
| quick (standard) | 小規模な機能追加（3-5 ファイル、security 影響なし）  | 承認 → 設計 → タスク分解 → 実装 → レビュー → 完了   |
| standard         | 6+ ファイル or route / security / 外部連携 影響あり  | 承認 → 詳細設計 → 実装ループ → refactor gate → 完了 |

「GDD は重い」と感じたら、まず `/gdd-dev <小さなタスク>` を試す。sizing が自動で適切なセレモニーを選ぶ。`--express` で express を明示指定できる。

補足: human check は planning の初回 gate が基本で、承認後の build / review / PR では原則止まらない。再承認が必要なのは、`human_recheck_required` に相当する policy / scope / ownership / security boundary / prompt-output contract / technology stack / access method / credential backend / multi-tenant boundary の変更だけ。

補足2: `API mismatch` や `runtime / env / packaging / dependency` のずれは、契約形状と採用方式が変わらない限り human check ではなく self-heal の対象。ただし MCP / CLI / SDK / API の access method、公式統合の採否、credential backend、tenant / account 切替境界が変わる場合は、単なる dependency mismatch として閉じず、requirements の `実装方針` を更新して `human_recheck_required` を検討する。`AC` の追加・削除や pass/fail 判定の変更は別扱いで、`planning_rework_required` か `human_recheck_required` を検討する。

補足3: `AC` の意味が変わるなら `planning_rework_required` を優先する。`human_recheck_required` は、policy boundary の再承認が必要でも AC semantics が同じ場合だけ。

### 迷ったら見る 3 つ

| 状況               | 見る場所                                                |
| ------------------ | ------------------------------------------------------- |
| 現在地が分からない | `gdd-status` — 現在の phase / gate / next action を表示 |
| 初回の使い方       | `references/onboarding.md` — 最短シナリオ               |
| 詰まった           | `references/faq.md` — よくある症状と解決策              |

---

## Arguments

`$ARGUMENTS`

## Session Loop Setup

**他のアクションより先に**、以下のコマンドを Bash ツールで実行してセッション状態を初期化してください:

```
${CLAUDE_PLUGIN_ROOT}/scripts/setup-gdd-loop.sh $ARGUMENTS
```

実行後、その出力を読んでワークフローを継続してください。

`setup-gdd-loop.sh` の出力は bootstrap 用の補助ヒントです。entry intent / phase / stop 判定の最終責任はこの command 本文と `references/entry-intent.md` / `references/state-machine.md` / ディスク上の `state.md` にあります。shell heuristic と正本が食い違う場合は正本側を優先してください。

### スクリプトが走らなかった場合のフォールバック

`setup-gdd-loop.sh` が走らなかった場合（permission classifier など）、以下を手動で行う（走って 0 以外で終われば止まって知らせる）:

1. `CLAUDE_CODE_SESSION_ID` が設定されているか確認する（`env | grep CLAUDE_CODE_SESSION_ID`）
2. `.claude/gdd-dev.local.md` が `active: true` で別の `session_id` を持つなら止まって知らせる（持ち主の時刻も。取り方は `${CLAUDE_PLUGIN_ROOT}/docs/TROUBLESHOOTING.md` のロックの節）。無ければ Write で次の内容で作る:
   ```
   ---
   active: false
   session_id:
   ---
   ```
3. `references/subagent-dispatch.md` の「1. Brainstorming + Requirements-Gating」セクションを Read ツールで読み、`${ARGUMENTS}` と `${CLAUDE_PLUGIN_ROOT}` を実際の値に置換して Opus subagent として起動する（Instruction 7 と同じテンプレート使用ルール・カスタムプロンプト禁止・Worktree Post-Return Validation を適用する）
4. brainstorming の後、手順 2 の形で Write で書き直し、`active: true` と `session_id` を入れて継続する（書く直前に読み直し、別の active な session_id は書き換えずに時刻も添えて止まる）

**Why:** 手動で最小 state を作れば、同じフローに入れる。

## Quick References

- 概要と使い分け: `README.md`
- 初回の最短シナリオ: `references/onboarding.md`
- 詰まりどころ: `references/faq.md`
- contract の境界: `references/self-contained-contract.md`
- routing / resume / state の正本: `references/state-machine.md`
- entry intent 解決ルール: `references/entry-intent.md`
- phase 進行ルール: `references/phase-progression.md`
- model routing: `skills/gdd-model-routing`
- reviewer 選定の正本: `references/reviewer-selection.md`
- subagent dispatch: `references/subagent-dispatch.md`
- phase 遷移ヘッダー: `references/output-format.md`
- task sizing + Complexity Evaluation: `references/task-sizing.md`
- express requirements template: `references/requirements-template-express.md`（quick express は full template から始めない）
- compact human check template: `references/human-check-template-compact.md`（初回表示の一次テンプレート）
- 運用レベル: `references/operation-levels.md`
- context 管理: `references/context-budget.md`
- session state: `.claude/gdd-dev.local.md`
- task identity registry: `.gdd/tasks/<task_id>/binding.json`（生成・解決: `scripts/gdd_task_binding.py`）
- 変更履歴: `CHANGELOG.md`

## Post-Merge Same-Chat Boundary

PR merge 後に同じチャットで続ける場合は、マージ後のローカル整理案内を先に出す。方針は「同じチャット継続 + stageごとに新 worktree」。cleanup 前に worktree 外へ保存したことを確認し、worktree remove で消える成果物がないか確認する。必要に応じて `gdd-using-git-worktrees` を使い、`worktree remove` / `branch delete` の候補を提示する。旧 worktree では後続実装しない。

### Merge Report Cleanup Trigger

`マージした` / `mergeした` / `merged` は post-merge verification、deployment/status verification cue、cleanup cue として扱う。`safe cleanup ready` の判定条件は `skills/gdd-using-git-worktrees/SKILL.md` の Post-Merge Cleanup に従い、揃えば追加の cleanup 指示を待たず実行する。揃わない場合は cleanup 候補とブロッカーを出す。

## Instructions

0. **Plan mode に入らない。** `/gdd-dev` は自身のワークフロー内で要件整理・設計・実装を行う。`EnterPlanMode` ツールを呼ばず、直接 `gdd-brainstorming` skill に進む。タスクの複雑さは Plan mode ではなく task sizing（trivial / quick / standard）で対応する。
   - **Active Session Follow-up Contract**: `.claude/gdd-dev.local.md` が `active: true` の間、`/gdd-dev` は loop state を消す reason（`references/output-format.md` の許容値）まで sticky に継続する。後続発言で「計画して」「これも対応して」「レビュー指摘を直して」と言われても、host Plan mode や generic Agent process へ移らず、`references/phase-progression.md` の "Active Session Follow-up Classification" で route を決める。
   - **Manual merge continuation**: PR 作成後にユーザーが `mergeした` / `マージした` / `merged` と伝えた場合、直前の文脈に「apply 完了を待つ」「deploy 後に続行」「merge 後に確認」「後続作業を実施」などの継続意図があれば、追加の「続行して」を待たずに `references/phase-progression.md` § Post-PR / Post-Merge Contract の manual merge continuation に従う。merge 後 workflow 監視、post-merge / post-apply verification、state/tasklist re-read、Approved Direction / 自走上限確認、残タスク確認まで進める。ただし `mergeした` は read-only 監視・検証の再開 cue であり、新たな write 操作は既存の approval gate を維持する。
   - **分類してから実装**: active session 中のユーザー入力は、実装前に `implementation_fix_only` / `design_detail_only` / `requirements_amendment` / `human_recheck_required` / `cancelled` のいずれかに分類する。AC の追加・削除・意味変更は `gdd-requirements-amendment` に委譲し、既存 AC 内の reviewer 修正・テスト修正は human check に戻さず build/debug route で継続する。
   - **human check の再要求条件**: 初回承認後の再 human check は、AC semantics / scope / policy / ownership / security boundary / prompt-output contract / technology stack / access method / credential backend / multi-tenant boundary / official integration adoption が変わるときだけ。既承認範囲内の実装修正、reviewer 指摘対応、E2E で見つかった implementation bug は、判断根拠を state / tasklist / worklog に残して自走する。
   - **Post-Implementation Modification Guard（done 後の修正依頼）**: active steering の `Next Action=done` または直前ターンで `<gdd-stop reason="done">` が発火した状態で修正依頼が来た場合、brainstorming に渡す前に以下を確認する。
     - **Default は `requirements_amendment`**。以下の**すべて**を満たす場合のみ `implementation_fix_only` に倒せる:
       1. 既存テストが fail しており、テスト変更なしに実装を直すだけの純粋バグ修正（ユーザーの申告ベースで判断する。修正後もテストが fail した場合は条件 1 が成立しないとみなし、改めて分類し直す）
       2. 新しいユーザー向け挙動が一切追加されない
       3. 既存 AC の意味・条件・境界値が変わらない
     - 1 つでも満たさない場合は `requirements_amendment` として `gdd-brainstorming` → `gdd-requirements-amendment` に委譲する（ユーザー向け挙動は変わらないが実装アプローチだけが変わる場合は `design_detail_only` となる。詳細は `references/phase-progression.md` § Post-Done Correction Default 参照）
     - 判断に迷ったら `requirements_amendment` に倒す（安全側優先）
     - **Why**: `done` 後の修正は定義上「承認外の変更」の可能性が高く、`implementation_fix_only` に落とすには明確な純粋バグ修正の証拠が必要。
1. この command は v1 の正式 workflow entrypoint。壁打ちだけなら `gdd-pre-workflow-brainstorming` を使う。
2. `references/self-contained-contract.md` と `references/state-machine.md` の contract を崩さない。
   2.0. **Task Binding Registry（混線防止）**: 自然文の「続き」「今どこ？」「再開して」は entry cue であり、current task を決める根拠にしない。task identity は `.gdd/tasks/<task_id>/binding.json` と current worktree / branch の一致で解決する。
   - `state.md` を作成または更新した後は `<plugin-root>/scripts/gdd_task_binding.py upsert-from-state --repo-root <repo-root> --state <worktree>/.steering/<task>/state.md` で binding を更新する。
   - resume / status / compact 503 復帰では `<plugin-root>/scripts/gdd_task_binding.py resolve --repo-root <repo-root> --cwd <cwd> --current-branch <branch> --local-state-path .claude/gdd-dev.local.md --latest-user-text "<user text>"` と同じ deterministic resolver を使う。
   - `.claude/gdd-dev.local.md`、`session_id`、root 側 `.steering` は soft signal / diagnostic。registry と current worktree の hard match を上書きしない。
   - resolver が 0 件または複数候補を返す場合は fail-closed で停止し、古い task の phase / Current Task / Last Handoff を current として表示しない。
   2.1. **Entry intent の短縮ルール**: 詳細判定は `references/entry-intent.md` を正本とするが、初動では次を優先する。
   - **`new` に倒してよい条件**: active steering が未解決で、入力に「何を変えたいか」が具体的に書かれている（対象・目的・変更内容が分かる）場合。既存機能の修正依頼でも、resume cue や active steering が無ければまず `new` を候補にする。
   - **Codex compact 503 は resume cue**: `Error running remote compact task` / `responses/compact` / `unexpected status 503 Service Unavailable` を含む入力は、host-level interruption からの復帰として扱う。新規 task に倒さず、active steering を 1 件に絞って `state.md` / `tasklist.md` の正本から再開する。候補 0 件または複数なら fail-closed。
   - **`ambiguous` で fail-closed する条件**: `変更した` / `続き` / `あれ` / `例の件` のような弱い cue しかなく、かつ active resume candidate が **1 件以上存在** して `new` と `resume` を一意に決められない場合。
   - **`ambiguous` でも `new` default で進めてよい条件**（Lightweight Path）: 上記の weak cue + active candidate が **0 件**、または `$ARGUMENTS` 空 + candidate 0 件。fail-closed せず `new` として brainstorming を開始し、「既存タスク再開なら `/gdd-dev resume <slug>` で再入力」の revert option を 1 行添える。
   - **`amendment` に倒す条件**: 既存の対象を **一意に anchor できる** 場合のみ。anchor には active steering / 進行中 plan / 明示された既存 feature・artifact 名を含む。単に「既存機能のバグ修正」だからという理由だけで `amendment` にしない。
3. same-name ambient asset が plugin-managed symlink alias なら衝突に含めない。別実体で解決不能なら fail-closed で停止。
4. fail-closed や mandatory gate で止めるときは `参照した正本` / `停止理由` / `次の1アクション` と `## 👤 次にすること` を返す。
5. ユーザーが現在地に迷っていそうなら `現在 phase` / `参照した正本` / `次の1アクション` を先に示す。
6. **モデルルーティング（重要）**: 計画フェーズは `references/subagent-dispatch.md` の Template（`subagent_type` 付き）で Opus subagent に委譲する。mainのターミナル設定に依存しない。詳細は `references/subagent-dispatch.md` § Subagent Model Routing と後述の「Model Routing（概要）」を参照。
   - **Codex Subagent Permission Gate**: Codex では planning / reviewer / dialectic review / implementation worker のいずれでも、ユーザー発言・project policy・`/gdd-dev` 引数から `explicit_delegation_source` を確認する。明示委譲ソースがあれば `state.md` の Approved Direction に `Codex Subagent Delegation Permission: approved_by_explicit_delegation` と `explicit_delegation_source=<source>` を記録し、HITL で再確認しない。明示委譲ソースも `approved` も無い場合、Codex では許可が無いまま subagent dispatch を起動しない。同じ contract を **main session inline execution** として実行し、parallel batch は **sequential execution** に落とす。これは危険操作や merge / deploy の承認とは別物。
7. **Brainstorming dispatch（テンプレート必読）**: brainstorming subagent を dispatch する前に、**必ず** `references/subagent-dispatch.md` の「1. Brainstorming + Requirements-Gating」セクションを Read ツールで読む。そのテンプレートを `${ARGUMENTS}` / `${CLAUDE_PLUGIN_ROOT}` を実際の値に置換して使い、Opus subagent として dispatch する。置換の前に、`${ARGUMENTS}` に MCP でしか読めない URL（社内の wiki・チケット管理・Slack など、WebFetch で読めないものや利用者の指示で MCP 経由と決まっているもの）があれば、メインが MCP で読んで本文を一時ファイルに保存し、Template の `読むファイル` にその絶対パスを書く（runner は MCP のツールを持たない）。書く形は `<URL> → <絶対パス>` の対にする。一時ファイルはセッションの scratchpad（無ければ `mktemp` で作る repo の外のファイル）に置き、runner が戻ったら消す。カスタムプロンプトを書いてはならない（テンプレートの `手順` 欄が worktree 作成・entry intent 解決・contract 準拠を保証する）。
   - **Worktree Post-Return Validation（Instruction 9 の 2 系統検証より先に実行）**: brainstorming subagent 復帰後、まず `.steering/` ディレクトリのパスを確認する（worktree 違反は前提条件の検証であり、state.md の内容検証より先行する）。パスがリポジトリ root（worktree パスではなく repo の checkout 先）直下にある場合、worktree が作成されていない違反状態。この場合は fail-closed で停止し、以下を返し、`<gdd-stop reason="blocked">` の後に `## 👤 次にすること` を付ける:
     - 参照した正本: `gdd-using-git-worktrees` SKILL.md § Guardrails（root に `.steering/` を作らない）
     - 停止理由: worktree なしで `.steering/` が repo root に作成された
     - 次の1アクション: `gdd-using-git-worktrees` で worktree を作成し、steering artifacts を worktree 内に移動してからワークフローを継続する
   - **Pre-Write Guard 優先**: 上記は最後の検知であり、通常ルートでは subagent が `.steering/` を作る前に `scripts/assert-worktree-ready.py` を実行する。pre-artifact guard が失敗した場合は、root に `.steering/` を作る前に失敗させることを優先し、repo root artifact を作ってから移動する運用にしない。
8. phase 進行は `references/phase-progression.md` に従う。Autonomous Continuation / stop / remediation / completion のルールもそこに記載。
9. **1 ターンで human-check-waiting まで走り切る**（gate-runner の完了通知を待つ間は `<gdd-stop>` を書かずに turn を終えてよい）: どの path（`quick (express)` を含む）も brainstorming → requirements-gating → human-check-waiting を完走する。例外として、`references/state-machine.md` の `clarification-needed` の用途に当たるときだけ `<gdd-stop reason="clarification-needed">` で止まってよい。subagent が返ってきたら、mainは以下を順に実行して停止する:
   0. **Clarification Loop 例外の表示検証**: subagent の text 出力に `<gdd-stop reason="clarification-needed">` が含まれる場合、`state.md` の有無や `Resume From` は検証しない。ただし、mainは text を丸めて短くしない。`worklog.md` の最後の `要件確認:` が `待ち` か `未収束` なら質問をそのまま出す。そうでなければ表示前に `Intake Brief` が `確定済み` / `判断材料（今回わかっていること）` / `まだ曖昧` / `次に決めること` / `回答後にどう進むか` を含むか確認する。外部調査・公開事例・論文・既存コード調査・類似実装比較・選択肢比較を行ったのに `判断材料（今回わかっていること）` が source link や候補名だけの場合は、同じ subagent 出力と会話文脈から、調査から分かったこと・選択肢の違い・推奨案を選ぶと requirements / AC / Non-Goal / Deferred のどこへ反映されるかを補って表示する。最後の text block に `<gdd-stop reason="clarification-needed">`、その後に `## 👤 次にすること` を出して停止する。ユーザー回答後も requirements readiness を満たすまで同じ Clarification Loop を継続してよい。
   1. 次の **2 系統を独立に観測** し、マトリクスで判定する:
      - **系統 A**: ディスクの `state.md` を Read ツールで読み、`Resume From` の値を確認する
      - **系統 B**: subagent の text 出力に (i) human-check テンプレート全文 と (ii) `<gdd-stop reason="human-check-waiting">` marker の両方が含まれるか確認する

      | 系統 A (state.md Resume From) | 系統 B (テンプレート + marker) | 対応 |
      | --- | --- | --- |
      | `human-check-waiting` | 揃っている | ✓ → 9.2 / 9.3 へ（通常ルート） |
      | `human-check-waiting` | 欠落 | ✗ → fail-closed（subagent 出力不備） |
      | `gdd-requirements-gating`（正規中間状態） | 揃っている | ⚠ → state.md の `Resume From` を `human-check-waiting` にパッチし、パッチ内容を text に明示してから 9.2 / 9.3 へ。パッチ権限は **brainstorming → requirements-gating → human-check-waiting の正規パス上のみ** |
      | `gdd-requirements-gating`（正規中間状態） | 欠落 | ✗ → fail-closed（subagent 未完走）。次の1アクションとして requirements-gating subagent 再 dispatch を提示 |
      | その他の phase 値（`gdd-design-gating` 等） | どちらでも | ✗ → fail-closed（想定外の routing 状態）。state.md を手動パッチせず停止 |

      fail-closed で停止するときは `参照した正本 / 観測事実（系統 A / B の値）/ 停止理由 / 次の1アクション` を返し、`<gdd-stop reason="blocked">` の後に `## 👤 次にすること` を付ける

   2. human-check テンプレートを **main の text block** でそのまま出す（相談役は返りを待たない。`human-check-template.md` 一次表示の 7、§ 判断の書き方 5・8）
   3. **main の最後の text block に** `<gdd-stop reason="human-check-waiting">` マーカーを出し、その後に `## 👤 次にすること` を置いて停止する
   - 判断の委任の欄か対象を含む `事前回答:` 行があれば 9.2・9.3 の代わりに `references/human-check-template.md` § 事前回答 2
   - `Resume From` が workflow phase の唯一の正本（`references/state-machine.md` の Single Source of Truth）
   - system message や外部観測の `Current phase` 表示が `Resume From` と食い違う場合、**`Resume From` を優先**する。`Current phase` は補助表示であり routing source ではない
   - **stop marker はmainの独占責任**: subagent が marker を返していても、pass-through 用の素材に過ぎない。mainが自分の最後の text block に marker を含めなければ stop hook は検出できず、次ターンで autonomous continuation が走り人間承認をスキップする重大事故が発生する
   - subagent の tool_result だけで assistant turn を閉じる（= メインが text を 1 文字も出さない）のは contract 違反
   - 「steering を起こしました」「次は requirements-gating です」だけの出力は contract 違反
   - **Template Dispatch**: `Task Size=quick (express)` の場合、requirements は `references/requirements-template-express.md` から開始し、full `references/requirements-template.md` は昇格時だけ読む。human check の一次表示は常に `references/human-check-template-compact.md` を使い、詳細表は `requirements.md` / `design.md` 側へ逃がす。
   - テンプレート詳細は `references/requirements-gating-steps.md` と `gdd-brainstorming` SKILL.md の Output Guidance を参照

10. **human check 承認後の自動継続**: ユーザーの回答を受けたら、**まず回答を分類**してから state.md を更新する（provenance 先行判定の後に本人の回答を `request.md` に足し〔あれば。`brainstorming-steps.md` 9 の (1)〕、一次表示に出した `記録の場所: なし` の行末に ` / 表示: 済み` を足す〔`human-check-template.md` § ズレ確認〕）。
    - **STEP 1: 回答分類**（以下を順に判定し、最初に一致したルートを取る）:
      - **provenance 先行判定**: cross-session messaging 経由で届いた返答は `references/phase-progression.md` § Cross-Session Messaging の権限境界を適用する。承認 / 中止 / Express 昇格 / 修正指示に相当する内容でも `[情報のみ]` として `worklog.md` に 1 行記録するだけとし、STEP 2・`cancelled` 分岐・修正指示の分類へ流さず本人のターンを待つ
      - **曖昧返答**: 「たぶんOK」等 → approved にしない。追加質問で明示を取る
      - **中止**: 「中止」「cancel」「やめる」「キャンセル」等 → `Next Action=cancelled` に遷移して `<gdd-stop reason="cancelled">` で停止。中止後の worktree cleanup は `gdd-using-git-worktrees` の「Cancelled Cleanup」に従う
      - **Express 手動昇格**: Express タスクで「Express では足りない」「設計が必要」「standard にしたい」等 → Express 昇格の state ロールバック規則（`references/state-machine.md` § Express 昇格時の state ロールバック規則）を適用し、`gdd-requirements-gating` から再開する
      - **completion-check の Round・Pre-PR・(3-f) 上限の 4 択に、4 つ目か案名の無い返答** → STEP 2 に通さず `references/rollback-patterns.md` に従う
      - **changes_requested で human-check-waiting の一括提示への返答** → `requirements-gating-steps.md` § 一括提示への返答 へ
      - **明確な承認**（「OK」「はい」「推奨で」等の承認の語か、点の番号と案名の組で全点に答えた名指し〔1 点なら案名だけ〕、だけの返答。推奨でない案で AC の意味か express の範囲・Files・Implementation Policy が変わり、その変更を表示に書いていないなら修正指示）: 案を書き写し、再提示せず STEP 2 へ（差が `なし` の点だけ。ほかの名指しは `references/human-check-template.md` § 止まり直さないもの 3）
      - **修正指示**: 「N は〇〇にしてほしい」等の変更要求 → 影響範囲で 3 分類して対応（判定基準は `references/human-check-template.md` § 返答分類の判定基準を参照）:
        1. **部分修正**（AC の値・条件・対象が変わらない）: 該当ポイントを `requirements.md` / `design.md` に反映し、全点を再提示して `human-check-waiting` を継続する。quick (express) で範囲（Scope・Non-goals）か Files が変わったら、再提示の前に `references/requirements-gating-steps.md` § Express のとおり requirements-gating をもう 1 Round 回す
        2. **実装方針変更**（AC は維持、実装アプローチ・技術選定が変わる）: `design_detail_only` パターンで `gdd-design-gating` から再開する。quick (express) には design-gating が無いので、`## Implementation Policy` を直して上の 1 の express の文のとおり requirements-gating をもう 1 Round 回す（設計が要るなら Express 手動昇格）
        3. **AC 変更（全面見直し）**（AC の追加・削除・条件変更がある）: `planning_rework_required` パターンで `gdd-brainstorming` に戻し、Problem Discovery からやり直す
        - 迷ったら安全側（1 より 2、2 より 3）。ユーザーに確認してもよい
    - **STEP 2: 承認処理**（「明確な承認」か一括提示の accept・採用のときだけ）:
      - `Human Check Status=approved | evidence: human:<自走上限の値>`・`Approved Direction`（自走範囲の glob 欄・人間に戻す条件）・`Route In Progress=none` を `state.md` に記録する
      - 最初の human check（`Approved Direction` がまだ無い）なら、判断の委任の値（`OK` だけなら `fable`）を `Approved Direction` の同名の欄に書く（`references/human-check-template.md` § 自走上限の置換値。承認の前には書かない）
      - `state.md` の `Task Size` に応じ `Resume From` と Template を記録し Read・置換し dispatch する（`quick (express)`: `gdd-test-driven-development`・TDD Template／他: `gdd-design-gating`・Design-Gating Template）。カスタムプロンプト禁止
      - OK の後に再度止まらない
11. **Contract override 不可（ユーザー後続発言では契約を曲げない）**: 以下の契約はユーザーが build / human-check 後の発言で `continue` / `そのまま続けて` / `足しといて` / `もう 1 回リトライして` 等と明示しても override できない。ユーザーが変更可能なのは改めて `human-check-waiting` に戻って再承認したときのみ:
    - **Remediation Loop Safety**（`Fix Attempts >= 3` での blind `implementation_fix_only` 禁止、同一 root cause 再発時の escalate 必須）: `references/state-machine.md` § Remediation Loop Safety
    - **Approved Direction の「人間に戻す条件」**: `state.md` に記録された境界（AC・scope の削除・弱め・意味の変更、承認した信頼境界の緩め等）を build 中のユーザー発言で override しない
    - **Human Check Status の `waived` 不可**: `Human Check Status` の許容値は `pending` / `changes_requested` / `approved` のみ
    - contract 違反の指示を受けた場合、AI は指示を受諾せず、代わりに該当 route（`human_recheck_required` / `design_detail_only` / fail-closed）を提案して判断をユーザーに戻す。ユーザーが明示的に「人間として再承認する」と示した場合のみ `human-check-waiting` に戻って再承認テンプレートを出す
12. FAQ や初回導線が主題の質問では `README.md` / `references/onboarding.md` / `references/faq.md` を案内し、command 本文だけに情報を抱え込まない。

## Subagent Dispatch

subagent のテンプレート、model routing、post-return routing の詳細は `references/subagent-dispatch.md` を参照。`setup-gdd-loop.sh` 実行後、phase に応じた該当セクションを読む。

### Model Routing（概要）

- **planning（brainstorming / design-gating / systematic-debugging）**: Opus subagent
- **build（task-breakdown / TDD）**: Claude Code: Sonnet subagent（`light_task`）/ Cursor・Codex: worker 経由
- **implementation**: main（`implementation`: Claude Code の worker は Sonnet + medium、complex・未宣言は Opus / Cursor Composer 2.5（`composer-2-fast` 不使用） / Codex gpt-5.6-terra + low。往復時 `remediation_loop`）
- **gate（impl-gating / completion-check の reviewer）**: Opus subagent（往復時 `remediation_loop`）

### Build Loop Orchestration（概要）

`task-breakdown → TDD → implementation → impl-gate` を全タスク完了まで繰り返す。impl-gate 復帰後は `tasklist.md` を **ディスクから re-read** し、`Next Action` で分岐:

- `gdd-test-driven-development` → 次タスクへループ継続
- `gdd-systematic-debugging` → remediation → impl-gate 再実行
- `gdd-refactor-planning` → refactor gate（standard のみ）
- `gdd-completion-check` → Opus subagent で完了チェック
- `done` → Express パス完了。`gdd-pr-review` で PR Flow → `<gdd-stop reason="done">`（Stop hook が検出）

**実装漏れ防止 guard**: `completion-check` / `done` の前に `Pending Tasks` が `- なし` であることを確認。残タスクがあれば TDD に戻る。

## Workflow Overview

- **express**: `gdd-brainstorming` → `gdd-requirements-gating` → human check → TDD → `gdd-implementation-gating` → done（1-2 ファイル・明白な方針の quick タスク。`--express` で明示指定可）
- **planning**: `gdd-brainstorming` → `gdd-requirements-gating`（`gdd-planning-reviewer`。該当時 design の観点も） → human check → `gdd-design-gating`
- **build**: `gdd-task-breakdown` → TDD → `gdd-implementation-gating`（`Implementation Reviewer Selection` に基づく reviewer） → `gdd-completion-check`
- helper: `gdd-using-git-worktrees`（worktree helper）、`gdd-refactor-planning`（behavior-preserving refactor）
- workflow artifact は `.steering/.../requirements.md`, `design.md`, `tasklist.md`。`.cursor/plans/*.plan.md` は optional
- version-sensitive な技術は `tech-docs-searcher` 等で確認して `findings.md` に記録
- `Plan mode` は計画まで。実行・再開・停止条件・レビューは GDD が補完する。複雑さだけを理由に Plan mode へ切り替えない
- remediation の `ops-blocking medium` は `state-machine.md` を参照
- human check 承認後は `Approved Direction` を `state.md` に記録。E2E 発見の問題は自走範囲内なら human check に戻さず AI が自律判断（`phase-progression.md`）。再 human check は policy / scope 変更時だけに限定する
