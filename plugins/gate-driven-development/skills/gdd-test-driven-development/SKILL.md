---
name: gdd-test-driven-development
description: "Internal: auto-routed only when Next Action=gdd-test-driven-development. Runs AC-bound TDD."
version: 0.1.0
contract_terms: "RED-created; Expected RED Failure Verification"
---

# Test Driven Development Lite

task 単位で RED を明確にし、実装前のテスト準備を固定する。

## Phase Gate Pre-check（必須）

`references/phase-gate-prechecks.md` § Template A（3-Gate Approval Required）を実行する。Task Size 別の必須フィールド検査と戻り先 phase 提示は同 reference を正本とする。

## Fixed Model

- `Claude Code`: `sonnet`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light tier）
- テスト設計は承認済みの AC に基づく定型作業のため、軽いモデルで十分。cheap lane モデルでは RED Evidence の Contract Surface Coverage 取りこぼしがあったため light tier を維持する

## Goal

- 実装前に failing test または executable verification を用意する
- RED の証跡を作る（テスト実行結果の fail output を記録する）
- この phase は RED 準備までに限定し、GREEN / REFACTOR は `gdd-subagent-driven-implementation` に渡す
- test 要件の変更が必要なら build を止めて planning へ戻す
- `/gdd-dev` からは Claude Code: Sonnet subagent として / Cursor・Codex: worker 経由で dispatch される。RED 確立・state.md 更新後に 5行以内（報告行 1 行必須）のサマリーを返して終了する。実装への継続はメインセッションが担う

## In-Progress AC Trace Updates

RED を作成した時点で AC Trace Ledger（`ac-ledger.md`。`references/ac-trace-ledger.md`）に `RED-created` を append-only で追記する。実装前の RED は `status=unverified` として扱い、GREEN / REFACTOR で上書きせず新しい row を足す。

## Expected RED Failure Verification

wrong failure is not RED。test passes immediately なら RED ではない。failure message is expected で、fails because feature is missing と説明できる場合だけ RED とする。環境エラー・依存不足・テストランナー不備で落ちた場合は RED を取り直す。

## RED 証跡とは

RED 証跡は「実装前にテストが失敗していること」を示す記録。以下のいずれかの形式で残す。

## Pre-existing Implementation Without RED

superpowers `test-driven-development` の Iron Law を GDD TDD に吸収する。**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**。ただし GDD では既に差分が存在する resume / compact / handoff があり得るため、削除一択ではなく state machine に合う隔離手順を使う。

RED Evidence が無いのに production code 差分が既に存在する場合:

1. **Implementation Quarantine**: 既存差分を GREEN とみなさない。`tasklist.md` / `worklog.md` に「RED なし実装検出」と対象ファイルを記録し、`do not mark GREEN` と明示する。
2. **characterization RED**: 既存差分を見て期待結果に合わせるのではなく、`requirements.md` の AC と `Planned RED / E2E` から、現在の実装差分が無ければ失敗する最小テストまたは executable verification を作る。
3. **RED 確認**: 可能なら quarantine 前の base / 対象実装を一時的に無効化した状態 / missing behavior を再現できる方法で、テストが正しい理由で失敗することを確認する。
4. **GREEN 再判定**: 既存差分を戻して test が pass しても、それは「後付け GREEN」ではなく、RED evidence と AC binding が成立した後の verification として記録する。

この手順で RED が作れない場合は、実装を進めず `design_detail_only` または `human_recheck_required` に戻す。RED なしの既存実装を「もう動いているから」と completion evidence にしない。

### Quarantine Output Contract

RED なし実装を検出した場合は、通常の GREEN handoff ではなく quarantine handoff として出力する。

- `Gate Decision` に `result: RED not established` / `status: Implementation Quarantine required` / `decision: do not mark GREEN` を含める。
- `Implementation Quarantine` に対象 production files、`AC: <Current Task の AC ID>`、`Planned RED/E2E: <対応項目>` を記録する。実 ID が不明なら捏造せず、Current Task の再読を要求する。
- `Characterization RED Required` に「source は AC + Planned RED/E2E」「既存実装挙動から期待値を逆算しない」を明記する。
- route の既定は `design_detail_only`: AC / Planned RED は存在するが、RED evidence を作るために design / tasklist の詳細化が必要な場合。
- `human_recheck_required` に上げる条件: AC や Planned RED の意味変更、要求同士の矛盾、scope / policy 判断、または人間承認なしに testable AC へ変換できない場合。
- 出力ヘッダーの `Phase:` は `references/output-format.md` の workflow phase（通常 `build`）を使う。進捗バー上の表示名は `TDD:RED` であり、両者を混同しない。

### 形式 1: テストフレームワークがある場合（推奨）

テストファイルを作成し、実行して失敗を確認する。

```
# テスト作成
tests/test_pagination.py に AC-1 に対応するテストを追加

# テスト実行 → 失敗確認
$ pytest tests/test_pagination.py
FAILED tests/test_pagination.py::test_cursor_pagination - AttributeError: ...
1 failed in 0.12s

# → この fail output が RED 証跡
```

tasklist.md の Current Task に証跡を記録:

```markdown
#### RED Evidence

- test: `tests/test_pagination.py::test_cursor_pagination`
- result: FAILED (AttributeError: module 'api' has no attribute 'paginate')
- AC: AC-1
- Worktree: /Users/alice/.gdd/worktrees/example-repo/20260503-my-task
```

### 形式 2: テストフレームワークがない場合

executable verification（手動で実行可能な検証手順）を定義する。

```markdown
#### RED Evidence (executable verification)

- verification: `curl -s localhost:3000/api/users?cursor=abc | jq .next_cursor`
- expected: next_cursor フィールドが存在する
- current: エンドポイント未実装（404）
- reason: テストフレームワーク未導入（Terraform module / shell script 等）
- AC: AC-1
- Worktree: /Users/alice/.gdd/worktrees/example-repo/20260503-my-task
```

### 形式 3: 型チェック・lint が failing test の代替になる場合

```markdown
#### RED Evidence

- verification: `tsc --noEmit src/api/users.ts`
- result: error TS2339: Property 'paginate' does not exist on type 'UserRepository'
- AC: AC-1
- Worktree: /Users/alice/.gdd/worktrees/example-repo/20260503-my-task
```

## RED 証跡の品質基準

RED 証跡は形式だけでなく、**正しい理由で失敗していること**が必要。以下を満たさない場合は RED として認めない。

### 合格条件

- テストが **コードの不在/不足** で失敗している（`AttributeError`、`AssertionError`、`TypeError`、`not found` 等）
- executable verification の場合: 期待値と現在値の差分が AC に対応している
- 型チェックの場合: エラーが実装対象の型/プロパティに関するもの
- **AC ID が必須記載されている**（下記「AC ID Binding（必須）」参照）

### AC ID Binding（必須）

RED Evidence の各エントリには、`requirements.md` の AC ID（`AC-1` / `AC-F1` / `AC-deploy-smoke` 等の形式）を **必須フィールド** として記載する。`AC: <ID>` 行が無い RED は fail-closed で reject する（例外: `gdd-subagent-driven-implementation` 手順 17 が、`Covers AC:` の無い remediation task に書き写した節と、Step 1 で同じ task の節に追記するエントリと、`Fix Findings:` の行がある remediation task で Step 2〜5 が作る節で、差し戻しの元の finding が AC ID を明示していないもの。`AC:` を推定で書かず、`lint-ac` の WARN で残す）。

**必須ルール**:

- 1 つの RED Evidence エントリは 1 つ以上の AC ID に紐付ける（複数 AC を 1 RED でカバーする場合は `AC: AC-1, AC-2` のようにカンマ区切り）
- AC ID は `requirements.md` に実在するものでなければならない。架空 ID（`AC-todo` / `AC-pending` 等）は不可
- `Contract Surface Coverage` の各観点も、可能なら AC ID と紐付けて記録する（surface だけでは AC 対応が追えない）
- AC ID 未紐付けで RED を作成した場合、**fail-closed で停止**し以下を返す（main が inline で止まるときは `<gdd-stop reason="blocked">` の後に `## 👤 次にすること` も付ける。**text 出力のみ。state.md / tasklist.md への書き込みは不要**。書き込みは task-breakdown 側の責務）:
  - 参照した正本: 本 skill の「AC ID Binding（必須）」
  - 停止理由: RED Evidence に AC ID が未記載
  - 次の1アクション: `requirements.md` の AC を確認し、対応する AC ID を RED Evidence の `AC:` 行に追加してから再実行する（または `tasklist.md` の Current Task に `Covers AC:` 行を追記する）
- **AC ID 紐付けの責務分界**: AC ID と task の紐付け確定は **`gdd-task-breakdown` の責務**。TDD subagent は確定済み AC を消費する側であり、`requirements.md` を独自に読んで AC ID を推定で紐付けない。tasklist.md の `Covers AC:` 行が未記載なら fail-closed で task-breakdown に戻す（`Fix Findings:` の行がある remediation task は、上の例外のとおり戻さない）

**Why（state machine 一体型 TDD としての差別化）**: AC ID 紐付けが無い RED は「テストはあるが何の要件を担保しているか不明」になり、`gdd-completion-check` の AC Drift Check / `gdd-pr-review` の Spec Drift Check で追跡できない。superpowers の TDD は単体機能として完結するが、GDD TDD は AC ID を通じて `requirements.md` / `tasklist.md` / completion-check と一体化する。AC ID Binding を必須化することで、この一体性を構造で保証する。

### Worktree Binding（必須）

`references/subagent-dispatch.md` § Worktree Binding Precheck を RED 確立前に実行する（不一致・コマンド失敗なら fail-closed で停止し、テストファイルを一切書き込まない）。RED Evidence の各エントリには `Worktree: <path>`（precheck 実行後に観測した `git rev-parse --show-toplevel` の出力。宣言値ではなく観測値。`## Worktree` 自身との一致は既に precheck で確認済みのため、ここでは記録のみ）を必須記載する。`Worktree:` 未記載で RED を作成した場合はfail-closed で reject する（AC ID Binding と同じ「未紐付けなら reject」の型）。**Why（限界）**: この記録は自己申告であり、precheck 自体を無視した subagent の申告は検証できない。実効性の主体は `gdd-implementation-gating` § 1d の diff ファイル一覧突合（別 subagent による独立検出）にあり、本節はその前段（着手前の自己停止）を担う（subagent の cwd は呼び出し元セッションのまま変わらないため、2026-09-08 に呼び出し元 worktree への RED 漏れが実際に発生した再発防止）。

### Planned RED / E2E Binding（必須）

TDD は `requirements.md` の受入条件（AC）と `tasklist.md` の `Planned RED / E2E` を消費する。RED Evidence は AC ID に紐付くだけでなく、AC 本文が要求する検証水準と `Planned RED / E2E` に対応している必要がある。

**必須ルール**:

- Current Task に `Planned RED / E2E` が無い場合は fail-closed で task-breakdown に戻す。TDD 側で検証方法を推測し直さない
- RED Evidence は `Planned RED / E2E` に書かれた test / executable verification / E2E smoke と対応していることを記録する
- `e2e-required` の AC でも、E2E に残す境界と先に RED で固定する lower-level boundary を分ける。実配線 smoke だけを理由に unit / contract RED を省略しない
- `external-evidence-required` の AC は、実装前 RED と最終的に必要な外部証跡（CI / plan / describe / screenshot / log）を分けて記録する
- matrix または tasklist に `needs-clarification` / `non-testable-deferred` が accepted AC として残っている場合は、テストを書いて解釈を固定せず requirements / human check に戻す

RED Evidence への追記例:

```markdown
#### RED Evidence

- test: `tests/test_pagination.py::test_cursor_pagination`
- result: FAILED (AttributeError: module 'api' has no attribute 'paginate')
- AC: AC-1
- Worktree: /Users/alice/.gdd/worktrees/example-repo/20260503-my-task
- Planned RED / E2E: unit RED for cursor pagination; final E2E smoke for API response shape
```

**例外規定**:

- `quick (express)` で `tasklist.md` を最小構成で作成する場合も、Current Task に紐付く AC ID は `requirements.md` から最低 1 つ引いて RED に記載する。Express だから AC ID 不要にはしない
- 真に AC に紐付かない hygiene 修正（typo / コメント整形のみ等）は `Task Size: trivial` 扱いで TDD phase に到達しないため、本ルール対象外

### 出力フォーマットの品質基準（外部サービスへの出力を伴う場合）

外部サービス（Slack / GitHub / wiki 等）に出力するスキルでは、RED に以下のフォーマット検証を含める:

- `format_*_output()` 等のフォーマット関数のユニットテストで、出力先の制約違反をアサートする
  - 例（AgentCore Slack path）: `assert "<" not in output and ">" not in output` — angle bracket は HTML エスケープされてリンクが壊れる
- JSON 出力（`--json` 等）のスキーマテストで、期待するキー構造をアサートする
  - 例: `assert "org" in group and "projects" in group`
- テスト用 fixture に外部 API レスポンスのサンプル JSON を含める（`references/brainstorming-steps.md` § 8a の fixture があれば、テストの fixture 置き場に置いて使う。`.steering/` は PR に入らない） — E2E に行く前にユニットテストで出力形式を確定させる
- **Why:** 一覧の投稿機能で Slack の `<url|text>` エスケープ問題がユニットテストで検出されず、E2E（コンテナデプロイ後）まで発見が遅れた。フォーマットテストの品質基準を明示すれば、ユニットテスト段階で出力の正しさを確定でき、E2E サイクルを最小化できる

### Contract Surface Coverage（E2E 前に単体・契約テストで潰す）

RED 作成前に、今回の task が触る contract surface を列挙する。単なる正常系 1 本だけでは RED 不足として扱う。

必須観点:

- success path
- no-op / silent success path
- external API response variants（`references/brainstorming-steps.md` § 8a の fixture があれば、それを元にする）
- external API failure / unavailable path
- validation / sanitize / fail-closed path
- 条件で挙動が分かれる AC（すべて。例: 入力を受け入れるか止めるか〔判定・検査・フィルタ・guard・パーサ〕、副作用を起こすか起こさないか、retry・状態遷移をするかしないか）では、どの観点の行に当たるかを問わず、上の行に加えて AC ごとに `<AC ID> 止める側:`・`<AC ID> 境界:` の 2 行を足す。止める側は、AC が「通さない・起こさない・しない」と定める側（その側で起こすと AC が定める副作用もこの行で見る。3 つ以上に分かれる AC では、通す側以外の枝ごとに 1 行）。境界は、止めるべき入力のうち通す入力に最も近いもの（閾値の止める側の端、通す形と 1 箇所だけ違う入力）。各行は `references/testing-anti-patterns.md` § テスト判定基準 で選び（消したら見逃す不具合をクラスと 1 文で言えるものだけ。この 2 行はクラス I に当たる）、言えない行は `not_applicable（理由）` にする。実装前から通るテストは、そのテストを書く行に `実装前から pass（対照）` と書き、RED Evidence には入れない。このテストは、同ファイル § 新しいテストの受入条件 2 のとおり、止める分岐を外す・閾値を 1 つ通す側へずらすなどの変異を既存の実装に入れて落ちることを確かめ（変異は git の履歴に触れずに入れて戻す。変える production ファイルを先に worktree の外の一時ディレクトリ〔`mktemp -d`〕へ複製し、変異を入れてテストを回す。テストが落ちても落ちなくても、次の操作（テストの修正・行の記録・次の変異）の前に複製で上書きして戻し、`cmp <複製> <ファイル>` で入れる前と同じことと、対照のテストが pass することを確かめる（テストを直して確かめ直すときは、戻した後にもう一度入れる）。commit・`git reset`・未 commit の差分を捨てる操作〔`git checkout --`・`git restore` など〕・worktree 間で共有される `git stash`・別の worktree は使わない。並列バッチでは、バッチの全 task の RED を取り終えてから 1 つずつ入れる）、行に `変異: <入れた変異> -> <落ちたテスト名>` と書く。落ちなければ検出力が無いので、テストを直す（2026-10-08〜10 に、implementation-gating が `test-power` で差し戻した理由は止める側のテストの欠落が最も多く、その大半は境界も欠けていた）
- formatting / output schema path
- duplicate / idempotency / lock path
- user-visible side effect path

各観点について `applicable` / `not_applicable`（AC ごとの 2 行は `実装前から pass（対照）` も）を tasklist.md の RED Evidence 付近に明示する。`applicable` な観点は、可能な限り unit test / contract test / fixture-based executable verification を少なくとも 1 本追加する。

外部サービス配線そのもの（GitHub に実コメントが表示される、Slack event が実配送される等）だけは E2E に残してよい。ただしその場合も、E2E に残す境界と unit / contract test で固定する境界を分けて記録する。

補足ルール:

- `formatting / output schema path` は Slack / GitHub / wiki / JSON / Markdown / machine-readable payload のような**外部向けまたは機械可読な出力契約**に使う。pure function の primitive return 値（number / bool / string など）は通常 `success path` / `validation path` で扱い、この観点には入れない。
- `external API failure / unavailable path` は、approved な AC / design に書かれた期待境界（fail-closed / skip / continue degraded / summary only 継続など）を RED に落とす。期待境界が未定義なら、テストで勝手に決めず planning / design へ戻して明文化させる。
- `duplicate / idempotency / lock path` は「その surface を今回の変更で触るか」で判断する。関連コードが repo に存在するだけでは `applicable` にしない。

例:

```markdown
#### Contract Surface Coverage

- success path: applicable -> `test_runtime_review_posts_summary`
- no-op / silent success path: applicable -> `test_cost_estimate_short_circuits_without_candidate_files`
- external API response variants: applicable -> `test_fetch_pr_files_accepts_gateway_data_payload`
- external API failure / unavailable path: applicable -> `test_fetch_pr_files_failure_continues_normal_route`
- validation / sanitize / fail-closed path: applicable -> `test_runtime_review_rejects_sanitized_secret_before_inline_post`
- AC-3 止める側: applicable -> `test_runtime_review_rejects_sanitized_secret_before_inline_post`
- AC-3 境界: 実装前から pass（対照） -> `test_runtime_review_rejects_shortest_matching_secret`、変異: secret とみなす最短長を 1 長くする -> `test_runtime_review_rejects_shortest_matching_secret`
- formatting / output schema path: applicable -> `test_pr_review_metadata_schema`
- duplicate / idempotency / lock path: not_applicable (no lock behavior changed)
- user-visible side effect path: E2E only -> GitHub comment visibility smoke
```

**Why:** E2E で見つかる不具合の多くは、実配線ではなく payload variant / no-op 分岐 / sanitizer 順序 / schema drift / lock 境界の見落とし。TDD 入口で surface を棚卸しして RED を作ると、E2E は配線 smoke に集中でき、デプロイ後の発見と手戻りを減らせる。

### 不合格条件（RED ではなく環境問題）

- `ConnectionRefused` / `ECONNREFUSED` → サーバーが起動していないだけ
- `Timeout` / `ETIMEDOUT` → ネットワークや外部サービスの問題
- `Permission denied` → ファイル/ポートの権限問題
- `Module not found` で、原因が `npm install` / `pip install` 漏れ → 依存解決の問題
- テストランナー自体のエラー（config 不備、plugin 不足等）

環境問題の場合は先に環境を修正し、改めて RED を取り直す。「修正」には次の 2 種類がある:

- **環境セットアップ修正**: DB/サーバーの起動、権限の付与、`npm install` / `pip install` 等
- **テスト設計の修正**: 実際の外部サービス（SMTP・DB・外部 API 等）を `mock/stub` で差し替える — テストが外部サービスに依存して接続エラーになっている場合は、環境を立てるのではなくモックで外部依存を除去し、コードの不在/不足で失敗するよう書き直す

## Steps

1. `tasklist.md` の現在 task を確認する。
   - **Express Path の場合（`Task Size: quick (express)`）**: `tasklist.md` がまだ存在しない。`references/phase-progression.md` § Express の遷移ルールに従い、最小構成（`Current Task` に AC を直接紐付けた 1 タスク〔`Complexity:` 付き〕 / `Pending Tasks: - なし` / `Completed Tasks: - なし` / `Next Action=gdd-test-driven-development` / `Fix Attempts: 0`）で新規作成してから次 Step に進む。`worklog.md` に `## Origin Findings` があれば、その行をこの 1 タスクの `Fix Findings:` に写す（`references/state-machine.md` § tasklist.md の canonical state）。
   - **Standard / quick (standard) / quick (express → standard) の場合**: `Current Task` が空なら、`Pending Tasks` の先頭 task を `Current Task` に移す。Gate Batch で `Current Task` に複数の task があるときは、`Execution Status: completed` でない task（差し戻し後は finding の対象の task）だけを対象にする。
   - **Post-Compaction Resume Check（必須）**: `Current Task`（並列バッチ実行中は Current Task に並ぶ各タスク）に `#### RED Evidence` が既に記録されているか確認する。記録済みのタスクは RED 確認済みとみなし、Step 2〜4 をスキップして Step 10（実装 handoff）へ進む。ただし、`gdd-implementation-gating` Step 1d が差し戻す形の節は記録済みに数えず、RED を今の worktree で取り直す。判定は Step 1d と同じにする（`Worktree:` の欠落・不一致、ファイルパスを持つ形式でそのパスが差分にも未 commit の分にも無いこと。形式の分け方・パスの正規化・`<default-branch>` の決め方も同じ。default branch は `git symbolic-ref --short refs/remotes/origin/HEAD` で決め、失敗するか `git rev-parse --verify` で解決できなければ `origin/main`・`origin/master`・`origin/trunk`・`origin/develop` の順に確かめた最初のもの。local の branch 名は使わない〔`agents/gdd-formal-gate-runner.md` の `対象の差分` と同じ〕）。判定の `git diff`/`git status` が失敗した節も数えない。取り直しは次のとおりで、`#### RED Evidence` が無い（未記録の）タスクでも、`gdd-implementation-gating` で差し戻された task（その task の `Gate Rounds` が 1 以上）で、その task の `Files:` の production ファイルに差分が既にあるときは同じにする（`Gate Rounds` が 0 の task は、前の task の実装で差分があっても通常の Step 2〜4 にする）: § Pre-existing Implementation Without RED の 2・3 で characterization RED を取る。3 で実装を無効にするのは `## Worktree` の中の一時 commit で戻せる形に限る（task のファイルだけを一時 commit し〔`.steering/` は入れない〕、base の内容でその production ファイルを外して RED を観測し、一時 commit の内容に戻して pass を確かめ、`git reset --soft HEAD~1` で一時 commit を外す。一時 commit の前の未 commit の差分を捨てる操作と、worktree 間で共有される `git stash`、別の worktree は使わない）。Step 5 の記録の前に、同節の 4 のとおり実装を戻してテストが pass することを確かめる。取れたら Quarantine Output Contract の既定 route には回さず Step 5・10 へ進み、取れなければ同節のとおり `design_detail_only` か `human_recheck_required` に戻す。`Covers AC` か `Planned RED / E2E` が無い task は、Step 2 のとおり task-breakdown に戻る（Step 2 の `Fix Findings:` の例外を除く）。取り直した RED は、数えなかった節を置き換えて記録する（節を足さない。古い節が残ると Step 1d が古い節を読む）。未記録のタスクだけを対象に Step 2〜4 を実行する（上の差し戻された task の取り直しを除く）。ただし、`Fix Findings:` の行がある task（差し戻しの finding が書かれた task。出所を問わない。書く側と形は `references/state-field-tiers.md` の `Fix Findings` の行）では、その行の finding ごとに、記録済みの RED Evidence にその指摘を再現するテストが無ければ、Step 3 で `references/self-review-lanes.md` § 直し方（冒頭の当てる範囲と 1・2）のテストを足して落ちることを確かめ、同じ節に追記する（節を足さない。RED Evidence の節がまだ無い task では、その finding を Step 2〜4 の RED の対象に含める。文言・帳簿だけの指摘には当てない。今の worktree ですでに通るテストしか書けない finding は RED に数えず、その task の RED Evidence の節に `再現せず: <finding>（書いたテストと pass の出力）` と書く。実装の controller は worker への handoff で RED Evidence を渡すので、この行も worker に届く）。**Why**: context compaction 後に再入した場合、どのタスクの RED が確認済みかがコンテキスト上から消える。`tasklist.md` の `RED Evidence` を正本として参照することで重複確認と余分な RED 取り直しを防ぐ
2. Current Task の `AC` / `Covers AC` / `Planned RED / E2E` を確認する（`Fix Findings:` の行がある remediation task では、`Covers AC` が無くても戻さない。AC ID Binding の例外）。`Planned RED / E2E` が欠けている、または AC 本文が要求する検証水準と矛盾している場合は fail-closed で task-breakdown に戻す。
3. 可能なら failing test を先に追加し、失敗を確認する。
4. test harness が無い場合は、理由を明記し、最小の executable verification を定義する（上記「形式 2」参照）。
5. RED の証跡を tasklist.md の Current Task に記録する。証跡には `AC:` と `Planned RED / E2E:` を含める。
6. planning へ差し戻す場合は `references/rollback-patterns.md` の該当パターンに従い Gate Status を永続化する。
7. planning の組み直しが必要なら `planning_rework_required` パターンで `gdd-brainstorming` に戻す。
8. 狭い要件・実装方針変更だけで人間判断が必要なら `human_recheck_required` パターンで永続化する。
9. 要件は変わらないが detailed design の修正が必要なら `design_detail_only` パターンで `gdd-design-gating` に戻す。
10. 実装準備が整ったら、RED の証跡を根拠に `Next Action=gdd-subagent-driven-implementation` に進める。
11. review handoff 可能な実装差分を作る責務は持たず、GREEN / REFACTOR と review handoff は `gdd-subagent-driven-implementation` に委譲する。

## Output Guidance

- phase 遷移時は `references/output-format.md` の統一ヘッダーを出力冒頭に付ける
- build-state の成功遷移を説明するときは、`gdd-test-driven-development` は RED 準備まで、成功後は `Next Action=gdd-subagent-driven-implementation` と明示する。
- `/gdd-dev` からは Claude Code: Sonnet subagent として / Cursor・Codex: worker 経由で dispatch される。`Next Action=gdd-subagent-driven-implementation` を state.md に設定し、tasklist.md に RED Evidence を記録した後、5行以内（報告行 1 行必須）のサマリーを返して終了する。`gdd-stop` マーカーは使わない。実装（GREEN / REFACTOR）への継続はメインセッションが担う。詳細は `.steering/<task>/handoff/tdd.md` に書く（`references/subagent-dispatch.md` § Subagent Return Output Contract 参照）。

## Rationalization Check（この skill 固有）

RED を省略したくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。全体向けは `references/common-guardrails.md` § 合理化防止テーブル。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「テスト書かなくても実装は正しい、見れば分かる」 | 「見れば分かる」で通った実装は後のリファクタで簡単に壊れる。RED は未来の自分への証拠 | [Bias for Action] 動くコードを早く見たい欲求が、リグレッション防止コストを過小評価する |
| 「この変更は test 不要なほど自明」 | 自明なら RED も 1 分で書ける。書けないなら「自明」ではない | [Curse of Knowledge] 「自明」と感じるのは書き手の脳内だけ。reviewer や保守者には自明ではない |
| 「テストフレームワークが無いから RED は取れない」 | 形式 2（executable verification）/ 形式 3（型チェック・lint）がある。「無い」が飛ばす理由にはならない | [Bias for Action] 「無いから飛ばす」は典型的な省略口実。代替手段の存在を確認していない |
| 「まず実装して後からテスト書く」 | 後から書くテストは「通る実装に合わせる」ので、バグを素通りさせる。先に失敗させる必要がある | [Confirmation Bias] 通る実装に合わせた test は、仮説の反証ではなく支持証拠の収集になる |
| 「ConnectionRefused で落ちたから RED 成立」 | 環境問題は RED ではない。コードの不在/不足で落ちたものだけが RED 証跡 | [Tooling Faith] テストフレームワークが「失敗を返した」だけで RED が成立すると錯覚する |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、planning 差し戻し route）。以下はこの skill 固有のルール。

- test より先に本体コードを書かない
- requirements / AC / 実装方針の変更を黙って進めない
- failing test の証跡か、その代替 verification を残す
- この phase で GREEN / REFACTOR や review handoff 完了まで進めない
- 本体コード実装と refactor の主責務は `gdd-subagent-driven-implementation` 側に置く
- **RED にするテストは `references/testing-anti-patterns.md` § テスト判定基準 で判定する**。消したら見逃す不具合をクラスと 1 文で言えないテストと、同節の「書かない・消すテスト」に当たるテストは RED として認めない。mock / stub を使う RED は同ファイルの Iron Laws（mock の振る舞いをテストしない / test-only コードを production に置かない / 依存を理解せず mock しない）を満たす（mock 要素へのアサーションや partial mock は false confidence を作る）
- **AC ID Binding（必須）**: RED Evidence に `AC: <ID>` 行を必須記載する。AC ID 未紐付け RED は fail-closed で reject する（state machine 一体型 TDD の構造保証。詳細は本 skill § AC ID Binding（必須）参照）
- **Planned RED / E2E Binding（必須）**: RED Evidence は Current Task の `Planned RED / E2E` に対応していることを記録する。`Planned RED / E2E` 欠落時は task-breakdown に戻し、TDD 側で検証方法を推測しない
- **Context Compaction Resilience**: RED 作成前に `tasklist.md` の `Current Task`（対象 AC と期待動作）をディスクから re-read する。複数 task の RED を連続作成する場合、2 task 目以降で compaction により AC 詳細が劣化するリスクがあるため、各 task の RED 開始時に re-read する。re-read 後は Step 1 の **Post-Compaction Resume Check** に従い、記録済みに数える節があるタスクの RED を再実行しない（Step 1d が差し戻す形の節は数えない）
