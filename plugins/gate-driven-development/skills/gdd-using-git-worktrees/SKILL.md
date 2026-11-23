---
name: gdd-using-git-worktrees
description: "Use for GDD worktree setup, root checkout protection, merge cleanup, or post-merge continuation."
version: 0.1.0
---

# Using Git Worktrees Lite

formal workflow の worktree 判断軸は `references/workspace-policy.md` を参照。この skill は active worktree の準備・再利用・guard・cleanup を一本化した helper。phase ではなく、worktree 管理の全操作を扱う。

## Worktree Provenance Gate

GDD の実装・PR・cleanup 前に Worktree Provenance Gate を通す。`task slug / branch / PR / steering / scope` が一致しない場合は fail-closed とし、root bleed や stale worktree を疑う。

## Fixed Model

- `Claude Code`: `sonnet` + `effort=low`
- `Cursor`: `Grok 4.5` + `reasoning.effort=low` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=low`（leaf tier）
- worktree の作成・cleanup は定型的な git 操作のため、leaf task 相当の軽いモデルで十分

## Goal

- active worktree を準備する（新規・resume・legacy migration）
- worktree なしで formal workflow が進む経路を止める（guard）
- PR merge 後の follow-up では既存 worktree を整理対象として診断し、追加実装用の新 worktree を latest default branch から作る
- merge 後の worktree / branch cleanup を安全に行う
- formal entry の呼び出し元へ `Baseline Verification Status`（`baseline_command` / `pass` / `fail` / `not_run`）を返し、brainstorming / human check が作業前の検証状態を表示できるようにする

## Worktree の準備

1. 対象プロジェクトが git repository か確認する。
2. default branch を判定する。判定できない場合は fail-closed で停止し、base branch を確認する復旧手順を返す。
3. **Dirty Working Tree Check**: `git status --porcelain` で未コミット・未ステージの変更を確認する。変更がある場合:
   - 変更内容の概要（ファイル数・種類）を表示する
   - **対話モード**（ユーザーが直接 `/gdd-dev` を呼び出し、かつこの skill を直接実行している場合）:
     - 以下の選択肢を提示し、ユーザーの選択を待つ:
       - **stash**: `git stash push -m "gdd: pre-worktree stash"` で退避してから worktree 作成に進む
       - **commit**: 現在の変更をコミットしてから進む（コミットメッセージはユーザーに確認）
       - **continue**: 変更を無視して worktree 作成に進む（変更は現在のブランチに残る）
   - **非対話モードの判定**: 以下のいずれかに該当する場合は非対話モード。判断に迷う場合も非対話モードに倒す（auto-continue の方が安全側）:
     - この skill を呼び出した元が別の skill / phase（brainstorming / design-gating 等）である
     - Cursor Composer / IDE のエージェントモードで実行されている
     - ユーザーが `/gdd-dev` または `/gdd-using-git-worktrees` をターミナルに直接入力していない
   - **非対話モード**（上記判定に該当する場合）:
     - **auto-continue**: ユーザー確認なしに worktree 作成へ進む。root の未コミット変更は新 worktree には反映されずそのまま残る（データロスはない）
     - 新タスクの `state.md` の `## Notes` セクションに以下を記録する:
       ```
       - worktree 作成時に root に未コミット変更あり（auto-continue）: <ファイル一覧>
       ```
   - **Why:** `git worktree add` 自体は dirty working tree でも正常動作する。未コミット変更は新 worktree に反映されないが root に残るためデータロスはない。subagent / Cursor Composer エージェントは対話 API を持たず、確認待ちで詰まると worktree 作成をスキップして root に `.steering/` を作る最悪の fallback が発生していた。non-interactive 時の auto-continue でこれを防ぐ
4. `new` の場合:
   - 現在の release branch や既存 task 用 branch を流用せず、default branch から task 専用の branch と worktree を作成する。
   - worktree の作成先パスは以下の優先順位で決定する:
     1. プロジェクトルートの `.gdd-config.md` に `Worktree Base:` が指定されていればそのパス（例: `~/.gdd/worktrees`）
     2. 未指定の場合は `~/.gdd/worktrees` をデフォルトとする
   - 作成先フルパス: `<Worktree Base>/<repo-name>/<task-slug>`（例: `~/.gdd/worktrees/example-repo/20260503-my-task`）
   - `git worktree add <full-path> -b <branch-name> <default-branch>` で作成する
   - 作成完了後、**worktree の絶対パス**（`$WORKTREE_ABS_PATH`）を呼び出し元 skill に明示的に返す。この値は後続の `.steering/` artifact 作成に必須
5. `resume` の場合:
   - `git worktree list` で既存候補を列挙する。
   - task slug が branch 名に含まれる（部分一致）worktree だけを再利用候補とする（例: slug `user-auth` は `feature/user-auth` にマッチする）。slug が branch 名に含まれない worktree は候補に含めない。
   - 候補に含める前に **Worktree Pollution Guard** の identity tuple を検証する。path slug / steering slug / state task id / git branch / state active branch がズレる candidate は再開候補にしない。
   - 再利用候補が見つかった場合、**差分汚染チェック**を行う:
     - `git diff --stat` と `git log --oneline main..HEAD` で、その worktree に現在のタスクと無関係な変更やコミットが含まれていないか確認する
     - 別テーマの変更が混在している場合は再利用せず、新規 worktree の作成をユーザーに提案する
     - 既に PR が作成されていて別テーマの変更を含む場合は、再利用より新規分離を優先する
   - worktree candidate が複数あれば fail-closed にする。新しい worktree や `.steering/...` を作って曖昧さを吸収しない。
6. legacy migration の場合:
   - worktree candidate が無く、migration 対象の root 側 `.steering/...` が 1 つに解決できたときだけ worktree を作成。
   - worktree 側 `.steering/...` が未配置なら root 側から 1 回だけコピーする。
7. active worktree 側 `.steering/...` を canonical artifact として扱う。
   7a. **Steering Ownership Check**:
   - task slug に対応する raw task steering `.steering/<slug>/` は **branch-only steering** であり、active branch / active worktree の中では managed artifact として扱う。
   - worktree 解決後に root 側 `.steering/<slug>/` が見つかった場合、**legacy migration 以外では通常の untracked file として無視しない**。root bleed / 置き去り artifact の疑いとして扱い、continue 前に解決する。
   - 許容されるのは以下だけ:
     1. legacy migration のコピー元として 1 回だけ読む
     2. active worktree 側 artifact が正本で、root 側 duplicate をユーザー確認付きで片付ける
   - worktree 側と root 側の両方に同一 slug の steering があり、どちらを正本とするか自明でない場合は fail-closed。新しい `.steering/<slug>/` を追加で作って曖昧さを吸収しない。
   - task の branch / PR を作る段階では、active worktree 側 `.steering/<slug>/` を「あとで回収する untracked file」ではなく **branch-only steering** として所在と正本性を確定する。ただし standard 運用では raw task `.steering/<task>/` を PR / main に載せず、重要判断は `docs/adr/` へ **Distill to ADR** する。main には raw task `.steering/<task>/` を含めない。
   - repo-level learned-patterns（例: `docs/learned-patterns.md`）は raw task steering ではない。repo が既に cross-task learning file として採用している場合だけ、cleanup 前の persistence 対象として扱う。採用済み判定は、`origin/<default-branch>` で `docs/learned-patterns.md` が tracked、または `.gdd-config.md` / repo docs に learned-patterns の保存先が明記されていること。repo が main に `.steering/` を置かない方針なら、新規作成せず `docs/adr/` または repo 既定の学習ファイルに蒸留する。
   - **Branch-only transfer**: 作業中の task branch では、別マシン・別ホスト・別人への引き継ぎが必要な場合だけ raw task `.steering/<task>/` を一時 commit / push してよい。原則は ADR / PR body / continuation summary で引き継ぐ。raw steering を push する前に機密情報チェックを通し、PR 作成前に重要判断を ADR / PR body / 採用済み learned-patterns へ蒸留し、tracked raw task steering は `git rm -r .steering/<task>/` などで除去する。main へ merge される diff は raw task steering net-zero でなければならない。raw steering を一時 push した branch は squash merge と merge 後 branch delete を前提にする。cleanup unsafe の場合でも旧 worktree は保持し、後続実装は latest default branch から作る新 worktree で進める。
8. この helper は `Next Action` を更新しない。phase の進行は呼び出し側 skill が所有する。

## Worktree Pollution Guard

resume / cleanup / active steering 解決では、候補を採用する前に以下の **Worktree Identity Tuple** を作る。

| field | 取得元 |
|---|---|
| `worktree_path_slug` | dedicated worktree の basename（例: `~/.gdd/worktrees/<repo>/<slug>` または repo-local `.worktrees/<slug>`） |
| `steering_slug` | `.steering/<slug>/state.md` の directory basename |
| `state_task_id` | `state.md` の `Task ID` / `Task` / `Steering ID`（無ければ `steering_slug` fallback） |
| `git_branch` | `git worktree list --porcelain` の `branch` または `git branch --show-current` |
| `state_active_branch` | `state.md` の `Active Branch`（無い場合は空） |
| `worktree_base_kind` | `gdd-managed` / `repo-local` / `host-managed` / `repo-root` |

> **注記**: `worktree_base_kind = host-managed` は `EnterWorktree` tool で作成された worktree を示す。active `/gdd-dev` session 中の新規作成は PreToolUse hook（`run-block-enter-worktree-hook.sh`）で block されるため、この分類が検出される場合は hook 導入前に作られたか、hook 対象外環境（Cursor 等、`EnterWorktree` tool 非対応）で作成された可能性が高い。

candidate は次をすべて満たす場合だけ clean とする。

- dedicated worktree（GDD managed / repo-local `.worktrees`）では `worktree_path_slug == steering_slug`
- `state_task_id` が存在する場合は `state_task_id == steering_slug`
- `git_branch` が存在する場合は branch 名に `steering_slug` が含まれる
- `state_active_branch` が存在する場合は `state_active_branch == git_branch`

以下は **worktree pollution** として fail-closed する。自動 resume しない。新しい `.steering/...` を作って mismatch を吸収しない。

- `path_slug_mismatch`: dedicated worktree basename と `.steering/<slug>` が違う
- `state_task_mismatch`: `state.md` の task id と directory slug が違う
- `branch_slug_mismatch`: current branch が別 task slug を指す
- `active_branch_mismatch`: `state.md` の `Active Branch` が current branch と違う
- `multiple non-terminal steerings`: 同一 worktree に 2 つ以上の non-terminal steering がある
- `mixed worktree bases`: GDD managed (`~/.gdd/worktrees` / configured Worktree Base) と repo-local `.worktrees` / host-managed `/private/tmp` などが同時に候補化する

fail-closed 時は候補表に identity tuple と mismatch reason を出し、人間の 1 アクション（どの slug を再開するか / どの worktree を cleanup するか / 新規作成するか）を要求する。

## Multi-Steering Active 解決

worktree 列挙で non-terminal（`Next Action` または `Resume From` が `done` / `cancelled` 以外）な steering が複数見つかった場合の解決ルール。

### 解決の優先順位

1. **worktree が異なる**: 各 worktree に 1 つずつ steering がある場合、ユーザーに候補一覧を提示して選択させる。自動選択しない
2. **同一 worktree に複数 steering**: 以下の順で絞り込む
   a. `state.md` を持つ steering だけを active candidate とする。`design.md` だけの旧 artifact は候補から除外する
   b. `Next Action` または `Resume From` が terminal（`done` / `cancelled`）なものを除外する
   c. stale brainstorming（`Started At` が 10 日超前かつ `Resume From=gdd-brainstorming`）を除外する
   d. Worktree Pollution Guard の identity tuple を全候補で検証する。polluted candidate が 1 件でもあれば fail-closed
   e. 同一 worktree に異なる slug の non-terminal steering が 2 件以上残る場合は fail-closed。`Started At` 最新だけで自動選択しない
   f. 同一 slug の duplicate など、clean かつ branch が同じ slug だけを指す場合に限り、`Started At` を tie-breaker として使える
   g. `Started At` が無い / 同率最新 / branch slug と latest candidate がズレる場合は fail-closed で停止し、候補一覧を返す
3. **worktree が無い環境（root 直接）**: legacy migration の対象か判定する。root 側 `.steering/` が 1 つだけなら worktree を作成して移行。複数あれば fail-closed

### Stale steering の判定

以下のすべてを満たす steering は stale 候補として扱い、active 解決の候補から除外する:

- `state.md` の `Started At` が 10 日超前
- `Resume From` が `gdd-brainstorming` のまま（planning 序盤で放棄された可能性が高い）

stale 候補を除外しても複数残る場合は fail-closed。stale 候補の自動削除はしない（ユーザーに cleanup を提案するだけ）。

**Stale 候補の一覧確認（manual cleanup helper）**:

```sh
${CLAUDE_PLUGIN_ROOT}/scripts/find-stale-steerings.sh                  # current worktree のみ
${CLAUDE_PLUGIN_ROOT}/scripts/find-stale-steerings.sh --all-worktrees  # 全 worktree
${CLAUDE_PLUGIN_ROOT}/scripts/find-stale-steerings.sh --threshold-days 30  # 閾値変更
```

各 stale 候補について、cancel / resume の手順を提案する read-only script（移動・削除は提案しない）。auto delete は禁止（Cursor 等の別 runtime で作業中の可能性があるため、各候補をユーザーが確認してから実行する）。

## Worktree Guard

- `/gdd-dev` の開始・再開時、`.steering/...` 更新前に worktree が決まっていることを保証する
- worktree 有無の判断軸は `references/workspace-policy.md` を参照。このガードを実施する

### Root Branch Creation 禁止

GDD formal workflow の setup is mandatory。repo root checkout で次のコマンドを使って task branch を作らない:

- `git switch -c`
- `git checkout -b`
- `git branch <name>`

existing `codex/YYYYMMDD-*` branch does not satisfy the GDD worktree contract。branch 名が GDD 風でも、dedicated worktree と `.steering/<slug>/state.md` の identity tuple が揃うまでは実装場所ではない。

正しい作成形:

```sh
git worktree add <full-path> -b <branch-name> <default-branch>
```

ただし、worktree created from `HEAD` is not enough。`HEAD` は現在の task branch や host-managed checkout の文脈を引き継ぐため、`origin/<default-branch>` または recorded Base Commit を使う。local `main` / `master` / `develop` も stale の可能性があるため、新規 task の base として直接使わない。 例外は Stage Continuation の stacked 分岐（`Continuation Mode=auto-stacked`）のみで、この場合だけ**未マージ先行 Stage の branch** を base にしてよい（`references/post-completion-pr-flow.md` Option 1 手順 6 § Stage Continuation）。

機械ガードは `run-worktree-command-guard.sh` / `validate-worktree-command.py` が担う。LLM 側も同じ契約を守り、root branch を作ってから後で移す運用にしない。

### Root Diff Patch Migration Recovery

root checkout で開始したため dedicated worktree へ移行した、という状態は recovery 専用手順として扱う。通常の GDD 開始手順として使わない。

- root task branch では TDD / implementation / verification / PR 準備を始めず、dedicated worktree だけで実行する
- host-managed Codex / Cursor / Claude Code checkout は implementation worktree として採用しない
- 新しい worktree は `origin/<default-branch>` または recorded Base Commit から作る
- 例外: Stage Continuation の stacked 分岐（`references/post-completion-pr-flow.md` Option 1 手順 6 § Stage Continuation）（`Continuation Mode=auto-stacked`）では、**未マージ先行 Stage の branch** を base にしてよい（第 3 の許容値）
- root checkout で TDD / implementation を完了してから移す運用は禁止
- すでに root diff ができている場合は、差分を patch として保存し、dedicated worktree に適用したことを worklog に記録する

## Pre-Follow-up Hygiene Gate

**Post-Merge Follow-up Worktree Policy**: `PRマージ後の追加実装`、またはユーザーが「既存 worktree を整理してから新しい worktree を切る」と指示した場合に適用する gate。元 worktree / branch は整理対象であり実装場所として再利用せず、必ず fetch 済み latest default branch から新しい amendment / hotfix worktree を作る。

### 診断項目

1. **merge 状態**: 対象 PR / branch が default branch へ merge 済みか確認する。merge 済みなら follow-up implementation は元 branch に追加しない。
2. **identity tuple**: Worktree Pollution Guard の `worktree_path_slug` / `steering_slug` / `state_task_id` / `git_branch` / `state_active_branch` / `worktree_base_kind` を対象 worktree ごとに表示する。
3. **dirty diff**: `git status --porcelain` / `git diff --stat` / default branch との差分を確認し、未 commit・未 push・別テーマ混入を整理対象として分類する。
4. **steering contamination**: 同一 worktree 内の non-terminal steering 数、root 側 duplicate `.steering/<slug>/`、host-managed / repo-local / GDD-managed の混在を確認する。
5. **cleanup ownership**: GDD managed worktree / host-managed worktree / repo root を分類し、削除してよい境界を判定する。
6. **default branch refresh**: 新 amendment / hotfix worktree を作る直前に `git fetch origin` を実行し、default branch の最新 `Base Commit` を記録する。fetch できない場合は fail-closed で停止し、offline base から作らない。

### HITL 出力

HITL には以下を短く出す。長い `git status` 全文ではなく、ズレると危険な判断だけを露出する。

| 項目 | 表示内容 |
|---|---|
| マージ後 follow-up 判定 | `read-only verification` / `amendment` / `hotfix` |
| 既存 worktree 整理結果 | `clean` / `dirty` / `polluted` / `host-managed` / `cleanup blocked` |
| 元 worktree の扱い | `cleanup/archive/keep 対象。実装場所として再利用しない` |
| 新 worktree | path / branch / base branch / base commit |
| 先行成果物 | origin steering / PR / origin branch / merge commit |
| 人間の次アクション | cleanup 方針の承認、または新 worktree 作成の承認 |

### 実装場所の決定

- `read-only verification`: 新しい実装 branch は作らず、merge 後確認だけを記録する。必要なら一時 workspace を使うが steering を更新しない。
- `amendment`: `git fetch origin` 後の latest default branch から `<YYYYMMDD-amendment-<slug>>` worktree / branch を作る。新 steering に `Amendment of` / `Origin PR` / `Origin Branch` / `Origin Merge Commit` / `Base Branch` / `Base Commit` を記録する。
- `hotfix`: `git fetch origin` 後の latest default branch から `<YYYYMMDD-hotfix-<slug>>` worktree / branch を作る。Hotfix Lane の `Origin Steering` / `Trigger Hotfix` / `Parent Hotfix` / `Abandoned Hotfix Attempts` / `## Origin Findings` 規約に従い、`Base Branch` / `Base Commit` も記録する。
- post-merge follow-up の `git worktree add` は local default branch ではなく、fetch 済みの `origin/<default-branch>` または記録済み `Base Commit` を base にする。

### Guardrails

- merge 済み branch / worktree へ follow-up 実装を追加しない。
- 元 worktree を実装場所として再利用しない。
- cleanup が未完了でも、元 worktree を「一時的に」実装場所へ戻さない。
- identity tuple が mismatch した worktree は cleanup 候補として表示し、resume / amendment の実装候補から除外する。
- host-managed worktree は削除せず、保持方針と手動手順を提示する。
- dirty diff がある場合は破棄しない。commit / stash / keep / archive / discard の必要判断を HITL に出す。
- 新 worktree の base branch / base commit が確認できない場合は fail-closed で停止する。
- `git fetch origin` が失敗した場合は latest default branch を確認できないため fail-closed にする。古い local default branch を latest とみなさない。

## Post-Merge Cleanup

merge 後の local cleanup を扱う。これは通常ローカル整理であり、後続実装前に案内する。

standard 運用では raw `.steering/<task>/` は branch-only steering であり、merge 後の読者向け正本は `docs/adr/` の Distill to ADR、PR body、CI / test evidence である。cleanup 前に ADR または `ADR distilled: not_applicable | reason: ...` が保存済みであることを確認する。main には `.steering/` を含めない。

### Merge Report Cleanup Trigger

ユーザーが `マージした` / `mergeした` / `merged` と報告した場合、それは post-merge verification だけでなく **cleanup requested** と **deployment/status verification requested** の cue として扱う。GDD は worktree 作業が基本なので、merge 済みの旧 worktree / branch は次の実装場所ではなく整理対象である。

標準の流れ:

1. fetch して PR merge commit が default branch に **main reflected** か確認する
2. read-only で **CI/CD or deploy/apply reflection checked** を見る（見る workflow は `references/post-completion-pr-flow.md` § Manual Merge Continuation 1 の一覧か run）
3. そこに deploy/apply が無ければ「対象外」
4. 反映確認が成功し、`safe cleanup ready` なら local cleanup を実行する
5. cleanup 後、完了報告に main commit / CI-CD status / cleanup 結果を短く出す

ここでの deploy/apply は **既存 CI/CD の状態確認** であり、手動 deploy / terraform apply / production write の実行許可ではない。新しい write 操作が必要なら AGENTS.md / Operational Safety に従い別承認を取る。

`safe cleanup ready` は次をすべて満たす場合だけ:

- PR state が read-only 確認で merged
- default branch に merge commit が main reflected
- 必要な CI/CD or deploy/apply reflection checked が success または対象外
- post-merge verification が pass
- 対象が **GDD managed worktree**
- **stacked 依存の確認**: cleanup 対象 branch を `Stacked Base` に持つ worktree が `git worktree list --porcelain` に存在する場合、その stacked branch について `git merge-base <stacked branch> origin/<default-branch>` と `git rev-parse origin/<default-branch>` が**一致**する（= main tip を完全に含む = **rebase 完了**）まで cleanup しない。祖先関係（`git merge-base --is-ancestor <cleanup 対象 = 先行 branch> <stacked branch>`）は使わない。merge commit 戦略の repo では先行 tip が merge 後 `origin/<default-branch>` の祖先になるため、stacked が main へ rebase した後もこの判定が真のままになり、解除条件が永久に発火しない
- dirty diff なし
- 対象 worktree 内の全 `.steering/*/state.md` の `Resume From` が terminal（`done` / `cancelled`）（1 件でも進行中なら safe cleanup ready ではない）
- resume に必要な artifact / Continuation Registry / ADR / PR URL / 次 stage seed が worktree 外へ保存済み
- root duplicate steering なし
- branch / worktree / steering の identity tuple が一致
- 後続 Stage がある場合は、旧 worktree ではなく latest default branch から新 worktree を作る方針が出ている
- Stage Continuation（`references/post-completion-pr-flow.md` Option 1 手順 6 § Stage Continuation） では、先行 Stage の PR が未 merge のまま並列 Stage の worktree を同時に保持してよい。cleanup 契約は worktree 単位で「その worktree 内の全 steering が terminal」を判定するため干渉しない（判定根拠は Stage Continuation 節を参照）

`safe cleanup ready` の場合は、追加の cleanup 指示を待たずに `git fetch origin` → `git worktree remove` → `git branch -d` → default branch へ戻す、まで進めてよい。1 つでも不明なら実行せず、cleanup 候補・ブロッカー・人間の次アクションを短く出す。

### Output Guidance

Post-merge cleanup の出力では、削除や実行コマンドより先に次を表示する:

- cleanup 対象 worktree / branch
- dirty diff の有無
- ownership: GDD managed / host-managed / normal repo
- 実行候補: `git fetch origin` → `git worktree remove` → `git branch -d` → default branch へ戻す

### Persistence Gate

cleanup 前に、Continuation Registry、`.steering/<task>/requirements.md` / `design.md` / `state.md`、PR URL、次 stage の seed 情報が worktree 外へ保存済みであることを確認する。削除対象 worktree 内だけに残っている場合は cleanup しない。

1. `git fetch origin` で default branch を更新する。
2. cleanup 対象の worktree と branch を 1 つに絞る。候補が複数で曖昧なときはユーザーに確認する。
   2a. root 側 `.steering/<slug>/` に同一 task の copy / duplicate が残っていないか確認する。残っている場合は cleanup 完了扱いにせず、root bleed として解決方針（移行済み確認 / 削除 / keep）をユーザーに確認する。
   2b. 対象 worktree 内の全 `.steering/*/state.md` を読み、`Resume From` が terminal（`done` / `cancelled`）でない steering が 1 件でもあれば cleanup 対象から除外する。あわせて `safe cleanup ready` の **stacked 依存の確認**（正本）を満たすことを確認する。`--force` は使わず、停止してユーザーに報告する（進行中タスクの未コミット artifact 喪失事故の再発防止）。
3. worktree を `git worktree remove` で外し、branch を `git branch -d` で削除する。
4. default branch へ戻す。

### Cleanup Ownership Boundary

Post-Completion PR Flow の Options 1 / 4 から cleanup を依頼された場合でも、削除してよいのは GDD が所有する worktree だけ。`git rev-parse --git-dir` と `git rev-parse --git-common-dir` を比較し、以下の境界を守る。

- normal repo（`GIT_DIR == GIT_COMMON`）: worktree cleanup は不要。branch cleanup だけを扱う
- GDD managed worktree: path が configured Worktree Base（既定 `~/.gdd/worktrees`）配下、task slug / branch / `.steering/<slug>/` が一致し、かつ worktree 内 `.steering/*/state.md` の `Resume From` が全て terminal（`done` / `cancelled`）の場合だけ cleanup 可。加えて `safe cleanup ready` の **stacked 依存の確認**（正本）を満たすこと
- host-managed worktree: harness / IDE / Codex app / external tool が作った workspace と判断される場合は削除しない。cleanup ではなく保持方針と手動手順を提示する
- detached HEAD: branch delete / merge の対象が一意でないため fail-closed。PR 作成または keep を優先し、discard は typed confirmation の上で所有境界を再確認する

Option 2 / 3（PR 作成 / keep）では worktree を保持する。PR review や後続修正に必要なため、cleanup は Options 1 / 4 のみ。

## Cancelled Cleanup

`gdd-completion-check` で `Next Action=cancelled` になった場合の cleanup 手順。`gdd-completion-check` が `cancelled` を記録した後、ユーザーに cleanup を提案する（自動実行はしない）。

### 確認ステップ

1. **未 push のコミットの確認**: `git log --oneline <default-branch>..HEAD` で worktree 上に残っているコミットを表示する。
2. **未コミットの変更の確認**: `git status` で作業中の変更を確認する。

### Cleanup 選択肢

ユーザーに以下の選択肢を提示し、選択を求める:

| 選択肢      | 説明                                                  | 操作                                                            |
| ----------- | ----------------------------------------------------- | --------------------------------------------------------------- |
| **keep**    | worktree と branch を残す（後で再利用 or 参考にする） | `.steering/` の `Next Action=cancelled` のみ残して何もしない    |
| **archive** | branch を残すが worktree は外す                       | `git worktree remove <path>` のみ。branch は残る                |
| **discard** | worktree と branch を完全削除                         | `git worktree remove --force <path>` → `git branch -D <branch>` |

### Guardrails

- **自動 discard 禁止**: ユーザーの明示選択なしに worktree / branch を削除しない
- **remote branch は削除しない**: push 済みの remote branch の削除はユーザーに `git push origin --delete <branch>` の手動実行を案内する
- `.steering/` ディレクトリは worktree 内にあるため、worktree の discard で一緒に削除される。root 側にコピーが残っている場合はユーザーに確認してから削除する
- PR が既に作成済みの場合は close を案内するが、自動 close はしない

## Guardrails

- **GDD plugin 自身を変更するとき**は層で使い分ける: skills / references は local を直接編集してよいが、hooks は毎回パス実行され即座に影響するため worktree で開発し suite が green になるまで local に入れない。壊れたら `touch ~/.claude/gdd-hooks-disabled` で全 hook を no-op にできる。詳細は `references/gdd-self-development.md`
- git / worktree が使えない場合は停止し、通常ディレクトリへ自動フォールバックしない
- 停止するときは、git repository / default branch / candidate 解決のどこで詰まったかを示し、復旧手順を返す
- same-name task のためでも、別 task と worktree / branch を共用しない
- 別テーマの変更が混在した worktree を差分汚染チェックなしに再利用しない
- tracked な root 側 `.steering` を canonical state として更新しない
- active worktree を 1 つに決められない場合は fail-closed で停止する
- ambiguous worktree / branch は削除しない
- PR merge 後の追加実装では、Pre-Follow-up Hygiene Gate を通さずに元 worktree / 元 branch を再利用しない
- merge 済み follow-up の新 worktree は latest default branch から作る。release branch / task branch / merged branch を base にしない（**例外**: `auto-stacked` の stacked 継続時のみ、未マージ先行 Stage の task branch を base にしてよい）
- 未コミット・未 push の重要作業を壊す操作はしない
- **`--force` 付き `worktree remove` の事故防止**: 対象 worktree 内 `.steering/*/state.md` の `Resume From` が全て terminal（`done` / `cancelled`）であること、および `safe cleanup ready` の **stacked 依存の確認**（正本）を満たすことを確認してからのみ `--force` を使う。1 件でも進行中なら削除せず cleanup 対象から除外する（2026-07-26: design-gating 実行中 worktree の `--force` 誤削除で未コミット `.steering/` artifact を喪失した事故の再発防止）
- dirty working tree での worktree 作成: 対話モードではユーザーに stash / commit / continue を確認する。非対話モード（subagent / Cursor Composer エージェント）では auto-continue し、state.md Notes に未コミット変更ファイル一覧を記録する。いずれの場合も root に `.steering/` を作って代替しない
- **worktree 作成後、絶対パス（`$WORKTREE_ABS_PATH`）を呼び出し元に明示的に返す**。この値を返さないと呼び出し元（brainstorming 等）が root に `.steering/` を作る原因になる
- **`$WORKTREE_ABS_PATH` がプロジェクト root と一致する場合は fail-closed**：root での artifact 作成は防止しなければならない
- **同一 slug の root 側 `.steering/<slug>/` を silent ignore しない**: legacy migration source でない root 側 copy は root bleed / 置き去り artifact の疑いとして扱い、解決前に進めない
- **active worktree 側 `.steering/<slug>/` を optional 扱いしない**: 現在 task の steering は PR / cleanup 前に必ず所在と扱いを確定する。`git status` の `??` でも「管理外だから後回し」と判断しない
- PR merge / Issue close を自動では行わない
- `Next Action` を勝手に変更しない
