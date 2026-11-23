# Changelog Archive 4

`gate-driven-development` の変更履歴のうち、`### [0.40.15]` 〜 `[0.40.4]` をここへ移した。
記載ルール・Entry Template・Versioning Notes の正本は [`CHANGELOG.md`](CHANGELOG.md)。
本文は移動時に変更していない。

### [0.40.15] - 2026-09-06

#### Summary

PR 旧#45（`Pre-Merge Review Recheck` / `Last Review Push At` / `Bot Review Received` / `Independent Review` の reason code を Merge Approval と同じ3分岐 missing/unparsable/malformed へ揃えた変更）で `Medium Disposition` だけが対象から漏れており、field 完全欠落・必須 key 欠落・値ドメイン違反のすべてが `medium-disposition-missing` へ collapse していた。同じ3分岐へ揃えた。

#### Fixed

- `hooks/scripts/run-merge-gate-hook.sh`: `Medium Disposition` の invalid 判定を、他4フィールドと同じ `case "$GDD_MG_REASON"` 3分岐に変更した。field 完全欠落（`missing`）は従来どおり `medium-disposition-missing`、必須 key（`count`/`recorded`/`note`）欠落（`unparsable`）は `evidence-unparsable`、値ドメイン違反（`malformed`、例: `count` が非数値）は `evidence-malformed` を返す。sha 不一致・count 不一致（`GDD_MG_VALID == true` だが disposition が Independent Review の medium 件数と対応しない場合）は従来どおり `medium-disposition-missing` のまま変更していない（`Bot Review Received` の sha 不一致が `bot-review-flag-missing` のまま分岐しない前例と同じ扱い）

#### Changed

- なし（挙動は fail-closed 側のまま。block か allow かの結果は変えず、block 時の reason code のみ変更）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_evidence_gate.py`（`BlockingCategoryJudgmentTests` に 2 件追加: 必須 key 欠落→`evidence-unparsable`、非数値 `count`→`evidence-malformed`）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`、`docs/VERSIONING.md`（版数。origin/main が分岐後に v0.40.14 まで版数を消費していたため再度採番し直した）

#### User Action Required

- `Medium Disposition` の証跡が必須 key 欠落や値ドメイン違反で block されていた運用がある場合、block reason code が `medium-disposition-missing` から `evidence-unparsable` / `evidence-malformed` に変わる（block/allow の判定自体は変わらない）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q`: 全件 pass
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: 全 BLOCK pass
- `evals/evals.json` への影響なし（reason code の内部分岐のみで、gate の allow/block 判定・スキル契約は不変）

### [0.40.14] - 2026-09-06

#### Summary

`hooks/scripts/gdd_stop_hook.py` が Codebase Health Gate の high を 7 件抱えており、**このファイルに 1 行触るだけで `gh pr create` が exit 1 で止まる**状態だった。事前 PR ゲートは `--mode changed --fail-on high` で既存 high と新規 high を区別しないため、stop hook に関わる変更がすべて作成不能になっていた。**挙動を変えずに**解消する。

解消した high（すべて本 PR 以前から存在した負債）:

- 行数: 1595 行 > 上限 1500
- 複雑度: `main` 71 / `validate_done_preconditions` 47 / `try_stop_with_done_guard` 26 / `persist_handoff_summary` 22 / `maybe_block_incomplete_post_merge_continuation` 22 / `_count_task_progress` 16

#### Affected Files

- `hooks/scripts/gdd_stop_hook.py`（1595 → 1422 行。上記 6 関数を焦点化した helper へ分解）〔訂正: [0.41.1] 参照〕
- `hooks/scripts/lib/post_merge_continuation.py`（新規 / Manual merge continuation lane）
- `hooks/scripts/lib/handoff_summary.py`（新規 / Handoff Summary の state.md 永続化）
- `hooks/scripts/lib/done_guard.py`（新規 / tasklist.md 構造行の走査）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`、`docs/VERSIONING.md`（版数）

#### User Action Required

不要。stop hook の判定・停止条件・block reason はいずれも変更していない。

#### Validation / Eval Impact

- **挙動不変の根拠**: 全体 pytest が `origin/main` の baseline と同一件数で通ること（本 PR は test を 1 件も追加・変更していない）
- `gdd-codebase-health.py --mode changed --base-ref origin/main --fail-on high`: **high=0 / exit 0**（変更前は high=7）
- **トレードオフ**: high 7 件と引き換えに `python_function_count` の medium が 1 件増える（`gdd_stop_hook.py` 47 functions > warn 上限 40）。fail 上限 80 に対しては余裕があるが、同ファイルへの次の分解要求の起点になる
- `tests/checks/hooks.sh` が `gdd_stop_hook.py` の**ソース上に**要求する契約リテラル **17 件をすべて保持**。lane 名 `Manual merge continuation` と marker ファイル名は hook 側で宣言して lib へ引数で渡す（定数ごと lib へ移すと契約チェックが落ちることを実測で確認）。`実装漏れ防止` / `hook-enforced` を含む block reason の組み立てと、`unexpected_content` / `verification_section_found` / `verification_data_rows` を引数名に持つ 2 関数も hook 本体に残した

#### Notes

本 PR は旧作業ブランチ（main から 128 commit 遅れ・対象 4 ファイルすべて競合）を rebase せず、現在の main に対して作り直した。旧ブランチの古いコードを持ち込んでいないことは、**移設対象 4 関数**（`post_merge_state_path` / `write_post_merge_continuation` / `maybe_block_incomplete_post_merge_continuation` / `persist_handoff_summary`）の AST が、`origin/main` と旧ブランチ `20260906-health-refactor~1` とで一致することを確認して担保した（`git show <ref>:<path>` で両版を取り出し `ast.dump` を突き合わせる）。**lib 側の関数は抽出・再構成なので main と同名・同 AST ではない**（挙動等価の根拠は AST 一致ではない）。〔訂正: [0.41.1] 参照〕

**既知の残課題（本 PR のスコープ外）**: `tests/_stop_hook_test_base.py:persist_handoff_summary_to_content` は本番ロジックの再実装で、10 行切り詰めをハードコードしつつ `[truncated: original N lines]` マーカーを持たない。handoff テスト群はこの複製を叩いており本番実装を通らない（独立レビューの変異注入で、main / 本 PR の**両方**で 5 変異が SURVIVED することを確認）。本 PR が持ち込んだ欠陥ではないが、実装が hook 本体から lib へ移った分だけ複製との距離は 1 段遠くなった。別タスクで `lib.handoff_summary` への委譲に置き換えるのが筋。


### [0.40.13] - 2026-09-06

#### Summary

`validate-worktree-command.py` の no-op revision suffix 判定（`main@{upstream}` のような upstream/push 別名を local default branch の別名と誤分類しないための仕組み）に、2 件の欠陥を修正した。

1点目（false positive）: `@{upstream}`/`@{u}`/`@{push}` を no-op suffix 剥離の対象から除外する否定先読みが、大文字小文字を区別していた。git 自身は `@{...}` のキーワードマッチを大文字小文字を区別せずに行う（実測確認済み: git 2.50.1、`git rev-parse 'main@{upstream}'` / `'main@{UPSTREAM}'` / `'main@{U}'` / `'main@{Upstream}'` はいずれも同一の upstream 側コミットに解決し、`git worktree add <path> -b <name> 'main@{UPSTREAM}'` は実際に成功して upstream 側のコミットへ checkout する）。修正前の否定先読みは `UPSTREAM`（大文字）にマッチしないため除外に失敗し、`main@{UPSTREAM}` が no-op suffix として誤って剥がされて `main` に正規化され、local default branch 由来として誤って deny されていた。このガードが安全な base-ref として明示的に推奨している `origin/<default-branch>` 相当の upstream tracking ref を、誤って拒否しうる欠陥だった。

2点目（O(N^2) DoS 再発、1点目の修正のセルフレビュー中に追加発見）: 1点目の修正候補として最初に採用した scoped inline flag（`(?i:...)`）案は、正規表現の一括 `re.sub`（`_NOOP_REVISION_SUFFIX_CHAIN_RE = atom+\Z`、無アンカー）という既存実装をそのまま流用していたが、この実装は chain の**末尾**が否定先読みで除外される atom（`@{upstream}` 等）で終わる入力に対して、`\Z` に到達できるマッチが存在しないため全開始位置からのバックトラックが発生し O(N^2) になることが判明した（実測確認済み: `"HEAD" + "@{0}" * 8000 + "@{U}"`、32,008 文字で 3.5 秒、`"@{0}" * 16000 + "@{U}"`、64,008 文字で 13.3 秒。N を 2 倍で時間 4 倍、O(N^2) と一致）。これは v0.40.6 で「1 回の re.sub で O(N) に修正した」はずの問題の再発であり、実際には修正前から `@{u}`/`@{upstream}`/`@{push}`（小文字）終端の chain で既に同じ O(N^2) が存在していた（1点目の case-insensitive 化は、この既存の穴を突く文字列パターン（大文字小文字混在）を広げるだけで新規に持ち込んだわけではないが、既存の perf regression test は全要素が chain にマッチしきる `~0` のみの入力しか検証しておらず、この失敗モードを検出できていなかった）。

対応として、`_peel_noop_revision_suffixes` を正規表現の一括置換から、suffix 種別ごとに文字列末尾からの直接インデックス走査で 1 個ずつ判定する手動パーサーに書き換えた。剥がす（または剥がせないと判定する）suffix の長さに比例したコストのみで完了するため、chain 全体を通してのトータルコストは O(N) になる（実測: 上記 adversarial 入力が測定不能なほど高速化、既存の `~0` × 25000〜200000 chain も 0.002〜0.02 秒で完了）。

#### Fixed

- `main@{UPSTREAM}` / `main@{U}` / `main@{Upstream}` / `main@{PUSH}` のような大文字小文字違いの upstream/push 別名が、誤って local default branch 由来として deny されなくなった
- chain の末尾が upstream/push 系キーワード（大文字小文字を問わず）で除外される no-op suffix chain に対する O(N^2) ハングを修正した

#### Affected Files

- `hooks/scripts/validate-worktree-command.py`（`_NOOP_REVISION_SUFFIX_ATOM`/`_NOOP_REVISION_SUFFIX_CHAIN_RE` による正規表現ベースの一括剥離を廃止し、`_peel_one_noop_suffix_end`/`_peel_noop_revision_suffixes` による手動パーサーに置き換え）
- `tests/test_root_branch_guard_contract.py`（`test_hook_allows_gdd_worktree_creation_from_upstream_alias_case_insensitively` と `test_hook_peels_adversarial_noop_suffix_chain_ending_in_excluded_keyword_without_quadratic_slowdown` を追加）

#### User Action Required

- なし（内部の hook 判定ロジックのみの修正）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q` に本 issue の回帰テスト 2 件が追加された
- `evals/evals.json` への影響なし

### [0.40.12] - 2026-09-06

#### Summary

root branch guard（`command_creates_gdd_worktree_from_head` / `command_creates_gdd_worktree_from_local_default`）が `_HEAD_REVISION_ALIASES` / `_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES` を大文字小文字を区別する文字列一致だけで判定していたため、macOS の既定 APFS（大文字小文字を区別しない設定が既定）や Windows の既定 NTFS 上では、git 自身のファイルベースの ref 解決が OS の case-folding の影響を受け、`head`（小文字）や `MAIN`（大文字）のような表記でも実際には HEAD / local `main` と同一コミットに解決してしまい guard を bypass できる gap を是正した。この gap は `[0.40.4]` の独立セルフレビューで CONFIRMED としつつ、no-op suffix chain の解析（OS/filesystem のパス解決ではなく git revision 構文の解析に起因する別メカニズム）とはスコープが異なる orthogonal な pre-existing gap として独立 follow-up に切り出していたもの。TDD（RED→GREEN）で、実 git（2.50.1、macOS APFS）で bypass を先に実測確認してから修正した。

実測確認済み: `git rev-parse head` は HEAD と同一 SHA に解決する（`.git/HEAD` は常に loose file のため、`git gc` で ref を packed-refs に固めた後も再現する恒久的な bypass）。`git rev-parse MAIN`（大文字）は、`main` ブランチが loose ref のまま（`git branch -M main` 直後等）なら HEAD/local main と同一 SHA に解決するが、`git gc` で packed-refs に固められた後は失敗する（rc=1、一時的にのみ有効な bypass）。

修正方針は、alias 比較を無条件に大文字小文字無視にするのではなく、`git config --type=bool --get core.ignorecase`（git がリポジトリ初期化時にファイルシステムの実際の大文字小文字区別性を検出して自動設定する値）を問い合わせ、`true` の場合のみ比較を大文字小文字無視にする条件付き設計を採用した。無条件に大文字小文字無視化すると、Claude Code のサーバー/コンテナ実行環境で一般的な case-sensitive なファイルシステム（Linux ext4 等）上で、偶然 `Main` のような名前を持つ無関係な branch との衝突により新規の誤 deny（false positive）を生む懸念があったため。`core.ignorecase` が読めない・未設定の場合は既存の `git_output` 呼び出し（`active_gdd_state_exists` / `is_linked_worktree`）と同じ「読めなければ安全側のデフォルトに倒す」方針に揃え、case-sensitive 扱い（`False`）にした。

マージ前の独立セルフレビュー（`/code-review high`, 8 finder angle + 1 対 1 検証、実 git 2.50.1 で実測確認）で、上記の初回修正自体にも残存 gap 2 件を CONFIRMED し、同一 PR 内で追加是正した。1 件目: `git config --get core.ignorecase`（`--type=bool` 無し）は設定ファイルに書かれた値をそのまま返し git 自身の boolean 正規化を経由しないため、`git config core.ignorecase True`（大文字、git 自身は boolean true として受理する表記）を設定したリポジトリでは `"True"`（大文字のまま）が返り、`== "true"`（小文字リテラル一致）に掛からず、この gate が塞ごうとしている case-folding bypass を再び通してしまっていた。実測確認済み: git 2.50.1、`git config --type=bool --get core.ignorecase` は同じリポジトリで正規化済みの `"true"` を返す。`--type=bool` を付けて呼ぶよう修正した。2 件目: `command_creates_gdd_worktree_from_head` / `command_creates_gdd_worktree_from_local_default` が関数の先頭で無条件に `repo_core_ignorecase(cwd)`（`git config` subprocess 呼び出し）を実行しており、このガードは Bash/Shell コマンドごとに同期実行される PreToolUse hook であるにも関わらず、`git worktree add` 以外の大半の git コマンド（`git status` 等）でも無駄な subprocess 呼び出しを発生させていた（3 名の独立レビューエージェントが同一問題を独立に発見。実測: `git status` 相当のコマンドで約 37% のレイテンシ増加）。alias 比較に実際に到達するまで計算を遅延させ、同一関数呼び出し内でキャッシュするよう修正した。

**既知の限界（対応見送り、独立セルフレビュー指摘）**: `repo_core_ignorecase` は `core.ignorecase` という**設定値**を読むものであり、実行時にファイルシステムの実際の大文字小文字区別性を直接プローブするものではない。`core.ignorecase` は `git init` 時にファイルシステムの実際の挙動を検出して自動設定される値だが、その後に明示的に上書きされたり（`git config core.ignorecase false` 等）、リポジトリが異なる大文字小文字区別性のファイルシステム間で移動された場合は、設定値と実際の挙動が乖離しうる（実測確認済み: `core.ignorecase false` を明示設定した macOS APFS リポジトリでも、OS のファイルパス解決自体は引き続き大文字小文字を畳み込むため `git rev-parse head` は HEAD と同一 SHA に解決する）。実際のファイルシステムプローブ（一時ファイルを作成し大文字化したパスで読めるか検査する等）は、この hook が Bash/Shell コマンドごとに同期実行されることを踏まえるとコストが増すため、本 PR では採用しなかった。

#### Fixed

- `hooks/scripts/validate-worktree-command.py`: `repo_core_ignorecase(cwd)` を追加し、`command_creates_gdd_worktree_from_head` / `command_creates_gdd_worktree_from_local_default` に `cwd` を渡すようシグネチャを変更した。`_positionals_match_alias_after_peeling` に `ignorecase` キーワード引数を追加し、`core.ignorecase == true` のリポジトリでのみ `_HEAD_REVISION_ALIASES` / `_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES` との比較を `str.casefold()` ベースの大文字小文字無視に切り替えた
- `hooks/scripts/validate-worktree-command.py`（セルフレビュー是正 1/2、CONFIRMED）: `repo_core_ignorecase` を `git config --get` から `git config --type=bool --get` へ変更し、`True`/`1`/`yes`/`on` のような git 自身は truthy として扱う非小文字表記でも正しく `true` へ正規化されるようにした
- `hooks/scripts/validate-worktree-command.py`（セルフレビュー是正 2/2、CONFIRMED、3 名の独立レビューエージェントが同一問題を独立に発見）: `command_creates_gdd_worktree_from_head` / `command_creates_gdd_worktree_from_local_default` の `repo_core_ignorecase` 呼び出しを関数先頭での無条件実行から、alias 比較に実際に到達する箇所への遅延評価 + 同一呼び出し内キャッシュへ変更し、`git worktree add` 以外の git コマンドでの無駄な subprocess 呼び出しを解消した

#### Breaking Contract Changes

- root branch guard の検出面が narrowing された（allow から deny へ）が、**`core.ignorecase == true` のリポジトリ（macOS APFS / Windows NTFS の既定設定）に限る**: `git worktree add ... -b <name> head`（`HEAD` の小文字表記）、`git worktree add ... -b <name> MAIN`（`main` の大文字表記、`main` が loose ref の間のみ）は、従来 allow されていたが実 git は worktree を作成するため、active state 有り（または GDD 命名一致）の場合に新たに deny される。`core.ignorecase == false`（Linux ext4 等の一般的な CI/コンテナ環境）では判定ロジック・挙動とも変化しない

#### Affected Files

- `hooks/scripts/validate-worktree-command.py`
- `tests/_root_branch_guard_support.py`（`_repo_ignorecase` fixture helper 追加）
- `tests/test_root_branch_guard_contract.py`（case-folding 回帰テスト 2 件、`core.ignorecase` 正規化の回帰テスト 1 件を追加。前者 2 件は `core.ignorecase != true` の環境では skip、後者は `core.ignorecase` を明示的に上書きするため実行環境に依存せず常に実行される）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.40.12。origin/main が分岐後に v0.40.11 まで版数を消費していたため再度採番し直した）

#### User Action Required

- なし。`core.ignorecase == false` の環境（Linux ext4 等、Claude Code のサーバー/コンテナ実行環境で一般的）では挙動は不変。`core.ignorecase == true` の環境（macOS / Windows）でのみ、これまで bypass できていた `head` / `MAIN` 等の case-folded alias が新たに deny される

#### Validation / Eval Impact

- `tests/test_root_branch_guard_contract.py` に `test_hook_blocks_gdd_worktree_creation_from_case_folded_head_alias` / `test_hook_blocks_gdd_worktree_creation_from_case_folded_local_default_branch_alias`（`core.ignorecase != true` の CI 環境では `skipTest`）、`test_hook_normalizes_non_lowercase_core_ignorecase_config_value`（`core.ignorecase` を明示的に上書きするため実行環境に依存せず常に実行される）を追加。`evals/evals.json` への影響なし

### [0.40.11] - 2026-09-06

#### Summary

`validate-worktree-command.py` の `GDD_TASK_BRANCH_RE`（GDD task branch 名の判定に使う正規表現）が `re.IGNORECASE` を持たず、`Codex/`/`GDD/`/`Claude/`/`Cursor/` のように接頭辞が大文字始まりのブランチ名では `looks_like_gdd_task_branch` が False を返していた。この判定は `_worktree_creates_gdd_branch`（HEAD/local-default からの GDD worktree 作成ガードの入り口ゲート）と `_creates_gdd_named_branch`（root branch 作成ガードの fallback 判定）の双方が依存する共通関数のため、接頭辞の大文字小文字が異なるだけで両ガードを丸ごと bypass できていた（独立発見、実測確認済み）。

TDD（RED→GREEN）で、大文字始まり接頭辞（`Codex`/`GDD`/`Claude`/`Cursor`/`CODEX`）による bypass を先に実測確認してから修正した。ブランチ名の接頭辞判定は OS/filesystem の case-sensitivity とは無関係な命名規約上の判定であるため、条件分岐を増やさず常に `re.IGNORECASE` を適用する単純な修正とした。

#### Fixed

- `GDD_TASK_BRANCH_RE` に `re.IGNORECASE` を追加し、接頭辞の大文字小文字に関わらず GDD task branch として認識するようにした

#### Affected Files

- `hooks/scripts/validate-worktree-command.py`（`GDD_TASK_BRANCH_RE` に `re.IGNORECASE` を追加）
- `tests/test_root_branch_guard_contract.py`（回帰テスト3件を新規追加: worktree-from-HEAD 経路 / root branch 経路 / worktree-from-local-default 経路。3件目は独立セルフレビュー指摘の test-coverage gap 是正）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.40.11。origin/main が分岐後に v0.40.10 まで版数を消費していたため再度採番し直した）

#### User Action Required

不要。既存の小文字接頭辞（`codex/`/`gdd/`/`claude/`/`cursor/`）の判定結果は変わらない。

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q` -> 全 pass（fail 0）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` -> exit 0（全 BLOCK OK）
- 新規回帰テストの判別力: 修正前（RED）は `Codex`/`GDD`/`Claude`/`Cursor`/`CODEX` の全 prefix で bypass（HEAD worktree 経路は rc=0 で allow、root branch 経路も同様）を実測確認済み

### [0.40.10] - 2026-09-06

#### Summary

契約テストの正本コマンドを並列実行（`-n auto`、pytest-xdist）に切り替え、round ごとの検証を変更ファイル対応テストに限定する。実測: フルスイート 11 分 4 秒（直列）→ 1 分 53 秒〜2 分 10 秒（並列 4 回、並列起因の失敗なし）。小さな更新でもフルが 3〜6 回走り 1 時間前後がテスト待ちになっていた（W9 実測 6 回、W-36 実測 3 回）。

#### Changed

- `CONTRIBUTING.md` / `docs/VERSIONING.md` / `.github/copilot-instructions.md`: 正本コマンドを `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` に更新。`pytest-xdist` の導入手順を CONTRIBUTING に追記
- `references/gdd-self-development.md`: テストの階層を明記（impl-gate の各 round と remediation は変更ファイル対応の契約テストのみ / フルスイートは completion-check と pre-PR の 2 回）

#### Affected Files

- `CONTRIBUTING.md` / `docs/VERSIONING.md` / `references/gdd-self-development.md` / `.github/copilot-instructions.md` / `tests/test_hooks_kill_switch.py`
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.40.10）

#### User Action Required

- `python3 -m pip install --break-system-packages pytest-xdist`（未導入の環境のみ。未導入で `-n auto` を付けると pytest が unrecognized arguments で止まる）

#### Validation / Eval Impact

- `tests/test_hooks_kill_switch.py`: hook 起動の timeout を 10s → 30s（16 並列 + ESET exec 制限下で session-start hook が 10s を超える flake を実測 1/5 回）。`tests/test_governance_contract.py` の literal（`... -q`）は新コマンドの部分文字列として維持。並列フル 5 回で並列起因の失敗なし

### [0.40.9] - 2026-09-06

#### Summary

`references/cross-task-learning.md` は repo-level learned-patterns の正本置き場を `.steering/learned-patterns.md` と定めていたが、`.steering/` は branch-only の raw task steering 専用ディレクトリであり、main へ通常に tracked される cross-task learning file とは役割が違う。`check-no-raw-task-steering.py` はこの矛盾を `ALLOWED_STEERING_ROOT_FILES = {"learned-patterns.md"}` という単一ファイル例外で吸収していたが、例外は `.steering/` 直下の他のファイルにも将来紛れ込みうる穴になっていた。正本を `<repo-root>/docs/learned-patterns.md`（`docs/adr/` と同階層）へ移し、例外を撤去して `.steering/` 配下は無条件に reject する。

#### Changed

- `check-no-raw-task-steering.py`: `is_raw_task_steering()` を `".steering" in Path(path).parts` に単純化し、root-file 例外を撤去
- `.gitignore`: `!.steering/learned-patterns.md` の例外行を撤去（`docs/` 配下のため `.steering/*/` の対象にそもそも含まれない）
- 参照パス更新: `references/cross-task-learning.md` / `post-completion-learning.md` / `post-completion-pr-flow.md` / `workflow-incident-review.md` / `self-contained-contract.md` / `brainstorming-steps.md` / `inline-review-checklists.md` / `superpowers-overlap.md` / `task-breakdown-steps.md`、`docs/CI_GUARDS.md` / `docs/SECURITY.md` / `docs/references-archive/{team-onboarding,benchmark-scenarios}.md`、5 skill（`gdd-brainstorming` / `root-cause-investigation` / `gdd-task-breakdown` / `gdd-using-git-worktrees` / `gdd-subagent-driven-implementation`）の `SKILL.md`
- `docs/CI_GUARDS.md` / `docs/SECURITY.md` はプラグイン自身の `docs/` と repo-root `docs/` を区別するため `` `<repo-root>/docs/learned-patterns.md` `` 表記に変更（`tests/checks/docs-links-valid.sh` は `` `docs/<name>.md` `` をプラグイン内 `docs/` 相対として検査するため、区別しないと drift として検出される）

#### Breaking Contract Changes

- 既に `.steering/learned-patterns.md` を repo-level learned-patterns として採用している repo は、CI backstop が例外なく reject するようになったため `docs/learned-patterns.md`（repo-root）へ `git mv` する必要がある

#### Affected Files

- `plugins/gate-driven-development/scripts/check-no-raw-task-steering.py`
- `plugins/gate-driven-development/tests/test_steering_retention_contract.py`（旧例外の contract test を「`.steering/` 配下は reject」「`docs/` 配下は allow」の 2 系統に分割）
- `plugins/gate-driven-development/tests/fixtures/gdd-steering-retention-scenarios.json` / `tests/fixtures/gdd-scenario-eval-inputs/branch_only_steering_post_merge_continuation.assistant.md`
- 上記の reference / docs / skill 一覧、`.gitignore`
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`、`docs/VERSIONING.md`（版数）

#### User Action Required

- `.steering/learned-patterns.md` を運用中の repo は `docs/learned-patterns.md` へ移設する
- 新規に採用する repo は `.steering/` ではなく `docs/learned-patterns.md`（repo-root）を使う

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q`: 全件 pass
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: 全 BLOCK pass
- `bash plugins/gate-driven-development/scripts/measure-budgets.sh`: budget headroom 内（SKILL.md 5 本の変更はパス文字列置換のみで行数増減なし）

### [0.40.8] - 2026-09-06

#### Summary

PR 旧#38（reviewer finding category taxonomy・merge-gate 判定刷新）の独立セルフレビューで検出しつつ defer-follow-up としていた 3 件のうち、fail-closed 側で実害のない reason code の誤りと reviewer field 分岐の非対称を是正した。

#### Fixed

- `hooks/scripts/lib/merge-gate-evidence.sh`: `Independent Review` の near-miss walk（旧書式＝`blocking` key 欠落時に typo を検出する経路）が、自由文（`note` 等）中の複数語を空白ごと連結してしまい、句読点を挟まず「blocking」の直後に無関係な `key:` が続くと両語を結合して `blockingkey` を作り「blocking key の typo」と誤認していた（実測: `note: mentions blocking key: unrelated` が `evidence-malformed` に化ける）。正規化した候補文字列の**先頭**が `blocking` から始まる場合のみ near-miss とするアンカー付き判定（`*blocking*` の無アンカー部分一致 → `blocking*` の先頭一致）に変更し、無関係な語が候補の先頭に来る自由文だけを除外した。マージ前の独立セルフレビューで、初回修正案（コロン直前の最後の1語のみを見る案）が `blocking count` / `block ing` のような**末尾に無関係語が続く**正当な near-miss typo まで検出できなくなる fail-open 退行を CONFIRMED として指摘され、実 git 相当の実行環境で退行を実測確認したうえで先頭アンカー方式へ差し替えた

#### Changed

- `hooks/scripts/run-merge-gate-hook.sh`: `Pre-Merge Review Recheck` / `Last Review Push At` / `Bot Review Received` / `Independent Review` の証跡フィールドを、`Merge Approval` と同じ3分岐（missing / unparsable / malformed）に統一した。field が完全に欠落した場合は従来通り field 専用の reason code（`recheck-missing` 等）、field は存在するが必須 key が欠落した場合は `evidence-unparsable`、値ドメイン違反の場合は `evidence-malformed` を返す。従来はこの4フィールドが missing/unparsable/malformed を区別せず単一の reason code へ collapse していたため、利用者に返る復旧手がかり（「該当証跡行の書式を確認」/「値ドメインを確認」）が Merge Approval だけ手厚く、他4フィールドでは失われていた

#### Breaking Contract Changes

- 上記4フィールドで、field は存在するが値が unparsable/malformed な場合の reason code が `recheck-missing` / `review-push-missing` / `bot-review-flag-missing` / `independent-review-missing` から `evidence-unparsable` / `evidence-malformed` へ変わる（field 完全欠落時の reason code は不変）。block reason の文言が変わるため、この reason code 文字列に依存する外部ツール・ログ集計があれば更新が必要

#### Affected Files

- `hooks/scripts/lib/merge-gate-evidence.sh` / `hooks/scripts/run-merge-gate-hook.sh`
- `tests/test_merge_gate_hook_evidence_parsing.py` / `tests/test_merge_gate_hook_evidence_gate.py`
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.40.8）

#### User Action Required

- なし。gate 判定（allow/block の結果）自体は変わらない。block 時の reason code 文言のみ、上記4フィールドの unparsable/malformed ケースで変わる

#### Validation / Eval Impact

- near-miss walk の誤検知は `tests/test_merge_gate_hook_evidence_parsing.py::MergeGateEvidenceParserTests::test_independent_review_note_word_before_unrelated_key_is_not_a_false_positive` を追加し、修正前に fail（reason=malformed、期待値 legacy-no-blocking-field）することを確認してからコミットした
- reason code 3分岐化は `tests/test_merge_gate_hook_evidence_gate.py::EvidenceGateTests` に7件のテスト（4フィールド × unparsable/malformed、Independent Review は unparsable のみ追加）を追加し、いずれも修正前に fail することを確認してからコミットした。既存の「field 完全欠落」系テスト（`test_missing_recheck_blocks` 等）は reason code 不変のまま pass することも確認済み
- 独立セルフレビューで指摘された fail-open 退行を防ぐ回帰テストとして、`NEAR_MISS_BLOCKING_KEYS`（`tests/test_merge_gate_hook_evidence_parsing.py`）に `blocking count: 1` / `Blocking Count: 1` / `block ing: 1` の3変種を追加した。先頭アンカー方式への差し替え後、既存 near-miss 11 変種・新規追加3変種・誤検知修正1変種のいずれも期待どおりの結果（malformed / legacy-no-blocking-field）になることを実測確認済み
- `python3 -m pytest plugins/gate-driven-development/tests/ -q` フルスイート: 2045 passed, 1 skipped, 12427 subtests passed
- `evals/evals.json` への影響なし


### [0.40.7] - 2026-09-06

#### Summary

`CHANGELOG.md` が行数上限 1500 を大きく超え、**このファイルに触るだけで pre-PR の Codebase Health Gate が `gh pr create` を止める**状態になっていた。`## Policy` は「contract に影響する変更は必ずここに記録する」と定めているため、実質すべての PR が作成不能だった。古い release 節を 2 つの archive ファイルへ移して解消した。

`gdd-codebase-health-baseline.json` の `CHANGELOG.md` エントリは、その `reason` 自身が「縮小の道筋は古い release 節を別ファイルへアーカイブすること」と書いていた ratchet で、本変更でその道筋を実施したため削除した。baseline が無い方が large_file 判定は**厳しくなる**（`large_file_finding_for_baseline` は baseline 不在の非テストファイルを即 `high` にする）。

**release 節の本文は 1 行も変更していない。**

#### Affected Files

- `CHANGELOG.md`（`[Unreleased]` 〜 `[0.37.0]` を保持し、`## Archive` の案内を追加。行数の実値は書かない —— ゲートが検証するのは「上限 1500 以内」であって実数ではなく、main 追従のたびに陳腐化する）
- `CHANGELOG-archive.md`（新規 / `[0.36.0]` 〜 `[0.16.0]`）
- `CHANGELOG-archive-2.md`（新規 / `[0.15.0]` 〜 `v0.1.3`）
- `gdd-codebase-health-baseline.json`（`large_files` を空に）
- `tests/test_merge_approval_vocabulary_leak.py`（`SCAN_GLOBS` に `CHANGELOG-archive*.md` を追加し、配布物である archive 2 本を leak 検査の対象に含めた）
- `README.md` / `CONTRIBUTING.md` / `docs/SECURITY.md`（構成の記載に archive 2 本を追加）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`、`docs/VERSIONING.md`（版数）

#### User Action Required

新しい release entry は従来どおり `CHANGELOG.md` の先頭に追加する。過去の entry を参照する際は `## Archive` の案内から該当 archive を辿る。archive 側へ追記はしない。

`CHANGELOG.md` が **1200 行**に達したら、古い側の release 節を移して 800 行台まで戻す。**移動先は既存 archive ではなく新しい `CHANGELOG-archive-3.md`（以降は連番）にする** —— 既存 archive はどれも上限 1500 に対する余裕が数百行しかなく、そこへ 400 行足すと**今度は archive 側が large_file で `high` になり、同じ「CHANGELOG を触ると PR が作れない」状態に戻る**（独立レビューで指摘された罠）。上限 1500 に当たってから動くのでは、その時点の PR が自分の CHANGELOG 追記でゲートに阻まれる。

#### Validation / Eval Impact

- 分割の忠実性を機械照合: 3 ファイルから**追加ヘッダー（`## Archive` の 7 行 + 各 archive 先頭 6 行）を除いて**再構成した結果が、分割前と **sha256 一致**。release 見出しは**順序ごと全件保存**（fence 内の Entry Template の `### [Unreleased]` を除外して計数）
- `gdd-codebase-health.py --mode changed --base-ref origin/main --fail-on high`: **high=0 / exit 0**
- `tests/checks/version-not-consumed.sh` の層 B（統合先 CHANGELOG に出荷版数の見出しが無いこと）は `CHANGELOG.md` だけを見るため、分割で**観測範囲が保持分の版数に縮む**。これは本 PR で唯一「緩む方向」の変化。層 A（記録済み消費版数 < manifest version）が単調増加を強制するため実害は小さい
- 3 ファイルとも**上限 1500 行以内**

### [0.40.6] - 2026-09-06

#### Summary

state.md の canonical field reader が、**値が空の行**（書きかけの `- Resume From:`）を「現在値」として返していた欠陥を、reader 6 実装に横断で修正した（規約 R-1: 区切り文字の後ろが trim + backtick 除去後に空の canonical 行は現在値ではない。その行は飛ばして次の一致行を見る）。

実機再現: `- Resume From:`（空）の後に `- Resume From: gdd-test-driven-development` がある state.md で、`gdd_validate_active_state_fields` が「`Resume From` 欠落」と誤診断し、fail-closed で resume を塞いでいた。

**行の選択規則は変えていない**（最初の**値付き**一致。最終行採択にはしない）。安全性の根拠は 2 点: (i) 値付き行が 1 本も無ければ従来どおり空を返す、(ii) 値付き行がある場合に返す値は state.md に実際に書かれている値である。ただし (ii) の結果として、従来は空値行の遮蔽で偶然 block されていた形が通るようになる。到達可能になる既存挙動は `#### Changed` に列挙する。

#### Affected Files

- `hooks/scripts/lib/detect-steering.sh`（`gdd_extract_doc_field` の awk に空値スキップ。presence ループも同 reader 経由に統一）
- `hooks/scripts/gdd_stop_hook.py`（`resume_from_value()` を module 直下へ新設し `latest_steering_resume_from` から委譲。`RESUME_FROM_PATTERN` のアンカーを他 5 実装に合わせ、`*` bullet とインデント行を受理しないようにした）
- `hooks/scripts/validate-steering-write.py`（`state_field_value` が最初の**値付き**行を返す。`state_field_values` は write-once 判定用に**全出現**を返すまま据え置き）
- `hooks/scripts/lib/state_fields.py`（新規 / state.md の canonical field reader 5 本をここへ集約。`validate-steering-write.py` が行数上限 1500 に対して余裕 3 行しかなく、R-1 を足すと`gh pr create` を止める健全性ゲートに自分で阻まれるため）
- `hooks/scripts/lib/tasklist_parse.py`（`RESUME_FROM_PATTERN` / `resume_from_value` を`gdd_stop_hook.py` から移設。同 hook も行数上限を超過中で、追加分を吸収できないため）
- `scripts/gdd_task_binding.py` / `scripts/collect-gdd-telemetry.py` / `scripts/setup-gdd-loop.sh`（各 reader に同規約を適用）
- `references/state-schema.json`（`value_less_line_skip` として規約と適用範囲を記録）
- `tests/test_state_field_value_less_line_contract.py`（新規）/ `tests/test_canonical_field_line_anchoring_contract.py`
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`、`docs/VERSIONING.md`（版数）
- `docs/adr/2026-09-04-state-field-reader-unification.md`（新規 / 蒸留した判断）

#### User Action Required

不要。書きかけの空値行を残したまま次の行に値を書く形が、以後は正しく読まれる。

#### Changed

R-1 は「空値行による遮蔽」を取り除く。遮蔽は偶然 fail-close していたので、取り除くと**到達可能になる既存の挙動**がある。いずれも実装ガードは追加していない（列挙は網羅を主張しない）。

1. `run-pre-push-gate-hook.sh` の `Task Size` が `trivial` を読めるようになり、self-review 要求の全スキップに到達しうる
2. `run-pre-pr-gate-hook.sh` の `Next Action` / ADR 判定が、空値行の後ろの値を読むようになる
3. `run-merge-gate-hook.sh` の `PR URL` が読めるようになり、gate 対象判定が変わる
4. `gdd_detect_active_steering` の terminal 除外が効くようになり、空値行 + `Resume From: cancelled` の steering が active から外れる。`self-review-evidence.sh` の union フォールバックは `done` / `blocked` しか救済しないため、`cancelled` は `terminal-only` に落ちて merge gate が起動しなくなる。**遮蔽行の無い正しい `cancelled` は本変更の前から同じく素通りする**ので、変わるのは「書きかけ行があると偶然 block されていた」ケースのみ
5. `gdd_is_stale_brainstorming_candidate` 経由で、空値行 + `Resume From: gdd-brainstorming` と古い `Started At` の組が 10 日超の stale 候補として除外されうる（時間依存で発火する）
6. `gdd_stop_hook` の markerless human check fallback が、空値行 + `- Resume From: human-check-waiting` の形で発火するようになる

#### Fixed

- **不正 UTF-8 を含む state.md で書き込み検査が丸ごと無効化される fail-open を塞いだ**。`hooks/scripts/validate-steering-write.py` と `scripts/gdd_task_binding.py` が untrusted な steering markdown を `read_text(encoding="utf-8")` で読んでいたため、不正バイトが 1 つあると `UnicodeDecodeError`（`ValueError` 系）になる。直下の `except OSError` では捕捉できず、PreToolUse hook が exit 1（non-blocking error）で終了する ―― **exit 2 だけが deny** なので、検査を経ずに書き込みが通っていた。実測: 既存 state.md 末尾に `\xc3\x28` を置いて `Started At` を欠く書き込みを投げると、修正前は rc=1 + traceback（deny payload なし）、修正後は rc=2 + `permissionDecision: deny`。`errors="replace"` は repo の既存慣例（`scripts/lint-*.py` 群ほか。本 PR 適用後の実測で 47 箇所）と同じで、置換文字化しても canonical field の構造は保たれる。固定テスト: `PythonReadersSurviveMalformedInputTests`

#### Validation / Eval Impact

- 新規契約テスト `tests/test_state_field_value_less_line_contract.py` が、6 reader 実装の横断一致（AC-5）と各実装の空値形を固定する
- 変異注入で判別力を確認済み（awk の空値スキップ分岐を旧形へ戻すと当該テストが落ちる）


### [0.40.5] - 2026-09-06

#### Summary

pre-push / pre-PR gate の `dry` 収束条件を緩和する。旧定義「新規指摘ゼロが 2 連続」は帳簿系 medium が毎周新出して収束せず（standard で rounds 5 / consecutive_clean 0 の実測）、push 1 回に 1 時間前後の固定費が乗っていた。

#### Changed

- `references/self-review-lanes.md`: `dry` を「その周回で新規 high または blocking ゼロ」が 2 連続に統一（初回 push / followup とも）。medium / low / advisory は記録のみで `consecutive_clean` を戻さない。自己周回は 3 周を上限とし、未到達なら独立レビュー 1 回（Opus 5 max ＋ 観点レーン）で high 0 を `dry: yes` の根拠にできる（`state.md` の `Independent Review` 行に記録）
- リスク比例発火表: `quick (standard)` は dry 収束を要求しない（3 レーンは回す）。`hooks/scripts/run-pre-push-gate-hook.sh` / `run-pre-pr-gate-hook.sh` の Task Size 分岐に反映
- `skills/gdd-pr-review/SKILL.md` / `references/post-completion-pr-flow.md`: dry の定義と上限を参照側でも同期

#### Affected Files

- `references/self-review-lanes.md` / `references/post-completion-pr-flow.md` / `skills/gdd-pr-review/SKILL.md`
- `hooks/scripts/run-pre-push-gate-hook.sh` / `hooks/scripts/run-pre-pr-gate-hook.sh`
- `tests/test_pre_push_gate_contract.py` / `tests/test_self_review_lanes_contract.py`
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.40.5）

#### User Action Required

- なし（gate が緩む方向のみ。`Pre-Push Self Review` / `Pre-PR Self Review` の書式は不変）

#### Validation / Eval Impact

- `tests/test_pre_push_gate_contract.py`（quick (standard) 免除）/ `tests/test_self_review_lanes_contract.py`（発火表）を更新。`evals/evals.json` への影響なし

### [0.40.4] - 2026-09-06

#### Summary

`[0.40.1]` の独立セルフレビューで CONFIRMED としつつ非スコープに切り出していた 2 件の follow-up のうち、`_HEAD_REVISION_ALIASES`/`_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES` の有限文字列集合が `HEAD~0~0`/`HEAD^{}`/`main~0` のような no-op suffix の連鎖（`~0`/`^0`/`^{}`/`@{0}` は任意の順序・任意回数チェーンできる）を塞ぎきれない gap を是正した。TDD（RED→GREEN）で、実 git（2.50.1）で bypass を先に実測確認してから修正した。

当初案として `git rev-parse --verify` で base-ref token を実 git で解決し SHA を local `HEAD`/`main` 系の SHA と比較する方式（finite string-literal matching を git 呼び出しに置き換える）を検討したが、実測で退行を確認したため採用しなかった: フレッシュクローン直後は `origin/main` が local `main` と同一 SHA に解決する（`git clone` 直後、誰も先行 push していない一般的な状態）ため、SHA コンテンツ一致で判定すると、このガード自身が推奨し `test_hook_allows_worktree_add_branch_creation` で allow が固定されている安全な base-ref `origin/<default-branch>` まで誤って deny してしまう。代わりに、no-op suffix を正規表現で剥離してから bare 形の有限エイリアス集合と照合する方式を採用した。剥離はチェーンの長さ・順序に依存せず正規化できるため、`HEAD~0~0`/`main~0` 型の bypass を解消しつつ、`origin/main` のような別 ref とのコンテンツ一致による誤検知を避けられる。

マージ前の独立セルフレビュー（`/code-review high`, 8 finder angle + 1 対 1 検証、実 git 2.50.1 で実測確認）で、上記の初回修正自体にも残存 gap 2 件を CONFIRMED し、同一 PR 内で追加是正した（詳細は次段落）。**この 2 件目の是正が入る前の初回修正だけでは、`main~00`/`HEAD^{commit}` 等が依然 bypass し、かつ adversarial input で hook が数秒〜100 秒超ハングする状態だったため、単独ではリリースしていない。**

origin/main との merge conflict 解消後、マージ確定前の追加独立検証（adversarial に git revision 構文を再探索）で、Round 2 是正の `@{0+}`（reflog index の数字限定）自体にも gap を CONFIRMED した: git の `@{<n>}` 構文は数字だけでなく `now`/`yesterday`/`1.second.ago` のような approxdate（gitrevisions(7) 参照）も受理し、reflog が変化していなければ現在値と同一コミットに解決する。実測確認済み: git 2.50.1、`@{now}`/`HEAD@{now}`/`main@{now}` はいずれも HEAD/local main と同一 SHA に解決し、`git worktree add <path> -b <name> '@{now}'` は実際に成功する。同一 PR 内で Round 3 として追加是正した（`@{...}` の内容を数字限定からワイルドカードへ拡張しつつ、`@{upstream}`/`@{u}`/`@{push}`（reflog の過去値ではなく別 ref を指す特殊構文）は否定先読みで明示的に除外し、`origin/main` 相当の安全な ref を誤って local `main` の別名として deny する新規回帰を導入しないようにした）。

同じ追加独立検証で、大文字小文字を区別しない filesystem（macOS APFS・Windows NTFS の既定設定）上では `head`（`HEAD` の小文字表記。`.git/HEAD` は常に loose file のため gc 後も再現する）や、pack 前の loose ref であれば `MAIN` 等の大文字表記も、filesystem の case-folding により実 git がそのまま同一 ref として解決してしまう別クラスの bypass も CONFIRMED した。これは git revision 構文の解析ではなく OS/filesystem 側のパス解決に起因する別メカニズムであり、本 PR（no-op suffix chain の解析）のスコープ・本 PR が導入した regression のいずれにも該当しない。本 PR の是正前から存在していた orthogonal な pre-existing gap のため本 PR では対応せず、独立した follow-up として切り出した（`core.ignorecase` を git に問い合わせて条件付きで大文字小文字を畳み込む設計が必要で、単純な大文字小文字無視の追加は case-sensitive filesystem 上で正当に異なる branch 名との衝突による新規誤 deny を生む）。

#### Fixed

- `hooks/scripts/validate-worktree-command.py`: `command_creates_gdd_worktree_from_head`/`_local_default` の base-ref 判定に `_peel_noop_revision_suffixes`（no-op suffix chain の剥離）を追加し、有限 alias 集合では塞げなかった no-op suffix 連鎖によるすり抜けを修正
- `hooks/scripts/validate-worktree-command.py`: `_HEAD_REVISION_ALIASES`/`_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES` を bare 形のみに縮小（suffix 付き形は peeling が正規化するため列挙不要になった）
- `hooks/scripts/validate-worktree-command.py`（セルフレビュー是正 1/2、CONFIRMED）: `_NOOP_REVISION_SUFFIX_ATOM` の桁表現を 1 文字の `0` 固定から `0+`（0 のみからなる任意桁数）へ、type-peel 表現を空 brace `^{}` のみから `^{commit}`/`^{object}` を含む形へ拡張した。実測確認済み: git 2.50.1、`main~00`/`HEAD^00`/`HEAD@{00}`/`HEAD^{commit}`/`HEAD^{object}` はいずれも HEAD/local main と同一 SHA に解決し、拡張前の集合ではすり抜けていた（`^{tree}`/`^{tag}` は別オブジェクトに解決するため対象に含めていない）
- `hooks/scripts/validate-worktree-command.py`（セルフレビュー是正 2/2、CONFIRMED、2 名の独立レビューエージェントが別々に実測して一致）: `_peel_noop_revision_suffixes` の実装を `while True: ... .search(token)` の逐次ループ（chain 1 個剥がすたびに token 全体を再スキャンするため O(N^2)）から、`+` 量化子による 1 回の `re.sub`（O(N)）へ置換した。実測: 旧実装は adversarial な no-op suffix chain（例: `"~0" * 25000` を末尾に付けた token）で 40004 文字=約 3.9 秒、80004 文字=約 15.7 秒、200004 文字=約 99.5 秒（N を 2 倍にすると時間が約 4 倍になり N^2 と一致）。このガードは Bash/Shell コマンドごとに同期実行される PreToolUse hook であるため、この遅延はコマンド実行そのものを塞ぐ実害がある。新実装は同じ入力を数ミリ秒で処理する
- `hooks/scripts/validate-worktree-command.py`（副次修正）: 剥離の正規表現アンカーを `$`（Python では末尾の改行 1 個の直前にもマッチする）から `\Z` へ変更し、末尾に改行を含む無効な revision 文字列（例: `"main~0\n"`、git 自身は rc=128 で拒否する）を `"main"` と誤認識する経路を閉じた
- `hooks/scripts/validate-worktree-command.py`（DRY、セルフレビューの simplification 角度指摘）: `command_creates_gdd_worktree_from_head`/`_local_default` に重複していた `any(peel(candidate) in ALIASES for candidate in positionals)` を `_positionals_match_alias_after_peeling` へ抽出した
- `hooks/scripts/validate-worktree-command.py`（セルフレビュー是正 3/3、CONFIRMED、merge 確定前の追加独立検証で発見）: `_NOOP_REVISION_SUFFIX_ATOM` の `@{...}` 部分を数字限定（`@\{0+\}`）から任意内容（`@\{[^{}]*\}`）へ拡張し、`@{now}`/`@{yesterday}`/`@{1.second.ago}` のような approxdate（gitrevisions(7)）を用いた reflog 参照によるすり抜けを修正した。同時に `@{upstream}`/`@{u}`/`@{push}`（reflog の過去値ではなく別 ref を指す特殊構文）を否定先読みで除外し、`main@{upstream}`（`origin/main` 相当の安全な ref）を local `main` の別名として誤 deny する新規回帰を導入しないようにした

#### Breaking Contract Changes

- root branch guard の検出面が narrowing された（allow から deny へ）: `git worktree add ... -b <name> <HEAD の no-op suffix 連鎖形（例: HEAD~0~0, HEAD^{}, HEAD~00, HEAD^{commit}, @{now}）>`、`git worktree add ... -b <name> <local default branch の no-op suffix 連鎖形（例: main~0, main~00, main^{commit}, main@{now}）>` は、従来 allow されていたが実 git は worktree を作成するため、active state 有り（または GDD 命名一致）の場合に新たに deny される

#### User Action Required

- なし。既存の正当な GDD worktree 作成手順（`origin/<default-branch>` または記録済み Base Commit を base-ref に使う手順）は従来どおり allow される。HEAD/local default branch を no-op suffix 連鎖で明示的な base-ref に使っていた場合のみ、新たに deny される点に注意

#### Validation / Eval Impact

- RED テストを `tests/test_root_branch_guard_contract.py::test_hook_blocks_gdd_worktree_creation_from_chained_noop_suffix_revisions` に追加し、修正前に fail（3 subTest 全て `0 != 2`）することを確認してからコミットした
- 採用しなかった SHA コンテンツ比較方式の反例（`origin/main` が local `main` と同一 SHA でも deny してはならない）を `tests/test_root_branch_guard_real_git.py::test_allow_side_origin_default_branch_matching_local_content_is_not_blocked` として固定化した（実 git oracle、`git clone` 直後の実測で local/origin の `main` が同一 SHA になることを assert 済み）
- セルフレビュー是正 1/2 の RED テストを `tests/test_root_branch_guard_contract.py::test_hook_blocks_gdd_worktree_creation_from_generalized_noop_suffix_forms` に追加し、修正前に fail（7 subTest 全て `0 != 2`）することを確認してからコミットした
- セルフレビュー是正 2/2（O(N^2)）の RED テストを `tests/test_root_branch_guard_contract.py::test_hook_peels_adversarial_noop_suffix_chain_without_quadratic_slowdown` に追加し、修正前は 8.38 秒（閾値 3.0 秒超過で fail）、修正後は 0.40 秒で pass することを確認した
- セルフレビュー是正 3/3（reflog approxdate）の RED テストを `tests/test_root_branch_guard_contract.py::test_hook_blocks_gdd_worktree_creation_from_reflog_date_specifiers` に追加し、修正前に fail（4 subTest 全て `0 != 2`）することを確認してからコミットした
- `python3 -m pytest plugins/gate-driven-development/tests/ -q` -> merge 前は `1906 passed, 1 skipped`、origin/main（v0.40.2、PR 旧#38）との merge 後は `1966 passed, 1 skipped, 12263 subtests passed`（fail 0）、セルフレビュー是正 3/3 反映後も対象 6 ファイル（`test_root_branch_*`）で `78 passed, 298 subtests passed` を再確認した（fail 0。既存 AC-5 deny corpus・AC-12 実 git oracle・`test_hook_blocks_gdd_worktree_creation_from_head_revision_aliases`/`..._from_local_default_branch_aliases`（`[0.40.1]` で追加した alias 回帰）を含む）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` -> merge 前・merge 後ともに exit 0（全 BLOCK OK。`version-not-consumed` は `shipping v0.40.3; integration target consumed v0.40.2` で OK。分岐後に統合先が PR 旧#38（v0.40.2）を先行取得していたため、消費済み版数を v0.40.0 → v0.40.2 へ追随した）
- Snyk Code Scan（`snyk_code_scan`）を変更ファイル（`hooks/scripts/validate-worktree-command.py`、`tests/test_root_branch_guard_contract.py`、`tests/test_root_branch_guard_real_git.py`）に対して個別実行し、いずれも 0 件
- merge 解消の正しさは、マージ確定前に独立レビューエージェント（本 PR とは別セッション）が conflict 解消 5 ファイル（3 manifest / VERSIONING.md / CHANGELOG.md）を再検証し、conflict marker 残存なし・版数整合・CHANGELOG のエントリ順序と内容の欠落なし・origin/main 側が是正対象ファイル群を一切触っていない（semantic conflict の可能性なし）ことを確認済み
- 別途確認した非スコープ事項（本 PR では対応しない、CONFIRMED/PLAUSIBLE だが fail-closed 方向で実害が無いか、既に `[0.40.1]` で非スコープ合意済みの事項の再確認）: (1) `_worktree_positionals_and_names` は worktree path と start-point を区別せず（`[0.40.1]` で既知の PLAUSIBLE として記録済み）、peeling 導入によりこの誤 deny 対象が「別名文字列の完全一致」から「peel 後に別名一致するパス（例: `wt/main~0` という名前のディレクトリ）」へ僅かに拡大した。GDD 生成 path は機械的スラッグのため実運用での再現性は低いままであり、本 PR のスコープには含めない。(2) `_peel_noop_revision_suffixes` の空文字列 fallback（`token or "@"`）は、`@{...}` 系 suffix が token 全体を消費した場合に加え、`~0`/`^0`/`^{}` のみの chain が token 全体を消費した場合（その token 自体は元々無効な revision）にも `"@"` を返すが、いずれも deny 方向（fail-closed）にしか作用しないため許容した。(3) `_NOOP_REVISION_SUFFIX_ATOM` は依然として git revision 構文の**列挙**であり、ここに挙げた種以外の no-op 相当構文（将来 git が追加しうるものを含む）を網羅する主張はしない。この limitation はコード内コメントに明記した。(4) マージ確定前の追加独立検証で、大文字小文字を区別しない filesystem（macOS APFS・Windows NTFS の既定設定）上で `head`/`MAIN` のような大文字小文字違いの表記が filesystem の case-folding により実 git にそのまま同一 ref として解決される別クラスの bypass を CONFIRMED した。これは git revision 構文の解析ではなく OS/filesystem 側のパス解決に起因する orthogonal な pre-existing gap（本 PR の是正前から存在し、本 PR が導入した regression ではない）のため、本 PR のスコープには含めず独立 follow-up として切り出した

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`（base-ref no-op suffix 剥離の追加・拡張、alias 集合の bare 形への縮小、O(N^2) の O(N) 化、`_positionals_match_alias_after_peeling` への DRY 抽出、reflog approxdate 対応）
- `plugins/gate-driven-development/tests/test_root_branch_guard_contract.py`（RED 回帰テスト 4 件追加: チェーン検出、桁/type-peel 一般化、O(N^2) 性能回帰、reflog approxdate）
- `plugins/gate-driven-development/tests/test_root_branch_guard_real_git.py`（SHA コンテンツ比較を採用しなかった設計判断のロック回帰テスト追加）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.40.4 へ bump。origin/main の PR 旧#38（v0.40.2）・PR 旧#41（v0.40.3）との merge conflict を版数比較で解消。PR 旧#41 も本 PR と独立に `[0.40.3]` を採番していたため、統合確定順に本 PR 側を `[0.40.4]` へ採番し直した）
- `docs/VERSIONING.md`（現行バージョン・統合先の消費済み版数を v0.40.3 へ更新。同上 merge conflict を解消）
