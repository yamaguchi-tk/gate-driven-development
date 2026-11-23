---
type: minor
---

#### Summary

PR 作成後のレビュー指摘対応 push で、セルフレビュー/独立レビューの証跡がほとんど記録されていない実態が判明した（X-58: 全 5,247 session 走査で followup push 3,267 回中、証跡ありは 1%）。原因は既存の `run-pre-push-gate-hook.sh`（block gate）が `active: true` の GDD セッションでしか発火しないこと、かつ汎用 skill を作っても自発発火率は 24% にとどまること（X-59）。Opus advisory による独立検証で、既存 gate は `active: true` でも session-mismatch / opt-out / unresolved-steering で無言通過する分岐を多数持ち（直近30日で149件）、「active なら既存 gate が必ず文言を出す」という前提自体が成立しないことも確認した。対策として、GDD の有無に依存しない汎用 skill と、block ではなく `additionalContext` を注入するだけの新しい PreToolUse hook の 2 層構成を追加した。

#### Added

- `skills/pr-review-followup/SKILL.md`（新規）: PR 作成後の review findings -> fix -> push -> re-request review ループを GDD 非依存で定義する汎用 skill。collect → classify → verify → fix（規律A: 横展開検索 / 規律B: スレッド消化）→ 内部整合レーン → 独立レビュー（`references/independent-review.md` 契約）→ push → re-request の骨格と証跡の書き方を持つ。GDD 配下では `gdd-pr-review-followup` がこの手順を内包し、state.md/tasklist.md/steering/Auto-Arm/ADR distillation 等を追加で要求する
- `hooks/scripts/run-review-followup-nudge-hook.sh`（新規）: PreToolUse (Bash matcher) で `git push` を検知し、push 先 branch に PR が既にあるなら `pr-review-followup`（GDD active session 下では `gdd-pr-review-followup`）skill の手順に従うよう `additionalContext` を 1 行注入する。push 検出は `push_command_parse.is_git_push_at_command_start`（command-start 限定。人間レビュー対応で新設、下記参照）を使い、`-n/--dry-run` `-d/--delete` `-h/--help` を伴う push は対象外にする。push 対象 branch は `push_command_parse.classify_refspec` の `explicit_ref`（`git push origin HEAD` 等の自己参照形は現在の checked-out branch へ解決し直す）を優先し、無ければ現在の checked-out branch を使う（既知の限界: `<local>:<remote>` の colon 付き refspec は local 側の名前を使う）。`gh pr view --json state --jq '.state' -- <branch>` で PR 有無を判定し（state が `OPEN` のときだけ注入対象。実測 0.5〜1.0 秒）、結果を短い TTL でキャッシュする。ネットワーク障害・認証切れ・timeout は「PR なし」に誤判定せず「判定不能」として別イベントでログに残す（fail-safe = 注入しないだけで block はしない）。既存の kill switch と `GDD_SKIP_PRE_PUSH_GATE` opt-out（process-env / command-prefix）は尊重する。active GDD セッションかどうかに関わらず発火する（Opus advisory の実測根拠は上記 Summary のとおり）。`hooks/hooks.json` の Bash matcher に登録し、description の hook 一覧を 9 本 → 10 本に更新した（この時点の値。後に人間レビュー round 5 対応の `origin/main` 取り込みで 7 matcher / 11 hook へ再採番している。下記「人間レビュー round 5 対応」参照）
- `hooks/scripts/run-review-followup-nudge-hook.sh` の可観測化ログ: `${GDD_HOOK_STATE_DIR:-~/.claude/.gdd-hook-state}/review-followup-nudge.log` に `injected`（注入のたび） / `skipped`（reason: `optout` / `no-pr`。fresh に判定できた回のみ） / `undeterminable`（reason: `gh-not-found` / `gh-timeout` / `gh-error` / `mktemp-failed`）の 3 イベントを記録する。絶対パスは残さず repo をハッシュ化する（既存 `pre-push-optout.log` と同じ秘匿方針。ログファイル自体は独立にした）
- `tests/test_review_followup_nudge_hook.py`（新規、36 tests）: 非 push no-op / PR あり注入 / PR なし no-op / gh エラー・timeout の undeterminable 記録 / cache 命中で gh 再呼び出しされないこと / opt-out（process-env・command-prefix）・no-pr の skipped 記録 / kill switch / active GDD marker があっても発火すること / detached HEAD（明示 refspec 無し）no-op / HOME 未設定でクラッシュしないこと / 明示 refspec の branch が現在 branch を上書きすること・`gh pr view` にその branch が渡ること / `git push origin HEAD` が現在 branch へ解決されること / gh エラー文言の別表現でも no-pr に分類されること / 全桁数字 branch が判定不能になること / GH_TIMEOUT が hooks.json の hook timeout より確実に短くクランプされること / ログに絶対パスが残らないこと / hooks.json への配線を固定した。加えて PR 旧#88 人間レビュー対応（round 1・round 2・round 3・round 4）、独立レビュー round 4（round 1 是正自体が対象）、独立レビュー round 5（round 3 是正自体が対象、自己レビュー）対応で計 22 tests 追加、計 44 tests（下記参照）
- `tests/test_push_command_parse.py`: `is_git_push_at_command_start` / `push_has_side_effect_excluded_flag` の contract test、および round 5 対応の `find_optout`/`resolve_candidate_roots` widened-separators contract test を計 31 件追加（108 → 139 tests。この時点の値。その後の各ラウンド対応で最終的に 108 → 144 tests まで増加している。下記「Validation / Eval Impact」参照）
- `hooks/scripts/lib/push_command_parse.py`（人間レビュー対応、下記参照）: `is_git_push_at_command_start`（外部副作用を伴う hook 専用の狭い push 判定）と `push_has_side_effect_excluded_flag`（`-n/--dry-run` `-d/--delete` `-h/--help` 検出）を新設した。既存の `is_git_push`（block gate 向け、意図的な過検出）はそのまま維持する

#### 人間レビュー round 1 対応（PR 旧#88、独立レビューとは別枠の人間レビュー、head `6b016cc` に対するレビュー）

`run-review-followup-nudge-hook.sh` に対する人間レビューで High 2 件・Medium 6 件の指摘を受け、同じ push で全件是正した。

- **High（`_hash8` の pipefail 伝播）**: PATH 上の `shasum` が「無い」のではなく「非 0 終了する」場合、`set -euo pipefail` 下ではパイプライン全体の失敗が `_hash8` の呼び出し元へ伝播し、hook 全体が同じ終了コードで落ちうる。PreToolUse で終了コード 2 は block 扱いのため、advisory のはずの hook が空の reason で push を deny しうる不具合だった。各コマンドの失敗を `|| true` で個別に無害化し、shasum → sha1sum → `unknown` のフォールバック連鎖を「無い」と「壊れている」の両方で機能させた
- **High（未実行テキストでの認証付き `gh pr view`）**: push 検出に使っていた `is_git_push`（block gate 向けの広い判定。`echo git push` 等の過検出を意図的に許容）をそのままネットワーク I/O を伴うこの hook に使うと、`echo git push ...` / `# git push ...`（コメント代わり）/ `git push --help` 等、実行されないコマンド文面でも認証付き `gh` が呼ばれていた（PreToolUse は許可ダイアログより前のため、拒否した push でも問い合わせが走る）。`push_command_parse.is_git_push_at_command_start`（新設）で「git token がコマンド先頭 — `env`/代入列を読み飛ばした上で index 0 または区切り token 直後 — に現れる」場合だけに限定した。過検出源の後に本物の command-start push が続く形（`echo git push foo && git push origin bar`）は見逃さないよう、command-start 条件を満たす一致が見つかるまで全 token を走査する
- **Medium（dry-run/help/delete でも `gh` を呼んでいた）**: `push_command_parse.push_has_side_effect_excluded_flag`（新設）で `-n/--dry-run` `-d/--delete` `-h/--help`（`git push -h` 実測で確認、`--no-dry-run` のような明示的否定形は token 完全一致のため誤って除外しない）を検出し、該当する push は `gh` を呼ばず抜けるようにした
- **Medium（MERGED/CLOSED PR にも注入）**: `gh pr view` は `--json number,url` だけだと MERGED/CLOSED でも exit 0 で `"number"` を返す。`state` を見て `OPEN` の場合だけ注入するようにした（MERGED/CLOSED は `skipped(no-pr)` として記録。抽出方法は独立レビュー round 4 でさらに是正 — 下記参照）
- **Medium（文言が push 完了を断定）**: additionalContext は PreToolUse 時点（push 実行前）で作られるため、過去形「push しました」は断定になる（過検出を command-start 限定で大きく減らしても、design.md § Honest Limitations 由来の検出面の限界は完全には塞ぎきれないため）。「push を検知しました。成功した場合は…」の条件法に変更した
- **Medium（active GDD でも汎用 skill 名だけを提示）**: `pr-review-followup` skill 自身は「GDD 配下は `gdd-pr-review-followup`」と書いているが、hook の文言は常に汎用名だけを指していた。hook 側で active 判定を新たに行うと session-mismatch 等で誤判定しうるため、両方の skill 名と使い分けを 1 行で示す形にし、判定はモデル側に委ねた
- **Medium（timeout 時の `gh` プロセス孤児化）**: `( cd ... && gh ...; echo $? > rc ) &` のため `$!` は subshell の pid で、`gh` 本体はその子。subshell だけを `kill -9` すると `gh` は init に引き取られて残り続けていた。`pgrep -P` で直接の子を辿って先に殺すようにした
- **Medium（cache のパーミッション非対称）**: cache directory/file が既定の 0755/0644 のままで、同じ state dir 内の log（600）と非対称だった。近傍の state dir 契約（merge-gate / self-review-evidence / stop-failure-record）に揃え、`chmod 700`/`chmod 600` を追加した

これに合わせて `origin/main`（PR 旧#86/#87 マージ済み、X-53/X-56）を merge し、`skill-body-budget.sh` の references line budget ratchet（11927 → 11958、main 側で別途解決済み）を取り込んだ。

#### 独立レビュー round 4（上記「人間レビュー対応」の修正自体を対象とした自己レビュー、diff-only / read-only / 経緯非共有 / model: Opus 5 + effort=max）

上記の人間レビュー対応commit自体を独立レビューにかけ、`high: 0, medium: 3, blocking: 0` を得た。Medium 3 件をすべて是正し、あわせて Low 4 件のうち 3 件（記述精度・test assertion の強さ）を同じ push で吸収した。

- **Medium（`gh` の色付き整形出力で state 判定が壊れる）**: `--json number,url,state` の生 JSON を `grep -q '"state":"OPEN"'` で文字列一致させていたため、`CLICOLOR_FORCE=1` 等が設定された環境では gh がリダイレクト先でも色付き・整形出力に切り替わり、OPEN な PR でも一致に失敗し `skipped(no-pr)` に誤って倒れることを実測で確認した。`--json state --jq '.state'` に変更した（`--jq` は整形より前の生 API レスポンスに対して評価されるため影響を受けない）
- **Medium（timeout オーファン検証テストの flaky）**: `test_gh_process_is_not_orphaned_after_timeout` が `subprocess.run`（hook 完了までブロック）の後で stub の pid file 出現を確認していたため、`-n auto` の並列負荷下ではスケジューリング遅延で stub が起動する前に timeout kill が先に走り、「stub が起動しなかった」と誤って flaky に落ちることを実測で確認（`test_push_command_parse.py` と同時実行で再現）。`Popen` に切り替え、hook がまだ timeout 待ちをしている間に pid file の出現を確認する形にし、timeout も 1 秒 → 3 秒にした
- **Medium（command-start 限定判定が実行される push を過度に見逃す）**: `_COMMAND_START_SEPARATORS` に `)` `;;` `{` を追加し、`(cd /tmp) && git push ...` / `case x in a) git push ...;; esac` / `{ git push ...; }` のような、実 bash が実際に実行する compound command 内の push を拾えるようにした（`find_optout` の受理面には影響しない別集合として追加）。また、除外対象 flag（`--dry-run` 等）を伴う command-start push が最初に見つかった場合に、そこで諦めず続きを探すようにした（`git push --dry-run origin main && git push origin main` のように、除外対象の後に本物の push が続く形を見逃さない）。`then`/`do`/`else`/`elif`/`!` などの shell 予約語直後、および `timeout`/`time`/`nohup`/`sudo` のようなコマンド前置ラッパー直後は対応を見送り、Known limitations に明記した（fail-safe 側 = nudge が出ないだけで安全側）
- **Low（記述精度）**: `_hash8` の comment が「非 0 終了は block 扱い」と書いていたが、正しくは「終了コード 2 が block 扱い」（他の comment・changelog とも整合させた）。また `push_command_parse.py`/`test_push_command_parse.py` の新設 2 関数の由来コメントが「独立レビュー指摘」になっていたが、正しくは「人間レビュー指摘」（独立レビューとは別枠）だったため訂正した
- **Low（test assertion の強化）**: `assertIn("gdd-pr-review-followup", ctx)` は文字列として `"pr-review-followup"` を包含するため、直後の `assertIn("pr-review-followup", ctx)` はほぼ何も追加検証していなかった。汎用名が active 以外の分岐として独立に出現することを、より具体的な文言（`"それ以外では pr-review-followup"`）で固定した。文言の条件法テストも `assertNotIn("push しました", ...)` だけでなく `assertIn("成功した場合", ...)` を追加した

#### 人間レビュー round 2 対応（PR 旧#88、head `03c2e8c`＝上記 round 1 是正 + 独立レビュー round 4 是正の後に対する再レビュー）

上記2つの是正を経た commit に対する再レビューで High 1 件・Medium 5 件の指摘を受け、同じ push で全件是正した（`mergeStateStatus` は既に CLEAN、round 1 の High 2 件は解消済みと確認された上での指摘）。

- **High（先頭が `-` の branch 名が `gh` の flag になる）**: 全桁数字の branch 名は既に弾いていたが（独立レビュー 3 巡目）、先頭が `-` の branch 名は弾いていなかった。`"$BRANCH"` を `gh pr view` へ素のまま渡すと、`--repo=attacker/repo` のような branch 名（hostile clone の HEAD がこの ref 名を指す形。`git branch`/`checkout -b` は `check-ref-format` で拒否するが、`update-ref` + `symbolic-ref` の低レベル操作では実 git でも作成でき、`rev-parse --abbrev-ref HEAD` はそのまま返すことを実測確認した）が `gh` 自身のグローバル flag として解釈され、認証付き問い合わせの宛先を push 対象 repo の作者が選べてしまっていた。`gh pr view --json state --jq '.state' -- "$BRANCH"` のように全 flag の後に `--` を置き、`$BRANCH` を常に positional 引数だけとして渡すよう修正した（実 gh で実測確認: `--` 以降は先頭が `-` でも常に literal な branch 名として扱われる。`--` の位置は `--json`/`--jq` より後でなければならない — 前に置くとそれらの flag 自体が positional 扱いになって壊れる）
- **Medium（`{`/`)`/`;;` 検出面の拡大と opt-out/cd 解決の非対称）**: 独立レビュー round 4 で push 検出（`is_git_push_at_command_start`）だけ `{`/`)`/`;;` を command-start に含めて拡大した結果、opt-out 判定（`find_optout`）と cd 解決（`_find_cd_root` → `resolve_candidate_roots`）は既定の狭い集合のままだったため、nudge hook 内で「push とは判定するが opt-out は無視する」（`{ GDD_SKIP_PRE_PUSH_GATE=1 git push ...; }` / `case` 腕）「push とは判定するが誤った root で `gh` を呼ぶ」（`{ cd /other/repo; git push; }`）非対称が生まれていた。`find_optout` に `separators`、`_find_cd_root`/`resolve_candidate_roots` に `separators`/`cd_separators` 引数を追加し、nudge hook の呼び出しだけ widened な集合（`PUSH_DETECTION_COMMAND_START_SEPARATORS` / `PUSH_DETECTION_CD_SEPARATORS`）を明示して渡すようにした。両関数の**既定値は変えていない**ため、`run-pre-push-gate-hook.sh`（block gate）の受理面・cd 解決は影響を受けない
- **Medium（テストの env leak で除外系 regression test が空振りしうる）**: `test_review_followup_nudge_hook.py::_run_hook` は `os.environ.copy()` をそのまま使っていたため、テストを実行するシェル自身の環境に `GDD_SKIP_PRE_PUSH_GATE=1` 等が残っていると hook プロセスへ継承され、「対象コードで正しく除外された」のか「環境の opt-out で早期に抜けただけ」なのかテストが区別できなくなりうる状態だった。`_run_hook` で `GDD_SKIP_PRE_PUSH_GATE` / `GDD_HOOK_STATE_DIR` / `GDD_REVIEW_FOLLOWUP_*` の 6 変数を `extra_env` 適用前に pop するようにした
- **Medium（引用符内の埋め込み改行が command-start と誤認される）**: `tokenize_with_boundary` は生の改行を先に区切り token として残すため、`echo "手順\ngit push origin x\nです"` のように command 文字列自体に literal な改行が入っている形は、引用符の対応が壊れた状態で分割され、引用符内の行頭 `git push` が command-start と誤認されることを実測で確認した。heredoc 本文内の行頭一致（既存の Honest Limitations）と同じ根本原因（行分割が引用符状態を見ない）の別表れであり、真の fix には共有 tokenizer 全体に影響する quote-aware な書き換えが要る。fail-safe 側（余計に `gh` を呼ぶだけで push は block しない）の過検出であるため、tokenizer の書き換えは見送り、docstring と本 changelog（下記 Known limitations）に開示するに留めた。現状の（誤）挙動を pin する regression test を残した
- **Medium（`command -v` と実行時の binary 解決先の不一致）**: `command -v "$GH_BIN"` は hook 自身の起動 cwd（PROCESS_CWD）で解決していたが、実行は `( cd "$ROOT" && "$GH_BIN" ... )` で push 対象 repo（untrusted の可能性がある）に cwd を移した後だった。`$GH_BIN` が相対名（既定 `gh`）かつ PATH に `.`（カレントディレクトリ）を含む環境では、存在確認した実体と実際に実行される実体が別物になりうる（`cd` 後の再解決は `cd` 後の cwd を基準にするため）。この plugin で初めて untrusted repo を cwd にして外部バイナリを呼ぶ形だった。`command -v` による解決を起動 cwd で一度だけ行い、以後はその絶対パス（`GH_RESOLVED`）だけを実行するよう修正した（絶対パスは PATH 経由の再解決を経ないため、`cd` 後の cwd に依存しない）。**この修正は不完全だった（round 3 で是正、下記参照）**: `command -v` 自体が相対パスを返す場合（PATH に `.` があり、かつ起動 cwd 自身に `gh` があるケース）を見落としていた
- **Medium（後続可、常時 High と同型の穴）**: `_hash8` は round 1 で `|| true` を付けたが、`_log_event` 内の `date -u +%Y-%m-%dT%H:%M:%SZ` は裸のままだった。壊れた `date` が非 0 終了すると `set -euo pipefail` 下でこの代入自体が非 0 で終了し、advisory な log 記録の失敗が hook 全体の終了コードへ伝播しうる（実 `date` ではまず起きないが、`_hash8` の High-1 と同型の穴のため、後続可の指摘だったが同じ push で吸収した）。`|| true` を追加した
- **Low（changelog の記述が実装と食い違う）**: 本ファイルの `gh pr view <branch> --json number,url,state` という記述が、round 1 の是正（`--json state --jq '.state'`）後の実装と食い違っていた。記述を実装に合わせて更新した

#### 人間レビュー round 3 対応（PR 旧#88、head `e3488de`＝上記 round 2 是正の後に対する再レビュー）

round 2 の是正を経た commit に対する再レビューで High 1 件・Low 1 件の指摘を受け（Medium 1 件は残存の引用符内埋め込み改行 gap の再確認で、この push での必須修正にはしないと明示された）、同じ push で全件是正した（`mergeStateStatus` は CLEAN、round 2 の High「先頭 `-` の branch」は解消済みと確認された上での指摘）。

- **High（`command -v` が相対パスを返すケースが未解消だった）**: round 2 の「起動 cwd で一度だけ絶対パスへ解決する」修正は、`cd` 後に `$GH_BIN` を**再解決**する経路は塞いだが、`command -v` 自体が返す値が絶対パスとは限らないことを見落としていた。`command -v` は PATH の各要素を単に前置して候補を返すだけなので、PATH に `.` / 空要素 / 相対ディレクトリが含まれ、かつそこに `gh` という名前の実行可能ファイルがあると、`./gh` や `bin/gh` のような**相対パス**を返す（実測確認済み: `PATH=".:$PATH"` かつ起動 cwd に `gh` がある場合に再現）。その相対パスをそのまま `( cd "$ROOT" && "$GH_RESOLVED" ... )` で実行すると、実行時点の cwd（= `cd` 後の `$ROOT`。push 対象 repo で untrusted の可能性がある）を基準に再解決され、round 2 が防ごうとした攻撃面がそのまま残っていた。PreToolUse はユーザーが push を承認する前に実行されるため、承認前に untrusted repo 由来のバイナリが動きうる。`GH_RESOLVED` が `/` で始まらない（絶対パスでない）場合は「見つからない」と同じ fail-safe（`gh` を呼ばず `undeterminable`、reason: `gh-not-absolute`）に倒すよう修正した。起動 cwd に実行可能な `gh` を置いた regression test（`test_relative_gh_resolution_is_rejected_not_executed`）を追加し、修正前のコードに対して実際に注入まで進んでしまう（テストが red になる）ことを確認してから、修正後に green になることを確認した
- **Low（後続可、同じ push で吸収）**: `date +%s` が失敗すると既存の fallback で `NOW_EPOCH="0"` になるが、これをそのまま TTL 比較（`10#$NOW_EPOCH - 10#$_cached_epoch <= 10#$_ttl`）に使うと `0 - _cached_epoch`（大きな負数）が常に `<= _ttl` を満たしてしまい、どれだけ古いキャッシュでも期限切れにならなくなっていた。`NOW_EPOCH` が `"0"` のときはキャッシュ読みの分岐自体を無効化し、毎回 fresh に `gh` を呼ぶ縮退にするよう修正した。cache 書き込み自体は行うが、そのエントリの epoch は `0` になるため、`date` が正常に戻った後の比較（`now - 0` は常に巨大な値）で常に期限切れ扱いになり、書き込んだ値がそのまま再利用されることはない（独立レビュー round 5 で、修正当初のこの一文が「`date` が正常に戻ればそのキャッシュが有効に使われる」と誤って書いていた指摘を受け、訂正した。下記「独立レビュー round 5」参照）。regression test（`test_broken_date_does_not_reuse_stale_cache_forever`）を追加した
- **Medium（引用符内の埋め込み改行、残存を再確認）**: round 2 で開示した引用符内の埋め込み改行 / heredoc 行頭の gap は今回も残存が確認されたが、レビュー側から「tokenizer の見送りは妥当。受け入れた限界として PR 本文にも書く。今回の必須修正にはしない」と明示されたため、対応は行っていない（PR 本文・changelog の Known limitations に開示済み）

#### 独立レビュー round 5（上記「人間レビュー round 3 対応」の修正自体を対象とした自己レビュー、diff-only / read-only / 経緯非共有 / model: Opus 5 + effort=max。ユーザー指示「セルフレビューしてから push」の順序を確保するため、round 3 是正の push 後に追加で実施した）

`git diff 03c2e8c..HEAD`（round 2 是正の直後 = 直前の独立レビュー round 4 の対象範囲の続き）を対象に実施し、`high: 0, medium: 0, low: 4, blocking: 0` を得た。Low 4 件のうち 3 件を同じ push で吸収し、1 件は fail-safe 方向・contrived な入力のため開示のみとした。

- **Low（未来日付の cache entry が無期限に再利用される）**: round 3 で是正した `NOW_EPOCH="0"`（`date` 失敗時）と同じ根本原因（TTL 比較 `now - cached_epoch <= ttl` が負数側に倒れると常に「期限内」になる）が、cache に書き込まれた epoch が**未来**の場合にも起きることを検出（実 `date` が一時的にシステムクロックのずれ — RTC 復旧直後の VM/container 等 — で未来の時刻を返した場合に発生しうる。`date` 自体は正常に動いている点で round 3 の `NOW_EPOCH="0"` ケースとは異なる)。`NOW_EPOCH` が cache の epoch より小さい場合はそのエントリを無条件に無効（未来日付＝壊れている）として扱うガード（`(( 10#$NOW_EPOCH >= 10#$_cached_epoch ))`）を追加した。regression test（`test_future_dated_cache_entry_is_not_reused`）を追加した
- **Low（round 3 是正コメント・changelog の記述誤り）**: round 3 で `NOW_EPOCH="0"` 是正時に付けたコメント・本 changelog の記述が「`date` が正常に戻ればそのキャッシュ（epoch=0 で書かれたもの）が有効に使われる」と書いていたが誤りだった。`date` が正常に戻った後の比較は `now - 0`（常に巨大な値）で常にTTL超過＝期限切れ扱いになるため、epoch=0 で書かれたエントリが再利用されることはない（挙動自体は既に正しく、記述だけが誤っていた）。hook のコメントと本 changelog（上記「人間レビュー round 3 対応」参照）を訂正した
- **Low（test の fail-safe assertion が kill switch 下で vacuous green になりうる）**: `ReviewFollowupNudgeHookTests` の大半のテストは `HOME` を上書きせず実行環境の `HOME` を継承する。`gdd_kill_switch_active`（kill-switch.sh）は `${HOME}/.claude/gdd-hooks-disabled` の存在だけで hook 全体を即 no-op にするため、テスト実行環境にそのファイルが存在すると、本クラスの fail-safe 系 assertion（`gh` を呼んでいないこと・注入されていないこと）が「対象コードが正しく除外/是正した」からではなく「kill switch で hook 自体が即抜けた」だけで軒並み vacuous green になりうる（`test_kill_switch_suppresses_injection` 自身は明示的に別の `HOME` を使うため対象外。medium ではなく low とした理由: 同クラスの positive-assertion テストは kill switch 下では逆に失敗するため、テスト全体としては黙って green にはならない）。`setUpClass` で kill switch file の存在を事前検出し、存在する場合は誤った安心感を避けるため `unittest.SkipTest` でテストモジュール全体をスキップするガードを追加した
- **Low（後続可、対応は見送り）**: opt-out 抑制の非対称（`find_optout` が widened separators 下で dry-run push に付いた opt-out prefix を拾い、後続の本物の push への nudge まで抑制しうる）を検出。fail-safe 方向（注入が減るだけで block はしない）かつ contrived な入力のため、対応は見送り、上記「Known limitations」の既存 `find_optout` 関連の記述に追記する形で開示した（round 4 で検出・見送り済みの逆方向ギャップの姉妹指摘）

#### 人間レビュー round 4 対応（PR 旧#88、head `52a0a88`＝上記「独立レビュー round 5」是正の後に対する再レビュー）

round 5 の是正を経た commit に対する再レビューで High 1 件・Medium 2 件の指摘を受け、同じ push で全件是正した（`mergeStateStatus` は CLEAN、round 3 の High「`command -v` 相対パス」は解消済みと確認された上での指摘）。

- **High（`review-log/` の欠落。main 取り込み時に `validate-plugin.sh` が FAIL する）**: `origin/main` には本 PR のブランチ分岐後に X-52（`review-log/` 強制、`tests/checks/review-log-present.sh`）が別途取り込まれており、`changelog.d/` の断片ごとに対になる `review-log/<同じファイル名>` が無いと `validate-plugin.sh` の `review-log-present` チェックが FAIL する（本ブランチの merge-base はこの機能導入より前のため、現時点ではこのチェック自体がまだ見えていないが、main を取り込んだ時点で発火する）。軽いレーンの巡記録（`## 巡` / `## 指摘` / `pr:`）自体も X-52 の正本であり、mechanical gate の有無に関わらず記録すべきものだった。`review-log/20260915-x58-x59-review-followup-nudge.md` を新設し、本 PR の独立レビュー1〜6巡・人間レビュー1〜4巡の全指摘を X-52 書式（frontmatter `lane`/`pr`、`## 巡`表、`## 指摘`表）で記録した
- **Medium（opt-out 抑制の非対称、dry-run prefix 形の具体例）**: 上記「独立レビュー round 5」で開示した opt-out 抑制の非対称（`find_optout` の内部 `is_git_push` 最初の一致が、nudge hook が実際に検出した push と食い違いうる）について、Known limitations の記述が `echo git push foo && GDD_SKIP_PRE_PUSH_GATE=1 git push origin bar` のような非 push テキストが前にある形だけを例示しており、`git push --dry-run origin x && GDD_SKIP_PRE_PUSH_GATE=1 git push origin x` のような、side-effect-excluded な**本物の push**（dry-run）が前にある形（同じ根本原因の別の具体例）を明示していなかった。根本原因・対応方針（fail-safe 方向・対応は見送り）自体は round 5 の判断から変わらないため、コード修正は行わず、Known limitations の該当箇所にこの具体例を追記した
- **Medium（`gh` が exit 0 で想定外の state を返すと no-pr として確定キャッシュする）**: 「判定不能は undeterminable として記録し no-pr と誤判定しない」という fail-safe の契約が、これまで `gh` の非 0 終了・認識済みエラー文言にしか適用されていなかった。`gh pr view --json state --jq '.state'` が exit 0 でも、state が GitHub の PR state enum（`OPEN`/`MERGED`/`CLOSED`）のいずれでもない場合（`--jq` の出力異常・API 応答の想定外の形等）、「`OPEN` ではない」を無条件に `no-pr` と断定し 300 秒キャッシュしていた。既知の3値だけを確信を持った分岐にし、それ以外（空文字列を含む）は `undeterminable`（reason: `gh-unexpected-state`）に倒すよう修正した。regression test（`test_gh_exit_zero_with_unexpected_state_is_undeterminable_not_no_pr`）を追加し、修正前のコードでは実際に `no-pr` に誤分類される（テストが red になる）ことを確認してから、修正後に green になることを確認した

#### 独立レビュー round 6（上記「人間レビュー round 4 対応」の修正自体を対象とした自己レビュー、diff-only / read-only / 経緯非共有 / model: Opus 5 + effort=max。ユーザー指示「セルフレビューしてから push」の順序を確保するため、round 4 是正の push 前に実施した）

`git diff 52a0a88..HEAD`（独立レビュー round 5 の直後からの差分）を対象に実施し、`high: 0, medium: 0, blocking: 0` を得た（case 文の fail-safe 化・regression test の非空虚性・`review-log/` の X-52 書式適合性を、実際に `origin/main` の checker script を取得して実行する形で独立に検証済み）。Low 1 件を同じ push で吸収した。

- **Low（`review-log/` の `独立-1` 行が本 changelog の記述と矛盾していた）**: `review-log/20260915-x58-x59-review-followup-nudge.md` の `独立-1` 行を `high=1/medium=5/blocking=0`（X-52 の severity 値域に blocking が無いため、STATE_DIR crash を severity=high として再記録）としたが、本 changelog の「効果の再計測手順」直前の検証サマリ行は「1 巡目 high=0/medium=5/blocking=1」（当時の独立レビュー原文の表記）のままで、2つのドキュメントが同じ巡について食い違っていた。review-log の書式は checker（`review-log-present.sh`）が high/medium と指摘表の対応を検証するため変更できない一方、changelog 側は表記の正本ではないため、changelog 側を review-log に合わせて修正し、表記統一の経緯（severity 値域に blocking が無いための再分類である旨）を注記した（上記「Validation / Eval Impact」参照）

#### 人間レビュー round 5 対応（PR 旧#88、head `ea6e32d`＝上記「独立レビュー round 6」是正の後に対する再レビュー。新しい commit を追加していない tip に対する再レビューで、`mergeable` が main 側の別 PR 取り込みにより CONFLICTING に変化していたことを検出）

round 6 の是正を経た commit（tip は変わらず）に対する再レビューで High 1 件・Medium 1 件の指摘を受け、同じ push で全件是正した。

- **High（`origin/main`（`30aaa51`、PR 旧#91）と `hooks/hooks.json` で衝突）**: 本 PR のブランチ分岐後、main 側で別 PR（X-61 Agent dispatch model gate 等）が `hooks.json` の `PreToolUse.Agent` matcher を新設しており、本 PR が同じファイルの `description` フィールドと `PreToolUse.Bash` matcher（`review-followup-nudge-hook`）へ加えた変更と衝突していた（`git merge-tree --write-tree` で確認、衝突は `description` の 1 箇所のみ）。`origin/main` を取り込み、`description` を両ブランチの列挙を統合して再採番した（機械マージ後: 7 matcher / 11 hook。hook 本数の自己整合は `tests/test_pre_push_gate_contract.py::test_description_hook_count_matches_actual_pre_tool_use_wiring` が `hooks.json` から機械導出して検証する）。あわせて `README.md` の「6 matcher / 10 hook」表記（main 取り込み前の本ブランチ単独の値のまま）も「7 matcher / 11 hook」に更新した（main 自身の同表記が既に「6 matcher / 8 hook」で pre-existing にずれていたことも確認したが、これは本 PR と無関係な main 側の既存ドリフトのため対象外とした）
- **Medium（`(cd /repo); git push` のように区切り文字が空白無しで連続する形が検出されない）**: `shlex(punctuation_chars=True)` は隣接する punctuation（`();<>|&`）を無条件に 1 token へ集約するため、`)` と `;` が空白無しで隣接すると `");"` という未知 token になり、`COMMAND_SEPARATOR_TOKENS` との完全一致を要求する `_at_true_command_start`（`is_git_push_at_command_start` / `find_optout` / `_find_cd_root` が共有）が git push を command-start と判定できず、nudge を取りこぼす（fail-open。block はしないため実害は「取りこぼし」のみ）。個別の separator 集合に `");"` 等を追加する対症療法ではなく、tokenizer の根本（`git_command_parse.py::_lex_segment`）に punctuation だけの token を実 bash の演算子境界まで再分割する処理を追加して is_git_push_at_command_start / find_optout / _find_cd_root を一括で正した**当初の実装**は、token 列全体を書き換えたことで別の退行を生んだ（下記「独立レビュー round 7」で発見・是正。最終的には `token_ends_with_separator` によるコマンド先頭判定専用の局所的な再解釈に切り替えている）。regression test（`test_accepts_push_after_glued_separator_cluster`）で `);` `;;` `))` `&&` `||` の5形を固定した

#### 独立レビュー round 7（上記「人間レビュー round 5 対応」の修正自体を対象とした自己レビュー、diff-only / read-only / 経緯非共有 / model: Opus 5 + effort=max。ユーザー指示「セルフレビューしてから push」の順序を確保するため、round 5 是正の push 前に実施した）

`git diff 9f90d56..HEAD` のうち round 5 対応で変更したファイルに絞って実施し、high 2 件（うち blocking 相当 2 件）・medium 3 件・low 2 件・advisory 2 件の指摘を受けた。high 2 件は同じ push で全件是正した（実 bash での再現確認込み）。medium のうち 2 件は同じ是正で解消、1 件はテスト追加で解消、1 件は対応不要と判断した。low・advisory は開示のみ。

- **High/blocking（root-branch guard の segment 分割が deny→allow に退行）**: round 5 の Medium 是正（上記）で、punctuation だけの token を実 bash の演算子境界まで再分割する処理を token 列全体（`_lex_segment`）に適用していた。この結果、`&>`（stdout+stderr をまとめてリダイレクトする複合演算子）が `&`（区切り）+ `>` に誤分割され、`git switch &>/dev/null -c <branch>` のような入力で `validate-worktree-command.py` の segment 分割が git を含む segment から `-c` flag・branch 名を切り落とし、root-branch guard（block する guard）が実行対象の branch 作成コマンドを認識できなくなっていた（実 bash では実際に branch が作られることを確認済み。修正前は deny、修正後は無言 allow だったことも実測）
- **High/blocking（pre-push gate の refspec 曖昧判定が block→非block に退行）**: 同じ根本原因で、`classify_refspec`（AC-16）が `git push &>/dev/null --all origin` のような入力で `--all` flag の手前で走査を打ち切り、`ambiguous=False` に誤判定していた（実 bash はこのコマンドで `--all` push を実行するため、本来 block すべき入力が非 block になっていた）
  - 是正: token 列そのものは変更せず（`_lex_segment` を元の実装に戻し）、コマンド先頭判定（`is_git_push_at_command_start` / `find_optout` / `_find_cd_root`）専用の局所的な再解釈として `git_command_parse.py::token_ends_with_separator` を新設し、push_command_parse.py の3箇所をこれに差し替えた。これにより block する guard（root-branch guard・refspec 曖昧判定）は元の（無変更の）token 列をそのまま見るため退行しなくなる。RED/GREEN で両方の退行を実バグ再現→是正確認した上で、regression test を `test_push_command_parse.py`（`test_glued_redirect_operator_does_not_truncate_refspec_scan`）と `test_root_branch_deny_corpus.py`（`ROOT_BRANCH_DENY_CORPUS` に `&>` glued 形を追加、56→57件）に追加した
- **Medium（self-review evidence の照合対象ずれ）**: 同じ根本原因で `explicit_ref` 解決も誤解決されうる（`git push &>/dev/null origin feature-x` が HEAD 扱いになる）。上記と同じ是正で解消した
- **Medium（docstring の前提矛盾）**: `is_redirection_operator` 等の docstring が「shlex は演算子文字の連続を 1 token に集約する」前提を記述しており、token 列全体への再分割を適用していた間は実装と矛盾していたが、token 列を変更しない方式へ戻したことで前提が再び成立するため、docstring 側の修正は不要と判断した
- **Medium（fail-open 側の regression test 不足）**: block/allow を変える修正に fail-open 側のテストが無く、既存テストは上記2件の退行を素通ししていた。上記の regression test 追加で解消した
- **Low（2件、開示のみ）**: `_lex_segment` の `except ValueError` フォールバック（`segment.split()`）は punctuation の癒着解消の対象外のまま（環境依存の低頻度経路のため対応は見送り）。クォートで囲まれた punctuation だけの引数（例: `-m ');'`）が command-start 判定で誤って「区切り直後」と認識されうる（過検出方向。本 hook は block しないため実害は限定的と判断し対応は見送り）
- **Advisory（2件）**: 姉妹実装 `gh_command_parse.py`（merge gate）は演算子文字集合への membership 判定で解いており癒着 punctuation に構造的に免疫がある旨の指摘（今回の方式は `_TWO_CHAR_OPERATORS` の完全性に依存しない設計にしたため実装方式の転換は見送り）。`_TWO_CHAR_OPERATORS` のコメントが「貪欲マッチの優先順」と誤解を招く表現だった点はコメントを修正した

#### 人間レビュー round 6 対応（PR 旧#88、head `d7597ab`＝上記「独立レビュー round 7」是正の後に対する再レビュー。新しい commit を追加していない tip に対する再レビュー）

High 2 件の指摘を受けた（レビュー本文の独立レビュー形式サマリ行は medium 3 件も宣言していたが、本文には該当節が無く具体的な内容を取得できなかった。GitHub API で review 本体・pull request comments の両方を確認済み。対応不可のため開示に留める）。**同じ「glued punctuation」クラスタの high が独立レビュー round 7 に続き 2 巡連続で出たため、house rule（CLAUDE.md L1+ 安全策4）に従い修正を続けずユーザーへ修正方針を確認した**（AskUserQuestion。3 択のうち「nudge 側の局所述語に完全に閉じる」を選択）。

- **High/blocking（round 7 是正が実装として不完全だった: `_lex_segment` の token 列全体再分割が実際には残っていた）**: round 7 の是正コミット（92b85da）は commit message と docstring で「`_lex_segment` の token 列は変更しない」と主張していたが、実装は `_split_glued_punctuation` を token 列全体へ適用するループを削除しておらず、主張と実装が食い違っていた。`_TWO_CHAR_OPERATORS` に無い演算子（noclobber 上書き付き redirect 演算子 `>|` 等）を glue すると、依然として root-branch guard の segment 分割が deny→allow に退行することを実 bash とガードの両方で再現確認した（`git switch >|/dev/null -c <branch>` は実 bash で branch を作成するが、ガードは git を含む segment と後続引数の segment とに分断していた。round 7 の regression test は `&>` 1 リテラルのみを固定しており、この class の再発を検出できなかった）
- **High/blocking（`token_ends_with_separator` が block gate の opt-out・cd 解決の受理面まで広げていた）**: round 7 で新設した `token_ends_with_separator`（glued punctuation の局所再解釈）が、nudge hook 専用のつもりだった `is_git_push_at_command_start` だけでなく `find_optout`/`_find_cd_root`（block gate である run-pre-push-gate-hook.sh と共有）からも呼ばれる構造になっていた。`>|GDD_SKIP_PRE_PUSH_GATE=1 git push` のように、実 bash では redirect 演算子がファイル名として環境変数代入を消費するだけで opt-out が立たないコマンドが、演算子の末尾文字を区切りと誤って再解釈することで opt-out として受理されてしまっていた（同型で `_find_cd_root` も実行されない `cd` を候補 root にし、無記録の exit 0 という fail-open になりうる状態だった）
  - 是正: `_lex_segment` を実際に「token 列を一切再分割しない」元の形へ戻した。`find_optout`/`_find_cd_root` は `token_ends_with_separator` を使わず `token in separators` の完全一致に戻し、glued punctuation の再解釈は block しない `is_git_push_at_command_start`（nudge hook 専用、呼び出し元はこの1関数に限定）だけに使う設計にした。これにより block する guard（root-branch guard の segment 分割・refspec 曖昧判定・opt-out 受理・cd root 解決）は、いずれも `_TWO_CHAR_OPERATORS` の完全性に一切依存しなくなる。RED/GREEN で両方の退行を実バグ再現→是正確認した上で、regression test を3件追加した: `test_push_command_parse.py` に単一リテラルではなく `_TWO_CHAR_OPERATORS`/実区切りのいずれにも属さない全ての2文字 punctuation の組み合わせについて segment 分割が壊れないことを固定する property test（`test_unknown_glued_punctuation_never_splits_git_segment`）、opt-out 過検出の regression test（`test_rejects_optout_disguised_by_unenumerated_glued_redirect`）、cd root 過検出の regression test（`test_rejects_cd_root_disguised_by_unenumerated_glued_redirect`）。`test_root_branch_deny_corpus.py` にも `>|` glued 形を実 bash 相当のケースとして1件追加した（57→58件）

#### 独立レビュー round 8（上記「人間レビュー round 6 対応」の修正自体を対象とした自己レビュー、diff-only / read-only / 経緯非共有 / model: Opus 5 + effort=max。対象は `git diff 92b85da..HEAD -- . ':(exclude)review-log/'`。`review-log/` を diff から除外したのは、除外しないと reviewer が前巡の指摘を読んでしまい独立レビューの契約1（実装文脈を渡さない）が壊れるため）

high=0/medium=2/blocking=0。同一クラスタの high・blocking が 2 巡続くことはなく（L1+ 安全策4 の対象外）、medium 2 件はいずれも本 PR の差分ではなく `origin/main` 上で同一に再現することを、対象ファイルの `origin/main` 版を `/tmp/main_probe/` に取り出し同じ再現コマンドを実行して実測確認した（本 PR が新たに持ち込んだ退行ではなく、既存の base tokenizer / 優先順位設計の既知の限界）。house rule「実装中に見つけた別の問題は差分に入れず、再現手順を添えて後続課題にする」に従い、いずれも是正せず後続課題として開示のみに留めた（下記 Known limitations 参照）。他に low（低頻度コメントの陳腐化 1 件）・advisory（テストのハードコーディング 1 件）を受け、両方とも同じ push で是正した。

- **Medium（`);cd /tmp/evil && ...` のように `cd` root 候補の直前が `)` と `cd` の間に空白が無く連続する形で `_find_cd_root` が候補を取りこぼす、`origin/main` でも同一再現・後続課題）**: `token in separators` の完全一致判定は `);cd` のような glued token を区切りとして認識できないため、本来候補にすべき `cd` が `_find_cd_root` に拾われない（fail-safe 方向。block する `run-pre-push-gate-hook.sh` は候補を落とすだけで、誤って block を回避する方向にはならない）。`origin/main` の `push_command_parse.py`/`git_command_parse.py` を `/tmp/main_probe/` に取り出し同じ入力で再現し、本 PR の差分に起因しない既存の限界であることを確認した
- **Medium（POSIX quote で囲まれた opt-out prefix のクォート剥離により `find_optout` が意図しない形も受理しうる、`origin/main` でも同一再現・後続課題）**: shlex の POSIX クォート剥離により、opt-out prefix の実引用符表現が受理集合を広げうる。`origin/main` で同一に再現することを確認した（本 PR 差分起因ではない）
- **Low（`_TWO_CHAR_OPERATORS` のコメントが古い前提を残していた）**: 人間レビュー round 6 の是正で `find_optout`/`_find_cd_root` を `token_ends_with_separator` から切り離したにもかかわらず、`_TWO_CHAR_OPERATORS` のコメントが round 7 時点の「block gate 側の受理面にも影響しうる」という前提のまま残っていた。影響範囲が nudge 検出のみに縮小されたことと、H1/H2 是正の経緯を明記するようコメントを更新した（`git_command_parse.py`。挙動変更なし）
- **Advisory（`test_unknown_glued_punctuation_never_splits_git_segment` が除外集合をテスト内にハードコードしていた）**: `known_two_char_operators`/`real_separators` をテスト側に複製していたため、正本（`git_command_parse.COMMAND_SEPARATOR_TOKENS`/`_TWO_CHAR_OPERATORS`）が変わってもテスト側が追従せず drift しうる指摘。正本から直接参照する形に変更した（`test_push_command_parse.py`。挙動変更なし、39 subtests は変わらず pass）

#### 人間レビュー round 7 対応（PR 旧#88、head `e258d32`＝上記「独立レビュー round 8」是正の後に対する再レビュー）

high=0/medium=0/low=5。round 6 の High 2 件（H1/H2）が解消済みであることと、`mergeable: MERGEABLE`/`mergeStateStatus: CLEAN` を確認した上で、block gate 入口 442 ケースが `origin/main` と差分ゼロであることも確認済みとされた。Low 5 件はレビュー側から明示的に「後続でよい」と評価されたが、コードに触れない純粋なテキスト修正で吸収できるものは同じ push で是正した（house rule「advisory・low は既定で後続 PR に回す。取り込むのは、同じ push で吸収できる場合」に該当）。

- **Low（changelog 冒頭の test 件数・hook 本数が後続ラウンドの値と食い違っていた）**: `#### Added` セクションの「9 本 → 10 本」（人間レビュー round 5 対応の main 取り込みで 7 matcher / 11 hook へ再採番済み）、「108 → 139 tests」（その後の各ラウンド対応で最終 108 → 144 tests まで増加済み）が、当時の値のまま更新されておらず、読者が古い数値を最終値と誤読しうる状態だった。両箇所に「この時点の値」である旨と最終値への参照を追記した（挙動変更なし）
- **Low（PR 本文の hook 実装説明が実装と食い違っていた）**: PR 本文が push 検出後の PR 有無判定を `gh pr view --json number,url` と説明していたが、実装は人間レビュー round 2 対応（MERGED/CLOSED PR にも注入していた不具合の是正）で `gh pr view --json state --jq '.state'`（state が OPEN のときだけ注入）に変更済みで、PR 本文側が追従していなかった。PR 本文を実装に合わせて修正した
- **Low（`bash -c 'git push …'` 経由の push を nudge が検出できないことが Known limitations に未記載）**: `is_git_push_at_command_start` は生の command 文字列の token 列を command-start から走査する設計のため、`bash -c '...'` の引数文字列内に埋め込まれた `git push` は検出できない（fail-safe 方向。nudge が出ないだけで `gh` は呼ばれず block もしない）。この限界自体は design.md § Honest Limitations が列挙する「間接実行」の一種で既存の限界だが、Known limitations に明示されていなかったため追記した（対応は見送り。対応不要の判断根拠: 間接実行の網羅は他の既知の限界と同様に際限が無いため）
- **Low（opt-out skip ログの repo hash が他イベントと異なる基準を使っている）**: `run-review-followup-nudge-hook.sh` の `skipped(optout)` イベントは opt-out 判定（step 3）が root 解決（step 4）より前に走るため `$PROCESS_CWD` をハッシュ化してログに残すが、`injected`/`skipped(no-pr)`/`undeterminable` は解決済みの `$ROOT`（`-C`/`cd`/payload/process の優先順位で解決した実際の対象 root）をハッシュ化する。明示 `-C` や `cd` を伴う push では両者が異なる値になり、同一 repo への push でもイベント種別によって repo hash が食い違いうる（ログの相関付け精度の限界。opt-out 判定自体の正しさ・block/allow には影響しない）。Known limitations に追記した。ログの相関付け以外に実害が無いこと、順序を入れ替えるとステップの責務分離（opt-out 判定に root 解決を前提させない設計）が崩れることから、対応は見送った
- **Low（`skill-count-budget.sh` の上限変更が CONTRIBUTING.md の PR evidence 要件を満たしていなかった）**: 本 PR は `BASELINE_SKILL_COUNT`/`MAX_SKILL_COUNT` を 28 → 29 に変更しており、CONTRIBUTING.md の等価交換ルールにより `SKILL_COUNT_BUDGET_CHANGE=true` と `SKILL_COUNT_REDUCTION_PLAN=<理由と削減計画>` を PR evidence として残す必要があったが、PR 本文に記載していなかった（スクリプト自体は `BASELINE_SKILL_COUNT == MAX_SKILL_COUNT` のため実行時の env var チェックには引っかからず、機械的な block は発生していなかった）。理由と削減計画はスクリプト内コメントに既に記載済みだったため、同じ内容を PR evidence として PR 本文にも追記した

#### Changed

- `skills/gdd-pr-review-followup/SKILL.md`: Goal と Fix ステップに、collect → classify → verify → fix → 独立レビュー → push → re-request の骨格・修正時規律・証跡の書き方の正本が `pr-review-followup` skill へ移ったことを示すポインタ文を追加した（既存の state.md/tasklist.md/steering/Auto-Arm/ADR distillation 等の GDD 固有部分は変更していない）
- `references/self-review-lanes.md`: 所有ヘッダーの参照元リストに `skills/pr-review-followup/SKILL.md` を追加し、「参照先を上記 3 skill に限る」を「4 skill」に更新した
- `references/independent-review.md`: 所有ヘッダーの参照元リストに `skills/pr-review-followup/SKILL.md` を追加した（`state.md` への証跡記録を要求しない旨を明記）
- `tests/checks/skill-count-budget.sh`: `BASELINE_SKILL_COUNT` / `MAX_SKILL_COUNT` を 28 → 29 に更新した（新設 skill 1 件分。既存 `gdd-pr-review-followup` との consolidation は GDD 経路の routing を壊すリスクが高いため本 PR では見送り、次回の skill 棚卸しで検討する旨をコメントに残した）
- `tests/checks/skill-body-budget.sh` / `tests/checks/lint-scripts-functional.sh`: `--max-total-skill-body-lines` を 6982 → 7068 に更新した（新設 skill の body 105 行分。「6982 → 7068」は見た目 +86 だが、6982 という既存値自体が真の origin/main 実測値 6963 より 19 行古かった（本 PR と無関係な既存ドリフト。clean clone で検証済み）ため。7068 = 実測 pre-change 総数 6963 + 105 で、post-change の実測総数と一致する。express/standard runtime profile には含まれないため、実行時トークン予算は変化しない）

#### Affected Files

- `skills/pr-review-followup/SKILL.md`（新規）
- `skills/gdd-pr-review-followup/SKILL.md`
- `hooks/scripts/run-review-followup-nudge-hook.sh`（新規）
- `hooks/scripts/lib/push_command_parse.py`（人間レビュー対応・round6対応。`find_optout`/`_find_cd_root` を `token_ends_with_separator` を使わない完全一致へ戻した）
- `hooks/scripts/lib/git_command_parse.py`（人間レビューround5対応・独立レビューround7対応・round6対応・独立レビューround8対応。`_lex_segment` を token 列無変更の元の実装へ戻し、`_TWO_CHAR_OPERATORS` のコメントを round8 指摘で更新した）
- `hooks/hooks.json`（人間レビューround5対応。main 取り込みによる `description`/matcher 再採番を含む）
- `README.md`（人間レビューround5対応。`PreToolUse` の matcher/hook 件数表記を更新）
- `references/self-review-lanes.md`
- `references/independent-review.md`
- `tests/checks/skill-count-budget.sh`
- `tests/checks/skill-body-budget.sh`
- `tests/checks/lint-scripts-functional.sh`
- `tests/test_review_followup_nudge_hook.py`（新規）
- `tests/test_push_command_parse.py`（人間レビュー対応・round5対応・独立レビューround7対応・round6対応・独立レビューround8対応。ハードコードしていた除外集合を正本から直接参照する形に変更した）
- `tests/test_root_branch_deny_corpus.py`（独立レビューround7対応・round6対応。`ROOT_BRANCH_DENY_CORPUS` に2件追加）
- `review-log/20260915-x58-x59-review-followup-nudge.md`（新規、X-52。plugin ディレクトリの外、repo root 直下）

#### User Action Required

- なし。次回の `git push` から自動的に対象になる（PR があるブランチへの push で `pr-review-followup` skill を呼ぶよう促す 1 行が注入される）

#### Known limitations

- 注入は skill 呼び出しを「促す」だけで、実際に skill を呼ぶかどうかは agent 側の判断に委ねられる（block ではない設計上の必然）。additionalContext は push 実行前（PreToolUse）に作られるため、文言は「push を検知しました。成功した場合は…」の条件法にしてある（人間レビュー対応）。X-59 の実測（skill 自発発火 24%）を注入によってどこまで引き上げられるかは、本 PR 単体では測れず、dogfood 期間を経て再計測が必要（下記「効果の再計測手順」を参照）
- push 検出は `is_git_push_at_command_start`（command-start 限定）で過検出を大きく減らしたが、design.md § Honest Limitations が列挙する検出面の限界（`<<<` herestring / パイプ経由の shell / ANSI-C quoting / 変数展開・パラメータ展開・コマンド置換による間接実行、および heredoc 本文内の行頭一致）は残る。この hook はそれらのケースでも `gh` を呼びうる（fail-safe ではなく fail-open 側の残存ギャップ。PostToolUse への移行は本 PR では見送った）。人間レビュー round 2 で、同じ根本原因（行分割が引用符状態を見ない）の別表れとして、二重引用符内に埋め込まれた実改行を含む文字列（`echo "手順\ngit push origin x\nです"` のように command 文字列自体に literal な改行が入っている形）でも引用符内の行頭 `git push` が command-start と誤認されることを追加で確認した（過検出方向。push は block しない）
- command-start 判定は `)` `;;` `{` の直後を「コマンド先頭」として扱うが、`then`/`do`/`else`/`elif`/`!` のような shell 予約語の直後、および `timeout`/`time`/`nohup`/`sudo` のようなコマンド前置ラッパーの直後は対象外にする（独立レビュー round 4 で検出。予約語・ラッパーの一覧は shell によって異なり網羅すると際限が無いため意図的に見送った）。これらの形で実行される本物の push は取りこぼす（fail-safe = nudge が出ないだけで `gh` は呼ばれない）
- opt-out（`GDD_SKIP_PRE_PUSH_GATE=1` prefix 形）の判定 `find_optout` は、command-start 限定の狭い判定とは別に、内部で `is_git_push`（広い判定）が返す最初の一致を基準に代入列を遡る。過検出源が先にあり、その後に opt-out prefix 付きの本物の push が続く形（`echo git push foo && GDD_SKIP_PRE_PUSH_GATE=1 git push origin bar` のような contrived な入力）では、opt-out が尊重されないことがある（独立レビュー round 4 で検出、Low。対応は見送った）。過検出源に限らず、side-effect-excluded な**本物の push**（`--dry-run` 等）が先にある形でも同じことが起きる（`git push --dry-run origin x && GDD_SKIP_PRE_PUSH_GATE=1 git push origin x` のような入力。人間レビュー round 4 で追加指摘。根本原因は同じ「`find_optout` の内部 `is_git_push` 最初の一致」であり、対応方針も変わらないため対応は見送った）。逆方向のギャップも同じ根本原因（`find_optout` が判定対象にする push と、nudge hook が実際に検出した push が一致するとは限らない）から生じる: round 5 で nudge hook 専用に widened な `separators` を `find_optout` へ渡すようにした結果、`{ GDD_SKIP_PRE_PUSH_GATE=1 git push --dry-run origin x; }; git push origin x` のように、除外対象（dry-run）の push に付いた opt-out prefix を `find_optout` の内部 `is_git_push`（最初の一致）が拾ってしまい、後続の本物の push（nudge hook が実際に検出・判定しようとしている push）に対する nudge まで抑制されることがある（独立レビューで検出、Low。fail-safe 方向＝注入が減るだけで block はしないため対応は見送った）
- PR 有無の判定は `gh pr view` に依存する。`gh` が未インストール・未認証の環境では常に `undeterminable` になり注入されない（ローカル情報だけで正確に判定する材料が無いため。fail-safe だが取りこぼしにはなる）
- 同一 root+branch の判定結果は既定 300 秒（`unknown` は 30 秒）キャッシュする。TTL 内に PR が新規作成された場合、次の push まで注入が遅れることがある
- push 対象 branch の解決は `<local>:<remote>` 形の colon 付き refspec では local 側の名前を使う（remote 側の branch 名には解決しない）。この形は稀だが、使われた場合は誤った branch 名で PR 有無を判定する。delete-push（`git push origin :old-branch`）は local 側が空文字列になるため現在の checked-out branch へフォールバックする（削除対象とは異なる branch の PR 有無で判定してしまう）。なお `-d/--delete` を伴う push（`git push origin --delete old-branch` 等の明示 flag 形）は人間レビュー対応で `gh` 呼び出し自体の対象外にした
- `shasum` / `sha1sum` がどちらも無い環境では repo/branch のハッシュが固定文字列 `unknown` になるため、キャッシュを無効化して毎回 `gh` を呼ぶ（キャッシュ衝突の回避を優先し、性能を犠牲にする）。人間レビュー対応で `_hash8` を「shasum/sha1sum が無い」だけでなく「PATH 上にあるが非 0 終了する」場合も同じフォールバック経路で扱うよう修正した（各コマンドの失敗を個別に無害化し、hook 全体が block 扱いの終了コードで落ちるのを防ぐ）。この縮退経路自体の contract test は無い（実測では動作確認済みだが、環境依存が強く恒久的な regression test 化は見送った）
- `GDD_REVIEW_FOLLOWUP_GH_TIMEOUT` は `hooks.json` の hook 自体の timeout（8 秒）より確実に短くするため、内部で 6 秒に頭打ちする（8 秒以上を指定しても 6 秒として扱われる。クランプ値がハードコードのため、hooks.json 側の timeout を将来変更する場合はこの定数も見直しが必要）
- push 対象 branch が全桁数字（例: `git push origin 1234`）だと `gh pr view` の引数解釈上 branch 名ではなく PR 番号として解決されるため、判定不能として抜ける（独立レビュー3巡目で検出・是正）
- 人間レビュー round 6（head `d7597ab`）は独立レビュー形式サマリ行で medium 3 件を宣言していたが、本文に `### Medium` 節・inline comment のいずれも無く、具体的な内容を取得できなかった（GitHub API で review 本体・pull request comments の両方を確認済み）。対応不可のため review-log には記録せず、ここに開示するに留める
- 独立レビュー round 8 で指摘された medium 2 件は、いずれも本 PR の差分ではなく `origin/main` 上で同一に再現する既存の限界であり、本 PR では対応していない（後続課題）
  - `_find_cd_root` は `token in separators` の完全一致判定のため、`)` と `cd` が空白無しで連続する glued token（例: `(true);cd /tmp/evil && git push origin main`）を区切りとして認識できず、`cd` root 候補を取りこぼして `payload_cwd` へフォールバックする。再現（実測確認済み）:
    ```
    python3 -c "
    import sys; sys.path.insert(0, 'plugins/gate-driven-development/hooks/scripts/lib')
    import push_command_parse as pcp
    tokens = pcp.tokenize('(true);cd /tmp/evil && git push origin main')
    is_push, git_index = pcp.is_git_push(tokens)
    print(pcp.resolve_candidate_roots(tokens, git_index, payload_cwd='/payload', process_cwd='/proc'))
    "
    ```
    → `{'roots': ['/payload'], 'unresolvable': False}`（`/tmp/evil` が候補に出ない）。block する `run-pre-push-gate-hook.sh` は候補を落とすだけで、誤って block を回避する方向にはならないため fail-safe 側の残存ギャップ
  - shlex の POSIX クォート剥離により、クォートで囲んだ区切り文字（例: `echo ';' GDD_SKIP_PRE_PUSH_GATE=1 git push origin main` の `';'`）がクォート除去後に本物の区切り token と区別不能になり、`find_optout` が「クォート内の文字列」を実際のコマンド区切りと取り違えて opt-out を過剰に受理する（実 bash では `echo` の引数の一部でしかなく、変数代入も opt-out も成立しない）。再現（実測確認済み）:
    ```
    python3 -c "
    import sys; sys.path.insert(0, 'plugins/gate-driven-development/hooks/scripts/lib')
    import push_command_parse as pcp
    tokens = pcp.tokenize(\"echo ';' GDD_SKIP_PRE_PUSH_GATE=1 git push origin main\")
    print(pcp.find_optout(tokens, original_token_count=len(tokens)))
    "
    ```
    → `{'accepted': True, 'via': 'command-prefix'}`（`origin/main` の base tokenizer が持つ既存の quote-stripping 挙動に起因し、本 PR の差分では変更していない）
- `bash -c 'git push origin main'` のように `git push` が `bash -c` の引数文字列の中に埋め込まれている場合、`is_git_push_at_command_start` は生の command 文字列の token 列を走査するため検出できない（人間レビュー round 7 で指摘）。design.md § Honest Limitations が列挙する「間接実行」の一種で、fail-safe 方向（注入が出ないだけで `gh` は呼ばれず block もしない）。同じ理由（列挙すると際限が無い）で対応は見送っている
- opt-out skip（`skipped(optout)`）イベントの repo hash ログは、opt-out 判定が root 解決より前に走る設計のため `$PROCESS_CWD` を使う一方、`injected`/`skipped(no-pr)`/`undeterminable` イベントは解決済みの `$ROOT`（`-C`/`cd`/payload/process の優先順位で解決）を使う（人間レビュー round 7 で指摘）。明示 `-C` や `cd` を伴う push では同じ repo への push でもイベント種別によって repo hash が食い違いうる（ログの相関付け精度の限界。opt-out 判定自体の正しさ・block/allow の挙動には影響しない）。ステップの責務分離（opt-out 判定は root 解決を前提しない）を優先し、対応は見送った

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 追加 contract test: `tests/test_review_followup_nudge_hook.py`（36 → 44 tests）、`tests/test_push_command_parse.py`（108 → 144 tests。round5対応で `test_accepts_push_after_glued_separator_cluster`、round7対応で `test_glued_redirect_operator_does_not_truncate_refspec_scan`、round6対応で `test_unknown_glued_punctuation_never_splits_git_segment`（property test）・`test_rejects_optout_disguised_by_unenumerated_glued_redirect`・`test_rejects_cd_root_disguised_by_unenumerated_glued_redirect` を追加）、`tests/test_root_branch_deny_corpus.py`（round7対応で `&>` glued 形、round6対応で `>|` glued 形を追加、56 → 58 件）
- 独立レビュー（read-only, diff-only, 経緯非共有, model: Opus 5 + effort=max）: 8 巡実施（1 巡目 high=1/medium=5/blocking=0 → 是正（当時の独立レビュー原文は「blocking 1件・medium 5件」だったが、`review-log/20260915-x58-x59-review-followup-nudge.md`（X-52 書式。severity の値域に blocking は存在しない）に合わせ、STATE_DIR の HOME 展開クラッシュを severity=high として再記録した。独立レビュー round 6 で表記不一致を指摘され本行を訂正した） → 2 巡目 high=0/medium=3/blocking=0 → 是正 → 3 巡目 high=0/medium=2/blocking=0 → 是正 → round 4（人間レビュー round 1 対応の修正自体を対象）high=0/medium=3/blocking=0 → 是正 → round 5（人間レビュー round 3 対応の修正自体を対象。自己レビュー）high=0/medium=0/low=4/blocking=0 → low 4 件のうち 3 件是正、1 件は開示のみ → round 6（人間レビュー round 4 対応の修正自体を対象。自己レビュー）high=0/medium=0/blocking=0 → low 1 件是正 → round 7（人間レビュー round 5 対応の修正自体を対象。自己レビュー）high=2/medium=3/blocking=0/low=2/advisory=2 → high 2 件・medium 3 件のうち 4 件是正、1 件は対応不要、low・advisory は開示のみ）。3 巡目の medium 2 件のうち「全桁数字 branch が PR 番号と誤解釈される」は是正済み、「GH_TIMEOUT クランプ・shasum 不在縮退の contract test 不足」はテスト追加で一部（クランプ側）を解消し、shasum/sha1sum 不在の縮退経路自体は環境依存が強いため regression test 化を見送り、Known limitations に明記した。round 4 の medium 3 件は全件是正（上記「独立レビュー round 4」参照）。round 5・round 6・round 7 の詳細は上記「独立レビュー round 5」「独立レビュー round 6」「独立レビュー round 7」参照。**round 7 の是正コミット自体が commit message/docstring と実装が食い違っていた（「token 列は変更しない」と書いていたが `_lex_segment` の再分割ループは残っていた）ことを、後続の人間レビュー round 6 が発見した**（下記参照） → round 8（人間レビュー round 6 対応の修正自体を対象。自己レビュー、対象は `git diff 92b85da..HEAD -- . ':(exclude)review-log/'`）high=0/medium=2/blocking=0/low=1/advisory=1 → medium 2 件は `origin/main` 上で同一に再現することを実測確認し後続課題として開示に留め、low・advisory は同じ push で是正した（詳細は上記「独立レビュー round 8」参照）
- 人間レビュー（PR 旧#88、独立レビューとは別枠）: round 1（head `6b016cc`）で High 2 件・Medium 6 件、round 2（head `03c2e8c`。round 1 是正 + 独立レビュー round 4 是正の後）で High 1 件・Medium 5 件、round 3（head `e3488de`。round 2 是正の後）で High 1 件・Low 1 件（Medium 1 件は「今回の必須修正にはしない」と明示された残存 gap）、round 4（head `52a0a88`。round 3 是正 + 独立レビュー round 5 是正の後）で High 1 件・Medium 2 件、round 5（head `ea6e32d`。round 4 是正 + 独立レビュー round 6 是正の後。新しい commit の無い tip に対する再レビューで、main 側の別 PR 取り込みによる `mergeable: CONFLICTING` を検出）で High 1 件・Medium 1 件、round 6（head `d7597ab`。round 5 是正 + 独立レビュー round 7 是正の後）で High 2 件（medium 3 件も宣言されたが本文に詳細が無く対応不可）、round 7（head `e258d32`。round 6 是正 + 独立レビュー round 8 是正の後）で Low 5 件（レビュー側は「後続でよい」と評価。コードに触れない純粋なテキスト修正で吸収できるものは同じ push で是正した）の指摘を受け、いずれも同じ push で全件是正（上記「人間レビュー round 1 対応」〜「人間レビュー round 7 対応」参照）。round 6 は独立レビュー round 7 に続く同一クラスタの high であったため、house rule（L1+ 安全策4）に従いユーザーへ修正方針を確認してから是正した（方針メモ、`review-log/20260915-x58-x59-review-followup-nudge.md` の pm-1 参照）。結果は PR 本文・`review-log/20260915-x58-x59-review-followup-nudge.md` に記録する

#### 効果の再計測手順（X-58 のベースライン 1% を再計測する方法）

X-58 のベースライン計測は `~/.claude/projects/*/*.jsonl` 全 session を時系列走査し、`gh pr create` 以降の `git push` を数え、直前に `Pre-Push Self Review` / `Independent Review` を記録した件数を突合する方法（scratchpad `sr1.py` / `sr2.py`）。本 hook 導入後の再計測は同じ方法に加え、以下を追加する:

1. `${GDD_HOOK_STATE_DIR:-~/.claude/.gdd-hook-state}/review-followup-nudge.log` の `event: injected` 行数を数える（注入が実際に発生した回数）
2. 各 `injected` イベントのタイムスタンプと同時刻帯の session transcript を突合し、その push 以降に `Pre-Push Self Review` / `Independent Review` の記録、または `pr-review-followup` skill 呼び出しが続いたかを確認する（注入後に実際に手順へ入った率）
3. 1 と 2 の比率を、ベースライン計測と同じ集計期間・同じ 3,267 母数の枠組みで比較する

ある程度のダウンロード期間（数週間の dogfood）を経てから実施する。導入直後の再計測は母数が小さく、比率が安定しない。
