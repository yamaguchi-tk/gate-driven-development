# Changelog Archive 3

`gate-driven-development` の変更履歴のうち、`### [0.40.3]` 〜 `[0.38.0]` をここへ移した。
記載ルール・Entry Template・Versioning Notes の正本は [`CHANGELOG.md`](CHANGELOG.md)。
本文は移動時に変更していない。

### [0.40.3] - 2026-09-06

#### Summary

PR 旧#34 マージ前の独立実装レビュー・独立セキュリティレビューで AC-8（gate 1 の判定基準は変えない）によりスコープ外とし、`[0.40.1]`（マージ前は `[0.39.2]` として開発）の Validation / Eval Impact に「本 PR ではスコープに含めていない」と明記していた root branch guard の残存 gap を是正した。`_segment_creates_branch`（gate 1）は `-` 始まりの token が 1 つでもあれば既知の creating flag（`-c`/`-C`/`-f`/`--copy`/`--force`、および `[0.40.1]` で追加された `--track`/`--no-track`/`--create-reflog`/`-t`/`-q`）の有無だけで branch 作成操作かどうかを判定しており、`--color`/`--column`/`--abbrev` のような optional argument 型 flag（実 git は `=<value>` 必須で、空白区切りの次 token を値として消費しない）や `--sort`/`--format` のような必須値 flag の「値の後ろに残る positional」を一切考慮していなかった。実 git（2.50.1）はいずれの形でも branch を作成するため、site 自体が gate 1 の収集から漏れる guard bypass だった（`git branch --color always <name>` は "always" という branch を作成する）。名前分の追加 token が無い 2 token 形（`git branch --color always`）も実 git はこの唯一の positional を branch 名として作成するため、同じ bypass として扱う。実 git を oracle にした追加検証で `--column`/`--abbrev`（分離形・`=` 結合形の双方）にも同型の quirk があることを確認し、まとめて修正した。TDD（RED→GREEN）で対応。

なお本 PR は origin/main への統合時点で `[0.40.1]` を別 PR（PR 旧#40、`-t`/`-q`/`--track`/`--no-track`/`--create-reflog` の creating flag 追加・worktree add 名前抽出修正・base-ref revision 別名対応）が先に消費していたことが判明したため（両 PR が同じ独立レビュー由来の gap 群から独立に分岐し、偶然同じ版数 `0.40.1` を採番していた）、本 PR の版数を `[0.40.2]` へ採番し直して統合した。その後さらに 2 回目の origin/main 追従時点で、本 PR とは無関係な別 PR（PR 旧#38、reviewer finding category taxonomy・merge-gate 判定刷新）が同じ `[0.40.2]` を先に消費していたことが判明したため（origin/main が非常に高頻度で更新されているため版数衝突が繰り返し発生する。前例は `[0.40.1]` の PR 旧#40 との衝突を参照）、本 PR の版数をさらに `[0.40.3]` へ採番し直した。

マージ後、8 finder angle（correctness 3・reuse・simplification・efficiency・altitude・conventions）+ 1-vote 検証による独立セルフレビュー（`/code-review high`）を実施した。2 名の finder agent（angle A: line-by-line diff scan、angle B: removed-behavior auditor）が独立に同一の重大な bypass を実測確認した: `_segment_creates_branch` の非作成 flag 判定（`_token_is_branch_non_creating_flag`）が `rest` 全体を位置を無視して一括スキャンしていたため、`--sort`/`--format`（必須値 flag）の**値**の token が `-d`/`-D`/`-m`/`-M` の見た目をしていると、実際には branch を作成する操作（実 git は値として消費し残りの token から作成する。実測確認済み: git 2.50.1）を delete/move 操作と誤認し、site 自体が gate 1 の収集から漏れていた（`git branch --sort -d codex/... ` が active state 有りでも allow）。加えて `--sort`/`--format`/`--color` 等が値を消費した後に `--` が続く形（`git branch --sort committerdate -- <name>` 等）も実 git は branch を作成するが、新設した value-taking flag 判定が `--` を未知 token として保守側 `return False` に落としていた。逆方向として `-f --sort committerdate`（実際には名前引数が無く実 git は何も作成しない）が `has_creating_flag`/`has_positional` の独立 2 回スキャンにより誤って deny される fail-closed 方向の false positive も見つかった。3 件とも `_segment_creates_branch` を 1 パスの cursor walk へ書き換えることで同時に解消し、副次的に旧実装の到達不能分岐（`_token_is_branch_creating_flag` の重複チェック）と冗長な三項演算子も除去した。

#### Fixed

- `hooks/scripts/validate-worktree-command.py`: `_segment_creates_branch`（gate 1）を 1 パスの cursor walk へ書き換え、`--color`/`--column`/`--abbrev`（optional argument、`=` 無しの空白区切り値を消費しない）と `--sort`/`--format`（必須値、空白区切りでも値を消費する）を明示的にモデル化した。未知の `-` 始まり token が 1 つでも混ざる場合は保守的に非作成側へ倒し、`git branch -- <name>`（既知 limitation）や `-a`/`-r` 等との組み合わせを誤って作成操作にしない
- `hooks/scripts/validate-worktree-command.py`: 独立セルフレビュー指摘（2 名の finder agent が独立に実測確認）— `_segment_creates_branch` の非作成 flag 判定が `--sort`/`--format` の値 token（`-d`/`-D`/`-m`/`-M` の見た目）を独立の delete/move flag と誤認し、実際には branch を作成する segment を非作成と判定していた guard bypass を、1 パス化により「値として消費した token は独立の flag として再評価しない」ことを保証して修正した
- `hooks/scripts/validate-worktree-command.py`: 独立セルフレビュー指摘 — value-taking flag（`--sort`/`--format`/`--color`/`--column`/`--abbrev`）が値を消費した後に `--` が続く形（`git branch --sort committerdate -- <name>`、`git branch --color -- <name>` 等）で実 git が branch を作成するにも関わらず site 収集から漏れていた bypass を、「既に値取り flag を 1 つ以上消費済みの場合に限り `--` を読み飛ばす」ロジックで修正した（`git branch -- <name>` という creating flag 無しの bare 形は既知 limitation のまま allow を維持）
- `hooks/scripts/validate-worktree-command.py`: 独立セルフレビュー指摘 — `has_creating_flag`/`has_positional` を独立に 2 回スキャンする旧実装が `git branch -f --sort committerdate`（名前引数無し、実 git は何も作成しない）を誤って作成操作と判定し deny していた fail-closed 方向の false positive を、1 パス化により修正した

#### Breaking Contract Changes

- root branch guard の検出面が narrowing された（allow から deny へ）: `git branch --color/--column/--abbrev <value> [<name>]`（optional argument の空白区切り形。値そのものが branch 名になる 1 token 形を含む）、`git branch --color/--column/--abbrev=<value> <name>`、`git branch --sort/--format <value> <name>`、`git branch --sort/--format -d/-D/-m/-M <name>`（値が non-creating flag の見た目をしている形）、`git branch --sort/--format <value> -- <name>`、`git branch --color -- <name>` は、従来 allow されていたが実 git は branch を作成するため、active state 有り（または GDD 命名一致）の場合に新たに deny される
- 逆方向（deny から allow へ、fail-closed の過剰検出を是正）: `git branch -f --sort/--format <value>`（branch 名引数が無い形）は、実 git が何も作成しないにも関わらず従来誤って deny されていたが、新たに allow される
- **既知の limitation（本 PR 変更前後で不変、非スコープ）**: creating flag を伴わない単独の `git branch -- <name>` は、gate 1 が作成操作として検出せず allow のまま（既存の `test_hook_allows_bare_double_dash_branch_creation_known_limitation` で固定済み）。`-v`/`-i`/`--recurse-submodules` 等、本 PR でも `[0.40.1]` でもモデル化していないその他の flag と positional の組み合わせも同様に未モデル化のまま残る（`[0.40.1]` の独立セルフレビューが `-v`/`-i` を同種 gap として既に CONFIRMED 記録済みのフォローアップ課題であり、本 PR ではスコープに含めない）

#### User Action Required

- なし。既存の正当な GDD worktree / task branch 作成手順は従来どおり deny/allow される。`--color`/`--column`/`--abbrev`/`--sort`/`--format` を伴う root branch 作成（`--`/non-creating-flag 見た目の値との組み合わせを含む）を行っていた場合のみ、新たに deny される点に注意

#### Validation / Eval Impact

- `tests/test_root_branch_name_candidates.py::test_hook_blocks_branch_value_taking_flags_with_leftover_positional`（新設）で `--color`/`--column`/`--abbrev`（分離形・`=` 結合形）・`--sort`/`--format`（分離形）の deny を固定。`test_hook_allows_branch_value_taking_flags` から `git branch --color always` を除去し、実 git 未検証のまま allow 期待にしていた誤りを修正
- 独立セルフレビューで発見した 3 件の追加回帰テストを新設: `test_hook_blocks_mandatory_value_flag_when_value_looks_like_non_creating_flag`（`--sort`/`--format` の値が `-d`/`-D`/`-m`/`-M` の見た目をしていても deny を維持）、`test_hook_allows_creating_flag_with_mandatory_value_flag_and_no_name`（`-f --sort <value>` の名前引数無し形が allow になることを固定）、`test_hook_blocks_value_taking_flag_followed_by_double_dash_and_name`（value-taking flag の後に `--` が続く形の deny を固定。`git branch -- <name>` の既知 limitation が引き続き allow のままであることも同テストファイル内の既存 assertion で確認済み）
- `test_hook_falls_back_on_unknown_branch_flag` に companion creating flag（`-f`/`--force`/`-q`）を伴わない `git branch --color codex/20260903-x` 単独形を追加し、active state 無しでも AC-7(iii) fallback 経路が機能することを直接検証（独立セルフレビュー cross-file tracer 角度の指摘: 既存の追加 test はいずれも `-f` 等の companion flag を伴っており、新設した value-taking flag 判定単独での fallback 経路が未検証だった）
- `tests/test_root_branch_guard_real_git.py::test_deny_side_when_real_git_creates_gdd_ref` に `--color`/`--column`/`--abbrev`/`--sort`/`--format` の基本形 5 形と、独立セルフレビューで発見した `--sort -d`/`--format -m`（値が non-creating flag の見た目）・`--sort ... --`/`--color --`（`--` との組み合わせ）の追加 4 形を加え、実 git が実際に GDD 命名 ref を作ることと guard の deny を突き合わせた（AC-12 real git oracle）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q` -> 全 pass（fail 0、既存 AC-5 deny corpus・AC-12 実 git oracle・`[0.40.1]` の creating flag 拡張回帰テストを含む）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` -> 全 BLOCK OK（マージ作業中に `origin/main` が PR 旧#40（`[0.40.1]`）→ PR 旧#38（`[0.40.2]`）と 2 回連続で版数を先に消費していたため、統合先消費済み版数を v0.40.0 → v0.40.1 → v0.40.2 へ追随し、本エントリの版数を `[0.40.1]` → `[0.40.2]` → `[0.40.3]` と 2 回採番し直した。`version-not-consumed` は `shipping v0.40.3; integration target consumed v0.40.2` で OK）
- 独立セルフレビューで CONFIRMED したが本 PR ではスコープに含めない事項（フォローアップ課題）:
  1. **`_branch_names`/`_has_unknown_branch_flag`（gate 2、名前抽出）の flag 表が gate 1 と非同期のまま**: `_branch_names` は `--sort`/`--format` の値消費を一切モデル化していないため、`git branch --sort committerdate feature-x` の候補名を `"committerdate"` と誤抽出する。現状は `_has_unknown_branch_flag` の `_BRANCH_KNOWN_LONG_FLAGS = {"--copy", "--force"}` が `--sort`/`--format` を「未知」として fallback（コマンド全文の GDD 命名 regex 判定）に必ず倒すため無害だが、将来誰かが `_BRANCH_KNOWN_LONG_FLAGS` に `--sort`/`--format` を追加すると（gate 1 の creating flag 集合を拡張したのと同じ動機で）、`_branch_names` 側を同時に直さない限り誤抽出した名前で fail-open regression になりうる dormant landmine（独立セルフレビュー cross-file tracer 角度の指摘）
  2. **`_branch_value_taking_flags_leave_positional`（現 `_segment_creates_branch` に統合済み）の cursor 前進が `_take_flag_value`/`_next_value_index` を再利用していない**: 既存の値取得ヘルパーと機能重複しており、将来 `_next_value_index`側にのみ修正が入ると drift しうる（独立セルフレビュー reuse 角度の指摘）
  3. **finite allowlist アーキテクチャの再発**: gate 1 の creating/non-creating/value-taking flag 判定は本 PR で 3 度目の拡張になる（Round 6 の redirection 誤認修正、`[0.40.1]` の `-t`/`-q`/`--track` 追加、本 PR の `--color`/`--column`/`--abbrev`/`--sort`/`--format`）。`_has_unknown_branch_flag` が既に採用している fail-closed な「未知 flag は保守側」パターンを gate 1 自体（`_segment_creates_branch`）にも適用すれば、本 PR・`[0.40.1]`・既知の `-v`/`-i` gap を一括で閉じられる可能性があるが、AC-8（gate 1 の判定基準は変えない）の scope boundary を再検討する必要があり、本 PR 単独のスコープを超える（独立セルフレビュー altitude 角度の指摘）
  4. **2 個超の positional / `--force=x` のような無効な `=` 結合 boolean flag の扱いは fail-closed 側の未検証 divergence**: `git branch --color always feature-x extra`（実 git は "too many arguments" で何も作成しない）や `git branch --force=x codex/...`（実 git は不正な `=` 結合を拒否）は guard が deny 側に倒れるが、これは安全な方向（over-denial）であり実害は無い（独立セルフレビュー cross-file tracer 角度の指摘）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`（gate 1 の value-taking flag モデリング追加、独立セルフレビューで発見した 3 件の追加 bypass/false-positive を 1 パス cursor walk への書き換えで修正）
- `plugins/gate-driven-development/tests/test_root_branch_name_candidates.py` / `test_root_branch_guard_real_git.py`（回帰テスト追加・既存 test 期待値の是正・独立セルフレビューで発見した追加 bypass の回帰テスト）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.40.3 へ bump）
- `docs/VERSIONING.md`（現行バージョン・統合先の消費済み版数を更新）

### [0.40.2] - 2026-09-06

#### Summary

- finding に `category` を導入し、merge gate の block 判定を severity（`medium != 0`）から実害クラス（`high != 0 || blocking != 0`）へ置換した。あわせて帳簿系 finding の Round 消費を止め、PR 規模上限と `見積もり diff 行数` を新設して巡数爆発の上流を塞いだ

#### Affected Files

- `references/`: `reviewer-common.md` / `self-review-lanes.md` / `state-machine.md` / `state-field-tiers.md` / `task-sizing.md` / `task-breakdown-steps.md` / `requirements-template.md` / `human-check-template.md` / `team-onboarding.md`（当時の path。現在は `docs/references-archive/team-onboarding.md`）
- `hooks/scripts/`: `run-merge-gate-hook.sh` / `lib/merge-gate-evidence.sh`
- `skills/`: `gdd-implementation-gating` / `gdd-requirements-gating` / `gdd-pr-review-followup`
- `scripts/lint-hitl-stage-plan.py`（複雑度リファクタ含む）、`tests/`（新規 3 本 + 既存 5 本の更新 + `test_merge_gate_hook.py` の分割後 4 ファイルへの再配置）、`docs/references-archive/worked-examples.md`
- PR review / origin/main 統合対応（4 回の merge）: `docs/adr/2026-09-03-w29-pr-convergence-rules.md`（新規）、`docs/design/2026-09-03-w29-pr-convergence-rules-adr.md`（新規）、`docs/VERSIONING.md`、`gdd-codebase-health-baseline.json`、`.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.40.2）

#### Added

- finding に `category`（9 値。正本: `references/reviewer-common.md` § finding category）を導入
- `references/task-sizing.md` に PR 規模上限（production 差分 2,000 行 / 25 ファイル）を新設
- `Implementation Sequence Plan` / `段階実装案` に `見積もり diff 行数` 列を必須化

#### Changed

- merge gate（`hooks/scripts/run-merge-gate-hook.sh`）の block 判定を `medium != 0` から `high != 0 || blocking != 0` へ置換。medium ≥ 1 の証跡は `Medium Disposition` の記録を必須化
- `skills/gdd-implementation-gating/SKILL.md` の Round カウントを Round 消費 category に限定
- `references/task-breakdown-steps.md` の task 分割優先順位を 1 箇所に一本化
- `references/self-review-lanes.md` の `dry` 判定を緩和。followup 周回の終了条件が「内部整合レーンで 2 連続、新規 medium 以上ゼロ」から「内部整合レーンで 2 連続、新規 high または blocking ゼロ」になり、帳簿系 medium だけでは周回が終わらない状態を解消した（初回 push / PR 作成時の「3 レーンでの 2 連続」は変更なし）

#### Breaking Contract Changes

- `Independent Review` 証跡の `blocking` key 欠落（旧書式）は warning 記録のうえ `high != 0` のみで判定する段階移行に入る（`GDD_MG_REQUIRE_BLOCKING_FIELD=false`。W-28 着地後に反転予定）

#### User Action Required

- reviewer 出力に `category:` 行を含めることを推奨（W-28 未着地の間は未付与でも `product` 相当として動作する）

#### Validation / Eval Impact

- `tests/validate-plugin.sh` / `python3 -m pytest tests` が pass することを確認済み
- `tests/checks/skill-body-budget.sh` の 6 判定（budget 1〜3 を含む）が pass することを確認済み
- origin/main への 3 回目の追従（PR 旧#34 取り込み）後、全量 `python3 -m pytest tests/ -q` = **1908 passed, 1 skipped, 12232 subtests passed**（exit 0、fail 0）を確認済み

**版数訂正（origin/main 統合時、3回目）**: 本エントリは当初 `[0.39.0] - 2026-09-05` として作成し、origin/main への追従のたびに版数衝突が発生して `[0.39.1]`（PR 旧#34 と衝突）→ `[0.39.2]`（PR 旧#37/#40 が `[0.40.0]`/`[0.40.1]` を先に消費）→ `[0.40.2]` と付け替えを重ねた（`docs/VERSIONING.md` § 統合先が消費済みの版数を再利用しない に従う。前例: PR 旧#25 の `0.38.1→0.38.2`）。origin/main が非常に高頻度で更新されているため、この付け替えは PR がマージされるまで再発しうる。

### [0.40.1] - 2026-09-06

#### Summary

PR 旧#34 マージ前に実施した独立実装レビュー・独立セキュリティレビューで、AC-8（gate 1 の判定基準は変えない）によりスコープ外とした root branch guard の既存 gap を 3 件是正した。(1) gate 1（`_segment_creates_branch`）の creating/non-creating flag 判定が `-q`/`-t`/`--track`/`--no-track`/`--create-reflog` を一切考慮しておらず、実 git がこれらの flag と positional の組み合わせで branch を作成するにも関わらず site 自体が gate 1 の収集から漏れる guard bypass だった。(2) `git worktree add` 経路の名前抽出（`_worktree_positionals_and_names`）が switch/checkout/branch 側で既に検証済みの `_skip_redirection`/`_take_flag_value` を再利用せず、`-b` の分離値取得が redirection operator を無視して次 token を無条件取得し、bash 4.1+/zsh の named fd（`{name}>...`）も fd 候補として認識していなかったため、positionals/names が壊れて implicit HEAD からの worktree 作成検出をすり抜けていた。(3) `command_creates_gdd_worktree_from_head`/`_local_default` の base-ref 判定が文字列リテラル一致（`"HEAD"`、`{"main","master","develop"}`）のみで、`@`/`HEAD~0`/`HEAD^0`/`@{0}`（HEAD 別名）や `refs/heads/main`/`heads/main`/`main@{0}`（local main 別名）のような git revision 構文をすり抜けていた。いずれも実 git（2.50.1）で bypass を実測確認し、TDD（RED→GREEN）で修正した。

#### Fixed

- `hooks/scripts/validate-worktree-command.py`: gate 1（`_segment_creates_branch`）の `_BRANCH_CREATING_LONG_FLAGS`/`_BRANCH_CREATING_SHORT_LETTERS` に `--track`/`--no-track`/`--create-reflog`/`-t`/`-q` を追加し、`git branch -q <name>` 等の site 収集漏れによる guard bypass を修正
- `hooks/scripts/validate-worktree-command.py`: `_worktree_positionals_and_names` の自前 fd/redirection 判定（`token.isdigit()` のみ、`-b` の分離値を無条件に次 token から取得）を `_skip_redirection`/`_take_flag_value` に置き換え、redirection が `-b` の値位置や positional に混入して implicit HEAD からの worktree 作成検出をすり抜ける bypass を修正
- `hooks/scripts/validate-worktree-command.py`: `command_creates_gdd_worktree_from_head`/`_local_default` の base-ref 判定を、HEAD 別名（`_HEAD_REVISION_ALIASES`）・local default branch 別名（`_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES`）を含む集合との一致に拡張し、revision 別名によるすり抜けを修正

#### Breaking Contract Changes

- root branch guard の検出面が narrowing された（allow から deny へ）: `git branch -q/-t/--track/--no-track/--create-reflog <name>`、`git worktree add ... -b <name> <HEAD 別名>`、`git worktree add ... -b <name> <local default branch 別名>` は、従来 allow されていたが実 git は branch/worktree を作成するため、active state 有り（または GDD 命名一致）の場合に新たに deny される
- **既知の limitation（本 PR 変更前後で不変、非スコープ）**: creating flag を伴わない単独の `git branch -- <name>` は、gate 1 が作成操作として検出せず allow のまま（既存の `test_hook_allows_bare_double_dash_branch_creation_known_limitation` で固定済み）

#### User Action Required

- なし。既存の正当な GDD worktree / task branch 作成手順は従来どおり deny/allow される。`-q`/`-t`/`--track` 等を伴う root branch 作成、または HEAD/local default branch の別名 revision を明示的な base-ref に使っていた場合のみ、新たに deny される点に注意

#### Validation / Eval Impact

- `_BRANCH_CREATING_LONG_FLAGS`/`_BRANCH_CREATING_SHORT_LETTERS` 拡張の回帰テストを `tests/test_root_branch_name_candidates.py` に、`_worktree_positionals_and_names`・base-ref 別名対応の回帰テストを `tests/test_root_branch_guard_contract.py` に追加（いずれも実 git オラクルで bypass を先に実測確認済み）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q` -> `1852 passed, 1 skipped, 12114 subtests passed`（fail 0、既存 AC-5 deny corpus 56 件・AC-12 実 git oracle を含む）
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --repo-root . --mode changed --base-ref main --baseline-file gdd-codebase-health-baseline.json` -> コード側は `high=0, medium=0, low=0`。本 CHANGELOG 追記後は baseline ratchet（`current_lines`/`reduce_by` を実測 3228 行へ更新済み）に対して `medium=1`（`large_file_baseline_reduction`、headroom 0 運用方針どおりの想定内 advisory。デフォルト `--fail-on none` のため non-blocking）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` -> exit 0（全 BLOCK OK。マージ作業中に `origin/main` が PR 旧#37（v0.40.0）を先行取得したため、統合先消費済み版数を v0.39.1 → v0.40.0 へ追随し、本エントリの版数を `[0.39.2]` から `[0.40.1]` へ採番し直した。`version-not-consumed` は `shipping v0.40.1; integration target consumed v0.40.0` で OK）
- 別途確認した非スコープ事項（本 PR では対応しない）: `lib/push_command_parse.py:classify_refspec` にも同型の数字 only fd ヒューリスティック（named fd `{name}>...` 非対応）があるが、この経路では positional 過剰カウントは refspec ambiguity 判定を fail-closed（過剰 block）側に倒すのみで、GDD guard bypass のような fail-open 方向の脆弱性は生じないため対象外とした。`git branch --color always <name>` 等、value-taking と誤認しやすい一部 flag が単独 positional と組み合わさると実 git が branch を作成するケース（gate 1 の value-taking flag モデリングの追加 gap、独立実装レビューの対象範囲外の新規発見）も本 PR ではスコープに含めていない
- マージ前の独立セルフレビュー（`/code-review high`, 8 finder angle + 1-vote 検証、実 git 2.50.1 で実測確認）で、本 PR と同種だが別インスタンスの gap を追加で 3 件 CONFIRMED した（いずれも本 PR が導入した regression ではなく、本 PR の 3 修正と同じ「有限 allowlist / 有限文字列集合」アーキテクチャの限界。フォローアップ課題として切り出し、本 PR のスコープには含めない）: (1) gate 1（`_segment_creates_branch`）は `-v`/`-i` 等、`_BRANCH_CREATING_*`/`_BRANCH_NON_CREATING_*` のどちらにも無い flag で同型 bypass が再現する（`git branch -v <name>` は実 git が branch を作成するが active state 有りでも allow）。(2)(3) `_HEAD_REVISION_ALIASES`/`_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES` は有限文字列集合のため `HEAD~0~0`/`HEAD^{}`/`main~0` のような無制限に存在しうる revision 別名連鎖をすり抜ける（`git rev-parse` で同一 SHA に解決することを実測確認したうえで、実際に guard が allow することも確認済み）。加えて PLAUSIBLE 2 件: 実行に影響しない latent risk として `_has_unknown_branch_flag` の `_BRANCH_KNOWN_LONG_FLAGS`/`_BRANCH_KNOWN_SHORT_LETTERS`（gate 2）が本 PR で拡張した gate 1 の flag 集合と非同期のまま（fallback 経路が常により保守的側に働くため現状は誤 deny のみで済むが、要 追随）、および `_worktree_positionals_and_names` が worktree path と start-point を区別せず、path が別名文字列と一致すると誤 deny する既存の false positive（本 PR 前から存在、GDD 生成 path は機械的スラッグのため実運用での再現性は低い）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`（gate 1 creating flag 集合の拡張、worktree add 名前抽出の redirection 処理統一、base-ref 別名対応）
- `plugins/gate-driven-development/tests/test_root_branch_name_candidates.py` / `test_root_branch_guard_contract.py`（回帰テスト追加）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.40.1 へ bump）
- `docs/VERSIONING.md`（現行バージョン・統合先の消費済み版数を更新）


### [0.40.0] - 2026-09-06

#### Summary

タスク 1 本あたりの固定儀式コストを下げる 3 点を実装（計画書 §2 W-36、AC-3 / AC-5 / AC-6 / AC-7）。(1) `gdd-security-reviewer` を security-sensitive scope のみ条件起動する非該当リスト・非 waivable 上書き条項を `references/reviewer-selection.md` に追加、(2) 既存 PreToolUse hook `validate-steering-write.py` に `steering_size` deny category を追加し、`state.md` / `tasklist.md` / `design.md` の post-write サイズ超過 write を deny する、(3) `agents/gdd-planning-reviewer.md` の design phase に実装可能性の机上追跡（High finding 判定）を追加。AC-1 / AC-2 / AC-4 / AC-8 と `metrics.jsonl` は 2026-09-05 human check（Q4=案C / Q5=案B / Q7=案B）で後続タスクへ繰り越した。

#### Added

- `references/reviewer-selection.md`: § Security Reviewer 非該当リスト（AC-3）、非 waivable 上書き条項 1-5、`waived` 記録時の `reason` 書式規定
- `references/task-sizing.md`（quick / express の security skip に非 waivable 条項の但し書き）
- `skills/gdd-implementation-gating/SKILL.md`（quick 節に同但し書き）
- `agents/gdd-planning-reviewer.md`: § 実装可能性の机上追跡（Implementation Feasibility Desk Trace, design phase 専用）
- `hooks/scripts/validate-steering-write.py`: `steering_size` deny category（1 回目から deny。post-write サイズが上限を超えかつ増加する write のみ。減る write は常に allow）
- `references/config-defaults.md`: `GDD_STEERING_SIZE_DENY` の kill switch 正本表
- `docs/SECURITY.md`: deny category 一覧に `steering_size` と kill switch・降格対象の記載を追加
- `references/common-guardrails.md`: § .steering artifact の正本性 に size 上限の機械強制と退避先を追記（行数増 0）
- `tests/test_steering_size_deny_contract.py`: AC-3 / AC-5 / AC-6 の契約テスト（ケース数の正本は同ファイル。他の文書に数値を複写しない）

#### Changed

- `references/reviewer-selection.md`: § Quick Selection Table の untrusted-input 語彙リストの重複を統合し 1 箇所を正本にした
- `references/reviewer-selection.md`: AC-7 の budget 当て先として、§ レビュー関連 skill の「使い分けの原則」5 bullet（直上の表に等価な情報がある）と § Reviewer Responsibility Matrix 直後の `**Why**` 段落（rationale のみ）を削除した（-9 行 / +0 行。`git diff --numstat` 実測）。契約文・非該当リスト・非 waivable 上書き条項・`reason` 書式・適用範囲限定文は削っていない
- `references/task-sizing.md` / `skills/gdd-implementation-gating/SKILL.md`: quick / express の security reviewer skip に「`reviewer-selection.md` 非 waivable 上書き条項該当時は起動」の但し書きを追記（Copilot 指摘 旧#2）

#### Fixed

- PR 旧#37 レビュー指摘 3 件を修正（size decision の評価点は `design.md` § 実装契約 1 が正本）: (1) `steering_size` が既存 category（email 等）の escape hatch で迂回できた点 — size は既存違反の有無と独立に評価・記録し、既存 category が降格する write でも size deny が成立していれば deny を維持する（本文に両方の理由。size は自身が 3 回 deny を数えたときだけ降格する）、(2) `.steering/../state.md` のように `..` で `.steering/` の外へ抜けるパスに size 上限が適用されていた点 — resolve 後に `.steering/` 配下かを再確認する（既存 category の判定は不変）、(3) `GDD_STEERING_SIZE_DENY=0` の無効化通知が既存 deny と同時に消えていた点 — steering 対象 write では deny / allow / 降格のどの経路でも通知を合成する

#### Breaking Contract Changes

- `gdd-security-reviewer` の起動条件が緩和された（fail-open 方向）。既存の「迷ったら追加する」原則は非該当リスト・非 waivable 上書き条項のどちらにも当たらない場合にのみ適用される
- `.steering/state.md` / `tasklist.md` / `design.md` への write が、post-write サイズが `STEERING_SIZE_WARN_BYTES` を超えかつ増加する場合に deny されるようになった（従来は advisory のみ）。`GDD_STEERING_SIZE_DENY=0` で単独無効化可能

#### Affected Files

- `plugins/gate-driven-development/references/reviewer-selection.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/hooks/scripts/lib/steering_size.py`（新規。size 判定の分離）
- `plugins/gate-driven-development/references/config-defaults.md`
- `plugins/gate-driven-development/references/common-guardrails.md`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/tests/test_impl_gate_precision_tiering_contract.py`
- `plugins/gate-driven-development/tests/test_steering_size_deny_contract.py`（新規）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.40.0）
- `gdd-codebase-health-baseline.json`（CHANGELOG の re-ratchet。前例 commit `324da9f`）
- `docs/adr/2026-09-06-w36-task-ceremony-cost.md`（新規。ADR インデックス）
- `plugins/gate-driven-development/docs/design/2026-09-06-w36-task-ceremony-cost-adr.md`（新規。ADR 逐語アーカイブ＝正本）

#### User Action Required

- `.steering/` artifact を扱う利用者は、`state.md`（20,000 バイト）/ `tasklist.md`（80,000 バイト）/ `design.md`（60,000 バイト）を超える増加 write が deny されるようになったことを認識し、超過時は `worklog.md` へ退避する
- security reviewer が waived になったタスクでは `Implementation Reviewer Selection` / `Planning Reviewer Selection` の `reason` に非該当リスト項目名と非 waivable 確認済みの旨が書かれているかを確認する
- **v0.40.0 を取り込む前に**、進行中の worktree の `state.md` / `tasklist.md` / `design.md` を上限（20,000 / 80,000 / 60,000 バイト）内へ `worklog.md` に退避しておく。超過したまま取り込むと、当該ファイルへの増加 write が deny → deny → warning 付き allow の 3 回周期になる。緊急時は `GDD_STEERING_SIZE_DENY=0`

#### Validation / Eval Impact

- `tests/test_steering_size_deny_contract.py` は pytest で実行する（`python3 -m pytest plugins/gate-driven-development/tests/`）。`tests/validate-plugin.sh` は `tests/checks/manifest.tsv` の shell チェックのみを回し pytest は起動しないため、本テストは validate-plugin.sh の対象外
- `evals/evals.json` への影響なし

### [0.39.1] - 2026-09-06

#### Summary

`validate-worktree-command.py` の root branch guard が、`active_gdd_state_exists(cwd)` が偽のときに `looks_like_gdd_task_branch(command)`（コマンド**全文**への正規表現検索）で deny を決めていたため、作成される branch とは無関係な位置に GDD 命名パターン（`codex/20......` 等）が現れるだけで誤 deny していた（PR 旧#28 の Copilot review 指摘）。判定を、token 解析で抽出した「実際に作成される branch 名候補」への正規表現適用へ書き換えた。

#### Changed

- `hooks/scripts/validate-worktree-command.py`: root branch guard の allow/deny 判定を、`active_gdd_state_exists(cwd)` が偽のときの `looks_like_gdd_task_branch(command)`（コマンド全文の正規表現検索）依存から、token 解析で抽出した「実際に作成される branch 名候補」への正規表現適用へ置き換えた。作成される branch と無関係な引数に `codex/20......` 等が含まれるだけの誤 deny（例: `git checkout -b feature-x codex/2026...`、`git checkout -b feature-x -- codex/2026...`、別 segment の無関係な文字列）を解消。名前を確定できない形（候補 0 件・未展開 token・`branch` の未知 flag）は command 単位でコマンド全文判定へ fail-closed に退避する
- `hooks/scripts/validate-worktree-command.py`: `is_linked_worktree(cwd)` の呼び出しを AC-11 の `try` ブロック内へ移動。`git_output()` の非 UTF-8 デコード失敗等がこの呼び出し経路だけ未捕捉のまま `main()` を抜け、PreToolUse hook が rc=1（非ブロッキングエラー = fail-open）で終了する欠陥を修正（PR 旧#34 Copilot review 指摘）
- `hooks/scripts/validate-worktree-command.py`: `_has_unknown_branch_flag`（AC-7(iii)）・`_switch_branch_names`・`_checkout_branch_names` に `_skip_redirection` を適用し、redirection の対象 token が `-` 始まりのときに未知 flag / 2 個目の `-c`・`-b` flag と誤認して過剰 deny する欠陥を修正（PR 旧#34 Copilot review 指摘）
- `hooks/scripts/validate-worktree-command.py`: `_next_value_index` / `_skip_redirection` の fd 判定を、数字 fd（`2>...`）に加えて bash 4.1+ の可変 fd（`{name}>...`）にも対応させた。`{name}` が redirection operator に隣接する形を fd 候補として認識していなかったため、`git switch -c {fd}>/dev/null codex/...` 等で `{fd}` を候補として取り込み、後続の実際の作成名（`codex/...`）が候補から漏れて active state 無しで allow される **silent allow（guard bypass）** になっていた（PR 旧#34 Copilot review 指摘、Round 3）
- `hooks/scripts/validate-worktree-command.py`: gate 1 の site 判定 `_segment_creates_branch` が redirection を読み飛ばさず raw token を直接見ていたため、`git branch codex/... >-d` のように redirection の出力先が `-d`/`-D`/`-m`/`-M` 等の non-creating flag と同じ見た目になると、実際には branch を作成する segment を「作成操作ではない」と誤判定し、site 自体が gate 1 の収集から漏れて **active state が有っても検出されない guard bypass** になっていた。`_strip_redirections` を新設し、flag 分類の前に redirection の operator/対象を除去するよう修正（PR 旧#34 Copilot review 指摘、Round 6）。この初版修正は `_strip_redirections` が gate 2 用の `_skip_redirection`（数字 fd ヒューリスティック）を再利用していたため、`git branch 2 >/dev/null` のように branch 名そのものが数字だと唯一の positional を fd 宣言と誤認して除去し、gate 1 の site 収集自体が漏れる新規の fail-open regression を生んでいた（独立実装レビュー指摘、実測確認済み）。gate 1 では fd ヒューリスティックを使わず operator + 対象のみを機械的に除去するよう修正して解消（回帰テスト追加）

#### Breaking Contract Changes

- root branch guard の検出面が narrowing された: 実際に作成される branch とは無関係な位置に GDD 命名パターンが含まれるだけの一部コマンド（例: `git checkout -b feature-x -- codex/2026...`、`git branch <name> codex/2026...`（start-point）、`git branch -c codex/2026...-old <new>`（copy 元）、別 segment に無関係な文字列がある形）が新たに allow される。`command_creates_root_branch` 本体の判定基準・`active_gdd_state_exists` が真の場合の deny・`(d)(e)` 系の deny 維持（value-taking flag 分離引数、`git branch -f -- <name>` 等の creating flag 付き `--` 形）は変更していない（回帰テスト: `tests/test_root_branch_name_candidates.py::test_hook_allows_checkout_start_point_and_pathspec` / `::test_hook_allows_branch_non_copy_and_copy_forms`）。逆に値結合形（`git switch -ccodex/2026...` / `-fccodex/...` / `git checkout -bcodex/...`）は `\b` 不成立で従来 allow だったが、新たに deny される（安全側）
- **既知の limitation（本 PR 変更前後で不変、非スコープ）**: creating flag を伴わない単独の `git branch -- <name>` は、gate 1（`_segment_creates_branch`）が作成操作として検出せず allow のまま（AC-8 は gate 1 の判定基準を変えない方針のため対象外。回帰テスト: `tests/test_root_branch_name_candidates.py::test_hook_allows_bare_double_dash_branch_creation_known_limitation`）
- **既知の limitation（tokenizer 共有の制約、非スコープ）**: `2>/dev/null`（fd 番号）と `2 > /dev/null`（独立引数 + 既定 fd への redirection）は tokenizer 通過後に同一 token 列になり区別できないため、`git switch -c 2 > /dev/null codex/...` のような形は実際に作成される branch 名（`2`）ではなく start-point（`codex/...`）を候補と誤認して過剰 deny する（fail-closed 方向で silent allow ではない。回帰テスト: `tests/test_root_branch_name_candidates.py::test_hook_blocks_switch_when_digit_positional_precedes_unrelated_redirection_known_limitation`）

#### User Action Required

- なし。既存の正当な GDD worktree / task branch 作成手順は従来どおり deny/allow される。値結合形（`git switch -ccodex/...` 等）を意図的に使っていた場合のみ、新たに deny される点に注意

#### Validation / Eval Impact

- branch 名候補抽出（AC-1〜AC-4）、fail-closed fallback（AC-7）、deny corpus 非回帰（AC-5, 56 件を `assertEqual` で固定）、実 git oracle 双方向検証（AC-12）、`is_linked_worktree` の fail-closed 化（AC-11）、`git branch -- <name>` 既知 limitation の allow 固定（AC-8）、`_has_unknown_branch_flag` の redirection 誤認修正・digit-adjacency 既知 limitation の固定・bash 4.1+ 可変 fd（`{name}>...`）の guard bypass 修正・`_segment_creates_branch` の redirection 対象誤認 guard bypass 修正（AC-7(iii)）の回帰テストを追加。追加で 1652 行に達した `tests/test_root_branch_guard_contract.py` は関心事ごとに `test_root_branch_guard_contract.py` / `test_root_branch_guard_segmentation.py` / `test_root_branch_name_candidates.py` / `test_root_branch_deny_corpus.py` / `test_root_branch_guard_fail_closed.py` / `test_root_branch_guard_real_git.py` へ分割し、共有 fixture を `tests/_root_branch_guard_support.py` へ集約した（テスト件数・assertion は不変: `cd plugins/gate-driven-development && python3 -m pytest tests/test_root_branch_guard_contract.py tests/test_root_branch_guard_segmentation.py tests/test_root_branch_name_candidates.py tests/test_root_branch_deny_corpus.py tests/test_root_branch_guard_fail_closed.py tests/test_root_branch_guard_real_git.py tests/test_push_command_parse.py` -> 177 passed / 558 subtests）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` を実行し全 BLOCK OK（exit 0）を確認（CONTRIBUTING.md § 必須チェック）
- `origin/main` merge 後、独立実装レビュー指摘（gate 1 での fd 数字ヒューリスティック誤用による新規 regression）の是正後の full suite: `python3 -m pytest plugins/gate-driven-development/tests/ -q` -> `1848 passed, 1 skipped, 12103 subtests passed`（fail 0）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`（branch 名候補抽出、redirection token 読み飛ばし、fail-closed fallback、`is_linked_worktree` の fail-closed 化）
- `plugins/gate-driven-development/hooks/scripts/lib/git_command_parse.py`（`COMMAND_SUBSTITUTION_PLACEHOLDER` を public 定数として公開）
- `plugins/gate-driven-development/tests/_root_branch_guard_support.py`（新規、共有 fixture）
- `plugins/gate-driven-development/tests/test_root_branch_guard_contract.py`（中核契約のみに縮小）/ `test_root_branch_guard_segmentation.py` / `test_root_branch_name_candidates.py` / `test_root_branch_deny_corpus.py` / `test_root_branch_guard_fail_closed.py` / `test_root_branch_guard_real_git.py`（いずれも新規、分割先）
- `gdd-codebase-health-baseline.json`（CHANGELOG の `current_lines` を rebase 後の実測値へ再 ratchet）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.39.1。origin/main 取り込み時点の消費済み版数 v0.39.0 より大きい値へ bump）
- `docs/VERSIONING.md`（現行バージョン / 統合先の消費済み版数を更新）

### [0.39.0] - 2026-09-04

#### Summary

W-27 で導入した completion-check の 3 契約（差分スコープ / Round 上限 / 記録 stale の非 blocker 化）を実際の gate へ適用し、reviewer の実起動検証と design 順方向整合チェックを追加。cross-session messaging（別セッションからのメッセージ）を受け取った際に起動元セッションへ通知する経路と、人間承認点直前だけを対象にした Fable ベースの軽量方向確認 tier（`human_check_gate`）を新設した。

#### Added

- **completion-check loop safety（塊A）**: `references/state-machine.md` に Round 上限契約を正本化し、`skills/gdd-completion-check/SKILL.md` に `## Completion Loop Safety`、`references/gate-checklists.md` に `## Checklist E`（差分スコープ確認・Round カウンタ操作手順）、`references/state-field-tiers.md` に `Completion Rounds` / `Completion Baseline` field を追加
- **reviewer 実起動検証 + design 順方向整合（塊B）**: `references/inline-review-checklists.md` に reviewer が実際にコマンドを実行したかを検証する checklist と、実装が design の意図した方向へ進んでいるかの順方向整合項目を追加。`agents/gdd-implementation-reviewer.md` / `agents/gdd-security-reviewer.md` の Review Focus と `skills/gdd-implementation-gating/SKILL.md` Step 7 の escalation 条件を拡張
- **cross-session HITL 通知（塊C-1）**: `references/phase-progression.md` に `## Cross-Session Messaging`（送信 allowlist・受信分類・受信側の権限境界・fail-open 禁止）を新設。`references/state-field-tiers.md` に `Origin Session` / `Origin Notification` / `Direction Check` field を追加。cross-session 経由の返答が承認・マージ承認・中止を偽装できないよう、`hooks/scripts/lib/transcript.py` に `last_user_turn_is_peer()`、`hooks/scripts/validate-steering-write.py` に peer turn 直後の危険な state 書込みを block する機械的境界（`NON_DEMOTABLE_CATEGORIES` に `peer_turn_state_write` を追加）を実装
- **`human_check_gate` tier（塊C-2）**: 新規 agent `agents/gdd-direction-checker.md`（Fable + effort=medium）を追加し、`references/fixed-models.md` に tier 定義を登録。requirements-gating の human check 直前と `human_recheck_required` 提示直前の 2 発動点でのみ dispatch し、既定案は変更せず代替案を判断材料として HITL に埋め込む（design-gating・completion-check・express 初回 HITL は対象外）

#### Changed

- budget 収支確定（塊D）: `skills/gdd-writing-skills/SKILL.md` の development-only テンプレート（新規 Phase Gate skill / Methodology skill 雛形）を `docs/references-archive/gdd-writing-skills-templates.md` へ分離。`references/team-onboarding.md` を `docs/references-archive/team-onboarding.md` へ移設し、参照している 7 ファイル 11 箇所のパスを更新
- express / standard runtime token budget 超過（T-1〜T-4 の追記分）を、同一ファイル内の重複説明・冗長な言い回しの圧縮で解消（契約の意味・数値・fail-closed 条件は変更なし）

#### Fixed

- `docs/VERSIONING.md` の「統合先の消費済み版数」が origin/main 取り込み時に更新されておらず stale だった点を、origin/main の複数回の進行それぞれで是正
- completion-check remediation で `test_reviewer_live_execution_contract.py` / `test_peer_turn_write_boundary_contract.py` の一部 needle が file-global `assertIn` のため退行を検知できなかった問題を、section 限定 assert とサブプロセス経由の import bootstrap regression test で解消
- `hooks/scripts/lib/transcript.py` の peer 判定が `item.get("origin", {}).get(...)` 形だったため、`"origin": null` / `"message": null` を含む transcript record で `AttributeError` が送出され hook 全体が落ちる問題を、`isinstance` ガードで修正（peer 判定は安全側の False に倒す）
- `Origin Session`（cross-session 通知の宛先）の write-once が文書契約だけで機械強制されておらず、既存値を別 ID へ書き換えると送信内容 allowlist を通っても第三者セッションへ HITL 要約と steering path が送られる問題を、`hooks/scripts/validate-steering-write.py` の新規検査 `collect_origin_session_rewrite_violations()` で修正（`state.md` への異なる値の書込のみ deny。初回書込と同値の再書込は許可。category `origin_session_rewrite` は非降格）。`STATE_REQUIRED_FIELDS` は変更なし
- `agents/gdd-direction-checker.md` が発動点 (a)（requirements-gating の human check 直前 = 人間承認前）でも `Approved Direction` を必須入力にしていたため、`human_check_gate` の主要な発動点で毎回「参照不能（入力不足）」に落ちて方向確認が走らない問題を、入力契約の発動点別分岐で修正
- `Completion Baseline` の更新契約が `references/gate-checklists.md`（初回のみ記録）と `references/state-machine.md` / `references/state-field-tiers.md` / `skills/gdd-completion-check/SKILL.md`（各 Round 開始時に記録）で矛盾しており、後者どおり上書きすると 2 回目以降の再検証 diff が空になる問題を、4 箇所すべて「初回のみ記録・以降上書きしない」に統一して修正
- `references/state-machine.md` の Round 上限超過 route（`Route In Progress=human_recheck_required` + `Next Action=gdd-systematic-debugging`）が、同じ正本の Resume 時 state 整合性検証（`human_recheck_required` なら `human-check-waiting`）と矛盾し再開時に fail-closed で止まる問題を、整合性検証側に carve-out（`Resume From=human-check-waiting` かつ `Human Check Status=pending` が揃う場合限定）を明示して修正。`Next Action` 許容値表は変更していない
- `Fable 確認`（`human_check_gate` の方向確認）の HITL 表示契約が full template にしかなく、一次表示の正本である `references/human-check-template-compact.md` には挿入位置も必須語も無かったため、通常の requirements HITL で表示から落ちても契約テストが通る問題を、compact への埋込枠追加と位置を含む契約テストで修正
- バックグラウンド Agent の完了通知 `<task-notification>` が `_HOOK_INJECTION_PREFIXES` に無く人間ターンと判定されていたため、peer message の直後に無関係な Agent が完了しただけで peer 状態が解除され、承認・中止 write の境界を人間の発話なしに迂回できる問題を、`_TASK_NOTIFICATION_TEXT_PREFIX` の追加で修正
- `hooks/scripts/lib/transcript.py` が JSON として妥当でも最上位が `null` / 配列 / 文字列の transcript 行で `AttributeError` を送出し、peer 判定を呼ぶ write hook 全体が落ちる問題を、`isinstance(item, dict)` ガードで修正
- peer turn の書込検査と `Origin Session` write-once 検査がどちらも chunk（追加文字列）だけを見ていたため、値のみを置換する `Edit`（`old_string="pending"` / `new_string="approved"` 等）では field 名が現れず security boundary を素通りする問題を、`project_edited_text()`（対象 state.md へ Edit / MultiEdit を仮想適用した書込み後テキスト）の field 値でも判定することで修正。deny するのは「この書込みで値が変わる」ときだけ
- `collect_origin_session_rewrite_violations()` の「初回書込みは無条件許可」により、`Origin Session` を持たない `state.md` へ peer turn から攻撃者 ID を初回書込みでき、その値が write-once で固定されて以後の HITL 要約の送信先になる問題を、peer turn 中は初回書込みも deny することで修正（正当な初回設定は起動元セッション = 非 peer ターンが行う）
- `validate-steering-write.py` の `from lib.transcript import` が、既に `sys.modules["lib"]` に `scripts/lib` がキャッシュされたプロセスで `ModuleNotFoundError` になる問題を、import 前後の `lib` / `lib.*` エントリ退避・復元で修正（既存の import テストは空の interpreter しか見ておらず検知できていなかった）
- `human_check_gate` tier が `scripts/resolve-gdd-model.py` の phase 表に登録されておらず、Cursor / Codex の worker dispatch（`run-gdd-worker.py --phase gdd-direction-checker`）が既定の `light_task` に落ちて Grok 4.5 / gpt-5.6-terra が選ばれる（正本の Opus 5 / gpt-5.6-sol と食い違う）問題を、`gdd-direction-checker` phase と `human_check_gate` tier の登録で修正
- `Origin Session` の write-once を、宛先を**削除**してから別 ID を「初回値」として設定する 3 経路（行ごと消す `Edit`（`new_string=""`）/ 全文 `Write` で行を省く / 削除のみの `ApplyPatch`）で迂回できる問題を修正。`main()` の「content chunk が空なら早期 allow」を security boundary の 2 検査には適用しないようにし、`project_written_text()`（`Write` は `content` が書込み後の全文）と `patch_removes_state_field()`（削除行から検出）を追加して、判定を「書込み後の値が既存値と変わるか」に一本化した
- `hooks/scripts/lib/transcript.py` の text block で `text` が JSON `null` / 数値のとき `t.strip()` が `AttributeError`、`tool_result` 側は正規表現に渡って `TypeError` になり、peer 判定を呼ぶ write hook 全体が落ちる問題を、`_block_text()` ヘルパによる文字列限定の取り出しで修正（`last_user_turn_is_peer` と `parse_transcript` の同型 3 箇所へ横展開）
- `human_check_gate` の再起動抑止が同一 timestamp の `done` だけを見ており、失敗値 `Direction Check: unavailable (<理由>)` が timestamp を持たないため、起動不能後の compaction / resume で同一 HITL に対して何度でも再 dispatch できてしまう問題を、失敗値にも HITL 到達の timestamp を持たせ（`unavailable (<HITL 到達の timestamp>: <理由>)`）、同 timestamp の `done` / `unavailable` のいずれかを「起動済み」として扱う契約に修正
- `references/human-check-template-compact.md` の `Fable 確認:` 埋込 schema が 2 出力（方向 OK / 既定案を変更しない）しか許しておらず、direction checker の `参照不能（入力不足）` と dispatch 起動不能の 2 経路では結果を偽装するかテンプレート違反で省略するしかない問題を、失敗時の表示形式 2 形（`参照不能（入力不足）` / `起動不能（<理由>）`）の追加で修正（4 形の正本は `references/human-check-template.md`。compact の等価削減で express token budget は維持）
- `scripts/resolve-gdd-model.py` の `classify_tier()` が phase tier を返す前に `large_working_set` / `undocumented_step` / `final_review` 等の signal 昇格を評価するため、direction checker の入力に「広いスコープ」等が含まれるだけで `general_heavy_risk` になり正本と食い違う問題を、`remediation_loop` と同じ用途固定 tier として `human_check_gate` を signal 昇格より先に確定することで修正
- `validate-steering-write.py` は `hooks/hooks.json` 上で `Write|Edit|MultiEdit|ApplyPatch` にしか配線されておらず、Bash 経由の `.steering/**` 書込は無検査で通る（本 PR 以前からの制約）。新しい検出機構は実装せず、ADR の「唯一の PreToolUse 関門」という不正確な表現を実際の配線内容に訂正し、既知の限界として明記した
- `Origin Session` write-once 保護の残る迂回 3 点を、chunk 集約の未スコープ化という共通の根本原因ごと修正: (1) `ApplyPatch` の `*** Delete File:` が path 収集から漏れ、既存値ごとファイルを削除して再設定できた（`parse_patch_paths()` に Delete File を追加、`patch_deletes_file()` で検出）(2) 既存値を残したまま別の値の行を追加すると `state_field_value()` が最初の 1 件だけを見て「変化なし」と誤判定した（`state_field_values()` で全出現を見て複数値・異なる値を deny）(3) `ApplyPatch` の追加行が対象ファイルごとにスコープされておらず、別ファイル（`worklog.md` 等）へ既存値と同じ行を先に書くと実際の変更を隠せた（`patch_added_lines()` を新設し `patch_removed_lines()` と対称な section 単位スコープに統一）。あわせて peer turn の値再構成が `state.md` 限定だったため `tasklist.md` の `Next Action` を値だけ置換する `Edit` が素通りする問題も、対象 field ごとに正本ファイルを持つ方式で修正
- `scripts/resolve-gdd-model.py` の `human_check_gate` 固定判定（signal 昇格対策）が `--complexity` の明示指定より後ろにあり、`--phase gdd-direction-checker --complexity heavy` 等で迂回できた問題を、phase 固定を complexity 判定より先に確定することで修正
- `references/phase-progression.md` の peer 識別基準が `isMeta: true` **かつ** `origin.kind: "peer"` という AND 条件で記述されていたが、当時の実装は `isMeta` / `origin.kind` / 固定 text prefix fallback の OR 条件だったため、記述を実装どおりに訂正した（`isMeta` はこの後の独立セルフレビュー是正で判定条件から除外されている。下記のエントリ参照）
- 新規 `state.md` の作成時（`PreToolUse` の段階でファイルがまだ存在しない）、`Path.read_text()` の `OSError` を `continue` していたため `collect_origin_session_rewrite_violations()` の検査全体が skip され、peer turn からの `Write` で `Origin Session` を初回設定できた（Finding D の初回書込み deny が新規作成では効かない）問題を、`OSError` を「既存値なし」として扱い後続判定へ進めるよう修正
- `skills/gdd-implementation-gating/SKILL.md` の escalation 条件「実起動できない場合」が quick / quick (express) の「subagent escalation は行わない」規約と衝突していた問題を、quick/express では既存の「High 疑いは standard へ昇格」経路で Task Size を上げてから再評価するよう明記して修正
- `validate-steering-write.py` がコード健全性の目安（1 ファイル 1500 行以内）を超過した問題を、patch 本文を path 単位にスコープ化する純粋関数群を `hooks/scripts/lib/patch_scoping.py` へ抽出して解消（1540 行 → 1425 行）
- （Copilot レビュー是正の再発）move 迂回修正・peer 判定修正の追加でファイルが再度 1507 行まで増え、コード健全性の目安を再超過していた（上記エントリの「1425 行」という記録も stale）問題を、秘匿情報・PII・placeholder 検出の純粋関数群（`find_email` 等・関連 regex 定数）を新規 `hooks/scripts/lib/secret_scanning.py` へ抽出して解消（1507 行 → 1368 行）
- `hooks/scripts/lib/patch_scoping.py` が `ApplyPatch` の `*** Move to:` を認識しておらず、`*** Update File: <old>` の直後に置くと section が汎用の `*** ` catch-all で閉じ、旧 path からの削除にも新 path 宛の書込みにも判定が及ばなかった（`state.md` を move 元にすると既存 `Origin Session` を検査なしで消せ、任意ファイルを `state.md` へ move 先にすると移動先が `steering_targets` に入らず検査を完全に迂回できた）問題を、`parse_patch_paths()` に move 先の収集、`parse_patch_sections()` に move 先側だけへ内容を積む設計、`patch_deletes_file()` に move 元の判定を追加して修正
- `parse_transcript()` が peer turn を `last_user_text` 候補から除外する結果、`[human: "/gdd-dev ...", peer: "中止"]` のような並びで `last_user_text` が古い人間発話のまま stale で残り、`gdd_stop_hook.py` の `looks_like_gdd_continuation()` がそれを継続意図と誤判定して peer 受信を契機に停止中の workflow を再開しうる問題を、`last_user_turn_is_peer()` の先行判定で修正
- `human_check_gate` の再 dispatch 抑止と `Origin Notification` の重複排除が使う「HITL 到達の timestamp」の正本が未定義で、resume 時の再計算方式次第で永久抑止 / 常時再起動のどちらにも倒れうる問題を、`Human Check Status` の `updated_at` を正本と定義して解消
- completion-check の stale 3 分類 (ii) で、`Route In Progress=implementation_fix_only` の残存を `git log` や検証コマンド単独で (ii) に落とせるため、修正コミットより古い `Reviewed by:` 行を根拠に impl-gate 再実行を省略できる問題を、`Reviewed by:` 行が修正コミット以降であることの確認を必須化して修正
- （独立セルフレビュー是正、Copilot 巡外）`hooks/scripts/lib/transcript.py` の peer 判定が `isMeta: true` 単独を peer 信号として使っていたため、skill 起動時のプリアンブルや Stop hook feedback 等の無関係な host 注入（実 transcript 検証で 31 件中 27 件が false positive）まで peer turn と誤検出し、`peer_turn_state_write`（非降格 boundary）が正当な承認・マージ承認・中止の書込みを block する問題を、`isMeta` を外し `origin.kind=="peer"` + text prefix fallback のみで判定するよう修正
- `state_field_pattern()` が field 名周りの単一任意 backtick しか許容しておらず、二重 backtick / field 名内 backtick / bullet 前置 backtick を含む書込みが field 行未検出のまま素通りする（読み取り側 `gdd_extract_doc_field()` は行内の backtick を全 `gsub` するため実際には値が書き換わる）`Origin Session` write-once 迂回を、field 行判定の直前に backtick を全除去する正規化で修正
- `project_written_text()` / `project_edited_text()` が呼び出し元の `tool_name` を確認せず常時 Edit 投影を行っていたため、`ApplyPatch` payload に対象ファイルへ存在しない文字列を狙う無害な `old_string`/`new_string` を混ぜるだけで「変化なし」の projected テキストが本物の patch 削除の検出（`patch_removes_state_field()` / `patch_deletes_file()`）より先に確定してしまう `Origin Session` write-once 迂回を、`tool_name in ("Edit", "MultiEdit")` のときだけ Edit 投影を行うよう修正
- `is_steering_path()` / `is_state_md_path()` / `is_tasklist_md_path()` が大文字小文字を区別する文字列比較のみで判定していたため、大文字小文字を区別しないファイルシステム（macOS 既定の APFS / Windows）で casing を変えた path が `steering_targets` から漏れ、この hook の全検査を素通りしたまま実 file を書き換えられる問題を、大文字小文字を無視した比較に統一して修正
- `hooks/scripts/lib/transcript.py` が transcript を厳格 `utf-8` decode していたため、不正バイト 1 つ（`UnicodeDecodeError` は `OSError` のサブクラスではなく既存の `except OSError` で拾えない）で hook プロセスごと落ち、peer / write-once / secrets の全検査が無効化される（fail-open）問題を、`errors="replace"` での読み取りに変更して修正（`hooks/scripts/lib/detect-steering.sh:gdd_extract_route_in_progress` の既存の同型修正に揃える）
- `project_written_text()` の `Write` 判定が `file_path` key だけを見ていたため、対象 path を `path` / `target_file` / `target_notebook` 等の別 key で示す harness（Cursor / Codex 等）で target が常に不一致になり、全文 `Write` が `Origin Session` 行を省く形の削除を検出できない問題を、`extract_target_paths()` と同じ key 集合を見るよう修正
- `last_user_turn_is_peer()` が record 内の複数 text block のうち最初の非空 block だけを見て走査を打ち切っていたため、無害な block が先・peer marker 付き block が後という並びで `parse_transcript()`（最後の block を採用）と判定が食い違い peer turn を見落とす問題を、`parse_transcript()` と同じ「最後の非空 block を採用」に統一して修正
- （上記の再検証是正）「最後の非空 block を採用」への統一は単一 block しか peer 判定に使わない設計自体を変えておらず、非対称を反転させただけで「peer marker 付き block が最初・無害な block が後」（`<task-notification>` 等 injection-prefix 一致 block が最後だとさらに悪化し、直前の人間発話まで遡って peer 状態を見落とす）では依然として peer turn を見落とす問題が残っていた。`text`（injection-prefix skip / 空判定用）は最後の非空 block を採用したまま、peer marker の検出だけは record 内の**全 block を独立に走査**するよう修正し、いずれの block に marker があっても検出できるようにした
- `hooks/scripts/lib/transcript.py` の `parse_transcript()` / `last_user_turn_is_peer()` が `str.splitlines()` で transcript を行分割していたため、JSON が escape を要求しない U+2028 / U+2029 等（Node の `JSON.stringify` は既定で escape しない）を peer record 自身の text 値に埋め込むと record が 2 断片に割れてどちらも `json.loads()` に失敗し、peer 判定を完全に迂回できる問題を、JSONL の実際の record 区切りであるリテラル `"\n"` での分割に変更して修正
- `ApplyPatch` の診断行（diff hunk）を持たない純粋 move（`*** Update File: <old>` の直後に `*** Move to: <new>` だけが続く move。ファイル名だけを変え内容は変えない）は `parse_patch_sections()` が移動先の section を空リストのまま作るため、`patch_added_lines()` / `project_written_text()` のどちらでも投影不能扱いになり、移動先（`state.md`）の書込み後内容が一切検査されなかった。`.steering/` 外にあるこの hook の検査対象外ファイル（既に `Origin Session` を含みうる）を hunk 無しで `state.md` へ move するだけで write-once 検査を完全に迂回できる問題を、純粋 move の移動先に対して移動元の現在のディスク内容を書込み後内容として判定する `patch_pure_move_source()` の新設で修正
- `parse_transcript()` の `last_user_text` 選定が、`last_user_turn_is_peer()` とは異なり最後の非空 text block だけで peer 判定していたため、複数 block の record で peer marker が先頭 block・無害な文（manual-merge trigger の `merged` 等）が末尾 block だと、その無害な文が peer 判定を経ずに `last_user_text` へ採用され、`gdd_stop_hook.py` の peer guard より前段で `last_user_text` を読む処理を peer が起動できてしまう問題を、peer marker の検出を record 内の全 block を独立に走査する方式に統一して修正（F-8 と同根の非対称）
- `CHANGELOG.md` / `docs/adr/20260904-w29-gate-feedback-loop.md` / `references/phase-progression.md` の `isMeta` に関する記述が、独立セルフレビュー是正（`isMeta` を判定条件から除外）より前の実装を前提にしたまま残っており、最終的な判定条件（`origin.kind=="peer"` または固定 text prefix。`isMeta` 単独は不使用）と矛盾していた問題を、実装どおりに訂正
- `references/gate-checklists.md` の Completion Round 再検証手順（`git diff <Completion Baseline>...HEAD`）が commit 間の差分のみで staged/unstaged/untracked を含まないため、blocker 修正が未コミットのまま次 Round に入ると差分が空になり修正箇所を再検証できない問題に、再検証前 commit の必須化を明記して修正
- `patch_pure_move_source()`（診断行 = diff hunk を持たない move だけを対象にした初版修正）は、対象 field と無関係な hunk が 1 行でも付く通常の move+hunk には対応しておらず、hunk に現れない移動元の既存 `Origin Session` が無検査のまま移動先へ運ばれる write-once 迂回が残っていた問題を、診断行の有無を問わず move である限り移動元を検査する `patch_move_sources_for()` へ設計を改め、同一移動先への複数 move の全件収集・hunk による明示的な field 削除の除外・移動元読み取りの `errors="replace"` 化（`UnicodeDecodeError` による hook クラッシュの防止）とあわせて修正
- `parse_patch_sections()` が `*** Move to:` 検出時に旧 key の section を破棄していたため、hunk が `Move to:` より前（非正規な順序）に置かれる patch で hunk の内容が旧 key・新 key のどちらにも属さず完全に消え、`Origin Session` を書き換える hunk ごと無検査になっていた問題を、旧 key の内容を新 key へ引き継ぐよう修正
- `hooks/scripts/lib/transcript.py` の `parse_transcript()` が `content` list 中の bare str block（dict ではなく文字列そのものの block）を peer marker の判定対象にしておらず、`origin.kind` を送らない host からの bare str block 経由の peer message を見落とす問題と、空白のみの trailing text block が `if t:` により直前の意味のある candidate を上書きしていた問題を修正（`last_user_turn_is_peer()` にも同様の対応を追加し、両関数の判定基準を統一）
- `hooks/scripts/gdd_stop_hook.py` の `maybe_block_incomplete_post_merge_continuation()` が、`looks_like_gdd_continuation()` 用の peer-turn guard（Finding Z）より**前**に呼ばれるため、その guard の保護を受けていなかった問題を修正。`[human: "mergeした", peer: "..."]` という並びでは `tv.last_user_text`（peer 除外済み）が古い `mergeした` のまま残り、直近の実会話ターンが peer であるにも関わらず `decision:block` が出て workflow を再開させていた。この経路にも先行 peer 判定を追加し、他の権限境界と同じ「peer message は停止中の workflow を再開させない」原則を適用した

- 塊A（completion-check loop safety）: `references/state-machine.md`, `skills/gdd-completion-check/SKILL.md`, `references/gate-checklists.md`, `references/state-field-tiers.md`, `references/rollback-patterns.md`
- 塊B（reviewer 実起動+design順方向整合）: `references/inline-review-checklists.md`, `agents/gdd-implementation-reviewer.md`, `agents/gdd-security-reviewer.md`, `skills/gdd-implementation-gating/SKILL.md`
- 塊C-1（cross-session HITL通知）: `references/phase-progression.md`, `references/common-guardrails.md`, `references/requirements-template.md`, `hooks/scripts/lib/transcript.py`, `hooks/scripts/lib/constants.py`, `hooks/scripts/validate-steering-write.py`, `skills/gdd-brainstorming/SKILL.md`, `skills/gdd-requirements-gating/SKILL.md`, `skills/gdd-pr-review-followup/SKILL.md`, `skills/gdd-requirements-amendment/SKILL.md`, `skills/gdd-systematic-debugging/SKILL.md`
- 塊C-2（human_check_gate tier）: `agents/gdd-direction-checker.md`（新規）, `references/fixed-models.md`, `references/human-check-template.md`, `references/requirements-gating-steps.md`, `references/subagent-dispatch.md`, `references/cursor.md`, `references/codex.md`, `skills/gdd-model-routing/SKILL.md`, `commands/gdd-dev.md`
- PR 旧#31 レビュー是正（Copilot 8 巡・計 44 件 + 独立セルフレビュー 3 巡・計 11 件）: `hooks/scripts/validate-steering-write.py`, `hooks/scripts/lib/patch_scoping.py`（新規）, `hooks/scripts/lib/secret_scanning.py`（新規）, `hooks/scripts/lib/transcript.py`, `hooks/scripts/lib/constants.py`, `hooks/scripts/gdd_stop_hook.py`, `scripts/resolve-gdd-model.py`, `agents/gdd-direction-checker.md`, `references/phase-progression.md`, `references/state-field-tiers.md`, `references/state-machine.md`, `references/gate-checklists.md`, `references/rollback-patterns.md`, `references/requirements-gating-steps.md`, `references/human-check-template-compact.md`, `references/human-check-template.md`, `references/fixed-models.md`, `skills/gdd-completion-check/SKILL.md`, `skills/gdd-implementation-gating/SKILL.md`, `docs/adr/20260904-w29-gate-feedback-loop.md`, `tests/checks/hooks.sh`, `tests/test_steering_retention_contract.py`, `tests/test_distribution_readiness_contract.py`
- 塊D（budget収支確定+release）: `docs/references-archive/gdd-writing-skills-templates.md`（新規）, `docs/references-archive/team-onboarding.md`（`git mv`）, `skills/gdd-writing-skills/SKILL.md`, `skills/gdd-using-git-worktrees/SKILL.md`, `skills/gdd-using-skills/SKILL.md`, `references/requirements-template-express.md`, `references/task-sizing.md`, `README.md`, `docs/ONBOARDING.md`, `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`, `docs/DISTRIBUTION_READINESS.md`, `docs/VERSIONING.md`, `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.39.0）
- 契約テスト（新規）: `tests/test_completion_check_loop_safety_contract.py`, `tests/test_reviewer_live_execution_contract.py`, `tests/test_cross_session_hitl_contract.py`, `tests/test_peer_turn_write_boundary_contract.py`, `tests/test_human_check_gate_tier_contract.py`
- 契約テスト（既存を更新）: `tests/checks/agent-effort-schema.sh`, `tests/checks/hooks.sh`, `tests/checks/skill-body-budget.sh`, `tests/test_model_routing_contract.py`, `tests/test_distribution_readiness_contract.py`

#### User Action Required

- なし。既存の GDD workflow の使い方は変わらない。cross-session messaging 経由のメッセージや `human_check_gate` の方向確認は既存の HITL 表示に判断材料として追加されるだけで、承認フロー自体は変わらない

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`: 全 BLOCK OK（exit 0）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q`: `1817 passed, 1 skipped, 11972 subtests passed`（fail 0。origin/main 取り込み（PR 旧#32/#33/#36 分含む）+ completion-check remediation / pr-review remediation / PR 旧#31 レビュー是正 8 巡 + 独立セルフレビュー 3 巡での regression test 追加により母数が baseline 1556 passed から増加、fail 増加なし）

### [0.38.7] - 2026-09-05

#### Summary

`scripts/lint-ac.py` の AC ID 文法に 2 件の取りこぼしがあり、GDD completion-check（`20260904-state-field-reader-unification`）で実測された。(1) AC 定義行の判定が「ID の直後に `:`」の形しか受けず、`- **AC-8-2**（DH-1、人間承認済み）: ...` のように ID と `:` の間に注記が入る定義を認識できなかった。その結果 `tasklist.md` の `method=ac:AC-8-2` や RED Evidence の `- AC: AC-8-2` が「requirements に存在しない架空 AC」と誤判定され exit=1 になっていた（false positive）。(2) AC ID の複合サフィックスが数字しか受けず、`AC-3-d` が `AC-3` に潰れていた。定義側も参照側も同じ ID に潰れるため矛盾が検出されず、**エラーも警告も出ないまま** coverage 検査を素通りしていた（false negative）。実例として `20260904-state-field-reader-unification` の `AC-3-d`（意図的な挙動変化 missing→present を固定する唯一の AC）が機械検査の対象外になっており、当該 `tasklist.md` にも「lint 側の限界」として記録されていた。

#### Added

- `tests/test_lint_ac_id_grammar_contract.py`: 上記 2 件を固定する回帰テスト（新規）。注記つき定義の認識、本文中の偶発的な `AC-N` 言及を定義と誤認しないこと、`AC-3-d` の独立トークン化、`AC-3` のみ定義された状態で `AC-3-d` を参照した場合に ERROR になること、既存 ID 形（`AC-1` / `AC-2a` / `AC-3b` / `AC-F1` / `AC-8-2` / `AC-E9-1` / `AC-E9-1a`）の解決結果が不変であることを検査する

#### Changed

- `scripts/lint-ac.py`: `_AC_ID_CORE` の複合サフィックスを `(?:-\d+)?` から `(?:-(?:\d+|[a-z]))?` へ拡張し、`AC-3-d` 形を表現できるようにした。`AC_ID_RE` / `AC_DEF_RE` / `AC_REF_RE` の 3 者が同じ core を共有するため、定義・`method=ac:` 参照・RED Evidence の `- AC:` 行すべてで `AC-3-d` が `AC-3` と区別される

#### Fixed

- `scripts/lint-ac.py`: `AC_DEF_RE` に注記部（`_AC_DEF_ANNOTATION`）を追加し、`- **AC-8-2**（DH-1、人間承認済み）: ...` のように ID と `:` の間に括弧注記が入る定義行を認識するようにした。注記として受けるのは括弧で閉じた塊（`（）` / `()` / `［］` / `[]` / `【】`）のみで、かつ注記の直後に `:` / `：` が来ることを要求する。これにより `- AC-2 (前述) は本 task の対象外: 次 task で扱う` のような本文中の偶発的言及は従来どおり定義と見なさない

#### Breaking Contract Changes

- なし（検出面が広がるため、`AC-3-d` 形を使っており `tasklist.md` 側が `AC-3` としか対応づいていない steering では、新たに「verify されない AC ID」WARN または「存在しない AC ID を参照」ERROR が出うる。これは従来 false negative だった箇所の顕在化であり、意図した挙動）

#### Affected Files

- `plugins/gate-driven-development/scripts/lint-ac.py`
- `plugins/gate-driven-development/tests/test_lint_ac_id_grammar_contract.py`（新規）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.38.7、統合先消費済み版数 v0.38.6）

#### User Action Required

- なし。既存の requirements.md / tasklist.md（本リポジトリ内 markdown 221 件で旧新の正規表現差分を実測、変化 0 件）では解決結果が変わらない

#### Validation / Eval Impact

- `tests/test_lint_ac_id_grammar_contract.py` を新設（RED 6 件を確認してから実装 → GREEN 9 passed / 8 subtests）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q`: 全 contract test OK（回帰なし）
- `bash tests/validate-plugin.sh`: 全 BLOCK OK
- 実データ確認: `20260904-state-field-reader-unification` の steering に対し、修正後は `AC-3-d` が独立 AC として認識され（旧: `AC-3` に潰れて不可視）、`method=ac:AC-3-d` と対応づいて exit=0 のまま
- Superpowers Benchmark Summary: not_applicable (no changed GDD primitive)

### [0.38.6] - 2026-09-04

#### Summary

`scripts/collect-gdd-telemetry.py`・`scripts/gdd_task_binding.py`・`hooks/scripts/validate-steering-write.py`（`tasklist_parse` import 箇所）の 3 箇所で、`sys.path.insert(0, _LIB_DIR)` → `from tasklist_parse import ...` → `sys.path.remove(_LIB_DIR)` が try/finally で保護されておらず、import が例外を送出した場合に `_LIB_DIR` が `sys.path` に残留する欠陥を修正（PR 旧#32、Copilot review 指摘）。同型の問題は `validate-steering-write.py` の別 import 箇所（`lib.transcript`）で PR 旧#31 にて既に修正済みだったが、同ファイル内の `tasklist_parse` import 箇所は横展開の対象から漏れていた。

#### Added

- `tests/test_sys_path_rollback_on_import_failure_contract.py`: `tasklist_parse` の import 失敗を注入し、`sys.path` に残留しないことを対象スクリプトごとに固定する回帰テスト（`tests/_plugin_module_loader.py` の共有ローダーを再利用）。加えて、`sys.path.insert(0, X)` が新たに try/finally 保護なしで追加されていないことを、変数名 `X` に依存せずバックリファレンス正規表現で構造的に検査するテストを追加（独立セルフレビューで、初版の検知ロジックが変数名 `_LIB_DIR` にハードコードされていた・finally 内で実際に remove しているかまで見ていなかった、の2点の不備を発見し修正）

#### Changed

（なし）

#### Fixed

- `scripts/collect-gdd-telemetry.py` / `scripts/gdd_task_binding.py` / `hooks/scripts/validate-steering-write.py`: `tasklist_parse` の import を try/finally で保護し、import 例外時にも `_LIB_DIR` を確実に `sys.path` から除去する

#### Breaking Contract Changes

- なし

#### Affected Files

- `plugins/gate-driven-development/scripts/collect-gdd-telemetry.py`
- `plugins/gate-driven-development/scripts/gdd_task_binding.py`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/tests/test_sys_path_rollback_on_import_failure_contract.py`（新規）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.38.6、統合先消費済み版数 v0.38.5）

#### User Action Required

- なし。import が例外を送出しない通常経路の挙動は変わらない

#### Validation / Eval Impact

- `tests/test_sys_path_rollback_on_import_failure_contract.py` を新設: 3 スクリプトそれぞれで import 失敗時に `sys.path` が汚染されないことを固定
- `python3 -m pytest plugins/gate-driven-development/tests/ -q`: 全 contract test OK（回帰なし）
- `bash tests/validate-plugin.sh`: 全 BLOCK OK
- Superpowers Benchmark Summary: not_applicable (no changed GDD primitive)

### [0.38.5] - 2026-09-04

#### Summary

2 件の独立した修正を含む。(1) `validate-worktree-command.py`（root branch / GDD worktree guard）の git 呼び出し識別を、`-C <path>` のみ許容する固定正規表現 + 行全体の文字列 gate から token ベース判定へ置き換え（PR 旧#28）。(2) `gh_command_parse.py`（`gh pr merge` を検査する merge-gate hook のパーサ）の heredoc pipeline 境界検出 `PIPELINE_BOUNDARY_RE` が、実行される heredoc（`cat <<EOF |& bash` 等）で `&` を無条件に境界扱いし、bash interpreter の検出に失敗する欠陥を修正（PR 旧#30）。同型のバグは (1) の Copilot review が `git_command_parse.py` で発見していたもので、(2) は merge-gate hook 自身が使う同型パターンへ同じ修正を横展開したもの。

#### Added

- `hooks/scripts/lib/git_command_parse.py`: `push_command_parse.py` から移設した汎用 git コマンド解析（`tokenize` 系・nested shell 展開）+ 新規 `subcommand_candidates`（public）・`GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT`・`is_git_token`・`split_segments`

#### Changed

- `hooks/scripts/lib/push_command_parse.py`: 汎用部分を `git_command_parse` から import する re-export 形へ縮小（537 → 310 行）。public API（`tokenize` / `tokenize_with_boundary` / `NEWLINE_TOKEN` / `COMMAND_SEPARATOR_TOKENS` / `GIT_GLOBAL_FLAGS_WITH_ARGUMENT`）は不変
- `hooks/scripts/validate-worktree-command.py`: `command_creates_root_branch` / `command_creates_gdd_worktree_from_head` / `command_creates_gdd_worktree_from_local_default` を token ベース判定へ書き換え。global option を挟んだ root branch / GDD worktree 作成（false negative 3 系統）と、`git branch -a`/`-v`/`-vv` の読み取り専用操作・クォート内文字列への誤爆（false positive 2 系統）を解消

#### Fixed

- **`gh_command_parse.PIPELINE_BOUNDARY_RE` が `|&`/`&>`/`>&`/`<&` に含まれる `&` を境界と誤認する欠陥を修正**: `cat <<'EOF' |& bash` や `cat <<'EOF' 3<&0 | bash` のような実行される heredoc で、境界検出が `&` の直前で走査範囲を打ち切っていたため、本文中の interpreter 名（`bash`）が走査範囲外に落ち、heredoc 本文内の `gh pr merge` が merge-gate hook から不可視になっていた（guard bypass）。lookbehind/lookahead を追加し、`&&`・`;`・単独 `&`・`||` は従来どおり境界のまま、`|&`・`&>`・`>&`・`<&` 中の `&` だけを境界から除外する（`git_command_parse._PIPELINE_BOUNDARY_RE` と同一の正規表現へ揃えた）

#### Breaking Contract Changes

- guard の検出面が広がった: `git switch --create` / `--force-create`、`git worktree add ... -B ...`、base 省略の暗黙 HEAD 形（`git worktree add <path> -b codex/...`）が新たに deny される（human recheck で承認済み、design.md § Human Check Question）。未知の git global option は fail-closed（検出側に倒す）
- `lib/git_command_parse.py` の import に失敗した場合（ファイル欠落・構文エラー等）、`git` を含む Bash コマンドは判定不能として deny される（parser unavailable。復旧は該当ファイルの `git checkout --` またはプラグイン再インストール）

#### Affected Files

- `hooks/scripts/lib/git_command_parse.py`（新規）/ `hooks/scripts/lib/push_command_parse.py`（re-export 化）/ `hooks/scripts/validate-worktree-command.py`（token ベース判定）
- `hooks/scripts/lib/gh_command_parse.py`（`PIPELINE_BOUNDARY_RE` を修正）
- `tests/test_root_branch_guard_contract.py`（AC-1〜AC-8・AC-12 回帰テスト）/ `tests/test_push_command_parse.py`（`git_command_parse` の re-export・oracle テスト）
- `tests/test_merge_gate_hook_command_parse.py`（`|&`/`&>`/`<&` 経由の heredoc bypass を固定する回帰テストを追加）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.38.5 と統合先消費済み版数 v0.38.4）

#### User Action Required

- なし。既存の正当な GDD worktree 作成手順（`git worktree add <path> -b <branch> origin/<default-branch>`）は従来どおり動作する。merge-gate 側の修正も fail-open だった guard bypass を塞ぐのみで、正当な `gh pr merge` コマンドの挙動は変わらない

#### Validation / Eval Impact

- `tests/test_root_branch_guard_contract.py` に AC-1〜AC-8・AC-12 の回帰テストを追加
- `tests/test_push_command_parse.py` に `git_command_parse` の re-export・oracle・`split_segments` の直接テストを追加（既存 1243 行は無変更）
- `tests/test_merge_gate_hook_command_parse.py::GhCommandParseTests::test_executed_heredoc_body_through_ampersand_redirect_is_detected` を新設: `|&`/`&>`/`<&` の3パターンで `gh pr merge` が検出されることを固定（TDD で先に失敗を確認してから修正）
- `python3 -m pytest tests/ -q`: 1642 passed, 1 skipped, 11594 subtests passed
- Snyk Code Scan（変更ファイル個別）: issue 0 件

### [0.38.4] - 2026-09-04

#### Summary

`Route In Progress` を読む 2 経路（`select_route_in_progress()` / `gdd_extract_doc_field`）が同じ `state.md` に対して別の値を返していた不整合を修正。人間が `- Route In Progress: none | reason: 解除` を追記して route を解除しても、`run-session-start-hook.sh` / `run-user-prompt-submit-hook.sh` が最初の一致（古い route）を context に注入し続ける誘導ズレだった。

#### Fixed

- **`Route In Progress` の値選択規則を単一正本に統合**: 分岐は「行の選択」だけでなく、書式優先（正準形 `:` vs 旧等号形 `=`）・空値スキップ・注記除去（`none（注記）` の fail-open）・行頭アンカーの計 7 次元に及んでいた。`hooks/scripts/lib/tasklist_parse.py:select_route_in_progress()` を単一正本とし、shell 側は新設の `gdd_extract_route_in_progress`（`hooks/scripts/lib/detect-steering.sh`）から python へ委譲する形に統一した。汎用 reader `gdd_extract_doc_field` へこの field を渡す call site は機械検査で禁止する
- **存在判定（`gdd_validate_active_state_fields`）も同じ規約に揃えた**: 汎用 reader は最初の一致で `exit` するため、`- Route In Progress:`（値の無い書きかけ行）が先頭にあると後続の正しい行を見ずに「field 欠落」と誤判定し、正しく書かれている state.md の resume を塞いでいた
- **python3 不在時のフォールバックの locale 依存バグを修正**: 退避経路の識別子抽出に `[[:alnum:]]` を使うと、UTF-8 ロケールでは CJK 文字も alnum とみなされ、`systematic_debugging実装` のような識別子+全角の連結値で境界を見失っていた（`LC_ALL=C` とで結果が割れる）。ASCII 直書き（`[A-Za-z0-9_-]`）に統一し、python 側 `route_value()` と一致させた
- **独立セルフレビュー（code-review skill, high effort, 8 finder angles）で追加検出した 4 件の欠陥を remediation**（PR 旧#27 マージ前。詳細は下の「独立セルフレビュー」節）:
  - `gdd_extract_route_in_progress` が **python3 の任意の非ゼロ終了**（`UnicodeDecodeError` 等のデータ起因も含む）を「python3 不在」と同一視し、python3 が使える状態のまま本 PR が閉じたはずの stale route 再注入バグへ無言で退避していた。python 側の decode を `errors="replace"` にして根絶した
  - python3 不在時のフォールバックが `route_value()` の装飾除去（バッククォート/アスタリスク/引用符）と識別子先頭アンカー（数字始まりの値を切り詰めない）を再現していなかった。sed ベースの正規化を追加して一致させた
  - `run-user-prompt-submit-hook.sh` が同じ `state.md` の `Route In Progress` を 1 回の hook 実行内で 2 回（存在判定と表示用）別々に python3 起動して読んでいた。`gdd_validate_active_state_fields` が読んだ値を `GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS` として公開し、再利用するよう変更して 1 回に削減した

#### Affected Files

- `hooks/scripts/lib/tasklist_parse.py`（行頭アンカー強化、shell 委譲の docstring 追記）
- `hooks/scripts/lib/detect-steering.sh`（`gdd_extract_route_in_progress` 新設、存在判定の call site 切り替え、`errors="replace"` decode、装飾除去/識別子アンカーの正規化、`GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS` の公開）
- `hooks/scripts/run-session-start-hook.sh`（共有 reader へ切り替え） / `hooks/scripts/run-user-prompt-submit-hook.sh`（`gdd_validate_active_state_fields` が公開する値を再利用し、python3 の二重起動を解消）
- `references/state-schema.json`（`route_in_progress_reader` 節を追加）
- `tests/test_route_in_progress_reader_contract.py`（新規。両 reader を同じ表で拘束する契約テスト、独立レビューで追加した 4 テストクラス）
- `tests/test_merge_gate_followup_findings.py`（既存 class の docstring を新規契約テストへの参照に更新）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.38.4 と統合先消費済み版数 v0.38.3。分岐後に origin/main が別 PR（テストファイル分割）で v0.38.3 を先行出荷したため付け替え）

#### User Action Required

- なし。挙動は「解除の追記が効くようになる」「注記付き `none` が正しく解除扱いになる」という fail-open 側の是正のみで、正しく書かれた `state.md` の挙動は変わらない

#### 未確認事項（判断に使った情報の限界）

- **本リリースで意図的に未対応（follow-up）**: 独立セルフレビューが確認した 2 件は、対処範囲を広げると本 PR が閉じた「規約が複数実装に散る」欠陥のクラスを別の形で再生産するため、修正せず**既知の限界として明示**するに留めた
  - python3 が真に不在の場合、`gdd_extract_route_in_progress` のフォールバックは依然として最初の一致を返す（最終行採択を再現しない）。fence 追跡込みの選択規則をこのローカル関数へ複製すると規約が再び 2 実装に散るため、あえて実装しなかった。python3 の真の不在は環境要因であり、同じ環境では `Resume From` 等の他 field も同じ「最初の一致」規則のままなので、Route In Progress だけが劣化するわけではない。この判断は `tests/test_route_in_progress_reader_contract.py` の `test_multiple_matching_lines_return_the_first_not_the_last` がテストとして明示的に固定する
  - `gdd_validate_active_state_fields` の存在判定は `Route In Progress` だけ最終行採択（空値行をスキップ）になり、`Resume From` / `Human Check Status` は従来どおり汎用 reader の最初の一致のまま（空値の書きかけ行が先頭にあると誤って「欠落」と判定しうる）。これは本 PR が持ち込んだ退行ではなく既存の欠陥だが、汎用 reader `gdd_extract_doc_field` の挙動を変えると他の全消費者（field 種別を問わず 25 箇所超）に影響するため、本 PR のスコープ外とした

#### Validation / Eval Impact

- `tests/test_route_in_progress_reader_contract.py` を新設: 両 reader が同じ入力表（行選択・書式優先・空値・注記除去・行頭アンカー・fence 追跡・python3 不在時フォールバックの locale 差）で同じ値を返すことを固定。generic reader への call site を機械検査で禁止する 2 テストも追加
- 変異注入で全 13 変異を KILL することを実測（隔離コピー上で修正を戻し、テストが落ちることを確認）。途中で発見した 2 つの空洞（空値スキップの実害の向き、フォールバック経路の locale 依存文字クラス）は該当箇所を修正しテストを強化した
- **独立セルフレビュー（code-review skill, high effort）を PR 旧#27 マージ前に 1 周実施**: 8 finder angle（correctness A/B/C・reuse・simplification・efficiency・altitude・conventions）を並列 dispatch し、候補を 1-vote verifier で検証。6 件を報告（correctness 4 件・efficiency 1 件が CONFIRMED、correctness 1 件が PLAUSIBLE/スコープ外）。CONFIRMED 4 件のうち 4 件を remediation（下記）、PLAUSIBLE 1 件は既存の欠陥かつ汎用 reader の影響範囲が広いためスコープ外として follow-up task へ切り出した（本節「未確認事項」参照）
  - remediation した 4 件はいずれも新規テストを先に書いて RED を確認してから実装し、隔離コピー上の変異注入で判別力を実測（5 変異 KILL: `errors="replace"` の revert / 装飾除去 sed の削除 / 識別子先頭アンカーの削除 / `GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS` 代入の削除 / ups-hook のキャッシュ再利用を直接呼び出しへ戻す、の 5 形）
  - remediation 後に `tests/test_route_in_progress_reader_contract.py` の既存テスト 1 件（`test_both_context_injection_hooks_use_the_shared_reader`）が、正当な効率化変更（ups-hook がキャッシュを再利用する形に変わったこと）と衝突して落ちたため、直接呼び出し/再利用のどちらでも通す形に更新し、再利用側だけを個別に固定する専用テストを追加した
- `python3 -m pytest tests/ -q`: 1641 passed, 1 skipped, 11573 subtests passed（クリーン環境、並行負荷なし。独立レビュー remediation 後の最終計測）
- `bash tests/validate-plugin.sh`: 全 BLOCK OK（done-guard の `H=block-route-in-progress` を含め既存契約に回帰なし）
- Superpowers Benchmark Summary: not_applicable (no changed GDD primitive)

### [0.38.3] - 2026-09-03

#### Summary

`tests/test_merge_gate_hook.py`（2355行/155テストメソッド）を、`gdd-codebase-health.py` の large_file / python_function_count medium 指摘を解消するため関心事別に分割した。振る舞い変更なし（テスト構成の再編成のみ）。

#### Changed

- `tests/test_merge_gate_hook.py` を削除し、共有フィクスチャ（`_init_repo` / `_head_sha` / `_run_hook` / `_write_state` ほか）を `tests/_merge_gate_support.py` へ抽出（既存の `tests/_block_reason_support.py` パターンに準拠）
- テストクラスを関心事別の 7 ファイル（コマンドパース・hookプロセス/ゲート活性化系 2 ファイル・evidence gate・block reason 品質・contract）へ分割
- 独立セルフレビューで検出した stale filename 参照（`hooks/scripts/lib/gh_command_parse.py` / `constants.py` / `references/config-defaults.md` / `run-merge-gate-hook.sh` / `tests/test_merge_gate_followup_findings.py`）を新ファイル名へ更新し、`PLUGIN_ROOT` / `LIB_DIR` のローカル再定義を `tests/_merge_gate_support.py` からの import へ統一
- `docs/VERSIONING.md`: 統合先の消費済み版数を v0.38.0 → v0.38.2 へ更新（origin/main が別 PR で v0.38.1 → v0.38.2 を先行出荷したため 2 段階で追随）

#### Affected Files

- `tests/_merge_gate_support.py`（新規）
- `tests/test_merge_gate_hook.py`（削除）
- `tests/test_merge_gate_hook_command_parse.py` / `test_merge_gate_hook_gate_activation.py` / `test_merge_gate_hook_gate_regressions.py` / `test_merge_gate_hook_evidence_gate.py` / `test_merge_gate_hook_evidence_parsing.py` / `test_merge_gate_hook_block_reason_quality.py` / `test_merge_gate_hook_contracts.py`（新規）
- `hooks/scripts/lib/gh_command_parse.py` / `hooks/scripts/lib/constants.py` / `hooks/scripts/run-merge-gate-hook.sh` / `references/config-defaults.md` / `tests/test_merge_gate_followup_findings.py`（stale filename 参照の更新のみ）

#### User Action Required

- なし。テスト専用ファイルの再編成であり、`hooks/scripts/` の本番コード挙動は無変更（コメント中のファイル名参照のみ更新）

#### Validation / Eval Impact

- `python3 -m pytest tests/ -q`: 1621 passed / 1 skipped / 11491 subtests（分割前後・独立レビュー remediation 前後で一致を実測確認）
- `bash tests/validate-plugin.sh`: exit 0
- `gdd-codebase-health.py --mode changed --base-ref origin/main`: medium 指摘解消（high=0/medium=0/low=0）
- 独立セルフレビュー（code-review skill, high effort, 8 finder angles）を実施。correctness 系の指摘は 0 件、cleanup 系 3 件（stale filename 参照 / PLUGIN_ROOT・LIB_DIR 重複 / 関数数閾値への到達）を検出し、うち 2 件を本 PR 内で remediation（stale 参照修正・定数の import 統一）。残る 1 件（`test_merge_gate_hook_evidence_parsing.py` が関数数警告閾値 40 にちょうど到達し余裕がゼロ）は現時点で閾値を超えておらず、次に同ファイルへテストを追加する際の分割検討事項として記録するに留めた

### [0.38.2] - 2026-09-03

#### Summary

`lint-state-tasklist-continuity.py` が実運用の steering を通せなかった 2 件の欠陥を修正。20260901-pr-w17-merge-gate の completion-check で dogfooding 中に検出。

#### Fixed

- **Agentic Worker Header の bold 記法を読めるようにした**: `FIELD_PATTERNS` が `- Field: value` / `Field: value` しか読まず、header の正準記法 `**Field:** value` で記録された field を黙って照合対象外にしていた。`**Field:** value` / `**Field**: value` を追加した
- **未文書 field の必須化を解除**: 同 script は `tasklist.md` に `Requirements Revision` / `Design Revision` を必須要求していたが、この 2 つは同 script と自前 fixture 以外に存在せず（`references/` / `skills/` を全走査して 0 件）、`references/task-breakdown-steps.md` の Agentic Worker Header にも記入指示が無い。GDD が正規手順で生成した tasklist は構造的に通らなかった。段階計画の revision counter は `state.md` § Stage Continuity の `Plan Revision`（`references/state-machine.md` 正本）が既にあり、`requirements.md` / `design.md` には `Revision` field 自体が無いため、2 counter を新設せず **lint 側の必須要求を外す**方を採った。tasklist に記録がある場合だけ artifact の `Revision` と突き合わせる任意 field として扱う
- **`Task ID` 抽出の衝突を解消**: `extract_field()` がファイル先頭から最初の一致を返すため、`tasklist.md` § `Implementation Reviewer Selection` の per-task field `- Task ID: Task D` を steering task id と誤認して `task id mismatch: state=<slug> tasklist=Task D` を誤検知していた。tasklist 側の走査範囲を最初の `## ` 見出しより前の header region に限定した（`extract_header_region()` を新設）。state 側は全文走査のまま（`Task ID` の配置は contract に固定されておらず、`lint-resume-integrity.py` / `lint-worktree-provenance.py` / `gdd_task_binding.py` も全文で読む）

#### Affected Files

- `scripts/lint-state-tasklist-continuity.py`
- `tests/checks/state-tasklist-continuity-lint.sh`
- `references/prompt-contract-map.md` / `docs/DISTRIBUTION_READINESS.md`（runner の実際の検出力に合わせて note と Release Candidate チェック項目 16 を更新）
- `.gitignore`（`.serena/` を ignore 登録）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md` / `CHANGELOG.md`（版数 0.38.1 と統合先消費済み版数 v0.38.0）

#### User Action Required

- なし。`Requirements Revision` / `Design Revision` を独自に記録していた steering はそのまま突き合わせが続く

#### 未確認事項（判断に使った情報の限界）

- **本リリースで意図的に未対応（follow-up）**: 必須化を外した結果、canonical template が生成する artifact に対して本 runner が常時強制するのは `build-like resume requires tasklist.md Current Task` の 1 本だけになる。`Requirements Revision` / `Design Revision` に加え、tasklist の `Task ID`（Agentic Worker Header に無い）と design の `Stage Continuity Source`（design template に無い）も canonical には存在せず、いずれも steering 側が記録した場合だけ発火する。修正前は canonical artifact に対して常に exit 1 だったため、この runner が当該事故を実際に検出できていたわけではない（誤検知で止まっていた）。requirements / design 改訂後の tasklist 再生成は `Route In Progress` の運用（`references/task-breakdown-steps.md` Step 2）が正本で、機械強制の追加は `state.md` の `Plan Revision` を tasklist header へ引き継ぐ contract 追加を伴うため、design 改訂と human check を要する別 PR へ回す。`references/prompt-contract-map.md` / `docs/DISTRIBUTION_READINESS.md` の当該行は実態どおりに書き換えた

#### Validation / Eval Impact

- `tests/checks/state-tasklist-continuity-lint.sh` に 6 ケース追加: (1) 実運用形状（Agentic Worker Header / Revision 無し / `## Implementation Reviewer Selection` に per-task `Task ID` 有り）が pass すること、(2) header で宣言された task id が state と食い違う場合は依然 fail すること、(3) `Task ID` を `## Gate Status` の外に置いた state.md でも照合が走ること、(4) build-like な再開で `## Current Task` が無い tasklist は fail すること、(5) design の `Stage Continuity Source` が requirements を指さない場合は fail すること（既存 BAD / e2e fixture は Revision mismatch との併記形で、この分岐だけを無効化する mutation が生存していたため単独形へ分解した）、(6) Agentic Worker Header の正準記法 `**Task ID:** value` で記録された field も照合対象になること。6 ケースはいずれも固有の mutation を KILL することを実測済み（`extract_header_region` の無効化 / Revision 必須化の復活 / state 側の節絞り込み / task id 比較の削除 / `build-like` 条件の `if False:` 化 / design 分岐の `if False:` 化 / header region 境界の `^## `→`^#` 緩和 / bold パターンの削除）。case 2 の fixture は H1 見出しを持つ実運用形状に揃えた（H1 が無いと header region 境界を緩める mutation が生存する）。既存の OK / BAD ケースと `tests/fixtures/e2e-replay/tasklist-stale-after-design-revision` は無変更で green
- 実測: 修正前は実タスク `.steering/20260901-pr-w17-merge-gate/` で exit 1（3 件）、修正後は exit 0
- 独立セルフレビュー（pre-merge / fresh reviewer）を 5 周実施し、累計 high 2 / medium 10 を検出して全件 remediation 済み。3 周連続で指摘が出たため 4 周目以降は `remediation_loop` tier（Fable / effort=high）で起動し、5 周目は PR タイトル・本文も走査対象に含めた
  - 1 周目 high 1 / medium 2: (1) doc の検出力主張と実挙動の乖離（上記 未確認事項 に開示）、(2) state 側 `Task ID` 抽出を `## Gate Status` に絞っていた点を全文走査へ戻し回帰テストを追加（他 consumer は `lint-resume-integrity.py` / `lint-worktree-provenance.py` / `gdd_task_binding.py` とも全文走査）、(3) `.serena/` の ignore 登録
  - 2 周目 high 1 / medium 2: (1) 1 周目の doc 書き換えが `docs/DISTRIBUTION_READINESS.md` の runner 表だけに適用され Release Candidate チェック項目 16 に未適用だった、(2) 本 PR 後に唯一常時発火する `build-like resume` 判定が無テストで mutation 生存、(3) CHANGELOG の Affected Files が実 diff と不一致
  - 3 周目 medium 2: (1) 本節の追加ケース件数と review 周回記録が実態と不一致、(2) 出荷文書に新設した限定断定が `bounded-claim-evidence` の語彙を避ける形で書かれ実測記録が無かった → `references/prompt-contract-map.md` / `docs/DISTRIBUTION_READINESS.md` に実測記録節を追加し、当該 BLOCK の対象文書を 1 → 3 に増やした
  - 4 周目 medium 2: (1) PR タイトル・本文が remediation 前の内容（旧版数 / state 側の節絞り込み / 旧テスト件数 / 旧 pytest 件数）のまま残っていた、(2) design の `Stage Continuity Source` 判定を単独で KILL するテストが無く mutation が生存していた
  - 5 周目 medium 2: (1) header region の境界を緩める mutation（`^## `→`^#`）が生存していた（case 2 の fixture に H1 見出しが無かったため）、(2) 「記録すれば照合される」という限定断定が Agentic Worker Header の正準記法 `**Field:** value` では偽だった → `FIELD_PATTERNS` に bold 記法を追加し、doc の主張と実挙動を一致させた
- budget: `references/` 行数は 11922/11922 で不変（実測記録節を独立見出しにすると 11926 で超過したため、既存の Residual risk セル内へ畳んだ）
- 統合先の消費済み版数を v0.37.4 → v0.38.0 へ更新（origin/main の W-17 merge gate マージを取り込んだ upstream drift 反映）。出荷版数は 0.37.5 → 0.38.1 に付け替え
- **追加の upstream drift 反映**: 独立セルフレビュー継続中に origin/main が本 PR と無関係な別 PR（merge gate followup remediation）を v0.38.1 として先行出荷した。同一 branch から分岐した 2 系列が同じ版数を独立に消費したため、`docs/VERSIONING.md` § 統合先が消費済みの版数を再利用しない が警告する事故そのものが発生した（3 manifest と `**現行バージョン**` は文字列として同値のため無競合で auto-merge され、CHANGELOG.md のみが真の衝突として可視化された）。origin/main を merge し、統合先の消費済み版数を v0.38.0 → v0.38.1、出荷版数を 0.38.1 → **0.38.2** に付け替えて解消した

### [0.38.1] - 2026-09-03

#### Summary

v0.38.0（merge gate）を main へ取り込んだあとに到着した独立レビューを、マージ済み main で実測して確定した欠陥の remediation。運用ロックアウト 1 件、fail-open 2 件、誤 block・性能・テスト環境依存の 4 件を修正する。

#### Fixed

- `hooks/scripts/lib/constants.py` / `skills/gdd-pr-review-followup/SKILL.md`: 人間が明示承認しても `Merge Approval` を記録できず `approval-missing` の恒久 block になっていた欠陥を、**承認の取り方**を変えて解消した。`is_merge_approval()` の入力域を「任意の自由文」から「`PR #<n>` と `head <sha>` を提示した**閉じた確認への短い返答**」に限定し、実装は全文アンカー + 肯定間投詞の任意前置に固定する（`はい、マージしてください` / `OK、マージして` / `LGTM, merge it` を受理）。SKILL.md 側にはマージ直前に閉じた確認を出す手順を明記し、恒久 block の復帰路（確認の出し直し）を導線として持たせた。否定語の列挙は**持たない** —— 前置きを自由にすると極性判定が必要になり regex で閉じないため（実測: `cannot merge it` は `\bnot\b` の境界が成立せず、日本語の条件節 `〜たら` / `〜次第` にも対応が無い一方、`Not bad, merge it` のような正当な承認まで落としていた）。配布物の承認語彙リークテストは緑のまま（実測: 走査対象の全行でリーク 0 件）
- `hooks/scripts/run-merge-gate-hook.sh`: コマンド解析の失敗（python3 不在 / 不正 JSON / import 失敗）で `is_merge` が false のまま残り、承認も証跡も検査されずに**無出力で素通り**していた。解析完走の標識を導入し、解析できなかった場合は新 reason code `parse-error` で fail-closed に倒す。あわせて `block()` から python3 依存を外した（block 自体が同じ依存で沈黙すると fail-closed に倒せない）。kill-switch は従来どおり出口として効く
- `hooks/scripts/lib/detect-steering.sh`: `gdd_extract_doc_field` が fenced code block（``` / ~~~）を追跡していなかったため、`state.md` に書式の記入例を 1 つ置くだけで `Merge Approval` 等の証跡が成立していた。fence 内は現在値ではなく記入例として読み飛ばす
- `hooks/scripts/run-merge-gate-hook.sh`: `merge` の事前判定は payload 全体に掛かるままとした（パスに `merge` を含む worktree では Bash 呼び出しごとに python3 が 1 回起動する。実測 85〜100ms）。**絞り込みは 2 案とも実装したうえで撤回している**: (1) bash で `tool_input.command` の値を切り出す案は値長に対して二乗で効き、200KB の payload で 5.7 秒・400KB で 22 秒（hook の timeout は 10 秒）。timeout で kill されると block を返せず素通りになるため、python3 起動より高くつく。(2) `gh` の共起を要求する案は、解析側が shlex の**クォート除去後**の token を見るため `g\h pr merge 7` / `'g''h' pr merge 7` が payload に literal `gh` を持たず、gate ごと素通りする（実測）。精密判定は step 2 の python 側（`tool_input.command` だけを見る）が担う
- `hooks/scripts/lib/gh_command_parse.py`: `--author-email` の短縮形 `-A` を値を取る flag の集合へ追加（v0.38.0 の未確認事項に follow-up として記録していた 1 件）。`gh pr merge 23 -A 99` が対象 PR を `99` に化けさせ、`-A alice@example.com` が `pr-target-unresolvable` で block されていた
- `hooks/scripts/lib/gh_command_parse.py`: `GH_HOST=github.com`（既定ホストの明示）を repo 決定要因として扱わない。明示しただけで `pr-target-unresolvable` になっていた。`GH_REPO` と既定以外の `GH_HOST` は従来どおり conflict
- `hooks/scripts/run-merge-gate-hook.sh`: owner/repo の照合を大小文字非依存にした（GitHub の実仕様に合わせる）。`-R acme/widgets` と `PR URL` の `Acme/Widgets` が別 repo 扱いになり block されていた

#### Changed

- `hooks/scripts/run-merge-gate-hook.sh` / `hooks/scripts/lib/gh_command_parse.py`: 出荷物から解決できない steering 内の識別子（`ADR-n` / `gate #n` / レビュー回の finding ID）をコメントから除去し、判断理由そのものを残す形へ書き換え。markdown 側は除去済みだった
- `tests/test_merge_gate_hook.py`: hook 実起動 helper が `GH_HOST` / `GH_REPO` を実行環境から継承しないようにした（これらを設定している開発者の手元でだけ verdict が変わる環境依存の失敗）

#### Changed（PR レビュー対応）

- `hooks/scripts/run-merge-gate-hook.sh`: `parse-error` の fail-closed を GDD セッション判定の **後ろ** へ移動。前に置くと、python3 が壊れた環境で `gh` と `merge` を含む無関係なコマンドが gate 管轄外の repo でも block され、逃げ道が kill-switch だけになる
- 大小文字の正規化を `LC_ALL=C tr` へ固定（`[:upper:]`/`[:lower:]` の写像は POSIX 上ロケール依存）。同型を全域 grep し、出荷 script の 7 箇所（pre-push gate 1 / pre-PR gate 4 / suggest-task-size 1 / setup-gdd-loop 1）を一括修正
- fence 追跡を canonical field 読み取りの **5 実装すべて**（`gdd_extract_doc_field` / `validate-steering-write.py` / `gdd_task_binding.py` / `collect-gdd-telemetry.py` / `setup-gdd-loop.sh`）へ拡大。読み手だけを対応させると、書き手バリデータが通した state.md を読み手が別の値で routing する非対称が残る（実測: 同一文書に対して 3 通りの値が返っていた）
- `hooks/scripts/run-merge-gate-hook.sh`: gate 対象判定（PR URL 一致）の比較も大小文字非依存にした。ここを落とすと `gh pr merge https://github.com/Acme/Widgets/pull/7` が gate 対象判定で外れ、`active: false`（merge 時の既定状態）では承認も証跡も見ずに素通りする。実装は `tr` ではなく bash builtin の `shopt -s nocasematch`（`| tr` は `set -euo pipefail` 下で外部コマンドが失敗すると hook ごと即死し、block を返せない = fail-closed の判定本体に block と同じ失敗モードを持ち込む）。merge gate 以外の 7 箇所は `LC_ALL=C tr` のまま
- `hooks/scripts/gdd_stop_hook.py`: `Resume From` の読み取りにも fence 追跡を入れた。ここだけ非対応だと、同じ state.md に対して stop hook だけが記入例を現在値として読み、`human-check-waiting` で誤停止する
- `docs/VERSIONING.md`: 統合先の消費済み版数を v0.37.4 → v0.38.0 へ更新（origin/main が v0.38.0 を出荷済み）

- `hooks/scripts/lib/tasklist_parse.py` ほか 5 実装: fence 判定のインデントに **TAB を含める**。fence 追跡を `tasklist_parse.strip_fenced_blocks` へ集約した際に半角スペースだけへ狭まり、TAB でインデントした fence が認識されず「記入例が証跡になる」欠陥が復活していた（実測: TAB fence に包んだ証跡一式で hook が無出力素通り）
- `hooks/scripts/lib/tasklist_parse.py` / `scripts/setup-gdd-loop.sh`: fence の閉じ忘れ時の救済範囲を「本文を丸ごと残す」から「**未閉鎖の開き fence 以降だけ**を残す」へ。丸ごと残すと、それ以前の正しく閉じた記入例まで復活し、閉じ忘れ 1 つで記入例が全面的に証跡化する。`detect-steering.sh` の awk は既にこの規約で、揃えないと「書き手は通すのに読み手には見えない」非対称が残っていた
- `hooks/scripts/run-merge-gate-hook.sh`: 大小文字非依存の一致判定 `_mg_equals_ci` で `shopt -p nocasematch` の失敗を吸収する。同コマンドは option が未設定のとき exit 1 を返すため、`set -euo pipefail` 下で `if` 条件の外に置いた呼び出しが hook を**無出力 exit 1** で終わらせる（= block を返せず素通り）失敗モードを持っていた
- `hooks/scripts/lib/constants.py`: 承認返答に許す句読点の定義を 1 定数（`_MERGE_APPROVAL_PUNCTUATION`）に集約。肯定間投詞の後ろと承認語彙の後ろで別々に列挙していたため片方にだけ `。` が無く、`はい、マージしてください` は通るのに `はい。マージしてください` が落ちていた
- `scripts/lint-pr-review-followup-state.py` ほか 4 ファイル: `hooks/scripts` を `sys.path` に載せて `from lib.X import` する形を撤去し、`hooks/scripts/lib` を top-level module として読んで直後に path を戻す形へ統一。前者は `sys.modules["lib"]` を hooks 側に固定し、同一プロセスの `scripts/lib`（`lint_base` 等）を解決不能にする（実測: ModuleNotFoundError）

#### Added

- `tests/test_fence_policy_single_source_contract.py`: fence 規約を「手で列挙した形の表」ではなく**生成した文書**で固定する契約テスト。fence の構成要素（記号種別 × 長さ × インデント × info string × 閉じる / 閉じない）から文書を組み立て、組み立て側が「payload を閉じた fence に入れたか」を構成として持つので、実装を参照しない独立した正解になる（実装間の差分テストと違い、全実装が揃って間違っている場合も落ちる）。あわせて、可視性の決定を `strip_fenced_blocks` 1 箇所に限る許可制テストを持つ。**導入理由**: 本 PR の回帰はすべて「誰も列挙していない形」で起きた（fence のインデントを半角スペースへ狭めた / 閉じ忘れ救済を広げた / awk の backtick-in-info 規約を落とした / 可視性の再導出が 2 箇所目に増えた）。既存の契約表は 5 実装を拘束していたが表に無い形は検査されず、形を足し続ける限りこの失敗モードは消えない。実測: 上記 5 件の退行を注入すると、この 1 ファイル（約 3 秒）がすべて検出する

#### User Action Required

- **マージ承認の取り方が変わる**。`gh pr merge` の直前に、AI が `PR #<n>` と `head <sha>` を提示して可否を問う 1 問（受理される返答形を添えた閉じた確認）を出すようになる。自由文の作業指示（`独立セルフレビューしてマージして` 等）は承認として記録されない —— 承認は特定の head sha に紐づく必要があり、指示の時点では sha が確定していないため。判定できない返答は恒久 block にはならず、確認の出し直しで進む
- 証跡の書式・既定値・gate 対象の面はいずれも変更していない
- `state.md` に証跡の記入例を fenced code block で書いていた場合、その行は今後 canonical field として読まれない（意図した現在値は fence の外に置く）

#### Validation / Eval Impact

- 新規 `tests/test_merge_gate_followup_findings.py`: 上記各件に 1:1 対応する回帰テスト（閉じた確認の手順が出荷物に在ることの契約テスト、TAB fence を包んだ証跡で hook が block することの実起動テスト、`_mg_equals_ci` を `set -euo pipefail` 下で素の statement として呼ぶテストを含む）（承認発話の肯定 / 否定、解析失敗の fail-closed、fence 追跡、事前判定の範囲、`-A` / 既定ホスト / 大小文字、steering 識別子の走査）に加え、鮮度 10 分・待機 40 分の境界を hook 実起動で踏むテスト
- `tests/test_hook_block_reason_recovery_contract.py` / `tests/test_merge_gate_hook.py`: reason code `parse-error` を gate 故障 family（kill-switch を出口として案内する family）へ登録し、到達可能な fixture を追加
- パーサの回帰は 42 形（`bash -c` / `eval` / heredoc / リダイレクト / 複数 merge / repo 決定要因 / 各 flag）を実測して差分 0 件を確認
- 全体回帰: 1621 passed / 1 skipped / 11491 subtests（変更前 1556 passed / 1 skipped）、`tests/validate-plugin.sh` exit 0
- budget: references 行数 11922/11922・total skill body 行数 6982/6982（いずれも変更なし。本 PR は hooks / scripts / tests のみ）
- hook の所要時間は payload 長に依存しない（実測: 14KB〜400KB で 0.02〜0.16 秒。hook の timeout は 10 秒）
- 独立レビュー（実装文脈を渡さない diff-only）を 5 巡実施。high 6 / medium 15 をいずれも remediation し、各指摘に変異注入で検出可能なテストを追加した。4 巡目以降は「前の修正が生んだ退行」（fence インデントの狭まり、閉じ忘れ救済の広がり、空洞化した契約テスト）が主で、修正ごとに変異注入で判別力を実測している

#### 未確認事項（判断に使った情報の限界）

- **本リリースで意図的に未修正（follow-up）**: merge gate の所要時間は `.steering/` のディレクトリ数に比例して増える（実測: 10 件で 0.92 秒、240 件で 9.11 秒、300 件で 11.26 秒。hook の timeout は 10 秒）。timeout 超過は無出力 = 素通りになる。原因は `gdd_pre_push_resolve_steering` と `_mg_match_steering_by_target` が全 `state.md` を個別に開くことで、これは v0.38.0 から変わっておらず本 PR では触っていない。修正には走査対象の絞り込み（候補上限・一括読み取り）という設計判断が要るため別 PR へ回す。通常運用（steering 数十件）では 1〜3 秒台で、`scripts/find-stale-steerings.sh` による棚卸しが緩和策になる

### [0.38.0] - 2026-09-02

#### Summary

PR-W8 / W-17: マージゲートの機械化。`gh pr merge` を `PreToolUse`/`Bash` hook で検査し、直前 re-fetch 証跡・40 分待機/独立レビュー代替・`Merge Approval` 明示フィールド（存在 / PR 番号・head SHA 一致 / 鮮度 120 分）の 3 条件を実行時に強制する。

#### Added

- `hooks/scripts/run-merge-gate-hook.sh`: `gh pr merge` を検査する gate hook（3 本目の gate hook、`PreToolUse`/`Bash` matcher の 4 entry 目）
- `hooks/scripts/lib/merge-gate-evidence.sh` / `hooks/scripts/lib/gh_command_parse.py`: 証跡パーサ・コマンド解析
- `hooks/scripts/lib/constants.py`: `MERGE_APPROVAL_RE` / `is_merge_approval()` / `MERGE_GATE_REVIEW_WAIT_MINUTES=40` / `MERGE_GATE_RECHECK_FRESHNESS_MINUTES=10` / `MERGE_GATE_APPROVAL_FRESHNESS_MINUTES=120`
- `tests/test_merge_gate_hook.py` / `tests/test_merge_approval_vocabulary_leak.py`: 契約テスト（md↔code 同期テスト・kill-switch 順序 pin テスト・parse チャネルの injection 耐性テストを含む）

#### Changed

- `references/self-review-lanes.md` / `references/config-defaults.md` / `references/state-field-tiers.md`: merge gate 証跡 6 種（`Merge Approval` を含む）の書式・既定値・Tier 3 登録
- `references/post-completion-pr-flow.md`: マージ後着弾レビューの定型手順 + 重複削除
- `skills/gdd-pr-review-followup/SKILL.md`: `PR URL` の `state.md` 記録を必須化、severity 既定の接続、`ScheduleWakeup` 再武装導線
- `skills/gdd-pr-review/SKILL.md`: PR Body 4 チェックを参照 1 行へ集約
- `tests/_block_reason_support.py`: `RECOVERY_ELEMENTS` を shell 定数名からの literal 抽出方式へ移行（既存 2 hook にも適用）

#### Breaking Contract Changes

- `gh pr merge` は active GDD セッションか対象 PR がローカル steering の `PR URL` と一致する場合、re-fetch 証跡・待機/独立レビュー・`Merge Approval` のいずれかが欠けると block される。steering が解決できるのに `PR URL` が**未記録**の場合も判定材料の欠落として block する（reason code: `pr-url-unrecorded`）。正当なマージ運用は証跡を記録すれば従来どおり通り、stale な `.steering/` が残る repo での誤爆は kill-switch で逃がす。**gate 対象の面は 3 点広い**: (1) `gh pr merge <branch>`（ブランチ名を位置引数に取る一級の呼び出し形）も gate 対象で、URL か `-R owner/repo <番号>` で対象を明示しない限り `pr-target-unresolvable` で block する (2) done / blocked の steering が **2 件以上**ある repo で、対象 PR を `PR URL` に記録した steering を一意に選べない場合は block する（reason code: `steering-ambiguous`。対象 PR を URL / 番号で明示するか、完了済み steering を 1 件に整理するか kill-switch。対象 PR がどの steering とも無関係で `active: true` でもなければ、gate 対象外として従来どおり素通りする。ただしこの素通りは **候補 steering がすべて `PR URL` を記録済み**のときだけで、候補のどれか 1 件でも `PR URL` を記録していなければ「対象 PR と無関係」ではなく「判定不能」として `pr-url-unrecorded` で block する。単一 steering 経路と同じ扱いで、steering 件数によって fail-closed が反転しない） (3) `bash -c 'gh pr merge ...'` / `eval 'gh pr merge ...'` も検出する（入れ子 3 段まで。`git commit -m "gh pr merge ..."` のような散文引数は従来どおり検出しない） (4) `bash <<EOF ... gh pr merge ... EOF` / `bash -s <<EOF ...` のように **shell interpreter へ食わせる heredoc の本文**も検出する（heredoc は「データを渡す形」であると同時に「コマンドを実行する形」でもあるため）。`git commit -F - <<MSG ... MSG` / `cat <<EOF > file` のようにデータとして渡す heredoc の本文は従来どおり検出しない。逆に、リダイレクト付きの `gh pr merge 7 2>&1` / `... </dev/null` は位置引数の誤読による誤 block をしなくなった。**リダイレクトは位置引数の前後どちらに来ても読み飛ばして走査を続ける**ため `gh pr merge </dev/null <branch>` / `gh pr merge 2>&1 999` も対象 PR を正しく読む。`gh pr merge 7 && gh pr merge 999` のように 1 行へ merge を 2 本以上並べた形は、対象を一意に決められないため `pr-target-unresolvable` で block する（1 コマンド 1 マージへ分ける）

#### User Action Required

- `gh pr merge` を使う active GDD セッションでは、マージ前に `Merge Approval` 等の証跡を `state.md` に記録すること（書式は `references/self-review-lanes.md`）
- 誤検知時の逃げ道は kill-switch のみ（`~/.claude/gdd-hooks-disabled`）。使用は `merge-gate-suppressed.log` に記録される

#### Validation / Eval Impact

- `tests/validate-plugin.sh` に `run-merge-gate-hook.sh` の kill-switch drift 検査・hooks.json wiring 検査・block reason recovery 検査が追加される
- budget: references 行数 11922/11922・total skill body 行数 6982/6982（いずれも headroom 0 で上限不変）
- 統合先の消費済み版数を v0.37.3 → v0.37.4 へ更新（origin/main の W-27 / remediation_loop マージを取り込んだ upstream drift 反映）

#### 未確認事項（判断に使った情報の限界）

- **本リリースで意図的に未修正（follow-up）**: `gh pr merge -R` 省略かつ `git remote get-url origin` が空 / GitHub URL として分解できない構成では、`run-merge-gate-hook.sh` の owner/repo 照合（対象 PR の 3 組解決の (d)）が skip され PR 番号一致だけで通る。到達条件は「origin から owner/repo を導出できないが `gh` は別経路で PR を解決できる」構成に限られ、番号一致・head SHA 一致・承認鮮度の他条件は従来どおり強制される。修正には「origin 不在時に fail-open を維持するか `pr-target-unresolvable` へ倒すか」の設計判断が要り、後者は origin なしの fork 運用を新たに block しうるため、design 改訂と human check を伴う別 PR へ回す。**あわせて gate 旧#16 の検出範囲の限界と low 2 件**: 本文が実行される形の判別は heredoc の introducer 行のうち **その heredoc を所有する pipeline**（`;` `&&` `||` `&` で区切った区間。クォートの内側で開く heredoc はその中身だけ）に `bash` / `sh` / `zsh` / `dash` / `ksh` が現れるかだけで行う。`python3 - <<EOF` のように **shell 以外の interpreter** へ食わせて中から `gh pr merge` を起動する形、`ssh host bash <<EOF` のようにリモートで実行する形、`bash \` + 改行 + `<<EOF` / `cat <<EOF \` + 改行 + `| bash` のように **行継続で introducer が次行へ折り返す**形は検出しない（前 2 者は本文が shell コマンド列とは限らない / 別ホストの gh 認証に依存してローカル steering で判定材料が揃わない。行継続は「1 行 = 1 introducer」の前提を崩すが、通常操作では現れない）。判別を本文の内容にまで広げると、データとして渡す散文に interpreter 名が出てくるだけで実行形へ化けるため、introducer 行だけを見る側に倒している。あわせて severity=low の 2 件を follow-up に回した: (1) `--author-email` の短縮形 `-A` が値を取る flag の集合に無く、`gh pr merge 23 -A 99` は `99` が対象 PR を上書きし `-A alice@example.com` は `pr-target-unresolvable` で block される（fail-closed 側） (2) `echo gh pr merge 23` / `gh pr merge --help` は全 token 走査で `gh` を拾うため過検出 block になる（既存挙動、逃げ道は kill-switch）
