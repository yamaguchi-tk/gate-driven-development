---
lane: L1+
pr: 88
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: opus) | fd56427 | 1 | 5 | 0 | 2026-09-15T13:10+09:00 |
| 独立-2 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: opus) | 618a847 | 0 | 3 | 0 | 2026-09-15T13:29+09:00 |
| 独立-3 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: opus; 対象は2巡目以降のdelta) | 6b016cc | 0 | 2 | 0 | 2026-09-15T13:39+09:00 |
| PR後-1 | yamaguchi-tk (PR 旧#88 review) | 14ef806 | 2 | 6 | 0 | 2026-09-15T15:28+09:00 |
| 独立-4 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: Opus 5 effort=max) | 03c2e8c | 0 | 3 | 0 | 2026-09-15T16:14+09:00 |
| PR後-2 | yamaguchi-tk (PR 旧#88 review) | e3488de | 1 | 5 | 0 | 2026-09-15T22:55+09:00 |
| PR後-3 | yamaguchi-tk (PR 旧#88 review) | 241106f | 1 | 1 | 0 | 2026-09-15T23:51+09:00 |
| 独立-5 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: Opus 5 effort=max) | 52a0a88 | 0 | 0 | 0 | 2026-09-16T00:19+09:00 |
| PR後-4 | yamaguchi-tk (PR 旧#88 review) | eb58977 | 1 | 2 | 0 | 2026-09-16T11:42+09:00 |
| 独立-6 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: Opus 5 effort=max; 対象は `git diff 52a0a88..HEAD`) | 9f90d56 | 0 | 0 | 0 | 2026-09-16T11:57+09:00 |
| PR後-5 | yamaguchi-tk (PR 旧#88 review) | 13425e4 | 1 | 1 | 0 | 2026-09-16T13:44+09:00 |
| 独立-7 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: Opus 5 effort=max; 対象は `git diff 9f90d56..HEAD` のうち round5対応のコード差分) | 92b85da | 2 | 3 | 0 | 2026-09-16T14:28+09:00 |
| PR後-6 | yamaguchi-tk (PR 旧#88 review) | d7597ab | 2 | 0 | 0 | 2026-09-16T16:24+09:00 |
| 方針メモ | user (AskUserQuestion 確認。L1+ 安全策4: 同一クラスタ「glued punctuation」の high/blocking が独立-7 と PR後-6 で2回続いたため、修正を続けず修正方針をユーザーに確認した) | - | 0 | 0 | 0 | 2026-09-16T16:52+09:00 |
| 独立-8 | general-purpose subagent (read-only, diff-only, 経緯非共有, model: Opus 5 effort=max; 対象は `git diff 92b85da..HEAD -- . ':(exclude)review-log/'`) | 4c8e9af | 0 | 2 | 0 | 2026-09-16T17:21+09:00 |
| PR後-7 | yamaguchi-tk (PR 旧#88 review) | e258d32 | 0 | 0 | 0 | 2026-09-16T19:21+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | yes | self-inflicted | fail-open-crash | fixed | `STATE_DIR` の `${HOME}` 展開が `set -u` 下で `HOME` 未設定時にシェルごと即死する（`self-review-evidence.sh` が既に修正済みの旧パターンを再導入していた）。`HOME`/`GDD_HOOK_STATE_DIR` とも無い場合はログ・キャッシュを no-op にし、`gh` 呼び出し自体は続行するよう縮退させた |
| F2 | 独立-1 | medium | no | self-inflicted | predictable-fallback | fixed | `mktemp` 失敗時のフォールバックが予測可能な固定パスだった。fail-safe に倒し `undeterminable` として記録するよう変更した |
| F3 | 独立-1 | medium | no | self-inflicted | observability-gap | fixed | `injected`/`undeterminable` しかログされず、「発火機会が無かった」と「hook が壊れていた」を再計測手順で区別できなかった。opt-out と no-pr の分岐にも `skipped` イベントを追加した |
| F4 | 独立-1 | medium | yes | self-inflicted | accept-set-asymmetry | fixed | 現在の checked-out branch だけを見て PR 有無を判定していたため、明示 refspec 付き push（`git push origin <別branch>`）を取り違えていた。`push_command_parse.classify_refspec` の `explicit_ref` を優先するようにした |
| F5 | 独立-1 | medium | no | self-inflicted | doc | fixed | `additionalContext` は push 実行後にしか届かないため、nudge 文言を過去形（「push しました」）に変更した |
| F6 | 独立-1 | medium | no | self-inflicted | doc | accepted | 「opt-out 経路はこの hook でも塞がらない」という finding は既存 changelog / `hooks.json` description が既に「但し opt-out は尊重する」と正しく記載しており、overclaim ではないと判断し対応不要とした |
| F7 | 独立-1 | low | no | self-inflicted | secrecy-asymmetry | fixed | cache ファイル名が branch 名を平文で残しており、ログ側のハッシュ化方針と非対称だった。branch もハッシュ化して揃えた |
| F8 | 独立-1 | low | no | self-inflicted | detection-widening | fixed | `gh` のエラー文言 "no pull requests found" への正規表現を軽く広げ、"no open pull requests found" 等の別表現も no-pr として分類されるようにした |
| F9 | 独立-1 | low | no | self-inflicted | doc | fixed | `README.md` の PreToolUse hook 数（8 hook のまま）を実数の 10 hook に更新した |
| F10 | 独立-1 | low | no | self-inflicted | defensive-guard | fixed | `CANDIDATE_ROOTS` が空になった場合に bash 3.2 の `set -u` で落ちる潜在的経路を防御的に guard した（現状は到達しないが、emit 順序変更で顕在化しうる） |
| F11 | 独立-2 | medium | yes | self-inflicted | wiring-gap | fixed | `classify_refspec` で解決した `BRANCH` をキャッシュキーには使うのに `gh pr view` 呼び出し自体には渡していなかった。1周目で入れた「明示 refspec を優先する」修正が実質無効化されていた |
| F12 | 独立-2 | medium | yes | self-inflicted | cache-key-collision | fixed | `git push origin HEAD` は `explicit_ref="HEAD"` になり、そのまま branch 名に使うと全 branch が同一キャッシュキーを共有する。`EXPLICIT_REF=="HEAD"` の場合は現在の checked-out branch へ解決し直すようにした |
| F13 | 独立-2 | medium | no | self-inflicted | doc | fixed | changelog fragment の記載精度（テスト件数・ログ event 一覧・`skill-body-budget.sh` の数値の食い違い）を明記した |
| F14 | 独立-2 | low | no | self-inflicted | cache-key-collision | fixed | `shasum`/`sha1sum` が両方無い環境で `_hash8` が `unknown` を返しキャッシュキーが衝突する。その場合はキャッシュを無効化するようにした |
| F15 | 独立-2 | low | no | self-inflicted | timeout-budget | fixed | `GDD_REVIEW_FOLLOWUP_GH_TIMEOUT` を `hooks.json` 側の hook timeout（8秒）より確実に短くするため6秒に頭打ちする |
| F16 | 独立-3 | medium | yes | self-inflicted | input-classification-gap | fixed | `gh pr view <arg>` は `<arg>` が全桁数字だと branch 名ではなく PR 番号として解決する。branch が全桁数字なら判定不能として抜けるようにした |
| F17 | 独立-3 | medium | no | self-inflicted | test-coverage | accepted | `GH_TIMEOUT` クランプ・`shasum` 不在縮退の contract test 不足。クランプ側のテストを追加して一部解消し、`shasum`/`sha1sum` 不在の縮退経路自体は環境依存が強く regression test 化を見送り、Known limitations に明記した |
| F18 | 独立-3 | low | no | self-inflicted | defensive-guard | fixed | `CACHE_DIR=""` のとき `CACHE_FILE` がファイルシステムルート直下のパスになっていた。`CACHE_DIR` が空の場合は `CACHE_FILE` も空にした |
| F19 | PR後-1 | high | yes | self-inflicted | pipefail-propagation | fixed | PATH 上の `shasum` が非0終了する場合、`set -euo pipefail` 下でパイプライン全体の失敗が `_hash8` の呼び出し元へ伝播し、hook 全体が同じ終了コードで落ちうる。各コマンドの失敗を無害化するフォールバック（シェルの or-true 演算子）を個別に付けた |
| F20 | PR後-1 | high | yes | self-inflicted | overbroad-detection | fixed | push 検出に使っていた `is_git_push`（広い判定）をそのままネットワーク I/O を伴うこの hook に使うと、`echo`/コメント代わり/`--help` 等の未実行テキストでも認証付き `gh` が呼ばれていた。`is_git_push_at_command_start`（新設）で command-start 限定にした |
| F21 | PR後-1 | medium | yes | self-inflicted | overbroad-detection | fixed | dry-run/help/delete でも `gh` を呼んでいた。`push_has_side_effect_excluded_flag`（新設）で検出し対象外にした |
| F22 | PR後-1 | medium | yes | self-inflicted | state-check-missing | fixed | `gh pr view` は `--json number,url` だけだと MERGED/CLOSED でも exit 0 で `"number"` を返す。state を見て `OPEN` の場合だけ注入するようにした |
| F23 | PR後-1 | medium | no | self-inflicted | doc | fixed | `additionalContext` は push 実行前（PreToolUse 時点）に作られるため過去形「push しました」は断定になる。条件法に変更した |
| F24 | PR後-1 | medium | no | self-inflicted | doc | fixed | active GDD でも汎用 skill 名だけを提示していた。両方の skill 名と使い分けを1行で示す形にした |
| F25 | PR後-1 | medium | yes | self-inflicted | process-orphaning | fixed | timeout 時に `gh` 本体（subshell の子）が孤児化していた。`pgrep -P` で直接の子を辿って先に殺すようにした |
| F26 | PR後-1 | medium | no | self-inflicted | permission-asymmetry | fixed | cache の directory/file パーミッションが既定の 0755/0644 のままで、同じ state dir 内の log（600）と非対称だった。700/600 に統一した |
| F27 | 独立-4 | medium | yes | self-inflicted | parsing-fragility | fixed | `--json number,url,state` の生 JSON を `grep` で文字列一致させていたため、`CLICOLOR_FORCE=1` 等の環境で `gh` が色付き整形出力に切り替わり OPEN な PR でも一致に失敗していた。`--json state --jq '.state'` に変更した |
| F28 | 独立-4 | medium | no | self-inflicted | test-flakiness | fixed | timeout オーファン検証テストが `subprocess.run` の後で stub の pid file 出現を確認していたため、`-n auto` 並列負荷下で flaky に落ちていた。`Popen` に切り替えた |
| F29 | 独立-4 | medium | no | self-inflicted | accept-set-asymmetry | fixed | command-start 限定判定が `)`/`;;`/`{` 直後の push を見逃していた。`COMMAND_START_SEPARATORS` に追加し、実行される push を拾えるようにした |
| F30 | 独立-4 | low | no | self-inflicted | doc | fixed | `_hash8` の comment 記述精度・独立レビュー/人間レビューの帰属表記の訂正 |
| F31 | 独立-4 | low | no | self-inflicted | test-coverage | fixed | test assertion の強化（`gdd-pr-review-followup` の包含関係、条件法文言の直接 assertion 追加） |
| F32 | PR後-2 | high | yes | self-inflicted | argument-injection | fixed | 先頭が `-` の branch 名を `gh pr view` へ素のまま渡すと `--repo=attacker/repo` のような branch 名が `gh` 自身のグローバル flag として解釈されうる。全 flag の後に `--` を置き `BRANCH` を常に positional 引数として渡すよう修正した |
| F33 | PR後-2 | medium | no | self-inflicted | accept-set-asymmetry | fixed | push 検出だけ `{`/`)`/`;;` を command-start に含めて拡大した結果、opt-out 判定・cd 解決は既定の狭い集合のままで非対称だった。`find_optout`/`_find_cd_root`/`resolve_candidate_roots` に `separators` 引数を追加し、nudge hook の呼び出しだけ widened な集合を渡すようにした |
| F34 | PR後-2 | medium | no | self-inflicted | test-isolation | fixed | テストの `_run_hook` が `os.environ.copy()` をそのまま使っていたため、実行環境の `GDD_SKIP_PRE_PUSH_GATE=1` 等が除外系 regression test に漏れ込みうる状態だった。6 変数を `extra_env` 適用前に pop するようにした |
| F35 | PR後-2 | medium | no | self-inflicted | tokenizer-limitation | deferred | 引用符内の埋め込み改行が command-start と誤認される。tokenizer の書き換えは見送り、docstring と changelog に開示するに留めた |
| F36 | PR後-2 | medium | yes | self-inflicted | trust-boundary-cwd | fixed | `command -v "$GH_BIN"` は起動 cwd で解決していたが実行は `cd` 後の cwd だった。起動 cwd で一度だけ絶対パスへ解決し、以後はその絶対パスだけを実行するよう修正した（この修正は不完全だった。round 3 で是正） |
| F37 | PR後-2 | medium | no | self-inflicted | pipefail-propagation | fixed | `_log_event` 内の `date -u ...` が裸のままで、`_hash8` の High-1 と同型の穴だった。同じ無害化フォールバック（or-true 演算子）を追加した |
| F38 | PR後-2 | low | no | self-inflicted | doc | fixed | changelog の `gh pr view` 記述が実装と食い違っていた。記述を実装に合わせて更新した |
| F39 | PR後-3 | high | yes | self-inflicted | trust-boundary-cwd | fixed | `command -v` 自体が相対パス（`./gh` 等）を返す場合があり、round 2 の修正は `cd` 後の再解決経路しか塞いでいなかった。`GH_RESOLVED` が絶対パスでない場合は fail-safe（`gh-not-absolute`）に倒すよう修正した |
| F40 | PR後-3 | low | yes | self-inflicted | clock-skew-cache | fixed | `date +%s` 失敗時の `NOW_EPOCH="0"` をそのまま TTL 比較に使うと `0 - cached_epoch` が常に TTL 以内を満たし、キャッシュが永久に有効化されてしまう。`NOW_EPOCH="0"` のときキャッシュ読みの分岐自体を無効化した |
| F41 | PR後-3 | medium | no | self-inflicted | tokenizer-limitation | deferred | 引用符内の埋め込み改行の残存を再確認したが、レビュー側から「今回の必須修正にはしない」と明示された |
| F42 | 独立-5 | low | no | self-inflicted | clock-skew-cache | fixed | round 3 で是正した `NOW_EPOCH="0"` と同じ根本原因が、cache に書き込まれた epoch が未来の場合にも起きる。`NOW_EPOCH` が cache の epoch より小さい場合は無条件に無効として扱うガードを追加した |
| F43 | 独立-5 | low | no | self-inflicted | doc | fixed | round 3 是正時のコメント・changelog の記述が「`date` が正常に戻ればそのキャッシュが有効に使われる」と誤っていた。正しくは常に期限切れ扱いになり再利用されない。訂正した |
| F44 | 独立-5 | low | no | self-inflicted | test-vacuity | fixed | `HOME` を上書きしない大半のテストが kill switch 下で fail-safe assertion が軒並み vacuous green になりうる。`setUpClass` で kill switch file の存在を事前検出しスキップするガードを追加した |
| F45 | 独立-5 | low | no | self-inflicted | accept-set-asymmetry | accepted | opt-out 抑制の非対称（widened separators 下で dry-run push に付いた opt-out prefix を拾い、後続の本物の push への nudge まで抑制しうる）。fail-safe 方向・contrived な入力のため対応は見送り、Known limitations に開示した |
| F46 | PR後-4 | high | yes | self-inflicted | process-record-gap | fixed | `origin/main` に本 PR 分岐後に X-52（`review-log/` 強制）が別途取り込まれており、`changelog.d/` の断片ごとに対になる `review-log/<同じファイル名>` が無いと main 取り込み時に `validate-plugin.sh` が FAIL する。`review-log/20260915-x58-x59-review-followup-nudge.md` を新設した |
| F47 | PR後-4 | medium | no | self-inflicted | accept-set-asymmetry | accepted | opt-out 抑制の非対称の開示が非 push テキストが前にある形だけを例示しており、side-effect-excluded な本物の push（dry-run）が前にある形を明示していなかった。根本原因・対応方針は変わらないため Known limitations に具体例を追記した |
| F48 | PR後-4 | medium | yes | self-inflicted | state-check-missing | fixed | `gh pr view` が exit 0 でも state が OPEN/MERGED/CLOSED のいずれでもない場合、「OPEN ではない」を無条件に no-pr と断定し 300 秒キャッシュしていた。既知の3値だけを確信を持った分岐にし、それ以外は `undeterminable` に倒すよう修正した |
| F49 | 独立-6 | low | no | self-inflicted | doc | fixed | この review-log の `独立-1` 行を `high=1/blocking=0`（severity 値域に blocking が無いための再分類）としたが、changelog.d の検証サマリ行が当時の独立レビュー原文どおり `high=0/blocking=1` のままで、2つのドキュメントが同じ巡について食い違っていた。changelog 側を本ファイルに合わせて修正し、再分類の経緯を注記した |
| F50 | PR後-5 | high | yes | self-inflicted | process-record-gap | fixed | `origin/main` に本 PR 分岐後に別 PR（X-61 Agent dispatch model gate 等）が `hooks.json` の `PreToolUse.Agent` matcher を新設しており、本 PR の `description`/`PreToolUse.Bash` matcher 変更と衝突していた（`mergeable: CONFLICTING`）。`origin/main` を取り込み、`description` を両ブランチの列挙を統合して再採番し（7 matcher / 11 hook）、`README.md` の同表記も更新した |
| F51 | PR後-5 | medium | yes | self-inflicted | tokenizer-boundary-gap | fixed | `shlex(punctuation_chars=True)` が隣接区切り文字を 1 token に集約するため、`(cd /repo); git push` のように `)` と `;` が空白無しで連続すると未知 token になり、command-start 判定を共有する `is_git_push_at_command_start`/`find_optout`/`_find_cd_root` が git push を検出できなくなっていた（nudge の取りこぼし）。tokenizer の根本（`_split_glued_punctuation`）で実 bash の演算子境界まで再分割するよう修正した |
| F52 | 独立-7 | high | yes | self-inflicted | guard-bypass | fixed | F51 の再分割を token 列全体（`_lex_segment`）に適用した結果、`&>`（stdout+stderr の複合リダイレクト演算子）が `&`（区切り）+ `>` に誤分割され、root-branch guard の segment 分割（`validate-worktree-command.py`）が `git switch &>/dev/null -c <branch>` から git を含む segment の `-c` flag・branch 名を切り落としていた（実 bash で deny→allow への退行を再現確認）。token 列は変更せず、コマンド先頭判定専用の局所的な再解釈（`token_ends_with_separator`）に切り替えて是正した |
| F53 | 独立-7 | high | yes | self-inflicted | guard-bypass | fixed | 同じ根本原因で、pre-push gate の refspec 曖昧判定（`classify_refspec`, AC-16）が `git push &>/dev/null --all origin` の `--all` 手前で走査を打ち切り、`ambiguous=False` に誤判定していた（実 bash はこのコマンドで `--all` push を実行するため block すべき入力が非block になっていた）。F52 と同じ是正で解消した |
| F54 | 独立-7 | medium | yes | self-inflicted | evidence-scope-mismatch | fixed | 同じ根本原因で `classify_refspec` の `explicit_ref` 解決も `&>` 等の glued redirection で早期に走査が止まり、`git push &>/dev/null origin feature-x` が `explicit_ref=None`（HEAD 扱い）に誤解決されていた。self-review evidence の照合対象が実際の push 先 ref とずれうる。F52 と同じ是正で解消した |
| F55 | 独立-7 | medium | no | self-inflicted | doc | accepted | `is_redirection_operator` 等の docstring が「shlex は演算子文字の連続を 1 token に集約する」前提を記述しており、F52 是正前（token 列全体への再分割を適用していた間）は実装と矛盾していた。token 列を変更しない方式へ戻したことで前提が再び成立するため、docstring 側の修正は不要と判断した |
| F56 | 独立-7 | medium | yes | self-inflicted | test-coverage-gap | fixed | block/allow を変える修正（F51）に fail-open 側の regression test が無く、既存テストは F52/F53 の退行を素通ししていた。`test_glued_redirect_operator_does_not_truncate_refspec_scan`（refspec 側）と `ROOT_BRANCH_DENY_CORPUS` への `&>` glued 形の追加（root-branch guard 側）で、両方の退行を RED/GREEN 確認の上で固定した |
| F57 | 独立-7 | low | no | self-inflicted | fallback-path-gap | accepted | `_lex_segment` の `except ValueError` フォールバック（`segment.split()`）は空白分割のみで、punctuation の癒着解消の対象外のまま。既存の（F51 以前からある）限界であり、command-start 判定専用の局所的な再解釈方式への転換でも解消されない。環境依存の低頻度経路のため対応は見送った |
| F58 | 独立-7 | low | no | self-inflicted | over-detection | accepted | クォートで囲まれた punctuation だけの引数（例: `git commit -m ');'`）はクォート除去後 `);` という token になり、これが command-start 判定の直前 token に来る配置では「区切り直後」と誤認されうる（過検出方向）。本 hook の block しない性質（fail-safe 側）と、実 bash ではそもそも別コマンドに分かれない配置であることから実害は限定的と判断し、対応は見送った |
| F59 | 独立-7 | advisory | no | self-inflicted | design-alternative | accepted | 姉妹実装 `gh_command_parse.py`（merge gate）は token を割らず「全文字が演算子文字集合に属するか」という述語で解いており、癒着 punctuation に構造的に免疫がある。今回の方式は `_TWO_CHAR_OPERATORS` の完全性に依存せず、未知演算子でも影響範囲を command-start 判定に限定する設計に修正したため、同型の再発リスクは許容範囲と判断し、実装方式自体の転換は見送った |
| F60 | 独立-7 | advisory | no | self-inflicted | doc | fixed | `_TWO_CHAR_OPERATORS` のコメント「貪欲マッチの優先順」が、実際には順序に意味が無い（`in` 判定のみ）ことを示していなかった。F52 是正時にコメントを「完全性には依存しない設計」という設計意図の説明に書き換えた |
| F61 | PR後-6 | high | yes | self-inflicted | guard-bypass | fixed | round 7 の是正コミット（92b85da）は commit message と docstring で「`_lex_segment` の token 列は変更しない」と主張していたが、実装の `_lex_segment` は演算子分割ヘルパーを token 列全体へ適用するループを削除しておらず、主張と実装が食い違っていた。`_TWO_CHAR_OPERATORS` に無い 2 文字 punctuation（noclobber 上書き redirect 演算子等）を glue すると、依然として segment 分割ガード（root-branch guard）が deny から allow に退行することを実 bash とガードの両方で再現確認した（実 bash で branch を作成するコマンドを、ガードは git を含む segment と後続引数の segment とに分断していた）。`_lex_segment` を実際に「token 列を一切再分割しない」元の形へ戻した |
| F62 | PR後-6 | high | yes | self-inflicted | guard-bypass | fixed | `token_ends_with_separator`（F52 是正で新設）が `find_optout`/`_find_cd_root`（block gate である run-pre-push-gate-hook.sh と共有）からも呼ばれており、glued punctuation の再解釈が block gate 自体の opt-out 受理面・cd root 解決まで広げてしまっていた。実 bash では未列挙の redirect 演算子が環境変数代入の直前に glue された形で環境変数を立てないコマンドが、演算子の末尾文字が区切りと再解釈されることで実際には立っていない opt-out を受理していた（同型で `_find_cd_root` も実行されない `cd` を誤って候補 root にし、無記録の exit 0 という fail-open になりうる状態だった）。`find_optout`/`_find_cd_root` は `token_ends_with_separator` を使わず `token in separators` の完全一致に戻し、glued punctuation の再解釈は block しない `is_git_push_at_command_start`（nudge hook 専用）だけに限定した |
| F63 | PR後-6 | advisory | no | self-inflicted | process-record-gap | accepted | レビュー本文の独立レビュー形式サマリ行は `medium: 3` と宣言していたが、本文には `### High` 節のみで `### Medium` 節が無く、inline comment も無かったため、3 件の具体的な内容を取得できなかった（GitHub API で review 本体・pull request comments の両方を確認済み）。対応不可のため review-log には記録せず、PR 本文に開示するに留める |
| pm-1 | 方針メモ | advisory | no | self-inflicted | design-alternative | fixed | F61/F62 が独立-7 に続く同一クラスタ（glued punctuation）の high であったため、house rule（CLAUDE.md L1+ 安全策4）に従い修正を続けずユーザーへ選択肢を提示した: (1) nudge 側の局所述語に完全に閉じる（block gate は token 列・opt-out・cd 解決とも一切再解釈しない）、(2) 共有 `_lex_segment` の分割を維持し演算子表の完全性を block 側の正式契約にする、(3) 現状の限界を開示してこの PR はここで止める。ユーザーは (1) を選択し、F61/F62 の是正方針として採用した |
| F64 | 独立-8 | medium | yes | inherited | cd-detection-gap | deferred | `_find_cd_root` が既定（完全一致）に戻ったことで `(true);cd <repo> && git push` のような隣接区切り直後の `cd` を command-start として認識できず、`resolve_candidate_roots` が `cd_root` を得られないまま `payload_cwd` にフォールバックする。`origin/main`（このブランチが分岐する前の実装）でも同一入力で同じ挙動になることを実測確認した（`git show origin/main:.../push_command_parse.py` を分離環境へ配置し同じ入力で照合）。round 7 の是正コミット（92b85da、未 merge）だけが `token_ends_with_separator` を全 3 箇所に適用していた副作用でこの入力を偶然拾えていたのであり、`main` に対する新規の退行ではない。`resolve_candidate_roots` は `-C`/`cd`/payload/process の優先順位で単一 root に絞る設計（AC-17）そのものが古くからの限界であり、本 PR の変更範囲外のため、再現手順を添えて後続課題にする |
| F65 | 独立-8 | medium | yes | inherited | quote-stripping-bypass | deferred | shlex の POSIX クォート除去により、`echo ';' GDD_SKIP_PRE_PUSH_GATE=1 git push` のようにクォートで囲った区切り文字（例: `';'`）がクォート除去後に本物の区切り token と区別不能になり、`find_optout`/`_find_cd_root` の代入列遡りが「クォート内の文字列」と「実際のコマンド区切り」を取り違える（実 bash では変数は立たない）。`origin/main` でも同一入力で同じ挙動になることを実測確認済みで、本 PR が触れていない `_lex`/`shlex.shlex(posix=True, ...)` 自体の性質に起因する既存の限界のため、再現手順を添えて後続課題にする |
| F66 | 独立-8 | low | no | self-inflicted | doc | fixed | `_TWO_CHAR_OPERATORS` のコメントが「push検出・opt-out・cd解決が過剰/過小に反応しうる」と、F62 是正後は不正確な記述のまま残っていた（opt-out・cd 解決はもう本定数の完全性に依存しない）。コメントを実装と一致させ、F61/F62 の経緯も追記した |
| F67 | 独立-8 | advisory | no | self-inflicted | test-drift-risk | fixed | 新設した property test が `_TWO_CHAR_OPERATORS`/`COMMAND_SEPARATOR_TOKENS` の複製をテスト内にハードコードしており、正本が変わってもテスト側が追従せず drift しうる状態だった。`git_command_parse` の実定数を直接参照するよう修正した |
| F68 | PR後-7 | low | no | self-inflicted | doc | fixed | changelog.d 冒頭の `#### Added` セクションの test 件数（108 → 139 tests）・hook 本数（9 本 → 10 本）が、その後の各ラウンド対応で更新された最終値（108 → 144 tests／7 matcher / 11 hook）と食い違ったまま残っていた。読者が古い数値を最終値と誤読しうるため、両箇所に「この時点の値」である旨と最終値への参照を追記した |
| F69 | PR後-7 | low | no | self-inflicted | doc | fixed | PR 本文が push 検出後の PR 有無判定を `gh pr view --json number,url` と説明していたが、実装は人間レビュー round 2 対応（MERGED/CLOSED PR にも注入していた不具合の是正）で `gh pr view --json state --jq '.state'` に変更済みで、PR 本文側が追従していなかった。PR 本文を実装に合わせて修正した |
| F70 | PR後-7 | low | no | self-inflicted | doc | fixed | `bash -c 'git push …'` のように `git push` が `bash -c` の引数文字列に埋め込まれている場合、`is_git_push_at_command_start` は検出できない（design.md § Honest Limitations の「間接実行」の一種。fail-safe 方向）。この限界が Known limitations に未記載だった。追記した |
| F71 | PR後-7 | low | no | self-inflicted | doc | fixed | opt-out skip（`skipped(optout)`）イベントの repo hash ログは opt-out 判定が root 解決より前に走る設計のため `$PROCESS_CWD` を使う一方、`injected`/`skipped(no-pr)`/`undeterminable` は解決済みの `$ROOT` を使う。明示 `-C`/`cd` を伴う push では同じ repo への push でもイベント種別によって repo hash が食い違いうる（ログの相関付け精度の限界。opt-out 判定自体の正しさ・block/allow の挙動には影響しない）。Known limitations に未記載だった。追記した |
| F72 | PR後-7 | low | no | self-inflicted | process-record-gap | fixed | 本 PR は `skill-count-budget.sh` の `BASELINE_SKILL_COUNT`/`MAX_SKILL_COUNT` を 28 → 29 に変更しており、CONTRIBUTING.md の等価交換ルールにより `SKILL_COUNT_BUDGET_CHANGE=true`/`SKILL_COUNT_REDUCTION_PLAN=<理由と削減計画>` を PR evidence として残す必要があったが、PR 本文に記載していなかった（スクリプト自体は `BASELINE_SKILL_COUNT == MAX_SKILL_COUNT` のため実行時の env var チェックには引っかからず機械的な block は発生していない）。理由と削減計画はスクリプト内コメントに既に記載済みだったため、同じ内容を PR 本文にも追記した |
