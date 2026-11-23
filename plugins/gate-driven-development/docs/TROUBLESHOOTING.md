# TROUBLESHOOTING

## 緊急停止（kill switch）

GDD hook が想定外に block・介入し続けて作業が止まる場合、以下のコマンドで全 GDD hook を即時 no-op にできる。

```sh
mkdir -p ~/.claude && touch ~/.claude/gdd-hooks-disabled
```

復帰する場合:

```sh
rm -f ~/.claude/gdd-hooks-disabled
```

- GDD の手動利用（skill 呼び出し）は kill switch 有効時も継続できる。
- kill switch は `run-worktree-command-guard.sh` などの safety guard（破壊的 git 操作・root checkout 保護）も無効化する。有効化しっぱなしにするとこれらの保護が効かなくなるため、原因調査後は速やかに `rm` で復帰すること。

> **対象**: GDD の停止・エラー・挙動不審に遭遇した利用者
> **使い方**: ターミナルの停止メッセージで検索するか、症状カテゴリから目次を辿る
> **上位正本**: 各症状の詳細契約は `references/faq.md` / `references/state-machine.md` / `references/self-contained-contract.md`
> **この文書の位置付け**: 「停止パターン → 原因 → 復帰手順」を 1 枚にまとめた他チーム向け FAQ

---

## 目次

1. [起動・初期化で詰まる](#起動初期化で詰まる)
2. [human check 周辺](#human-check-周辺)
3. [自動実行が止まる / 進まない](#自動実行が止まる--進まない)
4. [reviewer 指摘のループ](#reviewer-指摘のループ)
5. [state 不整合・復旧](#state-不整合復旧)
6. [worktree / git 関連](#worktree--git-関連)
7. [hook が動かない](#hook-が動かない)
8. [superpowers / 他 plugin との競合](#superpowers--他-plugin-との競合)
9. [復帰コマンド早見表](#復帰コマンド早見表)

---

## 起動・初期化で詰まる

### `/gdd-dev` だけで実行すると「新規か再開か判断できない」と言われる

- **原因**: `entry_intent=ambiguous`（fail-closed）
- **復帰**:
  - 新規: `/gdd-dev <やりたいこと>`
  - 再開: `/gdd-dev 再開`

### `gdd loop is already active in another session.` で止まる

- **原因**: 同じ checkout の別のセッションの `/gdd-dev` が、まだ終わっていない（human check 待ちなどで止まっている）。`.claude/gdd-dev.local.md` が `active: true` で、別の `session_id` を持っている
- **復帰**:
  - エラーの `Existing session last active:` の行で、前のセッションが最後に動いた時刻と経過時間を見る。時刻は Claude Code の transcript（`$CLAUDE_CONFIG_DIR`、無ければ `~/.claude` の `projects/*/<session_id>.jsonl`。session_id が英数字・`-`・`_` の形のときだけ）の末尾 1 MiB にある記録の top-level の `timestamp` のうち最も新しいもの（UTC。括弧の中にローカル時刻も出る）。経過時間は 1 時間未満なら分で出し、時計のずれで未来の時刻なら `in the future` と出す。返事待ちの間などは記録が増えないので、動いているセッションでも古い時刻が出る。transcript が無い・読めない・時刻が無いときは `unknown` で、state に `started_at` があれば、少なくともその時刻には動いていたものとして添える
  - script が走らず、`commands/gdd-dev.md` の手動の手順（手順 2・4）で止まるときは、時刻を手で取る。state の `session_id` が英数字・`-`・`_` の形のときだけ、上の場所の `<session_id>.jsonl` を探し、末尾の行から top-level の `timestamp` の最も新しい値だけを取り出して、UTC のままユーザーに見せる（`tail -c 1048576 <file> | grep -o '"timestamp":"[^"]*"' | sort | tail -1` など。入れ子の `timestamp` も拾うので、目安として扱う）。記録のほかの中身は読まない。見つからなければ `unknown` と書き、`started_at` があれば添える
  - 前のタスクを続けるなら、そのセッションに戻る
  - 新しいタスクは、どのタスクも使っていない checkout（新しく作った worktree など）で始める
  - 前のセッションを閉じてしまい、もう動いていないことを確かめたら、エラーに出る State file の `active:` を `false` にする（`active: false` の state はロックの対象外）。その後 `/gdd-dev` をやり直す。`session_id` は書き換えない

### 「git リポジトリ外」エラー

- **原因**: GDD は worktree を前提とする
- **復帰**: git リポジトリ内で実行するか、`git init` してから再試行

### `同名 skill/agent` の衝突で停止

- **原因**: 別の plugin に同名 skill/agent がある
- **復帰**: 競合する plugin を一時退避または無効化。`~/.claude/plugins/` を確認し、重複する plugin を特定して無効化

### 自己検証（`validate-plugin.sh`）が落ちる

- **原因候補**:
  - Required file 欠損（plugin 取得が不完全）
  - Frontmatter 破損
  - `evals/evals.json` の schema 不一致
- **復帰**: エラー出力の BLOCK 名を見て `tests/validate-plugin.sh` の該当ブロックで読むファイルを特定。再取得で直らない場合は配布元に問い合わせ

---

## human check 周辺

### 「何を承認すればいいか分からない」

- **原因**: ターミナル出力の承認ポイントを読み飛ばしている可能性
- **復帰**:
  - ターミナルの **承認ポイント** セクションだけを読む（**背景** / **変更前 → 変更後** / 採用案 / 代替案）
  - artifact 全文を読まなくても判断できる設計
  - 複数ポイントある場合は番号ごとに OK / 別案希望 を返す
  - 末尾の **方向性承認** で AI の自走範囲を合意する

### 曖昧な返答（「たぶんいいと思う」「様子見で」等）をすると追加質問される

- **原因**: GDD は曖昧返答を検出して fail-closed する
- **復帰**:
  - 明確に `OK` / `別案希望: <詳細>` / `修正してほしい: <詳細>` と答える
  - 詳細: `references/human-check-template.md` § 返答分類の判定基準

### 承認後に何度も human check に戻ってくる

- **原因候補**:
  - `Approved Direction` の自走範囲が狭すぎる
  - E2E で発見された変更が AC の根本追加/削除に該当
  - `Scope Drift Guard`（`design_detail_only` が 3 回超）が発動
- **復帰**:
  - 承認時に自走範囲を広めに合意する
  - AC の根本変更が必要な場合は `gdd-requirements-amendment` で正式に要件を追加する

### human check を取らずに実装に進んだ

- **原因**: phase-skip 迂回（H-4 で塞がれたが旧バージョンだと残存）
- **復帰**: plugin を最新版に更新。各 phase skill に `Phase Gate Pre-check（必須）` ブロックが入っていることを確認

---

## 自動実行が止まる / 進まない

### 進捗表示が出ない

- **原因**: hook が有効化されていない可能性（Cursor 環境で多い）
- **復帰**:
  - plugin manifest 経由でインストールされているか確認
  - Cursor は manifest 経由で hook を有効化（`references/cursor-guide.md`）
  - symlink 方式の場合は `hooks/hooks.json` が読まれないため自走しない

### phase 遷移ごとに止まる（Autonomous Continuation しない）

- **原因**:
  - `.claude/gdd-dev.local.md` が生成されていない
  - 前回返答に `<gdd-stop>` が混入
- **復帰**:
  - `bash scripts/setup-gdd-loop.sh` を手動実行して `.claude/gdd-dev.local.md` を再生成
  - 返答ログの末尾に `<gdd-stop reason="...">` が誤って残っていないか確認

### 停止理由が出ない、または不明瞭

- **原因**: 出力テンプレート違反
- **復帰**:
  - 停止時は `参照した正本` / `停止理由` / `次の1アクション` と、`<gdd-stop>` の後の `## 👤 次にすること`（`cancelled` を除く）が必須
  - 欠けている場合は `gdd-status` で現在地を再確認

### auto-mode 中に AWS/Terraform 操作が勝手に走った

- **原因**: 利用者の CLAUDE.md に Operational Safety ルールが未設定
- **復帰**:
  - `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` の **Operational Safety** セクションを CLAUDE.md に追加
  - 破壊的操作は 1 操作ごとに明示承認が必要（`-auto-approve` 禁止、包括承認の連鎖禁止）

---

## reviewer 指摘のループ

### 同じ指摘が 3 回以上繰り返される

- **原因**:
  - `implementation_fix_only` の 3 回制限到達
  - または `design_detail_only` に昇格したが根本解決していない
- **復帰**:
  - `design_detail_only` に昇格して根本原因を探る
  - それでも 5 回連続 `changes_requested` になると **Reviewer Loop Escape Hatch** が自動発動し route recalibration に入る
  - procedural / evidence only（`Reviewed by:` 欠落、verification wording 不整合、reviewer evidence 整形ミスなど）なら failing gate の再実行条件を整え、必要なら `blocked` で具体的な修正手順を返す
  - policy / scope / ownership / security boundary / prompt-output contract の変更が必要な場合だけ human check に戻る
  - 詳細: `references/rollback-patterns.md` § Reviewer Loop Escape Hatch

### AI reviewer の false positive が多い

- **原因**: プロジェクト固有の規約・学習済みパターン不足
- **復帰**:
  - Reviewer Calibration により差し戻し→修正→再通過の記録が `tasklist.md.Fix Attempts` に残る
  - false positive が多いパターンは `learned-patterns.md` に蓄積され、次回以降の severity が調整される
  - 詳細: `references/inline-review-checklists.md` § Reviewer Calibration

### reviewer が動かない

- **原因**: reviewer selection 未記録（`Implementation Reviewer Selection` が欠落）
- **復帰**:
  - `gdd-task-breakdown` に戻って reviewer selection を記録する
  - 詳細: `gdd-implementation-gating/SKILL.md` § Phase Gate Pre-check Step 4

---

## state 不整合・復旧

### resume で何を選べばいいか分からない

- **原因**: GDD の内部では Task Binding Registry / `state.md` / worktree の 3 層で task identity を守っているが、利用者がこの 3 層を理解して手動復旧する必要はない
- **復帰**:
  - まず `gdd-status` を実行し、候補と **次の1アクション** だけを見る
  - 同じ task を続ける場合は `/gdd-dev resume <候補>` を使う
  - PR merge 後の段階実装や新チャット復旧の場合は `/gdd-resume <continuation-id>` を使う
  - 候補が複数ある、または branch / worktree / state が一致しない場合は、GDD が自動再開せず fail-closed する。候補を 1 つ選ぶまで実装を始めない

### binding / state / worktree の不整合で止まる

- **原因**:
  - 古い worktree が残っている
  - merge 済み branch の worktree を追加実装に再利用しようとしている
  - `.gdd/tasks/<task_id>/binding.json` と current worktree / branch / steering path が一致しない
- **復帰**:
  - `gdd-status` で `Task Identity` と `Integrity Issues` を確認する
  - current task として断定されていない候補は、会話履歴だけで再開しない
  - `/gdd-dev resume <task_id>` で対象を明示する
  - PR merge 後の次 stage は、古い worktree ではなく latest default branch から新しい worktree を作る
  - Continuation ID がある場合は `/gdd-resume <continuation-id>` を使い、registry → read-only facts → new worktree → HITL の順で復元する

### `Resume From` と `Next Action` が矛盾する

- **原因**: hook 実行タイミングのずれ、または手動編集
- **復帰**:
  - planning 中: `state.md` の `Resume From` が正本
  - build 中: `tasklist.md` の `Next Action` が正本
  - `references/state-machine.md` の「routing source」定義に従い、正本側を信頼して副側を合わせる

### `Route In Progress` が残ったまま terminal 状態になった

- **原因**: `Route In Progress のクリア` が抜けた（2026-04 までに修正済みだが古い state で発生）
- **復帰**:
  - `state.md` の `Route In Progress` を `none` に手動で書き戻す
  - 次回 `gdd-completion-check` 通過時に自動で `none` に戻る

### active steering の required field 欠落で `[gdd:blocked]` になった

- **原因**:
  - `state.md` の Tier 1 (Core) field（`Started At` / `Resume From` / `Human Check Status` / `Route In Progress`）のどれかが欠けている
  - または canonical な `tasklist.md`（3 gate approved 後）に `Next Action` が無い
- **正本**: Tier 分類と phase 別 Minimum Required Set は `references/state-field-tiers.md`。Hook 検査ロジックは `hooks/scripts/validate-steering-write.py:STATE_REQUIRED_FIELDS` / `hooks/scripts/lib/detect-steering.sh:gdd_validate_active_state_fields`
- **復帰**:
  - `state.md` を正本として、欠けた Tier 1 field を書き戻す
  - `Requirements Review Status=approved` / `Design Review Status=approved` / `Human Check Status=approved` が揃っているなら、`tasklist.md` に `Next Action=<current-phase>` も復元する
  - 復旧後に `/gdd-dev` または `gdd-status` で再開し、`[gdd:blocked]` が消えていることを確認する
  - **Tier 2 / Tier 3 field（`Approved Direction` / `Requirements Review Status` 等）の不在では `[gdd:blocked]` にならない**。それらが必要な phase に入る前は欠落で問題ない

### active steering が複数検出されて通知が出る

- **原因**: current worktree の `.steering/<slug>/state.md` に、作業中の steering が 2 件以上ある。pre-push gate（`steering-multiple`）は、作業中の steering が 2 件以上、または作業中が無く done・blocked の steering が 2 件以上あり、かつ push 対象の tip の `Pre-Push Self Review` を記録した steering が 1 件に決まらないとき、pre-PR gate は done の steering が 2 件以上のときに、止めずに通す。通知はコマンドの実行後に届く（コマンドが成功していれば、push・PR はもう済んでいる）
- **復帰**:
  - `/gdd-dev 再開 <steering名>` で絞り込む
  - どれを終えるかユーザーに確認したうえで、使わない steering（PR が open のものは除く）は、削除も移動もせず、`state.md` の `Resume From` と `Next Action` をどちらも `cancelled` にする。手順と理由の正本は `references/self-review-lanes.md` § 使わないステアリングの終え方
  - **古い brainstorming-only steering が混ざっている場合**: `${CLAUDE_PLUGIN_ROOT}/scripts/find-stale-steerings.sh --all-worktrees` で stale 候補（10 日超 + Resume From=gdd-brainstorming）を一覧化し、各候補について終えるか resume するかをユーザーに確認する。終えるものは上と同じく両 field を `cancelled` にする（`.steering/` の外へ移すと `.steering/` の ignore から外れて git に見え、削除は取り戻せない）。auto delete は禁止（別 runtime で作業中の可能性があるため）

### ステアリングが読めないとして push・merge の後に通知が出る

- **原因**: `.steering/` の下に、steering の列挙から落ちるものがある。`.steering` 自体・その下の task dir・task dir の中の `state.md` が symlink、一覧できない（権限が無い）ディレクトリ、在るのに読めない `state.md`。pre-push gate は `steering-unreadable`、merge gate は `state-unreadable` を、止めずに通す。通知はコマンドの実行後に届く（コマンドが成功していれば、push・merge はもう済んでいる）
- **復帰**:
  - 権限を戻す（`chmod u+rx .steering/<slug>`、`chmod u+r .steering/<slug>/state.md`）
  - symlink は実体のディレクトリ・ファイルに置き換える（GDD は symlink を作らない。別の worktree の steering を指すと、そちらのタスクで判定してしまう）
  - task dir でないファイル（README など）と、`state.md` の無い task dir は通知の原因にならない

### `/clear` 後に state が復元されない

- **原因**: SessionStart hook が有効化されていない
- **復帰**:
  - plugin manifest 経由でインストールされているか確認
  - `.steering/.../state.md` の `Last Handoff Summary` が存在すれば手動で文脈復元可能

---

## worktree / git 関連

### worktree 作成に失敗

- **原因**:
  - bare clone
  - disk quota 不足
  - 既存 worktree と名前衝突
- **復帰**:
  - `git worktree list` で現状確認
  - 不要な worktree を削除: `git worktree remove <path>`

### merge 後に worktree が残っている

- **原因**: `gdd-completion-check` の `Post-Completion 4 Options Flow` でローカル merge を選んだが cleanup していない
- **復帰**:
  - `gdd-using-git-worktrees` skill の「merge 後のローカル整理」で cleanup
  - または手動で `git worktree remove <path>` + `git branch -d <branch>`

---

## hook が動かない

### `hooks/hooks.json` が認識されない

- **復帰**:
  - plugin が manifest 経由で登録されているか確認（symlink だけだと hook が読まれない）
  - `~/.claude/settings.json` の plugin 有効化を確認

### Stop hook が `<gdd-stop>` 以外を block しない

- **復帰**:
  - hook 実装の問題の可能性。`hooks/scripts/run-gdd-stop-hook.sh` が実行可能か確認（`chmod +x`）
  - `bash tests/validate-plugin.sh` の `BLOCK: hooks` が OK か確認

### PreToolUse hook が遅い

- **原因**: `.steering/.../requirements.md` / `tasklist.md` を毎回読むため
- **復帰**:
  - artifact サイズが肥大化していないか確認（1 steering 内で数 MB 超えは異常）
  - 肥大化時は古い `worklog.md` をアーカイブする

---

## superpowers / 他 plugin との競合

### GDD と superpowers の両方が反応する

- **原因**: 両 plugin が skill 名前空間で競合
- **復帰**:
  - CLAUDE.md に「formal workflow は `/gdd-dev` で入る」旨を明記し、superpowers は単発タスクだけで使う運用にする
  - GDD の `gdd-using-skills` skill が優先規則を持つので、セッション開始時に Skill tool で呼ぶ

### `EnterPlanMode` がブロックされる

- **原因**: GDD session 中の Plan mode は `run-block-plan-mode-hook.sh` で拒否される仕様
- **復帰**:
  - GDD フロー中は `/gdd-dev` 経由で進める（Plan mode 不要）
  - Plan mode を使いたい場合は `/gdd-dev` を完了させてから別セッションで実行

---

## 復帰コマンド早見表

| 停止状態            | 復帰コマンド                                                        | 備考                       |
| ------------------- | ------------------------------------------------------------------- | -------------------------- |
| 初回起動            | `/gdd-dev <やりたいこと>`                                           | 新規タスク開始             |
| human check 待ち    | ターミナルの承認ポイントに `OK` / `別案希望` で回答                 | 各ポイント個別に           |
| 中断からの再開      | `/gdd-dev 再開`                                                     | 最新 state から続行        |
| 複数候補がある      | `/gdd-dev 再開 <steering名>`                                        | 特定タスクを再開           |
| reviewer 指摘対応後 | `/gdd-dev 再開`                                                     | 修正後の再レビュー         |
| evidence 不足       | evidence 追加後 `/gdd-dev 再開`                                     | completion 再試行          |
| worktree 問題       | `git worktree list` で確認後再実行                                  | git 環境の復旧             |
| 新規に切り替え      | `/gdd-dev 新規開始: <task>`                                         | 既存タスクを残して新規開始 |
| 中止                | human check 中: `中止` / build 中: `state.md` の `Resume From`・`Next Action` をどちらも `cancelled`（`references/self-review-lanes.md` § 使わないステアリングの終え方） | タスクの放棄               |

---

## それでも解決しない場合

1. `gdd-status` で現在の state 全体を出力
2. `.steering/<task>/state.md` と `tasklist.md` を開いて状態を直接確認
3. `CHANGELOG.md` で最近の breaking change を確認
4. plugin 配布元へ issue / 問い合わせ

---

## 参考リンク

- 契約正本 Q&A: `references/faq.md`
- state field 詳細: `references/state-machine.md`
- 差し戻し route: `references/rollback-patterns.md`
- hook 挙動: `hooks/hooks.json` + `hooks/scripts/`
- セキュリティ境界: `docs/SECURITY.md`
