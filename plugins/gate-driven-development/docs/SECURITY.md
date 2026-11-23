# SECURITY（セキュリティ境界と情報取り扱い）

> **対象**: GDD plugin を導入するチームのテックリード・セキュリティ担当
> **目的**: plugin の各コンポーネントが「何を読み、何を書き、どこと通信するか」を明示し、導入リスク評価を可能にする
> **上位正本**: `references/common-guardrails.md` § .steering artifact の正本性 / § Honest Limitations
> **この文書の位置付け**: セキュリティ観点で GDD を評価する際のリファレンス

---

## セキュリティ境界の全体像

```
┌─────────────────────────────────────────────────────────────┐
│ User Terminal (Claude Code / Cursor / Codex)                │
│  ├─ /gdd-dev input ─────┐                                   │
│  └─ stdout to user ─────┘                                   │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────▼────────┐
       │ GDD plugin     │
       │ (read/write)   │
       └───────┬────────┘
               │
    ┌──────────┼──────────────────────────────┐
    │          │                              │
    ▼          ▼                              ▼
┌───────┐  ┌──────────┐               ┌─────────────┐
│ hooks │  │ .steering│               │ reviewer    │
│       │  │ artifacts│               │ subagents   │
└───┬───┘  └──────────┘               └──────┬──────┘
    │                                        │
    ▼                                        ▼
┌─────────┐                          ┌──────────────┐
│ stderr  │                          │ LLM API      │
│ stdout  │                          │ (Anthropic   │
│ filesys │                          │  / OpenAI)   │
│ GitHub* │                          └──────────────┘
└─────────┘
```

\* hook が GitHub に出るのは、PR 後の push の案内が `gh pr view` で PR の有無を読むときだけ（§ 4・§ 通信境界）

---

## コンポーネント別の権限境界

### 1. Skill（GDD フェーズ）

| 項目         | 範囲                                                                                                                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **読み取る** | `.steering/<task>/` 配下、対象リポジトリのソースコード、CLAUDE.md、ユーザーの会話履歴                                                                                                    |
| **書き込む** | `.steering/<task>/` 配下（requirements.md / design.md / tasklist.md / state.md / worklog.md / adr.md / findings.md）、`<repo-root>/docs/learned-patterns.md`（採用済みの repo だけ）、リポジトリのソースコード（実装フェーズのみ） |
| **通信する** | LLM API 経由のみ（ホスト環境の設定に依存、skill 自体は外部通信しない。hook の例外は § 4）                                                                                                                  |
| **権限**     | Claude Code / Cursor / Codex の Tool 権限に従う（Read / Edit / Write / Bash / Grep / Glob / connector / app tool 等）                                                                     |

### 2. Reviewer Agent（4 種類）

| Agent                         | 読み取り範囲                                     | 書き込み権限                            | 起動条件                                    |
| ----------------------------- | ------------------------------------------------ | --------------------------------------- | ------------------------------------------- |
| `gdd-planning-reviewer`       | `requirements.md` / `design.md` / 関連既存コード | なし（findings を呼び出し元に返すだけ） | requirements / design gate                  |
| `gdd-implementation-reviewer` | `tasklist.md` / 実装差分 / テスト / 既存コード   | なし                                    | implementation gate                         |
| `gdd-security-reviewer`       | 同上 + secrets / auth 関連コード                 | なし                                    | 認証・PII・untrusted input がスコープの場合 |
| `gdd-completion-reviewer`     | steering 全体 + 全実装差分                       | なし                                    | standard タスクの completion check のみ     |

**境界**:

- reviewer は **read-only**。ファイルの編集は行わない
- findings は親 skill に返され、親 skill が `state.md` / `tasklist.md` に記録する
- reviewer が読むのは**導入先リポジトリのコードと `.steering/` の内容のみ**。ホスト外リソースは読まない

### 3. Subagent（gdd-subagent-driven-implementation が起動）

| 項目                         | 範囲                                                                       |
| ---------------------------- | -------------------------------------------------------------------------- |
| **起動元**                   | `gdd-subagent-driven-implementation` の controller（メインセッション）     |
| **読み取り**                 | task に関連するファイルのみ（controller が prompt で明示）                 |
| **書き込み**                 | task が指定する範囲のソースコード                                          |
| **並列性**                   | 最大 3 並列（standard タスクの independent batch）                         |
| **tasklist.md 書き込み禁止** | subagent は `tasklist.md` を直接編集しない（controller の責務）            |
| **戻り値**                   | `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` の 4 値 status |

**境界**:

- subagent は独立コンテキストで動作し、controller の会話履歴は見えない
- subagent から子 subagent を起動する再帰呼び出しは行わない（controller 経由のみ）
- subagent の出力は controller が独立検証する（`verification-before-completion` 原則）

### 4. Hook（4 種類）

| Hook               | 読み取り範囲                                                         | 書き込み先                                 | タイミング                        |
| ------------------ | -------------------------------------------------------------------- | ------------------------------------------ | --------------------------------- |
| `SessionStart`     | `.steering/*/state.md` / `tasklist.md`、state dir の `last-turn-failure.json` | systemMessage（LLM 注入用）、`last-turn-failure.json` の削除（同じ project の記録か、壊れた記録・symlink のとき。compaction の直後は除く） | session 開始時                    |
| `SessionStart`     | payload の `transcript_path`・`source` | `$CLAUDE_ENV_FILE`（git の設定による pre-push hook〔`GIT_CONFIG_*`〕と transcript のパス。パスが安全な文字だけのときに書く）、パスが安全な文字だけでなく書かなかったときは、state dir の `push-review.log` に 1 行（`source` が compact のときは書かない） | session 開始時（compact・resume を含む） |
| `PreToolUse`       | `.steering/<active>/requirements.md` + `tasklist.md` | systemMessage（Goal + AC 注入）、deny 応答 | Write/Edit 実行直前 |
| `PreToolUse`       | `.steering/` への書き込みの中身、書き込み先の steering ファイル（書き込み前と、Write・Edit・MultiEdit を当てた後の `state.md`）、同じ steering の `requirements.md`・`tasklist.md`・`design.md`（advisory の lint）、payload の `transcript_path` の transcript（直近の実会話のターンが peer か）、state dir の連続 deny の counter | deny 応答、systemMessage（advisory の lint）、additionalContext（自走上限と `Human Check Status` の evidence の値を 80 文字まで引用し、自走のマージに入らない理由を返す）、state dir の連続 deny の counter | Write/Edit/MultiEdit/ApplyPatch 実行直前 |
| `PreToolUse`       | `.steering/*/state.md`                                               | deny 応答                                  | EnterPlanMode・EnterWorktree 実行直前（GDD session 中だけ止める） |
| `PreToolUse`       | Skill の名前、`.steering/*/state.md`                                 | deny 応答、additionalContext（gate の skill の dispatch の案内） | Skill 実行直前 |
| `PreToolUse`       | Agent の `subagent_type`・`model`、`.steering/*/state.md`、background-dispatch-gate は Agent の `run_in_background`・payload の `agent_id`、git の toplevel、`.claude/gdd-dev.local.md` | additionalContext（model の警告。block しない）、deny 応答（main からの gdd-formal-gate-runner の同期の起動）、`.gdd/hook-errors.log`（読めない payload・判定の例外） | Agent 実行直前 |
| `PreToolUse`       | Bash のコマンド文字列と `run_in_background`、`.claude/gdd-dev.local.md`（root-branch guard は、その `session_id` を payload の `session_id` と hook のプロセスの環境変数 `CLAUDE_CODE_SESSION_ID` に照合する）、`.steering/*/` の state・証跡、git の状態、state dir の PR 台帳と、台帳に載った worktree の `.steering/*/state.md`、root checkout と各 worktree の `.gdd/tasks/*/binding.json` と、それが指す `state.md`（merge gate）、push 先 branch の PR の有無（`gh pr view`） | deny / block 応答（root-branch guard・background の待ちのループの deny）、additionalContext（PR 後の push の案内、merge gate・pre-PR gate・pre-push gate の実行後の通知）、state dir の PR 台帳・ログ・PR の有無のキャッシュ | Bash 実行直前 |
| git の `pre-push`（SessionStart が差し込む） | git が渡す remote の名前・URL と stdin の ref、remote の `pushurl`・`url`、session の transcript の全体、push する commit の時刻と履歴、レビュー時点の commit の `.gdd-config.md`、push 先 branch の open の PR の数（`gh pr list`） | state dir の `push-review.log` | git push の直前（log-only。push は止めない） |
| `UserPromptSubmit` | `.steering/<active>/`                                                | systemMessage（AC 詳細注入）               | ユーザー入力送信時                |
| `Stop`             | assistant の直近出力、`state.md`                                     | systemMessage（Handoff 警告）、block 応答  | LLM 応答完了時                    |

**境界**:

- hook は shell/Python で書かれ、**外部通信しない**（ファイルシステム操作と stdout/stderr 出力のみ）。例外は、PR 後の push の案内（`run-review-followup-nudge-hook.sh`）が push 先 branch の PR の有無を `gh pr view` で、git の pre-push hook（`git_pre_push_review.py`。SessionStart の hook が差し込む）が push 先 branch の open の PR の数を `gh pr list` で GitHub から読むことだけである（利用者の `gh` の認証を使う読み取り。GitHub へは書き込まない。後者は remote が github.com のときだけ呼ぶ）
- hook は state dir（`~/.claude/.gdd-hook-state/`。`GDD_HOOK_STATE_DIR` で変えられる）に次を書く。PR 台帳・ログ・キャッシュのファイル・`last-turn-failure.json` は `chmod 600`、キャッシュのディレクトリは `chmod 700` にする。deny の counter は chmod せず、umask のまま作る（通常は 0644）。state dir 自体も umask のまま作り、`last-turn-failure.json` を書くときは `chmod 700` にする。push review の hook が state dir を新しく作るときは 0700 で作る
  - `gdd-pr-roots`：pre-PR gate が、active GDD で `gh pr create` を検査したときの GDD worktree の root を **絶対パスの平文**で 1 行ずつ追記する PR 台帳。merge gate が、対象 PR が GDD の PR かを照合するために読む
    - 限界：台帳に載るのは、pre-PR gate が root の marker を見て検査したときだけである。marker は `/gdd-dev` を始めた root にだけ作られ、通常の GDD worktree には無い。そのため `cd <GDD worktree> && … gh pr create` の形で移動先に marker が無いと、pre-PR gate は marker の判定より後の検査すべて（completion-check・PR body の機密の検査・ADR・Codebase Health・`--head` の照合・steering の一意性・自己レビューと独立レビューの証跡など）をせずに通し、台帳にも書かない（その前にある raw task steering の検査は、base branch を解決できるときだけ走る）。同じ形の `cd <GDD worktree> && … git push` でも、pre-push gate は移動先に marker が無ければ証跡を検査せずに通す。台帳に載っても、state.md に `PR URL` が無ければ照合で当たらない。merge gate は台帳より先に、`gh` の実行先の repo の binding（root checkout と各 worktree の `.gdd/tasks/*/binding.json`）が指す state.md の `PR URL` を対象 PR と照合し、1 件だけ当たればその GDD worktree の証跡で検査する。binding を引くのは、対象 PR を番号か URL で明示し、hook が root を決められ（セッションの cwd が repo の中、または cd 先・payload の cwd に marker がある）、実行先の git repo を決められる merge である（root・GDD worktree・同じ repo の別 worktree のどこから打っても同じ binding を引く）。例外として、marker のある root からの、対象を repo つきで明示した merge は、実行先を決められなくても root の repo の binding を引く。次の merge は binding を引かない。実行先が git の外か決められない merge（cwd が git の外のセッション〔marker の無い GDD worktree へ cd しても同じ〕、`cd "$X"` など）、番号だけの merge で `gh` が origin の repo を選ぶと決まらないとき（remote が origin だけで `gh repo set-default` が無いか、origin が set-default であるとき以外）、番号だけの merge で cd 先が元の cwd と別の repo のとき（`cd X && gh pr merge 7`・`cd X & gh pr merge 7` など）、対象を省いた・決められない merge、`GH_REPO`・`GH_HOST` を設定した merge。state.md を worktree の `.steering/` の下に持たない binding は当たりにしない。binding でも台帳でも外れた GDD の PR の merge は、次のときに証跡を見ずに通る。root に marker が無いとき（root の steering に対象 PR があっても読まない）、root を決められず GDD の外と判定できたとき、marker のある root の steering が対象 PR を記録していないとき（reason code `state-unreadable`・`pr-url-unrecorded`・`steering-ambiguous`・`untrusted-root-unverified`・`pr-target-unresolvable` など、理由つきで通知する場合と、自セッションが所有する active な marker の下で steering の証跡を検査する場合を除く）。GDD はこの経路でマージの承認を検査しないので、承認は導入先の運用（人がマージを決めるなど）で担保する。逆に台帳で当たった PR は、binding が対象 PR の steering を指さず、marker を持つ場所の無いセッションからは、案内どおり GDD worktree へ cd しても同じ照合で通知が出る（merge は止まらない）。PR 作成時・push 時の検査の素通りは、直さずに受け入れた限界である（旧#431 で閉じた）。PR 作成時について実測すると、pre-PR gate・pre-push gate の root の選び方を merge gate にそろえる案も、GDD worktree にも marker を書く案も、completion-check を受けずに作られた PR をほとんど止めないと見込まれた。別のセッションが作った worktree から、さらに別のセッションで打つ形は、marker を使うどの案でも止まらない。push 時の素通りで失ったものは測らずに受け入れた。completion-check を通さずに作られる PR が増えたら、旧#431 を開き直す
  - `pre-push-optout.log`・`merge-gate-suppressed.log`・`pre-push-gate-suppressed.log`・`pre-pr-gate-suppressed.log`・`review-followup-nudge.log`：gate のログ（`*-suppressed.log` には、gate が止めずに通した不足を `would-block:<code>` の行で書く）。repo は絶対パスの sha1 の先頭 8 桁で記録し、パスは残さない
  - `push-review.log`：git の pre-push hook が、PR が open の branch への push ごとに判定（`reviewed`・`would-deny` など）を 1 行書く（log-only）。repo・branch・session はハッシュの先頭 8 桁、commit は sha の先頭 8 桁で記録し、パスと branch 名は残さない。起動した Agent の subagent_type（`reviewed` は成功した reviewer、`other-agent-only` は最大 3 件）と起動の timestamp は、英数字と一部の記号以外を `_` に置き換えて書く。ファイルは 0600、state dir を新しく作るときは 0700 にする
  - `main-model-gate.log`：main のモデルの gate が、判定ごとに時刻・session（sha1 の先頭 8 桁）・入口（`Skill`・`Write`・`setup`）・モデルを決めた段・モデル名・判定を 1 行書く。ファイルは 0600。書けないときは書かずに判定を続ける
  - `wait-loop-gate.log`：待ちのループの deny の hook が、payload を JSON として読めなかったときに、例外の型とメッセージの 1 行目だけを書く（payload の中身と repo のパスは書かない）
  - `review-followup-pr-cache/`：PR 後の push の案内が、PR の有無をキャッシュする（既定 300 秒、判定できなかったときは 30 秒。ファイル名は repo と branch のハッシュ）
  - steering への書き込みの検査（`validate-steering-write.py`）の、連続 deny の counter：回数と時刻だけを持つ。ファイル名は (書き込み先のパス, category) の sha1 の先頭 16 桁。category ごとの counter は、同じ書き込み先に中身を書く書き込みが deny されずに通ると消す（行を消すだけの Edit では消さない）。size の上限は止めないので counter を持たない。1 時間を過ぎると回数を 0 と読むが、ファイルは消さない（以前の版が作った counter は、書き込み先のパスと category も平文で持つ）
  - `last-turn-failure.json`：StopFailure の hook が、異常終了したターンのエラー・session id・project root（絶対パス）を書く。project root が一致する次の SessionStart が読んで消す（壊れた記録も消す。記録の場所が symlink ならリンクだけを消す）。compaction の直後の SessionStart は読まずに残す。別の project のセッションと、python3 が無いなどで解釈できないときは消さず、次の異常終了で上書きされるまで残る
- `validate-steering-write.py` は `.steering/` への書き込みを検査し、以下を deny する:
  - email アドレス（例外: `example.com` / `example.org`）
  - ローカル絶対パス（`/Users/...` / `/home/...` / Windows UNC）
  - AWS アカウント ID 文脈の 12 桁値
  - 秘密鍵 marker / 既知接頭辞の token 実値（AWS `AKIA`・`ASIA` / GitHub `ghp_` 系・`github_pat_` / Slack `xoxb-` 系・`xapp-`）
  - `password` / `token` / `secret` / `credential` などの key に紐づく実値らしき値
- `validate-steering-write.py` は、`.steering/` の `state.md` / `tasklist.md` / `design.md` への write で、post-write サイズが上限（20,000 / 80,000 / 60,000 バイト）を超え、かつ増える場合は止めずに通知する（`additionalContext` と `systemMessage`。ほかの category の deny と降格した allow でも本文に付ける。減る write には出さない）
- `run-block-plan-mode-hook.sh` は GDD session 中の `EnterPlanMode` を deny
- `validate-steering-write.py` は、同一 `(path, category)` で 3 回連続 deny すると warning 付き allow へ降格する escape hatch を持つ。降格しない category は `validate-steering-write.py` の `NON_DEMOTABLE_CATEGORIES`（`secret_marker`・`self_review_evidence`・`peer_turn_state_write`・`origin_session_rewrite`・`steering_line_break`）で、違反を取り除くまで block され続ける。size の上限は止めないので、降格の判定に関わらない
- hook は失敗時 fail-closed（安全側倒し）を原則とするが、例外がある（網羅ではない）。どれも、全 Bash・Agent・Skill を止めるより、止めそこねる方が影響が小さいと判断したもの
  - 型を読めない payload と判定の例外で通す: 待ちのループの deny（wait-loop-gate。例外は state dir の `wait-loop-gate.log` に記録する）、gdd-formal-gate-runner の同期の起動の deny（background-dispatch-gate。例外は project の `.gdd/hook-errors.log` に記録する）。止めそこねても実害は待ちが長くなること
  - command や skill の名前を解析できないと、対象の操作ではないとして通す: active-gdd-skill gate と、その expansion の gate（pre-push gate・pre-PR gate は、もともと止めない。下の § 制限事項）
  - python が見つからないと通す: worktree-command-guard
  - main のモデルを判定できないと通す: main-model-gate（transcript にモデルの信号が無い、読めない、payload が JSON でない）。今の返事の行が transcript にまだ無いときは前の返事のモデルで判定するので、画面で Sonnet に切り替えた直後は通すことがある。判定するのは gdd-dev・gdd-resume の Skill の呼び出し、`setup-gdd-loop.sh` の中、手動の手順で run を始める `.claude/gdd-dev.local.md` への Write・Edit・MultiEdit だけで、Bash で `.claude/gdd-dev.local.md` を書く形、state ファイルの hardlink や名前の違う symlink を通した Write・Edit・MultiEdit と、`setup-gdd-loop.sh` に `CLAUDE_CODE_SESSION_ID`・`CLAUDE_CONFIG_DIR`・`HOME` の別の値を前に付けて transcript・settings・kill switch の場所を変える形は止めない。`setup-gdd-loop.sh` の外し方は settings のファイルの env だけを読み、`GDD_RUNTIME` では判定を外さない。これは利用条件の gate で、信頼境界ではない。止めそこねても実害は確認の作り直しが増えること
  - 動かないときは何も見せずに止めない: request-diff-hook（`claude` が無い、失敗した、答えを読めないときは、理由を `request-diff.log` に残す。例外と壊れた payload は記録にも残らない）。止める hook ではないので、判定の穴にはならない。この hook は transcript のユーザーの発言と提示の本文を、伏せずに `claude -p` に渡す（送信先は Claude Code の本体と同じ）。`request-diff.log` に残す引用は `_redact` で伏せる
  - 読めないと写さない: request-capture-hook（transcript が読めない、payload が JSON でない、state.md の `Created In Session` が無いか payload の session_id と違う、`Started At` が読めない、steering を作った起動が transcript に無い。写せないときは、写していないことと理由の見出しの request.md を作り、systemMessage でも知らせる。steering の書き込み検査（risk_tier.py）は、request.md が hook の節で始まる通常のファイルでないとき（この形、runner・main が書いたもの、無いとき。Codex・Cursor を含む）は `risk-low` の承認を止める。例外で落ちたときは request.md を作らず、runner が同じ形で作る。既にある request.md は書き換えない）。起動を止めない記録の hook で、信頼境界ではない。写すときは、steering の書き込み検査が止める 6 種の値を同じ検出器で語に置き換える

**token 検出は接頭辞 allowlist であり網羅ではない**。接頭辞を持たない token（例: 40 文字のランダム文字列）、AWS secret access key、未登録サービスの API key（OpenAI / Anthropic / GitLab / Stripe 等）は検出されない。hook は「よくある事故の自動検出」であって、秘密情報を書かない判断そのものは人間と AI の責任に残る。

---

## `.steering/` への書き込み禁止情報

Hook が自動検出・ブロックする情報（`validate-steering-write.py`）:

| 種類             | 例                             | 許容される代替                                |
| ---------------- | ------------------------------ | --------------------------------------------- |
| 個人メール       | `user@company.com`             | `user@example.com`                            |
| ローカル絶対パス | `/Users/alice/project/src/...` | 相対パス `src/...`                            |
| AWS アカウント ID 文脈の 12 桁値 | `AWS account: <12-digit-account-id>` | `<redacted-account-id>` |
| 秘密鍵 / API トークン / パスワード marker | `<private-key-marker>` / `AKIA...` / `token key with redacted value` | `<redacted>` |
| 既知接頭辞の token 実値 | GitHub `ghp_...` / `github_pat_...`、Slack `xoxb-...` / `xapp-...`、AWS `AKIA...` / `ASIA...` | `<redacted>`、または接頭辞だけの言及（`ghp_ で始まる`） |

Hook が自動検出で完全保証しないが**書いてはいけない情報**（人間側でも除外する）:

| 種類                                 | 理由                                 |
| ------------------------------------ | ------------------------------------ |
| AWS アカウント ID（12 桁）           | コスト分析・権限推定の手がかりになる |
| 秘密鍵 / API トークン / パスワード   | 漏洩即被害                           |
| Secrets Manager / SSM パラメータ実値 | 同上                                 |
| 顧客個人情報 / 業務データ実値        | 個人情報保護法 / GDPR                |
| 内部 URL（SSO 保護リソース）         | 識別子以上の情報を残さない           |

**保護メカニズム**:

- hook による自動 deny（email / path / AWS account ID 文脈 / secret marker / sensitive value）
- `CLAUDE.md` の `機密情報の commit / push 禁止` ルール
- `docs/CI_GUARDS.md` の raw task steering guard（PR / main に `.steering/<task>/` を含めない）
- `.gitignore` に `.steering/` を含めるかはチーム判断（含めない場合や一時 push した場合は git 履歴に残るため特に注意）

---

## 通信境界

GDD plugin 自体は、下の表の「PR の有無の照会」の 1 件を除いて**外部ネットワーク通信を行わない**。それ以外の行は、すべてホスト環境（Claude Code / Cursor / Codex）の責任:

| 通信種別                          | 担当                                  | 備考                                              |
| --------------------------------- | ------------------------------------- | ------------------------------------------------- |
| LLM API（Anthropic / OpenAI）     | Claude Code / Cursor / Codex          | plugin は prompt を構築するのみ                   |
| MCP サーバー通信                  | Claude Code / Cursor / Codex          | plugin は MCP を起動しない                        |
| git / GitHub                      | Bash tool 経由でユーザー権限          | skill は `gh` コマンド等を実行するが認証はホスト |
| PR の有無の照会（GitHub）         | hook（`run-review-followup-nudge-hook.sh`）が利用者の `gh` を直接実行 | `gh pr view` の読み取りだけ。Bash tool を通らない（§ 4） |
| 社内ドキュメント（wiki・チケット管理） | MCP 経由（ユーザー CLAUDE.md で規定） | plugin は直接アクセスしない                       |
| 外部検索（WebFetch / WebSearch / Browser） | ホストのツール経由                    | plugin は検索を要求するが通信は行わない           |

---

## 信頼境界

### Trusted（plugin が信頼する入力）

- `.steering/<task>/` 内の artifact（自分が書いた / reviewer を通過した）
- plugin 内部の `references/` / `skills/` / `agents/` 定義
- hook が生成する systemMessage

### Untrusted（検証が必要な入力）

- ユーザーの `/gdd-dev <input>` テキスト
- 対象リポジトリのソースコード内容（可能性として悪意のあるコメント / prompt injection）
- 外部取得した検索結果・ドキュメント（WebFetch / tech-docs-searcher 経由）
- subagent の戻り値（controller が独立検証する）
- 別の session の Claude Code transcript の末尾（`scripts/setup-gdd-loop.sh` が、別の session の state でロックするときに、`$CLAUDE_CONFIG_DIR` か `~/.claude` の `projects/*/<session_id>.jsonl` の末尾 1 MiB を読む。session_id は英数字・`-`・`_` の形のときだけ使い、記録の top-level の `timestamp` だけを取り出して、ロックのメッセージに時刻として出す。ロックするかどうかには使わない）。`commands/gdd-dev.md` の手動の手順で止まるときも、agent が同じ transcript の末尾から `timestamp` だけを取り出してユーザーに見せる（`docs/TROUBLESHOOTING.md`）

**保護メカニズム**:

- prompt injection 対策: reviewer agent は `### Ignore previous instructions` 等のパターンを findings として扱う
- subagent 出力の独立検証: controller が `verification-before-completion` を実行
- 外部取得データのマスキング: 社内ドキュメント取得時は `***` マスクを要求（CLAUDE.md ルール）

---

## 運用者責任（plugin 外で担保すべき項目）

GDD plugin が提供しないため、導入チームが別途担保する必要がある項目:

| 項目                                | 推奨対応                                       |
| ----------------------------------- | ---------------------------------------------- |
| Claude Code / Cursor / Codex の認証情報管理 | ホスト OS のキーチェーン / 環境変数            |
| LLM API キーの保護                  | 環境変数、ローテーション                       |
| MCP サーバーの認証                  | 各 MCP の認証手順に従う                        |
| git 認証（HTTPS token / SSH key）   | ホスト OS の標準管理                           |
| `.steering/` の git 管理方針        | standard では raw task steering を main に残さず、導入先 CI で `docs/CI_GUARDS.md` の guard を入れる |
| reviewer の false positive 監視     | `gdd-metrics` で定期確認                       |
| 監査ログの長期保管                  | `.steering/<task>/worklog.md` + git 履歴       |

---

## 脅威モデル（想定される攻撃と対応）

| 脅威                                     | 攻撃経路                                         | 対応                                                                                                      |
| ---------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Prompt injection（リポジトリコード経由） | 悪意のあるコメント/文字列で skill を誘導         | reviewer agent が findings として扱う。subagent 出力の独立検証                                            |
| Secrets 漏洩（`.steering/` 経由）        | うっかり secrets を artifact に書く / raw steering を branch 履歴へ push する | hook で email / path を deny。人間が AWS ID / API key を書かない規律。導入先 CI guard、PR 前 local check、squash merge、merge 後 branch delete を併用 |
| Plan mode 迂回による意図しない実装       | Plan mode で GDD state を無視して実装            | `run-block-plan-mode-hook.sh` が GDD session 中の `EnterPlanMode` を deny                                 |
| phase-skip 迂回                          | internal skill を直接呼び出して gate を飛ばす    | 各 phase skill の `Phase Gate Pre-check` で state 検証、Internal skill の description で auto-routed 明示 |
| 破壊的操作の暴走                         | auto-mode で terraform apply / aws delete が連鎖 | Operational Safety ルール（CLAUDE.md）、`-auto-approve` 禁止、1 操作ごとの確認                            |
| reviewer の loop 暴走                    | 同一指摘が無限に繰り返される                     | Reviewer Loop Escape Hatch（5 回連続で route recalibration。policy-level 変更時だけ human recheck）       |
| 複数セッションの race condition          | 同時実行で state が壊れる                        | `setup-gdd-loop.sh` の atomic lock（mkdir 方式）                                                          |

---

## チーム外への配布前の確認

広めに配布する前に、導入担当者は以下を確認する:

1. `bash tests/validate-plugin.sh` と Python unittest が通っている
2. `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` の Operational Safety / 機密情報 / ブランチ・PR 方針を導入先の `CLAUDE.md` または `AGENTS.md` に反映した
3. PM / PO / 非エンジニア承認者には `docs/NON_ENGINEER_APPROVER_HANDOUT.md` を先に共有し、必要な場合だけ `docs/NON_ENGINEER_HITL_GUIDE.md` を案内した
4. `docs/CI_GUARDS.md` の raw task steering guard を導入先 repo の CI に追加した
5. Codex で使う場合、`references/codex.md` の model routing と host-level interruption 境界を確認した

`validate-steering-write.py` の検査は防御層の 1 つであり、自動検出で完全保証しない。配布時は commit 前の機密情報チェック、PR 前の `gdd-pr-review`、`docs/CI_GUARDS.md` の raw task steering guard、プロジェクト側 secret scanning を併用する。

---

## 監査証跡

GDD の動作は以下の場所に証跡が残る:

| 証跡                            | 内容                                                          | 保持期間       |
| ------------------------------- | ------------------------------------------------------------- | -------------- |
| `.steering/<task>/state.md`     | gate status / Resume From / Approved Direction                | git 履歴と同じ |
| `.steering/<task>/tasklist.md`  | タスク進捗 / Implementation Reviewer Selection / Fix Attempts | 同上           |
| `.steering/<task>/worklog.md`   | 作業ログ / 試行記録 / Error Log                               | 同上           |
| `.steering/<task>/adr.md`       | 意思決定記録                                                  | 同上           |
| `<repo-root>/docs/learned-patterns.md` | 横断的な学習パターン                                          | 同上           |
| git log                         | コミット履歴                                                  | git 履歴       |
| CHANGELOG.md                    | plugin 自体の変更履歴                                         | 永続           |
| CHANGELOG-archive*.md           | 古い release 節（行数上限のため分割。本文は移動時に無変更）    | 永続           |

---

## 制限事項（Honest Limitations）

GDD が**保証しないこと**を明示する:

- **ホスト LLM の安全性**: plugin は LLM API の応答が安全であることを保証しない
- **外部データの正確性**: WebFetch / tech-docs-searcher 経由で取得した情報の正確性は検証しない
- **MCP 実装の信頼性**: MCP サーバーのコードは plugin の scope 外
- **実装の完全性**: reviewer agent は既知のパターンを検出するが、未知のバグ・脆弱性は検出しない
- **プロジェクト固有の compliance**: PCI-DSS / HIPAA / 特定業界規制への準拠はプロジェクト責任
- **merge gate は merge を止めない**: merge gate は、不足を見つけても merge を通し、reason code を実行後の通知（additionalContext と systemMessage）で返し、`merge-gate-suppressed.log` に `would-block:<code>` を記録する。通知が agent に届くのは merge の後である。承認の無い merge・bot レビューを待たない merge を plugin は止めないので、承認は導入先の運用（人がマージを決める、branch protection、auto mode classifier など）で担保する。以下の merge gate の記述で「止める」「通す」は、通知を出すか・出さないかを指す
- **pre-push gate・pre-PR gate は push・PR 作成を止めない**: 2 つの gate は、不足を見つけても push・`gh pr create` を通し、不足を実行後の通知（additionalContext と systemMessage）で返し、`pre-push-gate-suppressed.log`・`pre-pr-gate-suppressed.log` に `would-block:<code>` を記録する（pre-PR gate は、見つけた不足をまとめて 1 本の通知と 1 行の記録にする）。通知が agent に届くのは push・PR 作成の後である。そのため、PR 本文に機密の候補があっても本文は GitHub に出る（通知は、ただちにユーザーに報告するよう求める）。raw task steering を含む diff も push 済みの branch に残る。merge gate も止めないので、push から merge までに plugin が止める地点は無い。証跡とレビューは agent が通知に従うかで決まり、承認は導入先の運用で担保する。以下の 2 つの gate の記述で「止める」「通す」は、通知を出すか・出さないかを指す
- **shell 文字列を解析する block guard の守る範囲**: pre-push gate・pre-PR gate は今はコマンドを止めずに不足を実行後に通知するが、検査する形の線引きは block guard と同じく、agent が事故で打つ形から守る。敵対的に作った形（here-string で読み込んだ `cd`、利用者のシェル設定の alias など）は検査せず、通知もしない（根拠: repo の `docs/adr/2026-10-03-block-guard-threat-model.md`）。ただし、GDD worktree へ cd して打つ `gh pr create`・`git push` は、agent が実際に打つ形だが、移動先に marker が無ければ pre-PR gate・pre-push gate は marker を見る検査をしない（§ 4 の `gdd-pr-roots` の限界）。この形は、ADR が守る範囲の内に入るが、2026-10-12 のユーザーの決定（旧#431）で直さない。gate は形を正しく解析していて、素通りは marker を作る場所の設計から来るので、許可リストで閉じる規定は当てない
- **marker の無い git cwd から、parser が対象を決められない形（cd 先を採らない形・`-R` の値に `$` を含む形を含む）で打つ merge**: merge gate は、プロセスの cwd・payload の cwd・採った cd 先のうち、marker（`.claude/gdd-dev.local.md`）のある repo を root にして証跡を検査する。どれにも marker が無く、root が marker の無い git repo の cwd に決まったとき（marker 不在の出口）、merge を止めるのは、対象 PR が PR 台帳（§ 4 の `gdd-pr-roots`）に載っているときと、binding（`.gdd/tasks/*/binding.json`）が対象 PR の steering を指すときだけである。binding を引くのは、番号か URL があり、repo を URL・`owner/repo` の形の `-R`・gh が選ぶ origin で決められ、`GH_REPO`・`GH_HOST` が無く、parser（`hooks/scripts/lib/gh_command_parse.py` の `parse_gh_pr_merge`）が対象を決めきれ（`unresolvable` でない）、cd が無いか cd 先を採れた merge だけである（条件の正本は `hooks/scripts/lib/merge-gate-binding.sh` の `gdd_mg_binding_lookup`・`gdd_mg_binding_exec_root`）。cd 先を採るのは、merge を含む segment までに cd が 1 つだけあってそれが先頭にあり、引数が `..` を含まない絶対パスで、その範囲に `env` が無く、コマンド全体に `$`・バッククォートが無いときだけである（走査範囲は `_through_merge_segment`、条件は `_select_cd_target` が正本。`--body "$(…)"` のような flag の値の `$` でも採らない）。そのため、引用符の無い `$(…)` が位置引数に数えられる形、番号を `$pr` などで渡す形、`-R` の値に `$` を含む形、`$`・相対パス・`~` などで cd 先を採らない cd を含む形は、binding も cd 先の証跡も読まず、台帳で当たらなければ通す。台帳を読めないとき、対象 PR を特定できないときも通す。この形を cwd が git repo でない場所から打つと、binding は引かず、cd 先を採らなかった形のうち、parser が対象を決めきれ、URL か `owner/repo` の形の `-R` と番号で対象を明示した merge だけを、台帳で当たらないときに通し、ほかは止める（採った cd 先が marker の無い repo を指す merge は、この形に当たらず、台帳で当たらなければ通る）。この形は agent が実際に打つので、ADR（repo の `docs/adr/2026-10-03-block-guard-threat-model.md`）が守る範囲の内に入るが、2026-10-13 のユーザーの決定（旧#468）で直さず、限界として書いた。開き直すのは、この形の merge のうち、binding が読める steering（`PR URL` の行を読め、`worktree_path` が実在するもの）に対象 PR が記録されたものが 1 件以上見つかったときである。2026-10-14 に、番号と repo を読める merge なら `$` があっても binding を引く案を測り、直さないことにした（yamaguchi-tk/gate-driven-development の `review-log/20261014-merge-gate-dollar-binding.md`）。2026-04-17〜10-14 の Bash（`~/.claude/projects/*/*.jsonl` と subagents の transcript）を 2026-10-14 の main の parser に通すと、merge は 1,404 件で、そのうち marker の無い git cwd から、cd 先を採らなかった形か parser が対象を決めきれない形で打った merge は 37 件だった（cwd の marker の有無は今の状態で近似した。2026-10-13 に数えた 43 件から減ったのは、lexer の統一〔旧#473〕で、parser が対象を決めきれる形が増えたため）。内訳は、cd の引数に `$` を含む 13 件、cd 先は `$` の無い絶対パスでコマンドの他所に `$` を含む 17 件、cd 先の問題は無く parser が対象を決めきれなかった 7 件である。相対パスの cd は 0 件だった。照合する番号を読めない形（`for pr in …; do gh pr merge $pr; done`・位置引数の `$(…)` など）は 10 件で、binding とも台帳とも照合できない。番号を読める 27 件のうち、steering の state.md に対象 PR の `PR URL` が記録されていたのは 2 件で、どちらも binding では当たらない（1 件は task の binding が無く、1 件は binding の `worktree_path` が実在するパスでなく、`PR URL` が `gdd_extract_doc_field` の読まない太字の形だった）。そのため、binding を引く条件を広げても、判定が変わる merge は 0 件である。承認の無い merge がこの形で通ったかは、37 件のうち 5 件を、merge の前のユーザーの発言をそのセッションの transcript で読んで確かめた（5 件ともユーザーの事前承認があった）
- **AI エージェントの悪意ある指示への耐性**: prompt injection 対策は best effort。完全保護は不可能

---

## セキュリティ関連の参考

- Operational Safety: `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` § Operational Safety
- hook の詳細挙動: `hooks/hooks.json` + `hooks/scripts/`
- reviewer の責務: `agents/gdd-*-reviewer.md`
- `.steering/` 書き込み検査: `hooks/scripts/validate-steering-write.py`
- raw steering CI guard: `docs/CI_GUARDS.md`
- Escape Hatch: `references/rollback-patterns.md` § Reviewer Loop Escape Hatch
- 共通 guardrail: `references/common-guardrails.md`

---

## セキュリティ issue の報告

plugin 自体の脆弱性を発見した場合は、plugin 配布元（GitHub repo 等）に非公開経路で報告する。公開 issue tracker には書かない。
