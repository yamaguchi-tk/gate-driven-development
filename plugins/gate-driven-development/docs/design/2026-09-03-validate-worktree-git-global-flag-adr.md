# ADR アーカイブ: validate-worktree-command.py の git global flag 対応

- 対象タスク: `20260903-validate-worktree-git-global-flag`
- リリース: `CHANGELOG.md` § `### [Unreleased]`（PR 旧#28）
- 内容: `hooks/scripts/lib/git_command_parse.py` の新設（`push_command_parse.py` からの汎用 git コマンド解析の抽出）、`validate-worktree-command.py` の token ベース判定への書き換え、および Option C 採用・fail-closed 方針・cluster 検出統一に至る **ADR-1〜ADR-7**

`.steering/` は feature branch 上でのみ追跡し、merge 時に本ファイルへ蒸留して `main` には含めない運用のため、
**GDD の steering から逐語でアーカイブした**（再要約による転記誤りを避けるため意図的にコピーのみ）。
本文中の `design.md` / `requirements.md` / `tasklist.md` / `worklog.md` への参照は
branch 上の `.steering/20260903-validate-worktree-git-global-flag/` を指しており、アーカイブ対象外のため解決しない。
結論の正本は `CHANGELOG.md` の Unreleased エントリと、`hooks/scripts/lib/git_command_parse.py` / `hooks/scripts/validate-worktree-command.py` の実装そのもの。

**PR followup での追加修正について**: PR 旧#28 の Copilot review（commit `324da9f` → `f0d7a6b`）と `gdd-completion-check` の comprehensive review が、本 ADR 確定後の実装フェーズで以下のバグを追加検出・修正した。これらは既存 ADR が定めた方針（fail-closed、cluster 検出の統一）の**実装バグ修正**であり、新たな設計判断を伴わないため、独立の ADR エントリは起票していない（`.steering/` 側の `tasklist.md` `#### Attempts` に詳細記録済み、branch 上のみ）。

- `_PIPELINE_BOUNDARY_RE`（heredoc 所有 pipeline の境界検出）が `|&`/`&>`/`>&`/`<&` 中の `&` を無条件に境界扱いし、実行される heredoc 本文が guard から不可視になっていた（ADR-5 の実装バグ、`_feeds_shell_interpreter` の判定範囲が誤って縮む形の fail-open）
- `_worktree_positionals_and_names`（M-1）と `_segment_creates_branch`（H-1）が、`_segment_creates_switch`/`_segment_creates_checkout` と非対称に、短 option cluster 形（`-fb<name>` / `-cf`/`-fc` 等）を認識していなかった（ADR-6 の対象範囲外だった箇所への同型パターン未適用。cluster 検出は最終的に全 4 経路 — branch/switch/checkout/worktree add — で統一された）
- `_PIPELINE_BOUNDARY_RE` と同一の欠陥が `hooks/scripts/lib/gh_command_parse.py`（`gh pr merge`/`gh pr create` を検査する別 hook が使う独立実装）にも存在することが横展開検索で判明したが、本 PR の承認済み変更ファイル範囲（AC-11）に含まれないため別 task（follow-up）として切り出した

---

# ADR: validate-worktree-command.py の git global flag 対応

## ADR-1: 汎用 git コマンド解析を新 module へ抽出する（Option C）

### Context

`validate-worktree-command.py` は `git` と subcommand の間に `-C <path>` だけを許容する正規表現 5 本と、行全体を見る文字列 gate 3 箇所で git 呼び出しを識別していた。実測で false negative 3 系統・false positive 2 系統を確認した。同一プラグイン内の `hooks/scripts/lib/push_command_parse.py` に、token 化・セグメント分割・global option の arity 解決・未知 flag の fail-closed 扱いがすでに実装され、pre-push gate が使っていた。

requirements phase では差分の小ささから Option B（`push_command_parse` を直接再利用）を推奨案としたが、human check で **Option C（汎用部分を新 module へ抽出）** が明示選択された。

### Decision

`hooks/scripts/lib/git_command_parse.py` を新設し、`push_command_parse.py` の汎用部分（`tokenize` 系 / nested shell 展開 / `COMMAND_SEPARATOR_TOKENS` / `GIT_GLOBAL_FLAGS_WITH_ARGUMENT` / subcommand 候補解決）を移設する。`push_command_parse.py` は push 固有ロジックだけを残し、既存 public API は re-export で維持する。`validate-worktree-command.py` は新 module だけを import する（push 固有 module には依存しない）。

### Why

- Option B は worktree guard が「push gate 用 module」に依存する形になり、依存の向きが意味論的に逆転する。Option C は「汎用 parser ← push gate / worktree guard」という素直な依存になる
- SSOT の範囲は限定的である点を明示する（design review で過大主張と指摘され訂正）。同 lib には既に **3 つ**の tokenizer が並存する: `push_command_parse.py`（nested depth 5）/ `gh_command_parse.py`（nested depth 3、heredoc 除去あり）/ `run-pre-pr-gate-hook.sh` の inline heredoc。本 ADR が統合するのは **git コマンド解析の 2 経路（push gate + worktree guard）だけ**であり、`gh_command_parse` と inline heredoc の統合は scope 外（follow-up 候補）。「parser が 2 つ並ぶのを避ける」ではなく「git コマンド解析の正本を 1 つにし、3 つ目を増やさない」が正確な主張
- FP-1 / FP-2 は「クォートを解釈せず生文字列に正規表現を当てている」ことが原因で、Option A では構造的に直らない
- Option C のリスク（release critical な pre-push gate の import 経路を触る）は、`gdd-security-reviewer` の追加起動と `tests/test_push_command_parse.py`（1243 行）全 pass で抑える

### Rejected Alternatives

- **Option A（正規表現の増強のみ）**: FN は塞げるが FP-1 / FP-2 が構造的に残り、parser の重複も残る
- **Option B（`push_command_parse` を worktree guard から直接 import）**: 差分は最小だが依存の向きが逆転し、SSOT にならない

### Consequences

- 良い: git コマンド解析の正本が 1 つになる。worktree guard の FN 3 系統・FP 2 系統が同時に解消する。将来 3 つ目の git 系 gate を足すときの土台ができる
- 悪い: 変更ファイルが 5 件になり、pre-push gate の内部実装に触れる。`push_command_parse.py` の re-export を消すと push gate と既存テストが壊れるため、re-export は契約として維持する必要がある
- 制約: 新 module の import 形式は flat（後述 ADR-2）に固定される

---

## ADR-2: lib 内の import は flat（`from git_command_parse import ...`）に固定する

### Context

`hooks/scripts/lib` 配下の module は 2 通りの読まれ方をしている。

- `run-pre-push-gate-hook.sh` / `run-merge-gate-hook.sh` / `tests/test_push_command_parse.py`: `sys.path` に **`hooks/scripts/lib`** を載せて `import push_command_parse`（flat）
- `hooks/scripts/gdd_stop_hook.py` / `tests/test_merge_gate_hook.py`: `sys.path` に **`hooks/scripts`** を載せて `from lib.constants import ...`（package）

requirements.md は Option B の import 経路として `from lib.push_command_parse import ...` を実測確認済みとして記載していたが、Option C では新 module が `push_command_parse.py` から import されるため、この 2 形式の共存が破綻する。

### Decision

`push_command_parse.py` は `from git_command_parse import ...`（flat）で新 module を読む。`validate-worktree-command.py` も `sys.path.insert(0, <scripts>/lib)` + flat import を採用し、`from lib.push_command_parse import ...` は使わない。

### Why

- `push_command_parse.py` が `from lib.git_command_parse import` を使うと、`sys.path` が `hooks/scripts/lib` である pre-push gate と `test_push_command_parse.py` の両方で `ModuleNotFoundError` になる（release critical な経路が壊れる）
- 逆に flat にすると、`from lib.push_command_parse import` する呼び出し側（sys.path = `hooks/scripts`）が壊れる。よって呼び出し側も flat に揃える必要がある
- `hooks/scripts/lib` と `scripts/lib` は**同名パッケージ `lib`** であり、`sys.path` + `from lib.X import` は import 順序に依存して落ちることが本 repo で実測記録済み（`tests/_plugin_module_loader.py` docstring、`scripts/collect-gdd-telemetry.py` 58-66 行）。flat はこの既知の落とし穴も回避する
- 2 形式を try/except で両対応する互換レイヤーは循環的複雑度を増やすだけなので採らない

### Consequences

- 良い: `run-pre-push-gate-hook.sh` の変更が不要になり、変更ファイルが 6 → 5 に減る。release critical な shell wrapper に触れずに済む
- 悪い: `hooks/scripts/lib` 配下に 2 つの import 規約が併存し続ける（既存 `constants.py` 等は package 形式のまま）。本 PR では既存 module の規約統一までは行わない（YAGNI）
- 制約: 将来 `push_command_parse` / `git_command_parse` を `from lib.X import` で読もうとすると壊れる。両 module の docstring にこの規約を明記する

---

## ADR-3: 既知 no-arg global flag 集合を追加して AC-5 と AC-6 (f) を両立させる

### Context

承認ポイント 3 で「未知 git global option は fail-closed」が確定した。既存 `_subcommand_candidates` は未知の `-` 始まり token に対し「引数を取る / 取らない」の両方を subcommand 候補にする。

この設計をそのまま worktree guard に適用すると、`--no-pager` を「引数を取る」と解釈した候補が `branch` を指し、AC-6 (f) の `git --no-pager diff branch main` が root branch creation として **deny** される（新規 false positive）。requirements.md § Honest Limitations が「Option B × fail-closed が持ち込む新規 FP 面」として予告していた事象である。

### Decision

`git_command_parse.py` に `GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT`（既知の no-arg global flag 12 件）を新設し、`subcommand_candidates` はこの集合に属する flag を「引数を取らない」1 候補に確定させる。集合外の未知 flag は従来どおり両 arity 候補（fail-closed）のまま。

あわせて **`=` を含む token（値結合形）は既知・未知を問わず 1 候補に確定**させる（design review round 1 の medium 指摘）。既存実装は `"=" not in token` を条件にしていたため、既知の with-arg flag でも `=` 形は両 arity 列挙に落ち、`git --git-dir=/x diff branch main` が deny される FP を生んでいた。`=` 以降は定義上その flag に結合した値であり分離引数を消費しないので、この確定は arity 一覧の完全性に依存しない。未知 flag の `=` 形（`--future-flag=v switch -c codex/...`）も 1 候補が `switch` を指すため AC-5 の fail-closed は維持される（実測確認済み）。

新分岐はいずれも既存の with-arg 分岐と同じく `takes_argument` を評価し、区切り token を候補に入れない。

集合の正しさは実 git への問い合わせをテスト oracle にする（`git --help` の synopsis のような二次情報を正本にしない。既存 `GIT_GLOBAL_FLAGS_WITH_ARGUMENT` と同じ規律）。

### Why

- AC-5（未知 flag は deny）と AC-6 (f)（`--no-pager diff branch main` は allow）は、両 arity 列挙だけでは同時に満たせない
- 候補集合が縮むのは既知 flag に限られ、その flag が分離引数を消費しないことは実 git で検証される。したがって push gate の検出が漏れる経路は生じない
- 集合の**不完全性は fail-closed 側**（未知扱い = 両 arity 列挙）に倒れるため、追加漏れが安全性を下げない

### Rejected Alternatives

- **worktree guard 側だけで候補を後処理して曖昧さを解く**: 判定ロジックが分岐だらけになり、fail-closed の意味論が 2 箇所に分かれる
- **AC-6 (f) を諦めて新規 FP を Honest Limitations に残す**: 承認済み AC の後退にあたり、`design_detail_only` の範囲を超える

### Consequences

- 良い: worktree guard と push gate の双方で subcommand 解決の精度が上がる。fail-closed の適用範囲が「本当に未知の flag」に絞られる
- 悪い: `subcommand_candidates` は push gate が使う共有ロジックであり、pre-push gate の内部挙動を変える。実 git oracle テストと `tests/test_push_command_parse.py` 全 pass で抑える
- 残るリスク: `git --future-flag diff branch main` のような「未知 flag（値結合形でない）+ 別 subcommand」形は依然 deny 側に倒れる。これは承認済みの fail-closed 方針の帰結として受容し、design.md § Honest Limitations に記載する
- 2 集合が重複した場合の挙動は未定義なので、`WITH & WITHOUT == frozenset()` をテストで固定する

---

## ADR-6: `git branch` の creation 判定は「直後 positional」または「明示 creating flag」で決める

### Context

初版の設計は「`branch` 以降に非 flag positional があり、`BRANCH_NON_CREATING_FLAGS` が無ければ creation」としていた。design review round 1 の実測で、値を取る branch flag の**引数が positional に化ける** FP が判明した: `git branch --format %(refname)` / `--abbrev 10 -a` / `--sort committerdate` / `--color always` / `--set-upstream-to=origin/main feature-x` がいずれも deny になる。これは承認ポイント 2（誤ブロックを直す）と逆方向の劣化である。

flag の arity 表（`BRANCH_FLAGS_WITH_ARGUMENT`）を持てば解けるが、`git branch` の値取り flag は多く、増え続け、しかも列挙漏れは deny 側（誤ブロック）に倒れる。

### Decision

creation 判定を次にする。

1. 以降に `BRANCH_NON_CREATING_FLAGS`（`-d` / `-D` / `--delete` / `-m` / `-M` / `--move`、`split("=",1)[0]` で照合）があれば creation ではない
2. `branch` の**直後 token が positional** なら creation（`git branch codex/2026...`）
3. `BRANCH_CREATING_FLAGS`（`-c` / `-C` / `--copy` / `-f` / `--force`）があり positional が存在すれば creation（`git branch -c old codex/2026...`）
4. それ以外は creation ではない

### Why

- 値取り flag の arity 表を持たずに、実測で判明した 5 形すべてが allow になる（flag が先頭に来るため条件 2 に入らず、条件 3 の creating flag も無い）
- FP-1（`git branch -a` / `-v` / `-vv`）も「positional が無い / 直後が flag」で自然に解消し、除外リストへの追加ではなく構造で解ける
- 条件 1 が `git branch -d -f foo`（`-f` が creating flag だが削除操作）の誤 deny を防ぐ
- 現行正規表現も `git branch -c old new` を「`-c` を branch 名としてマッチ」という偶然で deny しているだけであり、条件 3 はそれを意図的な規則として書き直したもの

### Rejected Alternatives

- **`BRANCH_FLAGS_WITH_ARGUMENT` の arity 表を持つ**: 列挙が増え続け、漏れが誤ブロックに倒れる。条件 2 で同じ FP が解消するため不要
- **「直後 positional」だけにする**: `git branch -c old codex/...`（branch copy）と `git branch -f codex/...` を見逃す。現行より後退する

### Consequences

- 良い: arity 表なしで FP-1 と値取り flag 5 形が同時に解消する
- 悪い: 列挙（`BRANCH_CREATING_FLAGS`）の不完全性が **fail-open 方向**（exotic な作成形の見逃し）に倒れる。他の判定が fail-closed 側なのに対し向きが逆になる
- 受容理由: `git branch` の主要な作成形は `git branch <name>` と `-c` / `-f` に尽き、guard の本命である `switch -c` / `checkout -b` / `worktree add` は別ルートで fail-closed に判定される。design.md § Honest Limitations に向きを明記する
- **PR followup での訂正（H-1）**: 上記条件 3 は当初 `_BRANCH_CREATING_FLAGS` の厳密一致でのみ実装されており、`switch`/`checkout` 側の `_short_cluster_has` と非対称に短 option cluster 形（`-cf`/`-fc`/`-Cf`/`-fC`）を認識しない regression が実装フェーズで混入した。`gdd-completion-check` の comprehensive review が検出し、`_short_cluster_has` を適用する形へ是正した（本 ADR の Decision 自体は無変更、実装バグの修正）

### Superseded（2026-09-06、`20260906-branch-guard-unknown-flag`）

本 ADR の Decision（条件3「BRANCH_CREATING_FLAGSがありpositionalが存在すればcreation」、条件1相当のnon-creating優先）と、Consequencesが受容した「列挙の不完全性がfail-open方向に倒れる」前提は、`20260906-branch-guard-unknown-flag`タスクで反転した。未知`-`始まりflagはfail-closed（作成候補側）に倒すよう変更し、非作成（mode）判定はunconditional veto/conditional vetoの2区分＋末尾評価に置き換えている。詳細設計は`plugins/gate-driven-development/CHANGELOG.md`の本タスク（`20260906-branch-guard-unknown-flag`）エントリと`docs/adr/2026-09-06-branch-guard-unknown-flag.md`を正本とする。本節のDecision自体は歴史的記録として残し上書きしない。

---

## ADR-4: parser import 失敗時は fail-closed（git を含むコマンドを deny）にする

### Context

Option B / C は「module import の失敗」という新しい失敗クラスを持ち込む。import は module top-level で走るため、`main()` の既存 try/except に到達する前にプロセスが落ちる。PreToolUse hook が rc=1 で落ちた場合、コマンドはそのまま実行される（実質 fail-open）。requirements.md AC-12 が「guard が無言で allow に倒れない」ことをテスト固定するよう求めている。

### Decision

import を `try/except Exception` で包み、`PARSER_AVAILABLE` フラグに落とす。`main()` は command 取得直後に「parser 不在 かつ コマンドに `\bgit\b` を含む」場合、新規 deny 関数 `emit_deny_parser_unavailable` で deny する。git を含まないコマンドは allow のまま。

`ImportError` ではなく `Exception` を捕捉する（design review round 1 の high 指摘）。`git_command_parse.py` が「存在するが壊れている」場合（構文エラー・途中書き込み・不正マージ）は `SyntaxError` や top-level 例外になり `ImportError` では捕まらず、プロセスが rc=1 で落ちて PreToolUse はコマンドをそのまま実行する = ADR-4 が閉じたはずの fail-open が残る。`run-worktree-command-guard.sh` は `exec python3 ...` なので rc がそのまま伝播する。AC-12 のテストも「削除した tree」だけでは `ModuleNotFoundError` しか再現せず false pass するため、「構文エラーで上書きした tree」を追加する。

deny メッセージの復旧手順は **scoped なものを第一手段**にする: 該当ファイルの `git checkout --` による復元、または plugin の再インストール。全 hook を止める kill switch（`~/.claude/gdd-hooks-disabled`）は「人間が判断して実行する最終手段」として書き、エージェントが閉塞解除のために作成する誘導にしない。deny メッセージは systemMessage としてモデルに返るため、kill switch を第一手段に書くと自走中のエージェントが pre-push gate / merge gate を含む GDD の全 guardrail をマシン全体で静かに無効化しうる（requirements § 目的と正面から衝突する）。

### Why

- 承認ポイント 3 の fail-closed 方針、および requirements.md § 目的「guardrail がある条件で静かに無効化される状態は、guardrail が無い状態より危険」と整合する
- 全コマンドを deny すると、parser 破損時にリポジトリ操作が一切できなくなり復旧手段まで塞ぐ。`\bgit\b` に絞ることで判定対象だけを止める
- 既存 3 つの deny メッセージ文面は変更しない（制約）。新規メッセージの追加は制約に反しない

### Rejected Alternatives

- **ImportError をそのまま伝播させる（rc=1 + traceback）**: stderr に出るので完全な無言ではないが、コマンドは実行される。AC-12 の趣旨（guard の無効化を止める）を満たさない
- **全コマンドを deny**: 過剰。復旧操作まで止める

### Consequences

- 良い: guard が静かに無効化される経路が閉じる。削除・破損の両方をテストで固定できる
- 悪い: `lib/git_command_parse.py` が壊れると、その worktree の全 git 操作が block される
- 残るリスク: `lib/` が配布経路（plugin パッケージング）で欠けると同じ状態になる。既存 `push_command_parse.py` と同じディレクトリ・同じ配布単位なので新規リスクではないが、implementation 後に plugin install 経路で 1 度実機確認する

---

## ADR-5: セグメント分割は「区切り token」に加えて「nested shell 展開グループ」でも切る

### Context

design review round 1 で 3 レビューが独立に同じ high を挙げた。`push_command_parse._expand_nested_shell_tokens` は `bash -c '<cmd>'` / `eval '<cmd>'` の中身を lex して **区切り token なしで token 列の末尾に append** する。実測:

```
bash -c 'git log HEAD' && git worktree add /tmp/w -b codex/2026... origin/main
→ [... 'origin/main', 'git', 'log', 'HEAD']
```

展開 token が最終セグメントと融合するため、worktree 判定の positional 集合に `HEAD` が混入し、**GDD が agent に指示している正規手順そのものが誤 deny される**。同じ機構で `bash -c "git branch --list" && git branch codex/...` は展開由来の `--list` が creation 判定を抑止して deny→allow に倒れる（fail-open）。

### Decision

`tokenize()` の出力は**変更しない**（push gate の contract と `tests/test_push_command_parse.py` の 79 箇所の token 列 assert を壊さないため）。代わりに `git_command_parse.split_segments(command)` を新設し、そこで:

1. `strip_heredoc_bodies` で heredoc 本文を落とす
2. `_lex` して `COMMAND_SEPARATOR_TOKENS` で分割する
3. nested shell / eval の展開を **1 グループずつ独立に** lex し、それぞれを別セグメント群として追加する（深さ上限は既存の `_MAX_NESTED_SHELL_DEPTH`）

`_expand_once` は `_expand_once_grouped` を平坦化するだけの実装に置き換え、既存の `tokenize` 経路は挙動不変にする。

### Why

- 展開 token を元コマンドのセグメントに混ぜると、fail-closed 側（誤 deny）と fail-open 側（誤 allow）の**両方**の事故が起きる。実測で両方を再現した
- `tokenize` の出力を変えると release critical な push gate の contract test が広範に壊れる。guard 専用の入口関数を足す方が影響半径が小さい
- heredoc 除去を同じ入口に置くのは、`gh_command_parse.py` が既に `_strip_heredoc_bodies` を持つ先例に揃えるため

### Rejected Alternatives

- **`_expand_nested_shell_tokens` が展開グループ間に `NEWLINE_TOKEN` を挿入する**: `tokenize` の出力が変わり、`tests/test_push_command_parse.py` の token 列 assert が壊れる（AC-10 の「既存テスト無変更で全 pass」に反する）
- **展開 token を worktree guard で無視する**: `bash -c 'git switch -c codex/...'` の検出（AC-4 の nested shell ケース）ができなくなる

### Consequences

- 良い: 正規手順の誤 deny と nested shell 由来の誤 allow が同時に閉じる。heredoc 本文への誤爆も解消する
- 悪い: `git_command_parse` に guard 専用の入口が 1 つ増え、`tokenize` と `split_segments` の 2 系統が並ぶ。docstring で用途を書き分ける
- 制約: `split_segments` は push gate からは使わない（push gate は token index 契約に依存するため）
- **PR followup での拡張（Security High remediation）**: 実装フェーズで、「heredoc 本文の除去」が実行される heredoc（`bash <<EOF` 等）も無条件に除去してしまい guard から不可視になる regression が判明。`gh_command_parse.py` の `_heredoc_owner_scope` / `_feeds_shell_interpreter` を移植し、実行系 heredoc の本文は独立セグメントとして残す二重化を追加した。あわせて heredoc 所有 pipeline の境界検出 `_PIPELINE_BOUNDARY_RE` が `|&`/`&>`/`>&`/`<&` 中の `&` を誤って境界扱いする実装バグが PR review で 2 段階にわたり発見・修正された（本 ADR の Decision 自体は無変更）
- **PR followup での拡張（コマンド置換）**: `$(...)` / バックティックのコマンド置換がセグメント分断を引き起こし `git worktree add $(mktemp -d) -b codex/... HEAD` 等が検出漏れになる regression が判明。`_extract_command_substitutions` を新設し、置換対象を独立セグメント化する形で解消した（クォート追跡・nested shell 経路との整合を含む複数ラウンドの remediation を経た）

---

## ADR-7: token 化で新たに塞がる allow→deny 拡大 3 件（Q-a/Q-b/Q-c）はすべて deny 側へ倒す

### Context

detailed design を token ベースへ書き換える過程で、承認済み AC が要求していない **allow→deny の拡大**が 3 件見つかった: `-B`（worktree add）/ `--create` `--force-create`（switch）/ base 省略の暗黙 HEAD（worktree add）。requirements phase の実測表には無く、design phase で判明したため `design.md` § Human Check Question として human recheck に回した。design.md にはあらかじめ「無回答時のデフォルト: 推奨案（3 件とも塞ぐ）」を明記し、人間は「OK」の無条件承認でこれを追認した。

### Decision

Q-a / Q-b / Q-c の 3 件すべてを deny 側に倒す。`requirements.md` の AC-1（`--create` / `--force-create` を追加）と AC-2（`-B` と base 省略の暗黙 HEAD を追加）を拡張し、`design.md` § 判定ルールの `switch` / `worktree` 行をこの拡張に合わせて更新した。

### Why

- requirements.md § 目的にある「guardrail がある条件で静かに無効化される状態は、guardrail が無い状態より危険」という論理は、ユーザーが報告した `git -c ... switch -c` 型の見逃しと、Q-b/Q-c の「うっかりスキップ」経路（`--create` は `-c` の長形、base 省略は git 標準の暗黙 HEAD 解釈）で同型である。片方だけ塞いで他方を残す理由がない
- 実装コストがほぼゼロ（token ルールが `-B` を自然に拾う、判定表に条件を 1 行足すだけ）に対し、残すことで生じる bypass 経路の説明コストの方が大きい
- 変更ファイル数は増えない（AC-1/AC-2 の文言拡張とテストケース追加のみ）

### Rejected Alternatives

- **現状維持（3 件を Honest Limitations の既知ギャップとして残す）**: 今回の PR スコープを「ユーザーが報告した FN-1 とその同族」に厳密限定する案。却下理由は Why 欄と同じ（guardrail の一貫性）
- **3 件を個別に判断する（一部だけ塞ぐ）**: design.md は「推奨案は 3 件セット」として提示しており、人間は個別回答をせず無条件承認したため、個別に割ることはしなかった

### Consequences

- 良い: 3 系統の bypass 経路が閉じ、guardrail の一貫性（fail-closed 方針）が保たれる
- 悪い: なし（変更ファイル数・release critical な経路への影響は増えない）
- 制約: `tests/test_root_branch_guard_contract.py` に AC-1（Q-b）/ AC-2（Q-a・Q-c）の回帰テストを追加する（§ テスト方針）
- **PR followup での拡張（M-1）**: worktree add 側（`_worktree_positionals_and_names`）も `_short_cluster_has` 型の cluster 対応がされておらず `-fb<name>` の短 option cluster 形が deny されない regression が実装フェーズで判明。`gdd-completion-check` の comprehensive review が検出し、`_short_cluster_value` helper を新設して is-closed した（本 ADR の Decision・AC-2 の意味は無変更）
