---
name: gdd-implementation-gating
description: "Use for the formal GDD implementation gate after implementation and before completion-check."
version: 0.2.0
---

# Implementation Gating

## When to use this skill (vs `gdd-pr-review`)

実装直後の formal gate 専用。**PR 作成直前の review には使わない**（その場合は `gdd-pr-review`）。Claude Code の main セッションで、この gate を回すためにこの手順を読んでいるとき（Skill ツール・slash コマンド・Read のどれで開いても）は、ここで実行しない。`references/subagent-dispatch.md` § Implementation-Gating Template を Read・置換して `gate-driven-development:gdd-formal-gate-runner` に dispatch する（`gdd-formal-gate-runner` の中で読んでいるなら、このまま続ける。Codex・Cursor には、この段落は当てはまらない）。
- どの runtime でも、gate を実行した側（gate runner。inline 実行なら main。main が gate runner を時間上限・エラーで止めて出口を決めたときも main。worker 経由なら結果を統合する main で、worker 自身は書かない）は、Round の判定を決めた後に `worklog.md` へ `gate結果:` 行を 1 行足す（正本: `references/subagent-dispatch.md` § Subagent Return Output Contract）。

| 状況 | 使う |
|---|---|
| 実装が完了し、reviewer 起動 → 合否判定したい | この skill |
| `Next Action=gdd-implementation-gating` の auto-route | この skill |
| 「実装レビューして」（実装直後の文脈） | この skill |
| 「PR レビューして」「マージ前に確認して」「差分チェックして」 | `gdd-pr-review` |
| 「コードレビューして」（曖昧） | tasklist の `Next Action` を見る。impl-gating になっていれば本 skill、それ以外で PR 作成直前なら `gdd-pr-review` |

判断に迷う場合は `references/skill-responsibility-matrix.md` § Pair 1 を参照。

`gdd-implementation-reviewer` を常時起動し、`gdd-security-reviewer` は applicability で選んで実装を gate する。Terraform ファイルが変更対象に含まれる場合は `gdd-implementation-reviewer` が追加の terraform checklist を走査する。状態遷移の概要は `references/state-machine-overview.md`、詳細な遷移表は `references/state-machine.md` を参照。

## Phase Gate Pre-check（必須）

`references/phase-gate-prechecks.md` § Template A（3-Gate Approval Required）を実行する。Task Size 別の必須フィールド検査と戻り先 phase 提示は同 reference を正本とする。

**この skill 固有の追加 check**:

- `tasklist.md` の `Implementation Reviewer Selection` セクションが存在し、**少なくとも `gdd-implementation-reviewer` が `selected` または `in_review`** であること
- 欠落の場合は **fail-closed で停止**:
  - `Implementation Reviewer Selection` セクション自体が存在しない → `gdd-task-breakdown` で初期枠が未作成。task-breakdown からやり直す
  - `gdd-implementation-reviewer` が記録されていない → 必須 reviewer の欠落。Step 3 の reviewer selection を先に実行する

## Review Set

- always:
  - `gdd-implementation-reviewer`
- conditional:
  - `gdd-security-reviewer`（適用条件は Step 3 と `references/reviewer-selection.md` § Gate Rules の `gdd-implementation-gating`。どちらかに当たれば selected）
- conditional checklist（独立 reviewer ではなく implementation-reviewer の追加走査）:
  - terraform checklist（`.tf` / `.tfvars` / `.tf.json` の変更が current task にある場合）
- selection rule の正本:
  - `references/reviewer-selection.md`

## Two-Stage Review Order

superpowers `subagent-driven-development` の二段階レビューを GDD formal gate に吸収する。review は常に **Spec Compliance Review -> Code Quality Review** の順で実施する。

- **Stage A: Spec Compliance Review**: `requirements.md` / `design.md` / `tasklist.md` / `Approved Direction` に対して、実装差分が scope 内であるか、AC と承認済み方針からズレていないかを確認する。実装差分が新設要素（関数・state field・trigger・閾値・マーカー）を導入している場合は、書く側・読む側・入口からの到達経路が実コードに揃っているかを配線として確認する（`gdd-planning-reviewer` の配線表整合チェックと同じ観点）。design.md が無い（Express）場合は Stage A でこの確認を行う。新設要素ごとに、実際の入口から効果が出るところまでを通すテストが1本以上あるかを確認し、無ければ `implementation_fix_only` として差し戻す。
- **Stage B: Code Quality Review**: Stage A が pass した場合だけ、保守性、dead code、命名、境界処理、security / IaC checklist、project pattern との整合を確認する。
- Stage A が fail した場合、Stage B は `not_run` と記録する。**code quality review before spec compliance** を行わない。
- Stage A failure は `implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required` の route 判定に直結させる。品質改善で仕様ズレを覆い隠さない。

**Why:** 仕様ズレと品質指摘を同じ review に混ぜると、HITL では「何が承認済み方針から外れたのか」と「コードをどう綺麗にするか」が混線する。先に spec compliance を閉じ、通った差分だけ code quality に進めることで、GDD の gate 判断と人間向け説明を安定させる。

### Stage A Failure Route Hint

最終 routing は `gdd-systematic-debugging` の Routing Decision Tree が正本。ただし Stage A failure を出すときは、以下の hint を finding に添えて `gdd-systematic-debugging` へ渡す。route 境界を reviewer の裁量にしない。

| route hint | 使う条件 | 典型例 |
|---|---|---|
| `implementation_fix_only` | AC / Approved Direction / design は有効なまま、実装差分が承認済み仕様を満たしていない | required Browser deny が未実装、許可済み API の引数取り違え、承認済み guardrail の適用漏れ |
| `design_detail_only` | AC は変えないが、設計詳細・テスト設計・実装手順の更新が必要 | 採用ライブラリ API が想定と違う、既存 hook 境界に合わせて設計詳細を修正する必要がある |
| `human_recheck_required` | AC / Approved Direction / scope / security policy の解釈や公開範囲を人間が決め直す必要がある | sensitive data の許可範囲変更、production inline Judge 採用、承認済みスコープ外の判断 |
| `planning_rework_required` | 要件の前提や実現可能性が崩れ、requirements から組み直す必要がある | 外部依存が使えない、前提 platform が未対応、要求自体がテスト可能な AC に落ちない |

`implementation_fix_only` と `design_detail_only` で迷う場合は、「承認済み design を編集せず実装だけで閉じられるか」を境界にする。Yes なら `implementation_fix_only`、No なら `design_detail_only` を hint にする。

### Task Size による review mode 分岐

- **quick（inline checklist only。`quick (standard)` に加え、Express 昇格後の `quick (express → standard)` もこのモードを使う。`references/task-sizing.md` § パスごとの違い の `gdd-implementation-gating` 行と、`references/phase-progression.md` § Express → standard 昇格 の「昇格後は通常の quick (standard) フローに従う」に合わせる）**:
  - `gdd-implementation-reviewer` の inline checklist（`references/inline-review-checklists.md`）だけで gate を通す
  - security reviewer は起動しない（`references/reviewer-selection.md` 非 waivable 条項該当時を除く）、terraform 追加チェックも走査しない
  - subagent への escalation は行わない（checklist で High 相当の疑いがある場合のみ standard に昇格して再 gate）
  - **Why**: superpowers v5.0.7 で実証された知見。inline checklist への切り替えで review 時間 25 分 → 30 秒。quick タスクは scope が狭く specialist が waived ばかりになるため、agent 起動の overhead を削減する

- **quick (express)**:
  - Task Size = quick (express) の場合: impl-gate は `gdd-implementation-reviewer` の inline checklist を 1 回のみ実行する（express は元来 inline-checklist-only。security-reviewer subagent は起動しない・subagent escalation もしない = 従来どおり。standard 相当の security-reviewer dispatch を express に新設しない）。
    fail-closed 集合の disposition は新設せず既存の express remediation 経路を用いる（`changes_requested` = 自律 remediation ループの開始点は本 SKILL「## Goal」節を参照 / High（確定・疑い相当のいずれも含む。直前の `quick（inline checklist only）` バレットの「High 相当の疑いがある場合」と同一条件）は standard へ昇格し再 gate する / 共通 Reviewer Loop Escape Hatch（累積 5 回で human_recheck に昇格）は express にも同一条件で適用する。適用条件は本 SKILL「## Guardrails」節を参照）。
    findings の裁きは全 Task Size 共通で、Steps 9・13 に従う（High と実害クラスは差し戻し、それ以外の medium / low は `## Advisory Findings (Impl-Gate)` に記録して `approved`）。
    express 昇格条件（`references/task-sizing.md` § Express 昇格条件）に該当する finding が出た場合は既存の `express_promotion_required` route を優先する。

- **standard（従来動作）**:
  - inline review (default):
    - `references/inline-review-checklists.md` のチェックリストを gate skill 自身が走査する
    - チェックリストで判断がつかない場合だけ `agents/*.md` の subagent に escalation する
  - deep review (opt-in):
    - user が明示的に deep review を要求した場合、または escalation 条件に該当した場合だけ `agents/*.md` を読んで subagent を起動する

## Goal

- 実装差分を設計準拠、通常品質、非機能、実現可能性、セキュリティの各面から確認する
- 実装後レビューの必須 gate として、`gdd-subagent-driven-implementation` の mandatory refactor checkpoint 済みを前提にし、差し戻し時は原則リファクタループへ戻す
- `changes_requested` を報告だけで終わらせず、自律 remediation ループの開始点として扱う
- reviewer ごとの結果を別々に保持する
- `Review Status` と `Next Action` を更新する
- generic な review 依頼の正式レーンを維持する

## Fixed Model

`references/fixed-models.md` を参照（Claude Code: `opus` + `effort=high` / Cursor: `Grok 4.6` + `medium` / Codex: `gpt-5.6-sol` + `medium` 固定。理由: autonomous continuation を止める formal gate）。

## Status Update Format

Schema の正本は `references/gate-status-schema.md`（reviewer-level status / Reviewer Selection の仕様含む）。この skill 固有の補足:

- 対象 reviewer: `gdd-implementation-reviewer`, `gdd-security-reviewer`
- `evidence` には `Current Task` を識別できる情報を含める

## Remediation Priority

- `High`:
  - 常に最優先で自律 remediation する
  - 未着手のままユーザー確認待ちにしない
- `ops-blocking medium`:
  - `Medium` のうち、本番挙動、セキュリティ境界、データ整合性、resume / gate correctness（範囲は `references/reviewer-common.md` § 常時 High の適用範囲に従う）、rollout / rollback / recovery、観測性、required verification evidence に影響するもの
  - Step 9 に当たるときだけ、`High` の次に優先して自律 remediation する。当たらないものは Step 13 のとおり記録し、この loop では直さない
- その他 `Medium`:
  - 実害クラス（`references/reviewer-common.md` § finding category）なら blocking issue。実害クラスでなければ advisory として記録し（Step 13）、この loop では直さない
  - `design_detail_only` / `human_recheck_required` / `planning_rework_required`、または non-local な意思決定が本当に必要な場合だけユーザーへ戻す
- 上の並びは remediation の順番である。差し戻すかどうかは Step 9 の述語で決め、Task Size（express を含む）によらない

## Steps

Step 1 の前に `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/impl-gate-context.py --steering-dir <Steering Dir>` を 1 回回す。下の Steps が読む steering の節（tasklist.md の全節の索引・冒頭の Agentic Worker Header・Current Task・Pending Tasks・Implementation Reviewer Selection・Review Status・Execution Plan・Refactor Gate Status・Completed Tasks の task 行と `was_valid: false` の `[Review Calibration]`、state.md の Task Size・Route In Progress・Active Worktree Path、Step 5 の置き場の learned-patterns.md の Rejected Alternatives、worklog.md の末尾、handoff の State Machine Impact と前回の gate の出力の見出しと判定の行）は、その出力を使い、tasklist.md を通読しない。tasklist.md の、出力に無い節が要るとき・Edit の前は、索引と出力の行番号の範囲だけを Read する（state.md・worklog.md の Edit の前の Read は、この範囲の規定の外）。exit 1 のときは、出力を使わず従来どおり自分で読む。

1. **差分 scope guard**: reviewer に入る前に `git diff <default-branch>...HEAD --stat`（default branch は `gdd-using-git-worktrees` で判定済み）で変更ファイル一覧を取得し、`requirements.md` のスコープと照合する。
   1a. **E2E 一貫性検証（Output Consistency Check）**: `references/e2e-verification-catalog.md` § Pattern 1 を適用する。構造化データ出力 + AC に決定性・網羅性が含まれる場合、2 回以上の E2E 実行と件数・分割・通し番号の一致を確認する。未実施は Medium finding（category は `test-power`）。
   - scope 外のファイル変更が含まれている場合は Medium finding（category は `product`）として報告する。明らかに無関係な変更（別タスクのファイル、ローカル状態ファイル等）は High finding とし、remediation 対象にする
   - `.claude/*.local.md` 等の worktree ローカルファイルが変更に含まれていないか確認する
   - scope guard は reviewer selection の前に実行する。scope 外変更が High の場合は reviewer を起動せず `changes_requested` で `gdd-systematic-debugging` に戻す（Gate Batch では Step 9 の Gate Batch の扱いも適用する。`Gate Rounds` の加算も Step 9 のとおりにする）
   1b. **関数コンテキストスキャン（function-level context scan）**: `git diff` の変更行だけでなく、**本タスクで修正した関数の全体**を読む。scope 内変更であっても、その関数内に本タスクと無関係な dead code / dead return / 未処理 TODO / 到達不能分岐 が並存している場合は Medium finding（category は `product`）として列挙する。
   1c. **Reviewer File Scope Constraint（レビュアー指摘のファイルスコープ検証）**: `git diff <default-branch>...HEAD --name-only` で変更ファイルリストを確定する。reviewer の指摘を処理する際に、各 finding が **このリスト内のファイル** を根拠にしているかを確認する。
   - diff リスト内のファイルを参照している → 有効な指摘として処理する
   - diff リスト外のファイル（worktree 外の絶対パスを含む）を参照している → **実在確認必須**。diff に含まれないファイルへの finding は `unverified` とフラグし、そのファイルが実際に変更されていることを確認してから対応する。確認できない場合は finding を `advisory:unverified_file` に降格する（high・実害クラスは、根拠の path が `references/finding-dispositions.md` の `absent@` の条件〔履歴・未 commit の file にも、同じ basename の file にも無い〕に当たれば根拠に `absent@<HEAD の sha>` と書いて下げ、Step 8 の検査がその path を git で確かめる。それ以外は検証役 `gdd-finding-verifier` が `refuted` と判定したときだけ。判定できなければ通常の行き先。正本 `references/finding-dispositions.md`）
   - **Why:** impl-gating の reviewer が worktree 外のファイルを参照して無効な指摘を生成するケースが観測された。指摘対応の前にファイル存在確認を挟むことで、無効指摘への対応コストを削減する
     - 例: 本タスクで修正した関数の末尾に以前から残る `return null` の dead return がある、関数先頭に使用されない TODO コメントがある、条件分岐の片側が恒真/恒偽で実質死んでいる
     - remediation 方針は finding に併記する: (a) 本 PR で一緒に修正する（低リスク・1〜数行） (b) separate PR / separate steering に切る（スコープ拡大になる規模）
     - **Why**: 変更行だけを見ると「scope 内」で通過するが、PR reviewer は関数全体を読むため既存 dead code を指摘してくる。事前に拾うことで PR 後の review gap を減らす
   1d. **RED Evidence Worktree Provenance Check**: Current Task の（Gate Batch では各 task の）`#### RED Evidence` から `Worktree:` 行を取得し、`## Worktree`（本 gate に渡された worktree 絶対パス。dispatch template を経由しない inline 実行等で未提供の場合は `state.md` の `Active Worktree Path` を代わりに用いる。どちらも解決できない場合は本 check 自体を High finding とし fail-closed で `changes_requested` にする）と、バッククォート等の装飾を除き realpath 相当で正規化した上で一致するかを確認する（`Worktree:` は TDD subagent の宣言ではなく観測値である前提だが、この一致確認自体は自己申告への依存を消せない。実質の独立検出は次の diff 突合）。`test:` にファイルパスを含む形式（形式1/3）は、そのパスが `git diff <default-branch>...HEAD --name-only`（1c で確定）または `git -C "<上記で解決した worktree 絶対パス>" status --porcelain` の未 commit 分に含まれるかを確認する。`verification:` のみでファイルパスを持たない形式（形式2）は値一致チェックのみを適用し `provenance: file-path-absent` として記録する。`Worktree:` 未記載・値不一致・（ファイルパスを持つ形式で）diff/未 commit いずれにも未掲載・`git diff`/`git status` 自体の実行失敗のいずれかなら High finding（category は `product`。`changes_requested` なので `Gate Rounds` が増え、`gdd-test-driven-development` の Post-Compaction Resume Check が差し戻された task と判定できる）とし、reviewer を起動せず `changes_requested` で `gdd-systematic-debugging` に戻す（Gate Batch では Step 9 の Gate Batch の扱いも適用する。`Gate Rounds` の加算も Step 9 のとおりにする）（コマンド失敗を「未掲載」と区別せず fail-closed にする。RED が呼び出し元 worktree に書かれた場合、本 worktree の diff / working tree には現れないため。2026-09-08 の実害再発防止）。
   1e. **review を外すか（判定の線）**: Step 1 の scope guard と 1d の後、1a・1b より先に、`impl-gate-context.py` の `impl-gate-review:` 行を読む（正本: `references/task-breakdown-steps.md` § Judgment Change）。`skip <task 名>` のときだけ、その task 名が Current Task に見える task と一致すること、行が示す差分の起点からの差分（`git diff <起点>` と untracked）が線に触れないこと、Step 2 の State Machine Impact block に `ADR 起票: 要`・`Reviewer Lineage 追加提案`（`なし` 以外）・`Routing 提案: human-check-waiting` が無いことを確かめる。満たせば 1a・1b と Step 2〜10 を行わず（reviewer を起動しない）Step 11 へ進み、`Reviewed by: none (Judgment Change: no)` を付けて `approved` とする。満たさない・判定できないときは、線に触れた変更を入れた task（決められなければ gate 単位の全 task）の欄を `- Judgment Change: yes` に書き換えて（`no` には下げない）通常どおり進む。行が無い・`run`・script が exit 1 のときも通常どおり（差し戻し後の再 gate は `Gate Rounds` で `run` になり、8a を含む Step 2〜10 を飛ばさない）。
2. `requirements.md`, `design.md`, `tasklist.md`（上の script の出力）, 実装差分を読む。active worktree 側 `.steering/.../adr.md` があれば、既に確定した重要判断や却下済み代替案も補助コンテキストとして確認する。

   **State Machine Impact Block の確認**: `gdd-subagent-driven-implementation` からの handoff 出力に `### State Machine Impact` block が含まれているか確認する。あれば以下を抽出して reviewer 選定 / routing 判断の入力にする:
   - `ADR 起票`: `要` の場合、`.steering/.../adr.md` が実際に追記されているか確認（未追記なら remediation 対象）
   - `Reviewer Lineage 追加提案`: `なし` 以外なら Step 3 の reviewer selection で必ず該当 reviewer を `selected` に昇格させる（既に `selected` なら no-op）
   - `Routing 提案`: `human-check-waiting` が来ていれば formal gate を通さず human check に escalate（AC 根本変更 or Approved Direction 変更時）
   - block が無い → 純粋実装として通常 review に進む
3. `references/reviewer-selection.md` に従って applicable reviewer を選び、`Implementation Reviewer Selection` を `tasklist.md` に記録する。
   - `gdd-implementation-reviewer` は必ず `selected`
   - `gdd-security-reviewer` は auth・secrets・untrusted input・shell/filesystem・permissions・LLM呼び出し・エージェント実装 が current task（Gate Batch では batch のどれかの task）にある場合に `selected`
   - 同じ `Current Task` の再レビューで scope が変わらないなら前回 selection を再利用する
   - **再利用条件（すべて満たす場合のみ）**:
     - `Implementation Reviewer Selection` の `updated_at` が**現在の** `Current Task` の実装開始以降である（前タスクの selection が残っていないか確認）
     - `Implementation Reviewer Selection` の Task ID が現在の `Current Task` の Task ID と一致する（Gate Batch では `Gate Batch <N>` を Task ID として書き、比べる）
     - scope 変更の判定（下記）に該当しない
   - **前タスクの selection が残っている場合**: `updated_at` が古い、または Task ID が異なる場合は selection を stale とみなし、必ず再評価する。特に `gdd-security-reviewer` が前タスクで `waived` だった場合、現タスクで security-sensitive な変更が含まれていれば `selected` に変更する
   - **scope 変更の判定**: 前回 review 時の diff ファイル一覧と今回を比較し、以下のいずれかに該当すれば scope 変更とみなす:
     - 前回に無かった新規ファイルが diff に含まれている
     - security-sensitive なファイル（auth / secrets / permissions / middleware / IAM）が新たに追加された
     - 変更ファイル数が前回から 2 倍以上に増えた
   - scope 変更で selection を変える場合は `selection_change_reason` を残す

4. reviewer 起動前に、selected reviewer status だけを `in_review`、`evidence=review-start:<current-task-id>`、`updated_by=gdd-implementation-gating`、`updated_at=<timestamp>` に更新し、non-selected reviewer は `waived` + `waiver_reason=<reviewer-selection-reason>` に更新し、`Next Action=gdd-implementation-gating` を記録する。
5. **Reviewer Calibration 参照**: review 開始前に以下の 2 ソースから false positive 記録を収集する。
   - **Cross-task（前タスク群の蓄積）**: worktree 直下の `docs/learned-patterns.md`（置き場の正本は `references/cross-task-learning.md`）の `Rejected Alternatives` セクション
   - **Intra-steering（同一タスク群内）**: `tasklist.md` の `Completed Tasks` 内の各タスクの `#### Attempts` セクション **および 現在の `Current Task` 自身の `Attempts`（同一タスクで複数回 `changes_requested` が続いた履歴）** から `[Review Calibration] was_valid=false` が 2 回以上記録されている checklist 項目。Current Task 自身の Attempts を含めるのは、長い remediation ループ中に false positive と判明した指摘が再提出されるのを防ぐため
   
   いずれかの false positive が記録されている checklist 項目は、同じパターンに該当する finding の severity を 1 段階下げる（High → Medium、Medium → advisory）。**ただし**: security-reviewer の項目は severity 調整しない（安全側に倒す）。`references/reviewer-common.md` § 常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）の適用範囲に当たる finding も、reviewer を問わず調整しない（適用範囲外の扱いは同節が正本）。調整した場合は evidence に `calibration: <ソース（learned-patterns or Attempts T-N）の該当記録>` を付記する。
   
   **Why**: `learned-patterns.md` への反映は `done` 時のため、同一 steering 内の false positive は Attempts を直接参照して埋める。
6. **Two-Stage Review（Spec Compliance Review → Code Quality Review）**: review は必ず 2 段階で行う。Superpowers の subagent-driven-development と同じく、先に「作るべきものと一致しているか」を閉じ、その後で「よく作られているか」を見る。**code quality review before spec compliance は禁止**。

   - **Stage A: Spec Compliance Review**
     - `requirements.md` の AC、`design.md`、`tasklist.md` の Current Task、Agentic Worker Header の `Approved Direction` / `Human Recheck Boundary` と diff を照合する
     - 実装が AC を満たしていない、approved scope を超えている、`Tech Stack` / `実装技術スタック` と違う技術を採用している、Human Recheck Boundary に触れている場合は Code Quality Review に進めず `changes_requested`（finding の severity・category によらない。Step 9）
     - ここでの finding は「仕様不一致」として扱い、単なるリファクタ指摘と混ぜない
   - **Stage B: Code Quality Review**
     - Stage A が pass した場合だけ、`references/inline-review-checklists.md` の `implementation-reviewer checklist` と selected reviewer checklist を走査する
     - 命名、責務分割、dead code、security-sensitive 実装、Terraform 追加チェック、maintainability などはこの段階で扱う
   - 出力には `Spec Compliance Review: pass|changes_requested` と `Code Quality Review: pass|changes_requested|not_run` を分けて記録する。Stage A が fail した場合、Stage B は `not_run` とし、仕様修正後に再実行する。**各 finding には `category` を 1 つ付ける（値域と導出述語の正本: `references/reviewer-common.md` § finding category）。未付与の finding の扱いは同節の既定に従う。差し戻すかは Step 9 の述語で決める**
   - **再入時の差分スコープ**: 同じ `Current Task` の再レビューでは、前回 `changes_requested` 以降の差分と影響範囲だけをレビューする。通過済み箇所への新規指摘は advisory（新情報の根拠がある場合のみ blocking へ昇格）
   - **Honest Limitations 既載の例外**: `requirements.md` § Honest Limitations（**`Human Check Status=approved` 時点の内容に限る**。build 中の追記と design.md 側は対象外）に「防げない」と明示された限界に該当する finding は blocking にしない（advisory として記録）。新たな攻撃面の発見は security-reviewer の安全側倒しどおり blocking のまま。reviewer 指示に承認時点の Honest Limitations を渡す（渡さないと、requirements が諦めた偽装耐性を reviewer が繰り返し求め、修正が発散する）。**実害クラス category（正本: `references/reviewer-common.md` § finding category）に該当する finding はこの例外の対象外とし、Honest Limitations 既載でも blocking のまま残す。`severity: High` の finding も category によらず blocking のまま残す** 既載例外を適用するときは、その限界が別の AC を破らないことを確認し、破る場合は適用しない（blocking のまま）。

7. `references/inline-review-checklists.md` の `implementation-reviewer checklist` と（selected の場合）`security-reviewer checklist` を走査してインラインレビューを実施する。current task に `.tf` / `.tfvars` / `.tf.json` の変更が含まれる場合は `terraform 追加チェック` も走査する。以下の escalation 条件に該当する場合だけ、該当 reviewer の `agents/*.md` を読んで subagent に escalation する（起動は `references/subagent-dispatch.md` § Reviewer Input and Time Budget に従う）。`remediation_loop` 中は escalation 先 reviewer も `Agent(model="opus")` で起動する（Claude Code の場合。Cursor / Codex の host 別モデルは `references/fixed-models.md` の tier 表を正本とする。effort の扱いも同所）。
   - **escalation 条件**（いずれか 1 つでも該当すれば escalation）:
     - checklist 項目で、影響範囲を自信を持って判定できない（例: 「このコードのセキュリティ影響を評価できない」）
     - 変更が 3 ファイル以上に跨り、ファイル間の相互作用を checklist だけで追えない
     - 外部依存（DB schema、API 契約、インフラ構成、認証フロー）に影響する変更がある
     - 前回の inline review で見逃した issue が `changes_requested` で戻ってきた
     - 実起動できない場合（副作用境界の除外に該当しないのに fixture 実行環境が無い等）。quick / quick (express) では subagent へ直接 escalation せず、既存の「High 疑いは standard へ昇格して再 gate」と同じ経路で Task Size を standard に上げてから本条件を再評価する（quick/express の「subagent escalation は行わない」規約と衝突させない）

   **終端規則**: subagent でも実起動できない場合は `実起動: unavailable (<理由>)` を finding の evidence に必ず残し、当該 entry point を未検証の残リスクとして impl-gate 出力に advisory で明示する。無言スキップにしない。
8. reviewer ごとに次を判断する。判定を決める前（8a 以降の出口の前）に、この Round の全 finding の行き先を `review-findings.md` の `IG<k>` 節（k は IG だけで数える steering 通しの連番。見出しに HEAD の sha と Current Task の Gate Rounds）に書き（`rejected:refuted` と、high・実害クラスの `advisory:calibration`・`advisory:unverified_file` は、検証役 `gdd-finding-verifier` が refuted と判定したものか、Step 1c の `absent@<sha>` の行だけ。正本は同書 § 検証役）、`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-finding-dispositions.py --steering <Steering Dir> --task <Current Task> --base <default-branch>` が ok になるまで直す（書式・値域・行き先の規則の正本: `references/finding-dispositions.md`）。
   - `approved`
   - `changes_requested`
   - `waived`（`waiver_reason` 必須。reviewer 観点が current task に本当に非該当な場合だけ使う。real issue の受容には使わない）
   8a. **ADR ≥2 独立トリガー（reviewer 判定結果に関わらず無条件で評価。全員 approved でも Step 11 の完了処理へ進めない）**: 同一 `Current Task` の remediation 由来 ADR entry（`- **Origin**: remediation / <Current Task>` 行を持つ entry）が 2 件以上なら（Gate Batch では Step 9 の Gate Batch の扱いも適用し、件数は task ごとに数える。対象の task の決め方は `references/state-machine.md` § Remediation Loop Safety の Gate Batch の項）、reviewer status は Step 8 の判定どおり schema 付きで記録し、その判定が `changes_requested` なら `Gate Rounds` を +1 して root cause カテゴリを Error Log に記録したうえで、`Next Action=gdd-systematic-debugging` として route 確定を委譲する（`Route In Progress` はここでは書かない。route 強制は `gdd-systematic-debugging` の Routing Decision Tree 側の責務。正本: `references/state-machine.md` § Remediation Loop Safety）。Step 9〜11 の残りは評価せず、本 skill の処理をここで終えて handoff する。
9. High の finding か実害クラス（`references/reviewer-common.md` § finding category の `is_blocking`）の finding が reviewer ごとに 1 件でも残る場合（Task Size によらない。Honest Limitations 既載の例外は §Steps 6 を参照）。Stage A の fail と Spec Drift（`references/inline-review-checklists.md` の実装 → artifact の逆方向整合）は、severity・category によらずこの場合に入る:
   - reviewer status を schema 付きで `changes_requested` にする。`tasklist.md` の `Current Task` セクションの `Gate Rounds` を +1 する（無ければ `Gate Rounds: 1` を追加）。**Gate Batch の扱い**: どの出口（Step 1・1d・8a・本 Step）から `changes_requested` を返すときも、batch の全 task を `changes_requested` とし、`Gate Rounds` を足すときは全 task に同じだけ足す。finding には対象の task id を付け、対象の task を `Execution Status: in_progress` に戻して `Current Task` の先頭に移す（対象の task を決められない finding は batch の全 task を対象にする。対象が複数なら severity の高い順、同じ severity なら `Gate Batch <N>` に書いた順に並べる。remediation は対象の task だけを直し、再 gate は前回 `changes_requested` 以降の差分を見る）
   - `Next Action=gdd-systematic-debugging`
   - `changes_requested` はユーザー確認待ちの停止点ではなく、自律 remediation ループの開始点として扱う
   - remediation 優先順位は `High` -> `ops-blocking medium` -> その他 `Medium` にする（`gdd-systematic-debugging` が `implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required` を見分けて戻り先を決める）
   - **Loop Safety の閾値**（impl-gating からは `gdd-systematic-debugging` への signal として伝達するだけで、route 強制は systematic-debugging 側。正本: `references/state-machine.md` § Remediation Loop Safety。`remediation_loop` 中は本 skill の gate subagent 自体を `Agent(model="opus")` で、remediation worker を `gdd-remediation-worker`（`## Worktree` と `## Plugin Root` を渡す）で起動する（Claude Code の場合。Cursor / Codex は host 別モデルを使う）。開始条件・正本: `references/fixed-models.md`）:

     | 到達条件 | ルール |
     |---|---|
     | **`Gate Rounds` ≥ 2** | `remediation_loop` tier（`references/fixed-models.md`）。本 skill の gate subagent・escalation 先 reviewer を `model="opus"`、remediation worker を `gdd-remediation-worker`（`## Worktree` と `## Plugin Root` を渡す）で起動（Claude Code の場合。Cursor / Codex は host 別モデル、正本 `references/fixed-models.md`） |
     | **3/3 到達** | blind `implementation_fix_only` 禁止。同種 root cause の再発を疑い、`design_detail_only` 等を検討させる（soft）。`Gate Rounds` が 3 以上になった task では、`gdd-systematic-debugging` が方針を考え直した結果を `Approach Rethink` の行に書く（正本: `references/state-machine.md` § Remediation Loop Safety） |
     | **5/5 到達** | 強制 `human_recheck_required`（Reviewer Loop Escape Hatch。hard cap）。承認後は reset のうえ上限 2/2 |
     | **承認後 2/2 到達 / 同一 root cause カテゴリ 3 回連続 finding / 同一 `Current Task` の remediation 由来 ADR entry が 2 件以上** | 修正を続けず**方式転換**の選択肢を人間へ一括提示（正本: § Remediation Loop Safety。impl-gating は `changes_requested` のたびに finding の root cause カテゴリを Error Log に記録する） |
10. **Reviewer Calibration 記録**: 同じタスクの再レビュー（前回 `changes_requested` → 修正 → 今回 `approved`）の場合、前回の指摘と実際の修正を照合し、`tasklist.md` の `Attempts` セクションに Calibration データを追記する（`references/inline-review-checklists.md` § Reviewer Calibration 参照）。初回レビューではスキップする。
11. selected reviewer がすべて `approved` で、non-selected reviewer がすべて理由付き `waived` の場合:

- reviewer status を schema 付きで更新する
- `state.md` の `Route In Progress` が `implementation_fix_only` の場合は `none` にクリアする（`references/rollback-patterns.md` 参照）
- `Current Task` の task を `Completed Tasks` に移す。移す際に `Reviewed by: <selected reviewer 名のカンマ区切り>`（Step 1e で review を外したときは `Reviewed by: none (Judgment Change: no)`）を task block 末尾に 1 行付記する（completion 時の監査根拠として残す）。task block の `Fix Findings:` の行は消す（並列・Gate Batch で複数の task を移すときも同じ）。移した後に `Current Task` が空なら、次の task を昇格する前に `state.md` の `Impl Gate Base:` を `git rev-parse HEAD` の値に、`Impl Gate Completed:` を `Completed Tasks` の task の数にする（次の gate 単位の起点。Step 1e。並列の batch の途中では書かない）
- **tasklist re-read（実装漏れ防止）**: task 移動後に `impl-gate-context.py` をもう 1 回回して（exit 1 なら `tasklist.md` をディスクから re-read して）、`Pending Tasks` の実際の内容を確認する。context に残っている古い情報だけで判断しない。これにより、long session でのコンテキスト劣化による残タスク見落としを防ぐ
- **逐次実行時**: `Pending Tasks` に task があればその先頭を `Current Task` に昇格し、残りを `Pending Tasks` のまま維持する
- **並列実行時**（`Execution Plan: parallel` の場合）: 同一バッチ内の他タスクがまだ `Current Task` にあれば、次タスクのレビューに進む。バッチ内の全タスクが通過したら、次バッチの全タスクを `Current Task` に昇格する
- **Gate Batch のとき**（逐次の `Execution Plan` に `Gate Batch <N>` があり、`Current Task` にその batch の task が並ぶ。条件は `references/task-breakdown-steps.md` § Gate Batch）: batch を 1 つの gate 単位として、1 回の gate で全 task をレビューする（差し戻しは Step 9）。全員 approved なら、全 task を `Completed Tasks` に移して、それぞれに `Reviewed by:` を付け、`Pending Tasks` の先頭を `Current Task` に昇格する
- 次の task に進む場合は implementation reviewer status を `pending | evidence: none | updated_by: gdd-implementation-gating | updated_at: <timestamp>` に戻し、`Implementation Reviewer Selection` も reviewer ごとに `pending | reason: none`、`selection_change_reason: none | updated_by: gdd-implementation-gating | updated_at: <timestamp>` に戻し、`Next Action=gdd-test-driven-development`。**この場合 Refactor Gate チェックはスキップする（次タスクが存在するため）。**
- 次の task に進まない場合（re-read した `Pending Tasks` が `- なし` ＝ すべての task が完了）は、**Refactor Gate** を確認する:
  - `tasklist.md` に `Refactor Gate Status` 行を探す
  - `Refactor Gate Status` が `pass-empty` または `pass-applied` の場合: `Next Action=gdd-completion-check`
  - `Refactor Gate Status` が `in-progress` の場合: リファクタタスクが完了したので `Refactor Gate Status=pass-applied` に更新し、`Next Action=gdd-completion-check`
  - `Refactor Gate Status` が absent または `pending` の場合: `Task Size` が `quick (express)` に完全一致するときは `Next Action=done`（completion-check / refactor gate ともにスキップ — `state-machine.md` §Express 遷移表を参照）、それ以外（`standard`／`quick (standard)`／`quick (express → standard)` を含む）なら `Next Action=gdd-refactor-planning`
  - **Why**: 個別タスクの REFACTOR チェックポイントは局所的な改善にとどまる。全タスク完了後に一度コードベース全体を俯瞰する機会を設けることで、タスクをまたいだ重複排除や命名統一が可能になる

12. `waived` の場合は reviewer ごとに `waiver_reason` を必ず残す。`waiver_reason` は `references/reviewer-selection.md` に沿った non-applicable 根拠だと第三者が読んで分かる粒度で書く。
13. Step 9 に当たらない medium / low は差し戻さず、この loop では直さない。`state.md` の `## Advisory Findings (Impl-Gate)` 節（`references/state-field-tiers.md` Tier 3 定義）に記録して `approved` にし、PR 本文に全件を書く（`Review Status` は `references/gate-status-schema.md` の既定許容値のまま。`approved(advisory)` という status 値は作らない）。`references/independent-review.md` の (3-f) の finding は同項の申し送りにも回し、`state.md` の `Decision Handoff` を書く。`waived` は non-applicable reviewer だけに使う。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける
- `waived` を説明するときは reviewer ごとに名前で分けて説明する。
- `Spec Compliance Review → Code Quality Review` の順序と各 stage の status を表示する。Stage A が fail した場合は Stage B を `not_run` とし、code quality review before spec compliance を行わない。
- 成功遷移を説明するときは `Current Task` / `Pending Tasks` / `Completed Tasks` の更新と `Next Action` をセットで答える。
- 証拠なしに成功表現を使わない。`approved` / `pass` / `review clean` / 「実装完了」と言う前に、読んだ diff、実行した test / lint / checklist、reviewer judgment、残 issue の有無を列挙する。
- active な `/gdd-dev` run では自律継続（`common-guardrails.md` § 自律継続）に従い、`Next Action` を説明して終えるのではなく same run 内で次 phase に進める。
- generic な「コードレビューして」「実装レビューして」だけの依頼なら、まず formal gate は `gdd-implementation-gating` だと案内し、`gdd-requesting-code-review` は明示実行があるときだけ使うと説明する。
- generic review request だけで、現在の repository 全体に対する ad-hoc review や advisory lane をその場で始めない。
- scope guard 違反で差し戻す場合は以下のテンプレートを使う:

```markdown
## スコープ外の変更が検出されました

### スコープ外ファイル

| ファイル | 変更内容   | 深刻度      | 理由               |
| -------- | ---------- | ----------- | ------------------ |
| <path>   | <変更概要> | High/Medium | <なぜスコープ外か> |

### 対応

- High（security-sensitive / 大規模変更）→ reviewer を起動せず差し戻し
- Medium（低リスクな変更）→ reviewer に進み Medium finding として報告

### 次のアクション

- → <スコープ外変更を revert するか、requirements に追加するか>
```

## Worked Example: Scope Guard 判定

**状況**: requirements.md の scope は「ページネーション API の追加」（AC-1: cursor パラメータ、AC-2: next_cursor レスポンス）。

`git diff main...HEAD --stat` の結果:

```
src/api/users.ts       | 45 +++
src/api/users.test.ts  | 30 +++
src/auth/middleware.ts  | 12 +++   ← scope 外
```

**判定**:

- `src/api/users.ts` と `src/api/users.test.ts` → scope 内（ページネーション実装）
- `src/auth/middleware.ts` → requirements.md に auth 関連の AC がない → **scope 外**
  - auth ファイルは security-sensitive → **High scope violation**
  - reviewer を起動せず `changes_requested` で `gdd-systematic-debugging` に戻す

**もし scope 外が `README.md` の typo 修正だったら**:

- → Medium scope violation（無関係だが低リスク）→ reviewer に進み、Medium finding として報告

## Rationalization Check（この skill 固有）

reviewer finding を軽視したくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。全体向けは `references/common-guardrails.md` § 合理化防止テーブル。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「High だけど実装の意図は正しい、waive で流す」 | `references/reviewer-selection.md` で `waived` は「current scope に非該当」のみ許可。real issue の受容 waive は guardrail 違反 | [Authority Substitution] reviewer の判断を「自分の意図」で上書きする。reviewer 指摘の独立性が失われる |
| 「Medium は Advisory Findings に書かずに後回し」 | Step 9 に当たらない medium も Step 13 のとおり `## Advisory Findings (Impl-Gate)` に記録し、PR 本文に全件を書く。記録しないと、直さないまま誰の目にも触れずに PR を通る | [Premature Closure] 早く approve したい欲求が、後続 phase での再検出コストを過小評価する |
| 「同じ実装で 3 回目の blind fix で通す」 | 3 回続く changes_requested は route の誤り。loop safety が強制的に `design_detail_only` に昇格させる | [Sunk Cost Fallacy] 既に 2 回 fix した投資を惜しんで撤退できない。routing 誤りを認められない |
| 「スコープ外の変更、ついでだから含めちゃう」 | scope guard が High で差し戻す。scope 外変更は新規 steering として切る | [Scope Creep Justification] 一回でまとめたい欲求が、PR 単位の判断粒度を曖昧にする |

## Bounce Log（無限ループ防止、Fix Attempts とは独立）

`references/bounce-log-schema.md` の共通仕様に従う。bounce log 名 `Implementation Gating Reviewer Bounce Log` / identifier-key `task-id + reviewer指摘カテゴリ` / 閾値 `>= 2` / escalate 先 `既存の gdd-systematic-debugging`（新規destinationは追加しない）。この bounce log は `tasklist.md` の `Fix Attempts` カウンタ（同一 route 3回失敗で Architecture Gate 発動）とは**別軸のカウンタ**であり、互いにリセット・閾値を共有しない（ADR-2参照）。「reviewer が同じ指摘を繰り返す」（レビューループ、本 bounce log の対象）と「同じ修正を試みて失敗する」（デバッグループ、`Fix Attempts` の対象）は異なる事象として扱う。

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、gate 開始前の記録ルール、planning 差し戻し route、fail-closed 応答）。`approved` 判定前の evidence 要件は `references/verification-before-completion.md` § Key Patterns / § Fresh Verification を参照。以下はこの skill 固有のルール。

- 実装差分のレビュー観点（3 レーン・10 分類）は `references/self-review-lanes.md` を正本とする。inline checklist と重複する観点の分類 ID は同 reference § inline checklist との責務境界 に従う。
- `gdd-implementation-reviewer` は常時 selected を維持する（Step 1e で review を外すときは reviewer を起動せず、selection と status は Step 11 の末尾の reset だけを行う）
- **stale な Implementation Reviewer Selection を再利用しない**。前タスクの `waived` が現タスクに引き継がれると、security-sensitive な変更が security review なしで通過する。Task ID と `updated_at` が現タスクと一致しない selection は必ず再評価する
- high / medium を `waived` で流さない・黙ってスキップしない
- 同じ `Current Task` で `changes_requested` が続く場合、blind `implementation_fix_only` を繰り返さず loop safety に従う
- `Review Status` を更新せずに gdd-completion-check へ進まない
- `gdd-completion-check` は全 task 完了時だけに進める（standard / quick-standard 系〔`quick (express → standard)` を含む。列挙外の値も standard 扱い〕のみ。`quick (express)` は completion-check をスキップし `done` に直接遷移する）
- **reviewer `approved` の evidence 要件**: 「tests pass」と主張する前に、本セッション内でテストコマンドを実行した出力を確認する（以前のセッションや agent の成功報告だけを根拠にしない）。詳細は `references/verification-before-completion.md`
- Express パスで `Next Action=done` にする場合: impl-gate 内で最低限の AC 検証 + stub detection を行ってから `done` にする。completion-check をスキップするため、この検証が最後の safety net になる:
  - **AC 検証**: `gdd-ac-verification` を呼んで該当タスクの AC 行を verify する（Verification schema / fresh evidence / speculative language 拒絶ルールは ac-verification が一元管理）
  - **stub detection**: 以下のパターンを grep で検索する（テスト・mock・fixture ファイルは除外）:
  - `return null` / `return None` / `return []` / `return {}` がメインロジックに残っていないか
  - `raise NotImplementedError` / `throw new Error("not implemented")` が未削除でないか
  - `TODO` / `FIXME` コメントが実装箇所に残っていないか
  - 空の関数本体（`pass` のみ / `{}` のみ）が意図せず残っていないか
  - **判定の境界**: `return null` 等の「空値 return」単独では stub 断定しない（正当な欠損ハンドリングの可能性）。ただし **同一行もしくは直前直後に `TODO` / `FIXME` / `not implemented` / `handle ... case` 等の未完成マーカーが併記されている場合は High stub 確定**（設計意図ではなく未完了の痕跡）。マーカー無しの空値 return は Medium finding（category は `product`）として「意図確認」を要求
- Express パスでも `gdd-systematic-debugging` の **Reviewer Loop Escape Hatch** は同じく適用される。同じ `Current Task` で累積 5 回目の `changes_requested` で強制 `human_recheck_required` に昇格する（standard と同一）
- 差分 scope guard を skip して reviewer に入らない。scope 外変更の High finding がある場合は reviewer を起動せず差し戻す
