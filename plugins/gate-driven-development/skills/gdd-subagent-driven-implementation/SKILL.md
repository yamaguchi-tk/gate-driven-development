---
name: gdd-subagent-driven-implementation
description: "Internal: auto-routed only when Next Action=gdd-subagent-driven-implementation. Runs GDD implementation workers."
version: 0.1.0
contract_terms: "GREEN-verified; REFACTOR-reverified"
---

# Subagent Driven Implementation Lite

承認済み task を小さく安全に実装する。

Loop owner の正本は `references/state-machine.md` § Goal-Driven Loop Ownership。`gdd-subagent-driven-implementation` は implementation inner loop を所有し、outer loop / Goal 達成判定 / root cause 確定を所有しない。

Inner loop handoff: return implementation status to the outer loop with changed files, verification evidence, and remaining concerns. This skill does not decide Goal completion; `DONE` / `DONE_WITH_CONCERNS` は completion claim ではなく、outer loop または completion gate が fresh evidence を読んで `verified_done` を判断する。

## Fixed Model

- `Claude Code`: worker subagent の model・effort は、task の `Complexity:` と `Gate Rounds` で選ぶ agent 定義が決める（`standard` は `sonnet` + `effort=medium`、それ以外は `opus` + `effort=high`、`Gate Rounds` ≥ 2 は `opus` + `effort=xhigh`。inline は main の model。正本: `references/fixed-models.md` の `implementation` tier の段落）
- `Cursor`: `Composer 2.5`（`composer-2-fast` は使用しない）
- `Codex`: `gpt-5.6-terra` + `reasoning.effort=low`

## Phase Gate Pre-check（必須）

`references/phase-gate-prechecks.md` § Template A（3-Gate Approval Required）を実行する。Task Size 別の必須フィールド検査と戻り先 phase 提示は同 reference を正本とする。

## Goal

- task 単位または小 batch 単位で実装する
- `Execution Plan` が `parallel` の場合、同一バッチ内の独立タスクを subagent で並列実行する
- 実装後は必ず REFACTOR チェックポイントを通す
- 実装後レビューで出た指摘をリファクタで解消する
- review 差し戻し時は、差し戻しの理由になった finding（`gdd-implementation-gating` Step 9 の述語に当たるもの）を `High` -> `ops-blocking medium` -> その他 `Medium` の順で最小差分修正する。直す順序は `references/self-review-lanes.md` § 直し方 に従い、worker に渡す prompt の Constraints でこの節を指す。Advisory Findings に記録した finding は直さない。guard に deny の分岐（拒否する条件・上限・受理する集合の縮小）を足す修正は、先に `references/self-review-lanes.md` § 修正時規律 の規律 C で、新しく deny になる入力を本番で誰が何件出すかを測る
- RED 後の GREEN / REFACTOR を担い、review handoff 可能な差分に仕上げる
- 承認済み要件・実装方針と AI gate 通過済み detailed design から逸脱しない
- review に渡せる差分を作る
- plugin 外 workflow に依存せず、承認済み artifact と RED だけを根拠に進める

## Current Task Readiness Review

before touching code に `Current Task Readiness Review` を行う。critical plan gaps、missing dependency、instruction unclear、planned verification の欠落を確認し、問題があれば実装せず `gdd-task-breakdown` など適切な route に戻す。

## In-Progress AC Trace Updates

GREEN 成功時は AC Trace Ledger（`ac-ledger.md`。`references/ac-trace-ledger.md`）に `GREEN-verified` を append-only で追記する。REFACTOR 後に同じ検証を再実行し、`REFACTOR-reverified` を追記する。subagent の DONE だけで pass にせず、controller が fresh verification を読んで記録する。

## Subagent Prompt Contract

superpowers の subagent / parallel dispatch prompt discipline を GDD の controller 責務に吸収する。subagent は親 session の暗黙 context を継承しない前提で、controller が **self-contained context** を渡す。

subagent prompt には最低限、以下を含める:

- **Specific scope**: 対象 task ID、AC ID、変更対象 file、実装してよい範囲。
- **Constraints**: 承認済み technology stack / access method / credential backend / security boundary / Do NOT touch file や非スコープ。差し戻しの修正で guard に deny の分岐を足すなら、controller が先に規律 C（`references/self-review-lanes.md` § 修正時規律）で測った結果を渡す。worker が自分の判断で deny の分岐を足すことにしたら、足す前に `NEEDS_CONTEXT` で返させる。差し戻しの修正では、直す順序として `references/self-review-lanes.md` § 直し方 を指し、§ 直し方 5 の材料として `worklog.md` の § Error Log の行をすべて渡す（前の Round を選ばない。同じ部品の修正が続いたかは worker が判定する。行が無ければ渡さず、worker は § 直し方 5 の記録に `材料なし` と返す）。
- **Expected output**: `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` の status、変更概要、実行した verification、残 issue、触った files、**`Carry Forward` 候補**（次段がそれを知らないとブロックされる / 誤った前提で進む実測値。確定したシグネチャ・定数名・環境変数名・実行時に判明した制約・未解決の申し送り。無ければ `なし`）、差し戻しの修正では § 直し方 4・5 の記録（比べた案と採った理由、部品が要るかの答え。当たらなければ `なし`）。controller はこれを規律 C と同じ記録先に写す。この報告が唯一の供給源で、subagent の文脈は境界で破棄されるため、ここに出なかった事実は復元できない。
- **Do NOT touch**: 同一 batch の他 task、root 側 `.steering/`、unrelated services、secret / `.env`、AGENTS.md が禁止する write 操作。
- **Verification handoff**: `Planned Verification` と RED Evidence を明記し、subagent の成功報告だけで task 完了扱いにならないことを伝える。
- **Carry Forward（上流からの引き継ぎ）**: `tasklist.md` の **直近 1〜2 task** の `Carry Forward:` をそのまま渡す。上流で確定した実測値を知らずに実装させると、同じ調査をやり直すか誤った前提で進む。**渡すのはこの欄だけ**で、他 task の実装詳細・試行錯誤・ログは渡さない（境界での破棄は意図した設計であり、ここはその例外を最小限に切る枠）。

prompt がこの契約を満たさない場合は、subagent を起動せず controller 側で prompt を補強する。`requirements.md を読んで適当に進めて` のような broad prompt は禁止。

## Codex Subagent Delegation Permission

Codex では、`state.md の Approved Direction` に `Codex Subagent Delegation Permission` があり、`approved_by_explicit_delegation` / `approved` と `explicit_delegation_source` が確認できる場合だけ subagent を起動する。Codex では許可が無いまま subagent を起動しない。許可がない場合は main session inline execution として同じ contract を逐次実行する。

## Steps

1. plugin 内 `references/contract-overview.md`、`references/state-machine-overview.md`、`references/self-contained-contract.md` の relevant な制約を確認する（詳細な遷移表が必要なら `references/state-machine.md` を参照）。
1a. **Implementation Guidance（実装品質の前提確認）**: コードを書き始める前に、次の順で「このプロジェクトではどう書くべきか」を把握する。
   - プロジェクトのコード規約ファイル（`CONVENTIONS.md` 等）があれば読む。命名規則、アーキテクチャ制約を確認する
   - 変更対象ファイルの既存コードを Read し、使われているパターン（命名規則、import 構成、エラーハンドリング、ログ形式）を把握する
   - 同じモジュール内の類似ファイルがあれば 1-2 ファイル参照し、一貫したスタイルで実装する
   - worktree 直下の `docs/learned-patterns.md`（置き場の正本は `references/cross-task-learning.md`）があれば読む。過去タスクで確定したパターンや却下された代替案を確認する
   - **テストに mock / stub を入れる場合は `references/testing-anti-patterns.md` を参照**。mock の振る舞いを検証するテスト・production class へのテスト専用メソッド追加・partial mock は禁止パターン。Iron Laws を満たす mock 設計を守る
   - **Tasklist Freshness Check**: `design.md` を読んだ後、`tasklist.md` の全タスクの `Covers AC:` 行を横断して、`design.md` の `受入条件` に列挙された AC ID が網羅されているかを確認する。`design.md` に存在するが `tasklist.md` のどのタスクにも `Covers AC:` されていない AC が 1 件以上あれば、tasklist が stale である可能性がある。stale が疑われる場合は実装を始めず、未カバー AC を列挙した上で `Next Action=gdd-task-breakdown` に設定して再分割を先行する。**Why**: task-breakdown 完了後にユーザーが設計変更を行い tasklist と乖離した状態で実装が進む事例が複数のセッションで発生した。AC カバレッジの cross-check により、filesystem 依存なく任意環境でストール前に検出できる
   - **Why:** テストを通すだけでなく、プロジェクトの既存コードと一貫したスタイルで実装することで、reviewer 差し戻しを減らし「良い感じに実装してくれた」体験を実現する。パターンの事前把握は短い Read で済むが、reviewer 差し戻しの修正ループはそれよりずっと長くかかる
1b. **Plan Execution Readiness Review（実行前の批判的レビュー）**: code を書き始める前に、`tasklist.md` の `Current Task` を execution plan として読み、欠陥があれば実装へ進まず route を決める。
   - `Current Task` の `Covers AC:` / `Depends on:` / `Steps` / `Planned Verification:` / `Stop Conditions:` / `Return Route:` を確認する
   - steps が抽象的、検証が曖昧、依存が未解決、または task が 1 回の集中作業で終わらない場合は `Execution Status: blocked` に更新し、`worklog.md` に理由を書く
   - **Plan Execution Stop Conditions**: blocker / missing dependency / instruction unclear / verification repeatedly fails / active worktree ambiguity に該当したら停止する。同じ入力・同じ model で retry しない。`verification repeatedly fails` は、同じ Planned Verification command が **2 回連続**で同じ原因または same failure signature により失敗した状態を既定閾値とする
   - **Return to Plan Review**: partner updates the plan、または fundamental approach の見直しが必要になった場合は、GDD の planning gate へ戻す。AC / scope / policy が変わるなら `gdd-requirements-amendment` または `human_recheck_required`、要件は不変で設計詳細だけなら `gdd-design-gating`、方向性や task 粒度から組み直すなら `planning_rework_required` で `gdd-brainstorming` に戻す
   - verification failure と承認済み artifact からの逸脱が同時に起きた場合は、追加 debug route よりも設計逸脱を優先して route する。technology stack / access method / credential backend / external service / policy / scope / security boundary が承認済み trace から外れるなら `human_recheck_required` とし、silent に design detail として吸収しない。純粋な test failure だけなら debug route（`gdd-test-failure-debug-pack` / `root-cause-investigation` / `gdd-systematic-debugging`）に進む。設計逸脱を優先した場合も verification failure の証跡は捨てず、人間確認後に元の設計で続行するなら debug route へ、変更承認されたなら `gdd-requirements-amendment` / `gdd-design-gating` へ接続する
   - route を変えずに実装できる場合だけ `Current Task Execution Status` として `Execution Status: in_progress` を `tasklist.md` に反映し、実装へ進む（Gate Batch では手順 2b の対象の task だけに書き、実装を終えた task の `completed` は変えない）
2. `tasklist.md` の `Execution Plan` セクションを確認する。`Mode: parallel` の場合は Step 2a に進む。`Mode: sequential` または `Execution Plan` が無い場合は Step 2b に進む。
2a. **並列実行パス**: 現在のバッチを特定し、バッチ内の全タスクに対して RED を確認した上で、subagent を並列に起動する（worker の選び方と `## Plugin Root` の受け渡しは手順 3 と同じで、task ごとの `Complexity:` と `Gate Rounds` による）。各 subagent には対象タスクの情報（AC、Files、Steps）と design.md の該当セクションに加えて `## Worktree`（絶対パス。`references/subagent-dispatch.md` § Worktree Binding Precheck 必須。GREEN で production code を書く phase のため RED と同じ precheck を課す）を渡す。全 subagent が GREEN + REFACTOR を完了したら、手順 17 の「gate の前の RED Evidence の確認」をしてから、バッチ内の全タスクをまとめて `gdd-implementation-gating` に回す。バッチ内の 1 タスクが失敗しても他タスクは継続する（失敗タスクだけ retry する）。
   - **Parallel Dispatch Integration Discipline**: 並列化は **Independent Domains** に限定する。one agent per problem domain を原則とし、同一ファイル・同一 API・同一 state field・同一 external resource を触る task は sequential に降格する
   - **Parallel Safety Conditions**: 並列実行は no shared state / no order dependency / no overlapping files / no shared external resource を満たす場合だけ許可する。state.md / tasklist.md / worklog.md / `.steering/` の更新は controller is the only writer とし、subagent は直接書き込まない
   - **Integration review**: 全 subagent が返ったら controller が review each summary → check for conflicts → run full suite の順で統合確認する。個別 subagent の pass を足し合わせて batch pass としない
   - **独立性確認（起動前）**: 同一ファイルへの編集がバッチ内で重複しないか、共有 resource（DB schema 変更、同一 API エンドポイント、共有 config ファイル）への競合がないかを確認する。競合がある場合は affected タスクを sequential に移行する
   - **tasklist.md 書き込み制約（並列時必須）**: 並列実行中の subagent は `tasklist.md` を**直接編集しない**。Attempts 記録・task status 更新・AC Owner Migration 等の tasklist.md への書き込みは、すべて controller（親 session）が subagent の完了報告を受けて集約する。subagent が同時に tasklist.md を書くと lost update が発生する（一方の Attempts が消える）。subagent は作業結果を完了報告（`DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` + 詳細）で返し、controller がまとめて tasklist.md に反映する
   - **Conflict Detection（全 subagent 完了後）**: `git status` と `git diff` で merge conflict や unexpected な変更がないかを確認する。conflict がある場合は手動で解消する。そのうえで、conflict の有無を問わず手順 17 の「gate の前の RED Evidence の確認」をしてから `gdd-implementation-gating` に進む
2b. **逐次実行パス（従来通り）**: `tasklist.md` の `Current Task` にある task と対応 AC を確認する。Gate Batch で複数の task が並ぶときは、`Execution Status: completed` でない task（差し戻し後は、impl-gating が `in_progress` に戻した対象の task すべて）を対象にする。active worktree 側 `.steering/.../adr.md` があれば、既に確定した重要判断を補助コンテキストとして読む。
3. 実装は小さく分ける。必要なら subagent を使う（dispatch 時は常に `## Worktree` を渡し § Worktree Binding Precheck を必須実行させる）。Claude Code では、worker の `subagent_type` を task の `Complexity:` と `Gate Rounds` で選び、`model` は省略し、`## Plugin Root`（`${CLAUDE_PLUGIN_ROOT}`）も渡す（`Gate Rounds` ≥ 2 → `gate-driven-development:gdd-remediation-worker`、`Complexity: standard` → `gate-driven-development:gdd-implementation-worker`、それ以外 → `gate-driven-development:gdd-implementation-worker-heavy`。正本 `references/fixed-models.md`）。`remediation_loop` 中（`Gate Rounds` ≥ 2）は subagent を省略せず `gdd-remediation-worker` を dispatch し、inline では修正しない（Claude Code の場合。Cursor / Codex は worker runner が tier 表の host 別モデルを解決する）。phase 名、artifact 保存先、`Next Action`、gate 順序、reviewer 構成は変えない。implementer subagent が質問してきた場合、「design.md に書いてある」「requirements.md を参照」だけで返さず、具体的な行・値・パターンを示した上で回答する。subagent が不完全な情報のまま実装を進めると、reviewer 差し戻しが増える。
   - **subagent への完了報告指示**: subagent を dispatch するときは、完了時に `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` のいずれかで status を明示するよう prompt に含める。report を受け取ったら、下記 `Implementer Status Handling` セクションに従って処理する
4. `build-implementer` という外部 workflow には依存しない。判断根拠は承認済み `requirements.md` / `design.md` / `tasklist.md` と `gdd-test-driven-development` で確定した RED だけに限定する。
5. planning へ差し戻す場合は `references/rollback-patterns.md` の該当パターンに従い Gate Status を永続化する。
6. planning の組み直しが必要なら `planning_rework_required` パターンで `gdd-brainstorming` に戻す。
7. 承認済み policy / scope / ownership / security boundary / prompt-output contract / technology stack / access method / credential backend / multi-tenant boundary / official integration adoption を跨ぐ変更だけで人間判断が必要なら `human_recheck_required` パターンで永続化する。runtime / packaging / env / dependency / API mismatch は、approved scope と採用方式の範囲内なら `design_detail_only` または `implementation_fix_only` に倒す。
8. 要件は変わらないが detailed design の修正が必要なら `design_detail_only` パターンで `gdd-design-gating` に戻す。
9. task が大きすぎる場合は、build フェーズから直接 `Next Action=gdd-task-breakdown` に戻さない。planning の見直しが必要なら `gdd-brainstorming` に、狭い人間判断だけなら `human-check-waiting` に、detailed design の見直しだけなら `gdd-design-gating` に差し戻し、承認後に `gdd-task-breakdown` をやり直す。
10. active worktree を一意に解決できない状態で build に入っていた場合は fail-closed で停止し、state 修復または active worktree の特定を要求する。
11. **Spec Change Detection（仕様変更の反映を強制）**: 実装中に以下のいずれかに該当する判断が発生した場合、**必須**で active worktree 側 `.steering/.../adr.md` を追記し、該当する artifact（`requirements.md` / `design.md`）を同じ diff 内で更新する:
    - `design.md` に記載されていない API / データ形式 / UI 挙動 / 外部 I/F を実装した
    - AC の文言と異なる挙動を実装した（境界値、エラー処理、空ケース、失敗時の挙動等）
    - brainstorming で承認された代替案と異なる approach を採用した
    - 承認済みの `実装方針` と異なる technology stack / access method / credential backend / multi-tenant boundary / official integration adoption を採用した
    - E2E Discovery（動かして判明した制約）で、AC または `Approved Direction` の前提に影響する設計変更が発生した

    記録要件（`references/adr-vs-design.md` の書き分けルールに従う）:
    - `adr.md`: `Context` / `Decision` / `Why` / `Consequences` を追記（1 変更 1 エントリ）。`state.md` の `Route In Progress` が `none` 以外（remediation 中）なら `- **Origin**: remediation / <Current Task>` 行も必須（`references/state-machine.md` § Remediation Loop Safety の ADR ≥2 独立トリガーが数える）
    - `requirements.md`: AC 本文に影響する変更（境界値、エラー処理、新 AC、AC 削除）は該当 AC を更新
    - `design.md`: 設計判断（Route / Ownership / Sensitive Data / enforcement point 等）が変わる場合は該当セクションを**現在の正しい設計に上書き更新**する（差分は git で見る）

    **Reviewer Lineage 影響判定（必須）**: 上記いずれかの仕様変更が以下に該当する場合、`tasklist.md` の `Implementation Reviewer Selection` に reviewer 種別追加を提案する（`root-cause-investigation` の Phase 4 SMI と対称的な構造）:
    - auth / secrets / trust 境界 / IAM / 認可ロジックに触れる変更 → `gdd-security-reviewer` を Lineage に追加
    - terraform / IaC ファイルへの変更を含む → terraform checklist reviewer を Lineage に追加
    - 既に追加済みなら no-op（重複追加しない）
    - 追加根拠は `adr.md` の `Why` を流用し、`Implementation Reviewer Selection` の selection rationale に 1 行追記
    - **追加 entry には `added_by: impact_block` と `source_signal: <仕様変更の 1 行要約>` を必ず記録する**（completion-check Post-Completion Learning が学習 pattern として capture するため）

    **記録形式例**:

    ```markdown
    - reviewer: gdd-security-reviewer
    - status: selected
    - reason: Spec Change Detection — auth middleware の signature 変更を実装
    - added_by: impact_block
    - source_signal: signRequest() の HMAC 検証ロジック追加（auth boundary 拡張）
    - added_at: 2026-05-12T14:30:00+09:00
    ```

    escalation:
    - **AC の根本追加 / 削除 / 意味変更**を伴う場合は silent に更新せず `human_recheck_required` に昇格する（`references/rollback-patterns.md`）
    - **Approved Direction の方向性自体**が変わる場合も `human_recheck_required` に昇格する
    - **technology stack / access method / credential backend / multi-tenant boundary / official integration adoption** が承認済み trace から変わる場合も `human_recheck_required` に昇格し、単なる dependency self-heal として閉じない

    単なる実装内部のリファクタ、命名変更、import 整理等で外部観測可能な挙動が変わらない変更は追記不要。

    **State Machine Impact Block の出力（handoff 時必須）**: 仕様変更を含む実装を完了したら、`Next Action=gdd-implementation-gating` に handoff する際に出力末尾へ以下の block を含める（root-cause-investigation の SMI block と対称）:

    ```markdown
    ### State Machine Impact（実装由来の波及）

    - **ADR 起票**: 要 / 不要（理由: <Step 11 の 4 トリガーから該当のみ列挙、slash 区切り>）
    - **Reviewer Lineage 追加提案**: なし / `gdd-security-reviewer` / `terraform checklist reviewer` / <他>
    - **Routing 提案**: `gdd-implementation-gating`（通常時）/ `human-check-waiting`（AC 根本変更 or Approved Direction 方向性変更時）
    - **判断根拠**: <AC / scope / contract への影響 1-2 行>
    ```

    仕様変更が一切無い純粋実装の場合は block 自体を省略してよい。block 受け取り側（`gdd-implementation-gating`）は Reviewer Selection 適用と Routing 確認に使う。

    **Why**: 仕様変更が silent に実装されると、completion-check で AC と実装が一致していても AC 自体が古いため意味を成さない。ADR がないと次回の brainstorming で同じ議論が繰り返される。`gdd-implementation-gating`（checklist）/ `gdd-completion-check`（AC Drift Check）/ `gdd-pr-review`（Spec Drift Check）の 3 層で検出されるため、実装段階で記録する方が手戻りが小さい。Reviewer Lineage 提案と State Machine Impact Block により、root-cause-investigation の Phase 4 SMI と同じ構造で波及点を残せる（state machine 一体型 implementation としての差別化）
12. 実装後に関連 test を更新する。`Verification` の formal update は `gdd-completion-check` の責務として残し、この skill では必要な evidence を集めるところまでに留める。
12b. **Task-Level Verification**: `Current Task` を `Completed Tasks` へ移す前に、task entry の `Planned Verification:` を実行し、`Verification Evidence` として command / test 名 / 結果 / 未実行なら理由を `tasklist.md` または `worklog.md` に記録する。同時に task entry の `Carry Forward:` を埋める（実装文脈はこの境界で破棄されるため、**次段が知らないと詰まる実測値**だけを残す。判定基準・上限は `references/context-budget.md` § Carry Forward。該当が無ければ `なし`）。
    - verification 開始時に `Current Task Execution Status` を `Execution Status: verifying` に更新する
    - verification が通らない場合は `Execution Status: blocked` にする。同じ Planned Verification command が **2 回連続**で同じ原因または same failure signature により失敗したら、Plan Execution Stop Conditions の `verification repeatedly fails` として扱う。純粋な test failure なら `gdd-test-failure-debug-pack` / `root-cause-investigation` / `gdd-systematic-debugging` へ route する。承認済み design / technology stack / policy / scope の逸脱も同時に検出された場合は、debug route より設計逸脱を優先して `human_recheck_required` など planning route に戻す。人間確認後に元の設計で続行する場合は、保存した `Verification Evidence` を入力に debug route を再開する。変更が承認された場合は requirements/design を更新してから改めて task-level verification を行う
    - subagent の完了報告だけで `Completed Tasks` に移さない。controller が `git diff` / `git log` / test 再実行 / evidence 確認で独立検証してから次へ進む
    - verification が通り、REFACTOR / Self-Correct Pass / handoff 条件を満たした場合だけ `Execution Status: completed` に更新できる
13. task 完了ごとに `tasklist.md` を re-read し、`Current Task` / `Pending Tasks` / `Completed Tasks` を更新する。長い実装中に AC や次タスクを見失わないための periodic re-read（planning-with-files の 2-Action Rule に相当）。
14. GREEN を通したら、機能追加ではなく REFACTOR チェックポイントを必ず 1 回実施する。以下の観点から安全に直せるものを最低 1 つは改善する:
    - **命名**: 変数名・関数名・ファイル名がプロジェクトの命名規則と一致しているか
    - **重複**: DRY 原則の適用（同じロジックが 3 箇所以上に散在していないか）
    - **分割**: 1 関数 1 責務になっているか（長すぎる関数の抽出）
    - **コメント**: 自明でないロジックへの説明（理由・意図を書く。動作説明は不要）
    - **プロジェクトパターンの一致**: エラーハンドリング・ログ形式・return 型が既存コードと一致しているか（`Step 1a` で確認した規約と照合する）
    - **不要 abstraction / import の除去**
    - **skip 許可条件**（以下のいずれかに該当する場合のみ skip し、理由を worklog に残す）:
      - task の変更行数が 10 行以下
      - テストファイルのみの変更
      - 外部 API の stub / mock 追加のみ
      - 自動生成コード（migration ファイル、schema 生成等）のみ
    - 上記に該当しない場合は最低 1 つの改善を必須とする。「改善点が見つからない」は理由として不十分 — 命名・コメント・不要 import のいずれかは常に改善余地がある
14a. **自動簡素化パス（Task Size 分岐あり）**: REFACTOR チェックポイントの一部として、`gdd-code-simplifier` agent を dispatch して差分を自動整理する。
    - **`quick (express)`**: agent を起動しない。inline で済ませる（agent 起動の overhead を避ける）
    - **`standard` / `quick (standard)` / `quick (express → standard)`**: `gdd-code-simplifier` を dispatch する（`## Worktree` を渡し § Worktree Binding Precheck を必須実行させる）。agent が「テスト再実行 green」を確認してから制御を返す。green が確認できなければ agent が編集を破棄して報告するので、受け取り後に REFACTOR-reverified の記録を行わず Step 14 の手動観点に戻る
    - 簡素化後に AC Trace Ledger（`ac-ledger.md`）へ `REFACTOR-reverified` を追記する（テスト green が振る舞い不変の証明）
    - **Why**: REFACTOR チェックポイントの命名・重複・ネスト整理を人手で行うと抜け漏れが出る。専用 agent に委ねることで機械的に網羅できる。Self-Correct Pass（ハードコード検出・命名照合・known pitfalls）とは観点が異なるため統合しない
14b. **Implementer Self-Correct Pass（旧称: Pre-flight Self-Check）**: REFACTOR 直後、`gdd-implementation-gating` に handoff する前に implementer 側で **機械的に検出可能な問題を自己修正** する。impl-gate の reviewer に判断を委ねるのではなく、implementer がその場で直せる類型に限定する。発見した問題は impl-gate に持ち越さずここで修正する。
    - **ハードコード値スキャン**: `grep` で変更ファイルを走査し、AWS アカウント ID（12桁数字）・IAM ロール ARN（`arn:aws:iam::`）・認証情報・API キーが直接埋め込まれていないか確認する。検出したら環境変数または SecretsManager 参照に置き換えてから次へ進む
    - **環境変数・定数名の照合**: 追加・変更した環境変数名・定数名を `design.md` / `requirements.md` に記載の名前と照合する。不一致がある場合は実装または artifact を修正し、Step 11 に従って `adr.md` に記録する
    - **learned-patterns.md の known pitfalls 確認**: `docs/learned-patterns.md` に「プロジェクト固有のよくある実装ミス」が記録されている場合は、今回の変更がそのパターンに該当しないかを確認する（旧フロー混在・廃止 API 利用・命名規則違反等のプロジェクト固有の落とし穴）
    - **判断軸 — このパスに入れるべき check か?**: 新しい self-correct check を追加するとき、以下を全て満たすときだけここに置く。1 つでも該当しなければ `gdd-implementation-gating` 側の reviewer に委ねる:
      1. `grep` / regex / 名前照合など **機械的に検出できる**
      2. context 理解や設計判断を伴わない（implementer の手元情報だけで判定できる）
      3. 修正方法が一義的（reviewer 主観なしで実装変更できる）
      4. AC drift / scope / security boundary に **直接は触れない**（触れる場合は impl-gate に残す）
      詳細な分類基準は `references/skill-responsibility-matrix.md` § Pair 3 を参照
    - **Why**: 実装セッション log の分析で、impl-gate 差し戻しの主因がハードコード値・命名不整合・プロジェクト固有パターン違反の 3 類型と判明した。これらは全て **機械的検出可能・修正一義的** で、reviewer の独立判断が要らない。REFACTOR と同ターンで implementer 側が潰すことで impl-gate の往復回数を削減する。逆に scope guard / dead code / 設計整合は impl-gate に残す（reviewer の context 理解が必要なため）
15. PR 前 final diff review や security-sensitive change で companion review を入れる場合も、自動起動せず `gdd-requesting-code-review` の明示実行を必須にする。
    - **Early Lightweight Review Handoff**: task completion or natural checkpoint で、後続 task に影響する設計判断・権限境界・HITL 文面・テスト戦略が固まった場合は、formal gate とは別に `gdd-requesting-code-review` を提案してよい。これは advisory review であり、`gdd-implementation-gating` の代替ではない。提案時は対象 diff、BASE_SHA / HEAD_SHA、確認してほしい観点、参照する requirements / design / tasklist を短く添える。
16. advisory review は out-of-band とし、formal gate は引き続き `gdd-implementation-gating` に残す。
17. REFACTOR チェックポイントを終え、review に回せる状態になったら `Next Action=gdd-implementation-gating` に更新する。ただし逐次実行で、`Pending Tasks` の先頭が今の task と同じ `Gate Batch`（`references/task-breakdown-steps.md` § Gate Batch）なら、今の task を `Execution Status: completed` のまま `Current Task` に残し、`Pending Tasks` の先頭の task を `Pending Tasks` から外して `Current Task` の先頭に移し（文脈を注入する hook は task 名を先頭の task から読む）`Next Action=gdd-test-driven-development` にする（gate は Gate Batch の最後の task の後に 1 回だけ回す）。
    - active な `/gdd-dev` run では自律継続（`common-guardrails.md` § 自律継続）に従い same run 内で formal gate まで進める。
    - **gate の前の RED Evidence の確認**: この skill で `Next Action=gdd-implementation-gating` にするとき（手順 2a・20 を含む）は、その前に、gate にかける task（Gate Batch では gate にかける全 task）の `#### RED Evidence` を確かめる。`gdd-implementation-gating` の Step 1d は、`Worktree:` の行が無いか値が gate の worktree と違うと、reviewer を起動せずに High で差し戻す（`test:` のファイルが差分にも未 commit の分にも無いときも同じ）。`test:` か `verification:` の行は `gdd-test-driven-development` の形式として要る。`gdd-completion-check` の差し戻しで作った remediation task と、`gdd-test-driven-development` を経ずに進めた task では欠けやすい。
      - 節か行が欠けていたら、その task で観測した RED の結果（TDD の runner・自分・worker のどれが観測したものでもよい。`references/rollback-patterns.md` の RED 再現テストを含む）を、同 skill の形式で書き写してから gate に回す（節が無ければ作り、`AC:` の行も同 skill の形式どおり書く。task に `Covers AC:` が無い remediation task では、差し戻しの元の finding が AC ID を明示しているときだけその ID を書き、明示していなければ推定で書かない（AC と task の紐付けの正本は `gdd-task-breakdown` の `Covers AC:`。`lint-ac` の WARN は残る）。無い `Worktree:` の行は `references/subagent-dispatch.md` § Worktree Binding Precheck で今観測した値で足す）
      - 既にある `Worktree:` の値が今の観測値と違うときは書き換えない（Step 1d が差し戻す本来の場面である）。書き写す RED の `test:` のファイルが差分にも未 commit の分にも無いとき（変えていない既存のテストで RED を観測したとき）も、書き写さない（Step 1d が差し戻す。差し戻しの後に戻った `gdd-test-driven-development` は、この形の節を記録済みに数えずに RED を取り直す）
      - 観測した RED が無い task は、書き写さず推定で埋めずに、そのまま gate に回す（差し戻しの後は `gdd-systematic-debugging` が扱う）。ここで `gdd-test-driven-development` には戻さない（Gate Batch で `completed` のまま残る task は TDD の対象に入らないため。差し戻しの後に RED を取り直すかは `gdd-systematic-debugging` が route で決める）
18. `gdd-implementation-gating` で差し戻しになった後に再入した場合は、新機能追加ではなくレビュー指摘の解消（リファクタ）を優先する。
19. 差し戻し再入時の優先順位は `High` -> `ops-blocking medium` -> その他 `Medium` に固定し（対象は差し戻しの理由になった finding だけ）、まず実運用影響のある blocker を落とす。
20. `High` と `ops-blocking medium` を潰す前に cosmetic cleanup や scope 拡張へ寄らない。修正後に、手順 17 の「gate の前の RED Evidence の確認」をしてから、再び `Next Action=gdd-implementation-gating` に戻す。

## Implementer Status Handling（subagent 完了報告の扱い）

implementer subagent は以下の 4 値 status のいずれかで報告する。controller（この skill）は status ごとに定められた処理を行い、単純な retry ループに陥らない。

- **`DONE`**: 実装・テスト・コミット・self-review まで完了した
  - → `git diff` / `git log` で独立検証してから `gdd-implementation-gating` に handoff
  - subagent の「完了」報告だけを根拠に `Completed Tasks` に移さない（詳細: `references/verification-before-completion.md` § Subagent 報告の独立検証）

- **`DONE_WITH_CONCERNS`**: 完了したが subagent 自身が懸念を挙げた
  - → 懸念を先に読み、次の 3 種類に分類する:
    1. **仕様乖離 concern**（「design.md と異なる実装になった」「AC の境界値を変更した」「新しい field を追加した」等、artifact との差分を subagent が自覚している）
       - → Step 11 の Spec Change Detection に従って `adr.md` を追記し、必要なら `requirements.md` / `design.md` を同じ diff 内で更新する
       - 記録が完了した時点で review に進める（再実装の必要なし）
       - AC の根本追加 / 削除 / 意味変更を伴う場合は `human_recheck_required` に昇格する（review に進めず planning に戻す）
    2. **正しさ / scope concern**（実装バグ疑い、scope 違反の疑い）
       - → review に進む前に解消する（controller が追加指示して subagent を再 dispatch）
    3. **観察 concern**（「このファイルが大きくなってきた」「同じパターンが 3 箇所ある」等の metacode observation）
       - → メモしてから review に進む。observation は `docs/learned-patterns.md` の候補として記録してよい

- **`NEEDS_CONTEXT`**: 実装には必要な情報が subagent に渡されていなかった
  - → 不足コンテキスト（design.md の該当行、既存 API の shape、プロジェクト規約等）を具体的に示して再 dispatch する
  - 同じモデルで再 dispatch してよい（モデル能力の問題ではなく入力の問題なので）

- **`BLOCKED`**: subagent が task を完了できない
  - → blocker を分類して対応を分ける:
    1. **コンテキスト不足が原因** → 追加情報を渡して **同じモデル** で再 dispatch
    2. **推論力が不足** → **1 段上の worker** で再 dispatch（`gdd-implementation-worker` → `-heavy` → `gdd-remediation-worker`。`Gate Rounds` ≥ 2 の間は remediation worker より下げない。remediation worker でも不足なら 3・4 に進む）
    3. **task が大きすぎる** → `gdd-task-breakdown` の granularity に従い task を分割してから再 dispatch
    4. **plan 自体が誤っている** → `references/rollback-patterns.md` の該当パターンで planning 差し戻し（`design_detail_only` / `human_recheck_required` / `planning_rework_required`）

**Never**: `BLOCKED` を無視して同じモデル・同じ入力で retry しない。subagent が stuck と言った時点で何かを変える必要がある。同じ条件で再試行すると context 汚染とコスト浪費だけが残る。

**Why**: subagent の報告を structured に扱うことで、controller が「とりあえず retry」に逃げずに根本原因（コンテキスト・推論力・task 粒度・plan）を見分けて処置できる。superpowers v5.0.7 の `subagent-driven-development` で実証されたパターン。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける

## Rationalization Check（この skill 固有）

実装中に scope を広げたくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。全体向けは `references/common-guardrails.md` § 合理化防止テーブル。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「ついでに周辺もリファクタしたい」 | scope 拡張は reviewer で High として差し戻す。refactor は `gdd-refactor-planning` で別タスク化 | [Scope Creep Justification] 「一回のコンテキストで複数」が効率的に見えるが、fix の効果分離ができなくなり review 負荷も増す |
| 「RED 無しで実装を先行」 | RED が無い実装は `gdd-test-driven-development` に戻される。build 開始前に RED を確認 | [Bias for Action] 動くコードを早く見たい欲求が、検証順序を後回しにする |
| 「subagent なしで inline 実装が早い」 | subagent は context 隔離のためにある。inline 実装は親 context を消費し後の phase が詰まる | [Planning Fallacy] 短期的には inline が速く見えるが、context 消費で後段の phase が詰まる total cost を見落とす |
| 「cosmetic な medium も一緒に直す」 | High と ops-blocking medium を先に対応。cosmetic は追加 PR で分離するほうが review 負荷が軽い | [Scope Creep Justification] ついで修正は review 負荷を倍にし、PR 単位の判断を曖昧にする |
| 「既存コードの書き方に合わせる必要はない」 | プロジェクトの既存規約 / `learned-patterns.md` / 既存コードの確認が Step 1a。合わせないと reviewer 差し戻しが増える | [Curse of Knowledge] 自分の書き方が「普通」と思い込み、project 規約の確認を省く |
| 「仕様と少し違うけど動くから adr.md 更新は後で」 | 後でやらずに forget される。Step 11 は必須 gate。completion-check / pr-review の AC Drift Check で結局止められ、手戻りが大きくなる | [Premature Closure] 早く done にしたい欲求が、後続 gate での再検出コストを過小評価する |
| 「AC の境界値を 1 個変えただけだから human check 不要」 | AC の境界値変更は AC 本文の意味変更。`human_recheck_required` に昇格する。方向性承認の前提が変わる可能性があるため自走しない | [Locus of Control Drift] AC 意味変更は人間責任。「些細」と自己判断すると承認前提が崩れる |
| 「Implementer Self-Correct Pass は REFACTOR と重複する」 | REFACTOR は命名・DRY・分割を対象にする。Self-Correct Pass は grep によるハードコード検出・artifact 名前照合・learned-patterns の known pitfalls 確認を対象にする。扱う観点が異なる | [Premature Closure] 2 つを「同じ」と片付けることで早く完了を主張したい欲求 |
| 「簡素化パスは REFACTOR または Self-Correct Pass と重複する」 | 簡素化パス（`gdd-code-simplifier`）は重複・過剰ネスト・過剰抽象の自動整理を担う。REFACTOR の手動観点リストを agent が機械的に網羅する役割で、Self-Correct Pass のハードコード検出・命名照合・known pitfalls とは観点が違う。3 つを残し役割を分担する | [Premature Closure] 3 工程を「同じ」と片付けることで早く完了を主張したい欲求 |
| 「impl-gate でどうせ検出されるから Self-Correct Pass は省略していい」 | impl-gate に持ち込むほど往復が増える。Self-Correct Pass の 3 類型（ハードコード値・命名不整合・known pitfalls）は機械的検出可能で、implementer 側で潰すべき責務 | [Authority Substitution] reviewer の判断に丸投げしたい欲求が、責務分界を崩す。`references/skill-responsibility-matrix.md` § Pair 3 を参照 |
| 「tasklist は task-breakdown で作ったから正しいはず」 | task-breakdown 後にユーザーが設計変更を入れると、AC カバレッジが乖離したまま実装が進む。Step 1a の Freshness Check をスキップする理由にならない | [Context Compaction Overconfidence] 過去の artifact を「正本」と信じ込み、ディスクから re-read しない |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、planning 差し戻し route、scope の勝手な拡大、.steering artifact の正本性）。subagent 完了報告の独立検証ルールは `references/verification-before-completion.md` § Subagent 報告の独立検証。以下はこの skill 固有のルール。

- active worktree を一意に解決できない状態で build を継続しない
- build フェーズから `Next Action=gdd-task-breakdown` を直接使わない
- 変更は小さくまとめ、review しやすい差分を優先する
- `High` と `ops-blocking medium` を cosmetic な medium や scope 拡張より優先する
- レビュー指摘対応時は、scope を増やさず最小のリファクタ修正に限定する
- **subagent の完了報告だけで Current Task を Completed Tasks に移さない**。`git diff` / `git log` / test 再実行で独立に検証してから `gdd-implementation-gating` に handoff する（詳細: `references/verification-before-completion.md`）
- **仕様変更を silent に実装しない**。`design.md` / AC / 承認済み代替案と異なる判断をした場合は Step 11 の Spec Change Detection に従って `adr.md` / `requirements.md` / `design.md` を同じ diff 内で更新する。AC の根本追加 / 削除 / 意味変更は `human_recheck_required` に昇格する。反映忘れは `gdd-implementation-gating` の checklist、`gdd-completion-check` の AC Drift Check、`gdd-pr-review` の Spec Drift Check の 3 層で検出されるが、手戻りが大きくなるため実装時点で記録する
- **REFACTOR 後、impl-gate に進む前に Implementer Self-Correct Pass（Step 14b）を省略しない**。ハードコード値・命名不整合・learned-patterns の known pitfalls は機械的検出可能なため、impl-gate が検出するより実装フェーズで自己修正する方が往復コストが小さい。新規 check を追加するときは Step 14b の判断軸（4 条件）と `references/skill-responsibility-matrix.md` § Pair 3 に従って Self-Correct Pass / impl-gate のどちらに置くかを決める
- **Tasklist Freshness Check（Step 1a）を省略しない**。task-breakdown 後に設計変更が入った場合、AC カバレッジ不一致として検出できる。スキップして実装を始めると completion-check での AC drift が確実に膨らむ
- **並列 subagent は tasklist.md を直接編集しない**。Attempts 記録・task status 更新は controller が集約する。lost update を防ぐ構造的制約
