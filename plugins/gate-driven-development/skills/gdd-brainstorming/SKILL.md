---
name: gdd-brainstorming
description: "Use for /gdd-dev new-workflow intake before formal HITL, especially when requirements or completion criteria are unclear."
version: 0.1.0
---

# Brainstorming

`/gdd-dev` 開始時の最初の resolver。entry intent（`new` / `resume` / `ambiguous`）を解決し、formal workflow の canonical workspace である active worktree を準備または再利用したうえで、人間承認の正本となる `requirements.md` と human check 前の lightweight `design.md` skeleton を育てる。artifact/state を持たない相談専用レーンは `gdd-pre-workflow-brainstorming` が担当し、この skill は formal workflow に入った後だけ使う。

## Goal

- 「速く作る」より「正しく作る」を優先し、要件・実装方針・検証可能性・既存コード理解の正しさを初回 planning の成果にする
- **What / How Separation**: What（何を達成したいか、完了条件は何か）と How（どう実装・検証するか）を分け、両方を human check で判断できる形にする
- 曖昧さ・選択肢・スコープ・非スコープ・受入条件を整理し、human check で最初に読む `Summary Brief` を作る
- `requirements.md` に実装方針まで含め、requirements reviewer と人間が承認できる単位まで固め、human check 前に lightweight `design.md` skeleton を揃える
- 経路変更・owner 変更・sensitive data・masking・rollout/rollback を独立見出しに出す
- 未確定事項・Open Questions を自動的に解消し、human check に出せる品質まで詰める
- 要件が広い / 大きすぎる場合は、AI が 1 案に狭め切らず、選択肢・推奨案・分解単位を human check の承認ポイントに出す
- ユーザーが「現状よりシンプルに」「削除したい」「分散をなくしたい」「複雑さを下げたい」など **結果としての単純化** を求めた場合、実装方針だけでなく「何が減るか」を requirements の成果指標にする。追加 metadata / docs / guardrail だけで目的達成扱いにしない
- version-sensitive / fast-moving な利用技術の最新情報を確認し、planning に反映する
- 再開時だけ active steering を 1 つに解決する
- dedicated branch / worktree を canonical workspace として扱う
- UI / Web 画面を変更する場合は QA観点を要件化し、Playwright で確認する方針を `Verification Plan` に入れる。Playwright fallback minimum: 実行不可なら、実行不可理由、manual reproduction steps、screenshot or DOM evidence（locator text / accessible name / URL / timestamp）、console / network error check、対象 viewport / browser、未確認として残るリスク、人間に戻す条件を human check に出す。主要導線が確認できない場合は PR ready / done と言わない
- UI / Web 画面の依頼で **対象画面**、**検索対象**、**成功条件** のいずれかが曖昧な場合は、既存コード調査や worktree 作成の前に **Clarification Loop** を使う。代表画面を AI が推測して human check へ進めない。質問は「どの画面か」「何を検索するか」「何ができたら完了か」の最小 1-2 件に絞る
- `/gdd-dev` の開始・再開・amendment・active follow-up では、複雑さだけを理由に **Plan mode** へ切り替えない。active session 中の後続入力は `references/phase-progression.md` § Active Session Follow-up Classification で分類する

## Subsystem Decomposition Gate

superpowers `brainstorming` / `writing-plans` の scope decomposition を吸収する。複数の独立 subsystem（independent subsystem）を 1 つの steering に押し込まない。

**独立 subsystem とみなす条件**（1 つでも強く当てはまるなら検討必須）: 別々に ship / rollback / test できる / runtime / repository / service boundary / data model / owner が異なる / AC を共有せず、それぞれ単独の完了条件を持てる / 片方の失敗がもう片方の価値提供を妨げない。

該当する場合、requirements を確定する前に `Design Policy Discussion` へ **Subsystem Decomposition Gate** を置く。

```markdown
### Subsystem Decomposition Gate
- detected: yes
- units: <subsystem A> / <subsystem B> / ...
- recommendation: separate steering | phased single steering | first subsystem only
- first unit: <今回の GDD で着手する単位>
- deferred units: <別 steering または後続 phase に送る単位>
- human decision: <どの単位から始めるか / 1 steering にまとめる例外を認めるか>
```

原則は **separate steering** または **first subsystem only**。`phased single steering` は、同一 repository / 同一 runtime / 同一 AC family で、後続 phase が前 phase の成果物なしに検証不能な場合だけ使う。

## Baseline Verification Before Work

superpowers `using-git-worktrees` の baseline discipline を吸収する。worktree 準備後、requirements / human check を固める前に test / build / validate の基準状態を確認する。目的は「今回壊した failure」と「既存の failure」を分けること。This section records Baseline Verification Status in steering artifacts and the human-check summary.

`gdd-using-git-worktrees` で worktree を解決した後、repo の代表的な検証コマンド（例: `make test` / `npm test` / `pytest` / `tests/validate-plugin.sh` / project docs の verify command）を 1 つ選び、実行可否と結果を steering に記録する。重い full suite しかない場合は、最小 smoke / contract test を選んでよい。適切なコマンドを特定できない場合は、無理に実行せず `not_run` と理由を書く。

command selection priority:

1. リポジトリの明示手順（README / AGENTS.md / package scripts / Makefile / `tests/validate-plugin.sh` 等）
2. 変更対象に最も近い既存 contract / unit / smoke test
3. full suite が重すぎる場合の最小 smoke
4. どれも特定できない場合は `not_run` とし、未計測理由を書く

```markdown
### Baseline Verification Status
- command: <実行したコマンド。未実行なら not_run>
- status: pass | fail | not_run
- evidence: <出力の要点または未実行理由>
- interpretation: clean baseline | pre-existing failure | not measured
```

- `status=fail` の場合、その failure は **pre-existing failure** として扱い、TDD / implementation / completion で「今回の変更による新規 failure」と混同しない。
- `status=not_run` の場合も、なぜ測れなかったかを human check に出す。未計測を pass 扱いしない。
- baseline が fail していても要件整理は止めない。ただし AC / tasklist / HITL で「作業後に何を pass させるか」「既存 failure を今回直すか」を明示する。

## Fixed Model

- `Claude Code`: `opus`（`/gdd-dev` 経由時は Opus subagent として dispatch されるため、skill 内でのモデル切り替え判断は不要。`subagent-dispatch.md` § Brainstorming + Requirements-Gating 参照）
- `Cursor`: `Grok 4.6` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-sol` + `reasoning.effort=medium`（formal gate 扱い。risk signal がある場合は `high`）
- brainstorming + requirements-gating を同一ターンで完走するため、重いモデルを使う

## Model Routing

- モデル選択が曖昧なときは `gdd-model-routing` Skill を参照する。上記 model 名は host default の説明で、shared skill を両環境で使うときの最終判断は `gdd-model-routing` と `subagent-dispatch.md` を正本にする。
- この skill では `ultrathink` を使わない。

## Trigger Matrix

- 明示実行: `/gdd-dev`
- 再開: 既存 `gate-driven-development` steering があり、現在 phase を継続したい
- v1 非サポート:
  - generic な複雑タスク依頼だけを理由に、この skill を direct auto-trigger すること
  - 壁打ちだけの相談をこの skill で受けること
  - generic な creative work / feature idea / requirements clarification without `/gdd-dev` を受けること。formal brainstorming remains /gdd-dev only; use `gdd-pre-workflow-brainstorming` until explicit formal start

## Artifact Rule

- workflow artifact（この skill が作成するもの）: active worktree 側 `.steering/.../requirements.md` / `.steering/.../design.md`（lightweight skeleton）/ `.steering/.../state.md`
- workflow artifact（この skill では作成しない。後続フェーズが作成する）:
  - `tasklist.md` → `gdd-task-breakdown` が作成する。brainstorming で先行して作らない
- optional output: active worktree 側 `.steering/.../adr.md` / `.steering/.../findings.md` / `.cursor/plans/*.plan.md`
- Plan は **Plan mode** とは別物の補助成果物であり、ユーザーが明示的に比較案や壁打ちログの保存を求めたときだけ作る
- `adr.md` は重要な意思決定を残す任意の decision log で、必要になったときだけ作る。routing source や gate 条件にはしない

## Critical: 同一ターンで human-check-waiting まで走り切る

この skill は、正式な GDD workflow に入った後は **1 回の assistant turn の中で** `human-check-waiting` まで到達しなければならない。途中でターンを終了してはならない。

### Clarification Loop 例外（artifact 作成前）

入力が広い・曖昧・成功条件不足で AI が一発で仮決定すると scope を誤る可能性が高い場合は、Step 2a の **Clarification Loop** で artifact / worktree 作成前に要件を固める。固まるまでは requirements を作らず往復してよい。

特に UI / Web 画面・検索 UI・管理画面変更では、以下の 3 点が揃うまで human-check へ進めない:

- **対象画面**: どの画面・route・管理画面を変更するか（候補が複数なら人間に選んでもらう）
- **検索対象**: 名前、ID、ステータスなど、何を検索・絞り込みするか
- **成功条件**: 何ができたら完了か（例: 入力で結果が絞れる、空結果が表示される、リセットできる、Playwright で主要導線を確認できる）

- 停止時は `<gdd-stop reason="clarification-needed">` の後に `## 👤 次にすること` を置く
- 各往復で `Intake Brief`（確定済み / 未確定 / 次に決めること）を短く更新する
- 質問は scope / 成功条件 / 非スコープ / 優先度の確定に限定し、実装方式の細部は聞かない
- 一度に聞く量は、ユーザーがその場で判断できる最小量に絞る。readiness 全軸を一度に埋めようとせず、最も誤決定リスクが高い 1〜2 軸から聞く。足りなければ次の往復でさらに詰める
- この停止では `.steering/...`、`requirements.md`、`design.md`、`state.md` を作成しない
- ユーザー回答後は、回答を `$ARGUMENTS` に追記したものとして Step 1 から再評価する。ready criteria を満たせば同一ターン完走ルールに戻り、まだ曖昧なら継続する

### 途中停止禁止

- Clarification Loop と要件を固める確認（brainstorming-steps 9）以外では、**ユーザーに質問して assistant turn を終了しない**。未確定事項は AI が自律的に仮決定し、`requirements.md` に書き込む
- AI だけでは判断できない policy-level の事項は `Human Check Questions` に集約し、停止時にまとめて提示する
- artifact 作成後に「この点を確認してください」「どうしますか？」と聞いて止まるのは contract 違反
- artifact 初稿を作ったら Iterative Refinement Loop（Step 13）と Self-Review（Step 14）を完走し `Resume From=gdd-requirements-gating` に進める。初稿だけ作って止まらない

### 同一ターンで requirements-gating まで実行する

- brainstorming の全 Step を完了したら、**同じ assistant turn 内で** `gdd-requirements-gating` の処理も実行する。approved になったら同じ turn 内で `🔍 確認をお願いします` テンプレートを出力し `<gdd-stop reason="human-check-waiting">` で停止する
- 「次は requirements-gating です」「steering を起こしました」だけ出力してターンを終えるのは contract 違反
- **Express**: `quick (express)` も同じく requirements-gating を通ってから止まる（`references/requirements-gating-steps.md` § Express）。Express は `gdd-task-breakdown` もスキップするため、human check 承認後 TDD 開始前に `### Task: T-N` 形式で最小 tasklist.md を作成する（Step 7a-5e）。`- [x]` チェックボックス形式は session-start hook が進捗検出できないため使用禁止
- **Why**: Cursor など Stop hook が無い環境ではターン終了で autonomous continuation が動かない。hook の有無に関係なく 1 ターンで完走する

### 自律解決の判断基準

- 技術的な不明点（API 仕様、ライブラリの使い方）→ AI が調査して決定
- 設計トレードオフ（内部の上限値・バッチサイズ・retry 回数・接続プールサイズ等）→ AI が最もシンプルな案を採用し `Design Policy Discussion` に記録
- **ユーザー対向の機能的な数値上限**（「最大 N アカウント」「最大 M 件まで処理」「最大 K リージョン」のように、ユーザーが実際に処理できる量・スコープを直接制限するもの）→ ユーザーの実運用スケールは AI に知る術がないため `Human Check Questions` に集約する。技術的制約（API クォータ、Lambda メモリ上限、外部サービス rate limit 等）から客観的に導出される場合のみ AI が値を決定してよい
- ビジネスポリシー（権限、ロールアウト戦略）→ `Human Check Questions` に集約して一括確認
- 要件の広さ・方向性（「通知を改善」「運用を楽にする」「レビュー体験を良くする」等）→ **AI が勝手に単一 scope へ固定しない**。2-3 案（縮小案 / やらない案を含む）を `Design Policy Discussion` と human check の承認ポイントに出し、推奨案は示すが最終選択は人間に委ねる
- **価値ベースの scope 絞り込み確認（必須）**: 広い要件を検知したら、`Design Policy Discussion` に **Value-Based Scope Narrowing** セクションを作り、以下の構造で「価値が出る範囲で絞り込む選択肢」を **必ず明示提示** する。**Pre-option Scope Narrowing（明らかな nice-to-have の defer 落とし）は Value-Based Scope Narrowing の前段として実行**し、defer に落とした候補を Value-Based Scope Narrowing 冒頭に列挙する（並列ではなく逐次関係）:
  - **Option A（最小価値）**: 「N をやれば XX という価値が出る最小単位」 — keep / defer / 期待価値
  - **Option B（標準価値）**: 「N + M をやれば YY も達成できる単位」 — keep / defer / 期待価値
  - **Option C（やらない / 縮小）**: 「やらない判断 or さらに小さい単位」 — 何がトレードオフか / なぜこの選択肢があるか
  - 各 option に「期待価値（ユーザー / 運用 / 開発のどれに、どれくらい価値が出るか）」を明記（書き方は `references/human-check-template.md` § 判断の書き方）
  - **AI 推奨案を 1 つ示すが、最終選択は人間に委ねる**（「Option A を推奨、ただし最終判断はユーザー」）
  - human check の承認ポイントに **scope 選択** を独立項目として並べる（design / 実装方針と同じ階層）
  - **Why**: 「全部入り」案だけを提示すると、ユーザーは全部やる前提で承認し、後で手戻りが起きやすい。最小単位を Option A として必ず示すことで、価値レンジを意識的に選べるようにする
- 広い要件では **実装方式を考え込みすぎない**。brainstorming の責務は scope の選択肢と判断材料を出すことまで。ライブラリ選定・詳細設計・ファイル単位の実装計画は、採用 scope が人間承認された後の design-gating に送る
- 承認ポイントに載せる前に **Pre-option Scope Narrowing** を行う。明らかに後回しにできる nice-to-have / 将来拡張 / 横展開は先に `defer` へ落とし、最小の一貫した scope だけを `keep` にする
- 明示対象が無い広い要件では、AI が「代表」「利用頻度が高そう」と推測して keep を 1 つに決めない。`keep=<要人間選択: 候補...>` として、対象選択だけを human check に出す
- 明示対象が複数あり、どれが最小対象かを機械的に決められない場合も、AI が好みで片方を選ばない。`keep=<要人間選択: 明示対象...>` に戻す
- 大きすぎる要件では **分解が先**（§ Subsystem Decomposition Gate）。複数の独立 subsystem / user journey / rollout phase が含まれる場合、詳細を詰める前に「どの単位から始めるか」を 2-3 案で human check の承認ポイントに出す

## Steps

詳細な手順は `references/brainstorming-steps.md` を参照。概要:

1. `references/self-contained-contract.md` で entry intent / fail-closed 条件を確認する。`references/state-machine-overview.md` と `references/state-machine.md` は entry intent が `ambiguous` または fail-closed 判定の根拠が必要な場合のみ読む（通常の `new` / `resume` では読まない）
2. `references/entry-intent.md` に従い `new` / `resume` / `amendment` / `ambiguous` を判定する。`ambiguous` なら § Output Guidance の fail-closed 停止時の形で止まる
   - **`amendment` の判定条件**: マージ済みまたは実装済みの機能に対して追加要件・仕様変更・不具合修正が来た場合。以下のキーワードで検出する: 「追加要件」「仕様変更」「出力が違う」「これも対応して」「挙動がおかしい」「修正して」+ 既存機能名の言及
   - `amendment` は `gdd-requirements-amendment` に委譲する。active GDD 中の follow-up で AC の追加・削除・条件変更・意味変更が疑われる場合も、別 Plan を作らず同 skill へ
   - **`new` と判定した場合の即時ルール**: `gdd-dev.local.md` に既存 steering candidate が列挙されていても、それらのパス（`requirements.md` / `design.md` / `state.md` / `tasklist.md`）を Read しない。`docs/learned-patterns.md` のみ例外。このルールは Step 9 以降でも維持する
   - **Entry Intent 永続化（必須）**: 判定結果を `state.md` 作成時（Step 5 以降）に **`Entry Intent` セクション** として **必ず記録する**。テンプレートは `references/requirements-template.md` § Entry Intent テンプレート。`判定` / `判定理由` / `参照した正本` / `判定日時` の 4 項目を必須記載。`amendment` 判定時は判定理由に `anchor=<既存 feature / artifact 名>` を必ず含める。**Why**: 後続 phase（completion-check / reviewer / pr-review）が「なぜこの phase 構成になっているか」を再判定なしに参照できる。state machine 一体型 brainstorming の構造保証
   - **2a. Clarification Loop**: `new` かつ入力不足なら `references/brainstorming-steps.md` § 2a の判定を行う。該当時は requirements を作らず停止し、ready criteria を満たしたら Step 3 へ進む（詳細は § Clarification Loop 例外）
3. `resume` なら git worktree 列挙で active steering candidate を 1 つに絞る。同一優先順位に複数あれば `候補一覧` を返して停止。legacy root steering は `legacy migration` を検討
4. worktree 解決は `gdd-using-git-worktrees` の helper 契約に従う。helper が返した `Baseline Verification Status`（`baseline_command` / `pass` / `fail` / `not_run`）を `requirements.md` の Summary Brief または `state.md` Notes に記録し、human check にも出す
5. `.steering/YYYYMMDD-short-title/` を決める
6. 運用レベルを解決する。優先順位: ユーザー明示（`--level`） > リポジトリ設定（`.gdd-config.md` の `Operation Level`） > デフォルト（`standard`）。詳細は `references/operation-levels.md`
7. タスク規模を `trivial` / `quick (express)` / `quick (standard)` / `standard` で判定する（`references/task-sizing.md`）。`scripts/suggest-task-size.sh` でキーワード・diff ベースの自動提案を得られる。運用レベルに応じて gate / reviewer の適用範囲が変わる（`references/operation-levels.md`）。`trivial` の場合は最小 `state.md` を作成し（Step 7t）、artifact を作らず直接変更を実施して完了する（step 8 以降は skip）。`quick (standard)` の場合は **即座に最小 `state.md` を作成し**（Step 7s）、brainstorming 中断時のセッション復帰を保証してから step 8 以降に進む。`quick (express)` の場合は **Direct Intent 判定**（`references/brainstorming-steps.md` § 7b）を行い、Express Path（§ 7a）に進む。Direct Intent 判定でユーザー入力が十分具体的と判断されれば Options Exploration と Iterative Refinement Loop を skip し、brainstorming を高速化する
   - **ワークフロー適合判定**: `GDD formal workflow` / `standalone route` / `superpowers sufficient` を仮判定する。AC ID、state machine、Reviewer Lineage、PR/Release gate が必要なら GDD formal workflow。artifact-less な壁打ち・単発 debug / refactor で state machine 連動が不要なら standalone route または superpowers sufficient とし、HITL 前に理由を短く出す
8. 具体的な技術名が明示された場合のみ、version-sensitive なものに絞って `tech-docs-searcher` 等で最新情報を確認し `findings.md` / `Open Questions` に残す。外部 API 連携・認証フロー等では `similar-case-researcher` で類似事例を調査し `findings.md` に記録する
   8a. **外部 API 統合チェック（External API Integration Check）**: 外部 API の応答の形・認証・レート制限・ページングを `外部依存の確認結果` に、未解決を `Open Questions` に書く。AC か design が外部の形式（API 応答・通知・Webhook・ログ書式など）の欄の位置や値の形に依存するなら、AC を書く前に**外部形式の実測**をする（`references/brainstorming-steps.md` § 8a）
     8b. **Runtime 環境変数の依存（Runtime Environment Variable Dependencies）**: 新しいスキルや機能が Runtime 環境変数を必要とする場合、以下を `requirements.md` に明記する:
   - 環境変数名・用途・取得元 / IaC（Terraform `agent_runtime_env` 等）への反映先 / 必要な IAM 権限（`secretsmanager:GetSecretValue` / `ssm:GetParameter` 等）
     8c. **Migration / Conversion タスク判定**: 別フォーマットへの変換タスク（`.md` → `.yml`、JSON → YAML、table markup → form field 等）では、`受入条件` に「原文保全」「変換先ネイティブ機能の活用」「content-diff 検証手段」「レンダリング / 実動作の目視確認」の 4 件を必須 AC として追加する（詳細: `references/brainstorming-steps.md` § 8c）
     8d. **IDE 互換性チェック**: skill / hook / plugin / slash command / `settings.json` / `.claude/` 配下を新規作成・変更する場合、Claude Code と Cursor 両環境での動作可否・環境変数依存・静的指示による代替を `受入条件` に明示する（詳細: `references/brainstorming-steps.md` § 8d）
9. **Problem Discovery（問題の掘り下げ）**: requirements.md を書き始める前に、以下を必ず実施する（詳細は `references/brainstorming-steps.md` § 9）:
   - **`docs/learned-patterns.md` を読む**（存在する場合）: worktree 内の task 固有ディレクトリではなく **リポジトリルート**（`main` が `checkout` された作業ディレクトリ）が対象。類似の過去判断・却下済み代替案を先に確認する
   - **要件に登場する全パスの存在確認**: 要件に登場するディレクトリ・ファイル・モジュールを `Glob` / `ls` で確認し、各パスを「既存」「新規作成」「不明」に分類する。「存在するはず」の前提で requirements を書かない。分類ルール: (a) 既存パス → 実在を確認してから要件化。(b) 新規作成パス → 要件に「新規作成」と明示して続行。(c) 存在するはずなのに見つからないパス → `Human Check Questions` に集約してターンを継続（ユーザーへの質問でターンを終了しない；該当箇所の要件化は Human Check 回答を待ち、他パスの requirements 記述は続ける）。混在シナリオでは各パスを (a)/(b)/(c) に個別分類し、(c) の保留が (b) の続行をブロックしない
   - **現状の把握**: 変更対象を読み、対象シナリオが現在どう処理されるかを動作の視点で確認する（`references/brainstorming-steps.md` § 9 § 現状の把握）
   - **依頼と既存コードの突き合わせ**: `brainstorming-steps.md` § 9 のとおり `request.md` と `request-crosscheck.md` を作る
   - **Pre-HITL Codebase Survey**: repo 構造、関連ファイル、類似実装、read / write / persistence / API / MCP / wrapper / adapter 経路、tests / contracts、docs、policy 境界を調査し、調査ログは `findings.md` に残す。ユーザーが「既存コードがあるはず」と示した場合や、読み書き・保存・投稿・検索・外部連携を含む場合は **Read/Write Surface Survey** を必須にし、新規機構より既存経路の再利用可否を先に確認する。必須 surface 未調査のまま human-check に進めない
   - **アーキテクチャ・依存関係の確認**: 初回設計前に architecture / code structure / dependency / runtime / install / test / CI を確認する（調査ログは `findings.md`）。既存 repo は Follow / Fit + Small Refactor / Reshape を判定し、採用する構造判断は `実装方針`（policy-level なら human check の `アーキテクチャ提案`）に結論だけ出す。runtime / deploy / owner / credential boundary が変わる候補は policy-level 判断
   - **選択肢の比較**: architecture / CI / IaC policy / runtime / framework / test tooling / access method / credential backend の選定で複数の妥当な選択肢がある場合、AI が勝手に単一案へ丸めない。既存 repo 標準、業界標準 / vendor official、最小の自前実装を比較し、採用案・却下理由・人間に確認する点を承認ポイントに出せる粒度で整理する（詳細比較は `findings.md`）。非標準な自前実装を採る場合は必ず policy-level 判断にする
   - **Why の言語化**: なぜ必要かを 1-2 文で書き出す
   - **外部依存コンポーネントの実動作調査**: 要件に「X のログから参照」「Y の出力を記録」「Z と突合」等が含まれる場合、そのコンポーネントのコードを読んで動作を確認する（非同期/同期の別、実際のフィールド名、記録タイミング等）。「取得できるはず」の前提で要件化しない（詳細トリガー・調査強度: `references/brainstorming-steps.md` § 9 § 外部依存コンポーネントの実動作調査）
   - **影響範囲の事前スキャン**: 変更が影響しそうなファイル・モジュールを `grep` / `glob` で特定する。**既存の同種コンポーネントと同カテゴリのリソースを新規追加する場合（IAM ロール、API エンドポイント、StackSets テンプレート、認証フロー等）、既存インスタンスのセキュリティ設定を確認し、新規追加分が既存より弱い保護にならないことを検証する。弱い場合は `受入条件` に「既存と同等以上の保護を持つこと」を追加するか `Human Check Questions` で正当化を求める。** Why: 既存が暗黙のセキュリティ下限になり、新規追加時の水準低下は設計者自身が気づきにくい
   - **Simplification Outcome Check**: ユーザーの意図が「シンプル化 / 中央集約 / 分散削減 / 複雑さを下げる / 重複削除 / 責務整理」である場合、現状の複雑さを具体的に数える（例: prompt assembly の実装箇所、分岐数、責務重複、削除候補）。`requirements.md` の AC に「削除または統合されるもの」「残す互換分岐の理由」「削除できない場合の説明責任」を入れる。**Why:** 境界の明文化だけでは期待したコード削減や責務整理が起きない。複雑さの減り方を AC 化しないと、追加実装だけで完了してしまう
   - **Reliability-only exception**: 「堅牢化 / fail-closed / guardrail / validation」だけが目的で、複雑さ削減が明示されていない場合は Simplification Outcome Check を必須にしない。信頼性向上は validation や guardrail 追加が正しいこともあるため、削除 AC を無理に作らない
   - **Scope Reduction Check**: 終盤に要件縮小の可能性を 1 回検討し、縮小候補は Approach C または `Human Check Questions` に記録する（質問で止まらない）
10. **Options Exploration（選択肢の提示）**: standard タスクでは 2-3 の選択肢（「やらない」案含む）を比較し、方向性が決まったら実装方式の候補を洗い出して比較表を `Design Policy Discussion` に記録する。quick では省略可。**UI/UX 変更・出力フォーマット変更を含む場合**（画面設計・通知メッセージ・wiki / Slack / GitHub 等への出力フォーマット変更）は、各 Approach に ASCII mockup / Before-After サンプル等の **視覚的叩き台** を必ず添え、mockup の採用案を human check の承認ポイントに昇格させる（**Visual Companion**）。発火条件・採用形式・skip 条件の詳細は `references/brainstorming-steps.md` § Step 10 § Visual Companion
11. `requirements.md`（サイズ別テンプレート dispatch）と lightweight `design.md` skeleton を育てる。`quick (express)` は **`references/requirements-template-express.md` から開始し、full `references/requirements-template.md` を読んで埋め始めない**。express template に無い Stage / design detail が要る場合だけ `quick (standard)` へ昇格して full template を読む（`quick (standard)` / `standard` は full template）。`Summary Brief` は **3 層構造 + Honest Limitations**（`一言` / `判断材料`: 確定事項・未確定事項・やらないこと・外部依存の確認結果・設計方針 / `承認ポイント`: 背景・変更前→変更後・採用案/代替案・方向性承認 / `Honest Limitations`: この設計で確認できないこと）を冒頭に置く（standard は Honest Limitations 必須、quick は任意）。`Design Policy Discussion` で設計方針の候補を整理。requirements の節構成（常設 11 節 + 条件付き節）と design.md skeleton の節・粒度は `references/requirements-template.md` に従う。entry intent 判定は `条件` / `見る入力` / `出力または次アクション` / `不足時の扱い` で記述（`unknown -> needs_input`）
    11a. **Complexity Evaluation** (steps.md Step 12a): 初稿後に `references/task-sizing.md` § 正式判定: Complexity Evaluation で 5 次元を評価し、暫定 sizing を確認・昇格する
12. `Gate Status` 初期値を `state.md` に設定する (steps.md Step 13): `Requirements Review Status=pending` / `Design Review Status=pending` / `Human Check Status=pending` / `Resume From=gdd-brainstorming`
13. **Iterative Refinement Loop（自律解決）** (steps.md Step 16): artifact 初稿の後、未確定事項・Open Questions・曖昧な AC・不足セクションを **AI が自律的に解決** する。ユーザーに質問して止まらない。Gap Scan → Self-Resolve → Update → Re-scan を未解決 0 件まで繰り返す（最大 3 回）。policy-level の事項は § 途中停止禁止 のとおり
14. Self-Review (steps.md Step 17) を通過したら `Resume From=gdd-requirements-gating` に更新する（`Resume From=human-check-waiting` には直接進まない）
    - ⚠ **中間状態注意**: 更新後、**ここで停止しない**（§ 同一ターンで requirements-gating まで実行する）。`gdd-requirements-gating` のまま停止するのは contract 違反
15. **Exit Decision（必須）**: Step 13 / Step 14 を経た後、要件として実施する価値があるかを内部判定し、3 経路に振り分ける。`/gdd-dev` 投入即破棄（artifact だけ残って放置）を防ぐゲート。
    - **判定軸**:
      1. `Why` が明確に言語化できているか（曖昧 / 既存機能で代替可 → discard 候補）
      2. AC が測定可能で、reviewer / 人間が pass/fail を判定できる粒度か（不可 → refine 候補）
      3. 影響範囲が repo の他作業や進行中の steering と矛盾しないか（矛盾 → refine 候補で human check 質問へ）
      4. 実装コストが現状の優先度と釣り合うか（割に合わない → discard 候補）
    - **3 経路**:
      - `proceed`: 通常パス。`Resume From=gdd-requirements-gating` に進む（Step 14 の通常遷移）
      - `refine`: 上記 1〜4 のうち 1 つでも未充足。Iterative Refinement Loop に戻り、不足を埋めてから再判定する（最大 3 周）
      - `discard`: 上記 1〜4 のうち 2 つ以上が未充足、またはユーザーが「やらない」「discard」「中止」を明示した場合。以下を実施して fail-closed 停止する:
        1. `state.md` を `Resume From: cancelled` / `Next Action: cancelled` に書き換える
        2. `requirements.md` 冒頭に `Status: Discarded` と discard 理由を追記する（artifact は削除しない）
        3. `docs/learned-patterns.md` に「discard 判断の理由」を 1 entry 追記する
        4. worktree cleanup を提案する（`gdd-using-git-worktrees` の Cancelled Cleanup に従い keep / archive / discard の 3 択）
        5. `<gdd-stop reason="cancelled">` で停止する（`human-check-waiting` には進まない）
    - **Why:** discard 経路を閉じないと `/gdd-dev` の試し投げで `.steering/<task>/` が放置され、active steering 数が膨らんで後続 session の routing を撹乱する。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを冒頭に付ける
- **Formal Handoff Progress Note**: pre-workflow / 相談レーンから「GDDで実装計画を作って」「正式に進めたい」などの Go サインで入った直後は、重い worktree / steering 探索を始める前に 1 文で次に出るものを示す。例: `ここから formal GDD に入ります。次に worktree を確定し、requirements.md / lightweight design.md を作成して human check を出します。` worktree 探索や baseline 検証で時間がかかる場合も、この案内を先に出す
- **Clarification Loop 停止時**: これは fail-closed ではなく artifact 作成前の intake 待ちである。`Intake Brief`（確定済み / まだ曖昧 / 次に決めること）と次の質問を出し、`<gdd-stop reason="clarification-needed">` とその後の `## 👤 次にすること` を付けて停止する。**前回と同一内容の質問を再掲しない**: 進展がなければ、前置き 3 行（`human-check-template.md` § 判断の書き方 2）と、待っている問いを出し直す
- **サブエージェント dispatch 後の待機（No Manual Polling）**: background で dispatch したら `<gdd-stop>` を書かずに turn を終えて完了通知を待つ（`blocked` は loop state を消す）。`find` / `ls` 等での手動ポーリングを繰り返さない
- **human-check-waiting 停止時**: 一次表示は `references/human-check-template-compact.md` を使い、詳細の WHY → WHAT → HOW は `requirements.md` の中でこの順に読めるようにする。full `references/human-check-template.md` は返答分類・詳細 trace・例外ルールの正本として必要時だけ参照し、人間へ最初に出す本文へ長い表を貼らない。置換後の compact output を出し、**`<gdd-stop reason="human-check-waiting">`** マーカーとその後の `## 👤 次にすること` を付けて停止する。`Origin Session` 有時の起動元通知は `references/phase-progression.md` § Cross-Session Messaging に従う
- 初回 human check では、要件・方向性だけでなく **自走上限**（値は human-check-template § 自走上限の置換値）を必ず承認ポイントに含める。ユーザーの `OK` はこの上限までの自走承認として扱い、上限を超える PR merge / deploy / 本番 write 操作は止める
- **fail-closed 停止時（`ambiguous` 等）**: `参照した正本` / `停止理由` / `次の1アクション` を出力し、`<gdd-stop reason="blocked">` と `## 👤 次にすること` で止まる（`discard` は上のとおり `cancelled`）
- 「requirements.md を確認してください」「steering を起こしました」だけの出力は contract 違反（template.md § 必須ルール）
- **承認後の即時継続**: 全承認ポイント（差 `なし`）に「OK」で回答されたら追加確認なしに即座に `gdd-design-gating`（express なら `gdd-test-driven-development`）へ進む。「OK なら進めます」で止まるのは contract 違反
- **回答パターン別処理**:
  1. **全 OK** → 即時継続
  2. **一部変更**（「N は〇〇にしてほしい」等。案の名指しは変更要求ではない。`commands/gdd-dev.md` #10 STEP 1）→ 該当箇所を反映し、全点を再提示して `<gdd-stop reason="human-check-waiting">` で停止。全 OK になるまでループ
     - **Sizing 再評価 trigger**: 修正反映後、以下のいずれかに該当した場合は再提示の前に Complexity Evaluation を再実行し、sizing 昇格を検討する（express は、範囲・Files・`## Implementation Policy` が変わったら requirements-gating をもう 1 Round 初回と同じ扱いで回し、AC が変わったら brainstorming に戻す。`references/requirements-gating-steps.md` § Express）：
       - (a) AC 数が +2 以上 または +50% 以上 増加した（同一の事象を複数フォーマット・方法で検出する variant は sub-condition として 1 AC にまとめる；別の事象を対象にする条件は独立 AC）
       - (b) 独立した検出パターン・条件カテゴリ・分岐ルールが +1 以上 増加した
       - (c) 新規の外部依存・他コンポーネント影響・Python/IaC 変更が判明した
       - (d) AI が「却下した代替案」を 2 件以上書く必要が生じた（≒ 設計判断が選択肢相当）
     - 詳細: `references/brainstorming-steps.md` § 要件変更時の再評価 trigger
  3. **全面見直し** → `Resume From=gdd-brainstorming` に戻し Problem Discovery からやり直す

## Transition Rules（formal ⇄ pre-workflow の切り替え）

formal workflow の途中でユーザーが「相談に戻したい」と意図を変えた場合の手順（`references/skill-responsibility-matrix.md` § Pair 2 と整合）。pre-workflow → formal の upgrade は `gdd-pre-workflow-brainstorming` 側に記載。

### downgrade: `gdd-brainstorming` → pre-workflow（正式 → 相談）

**契機**: formal workflow 中にユーザーが「相談だけに戻したい」「実装やめて整理しなおしたい」「pre-workflow に戻したい」と明示した。

**auto-downgrade 禁止**: `.steering/<slug>/` の artifact が既にある状態で勝手に pre-workflow に戻すと state が dirty になる。必ず人間に確認する。

**手順**:

1. **3 択をユーザーに提示**:
   - `discard`: artifact を削除して pre-workflow に戻る（やり直し前提）
   - `archive`: `.steering/<slug>-archived-YYYYMMDD/` にリネームし、その `state.md` の `Resume From` と `Next Action` をどちらも `cancelled` にして pre-workflow に戻る
   - `continue`: pre-workflow に切り替えず、本 skill の中で会話モードを継続する（state を残す）
2. ユーザー選択を待つ（auto-select しない）
3. `discard` / `archive` 選択時の worktree / branch 処理は `gdd-using-git-worktrees` § Cancelled Cleanup に委譲する
4. `continue` 選択時は `gdd-pre-workflow-brainstorming` を起動せず、本 skill の中で軽い会話モードに戻る

この downgrade は明示指示でのみ受け付ける。曖昧な発言（「ちょっと待って」等）では実行せず、まず内容を確認する。

### 同時並行の禁止

同じ slug / 同じ worktree で `gdd-pre-workflow-brainstorming` と本 skill を並行起動しない。並行が疑われる場合は fail-closed で停止する。判断材料は `references/entry-intent.md` と `references/skill-responsibility-matrix.md` § Pair 2。

## Rationalization Check（この skill 固有）

brainstorming を短絡したくなる思考パターン。`Why` 列のラベルは `references/rationalization-root-causes.md`、全体向けは `references/common-guardrails.md` § 合理化防止テーブルを参照。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「ユーザーの指示が具体的だから Options Exploration は不要」 | Direct Intent Shortcut（Step 7b）が正式に短縮を許すケース以外、代替案比較は暗黙の前提を炙り出す | [Curse of Knowledge] 「具体的」と感じるのは説明者側の脳内モデルが豊富だから。受信側に同じ前提があるとは限らない |
| 「要件が広いので AI が良さそうな scope に切ればよい」 | 広い要件ほど方向性の選択が人間責任になる。選択肢・縮小案・推奨案を human check に出し、AI は根拠を添える | [Locus of Control Drift] scope 判断を AI に委ねると、承認後の覆しコストが急上昇する |
| 「広いが、考えれば実装案まで作れそう」 | 実装案を作り込むほど scope が既成事実化する。広い段階では scope 比較だけに留め、実装方式は承認後の design-gating に送る | [Scope Creep Justification] 作り込みは「既に投資した」シグナルになり、scope 削減判断が歪む |
| 「広いので全部を承認ポイントに並べよう」 | 承認ポイント化の前に scope を削る。明らかな nice-to-have / 横展開 / 将来拡張は defer し、最小 scope だけを承認対象にする | [Planning Fallacy] 全部入りで見積もると best case に近い印象を与え、人間が誤った承認をする |
| 「対象が未指定なので代表を AI が選ぶ」 | 代表選定も scope 判断。機械的に 1 つへ絞れる根拠がなければ、対象候補だけを human check で選ばせる | [Locus of Control Drift] 代表選定を AI に渡すと、後で「別の対象だった」と言われたとき再走になる |
| 「明示対象が複数あるので AI が片方を選ぶ」 | 依存関係・単独検証性で機械的に最小対象を決められないなら、人間に対象選択を戻す | [Locus of Control Drift] 同上 |
| 「大きいが、全部まとめて requirements にできる」 | 大きすぎる task は実装計画ではなく分解が必要。sub-project / phase に切り、最初の単位だけを GDD task として承認に出す | [Planning Fallacy] 大きい task は楽観的見積もりが効きやすく、実測との差が拡大する |
| 「変更が小さいから design.md は不要」 | skeleton だけでも必ず作る。小さい変更ほど AC の曖昧さが後で効いてくる | [Curse of Knowledge] 自分にとって小さい変更も、reviewer や保守者には文脈が無い |
| 「Problem Discovery は形式的、既存コードは知ってる」 | 既存コードの前提は時間と共にズレる。Step 9 の具体的事実確認は reviewer 差し戻しの最大の防御線 | [Recency Bias] 直近見たコードを「現状の正解」と思い込み、その後の変更を見落とす |
| 「中央集約したので追加 metadata を出せば十分」 | ユーザーの目的がシンプル化なら、追加だけでは目的未達の可能性が高い。削除・統合・残す理由を AC と検証に入れる | [Confirmation Bias] 目的を「達成済み」と読み替える証拠だけ集めて、削除責務をスルーする |
| 「対象ディレクトリは存在するはずだから確認不要」 | 実在しないパスへの要件化が planning_rework_required を引き起こす。Glob で 10 秒の確認が数時間の手戻りを防ぐ | [Curse of Knowledge] 自分の頭の中の構造をリポジトリ実体と同一視する |
| 「外部コンポーネントの動作はドキュメントで十分」 | async/sync の別、実際のフィールド名、記録タイミングはコードを読まないと分からない。「出力を記録できるはず」前提の要件は rework になる | [Curse of Knowledge] ドキュメントは説明者の理解レベルで止まる。実装の細部はコードにしか無い |
| 「Open Questions に残しておけば human check で聞ける」 | scope / 方針レベルの questions は Self-Review 前に埋める。未確定のまま gate に渡すと reviewer がブロックする | [Locus of Control Drift] 判断を human check に丸投げすると、人間が再起動コストを払うことになる |
| 「worktree を切らなくても作業できる」 | 既存ブランチに `.steering/` を作ると別タスクの state と混ざる。fail-closed で停止し worktree を先に切る | [Bias for Action] 着手を急いで分離コストを後回しにすると、後で state 混入を解くコストが跳ね上がる |
| 「上限値は設計トレードオフだから AI が決める」              | ユーザーが処理できる量（アカウント数・件数・リージョン数等）を制限する上限はスコープの判断。技術的制約から客観的に導出されない場合は Human Check Questions に出す |
| 「新規追加なので既存とは独立した設計でよい」               | 同種のコンポーネントを追加するとき、既存インスタンスのセキュリティ設定が暗黙の下限になる。新規追加が既存より弱い保護になっていないか影響範囲スキャン時に確認する |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、承認見出しルール、blocking Open Questions、最新情報確認、fail-closed 応答）。以下はこの skill 固有のルール。

- worktree が確定していない状態で Step 5 以降（`.steering/` 作成）に進まない。worktree 作成に失敗した場合は fail-closed で停止し、root directory に `.steering/` を作って代替しない
- **Entry Intent を `state.md` に永続化していない状態で次 phase に進まない**。`state.md` 作成時に `Entry Intent` セクション（判定 / 判定理由 / 参照した正本 / 判定日時）を必ず記録する（state machine 一体型 brainstorming の構造保証）
- **広い要件で Value-Based Scope Narrowing を省略しない**。`Broad Requirement: true` または「対象が複数」「方向性のみ示された」要件では、`Design Policy Discussion` に Option A（最小価値）/ Option B（標準価値）/ Option C（やらない / 縮小）の 3 案 + 各 option の期待価値を必ず明示し、scope 選択を human check の独立承認ポイントに並べる。AI が「全部入り」「代表 1 つ」だけ提示して承認を取らない（自律解決の判断基準 § 価値ベースの scope 絞り込み確認 参照）
- **新規タスクの worktree**: `new` の場合、`main`（またはデフォルトブランチ）から新しい worktree を切ってから `.steering/` を作成する。dirty な作業ディレクトリや既存の別タスクブランチの上に `.steering/` を作らない
- **Anti-Pattern: "シンプルだから設計不要"**: 変更が小さいことを理由に `requirements.md` と `design.md` の作成を省略しない。内容が数行でもよいが、skeleton は必ず作る。「明らかに単純」に見えるタスクでも、AC が曖昧なままでは実装判断と reviewer 判定がブレる
- `tasklist.md` を brainstorming で作成しない。実装順・タスク分割は `gdd-task-breakdown` の責務であり、brainstorming が先行して書くと design-gating の判断を歪める
- `requirements.md` と lightweight `design.md` が無いまま task 分割や実装に進まない。ただし `quick (express)` は Express Path の正規例外として `design.md` 不要
- 代表例は `受入条件` または `検証ヒント` の箇条書き内に書き、独立した `Examples` セクションを増やさない
- stopped workflow の review 差し戻しを、新規 task 扱いにして worktree を切り直さない
- resume cue の無い明示的新規 task を、途中で止まっている既存 steering に吸わせない
- **新規タスクの steering 隔離（intent=new の必須ルール）**: `intent=new` と判定したら、他タスクの steering ファイルを **一切 Read しない**。`gdd-dev.local.md` に既存 steering candidate のパスが「for reference only」として列挙されていても、それらの `requirements.md` / `design.md` / `state.md` / `tasklist.md` を開いてはならない。唯一の例外は cross-task learning 正本の `docs/learned-patterns.md`。**Why**: 旧タスクの文脈混入で要件定義が汚染され、誤った実装方針が採用されうる。「参照するだけ」は不十分
- human check 前に `design.md` の詳細を完成品扱いしない
- 広い要件 / 複数の合理的 scope がある要件で `Design Policy Discussion` と human check 承認ポイントを省略しない。AI 推奨案だけを書いて実装 scope を確定しない
- `Broad Requirement: true` の間は、実装方式比較・詳細設計・ファイル単位の変更計画を作り込まない。scope 選択に必要な制約確認を超える調査は design-gating に送る
- `Broad Requirement: true` では、Options Exploration の前に `Scope Narrowing`（keep / defer / reason / reopen trigger）を作る。最小 scope が 1 つに絞れた場合は、A/B/C 比較を無理に増やさず、narrowing の妥当性を human check で確認する
- `Scope Narrowing` の keep は、ユーザー明示対象または機械的に絞れる対象だけにする。根拠なく代表 scope を AI が仮決定しない
- 明示対象が複数ある場合でも、最小対象を機械的に決められないなら `keep=<要人間選択: ...>` とする
- 複数 subsystem / phase を含む大きすぎる要件では、全体を 1 つの requirements に詰め込まない。分解案と最初の着手単位を human check に出す
- `未確定事項` や `Open Questions` にスコープ・方針レベルの項目を残したまま Self-Review に進まない
- Iterative Refinement Loop を skip して artifact 初稿のまま requirements-gating に渡さない
- 調査操作を 2 回行ったら `findings.md` に知見を書き出す（詳細は `references/brainstorming-steps.md` Step 15）
- **ユーザー対向の数値上限はポリシー判断**: `max_accounts`・`max_results`・`max_files` 等ユーザーが直接体感する上限は、内部実装の技術上限（バッチサイズ、DB クエリ LIMIT 等）と混同しない。ユーザーの実運用スケールが不明な場合、AI が推測した値を `Design Policy Discussion` に記録しつつ、同じ値を `Human Check Questions` にも列挙してユーザー確認を取る
