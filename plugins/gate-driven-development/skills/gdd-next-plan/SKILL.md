---
name: gdd-next-plan
description: "Use after a GDD milestone, PR, merge, or phase boundary when the user asks what to do next."
version: 0.1.0
---

# GDD Next Plan

GDD の milestone / PR boundary / stage boundary 後に「次の計画」を出すための skill。`gdd-status` は現在地表示、`gdd-next-plan` は現在地を踏まえた次アクション計画を担当する。

## Read/Write Boundary

- **read-only fact verification**: PR state、merge commit、CI、review、test result、diff、`state.md / tasklist.md / worklog.md` の確認は read-only で行う。merge / push / deploy / apply / AWS write はしない。
- **Registry artifact creation is allowed**: merge 後の後続実装がある場合だけ、復旧用の受け渡しキーとして `.claude/gdd-continuations/<continuation-id>.json` を作成してよい。通常導線は同じチャットで「次に進んで」であり、Registry はチャット破損・compaction 不安・明示的な新チャット開始時の復旧用である。これは実装開始や production write ではなく、GDD artifact の follow-up seed 作成として扱う。
- 後続 Stage が無い場合は Registry を作らない。`Continuation Registry 未作成: 後続 Stage なし / remaining_stage_ids empty のため不要` と書き、cleanup only / 完了として扱う。
- 後続 Stage があるのに Registry を作れない場合は、長文プロンプトを人間に貼らせず、`Continuation Registry 未作成` と理由、次の1アクションを出す。

## Goal

- 「P1完了後、次の計画は？」のような自然文 follow-up を GDD 側で受ける
- `マージした` / `mergeした` / `merged` のような報告だけでも、active GDD の merge report is also a next-plan cue として扱う
- **Merge Report Cleanup Trigger**: `マージした` 報告は cleanup cue かつ deployment/status verification cue でもある。main reflected と deploy/apply を含む CI/CD 反映確認後、safe cleanup ready なら追加の cleanup 指示を待たず GDD managed worktree を整理する
- `state.md / tasklist.md / worklog.md`、PR 状態、`Planned Follow-up Stage Lane` を読んで、次に何をするかを順序化する
- PR 未 merge / merge 後 / 後続 Stage / same-chat continuation / 復旧用 resume を区別する
- merge 後の follow-up は `Phase Continuity Packet` として、前フェーズで完了したこと、今回のPRでやること、後続PRに送ること、最終到達点を明示する。`Post-Merge Follow-up Prompt` は内部互換名であり、人間に長文プロンプトを貼り付けさせる表示名ではない
- merge 後の後続実装は、長文プロンプトを人間が貼る運用にしない。same-chat continuation が標準であり、ユーザーは同じチャットで「次に進んで」と言えば次 Stage へ進める。`Continuation Registry` は復旧用として保存し、チャットが壊れた場合だけ `/gdd-resume <continuation-id>` を使う
- 同じチャットで継続するのが標準。ただし実装場所は stageごとに新 worktree とし、旧 worktree / 旧 branch には積まない。後続 Stage の `このOKで承認する範囲` が `事前回答で後続PRも実施許可` なら、本人の事前回答が「次に進んで」を代える。post-merge verification が済み、元の `事前回答:` 行を `references/human-check-template.md` § 事前回答 の 2 のとおり確かめられたら待たずに着手する（確かめられなければ `### 次の計画` を出して待つ）。記録と着手は § 事前回答 の 4、人に戻す条件は 3 に従う
- merge 後は通常ローカル整理（旧 worktree / branch cleanup）を案内し、同じチャット継続 + stageごとに新 worktree で後続実装へ進む導線を出す
- active GDD 中に `superpowers:writing-plans` / `superpowers:executing-plans` / `superpowers:finishing-a-development-branch` へ workflow handoff しない

## Fixed Model

- `Claude Code`: `sonnet` + `effort=low`
- `Cursor`: `Grok 4.5` + `reasoning.effort=low` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=low`
- state / PR / tasklist の読解が主目的なので leaf tier。mini には落とさない

## When To Use

- ユーザーが「P1完了後、次の計画は？」「次の計画は？」「次は何する？」「このPRの後どう進める？」「次PRの計画を出して」「merge後どうする？」と聞いた
- ユーザーが active GDD PR の後で「マージした」「mergeした」「merged」と報告した。質問形でなくても `Manual Merge Continuation` と `gdd-next-plan` の対象にする
- 上記の merge 報告は cleanup cue かつ deployment/status verification cue でもある。main reflected / deploy/apply を含む CI/CD or deploy/apply reflection checked / GDD managed worktree / dirty diff なし / persistence 済み / root duplicate steering なしなら `safe cleanup ready` として `gdd-using-git-worktrees` の Post-Merge Cleanup へ進める
- active GDD の `Completed Tasks` / `Current Stage` / `Planned Follow-up Stage Lane` があり、次の実装・PR・検証の順序を知りたい
- PR 作成後または merge 後に、同じチャットで次 Stage へ進む follow-up plan が必要

使わない場面:

- 単に現在地だけ知りたい → `gdd-status`
- 新しい formal workflow を開始する → `/gdd-dev` / `gdd-brainstorming`
- 既存機能に要件追加・仕様変更を入れる実装開始 → `gdd-requirements-amendment`
- PR 作成後のレビュー指摘そのものの修正・push・再レビュー依頼ループ → `gdd-pr-review-followup`
- GDD 外の単発計画 → superpowers を使ってよい

## Steps

1. **status-first**: まず `gdd-status` と同じ deterministic resolver で active steering を一意に解決する。使える場合は `scripts/gdd_task_binding.py resolve <repo>` で Task Binding Registry を確認する。Task Binding Registry を正本にし、registry と current worktree/branch の整合が取れた場合のみ active steering とする。current worktree、会話履歴、root `.steering` は soft signal であり、単独では採用しない。解決できなければ計画を作らず、候補と次の1アクションを出す。
2. `state.md / tasklist.md / worklog.md` を読む。存在すれば `requirements.md` の `Implementation Sequence Plan` と `Planned Follow-up Stage Lane` も読む。
3. PR が関係する場合は read-only で PR 状態を確認する。`gh pr view` が使えるなら `state` / `mergedAt` / `mergeCommit` / `mergeStateStatus` / `statusCheckRollup` / `reviewDecision` / `headRefName` を見る。使えなければ「PR状態未確認」と明示する。ユーザーが `マージした` と言っていても PR state is MERGED を read-only に確認するまで実行用プロンプトを確定しない。
4. 次の状態を分類する:
   - **PR 未 merge**: 次の計画は新規実装ではなく、CI / review / PR follow-up を先に収束する。必要なら `gdd-pr-review-followup` に案内する。後続実装の正式プロンプトを確定しない。
   - **merge 後**: `Manual Merge Continuation` として post-merge verification を行う。merge commit / CI / 最終差分 / state-tasklist再読込 / Planned Follow-up Stage Lane確認 後に `ready_after_merge_verification` と判断できる場合だけ、`Post-Merge Follow-up Prompt` を確定する。PR作成時点では確定プロンプトを出さない。後続実装は **same-chat continuation が標準**。同じチャットで「次に進んで」と言えば次 Stage に進む。ただし実装場所は stageごとに新 worktree とし、旧 worktree / 旧 branch には積まない。直さないと決めた medium・low（Advisory Findings・`指摘止まり（` の行）は、後続 Stage の有無によらず、Phase Continuity Packet の「後続PRに送ること」にも次にやることにも入れず、直す PR を申し出ない（本人が PR 番号を挙げて頼んだら 1 本にまとめる）。
     - `Post-Merge Follow-up Prompt` は内部互換名であり、人間に長文プロンプト貼り付けを求めるものではない。実際の表示と保存は必ず `Phase Continuity Packet` として扱う。最低限、前フェーズで完了したこと、今回のPRでやること、後続PRに送ること、最終到達点、今回のスコープ、今回やらないこと、検証方法、自走上限、参照するPR/commit/steering、開始コマンドを含める。
     - 表示上は「今回のPRでやること」だけでなく、ユーザーが日常的に使う言い方として「このPRでやること」も分かるようにする。段階実装では、`このPRでやること` / `後続PR` / `段階実装` の境界を同じ出力内で読めること。
     - same-chat continuation 側の first workflow artifact action must create requirements.md / design.md / state.md。artifact creation is not optional。cleanup 候補提示と必要なら旧 worktree cleanup を終え、次 Stage 用の新規 worktree に入ったら、実装より前に requirements.md / design.md / state.md を作成し、HITL before implementation を出す（`事前回答で後続PRも実施許可` の Stage は `references/human-check-template.md` § 事前回答 4 で、HITL は 2 で扱う）。steering artifact empty のまま止まった場合は未完了として扱い、次回 resume では artifact 作成から再開する。
     - **Post-Merge Same-Chat Boundary**: 同じチャットでは read-only verification、post-merge / post-apply confirmation、follow-up seed 整備、Phase Continuity Packet 生成、ローカル整理案内、cleanup 候補提示、必要条件が満たされた場合の旧 worktree cleanup、次 Stage 用の新 worktree 作成、requirements / design / state 作成、HITL before implementation（事前回答の Stage は § 事前回答 2 の扱い）まで進めてよい。旧 worktree では後続実装しない。実装は stageごとに新 worktree で、Pre-Follow-up Hygiene Gate 後に latest default branch から作業する。
     - **Post-Merge Local Cleanup Guidance**: 表示順と実行順を分けない。merge 後の標準導線は read-only verification → Phase Continuity Packet / Continuation Registry → 次の計画 output → ローカル整理案内 → cleanup 候補提示 → 必要条件がすべて満たされた場合だけ cleanup 実行。cleanup 案内も実削除も、この順序より前に出さない。`gdd-using-git-worktrees` の `Post-Merge Cleanup` に従い、`fetch` / cleanup 対象確認 / `worktree remove` / `branch delete` / default branch へ戻す手順を案内する。cleanup 実行は所有境界・dirty diff・root bleed を確認してからであり、曖昧な worktree / branch は削除しない。
     - **Merge Report Cleanup Trigger**: ユーザーの `マージした` / `mergeした` / `merged` は cleanup cue かつ deployment/status verification cue。`PR merged` / `main reflected` / `CI/CD or deploy/apply reflection checked` / `post-merge verification pass` / `GDD managed worktree` / `dirty diff なし` / `Continuation Registry created または後続 Stage なし` / `resume 情報が worktree 外` / `root duplicate steering なし` / `identity tuple clean` / `safe cleanup ready` の **stacked 依存の確認** を満たすなら `safe cleanup ready` とし、追加の cleanup 指示を待たずに旧 worktree / branch cleanup へ進む。満たさない場合は cleanup 候補とブロッカーだけ出す。deploy/apply は既存 workflow の read-only 監視であり、新規 write 操作は別承認。
     - **Cleanup Persistence Gate**: `git worktree remove` は削除対象 worktree 内だけにある未コミット成果物を消す。cleanup 前に、resume に必要な未コミット成果物（`.steering/<task>/requirements.md` / `design.md` / `state.md` / `tasklist.md` / `worklog.md` / eval report / no-post artifact / `.claude/gdd-continuations/<id>.json`）が PR / merge 済み commit / worktree 外の Continuation Registry / repository root の安定場所へ保存済みであることを確認する。保存先が cleanup で消える場所なら `Continuation Registry created` とみなさない。
     - **Cleanup Execution Gate**: 実際に worktree / branch を削除する前に、`PR merged` / `post-merge verification pass` / `Continuation Registry created または後続 Stage なし` / `Continuation Registry が worktree 外` / `resume に必要な未コミット成果物なし` / `dirty diff なし` / `ownership 明確` / `root duplicate steering なし` / `safe cleanup ready` の **stacked 依存の確認** を確認する。1 つでも不明なら cleanup 実行ではなく cleanup 候補の提示に留める。
     - **Continuation Registry**: `Phase Continuity Packet` は `.claude/gdd-continuations/<continuation-id>.json` に保存する。最低限 `continuation_id` / `origin_pr` / `origin_branch` / `origin_merge_commit` / `origin_steering` / `base_branch` / `base_commit` / `remaining_stage_ids` / `phase_continuity_packet` / `conversation_history=reference_only` / `artifact_source=canonical` / `fact_source=git_pr_ci_test` を含める。`continuation-id` は `<origin-task-slug>--after-pr-<number>--<YYYYMMDD>` を基本形にし、衝突時だけ `-2` / `-3` を suffix する。実際にファイルを書けた場合だけ `Continuation Registry: created` と書く。ファイルを書けていない場合は `Continuation Registry 未作成` または `作成予定` と書き、作成済みと主張しない。Registry は復旧用であり、通常は同じチャットで「次に進んで」を主導線にする。復旧用には短い再開導線 `/gdd-resume <continuation-id>` を添える。チャットが壊れた場合だけ `/gdd-resume <continuation-id>` を使う。
     - **No Follow-up Stage**: `remaining_stage_ids` が空で、requirements / tasklist / worklog に後続 Stage が無い場合は、Phase Continuity Packet を捏造しない。`Continuation Registry 未作成: 後続 Stage なし / remaining_stage_ids empty のため不要` と出し、次にやることは cleanup only / 完了と書く。
     - **Bootstrap vs First Workflow Artifact Action**: 新チャットで `/gdd-dev` が始まったら `setup-gdd-loop.sh は bootstrap` として先に実行してよい。その後の first workflow artifact action は `requirements.md / design.md / state.md` の作成である。worktree 作成だけでは planning 未完了であり、steering artifact empty のまま実装に入らない。
   - **Planned Follow-up Stage Lane あり**: `Pending Stage ID` / `Next Planned Stage` / `Human Recheck` / `Tracking Destination` を使って、次PRの入口を示す。
   - **Next Action が build phase**: `tasklist.md` の `Next Action` に戻し、つまり tasklist.md の Next Action に戻し、実装計画を作り直さない。新しい実装計画を作らず、current GDD phase route に戻す。
   - **Next Action が done だが追跡先なし**: 後続 Stage がないなら完了。後続が worklog にだけあるなら `Planned Follow-up Stage Lane` 不足として補完候補を出す。
5. `superpowers:writing-plans` / `superpowers:executing-plans` / `superpowers:finishing-a-development-branch` は active GDD 中の workflow として呼ばない。比較や考え方を参照する場合も、出力には `GDD primary / superpowers advisory only` と書き、反映先を GDD artifact / GDD route に戻す。

## Output Template

```markdown
## 次の計画

**現在地**: <phase / PR 状態 / Stage>
**判定**: <PR 未 merge / merge 後 / 後続 Stage あり / build 継続 / 完了>
**GDD primary**: active GDD のため、superpowers:writing-plans / superpowers:executing-plans には渡さない

### まずやること
1. <CI / review / post-merge verification / tasklist Next Action など>
2. <必要な read-only 確認>

### その後
1. <merge / review loop / next PR seed / recovery resume key>
2. <次PRの入口>

### 次 Stage へ進む（merge 後に後続 Stage がある場合）
1. おすすめ: 同じチャットで「次に進んで」と言えば続行できます
2. GDD は旧 worktree を整理対象にし、latest default branch から stageごとに新 worktree を作ります
3. その新 worktree で requirements.md / design.md / state.md を作り、HITL before implementation を出します
4. 復旧用: Continuation ID を保存します。チャットが壊れた場合だけ `/gdd-resume <continuation-id>` を使います

### マージ後のローカル整理（merge 後の場合）
1. 通常は後続実装の前に、旧 worktree / branch を整理します
2. 実行前に確認すること: PR merged / dirty diff / cleanup ownership / root duplicate steering / cleanup で消える場所に resume 情報が残っていないこと
3. 標準手順: fetch -> cleanup 対象確認 -> worktree remove -> branch delete -> default branch へ戻る
4. まだ削除しないもの: dirty / ownership 不明 / host-managed / 複数候補で曖昧な worktree
5. cleanup 実行は、次の計画と Continuation Registry（または後続 Stage なしの明示）を出した後にだけ行う
6. resume に必要な未コミット成果物が削除対象 worktree 内だけにある場合は、worktree 外へ保存してから cleanup する
7. Merge Report Cleanup Trigger: `マージした` は cleanup cue かつ deployment/status verification cue。main reflected と deploy/apply を含む CI/CD 確認後、safe cleanup ready なら追加の cleanup 指示を待たず、GDD managed worktree を整理する

### 復旧用の受け渡し（merge 後に必要な場合）
<Continuation Registry に保存し、同じチャット継続の復旧導線を出す。Post-Merge Follow-up Prompt は内部互換名で、人間向けには Phase Continuity Packet として registry に保存する。復旧用には短い再開導線を添える>

```text
Continuation ID: <continuation-id>
保存先: .claude/gdd-continuations/<continuation-id>.json
通常の続行: このチャットで「次に進んで」
復旧時だけ: /gdd-resume <continuation-id>

人間が長文プロンプトを貼り付けないで済むよう、通常は同じチャットで進め、チャットが壊れた場合だけ上の resume を使います。
```

Registry payload summary:
- conversation_history=reference_only
- artifact_source=canonical
- fact_source=git_pr_ci_test

```text
/gdd-dev <次フェーズ名>

Phase Continuity Packet:
- 前フェーズで完了したこと: <PR / merge commit / 完了AC / 検証済み事項>
- 今回のPRでやること: <今回実装・検証する Stage / AC / ファイル範囲>
- 後続PRに送ること: <今回やらない Stage / 後続で再承認すること>
- 最終到達点: <複数フェーズ全体でどこまで行けば完了か>

今回のスコープ:
- やること: <触ってよい範囲>
- やらないこと: <production default / deploy / external write など>
- 検証方法: <unit / contract / no-post / E2E / external evidence>
- 自走上限: <PR作成まで / post-merge verificationまで / など>

最初にやること:
- first action must create requirements.md / design.md / state.md
- artifact creation is not optional
- setup-gdd-loop.sh は bootstrap。first workflow artifact action は requirements.md / design.md / state.md
- worktree 作成だけでは planning 未完了
- requirements/design/state 作成後、HITL before implementation を出す
- steering artifact empty のまま止まらない
- 段階計画なしで実装に入らない
```

### まだやらないこと
- <PR 未 merge なら後続実装に入らない等>
```

出力は短くする。PR 未 merge の場合は、次PRの詳細設計を作り込まず「CI / review / merge が先」と明示する。

## Scenario Fixture Contract

この section は fixture 型テストの正本。`gdd-next-plan` の出力を迷ったら、下の入力に対して expected / forbidden を満たす。

### Fixture: unmerged_pr_next_plan

- input: pr_state=open / merge_state=not_merged / user asks 次の計画は？
- expected判定: PR 未 merge
- expectedまずやること: CI / review / PR follow-up
- forbidden: Post-Merge Follow-up Prompt を確定しない
- forbidden: 次PRの詳細設計を作り込まない

### Fixture: merged_pr_followup_prompt

- input: pr_state=merged / follow-up stage exists / user asks 次PRの計画を出して or 次に進んで
- expected判定: merge 後
- expectedまずやること: post-merge verification
- required_before_prompt: merge commit / CI / 最終差分 / state-tasklist再読込 / Planned Follow-up Stage Lane確認
- allowed_after: ready_after_merge_verification
- expectedその後: ローカル整理案内 -> Phase Continuity Packet（内部互換名: Post-Merge Follow-up Prompt）
- expectedその後: Phase Continuity Packet
- expected標準導線: 同じチャットで「次に進んで」
- required_worktree_boundary: stageごとに新 worktree / 旧 worktree では後続実装しない
- required_cleanup_guidance: gdd-using-git-worktrees Post-Merge Cleanup / fetch / worktree remove / branch delete / default branch
- required_prompt_shape: Phase Continuity Packet
- required_prompt_fields: 前フェーズで完了したこと / 今回のPRでやること / 後続PRに送ること / 最終到達点
- required_first_action: first action must create requirements.md / design.md / state.md
- required_registry: .claude/gdd-continuations/<continuation-id>.json
- required_resume_entry: /gdd-resume <continuation-id> は復旧用
- forbidden: 人間が長文プロンプトを貼り付けない

### Fixture: new_chat_prompt_artifact_completion

- input: new chat receives Post-Merge Follow-up Prompt and starts /gdd-dev
- expectedまずやること: requirements.md / design.md / state.md を作成して HITL before implementation
- forbidden: steering artifact empty のまま止まらない
- forbidden: 段階計画なしで実装に入らない

### Fixture: merge_report_without_question

- input: user says マージした / mergeした / merged after a GDD PR
- expected判定: merge 後
- expectedまずやること: Manual Merge Continuation
- expectedその後: post-merge verification -> ローカル整理案内 -> gdd-next-plan
- expectedその後: post-merge verification -> gdd-next-plan
- forbidden: superpowers:finishing-a-development-branch
- forbidden: superpowers:writing-plans

### Fixture: ambiguous_or_build_phase

- input: registry/current worktree mismatch OR Next Action が build phase
- expected判定: 解決できなければ計画を作らず
- expectedまずやること: 候補と次の1アクション
- expectedbuild中: tasklist.md の Next Action に戻し
- forbidden: 新しい実装計画を作らない

## Rationalization Check

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「次の計画なら superpowers:writing-plans が得意」 | active GDD 中の次計画は state / PR / Stage / worktree 境界が正本。汎用 plan に渡すと context が切れる | [Tool Affordance Bias] 汎用 skill の名前が合っていると、状態機械の正本を飛ばしやすい |
| 「マージしただけなら branch finishing だから superpowers:finishing-a-development-branch でよい」 | active GDD では merge 報告は Manual Merge Continuation と post-merge verification の cue。branch finishing だけで閉じると次計画が出ない | [Tool Affordance Bias] 操作名が似ている standalone skill に吸われ、GDD の Stage / PR 境界を読み落とす |
| 「gdd-status で現在地を出したから十分」 | status は read-only 現在地表示。次の順序、PR 未 merge の停止境界、same-chat continuation 導線は `gdd-next-plan` が担当する | [Premature Closure] 現在地が分かると、次の安全な入口も分かった気になりやすい |
| 「PR作成後に次PRの実装計画まで出してよい」 | PR作成後はレビュー指摘・CI・最終差分が変わる。実行用プロンプトは merge 後に確定する | [Recency Bias] PR作成直後の情報を最終状態と誤認する |
| 「次チャットに `/gdd-dev` と目的を書けば十分」 | 複数フェーズでは、前フェーズで完了したこと / 今回のPRでやること / 後続PRに送ること / 最終到達点が無いと、新チャットが局所計画だけを作る。通常は同じチャットで「次に進んで」が標準 | [Context Collapse] 新しいチャットでは会話履歴が無く、Phase Continuity Packet が唯一の継続契約になる |
| 「worktree を作ったから planning は始まっている」 | requirements.md / design.md / state.md が無い、または空の steering artifact empty なら GDD planning は未完了。artifact creation is not optional | [False Progress] ディレクトリ作成を進捗と誤認し、HITL before implementation が抜ける |
| 「merge 後は復旧用プロンプトだけ出せばよい」 | 通常は同じチャット継続 + stageごとに新 worktree。後続実装の前に旧 worktree / branch を整理する。整理案内が無いと merged branch や古い steering を再利用して混線しやすい | [State Hygiene Gap] 実装計画だけを急ぐと、ローカル状態の掃除が抜けて次フェーズの土台が汚れる |

## Guardrails

- fact verification は read-only。`state.md / tasklist.md / worklog.md` を変更しない
- merge 後の `Continuation Registry` artifact 作成だけは例外として許可する。実装開始、既存 state の書き換え、production write とは扱わない
- PR 状態確認は read-only のみ。merge / push / deploy / apply はしない
- PR 未 merge なら、後続実装の正式プロンプトを確定しない
- merge 後の出力ではローカル整理案内を省略しない。cleanup 実行は `gdd-using-git-worktrees` の Post-Merge Cleanup に従い、所有境界 / dirty diff / root bleed を確認してからにする
- `Planned Follow-up Stage Lane` がある場合はそれを優先し、会話履歴だけで次 Stage を作らない
- active GDD 中は `superpowers:writing-plans` / `superpowers:executing-plans` / `superpowers:finishing-a-development-branch` を workflow として直接起動しない
- 次段階実装を始める場合は `/gdd-dev` / `gdd-requirements-amendment` / post-merge prompt のいずれかに明示的に接続する
