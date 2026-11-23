# Changelog Archive 2

`gate-driven-development` の変更履歴のうち、`### [0.15.0]` 〜 `v0.1.3` をここへ移した。
記載ルール・Entry Template・Versioning Notes の正本は [`CHANGELOG.md`](CHANGELOG.md)。
本文は移動時に変更していない。

### [0.15.0] - 2026-07-27

#### Summary

コンパクション後に作業内容が失われる問題と、`state.md` の schema 逸脱を軽減する。実運用の `.steering/*/state.md` 77 件を調査したところ、canonical Tier 1 field が 3 つとも揃っていたのは 9 件 (12%)、`Last Handoff Summary` が書かれていたのは 1 件 (1.3%)、`.steering/.../adr.md` は 0 件だった。

#### Added

- `validate-steering-write.py` に Tier 1 (Core) field の充足検査（`collect_state_core_field_violations`）を追加。従来 write 側には充足検査が無く、`STATE_REQUIRED_FIELDS` は `Started At` の transitive 判定にしか使われていなかった。read 側（`detect-steering.sh:gdd_validate_active_state_fields`）は 3 field 全部を要求して fail-closed するため、書き込み側無検査・読み取り側厳格という非対称が充足率 12% の原因だった。判定は「既存ファイル内容 + 書き込み chunk」に対して行う（chunk だけでは Edit で 1 field ずつ更新する運用で永久に検査されないため）
- compact 自動復帰プロンプトに context source field（`Approved Direction` / `Last Handoff Summary`）を注入。従来は Task / Phase / Next Action の 3 行のみで、「何を作っていたか」が復元されなかった
- plan-reread hook（PreToolUse）が `Last Handoff Summary` の未記入を検出したとき、注入 context に記入を促す 1 行を追加。新しい hook は追加していない
- `post-completion-learning.md` 手順 1 に、`adr.md` が**無い場合**に重要な意思決定を残す導線を追加。`self-contained-contract.md` の optional / fail-closed しない条項は変更していない

#### Changed

- `GDD_MAX_AUTO_CYCLES` のデフォルトを 10 → 30 に緩和。実タスクで上限到達例があり、到達後は context なしの再開になっていた。無限復帰ループ防止という上限の趣旨は維持し、環境変数で従来値に戻せる
- compact 復帰プロンプトの Task 名は `Task ID` field を優先するようにした（従来は field 名の前方一致で `Task ID:` を拾えず、steering ディレクトリ名に fallback していた）
- `phase-gate-prechecks.md` の Common Pre-check を 2 step → 3 step に変更し、phase を抜けるときの `Last Handoff Summary` 更新を追加（Tier 3 のため不在では fail-closed しない）
- 同 reference を読む skill は従来 build 系 5 件のみだったため、`gdd-requirements-gating` / `gdd-design-gating` にも pointer を追加。**`gdd-brainstorming` は body budget 超過（352/350・allowlist 対象で削減方向のみ）のため未対応**。`state-field-tiers.md` が定義する「phase 遷移ごとに上書き」に対し、brainstorming phase だけ導線が無い状態が残る
- 上記 pointer 追加に伴い、express runtime profile のトークン上限を 33450 → 33500、standard runtime profile を 57400 → 57450 に引き上げ（実測 33464 / 57438）。行数は増やさず既存行への追記に留めている
- `docs/VERSIONING.md` の現行バージョン表記を v0.15.0 に更新

#### Fixed

- `state-field-tiers.md` の Tier 1 表が write 側の検査箇所を `validate-steering-write.py:96` と記載していたが、96 行目は無関係な正規表現定義であり、検査内容の記述自体が事実と異なっていた。行番号はドリフトするため関数名表記に統一
- `post-completion-pr-flow.md` が `post-completion-learning.md` を「7 steps」と参照していたが実際の手順は 8 項目だった。再ドリフトを避けるため件数を書かず `§ 手順` 参照に変更。あわせて plugin 全体を走査し、`ファイル名:行番号` 形式の参照と件数を主張する参照が他に残っていないことを確認済み

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-tool-use-plan-reread-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/phase-gate-prechecks.md`
- `plugins/gate-driven-development/references/post-completion-learning.md`
- `plugins/gate-driven-development/tests/test_session_start_hook_compact_resume.py`
- `plugins/gate-driven-development/tests/test_state_core_fields_contract.py`（新規）
- `plugins/gate-driven-development/tests/test_last_handoff_summary_contract.py`（新規）
- `plugins/gate-driven-development/tests/test_adr_guidance_contract.py`（新規）

#### User Action Required

- `state.md` を書く際、Tier 1 field（`Resume From` / `Human Check Status` / `Route In Progress`）が揃っていないと write hook が deny する。既存の完了済み steering は write が発生しないため影響を受けない。誤爆時は既存の escape hatch（同一 (path, category) で 3 回連続 deny すると warning 付き allow に降格）が働く
- 従来のサイクル上限に戻したい場合は `GDD_MAX_AUTO_CYCLES=10` を設定する

#### Validation / Eval Impact

- `python3 -m pytest tests/ -q` green（718 passed, 1 skipped, 455 subtests / 変更前 710 passed に対し新規 8 件追加）
- `gdd-completion-check/SKILL.md` の body は 347/350 行のまま（導線は reference 側に配置し、body を増やしていない）

### [0.14.2] - 2026-07-26

#### Fixed

- `gdd-using-git-worktrees` の Post-Merge Cleanup / Cleanup Ownership Boundary / 全体 Guardrails に、`--force` 付き `git worktree remove` の前に対象 worktree 内の全 `.steering/*/state.md` の `Resume From` が terminal（`done` / `cancelled`）であることを確認するガードを追加。1 件でも進行中（design-gating の human check 待ちなど）なら safe cleanup ready と判定せず、cleanup 対象から除外する
- 背景: 2026-07-26、別セッションの merged-worktree cleanup が design-gating 実行中（human check 未完了）の worktree を `git worktree remove --force` → `git branch -d` で誤削除し、未コミットの `.steering/<slug>/`（requirements.md / design.md / adr.md / worklog.md）を喪失する事故が発生した。transcript からの復元で実害は限定的だったが、cleanup 側に「進行中タスクを対象外にする」機械的な判定基準がなかったことが根本原因

#### Changed

- express runtime profile のトークン上限を 33400 → 33450、standard runtime profile のトークン上限を 57350 → 57400 に引き上げ（`gdd-using-git-worktrees` のガード追加分。`skills/gdd-using-git-worktrees/SKILL.md` の body line 数は 340 → 343 行で budget 350 内）

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-using-git-worktrees/SKILL.md`
- `plugins/gate-driven-development/tests/test_post_merge_local_cleanup_contract.py`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`
- `plugins/gate-driven-development/tests/checks/lint-scripts-functional.sh`
- `plugins/gate-driven-development/tests/test_p0_meta_feedback_contract.py`

#### User Action Required

- なし。既存の cleanup 導線に判定基準が追加されるのみ。進行中 steering を含む worktree は、以後 `--force` 削除ではなく人間への報告に倒れる

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q` green（`test_worktree_skill_guards_force_removal_against_active_steering` を新規追加）
- `bash tests/validate-plugin.sh` の `skill-body-budget` は 343/350 行で budget 内

### [0.14.1] - 2026-07-26

#### Added

- `gdd-requirements-gating` skill の Additional Review Concerns に「Non-Functional Requirements Check」を追加。非機能要求グレード（IPA）の6大項目（可用性 / 性能・拡張性 / 運用・保守性 / 移行性 / セキュリティ / システム環境）を検討観点のフレームワークとして要件特性ごとに検討する。特に可用性（耐障害性・回復性）/運用・保守性（障害時運用）は視点名だけでは見落としやすいため、べき等性・リトライ発火まで具体的に確認する旨を明記し、AC 化すべきなのに漏れていれば Medium finding として報告する
- 残り4視点（性能・拡張性 / 移行性 / セキュリティ / システム環境）は視点名だけでは判定の粒度が粗いため、`references/nfr-viewpoints.md` に該当要件特性ごとの観点集（検討を促す問いの形式。固定チェックリストではない）を新設。`skills/gdd-requirements-gating/SKILL.md` から該当要件特性がある場合のみ参照する inline pointer を追加し、非該当要件には finding を出さない
- `evals/gdd-scenario-fixtures.json` に Non-Functional Requirements Check の検出精度を確認するシナリオを2件追加（べき等性・リトライ発火のAC欠落検出、性能・拡張性観点のAC欠落検出）

#### Changed

- express runtime profile のトークン上限を 33300 → 33400、standard runtime profile のトークン上限を 57300 → 57350 に引き上げ（Non-Functional Requirements Check の観点追加分。前回 0.13.1 相当の 33300 → 33330 の調整を含む）

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-requirements-gating/SKILL.md`
- `plugins/gate-driven-development/references/nfr-viewpoints.md`（新規）
- `plugins/gate-driven-development/evals/gdd-scenario-fixtures.json`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`
- `plugins/gate-driven-development/tests/checks/lint-scripts-functional.sh`
- `plugins/gate-driven-development/tests/test_p0_meta_feedback_contract.py`

#### User Action Required

- なし。requirements-gating の既存 reviewer 挙動に確認観点が追加されるのみ

#### Validation / Eval Impact

- `tests/validate-plugin.sh` green（skill-body-budget 含む全 block）
- `pytest tests/test_p0_meta_feedback_contract.py` green

### [0.14.0] - 2026-07-24

#### Changed

- F-2: express の impl-gate を advisory 化。`gdd-implementation-reviewer` の inline checklist を 1 回のみ実行し、High + ops-blocking medium 以外の medium / low は remediation ループに入れず advisory 記録（PR 本文 `## Advisory Findings` に全件列挙）とする。fail-closed 集合（High + ops-blocking medium）は非退行。standard / quick (standard) の挙動は変更なし。
### [0.13.0] - 2026-07-23

#### Changed

- `root-cause-investigation` の Architecture Check 発火条件に、in-session の fix 失敗回数（既存: 3 回）に加え「過去 6 か月で同一 symbol の出現回数が変化した（pickaxe 検索）fix / 修正相当の commit が 3 件以上」という session をまたぐ履歴パターン条件を追加。in-session 失敗回数が 0 でも履歴パターン単独で発火する。Phase 1 step 3（直近の変更確認）に `git log --since="6 months ago" -S"<symbol>" --oneline`（`<symbol>` はプレースホルダ。クォート必須）の実行を追記し、発火判定の材料を毎回集める
- Architecture Check 発火時の出力契約に「深掘り調査・リファクタ計画の作成はこの skill の責務外」を明記。発火条件と該当 commit を Phase 4 出力（または `No Root Cause Decision`）に記録したうえで、必要なら別途 dedicated な調査（人間主導、または別 agent への委任）を推奨する 1 行に留め、この skill 自身は実行しない
- skill body budget（baseline 650 行）を維持するため、「`root-cause-investigation` vs `superpowers:systematic-debugging`」比較表を `./references/superpowers-relationship.md` へ分離し、本文には参照ポインタのみ残す

#### Fixed

- **E-9**: Stop hook がバックグラウンド dispatch した Agent の完了待ちを継続ブロックし続ける問題を解消（3 独立バグ）:
  1. in-flight 誤判定 — バックグラウンド Agent の起動応答 tool_result を「完了」と誤認識していたのを、tool-use-id 直接一致（高速経路）+ agentId↔task-id 照合（フォールバック）のハイブリッド方式で区別するように修正（`lib/transcript.py`）
  2. 停止契約の矛盾 — continuation メッセージの指示（次にすることを明記）と done guard の要求（👤 ブロック必須）が食い違い、指示どおりに停止しても再ブロックされていたのを、共有定数 `NEXT_ACTION_HEADING`（`lib/next_action_check.py`）で両者を同期
  3. ceiling 空振り — 連続ブロック上限のリセットが task-notification 到着のたびに起きてしまい上限が機能しなかったのを、`GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS`（時間窓）ベースのリセット条件に変更（`gdd_stop_hook.py`）
- （scope amendment）`scripts/lint-ac.py`: AC ID 正規表現の 2 バグを修正（複合ハイフン形式の AC ID 非対応、閉じ `**` 非対応）。E-9 の AC 検証 gate を機能させるために必要だった付随修正

#### Affected Files

- `plugins/gate-driven-development/skills/root-cause-investigation/SKILL.md`
- `plugins/gate-driven-development/skills/root-cause-investigation/references/superpowers-relationship.md`（新規）
- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/lib/next_action_check.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/scripts/lint-ac.py`
- `plugins/gate-driven-development/tests/test_stop_hook_e2e.py` / `test_stop_hook_unit.py` / `test_stop_hook_validate.py`

#### User Action Required

- root-cause-investigation 側: なし。既存の in-session 3 回失敗トリガー・4 Phases・Iron Law の挙動は無改変。Architecture Check がこれまでより早い段階（履歴パターン一致時点）で発火するようになる点のみ既存利用者は認識しておく
- E-9 側: なし。同期 subagent の in-flight 抑止・既存の停止経路（kill switch・E-8 実装分）は非退行。バックグラウンド Agent を使うタスクで継続ブロックの発火頻度が下がることを確認する（dogfood 観察事項）

#### Validation / Eval Impact

- `tests/validate-plugin.sh` green（skill-body-budget 含む全 block）。root-cause-investigation の body line 数は 650 → 643（baseline 内）
- E-9: `pytest plugins/gate-driven-development/tests/ -q` 697 passed / 451 subtests passed, exit 0。`tests/validate-plugin.sh` exit 0

### [0.12.1] - 2026-07-18

#### Added

- `gdd-pr-review-followup` skill の Repeat ステップ（PR Review Follow-up Loop）に、レビュー待ちポーリングの軽量化指針 2 点を追記（E-2 縮小版）: (1) 確認間隔はレビュー所要（実測 5〜10 分）に合わせ 5〜10 分に 1 回、(2) 待機中は最小フィールドのみ取得（フル diff/コメント全文の再取得はしない）。ただし完了判定・対応要否の判断時は既存の fresh verification evidence 契約に従い全量取得する。memory `feedback_token_efficient_polling` の定着で、レビュー待ちの `gh` 反復クエリによるトークン浪費を軽減する
- doc-check `pr-review-followup-polling-tokens`（section-scope）を追加。`## PR Review Follow-up Loop` セクション内に literal token `5〜10 分` / `最小フィールド` / `全量を取得` の 3 種が存在することを機械検証する

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/tests/checks/pr-review-followup-polling-tokens.sh`（新規）
- `plugins/gate-driven-development/tests/checks/manifest.tsv`

#### User Action Required

- なし。skill 文面（プロンプト規約）の追記のみで、既存の poll 上限（12 回）・Escape Hatch・fresh verification evidence 契約・Collect / Push / Re-request の挙動は無改変

#### Validation / Eval Impact

- `tests/validate-plugin.sh` green（新 doc-check 含む）。gh 呼び出し回数を計測・強制停止する hook 機構は作らない（YAGNI）。実行時の間隔遵守そのものは eval ループの責務

### [0.12.0] - 2026-07-18

#### Changed

- Stop hook 自動継続（`decision: block`）の `reason` を、state 本文の全文再生からコンパクトな継続指示（継続指示 + terminal マーカー一覧 + `.claude/gdd-dev.local.md` 本文へのポインタ、3 行程度）に変更。従来は継続のたびに約 60 行の bootstrap 定型文がユーザー表示とモデル文脈の両方に再注入されていた（実測: session 02b73028 で 184 回 = 約 11,000 行の重複注入）。bootstrap 契約の正本は従来どおり `setup-gdd-loop.sh` が書く state 本文にあり、初回起動時の表示は変更なし

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`

#### User Action Required

- なし。自動継続時の表示が短くなるのみで、停止判定・iteration 管理・systemMessage は変更なし

#### Validation / Eval Impact

- `tests/test_stop_hook_e2e.py`（継続 block の reason 契約を更新 + 本文非再生テストを新規追加）、全テスト 675 passed、`scripts/validate-plugin-layout.py` green

#### Changed (R9-2、v0.11.0 リリース後に main へマージ済みの分)

- R9-2 Wave 0: 実行時 Read ゼロの references 6 ファイル（ac-machine-readable-schema / autonomous-model-workers / benchmark-scenarios / hitl-offline-judge / infra-accretion-prevention-decision / worked-examples）を `docs/references-archive/` へ移動（設計時参照化）。根拠は 2026-07-16 の transcript 839 セッション実測（追加後 1 ヶ月以上・実行時 Read 0・hook/スクリプト消費 0）。引用パスと契約テストを追随更新
- R9-2 pilot: `references/brainstorming-steps.md` を 4 値ルーブリック（keep / rewrite-to-intent / delete / relocate）で蒸留（517 → 139 行、-73%）。Step 番号・§ アンカー・契約テスト固定文字列・成果物フォーマット・main 側の直近契約（F-3 段階的対話 / 罠7 実測義務 / design.md skeleton の Decision Packet 粒度）は維持。原本は `docs/references-archive/brainstorming-steps-pre-r9-2-original.md` に退避。監査シート: docs/audits/r9-2-brainstorming-steps-audit-20260716.md
- R9-2 実測メモ: gate-checklists / uat-checklist / parallel-failure-investigation / workflow-incident-review も実行時 Read 0 だが、skill から実行指示があるため残置（「参照指示が実行時に無視されている」証拠として Wave 1 のインライン化候補）

### [0.12.0] - 2026-07-18

#### Added

- active `/gdd-dev` session 中の host-native `EnterWorktree` tool 呼び出しを block する新規 PreToolUse hook（`run-block-enter-worktree-hook.sh`）を追加。worktree 作成経路を GDD 管理（`gdd-using-git-worktrees` skill）に一本化する（P0-3）。kill-switch → state file 存在 → `active: true` → session 一致 の4ゲートすべて通過したときだけ block し、それ以外は fail-open。

#### Changed

- `references/workspace-policy.md` §系統の注記に、hook による block 挙動と Cursor（`EnterWorktree` tool 非対応）での扱いを明記。
- `skills/gdd-using-git-worktrees/SKILL.md` § Worktree Pollution Guard に、`worktree_base_kind = host-managed` 検出時の注記（hook 導入前作成 or hook 対象外環境の可能性）を追加。
- kill-switch 回帰テスト（`tests/test_hooks_kill_switch.py`）の対象を新規 hook を含む12本に拡張。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-block-enter-worktree-hook.sh`
- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/tests/test_block_enter_worktree_hook.py`
- `plugins/gate-driven-development/tests/test_hooks_kill_switch.py`
- `plugins/gate-driven-development/references/workspace-policy.md`
- `plugins/gate-driven-development/skills/gdd-using-git-worktrees/SKILL.md`
- `plugins/gate-driven-development/.claude-plugin/plugin.json`
- `plugins/gate-driven-development/.codex-plugin/plugin.json`
- `plugins/gate-driven-development/.cursor-plugin/plugin.json`
- `plugins/gate-driven-development/docs/VERSIONING.md`

#### User Action Required

- 既存の worktree 作成フローに変更はなく、active `/gdd-dev` session 中の `EnterWorktree` 直接呼び出しのみ block 対象になる。
- **post-merge 確認（本 PR の検証範囲外）**: 本 hook の実 harness 上での matcher 発火（AC-8）は、開発時に使用した main session が本プラグインの別インストール系統をロードしていたため、この PR の中では確認できていない（`pytest tests/test_block_enter_worktree_hook.py`・`hooks.json` wiring の静的確認による proxy coverage のみ）。マージ後、本プラグインがロードされた session（root が対象リポジトリ）で以下を 1 回実施し、block が実際に発火することを確認してほしい: `.claude/gdd-dev.local.md` を `active: true` + 該当 session_id で用意 → `EnterWorktree` を 1 回呼び出す → block reason に `workspace-policy` を含む文言が出ることを確認する。発火しない場合は、hooks.json の matcher 文字列 `"EnterWorktree"` が実際の tool 名と厳密一致していない可能性がある（リスクは低いと見積もっている。理由: harness の deferred-tool registry 上でも tool 名は prefix なしの平文 `EnterWorktree` として扱われている）。発火しなければ追加 issue 化する。

#### Validation / Eval Impact

- `tests/test_block_enter_worktree_hook.py`（6 passed: block/allow 5ケース + hooks.json wiring 確認）、`tests/test_hooks_kill_switch.py`（24 passed）、`tests/validate-plugin.sh` green 確認予定。

### [0.11.0] - 2026-07-17

#### Fixed

- `.claude/gdd-dev.local.md` の `parse_state`/`write_state` 往復が非冪等で、Stop hook 発火のたびに body の先頭改行が蓄積するバグを修正（`lib/state_io.py::parse_state` に `lstrip("\n")` を追加）。
- 壊れた `.claude/gdd-dev.local.md`（frontmatter パース失敗）が Stop hook をブロックしていた fail-closed 挙動を fail-open に変更（`gdd_stop_hook.py` L1017-1019 のみ。`.steering/state.md` 側の fail-closed 契約と `iteration` 破損チェックは変更なし）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/state_io.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`

#### User Action Required

- なし。既存の `.local.md` は次回の Stop hook 発火時に自動的に正規化される。

#### Validation / Eval Impact

- `tests/test_stop_hook_unit.py`（往復冪等テスト2件 + fail-open テスト2件を追加）、`tests/test_stop_hook_e2e.py`（iteration fail-closed 非退行を確認済み）、`tests/validate-plugin.sh`（green）。

### [0.10.1] - 2026-07-16

#### Fixed

- `scripts/setup-gdd-loop.sh` のセッションロック判定が `gdd-dev.local.md` の `active:` フラグを見ておらず、`active: false` に手動 disable した stale state file でも `session_id` 不一致だけで「gdd loop is already active in another session.」を誤ってブロックしていた不具合を修正。`active: true` かつ `session_id` 不一致のときのみブロックするよう変更
- `active:` の値判定を `gdd-active-check.sh` と同様に大文字小文字を無視するよう修正（`active: True` 等の表記揺れでもブロックされるように）
- state file の frontmatter パースが `---` 区切り必須になっており、`gdd-dev.md` のフォールバック手順（区切りなし）で作成した state file や行末コメント付きの値を検知できなかった問題を修正。区切りの有無に関わらず全行を走査し、行末コメント（`#` 以降）を無視するよう変更
- state file 全体を走査する際、本文中に `active:` / `session_id:` と同名のキーが再度出現すると frontmatter の値を上書きしてしまう問題を修正。各キーは最初に出現した値を採用し、以降は上書きしないよう変更

#### Validation / Eval Impact

- `tests/test_setup_gdd_loop_session_lock.py` を新規追加（active:true+不一致でブロック / active:false+不一致で非ブロック / state file 無しで非ブロック / active:true+同一session で非ブロック / active 表記揺れ（大文字小文字）でもブロック / `---` 区切りなしの state file でもブロック / 行末コメント付きでもブロック / 本文中の重複キーで frontmatter が上書きされないこと の8ケース）
- `tests/validate-plugin.sh` green 確認済み

### [0.10.0] - 2026-07-16

#### Changed

- reviewer 4 体（gdd-planning-reviewer / gdd-implementation-reviewer / gdd-security-reviewer / gdd-completion-reviewer）と gdd-code-simplifier の agent frontmatter に `effort` を明示配線した（reviewer: high、code-simplifier: medium）。`gdd-model-routing` 宣言と実装の齟齬を解消
- `scripts/resolve-gdd-model.py` の Claude Code 向けモデルピン表記をリテラルバージョン文字列 `"opus-4.8"` から alias `"opus"` に統一（`formal_gate` / `general_heavy` / `general_heavy_risk`）

#### User Action Required

- resolver の返値文字列に完全一致比較で依存する外部ツールがあれば `"opus-4.8"` → `"opus"` への追従が必要

#### Validation / Eval Impact

- `tests/checks/agent-effort-schema.sh` を新規追加し `tests/checks/manifest.tsv` に登録（reviewer 4 体 = effort:high / code-simplifier = effort:medium の pin を検証）
- `tests/test_model_routing_contract.py` / `tests/checks/hooks.sh` / `scripts/benchmark-model-routing.py` の期待値を `"opus"` に同期
- AC-E7-1（dogfood 挙動確認）は本リリースでは未実施。PR マージ後、正式インストール済みプラグインを使った別セッションで確認する

### [0.9.0] - 2026-07-12

#### Fixed

- **PR-0b: R8-A 契約食い違い・参照切れの解消（A-4/A-5/A-6/A-7/A-8）**:
  - Summary:
    1. 「safe cleanup ready」条件の正本を `gdd-using-git-worktrees` SKILL に一本化し、`commands/gdd-dev.md` / `references/phase-progression.md` は参照のみに変更（A-4）
    2. root-cause-investigation から参照されていた不存在スクリプト（`scripts/find-polluter.sh` / `scripts/verify-env-propagation.sh`）を手動手順記述に置き換え、`tests/checks/broken-reference-lint.sh` を新設して `validate-plugin.sh` に追加（A-5）
    3. `references/state-machine.md` の stop-worthy phantom state（`impl-review-waiting` / `completion-check-waiting` の「等」）を閉集合化（A-6）
    4. `run-pre-compact-hook.sh` の sed 置換が対象行なしで無音成功していた silent no-op を修正し、対象行が無ければ追記・置換 0 件は stderr 報告するよう変更（A-7）
    5. `run-pre-pr-gate-hook.sh` の ADR not-applicable 免除判定を `task_size`+`reason` 連結への部分一致から `Task Size:` フィールド完全一致に変更し、reason の case-insensitive 判定漏れも修正（A-8）
  - Affected Files: `commands/gdd-dev.md`, `references/phase-progression.md`, `references/root-cause-investigation.md`, `references/state-machine.md`, `hooks/scripts/run-pre-compact-hook.sh`, `hooks/scripts/run-pre-pr-gate-hook.sh`, `tests/checks/broken-reference-lint.sh`
  - User Action Required: なし（すべて内部契約の不整合修正、利用者向け手順に変更なし）
  - Validation / Eval Impact: `tests/validate-plugin.sh` に `broken-reference-lint` BLOCK を追加。`python3 -m pytest plugins/gate-driven-development/tests/ -q` 全 pass。

### [0.8.1] - 2026-07-06

#### Added

- **`references/workspace-policy.md` を新設し、worktree 有無の判断ルールを一本化**:
  - Summary:
    1. 判断軸を「commit を生む作業＝worktree／生まない作業＝root」の2値に統一（レーン・サイズ・系統で判断を変えない）
    2. `task-sizing.md` / `common-guardrails.md` / `operation-levels.md` / `gdd-using-git-worktrees/SKILL.md` / `gdd-pre-workflow-brainstorming/SKILL.md` / `faq.md` の重複していた判断本文を参照に置換（enforcement 本文は保持）
    3. `output-format.md` に「作業場所宣言」節を新設し、応答の最初の1行での宣言フォーマットを規定
    4. `source-of-truth-map.md` に worktree 判断ルールの正本として登録
  - Affected Files: `references/workspace-policy.md`（新設）、`references/output-format.md`、`references/task-sizing.md`、`references/common-guardrails.md`、`references/operation-levels.md`、`references/source-of-truth-map.md`、`references/gdd-scenario-evals.md`、`references/faq.md`、`skills/gdd-using-git-worktrees/SKILL.md`、`skills/gdd-pre-workflow-brainstorming/SKILL.md`、`evals/gdd-scenario-fixtures.json`
  - User Action Required: なし（既存の worktree 挙動は変更しない。作業場所宣言の必須化のみが新しい可観測な挙動）

#### Validation / Eval Impact

- `evals/gdd-scenario-fixtures.json` に `workspace_policy_quick_declares_worktree_path` / `workspace_policy_trivial_declares_root_reason` を追加
- `tests/test_gdd_scenario_eval_contract.py` green

### [0.8.0] - 2026-06-28

#### Added

- **調査・検証規律の構造的改善（改善1〜5）**: セッション56b3bfd1で観測された4パターンの手戻りを GDD ワークフローに組み込んだ。
  - **改善1（Runner Structure Check）**: `Engineering Baseline Survey` に `runner / eval harness structure` 行を追加。設計前にテストランナー / eval ハーネスの内部構造（実行時設定・MCP強制無効化等）を確認するチェックを義務化。
  - **改善2（Verification Sanity Check）**: `requirements-template.md` に `## Verification Sanity Check` セクションを追加。`brainstorming-steps.md` に Step 8h を追加。検証実行前に「そのセットアップで目的の改善が測れるか」を確認する手順を明文化。
  - **改善3（Structural Mismatch Early-Exit）**: `phase-progression.md` の Escalation Decision Table に structural mismatch 行を追加。前提崩壊（refinement ではなく設計前提そのものが崩れている失敗）はリトライ回数を待たず attempt 1 で `planning_rework_required` として中断する規律。`gdd-pr-review-followup/SKILL.md` の Escape Hatches から正本を参照。
  - **改善4（Knowledge Transfer Check）**: `Existing Implementation Survey` に `knowledge transfer check` 行を追加。`brainstorming-steps.md` の Problem Discovery に過去セッション棚卸しチェックを追加。過去の実験結果・技術的制約・失敗アプローチの引き継ぎ漏れを防ぐ。
  - **改善5（WHY→WHAT→HOW 順序統一）**: `human-check-template-compact.md` / `human-check-template.md` / `gdd-brainstorming/SKILL.md` の HITL 表示順序を WHY（なぜやるか・根本原因）→ WHAT（整理した要件）→ HOW（実装する方法・内容）に統一。WHY を先頭に置くことで WHAT と HOW の判断根拠が見える。
  - **gdd-planning-reviewer** に改善1/2/4 対応の reviewer 観点（Runner Structure Check / Verification Sanity Check 確認 / 過去セッション棚卸し確認）を追加。
  - Affected Files: `references/requirements-template.md`, `references/brainstorming-steps.md`, `agents/gdd-planning-reviewer.md`, `references/phase-progression.md`, `skills/gdd-pr-review-followup/SKILL.md`, `references/human-check-template.md`, `references/human-check-template-compact.md`, `skills/gdd-brainstorming/SKILL.md`
  - User Action Required: なし（既存ワークフローへの追記・拡張のみ。破壊的変更なし）
  - Validation / Eval Impact: `python3 -m pytest plugins/gate-driven-development/tests/` 全件 pass を確認

### [0.7.9] - 2026-06-24

#### Fixed

- **TDD Template Return Contract の欠落ケースを修正（empirical-prompt-tuning による発見）**:
  - Summary:
    1. `planned_red_missing` ケースを追加（Planned RED/E2E 欠落時 → `Next Action=gdd-task-breakdown`）
    2. `needs_clarification` ケースを追加（Completion Testability Matrix に `needs-clarification` 残留時 → `human-check-waiting` 優先）
    3. 異常完了時は handoff ファイル不要であることを明示
    4. TDD Post-Return Routing に `gdd-task-breakdown` を追加
    5. 正常完了 handoff の最小構成を inline 化（references descent 解消: 46→22 tool_uses）
  - Affected Files: `references/subagent-dispatch.md`
  - User Action Required: なし

### [0.7.8] - 2026-06-24

#### Changed

- **コンテキスト節約: TDD subagent 化・Handoff ファイル化・impl ループ disk 参照規律**:
  - Summary:
    1. **TDD を Sonnet subagent 化**: `gdd-test-driven-development` をメインセッションから Sonnet subagent に変更。RED 証跡を tasklist.md に書き、state.md 更新後に 5行以内のサマリーを返して終了する。実装継続はメインセッションが担う。
    2. **Handoff をファイル経由に**: `references/subagent-dispatch.md` に `## Subagent Return Output Contract` セクションを追加。全 subagent は詳細な Handoff Summary を `.steering/<task>/handoff/<phase>.md` に書き、main session への return は 5行以内に制限する。
    3. **impl ループの disk 参照規律**: `### Loop Context Discipline` セクションを追加。毎サイクルで tasklist.md / state.md を disk から再読し、前サイクルの詳細を次サイクルに持ち込まない規律を明文化した。
  - Affected Files: `references/subagent-dispatch.md`, `skills/gdd-test-driven-development/SKILL.md`, `commands/gdd-dev.md`
  - User Action Required: なし（ユーザー向けフロー変更なし）
  - Validation / Eval Impact: なし（動作は等価。コンテキスト消費量の改善）

### [0.7.7] - 2026-06-24

#### Changed

- **task-breakdown を Sonnet subagent として dispatch（コンテキスト分離）**:
  - Summary: `gdd-task-breakdown` をメインセッション実行から Sonnet subagent 実行に変更した。design → task → TDD の流れは変わらないが、タスク分解フェーズに必要なファイル読み込み（requirements.md / design.md 等）がメインセッションのコンテキストを汚染しなくなる。メインセッションは subagent の return 後に state.md を re-read して Next Action を確認し、TDD へ継続する。
  - Affected Files: `references/subagent-dispatch.md`, `skills/gdd-task-breakdown/SKILL.md`, `commands/gdd-dev.md`
  - User Action Required: なし（ユーザー向けフロー変更なし）
  - Validation / Eval Impact: なし（動作は等価）

### [0.7.6] - 2026-06-21

#### Added

- **SSO/auth 失効の非終端 pause reason `auth-waiting`（S-1: self-healing 自走再開の基盤）**:
  - Summary: SSO/auth セッション失効を表す新しい非終端 stop reason `auth-waiting` を、既存の `external-review-waiting` と同じ pause 機構（`ALLOWED_STOP_REASONS` / `GOAL_INCOMPLETE_REASONS` への登録、Stop hook の state.md 保持分岐）に 1 つ追加した。再ログイン後の wake で自走再開する想定。あわせて (1) next-action guard 通過の固定（`auth-waiting` は `EXEMPT_REASONS` に入れず `👤 次にすること` ブロックを必須化）、(2) `gdd-pr-review-followup/SKILL.md` への機械パース可能な構造化マーカー（`gdd-auth-pause` ブロック、reason/resume-on/no-cred の 3 ラベル）と lint 検証（`lint_auth_pause_marker`、reason 値を `ALLOWED_STOP_REASONS` と突合）、(3) wake 上限 `AUTH_WAITING_MAX_WAKES`（既定 12）到達で silently 再 arm せず `blocked` へ倒す bounded wake helper、(4) 認証情報不混入の negative contract test（token-shaped 値が停止出力・state.md に残らない preserve-only 経路の実証）を追加した。S-1 のみ。S-2（reviewer reachability）/ S-3（別経路封鎖 + 既 land 軽量検証）は後続 PR。
  - Affected Files: `hooks/scripts/lib/constants.py`, `hooks/scripts/lib/auth_waiting.py`（新規）, `hooks/scripts/gdd_stop_hook.py`, `references/output-format.md`, `scripts/lint-pr-review-followup-state.py`, `skills/gdd-pr-review-followup/SKILL.md`, `tests/test_auth_waiting_pause_contract.py`（新規）, `tests/validate-plugin.sh`
  - User Action Required: SSO/auth 失効で停止する場合は `<gdd-stop reason="auth-waiting">` を `## 👤 次にすること`（再ログイン案内）付きで出す。再ログイン後の wake で自走再開する。wake 上限到達時は `blocked` になるため「続行して」で再開する。認証情報（SSO token 等）は plugin が保持・出力しない。
  - Validation / Eval Impact: `tests/test_auth_waiting_pause_contract.py`（13 contract test：constants membership / output-format 両テーブル / Stop hook preserve / next-action guard 通過 / 構造化マーカー lint + CLI / token-free preserve-only / wake 上限）を追加。`tests/validate-plugin.sh` に followup SKILL の auth-pause マーカーを `--skill` で検証する release-gate 配線を追加（exit 0 維持）。

### [0.7.5] - 2026-06-21

#### Added

- **停止境界の次アクション強制 / 多段 stage / 外部レビュー自走 / コンテキスト節約**:
  - Summary: OT-F10（停止時に reason 別の `👤 次にすること` ブロックを Stop hook で fail-closed 検査）、OT-F9（multi-stage を `Planned Follow-up Stage Lane` に登録し、done + 未完 stage で `### 次の計画` を強制）、OT-F2（done-guard を active task に scope し、複数 `.steering` 併存時の誤ブロックを解消）、OT-F3（`external-review-waiting` を一級 pause reason にし、followup を `ScheduleWakeup` で自走待機・ポーリング上限付き）、Ctx-1（plan-reread 注入の time-windowed dedup）を追加。
  - Affected Files: `hooks/scripts/gdd_stop_hook.py`, `hooks/scripts/lib/constants.py`, `hooks/scripts/run-user-prompt-submit-hook.sh`, `hooks/scripts/run-pre-tool-use-plan-reread-hook.sh`, `references/output-format.md`, `skills/gdd-pr-review-followup/SKILL.md`, `evals/gdd-scenario-fixtures.json`
  - User Action Required: 停止出力には reason 対応の `👤 次にすること` ブロックを必ず付ける。複数段階作業は stage lane に登録し、続行は「次に進んで」。
  - Validation / Eval Impact: stop hook / prompt-submit / plan-reread の contract テストと外部レビュー収束の scenario eval を追加。

#### Changed

- **Runtime budget backstop for SKILL and templates**:
  - Summary: HITL だけでなく、GDD 実行時に読まれる `SKILL.md` 本文、runtime template、express / standard runtime profile にも budget lint を追加した。`lint-runtime-budget.py` は SKILL body line budget / Runtime template budget / estimated runtime tokens を出力し、source docs の増加と利用者体験の重さを分けて検出する。
  - Affected Files: `scripts/lint-runtime-budget.py`, `references/context-budget.md`, `tests/test_p0_meta_feedback_contract.py`, `tests/validate-plugin.sh`
  - User Action Required: SKILL 本文や runtime template を増やす変更では、`lint-runtime-budget.py` の cap を超えないことを確認する。cap を上げる場合は、なぜ runtime surface を増やす必要があるかと後続の削減計画を PR に書く。
  - Validation / Eval Impact: `tests/validate-plugin.sh` が `lint-runtime-budget.py` を実行し、`test_p0_meta_feedback_contract.py` が linter の pass / fail と Runtime Budget の正本表記を検証する。

- **HITL primary surface runtime budget**:
  - Summary: compact HITL の `Architecture Option Matrix` / `Multiple PR Strategy Options` を常設の詳細表から条件付きの 1〜3 行要約へ変更した。詳細比較は `requirements.md` / `design.md` に置き、HITL 一次表示には判断に必要な差分だけを残す。あわせて Context Budget に Runtime Budget / Source Budget の分離を明記し、references 行数 budget は source sprawl backstop であり runtime budget ではないことを固定した。
  - Affected Files: `references/human-check-template-compact.md`, `references/context-budget.md`, `skills/gdd-requirements-gating/SKILL.md`, `tests/test_reference_integrity_contract.py`, `tests/test_p0_meta_feedback_contract.py`, `tests/validate-plugin.sh`
  - User Action Required: 複数の妥当な architecture / CI / tooling 選択肢がある場合、HITL には要約と人間に確認する点だけを出し、候補別の詳細表は requirements / design に置く。単一案なら空の Matrix 見出しを出さず、`選択肢なし（単一案。理由: ...）` と書く。
  - Validation / Eval Impact: compact HITL は 100 行以内に縮小し、Architecture Option Matrix の詳細表を一次表示に常設しないことを `test_reference_integrity_contract.py` で検証する。`test_p0_meta_feedback_contract.py` は Runtime Budget / Source Budget の分離を固定する。

- **Superpowers execution disciplines imported into GDD**:
  - Summary: superpowers の `finishing-a-development-branch` / `dispatching-parallel-agents` / `requesting-code-review` から、GDD に合う 3 つの作法を取り込んだ。completion 後は検証済み証跡と worktree provenance を確認したうえで 4 択（PR 作成 / 保持 / ローカル整理 / 破棄）を出す。原因調査の並列化は independent failure-domain に限定し、related failures や shared state は sequential に戻す。レビューは formal gate を置き換えず、task completion や natural checkpoint で早めの軽量 advisory review を提案できるようにした。
  - Affected Files: `skills/gdd-completion-check/SKILL.md`, `references/parallel-failure-investigation.md`, `skills/gdd-systematic-debugging/SKILL.md`, `skills/gdd-requesting-code-review/SKILL.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `tests/test_superpowers_imported_disciplines_contract.py`
  - User Action Required: completion 後の選択肢では、PR 作成が既定でも merge / deploy / apply / release は別承認として扱う。並列調査を使う場合は no shared state / no order dependency / no overlapping files を満たすことを確認する。
  - Validation / Eval Impact: `test_superpowers_imported_disciplines_contract.py` が 4 択 completion menu、independent failure-domain dispatch、early lightweight advisory review の契約を検証する。
- **PR review follow-up waiting loop**:
  - Summary: `gdd-pr-review-followup` に `Review Pending Loop` を追加し、PR 作成直後や再レビュー依頼後にレビューが未着の場合は `clean` ではなく `waiting_for_review` / `pushed_waiting_re_review` として扱うようにした。GraphQL `reviewThreads` の `isResolved` / `isOutdated` と `headRefOid` を使う thread-aware evidence を契約化し、flat comments only では完了判定しない。Codex では heartbeat / Codex automation を待機確認に使える一方、Claude Code / Cursor でも同じ visible state contract を state.md / worklog.md に残す。
  - Affected Files: `skills/gdd-pr-review-followup/SKILL.md`, `skills/gdd-completion-check/SKILL.md`, `references/skill-responsibility-matrix.md`, `tests/test_pr_review_followup_contract.py`, `tests/test_p0_meta_feedback_contract.py`
  - User Action Required: PR 作成後レビュー待ちの状態では `clean` とせず、`waiting_for_review` と次回確認条件を残す。レビュー修正を push して再レビュー依頼した後は `pushed_waiting_re_review` とし、latest head の unresolved actionable thread と required checks を確認してから `clean` にする。
  - Validation / Eval Impact: `test_pr_review_followup_contract.py` が review pending loop / thread-aware evidence / cross-platform waiting を検証する。`test_p0_meta_feedback_contract.py` は新しい follow-up status set を固定する。

- **Raw steering local pre-commit guard**:
  - Summary: `check-no-raw-task-steering.py` に `--staged` を追加し、raw task `.steering/<task>/` を誤って `git add` した時点で検出できるようにした。CI の `--against` backstop に加え、commit / PR 作成前の local check と optional pre-commit hook 導線を `docs/CI_GUARDS.md` / `PROJECT_CLAUDE_MD_TEMPLATE.md` / `gdd-completion-check` に接続した。
  - Affected Files: `scripts/check-no-raw-task-steering.py`, `docs/CI_GUARDS.md`, `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`, `skills/gdd-completion-check/SKILL.md`, `tests/test_steering_retention_contract.py`, `tests/test_distribution_readiness_contract.py`
  - User Action Required: 導入先 repo で raw steering 混入を早期検知したい場合は、`docs/CI_GUARDS.md` の optional pre-commit hook を追加する。PR 作成前は `python3 scripts/check-no-raw-task-steering.py --staged` と `--against origin/main` の両方を実行する。
  - Validation / Eval Impact: `test_steering_retention_contract.py` が staged raw task steering の reject と repo-level learned-patterns の allow を検証する。`test_distribution_readiness_contract.py` が local guard / pre-commit 導線の配布文書記載を固定する。

- **Goal-driven loop ownership and skill count budget guard**:
  - Summary: `gdd-goal-driven-execution` / `root-cause-investigation` / `gdd-subagent-driven-implementation` / Stop hook の loop 責務を `references/state-machine.md` の `Goal-Driven Loop Ownership` に単一正本化し、outer loop / inner loop / routing bridge / continuation guard の境界を明確化した。outer loop が root cause probe や実装完了判定を横取りしない `Outer Loop Boundary` / `Inner Loop Handoff Contract` を追補し、inner loop は status/evidence を返すだけで Goal Contract / `verified_done` を所有しないことを固定した。あわせて `validate-plugin.sh` に Skill count budget を追加し、現行 28 skill を超える加算式改修、budget 変更時の削減計画欠落、Codex manifest の skill count drift を fail するようにした。
  - Affected Files: `references/state-machine.md`, `skills/gdd-goal-driven-execution/SKILL.md`, `skills/root-cause-investigation/SKILL.md`, `skills/gdd-systematic-debugging/SKILL.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `CONTRIBUTING.md`, `tests/validate-plugin.sh`, `tests/test_superpowers_differentiation_contract.py`
  - User Action Required: 新しい skill を追加する場合は、既存 skill の統合・削除・責務移管で 28 以内に収める。上限自体を変える場合は `SKILL_COUNT_BUDGET_CHANGE=true` と `SKILL_COUNT_REDUCTION_PLAN=<理由と削減計画>` を validation / PR evidence に残す。
  - Validation / Eval Impact: `test_superpowers_differentiation_contract.py` が Goal-driven loop owner の state-machine 正本化、outer/inner handoff 境界、Skill count budget の機械 enforcement を検証する。`validate-plugin.sh` は 29 個目の skill、budget 変更時の削減計画欠落、Codex manifest の skill count mismatch で fail する。

- **Branch-only steering retention with CI backstop**:
  - Summary: standard GDD task の raw task `.steering/<task>/` は branch-only working state とし、merge 後の main には残さない運用へ変更した。作業中の task branch では cross-machine handoff が本当に必要な場合だけ一時 commit / push してよいが、PR 作成前に ADR / PR body / 採用済み repo-level learned-patterns へ蒸留し、`git rm -r .steering/<task>/` 等で PR / main の diff を net-zero にする。raw steering の一時 push は branch 履歴に残るため、squash merge と merge 後 branch delete を前提にする。
  - Affected Files: `skills/gdd-completion-check/SKILL.md`, `skills/gdd-using-git-worktrees/SKILL.md`, `references/post-completion-learning.md`, `references/cross-task-learning.md`, `docs/CI_GUARDS.md`, `docs/ONBOARDING.md`, `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`, `docs/SECURITY.md`, `scripts/check-no-raw-task-steering.py`, `.github/workflows/plugin-lint.yml`, `tests/test_steering_retention_contract.py`, `tests/test_distribution_readiness_contract.py`, `tests/fixtures/gdd-steering-retention-scenarios.json`
  - User Action Required: 導入先 repo の CI に `docs/CI_GUARDS.md` の raw task steering guard を追加する。進行中 branch で raw task steering を handoff 用に commit している場合、PR 作成前に重要判断を ADR 等へ蒸留し、raw task `.steering/<task>/` を除去してから push する。repo-level `.steering/learned-patterns.md` は既に採用済みの場合だけ更新する。
  - Validation / Eval Impact: `check-no-raw-task-steering.py` を CI の `plugin-lint` に接続し、tracked raw task steering が残る PR / main を fail する。repo root 直下だけでなく `services/foo/.steering/<task>/...` のような subdirectory steering も検出する。`branch_only_steering_post_merge_continuation` scenario fixture と `test_steering_retention_contract.py` が branch-only transfer / ADR distillation / learned-patterns adoption boundary を検証する。

#### Breaking Contract Changes

- **Raw task steering is no longer merged to main by default**:
  - 以前の「current task の `.steering/<slug>/` を PR に載せる」前提を改訂し、standard 運用では raw task `.steering/<task>/` を main に含めない。strict 監査用途で main へ残す場合は human check で `strict steering retention` を明示承認し、理由を ADR と PR body に残す。

#### Fixed

- **P0 E2E replay fixture tuning pass**:
  - P0: empirical-prompt-tuning の白紙評価で、非エンジニア向けHITLの読みにくさと PR review follow-up 早期 clean が既存 replay runner では固定できないことを確認し、`lint-human-check-language` / `lint-hitl-complexity` / `lint-pr-review-followup-state` を replay runner に追加した
  - P0: `hitl-readability-unexplained-terms` と `pr-review-followup-early-clean` の bad fixture を追加し、説明なし内部用語と fresh evidence / push / re-review request なしの clean claim が release gate で fail するようにした
  - P0: `docs/DISTRIBUTION_READINESS.md` に E2E Replay Fixture Authoring を追加し、開発元だけで実行する責任分界、`expected.json` schema、対応 runner、未対応 runner の追加手順を明示した
  - Pressure scenario: maintainer が workflow 事故を fixture 化したいが、どの runner を使うか分からず、配布先に replay fixture 実行を求めるか、既存 runner で表現できない事故を covered と誤認する
  - Affected Files: `scripts/lint-pr-review-followup-state.py`, `tests/test_e2e_replay_fixtures.py`, `tests/fixtures/e2e-replay/**`, `docs/DISTRIBUTION_READINESS.md`, `references/workflow-incident-review.md`, `skills/gdd-completion-check/SKILL.md`, `references/post-completion-learning.md`, `tests/validate-plugin.sh`
  - User Action Required: 配布先で replay fixture を実行する必要はない。開発元の PR / release gate で `python3 -m unittest plugins/gate-driven-development/tests/test_e2e_replay_fixtures.py` と通常の plugin validation を実行する
  - Validation / Eval Impact: replay fixture tests が 5 fixture 以上を要求し、validate-plugin に `pr-review-followup-state-lint` smoke を追加した
- **P0 E2E replay fixtures for workflow regressions**:
  - P0: 非エンジニアに読めない最終 HITL を防ぐため、`lint-human-check-language.py` が human-check-waiting の最終HITLに `30秒判断` / `今回OKすると決まること` / `OKしても決まらないこと` / `AIが自走しないこと` / `変更したいなら言う場所` を必須化するよう強化した
  - P0: PRレビュー後ループが早く終わる問題を防ぐため、修正を push した iteration で clean を名乗るには `Post-fix Fresh PR Review Evidence` と `Post-fix Fresh PR Checks Evidence` を必須化し、pending / queued / in_progress / running / failed checks では clean にならないようにした
  - P0: `hitl-missing-decision-brief` / `pr-review-followup-post-fix-refresh-missing` replay fixture を追加し、最終HITLの冒頭判断欄欠落と、修正後PR再取得なしの premature clean を release regression test で検出できるようにした
  - P0: 既存コード読解不足の再発防止として `Existing Code Reading Evidence` に `existing_capability_refs` を追加し、既存 DSL / config / helper / workflow を再利用できるかを HITL 前に明示する契約へ拡張した
  - P0: `existing-capability-missed` replay fixture を追加し、呼び出し元・設定・テストを読んでいても既存機能・再利用候補が未確認なら release regression test で fail するようにした
  - Pressure scenario: 既存の schedule DSL / 成功・失敗通知分離が実装済みなのに、GDD 計画が新設寄りに進み、ユーザーが「設定できるようにしたはず」と補正するまで既存機能再利用が HITL に出ない
  - P0: `tests/fixtures/e2e-replay/` と `tests/test_e2e_replay_fixtures.py` を追加し、過去事故型の artifact を既存 lint へ replay する release regression test を作った
  - P0: 初期 fixture として `resume-mixup` / `shallow-code-reading` / `stripped-hitl` を追加し、resume混線、既存コード読解不足、最終HITL詳細欠落を再現する bad artifact が期待どおり fail することを確認できるようにした
  - Pressure scenario: 開発元では個別 lint が通っているが、実運用で起きた事故に近い artifact 一式を再生していないため、resume混線やHITL詳細欠落の再発がPRレビューで見えない
  - Affected Files: `tests/test_e2e_replay_fixtures.py`, `tests/fixtures/e2e-replay/**`, `docs/DISTRIBUTION_READINESS.md`, `CHANGELOG.md`
  - User Action Required: 配布先で fixture replay を実行する必要はない。開発元の PR / release gate で `python3 -m unittest plugins/gate-driven-development/tests/test_e2e_replay_fixtures.py` または通常の unittest discover を実行する
  - Validation / Eval Impact: `python3 -m unittest discover -s plugins/gate-driven-development/tests -p 'test_*.py'` に E2E replay fixture tests が含まれる
- **P0 workflow stability guard pass**:
  - P0: `scripts/lint-resume-integrity.py` を追加し、`Task ID` / steering directory / branch slug / worktree path / build phase の `tasklist.md` 有無がズレた状態で resume しない fail-closed check を追加した
  - P0: `validate-plugin.sh` に resume integrity、existing-code-reading、HITL display integrity、human-check language lint の pass / fail smoke を接続し、配布前の安定化 guard を増やした
  - P0: `gdd-pr-review-followup` に `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` の follow-up iteration status handling を追加し、fresh に PR reviews / review threads / comments / required checks を再取得するまで `actionable finding 0件` と言わない契約を強化した
  - Pressure scenario: compact / resume 後に古い `20260601-example-review-task` の state が別 branch の作業に混入する、または PR review follow-up が `DONE_WITH_CONCERNS` を clean と誤認して指摘ゼロを宣言する
  - Affected Files: `scripts/lint-resume-integrity.py`, `references/state-machine.md`, `skills/gdd-pr-review-followup/SKILL.md`, `docs/DISTRIBUTION_READINESS.md`, `tests/test_p0_meta_feedback_contract.py`, `tests/validate-plugin.sh`
  - User Action Required: resume / compact recovery / SessionStart hook の変更では `lint-resume-integrity.py` の pass / fail sample を release evidence に含める。PR review follow-up では clean claim 前に fresh な PR reviews / comments / checks を再取得する
  - Validation / Eval Impact: `test_p0_meta_feedback_contract.py` に resume integrity linter と PR review follow-up loop の contract tests を追加し、`validate-plugin.sh` に resume / existing-code-reading の fail sample を追加した
- **P0 deep existing-code reading gate**:
  - P0: `Existing Code Reading Evidence` を、変更対象ファイル名だけではなく、呼び出し元 / consumer / 既存テスト / runtime-config / 類似実装 / 入口から下流までの経路 / 未読 gap / 作り方への影響まで残す契約に拡張した
  - P0: `scripts/lint-existing-code-reading.py` を追加し、target file only や読んだファイル名だけの浅い証跡を検出できるようにした
  - P0: requirements-gating / task-breakdown / implementation が同じ読解証跡を引き継ぎ、実装フェーズで推測補完せず design_detail_only または human_recheck_required に戻す契約を強化した
  - Pressure scenario: GDD が既存コード変更を計画する際、変更対象ファイルだけを読んで HITL に進み、呼び出し経路・runtime 設定・類似実装・下流 consumer を見落として「思った作り方と違う」実装になる
  - Affected Files: `scripts/lint-existing-code-reading.py`, `references/requirements-template.md`, `references/brainstorming-steps.md`, `references/requirements-gating-steps.md`, `references/human-check-template.md`, `references/task-breakdown-steps.md`, `skills/gdd-requirements-gating/SKILL.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `tests/test_hitl_trace_contract.py`, `tests/validate-plugin.sh`
  - User Action Required: 既存コード変更の GDD では、HITL 前に `Existing Code Reading Evidence` の各列を埋める。見つからない項目は空欄にせず、検索範囲・未発見理由・作り方への影響を書く
  - Validation / Eval Impact: `test_hitl_trace_contract.py` に deep existing-code reading contract と linter regression test を追加し、`validate-plugin.sh` に lint smoke を追加した
- **P0 final HITL trace visibility hardening**:
  - P0: `scripts/lint-hitl-display-integrity.py` を追加し、壁打ち後に GDD で計画した最終表示HITLから `初期案・壁打ちから変わったこと` / `ズレ確認` / `完了条件の変換` / `テスト化確認` / `技術スタック確認` / `作り方の重要判断` が落ちる regression を検出できるようにした
  - P0: `human-check-template` / `requirements-gating` に **Final HITL Display Integrity** を追加し、subagent が生成した HITL を main session が再要約して省略しない契約を明示した
  - Pressure scenario: subagent の completed HITL には詳細なズレ確認があるのに、main session が人間へ出す最終HITLで前提と承認ポイントだけに圧縮され、壁打ちで決めた path_index / source evidence depth / テスト化境界が見えないまま OK される
  - Affected Files: `scripts/lint-hitl-display-integrity.py`, `references/human-check-template.md`, `references/requirements-gating-steps.md`, `skills/gdd-requirements-gating/SKILL.md`, `tests/test_hitl_trace_contract.py`, `tests/validate-plugin.sh`
  - User Action Required: generated HITL sample を release evidence に含める場合は、`scripts/lint-hitl-display-integrity.py <sample.md>` を実行し、最終表示HITLで壁打ち差分とズレ確認が見えることを確認する
  - Validation / Eval Impact: `test_hitl_trace_contract.py` に Final HITL Display Integrity の regression / pass / contract tests を追加し、`validate-plugin.sh` に lint block を追加した
- **P0 meta feedback hardening pass**:
  - P0: `scripts/lint-hitl-outcome-audit.py` を追加し、`HITL Outcome Audit` に `mismatch` / `unverified` が残る場合は completion を通さない hard gate として検出できるようにした
  - P0: `scripts/lint-hitl-complexity.py` を追加し、生成された HITL sample の HITL行数 / 承認ポイント数 / 詳細表数 / 内部用語数を GDD Complexity Budget として実測できるようにした
  - P0: `references/workflow-incident-review.md` を追加し、`hitl_readability` / `resume_mixup` / `worktree_contamination` / `skill_arbitration` / `context_loss` / `code_reading_gap` を workflow 事故として分類し、再発防止を post-completion learning に接続した
  - Pressure scenario: HITL Outcome Audit に mismatch / unverified が残ったまま completion へ進む、または HITL が肥大化して読めない状態が再発する、または resume混線やworktree汚染などGDD workflow自体の事故が学習されず同じ失敗を繰り返す
  - Affected Files: `scripts/lint-hitl-outcome-audit.py`, `scripts/lint-hitl-complexity.py`, `references/workflow-incident-review.md`, `skills/gdd-completion-check/SKILL.md`, `references/post-completion-learning.md`, `tests/test_p0_meta_feedback_contract.py`, `tests/validate-plugin.sh`
  - User Action Required: generated HITL sample や requirements.md を release evidence に含める場合は、`lint-hitl-complexity.py` と `lint-hitl-outcome-audit.py` を実行する。workflow事故が起きた場合は Workflow Incident Review の type と再発防止を残す
  - Validation / Eval Impact: `test_p0_meta_feedback_contract.py` が 10 tests に増え、Outcome Audit hard gate、Complexity Budget lint、Workflow Incident Review、validate-plugin 統合を検証する
- **P0 meta feedback loop pass**:
  - P0: `gdd-completion-check` に **HITL Outcome Audit** を追加し、human check の `Approved Direction` と最終成果物を照合する契約にした。`何を作るか` / `どう作るか` / `何を完了とみなすか` / `確認すること` / `確認しないこと` / `AIに任せる範囲` / `AIが止まって人間に戻す条件` を `match / mismatch / unverified` で確認し、ズレが残る場合は completion を通さない
  - P0: HITL の **GDD Complexity Budget** を追加し、内部用語数、HITL行数、承認ポイント数、正本重複、似たルールの重複が増えすぎた場合に詳細表削減または easy summary へ戻す契約にした
  - P0: `scripts/lint-human-check-language.py` を追加し、`holdout` / `human-confirm` / `executable` など代表的な内部用語が説明なしで人間向け HITL に出ることを検出できるようにした
  - Pressure scenario: HITL は一見分かりやすいが、最終成果物が承認された作り方・完了条件・検証範囲からズレたまま PR 作成まで進む。また、内部用語が説明なしに出て「何を言っているのかわからない」状態で承認される
  - Affected Files: `skills/gdd-completion-check/SKILL.md`, `references/requirements-template.md`, `references/human-check-template.md`, `skills/gdd-requirements-gating/SKILL.md`, `docs/DISTRIBUTION_READINESS.md`, `scripts/lint-human-check-language.py`, `tests/test_p0_meta_feedback_contract.py`, `tests/validate-plugin.sh`
  - User Action Required: HITL / prompt / skill 文面を変える PR では、HITL Outcome Audit と GDD Complexity Budget の観点を確認する。human-check sample がある場合は `scripts/lint-human-check-language.py <sample.md>` を実行する
  - Validation / Eval Impact: `test_p0_meta_feedback_contract.py` を追加し、HITL Outcome Audit、Complexity Budget、説明なし内部用語の lint、validate-plugin 統合を検証する
- **P0/P1/P2 human-check readability pass**:
  - P0: HITL の冒頭を「このOKでAIが自走した場合、期待どおりの結果になりそうですか？」に寄せ、`このOKで承認するもの` / `このOKで承認しないもの` / `AIに任せる範囲` / `AIが止まって人間に戻す条件` を先に出す契約にした
  - P1: `初期案・壁打ちから変わったこと` を `ズレ確認` より前に出し、`変更点` / `理由` / `OKするとどうなるか` / `影響する承認項目` を明示することで、壁打ち内容と HITL の承認対象の差分を見えるようにした
  - P2: エンジニア向け HITL でも専門用語だけで説明せず、まず結論、次に OK の意味、その後に詳細を出す `やさしい表示順` を追加した。詳細表は根拠確認用とし、詳細表を読まないと OK の意味が分からない構造を避ける
  - Pressure scenario: 人間が「何を言っているのかわからない」と感じる HITL に OK してしまい、AI が意図と違う作り方・完了条件・検証範囲で自走する
  - Affected Files: `references/human-check-template.md`, `references/requirements-template.md`, `references/requirements-gating-steps.md`, `skills/gdd-requirements-gating/SKILL.md`, `docs/NON_ENGINEER_HITL_GUIDE.md`, `tests/test_hitl_trace_contract.py`
  - User Action Required: 新しい HITL では、まず `30秒判断` と `初期案・壁打ちから変わったこと` を確認する。分からない場合は OK せず `判断材料が足りない。もっとやさしく説明して` と返す
  - Validation / Eval Impact: `test_hitl_trace_contract.py` に 5 tests を追加し、中心質問、承認する/しない境界、検証範囲と自走範囲の分離、壁打ち差分、やさしい表示順を検証する
- **P0/P1/P2 state-machine hardening pass**:
  - P0: Express Auto-Confirm が `Human Check Status: auto_confirmed` という schema 外 status を使う矛盾を修正し、`Human Check Status=approved | evidence: auto-confirm:<condition-id>` + `Auto Confirm Reason` / `Auto Confirm Timestamp` に分離した
  - P0: `/gdd-dev` command 本体に **Codex Subagent Permission Gate** を追加し、Codex では `explicit_delegation_source` または approved permission が無いまま planning / reviewer / dialectic / implementation worker の subagent dispatch を起動しない契約を明示した
  - P1: UserPromptSubmit hook に `AC Coverage Health` を追加し、`requirements.md` と Current Task の AC ID 数、`Covers AC:` 由来の AC set を context に注入して compact 後の AC 欠落を見えやすくした
  - P1: `test_p0_p1_operational_hardening_contract.py` に auto-confirm / Codex permission / AC miss hook / minimal state-machine scenario の contract test を追加した
  - P2: `references/state-schema.json` を追加し、phase status 許容値・Auto-Confirm 表現・build precheck を機械可読化した。`lint-ac.py --strict` では high-risk standard / strict 向けの machine-readable AC を強制する
  - Pressure scenario: Auto-Confirm で human check を省略した task が build pre-check で `approved` と認識されず停止する、または Codex が host 制約を無視して subagent dispatch する
  - Affected Files: `commands/gdd-dev.md`, `references/state-schema.json`, `references/task-sizing.md`, `references/gate-status-schema.md`, `references/phase-gate-prechecks.md`, `references/state-machine.md`, `references/subagent-dispatch.md`, `references/context-budget.md`, `references/ac-machine-readable-schema.md`, `references/operation-levels.md`, `hooks/scripts/run-user-prompt-submit-hook.sh`, `scripts/lint-ac.py`, `tests/test_p0_p1_operational_hardening_contract.py`
  - User Action Required: 既存 steering に `Human Check Status: auto_confirmed` を書いたものがある場合は `Human Check Status=approved | evidence: auto-confirm:<condition-id>` に直す。strict / high-risk standard task では `requirements.md` の YAML frontmatter `acceptance_criteria` を用意する
  - Validation / Eval Impact: `test_p0_p1_operational_hardening_contract.py` が 12 tests に増え、auto-confirm schema / Codex permission / AC Coverage Health / state-schema scenario / strict AC lint を検証する
- **Codex subagent delegation permission contract**:
  - Codex の subagent ツールが「ユーザーが明示的に委譲を依頼した場合のみ」という host 制約を持つため、GDD で subagent を使う予定がある場合は `Codex Subagent Delegation Permission` を state に記録する契約に変更
  - ユーザー発言 / project policy / `/gdd-dev` 引数に明示委譲ソースがある場合は `approved_by_explicit_delegation` とし、HITL で改めて承認を求めない。明示委譲ソースが無い場合だけ HITL に `subagent 委譲` の可否を露出する
  - `references/codex.md` / `references/subagent-dispatch.md` に `explicit_delegation_source` と main session inline execution fallback を追加
  - `gdd-subagent-driven-implementation` が `state.md` の Approved Direction を読み、Codex では許可が無いまま subagent を起動しないようにした
  - Pressure scenario: ユーザーが「承認しなくても subagent を使ってほしい」と明示したのに、GDD が毎回 HITL で subagent 委譲を確認し、実装開始が止まる
  - Affected Files: `references/codex.md`, `references/subagent-dispatch.md`, `references/human-check-template.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `tests/test_distribution_readiness_contract.py`
  - User Action Required: Codex で GDD に subagent を既定利用させたい場合は、初回依頼や project policy で `承認しなくてもsubagentを使ってほしい` のように明示する。明示が無い場合だけ HITL で可否を確認する
  - Validation / Eval Impact: `test_distribution_readiness_contract.py` に Codex subagent delegation permission の contract test を追加
- **Distribution readiness docs and guards**:
  - P0: `PROJECT_CLAUDE_MD_TEMPLATE.md` の branch / PR 方針を、GDD の completion flow と同じ `commit / push / PR 作成は許容、merge / Issue close / release / 本番デプロイ / terraform apply は別承認` に統一した
  - P1: 非エンジニア承認者向け `docs/NON_ENGINEER_HITL_GUIDE.md` を追加し、HITL の `30秒判断` / OK 条件 / 差し戻し条件 / 返答例 / 読まなくてよいものを独立ドキュメント化した
  - P1: `SECURITY.md` を Claude Code / Cursor / Codex 対応の境界に更新し、チーム外への配布前の確認事項と「自動検出で完全保証しない」制限を明示した
  - P1: `.steering/` 書き込み hook に AWS account ID 文脈、secret marker、sensitive value の追加検出を入れた
  - P1: `VERSIONING.md` の現行バージョンを manifest 実体に同期し、`.codex-plugin/plugin.json` と `scripts/sync-plugin-tooling.py --check` をリリース手順へ追加した
  - P1: `docs/DISTRIBUTION_READINESS.md` を追加し、チーム外への配布前の `git status --short` / `git diff --stat` / untracked 棚卸し、PR bundle 分割、`.vscode/` 等の除外を明示した
  - P2/P3: README の他チーム導入向け docs 一覧に配布 readiness / 非エンジニア docs を追加し、`docs/NON_ENGINEER_APPROVER_HANDOUT.md` を承認者向け 1 ページ配布文として追加した
  - P1/P2 follow-up: ONBOARDING に Claude Code / Cursor / Codex の host 別導入確認を追加し、README / SECURITY / DISTRIBUTION_READINESS の非エンジニア配布導線を `NON_ENGINEER_APPROVER_HANDOUT.md` first に統一した
  - Pressure scenario: 広めに配布した導入先で、`PR 作成まで自走` と `commit/push 禁止` が同居し、非エンジニア承認者が HITL の確認観点を誤解する
  - Affected Files: `CONTRIBUTING.md`, `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`, `docs/NON_ENGINEER_APPROVER_HANDOUT.md`, `docs/NON_ENGINEER_HITL_GUIDE.md`, `docs/DISTRIBUTION_READINESS.md`, `docs/ONBOARDING.md`, `docs/SECURITY.md`, `docs/VERSIONING.md`, `README.md`, `references/team-onboarding.md`, `hooks/scripts/validate-steering-write.py`, `tests/test_distribution_readiness_contract.py`
  - User Action Required: チーム外配布前に `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` の branch / PR 方針を導入先へ反映し、PM / PO には `docs/NON_ENGINEER_APPROVER_HANDOUT.md` を先に共有する
  - Validation / Eval Impact: `test_distribution_readiness_contract.py` を追加し、PR 自走範囲、非エンジニア HITL 導線、Security/Codex 境界、versioning sync、host 別 onboarding、handout-first の配布正本を契約テスト化
- **Existing code reading evidence gate before HITL and build**:
  - 既存コード変更・既存 workflow 変更で、変更対象ファイルだけを読んだ浅い理解のまま HITL / 実装へ進む問題を修正
  - `requirements.md` に `Existing Code Reading Evidence`（変更対象 / 呼び出し元 / consumer / 既存テスト / 既存 invariant / 反証 gap）を追加し、HITL には高リスク gap だけを `既存コード読解` として圧縮表示する契約に変更
  - `gdd-requirements-gating` / `gdd-task-breakdown` / `gdd-subagent-driven-implementation` が同じ証跡を消費し、責務・正本・consumer が曖昧な場合は HITL 前の Step-by-Step Clarification に戻すようにした
  - Affected Files: `references/requirements-template.md`, `references/brainstorming-steps.md`, `references/requirements-gating-steps.md`, `references/human-check-template.md`, `references/task-breakdown-steps.md`, `skills/gdd-requirements-gating/SKILL.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `tests/test_hitl_trace_contract.py`
  - User Action Required: 既存コード変更の GDD task では、HITL 前に既存コード読解の gap が露出する。判断材料が足りない場合は `判断材料が足りない` または対象の承認ポイント番号で差し戻す
  - Validation / Eval Impact: `test_hitl_trace_contract.py` に Existing Code Reading Evidence の contract test を追加
- **P0/P1 operational hardening for resume, HITL, PR provenance, and AC trace continuity**:
  - P0: telemetry collector が `state.md` を持たない legacy/root-bleed `.steering/` copy を task として集計しないようにし、`approved | evidence: ...` 形式の gate status を正規化して通過率へ反映するよう修正
  - P0: SessionStart の別セッション / default branch 上の non-terminal steering / branch-task mismatch は `Safe Resume Candidate Mode` として古い task 名や Current Task を出さず、`gdd-status` / `/gdd-dev resume <target>` に誘導するよう修正。一方で current session id が取得できないだけの same-worktree active steering は `[gdd:reboot]` を維持し、human-check の `OK` / `続けて` 自然再開を過抑制しないようにした
  - P0: `gdd-pr-review` / `gdd-completion-check` / `gdd-using-git-worktrees` に `Worktree Provenance Gate` を追加し、`task slug / branch / PR / steering / scope` 不一致や root bleed を fail-closed で止める契約に変更
  - P1: HITL の `30秒判断` 冒頭に 4 行境界（今回OKすると決まること / OKしても決まらないこと / AIが自走しないこと / 変更したいなら言う場所）を追加し、長い表の前に承認境界を読めるようにした
  - P1: AC Trace Ledger を TDD / implementation 中から append-only 更新する契約に変更し、`RED-created` / `GREEN-verified` / `REFACTOR-reverified` を completion 前の復元証跡として残すようにした
  - empirical-prompt-tuning を実施し、paused 時の通常 `/gdd-dev` resume guidance 混入を除去、description/body 乖離を同期、`root bleed` と `別 task steering 混入` の停止理由ラベルを分離、`30秒判断` 部分例での `<gdd-stop>` 扱いを明確化
  - Affected Files: `scripts/collect-gdd-telemetry.py`, `hooks/scripts/run-session-start-hook.sh`, `references/human-check-template.md`, `references/ac-trace-ledger.md`, `skills/gdd-requirements-gating/SKILL.md`, `skills/gdd-test-driven-development/SKILL.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `skills/gdd-pr-review/SKILL.md`, `skills/gdd-completion-check/SKILL.md`, `skills/gdd-using-git-worktrees/SKILL.md`, `tests/test_p0_p1_operational_hardening_contract.py`
  - User Action Required: plugin 更新後、別セッション再開時は `gdd-status` で候補を確認し、必要なら `/gdd-dev resume <target>` で明示再開する。PR 作成前に provenance mismatch が出た場合は、worktree / branch / steering の正本を解決してから再実行する
  - Validation / Eval Impact: `test_p0_p1_operational_hardening_contract.py` を追加。telemetry normalization / paused resume guidance / Worktree Provenance Gate / HITL 4 行境界 / in-progress AC trace update を契約テスト化
- **superpowers 同居時の GDD planning routing**:
  - SessionStart hook の `GDD will not auto-trigger` 表現が強すぎて、`GDDで計画して` と明示しない自然文の GDD planning / requirements / design 相談が `superpowers:writing-plans` / `superpowers:brainstorming` に吸われる問題を修正
  - formal GDD workflow の自動開始・古い task の自動再開は引き続き抑止しつつ、GDD natural-language planning intent / active GDD follow-up では GDD primary、superpowers advisory only とする契約に変更
  - `gdd-using-skills` に `GDDで計画して` / `GDDで進めたい` / active GDD follow-up の arbitration を追加
  - Affected Files: `hooks/scripts/run-session-start-hook.sh`, `skills/gdd-using-skills/SKILL.md`, `docs/SUPERPOWERS_COEXISTENCE.md`, `tests/test_superpowers_differentiation_contract.py`
  - User Action Required: superpowers と GDD を同時導入している環境では plugin 更新後に新規 session を開始する
  - Validation / Eval Impact: `test_superpowers_differentiation_contract.py` に SessionStart guidance と skill arbitration の契約テストを追加
- **P0 superpowers differentiation routing contract**:
  - `gdd-using-skills` に `Routing Contract Table`（RC-01〜RC-20）を追加し、active GDD / GDD 文脈 / compact-resume / explicit standalone superpowers request の primary route を固定
  - `GDD Workflow Lock` と `Escape Hatch` を追加。active GDD 中の意思決定・AC・タスク状態・完了証跡は GDD artifact を正本とし、別件の明示 standalone superpowers request だけ例外として許可
  - SessionStart hook に `Routing reason` を追加し、active marker の有無と GDD primary / superpowers advisory only の理由を短く表示
  - Affected Files: `skills/gdd-using-skills/SKILL.md`, `hooks/scripts/run-session-start-hook.sh`, `docs/SUPERPOWERS_COEXISTENCE.md`, `tests/test_superpowers_differentiation_contract.py`
  - User Action Required: superpowers と GDD を同時導入している環境では plugin 更新後に新規 session を開始する
  - Validation / Eval Impact: Routing Contract Table / Escape Hatch / SessionStart Routing reason の contract test を追加
- **GDD differentiation core: AC trace / completion gate / PR follow-up / compact resume**:
  - `references/ac-trace-ledger.md` を追加し、Minimal AC Trace Ledger（`AC ID` / `対応タスク` / `検証コマンド/結果` / `status` / `last verified at/phase` / `未解決リスク`）を定義
  - `gdd-completion-check` に AC Trace Ledger Gate を追加し、missing ledger row / unverified AC / failed AC が残る場合は `Next Action=gdd-completion-check` のまま completion を通さない契約に変更
  - `gdd-pr-review-followup` を source repo に追加し、PR 作成後の review findings -> fix -> push -> re-request review loop、actionable finding 0件の終了条件、idempotency key、same finding repeats >= 3 の停止条件を定義
  - compact/resume 復帰正本に `state.md / tasklist.md / worklog.md / AC Trace Ledger` を追加し、会話履歴が欠落しても AC 検証状態を復元する契約に変更
  - Affected Files: `references/ac-trace-ledger.md`, `skills/gdd-completion-check/SKILL.md`, `skills/gdd-pr-review-followup/SKILL.md`, `skills/gdd-status/SKILL.md`, `references/context-budget.md`, `references/superpowers-overlap.md`, `references/skill-responsibility-matrix.md`, `tests/test_differentiation_core_contract.py`
  - User Action Required: PR 作成後レビュー対応を GDD workflow に乗せる場合は `gdd-pr-review-followup` を使う。completion 前は AC Trace Ledger の未検証 AC を解消する
  - Validation / Eval Impact: AC Trace Ledger / completion block / PR follow-up loop / compact resume source の contract test を追加
- **HITL decision panel and pre-HITL clarification contract**:
  - `human-check-template.md` に `30秒判断` decision panel を追加し、AI の仮決定、OK すると許可されること、OK しても許可されないこと、人間が見るべき重要ポイント（最大 3 件）、承認してよい条件 / 差し戻す条件 / 保留する条件を冒頭に出す契約に変更
  - `gdd-requirements-gating` と `requirements-gating-steps.md` に Pre-HITL Critical Review / Step-by-Step Clarification を追加し、曖昧な要件・完了条件・作り方が残る場合は HITL テンプレートを出さず `clarification-needed` で一度に 1-3 問だけ確認する契約に変更
  - Affected Files: `references/human-check-template.md`, `references/requirements-gating-steps.md`, `skills/gdd-requirements-gating/SKILL.md`, `tests/test_hitl_trace_contract.py`
  - User Action Required: HITL 前に `clarification-needed` で止まった場合は、提示された 1-3 問へ回答する。回答後に requirements.md / design.md が更新され、再 review 後に通常の HITL が出る
  - Validation / Eval Impact: `test_hitl_trace_contract.py` に 30秒判断 / pre-HITL clarification の contract test を追加
- **Imported superpowers execution disciplines (P0/P1/P2)**:
  - P0: `Evidence before claims` を `gdd-completion-check` / `gdd-status` / `gdd-pr-review-followup` に接続し、fresh verification evidence 無しの pass / clean / done / actionable finding 0件 claim を禁止
  - P0: `task-breakdown-steps.md` に `Plan Placeholder Failure Gate` を追加し、`TBD` / `TODO` / `implement later` / `Similar to Task` / 空の `Code:` 等を残した tasklist を確定しない契約に変更
  - P1: PR review follow-up と receiving-code-review に External Review Skepticism を追加し、review feedback を検証対象として扱い、不明瞭な finding は一部実装前に確認する契約に変更
  - P1: completion 後の branch decision に worktree provenance / harness-owned worktree / typed discard confirmation / PR 作成時 worktree 保持を追加
  - P1: subagent implementation 開始前に Current Task Readiness Review を追加し、critical plan gaps / missing dependency / instruction unclear / planned verification 不足を code 前に差し戻す契約に変更
  - P2: TDD に Expected RED Failure Verification を追加し、wrong failure / immediate pass / setup error を RED と認めない契約に変更
  - empirical-prompt-tuning を実施し、fresh evidence の粒度、tasklist stale 時の戻り先、scope 外 review finding の human_recheck_required 条件、no valid findings claim の evidence 条件を追加明確化
  - Affected Files: `references/verification-before-completion.md`, `references/task-breakdown-steps.md`, `references/superpowers-overlap.md`, `skills/gdd-completion-check/SKILL.md`, `skills/gdd-status/SKILL.md`, `skills/gdd-pr-review-followup/SKILL.md`, `skills/gdd-receiving-code-review/SKILL.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `skills/gdd-test-driven-development/SKILL.md`, `tests/test_superpowers_imported_disciplines_contract.py`
  - User Action Required: GDD 実行中に `clarification-needed` / placeholder plan / wrong RED / evidence 不足で止まった場合は、提示された不足項目を埋めてから再開する
  - Validation / Eval Impact: superpowers discipline の取り込み contract test を追加。empirical-prompt-tuning は 3 シナリオ + targeted follow-up で実施し、最終ピンポイント構造審査で新規不明瞭点 0

#### Added

- **worktree pollution guard を追加**:
  - `gdd-using-git-worktrees` に Worktree Identity Tuple（path slug / steering slug / state task id / git branch / state active branch / base kind）を追加し、task slug・branch・state がズレた candidate を fail-closed にする契約を追加
  - `setup-gdd-loop.sh` が resume candidate 列挙時に `path_slug_mismatch` / `state_task_mismatch` / `branch_slug_mismatch` / `active_branch_mismatch` / `multiple non-terminal steerings` / `mixed worktree bases` を検出し、`worktree_pollution_warning_count` として HITL に露出するようにした
  - 汚染警告が 1 件でもある場合は auto-resume を無効化し、再開対象 / cleanup / 新規 worktree 作成を人間が選ぶまで止める
  - `tests/test_worktree_pollution_contract.py` を追加し、6/1 task worktree に 6/5 branch/state が混ざる pressure scenario を contract として検証
- **empirical-prompt-tuning Iteration 2 polish**:
  - `human-check-template` に baseline `fail` / `not_run` を承認ポイントへ昇格する条件を追加。前提には必ず出し、scope / 完了条件 / 既存 failure 修正判断に影響するときだけ承認ポイント化する
  - `gdd-systematic-debugging` に No Root Cause Decision の `final route label rule` を追加し、`status=non_reproducible` と GDD の最終 route 名を混同しないようにした
  - `root-cause-investigation` の `No Root Cause Decision` に `final route hint` を追加し、受け側の route 判定へ明示的に渡せるようにした
- **empirical-prompt-tuning Iteration 1 polish**:
  - `gdd-brainstorming` / `gdd-systematic-debugging` / `gdd-receiving-code-review` / `gdd-writing-skills` / `root-cause-investigation` の description に、今回追加した責務タグ（Baseline Verification Status / Human Partner Signals / No Root Cause Decision / Source-Specific Review Handling / Skill Type Testing Matrix）を反映し、description/body alignment を改善
  - `gdd-brainstorming` に baseline command selection priority を追加し、代表検証コマンドが不明な場合の `not_run` 判断を明確化
  - `gdd-systematic-debugging` / `root-cause-investigation` に `non_reproducible` / `insufficient_evidence` / `no_root_cause_yet` の status selection guide を追加
  - `gdd-systematic-debugging` に human signal の route selection guide を追加し、HITL 承認可否に関わる違和感は `human_recheck_required`、文面調整のみなら `design_detail_only` と選び分ける
- **superpowers 由来の残り 6 discipline を GDD に吸収**:
  - `gdd-brainstorming` / `human-check-template` に `Baseline Verification Before Work` を追加し、作業前 test/build 状態を `Baseline Verification Status` として HITL に露出。pre-existing failure と今回の failure を混同しない
  - `gdd-systematic-debugging` に `Human Partner Signals You're Doing It Wrong` を追加し、「それで大丈夫？」「非エンジニアにも使える？」等を route recalibration signal として扱う
  - `gdd-receiving-code-review` に `Source-Specific Review Handling` と `YAGNI Check for Professional Features` を追加し、human / formal reviewer / GitHub PR comment / security finding / external LLM reviewer を同列に扱わない
  - `gdd-writing-skills` に `Skill Type Testing Matrix` を追加し、Discipline / Phase Gate / Methodology / Helper / Lookup / Reference-only で failure mode に応じた contract test を選ぶ
  - `root-cause-investigation` に `When Process Reveals No Root Cause` を追加し、`No Root Cause Decision` では `fix allowed: no` として原因未確定の behavior-changing fix を禁止
  - `gdd-systematic-debugging` に `No Root Cause Routing` を追加し、root cause 未確定時に `implementation_fix_only` へ進まないよう route を明文化
- **superpowers 由来の追加 5 discipline を GDD に吸収**:
  - `gdd-implementation-gating` に `Two-Stage Review Order` を追加し、Spec Compliance Review を通してから Code Quality Review に進む順序を contract 化
  - `gdd-test-driven-development` に `Pre-existing Implementation Without RED` を追加し、RED なし実装を `Implementation Quarantine` / `characterization RED` で扱う規律を追加
  - `gdd-writing-skills` に `Process Documentation TDD` を追加し、skill / prompt / HITL 文面変更に pressure scenario / baseline failure / loophole close を適用
  - `gdd-subagent-driven-implementation` に `Subagent Prompt Contract` と `Parallel Dispatch Integration Discipline` を追加し、self-contained context / scope / constraints / expected output / integration verification を明文化
  - `references/parallel-failure-investigation.md` に shared state 条件を追加し、並列調査で evidence や修正が上書きされる経路を防止
- **superpowers 由来の 5 discipline を GDD state machine に吸収**:
  - `gdd-completion-check` に Evidence Before Claims と Development Branch Finish Discipline を追加し、fresh verification evidence なしの完了 claim と、host-managed worktree の誤 cleanup を防ぐ
  - `gdd-receiving-code-review` に READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT の順序を追加し、review finding を無検証で受け入れない
  - `gdd-task-breakdown` に File Structure Map / `#### Files` block を追加し、exact file paths / responsibility / Create・Modify・Test の対応を tasklist に残す
  - `gdd-requesting-code-review` に checkpoint review triggers と Reviewer Lineage context を追加し、major feature / security-sensitive / IaC などの節目で companion review を提案できるようにした
  - `gdd-implementation-gating` / `gdd-pr-review` に証拠なしの成功表現禁止を追加し、`tests/test_superpowers_method_import_contract.py` で契約を検証
- **active GDD に plan execution discipline を吸収**:
  - `skills/gdd-using-skills/SKILL.md` に `Plan Execution Discipline` を追加し、`superpowers:executing-plans` 由来の 5 要素（Plan Execution Readiness Review / Task-Level Verification / Plan Execution Stop Conditions / Current Task Execution Status / Return to Plan Review）を active GDD 中は GDD phase に戻して扱うことを明文化
  - `skills/gdd-task-breakdown/SKILL.md` に `Plan Execution Fields` を追加し、各 task に `Execution Status:` / `Planned Verification:` / `Stop Conditions:` / `Return Route:` を持たせ、HITL で現在地・検証方法・停止条件が読めるようにした
  - `skills/gdd-subagent-driven-implementation/SKILL.md` に実装前の批判的レビュー、task-level verification、簡潔な stop condition、plan 変更時の戻り先分類を追加。証跡なしに `Completed Tasks` へ移さない契約を強化
  - `tests/test_plan_execution_discipline_contract.py` を追加し、上記 5 要素が GDD 文書契約として残ることを検証
  - empirical-prompt-tuning Iteration 1 で、`Return Route` を default + 条件別 route として記録すること、`verification repeatedly fails` は同じ verification が 2 回連続で same failure signature により失敗した状態を既定閾値とすること、検証失敗と承認済み設計逸脱が同時に起きた場合は debug route より設計逸脱を優先することを追記
- **active GDD 中の superpowers 仲裁ルールを追加**:
  - `skills/gdd-using-skills/SKILL.md` に `Active GDD Workflow Arbitration` を追加し、`.steering/<task>/state.md` / `<gdd-stop>` 後の承認 / 自然文 follow-up がある場合は `GDD primary`、superpowers は `superpowers advisory only` と明文化
  - 仕様変更・実装方針変更は `gdd-requirements-amendment` / `gdd-systematic-debugging`、TDD は `gdd-test-driven-development`、失敗調査は `root-cause-investigation` → `gdd-systematic-debugging` へ戻す route を明文化
  - `superpowers:executing-plans` は汎用 standalone written-plan executor であり完全代替ではないこと、active GDD 中に発生した task progression 用途だけは `state.md` の `Next Action` と `tasklist.md` の `Current Task` / `Pending Tasks` を正本にした phase dispatch が担うことを明文化
  - `references/superpowers-overlap.md` と `docs/SUPERPOWERS_COEXISTENCE.md` に、Codex の `GDD will not auto-trigger to avoid conflicts` は新規 auto-trigger 抑制であり、active GDD を superpowers に譲る意味ではないことを追記
  - `tests/test_superpowers_active_gdd_contract.py` を追加し、GDD active 中に standalone superpowers primitive へ drift しない文書契約を検証
- **モデルルーティングの実行証跡を構造化**:
  - `scripts/resolve-gdd-model.py --json` に `effort` を追加。`model` だけでなく `low` / `medium` / `high` の期待値を機械検証できるようにした
  - Cursor / Codex の一般 heavy に risk escalation rule を追加。通常は `GPT-5.5 + low`、`undocumented_step` / `large_working_set` / `security_sensitive` / `final_review` signal では `GPT-5.5 + high` に上げる
  - `tests/validate-plugin.sh` に effort assertion を追加。formal gate は `medium`、leaf は `high`、一般 heavy は通常 `low` / risk escalation `high` で検証する
- **superpowers との差別化を構造化**（GDD primitives を state machine 一体型として明文化、「superpowers でいい」回避策の体系化）:
  - **`root-cause-investigation` Phase 4 に State Machine Integration セクション追加**: GDD workflow 内呼び出し時に ADR 起票判定 / Reviewer Lineage 追加提案 / Routing 提案（`gdd-subagent-driven-implementation` / `human-check-waiting` / `gdd-design-gating` / `gdd-brainstorming`）を Phase 4 出力に含めて呼び出し元へ渡す。standalone 呼び出しでは省略可
  - **`gdd-test-driven-development` に AC ID Binding 必須化**: RED Evidence に `AC: <ID>` 行が無い場合 fail-closed で reject。AC ID は `requirements.md` 実在 ID のみ許可。架空 ID（`AC-todo` 等）不可。`Contract Surface Coverage` の各観点も AC ID と紐付け推奨。state machine 一体型 TDD の構造保証
  - **`gdd-brainstorming` に Entry Intent 永続化必須化**: entry intent 判定結果（new / resume / amendment / ambiguous）を `state.md` の `Entry Intent` セクション（判定 / 判定理由 / 参照した正本 / 判定日時の 4 項目）に必ず記録。`amendment` 時は anchor 必須。`references/requirements-template.md` § Entry Intent テンプレートを正本として追加
  - **`references/superpowers-overlap.md` 新規追加**: GDD primitive と superpowers skill の overlap map（root-cause-investigation / TDD / brainstorming / subagent-driven-implementation の比較表）。GDD 固有 skill リスト、両 plugin install 時の使い分けルール、「superpowers でいい」回避のための構造を明文化
  - **`references/benchmark-scenarios.md` 新規追加**: superpowers 同等品との比較ベンチマーク用シナリオ集（7 シナリオ × 3 primitive pair）。精度 / steps / duration / state machine 連動を評価軸に、Hold-out Regression Gate（quick-gate 例外含む）で release-criteria に組み込み可能
  - **SKILL.md description に state machine 統合フレーズ追加**: `root-cause-investigation` / `gdd-test-driven-development` / `gdd-brainstorming` の description 冒頭に「state machine 統合済み」「state machine 一体型」のフレーズを追加。skill 検索時に GDD primitive の付加価値を明示
- **empirical-prompt-tuning 検証**: 上記 superpowers 差別化変更について 3 primitive × 2 iteration で並列 subagent eval を実施。Iter 1/Iter 2 ともに精度 100% × 3 シナリオ・retries 0・新規構造的不明瞭点 0（cosmetic レベルの微差のみ）で収束。Iter 2 では Iter 1 で出た 6 件の formatting-level 不明瞭点（ADR 起票記法 / Reviewer Lineage と Routing の独立軸 / fail-closed 出力範囲 / Entry Intent heading level / timestamp 形式）を polish 済み
- **受け側 skill への SMI block 連携を追加**（送り側だけでなく受け側も state machine 統合点として完備）:
  - **`gdd-systematic-debugging` に SMI Block Handoff セクション追加**: `root-cause-investigation` の Phase 4 SMI block を受け取り、Routing 提案を Decision Tree の入力に、Reviewer Lineage 追加を `tasklist.md` の `Implementation Reviewer Selection` に、ADR 起票要件を `.steering/.../adr.md` に反映する手順を明文化。SMI block 反映チェックリスト 5 項目で routing 決定前の必須確認を構造化
  - **Step 1 に SMI Block 受け取り確認を追加**: standalone 呼び出しと GDD workflow 内呼び出しを冒頭で分岐させる
- **`gdd-subagent-driven-implementation` を root-cause-investigation の SMI と対称構造に格上げ**:
  - **Reviewer Lineage 影響判定（必須）を Spec Change Detection に追加**: auth / secrets / trust 境界 / IAM / 認可ロジックに触れる変更は `gdd-security-reviewer` を、terraform / IaC 変更は terraform checklist reviewer を `Implementation Reviewer Selection` に追加提案する手順を必須化
  - **State Machine Impact Block の handoff 時出力を必須化**: 仕様変更を含む実装完了時、impl-gate への handoff 出力末尾に「ADR 起票 / Reviewer Lineage 追加提案 / Routing 提案 / 判断根拠」の 4 項目 block を出力。root-cause-investigation の Phase 4 SMI block と対称構造
  - **`gdd-implementation-gating` Step 2 に State Machine Impact Block 確認を追加**: handoff の SMI block を読み取り、ADR 追記の実在確認 / Reviewer Selection 昇格 / human-check escalation の判定に使う
- **ユーザー導線への反映**（「superpowers でいい」誤判定を直接減らす）:
  - **README.md に「Superpowers と併用するときの使い分け」セクション追加**: GDD primitives と superpowers primitives の設計思想を比較表で示し、使い分け目安を 3 行で明示。`references/superpowers-overlap.md` への導線を README から張る
  - **faq.md に「superpowers と GDD を両方 install している。どう使い分ける？」エントリ追加**: 短答 3 行 + 差別化ポイント 4 件 + overlap map / benchmark-scenarios.md への導線
  - **onboarding.md の「詰まったらどこを見るか」表に superpowers/GDD 迷い行追加**: superpowers-overlap.md への直接導線
- **`gdd-completion-check` に SMI / Impact Block 蓄積記録の確認を追加**（送り側 / 受け側の対称性を完備）:
  - Steps Part A に Step 4b（SMI / Impact Block 蓄積記録の確認）を新設し、build loop で発生した root-cause-investigation Phase 4 SMI と gdd-subagent-driven-implementation Impact Block を worklog.md / adr.md / Implementation Reviewer Selection から収集して AC Drift Check の入力とする手順を明文化
  - 3 項目チェックリスト（ADR 起票要件の充足 / Reviewer Lineage 追加の反映 / Routing 提案との整合）を必須化。未反映なら blocker として `gdd-completion-check` または `gdd-implementation-gating` で停止
- **`lint-ac.py` に RED Evidence の AC ID Binding 機械検証を追加**:
  - `#### RED Evidence` セクションを走査し、`AC:` 行不在を WARN（`--strict` で ERROR 昇格）、架空 AC（requirements.md に存在しない AC ID）参照を ERROR として検出
  - `gdd-test-driven-development` の AC ID Binding 必須ルールを文書ルールから機械検証に格上げ。completion-check の `lint-ac.py` 実行で RED Evidence の AC ID 不整合も同時に検出可能に
- **`gdd-brainstorming` に Value-Based Scope Narrowing を必須化**（広い要件で「勝手に想定せず価値ベースで選択肢提示」を強制）:
  - 自律解決の判断基準に「価値ベースの scope 絞り込み確認（必須）」項目を追加。広い要件検知時は `Design Policy Discussion` に Option A（最小価値）/ Option B（標準価値）/ Option C（やらない / 縮小）の 3 案 + 各 option の期待価値を明示し、scope 選択を human check の独立承認ポイントに並べる
  - Pre-option Scope Narrowing と Value-Based Scope Narrowing の前後関係を明文化（前者が前段、後者が本体、defer 候補は本体冒頭に列挙）
  - Guardrails に「Value-Based Scope Narrowing を省略しない」ルール追加
- **D: 新 reference の cross-link 強化**（recipe 発見率の底上げ）:
  - `common-failure-patterns.md` のパターン 3（Timing 依存）から `condition-based-waiting.md` / `find-polluter.sh` への詳細 recipe 導線追加
  - `common-failure-patterns.md` のパターン 7（Permission denied）から `defense-in-depth.md` § 多層防御モデルへの導線追加
  - `common-failure-patterns.md` の「関連 references」セクションを 2 → 6 件に拡張（`call-stack-tracing.md` / `condition-based-waiting.md` / `defense-in-depth.md` / `find-polluter.sh` を全て列挙）
  - `multi-layer-probing.md` / `call-stack-tracing.md` の「関連 references」に `condition-based-waiting.md` / `defense-in-depth.md` / `find-polluter.sh` を相互参照として追加
  - `condition-based-waiting.md` / `defense-in-depth.md` の「関連」セクションを bidirectional 構造化（逆参照を明示）
  - **Why**: Phase 1 で `common-failure-patterns.md` を参照した subagent が、各パターンに対応する詳細 recipe にすぐ到達できるよう導線を整備。Phase 2 / 3 で「適切な recipe にたどり着くまで」の references descent 回数を削減
  - **empirical-prompt-tuning 検証**: timing pattern / permission pattern / multi-layer probe の 3 シナリオで Iter 1 を回し、全シナリオで [critical] 全 ○ × 100% 精度（B は要件 5 で部分的だが [critical] ではないため成功維持）× retries 0 × **Read 経路 2 read（目標 3 以下）達成 100%**。recipe 発見が pattern 本文 inline / 二重リンク / 関連 references から取れる導線を確認。scope が狭く改修内容も保守的なため 1 iteration で打ち切り。Hold-out Regression Gate: pass（improvement 1 件 / degrade 0、新規追加で hot-fix-skip mode）
- **superpowers 差別化を A/B/C/D の 4 軸で補強**（残り改善点として識別された moat 強化）:
  - **A: 具体 recipe / tool 整備**（root-cause-investigation の補助 reference 拡充）:
    - `scripts/find-polluter.sh`: テスト汚染源（test pollution）を binary search で 1 件特定する shell script（`POLLUTER_TEST_LIST_CMD` / `POLLUTER_TEST_RUN_CMD` で test runner 切り替え可能、既定 pytest）
    - `references/condition-based-waiting.md`: flaky test / timing 依存バグ対策。固定時間 sleep の 5 anti-pattern と decision-tree 形式の決定的待機 recipe
    - `references/defense-in-depth.md`: 同じ root cause が形を変えて再発するケースの 5 層 validation 設計（Boundary / Sanitization / Business rule / Defensive output / Audit）と典型 anti-pattern
  - **C: telemetry 構築**（AI dispatch 不要の deterministic 集計）:
    - `scripts/collect-gdd-telemetry.py`: `.steering/<task>/` 配下の state.md / tasklist.md / worklog.md / learned-patterns.md を走査し、タスク数 / Task Size 分布 / Gate 通過率 / Fix Attempts / Route In Progress 分布 / Entry Intent 分布 / Reviewer Lineage 動的追加件数を text / json / csv で出力
    - `gdd-metrics` SKILL.md: スクリプト連携手順を「推奨: deterministic script を使う」セクションで明示。AI dispatch は数値解釈や次アクション提案が必要な場合のみ
  - **B: Express パス軽量化**（superpowers TDD と同等の「0 ゲート」体験を提供）:
    - **Express Auto-Confirm モード** を `references/task-sizing.md` に追加。`/gdd-dev --auto-confirm` で起動、Express + Direct Intent score ≥ 3 + 1 ファイル ≤ 30 行 + security / route / secret / cron keyword 一切無し + AC 数 ≤ 1 の全条件を満たす場合のみ human-check を省略して即 build に遷移
    - **Safety net**: 実装中に発動条件のいずれかが破られたら即 human-check-waiting にロールバック、impl-gate は通常実行、`learned-patterns.md` に `auto_confirmed: true` 記録
    - `commands/gdd-dev.md` の Task Size 表に Auto-Confirm 行を追加し、利用者向け説明を明示
  - **D: worked examples**（実例での superpowers / GDD 並記）:
    - `references/worked-examples.md`: 単一 commit regression / security boundary 変更 / flaky test 調査 / 機能 amendment / typo 修正 の 5 シナリオで superpowers / GDD 両方の挙動を並記し、差別化ポイントとまとめ表で利用判断材料を提供
    - README.md の Superpowers 使い分けセクションから導線を張る
  - **empirical-prompt-tuning 検証（Auto-Confirm + recipe）**: Express Auto-Confirm pass / fail / condition-based-waiting の 3 シナリオで Iter 1 を回し、Iter 1 で発見した 2 件の構造的不明瞭点（条件 6 影響範囲 scan の実行方法 / Auto-Confirm 辞退時の state.md 記録形式）を Iter 2 で明文化（`git grep -l <symbol>` 手順 + 4 field 必須記録形式）。Iter 2 再評価で fail case が 100% 精度 × 構造的不明瞭点 0 で収束。Hold-out Regression Gate: pass（improvement 1 件 / degrade 0、新規追加で hot-fix-skip mode）
  - **empirical-prompt-tuning 検証（defense-in-depth + find-polluter + Reviewer Lineage Patterns capture）**: 3 シナリオで Iter 1 を回し、Iter 1 で発見した 2 件の構造的不明瞭点（`added_by` field の lineage_pattern / task-breakdown allowed values 未定義 / terraform checklist reviewer 正式 key 名未定義）+ tool_uses 偏り（Scenario C で 6x）を Iter 2 で明文化:
    - `post-completion-learning.md` に `added_by` allowed values 4 値（`task-breakdown` / `lineage_pattern` / `smi_block` / `impact_block`）と capture 対象（smi/impact のみ）を明示
    - Reviewer 種別の正式 key 名（`gdd-implementation-reviewer` / `gdd-security-reviewer` / `gdd-terraform-checklist-reviewer`）を明示
    - `gdd-task-breakdown` Step 6a に `added_by: lineage_pattern` + `source_pattern` の必須記録を追加
    - `find-polluter.sh` docstring に exit code 表（0/1/2/3）追加、`--ordered` 文言を pytest 中立に
    - Iter 2 再評価で 100% 精度 × 構造的不明瞭点 0、tool_uses 6→4 に削減。Hold-out Regression Gate: pass
- **Reviewer Lineage trace + learned-patterns 自動 capture**（SMI / Impact Block の reviewer 追加履歴を次回 task で事前追加に進化させる Learning Loop）:
  - **`added_by` marker 追加**: SMI block / Impact Block で追加した reviewer entry に `added_by: smi_block | impact_block` と `source_signal: <原因要約>` を必須記録する形式を `gdd-systematic-debugging` § SMI Block Handoff (Step 2) と `gdd-subagent-driven-implementation` § Spec Change Detection (Reviewer Lineage 影響判定) に追加
  - **`Reviewer Lineage Patterns` セクション新設**: `references/post-completion-learning.md` に Step 5 を追加し、`Implementation Reviewer Selection` から `added_by: smi_block | impact_block` の entry を抽出して task signature 別に集約する手順と format を明文化。`task_signature` / `added_reviewer` / `trigger_source` / `source_signal` / `outcome` / `次回適用ヒント` / `記録日` / `起源 task` の 8 field
  - **task-breakdown で事前参照**: `gdd-task-breakdown` § Steps に Step 6a「Reviewer Lineage Patterns 参照（推奨）」を追加。`次回適用ヒント=強い推奨`（3 回以上記録済み）の pattern は **必ず** 初期枠に含める。`references/task-breakdown-steps.md` Step 6a も対応追加（drift check pass）
  - **lifecycle**: `references/cross-task-learning.md` の learned-patterns.md 書き込み内容を 3 種類 → 5 種類（Migration Patterns + Reviewer Lineage Patterns 追加）に拡張、Reviewer Lineage Patterns 反映ルールを明記
  - **影響範囲**: `skills/gdd-systematic-debugging` / `skills/gdd-subagent-driven-implementation`（記録形式例追加）/ `skills/gdd-task-breakdown`（Step 6a 追加）/ `skills/gdd-completion-check`（Post-Completion Learning 説明拡張）/ `references/post-completion-learning.md`（Step 5 + Reviewer Lineage Patterns format）/ `references/cross-task-learning.md`（書き込み内容拡張）/ `references/task-breakdown-steps.md`（Step 6a）
- **Cursor / Codex light tier 格上げ**（mini の取りこぼし対策）: `light` tier を `GPT-5.4 mini` + `high` から `GPT-5.4` + `medium` に格上げ。task-breakdown / TDD / pr-review / pre-workflow-brainstorming / test-failure-debug-pack / receiving-code-review / requesting-code-review の 7 skill が対象
  - 対策理由: mini では task 分割や RED Evidence の品質取りこぼしが発生していた
  - `leaf` tier（status / metrics / using-git-worktrees）は `GPT-5.4 mini` + `high` のまま（admin task で mini で十分）
  - コスト影響: light tier は約 3.3 倍の単価増だが effort=medium で実トークン約 70% に抑制、ネット約 2 倍。leaf は据え置きで影響なし
  - 影響範囲: `scripts/resolve-gdd-model.py`（cursor / codex `light`: `gpt-5.4-mini` → `gpt-5.4`）/ `tests/validate-plugin.sh`（light test cases）/ `references/cursor.md` / `references/codex.md` / `references/fixed-models.md` / `skills/gdd-model-routing/SKILL.md`（起動時固定表 + 共通 section）/ 7 個別 SKILL.md（pre-workflow-brainstorming / task-breakdown / test-driven-development / pr-review 等）
- **Cursor / Codex モデル再見直し（GPT-5.5 + effort 差別化体系へ移行）**: 既存の「`GPT-5.4` + `high` 基本 + 5 skill だけ `GPT-5.5` + `high`」体系を、「`GPT-5.5` ベース + effort で差別化」体系に再構築:
  - **heavy tier 既定を `GPT-5.4` → `GPT-5.5` に変更**: `scripts/resolve-gdd-model.py` の `TIER_TO_MODEL["cursor"]["heavy"]` / `TIER_TO_MODEL["codex"]["heavy"]` を更新
  - **PHASE_MODEL_OVERRIDE を削除**: heavy 既定が `gpt-5.5` になったため、formal gate を `gpt-5.5` に上書きする override が不要に
  - **effort 差別化**: 一般 heavy（debug / refactor / advisory review / implementation）は `effort=low`、formal gate（brainstorming / requirements / design / impl / completion）は `effort=medium`、leaf / light は `GPT-5.4 mini` + `high` を維持
  - **判断根拠**: Expert-SWE +4.6pp / Terminal-Bench 2.0 +7.6pp / MRCR v2 (1M context) +37.4pp の能力優位。long-context agent task で GPT-5.5 は約 40% 少ないトークンで完了するため、実効コストが GPT-5.4 + high と拮抗〜逆転。短プロンプト（2K 以下）では GPT-5.5 のコスト増が顕著（+92%）なので leaf / light は GPT-5.4 mini を維持
  - **出典**: OpenAI 公式（[GPT-5.5 introducing](https://openai.com/index/introducing-gpt-5-5/) / [Codex models](https://developers.openai.com/codex/models)）、サードパーティ比較（[llm-stats.com GPT-5.5 vs 5.4](https://llm-stats.com/blog/research/gpt-5-5-vs-gpt-5-4)、[OpenRouter コスト分析](https://openrouter.ai/announcements/gpt55-cost-analysis)）
  - **影響範囲**: `scripts/resolve-gdd-model.py` / `tests/validate-plugin.sh`（resolver test cases 全体）/ `references/cursor.md` / `references/codex.md` / `references/fixed-models.md`（heavy tier 表 + Cursor / Codex 列）/ `skills/gdd-model-routing/SKILL.md`（起動時固定表 + 初稿レビュー + 判断の書き方）/ `skills/gdd-brainstorming/SKILL.md` / `skills/gdd-refactor-planning/SKILL.md` / `skills/gdd-requirements-amendment/SKILL.md` / `skills/gdd-systematic-debugging/SKILL.md`
- **empirical-prompt-tuning 検証（追加 3 件）**: Value-Based Scope Narrowing / completion-check Step 4b / lint-ac.py RED Evidence について 3 シナリオ × 2 iteration で並列 subagent eval を実施
  - Iter 1: A ○ 100% / B × 92%（合成 routing ルール未明文化で要件 3 が部分的）/ C ○ 100%
  - Iter 1 → Iter 2 修正: completion-check Step 4b に「複数 blocker 同時発生時の合成 `Next Action` ルール」（優先順位 1-4 + 上流優先理由）を明文化、brainstorming の Pre-option / Value-Based の前後関係を明示、lint-ac.py の line N 出力に「`#### RED Evidence` 見出し行」を明示
  - Iter 2: A ○ 100% / B ○ 100% / C ○ 100%、retries 0 × 3、構造的不明瞭点 0 で収束
  - Hold-out Regression Gate: pass（improvement 1 件: Scenario B の構造問題 fix、degrade 0）


  - **Phase 1 に Early Exit Criteria を追加**: git history だけで主因 commit が一意に特定でき、再現性が deterministic で、single-component の場合は Step 4（境界証跡）以降を skip して Phase 2 へ移行可。CloudWatch / Terraform / 監査ログでコストを浪費しない判断基準
  - **Phase 1 Early Exit 節を補強**（Iter 2）: Phase 2 / Phase 3 を「簡略化または skip して Phase 4 へ直行」を明示。条件 1 を operational 表現（`git log -S` 結果 1 件 / 2 件以下 + 直近変更で確定）に
  - **Phase 4 出力構造を「最優先 1 + 副次 N + 副次的発見」に再編**: top 1 アクションを明示し、副次対応項目を分離。本論と独立した「副次的発見」セクション（bot 文言不整合 / IaC drift / 文書食い違い等）を追加し、後続タスクに引き継げる形に
  - **Phase 4 テンプレートを root cause 確定 / 未確定の両ケース対応に拡張**（Iter 3）: 確定時は fix 実装、未確定時は追加データ収集を最優先に。意思決定 question も「修正 vs メモのみ」/「データ収集 vs 運用回避」の 2 系統を提供。flaky / 探索的調査での運用が明確化
  - **意思決定の question を必須化**: 「修正に着手しますか? それとも調査メモのみで止めますか?」のような明示的な質問で締め、ユーザーの next step 判断を促す（superpowers パターン取り込み）
  - **一次原因と増悪要因の分離**: 多層的に発生した問題を「一次原因 1 つ」+「増悪要因 N 件」に分けて出力する構造に
  - **検証**: empirical-prompt-tuning で 3 iteration、3 シナリオ（単一 commit regression / multi-layer secret 伝播 / flaky test）すべて精度 100% × 3 連続、retries 0、tool_uses 1（自己完結）を確認
- **要件整理・初稿を GPT-5.5 限定使用に追加**: `gdd-brainstorming` と `gdd-requirements-gating`（brainstorming と同一 subagent で完走するため）を `PHASE_MODEL_OVERRIDE` に追加。GPT-5.5 限定使用 skill が 5 つに（brainstorming / requirements-gating / design-gating / impl-gating / completion-check）
- **Codex 環境のサポートを追加**:
  - `references/codex.md` 新規作成（Cursor と同じ GPT-5.4 / GPT-5.5 体系を採用）
  - **Codex の Dialectic Counter は Anthropic 不可のため別世代 GPT + reviewer prompt role**（Primary が `GPT-5.4` なら Counter は `GPT-5.5`、その逆も。Codex CLI は OpenAI 専用のため Cursor のような `Opus 4.7` Counter は使えない）
  - `scripts/resolve-gdd-model.py` の `--runtime` に `codex` を追加、`TIER_TO_MODEL["codex"]` と `PHASE_MODEL_OVERRIDE["codex"]` を Cursor と同じ mapping で実装（実装は `GPT-5.4` で代用、Composer 2 不在）
  - `gdd-model-routing/SKILL.md` の Dialectic Review role table と起動時固定表に Codex 列を追加（Counter は GPT prompt role 切替に明示）
  - `tests/validate-plugin.sh` に codex runtime の test cases を追加
- **Cursor model 設定の再調整**（ユーザー希望に基づく追加調整）:
  - **GPT-5.4 系の `reasoning.effort` を `high` 統一**（`xhigh` 廃止）。全 skill で同一 effort 値に
  - **`gdd-implementation-gating` を GPT-5.5 限定使用に追加**: `PHASE_MODEL_OVERRIDE` に追加し、design / impl / completion の 3 formal gate が GPT-5.5 を使う構成に
  - **leaf task を `GPT-5.4 nano` + `none` → `GPT-5.4 mini` + `high` に格上げ**: `GPT-5.4 nano` は推論力不足のため廃止。leaf も light も `GPT-5.4 mini` + `high` で統一
  - test: implementation-gating の phase_override test case を追加、leaf test の expected を `gpt-5.4-nano` → `gpt-5.4-mini` に更新
- **Cursor model 設定をコスト最適化方針に再構成**（CSV 使用実績ベース）:
  - **`GPT-5.4` 系列を heavy tier の基本**にする（cursor.heavy = `gpt-5.4`）。`GPT-5.5` は detailed design / 最終 gate に限定使用
  - `PHASE_MODEL_OVERRIDE` を `scripts/resolve-gdd-model.py` に追加: `gdd-design-gating` と `gdd-completion-check` だけ `gpt-5.5` を返す phase 別 override 機構
  - **Dialectic Review の Counter evaluator を `Opus 4.7` + `reasoning.effort=high` に固定**: Primary（GPT 系）と異なる model 系統で cross-system 観点を確保。Anthropic 側で `xhigh` は使わない
  - `reasoning.effort=xhigh` は GPT-5.4 系の難所判断に限定。Pre-workflow brainstorming は `mini + high` に降格
  - `composer-2-fast` 不使用ルールを明示（`composer-2` を実装の標準）
  - 影響範囲: `references/cursor.md` / `references/cursor-guide.md` / `references/fixed-models.md` / `skills/gdd-model-routing/SKILL.md` / `gdd-brainstorming` / `gdd-implementation-gating` / `gdd-pre-workflow-brainstorming` / `gdd-requirements-amendment` / `gdd-refactor-planning` / `gdd-systematic-debugging` の SKILL.md、`scripts/resolve-gdd-model.py`、`tests/validate-plugin.sh` の resolver test cases
- **発展系改善 5 件を追加実装**（lint 自動化 + 機械可読 schema + slim 化 + lineage lint）:
  - **`validate-steering-write.py` の advisory lint 統合**: state.md / requirements.md / tasklist.md write 時に `lint-approved-direction.py` / `lint-ac.py` を自動実行し、warning を systemMessage として通知（既存 deny ロジックは不変、allow 維持）
  - **`tests/validate-plugin.sh` に lint test 拡張**: 新規 reference 9 件・script 4 件の存在 check、Python lint scripts の `py_compile` syntax check、shell scripts の `bash -n` 構文 check、各 lint script の basic smoke test を `BLOCK: lint-scripts-syntax` / `BLOCK: lint-scripts-functional` として追加
  - **`gdd-completion-check` の Part D / Post-Completion Learning slim 化**: `references/uat-checklist.md` と `references/post-completion-learning.md` に切り出し、completion-check 本体を 376 → 344 行に slim 化
  - **`references/ac-machine-readable-schema.md` 新規追加**: AC を optional な YAML frontmatter で機械可読化する schema（`category` / `severity` / `boundary` / `verification_hint` / `grep_patterns` 等のメタデータ）。markdown bullet 形式と並行サポート、両方ある場合は YAML が正本。`lint-ac.py` が YAML を優先抽出する形に拡張
  - **`scripts/lint-reviewer-lineage.py` 新規追加**: `reviewer-lineage.md` の bias warning / repeated changes_requested / long chain without rotation を機械的に検出。3 種の WARN（fail-closed しない判断材料）を提供。`entry-intent.md` の Supersede Handling Step 5 から呼び出し
- **強化候補 4 件を実装**（差別化要因の深掘り分析から派生）:
  - `scripts/lint-approved-direction.py`: Approved Direction の glob pattern 自動検査。単一ファイル固定 glob (`src/foo.ts` 等) を ERROR、全域 glob × security-sensitive marker 交差を WARN として検出。`gdd-systematic-debugging` Routing Decision Tree Step 3c で `design_detail_only` 判定前の必須 lint として呼び出す
  - `scripts/find-stale-steerings.sh`: 10 日超の brainstorming-only steering を一覧化し archive / discard / resume コマンドを提案する read-only helper。auto delete は禁止（別 runtime 作業中の可能性配慮）。`gdd-using-git-worktrees` から参照、`docs/TROUBLESHOOTING.md` にも案内追加
  - `scripts/lint-ac.py`: requirements.md の AC 定義と tasklist.md の `method=ac:<id>` 参照を双方向で照合。orphan 参照 / 重複定義は ERROR、未 verify AC は WARN。`gdd-ac-verification` Schema Validation と `gdd-completion-check` Part B Step 5 から呼び出し
  - `references/reviewer-lineage.md`: 同一 root feature 系統（supersede / hotfix / amendment）での cross-steering reviewer 判定履歴を optional な `Reviewer Lineage` section に記録する仕様。Tier 3 (Audit) field として `state-field-tiers.md` に追加。自動継承はせず判断材料として参照
- **Gate Skill 共通 reference 4 件を新規追加**（4 gate skill の重複削減と SSOT 化）:
  - `references/fixed-models.md`: 4 gate skill が固定使用するモデル定義の唯一の正本。各 skill の Fixed Model section を 1 行参照に slim 化
  - `references/phase-gate-prechecks.md`: 各 gate skill が開始前に実行する Pre-check 手順テンプレート（Template A: 3-Gate Approval Required / Template B: Task-Size Aware Skip）。impl-gate / completion-check / task-breakdown / TDD / subagent-driven の 5 skill が参照
  - `references/e2e-verification-catalog.md`: Output Consistency / Delivery Channel Rendering / Multi-Run Comparison の検証パターン正本。design-gating / impl-gating / completion-check の 3 skill が phase 別役割で参照
  - `references/gate-checklists.md`: completion-check で実行される checklist 群（AC Drift Check / Stub Detection / External Dependency Completeness / Skill Document Quality）の独立正本
- **`references/state-field-tiers.md`** を新規追加（前回 release）。state.md の 13+ field を Core / Phase-Specific / Audit の 3 Tier に分類し、phase 別 Minimum Required Set と Lightweight Template を提供
- **`references/parallel-failure-investigation.md`** を新規追加（前回 release）。root cause 未確定で hypothesis 2-4 件あるときの failure-domain 並列調査パターン。superpowers `dispatching-parallel-agents` 相当を reference 化

#### Changed

- **empirical-prompt-tuning による superpowers import の route 境界 polish**:
  - 4 シナリオ（implementation-gating / test-driven-development / subagent-driven-implementation / writing-skills）で subagent eval を実施し、全 critical 要件が pass
  - `gdd-implementation-gating` に `Stage A Failure Route Hint` を追加し、Spec Compliance fail 時の `implementation_fix_only` / `design_detail_only` / `human_recheck_required` / `planning_rework_required` hint 境界を明文化
  - `gdd-test-driven-development` に `Quarantine Output Contract` を追加し、RED なし既存実装検出時の `do not mark GREEN` / AC・Planned RED binding / route 分岐 / `Phase: build` と `TDD:RED` の表記境界を明文化
  - `tests/test_superpowers_method_import_contract.py` に上記 route hint / quarantine contract の regression assertion を追加
- **superpowers 追加取り込み 1-5 を GDD contract 化**:
  - `gdd-writing-skills` に `Description Discovery Discipline（CSO）` を追加し、description の workflow summary shortcut 防止 / Phase Gate 例外 / description-body alignment / trigger collision scan を明文化
  - `gdd-brainstorming` に `Subsystem Decomposition Gate` を追加し、独立 subsystem を単一 steering に押し込まず separate steering / phased single steering / first subsystem only を human check に出す
  - `gdd-task-breakdown` に `Subsystem Boundary Check` と `Plan Self-Review Contract` を追加し、deferred units の task 化防止、Spec coverage / No Placeholders / Type consistency / granularity の自己点検を必須化
  - `gdd-refactor-planning` と `gdd-requesting-code-review` に `Before Refactor Baseline Review` / `Refactor Baseline Review Packet` / `REASON=before-refactor-baseline` を追加し、large / sensitive refactor 前の baseline review を扱えるようにした
  - `gdd-writing-skills` に `Skill Slimming Discipline` を追加し、frequently-loaded skill の reference 化と安全境界の本文保持を両立する方針を明文化
- **4 gate skill の重複セクションを reference 参照形に slim 化**（後方互換 100%、skill 名・state field・Resume From 値はすべて不変）:
  - 各 skill の `## Fixed Model` を 1 行参照に変更（合計 -12 行）
  - `gdd-implementation-gating` / `gdd-completion-check` / `gdd-task-breakdown` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` の `## Phase Gate Pre-check` を Template 参照に変更（合計 -50 行程度）
  - `gdd-design-gating` Step 5b（Delivery Channel Rendering Check）/ `gdd-implementation-gating` Step 1a（Output Consistency Check）/ `gdd-completion-check` Part A-2（Multi-Run Comparison）を E2E catalog 参照に変更（合計 -25 行程度）
  - `gdd-completion-check` Step 5a (AC Drift Check) / 9b (Stub Detection) / 9c (External Dependency) / 9d (Skill Quality) を gate-checklists.md 参照に変更（合計 -50 行程度）
- **`references/entry-intent.md`** の ambiguous 条件を整理（前回 release）。`Default-to-New` Lightweight Path を追加し、candidate 0 件時は fail-closed せず `new` default + revert option として進める。fail-closed 条件を明示的な必要ケースのみに限定
- **`references/gate-status-schema.md`** と **`references/state-machine.md`** に `state-field-tiers.md` への cross-reference を追加（前回 release）
- **`docs/TROUBLESHOOTING.md`** の required field 欠落セクションを Tier 認識ベースに更新（前回 release）

#### Fixed

- **モデルルーティング文書の drift を修正**:
  - 個別 gate skill の Fixed Model 記述を `references/fixed-models.md` と同期し、Cursor / Codex formal gate を `GPT-5.5 + reasoning.effort=medium` に統一
  - `skills/gdd-model-routing/references/cursor.md` の旧方針（`xhigh` / `GPT-5.4 nano` / `effort=none`）を削除し、現行正本に同期
  - README / `references/cursor-guide.md` / `references/cursor.md` / `references/codex.md` に risk escalation と現行 effort 方針を反映
- **`gdd-systematic-debugging` の skill サジェスト改善**: frontmatter description に「GDD systematic debug」「デバッグ中の設計判断」「route 判定」系の trigger phrase を追加。state machine router としての責務は維持しつつ、ユーザーが明示的に GDD debug routing を求めた場合に候補へ出やすくした。
- **Cross-runtime guard の根本対策**（前回 release）: `scripts/setup-gdd-loop.sh` のランタイム検出を `CLAUDE_CODE_SESSION_ID` 単独判定からプロセスツリー検出に変更。Cursor が継承した env-var による誤検知（Cursor 起動の GDD が Claude Code stop hook を誤発火させる事故）を構造的に解消

#### Breaking Contract Changes

なし。skill 名 / Resume From 値 / Next Action 値 / state.md field 名 はすべて不変。既存 active steering との互換性 100%。

#### User Action Required

なし。プラグイン更新後、既存の active steering はそのまま resume できる。新規 steering（特に Express / trivial）から `state-field-tiers.md` の Lightweight Template を採用可能。

#### Validation / Eval Impact

- `tests/validate-plugin.sh` の `BLOCK: docs-links-valid` で新規 reference 5 件（fixed-models / phase-gate-prechecks / e2e-verification-catalog / gate-checklists / state-field-tiers / parallel-failure-investigation）の実在チェックが追加対象
- `evals/evals.json` の test case は skill 名・Resume From 値が不変のため修正不要

- **Dialectic Review Lane** を追加。prompt / skill / review policy / 人間向け出力 / severity calibration など、採否や表示品質が揺れやすい変更で、Primary / Counter / Cross-review / Revision / Final synthesis の補助 lane を使えるようにした（`references/dialectic-review.md`）
- `gdd-design-gating` / `gdd-completion-check` / `gdd-pr-review` に dialectic review の trigger、evidence check、PR review metadata への反映ルールを追加
- `gdd-model-routing` に host 非依存の dialectic role assignment を追加。Claude Code / Cursor / Codex へ展開するときも model 名ではなく役割を維持する
- **`CONTRIBUTING.md`**（plugin 内部開発者向け）を新規追加。変更の種類別の出発点・必須チェック・skill/agent/hook/docs 改修時の詳細手順・テスト方針・レビュー観点・禁止事項・リリース手順を 1 ファイルに集約。plugin に PR を送る前の前提を明確化
- **`docs/VERSIONING.md`** を新規追加。v0.x → v1.0 昇格基準（機能成熟度・品質・文書・利用実績の 4 軸）、Breaking Change 分類（契約レベル / スキーマレベル / 利用者体験レベル）、SemVer 適用ルール、バージョン判定フローチャートを定義
- **`docs/SUPERPOWERS_COEXISTENCE.md`** を新規追加。両 plugin 有効時の使い分け、skill 重複対応表、判定フロー、auto-trigger 衝突の扱い、設定パターン別の推奨を明文化。既存 SessionStart hook の superpowers 検出ロジックと整合
- **`docs/METRICS_BASELINE.md`** を新規追加。`gdd-metrics` で収集した数値の「健全 / 要注意 / 危険」のしきい値、Core KPI（完了率・gate 通過率・差し戻し回数・Task Size 分布 / Human Check 差し戻し率）、Secondary KPI（Learning Loop / Blocked 率 / 自走率）、時系列期待傾向、赤信号条件、チーム内運用リズムを定義
- **validate-plugin.sh に `BLOCK: docs-links-valid` を追加**。`docs/*.md` が参照する `references/<name>.md` および `docs/<name>.md` の実在を検査し、他チーム向けドキュメントと plugin 内部正本の間の drift を構造的に防止
- **他チーム導入向け docs/ ドキュメント群** を新規追加。plugin 内部の正本（`references/`）とは別に、他チーム展開時の読み物を `docs/` に集約した 4 ファイル:
  - `docs/ONBOARDING.md`: 30 分で `/gdd-dev` 1 サイクルを完走できる段階的導入シナリオ。前提条件チェック・Plugin 有効化・CLAUDE.md 整備・自己検証・初回サイクル・中断再開・撤去手順を 7 ステップで提示
  - `docs/TROUBLESHOOTING.md`: 停止パターン別 FAQ（起動初期化 / human check / 自動実行 / reviewer loop / state 不整合 / worktree / hook / superpowers 併存）と復帰コマンド早見表
  - `docs/PROJECT_CLAUDE_MD_TEMPLATE.md`: 導入プロジェクトの `CLAUDE.md` 雛形。必須項目 4 つ（GDD 導線 / Operational Safety / Secrets 保護 / ブランチ PR）と推奨フルセット（会話ガイド / 設計原則 / 社内ドキュメント連携 / plugin 共存 / 監査）
  - `docs/SECURITY.md`: セキュリティ境界の明示。skill / reviewer / subagent / hook それぞれの読み取り・書き込み・通信範囲、Trusted/Untrusted 境界、脅威モデル（prompt injection / secrets 漏洩 / phase-skip 迂回 / 破壊的操作暴走 / race condition）、監査証跡、Honest Limitations を体系化
- `README.md` に `docs/` への導線セクション「他チーム導入向けドキュメント」を追加
- **Implementation Guidance** を追加。`gdd-subagent-driven-implementation` がコードを書く前に CLAUDE.md、変更対象の既存コードパターン、`learned-patterns.md` を参照し、プロジェクトの規約に合わせた実装を行う（Step 1a）。reviewer 差し戻しを減らし「良い感じに実装してくれた」体験を実現する
- **Direct Intent Shortcut** を追加。brainstorming でユーザー入力が十分具体的な場合（変更対象・アクション明示、代替案不要）に Options Exploration と Iterative Refinement Loop を skip/短縮する。自明なタスクの brainstorming 時間を大幅短縮（`references/brainstorming-steps.md` § 7b）
- **Cross-Task Learning** を追加。`gdd-completion-check` が `done` 時に採用パターン・却下案・発見した規約を `.steering/learned-patterns.md` に蓄積し、次の brainstorming と implementation で参照する（`references/cross-task-learning.md`）
- **Reviewer Calibration** を追加。`gdd-implementation-gating` が差し戻し→修正→再通過のサイクルで指摘の正当性を `tasklist.md` の Attempts に記録する。false positive の多いパターンを learned-patterns に蓄積し、同プロジェクトの将来レビューで参考にする（`references/inline-review-checklists.md` § Reviewer Calibration）
- **Progress Visibility** を追加。Stop hook が systemMessage に現在フェーズ名とタスク進捗（N/M done, current task name）を自動注入する。自律実行中もユーザーが進捗を把握できる
- **Smart Session Recovery** を追加。Stop hook が phase 遷移時に assistant 出力から Context Handoff Summary を抽出し、`state.md` の `Last Handoff Summary` に永続化する。SessionStart hook が session 再開時にこの値を Quick Reboot context に注入し、前セッションの最終決定事項を即座に復元する
- **Hook-enforced Context Budget** を追加。Stop hook が phase 遷移（`<gdd-phase>` マーカーの変化）を検出した際に Handoff Summary が出力に含まれていなければ `systemMessage` で警告を注入する。Context Budget を「ルール」から「構造的保証」に昇格
- **Multi-task Parallel Execution** を追加。`gdd-task-breakdown` でタスク間の依存関係を `Depends on:` フィールドで明示し、依存グラフから並列実行可能なバッチを構成する。`gdd-subagent-driven-implementation` がバッチ内の独立タスクを subagent で並列実行する。standard タスク（タスク数 3+）のみ有効
- `state.md` に `Last Handoff Summary` フィールドを追加。routing source にはしない
- `tasklist.md` に `## Execution Plan` セクション（optional）と各タスクの `Depends on:` フィールドを追加
- **Express Path**（`quick (express)`）を追加。1-2 ファイル・方針明白・AC 1-3 個の quick タスク向け最短経路。brainstorming → human check → TDD → 実装 → impl-gate → done。req-gate / design-gate / task-breakdown / completion-check を省略し、design.md / tasklist.md も不要。`/gdd-dev --express <task>` で明示指定可能
- Express テンプレートを `references/requirements-template.md` に追加。目的 + 変更内容 + AC + 承認ポイント（1-3件）の軽量構成
- Express フロー定義を `references/phase-progression.md` に追加
- Express 状態遷移を `references/state-machine.md` に追加
- Express 昇格条件を `references/task-sizing.md` に追加。変更ファイル 3+、AC 4+、security boundary 影響で quick (standard) に自動昇格
- Express 進捗バーを `references/output-format.md` に追加
- `--express` 引数を `references/entry-intent.md` に追加。intent 判定には影響せず sizing のみに適用
- **Graduated Autonomy** を追加。requirements.md の内容を 5 次元（Scope Breadth / AC Complexity / Integration Depth / Safety Surface / Uncertainty）で評価し、ceremony レベルを自動選択する（`references/graduated-autonomy.md`）。sizing の最終決定を「要件を書く前の推測」から「要件を書いた後の評価」に移動
- brainstorming Step 12a に Complexity Evaluation を追加。requirements 初稿の後に複雑さを評価し、暫定 sizing と比較して昇格を提案する
- **Context Budget Management** を追加。phase ごとの必要情報を定義し、context 圧縮後の品質低下を構造的に防ぐ
- `references/context-budget.md` を新規作成。Phase Context Manifest（phase ごとの必須/推奨/不要情報）を定義
- Context Handoff Summary を `references/output-format.md` に追加。phase 遷移時に前 phase の決定事項を 10 行以下で圧縮して引き継ぐ
- `Approved Direction`（方向性承認）を追加。human check 承認時に方向性・自走範囲・人間に戻す条件を `state.md` に記録する。E2E で発見された問題は自走範囲内なら human check に戻さず AI が自律判断する
- `E2E Discovery Loop`（E2E 発見ループ）を `references/phase-progression.md` に追加。自走条件（AC を壊さない・方向性と矛盾しない・セキュリティ要件の新規発生でない・AC の根本追加削除でない）をすべて満たす場合、`design_detail_only` で reviewer は通すが human check には戻さない
- `Scope Drift Guard` を `references/phase-progression.md` に追加。同一 steering 内で `design_detail_only` が 3 回を超えた場合、または累積変更ファイル数が初期スキャンの 3 倍を超えた場合に方向性との整合を再確認する
- `gdd-brainstorming` に Problem Discovery（Step 9）と Options Exploration（Step 10）を追加。既存コード・環境の具体的事実を確認し、候補案を比較してから承認ポイントに落とす
- `承認ポイント` に **背景**（なぜこの判断が必要か）と **変更前 → 変更後**（何がどう変わるか）の構造を追加。人間がコンテキストを遡らずに判断できるようにする
- `承認ポイント` の末尾に **方向性承認** カテゴリを追加。AI の自走範囲を human check 時に事前合意する
- **合理化防止テーブル（Rationalization Prevention）** を追加。GDD のルールを省略・簡略化したくなったときの 12 の「合理化パターン」と、それぞれの「現実」を左右対照で掲載（`references/common-guardrails.md`）。superpowers の Rationalization Tables 相当の仕組みを GDD にも導入
- `gdd-dev.md` の冒頭に **「30 秒で分かる GDD（人間向けメンタルモデル）」** セクションを追加。人間が覚える必要があるのは「伝える / 承認する / 待つ」の 3 ステップだけであることを明示し、20 skill / 31 reference / 4 reviewer agent / 4 hook は AI が参照する裏側であることを宣言。学習コストの心理的障壁を下げる
- Hook エラーメッセージに **教育的な「なぜ」説明** を追加。違反カテゴリごとに「なぜこのルールが存在するか」を 1-2 行で併記し、AI が次回以降に同じパターンを避けられるようにする
  - `hooks/scripts/validate-steering-write.py`: `.steering/` への email / 絶対パス / プレースホルダー書き込み時、`WHY_EXPLANATIONS` 辞書からカテゴリ別の理由を `systemMessage` に追記
  - `hooks/scripts/run-gdd-stop-hook.sh`: done guard 違反時に「未完了タスク / Verification 欠損 / Route In Progress 残存」の各カテゴリで「なぜこの guard が存在するか」を block 理由に追記
  - `hooks/scripts/run-block-plan-mode-hook.sh`: `/gdd-dev` session 中の EnterPlanMode ブロック時に「なぜ Plan mode と GDD を併用できないか」「どうすればよいか」「参照先」を block 理由に含める
- **8 skill に固有の Rationalization Check テーブル** を追加。superpowers の per-skill Rationalization Tables 相当。skill を省略・短絡したくなる思考パターンを skill ごとに 4-6 件列挙し、それぞれの「現実」で反論する
  - 対象: `gdd-test-driven-development` / `gdd-requirements-gating` / `gdd-systematic-debugging` / `gdd-brainstorming` / `gdd-implementation-gating` / `gdd-completion-check` / `gdd-task-breakdown` / `gdd-subagent-driven-implementation`
  - 共通の rationalization 防止は `references/common-guardrails.md` § 合理化防止テーブル、skill 固有の誘惑は各 SKILL.md の `## Rationalization Check（この skill 固有）` に置く
- **Scope Reduction Check** を追加。`references/brainstorming-steps.md` Step 9 (Problem Discovery) 終盤で「要件全体が本当に必要か、部分だけで済まないか」を AI が 1 回だけ内部検討する。縮小案は Options Exploration の Approach C として候補に含め、最終判断は human check に委ねる。過剰な scope のまま設計に入る手戻りを防ぐ（自律継続を維持するため mid-flow でユーザーに質問しない設計）
- **アプローチ比較の必須フォーマット** を追加。`references/brainstorming-steps.md` Step 10 (Options Exploration) で standard タスクに対し A/B/C 3 案 + 各案のメリット/デメリット + 単一の推奨案（理由付き）を強制。推奨案を 1 つに絞ることで人間の判断を「AI の提案を受け入れるか / 別案を指示するか」の 2 択に単純化する
- **Honest Limitations セクション** を追加。`references/requirements-template.md` の承認ポイント直後に `### Honest Limitations` を置き、この設計で確認できないこと / 担保できない部分を率直に列挙する。AI が「できることだけ」を提示する偏りを防ぎ、人間が scope reduction と後工程 E2E 計画を先に判断できるようにする（`references/common-guardrails.md` § Honest Limitations にも guardrail を追加）
- **Testing Anti-Patterns リファレンス** を追加（`references/testing-anti-patterns.md`）。superpowers v5.0.7 の testing-anti-patterns 相当。mock の振る舞いテスト / production class へのテスト専用メソッド追加 / 依存を理解しない mock / partial mock / テストの後付けの 5 禁止パターンを、Iron Laws・Gate Function・Quick Reference 付きで定義。`gdd-test-driven-development` Guardrails（RED 品質基準）、`gdd-subagent-driven-implementation` Step 1a（実装時の mock 設計指針）、`gdd-implementation-gating` のテスト品質 checklist（`references/inline-review-checklists.md`）から参照
- **Verification Before Completion リファレンス** を追加（`references/verification-before-completion.md`）。superpowers v5.0.7 の verification-before-completion 相当。Iron Law（NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE）、5 ステップの Gate Function（IDENTIFY → RUN → READ → VERIFY → CLAIM）、Common Failures 対応表、Rationalization Prevention、GDD 文脈での適用（Fresh Verification / 完了宣言の言語制限 / subagent 報告の独立検証 / Before-After 確認）を集約。`gdd-completion-check`（AC verification / done 判定）、`gdd-implementation-gating`（reviewer approval 前の evidence 確認）、`gdd-subagent-driven-implementation`（subagent 完了報告の独立検証）から参照
- **Implementer Status Handling（4 値 status）** を `gdd-subagent-driven-implementation` に追加。subagent は `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` のいずれかで報告し、controller は status ごとの処理を行う（同じモデルでの blind retry 禁止、BLOCKED 時は原因を分類して context 追加 / より capable なモデル / task 分割 / plan 差し戻しを選ぶ）。superpowers v5.0.7 の `subagent-driven-development` で実証されたパターン
- **Step Granularity ガイド** を `gdd-task-breakdown` に追加（`references/task-breakdown-steps.md` § Step Granularity）。task 内の 1 step を 1 action（2-5 分で完了）に切る。「実装してテストする」のような複合 step の禁止。failure point を明確化
- **No Placeholders パターン詳細** を `references/task-breakdown-steps.md` に追加。言い訳パターン（`TBD` / `TODO` / 「適切に」等）、コピペ回避パターン（「Task N と同様」）、抽象化逃避パターン（コード片なし）、未定義参照の 4 カテゴリで列挙。Task Self-Review の placeholder scan 項目で grep 対象として使用
- **Post-Completion 4 Options Flow** を `gdd-completion-check` に追加。`Next Action=done` 確定後、test 再実行 → 4 択提示（ローカル merge / PR 作成 / branch 保持 / discard with typed confirmation）→ 選択に応じた処理 → `<gdd-stop reason="done">` の順で進める。auto mode の既定は PR 作成。Option 4（discard）は破壊的操作のため `discard` という文字列の明示入力を必須とし、auto mode でもここで停止する。superpowers v5.0.7 の `finishing-a-development-branch` で実証されたパターン
- **Spec Change Detection（仕様変更の反映強制）** を `gdd-subagent-driven-implementation` Step 11 に追加。従来「任意」だった `adr.md` 追記を、design.md / AC / 承認済み代替案と異なる判断が発生した場合に **必須** に格上げ。`adr.md` の Context/Decision/Why/Consequences 追記に加え、AC 本文に影響する場合は `requirements.md` を、設計判断が変わる場合は `design.md` を同じ diff 内で更新する。AC の根本追加/削除/意味変更・`Approved Direction` の方向性変更は `human_recheck_required` に昇格。実装中の silent な仕様変更を防ぎ、completion-check / pr-review で遅れて検出される手戻りを削減
- **DONE_WITH_CONCERNS の 3 分岐** を `gdd-subagent-driven-implementation` Implementer Status Handling に追加。従来 2 分岐（正しさ/scope vs 観察）だった DONE_WITH_CONCERNS を、仕様乖離 / 正しさ・scope / 観察 の 3 分岐に拡張。仕様乖離 concern は Step 11 の Spec Change Detection に従って artifact を更新してから review に進める（再実装不要）
- **実装 → artifact 逆方向整合チェック** を `references/inline-review-checklists.md` の implementation-reviewer checklist AC・契約準拠セクションに追加。実装 diff の外部観測可能な挙動が AC / design.md / adr.md のいずれかに記載されているかを reviewer が検出し、Spec Drift を Medium 以上で報告する
- **AC Drift Check** を `gdd-completion-check` Part B に Step 5a として追加。`Verification.status=pass` を付ける前に実装 → artifact の逆方向整合を検査し、AC に書かれていない挙動が diff に含まれる場合は `requirements.md` / `design.md` / `adr.md` への反映を要求する。AC の根本追加/削除は `human_recheck_required`、scope 外は `implementation_fix_only` で差し戻す
- **design_detail_only の記録要件** を `references/rollback-patterns.md` と `gdd-design-gating` Step 12-13 に追加。route 通過時に `design.md` 本文更新と `adr.md` の Context/Decision/Why/Consequences 追記を必須化。AC の根本変更・`Approved Direction` の方向性変更・final output owner / delivery path 等の変更は自走範囲外として `human_recheck_required` に昇格する条件を明記。E2E Discovery Loop 自走中も記録の省略は認めない
- **Spec Drift Check** を `gdd-pr-review` の PR 作成前チェックリスト Step 3a として追加。completion-check の AC Drift Check と同等の逆方向整合を PR 作成直前に再実行し、completion-check 通過後の追加 commit で drift が再発するケースを最終 gate で検出する
- **ADR vs design.md 責務境界** リファレンス（`references/adr-vs-design.md`）を追加。`design.md` = 現在の正しい設計（What）、`adr.md` = 意思決定の履歴（Why + 却下案）の書き分けルールを定義。典型パターン（新判断 / Spec Change / E2E Discovery）とアンチパターンを含む。`gdd-subagent-driven-implementation`、`gdd-design-gating`、`rollback-patterns.md` から参照
- **AC primary owner 移行手続き** を `references/task-breakdown-steps.md` に追加。実装中に AC の primary owner を別 task に移す必要が生じた場合の `[AC Owner Migration]` 記録フォーマットと、移行時の primary 一意性保証ルールを定義。Self-Review 旧#2 にも移行記録の確認を追加
- **gdd-requirements-amendment** skill を新規作成。マージ済み / 実装済み機能への追加要件・仕様変更・不具合修正を独立した amendment タスクとして進める。先行 steering の参照維持、差分 AC のみの作成、通常 gate sequence の維持を保証。`references/entry-intent.md` に `amendment` intent 判定条件と `human_recheck_required` との違いの比較表を追加
- **Multi-Steering Active 解決ルール** を `gdd-using-git-worktrees` に追加。worktree 列挙で non-terminal な steering が複数見つかった場合の解決優先順位（worktree 別 → 同一 worktree 内 → root 直接）と stale steering の判定基準（10 日超前 + `gdd-brainstorming` 段階）を定義
- **Stop hook fail-closed 前提チェック** を `hooks/scripts/run-gdd-stop-hook.sh` に追加。Python / git コマンドが見つからない場合に `systemMessage` で `[GDD Stop hook 不全]` 警告を注入。Python スクリプトのクラッシュ時にも Shell レベルで exit code を検出し警告を出す
- **Cancelled Cleanup 手順** を `gdd-using-git-worktrees` に追加。`gdd-completion-check` で `cancelled` 後の worktree / branch / `.steering/` cleanup をユーザーに 3 択（keep / archive / discard）で提示。自動 discard 禁止・remote branch 自動削除禁止の guardrail 付き。`gdd-completion-check` Step 21 からも誘導を追加
- **並列 subagent の tasklist.md 書き込み制約** を `gdd-subagent-driven-implementation` Step 2a に追加。並列実行中の subagent は `tasklist.md` を直接編集せず、controller（親 session）が完了報告を受けて集約する。lost update（一方の Attempts が消える）を防ぐ構造的制約。Guardrails にも明記
- **Intra-Steering Reviewer Calibration** を `gdd-implementation-gating` Step 5 に追加。従来の `learned-patterns.md`（cross-task = done 時反映）に加え、同一 steering 内の完了済みタスクの Attempts から `[Review Calibration] was_valid=false` を直接参照する。同一 steering の T-1 で発覚した false positive が T-2 のレビューで即座に効く
- **Blocked Since タイムスタンプ** を `state.md` field として追加。`gdd-completion-check` が外部前提不足で `blocked` 停止した時刻を記録し、SessionStart hook が 24 時間超の blocked を警告する。blocker 解消時に自動削除
- **Reviewer Selection stale 防止** を `gdd-implementation-gating` Step 3 に追加。`Implementation Reviewer Selection` の再利用条件を Task ID + `updated_at` の一致で判定。前タスクの `waived` が現タスクに引き継がれて security review が bypass されるケースを防止。Guardrails にも明記
- **Context Compaction Resilience（共通 guardrail）** を `references/common-guardrails.md` に追加。長時間 phase で context compaction により artifact 情報が劣化するリスクに対し、判断ポイントでのディスク re-read を標準化。`gdd-task-breakdown`（分割最終確認前に AC + design re-read）、`gdd-test-driven-development`（各 task の RED 開始時に Current Task re-read）、`gdd-systematic-debugging`（route 決定前に state.md + tasklist.md re-read）の 3 skill に固有ルールを追加
- **Dirty Working Tree Guard** を `gdd-using-git-worktrees` の Worktree 準備に Step 3 として追加。`git status --porcelain` で未コミット変更を検出し、stash / commit / continue の 3 択をユーザーに提示。dirty な状態で worktree 作成すると変更を見失うリスクを防止。Guardrails にも明記
- **Reviewer Loop Escape Hatch** を `gdd-systematic-debugging` Loop Safety と `references/rollback-patterns.md` に追加。同一 Current Task で `changes_requested` が 5 回連続（`implementation_fix_only` + `design_detail_only` の累計）の場合、route 判定を無視して `human_recheck_required` を強制適用。`gdd-implementation-gating` Step 8 にも参照を追加
- **Abandon and Pause リファレンス**（`references/abandon-and-pause.md`）を新設。mid-build cancel（短縮パス）/ 明示的一時停止 / GDD 離脱 / gate スキップ不可の説明を文書化。`gdd-status` に離脱案内へのヒントを追加
- **Reviewer Responsibility Matrix** を `references/reviewer-selection.md` に追加。4 reviewer × 15 観点の交差表で「誰が・いつ・何を見るか」を RACI 形式で可視化。スコープ重複が意図的であることを Why セクションで説明
- **出力量ガイドライン** を `references/output-format.md` に追加。sizing ごとの出力行数上限目安（Express: 10 行以下、quick: 20 行以下、standard: 30 行以下）、findings 出力の絞り込みルール（High + ops-blocking Medium のみ出力、その他は worklog.md 参照に折りたたみ）、Express の phase ヘッダー圧縮（6 行 → 2 行）を定義
- **Gate 数予測** を `references/human-check-template.md` に追加。human-check-waiting 停止時の出力に「通過予定 gate 数」行を追加し、承認後にどれだけ AI が自走するかをユーザーが事前把握できるようにする
- **Integrity Check 修復案内の強化** — `gdd-status` の推奨アクションを `/gdd-dev 再開` 等のコマンド例を含む具体的な手順に改善
- **gdd-refactor-planning / Refactor Gate Status の state-machine.md 正式記載** — `state-machine.md` に `Refactor Gate Status` の field 定義・許容値（`pending` / `in-progress` / `pass-empty` / `pass-applied`）・保存場所（`tasklist.md`）を追加。`Next Action` 許容値に `gdd-refactor-planning` を追加。状態遷移表に `gdd-refactor-planning` の 4 遷移（全 task 完了→refactor-planning、改善あり→TDD、改善なし→completion-check、Refactor Gate 通過済み→completion-check）を追加。build candidate の `Next Action` リストに `gdd-refactor-planning` を追加（session crash 時の resume 分類漏れを修正）。`gdd-status` の整合性チェック3 に `gdd-refactor-planning` を追加
- **Subagent Dispatch の reference 抽出**（`references/subagent-dispatch.md`）— `gdd-dev.md` から subagent テンプレート（brainstorming / design-gating / impl-gating / completion-check）、Model Routing テーブル、Build Loop Orchestration、Post-Return Routing を抽出。`gdd-dev.md` を 330 行 → 141 行に削減（-57%）。`/gdd-dev` 起動時のコンテキストトークン消費を約 4,000 token 削減
- **Hook steering detection の共通ライブラリ化**（`hooks/scripts/lib/detect-steering.sh`）— 3 つの hook（session-start / user-prompt-submit / pre-tool-use）で重複していた steering 検出ロジック（worktree 列挙 + terminal state 除外 + 候補選択）と 3-field gate check を共通ライブラリに集約。`state.md || design.md` の判定を全 hook で統一（従来の user-prompt-submit / pre-tool-use は `design.md` のみで判定していた不整合を修正）
- **Stop hook の Python 外部ファイル化**（`hooks/scripts/gdd_stop_hook.py`）— `run-gdd-stop-hook.sh` の 898 行の heredoc Python を独立した `.py` ファイルに分離。shell ラッパーは 46 行に縮小。Python コードが IDE の syntax highlighting / linting / テスト対象になる
- **ユーザー起点の中止（Cancel）** — `human-check-waiting` からの `cancelled` 遷移を Express / standard 両方の状態遷移表に追加。build phase からの中止手順（steering 放置 or `Next Action=cancelled` 手動書き込み or worktree 削除）を `state-machine.md` § ユーザー起点の中止に文書化。`faq.md` に「途中でワークフローを中止したい」を追加。`gdd-dev.md` の human-check 応答処理に中止検出ルールを追加
- **Express 手動昇格（human-check-waiting）** — human check 時にユーザーが「Express では足りない」と判断した場合の昇格パスを Express 遷移表に追加。既存の build phase 自動昇格と合わせて 2 契機を `state-machine.md` § Express 昇格時の state ロールバック規則に明記。`gdd-dev.md` の human-check 応答処理に昇格検出ルールを追加。`faq.md` の Express FAQ を更新
- **Multiple-steering 検出時の警告表示** — `detect-steering.sh` に `GDD_STEERING_STATUS`（`found` / `none` / `multiple`）と `GDD_STEERING_CANDIDATES` を追加。session-start / user-prompt-submit hook が複数 steering 検出時にサイレントスキップではなく `[gdd:warning]` メッセージを additionalContext に注入する
- **Hook JSON 改行エスケープ** — `run-user-prompt-submit-hook.sh` で AC や Last Error に改行が含まれた場合に JSON が壊れる問題を修正。`run-pre-tool-use-plan-reread-hook.sh` と同じ改行ストリップ処理を追加
- **Heredoc injection 防止** — `setup-gdd-loop.sh` の state ファイル書き込みで `$USER_INTENT` を含む unquoted heredoc（`<<EOF`）を 3 分割（static header / dynamic fields / static body）に変更。ユーザーの task 記述がデリミタと一致しても state ファイルが切断されない
- **findings.md リマインダーの発火制限** — `run-user-prompt-submit-hook.sh` の findings.md リマインダーを 10〜30 分の範囲に限定。30 分超は調査終了とみなし発火を停止し、token 浪費を防止
- **Stop hook RESUME_FROM fallback の worktree 対応** — `gdd_stop_hook.py` の Resume From fallback が `project_root` 直下の `.steering/` のみを読んでいた問題を修正。`git worktree list --porcelain` で全 worktree を列挙し、active steering が worktree 側にある場合も stop signal を検出する
- **Stop hook dead code 削除** — `gdd_stop_hook.py` の `_done_guard_warning` モジュールレベル変数と `global` 宣言を削除。`SystemExit(0)` 直後で値を参照する箇所がなく dead code だった。stderr 出力は維持
- **resolve-gdd-model.py PHASE_TO_TIER 補完** — 未登録だった 9 phase（`gdd-refactor-planning`, `gdd-requirements-amendment`, `gdd-requesting-code-review`, `gdd-receiving-code-review`, `gdd-pr-review`, `gdd-test-failure-debug-pack`, `gdd-status`, `gdd-metrics`, `gdd-using-git-worktrees`）を追加。signal-based fallback への依存を解消
- **subagent-dispatch.md に上位正本を宣言** — 他の全 reference と同様に `上位正本: self-contained-contract.md, state-machine.md` を追記。authority 未宣言だったドキュメント整合性を修正
- **state-machine.md の重複行を削除** — `Blocked Since` の説明で `routing source にはしない` が 2 行連続で記載されていた merge artifact を修正
- **reviewer-selection.md の Completion Rule 表現修正** — 「常時必須」と括弧内の express skip 例外の矛盾を解消。「standard と quick (standard) で常時必須。quick (express) では completion-check 自体をスキップするため起動しない」に修正
- **Express Guard** を `gdd-systematic-debugging` Routing Decision Tree に追加。Express パスでは `design_detail_only` / `planning_rework_required` に route できない制約を明示。Express で設計変更が必要な場合は直接 `human_recheck_required` にエスカレートする。Express 専用の Failure Routing 復帰シーケンスも追加
- **Phase Gate Pre-check** を `gdd-refactor-planning` と `gdd-completion-check` に追加。Express パスが routing ミスでこれらの skill に到達した場合に fail-closed で停止し、`Next Action=done` に修正する safety net
- **Fixed Model 宣言** を 4 skill に追加（`gdd-receiving-code-review`: Sonnet、`gdd-requirements-amendment`: Opus 4.7、`gdd-using-git-worktrees`: Sonnet+low、`gdd-test-driven-development`: Sonnet）。`resolve-gdd-model.py` の `PHASE_TO_TIER` と整合
- **gdd-brainstorming Fixed Model を Opus 4.7 に修正** — `subagent-dispatch.md` では brainstorming は Opus 4.7 subagent として dispatch されるが、skill の Fixed Model 宣言は Sonnet だった不整合を解消。Model Routing セクションも整合
- **gdd-model-routing の brainstorming モデル記載を修正** — 起動時の固定表・Claude Code モデル使い分け・初稿とレビューセクションで brainstorming が Sonnet 側に分類されていた不整合を Opus 4.7 に修正
- **implementation-reviewer に Terraform 追加チェックの言及を追加** — `reviewer-selection.md` で定義済みの Terraform 追加チェック（`.tf` / `.tfvars` / `.tf.json`）が agent 定義側に未記載だった。description と Review Focus セクションに追加
- **gdd-using-skills skill を新規作成** — 従来 `references/gdd-using-skills.md` にあったスキル選択の判定基準（1% ルール・ユーザー依頼マッピング・rationalization 防止パターン）を独立した gateway skill に昇格。superpowers の `using-superpowers` 相当の entry gate として機能し、会話冒頭で Skill tool から invoke できるようにした
- **gdd-completion-check に Branch Hygiene Pre-Flight を追加** — Post-Completion PR Flow Option 2 の `gh pr create` 前に (1) `git fetch && git log HEAD..origin/<default-branch>` で main 進行検知 → 必要なら rebase 提案、(2) `git diff --name-only origin/<default-branch>...HEAD` と `requirements.md` のスコープ突合で scope 外 file 検出 → 別 PR 分離提案、を必須化。Cursor チャットログ分析で頻発が確認された「main 進んだから rebase」「これは別 PR にしたい」の手戻りを完了直前の最後のレイヤーで吸収する
- **gdd-completion-check に Plan mode 遷移禁止句を追加** — Output Guidance / Guardrails / `references/state-machine.md` の transition table 直後に completion-check の `Next Action` 許容値を `done` / `cancelled` / `gdd-completion-check` / `gdd-systematic-debugging` / `gdd-refactor-planning` / `gdd-implementation-gating` の 6 値に固定。harness 側 Plan mode への自動遷移を fail-closed で止める。実装完了後に harness が「複雑タスクは plan-mode へ」のデフォルトで暴走する事例への対応
- **gdd-brainstorming に Step 15 Exit Decision を追加** — Iterative Refinement Loop と Self-Review を経た後、`proceed` / `refine` / `discard` の 3 経路判定を必須化。`discard` 時は `state.md` を `Status: Discarded` でクローズし、`requirements.md` 冒頭に discard 理由を追記、`learned-patterns.md` に判断履歴を残し、worktree cleanup を提案して `<gdd-stop reason="cancelled">` で停止する。`/gdd-dev` 投入即破棄で放置 steering が蓄積する事例への対応
- **`references/debug-triage.md` に Runtime Silent Timeout 切り分けセクションを追加** — LLM runtime（AgentCore / Claude CLI / Lambda + agent）で「処理が止まった / 何も返ってこない」症状向けに、caller → Lambda → AgentCore → Claude CLI → tool の 5 階層 timeout 切り分け手順を追加。CloudWatch / stream-json / hook / subagent duration_ms / retry の確認チェックリストと、観測パターン別の次アクション表を含める。observability ゼロのまま「いつ止まったか分からない」状態を構造的に潰す

#### Changed

- bundled `pr-review` fallback の output format を、`対象PR` 1 行、1 文結論、2 bullet finding、GitHub checkbox のマージ前確認、`✅/⚠️/❌` 要件突合、件数付き不採用 Findings、圧縮 metadata の構成に更新

- **Sizing 二重判定の統合**: Graduated Autonomy の 5 次元評価を `references/task-sizing.md` § 正式判定: Complexity Evaluation に統合。暫定判定（Step 7）と正式判定（Complexity Evaluation）が同一ドキュメント内で完結するようになり、sizing の全体像が 1 ファイルで把握できる。`references/graduated-autonomy.md` はリダイレクトに変換。`brainstorming-steps.md` Step 12a、`gdd-brainstorming` SKILL.md Step 11a、`commands/gdd-dev.md`、`README.md` の参照先を `task-sizing.md` に更新
- **ルール重複記述の正本化**: 各 skill の自律継続 restatement を `common-guardrails.md` § 自律継続 への参照に簡略化（`gdd-test-driven-development`、`gdd-implementation-gating`、`gdd-subagent-driven-implementation`）。`brainstorming-steps.md` Step 17 の Placeholder scan を正本参照に置換。`task-breakdown-steps.md` の No Placeholders パターンに正本参照を追加。`validate-steering-write.py` に正本参照コメントを追加

- `references/task-sizing.md` から `micro` tier を完全削除し、`trivial / quick / standard` の 3 tier に統一した
- `references/brainstorming-steps.md` のステップを再番号（Problem Discovery / Options Exploration の挿入に伴い Steps 9-20）
- `gdd-brainstorming` の SKILL.md Steps summary を再番号（Steps 9-10 挿入、旧 11-12 → 13-14）
- `gdd-systematic-debugging` の Routing Decision Tree に Step 3b（Approved Direction の自走範囲判定）と Step 4 の自走分岐を追加
- `gdd-design-gating` に E2E Discovery Loop 経由時の自走分岐（Step 13）を追加。自走条件を満たせば reviewer は通すが human check に戻さない
- `references/self-contained-contract.md` に human check 契約（Approved Direction 記録、E2E Discovery Loop、Scope Drift Guard）と承認ポイントの背景・変更前後・方向性承認の契約を追加
- `references/contract-overview.md` に human check / E2E Discovery Loop の行を追加
- `references/state-machine-overview.md` に `Approved Direction` field と E2E Discovery Loop の記載を追加
- `references/state-machine.md` に `Approved Direction` field 定義を追加
- `references/common-guardrails.md` の planning 差し戻し route に E2E Discovery Loop 自走ルールを追加
- `references/rollback-patterns.md` の `design_detail_only` に E2E 自走時の注記を追加
- `commands/gdd-dev.md` の Workflow Overview に Approved Direction / E2E Discovery Loop の記載を追加
- `references/onboarding.md` の承認手順に背景・変更前後・方向性承認の説明を追加
- `references/faq.md` に「承認後に実装中の変更で human check が何度も戻ってくる」の FAQ を追加
- `README.md` に Problem Discovery、Approved Direction、E2E Discovery Loop の概念を追加
- `references/requirements-template.md` の承認ポイントテンプレートに背景・変更前後・方向性承認を追加。`state.md` セクションに `Approved Direction` を追加
- `references/requirements-gating-steps.md` に Approved Direction の記録手順と承認ポイントの背景・変更前後ルールを追加
- `references/requirements-template.md` の Summary Brief 構造定義を 3 層（一言 / 判断材料 / 承認ポイント）から **4 層**（+ Honest Limitations）に拡張。standard で必須、quick は任意
- `references/brainstorming-steps.md` Step 10 の Options Exploration で Approach C を「やらない案 / 縮小案」両対応に統合。Scope Reduction Check（Step 9）で出た縮小候補は Approach C として並べる
- `references/brainstorming-steps.md` Step 9 の Scope Reduction Check に、Options Exploration を skip する経路（quick / Express / Direct Intent）では縮小提案を `Human Check Questions` に直接追加する代替経路を定義
- `references/inline-review-checklists.md` の implementation-reviewer checklist に「テスト品質」セクションを追加（テストファイル変更がある場合のみ走査）。mock 要素アサート / テスト専用 production メソッド / partial mock / 過剰な mock / environment 起因を RED 扱いしているか、の 5 観点
- `skills/gdd-test-driven-development/SKILL.md` の Guardrails に `references/testing-anti-patterns.md` 参照を追加
- `skills/gdd-subagent-driven-implementation/SKILL.md` Step 1a に mock 使用時の `references/testing-anti-patterns.md` 参照を追加
- `skills/gdd-completion-check/SKILL.md` の Guardrails で `references/verification-before-completion.md` を参照先として明示
- `skills/gdd-implementation-gating/SKILL.md` の Guardrails に reviewer `approved` 判定時の Fresh Verification 要件（`references/verification-before-completion.md` 参照）を追加
- `skills/gdd-subagent-driven-implementation/SKILL.md` Step 3 / Guardrails に subagent 完了報告の独立検証ルールを追加
- `skills/gdd-task-breakdown/SKILL.md` の No Placeholders ポリシーに `references/task-breakdown-steps.md` のパターン詳細への参照を追加。Step Granularity 見出しを新設
- `references/task-breakdown-steps.md` Self-Review の番号ずれ（7 の次が 6 になっていた Attempts セクション）を 9 に修正。placeholder scan / Step Granularity / 型一貫性の 3 チェックを Self-Review に統合
- `skills/gdd-completion-check/SKILL.md` の Output Guidance を 4 択提示フローと整合（test 再実行 → 4 択 → 選択処理 → `<gdd-stop>` の順）
- `skills/gdd-subagent-driven-implementation/SKILL.md` の Guardrails に Spec Change Detection の bypass 禁止を追加。Rationalization Check に「仕様と少し違うけど adr.md は後で」「AC 境界値変更だけなら human check 不要」の 2 行を追加
- `skills/gdd-completion-check/SKILL.md` の Guardrails に AC Drift Check の bypass 禁止を追加。Rationalization Check に「AC pass だから diff で分かる」「E2E 追加 fix は AC 変わらないから adr 不要」の 2 行を追加
- `skills/gdd-design-gating/SKILL.md` Step 12 に `design_detail_only` の記録要件欠落時の非 approve ルールと AC 影響時の `human_recheck_required` 昇格条件を追加。Step 13 の E2E Discovery Loop 自走時にも `design.md` 本文更新と `adr.md` 追記の記録要件を明記
- `references/rollback-patterns.md` の `design_detail_only` パターンに記録要件（`design.md` 本文更新 + `adr.md` 追記）と AC 影響時の `human_recheck_required` 昇格条件を追加
- `gdd-subagent-driven-implementation` Spec Change Detection の記録要件に `references/adr-vs-design.md` への参照を追加。`design.md` の更新指示を「現在の正しい設計に上書き更新」に明確化
- `gdd-design-gating` Step 6 の adr.md 記述指示に `references/adr-vs-design.md` への参照を追加
- `references/rollback-patterns.md` の `design_detail_only` 記録要件に `references/adr-vs-design.md` への参照を追加。`design.md` の更新指示を「現在の正しい設計に上書き更新」に明確化
- `references/entry-intent.md` に `amendment` intent を追加（従来は `new` / `resume` / `ambiguous` の 3 値）。amendment 判定条件と `human_recheck_required` との比較表を定義
- `gdd-completion-check` Step 21（cancelled）に `gdd-using-git-worktrees` Cancelled Cleanup への誘導を追加
- `gdd-subagent-driven-implementation` Guardrails に「並列 subagent は tasklist.md を直接編集しない」制約を追加
- `gdd-implementation-gating` Step 5 の Reviewer Calibration 参照を 2 ソース（cross-task + intra-steering）に拡張。Why セクションで inter-task gap の理由を説明
- `gdd-implementation-gating` Step 3 の reviewer selection 再利用条件に Task ID + `updated_at` 一致チェックを追加。Guardrails に stale selection 再利用禁止を追加
- `gdd-completion-check` に `Blocked Since` timestamp 記録・削除のルールを追加
- `references/state-machine.md` の `state.md` field 一覧に `Blocked Since` を追加
- `hooks/scripts/run-session-start-hook.sh` に `Blocked Since` 24h 超の警告を追加
- **20 skill description を CSO 規則に整合** — superpowers `writing-skills` の Claude Search Optimization 規則（description は「いつ使うか」だけを書く、workflow 要約を書かない）に全 20 skill を揃えた。workflow 要約を削除し「Use when…」形式のトリガー条件に統一。`gdd-pr-review` / `gdd-requesting-code-review` / `gdd-task-breakdown` の冗長な「Do NOT use for X」節を gateway skill への参照に置き換え
- **Reference sprawl を削減** — deprecation shim だった `references/graduated-autonomy.md`（`task-sizing.md` への redirect 化から未参照化していた）を削除。`references/gdd-using-skills.md` を新 gateway skill に昇格して reference から削除。reference 総数 34 → 32 に削減
- **common-guardrails.md を Iron Law 化で圧縮** — 全 20 rule と section 見出しを保持したまま、各 rule の導入を bold 文で統一（Iron Law パターン）。Operational Safety テーブルから「理由」列を削除（下の Why セクションに統合）。冗長な導入 prose を削り 256 行 → 240 行に圧縮。skill からの `§ 合理化防止テーブル` / `§ 自律継続` 等の参照は維持
- **state-machine-overview.md を純粋な視覚図 + quick index に整理** — `State Fields` テーブルから「意味」列を削除（保存場所 index のみ保持）。重複していた `Autonomous Continuation` / `Scope Drift Guard` セクションを削除し、`common-guardrails.md` § 自律継続 と `phase-progression.md` § E2E Discovery Loop への pointer に置き換え。92 行 → 83 行に圧縮。`state-machine.md` との drift 源を排除しつつ Phase Flow 図と Key Principles は維持

#### Fixed

- **Cursor の Plan mode 移行ブロック漏れを修正**。active `/gdd-dev` session 中に Cursor の `SwitchMode(target_mode_id=plan)` が使われると、`EnterPlanMode` matcher だけでは hook が発火せず、実装完了後の修正・設計見直しが GDD の same-session correction ではなく host Plan mode に逃げることがあった。`hooks/hooks.json` の matcher に `SwitchMode` を追加し、`run-block-plan-mode-hook.sh` で `SwitchMode(plan)` だけを block、`SwitchMode(agent)` は許可するようにした。`tests/validate-plugin.sh` に回帰確認を追加
- **Hook の cross-worktree auto-resume を修正**。SessionStart / UserPromptSubmit / PreToolUse の active steering 検出を現在 cwd の git worktree に限定し、別チャットの worktree にある `.steering` を `[gdd:reboot]` として注入しないようにした。Stop hook の `Resume From=human-check-waiting` fallback も現在 worktree の `.steering` だけを見るように戻し、別 worktree の human-check 状態で非 GDD チャットが止まる問題を防止。別 worktree の resume 候補探索は `/gdd-dev resume ...` または空プロンプト `/gdd-dev` の時だけ行う
- `references/requirements-template.md` の design.md セクション定義が `Summary Brief` を「3 層構造」と記載していたが、実際の正本は 4 層構造（requirements と共有）。design.md も 4 層構造を用いる旨に修正
- `references/requirements-gating-steps.md` の「含めるべき情報の全体リスト」テーブルで `Summary Brief` を「3 層構造」と記載していたのを 4 層構造（Honest Limitations を含む）に更新
- `skills/gdd-brainstorming/SKILL.md` の Step 9 summary に Scope Reduction Check の言及を追加。steps.md 詳細に記載があっても SKILL.md 要約から漏れていたため、SKILL.md だけ読んだ AI が Scope Reduction Check をスキップするリスクがあった
- `skills/gdd-brainstorming/SKILL.md` Step 11 の `Summary Brief` 説明を 4 層構造（一言 / 判断材料 / 承認ポイント / Honest Limitations）に更新。従来 2 層しか書かれておらず AI が承認ポイント・Honest Limitations の必要性を見落とすリスクがあった
- `agents/gdd-planning-reviewer.md` の Completeness 観点に `Summary Brief` の 4 層構造チェックと standard タスクでの `Honest Limitations` 必須チェックを追加。reviewer が「standard で Honest Limitations 必須」を実際に検出できなかった enforcement gap を解消
- `skills/gdd-requirements-gating/SKILL.md` の Guardrails に standard タスクで `Honest Limitations` が欠けたまま `human-check-waiting` に進めない旨を追加
- **gdd-security-reviewer から requirements-phase セクションを削除** — `reviewer-selection.md` で「security reviewer は requirements phase では起動しない」と定義されているが、agent 定義に `Requirements phase (gdd-requirements-gating)` セクションが残っていた dead code を削除。description からも `gdd-requirements-gating` を削除
- **abandon-and-pause.md の参照元宣言を修正** — `gdd-completion-check` と `gdd-using-git-worktrees` を参照元から削除（実際の参照元は `gdd-status` のみ）
- **gdd-using-skills.md の参照元宣言を修正** — 「全 GDD skill（入口判定）」を `references/common-guardrails.md` に修正（実態に即した宣言）
- **gdd-pr-review の description からファイルパス参照を除去** — `skills/gdd-using-skills/SKILL.md` への path 参照は Skill tool の呼び出し方式（skill name 指定）と噛み合わず冗長。`gdd-implementation-gating` / `gdd-requesting-code-review` との棲み分けを description 内にインライン記載に変更
- **setup-gdd-loop.sh の multi-steering 警告を intent 分岐化** — 従来 `STEERING_CANDIDATE_COUNT >= 2` のときに無条件で「Resume requires explicit selection」を出していた。user intent が新規タスク記述（例: `issueをフォームベースに修正したい`）でも resume 選択を迫る誤警告になっていた。`classify_intent()` shell function（`references/entry-intent.md` のルールに準拠）を追加し、`new` / `resume` / `ambiguous` で state 本文と stdout 警告を分岐。`new` のときは「resume selection is not required」の informational メッセージに変更
- **validate-plugin.sh の transcript fixture を実 Claude Code 形式に整合** — `workflow-loop` BLOCK の fixture が `{"role": "assistant", ...}` を使っていたが、実際の transcript 形式は `{"type": "assistant", ...}`（`message.role` は入れ子側）。`last_assistant_text` の `item.get("type") != "assistant"` 判定と噛み合わず done-guard test A が false success していた問題を修正。5 箇所の `"role": "assistant"` を `"type": "assistant"` に更新し done-guard test A/B/C/D/E/F/G/H/I/J が正しく発火
- **`gdd_stop_hook.py` の `last_tool_result_text` を実 Claude Code 形式に修正** — fallback 1（subagent tool_result から `<gdd-stop>` を検出）が `item.get("role") != "user"` を使っていたが、実 transcript は top-level `type: user`（`role` は入れ子側）のため常に skip され fallback 1 が機能していなかった。`gdd-brainstorming` 等が subagent として `<gdd-stop>` を出してメイン session が echo し忘れた場合、fallback 3（`Resume From` state.md scan）頼みになり stop 判定が遅延するケースがあった。判定を `item.get("type") != "user"` に修正
- **`tests/test_stop_hook_logic.py` を本番 hook と同じ field 判定に揃える** — テスト側の helper 関数 (`last_assistant_text` / `last_tool_result_text`) と全 fixture が `role` を使っていたため、本番と「誤り同士で合致」して 46 test が false success していた。本番修正 (`type`) に追従して helper 2 箇所と全 fixture の `"role": "..."` を `"type": "..."` に変更。46 test 全て通過（`python3 -m unittest tests.test_stop_hook_logic`）
- **UserPromptSubmit hook (`run-user-prompt-submit-hook.sh`) の multi-steering 警告を intent 分岐化** — 従来 `GDD_STEERING_STATUS=="multiple"` のときに無条件で「/gdd-dev resume で対象を 1 つに絞ってください」を additionalContext に注入していた。session 中にユーザーが新規タスクを入力した場合でも resume 選択を迫る誤警告になっていた。UserPromptSubmit payload を stdin から読み出し、`classify_intent` 共通 lib（`hooks/scripts/lib/classify-intent.sh`, `references/entry-intent.md` のルールに準拠）で intent を判定して `new` / `resume` / `ambiguous` で警告を分岐。`new` は `[gdd:info]` で「既存を再開する場合は 再開/続き/resume を指示に含めてください」、`resume` は `[gdd:warning]` で candidate 選択を要求、`ambiguous` は両方の選択肢を提示。`setup-gdd-loop.sh` から `classify_intent` を共通 lib に抽出し DRY 化

#### Breaking Contract Changes

- `micro` tier が削除された。従来 `micro` だった変更は `trivial`（ロジック変更なし）または `quick`（ロジック変更あり）に分類される
- human check 承認時に `Approved Direction` の記録が必須になった。`requirements-gating-steps.md` の「Approved Direction の記録」に従い `state.md` に方向性・自走範囲・人間に戻す条件を記録する
- `承認ポイント` に **背景** と **変更前 → 変更後** が必須になった

#### User Action Required

- `micro` tier を使っていた場合は `trivial` または `quick` に読み替える
- human check handoff の `承認ポイント` に背景・変更前後・方向性承認が含まれているか確認する

#### Validation / Eval Impact

- `evals/evals.json` に Approved Direction 記録・E2E Discovery Loop 自走判定・Scope Drift Guard 発動・Problem Discovery・承認ポイント背景+変更前後のケースを追加すべき
- `tests/validate-plugin.sh` に `Approved Direction` / `E2E Discovery Loop` / `Scope Drift Guard` のトークン確認を追加すべき
- `scripts/grade_evals.py` に Approved Direction / E2E Discovery Loop 関連の grading rule を追加すべき

---

- `references/operation-levels.md` を追加し、light / standard / strict の 3 段階の運用レベルを定義した。`.gdd-config.md` でリポジトリ単位の設定が可能
- `references/team-onboarding.md` を追加し、チーム導入プロセス（個人試行 → レベル設定 → 展開 → 計測）を文書化した
- `README.md` を採用ランディングページとして書き直し、3 分クイックスタート、メンタルモデル図、ロール別ガイドを追加した
- `references/onboarding.md` に findings.md / worklog.md の使い方ガイドセクションを追加した
- `references/reviewer-selection.md` にレビュー関連 Skill の責務分類（Formal Gate / Companion / Triage / PR Review）テーブルを追加した
- `gdd-test-driven-development` に RED 証跡の 3 つの具体フォーマット（テストフレームワーク / executable verification / 型チェック・lint）を追加した
- `references/output-format.md` に 3 つの新ブロックパターン、リカバリコマンド早見表、構造化 stop 出力テンプレートを追加した
- `references/self-contained-contract.md` に Verification status 許容値の早見表と具体的な行例を追加した

#### Changed

- `references/brainstorming-steps.md` のステップ番号を SKILL.md と整合させた（Step 6 に運用レベル解決を挿入、後続を +1 で再番号）
- `gdd-requesting-code-review` の description に日本語トリガーフレーズを追加し、generic review request との境界を明確化した
- `gdd-pr-review` の description に `gdd-requesting-code-review` / `gdd-implementation-gating` との明示的な棲み分けを追加した
- `gdd-task-breakdown` の description に内部ルーティング専用であることを明記した
- `gdd-refactor-planning` に「リファクタと機能追加が混在する場合」の routing ガイダンスを追加した
- `gdd-completion-check` の Steps を Part A / B / C に分割し責務境界を明示した
- `install-claude-code-links.sh` と `install-cursor-links.sh` の共通ロジックを `_link-helpers.sh` に切り出した（DRY 改善）
- `uninstall-cursor-links.sh` の未使用関数 `build_entries_from_current_plugin()` を削除した
- `run-session-start-hook.sh` の `detect_active_steering` のエラーハンドリングを改善し、診断ログを `/tmp/gdd-session-start-diag.log` に出力するようにした
- `hooks/hooks.json` の Stop hook に `timeout: 10` を追加した
- `run-user-prompt-submit-hook.sh` の `stat` コマンドを macOS / Linux 両対応にした
- `references/phase-progression.md` で mandatory refactor checkpoint の正本が `gdd-subagent-driven-implementation` であることを明記した
- `references/cursor-guide.md` と `references/onboarding.md` の `gdd-model-routing/references/cursor.md` 参照を `references/cursor.md` に修正した
- `references/faq.md` の旧 Go1/Go2 セクションに非推奨注記を追加した
- `references/phase-progression.md` の micro パスセクションを `task-sizing.md` への参照に集約した
- `references/task-sizing.md` に運用レベルによる差分テーブルを追加した
- `.gitignore` に `gdd-resolver-state-*/` を追加し、19 個の孤立一時ディレクトリを削除した

#### Fixed

- `brainstorming-steps.md` のステップ番号が SKILL.md と不整合だった問題（Step 6 の運用レベル解決が brainstorming-steps.md 側に反映されていなかった）

#### User Action Required

- `install-claude-code-links.sh` / `install-cursor-links.sh` を再実行する場合は、共通ロジックが `_link-helpers.sh` に移動したことに注意する
- チーム導入を検討する場合は `references/team-onboarding.md` と `references/operation-levels.md` を確認する

#### Validation / Eval Impact

- `tests/validate-plugin.sh` に `references/operation-levels.md`、`references/team-onboarding.md` の存在確認と token チェックを追加した
- `tests/validate-plugin.sh` に `references/onboarding.md` の `findings.md` / `worklog.md` token チェックを追加した
- `README.md` の token チェックに `references/operation-levels.md` と `references/team-onboarding.md` を追加した

---

- `references/rollback-patterns.md` を追加し、差し戻し時の Gate Status 更新パターン（`planning_rework_required` / `human_recheck_required` / `design_detail_only` / `implementation_fix_only`）を 1 箇所に集約した（DRY 改善、4 skill × ~20 行の重複削減）
- `trivial` tier を追加（`task-sizing.md`）。typo 修正・コメント修正・文言変更など、コード変更なしまたは 1 行以下の typo 修正に限り、artifact / gate / human check / security evidence をすべて省略する最短パス
- `state.md` を新規追加し、Gate Status / Resume From / Reviewer Selection を `design.md` から分離した。`design.md` は純粋な設計コンテンツ文書になった
- `references/requirements-template.md` に `state.md` のセクション定義を追加した
- `references/cursor-guide.md` を追加し、Cursor 環境の差分・制約・導入手順・hooks なし運用を 1 箇所に集約した

#### Changed

- `self-contained-contract.md` / `phase-progression.md` の remediation / planning loop safety 詳細を `state-machine.md` への参照に集約し、重複記述を削減した
- `task-sizing.md` の micro 条件「新規コード 0 行」を「ロジック変更なし」に緩和し、テスト expected 値の修正などを許容した
- `hooks.json` の description に dual PreToolUse hook の設計意図を追記した
- `gdd-design-gating` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `gdd-systematic-debugging` の差し戻し status 更新ブロックを `references/rollback-patterns.md` への参照に置き換えた
- `run-pre-tool-use-plan-reread-hook.sh` を強化: Goal（Summary Brief の一言）と複数 AC（AC-1, AC-2...）を Write/Edit 前に注入するようにした。planning-with-files の Manus 原則「Manipulate Attention Through Recitation」に相当
- `run-user-prompt-submit-hook.sh` を強化: AC 詳細を注入に追加し、context 圧縮後の AC 見失いを防止
- requirements phase の reviewer を `gdd-requirements-reviewer` のみに集約（統合案 B）。specialist reviewer（NFR / feasibility / security / solution）は design phase 以降でのみ起動する設計に変更
- `reviewer-selection.md` の Quick Selection Table と Gate Rules を統合案 B に合わせて更新
- `self-contained-contract.md` の requirements gate 契約を統合案 B に合わせて更新
- quick タスクの `gdd-implementation-gating` を inline checklist only に変更（specialist skip・subagent escalation なし）。superpowers v5.0.7 の self-review パターンを参考に、review 時間を大幅短縮
- Gate Status（`Requirements Review Status` / `Design Review Status` / `Human Check Status` / `Resume From`）と Reviewer Selection（`Requirements Reviewer Selection` / `Design Reviewer Selection`）の保存場所を `design.md` から `state.md` に移動した
- `state-machine.md` / `state-machine-overview.md` / `self-contained-contract.md` / `phase-progression.md` / `rollback-patterns.md` / `common-guardrails.md` / `onboarding.md` / `faq.md` / `reviewer-selection.md` / `requirements-gating-steps.md` の保存場所参照を `state.md` に更新した
- `gdd-brainstorming` / `gdd-design-gating` / `gdd-completion-check` / `gdd-status` / `gdd-systematic-debugging` の SKILL.md を `state.md` 参照に更新した
- 3 つの hook スクリプト（session-start / pre-tool-use-plan-reread / user-prompt-submit）で Gate Status の読み取り元を `state.md` に変更し、`design.md` フォールバックで legacy steering と互換を維持した
- `onboarding.md` に Cursor ユーザー向け導線を追加し、`cursor-guide.md` への誘導を設置した
- `README.md` の導入セクションと Contract Sources に `cursor-guide.md` を追加した
- `faq.md` に Cursor 固有の FAQ（hooks が動かない / reviewer subagent が起動しない）を追加した

#### Breaking Contract Changes

- requirements phase では specialist reviewer を起動しなくなった。specialist 観点は design phase で confirmed facts に基づいて実施する
- trivial tier が追加され、typo 修正等で artifact / gate を一切通さないパスが新設された
- quick タスクの implementation gate は inline checklist only になり、subagent への escalation は行わない（High 相当の疑いがある場合のみ standard に昇格して再 gate）
- Gate Status / Resume From / Reviewer Selection の保存場所が `design.md` から `state.md` に変更された。既存の steering で `design.md` に Gate Status がある場合、hook スクリプトは `design.md` にフォールバックするが、新規 steering からは `state.md` に書き込まれる

#### User Action Required

- custom 運用で requirements phase に specialist reviewer を含めている場合は、design phase で同等のカバレッジを確認する
- trivial tier の判定条件を確認し、自動判定が適切か検証する
- quick タスクで deep review が必要な場合は、明示的に standard に昇格するか `gdd-requesting-code-review` を使う
- 既存の steering で `design.md` に Gate Status がある場合、次回の state 更新時に `state.md` への移行を検討する（hook は自動フォールバックするため緊急性は低い）

#### Validation / Eval Impact

- `tests/validate-plugin.sh` に `references/rollback-patterns.md` の存在確認を追加すべき
- `evals/evals.json` に trivial tier の判定・昇格テストケースを追加すべき
- `evals/evals.json` に quick タスクの inline checklist only gate のテストケースを追加すべき
- `evals/evals.json` に requirements phase で specialist が起動しないことを確認するテストケースを追加すべき
- `evals/evals.json` の Gate Status 参照を `design.md` から `state.md` に更新した
- `scripts/grade_evals.py` の grading rule を `state.md` 参照に更新した
- `tests/validate-plugin.sh` に `state.md` テンプレートの存在確認を追加すべき

---

### v0.1.3 (2026-04-06)

#### Added

- `references/faq.md` と `references/onboarding.md` を追加し、FAQ と初回導線を分離した
- `evals/evals.json` に category / priority / required を持たせる方針を追加した
- `scripts/grade_evals.py` に category / required 集計を追加する方針を追加した
- `gdd-test-failure-debug-pack` skill を追加し、real test failure を structured debug pack として整理する導線を追加した
- `references/reviewer-selection.md` を追加し、applicable reviewer selection と記録方式の正本を分離した
- `.claude/gdd-dev.local.md` と Stop hook を使って active な `/gdd-dev` run を same session で継続する contract を追加した
- `scripts/setup-gdd-loop.sh` と `hooks/scripts/run-gdd-stop-hook.sh` を追加した

#### Changed

- `README.md` を概要・使い分け・導線中心に整理した
- `commands/gdd-dev.md` から関連ドキュメントへ辿れるようにした
- `commands/gdd-dev.md` の Quick References から contract と changelog に直接辿れるようにした
- `references/state-machine.md` に `gdd-systematic-debugging` の出口遷移を追加し、formal state の正本だけで remediation loop を追えるようにした
- `gdd-implementation-gating` / `gdd-systematic-debugging` / `self-contained-contract` で repeated `changes_requested` 時の loop safety を明文化し、同じ `Current Task` に対する 3 回目の blind `implementation_fix_only` を禁止した
- `references/self-contained-contract.md` の検証契約で、`tests/validate-plugin.sh`、`evals/evals.json`、sample task / review の役割分担を明文化した
- `gdd-systematic-debugging` を routing 専任として整理し、real test failure の状況整理は `gdd-test-failure-debug-pack` を先に使う分担を README / skill / eval に反映した
- `references/self-contained-contract.md` / `references/state-machine.md` / `commands/gdd-dev.md` / `gdd-brainstorming` / `gdd-systematic-debugging` / README / FAQ で、stopped workflow を review 差し戻しや implementation policy 変更で reopen するときの implicit review / re-entry cue を定義し、single active steering なら新しい worktree を切り直さず同じ active worktree を再利用する contract を追加した
- `gdd-brainstorming` / `gdd-requirements-gating` / `gdd-design-gating` / `references/self-contained-contract.md` / `references/state-machine.md` で、`Behavior Change Summary` / `Route / Ownership Matrix` / `Sensitive Data / Masking Policy` / `Human Check Questions` を planning artifact の必須見出しとして追加し、blocking `Open Questions` が残る間は `human-check-waiting` に進めない contract を追加した
- `gdd-brainstorming` / `gdd-requirements-gating` / `references/self-contained-contract.md` / `references/faq.md` / `gdd-requirements-reviewer` で、`Human Check Questions` と `承認してほしい事項` は人間がそのまま読んで判断できる短い自然文で書き、内部 field 名や略語だけの箇条書きにしない wording rule を追加した
- formal reviewer を毎回フルセット起動する契約をやめ、`gdd-requirements-gating` / `gdd-design-gating` / `gdd-implementation-gating` で applicable reviewer selection と selection record を使う契約に変更した
- `gdd-completion-check` / `gdd-comprehensive-reviewer` が reviewer selection record の妥当性も確認するようにした
- `gdd-completion-check` を Snyk 固有の scan 実行・version・CLI 前提から切り離し、`Verification` 上の `security_evidence:<kind>` を読む汎用 external security evidence gate に寄せた
- `references/self-contained-contract.md` / `references/state-machine.md` / `references/phase-progression.md` / `references/task-sizing.md` を更新し、worktree 必須を維持したまま external verifier hook 連携へ責務分離した
- `tests/validate-plugin.sh` に optional な external verifier smoke を追加し、Snyk のスキャン結果を書く verifier plugin がある環境では `security_evidence:code` row の shape を結合確認できるようにした
- `scripts/external-verifier-smoke.sh` を追加し、validate と同じ最小 happy path を手動でも再利用できるようにした
- `references/reviewer-selection.md` と requirements/design/comprehensive reviewer 群で、prompt / output contract、route / owner change、runtime-owned delivery、masking policy、rollout / rollback order を reviewer 選定・固定質問・最終 diff 照合の対象として明文化した
- `commands/gdd-dev.md` / `README.md` / `references/state-machine.md` / `references/self-contained-contract.md` で、non-terminal phase は status summary だけで止まらず継続することと、`gdd-stop` marker でだけ terminal / blocked stop することを明文化した

#### Fixed

- dead-end stop を避けるため、停止時の返答契約を文書群で明示した
- `tests/validate-plugin.sh` で `grading-summary.json` の最小 schema を軽量 fixture で確認するようにした
- `gdd-design-gating` 通過後に `Resume From=gdd-task-breakdown` を報告して止まりやすかった導線を、Stop hook ベースの same-session continuation に寄せた
- `.steering` 書き込み hook から Snyk 固有の org UUID 判定を外し、GDD 本体が特定 scanner の組織 ID 契約を知らなくても動くようにした
- `references/faq.md` / `references/self-contained-contract.md` / `README.md` に、Snyk のスキャン結果を書く verifier plugin を generic external verifier の具体例として追記し、single active `tasklist.md` を決められないときは verifier 側 no-op を許容することを明文化した

#### Breaking Contract Changes

- formal reviewer は fixed full-set 前提ではなくなり、`references/reviewer-selection.md` に従って必要な reviewer だけを起動する
- `design.md` と `tasklist.md` には reviewer selection record が必須になった
- hook が有効な plugin 導入では、explicit な `/gdd-dev` run は `.claude/gdd-dev.local.md` と Stop hook を使って `done` / `cancelled` / `human-check-waiting` / `blocked` のいずれかまで継続する
- required security evidence は `snyk_*` 固有 ID ではなく `security_evidence:<kind>` 形式に変更した
- `gdd-completion-check` は特定 scanner plugin の version / auth / CLI 前提を直接検証しなくなった

#### User Action Required

- `README.md` 先頭の 1画面ガイドを確認する
- 詰まりどころは `references/faq.md`、初回利用は `references/onboarding.md` を参照する
- custom 運用や eval を持っている場合は、fixed reviewer 前提をやめて `references/reviewer-selection.md` に追随する
- symlink 方式だけでは Stop hook が有効にならないため、自走継続を使う場合は manifest 経由で plugin を有効化し、新規 session / reload を行う
- external verifier hook を使う環境では、`Verification` に required `security_evidence:<kind>` 行を書ける状態を整え、止まっていた workflow は同じ `Next Action=gdd-completion-check` から再実行する

#### Validation / Eval Impact

- `tests/validate-plugin.sh` は新規 docs と eval metadata を確認する
- `scripts/grade_evals.py` は iteration root に `grading-summary.json` を出力する
- `evals/evals.json` に repeated `changes_requested` 時の loop safety を確認する required case を追加した
- `evals/evals.json` に stopped workflow の review / re-entry cue で `resume` し、same worktree を再利用する case を追加した
- `evals/evals.json` / `scripts/grade_evals.py` に、planning artifact の新見出し、human handoff の `承認してほしい事項`、blocking `Open Questions`、reviewer selection trigger、`gdd-comprehensive-reviewer` の route/masking/diff 照合を確認する case と grading rule を追加した
- `tests/validate-plugin.sh` / `scripts/grade_evals.py` / `evals/evals.json` に `gdd-test-failure-debug-pack` の存在と期待出力を確認する項目を追加した
- `tests/validate-plugin.sh` / `evals/evals.json` / `scripts/grade_evals.py` は reviewer selection record と applicable reviewer selection の期待値を確認する
- `tests/validate-plugin.sh` は Stop hook / `.claude/gdd-dev.local.md` / `gdd-stop` marker の最小動作を確認する
- `evals/evals.json` / `scripts/grade_evals.py` は non-terminal state で status summary だけで止まらないことと blocked stop marker の期待を確認する
- `tests/validate-plugin.sh` / `evals/evals.json` / `scripts/grade_evals.py` を `security_evidence:<kind>` ベースの external security evidence 契約へ更新した
- `tests/validate-plugin.sh` は、利用可能な場合だけ sibling external verifier との smoke を追加で実行する
- `scripts/external-verifier-smoke.sh` で external verifier の手動 smoke を再利用できる
