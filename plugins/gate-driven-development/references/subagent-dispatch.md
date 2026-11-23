# Subagent Dispatch（正本）

> **所有**: subagent の起動テンプレート、model routing、post-return routing
> **上位正本**: `self-contained-contract.md`（fail-closed 条件）、`state-machine.md`（遷移表・Autonomous Continuation）
> **参照元**: `commands/gdd-dev.md`

`/gdd-dev` から dispatch される subagent のテンプレートと、復帰後の routing ルール。
`gdd-dev.md` の Instructions と Workflow Overview を読んだ上で、phase に応じた該当セクションを参照する。

## Codex Subagent Delegation Permission（Codex Subagent Permission Gate）

Codex では subagent ツールが「ユーザーが明示的に委譲を依頼した場合のみ」という host 制約を持つ。GDD はこの制約を fail-open で無視しない。

- 明示委譲ソース（初回依頼・project policy・`/gdd-dev` 引数）あり → `explicit_delegation_source=<source>` を `state.md` に記録し `approved_by_explicit_delegation` 扱い。HITL 再承認不要。
- 明示委譲ソースも human-check 承認も無い場合、Codex の planning / reviewer / dialectic review / implementation worker は **main session inline execution** として実行する。
- `denied` / `not_applicable` / 欠落の場合、Codex では許可が無いまま subagent dispatch を起動しない。parallel batch は sequential execution に落として進める。
- Claude Code / Cursor は各 host 標準機構に従う。GDD controller は subagent 報告を独立検証し `tasklist.md` 書き込みを集約する。permission は作業委譲のみ（危険操作承認とは別）。

## Subagent Report Contract（空 report 必須義務）

subagent は作業の有無に関わらず、必ず **1 件の報告行を返す義務** を持つ。これにより main session は「空 report（= 何も変更なし）」と「report 欠落（crash / network）」を区別できる。

作業あり: 通常報告。作業なし: `{task_id: <id>, result: no_change, reason: <text>}` を必ず返す。§ Worktree Binding Precheck 不一致時: `{task_id: <id>, result: worktree_mismatch, expected: <path>, actual: <実行結果>}` を必ず返す。`## 読む対象` の `対象の差分` の起点・tip の照合不一致時、または `git diff` の実行失敗時: `{task_id: <id>, result: diff_base_mismatch, expected: <起点または HEAD>, actual: <base または tip>}` を必ず返す。completion-check の reviewer が時間超過・エラーで 2 回とも返らないとき（§ Reviewer Input and Time Budget の「超過・無応答のとき」）: `{task_id: <id>, result: review_unavailable, reason: <text>}` を必ず返す。欠落（crash / network）: timeout / exit code で検知 → `phase-progression.md` § batch_mixed Rule 5（行欠落検知）で fail-closed 停止。

**Why**: 空 report と欠落を区別できないと false positive が起きる。空 report 義務化で deterministic 判定が可能。

## Worktree Binding Precheck（`## Worktree` を受け取る全 dispatch 経路共通）

`## Worktree` を受け取る template（design-gating / task-breakdown / TDD / implementation-gating / completion-check / GREEN 並列 worker・remediation worker・`gdd-code-simplifier` REFACTOR dispatch）は、着手前に `git -C "<## Worktree の値>" rev-parse --show-toplevel` を実行し、その出力を realpath 相当で正規化した値が `## Worktree` 自身（同じく正規化）と一致するか確認する（subagent 自身の ambient cwd とは比較しない。cwd は呼び出し元セッションのままなので、正常系でも `## Worktree` と一致しない。パスが存在しない・git worktree の root ではない・コマンドが失敗する、のいずれも不一致と同じ扱い）。一致すれば以降のすべての Bash を `cd "<## Worktree の値>"` 済みの状態で実行し、Read / Edit / Write は `## Worktree` を先頭に持つ絶対パスを使う。不一致なら、**いかなるファイルも書き込まず** fail-closed で停止し `{task_id: <id>, result: worktree_mismatch, expected: <## Worktree の値>, actual: <実行結果>}` を返す（`result` は § Subagent Report Contract の登録値。2026-09-08 に呼び出し元 worktree への RED 漏れが実際に発生した再発防止）。RED Evidence 等に記録する `Worktree:` 値は、この precheck 実行後に観測した `git rev-parse --show-toplevel` の出力（宣言値ではなく観測値）とする。

## Subagent Return Output Contract（コンテキスト節約）

全 subagent に適用する出力規律。subagent の return text はメインセッションのコンテキストに永続するため、フェーズ数に比例して累積する。

詳細は `.steering/<task>/handoff/<phase>.md` へ（正常完了時）。phase 名の例: `task_breakdown.md`（task-breakdown）、`tdd.md`（TDD）、`completion_check.md`（completion-check）。異常完了では handoff 不要。return は 5 行以内（報告行 1 行必須）。routing は state.md を disk から再読（return text 不使用）。gate の phase（requirements-gating・design-gating・implementation-gating・completion-check）を実行した側（gate runner。inline 実行なら main。main が gate runner を時間上限・エラーで止めて出口を決めたときも main。worker 経由なら結果を統合する main で、worker 自身は書かない〔§ Codex / Cursor Worker Dispatch〕）は、Round の判定を決めた後に（Round を進めずに止まる出口でも）、`worklog.md` へ 1 行 `gate結果: <phase> / task: <Current Task の task id。Gate Batch は , 区切り。task を持たない gate は -> / Round <n> / 判定: <approved | changes_requested | timeout | blocked> / 件数: high=<n> medium=<n> low=<n> blocking=<n>` を追記する。`timeout` は、requirements の、Round を消費する時間超過だけに使う。design・implementation・completion の時間超過など、Round を進めずに止まる出口は `blocked` と書く。`<n>` は、同じ phase・同じ task の既存の `gate結果:` 行の数に 1 を足した値で、`Gate Rounds`・`Completion Rounds`・`reviews.md` の見出しなどのカウンタからは取らない。件数は全 reviewer の finding を合わせ、blocking の再現を確かめた後の値（後から gate の効きを数えるための記録で、routing・カウンタは読まない。2026-10-10 の分析では、implementation・completion の Round 数と high の件数が steering の宣言された欄から数えられなかった）。

## Subagent Model Routing

ターミナルのモデル設定に依存せず、フェーズごとに適切なモデルを使う。Claude Code では `references/fixed-models.md` の tier 表と Formal gate 固定表の遵守が `PreToolUse`（`matcher: "Agent"`）の `run-agent-dispatch-model-gate-hook.sh` により起動時に warn される（未遵守は起動を止めない。詳細・既知の限界は `references/fixed-models.md` の該当節）。

フェーズごとの tier とモデル（実装の `Composer 2.5`〔`composer-2-fast` 不使用〕、`remediation_loop` 中の `gdd-remediation-worker` の dispatch 必須と gate subagent の `model="opus"` を含む）は `references/fixed-models.md` の tier 表と Formal gate 固定表を正本とし、ここに再掲しない。

## Typed Agent Resolution

各 Template は `subagent_type` を持つ。formal_gate（planning・design-gating・implementation-gating・completion-check）は `gate-driven-development:gdd-formal-gate-runner`、light_task（task-breakdown・TDD）は `gate-driven-development:gdd-light-task-runner`。model と effort は agent 定義の frontmatter で固定する（`Agent` ツールは effort を引数で受けない。値の正本は `references/fixed-models.md`）。`agent_dispatch_gate.py` は runner を免除せず、Template が明示する `model` を工程の tier で判定する。

formal_gate の Template（`gdd-formal-gate-runner`）は、Claude Code では `run_in_background=True` で起動して待つ（同期で起動すると期限を測れない。main からの同期起動は PreToolUse hook〔`lib/background_dispatch_gate.py`〕が deny する。Codex・Cursor はこの引数を使わない）。手順は次のとおり。
1. Template の `Agent` を起動した**後に**、`Bash` の `run_in_background: true` で期限 timer `sleep 3660` を起動する（先に置いた timer は期限を覆うものと認めない）
2. `<gdd-stop>` を書かずに turn を終えて待つ（`blocked` などで止まると loop state が消える。background の dispatch が動いている間は、停止理由が本文・tool result の marker、ポーリング上限での昇格のどれで決まっても、Stop hook がほかの停止の検査より先に押し返す。本文に目印が無いのに押し返されたら、最後の tool result〔Read した文書など〕の marker を拾っているので、marker を含まない tool を 1 回呼んでから待つ）。gate-runner 自身の完了通知（`<task-id>` が起動応答の agentId と一致するもの）の result を、Template の返り値として Post-Return Routing に進む。`<note>` が「This agent stopped with background work of its own still running」で始まる通知は途中で、返りではない（Stop hook も終わりに数えない）。routing も timer の停止もせず、同じ task-id の次の通知を待つ。timer の完了など、ほかの通知で起きたときは routing せず、state.md を読まない（gate-runner が書いている途中の値を読むため）。timer が先に完了したら、§ Reviewer Input and Time Budget の時間上限に従う
3. gate-runner が先に返ったら、timer を `TaskStop` で止める（止めないと、human-check の待ちの間に timer の完了で起きる）
4. result に `<gdd-stop>` があれば、その marker を main の本文に書く（human-check の本文があれば、判断ポイントの `相談役の推奨:` を一次表示の原則 7 のとおり書いて〔相談役は background で起動し、返りを待たずに表示する〕、main の最終回答に表示する。background の返りは tool result ではないので、Stop hook の tool result の marker の拾い上げ〔Fallback 1〕は効かない）（Stop hook の期限 watchdog は本文の marker だけを読む）

`## 読む対象` は呼び出し側が埋め、subagent が読む範囲を閉じる。大きい本文（diff・design.md）は貼らずにパスと範囲（base・tip の sha）で渡す（呼び出し側の出力 token を経由するより subagent が 1 回読むほうが安い）。`手順` は SKILL.md のパスで、節には絞らない（completion-check・task-breakdown は Steps の前に必須の節を持ち、切り出しは gate の観点を落とす）。`state.md 転記` の値は突合用の参考値で、判断に使う値と State Update Contract の read-back はディスクから読んで確定する。

**セッションが終わって background の dispatch が返らなかったとき**: background の subagent と期限 timer は、セッションのプロセスが終わると止まり、完了通知も残らない。再開したセッションで、完了通知も、host が動いていないと答えた `TaskStop` の結果（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`）も無い dispatch が transcript に残っていたら、その dispatch はもう動いていないものとして扱う。`TaskStop` をその agentId に 1 回呼ぶ。本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功か、`No task found` か `is not running` のエラーで返ったら、Stop hook の期限 watchdog・loop state を消す停止の押し返し・継続の押し返しの in-flight の判定のどれからも外れる。ほかの結果（拒否・別の文面のエラー、JSON の `task_id`・`shell_id` が止めた id でない成功）で返ったら、その dispatch はまだ動いているかもしれないので外れない。`TaskStop` を繰り返さず、loop state を保つ `clarification-needed` の `<gdd-stop>` を本文に書いて人に渡す（期限 watchdog は本文の marker を読んで止める。`blocked`・`cancelled` など loop state を消す停止は、dispatch が動いている間は押し返される。押し返しを飛ばす条件〔連続 block の上限など〕は `references/stop-hook-structured-markers.md`）。期限 watchdog が「上限を超えた。超過として扱う」と block しても、前のプロセスで起動して返らなかった dispatch なら、超過ではなくこの再開の手順に従う。次に `state.md` の `Resume From` と `reviews.md` の最新 Round を読み、同じ Template で起動し直す。gate は Round の判定を決めるたびに `reviews.md` と `state.md` に書いている（requirements-gating は `references/requirements-gating-steps.md` Step 6・7）ので、起動し直した gate は記録の済んだ Round の次から始まる。記録の無い途中の Round はやり直しになる。相談役（`gdd-opus-advisor`）は起動し直さない（`references/human-check-template.md` 一次表示の原則 7）。

agent 定義が見つからず `Agent` の起動が失敗したとき（定義はセッション開始時にしか読み込まれない。長く動いているセッションがこの版に切り替わった直後など）と、agent 定義の `tools:` の名前が解決できず起動に失敗したときは、1 回だけ `subagent_type="general-purpose"`・Template と同じ `model`・同じ `run_in_background` で、prompt の先頭に該当 `agents/<name>.md` の本文を貼って起動し直し（formal_gate なら上の待ち方の手順も同じ。`general-purpose` は期限 watchdog の対象外なので、期限は timer で自分で守る）、effort が main 継承であることを `worklog.md` に記録する。それでも起動できなければ fail-closed で停止する。

## Reviewer Input and Time Budget

`gdd-planning-reviewer`（requirements-gating・design-gating）と `gdd-implementation-reviewer`（implementation-gating の escalation）を gate から起動する側（gate runner。inline 実行なら main）の正本。agent 定義には要点だけを書き、範囲はここと一致させる（2026-10-02、GDD を使う別の repo のタスクで、requirements レビューが長い計画 doc の全文と plugin の reference を毎回読み、1 回ごとに長い時間がかかった。2 回目は応答が途絶えて stream watchdog に止められた）。
- **入力は 1 枚**: `.steering/<task>/review-input/<gate>-round-<N>.md` を書き、prompt には 1 枚の絶対パスと `## Worktree`（worktree の絶対パス）を渡す。1 枚の先頭は `- Worktree: <絶対パス>` の行にし、1 枚の中のパスは worktree からの相対、plugin の reference は `${CLAUDE_PLUGIN_ROOT}/references/<file>` で書く（`.steering/` に他の絶対パスを書くと steering write guard が止める）。中身は次のとおり。(1) 変更点: implementation は `対象の差分: <base>...<tip>`（本文を貼らず、reviewer が `git diff` する）。requirements の初回は Summary Brief（承認ポイント・Honest Limitations）・スコープ・非スコープ・Human Check Questions・Implementation Sequence Plan の写し（quick (express) では机上追跡の対象の `## Implementation Policy`・`## 既存実装の確認` も）。design の初回は具体化した節の写し（requirements-gating で design の観点の組に渡す 1 枚も同じ中身にし、ファイル名を `requirements-round-<N>-design.md` に、`- Worktree:` の次の行を `- Phase: design（gdd-requirements-gating から。human check の前）` にする）。再入（requirements・design とも）は、前回 Round の blocking の一覧（ID・要約・処置した場所。節名か `file:line`。requirements の再入では処置の `根拠:` と `伝播:` の値も）と、前回 Round から変えた節の写し（再入の定義と読む範囲は `requirements-gating-steps.md` § レビューループの契約 3）。(2) AC 表: `AC ID | 本文`（受入条件の写し。`根拠:`・`計測:` を含む）。(3) blocking の定義: 下の「blocking の条件」と、その gate の接地条件（requirements / design は `requirements-gating-steps.md` § 精度の第一原則 と § レビューループの契約、implementation は `reviewer-common.md` § 常時 High と実害クラス）の写し。(4) implementation だけ: 承認時点の `requirements.md` § Honest Limitations と、`Approved Direction`・`Human Recheck Boundary` の写し、task ごとの Contract Surface Coverage を指す `参照: .steering/<task>/tasklist.md § <task id> Contract Surface Coverage` の行（Gate Batch では task ごとに 1 行）。(5) `機械検査:` の行（下の script の結果）。(6) design の初回と implementation だけ: `worklog.md` の `AI が閉じた:`・`表示した文面を採用:` の行が名指しした AC（`requirements-gating-steps.md` § AI が閉じる blocking・§ 一括提示への返答）を `AI が閉じた計測: <AC ID>` の行で並べ、reviewer はその AC の `計測:` が壊れた実装を通さないかを確かめる（implementation では実装を壊して落ちることを確かめる）。1 枚は 200 行以内にし、超えたら (1) の大きい節から `参照:` に回す。**パスだけ渡すもの**: 計画 doc（`requirements.md`・`design.md`・`tasklist.md`）と gate が要る reference は、`参照: <path> § <節>` の行で書くだけにする。計画 doc の全文と plugin の `references/`（`reviewer-common.md` と、agent 定義か 1 枚が名指しした節を除く。`post-completion-pr-flow.md`・`human-check-template.md` など）は通読させない。対象 repo の実コード、planning の最新 Round の `reviews.md`、implementation の呼び出し側と対になる実装は、従来どおり読む。requirements の観点の reviewer の 1 枚には、`references/requirements-gating-steps.md` Step 4c の写し（`原文だけでは決まらない` の行と行き先、仮決定を添えた `既存とぶつかる` の行）も入れる。
- **機械的な整合は script**: requirements / design の reviewer を起動する前に `python3 scripts/lint-plan-consistency.py --steering-dir <steering> --entry <requirements の初回（express の human check の一部変更で回す Round を含む）なら requirements、再入なら requirements-reentry、design なら design>` を回す（`--entry` が無いと exit 2）（AC ID が Summary Brief・Implementation Sequence Plan・design.md で引用だけか、引用先が受入条件にあるか、同じ AC の数値が食い違わないか、requirements では AC と承認ポイントの番号つき項目が 1 件以上あり、AC ごとの `根拠:`・`計測:` と承認ポイントの項目ごとの `根拠:` の欄があるか、requirements の再入では加えて `reviews.md` の最新 Round の処置の 1 件ごとに `根拠:` と `伝播:` の欄があるか）。ERROR は起動の前に直す。exit 2 と、ERROR の行が無い exit 1 は起動を止め、原因を `worklog.md` に書く。結果は 1 枚に必ず 1 行書く（`機械検査: OK（AC 定義 <n> 件）` か `機械検査: WARN <内容>`）。reviewer はこの行があれば突合を手でやり直さず、無ければ自分で突合する。implementation では `機械検査: 対象外` と書く
- **blocking の条件**: blocking の finding には `failure scenario`（具体的な入力・状態 → 誤った結果）を必ず付ける。無いものは advisory として記録する。起動した側は受け入れる前に再現を確かめる（implementation はテストかコマンドで、planning は artifact と実コードを追って）。再現できなければ advisory に落とし、理由を `reviews.md`（implementation は `tasklist.md` の Attempts）に書く。ただし implementation では、`reviewer-common.md` § 常時 High の適用範囲に当たる finding・実害クラス（同 § finding category）・`gdd-security-reviewer` の finding は、failure scenario の有無と再現の成否を問わず blocking のまま扱う。requirements / design では、blocking のまま扱うのは `reviewer-common.md` § 常時 High の適用範囲の 4 型に当たる finding だけで、`gdd-security-reviewer` の finding もほかの reviewer と同じ規則で分ける（正本: `requirements-gating-steps.md` § 精度の第一原則）
- **時間上限**: planning・security・completion の reviewer 30 分、implementation 20 分、`gdd-formal-gate-runner` 60 分（起動から返るまで）。Claude Code では `Agent` の `run_in_background: true` で起動し、続けて `Bash` の `run_in_background: true` で期限 timer（`sleep <上限の秒数+60>`。コマンドはこの形だけ）を起動する。先に届いた完了通知（途中の通知を除く。§ Typed Agent Resolution の手順 2）で決める。reviewer が先なら timer を `TaskStop` で止める。timer が先なら reviewer を `TaskStop` で止め、超過として扱う（`TaskStop` の結果が、本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running` のどれでもなかったら（拒否など）、reviewer はまだ動いているものとして外れないので、`TaskStop` を繰り返さず、loop state を保つ `clarification-needed` の `<gdd-stop>` で人に渡す。`blocked` で止めると押し返される。押し返しを飛ばす条件は `references/stop-hook-structured-markers.md`）。stream watchdog などで reviewer がエラーで返ったときも、超過と同じに扱う。Stop hook（`lib/wait_watchdog.py`）が、background で実行中のこれらの dispatch（起動応答の agentId があるもの）に期限を覆う timer（起動応答を確かめられ、まだ終わっていないもの）が無いと block して置かせ、上限を超えると（起動時刻が読めないときも）block して `TaskStop` させる。人間に渡す停止（`cancelled`・`human-check-waiting`・`blocked`・`clarification-needed`・`staging-verification-blocked`）には当てない。この停止は本文の marker だけで見分ける（tool result の marker では見分けない）ので、subagent が返した marker で止まるときも本文に書く。background の dispatch が動いている間に loop state を消す停止は、これとは別に押し返す（§ Typed Agent Resolution）。main からの gate-runner の同期起動は、PreToolUse hook（`lib/background_dispatch_gate.py`）が deny する（手順は § Typed Agent Resolution）。gate-runner の中で起動する reviewer は対象外（subagent が完了通知を受け取れるかは確かめていない）。返ったときは所要時間（分）とツール呼び出しの回数（完了通知の `<usage>` の `tool_uses`。読めなければ `不明`）を `reviews.md` の Round（implementation は Attempts）に 1 行書く。これとは別に、gate を実行した側（gate runner。inline 実行なら main。main が gate runner を時間上限・エラーで止めて出口を決めたときも main。worker 経由なら結果を統合する main で、worker 自身は書かない）は、どの runtime でも Round の判定を決めた後に `worklog.md` へ `gate結果:` 行を 1 行書く（§ Subagent Return Output Contract）。**計れないとき**: background の起動か完了通知が使えない経路（Codex・Cursor、main session inline execution、通知を受け取れるかを確かめていない subagent の中）では時間上限を計れない。入力の上限と blocking の条件だけを適用し、`worklog.md` に `reviewer time budget: unmeasured (<理由>)` と書き、`reviews.md` の所要時間と呼び出しの回数は `不明` と書く
- **超過・無応答のとき**: 入力を狭めて 1 回だけ再実行する（`参照:` の行を消して 1 枚だけにする。ただし Contract Surface Coverage の `参照:` の行は残す。implementation は差分を Current Task の変更ファイルに絞る。completion は入力を変えない）。時間上限は同じ。それも返らなければ、その回は消費済みとする。requirements は `reviews.md` に `判定: timeout` の Round を書き、`Human Check Questions` に「planning review は時間超過で 2 回とも返らず、成立していない」と書いて、Round 上限到達と同じ一括提示（`requirements-gating-steps.md` Steps 7。選択肢は再レビュー / レビュー無しで承認 / 差し戻し。レビューが成立していないので、原因を変える案は足さない）で人間に渡す（requirements-gating が並行に起動した design の観点の組だけが返らないときは、`requirements-gating-steps.md` Step 5 のとおり Round 全体を timeout にしない）。design・implementation・completion は Round と `Gate Rounds`・`Completion Rounds` を進めず、`<gdd-stop reason="blocked">` で止めて人間に渡す。completion で main が gate runner を止めたときは、`Next Action` を変えず、停止理由を completion review が成立していないこととして main が表示する（不足 evidence は表示しない）

## Codex / Cursor Worker Dispatch

Codex / Cursor では、`Recommended model` を表示するだけでは実行したことにならない。phase dispatch must call the worker runner。工程ごとの model / effort を使う場合は `scripts/run-gdd-worker.py` を呼び、`worker_runs/<run_id>/result.json` を残す。

必須契約:

- do not treat Recommended model as applied。`setup-gdd-loop.sh` の表示は bootstrap recommendation であり、実適用の証跡ではない。
- main session must integrate worker result。worker は isolated artifact producer で、`state.md` / `tasklist.md` / `worklog.md` へ直接統合しない。
- formal gate unverified blocks automatic phase advancement。formal gate で `application_status=unverified` / `unavailable` / `failed` の場合、軽量 model へ黙って落とさず HITL または heavy retry を要求する。
- `gdd-task-breakdown -> gpt-5.6-terra / medium`
- `gdd-status -> gpt-5.6-terra / low`
- `remediation_loop` 中は `--complexity remediation_loop` を渡す。`--phase` 単独では往復による tier 昇格を検出できないため、controller が明示指定する（`resolve-gdd-model.py --complexity` は `--phase` 由来の判定より優先して tier 表の host 列を解決する。tier→model の対応は `references/fixed-models.md` が正本）。`--complexity` の受理値は `remediation_loop` のみ（CLI の `choices` レベルで強制。かつて `leaf` / `light` / `heavy` も受理していたが、formal gate phase に渡すと上の「formal gate unverified blocks automatic phase advancement」契約を迂回して降格できる fail-open だったため、実際に使う呼び出し元が無いことを確認したうえで削除した。PR 旧#89 self-review）

代表コマンド: `python3 scripts/run-gdd-worker.py --runtime codex --phase gdd-design-gating --text "<intent>" --cwd "<worktree>"`
`remediation_loop` 昇格時（Codex）: `python3 scripts/run-gdd-worker.py --runtime codex --phase gdd-implementation-gating --complexity remediation_loop --text "<intent>" --cwd "<worktree>"`。Cursor は現時点で `build_command()` の `cursor` 分岐が `codex` 分岐と同一実装のため、`--runtime cursor` を渡しても実際には codex CLI が起動し Cursor 実行として成立しない（model/effort の解決自体は resolver が正しく `grok-4.6` / `high` を返す）。Cursor 向けの worker dispatch は現状未実装であり、`application_status` を Cursor 固有の値へ倒す処理は無い（`build_command()` の `cursor` 分岐が `codex` 分岐と同一の argv を返すため。`application_status` 自体は `main()` が `--dry-run` の有無だけで決めており runtime では分岐しない。独立レビューで、先の版がここに実装の裏付けない挙動を書いていたこと、その訂正も「`build_command()` が `runtime` を見ない」という誤った根拠だったことを指摘された。実際には 3 分岐しており、`cursor` 分岐が `codex` 分岐と同一実装であるだけ）。実際に Cursor 環境で worker を起動する経路の追加は別課題とする

## Dialectic Review Dispatch

`dialectic-review.md` Trigger 該当時のみ実行。Primary / Counter 独立起動 → cross-review → `Dialectic Review Summary` のみ返す → summary 保存 → AC / scope 変更要求時 routing。Short Form: summary 欠落補完時 `dialectic-review.md` Short Form 可。Primary / Counter 独立評価 + cross-review。Cursor / Codex はメインセッション内 read-only review で実行可。

## 1. Brainstorming + Requirements-Gating

### Template

```
Agent(
  subagent_type="gate-driven-development:gdd-formal-gate-runner",
  model="opus",
  run_in_background=True,
  description="GDD planning: brainstorming + requirements-gating",
  prompt="""
  以下の GDD planning を実行してください。

  ## Phase
  gdd-brainstorming
  ## 読む対象（呼び出し側が埋める。ここに無いファイルは、SKILL.md が名指し・要求したもの以外は読まない）
  - 手順: ${CLAUDE_PLUGIN_ROOT}/skills/gdd-brainstorming/SKILL.md と ${CLAUDE_PLUGIN_ROOT}/references/brainstorming-steps.md（Step 1-2a）。requirements-gating 到達後は ${CLAUDE_PLUGIN_ROOT}/skills/gdd-requirements-gating/SKILL.md。new タスクの worktree 作成は ${CLAUDE_PLUGIN_ROOT}/skills/gdd-using-git-worktrees/SKILL.md
  - 読むファイル: <ユーザーの意図に含まれる URL（WebFetch で読む。MCP でしか読めない URL（定義は `commands/gdd-dev.md` instruction 7）は、runner が MCP のツールを持たないので、呼び出し側が MCP で読んで本文を一時ファイルに保存し、`<URL> → <絶対パス>` の対で書く）。既存 steering から再開する場合は Steering Dir 配下の state.md・requirements.md・design.md の絶対パス。new は無し>
  - state.md 転記: <再開時のみ Resume From / Gate Status / Route In Progress の現在値。new は「なし」>
  - 対象の差分: なし

  ## 実行手順
  0. URL 含む意図は WebFetch で読む。`読むファイル` に一時ファイルがある URL は WebFetch せず、そのファイルを読む。WebFetch で本文が取れない URL（ログイン画面・4xx・SSO へのリダイレクト）は推測で進めず、`Intake Brief` の「まだ曖昧」にその URL を書いて `<gdd-stop reason="clarification-needed">` で終了する。対の一時ファイルが読めない・空のときも同じく止まる（呼び出し側は Intake Brief を利用者に表示して止まる。利用者が本文を貼るか、MCP で読める環境で `/gdd-dev` をやり直す）
  0.5. 上の brainstorming の手順と Step 1-2a で Clarification Loop 要否判定。`clarification-needed` なら `Intake Brief` 出力後 `<gdd-stop reason="clarification-needed">` で終了
  0.6. new タスクのみ: 上の gdd-using-git-worktrees の手順で main から worktree 作成。`$WORKTREE_ABS_PATH` 記録。失敗 or repo root 一致なら fail-closed 停止
  0.7. `assert-worktree-ready.py` 実行
  1. 上の brainstorming の手順で brainstorming 実行。`brainstorming-steps.md` 9 の要件を固める確認で止まるときは、質問の本文と `<gdd-stop reason="clarification-needed">` を返して終える（下の 2〜5、State Update Contract の最終値、return の行数の上限は当てない。`Resume From=gdd-brainstorming` のまま）
  2. requirements-gating まで同一ターンで完走
  3. human-check-waiting 到達後 human-check テンプレート出力
  4. **必ず** `<gdd-stop reason="human-check-waiting">` とその後の `## 👤 次にすること` を出力
  5. artifacts 全文出力しない。human-check テンプレートのみ返す

  ## State Update Contract（return 前必須）
  `<gdd-stop>` 前に以下を満たす。`Resume From` は workflow phase の唯一の正本。
  - `.steering/<task>/state.md` の `Resume From` を最終値（通常 `human-check-waiting`）に更新
  - 更新後 read-back 確認
  - 確認不可なら `<gdd-stop>` 出さず報告停止
  未更新 return は contract 違反。メイン復帰後 `Resume From` 再読し期待値外なら fail-closed 停止。

  ## ユーザーの意図
  ${ARGUMENTS}
  ## Plugin Root
  ${CLAUDE_PLUGIN_ROOT}
  """
)
```

### Post-Return Routing

subagent の human-check テンプレートを、判断ポイントの `相談役の推奨:` を `references/human-check-template.md` 一次表示の原則 7 のとおり main が書いて表示（相談役 2 本は background で起動し、返りを待たずに表示する。返った後に全文を出し直すかは `references/human-check-template.md` 一次表示の原則 7 と § 止まり直さないもの 2）（`Approved Direction` の `判断の委任` の欄が委任の値か、対象を含む `事前回答:` 行があれば `references/human-check-template.md` § 事前回答 2）。subagent 出力に `<gdd-stop reason="human-check-waiting">` がなければ、`## 👤 次にすること` の前に追加。

subagent の出力が `<gdd-stop reason="clarification-needed">` で、steering の `worklog.md` の最後の `要件確認:` 行が `待ち` か `未収束` なら（`references/brainstorming-steps.md` 9 の要件を固める確認）、質問の本文をそのまま main の最終回答に表示し、同じ marker と `## 👤 次にすること` で止まる。相談役は起動しない。返事を受けたら、本人の発言を `request.md` に足し（表示した質問と推奨を assistant の文と分かる形で引用して添える）、`worklog.md` に `要件確認: 回答 <ISO 8601>` を書いてから、同じ Template で起動し直す。それ以外の `clarification-needed` は intake の停止で、`commands/gdd-dev.md` 9 の 0 に従う。

### HITL Pending Hard Invariant

`<gdd-stop reason="human-check-waiting">` または `Resume From=human-check-waiting` 確認時 HITL 表示必須。subagent HITL is not an internal notification。main session must render the HITL in the next main-session final answer。禁止: 内部状態だけ返答 / ユーザーに `HITLを出して` と言わせる / 要約で判断ポイント削る。実行: (1) HITL 本文そのまま表示（内部の記号の置き換えと相談役の追加の書き込みは `references/human-check-template.md` § 判断の書き方 5・8 のとおり。判断ポイントの `相談役の推奨:` は一次表示の原則 7 のとおり、main が `references/human-check-template.md` に従って書く。相談役の返りを待って表示を遅らせない） (2) 本文欠落時 HITL 再生成 (3) artifact 欠落時 fail-closed (4) 追加指示は Planning Interrupt Decision Menu で分類。ユーザー本人の入力は、扱う前に `request.md` に足す（あれば。`references/brainstorming-steps.md` 9 の (1)）。例外：`Approved Direction` の `判断の委任` の欄が委任の値か、`worklog.md` に対象を含む `事前回答:` 行があれば `references/human-check-template.md` § 事前回答 2 に従う（適用は表示の代わりになる）

## 2. Design-Gating（human check 承認後）

design フェーズでは human check 取り直さない。design-gating は detailed design 具体化と reviewer 通過のみ行い `gdd-task-breakdown` へ handoff。

### Design-Gating Template

```
Agent(
  subagent_type="gate-driven-development:gdd-formal-gate-runner",
  model="opus",
  run_in_background=True,
  description="GDD design-gating",
  prompt="""
  ## Phase
  gdd-design-gating
  ## Plugin Root
  ${CLAUDE_PLUGIN_ROOT}
  ## Steering Dir
  <state.md の steering ディレクトリパス>
  ## Worktree
  <Steering Dir の 2 階層上にある worktree 絶対パス。§ Worktree Binding Precheck 必須>
  ## 読む対象（呼び出し側が埋める。ここに無いファイルは、SKILL.md が名指し・要求したもの以外は読まない）
  - 手順: ${CLAUDE_PLUGIN_ROOT}/skills/gdd-design-gating/SKILL.md
  - 読むファイル: <Steering Dir 配下の requirements.md・design.md の絶対パス。存在すれば adr.md・worklog.md・findings.md も>
  - state.md 転記: <Resume From / Gate Status / Approved Direction / Task Size / Planning Reviewer Selection / Route In Progress の現在値>
  - 対象の差分: なし
  ## State Update Contract（return 前必須）
  `.steering/<task>/state.md` 最終化し read-back 確認後 `<gdd-stop>` 出力。`Resume From` は workflow phase の唯一の正本。
  - 正常完了: `Design Review Status=approved` / `Resume From=gdd-task-breakdown`
  - 差し戻し: `human_recheck_required` → `Resume From=human-check-waiting`、`planning_rework_required` → `Resume From=gdd-brainstorming`
  **出力制約**: design human-check テンプレート生成しない。正常完了時は Handoff Summary のみ返す（5行以内、§ Subagent Return Output Contract）。更新せず return は contract 違反。
  """
)
```

### Post-Return Routing

1. `state.md` の `Resume From` を read-back
2. `gdd-task-breakdown`: `gdd-task-breakdown` 開始ヘッダー表示後 task-breakdown subagent を dispatch（§ Task-Breakdown Template）
3. `human-check-waiting`: subagent の human-check テンプレート表示後 `<gdd-stop reason="human-check-waiting">` で停止
4. `gdd-brainstorming`: `gdd-brainstorming` 開始ヘッダー表示後 `<gdd-stop reason="blocked">` で停止
5. 上記以外: fail-closed 停止

`Resume From` が workflow phase の唯一の正本（`references/state-machine.md` の Single Source of Truth）。
route 名は `Route In Progress` や本文で伝え、`gdd-stop` の reason には使わない。`gdd-stop` の reason は `references/output-format.md` § `<gdd-stop reason>` の許容値だけ。

## 3. Build Loop Orchestration

design-gating 通過後、メインセッションは以下のビルドループを **全タスク完了まで** 駆動する。ループ途中で停止してはならない（reason の用途に当たって `<gdd-stop>` で止まるときを除き、自律継続する。reason と用途は `references/output-format.md` § `<gdd-stop reason>` の許容値、`clarification-needed` の使いどころは `references/state-machine.md` の Allowed stop reasons の段落）。background の dispatch の完了通知を待って `<gdd-stop>` を書かずに turn を終えるのは、停止ではなく待ちである（§ Typed Agent Resolution）。

### Diagram

task-breakdown → TDD（RED）→ implementation（GREEN/REFACTOR）→ impl-gate → 次タスク or systematic-debugging or refactor-planning/completion-check → done

### Phase Execution

1. task-breakdown: Sonnet subagent（§ Task-Breakdown Template）
2. TDD: Sonnet subagent（§ TDD Template）
3. implementation: メインセッション（SKILL.md、`implementation` tier）
4. impl-gate: Opus subagent
5. completion-check: Opus subagent

### Loop Context Discipline

(1) 毎サイクル disk から `tasklist.md` / `state.md` 再読 (2) verbose 出力は disk 上ファイルが正本 (3) 全 subagent の return は 5 行以内（§ Subagent Return Output Contract）

### Task-Breakdown Template

```
Agent(
  subagent_type="gate-driven-development:gdd-light-task-runner",
  model="sonnet",
  description="GDD task-breakdown",
  prompt="""
  ## Phase
  gdd-task-breakdown
  ## Plugin Root
  ${CLAUDE_PLUGIN_ROOT}
  ## Steering Dir
  <state.md の steering ディレクトリパス>
  ## Worktree
  <Steering Dir の 2 階層上にある worktree 絶対パス。§ Worktree Binding Precheck 必須>

  ## 読む対象（呼び出し側が埋める。ここに無いファイルは、SKILL.md が名指し・要求したもの以外は読まない）
  - 手順: ${CLAUDE_PLUGIN_ROOT}/skills/gdd-task-breakdown/SKILL.md
  - 読むファイル: <Steering Dir 配下の requirements.md・design.md の絶対パス。tasklist.md があればそれも。worklog.md に `## Origin Findings` があれば worklog.md も>
  - state.md 転記: <Resume From / Gate Status / Task Size / Next Action の現在値>
  - 対象の差分: なし
  ## Return Contract（return 前必須）
  以下を state.md に書き込んでから return。return text は **5 行以内（報告行 1 行必須、§ Subagent Report Contract）**。
  ### 正常完了
  - `tasklist.md` 作成・更新 / `Next Action=gdd-test-driven-development` 設定
  ### planning_rework_required
  - `Next Action=gdd-brainstorming` 設定
  ### human_recheck_required
  - `Next Action=human-check-waiting` / `Resume From=human-check-waiting` 設定
  ### design_detail_only
  - `Next Action=gdd-design-gating` 設定
  更新せず return は契約違反。詳細は handoff ファイルへ（§ Subagent Return Output Contract）。
  """
)
```

### Task-Breakdown Post-Return Routing

1. `state.md` を disk から再読
2. `Next Action` を確認:
   - `gdd-test-driven-development`: task-breakdown 完了表示 + TDD 開始ヘッダー表示後 TDD subagent を dispatch（§ TDD Template）
   - `gdd-brainstorming`: brainstorming phase 再起動
   - `human-check-waiting`: HITL テンプレート表示後 `<gdd-stop reason="human-check-waiting">` で停止
   - `gdd-design-gating`: design-gating subagent 再起動
3. 上記いずれでもない場合（`result: worktree_mismatch` で `Next Action` が更新されていない場合を含む）: 再 dispatch せず fail-closed で停止し、`参照した正本 / 停止理由 / 次の1アクション` と `## 👤 次にすること` を返す

### TDD Template

```
Agent(
  subagent_type="gate-driven-development:gdd-light-task-runner",
  model="sonnet",
  description="GDD TDD: RED preparation",
  prompt="""
  Current Task の RED 準備を実行してください。
  ## Phase
  gdd-test-driven-development
  ## Plugin Root
  ${CLAUDE_PLUGIN_ROOT}
  ## Steering Dir
  <state.md の steering ディレクトリパス>
  ## Worktree
  <Steering Dir の 2 階層上にある worktree 絶対パス。§ Worktree Binding Precheck 必須>

  ## 読む対象（呼び出し側が埋める。ここに無いファイルは、SKILL.md が名指し・要求したもの以外は読まない）
  - 手順: ${CLAUDE_PLUGIN_ROOT}/skills/gdd-test-driven-development/SKILL.md
  - 読むファイル: <Steering Dir 配下の tasklist.md・requirements.md（AC）・design.md（テスト方針）の絶対パス、${CLAUDE_PLUGIN_ROOT}/references/self-review-lanes.md（§ 直し方。レビューの指摘を直すテストを書くときに従い、同節が従う先として名指しする節〔reviewer 側の点検として挙げるものは除く〕も読む。直す指摘は tasklist.md の task の `Fix Findings:` の行から読む）。tasklist.md が無い express で worklog.md に `## Origin Findings` があれば worklog.md も>
  - state.md 転記: <Next Action / Task Size と、tasklist.md の Current Task の task id・AC ID の現在値>
  - 対象の差分: なし
  ## Return Contract（return 前必須）
  以下を完了してから return。return text は **5 行以内（報告行 1 行必須、§ Subagent Report Contract）**。
  ### 正常完了（RED 確立）
  - `tasklist.md` の `Current Task` に `#### RED Evidence`（`Worktree:` 行含む。SKILL.md § Worktree Binding 参照）記録済み
  - `Next Action=gdd-subagent-driven-implementation` を state.md 設定済み
  - 詳細は handoff ファイルへ（§ Subagent Return Output Contract）
  ### planning_rework_required
  - `Next Action=gdd-brainstorming` 設定済み
  ### human_recheck_required
  - `Next Action=human-check-waiting` / `Resume From=human-check-waiting` 設定済み
  ### design_detail_only
  - `Next Action=gdd-design-gating` 設定済み
  ### planned_red_missing（Planned RED/E2E 欠落のみ）
  - `Next Action=gdd-task-breakdown` / `Resume From=gdd-task-breakdown` 設定済み
  - **例外（AC ID 未紐付け）**: `tasklist.md` 書き込み不要。state.md 更新必須。詳細は return text へ（SKILL.md § AC ID Binding）
  ### needs_clarification（Yes/No で観測できない AC の残留）
  - `Next Action=human-check-waiting` / `Resume From=human-check-waiting` 設定済み
  - `planned_red_missing` と重なる場合は `needs_clarification` 優先

  **異常完了では handoff 不要。** state.md の `Next Action` / `Resume From` が正本。更新せず return は contract 違反。
  """
)
```

### TDD Post-Return Routing

subagent から復帰したら、メインセッションは以下を順に実行する:

1. `state.md` と `tasklist.md` を disk から再読する（§ Loop Context Discipline 参照）
2. `Next Action` の値を確認する:
   - **`gdd-subagent-driven-implementation`**: RED 確立。停止せずそのまま実装 phase に進む
   - **`gdd-brainstorming`**: planning rework。brainstorming phase を再起動する
   - **`gdd-task-breakdown`**: Planned RED/E2E 欠落。task-breakdown subagent を再起動する
   - **`human-check-waiting`**: HITL 表示 → `<gdd-stop reason="human-check-waiting">` で停止する
   - **`gdd-design-gating`**: design detail 差し戻し → design-gating subagent を再起動する
3. 上記いずれでもない場合: fail-closed で停止し、`参照した正本 / 停止理由 / 次の1アクション` と `## 👤 次にすること` を返す

### Implementation-Gating Template

```
Agent(
  subagent_type="gate-driven-development:gdd-formal-gate-runner",
  model="opus",
  run_in_background=True,
  description="GDD implementation-gating",
  prompt="""
  実装レビューを実行してください。
  ## Phase
  gdd-implementation-gating
  ## Plugin Root
  ${CLAUDE_PLUGIN_ROOT}
  ## Steering Dir
  <state.md の steering ディレクトリパス>
  ## Worktree
  <Steering Dir の 2 階層上にある worktree 絶対パス。§ Worktree Binding Precheck 必須>

  ## 読む対象（呼び出し側が埋める。ここに無いファイルは、SKILL.md が名指し・要求したもの以外は読まない）
  - 手順: ${CLAUDE_PLUGIN_ROOT}/skills/gdd-implementation-gating/SKILL.md
  - 読むファイル: <Steering Dir 配下の requirements.md・design.md の絶対パス。Current Task が名指しする実装・テストのファイル>（tasklist.md は通読せず、SKILL.md § Steps の先頭の `impl-gate-context.py` の出力で読む）
  - state.md 転記: <Gate Status / Task Size / Cumulative Diff Base の最新 entry / Next Action と、tasklist.md の Current Task の全 task id とそれぞれの Gate Rounds の現在値>
  - 対象の差分: <`<base>...<tip>`。base: `git -C "<Worktree>" symbolic-ref --short refs/remotes/origin/HEAD` の出力（コマンドが失敗した・解決できない ref のときは、`origin/main`・`origin/master`・`origin/trunk`・`origin/develop` の順に `git rev-parse --verify` で確かめた最初のもの。local の branch 名は書かない）/ tip: `git -C "<Worktree>" rev-parse HEAD` の sha>
  ## State Update Contract（return 前必須）
  1. `approved`（Step 1e で review を外したときを含む。Step 8a の出口を除く。そこでは 2 に従う）: `Current Task` を `Completed Tasks` 移動（task block の `Fix Findings:` の行は消す）/ 次タスクあれば `Current Task` 昇格 / `Next Action` 更新（次タスクあり: `gdd-test-driven-development`、全完了: `gdd-refactor-planning` or `gdd-completion-check`）
  2. `changes_requested`（と、reviewer が approved でも Step 8a の出口で `Next Action=gdd-systematic-debugging` にしたとき）: `Next Action=gdd-systematic-debugging` 設定
  3. tasklist.md 更新後 re-read して section 移動確認
  更新せず return は contract 違反。詳細は handoff ファイルへ（§ Subagent Return Output Contract: return は 5行以内）。
  """
)
```

### Implementation-Gating Post-Return Routing（最重要: 実装漏れ防止）

1. `tasklist.md` を disk から re-read
2. `Next Action` を確認:
   - `gdd-test-driven-development`: `Current Task` 更新確認後 TDD subagent を dispatch（ループ継続）
   - `gdd-systematic-debugging`: remediation 必要。起動前に `tasklist.md` の `Gate Rounds` で `remediation_loop` 判定（`references/fixed-models.md`）を行い、該当なら systematic-debugging・impl-gate（§ Implementation-Gating Template を使う）を `model="opus"`、worker を `gdd-remediation-worker`（prompt は `gdd-subagent-driven-implementation` の手順 3 のとおり `## Worktree` と `## Plugin Root` を渡す）で起動し実適用 model と effort を `worklog.md` に記録する（Claude Code の場合。Cursor / Codex は `model="opus"` を実行せず、上の § Codex / Cursor Worker Dispatch の worker runner が tier 表の host 列を解決する）。systematic-debugging 起動後 impl-gate 再実行
   - `gdd-refactor-planning`: 全タスク完了、refactor gate 未実施。`gdd-refactor-planning` skill 実行
   - `gdd-completion-check`: 全タスク完了（refactor gate 通過済み）。completion-check subagent 起動
   - `done`: Express パス全完了。Post-Completion PR Flow（PR を作ったなら CI の待機と自動修正を含む）実行後 `<gdd-stop reason="done">` で停止
3. **実装漏れ防止 guard**: `Next Action` が `gdd-completion-check` or `done` の場合、`tasklist.md` の `Pending Tasks` が `- なし` であることを確認。残タスクあれば TDD に戻る（`gdd-completion-check` の場合は、下の § Completion-Check の前の機械検査の行の順〔最初の `ok` 以外の行〕に従い、`remaining-tasks` 行より前の行が `ok` でなければその行の扱いを先に行う）
4. 上記いずれでもない場合（`result: worktree_mismatch` / `diff_base_mismatch` で `Next Action` が更新されていない場合を含む）: 再 dispatch せず fail-closed で停止し、`参照した正本 / 停止理由 / 次の1アクション` と `## 👤 次にすること` を返す

### Completion-Check の前の機械検査

Completion-Check Template を dispatch する前に、main が `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-completion-mechanical.py --steering <Steering Dir> --base <Template の対象の差分の base> --root <Worktree>` を 1 回実行する（行の意味は同スクリプトの先頭と `skills/gdd-completion-check/SKILL.md` Step 0）。機械で判定できる不備を、gate runner を起動せずに差し戻すためである。先に、worklog.md へ移しただけの `Reviewed by:` 行や完了タスクのような記録の書き漏れだけを tasklist.md に戻して実行し直してよい（ほかの値は直さない）。次に、出力の最初の `ok` 以外の行（行は Step の順に並ぶ）で、下の表の 1 つを行う。exit 2 なら引数の書き方と Plugin Root のパスだけを直して 1 回だけ実行し直す（`--steering`・`--root`・`--base` は Template の値から変えない）。この結果は gate の evidence にならない（gate は Step 0 で実行し直す）。 行ごとに行うこと: (1) どれかの行が `error`、exit が 0・1 以外、最後の行が終わりの行でない → dispatch しない。stderr と最後の行を報告し、外部前提不足として `Next Action=gdd-completion-check` のまま `<gdd-stop reason="blocked">` で止める（`Completion Rounds` に数えない）。(2) `reviewed-by`（2a） → `Implementation Gate Bounce Log` に行の詳細を key（`task-id + 欠落項目`）として足し、`Next Action=gdd-implementation-gating`。足した結果が閾値（`references/bounce-log-schema.md`）に達するなら、差し戻さずに dispatch する（昇格は gate の Step 2a が行う）。(3) `remaining-tasks`（3） → 上の Post-Return Routing 手順 3 のとおり `Next Action=gdd-test-driven-development`。(4) `route-in-progress`（4） → 差し戻さずに dispatch する（`references/gate-checklists.md` § Checklist E の分類は gate が決める）。(4a) `ac-source`（4c） → 差し戻さずに dispatch する（AC を閉じた形で読めないので、gate が読んで判定する）。`ac-coverage`（4c） → dispatch しない。task の `AC:` に無い AC を blocker として報告し、`gdd-task-breakdown` での再分割が要ると書いて、`Next Action=gdd-completion-check` のまま `<gdd-stop reason="blocked">` で止める。(5) `codebase-health`（4c-3） → `Next Action=gdd-systematic-debugging`。gate の差し戻しと同じく `Completion Rounds` を +1 し `Completion Baseline` を更新する（同 § Completion Rounds / Completion Baseline の操作手順 の 1・2。上限を超えたら `references/state-machine.md` § Remediation Loop Safety のとおり）。(5a) `follow-up-stage`（4d） → 差し戻さずに dispatch する（Lane の追跡先は gate が補う。`references/state-machine.md` の Tracking Destination の行）。(6) `ac-ids`（5） → dispatch しない。行の詳細を blocker として報告し、`Next Action=gdd-completion-check` のまま `<gdd-stop reason="blocked">` で止める。(7) すべて `ok` → dispatch する。差し戻したら dispatch せずに return し、次の phase へ進む。

### Completion-Check Template

```
Agent(
  subagent_type="gate-driven-development:gdd-formal-gate-runner",
  model="opus",
  run_in_background=True,
  description="GDD completion-check",
  prompt="""
  完了チェックを実行してください。

  ## Phase
  gdd-completion-check
  ## Plugin Root
  ${CLAUDE_PLUGIN_ROOT}
  ## Steering Dir
  <state.md の steering ディレクトリパス>
  ## Worktree
  <Steering Dir の 2 階層上にある worktree 絶対パス。§ Worktree Binding Precheck 必須>

  ## 読む対象（呼び出し側が埋める。ここに無いファイルは、SKILL.md が名指し・要求したもの以外は読まない）
  - 手順: ${CLAUDE_PLUGIN_ROOT}/skills/gdd-completion-check/SKILL.md
  - 読むファイル: <Steering Dir 配下の requirements.md（AC 一覧）・design.md・tasklist.md・worklog.md の絶対パス。存在すれば ac-ledger.md（AC Trace Ledger）・request.md・request-crosscheck.md と handoff/ 配下のファイル>
  - state.md 転記: <Resume From / Next Action / Gate Status / Cumulative Diff Base の最新 entry の現在値>
  - 対象の差分: <`<base>...<tip>`。base: Cumulative Diff Base の最新 hash_prefix（無ければ default branch。解決は implementation-gating の base と同じ）/ tip: `git -C "<Worktree>" rev-parse HEAD` の sha>。この欄は Approved Direction vs Diff Check（4c）と Codebase Health Gate（4c-3）の起点で、それ以外の検査の範囲は各 SKILL.md・checklist に従って別に実行する。default branch 起点なのは AC Drift Check（`references/gate-checklists.md` § Checklist A）と Pre-PR `gdd-pr-review` の 3a/3d
  ## 事前確認（起動時）
  - SKILL.md の Step 0（`scripts/check-completion-mechanical.py`）の行の順で、最初の `ok` 以外の行が `remaining-tasks` 行なら（`Current Task`・`Pending Tasks` が `- なし` でない）、completion を行わず、行の詳細をそのまま報告して return する。それより前の行が `ok` でなければ、その Step の扱いに従う

  ## State Update Contract（return 前必須）
  return する直前に、`.steering/<task>/state.md` の以下を最終化する。

  - 全 AC pass + evidence 充足: `Next Action=done`
  - 差し戻し: `Next Action=gdd-systematic-debugging`
  - 外部前提不足: `Next Action=gdd-completion-check`（再試行可能）。reviewer が時間超過・エラーで 2 回とも返らないときも同じ値のままにし、`result: review_unavailable`（§ Subagent Report Contract）と `<gdd-stop reason="blocked">` を返す（§ Reviewer Input and Time Budget の「超過・無応答のとき」）
  - 中止: `Next Action=cancelled`

  `done` 到達後は Post-Completion PR Flow を自動実行し、PR 作成後に `<gdd-stop reason="done">` を出力する（Auto-Arm 有効時はレビュー収束 clean 後に done。Stage Continuation 発火時はさらに後続 Stage の継続後。`references/post-completion-pr-flow.md` 参照）。

  更新できないまま return するのは contract 違反。
  詳細レビュー内容は `.steering/<task>/handoff/completion_check.md` に書く（§ Subagent Return Output Contract 参照: main session への return は 5行以内）。
  """
)
```

### Completion-Check Post-Return Routing

completion-check subagent から復帰したら、メインセッションは以下を順に実行する:

1. `state.md` の `Next Action` を read-back する
2. **`done`**: subagent が PR を作ったなら、Claude Code desktop ではまずメインセッションがその PR の Auto-fix をオンにする（`references/post-completion-pr-flow.md` Option 1 手順 6 の CI 失敗の自動修正。subagent は呼べない）。次に `Resume From` を確認する。`Resume From=external-review-waiting` なら Auto-Arm 待機中で完了ではない — メインセッションが `gdd-pr-review-followup` § Review Pending Loop を引き継ぎ、ScheduleWakeup を再 arm して `<gdd-stop reason="external-review-waiting">` で停止する。`references/post-merge-qa.md` § 入口 の条件を満たすなら、完了サマリーの代わりにメインセッションがその文書の手順を続ける。subagent が `<gdd-stop reason="blocked">` で戻ったなら（Post-PR Scope Continuation の未承認の操作など）、完了サマリーではなく blocker を表示して `<gdd-stop reason="blocked">` で停止する。それ以外なら subagent が PR 作成と `<gdd-stop reason="done">` を出力済みとして、完了サマリーを表示して停止する（完了サマリーには、`references/post-completion-pr-flow.md` Step 4 の条件に当たる `記録の場所: なし` の行を、main が同 Step 4 のとおり `requirements.md` を読んで書く。Stage Continuation が発火した場合、subagent は継続後の最終 Stage まで進めてから done を出す）
3. **`cancelled`**: 中止サマリーを表示し、`<gdd-stop reason="cancelled">` で停止する
4. **`gdd-systematic-debugging`**: AC failure / review blocker があった。systematic-debugging を起動して修正後、impl-gate → completion-check を再実行する。ただし `Resume From=human-check-waiting` なら § HITL Pending Hard Invariant を先に適用し、debugging を起動しない
5. **`gdd-completion-check`**: 外部前提不足で再試行待ち（`result: diff_base_mismatch` のときは起点／tip の不一致として、`result: review_unavailable` のときは completion review が成立していないこととして停止理由を出し、どちらも不足 evidence を表示しない）。それ以外は不足 evidence のリストをユーザーに表示し、`<gdd-stop reason="blocked">` で停止する
6. **`gdd-refactor-planning`**: refactor gate 未実施だった。メインセッションで実行後、completion-check を再起動する
7. 上記いずれでもない場合: fail-closed で停止
