---
name: gdd-requirements-amendment
description: "Use for GDD follow-ups that change requirements, acceptance criteria, or behavior after prior approval or merge, and for active planning-before-approval changes like 「計画途中でこれも追加して」「これも入れて」."
version: 0.1.0
---

# Requirements Amendment

マージ済みまたは実装済みの機能に対する追加要件・仕様変更・不具合修正を、既存の steering 成果物を活用して正規フローへ戻す skill。active `/gdd-dev` 中、または同じチャットセッション内で実装・PR・deploy・E2E 後に発覚したズレは、まず現在の session / current steering / current PR への correction として扱い、新しい Plan に逃がさない。ただし PR が default branch へ merge 済みの場合、元 worktree / 元 branch は実装場所として再利用せず、Pre-Follow-up Hygiene Gate の後に new amendment / Hotfix Lane の新 worktree を latest default branch から作る。

## Fixed Model

- `Claude Code`: `opus` + `effort=high`
- `Cursor`: `Grok 4.6` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-sol` + `reasoning.effort=medium`（要件整理レーン。AC 変更を扱うため formal gate 扱いで medium 固定）
- 既存の steering 成果物との整合判断が必要なため、重いモデルで固定する

## When to use

- `gdd-brainstorming` が entry intent を `amendment` と判定した場合に委譲される
- マージ済みの機能への追加要件、仕様変更、不具合修正
- 「前回の PR で作った機能に追加変更が欲しい」ケース
- active `/gdd-dev` の承認前・計画途中に、「これも入れて」「これも追加して」「計画を見直したい」など、requirements / AC / 完了条件の差分が発生したケース
- active `/gdd-dev` 中の follow-up で、AC の追加・削除・条件変更・意味変更が発生したケース（分類の正本は `references/phase-progression.md` § Active Session Follow-up Classification）
- active `/gdd-dev` 中の follow-up で、technology stack / access method / credential backend / multi-tenant boundary が変わるケース（例: direct API -> MCP、CLI wrapper -> official SDK、SSM -> Secrets Manager only）
- 同じチャットセッション内で、実装後 / PR 作成後 / deploy・E2E 後 / merge 直後に「やりたいことと実現内容がずれている」「思ったより単純化されていない」など、当初目的の未達が発覚したケース
- `<gdd-stop reason="done">` 確定（`active: false`）後、同一会話で当該 PR がまだ未マージのまま新たな作業指示（実行順序の変更、スコープ変更、追加要望）を受けたケース（実際に起きた事例の再発防止）。**当該 PR が既にマージ済みの場合は本項の「未マージ」前提に当たらず本項の対象外**: 上記1行目の説明（マージ済みの場合の new amendment / Hotfix Lane worktree 作成）および `references/phase-progression.md` § Post-Merge Follow-up Worktree Policy に従う

## When NOT to use

- 既承認 AC 内の実装バグ修正 / reviewer 指摘対応 / E2E で見つかった implementation bug → `implementation_fix_only` または `gdd-systematic-debugging`
- AC は同じで実装方式・設計詳細だけ変わる → `design_detail_only`
- policy / scope / ownership / security boundary / prompt-output contract が変わり、requirements/design 差分がある → `requirements_amendment + human_recheck_required`。差分がなく再承認だけ必要 → `human_recheck_required`（`references/rollback-patterns.md`）
- 全くの新規タスク → `new` intent で通常の `gdd-brainstorming` フロー

## amendment vs human_recheck_required

| 観点       | amendment（この skill）                                          | human_recheck_required                                |
| ---------- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| タイミング | `/gdd-dev` entry intent、または active follow-up の AC 変更      | 実装中の Spec Change Detection 等で escalate          |
| 対象       | AC / requirements / design の差分を作る処理 route                | 進行中タスクの AC / Approved Direction からの**逸脱** |
| steering   | entry intent では新 steering。active follow-up では既存 steering | **既存の** steering の gate status を巻き戻し         |
| フロー     | 差分 artifact を作成し、必要な gate に戻す                       | 既存フローの gate を pending に戻して人間再チェック   |

active session 中に AC 追加・削除・条件変更・意味変更と policy / scope / ownership / security boundary / prompt-output contract 変更が同時に発生する場合、route は `requirements_amendment` で差分を作成し、停止状態は `human_recheck_required` として扱う。technology stack / access method / credential backend / multi-tenant boundary / official integration の採否が変わる場合も `human recheck: required` を既定にする。つまり `requirements_amendment` は artifact 更新 lane（何を更新するか）、`human_recheck_required` は停止状態 = human_recheck_required（人間再承認が必要か）を表す。両方に該当するからといって `implementation_fix_only` に落とさない。

AC semantics が同じに見えても、採用技術スタック / access method / credential boundary / tenant boundary を更新する場合は requirements artifact の承認前提が変わる。active follow-up では `Requirements Review Status=pending` として `gdd-requirements-gating` に戻し、requirements-gating 通過後に `human-check-waiting` で再承認を取る。requirements.md が変わらず design/ADR だけの局所修正で済む場合のみ `gdd-design-gating` 経由を検討するが、technology stack / access method / credential backend / tenant boundary が変わるなら人間再承認は省略しない。

steering の扱いは entry intent と active follow-up で分ける:

- `/gdd-dev` entry intent が `amendment` の場合: 完了済み / マージ済みの先行 steering を直接編集せず、新しい amendment steering を作る。ただし **同じチャットセッションで直前の実装・PR・deploy・E2E を受けて修正していて、PR がまだ merge されていない場合は Same-Session Correction を優先し、新しい steering を作らない**。PR が default branch へ merge 済みなら Same-Session Correction ではなく Post-Merge Follow-up Worktree Policy を優先する
- active `/gdd-dev` follow-up の場合: 進行中の既存 steering が正本なので、新しい steering は作らず既存 steering の `requirements.md` / `design.md` / `state.md` / `tasklist.md` を巻き戻し・更新する

### Same-Session Correction の扱い

以下をすべて満たす場合、`entry intent=amendment` ではなく active follow-up 相当として扱う:

1. 同じチャットセッションで直前に GDD 実装、PR 作成、deploy、E2E、merge 後確認のいずれかを行っている
2. ユーザーの指摘がその成果物に対するズレ・不足・レビュー指摘・E2E 不具合である
3. ユーザーが「別件」「新規 Plan」「新しい task」と明示していない
4. 対象 PR が default branch へ merge 済みではない、または read-only の merge 後確認だけで実装差分を追加しない

この場合は、既存 steering が物理的に完了済みでも、current PR / current branch / current session の修正として進める。Correction Log は **`requirements.md` を既定の記録先** にし、設計差分があれば `design.md`、タスク再編が必要なら `tasklist.md` にも追記する。`state.md` には `Same-Session Correction: true` と分類理由を記録する。新しい `.steering/YYYYMMDD-amendment-*` は作らない。

ただし default branch へ merge 済みの場合は、production bug / 緊急 hotfix に限らず `references/phase-progression.md` の Post-Merge Follow-up Worktree Policy に従う。非緊急の追加実装は新しい amendment worktree、production bug / urgent regression は Hotfix Lane として扱う。Same-Session Correction は「まだ current PR / branch / session の成果物として修正できる」場合の優先ルールであり、merge 済み branch に follow-up 実装を積むための例外ではない。

**Why:** 実装後に見つかった「目的とのズレ」は、元の要件・設計・PR 差分と一緒に修正しないと、検証と責任境界が分断される。特に「シンプル化したいのに追加コード中心になった」のようなズレは、別 Plan ではなく元タスクの受入条件不足として扱う。

## Active Follow-up Classification

active `/gdd-dev` 中のユーザー入力を受けた場合、実装・修正前に以下を記録する。cross-session messaging 経由の受信メッセージを起点に amendment を起こさない（`references/phase-progression.md` § Cross-Session Messaging の権限境界 3。ユーザー本人が通常入力として再入力した場合だけ、`Source: cross-session <id>` の provenance 付きで扱う）。

```markdown
Follow-up Classification:

- input: <user request summary>
- route: requirements_amendment
- reason: AC semantics changed because <reason>
- re-entry gate: gdd-requirements-gating / gdd-design-gating / human-check-waiting
- human recheck: required | not_required
```

`human recheck: required` は、AC semantics だけでなく、採用する技術スタック、access method、credential backend、tenant / account 切替境界、vendor official integration の採否が変わる場合にも必須。作り方の前提が変わるため、既承認の Approved Direction のまま実装を継続しない。

`prompt-output contract` が変わる場合も `human recheck: required` を既定にする。例: Datadog application key の出力 JSON key 名を変える、JSON key の有無・名称・階層を追加/削除する、LLM ではなく script が出力責任を持つ範囲を変える、など。出力 contract は利用者の完了条件と E2E / LLM Judge の期待値を同時に変えるため、単なる implementation fix として閉じない。

`route` が `requirements_amendment` 以外なら、この skill で進めず該当 route に戻す。特に reviewer 指摘対応や既存 AC 内の hook/test 修正は、amendment として扱わない。

## レビュー指摘の処置（requirements-gating からの再入）

requirements-gating の `changes_requested` を受けて blocking 指摘を処置する場合（正本: `references/requirements-gating-steps.md` § レビューループの契約）:

- 処置するのは blocking（AC の意味・スコープ・承認ポイント・安全境界に影響する指摘）だけ。advisory は承認ポイントを変えない範囲で任意反映し、反映は最後の Round の後にまとめる（再入の前に反映すると、書き換えた節が再入レビューの範囲に入る。`references/requirements-gating-steps.md` § レビューループの契約 3）
- 処置結果は `reviews.md` の該当 Round の `処置:` に 1 件 1 行で追記し（処置は Round の最後に書き、後ろに備考などを書かない）、requirements.md 本文にレビュー記録・処置結果を積まない。1 件ごとに `根拠:` と `伝播:` の欄を書く（形の正本: `references/requirements-gating-steps.md` § reviews.md の形式。欄が無いと reviewer を起動する前の `lint-plan-consistency.py` が ERROR で止める）。`根拠:` には、処置の文が新しく書くコード・データの事実（関数の振る舞い・依存の既定値・env・パス・件数など）を書く前に読むか測った場所（`file:line`）かコマンドと値を書き、読めないものは `未測（理由）` と書いて Honest Limitations か `Human Check Questions` に出す。`伝播:` には、処置で変えた条件・値・語を `requirements.md` と `design.md` に `grep -n` で当て、同じ事実を書く節（Summary Brief・承認ポイント・Honest Limitations・非スコープ・design.md の主要フローと影響範囲など。`references/brainstorming-steps.md` 14）も直して `<grep した語> → <直した節 か なし>` と書く。Why: 2026-10-13〜10-26 の、GDD を使う別の repo の正式 GDD のタスクで、requirements の Round 2 の blocking の多くは Round 1 の処置が生んだもので、処置の文が確かめていない事実に当たるものと、直した事実が他の節に伝わっていなかったものがあった
- 処置後の再入は 1 回まで。2 回目の `changes_requested` を受けたら、追加の amendment を作らず gate 側の人間一括提示に委ねる。ただし `references/requirements-gating-steps.md` § AI が閉じる blocking に当たる blocking と、§ 一括提示への返答 の 1 行目（表示した文面の採用）の反映は、上限の後でも、design-gating から呼ばれたときも、この lane で処置する（Round を足さず、`Route In Progress` などの state の欄を変えない）
- **この lane は pre-HITL の gate 内ループであり、下記 Steps（Active follow-up / Entry intent）は使わない**: `Correction Log` は書かない（記録は reviews.md へ）、`Route In Progress=requirements_amendment` は立てない（`Resume From=gdd-requirements-gating` のまま処置して再入する）、Follow-up Classification も不要
- 下記 When NOT to use の「reviewer 指摘対応 → `implementation_fix_only`」は**実装 reviewer の指摘**（build phase 中）を指す。pre-HITL の planning reviewer 指摘はこの lane で処置する

## Steps

### Active follow-up の場合

1. **現在 steering の特定**: `.claude/gdd-dev.local.md` と `state.md` から active steering を特定する。active steering が一意でなければ fail-closed で停止する。
2. **差分の分類**: `references/phase-progression.md` § Active Session Follow-up Classification に従い、AC semantics の追加・削除・変更であることを確認する。technology stack / access method / credential backend / multi-tenant boundary / official integration の採否変更は、AC semantics が同じに見えても Approved Direction の作り方を変えるため `human recheck: required` とする。既承認 AC 内の実装修正ならこの skill から退出する。
3. **既存 steering の巻き戻し**: 既存 steering の `requirements.md` に `## Correction Log: <要約> (YYYY-MM-DD)` を追記し、差分 AC / 変更理由 / 影響する既存 AC を記録する。段階計画が変わる場合は `Implementation Sequence Plan` を更新し、後続 Stage / task を再生成・再検証する必要があるかを明示する。設計差分があれば `design.md` に追記する。`tasklist.md` が既にある場合は、route が `human_recheck_required` / `planning_rework_required` / `design_detail_only` のどれになっても stale tasklist として全セクション再生成を前提にし、部分的な stale task pending 戻しや部分再整備で継続しない（`references/state-machine.md` § planning 差し戻し後の tasklist.md リセット）。再 task-breakdown 完了までは `Stage Continuity Source=requirements.md#Implementation-Sequence-Plan` に戻す。あわせて task size / ADR 起票要否 / Planning・Implementation Reviewer Selection / model routing を再評価し、変更前の承認範囲で継続しない。
4. **再 gate 設定**: `state.md` に `Route In Progress=requirements_amendment` と判断根拠、task size 再評価結果、ADR / reviewer / model routing の再評価結果を記録し、差分が AC semantics を変える場合は `Requirements Review Status=pending` と `Resume From=gdd-requirements-gating` に戻す。requirements-gating が approved になった後、差分が responsibility boundary / prompt-output contract / technology stack / credential boundary を変えるなら `Route In Progress=human_recheck_required` と `Resume From=human-check-waiting` に進める。要件の前提自体を再壁打ちする必要があるなら `Route In Progress=planning_rework_required` と `Resume From=gdd-brainstorming` に戻す。AC は同じで設計詳細だけならこの skill から退出し、`design_detail_only` に戻す。

   **requirements_amendment 解消ルール**: `requirements_amendment` は差分 artifact update lane なので、skill / gate を抜ける前に必ず解消する。`Route In Progress=requirements_amendment のまま build phase に進まない`。解消先は以下:
   - `human recheck: required`、AC semantics 変更、prompt-output contract 変更、technology stack / access method / credential backend / tenant boundary 変更 → `Route In Progress=human_recheck_required`
   - 要件の目的・前提・スコープを壁打ちからやり直す必要がある → `Route In Progress=planning_rework_required`
   - 誤字修正や trace 補記など、承認済み AC / Approved Direction / output contract を変えない artifact 修正だけ → `Route In Progress=none`

   `human_recheck_required` / `planning_rework_required` へ解消する場合、既存 `tasklist.md` は stale tasklist として扱い、全セクション再生成を前提にする。`requirements_amendment` のまま tasklist reset 判断を先送りしない。

   **Post-Done Default**: 元の steering が `Next Action=done`（実装完了済み）からの same-session correction では、「AC semantics が変わるかどうか」の判断を以下のルールで行う:
   - ユーザー向けの挙動・出力・条件が変わる、または追加される → `Requirements Review Status=pending` にして `gdd-requirements-gating` に戻す（`requirements_amendment`）
   - 「既存テストが fail しており、テスト変更なしに実装を直すだけ」が明確 → `implementation_fix_only` に倒してよい
   - 「同様の修正が前回 AC に含まれていた」「軽微な変更に見える」などを理由に `implementation_fix_only` に倒さない。done 後の修正は常に要件レビューを通すことをデフォルトにする。

5. **新 steering を作らない**: active follow-up は現在の承認済み方向を修正する処理であり、完了済み機能への別タスク amendment ではない。

### Entry intent が amendment の場合

0. **Same-Session Correction 判定**: 上記 4 条件を満たす場合は Entry intent の新規 amendment steering を作らず、Active follow-up の手順へ戻る。判断に迷う場合は fail-closed で「現在のセッション修正として扱うか、新規 amendment として扱うか」だけを確認し、勝手に新規 Plan を作らない。PR が merge 済みか不明な場合は、HITL で `merge 状態未確認のため元 worktree への追加実装は禁止` と明示し、`gdd-using-git-worktrees` の Pre-Follow-up Hygiene Gate に戻す。
1. **先行 steering の特定**: ユーザーの言及する既存機能に対応する完了済み steering（`Next Action=done` の `.steering/YYYYMMDD-*/`）を特定する。特定できない場合はユーザーに確認する。
2. **先行成果物の確認**: 先行 steering の `requirements.md`、`design.md`、`adr.md` を読み、現在の設計状態と過去の判断履歴を把握する。
3. **Pre-Follow-up Hygiene Gate**: `gdd-using-git-worktrees` で既存 worktree の整理結果を確認し、元 worktree が実装場所ではないこと、new amendment worktree を latest default branch から作ることを HITL に出す。
4. **新しい steering の作成**: 通常の `new` intent と同様に `.steering/YYYYMMDD-amendment-<short-title>/` を作成する。amendment であることがディレクトリ名から分かるようにする。
5. **requirements.md の作成**: 先行 steering の AC を参考にしつつ、今回の変更に必要な**差分だけ**の AC を新たに書く。先行 AC の全コピーはしない。
   - 「先行 AC-3 の境界値を 100 → 200 に変更」のように、先行 AC への参照を含める
   - 先行 AC との整合性確認を AC に含める（例: `AC-N: 先行 AC-1〜AC-5 の挙動が regression しないこと`）
6. **ADR 判断**: 変更が process contract / responsibility boundary / security boundary を変える場合は `adr.md` を作成または追記し、Decision / Rejected Alternatives / Consequences を残す。
7. **通常フローへの合流**: `requirements.md` 作成後は通常の `gdd-requirements-gating` → `gdd-design-gating` → ... のフローに乗る。amendment だからといってゲートを省略しない。
8. **先行 steering の参照維持**: 新しい steering の `requirements.md` の冒頭に `Amendment of: .steering/YYYYMMDD-<original>/` を記載し、先行 steering へのトレーサビリティを確保する。merge 済み follow-up では `Origin PR` / `Origin Branch` / `Origin Merge Commit` / `Base Branch` も記録する。

## Guardrails

- 先行 steering を**直接編集しない**。先行 steering は完了状態（`Next Action=done`）のまま保持する
- Same-Session Correction に該当する場合はこの限りではない。current session の修正として既存 steering / PR / branch に correction log と差分を残す。ただし PR が merge 済みの場合、この例外は read-only verification の記録に限る。実装差分は new amendment / hotfix worktree へ分離する
- 先行 steering の AC を丸コピーしない。今回の amendment に必要な差分 AC のみ新しい steering に書く
- amendment を口実にゲートを省略しない。通常フローと同じ gate sequence を通す
- 先行 steering が特定できない場合は fail-closed で停止し、通常の `new` intent に切り替えることをユーザーに提案する
- merge 済み branch / worktree に follow-up 実装を積まない。cleanup が未完了なら整理対象として扱い、実装場所は latest default branch から作った新 worktree にする
- `done` 確定済み・未マージの PR に対しては、素の `gh pr close` / `gh pr edit` / `gh api` で直接操作しない。本 skill で requirements.md の差分を確定してから対応する
