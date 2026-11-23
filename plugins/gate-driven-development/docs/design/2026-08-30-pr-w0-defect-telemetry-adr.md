# ADR — 20260822-pr-w0-defect-telemetry

> `design.md` が「何をどう作るか」の正本。本ファイルは **なぜその判断にしたか / 何を却下したか** の正本。
> 書き分けは `references/adr-vs-design.md` に従う。

## ADR-1: `resolve_task()` に渡す `repo_root` は current worktree の toplevel とする

- **Context**
  W-9 は「Stop hook の done guard が他 worktree の `tasklist.md` を検査対象にする」誤バインドを塞ぐ変更。解決系として既存の `scripts/gdd_task_binding.py` の `resolve_task()` を再利用することは requirements § Architecture Recommendation Gate（案 A）で承認済みだが、**`repo_root` に何を渡すかは未定義**だった。
  design-gating の実測（2026-08-22）で、binding registry（`<repo_root>/.gdd/tasks/`）が **main repo root と各 worktree の 2 箇所に並存**していることが判明した。`.gdd/` は `.gitignore:7` で無視されるため、worktree ごとに独立したディレクトリが生える。
  - main repo の `.gdd/tasks/`: 2 件
  - 本 worktree `.gdd/tasks/`: 1 件（`20260822-pr-w0-defect-telemetry`）

- **Decision**
  `git rev-parse --show-toplevel`（= current worktree の toplevel）を `repo_root` として渡す。git 不在 / 取得失敗時は `conflict` 相当として warn 経路へ倒す。

- **Why**
  1. 既存 shell 側の唯一の呼び出し規約（`hooks/scripts/lib/detect-steering.sh:134-153` の `--repo-root "$_wt"`）と一致する。Architecture Driver「正本を 1 本にする」に沿う。
  2. main repo root を渡すと、worktree で作業中に**他 worktree の binding が候補に混ざる**。`resolve_task()` は `worktree_path == cwd` で絞るため即座に誤 bind するわけではないが、registry が 2 系統に割れたまま参照先だけ広げると `multiple_current_worktree_bindings` を誘発しうる。これは W-9 が塞ごうとしている失敗型（stale artifact が解決系を混乱させる）そのもので、同じ原因ファミリーを増やす。
  3. 実測で `--repo-root <worktree toplevel>` は本 worktree で `status: resolved` を返すことを確認済み。

- **Consequences**
  - registry の書き手（`commands/gdd-dev.md` の `upsert-from-state` 手順）が main repo root を渡した場合、hook 側と参照先がずれて `conflict`（= warn）になる。**block はしない**ので作業は止まらないが、done guard が実質無効になる。
  - この書き込み遵守率は dogfood で実測する（`design.md` § Codebase Health Survey finding の CH-5）。閾値超過なら次 PR で書き手側の強制化を検討する。本 PR では扱わない。

## ADR-2: 永続ファイルは append ではなく 1 件保持（last-write-wins）にする

- **Context**
  `requirements.md` § 実装方針 7 は `run-stop-failure-hook.sh` が「永続ファイルへ 1 件 append」と書いている。一方 AC-17 が要求するのは「記録 → `SessionStart` での `additionalContext` 注入 → 消費（削除）」の 3 段であり、履歴の保持は要求していない。

- **Decision**
  `~/.claude/.gdd-hook-state/last-turn-failure.json` に **JSON 1 オブジェクトを last-write-wins で保持**する。append しない。書き込みは tmp + `os.replace` の atomic write、消費は「読む → 注入 → `unlink`」。

- **Why**
  1. 履歴を読む consumer が存在しない。`SessionStart` は「前回ターン」だけを報告すればよい。
  2. append にすると「いつ truncate するか」「複数件をどう注入するか」という新しい判断が発生し、AC に無い分岐を増やす（KISS / YAGNI）。
  3. `unlink` による消費が AC-17 の「消費（削除）」を最も素直に満たす。append 形式だと消費 = 全削除になり、結局 1 件保持と同じ振る舞いになる。

- **Consequences**
  - AC-17 の意味（記録・注入・消費の 3 段）は変わらないため `design_detail_only` の範囲内。human recheck は不要。
  - 同一セッションで `StopFailure` が連続発火した場合、最後の 1 件だけが残る。これは「前回ターンの異常終了を知らせる」目的に対して十分。
  - `requirements.md` § 実装方針 7 の文言（「1 件 append」）と design が字面で食い違う。design.md § 論点 3 に具体化である旨を明記した。

## ADR-3: Route Decision の計上面は F1 + F2 に限り、残りは `unparsed_route_sections` で可視化する（design review で改訂）

- **Context**
  design-gating の全 worklog 走査（2026-08-22）で、Route Decision の記録書式が **3 種類**実在することが判明した。
  - **F1**: `## Route Decision` 節 + トップレベル `- <date> | ... | route: \`<r>\` | ...` 行（`20260817-pr-w3-self-review` に 20 件）
  - **F2**: `## <date> Systematic Debugging Route Decision` 見出し + `- route 判定:` 行（`20260407-example-allowlist` に 1 件）
  - **F3**（design-gating で新発見）: `## <date> ... = route \`<r>\`（...）` 見出し + `- **選んだ route**: \`<r>\`` 行（`20260817-pr-w3-self-review` L197 に 1 件）

  `requirements.md` AC-9 が計上対象として明示するのは F1 / F2 のみで、参照件数として 20 を挙げている。

- **Decision**
  parser の **section anchor** は「見出しに `Route Decision` を含む **または** `= route ` を含む」まで広げるが、**計上する受理面は F1 / F2 のみ**とする。F3 の節は「anchor には一致するが受理行 0 件」となり `unparsed_route_sections` に件数と所在が出る。

- **Why**
  1. AC-10 の要求は「Route Decision 見出しはあるが受理面に一致する行が 0 件の節を、黙って 0 件にせず可視化する」。F3 を anchor に含めて unparsed に落とすことは、この設計意図の直接的な実装である。
  2. 計上面を design 側で広げると、**approved な requirements が定めた計上の意味論を design が変えることになる**ため採らない（SKILL.md Guardrails「approved な requirements / implementation policy を design 側で勝手に追加変更しない」）。
     - **初版の根拠を訂正する**: 初版は「F3 を加えると AC-9 の参照件数 20 が 21 になるから」を理由にしていた。design review の指摘どおり、これは**数値の都合で意味論を決めており根拠として弱い**。正しい根拠は上記のとおり「承認された計上面を design が勝手に広げない」であり、20 が動かないのはその帰結にすぎない。
  3. F3 を anchor から外すと、実在する route 記録が**どの出力にも現れない silent drop** になる。これは本 PR が塞ごうとしている silent failure 型そのもの。

- **Consequences**
  - `unparsed_route_sections` の期待値が fixture に対して 1 件になる。テストで固定する。
  - F3 を正本書式へ昇格させるか、記録側を F1 に寄せるかの判断は **本 PR の非スコープ**。`worklog.md` に carry-forward する。
  - `references/phase-progression.md` には「正本書式は F1、F2 は legacy alias として読む」だけを書き、F3 は書かない（AC-11 の「書式定義は 1 箇所」を維持）。

## ADR-4: 通知本文と `additionalContext` に `error_details` を流さない

- **Context**
  `StopFailure` hook が受け取る payload の `error` / `error_details` は Claude Code 側が生成する値で、hook から見れば **untrusted input**。これが (a) `osascript` の AppleScript 文字列リテラル、(b) `SessionStart` の `additionalContext`（LLM が読む）、(c) `$HOME` 配下の永続ファイル という 3 つの trust boundary を跨ぐ（design-gating の security review で (d) `terminalSequence` = 端末の raw エスケープ が 4 つ目として追加された。ADR-6 参照）。
  requirements § Sensitive Data / Masking Policy は「長文は切り詰める」までしか定めておらず、注入面の扱いは未定義だった。

- **Decision**
  1. **永続ファイル**: `error` / `error_details` / `session_id` / timestamp のホワイトリスト。`error_details` は先頭 200 文字で切り詰め。
  2. **通知本文**: `error` 種別と固定文言のみ。`error_details` を載せない。`osascript` へは `-e` の文字列連結ではなく **stdin + 環境変数（`system attribute`）** で本文を渡す。`notify-send` は `argv` 渡し + `--` で option 終端。
  3. **`additionalContext`**: 固定ラベル `[gdd:last-turn-failed]` を前置し、`error` 種別 / timestamp / `session_id` 先頭 8 文字のみ。`error_details` は注入しない。

- **Why**
  1. AppleScript の文字列リテラルに外部由来の値を連結すると、`"` / 改行 / `&` で構文を抜けられる。**文字列を組み立てない**設計にすれば、エスケープの正しさを検証し続ける必要がなくなる（注入面を消す > 注入をフィルタする）。
  2. `additionalContext` は LLM のコンテキストに直接入る。外部由来の自由文を流すと prompt injection 面になる。**種別（enum 相当）だけを流せば injection 面が構造的に閉じる**。
  3. `error_details` は永続ファイルには残すので、人間が `cat` で読める。デバッグ可能性は失われない。

- **Consequences**
  - 通知と再開時報告の情報量が下がる。「何のエラーか」は種別で分かるが、詳細はファイルを開く必要がある。
  - テストで「`error_details` の値が通知本文と `additionalContext` に**現れない**」ことを負の assert で固定する（design.md § テスト方針）。
  - `gdd-security-reviewer` を design-gating で `waived` から `selected` に変更した（`state.md` § Planning Reviewer Selection）。requirements 時点の「外部送信面が無い」判定自体は正しかったが、**ローカルの注入面**を見落としていた。

## ADR-5: 共有 lib は 2 module に分ける

- **Context**
  W-9 は「bind 解決」と「`### Task` 見出しの受理面」の 2 つを共有化する。1 module にまとめるか分けるかが skeleton 段階の未確定事項（論点 1）だった。

- **Decision**
  `hooks/scripts/lib/task_binding_resolve.py` と `hooks/scripts/lib/tasklist_parse.py` の 2 module に分ける。

- **Why**
  1. 既存 `hooks/scripts/lib/` は責務ごとに小さく分かれている（`constants` / `errors` / `guards` / `state_io` / `transcript` 等）。既存規約に一致する。
  2. 2 つは**依存方向が異なる**。bind 解決は git と registry に依存する副作用ありの処理、受理面は文字列を受けて判定を返す純関数。1 module にすると `tasklist_parse` の単体テストが registry の存在に引きずられる。

- **Consequences**
  - `gdd_stop_hook.py`（現 1569 行、CH-1 で目安超過）から 2 module 分が抜けるため、AC-26 の「行数を実装前以下に保つ」に寄与する。
  - import は `lib/task_binding_resolve.py` が関数内で `sys.path.insert` して `scripts/gdd_task_binding` を読む。`ImportError` は `conflict` 相当（warn 経路）へ倒す。

## ADR-6: security review（design-gating）の指摘を初回 design gate 内で全件処置した

- **Context**
  `gdd-security-reviewer` を design-gating で `waived` → `selected` に変更して起動した結果、**High 2 件 / Medium 6 件**の指摘を受けた。requirements 時点の「外部送信面が無いので security 非該当」という判定は外部送信については正しかったが、**ローカルの注入面 4 つ**（AppleScript / `additionalContext` / 永続ファイル / `terminalSequence`）を見落としていた。

- **Decision**
  全 8 件を **初回 design gate の中で** design.md に反映して閉じ、`human_recheck_required` へは上げない。

  **route の扱いについて**: これは `design_detail_only` route ではない。`design_detail_only` は「一度 `approved` になった design を後続 phase から差し戻す」ための rollback route（`references/rollback-patterns.md`）であり、本件は `Design Review Status` が `in_review` のまま reviewer 指摘を反映しただけなので `Route In Progress` は `none` を維持する。判断基準として参照したのは同 route の **escalation 条件**（AC の根本追加削除 / 方向性変更 / final output owner / delivery path / prompt-output contract / masking enforcement / rollout order の変更）で、8 件のいずれも該当しない。

  | ID | 指摘 | 処置先 |
  |---|---|---|
  | H-1 | `additionalContext` は bash の `printf` 直埋めで `json.dumps` を通らない。`error` に `"` を仕込むと兄弟キー注入が成立 | enforcement point 3（既存 `run-session-start-hook.sh` の 3 段 escape 規約に揃える + トークン正規化の多重防御） |
  | H-2 | 永続ファイルの**読み手**に symlink guard も shape 検証も無い | § 論点 3「消費側の契約」（symlink 拒否 + shape 検証 + fail-closed 削除） |
  | M-1 | `binding.json` の `steering_path` が無検証の絶対パスのまま block 理由文と継続注入に載る | § 論点 2b「binding の containment 検証」（wrapper 側で `task_id` 形式 + `is_relative_to`） |
  | M-2 | 永続ファイル / state dir の permission 未指定（既存 2 実装が 0600 と 0644 で不統一） | § 論点 3「permission」（0700 / 0600 + `GDD_HOOK_STATE_DIR` override） |
  | M-3 | `cwd` にプロセス実 cwd を渡すと sub-directory 起動で常に warn 降格し、CT-3 が実運用で成立しない | § 論点 2b（`cwd` にも toplevel を渡す） |
  | M-4 | `terminalSequence` と `Notification` の `message` が Delivery Channel の表に無い | enforcement point 4 + 2（リテラル定数のみ / 固定文言対応表のみ） |
  | M-5 | 固定ラベル前置は境界ではない。`error` 自体が自由文字列 | enforcement point 3（`error` のトークン正規化 + 固定枠の文面） |
  | M-6 | stub 方式のテストでは `-e` 連結への退行を検出できない | § テスト方針（`tests/checks/` に静的 BLOCK check を 1 本追加） |

- **Why**
  1. 8 件はいずれも「**承認済みの masking policy をどこでどう強制するか**」の具体化であり、policy そのもの・owner・delivery path・rollout 順序を動かさない。`references/rollback-patterns.md` の `human_recheck_required` の境界（AC の根本追加削除 / 方向性変更 / final output owner / prompt-output contract / masking enforcement **point の変更**）に照らすと、enforcement point を**追加で厳しくする**方向であり、人間が承認した「通知本文と永続ファイルは 4 フィールドに限定する」という判断と矛盾しない。
  2. H-2 について reviewer は AC 追加を提案したが、AC-17 が固定しているのは「記録 → 注入 → 消費」の 3 段であり、**「壊れた/敵対的な内容を注入しない」は「どう読むか」の実装詳細**として design 側で閉じられる。AC を増やすと human recheck が必要になり、指摘の性質（防御の追加）に対して往復が過剰になる。テストで固定するので検証可能性は落ちない。
  3. M-6 の BLOCK check 追加は `plugins/gate-driven-development/**`（自走範囲内）で、`CONTRIBUTING.md:221` が禁じるのは既存 BLOCK check の**削除**であり追加は許容される。

- **Consequences**
  - 実装量が増える（注入面の契約テスト 7 種 + BLOCK check 1 本）。AC-22 の baseline 比較は「増える方向の差分のみ」になる。
  - `run-session-start-hook.sh` の変更が「前回異常終了の報告注入を足す」だけでなく「注入 field の sanitize 規約を守る」を含むことになった。既存経路（`_compact_resume_check`）の規約をそのまま踏襲するため、新規の書き方を発明しない。
  - M-3 は **CT-3（bind 済みは従来どおり block）の成立条件そのもの**だった。これを落としていたら「実装したが実運用では guard が全部 warn」という、計測でしか気づけない失敗になっていた。design-gating で security reviewer を起動した価値がここにある。
  - advisory（low）のうち採用したもの: `sys.path` は `insert(0, ...)` ではなく import 直後に取り除く / warn 経路の候補一覧は絶対パス全体ではなく slug + worktree basename に留める / tmp は同一ディレクトリに作る。いずれも design.md に反映済み。


## ADR-7: planning review の指摘（High 5 / Medium 7）を初回 design gate 内で全件処置した

- **Context**
  `gdd-planning-reviewer` が **High 5 件 / Medium 7 件**を報告した。うち 5 件（H-1〜H-5）は「design の記述が実コード・実データと食い違う」種類で、実測で全件裏が取れた。design が実測を主張しながら走査が不十分だったことが共通原因。

- **Decision**
  全 12 件を初回 design gate 内で design.md に反映して閉じ、`human_recheck_required` へは上げない。`Route In Progress` は `none` を維持する（ADR-6 と同じ理由）。

  | ID | 指摘 | 実測での裏取り | 処置先 |
  |---|---|---|---|
  | H-1 | AC-6 棚卸し表が grep 出力と一致せず、`collect-gdd-telemetry.py:178/188` の **Python 受理面 2 行**を取りこぼし | 確認。`^###\s+Task:` が 2 箇所。改修対象ファイル自身 | § AC-6 棚卸し表を再実測して差し替え + CH-6 |
  | H-2 | `phase-progression.md` に既存の `## Batch Route Decisions`（worklog 向け）が anchor と衝突し、AC-11 の「正本 1 箇所」が成立しない | 確認。同ファイルに「Worklog フォーマット」として明記あり | § Batch Route Decisions との衝突をどう決めたか（計上対象外 + AC-11 の「1 箇所」を再定義） |
  | H-3 | 実測が under-inclusive。route 見出しが**あと 3 件**あり、負の assert が空振り | 確認。route 見出しは計 5 件。`route: ` は 20 行**全てトップレベル**で表セルには 0 件 | § 実測やり直し（見出しベース）+ 負の assert を実在形に差し替え |
  | H-4 | `run-session-start-hook.sh` は `additionalContext` の printf が **7 箇所**、compact resume で **早期 exit** する。素直な前置は JSON 2 個出力で契約破壊 | 確認。66/126/175/539/546/556/582 行 + L130-131 で `exit 0` | enforcement point 3b（全 7 出力点に前置 / printf 成功後に unlink / 3 経路をテスト） |
  | H-5 | fixture 元が別業務 repo の運用ログで、内部 repo 名 / log id / 12 桁数値を含む。verbatim commit は配布経路に内部情報を載せる | 確認。内部 repo 名 3 件 + `gh_…` + 12 桁数値 | enforcement point 5（fixture は最小化 + 匿名化） |
  | M-1 | AC-26 が Requirements Trace に無く検証方法も無い | trace は反映済みだったが検証方法が未定義 | § テスト方針 § AC-26（行数）の検証 |
  | M-2 | AC-21 の文言の置き場所も静的検査の実装先も未定 | 確認 | § AC-21 の実装場所の確定 |
  | M-3 | `cwd` の規約未定義で false green（サブディレクトリ起動で常に warn） | security review M-3 と同一指摘 | § 論点 2b（処置済み） |
  | M-4 | AC-2 の条件節と design の分岐が不一致。guard 無効化の範囲が承認より広い可能性 | CH-5 の実測（3 worktree 中 1 件に binding なし）と併せて確認 | § 主要フロー 3（一律 warn を採る根拠 + 無効化範囲の明示） |
  | M-5 | 永続ファイルがグローバル 1 件でキーが無く、別 project のセッションが消費してしまう | 設計上そのとおり | § 論点 3「project キーを持たせる」 |
  | M-6 | dedupe / tracked 除外のモード別適用が未定義。AC-13 と AC-15 が衝突しうる | 確認 | § 変更点 4 のモード別表 |
  | M-7 | AC-1/AC-3 の RED 構成が未定義で、RED にならない fixture を書ける | 確認。`git worktree add` の先例は `test_root_branch_guard_contract.py:97-124` | § テスト方針 § W-9 の RED 構成 |

> **[SUPERSEDED 2026-08-30 / T-31]** 本項の「一律 warn」「実装は AC-2 より広い範囲で warn」は**逆転した**。completion-check が **AC-2 の fail-open 逸脱を出荷コードの挙動欠陥として検出**し、ユーザー判断「実装を AC に合わせる」に従って**狭めた**。現行の契約は **3 分岐** ——**bind 解決済み = 検査 / bind 不能 + 自 worktree の steering が「ちょうど 1 つ」= 検査（ただし containment 検査を通ったものに限る）/ 0 個または複数 = warn して通す**。**この行を写経しないこと**（正しい制約は `docs/adr/2026-08-30-pr-w0-defect-telemetry.md` § 後続 task が守るべき制約）。


- **Why**
  1. 12 件はいずれも **「承認済み AC を design がどう実現するか」の精度の問題**であり、AC の追加削除・方向性変更・owner / delivery path / masking policy / rollout order の変更を伴わない。`references/rollback-patterns.md` の escalation 条件に該当しない。
  2. H-1 / H-2 / H-3 は **AC-6 / AC-9 / AC-10 / AC-11 の pass 条件そのもの**に関わる。ここを直さずに `approved` にすると、実装は「design のとおり作ったのに AC を満たさない」状態になる。design gate で閉じるのが正しい。
  3. M-4 だけは AC の文言と実装の差に触れるため、**requirements の AC-2 を変更せず、design 側で「実装は AC-2 より広い範囲で warn になる」ことを明示する**形で閉じた。AC-2 が要求する観測可能な振る舞い（`block` を返さない / 候補一覧を出す）は満たすため AC 変更に当たらない。無効化範囲を隠さず書いたので、dogfood で判断材料になる。

- **Consequences**
  - **`collect-gdd-telemetry.py` の task 計数が本 PR の変更対象に加わった**（CH-6）。AC-8 の改修と同じファイルなので Stage S-2 の内側で収まる。既存 telemetry 値が変わる（過小計上の是正）ため、CHANGELOG に「telemetry の task 計数が是正され、既存の値より増える方向に変わる」を書く。
  - fixture 作成に「最小化 + 匿名化」の工数が乗る。逐語コピーより手間だが、公開経路を持つ plugin では必須。
  - **H-4 を落としていたら compact auto-resume を壊していた**。self-development の危険（`gdd-self-development.md`「hook 変更は自分自身のセッションを壊しうる」）が具体化した例で、requirements § 制約 の「worktree で green にしてから local へ入れる」が効く場面。
  - H-3 の負の assert 訂正により、初版のテスト計画にあった**判別力ゼロのテストが 1 本消えた**。「負の assert を書く前に、対象が実データに存在するか実測する」を Stage S-2 の規律として `worklog.md` に残す。


## ADR-8: bind 不能時、進捗表示と markerless resume-from は current worktree の steering に fall back する

- **Context**
  T-4 は `_count_task_progress()` / `_find_tasklist_text_for_progress()` / `latest_steering_resume_from()` を bind 解決へ寄せる task。`tasklist.md` § T-4 § Steps 3 の計画コードは、bind 不能時に `_find_tasklist_text_for_progress()` が `return ""` する形だった（done guard の「推測で拾わない」= `design.md` § 主要フロー 3 と対称にする意図）。
  RED 作成時の実読で、出荷済みの 4 テストが **binding.json の無い workspace** でこの fallback を要求していることが判明した。
  - `tests/test_stop_hook_e2e_block_content.py::TestHookE2EContinuationBlockContent::test_continuation_block_includes_task_progress` — 非 git tmpdir で `tasks: 1/3 done` を要求
  - `tests/test_stop_hook_e2e.py::TestHookE2EFallback3SteeringResumeFrom` の 3 本 — 非 git tmpdir で `.steering/*/state.md` の `Resume From: human-check-waiting` による停止 / 抑止を要求

- **Decision**
  bind 不能時の扱いを **done guard と非対称**にする。この 2 経路は `git worktree list` の走査（= 他 worktree の列挙）だけをやめ、**current worktree 自身の `.steering` を名前の降順で見る fallback は残す**。対象の決め方は `_bound_steering_file(root, filename)` 1 関数に集約し（進捗表示の `tasklist.md` と resume-from の `state.md` が同じ containment を通る）、**この 2 経路には**他 worktree を列挙する形を残さない。
  **限定の外側（T-4 impl-gate M-1 で訂正）**: `gdd_stop_hook.py` 全体では本 ADR の対象外に live な worktree 列挙が 2 経路残る（`persist_handoff_summary()` = 他 worktree の `state.md` へ書き込み / `_find_active_tasklist()` = 他 worktree の `tasklist.md` を読み）。処置先は `tasklist.md` § Verification § Carry-forward の `T-4 impl-gate M-1 の残り` 行が正本。 **read 側も無害ではない（Attempt 4 / M-1''-c の実測）**: 他タスクの `worklog.md` の `bounce_count` が本セッションの stdout を変え、bounce log は本来の worktree に残らない。実測は `tasklist.md` § T-4 § Attempts § Attempt 4 remediation § M-1''-c が正本。

- **Why**
  1. **bind が解決している間は AC-7 を完全に満たす**（読む先が `bind.steering_dir` に固定される）。**bind 不能時はどの steering が「関係する」かを判定する材料が無い**ので、markerless recovery を残す側に倒した（`design.md` L753「bind 不能 / 計測 / 新 hook は fail-open」と整合）。W-9 の欠陥は越境であって「binding が無いのに steering を読むこと」ではない。
     なお **「無関係 steering」は他 worktree だけの話ではない**。同一 worktree にも無関係 steering は存在しうる（RED fixture `20260901-unrelated` がまさにそれ）ので、bind 不能時の残余は § Consequences の 1 点目に書いたとおり残る。
  2. done guard を「推測で拾わない」にしたのは **stop を block する fail-closed 判断**だから（`design.md` § 主要フロー 3）。この 2 経路は (a) `[GDD #N]` の進捗表示、(b) markerless recovery の停止 fallback で、いずれも block 判断を持たない。`return ""` に倒すと markerless recovery が**無言で消える** ―― CH-5 の実測（active worktree 3 件中 1 件に binding なし）ではその 1/3 で復帰導線が失われる。
  3. 却下案「`return ""` に倒し、出荷済み 4 テストを書き換える」: テストを変えて GREEN にする形になり、しかも縮んだテストは静かに通る。AC-7 は満たせるが AC に無い既存挙動を落とす。

- **Consequences**
  - `_find_tasklist_text_for_progress()` / `latest_steering_resume_from()` は bind 不能時、current worktree に**別タスクの steering が複数ある**と名前の降順で 1 件目を採る（従来どおり）。bind 済みならこの曖昧さは無い。
  - `RESUME_FROM_PATTERN` を module level へ出した（`main()` 内の nested 定義のままだった）。読み取りループは呼び出し側が 1 箇所なので `latest_steering_resume_from()` に inline のまま残す。
  - `_bound_steering_file()` は `_worktree_toplevel()` で root を正規化するので、`latest_steering_resume_from()` の fallback も **サブディレクトリ起動で効くようになった**（旧実装は `root/.steering` 直下しか見ず、サブディレクトリ起動では markerless recovery が黙って効かなかった）。bind 経路は元から toplevel 正規化済みで、fallback だけが非対称だった。
  - `design.md` § 変更点 2 に非対称であることを明記した。次に読む人が「done guard と揃っていない」を欠陥と誤認して `return ""` へ倒すと、上記 4 テストが落ちる。


## ADR-9: 除外一覧の「所在」は worktree の絶対パスにする（design の basename から変更）

- **Context**
  design.md § 変更点 4 は AC-13 の「除外した重複の所在」を `<slug> @ <worktree basename>` で出すと
  書いていた。T-14 の実装時に、`find-stale-steerings.sh` の candidate ブロックが **base 時点から
  `worktree:    $WT`（絶対パス）を出している**ことを実測で確認した（`git show <base>:<script>` に
  `worktree:    $WT` が 1 行）。basename に縮めると、同じ slug が別 repo の同名 worktree に
  ある場合に採用側と除外側を突き合わせられない。

- **Decision**
  除外一覧の所在は **worktree の絶対パス**（`<slug> @ <worktree 絶対パス>`）にする。
  design.md § 変更点 4 の当該箇所を現在の正しい設計へ上書き更新した。AC-13 の本文（「所在が
  出力に残る」）は変更していない ―― 絶対パスは basename の上位集合で、AC が要求する述語を満たす。

- **Why**
  1. 同一ファイル内の既存出力契約（candidate ブロックの `worktree:` 行）と表記を揃えるほうが、
     採用された代表と除外された重複を突き合わせやすい。design の basename 指定は既存出力の
     実測に基づいていなかった。
  2. 判別力を実測している。除外の所在を basename に縮める変異（M8）は
     `test_same_slug_in_two_worktrees_yields_one_candidate` を kill する ＝ 絶対パスであることが
     観測されている（null 変異 control を先置きした変異試験。measurement 側の正本は
     `handoff/impl-t14.md` § 変異試験）。
  3. ADR-6 の advisory「候補一覧は絶対パス全体ではなく slug + worktree basename に留める」とは
     **面が違う**。あれは stop hook の warn 経路（`additionalContext` としてモデル / 端末へ注入
     される面）に対する指摘で、本件はローカル CLI の read-only レポートであり、同じレポートが
     base 時点から絶対パスを出している。

- **Consequences**
  - 除外行が長くなる。worktree の絶対パスがそのまま端末に出るが、これは base の candidate
    ブロックと同じ露出面で、本 task で新たに広げた面ではない。
  - design.md と実装の表記が一致したので、impl-gate / completion-check の AC Drift Check で
    basename との差分が偽陽性として上がらない。

## ADR-10: `--help` は行番号範囲ではなく先頭コメントブロックの機械抽出に変える（AC-15 の字句との緊張を human へ上げる）

- **Context**
  T-14 `#### Steps` 4 と design.md § 変更点 4 は「tracked 除外の副作用を `--help` に 1 行書く」ことを
  要求する。一方 AC-15 の字句は「`--registry` モードの既存出力契約 … と `--help` は不変」と書いている。
  さらに、base の `--help` は `sed -n '2,19p' "$0"` という**行番号 literal の範囲指定**で、実際には
  コメントブロックを越えて実行コード 3 行（`set -euo pipefail` 以下）を出していた（RED で観測）。
  行番号 literal のままコメントを足すと、範囲がずれて漏れがさらに増える。

- **Decision**
  `--help` を `awk 'NR > 1 { if ($0 !~ /^#/) exit; print }' "$0"` に変え、**先頭コメントブロックだけ**を
  機械的に出すようにした（範囲の終端に literal を持たせない）。design が後発かつ具体的なので
  design に従って tracked の記述も追記した。**AC-15 の字句は書き換えていない**。
  要件文をどちらに寄せるか（`--help` を「不変」から外すか、design を戻すか）は human 判断として
  impl-gate / HITL に上げる。

- **Why**
  1. 行番号 literal は「本文を 1 行足すたびに壊れる」形の依存で、この steering で繰り返し是正して
     きた規律（行番号 literal を持たせない）に真っ向から反する。範囲を実測すると
     `sed -n '2,Np'` は **N >= 20 で実行コードが漏れ、N <= 19 では漏れない**（測定時点の
     コメント行数に依存）。旧 literal `19` は、本 task でコメントを 4 行足した結果**たまたま**
     無害な側に留まっていただけで、次に 1 行足せば漏れる。
  2. AC-15 と design の衝突は本 task で発生したものではなく、design gate の M-6（「AC-13 と AC-15 が
     衝突しうる」）で既に認識されていた論点の延長。implementer が字句を書き換えると、人間が承認した
     前提を実装側の都合で動かすことになる。

- **Consequences**
  - `--help` の出力は base から 2 方向に変わる: (a) 実行コード 3 行の漏れが**なくなる**、
    (b) tracked 除外の副作用 4 行が**増える**。AC-15 の「`--help` は不変」の字句とは一致しない。
  - `--registry` の 6 列出力契約と既存 12 テストは不変であることを実測で固定した（AC-15 の残り）。
  - 要件文の字句訂正が未了のまま merge すると、completion-check の AC Drift Check で必ず上がる。
    human 判断を PR 前に取る必要がある。
  - **（2026-08-25 追記）本 ADR が上げた二択は closed**。ユーザーは「AC-15 を実挙動へ改訂する」を選択し、
    改訂の内容・理由・非緩和の実測は **ADR-11** と `requirements.md` § Correction Log（R1.2）が正本。

## ADR-11: AC-15 の `--help` 述語を「不変」から実挙動（内容 + 位置）へ改訂する

- **Context**
  ADR-10 が human へ上げた二択（`--help` を「不変」から外すか、design を戻すか）に対し、
  **2026-08-25 にユーザーが「AC-15 を実挙動へ改訂する」を選択**した。改訂対象は AC-15 の字句のみで、
  `Approved Direction` / 他 AC / 出荷済みコードは動かさない。

- **Decision**
  AC-15 を次の形へ改訂した（`requirements.md` R1.2）。`--registry` 側（6 列固定幅 / list only / exit 0）と
  「既存 12 テストが全て pass」は**そのまま残し**、`--help` の「不変」を **2 述語**に置き換える:
  **(a) 内容** = `--help` の出力に `tracked` の語を含む行が **1 行以上**あり、その行が AC-14 の副作用
  （tracked 運用 repo は stale 検出対象外）を述べている。**(b) 位置** = その記述はスクリプト先頭の
  コメントブロック内にあり、`--help` の出力は当該コメントブロックだけで構成される
  （非コメント行 ＝ 実行コードを **1 行も含まない**）。
  **AC の追加・削除は行わない**（総数 **26** / ID 集合 **AC-1〜AC-26** は改訂前後で不変。機械カウントで確認）。

- **Why**
  1. **原因は「design gate を通った設計意図が AC 側に反映されていなかった」こと**。
     `design.md` § 変更点 4 と `tasklist.md` T-14 `#### Steps` 4 は `--help` への 1 行追記を**明示要求**しており、
     実装はその承認済み計画に従っただけである。実装都合による AC の後追いではない。
  2. **当初「不変」と書いた理由も記録する**（将来この判断を読む人が、安易な緩和と区別できるように）。
     (i) AC-15 は `--registry` の回帰防止を目的に書いた AC で、`--help` は「利用者から見える面は一切動かさない」と
     1 文で言い切るための**巻き込み併記**だった。(ii) 起草時点で `--help` が `sed -n '2,19p' "$0"` ＝
     **行番号 literal**で実装され、先頭コメントブロックを越えて実行コードを出しうることを**実測していなかった**
     （「`--help` ＝ 先頭コメントの写し」という未検証の前提の上に「不変」と書いた）。(iii) tracked 除外の副作用を
     利用者に伝える必要があるという論点は requirements 起草より**後**の design review **M-6** で出た ＝
     「不変」はその論点を検討したうえでの決定ではない。
  3. **判定は緩んでいない**（実測）。base（`7f69caf`）の `--help` を改訂後の述語に当てると、
     (a) は出力 **18 行**中 `tracked` の語 **0 行**で**不合格**、(b) は非コメント行が **3 行**
     （`set -euo pipefail` / `THRESHOLD_DAYS=10` / `SEARCH_ALL_WORKTREES=0`）漏れるため**不合格**。
     出荷版（`726d9a2`）は出力 **17 行** / 非コメント行 **0** / `tracked` を含む行 **2 行**で合格。
     ＝ **旧字句「不変」を満たしていた実装が、改訂後の述語では落ちる**。
  4. 追記の**内容と位置**を分けて書いたのは、「1 行足した」だけでは位置（先頭コメントブロック内 ＝
     実行コードを漏らさない範囲）が固定されず、行番号 literal 依存の再発を防げないため。

- **Rejected Alternatives**
  - **design を戻す（`--help` に何も足さない）**: AC-14 の副作用（tracked 運用 repo が丸ごと検出対象外になる）を
     利用者が知る面が `--help` から消える。design gate（M-6）と ADR-10 が明示的に採った方向を、
     AC の字句都合で巻き戻すことになる。
  - **AC-15 から `--help` の言及を丸ごと削る**: 「不変」を外すだけの**純粋な緩和**になり、
     `--help` が何を出すかを誰も pin しなくなる。今回の改訂で最も避けたい形。
  - **`--help` の実装を `awk` から literal 範囲へ戻す**: ADR-10 の理由（本文を 1 行足すたびに壊れる依存）が
     そのまま復活する。旧 literal `19` が無害だったのは**たまたま**であることを実測済み。

- **Consequences**
  - 検証は **T-14 が既に出荷したテスト 2 本**が担う（`HelpOutputTests` の 2 method）。本改訂で**追加するテストは 0 本**。
    両テストが実際に発火することは positive control 変異（**X8b** = 先頭コメントから `tracked` を機械的に除去 /
    **X7b** = `--help` を `sed -n '2,20p'` へ戻す）で**それぞれ単独 KILLED** を確認済み（null 変異 control **X0b** で kill 0）。
  - `gdd-completion-check` の AC Drift Check は、改訂後の AC-15 と出荷挙動が一致するため上がらない。
  - 測っていない入力空間: `-h` 短縮形（同一 case 分岐だが別実行はしていない）、非 UTF-8 locale、
    `$0` が symlink 経由のときの出力。測定時点 2026-08-25 / 測定機 `/bin/bash` = GNU bash 3.2.57(1)-release。

## ADR-12: T-15 を「計画 3 本の新規テスト」から「L-11 hardening + 負の pin」へ振り替える

- **Context**
  T-15 の `#### Steps` 1 が計画していた新規テスト **3 本**は、T-14 が出荷したテストに**すべて包含**されている。
  そのままだと T-15 は**空タスク**になる。一方 T-14 impl-gate は新規欠陥 **L-11** を 1 件見つけている
  （`git ls-files --error-unmatch "$STATE_FILE"` が pathspec の glob 解釈を受け、slug に `? * [` が入ると
  **未追跡の別 steering を tracked として誤除外**する。方向は over-exclusion ＝ silent false negative）。

- **Decision**
  T-15 の本文を、**L-11 の 1 行 hardening（`-- ":(literal)$STATE_FILE"`）+ 負の pin テスト 1 本**へ振り替える。
  新規テスト 3 本の追加は**行わない**（増分 0 の pin を残さない）。`Files` に
  `scripts/find-stale-steerings.sh` が加わる **scope 変更**を伴う。AC binding（AC-13 / AC-14 / AC-15）は変えない。

- **Why**
  1. **包含関係を実測した**（申し送られた記述を owner が測り直す）。計画 3 本を字句どおりに再現した
     `test_t15_planned.py` と T-14 出荷テストを、**null 変異 control 先置き**の変異 **5 形**へ当てた結果、
     計画側が kill する変異は**全ペアで**出荷側も kill する（構造的支配）。逆向きには、
     出荷側だけが kill する変異が **3 形**ある（順序契約 / `--help` 2 述語）＝ **上位互換**。
     母集団・測定時点・測っていない空間は `tasklist.md` § Current Task § T-15 § 振り替えの根拠 に置く。
  2. **到達性が無い（Low）ものを直す判断の根拠**: (i) remediation が **1 行**で、
     出荷済み 22 テストの観測ベクトルを**変えない**（fixed 側でも 22 passed / 2 subtests を実測）＝
     直すコストと退行リスクがどちらも最小。(ii) 失敗モードが **silent false negative**（提案が黙って 1 件消える）で、
     W-10-3 の狙い（stale 検出の健全化）と**逆向き**。壊れても気づけない側の欠陥は、到達性が低くても
     気づける形（テスト）に変えておく価値がある。(iii) 到達不能性の根拠は **git の refname 規則**という
     **外部仕様**への依存で、GDD 側の slug 生成規約が変われば失われる。前提が外部にある不変条件は pin しておく。
     (iv) 代替（そのまま advisory として PR 本文に残す）を採ると T-15 が空タスクになり、
     `Execution Status` を空で `completed` にする形が残る。
  3. **判別力の増分は 1**（実測）。`:(literal)` の有無だけが異なる 2 ツリーで既存 **22 テストは両方とも 22 passed**
     ＝ 既存セットの当該述語に対する判別力は **0**。負の pin は **未修正で FAIL / 修正後に PASS** ＝ **増分 1**。

- **Rejected Alternatives**
  - **計画 3 本をそのまま追加する**: 上記の実測どおり増分 **0**。「増分 0 の pin は残さない」に反する。
  - **T-15 を削除する / `completed` にする**: 台帳上の task 総数と Stage の連続性が崩れ、
    L-11 の owner も失われる。
  - **L-11 を PR 本文の advisory のままにする**: T-15 が空タスクになるうえ、
    「到達性が無いから直さない」判断の根拠が pin されないまま残る。

- **Consequences**
  - T-15 の `Files` が 1 ファイル増える（`tests/` のみ → `tests/` + `scripts/find-stale-steerings.sh`）。
    `File Structure Map` の `scripts/find-stale-steerings.sh` 行の owner に T-15 を追記する。
  - reviewer selection は T-15 の scope が shell script 変更を含む形になるため、
    `gdd-security-reviewer` の再評価が必要（`Implementation Reviewer Selection` は既に `pending`）。
  - AC-13 / AC-14 / AC-15 の要求は変わらない。L-11 の修正は AC-14 の要求（tracked な steering を除外する）を
    **より正確に**満たす方向で、AC の緩和でも拡張でもない。


## ADR-13: `last-turn-failure.json` の key 集合は `project_root` を含む 5 キーを正とし、design 本文 3 箇所を是正する

- **Context**（T-17 impl-gate Attempt 1 / G-1。両 reviewer が独立に同一 finding へ到達）
  `project_root` は design review M-5 で後から追加されたが、design 本文の 3 箇所へ伝播していなかった。
  **実物を読んで確認した 3 箇所**（2026-08-25 時点の行番号。以後ずれるため literal に依存しない形で内容を併記する）:
  1. § enforcement point 1 の whitelist 記述 — 「payload の他フィールド（… `cwd` …）は読まない」と書きながら、
     `project_root` の導出には `cwd` が要る。
  2. § 論点 3「消費側の契約」の **shape 検証 key 集合** — 「`{error, error_details, session_id, timestamp}` の部分集合」。
     出荷 record は `project_root` を加えた **5 キー**。
  3. § Delivery Channel Rendering Check の**サンプル JSON** — `project_root` が無い。
  一方、同じ design の § 論点 3「project キーを持たせる（design review M-5）」と § Verification の
  「永続ファイルの `project_root` が current と異なるとき、注入も削除もされないこと（M-5）」は
  `project_root` 込みで書かれており、承認済み `tasklist.md` の T-17 / T-20 の `Produces:` も M-5 側と一致する。

- **Decision**
  **M-5 側（`project_root` を含む 5 キー）を正とする。** 実装は変えず、design 本文の上記 3 箇所を是正した。
  `tasklist.md` は変更しない（T-20 の `Produces:` は「shape 不正なら注入せず削除」としか書いておらず、
  key 集合を再掲していないため矛盾していない）。

- **Why**
  - 「tasklist が新しいから」ではなく、**design 内部で新しい節（M-5 / Verification）が古い 3 箇所を上書きしている**から。
    承認済み方針からの逸脱ではなく、design 本文の未反映。
  - 2 の記述は**元々 stale だった行**を、本差分が「5 キーを常時書く」ことで **load-bearing にした**。
    したがって this-diff 由来として T-17 で閉じるのが正しい。
  - 放置した場合の帰結が最も重い: T-20 が 2 を字面どおり実装すると、T-17 が書いた record は
    **1 件残らず shape 検証で落ちて「注入せず削除」される**。通知は出るので気づけず、record は毎回消えるので
    追跡の痕跡も残らない ＝ **AC-17 が例外もログもなく全損する**。

- **Rejected Alternatives**
  - **実装から `project_root` を外して 4 キーに戻す**: M-5 が塞いだ取り違え（project A の異常終了を
    project B の SessionStart が消費する）が再発する。§ Verification の M-5 検証項目も失われる。
  - **design を触らず T-20 のレビューで気づく前提にする**: 契約文書が矛盾したまま残り、
    「字面どおり実装すると壊れる」状態を次タスクへ送る。silent failure の作り方そのもの。

- **Consequences**
  - design の 3 箇所が M-5 と整合し、T-20 は shape 検証を 5 キーで実装する。
  - `project_root` を持つ record は `cwd` を読むため、enforcement point 1 の whitelist は 4 キー
    （`error` / `error_details` / `session_id` / `cwd`）。`cwd` は導出元としてのみ読み、記録には載せない。

## ADR-14: 通知（AC-16）は記録（AC-17）に従属させない

- **Context**（T-17 impl-gate Attempt 1 / G-10）
  初版実装は通知本文を「記録に成功した python 起動の stdout」でしか得られない構造にしており、
  書き込み失敗で通知も消えていた。この挙動はテスト（`test_unwritable_state_dir_fails_open`）が固定していた。
  **AC 本文を実物で読んで確認した**: requirements AC-16 は「通知コマンドが 1 回呼ばれる。
  **通知コマンドが存在しない環境では no-op**」であり、**no-op の条件は通知コマンドの不在だけ**。
  design § 論点 3 の fail-open は**永続ファイルの節**にあり、記録についての規定。

- **Decision**
  **AC-16 と AC-17 を独立にする。** 記録の成否にかかわらず通知本文を stdout に返し、
  非 0 で抜けるのは **payload を解釈できない場合だけ**にした。記録が落ちた場合は
  **失敗理由の型名だけ**を stderr に 1 行出す（payload 由来の断片は載せない）。
  design § 論点 3 の fail-open 記述に「通知を抑止しない」を明記し、テストの期待値も
  「記録は無い / 通知は出る / exit 0 / 理由が観測できる」へ改めた。

- **Why**
  - 逆方向（通知コマンド不在でも記録は残る）は既に独立が保証されていたのに、この方向だけ従属していた。
  - ディスクフル / read-only な `$HOME` / state dir が別ユーザ所有 といった**記録と無関係な事象**で、
    人間が異常終了に気づく唯一の即時シグナルが無症状で消える。
  - **AC が規定していない境界をテストコードで決めていた**。テストを現挙動に合わせたまま残さない。

- **Rejected Alternatives**
  - **現挙動を維持し design に「記録に失敗したら通知しない」と書き足す**: AC-16 の文面に無い制約を
    後から design 側で足す形になり、AC を狭める。人間承認の対象を実装都合で動かすことになる。
  - **`human_recheck_required` へ上げる**: AC-16 の文面（no-op 条件の明示）が十分に一意で、
    scope / policy の判断を必要としない。

- **Consequences**
  - 記録できない環境でも通知は出る。通知が出て record が無い状態は正常系として扱う（stderr に理由が残る）。
  - T-20（消費側）は「通知は出たが record が無い」ケースを異常として扱わない。

## ADR-15: `run-stop-failure-hook.sh` の fail-open は全称をやめ、射程を列挙で定義する

- **Context**
  T-17 impl-gate は Attempt 4 まで 4 ラウンド `changes_requested` を返し、その blocking の lineage は
  **G-8（記録が silent に消える）→ MED-1（guard が診断を握り潰す）→ MED-2（`|| true` がシグナルを捕まえない）→
  NEW-2（`trap` が 1 シグナルしか捕まえない）** の 4 連だった。毎ラウンド「1 つ外側の形」が見つかっており、
  gate は route を `human_recheck_required` へ上げた（`handoff/impl-gate-t17-attempt4.md` § 6）。
  根にあるのは実装コメント行 11 の全称 **「hook は決してターンを壊さない。どの経路でも exit 0（fail-open）」**。
  `SIGKILL` / `SIGSTOP` は trap 不能なので、**この全称はどんな実装でも達成できない**。
  **2026-08-26 にユーザーが「射程を明記して限定する」を選択**した。

- **Decision**
  1. exit 0 の射程を **(E) errno 経路 + (S) 既定環境で成立しうる trap 可能シグナル（実測で `SIGPIPE` のみ）** に限定し、
     **AC-16 本文（`requirements.md`）・hook のヘッダコメント・`lib/stop-failure-record.py` の docstring** の
     3 箇所に同じ射程を書く。
     （**ADR-17 で改訂**: (E) の粒度を「hook 自身の read / write」から「hook が扱う**データ**の I/O」へ絞り、
     **docstring 側は射程を複写せず正本ポインタに変えた**。射程の所在を 3 箇所に置く決定自体は維持）
  2. **射程外は「その他」で括らず、実測した形を個別列挙**し、それぞれの実測値と「既定環境で成立するか」を併記する。
     **実測値（rc 値）の正本は `requirements.md` § Correction Log の射程外表 1 箇所**とし、本 ADR / AC-16 本文 /
     hook ヘッダには複写しない（ADR-17。以前は 4 箇所に複写していた）。
  3. **NEW-2（`SIGXFSZ` / `SIGTTOU`）は閉じない**。`RLIMIT_FSIZE` は既定 `RLIM_INFINITY`、`TOSTOP` は新規 pty で
     既定 off（いずれも実測）で出荷リスクが小さく、閉じても「次の 1 形」を呼ぶだけだから。
  4. **MED-1 の診断（stderr へ 1 行）は残す**。silent に消える問題（G-8 / MED-1）を閉じた価値のほうが大きい。
     診断に伴うシグナル面は 1 と 2 の射程明記で扱う。
  5. 射程内は**面で機械検証する**。`test_in_scope_output_failures_all_exit_zero`（**18 subtests** ＝
     2 変位 × 3 失敗形 × 3 fd）を追加する。**出荷コードの挙動は 1 バイトも変えない**
     （`lib/*.py` の docstring 剥ぎ AST は `c9f3621` と完全一致）。

- **Why**
  1. **達成不能な全称が finding を生み続ける構造だった**。全称を掲げている限り、シグナルを 1 つ塞ぐたびに
     次の 1 つが「未閉鎖」として正当に指摘できてしまう。射程を列挙に変えると、
     「閉じた」も「閉じていない」も実測で判定でき、追いかけっこが止まる。
  2. **当初なぜ全称で書いたかも記録する**（安易な緩和と区別できるように）。(i) AC-16 は exit 0 の射程を
     規定しておらず、事実上の契約は実装コメント側にあった。(ii) 起草時の型空間は「判定不能 / コマンド不在なら
     no-op」という**制御フローの話**で、「hook 自身の write が原因でシグナル死する」経路を想定していなかった
     （反例を 1 つも実測せずに全称を書いた）。(iii) 「どの経路でも」は書き手には安全側の宣言に見えた。
     誤りだったのは、**強く書いても実装が強くなるわけではない**という一点。
  3. **判定は甘くなっていない**。改訂前の AC-16 は射程を無規定にしていたので、この改訂は
     「無規定 -> 検証可能な述語」の方向。改訂前の実装 `c9f3621` は改訂後の述語を **30 形中 2 形で満たさない**。

- **Rejected Alternatives**
  - **`trap '' PIPE XFSZ TTOU TTIN` に広げる**: 「1 形ずつ」を 4 形ずつに変えただけで、全称は依然として
    達成不能（`SIGKILL` / `SIGSTOP`）。加えて `SIGTTIN` を無視すると background 起動で read が
    `EIO` を返し続ける経路を新たに作る（**自分の修正が新たな破綻経路を作る**形の 5 回目になる）。
  - **診断（MED-1 remediation）を取り下げる**: G-8 / MED-1 が閉じた「記録も通知も stderr も 0 バイトで消える」を
    再び開く。射程外のシグナルは既定無効の設定を要するのに対し、silent 喪失は**既定環境で起きる**。
  - **`design.md` 側で fail-open を弱める**: 承認済み AC が射程を持たないまま design だけ動かすと、
    AC と design の食い違い（Attempt 1 で closed 済みの G-1 と同型）を再生産する。

- **Consequences**
  - 射程外の列挙は**既知の未閉鎖**として PR 本文の pre-existing / known-gap 欄へ送る（owner 未指名）。
  - 以後、この hook に write を足すときは「射程内か / 射程外か」を先に判定する。射程外なら閉じずに列挙へ足す。
  - AC-16 は subtests 18 形の機械検証を伴うため、`trap '' PIPE` の削除は CI で KILL される（変異 S6e で実測）。
  - AC 総数 26 / ID 集合 AC-1〜AC-26 は不変（機械カウントで確認）。

## ADR-16: 無防備な `source lib/kill-switch.sh`（NEW-1）は 14 hook 横断の別 PR に送る

- **Context**
  T-17 impl-gate Attempt 4 の **NEW-1**（`handoff/impl-gate-t17-attempt4.md` § 4-1）。
  `run-stop-failure-hook.sh` の `source "$SCRIPT_DIR/lib/kill-switch.sh"`（kill switch 読み込み）は無防備で、
  `lib/` を取りこぼす同期が起きると `set -e` により **rc 1** で死ぬ。
  その結果、記録 script 欠落の診断ブロック（MED-1 で足したもの）に到達しない。
  **2026-08-26 にユーザーが「別 PR へ送る」を選択**した。

- **Decision**
  **本 PR では直さない**。実測（形ごとの rc 値は `requirements.md` § Correction Log の射程外表 旧#9 が正本）と、
  **`set -euo pipefail` を持つ 14 hook 横断の pre-existing パターン**であることを、
  hook のコメント 1 行 + PR 本文の known-gap 欄に明記するに留める。
  **ADR-17 で追記**: NEW-1 は AC-16 の**射程外**（「プログラム本体の読み込み失敗」）として正本に明示列挙した。
  R1.3 の字句では (E) に文字どおり当てはまってしまい、「射程内なのに rc 1」という自己矛盾になっていた。

- **Why**
  1. **本 hook だけ塞ぐと 14 hook のうち 1 本だけ規約が割れる**。どう塞ぐか（`[[ -f ]]` guard / `|| true` /
     `set +e` 区間 / lib 側で自己申告）は 14 hook 共通の規約判断であり、T-17 の scope ではない。
  2. **実害は限定的**。Claude Code の hook 契約では exit 2 以外の非 0 は non-blocking error でターンは壊れず、
     診断も（bash 由来だが）出る（実測: stderr 257〜273 バイト）。
  3. 引き金は正常運用ではなく**不完全な配置**で、`d27e270` 以前から同型 ＝ **本 PR 由来ではない**。

- **Rejected Alternatives**
  - **本 hook だけ guard を足す**: 1 本だけ規約が割れる。かつ `source` の失敗を握り潰すと
    kill switch が効かないまま先へ進む経路を新設する（安全側ではない）。
  - **行 11 の不変条件を「ターンを壊さない」まで弱める**: ADR-15 で射程を列挙にしたので、
    弱める必要がない（NEW-1 は「射程内で rc 1」ではなく `set -e` による起動失敗として別立てにできる）。

- **Consequences**
  - PR 本文の known-gap 欄に **NEW-1（14 hook 横断・実測付き）** を明記する。owner は別 PR。
  - 本 PR の出荷差分は NEW-1 についてコメント 1 ブロックのみ（挙動変更 0）。

## ADR-17: 射程の (E) は「データ I/O」に限り、NEW-1 は射程外として明示列挙する

- **Context**
  T-17 impl-gate **Attempt 5**（Fix Attempts 5/5 ＝ hard cap ラウンド）の唯一の blocking **MED-A**。
  ADR-15 で導入した射程のうち **(E)「hook 自身の read / write が errno で失敗し `set -e` が非 0 に倒す経路」**は、
  **同一 commit が実測して記録した NEW-1（`source lib/kill-switch.sh` の `ENOENT` ＝ rc 1）を字句どおり含む**。
  しかも ADR-15 Decision 2 が「射程外は個別に列挙する」と宣言しているのに、NEW-1 はその列挙にいなかった。
  ＝ **契約文言が同一 commit の実測に反証されている**（`handoff/impl-gate-t17-attempt5.md` § 6-1）。
  gate は Reviewer Loop Escape Hatch の分岐を **procedural / evidence only** と判定しており、
  **policy / scope / ownership / security boundary / prompt-output contract はいずれも変えない**。

- **Decision**
  1. **(E) の粒度を「hook が扱う**データ**の I/O」に絞る** —— stdin からの payload の read /
     stdout・stderr への write / 記録先（state dir・record file）への write。
     **プログラム本体（`lib/` 配下のスクリプト）の読み込み失敗は (E) に含めない**。
  2. **射程外表に「プログラム本体の読み込み失敗」（NEW-1）の行を足す**。**案 1 と案 2 を併用する**
     （片方だけでは、NEW-1 が「射程内でもなく射程外の列挙にもいない」宙吊り、または
     「(E) の字句と射程外表が同じ形を両側に持つ」矛盾のどちらかが残る）。
  3. **射程外の完全性主張を撤回する**。射程外は射程内の補集合なので列挙で尽くせない。
     完全性を主張するのは `write(2)` / `read(2)` が生成しうるシグナル **4 形**についてだけ。
  4. **実測値（rc 値）の正本を `requirements.md` § Correction Log の表 1 箇所に寄せる**。
     AC-16 本文 / ADR-15 / hook ヘッダ / `lib` docstring からは数値と列挙の複写を落とし、正本を指す。
     ADR-15 Decision 1 の「3 箇所に同じ射程を書く」は**射程の所在**についての決定なので維持し、
     `lib` docstring は「この write は射程内 (E) に入る」+ 正本ポインタに変える。
  5. **行番号引用をやめ、節見出し参照に置換する**（`design L310` -> `design § 論点 3 / 消費側の契約`、
     `design L302` -> `design § 論点 3 / permission`）。**出荷コードの挙動は変えない**。

- **Why**
  1. **境界の切れ目が実測の切れ目と一致する**。データ I/O は面 30 形 + 個別 9 形（`ENOSPC` 含む）で全て rc 0、
     非 0 になったのは `source` の失敗だけ。粒度を絞った (E) は「測った述語」と「書く述語」が一致する。
  2. **判定は緩んでいない**。改訂前の実装 `c9f3621` が落ちる 2 形は**いずれも stderr へのデータ I/O 由来**なので
     R1.4 の述語でも射程内 ＝ **28/30 で不合格のまま**。粒度を絞っても不合格判定は動かない。
  3. **数値の複写は drift の口**。1 箇所直すと残りが黙って古くなる（現に本 commit は自分で行番号引用を 3 箇所壊した）。
  4. **ユーザー判断 (a) (b) (c)（2026-08-26）は動かしていない**。NEW-1 を本 PR で直さない決定（(b)）を、
     AC の射程分類に**書き写した**だけで、方針そのものの再検討ではない。

- **Rejected Alternatives**
  - **NEW-1 を本 PR で塞ぐ**: ユーザー判断 (b)（別 PR）に反する。かつ複数 hook 横断の規約が本 hook だけ割れる（ADR-16）。
  - **案 1 のみ / 案 2 のみ**: 上記 Decision 2 のとおり、どちらか一方だと別の形の自己矛盾が残る。
  - **(E) を「hook 自身の I/O」のまま、NEW-1 を「例外」と注記する**: 「その他」で括らない規律に反し、
    次に同型の形が出たとき例外が増える（追いかけっこの再開）。
  - **射程外表から実測値を消して簡素化する**: 「未閉鎖であることを実測値付きで明記する」という AC-16 の要求を弱める。

- **Consequences**
  - 射程外は**列挙で尽くせない**ことが正本に明記されたので、「射程外に無いから射程内」という読み方はできなくなる。
    射程内は (E) (S) の positive な定義側だけで決まる。
  - rc 値を書き足すときは `requirements.md` § Correction Log の表に足す。他所へは複写しない。
  - 以後、この hook / lib に I/O を足すときは「データ I/O か / プログラム本体の読み込みか」をまず判定する。
  - AC 総数 26 / ID 集合 AC-1〜AC-26 は不変（機械カウント）。出荷コードの挙動変更 0。

## ADR-18: hook の実測基盤に「環境（bash 版数 / OS）」の軸を入れ、`run-notification-hook.sh` にも `trap '' PIPE` を足す

- **Context**
  T-18 impl-gate **Attempt 1** の唯一の blocking **MED-T18-A**（ops-blocking Medium）。
  出荷ヘッダは「本 hook には SIGPIPE の**発生源が無い**」ので `trap '' PIPE` を足さない、と書いていた。
  根拠は fd 破壊 18 形の実測（全形 rc 0）だが、**18 形は bash 3.2.57 / macOS でしか測られていない**。
  gate が bash 5 で測り直すと、**payload に NUL が 1 バイト混じるだけ**で bash 自身が fd 2 に警告を書き
  （`PAYLOAD="$(cat 2>/dev/null || true)"` の `2>/dev/null` は `cat` の stderr にしか掛からない）、
  fd 2 が読み手の消えた pipe なら hook は **SIGPIPE で死ぬ**。
  これは AC-16 の **(S)**「hook 自身の write が原因で届き、追加の資源制限・端末設定なしの既定環境で
  成立しうる trap 可能シグナル」に**そのまま当てはまる ＝ 射程内**であり、射程外へ逃がせない。
  ＝ ADR-15 / ADR-17 で 4 ラウンドかけて閉じた「契約文言が同一 commit の実測に反証される」欠陥が、
  **プラットフォーム軸という新しい抜け方**で 2 本目の hook に再発した（`handoff/impl-gate-t18-attempt1.md` § 5）。

- **Decision**
  1. **`run-notification-hook.sh` にも `trap '' PIPE` を 1 行足す**（sibling と同形）。
     「発生源が無い」という根拠文は**偽なので書き換える**。実装だけ直して根拠を残すと逆立ちしたままになる。
  2. **hook の射程実測には「環境」を入力空間の 1 軸として明示的に振る**。
     最低でも **bash 3.2.57 系（macOS 既定）と bash 5 系（主要 Linux ディストリ既定）の両方**を通す。
     **測った環境（bash 版数 / OS / 測定時点）を記録に明記する**。
  3. **射程外を再列挙するときは、正本（`run-stop-failure-hook.sh` 冒頭の 5 群）との差分 0 を機械検証する**。
     「同じ」と書くだけの再列挙は許可しない（Attempt 1 は第 2 群まるごと + 第 4 群の半分を落としていた）。
     本 PR では `test_out_of_scope_enumeration_matches_sibling` が識別子トークン集合の一致で pin する。
  4. **「stdout / stderr へ 1 バイトも書かない」は hook 本体についての主張に限定する**。
     解釈器の bash が fd 2 に書く形が実在するため（NUL 警告 ＝ 射程内 / `RLIMIT_FSIZE=0` の SIGXFSZ 報告 ＝ 射程外第 2 群）、
     プロセス全体についての無条件の全称としては書かない。

- **Why**
  1. **環境は入力空間の 1 軸である**。同じ payload・同じ fd 構成でも、bash 3.2.57 は無言・bash 5 は 104〜110 バイト
     という**観測できる差**があった。1 環境だけで測った「全形 rc 0」は、入力空間の 1 軸を固定した条件付きの主張にすぎない。
  2. **本 hook は Linux を明示サポートしている**（`notify-send` 分岐）。bash 5 は主要 Linux ディストリの既定 bash なので、
     測っていない環境が「出荷先の既定環境」だった。
  3. **引き金が untrusted payload の中身**（NUL 1 バイト）であり、運用者の異常な設定を要しない。
     AC-18 が求める「no-op で exit 0」の姿勢と、hook 自身が掲げる不変条件の両方から外れる。
  4. **`trap '' PIPE` は実際に効く**（rc 141 -> rc 0 を 3 環境で実測）。「効かないから足さない」でもない。

- **Rejected Alternatives**
  - **射程外の列挙に書き足すだけで閉じる**: 不可。反例は AC-16 の (S) が**射程内**と定義した領域に実在するので、
    射程外へ逃がすと今度は AC-16 と矛盾する。
  - **`PAYLOAD="$(cat)"` の書き方を変えて NUL 警告そのものを消す**（例: `2>/dev/null` をコマンド置換の外へ、
    または `cat` を使わない読み方へ）: 警告の抑止は bash 5 の NUL 経路 1 つしか塞がず、同じ class の
    「解釈器が fd 2 に書く」形（SIGXFSZ 報告）が残る。`trap '' PIPE` は fd 2 への write 起因の SIGPIPE を
    書き手に依らず閉じるので、1 行で広く効く。
  - **契約テストを bash 5 でしか動かさない / macOS では skip する**: 開発機（macOS）で常に緑になる skip は
    「測っていない」ことを隠す。**見つかった bash を版ごとに全部通す**形にして、環境の有無を記録に出す。
  - **18 形すべてを bash 5 でも出荷テストに pin する**: `trap` の有無で結果が変わらない面（実測: 18 形 x 2 版とも
    non-zero 0）なので、**判別力の増分が 0 の pin** になる。harness 実測に留め、pin は判別力のある 1 形に絞る。

- **Consequences**
  - 以後、hook の「射程」「全称」「rc 0」を記録するときは、**測った環境（bash 版数 / OS / 測定時点）を必ず併記する**。
    併記の無い実測値は「1 軸を固定した条件付きの主張」として扱う。
  - **他の hook にも同じ測り漏れが無いかを見る**のは carry-forward **GATE-T18-1**（owner T-23）。
  - `run-notification-hook.sh` の出荷差分は `trap '' PIPE` **1 行 + コメント / ヘッダの記述**のみ。
    allowlist・通知経路・出力契約（stdout 空）は 1 バイトも変えない。
  - 契約テストは 20 -> **22 本**。増えた 2 本はいずれも**単独で殺せる変異がある**
    （trap 削除 / 射程外列挙からのトークン脱落）。数値の正本は `tasklist.md` § T-18 § Attempts § Attempt 1 remediation。


## ADR-19: 「使えない記録」は例外なく fail-closed で削除する ―― 空 `project_root` を `MISMATCH` から `INVALID` へ

- **Context**（T-20 impl-gate Attempt 1 / M-3。gate が書き手から end-to-end で独立再現）
  `last-turn-failure.json` の読み手（`run-session-start-hook.sh`）は、記録を 3 クラスに分けていた ——
  `OK`（注入して削除）/ `MISMATCH`（**注入も削除もせず残す**）/ `INVALID`（注入せず削除 ＝ fail-closed）。
  `project_root` が空文字の記録は `MISMATCH` に分類されていた。
  `MISMATCH` が「残す」なのは、**他 project のセッションで消費されないようにするため**であり、
  「ユーザーがその project に戻れば消費される」ことが前提になっている。
  ところが `""` は `realpath("")` がどの cwd にも化けるため early reject され、
  **どの project の toplevel とも一致しえない** ―― 前提が成立しない唯一のクラスだった。
  帰結は (a) AC-17 の「次セッションで報告」が **silent に落ちる**、
  (b) 記録が無期限に残り、**すべての project の SessionStart が毎回 `git rev-parse` + `python3` の
  起動コストを払い続ける**（次の失敗で上書きされるまで）。
  **到達可能性は理論ではない**: 書き手 `lib/stop-failure-record.py::_project_root()` は
  payload の `cwd` が空 / `not os.path.isdir(cwd)` のとき `""` を返す。
  ターン中に worktree が消える形は、**この GDD workflow 自身が merge 時に行う操作**。
  実測（remediation 前）: 書き手 hook -> 読み手 hook を 3 連続起動して
  `marker=0 / record_still_there=YES` が 3 回とも再現。

- **Decision**
  **空 `project_root` は `INVALID`（注入せず削除）に分類する。** 誤一致防止（early reject）はそのまま、
  fail-closed 削除だけを加える。`design.md` § 消費側の契約 に分類規則として明記し、
  出荷テストを「注入しない / **削除する**」へ反転した
  （`test_empty_project_root_is_rejected_and_deleted`）。
  規則としては **「どのセッションからも消費されえない記録は、残さず削除する」** ―― 本 diff の他の
  不可用クラス（不正 JSON / 非 object / キー過不足 / 非 str / 記録ファイルが symlink）は
  すべて fail-closed 削除で、**ここだけが例外だった**。

- **Why**
  - この repo の規律「**silent に失敗する経路を残さない**。fail-closed にできないなら観測可能にする」に対し、
    空 `project_root` は **fail-closed にできる**（誤一致の心配は early reject が独立に閉じている）。
  - 「残す」の価値は**将来消費される可能性**にある。可能性が構造的に 0 なら、残すことに価値はなく
    コストだけが残る。

- **Rejected Alternatives**
  - **書き手側で `""` を書かないようにする**: 書き手の変更は T-17 の scope で、diff 外。かつ読み手は
    「同一ユーザ権限の任意プロセスが書ける」前提の fail-closed reader なので、**書き手を直しても
    読み手側の分類は必要**（防御の位置が違う）。
  - **TTL で掃除する**: 時間軸の限定は A-T20-S3 として別に残っている論点で、`MISMATCH` 全体の設計判断。
    本件は「そもそも消費されえない」クラスの話なので、TTL を待つ理由がない。
  - **観測可能にする（stderr に 1 行出す）**: SessionStart の stderr はユーザーの目に触れない経路で、
    「観測可能」の実体にならない。fail-closed にできる以上、そちらを採る。

- **境界（どこまでを「消費されえない」とみなすか）**
  **`""`（構造的に不可能）だけを削除対象にし、`/gone/worktree` のような「今は存在しないパス」
  （偶発的に不可能）は `MISMATCH` のまま残す。** 前者は `realpath("")` がどの cwd にも化けるため
  **どの入力でも一致しえない**が、後者は worktree の再作成やボリュームの再マウントで
  **将来一致しうる**。存在しないパスの記録が長期滞留する問題は**時間軸の話**で、
  TTL（**A-T20-S3**）が担当する。この境界を明記しないと、次の読み手が「不整合」と読んで
  削除範囲を広げ、一時的に消えたパスの失敗報告まで捨ててしまう。

- **Consequences**
  - `MISMATCH`（残す）の意味が **「別 project で消費されうる記録」** に純化された。
    以後 `MISMATCH` を増やすときは「**そのクラスは本当に将来消費されうるか**」を判定条件にする。
  - 変異 `empty_root_to_mismatch`（この決定を元に戻す向き）は KILLED ＝ 判別力あり。
  - **同じ「永久に消費されない記録」を作る経路がもう 2 本**あることが変異の数え直しで判明し、
    どちらも出荷テストで塞いだ（実測の正本は `handoff/tdd-t20.md` § 4-A-3）。
    (a) **5 キーと同名の文字列を並べた JSON 配列** —— object 検査を外すと python が落ち、
    読み手は「解釈不能」として注入も削除もしない。(b) **書き手の `not os.path.isdir(cwd) -> ""`
    分岐の欠落** —— 記録が「存在しないパス」を持って `MISMATCH` 側へ回る。
  - **規則**: 「解釈不能 ＝ 無音 no-op」は **python3 不在のような環境要因にだけ**許す。
    **記録の内容が原因の解釈不能は `INVALID`（削除）に倒す。**


## ADR-20: 承認済み design の字句は「後続タスクが写経しても壊れない形」で保つ

- **Context**（T-20 impl-gate Attempt 1 / M-1）
  `design.md` § 消費側の契約 に 2 つの食い違いがあった。
  1. **shape 検証の受理面**: design は「key 集合が 5 キーの**部分集合**」、出荷は **完全一致**。
     出荷の方が安全（部分集合だと `project_root` 欠落時に `realpath("")` が cwd へ化けて誤一致する）
     なので**バグではない**が、承認済み artifact と出荷が食い違ったまま残っていた。
  2. **symlink 拒否のスニペット**が `[[ -L "$f" ]] && { rm -f "$f"; exit 0; }`。
     **字句どおり実装すると SessionStart が JSON を 1 個も出さずに終了**し、
     同じ design の § enforcement point 3b-2「出力は常に JSON 1 個」と自己矛盾する
     （compact auto-resume・post-merge 継続・active steering reboot がそのセッションでまとめて死ぬ）。
     implementer は正しく loader 内の `return 0` にしたが、**`tests/test_hook_injection_security_contract.py`
     を書く T-24 はこの design 文言を参照して書かれる** ＝ **live trap**。

- **Decision**
  **出荷実装を正とし、`design.md` の字句を出荷へ合わせる。**
  (a) 「部分集合」-> **「完全一致（5 キー）」**、(b) スニペットの `exit 0` -> **`return 0`** ＋
  「**`exit` にしてはならない / 記録を読まないことと hook が何も出力しないことは別**」の明文化、
  (c) 5 キー硬結合の帰結として **「記録スキーマの変更は書き手と読み手を同一 PR で更新する」** を追記、
  (d) 一致判定を `os.path.realpath` 正規化後に行う規約（D-5）を § project キーを持たせる に追記。

- **Why**
  - 「計画コードを写経しない」は実装者側の規律であって、**計画側が罠を置いてよい理由にはならない**。
    後続タスクが字句どおり実装しても壊れない形にしておくのが、承認済み artifact の責務。
  - 硬結合（5 キー完全一致）は**安全だが脆い**。片側だけ field を足すと古い読み手は
    **全記録を `INVALID` と判定して削除する**（部分読みにはならない）。この帰結は明文化に値する。

- **Rejected Alternatives**
  - **実装を design（部分集合）へ戻す**: 誤一致の穴が開くので不可。
  - **design はそのままで T-24 の計画コードだけ直す**: 同じ字句を参照する将来の読み手が同じ罠を踏む。
    正本を直さない限り再発する。
  - **AC / scope を触る**: 触っていない。受理面の**記述**を実装へ合わせただけで、AC-17 の 3 段
    （記録 -> 注入 -> 消費）は不変 ＝ `design_detail_only` の範囲内で、re-entry gate は不要。

- **Consequences**
  - **書き手と読み手のスキーマ結合が明文化された**。以後 `last-turn-failure.json` に field を足す変更は
    同一 PR で両側を更新する。変異 `writer_extra_key` / `writer_ts_format` が
    `CrossHookContractTests` に KILLED されるため、**片側だけの変更は出荷テストが落とす**。
  - 読み手にも書き手と同じ **state ディレクトリの symlink 拒否**を入れた（A-T20-S1）。
    design § 消費側の契約 に規約として追記済み。
