---
name: gdd-requirements-gating
description: "Internal: auto-routed only when Next Action=gdd-requirements-gating. Prepares requirements for HITL."
version: 0.4.0
---

# Requirements Gating

human check の前に、requirements reviewer で `requirements.md` と lightweight `design.md` skeleton の品質を固める。状態遷移の概要は `references/state-machine-overview.md`、詳細な遷移表は `references/state-machine.md` を参照。

## 精度の第一原則

出荷物の品質はテストと implementation-gating が担保する。この gate が高精度で守るのは **人間の承認判断に使う箇所**（承認ポイント・スコープ・安全境界）と **AC の意味**（テストの正本）だけ。それ以外の記述の詳細化・網羅化を gate で追わない。

- **blocking にできる指摘は「AC の意味・スコープ・承認ポイント・安全境界（破壊的操作・秘匿・不可逆）」に影響するものだけ**。それ以外は advisory。severity・category・reviewer の観点では決めない（正本: `references/requirements-gating-steps.md` § 精度の第一原則）
- **レビューループの契約**（正本: `references/requirements-gating-steps.md` § レビューループの契約）: 初回 + **再入は 1 回まで**。Round は `reviews.md` で数え、**記録がなければ上限超過扱い**で AI が閉じない blocking を人間へ一括提示する。再入レビューは差分スコープ。レビュー記録は `reviews.md` へ分離し、requirements.md に積まない

## GDD Complexity Budget

HITL 作成時は easy summary を先に出し、GDD Complexity Budget を確認する。内部用語数、HITL行数、承認ポイント数、正本重複、似たルールの重複が超過していれば、判断に効かない段落を外して内部用語を説明する（`references/human-check-template.md` § 判断の書き方）。一次表示に置くもの（冒頭の前置き 3 行を含む）は `references/human-check-template.md` § 一次表示の原則 に従う。

**重要**: この skill は `gdd-brainstorming` と **同一 assistant turn 内** で実行される。brainstorming が `Resume From=gdd-requirements-gating` に更新したら、同じターン内でこの skill の処理を続行する。ターンを分けない。approved になったら同じターン内で `🔍 確認をお願いします` テンプレートを出力し `<gdd-stop reason="human-check-waiting">` で停止する。

## Goal

- human check に出せる requirements artifact を揃える
- 承認ポイント・スコープ・安全境界・AC の意味を AI で先に点検する
- `Requirements Review Status` を更新する
- 人間チェックは reviewer の blocking 指摘を解消してから 1 回で通しやすくする
- 要約だけでは見落としやすい route / ownership / masking / rollout 論点を、人間の承認事項として前に出す
- 初回承認後の再 human check を濫発しない。active session follow-up は `references/phase-progression.md` § Active Session Follow-up Classification に従い、既承認 AC 内の実装修正や reviewer 指摘対応は human check に戻さず build/debug route で継続する

## requirements_amendment 解消チェック

active follow-up から `Route In Progress=requirements_amendment` で到達した場合、この skill は requirements artifact update lane を完了させる責任を持つ。requirements review が approved になって human check へ出す直前に、`requirements_amendment` を以下のいずれかへ解消する。

- AC semantics / prompt-output contract / access method / credential backend / tenant boundary / responsibility boundary が変わる場合: `Route In Progress=human_recheck_required`、`Resume From=human-check-waiting`、`Human Check Status=pending`
- 要件の目的・前提・スコープをもう一度壁打ちする必要がある場合: `Route In Progress=planning_rework_required`、`Resume From=gdd-brainstorming`
- 承認済み AC / Approved Direction / output contract を変えない artifact 修正だけの場合: `Route In Progress=none`

`Route In Progress=requirements_amendment` のまま `<gdd-stop reason="human-check-waiting">` を出さない。build phase / task-breakdown に進む前にも必ず `requirements_amendment` が残っていないことを確認する。`human_recheck_required` / `planning_rework_required` へ解消した場合、既存 `tasklist.md` は stale tasklist として全再生成対象にする。

## Planning Interrupt Decision Menu

planning / requirements-gating / subagent planning の途中で、HITL をまだ人間に表示していない状態のままユーザーが追加指示や質問を挟んだ場合は、途中指示を黙って混ぜて HITL を省略しない。4 択の正本は `references/requirements-gating-steps.md` § Planning Interrupt Decision Menu。事前回答なら Menu の 3 の例外。自律判断できる場合でも、要件や承認範囲が変わるなら `requirements_amendment` に倒し、更新後の HITL を出して `human-check-waiting` で止める。分類に迷う場合は 4 択を人間に表示する。

## Fixed Model

`references/fixed-models.md` を参照（Claude Code: `opus` + `effort=high` / Cursor: `Grok 4.6` + `medium` / Codex: `gpt-5.6-sol` + `medium` 固定）。理由: 要件整理は human check の承認対象、brainstorming と同一 subagent で完走する formal gate の 1 つ。

## Inputs

- `.steering/.../requirements.md`
- `.steering/.../design.md`
- `.steering/.../adr.md`（存在すれば補助コンテキストとして読む）
- `.steering/.../reviews.md`（存在すれば最新ラウンド分だけを読む）

## Review Set

- always:
  - `gdd-planning-reviewer`（requirements の観点）
- design-gating を通るタスクでは、design の観点の組も並行に起動する（条件は下の正本）
- selection rule の正本:
  - `references/reviewer-selection.md`
- task sizing:
  - `quick (express)` の違いは `references/requirements-gating-steps.md` § Express
- lazy loading:
  - 起動する reviewer の agent 定義（`agents/*.md`）だけを読む

## Status Update Format

Schema の正本は `references/gate-status-schema.md`。フォーマット（`<status> | evidence | updated_by | updated_at`）・許容値・`waived` 禁止（phase-level のため）はすべて schema に従う。skill 固有の補足はなし。

## Additional Review Concerns

いずれも接地条件（AC の意味・スコープ・承認ポイント・安全境界）に該当する場合だけ blocking にする。

### Broad Requirement Check

`requirements.md` に `Broad Requirement: true` がある、または reviewer が要件を広いままと判断した場合、以下が揃うまで human check に進めない（scope は承認事項のため blocking 対象）:

- `Scope Narrowing` に keep / defer / reason / reopen trigger があり、承認ポイント化の前に明らかな nice-to-have / 横展開 / 将来拡張を削っている
- keep がユーザー明示対象または機械的に絞れる対象である。根拠なく「代表」「利用頻度が高そう」として AI が選んでいる場合は、keep を `<要人間選択: 候補...>` に戻す
- human check の承認ポイントに「採用 scope」「対象候補の選択」または「Scope Narrowing の妥当性」があり、人間が keep / defer を覆せる
- 選ばない案が `やらないこと` または `後回し` に反映される予定が明記されている

広い要件のまま AI 推奨案だけで scope を確定してはならない。広い scope をそのまま承認ポイントへ大量に並べるのではなく、先に削れる scope を削る。

### AC Quality Check

AC はテストの正本なので、以下を blocking 対象とする:

- steering に `request.md` と `request-crosscheck.md` がある（brainstorming-steps § 9）

- AC が Yes/No で観測できる文になっている。「よくなる」「使いやすい」「自然」だけの表現は accepted AC に残さない（`Open Questions` へ回すか具体化する）
- ユーザーが明示した完了条件が AC に写っている（照合元は `スコープ` に残した原文の箇条書き。一覧が無い場合はまず一覧を書かせる）。落とす場合は非スコープか Open Questions に理由付きで書かれている
- 人間が承認した重要判断が AC として書かれている（独立 trace 表ではなく）
- AC 以外の節・design.md の事実が AC と食い違わない（食い違わない書き直し・`[duplication lint]` の行・方向性を除き 2 個を超える HCQ は advisory。正本: `references/requirements-template.md` § 事実は AC に 1 回だけ書く）
- 観測面が外部にある AC（外部システムへの投稿 / デプロイ後の挙動 / 外部 API の実呼び出し）は、検証水準（E2E 必須 / 外部証跡必須）が AC 本文に明記されていること（下流の task-breakdown / completion-check は「AC 本文が要求する検証水準」を照合するため、書かれていない水準は守られない）
- 出力が外部システム（Slack / GitHub / wiki）に投稿され、構造化データが 20 件以上になりうる・正確な件数や網羅性が求められる・同一入力同一出力が期待される場合、網羅性・一貫性・責任分界（「LLM はフォーマットに関与しない」等）の非機能 AC があること（**Why:** LLM に大量データのフォーマットを任せると非決定的に省略される。一覧の投稿機能で、大半の行が落ちた事例あり）

### Fail-closed Default / Untrusted Input Boundary Check

安全境界に直結するため、以下のいずれかに該当する要件では AC に明示的な記載があるか確認する。欠けている場合は blocking（セキュリティ境界に直結するなら high）:

1. **denylist / allowlist の未設定時デフォルト挙動**: 「設定ファイルが無い」「設定が空」「parse 失敗」等の未設定時のデフォルト挙動が **fail-closed（全拒否 / 機能無効）** か **fail-open（全許可 / 機能継続）** かを AC に明記することを要求する。特にセキュリティ境界（認可判定 / コマンド実行 / 外部 API 呼び出し）では fail-closed を既定にする根拠を AC で言語化する
2. **untrusted input を LLM prompt に含める場合の区切り要求**: PR body / issue body / webhook body / 外部 API 応答 / email 本文 / chat 本文 を LLM の prompt / context に含める設計では、区切りタグで明示的に囲み、区切り内を「データ」として扱い instruction として解釈しない要求を AC 化する
3. **prompt injection 防御対象トリガー文字列の明示**: untrusted input 由来のトリガー文字列を LLM が誤って instruction として解釈しないための防御（エスケープ / 中立化 / 拒否）の有無を AC 化する

### 選択肢提示の品質

複数の妥当な選択肢（architecture / CI / access method / credential backend 等）がある採用判断は承認事項であり、以下を blocking 対象とする:

- AI が勝手に単一案へ丸めない。単一案にできるのは既存 repo 標準または公式標準に機械的に従う根拠がある場合だけで、その場合も `requirements.md` に `選択肢なし（単一案。理由: ...）` と残す。非標準な自前実装を採る場合は必ず承認ポイントに出す
- Option A / B / C を使う場合、同じ HITL 内で各 Option の意味・採用案・採用理由・却下理由を説明する。`Option B とは？` と聞かれる状態で出さない
- **定量データ必須化（Concrete Trade-off Data Requirement）**: コスト・品質・性能等の定量的なトレードオフが関わる選択肢は、実測値・具体例を伴わない抽象的な二択のみを提示しない。実測が難しい場合は推定値であることを明記して提示する（実測値のない抽象的な二択を提示し、承認後に方針転換して amendment を繰り返した事例の再発防止）
- credential backend（Secrets Manager / SSM / env / OAuth 等）・tenant 境界・IAM scope が未確定なら blocking Open Question または承認ポイントにする

### 段階実装の承認境界

複数 Stage / 複数 PR / 後続 PR がある場合、PR の分け方と後続の扱いは承認事項のため blocking 対象とする:

- `Implementation Sequence Plan` があり、`references/requirements-template.md` の条件付き節の欄が `段階実装案` を出せる粒度で書かれている
- `PR Boundary=follow-up-pr` / `post-merge-verification` の Stage がある場合、`Planned Follow-up Stage Lane` に `- [ ]` / `- [x]` チェックリスト形式で後続 stage が列挙されている（Stop hook の自動検出に必須）
- PR の分け方（単一PR / 複数PR / 後続PR着手前に再承認）が承認ポイントとして比較されている。段階表だけで既成事実化しない

## Steps

詳細な手順と Human Check Handoff ルールは `references/requirements-gating-steps.md` を参照。概要:

1. `requirements.md` / `design.md`（と `adr.md` / `reviews.md` の最新ラウンド）を読み、Review Round を数える
2. `references/requirements-template.md` の節一覧と `references/task-sizing.md` に従い、`Task Size` に応じた節見出しが揃っていることを確認する（中身の網羅性はここで採点しない）
3. `references/reviewer-selection.md` に従い reviewer を選び、`Planning Reviewer Selection` を記録する
4. gate status を `in_review` に更新し、提出前の照合（`gdd-requirements-precheck`。詳細手順 Step 4a）の `ng` を確かめて反映してから、reviewer を `references/subagent-dispatch.md` § Reviewer Input and Time Budget に従って起動し、待ち時間に HITL draft を組む
5. reviewer 結果を、reviewer の `blocking:` 欄に従って blocking / advisory に分けて `reviews.md` に記録する（書き換えてよい場合は詳細手順 § 精度の第一原則）。HITL 前に解消必須なのは blocking（AC の意味・スコープ・承認ポイント・安全境界に影響する指摘）だけ。他の反映時機は詳細手順 Step 6。policy-level の判断が必要な指摘は `Human Check Questions` に集約して blocking を解除してよい（解除してよい条件は詳細手順 § 精度の第一原則）
6. blocking が残る場合: Round 上限内なら（先に Step 4b の経過を確かめる）`changes_requested` → `gdd-requirements-amendment` で blocking だけを処置して再入（差分スコープ）。上限到達なら AI が閉じない blocking を人間へ一括提示して `human-check-waiting` で止める
7. blocking が無ければ Spec Self-Review Checklist を通し、`approved` → `Resume From=human-check-waiting` に進める。`state.md` の `Route In Progress` が `planning_rework_required` の場合は `none` にクリアする（`references/rollback-patterns.md` 参照）。phase を抜けるとき `references/phase-gate-prechecks.md` step 3 に従い `Last Handoff Summary` を更新する

## Human Check Handoff

`Origin Session` 有時の起動元通知は `references/phase-progression.md` § Cross-Session Messaging に従う。

`human-check-waiting` に入る前は、まず `references/human-check-template-compact.md` を一次表示テンプレートとして使う。full `references/human-check-template.md` は返答分類・詳細・例外ルールの正本として参照するが、初回 HITL に長い表をそのまま貼らない。

外部サービス、runtime、framework、test tooling、access method、credential backend のいずれかを採用または変更する場合、HITL には `実装技術スタック` を必ず出す。language / runtime、framework / library、test tooling、access method、credential backend だけを表示し、全 dependency 一覧や細かな version 羅列は避ける。

複数 Stage の `Implementation Sequence Plan` がある場合、HITL には `段階実装案` を必ず出す。どの段階で何を実装し、どこまでがこの PR で、何をもって完了確認し、どの条件で次へ進む / 人間に戻すか、後続 Stage は方針承認だけか再承認が必要か、追跡先はどこかを表で示す。段階実装と言いながら計画表を出さないまま承認させない。後続 Stage をこの OK で実装まで進める場合は、`Approval Scope` を独立承認ポイントに昇格し、暗黙の方向性承認だけで自走しない（`Continuation Mode=auto-after-clean` / `auto-stacked` も同様に独立承認ポイントへ昇格し、圧縮表示経路（`後続の追跡先`）を採る場合でもその値と選定理由を必ず HITL に表示する）。

初回承認後に再度 `human-check-waiting` へ戻すのは、AC semantics / scope / policy / ownership / security boundary / prompt-output contract が変わる場合だけ。既存 AC 内の修正なら `Follow-up Classification` の判断根拠を state.md / tasklist.md / worklog.md のいずれかに残して継続する。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける

## Rationalization Check（この skill 固有）

要件整理を短縮したくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。全体向けは `references/common-guardrails.md` § 合理化防止テーブル。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「要件は明確、すぐ実装に入れる」 | 「明確」な要件ほど暗黙の前提が多い。reviewer と human check が暗黙を言語化する | [Curse of Knowledge] 自分の中で明確 = 他人にも明確、ではない。文書化を省く最大の動機 |
| 「AC は後で書き足せばいい」 | AC が無い = 完了条件が曖昧 = 「動いた気がする」で done される。AC は先に書く | [Bias for Action] 着手したい欲求が、完了条件の言語化より優先される |
| 「Open Questions は残してもいい、実装しながら決める」 | 実装中に判断すると、決定の根拠が散らばる。blocking questions は human check 前に埋める | [Bias for Action] 進捗の見えなさを嫌い、未確定のまま動き出す |
| 「Summary Brief は省略、requirements.md を見れば分かる」 | 人間は要約で判断したい。Summary Brief は承認の前提条件。省略は guardrail 違反 | [Curse of Knowledge] 書き手は全文を読めるが、承認者は要約で判断したい |
| 「もう 1 ラウンド回せば品質が上がる」 | AC が変わらないラウンドは出荷物の品質に寄与しない。上限後は人間が判断する方が速くて正確 | [Premature Closure の逆] 完璧主義がループを回し続ける。ラウンドと時間が大きく膨らんだ実例がある |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、承認見出しルール、blocking Open Questions、gate 開始前の記録ルール、fail-closed 応答）。以下はこの skill 固有のルール。

- Bounce Log: `references/bounce-log-schema.md` 準拠、閾値`>= 2`、escalate先`human_recheck_required`（ユーザー提示escalation。`gdd-systematic-debugging`不使用）
- AC のファイル数・行番号・シンボルが実測値か確認、概算は差し戻す（未測+理由明示は可）
- `requirements.md` と lightweight `design.md`（express は requirements.md だけ）が揃うまで gate を始めない
- `Summary Brief` を省略した summary-only handoff で `human-check-waiting` に進めない
- `Summary Brief` に `対象` / `確定事項` / `未確定事項` / `やらないこと` / `外部依存の確認結果` が無いまま進めない
- standard タスクで `Summary Brief` の `Honest Limitations`（この設計で確認できないこと / 担保できない部分）が欠けたまま `human-check-waiting` に進めない。quick では任意（詳細は `references/common-guardrails.md` § Honest Limitations）
- `Design Policy Discussion` を省略した handoff で `human-check-waiting` に進めない（quick タスクの省略ルールは `references/task-sizing.md` が正本。quick では省略可）
- `Broad Requirement: true` なのに選択肢 A/B/C・縮小案・採用 scope の承認ポイントが無いまま `human-check-waiting` に進めない
- `Broad Requirement: true` のまま詳細実装案を既成事実化して `human-check-waiting` に進めない。scope 承認前の実装方式は provisional と明記する
- 根拠なく代表 scope を AI が選んだまま `human-check-waiting` に進めない。対象未指定なら対象候補の選択を承認ポイントにする
- planning reviewer を飛ばして human check に進めない（時間超過の一括提示を除く）。human check をこの skill の中で代替しない
- blocking 指摘を未解決のまま `gdd-design-gating` に進めない（advisory は残ってよい。`reviews.md` に記録されていること）
- Round 上限を超えてレビューループを回さない。上限後の blocking の扱いは人間が決める
- **human check 停止時は `references/human-check-template-compact.md` を Read し、テンプレートをそのまま埋めて出力する。`<gdd-hitl-fields ...>` タグ・`<gdd-stop reason="human-check-waiting">` マーカーとその後の `## 👤 次にすること` を含める**。上記欠落は guardrail 違反。個別ルールは `references/human-check-template.md` § 必須ルール / § content 品質ルールが正本
- **human check の回答パターン別処理**: (1) 全 OK（差 `なし`）→ 即時継続 (2) 一部変更指示 → 該当箇所を修正し全点を再提示→再停止（案の名指しは変更要求ではない。`commands/gdd-dev.md` #10 STEP 1） (3) 方向性レベルの全面やり直し → `Resume From=gdd-brainstorming` に戻す。いずれの場合も再承認なしに `gdd-design-gating` に進めない。詳細は `references/requirements-gating-steps.md` § 承認後の即時継続 を参照
