# FAQ

> **所有**: よくある詰まりどころと解決手順（契約レベルの Q&A）
> **上位正本**: なし（ユーザー向けガイドの独立文書）
> **参照元**: `commands/gdd-dev.md`、`onboarding.md`
> **症状別の他チーム向け復帰手順**: `docs/TROUBLESHOOTING.md`（停止パターン → 復帰コマンド早見表）

`gate-driven-development` で詰まりやすい点をまとめる。

## まずどの文書を見る？

- 概要と使い分け:
  - `README.md`
- 初回の最短シナリオ:
  - `references/onboarding.md`
- routing / resume の正本:
  - `references/state-machine.md`
- contract の境界:
  - `references/self-contained-contract.md`

## 旧 `Go1` / `Go2` や旧 workflow はどこに行った？

> **非推奨**: `Go1` / `Go2` は旧 workflow の用語であり、`gate-driven-development` では使用しない。以下は移行の参考情報としてのみ残している。

- 旧 `design-review-workflow` / `build-review-test-workflow` の happy path は `gate-driven-development` に統合した
- 旧 `Go1` 相当の人間ゲートは `human check`（`Human Check Status`）に統合された
- 旧 `Go2` 相当の第2人間承認は既定フローでは使わない。`gate-driven-development` では `human check` は 1 回のみ
- planning の正本は active worktree 側 `.steering/.../requirements.md` と `design.md`
- `.cursor/plans/*.plan.md` は比較案や壁打ちログを残したいときだけ使う任意の補助成果物

## `/gdd-dev` で `新規開始` か `再開` かを聞かれた

- entry intent が `ambiguous`
- fail-closed だが dead-end ではない
- 次の1アクション:
  - 新しく始めるなら `/gdd-dev 新規開始: <task>`
  - 続きなら `/gdd-dev 続きから <context>`

## resume candidate が複数あって止まった

- `resume` path で active steering を一意に決められていない
- 同一 worktree 内なら `Started At` が一意に最新の candidate を優先するが、それでも絞れない場合は停止する
- state は勝手に進めない
- 次の1アクション:
  - 再開したい steering を 1 つに絞って明示する
  - 候補のどれも不要なら、新規開始を明示する

## レビューで実装方針変更になった stopped workflow を続けたい

- 明示的な resume cue（`続きから`、`再開`）を付けて `/gdd-dev` を実行する
- resume で active steering が解決すれば、既存 active worktree を再利用する
- build candidate を reopen する場合は、`gdd-systematic-debugging` が `implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required` を切り分ける
- planning candidate を reopen する場合は、active worktree 側 `state.md` の `Resume From` を正本として続ける
- 次の1アクション:
  - `/gdd-dev 続きから` または `/gdd-dev 再開`
  - 本当に別件なら `/gdd-dev 新規開始: <task>` と明示する

## `/gdd-dev` が current phase の説明だけで止まった

- non-terminal な `Resume From` / `Next Action` は本来 stop 理由ではない
- active な `/gdd-dev` run では `.claude/gdd-dev.local.md` と Stop hook が同じ session の継続を担当する
- symlink 方式だけで使っている場合、`hooks/hooks.json` が有効化されず自走継続しない
- 次の1アクション:
  - plugin を manifest 経由で有効化し、hook が有効な新規 session / reload 後に再実行する
  - `.claude/gdd-dev.local.md` が作られているか確認する
- それでも止まる場合は、最後の返答に `<gdd-stop reason="...">` が誤って入っていないか確認する（`</gdd-stop>` は任意）

## human check に何を並べればいい？

- summary だけでなく `承認ポイント` を必ず付ける
- 各 `承認ポイント` には **背景**（なぜこの判断が必要か）と **変更前 → 変更後**（何がどう変わるか）を含める
- planning artifact には `Human Check Questions`（該当時は `Route / Ownership Matrix` / `Sensitive Data / Masking Policy`）を独立見出しで置く
- route / ownership / secret handling / masking / rollout / rollback が scope にある場合は、その承認事項を yes/no で判断できる形にする
- `承認ポイント` や `Human Check Questions` は、レビュー担当がそのまま読んで判断できる自然文（`references/human-check-template.md` § 判断の書き方）にし、内部名や略語だけで済ませない
- 末尾に **方向性承認** を置き、E2E 発見時に AI が自律判断してよい範囲を合意する
- これらに関する blocking `Open Questions` が残っている間は `human-check-waiting` に進めない
- 非該当の見出しは消さず、`N/A` と根拠 1 行を残す

## 承認後に実装中の変更で human check が何度も戻ってくる

- `Approved Direction`（方向性承認）の自走範囲内であれば、E2E で発見された問題は human check に戻さず AI が自律判断する
- 方向性が同じなら `design_detail_only` で閉じ、方向性自体が変わるときだけ `human_recheck_required` で人間に戻す
- Scope Drift Guard: 同一 steering 内で `design_detail_only` が 3 回を超えた場合は方向性との整合を再確認する
- 詳細は `references/phase-progression.md` の「E2E Discovery Loop」を参照

## 途中でワークフローを中止したい

- **human-check-waiting 中**: 「中止」「cancel」「やめる」「キャンセル」と答えると `Next Action=cancelled` に遷移して停止する
- **build phase（TDD / implementation）中**: セッションを終了して steering を放置できる。放置された steering は次回 `/gdd-dev resume` 時に候補として残る。明示的に終了するには:
  - `state.md` の `Resume From` と `Next Action` をどちらも `cancelled` にする（手順: `references/self-review-lanes.md` § 使わないステアリングの終え方）
- 中止後の worktree cleanup は `gdd-using-git-worktrees` の「Cancelled Cleanup」に従い、keep / archive / discard をユーザーに確認する

## 自走継続はいつ止まる？

- `done`
- `cancelled`
- `human-check-waiting`
- `blocked`

のいずれかで止まる。

- `blocked` は fail-closed、外部前提不足、ambiguous routing など、人間入力や環境修復が必須な停止（background の dispatch への `TaskStop` が待ちから外れない結果で返ったときは `clarification-needed`。`references/state-machine.md`）
- stop 時は `<gdd-stop reason="...">` を使い、`参照した正本` / `停止理由` / `次の1アクション` も返し、`<gdd-stop>` の後に `## 👤 次にすること` を付ける（`</gdd-stop>` は任意）

## same-name ambient asset 衝突で止まった

- `gate-driven-development` 側 asset と別実体の同名 asset があり、plugin 側 asset を deterministic に解決できない unsupported configuration
- `scripts/install-cursor-links.sh` が作り、`~/.cursor/plugins/gate-driven-development/cursor-links.tsv` で current plugin asset への alias と確認できる Cursor symlink は同一 asset とみなし、この衝突に含めない
- 衝突解消前は `/gdd-dev` を続行しない
- 次の1アクション:
  - 同名 command / skill / agent の退避、無効化、改名のいずれかを行う
  - 解消後に `/gdd-dev` を再実行する

## symlink を外したら `/gdd-dev` が見えなくなった

- symlink 方式だけで使っていた場合、Cursor から command / skill / agent が見えなくなる
- 次の1アクション:
  - `bash scripts/install-cursor-links.sh` で Cursor link を戻す
  - Cursor を reload してから `/gdd-dev` を再実行する
  - Stop hook も使いたい場合は plugin を manifest 経由で有効化する

## Cursor で hooks が動かない / Autonomous Continuation しない

- symlink 方式だけでは hooks は有効にならない
- hooks を使うには manifest 経由で plugin を有効化し、Cursor を reload する
- hooks なしでも workflow 自体は動作するが、以下の手動対応が必要:
  - phase 間で「次に進めて」と明示的に指示する
  - セッション復帰時は `/gdd-dev 再開` で手動 resume する
  - 長い build で AC を見失ったら `gdd-status` で確認する
- 詳細は `references/cursor-guide.md` を参照

## Cursor で reviewer subagent が起動しない

- Cursor の subagent 機能が Claude Code の Agent tool と異なる場合に発生する
- agent 定義を直接起動せず、定義の本文を prompt に貼って別コンテキストで起動する（`references/cursor.md` § 初稿とレビュー）。それでも起動できなければ inline review（`references/inline-review-checklists.md`）にフォールバックして review を完了できる
- quick タスクはもともと inline checklist only なので影響なし

## 途中の意思決定を残したい

- 重要な意思決定、却下した代替案、その理由、影響は任意で active worktree 側 `.steering/.../adr.md` に残してよい
- `adr.md` は optional な decision log であり、routing source や gate 条件にはしない
- `adr.md` が無いことだけを理由に fail-closed しない

## git repository / git worktree が使えず止まった

- formal workflow の worktree 判断軸は `references/workspace-policy.md` を参照
- 通常ディレクトリへの自動フォールバックはしない
- 次の1アクション:
  - git repository か確認する
  - `git worktree list` が使える状態にする
  - default branch を確認してから再実行する

## `gdd-completion-check` で external security evidence が足りない

- `done` に進めないが、code/debug failure とも限らない
- 外部前提不足だけなら `Next Action=gdd-completion-check` のまま再試行する
- 次の1アクション:
  - external verifier hook が有効か確認する
  - required `security_evidence:<kind>` 行が `Verification` に作られているか確認する
  - verifier が evidence を書ける状態か確認する
  - そろったら `gdd-completion-check` を再実行する
- 例:
  - Snyk のスキャン結果を書く verifier pluginを使う場合、編集で pending が立った scope に対して `| method=security_evidence:code | pass | ... | |` のような canonical 表行が active `tasklist.md` の `Verification` に入る。**`method=security_evidence:*` 行は external verifier hook が書く責務であり、agent の手書きは契約違反**。現行の外部 writer は canonical 形ではなく、2 列目に `security_evidence:<kind>` を持つ非 canonical な 5 列 list 行を書くため、その行は schema 違反として block される
  - `.steering/*/tasklist.md` が複数あって active を一意に決められない場合、verifier は fail-open で `Verification` を更新せず state だけ進めることがある

## `.steering` への書き込みを hook が拒否した

- 個人メールアドレス
- ローカル絶対パス

は拒否対象。

- 次の1アクション:
  - repo 相対パス
  - `${CLAUDE_PLUGIN_ROOT}`
  - `（ローカルパス）`・`（メールアドレス）` のような語

のいずれかへ置き換える。同じ行に placeholder（`${CLAUDE_PLUGIN_ROOT}`・`<redacted>` など）があっても、ローカルの絶対パスの形が残れば止まる。`/Users/<redacted>/...` のように一部だけを伏せた形も止まる。

## いま何を正本として見ればよい？

- planning 中:
  - active worktree 側 `state.md` の `Resume From`
- build 中:
  - active worktree 側 `tasklist.md` の `Next Action`
- 迷ったら:
  - 停止時の `参照した正本`
  - `停止理由`
  - `次の1アクション`

を先に見る。

## Express で始めたが途中で重くなった

- **自動昇格（build phase）**: Express 中に `references/task-sizing.md` § Express 昇格条件 のどれかを満たすと quick (standard) に自動昇格する
- **手動昇格（human check）**: human check 時に「Express では足りない」「設計が必要」と判断したら、その旨を伝える。Express 昇格の state ロールバックが適用される
- 昇格時は不足 phase（requirements-gating → design-gating → task-breakdown）が挿入される。着手の後に `request.md` に入力が足されていれば、その前に `brainstorming-steps.md` § 9 の依頼と既存コードの突き合わせを回し直す
- 次の1アクション:
  - human check 中なら「standard にしたい」と伝える
  - build phase で自動昇格した場合は、不足 artifact を埋めて通常フローで続行する

## Express パスか通常パスか迷う

- 1-2 ファイル・方針が明白・AC 1-3 個 → Express
- 3-5 ファイル・選択肢がある → quick (standard)
- 迷ったら quick (standard) を選ぶ。Express から昇格するより、最初から適切なパスで進める方が手戻りが少ない
- `--express` で明示指定もできる: `/gdd-dev --express <task>`

## `gdd-pre-workflow-brainstorming` と `/gdd-dev` の違いは？

- `gdd-pre-workflow-brainstorming`
  - 相談専用
  - `.steering/...` を作らない
- `/gdd-dev`
  - formal workflow の entrypoint
  - active worktree 側 `.steering/...` を正本として進める

## superpowers と GDD を両方 install している。どう使い分ける？

短答:

- **standalone な探索 / artifact 不要** → superpowers が軽くて速い（`superpowers:brainstorming` / `superpowers:test-driven-development` / `superpowers:systematic-debugging`）
- **要件 → 実装 → review → PR の一貫した workflow** → GDD（state machine が連鎖を保証）
- **同じ debug / brainstorm セッションで両方を並行起動しない**（時間が溶ける）

詳細な overlap map と「GDD primitive と superpowers 同等品の違い」は `references/superpowers-overlap.md` を見る。比較ベンチマーク用のシナリオは `docs/references-archive/benchmark-scenarios.md` にある。

差別化のポイント（GDD primitive が state machine 一体型である理由）:

- `gdd-test-driven-development`: RED Evidence に AC ID Binding 必須（`requirements.md` の AC と一体化。`Covers AC:` の無い remediation task の例外は同 skill § AC ID Binding）
- `gdd-brainstorming`: Entry Intent / Approved Direction を `state.md` に永続化
- `root-cause-investigation`: Phase 4 で State Machine Integration block を出力（GDD workflow 内呼び出し時のみ）
- `gdd-subagent-driven-implementation`: Spec Change Detection で `adr.md` / `requirements.md` / `design.md` を sync
