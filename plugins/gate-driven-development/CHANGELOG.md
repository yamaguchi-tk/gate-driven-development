# Changelog

`gate-driven-development` の利用者向け変更履歴。

## Policy

- contract に影響する変更は必ずここに記録する
- 特に次は breaking change 候補として明示する
  - `references/self-contained-contract.md`
  - `references/state-machine.md`
  - required external prerequisite
  - reviewer set / gate 順序
  - `Resume From` / `Next Action` の意味
  - `evals/evals.json` の schema
- entry には少なくとも次を含める
  - Summary
  - Affected Files
  - User Action Required
  - Validation / Eval Impact
- 断片（`changelog.d/<YYYYMMDD>-<slug>.md`）に書くのは、利用者から見える変更（配布物の挙動・契約・導線が、変更の前後でどう変わるか）だけ。レビューの経緯・巡の記録・指摘の一覧・受け入れた指摘（medium・low と advisory）は書かない（`review-log/` に残す。PR 本文に書く限界は root `CLAUDE.md` 手順 7 に従う）。断片は push の前に 1 回で確定し、レビューの巡ごとに書き足さない（レビューの修正が利用者から見える変更を変えたときだけ、その分を push の前の 1 回にまとめて直す）。必須の節は、利用者から見える変更が無い PR でも書く（Summary に「利用者から見える変更なし」と書いてよい）
- `#### Validation / Eval Impact` 欄に書くのは検証の種類（実行したコマンドの名前・対象の AC・追加した check / test の名前）のみ。テストの件数（`N passed` 等）・所要時間（`in Ns` 等）・commit sha・「最終ツリーで」のような時点依存の実測値は書かない。実測は PR 本文の「確認したこと」に書く（root `CLAUDE.md` 手順 7。PR 本文の更新は commit を作らず SHA を動かさないため、独立レビューの証跡を無効にしない）
- 既存エントリ（履歴）は書き換えない。この規約は新規エントリから適用する
- PR は版の節（`### [x.y.z]`）を足さず、版数も上げない。変更内容は `changelog.d/<YYYYMMDD>-<slug>.md` に断片として書く（書式は § Entry Template）。断片を版の節へ集め、版数を上げ、断片を消すのはリリースのときに `scripts/release.py` がまとめて行う（手順の正本: `docs/VERSIONING.md` § リリース手順）
- 切り替え時点: v0.43.0 までは PR ごとに版数を上げ、ここへ版の節を追記していた。v0.43.0 の次の版からは、断片を集めて版の節を作る

## Versioning Notes

- v0.x の間も contract 変更は breaking change として扱う
- 実装詳細だけの修正でも、利用者の手順や期待結果が変わるならここに残す

## Entry Template

断片（`changelog.d/<YYYYMMDD>-<slug>.md`）の書式。`type` は `patch` / `minor` / `breaking` のどれか（決め方は `docs/VERSIONING.md` § バージョン判定フローチャート）。必須の節は § Policy のとおりで、`breaking` なら Breaking Contract Changes も必須。見出しは `####` だけを使い、使わない節は書かない。書式の検査は `tests/checks/version-not-consumed.sh`。

```markdown
---
type: patch
---

#### Summary

- この変更が何であり、なぜ必要かの要約

#### Added

- 追加した機能や文書

#### Changed

- 挙動や導線の変更

#### Fixed

- 不整合や誤案内の修正

#### Breaking Contract Changes

- 破壊的変更がある場合だけ記載

#### Affected Files

- 変更したファイルの一覧

#### User Action Required

- 利用者が確認・更新・再実行すべき内容

#### Validation / Eval Impact

- 検証の種類（実行したコマンドの名前・対象の AC・追加した check / test の名前）のみを書く。件数・所要時間・sha・時点依存の実測値は書かない（実測は PR 本文の「確認したこと」に書く）
- `tests/validate-plugin.sh` で増える確認
- `evals/evals.json` / `scripts/grade_evals.py` への影響
```

## Archive

行数上限（1500 行）を守るため、古い release 節は別ファイルへ移した。**本文は移動時に変更していない**。

**回転のトリガと移動先**: `CHANGELOG.md` が **1200 行**に達したら、古い側の release 節を**新しい連番 archive**（`CHANGELOG-archive-N.md`）へ移して **800 行台まで戻す**。既存 archive へ足さないのは、どれも上限 1500 に対する余裕が数百行しかなく、そこへ数百行足すと今度は archive 側が `large_file` で `high` になり同じ状態に戻るため。上限 1500 に当たってから動くのでは、その時点のリリースが CHANGELOG への集約で Codebase Health Gate に阻まれる。回転はリリースのコミットで行う（`scripts/release.py --apply` が 1200 行以上になったことを知らせる）（初出は `### [0.40.7]` の § User Action Required。同節が archive へ移っても運用が失われないよう、ここへ昇格した）。移動時は `README.md` / `CONTRIBUTING.md` の構成一覧も同時に更新する。

- [`CHANGELOG-archive-4.md`](CHANGELOG-archive-4.md): `### [0.40.15]` 〜 `[0.40.4]`
- [`CHANGELOG-archive-3.md`](CHANGELOG-archive-3.md): `### [0.40.3]` 〜 `[0.38.0]`
- [`CHANGELOG-archive.md`](CHANGELOG-archive.md): `### [0.37.4]` 〜 `[0.16.0]`
- [`CHANGELOG-archive-2.md`](CHANGELOG-archive-2.md): `### [0.15.0]` 〜 `v0.1.3`

## Current Release Notes

### [0.44.0] - 2026-09-12

#### Summary

GDD から Fable の自動起動を撤去し、要件・設計レビュー（`gdd-planning-reviewer`）を実測で最も検出力の高かった構成（Opus 5 + effort max ＋観点レーン 6 つ）に変えた（計画 X-32 / X-47）。

- 方向確認（`human_check_gate` tier / `agents/gdd-direction-checker.md`、Fable + medium）を廃止した。W-29 で 5 回・env-s で 7 回すべて「方向 OK」で、13 タスクで指摘 1 件・実害 0。done-guard では毎回 unavailable だった（2026-09-11 の集計で約 $55）
- `remediation_loop` tier の Claude Code 列を Fable + high から Opus 5 + max に変えた。2026-09-08 のユーザー指示「Fable はよっぽど難解なとき以外は使わない」による。gate まわりの Fable は 2026-09-11 の集計で約 $250（impl-gate 89・remediation worker 76・方向確認 52 など）
- `gdd-planning-reviewer` を `effort: high` から `effort: max` にし、観点レーン（接地／内部整合／測定設計／実装接続／記録監査／実効性）を入れた。2026-09-05 の比較実験（設計成果物・正解 12 件・各構成 n=1）で、Opus max ＋観点レーン = $5.37・9/12（最多）、Opus max 素 = $3.91・7/12、Opus high 素（従来の構成）= $3.00・5/12、Fable high = $6.01・3.5/12 だった

#### Changed

- `references/fixed-models.md`: `remediation_loop` を `Opus 5` + `effort=max` にした（Cursor 列は `Opus 5` + `reasoning.effort=high`、Codex 列は変更なし）。Agent tool は effort を引数で受けないため、実適用 model と effort を `worklog.md` に記録する。planning reviewer の model / effort と `formal_gate`（gate 本体）の関係を段落で明記した
- `agents/gdd-planning-reviewer.md`: frontmatter を `effort: max` にした。`## Review Focus` の 7 項目は、`## 観点レーン` の 6 レーンと基本品質 3 項目に統合した（Consistency → (b)、Measurability → (c)、Simplicity → (f)、実行・評価環境の現実 → (a)）。既存の詳細チェック節は残し、各レーンの「受け持ち」から指す
- `skills/gdd-implementation-gating/SKILL.md` / `skills/gdd-systematic-debugging/SKILL.md` / `skills/gdd-subagent-driven-implementation/SKILL.md` / `references/subagent-dispatch.md`: `remediation_loop` 中の dispatch を `Agent(model="opus")` にした
- `skills/gdd-model-routing/SKILL.md` / `references/cursor.md` / `references/codex.md` / `scripts/resolve-gdd-model.py`: tier 表から `human_check_gate` を削除し、`remediation_loop` を更新した（resolver の claude_code は `opus` + `max`）
- `references/phase-progression.md`: Origin Notification が使う「HITL 到達の timestamp」の正本を、削除した `fixed-models.md` § `human_check_gate` から Cross-Session Messaging 自身へ移した（定義の中身は `Human Check Status` の `updated_at` のままで変えていない）

#### Breaking Contract Changes

- agent `gdd-direction-checker` と tier `human_check_gate` を削除した。`resolve-gdd-model.py --phase gdd-direction-checker` は既定の `light_task` に解決される
- `state.md` の Tier 3 field `Direction Check` を削除した
- HITL（requirements の human check / `human_recheck_required`）に `Fable 確認:` 行が出なくなった

#### Known Limitations

- `remediation_loop` の `effort=max` は、agent 定義を持たない subagent（gate subagent・remediation worker など）には強制できない。Agent tool の引数は model だけで、effort は host の既定値になる。実適用値は `worklog.md` の記録で確かめる
- Claude Code では `remediation_loop` の 3 工程のうち (1) route 判断・(2) 再レビューは、通常時と昇格後で `model="opus"` が同一になり、上の限界のとおり effort も強制できないため実質 no-op になる。実差が残るのは (3) worker（`Sonnet` → `opus` への切替と dispatch 必須化）だけ
- `remediation_loop` の `effort=max` は、escalation 先 reviewer が agent 定義を持つ場合（`gdd-implementation-reviewer` / `gdd-security-reviewer`、いずれも frontmatter `effort: high`）には適用されない。frontmatter の値が優先されるため、これらは `remediation_loop` 中でも `high` のまま動く
- 観点レーンの効果は n=1 の比較実験に基づく。実運用での初回検出率は未計測

#### Affected Files

- `agents/gdd-planning-reviewer.md`, `agents/gdd-direction-checker.md`（削除）
- `references/fixed-models.md`, `references/subagent-dispatch.md`, `references/cursor.md`, `references/codex.md`, `references/requirements-gating-steps.md`, `references/rollback-patterns.md`, `references/human-check-template.md`, `references/human-check-template-compact.md`, `references/state-field-tiers.md`, `references/phase-progression.md`
- `skills/gdd-model-routing/SKILL.md`, `skills/gdd-implementation-gating/SKILL.md`, `skills/gdd-systematic-debugging/SKILL.md`, `skills/gdd-subagent-driven-implementation/SKILL.md`, `commands/gdd-dev.md`, `scripts/resolve-gdd-model.py`
- `docs/adr/20260904-w29-gate-feedback-loop.md`（撤去の注記のみ）, `docs/VERSIONING.md`, `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`
- `tests/test_fable_removal_contract.py`（新規）, `tests/test_planning_reviewer_lenses_contract.py`（新規）, `tests/test_human_check_gate_tier_contract.py`（削除）, `tests/test_remediation_loop_model_routing_contract.py`, `tests/test_model_routing_contract.py`, `tests/test_cross_session_hitl_contract.py`, `tests/checks/agent-effort-schema.sh`, `tests/checks/hooks.sh`, `tests/checks/skill-body-budget.sh`

#### User Action Required

- 進行中の steering の `state.md` に `Direction Check:` 行が残っていても対応は不要（読む hook・skill は無い）
- `remediation_loop` 中の subagent は Opus になる。Fable を使いたいときは、ユーザーが明示的に指示する

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` と `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 新規 `tests/test_fable_removal_contract.py`（契約ファイルに Fable と方向確認の語が残らない）と `tests/test_planning_reviewer_lenses_contract.py`（opus + max、6 レーンの順序、`formal_gate` との関係）
- `tests/checks/agent-effort-schema.sh` の planning-reviewer の pin を `max` にした。`hooks` / `skill-body-budget` の BLOCK からは direction-checker を外した（BLOCK の増減なし）
- `evals/` の `fable_*` シナリオ ID は、Fable がレビューした出典の名前で dispatch 指示ではないため変更しない

### [0.43.0] - 2026-09-11

#### Summary

`gdd-pr-review-followup` に「設計見直し checkpoint」（巡数 / 自傷率 / クラスタ再発 / commit 比率の4トリガーで発火し、設計し直し・スコープ縮小・パッチ継続の3択を自律選択）を新設した。レビュー指摘の対応プロトコルを「受け入れ判定 → 原因クラスタリング → クラスタ判定 → 1巡の修正範囲」の4段へ置き換え、PR後の巡数上限を新規カウンタ `PR Review Rounds`（既存の `PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS` とは別軸）で管理する。あわせて W-27（同一原因判定の `file:function` 依存）を root cause カテゴリ判定へ統一し、新規 ADR 発行 ≥2 を独立トリガーとして追加した。PR後レビューループが収束しない問題への対処。

#### Added

- `skills/gdd-pr-review-followup/SKILL.md`: `## Design Review Checkpoint` 節（4トリガー・3択自律選択・事後報告・記録契約）
- `hooks/scripts/lib/constants.py`: `PR_REVIEW_ROUNDS_MAX` / `PR_CHECKPOINT_ROUNDS_THRESHOLD` / `PR_CHECKPOINT_SELF_INFLICTED_RATIO` / `PR_CHECKPOINT_CLUSTER_REPEAT_ROUNDS` / `PR_CHECKPOINT_REVIEW_COMMIT_RATIO`
- `references/state-machine.md` § Remediation Loop Safety: 新規 ADR 発行 ≥2（独立トリガー）と PR 版 checkpoint への接続 pointer
- `references/independent-review.md`: `fix_origin: self-inflicted | inherited` field（既存の `origin: this-diff | pre-existing` とは別軸。算出は main session）

#### Changed

- `references/state-machine.md` / `skills/gdd-implementation-gating/SKILL.md` / `skills/gdd-systematic-debugging/SKILL.md` / `references/phase-progression.md`: 同一原因の判定表現を `file:function` からroot causeカテゴリへ統一
- `skills/gdd-implementation-gating/SKILL.md`: Honest Limitations 既載例外の適用時に、別の AC を破らないことの確認義務を追加
- `references/bounce-log-schema.md`: `PR Review Cause Cluster Log`（identifier-key `PR + root cause カテゴリ`。既存 `PR Review Bounce Log` とは別カウンタ）を追加
- `references/self-review-lanes.md`: 規律 A（横展開検索）に followup 例外を追記（`gdd-pr-review-followup` では検出・記録までにとどめ、一括修正は再設計側で行う）

#### Affected Files

- `skills/gdd-pr-review-followup/SKILL.md`, `references/state-machine.md`, `references/state-field-tiers.md`, `skills/gdd-implementation-gating/SKILL.md`, `skills/gdd-systematic-debugging/SKILL.md`, `references/phase-progression.md`, `hooks/scripts/lib/constants.py`, `references/independent-review.md`, `references/bounce-log-schema.md`, `references/self-review-lanes.md`
- `tests/test_design_review_checkpoint_contract.py`（新規）, `tests/test_remediation_loop_root_cause_contract.py`（新規）, `tests/test_impl_gate_precision_tiering_contract.py`, `tests/checks/self-review-lane-tokens.sh`
- （PR 旧#68 レビュー対応 / ADR ≥2 独立トリガーの producer・route 確定側実装）`references/adr-vs-design.md`（ADR entry テンプレートに `Origin` 行を追加）, `skills/gdd-subagent-driven-implementation/SKILL.md`, `skills/gdd-design-gating/SKILL.md`（remediation 中の ADR 記録要件に `Origin` 行を追加）, `tests/test_adr_origin_producer_contract.py`（新規）

#### User Action Required

- 既存 PR の followup 対応中（`Iteration` / `Findings:` / `checkpoint:` 行が既に state.md・worklog.md のどちらかにある PR）に本バージョンへ upgrade した場合、`PR Review Rounds` は自動初期化されない。次回 followup で § Design Review Checkpoint の (a) 判定不能として扱われ、強制発火（設計し直し / スコープ縮小の 2 択、`(3) パッチ継続` は選べない）する。PR 作成後まだ 1 度もレビューを受けていない PR（記録が全くない状態）は followup 初回で `0` に初期化される（`skills/gdd-pr-review-followup/SKILL.md` § field 定義を参照）
- pre-push / pre-PR / merge gate の人間承認済み非退行 high 受理経路（当初案の AC-23〜AC-27）は本リリースに含まれない。別途フォローアップ PR で提供予定

#### Validation / Eval Impact

- `tests/validate-plugin.sh` の既存 BLOCK は増減なし
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` に新規 contract test 3 ファイルが追加（PR 旧#68 レビュー対応の `test_adr_origin_producer_contract.py` を含む）
- `tests/checks/skill-body-budget.sh` の `references/*.md` 行数 ratchet を 11922 → 11927 へ引き上げた。本 PR 分岐後に `origin/main` が無関係な変更（verification closed grammar 等）だけで旧 cap を使い切っており（`origin/main` tip 実測 11922 = headroom 0）、本 PR の必須追記（AC-8/AC-19 `PR Review Rounds` tiers 行、AC-11/AC-13 の checkpoint 独立トリガー・接続 pointer 行）は等価削減（`independent-review.md` / `self-review-lanes.md` で重複表現を 2 行統合済み）を行った上でも 5 行分の純増が残った。ユーザー承認（2026-09-11）により、新しい統合先 tip を反映した値へ引き上げた

### [0.42.3] - 2026-09-12

#### Summary

CHANGELOG の `#### Validation / Eval Impact` 欄に、テスト件数・所要時間・commit sha のような commit ごとに変わる実測値を書く慣行があり、テストを 1 本足すたびに「数値を直す commit → SHA 変化 → sha 束縛の独立レビュー証跡が無効化 → 再レビュー」という循環を生んでいた（正本の `CHANGELOG.md` § Policy はもともと件数を書けとは定めておらず、過去エントリを真似た慣行だった）。本 entry は § Policy に「Validation 欄に書くのは検証の種類（コマンド名・対象 AC・追加した check / test の名前）のみで、件数・所要時間・sha・時点依存の実測値は書かず PR 本文に `at <sha>` つきで書く」規約を明記し、§ Entry Template の説明行を揃える。見出し文字列 `Validation / Eval Impact` は変更しない（`tests/checks/hooks.sh` が検査対象にしている）。既存エントリは書き換えない。

#### Changed

- `CHANGELOG.md` § Policy に Validation / Eval Impact 欄の記載規約を追加した
- `CHANGELOG.md` § Entry Template の `#### Validation / Eval Impact` 説明行を規約に合わせて更新した

#### Affected Files

- `plugins/gate-driven-development/CHANGELOG.md`
- `plugins/gate-driven-development/tests/checks/hooks.sh`（契約テスト: CHANGELOG 必須トークン表に新規約文言を追加。トークンは § Policy にのみ出現する一意な部分文字列に限定した）
- `plugins/gate-driven-development/.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数。origin/main が本 PR の作業中に v0.42.1（PR 旧#67）・v0.42.2（PR 旧#69）と2度先行出荷したため、都度 merge して版数を再採番し、本 entry で v0.42.3 とした）
- `plugins/gate-driven-development/docs/VERSIONING.md`（現行バージョン v0.42.3 / 統合先の消費済み版数 v0.42.2 に更新）
- `plugins/gate-driven-development/tests/test_verification_closed_grammar_release_notes_contract.py`（付随修正: `VersionBumpContractTests` を、1 箇所（3 manifest のうち `.claude-plugin/plugin.json`）を基準値として読み、残り 4 箇所との完全一致を検証したうえで、基準値が `TARGET_VERSION` 以上であることを別途検証する形に再設計した。origin/main が同じ問題を `CURRENT_TOP_VERSION` という新しい版数固定リテラルで回避していたが、これは将来のバージョン bump のたびに再び conflict を起こす同型の問題だったため採用しなかった）
- `docs/learned-patterns.md`（repo-root。version bump 契約テストの検出力とトークン選定基準の学びを、レビュー指摘を反映した最終設計に合わせて更新した）

#### User Action Required

- 今後 CHANGELOG entry を書くときは、`#### Validation / Eval Impact` 欄に検証の種類（コマンド名・対象 AC・追加した check / test の名前）のみを書く。テスト件数・所要時間・commit sha は書かず、実測が必要な場合は PR 本文に `at <sha>` つきで書く

#### Validation / Eval Impact

- `tests/checks/hooks.sh` の CHANGELOG 必須トークン表に追加した § Policy 限定トークンについて、RED / GREEN / 変異実測（§ Policy の規約行のみを削った場合の検出を含む）の契約テストを実行した
- `tests/test_verification_closed_grammar_release_notes_contract.py` の `VersionBumpContractTests`（canonical-source 設計）を、5 箇所のいずれか 1 箇所だけを他と異なる値にした変異での検出を含めて実行した
- `bash tests/checks/version-not-consumed.sh` / `bash tests/checks/bounded-claim-evidence.sh` / `bash tests/validate-plugin.sh` / `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` を実行した。実測は PR 本文に `at <sha>` つきで書く

### [0.42.2] - 2026-09-11

#### Summary

`gh_command_parse.py` の tokenizer が、引用符・バックスラッシュで守られた `;` `|` `&&` 等の演算子文字を裸の演算子と誤読し、`gh pr merge -t ';' 8` のような形で PR 番号を見失っていた欠陥を修正した。修正前は、承認済み PR（例 旧#7）の証跡が揃った状態で、引用符付き演算子を含む別 PR 宛て merge コマンドが allow されてしまう fail-open があった。

#### Added

- `hooks/scripts/lib/gh_command_parse.py`: `OPERATOR_MASK_START` / `MASKED_OPERATOR_CHARS` / `_SHLEX_SPECIAL_CHARS` 定数、`_QuotedWord(str)` 型、`_pick_operator_masks` / `_mask_quoted_operators` / `_restore_token` 関数を追加

#### Fixed

- クォート・エスケープで守られた `;` `|` `&` `&&` `||` `|&` `;;` `<` `>` `>>` `>&` `<&` `(` `)` が、`_tokenize_checked` で裸の演算子と同一視され、simple command の区切り・リダイレクトの読み飛ばしとして誤処理されていた欠陥を修正した。`_is_operator` / `_is_control_operator` は、引用符・エスケープ由来の演算子文字（`_QuotedWord`）を演算子と見なさない
- 副次的に、`gh -R ';' pr merge 8` / `gh --hostname ';' pr merge 8` のように `-R` / `--hostname` の値に `;` `|` `&` を引用した形も修正した。修正前は `is_merge=False` で `gh` コマンドとして認識されず、証跡検査が一切走らない素通りだった（修正後は `is_merge=True` で block。独立レビュー実測、2026-09-11）

#### Known limitations

- 位置引数に引用符付き演算子を置く形（`gh pr merge 8 ';'` など）は、修正後は `pr-target-unresolvable` で block される（gh 自身が「引数過多」で拒否する形）。例外として `find . -exec gh pr merge 7 \;` の `\;` は find が消費するため gh には渡らないが、修正後の tokenizer 単体では同じ形を区別できず `pr-target-unresolvable` になる。回避策は `find` を介さず直接 `gh pr merge 7` と実行すること
- push gate・pre-PR gate・`git_command_parse.py` にも同型の tokenizer 実装があるが、今回の修正はそれらに波及しない（別 steering で扱う。追跡先: push gate `task_f423ebd0` / pre-PR gate `task_d6f46f36`）
- コマンド置換（`echo "$(gh pr merge 8)"`）が gate を素通りする既存の穴は、今回の修正の対象外（別の機構の既存の穴）
- heredoc introducer 行の pipeline 境界検出（`_feeds_shell_interpreter` / `PIPELINE_BOUNDARY_RE`）はバックスラッシュエスケープを考慮せず、`bash -s \; <<EOF` のように演算子文字をエスケープして heredoc を開始する形は pipeline 境界と誤認され、heredoc 本文（`gh pr merge N` を含みうる）が gate から不可視になり素通りする。今回の修正が対象とする `_tokenize_checked`（token 列の演算子判定）とは別経路の既存の穴で、origin/main から変わらない（今回の修正の対象外。独立レビュー実測、2026-09-11）
- `active: false`（管轄外）のとき、`gh pr merge 7 '&&' gh pr merge 8` の判定が block（2 本の merge とみなす）から allow（`'&&'` を語として読み 1 本の merge）へ変わる。実シェルでは gh が引数過多で拒否するため merge は起きず、`active: true` では block のまま
- `active: true` で、`eval gh ')' pr merge '|' 8` と `eval gh '(' pr merge '&&' 8` の判定が block 相当から allow に変わる（`eval` の読み直しで引用の区別が失われる。実 bash では構文エラーで何も実行されない）
- sub-command より前の位置に演算子文字だけの引用付き token を置く形も判定が両方向に変わる。`gh '(' pr merge 8` 等は `is_merge` が False に、`gh -R ';' pr merge 8` 等は True（block 方向）に変わるが、いずれも gh 自身が拒否するので merge は起きない
- 内部表現の候補を使い切る入力（U+0001〜U+00FF のうち shlex が特別扱いしない 241 文字と、U+E000〜U+10FFFF をすべて含む入力。UTF-8 で約 4.2MB 以上）では parser が例外になり、GDD の marker があるセッションでは `active` の値によらず parse-error で block する
- 性能: 置き換えの走査のぶん、parser が線形にわずかに遅くなる（実運用の典型的な長さのコマンドでは走査の固定費が相対的に重く約 14〜22%、`eval` の入れ子と組む形では約 30〜42% 増。N=550,000 の繰り返しのような長大な入力では相対的に約 1% と小さくなる。絶対値はいずれも μs〜ms オーダーで運用上の支障はない）。241 文字のうち 235 文字以上を含む入力に限り、一部の演算子の内部表現が 2 byte 幅になり、引用内の演算子が長く連なる形で約 1.8 倍遅くなる。さらに U+E000〜U+FFFF もすべて含む入力では 4 byte 幅になり、約 3.5 倍遅くなる（修正前の parser でも、引用内の先頭に絵文字を 1 つ置けば同じ遅さになる）。hook の timeout（10 秒）を超えると素通りになる既存の穴は、別の変更で扱う

#### Affected Files

- `hooks/scripts/lib/gh_command_parse.py`
- `tests/test_merge_gate_hook_quoted_operator.py`（新規）
- `tests/_merge_gate_support.py`（`_run_hook` に `timeout` 引数を追加）
- `CHANGELOG.md`（本 entry）
- `docs/VERSIONING.md`（現行バージョンを v0.42.2、統合先の消費済み版数を v0.42.1 に更新）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（version を 0.42.2 に更新）
- `docs/adr/2026-09-11-merge-gate-quoted-operator.md`
- `docs/learned-patterns.md`（repo-root。版数追従レースの学習パターンを追記）
- `tests/test_verification_closed_grammar_release_notes_contract.py`（`CURRENT_TOP_VERSION` を 0.42.2 へ追従）

#### User Action Required

- なし。既存の merge gate の使い方・出力契約は変わらない

#### Validation / Eval Impact

- `tests/test_merge_gate_hook_quoted_operator.py` を新規追加
- merge gate の unittest は `tests/validate-plugin.sh` から呼ばれないため、`tests/` で `python3 -m unittest discover -s . -p 'test_merge_gate_*.py'` と `python3 -m unittest test_hook_block_reason_recovery_contract test_hook_injection_security_contract` を明示的に実行して回帰がないことを確認した
- `tests/validate-plugin.sh` は rc=0（plugin 全体の構造・版数の検査）


### [0.42.1] - 2026-09-11

#### Summary

merge gate の `gh pr merge` 検出に、`env` の split-string オプション（`-S` / `--split-string`）で包んだコマンド本体を、実 env と同じく env の argv のその位置に差し込んだ後の argv（同じ simple command の後続引数を含む）として再走査する経路を追加した。`env -S 'gh pr merge 7'` のような 1 綴りの回避形は origin/main（64e33e0）では `is_merge=False` となり hook 自体が不発火（証跡・承認・待機のすべてを迂回した merge が完全に素通り）していた。`[0.41.11]` の Known limitations で「別 steering の第一候補」として開示していた `env -S '-C /B gh pr merge 7'` の素通りも同じ経路で塞がる。block へ倒れることは parser 単体テストと hook サブプロセスのテストで固定し、origin/main との A/B は実測で確認した。pre-push gate / pre-PR gate にも同型の穴が実測で確認されているが、本 PR の scope は merge gate のみ（Known limitations に開示）。あわせて、本体の末尾に語頭 `#` の語を置くと二重計上を避ける打ち切りが誤って働き repo を読み違える形を block 側に倒し、本体に `\c` を含む形（`gh` との位置関係を問わない一般形）と split-string を区切りなしで多数並べた入力の解析時間の退行は、いずれも「対応・解析を確かめられない形」として展開個数の上限 8 と同じ扱いで block 側に倒した（上限内に残る伸びは Known limitations に開示）。実装レビューで見つかった 2 件（展開個数の上限超過時に chdir intent 信号を捨てる形、`\c` の一般形の不発火）は、独立の人間確認（R7）を経て同じ Round で塞いだ。

#### Added

- `hooks/scripts/lib/gh_command_parse.py`: `env` の split-string オプションの本体と、本体を持つ token の位置を返す `_env_split_string_body` を追加。実 env の option 解析に合わせて、代入（`NAME=value`）と値取り option・その値を読み飛ばし、operand（env が起動するコマンド名）または `--` で打ち切る。短オプション束は左から 1 文字ずつ解釈する。対象綴りは `-S <str>` / `-S<str>` / 束ね（`-iS <str>` / `-iS<str>` / `-vS <str>`）/ 単独 `-` の後の `-S` / `--split-string=<str>` / `--split-string <str>` / GNU の一意な長オプション省略形。走査規則の正本はこの関数の docstring、綴りの正本は同ファイルの定数（`ENV_VALUE_TAKING_SHORT_OPTION_CHARS` / `ENV_REQUIRED_ARG_LONG_OPTIONS` / `ENV_NAME_VALUE_RE`）。長・短オプションの 1 token 分の処理は複雑度上限のため `_env_long_option_step` / `_env_short_option_step` に分けた
- `hooks/scripts/lib/gh_command_parse.py`: 本体を env の argv に差し込んだ後の argv（`env` + 本体の token + 同じ simple command の後続引数。次の制御演算子の手前まで）を 1 本の文字列で返す `_env_split_string_command` を追加し、`_nested_shell_commands` の env 分岐から `bash -c` / `eval` と同じ入れ子経路（tokenize・`MAX_NESTED_SHELL_DEPTH` の深さ予算・BFS 重複除去）に流す。新しい深さ定数・新しい tokenizer は導入しない
- `hooks/scripts/lib/gh_command_parse.py`: 同じ merge を 2 回数えないための打ち切り。トップ層の既存経路が既に数えている `gh … pr merge` の手前で argv を打ち切る。ただし打ち切るのは、打ち切る前の差し込み後の argv を同じ gh 探索で読んで見つかる gh が、トップ層の gh と同じ token に対応するときだけ（`_cutoff_matches_visible_gh`。対応しなければ打ち切らず block 側に倒す）。本体を持つ token 自身が gh と読まれるときは、本体の token 列のうち basename が `gh` の最後の token（`_last_gh_basename_index`）の手前までを残し、本体中の env option（`-C` 等）と代入（`GH_REPO=` 等）を `cd_intent` / `env_repo_conflict` の判定に残す。gh が本体由来のときの対応は、本体 token 列の最後の gh が本体 token 列の末尾にあることを条件に含む（Fixed 参照）
- `hooks/scripts/lib/gh_command_parse.py`: 1 層（`_nested_shell_commands` の 1 回の呼び出し）で展開する env split-string の個数の上限 `MAX_ENV_SPLIT_STRINGS_PER_LAYER = 8` と、上限超過または本体に `\c` を含む場合に `parse_gh_pr_merge` / `_extract_cd_target` まで伝える module 内の例外 `_EnvSplitStringBudgetExceeded` を追加。`_nested_shell_commands` の env 分岐で数え（制御演算子では数え直さない）、超えた時点で送出する。`_env_split_string_command` は本体を tokenize する前に `\c` の有無を見て同じ例外を送出する（Fixed 参照）。`parse_gh_pr_merge` は捕捉して「対象を決められない」の表現（`is_merge=True` / `unresolvable=True` / `cd_intent=True` / `pr_number` / `pr_url` / `cd_target` は None）を返し、`_extract_cd_target` は None を返す。深さ定数・tokenizer・reason code・出力 field は増やさない
- `hooks/scripts/lib/gh_command_parse.py`: `_is_chdir_long_option` と `--split-string` / 値取り長オプションの判定が共有する `_is_env_long_option(name, full_name)` を追加（DRY。受理下限は既存どおり `len(name) >= 3`）
- `hooks/scripts/lib/gh_command_parse.py`: `_scan_simple_command` の gh 探索を位置を返す `_find_gh_pr_merge` として切り出し、二重計上の判定と共有する（DRY。`_scan_simple_command` の挙動は不変）

#### Changed

- `_nested_shell_commands` の返り値に `env -S` の差し込み後の argv が加わる。`_scan_tokens`（merge 検出）と `_collect_nested_shell_layers`（chdir signal）が同じ関数を呼ぶため、env の split-string オプションを含む入力では `is_merge` / `pr_number` / `repo_flag` / `cd_intent` / `env_repo_conflict` / `unresolvable` の判定が変わりうる。split-string オプションを含まない入力の判定は変わらない。`cd_target` は既存の条件 (h)（走査範囲に `env` があれば None）により引き続き None
- origin/main で merge 対象を解決していた一部の `env -S` の組み合わせ形が、同じ merge を 2 層で数えて `pr-target-unresolvable` の block に変わる（fail-closed 方向の退行。人間承認のうえ開示して受容。形の一覧は Known limitations）

#### Fixed

- `env -S 'gh pr merge 7'`（chdir なし）/ `env -S '-C <別 repo> gh pr merge 7'`（chdir あり）が `is_merge=False` で hook ごと不発火になり、merge gate の証跡・承認・待機がすべて迂回されていた（実測: origin/main 64e33e0）。本 PR で `is_merge=True` として検出し、前者は証跡不足の集約 block（`approval-missing`）、後者は `pr-target-unresolvable` で block する
- `env -S 'gh pr' merge 7` / `env -S '-S "gh pr merge 7"'` のように `-S` の本体だけでは merge にならない形と、`env -S 'gh pr merge 7' -R other/repo` のように後続引数に repo / PR 番号 / `--admin` がある形も、差し込み後の argv を再走査することで既存経路と同じく読む
- `-R` / `--repo` の値や `-S` の本体全体の basename が `gh` になる形（`env -S 'gh -R' o/gh pr merge 7` / `env -S '/usr/bin/gh -R o/gh' pr merge 7` ほか。一覧は Known limitations）は、origin/main では現 repo の 旧#7 と読み違えて素通りしていた（実 env は別 repo の 旧#7 を merge する）。本 PR では `repo_flag` を読み、対象を決められないとして `pr-target-unresolvable` で block する
- 本体の末尾に語頭 `#` で始まる語を置く形（`env -S '/usr/bin/gh -R o/x #/gh' pr merge 7` と、綴り違いの `env -S'…'` / `env --split-string='…'` / `--repo=o/x` の 3 形）は、トップ層が本体の生文字列全体の basename（末尾の `#/gh` 由来）を gh と読む一方、本体 token 列の最後の gh（`/usr/bin/gh`）の後ろには `-R o/x` が残るのに、打ち切りの対応ありと誤判定していた。打ち切りで `-R o/x` が argv から消え、現 repo の 旧#7 と読み違えていた（実 env は `#` で始まる語から後ろを捨て、o/x の 旧#7 を merge する。origin/main と同じ読み違い）。`_cutoff_matches_visible_gh` に「最後の gh が本体 token 列の末尾にあるときだけ対応あり」の条件を足し、満たさない場合は打ち切らず二重に数えて `pr-target-unresolvable` で block する（`repo_flag="o/x"` / `unresolvable=True`。completion-check で発見。人間承認 2026-09-11T13:36:09+09:00）
- 上と同型で `#` の代わりに `\c` を使い、本体全体の basename が `gh` になる形（`env -S '/usr/bin/gh -R o/x \c/gh' pr merge 7`。`\c` を独立の語にした形も同じ）も同様に読み違えていた。`\c` は実 env にとって文字列の残りを無視する記号だが、parser の tokenize は `\c` を普通の文字 `c` として残すため、上の末尾の条件をすり抜ける（人間承認 2026-09-11T14:14:53+09:00 時点の修正）。ただしこの修正は、`\c` の後ろが `gh` にならない一般形（`env -S 'gh \cx' pr merge 7` 等）を判断材料に含めておらず、その一般形は打ち切り判定の経路にすら入らないため素通りが残っていた（実装レビューで発見）。本体に `\c` が含まれていれば位置を問わず「対応を確かめられない形」として展開個数の上限超過と同じ扱いに倒すよう改め、この一般形も含めて block する（`is_merge=True` / `unresolvable=True`。人間承認 2026-09-11T17:40:53+09:00）
- 1 つの simple command に env の split-string を区切りなしで多数並べると、各 argv が後続の split-string を抱えて次の深さで再展開され、解析時間が個数に対して指数的に伸びていた（`env -Sx ` × 100、813 byte で 21〜42 秒。`hooks.json` の `timeout: 10` を超えて無出力 allow になる。origin/main は同じ入力を 1 秒未満で merge と判定するので、本 PR の途中版が持ち込んだ退行。completion-check で発見）。1 層で展開する split-string の個数に上限 8 を設け、超えたら解析せず `is_merge=True` / `unresolvable=True` として既存の block 経路に乗せる。`bash -c` の本体の中や `eval` の後に並べた形にも同じ上限が効く（いずれも 1 秒未満で block。人間承認 2026-09-11T14:14:53+09:00）
- 展開個数の上限を超えたときに「対象を決められない」表現へ倒す既存の except 節は、`cd_target` だけでなく `cd_intent` も既定の `False` のまま残していた。GDD セッションの repo に steering が無い状態で、別 repo へ chdir してから split-string を 9 個以上並べて merge する形（`cd <別 repo> && env -S '' ×9 gh pr merge 7`。`env -C <別 repo>` / `bash -c 'cd <別 repo> && …'` でも同じ）が、hook の「chdir intent はあるが実行先を 1 つに決められない形を block する」既存の遮断を通り抜け、無出力 allow になっていた（origin/main は `pr-target-unresolvable` で block。実装レビューで発見）。except 節で `cd_intent=True` を立てて閉じる（人間承認 2026-09-11T17:40:53+09:00）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_command_parse.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_env_split_string.py`（新規）
- `plugins/gate-driven-development/tests/test_verification_closed_grammar_release_notes_contract.py`（origin/main 取り込み時の版数付け替えで、`[0.42.0]` 固定の version-pin テストに `CURRENT_TOP_VERSION` を分離）
- `plugins/gate-driven-development/tests/test_merge_gate_followup_findings.py`
- `plugins/gate-driven-development/CHANGELOG.md`
- `plugins/gate-driven-development/.claude-plugin/plugin.json`
- `plugins/gate-driven-development/.codex-plugin/plugin.json`
- `plugins/gate-driven-development/.cursor-plugin/plugin.json`
- `plugins/gate-driven-development/docs/VERSIONING.md`
- `plugins/gate-driven-development/CHANGELOG-archive-4.md`（新規。§ Archive の回転規約により `### [0.40.15]` 〜 `[0.40.4]` を本文を変えずに移動）
- `plugins/gate-driven-development/README.md`（構成一覧に archive-4 を追加）
- `plugins/gate-driven-development/CONTRIBUTING.md`（構成一覧に archive-4 を追加）
- `docs/adr/2026-09-11-env-s-merge-gate.md`（repo-root。新規 / 蒸留した判断）

#### User Action Required

- split-string オプションを含まない正当な形（`env VAR=x gh pr merge 7` / `env -u X -C /B gh pr merge 7` 等）の判定は変わらず、対応は不要
- `env -S` と `eval` / `bash -c` / 別の `env -S` を組み合わせた形などで、証跡が揃っていても `pr-target-unresolvable` の block に当たった場合は、`env -S` を外した `gh pr merge <番号>`（別 repo なら `-R owner/repo` を付ける）の形で実行し直す

#### Validation / Eval Impact

- `tests/test_merge_gate_hook_command_parse.py`（`EnvSplitStringDetectionTests`: 綴り・誤爆側・境界形・深さ・perf 予算）/ `tests/test_merge_gate_hook_env_split_string.py`（新規: 差し込み後の argv・二重計上・打ち切りの対応条件・開示した限界の挙動。加えて本体末尾の `#` による打ち切りの誤判定、split-string 展開個数の上限、実装レビューで見つかった `\c` の一般形と展開個数超過時の `cd_intent` の 2 件: `EnvSplitStringWordStartCommentCutoffTests` / `EnvSplitStringBackslashCEscapeCutoffTests` / `EnvSplitStringExpansionBudgetTests` / `EnvSplitStringExpansionBudgetChdirIntentTests` / `EnvSplitStringBackslashCGeneralFormTests`）/ `tests/test_merge_gate_followup_findings.py`（`EnvSplitStringHookBehaviorTests`: hook サブプロセスで 3 形が block、正当形 `env VAR=x gh pr merge 7` は証跡が揃えば allow）にテストを追加。既存テストの行は変更・削除していない（追加のみ）
- merge gate 系 4 ファイル（上の 3 ファイル + `test_merge_gate_hook_contracts.py`）: 196 passed / 6520 subtests passed（origin/main 64e33e0 では 3 ファイルで 143 passed / 5397 subtests passed）
- `tests/validate-plugin.sh`: `version-not-consumed` を含む全 BLOCK が OK / PASS / SKIP
- `evals/evals.json` への影響なし（hook の reason code・出力 schema の追加・変更なし）

#### Known limitations

- **pre-push gate（`push_command_parse.py`）/ pre-PR gate（`run-pre-pr-gate-hook.sh` の `expand_nested_shell_tokens`）に同型の `env -S` の穴が残る（本 PR の対象外）**。実測: `env -S 'git push origin main'` は `push_command_parse.tokenize` 経由で `is_git_push=(False, -1)`、pre-PR gate の `expand_nested_shell_tokens` は `eval` / `bash -c` しか展開しない。`env -S 'git push --force …'` は引き続き素通りする。別 steering で扱う
- `.cursor-plugin/plugin.json` は `skills` / `hooks` のいずれも宣言していない。Cursor host で merge gate hook 自体が動くかは未検証で、動かない host では本修正の有無に関わらず gate が発火しない
- `git_command_parse.py` にも同名の `_nested_shell_commands` があるが、`env` 分岐は merge gate 側（`gh_command_parse.py`）のみに入れた。同名関数の意図的な非対称であり、統合（共有 lib 化）は本 PR のスコープ外
- `-S` の本体の難読化形（変数展開・クォート分割で `gh` を組み立てる形）は検出できない。`-S` の本体は env 固有の構文（`${VAR}` 展開、`\c` による引数打ち切り、`#` コメント）を持ち、shlex での再走査はその近似にとどまる（既存の `bash -c` 本体と同じ限界）。加えて `bash -c` 本体と違い、env の `-S` の本体では shell の演算子（`;` `&&` `|` `&`）は実 env にとってただの文字なのに、parser は本体を割るときに区切りとして読む。同じ誤読は origin/main のトップ層でも引用符付きの演算子で起きる既存の問題（最後の項目）で、本 PR が広げた面ではない
- env の option 走査で、未知の値取り option の値、または識別子でない `NAME=` 形（代入判定 `^[A-Za-z_][A-Za-z0-9_]*=` は実 env より狭い）を operand（env が起動するコマンド名）と誤認すると、そこで走査を打ち切って `-S` を見落とす（検出漏れ = fail-open 方向）。値取り短オプションの集合（`C` / `P` / `u` / `a`）は macOS の BSD env と GNU coreutils env の和集合、値取り長オプション（`--chdir` / `--unset` / `--argv0`）は GNU coreutils env の列挙で、将来の env に option が増えた場合の追随はテストでは検知できない。打ち切らない設計は env より後ろの別プログラムの `-…S…` の値を shell 本体として再走査して過剰 block になるため、過剰 block を避ける側を選んだ
- `-S` の本体が shlex で割れない形（例 `env -S "echo don't"`）は、`-C` を含まなくても `-S` の本体の tokenize 縮退により `cd_intent=True` になる（出力の `degraded` は False のまま）。`gh pr merge N && env -S "…'…"` のような merge 併記形は過剰 block（fail-closed 方向）になりうる（人間承認 2026-09-10 で開示扱い）
- 1 つの env の argv に現れる `-S` は、入れ子・並び・密着のどの形でも 1 個ずつ既存の深さ予算（`MAX_NESTED_SHELL_DEPTH`=3）を使う。トップを含めて 4 個目以降の `-S` を持つ形（最短例 `env -S-S-S-Sgh pr merge 7`）は検出できず gate が不発火になる（fail-open）。新しい深さ定数は作らない（人間承認 2026-09-10）
- `eval` / `bash -c` / 別の `env -S` が `env -S` の前・本体の中・後続引数の**どこにあっても**、既存経路とこの差し込み経路が同じ merge を 2 層で数え、証跡が揃っていても `pr-target-unresolvable` で過剰 block になりうる（fail-closed）。うち `env -S 'VAR=x' bash -c 'gh pr merge 7'` / `env -S '' eval 'gh pr merge 7'` / `eval env -S 'gh pr merge 7'` / `eval env -S 'gh pr' merge 7` / `env -S 'eval' 'gh pr merge 7'` は origin/main（`pr_number="7"` に解決していた）からの退行、連鎖形 `env -S 'VAR=1' env -S 'gh pr merge 7'` は origin/main では `is_merge=False`（fail-open）だった形を新しく検出したものである。避けられるかは検証していないが、人間が退行分を含めて開示のうえ受容している（人間承認 2026-09-10）
- **値を取る gh の global flag（`-R` / `--repo` / `--repo=` / `--hostname` / `--hostname=`）の値、または `-S` の本体全体の basename が `gh` になる形**は、トップ層がその値や本体 token を gh 本体と読むため打ち切りの対応条件を満たさず、同じ merge を 2 層で数えて `pr-target-unresolvable` で block する（fail-closed）
  - origin/main では現 repo の 旧#7 と読み違えて素通りしていた形（本 PR で block 側に倒した形。origin/main は `pr_number="7"` / `repo_flag=None`、実 env は別 repo の 旧#7 を merge する）: `env -S 'gh -R' o/gh pr merge 7` / `env -S 'gh --repo' o/gh pr merge 7` / `env -S '/usr/bin/gh -R' o/gh pr merge 7` / `env -S'gh -R' o/gh pr merge 7` / `bash -c "env -S 'gh -R' o/gh pr merge 7"` / `env -S '/usr/bin/gh -R o/gh' pr merge 7` / `env -S 'gh --repo=o/gh' pr merge 7` / `env -S 'gh -R' o/r/gh pr merge 7`
  - 訂正: 「本体全体の basename が `gh` になる形は block 側に倒れる」という上の主張は、本体の末尾が語頭 `#` の語（`#/gh` 等）で終わる形では、Fixed の末尾条件を足すまで成り立っていなかった（打ち切りの対応ありと誤判定して素通り）。末尾条件の追加後は、この形も block 側に倒れる（`env -S '/usr/bin/gh -R o/x #/gh' pr merge 7` → `repo_flag="o/x"` / `unresolvable=True`）。本体に `\c` を含む形は、末尾条件とは別に「本体に `\c` があれば位置を問わず対応を確かめられない」扱いに倒すため block 側に倒れる（`\c/gh` の 1 形に限らない一般形も同じ。Fixed 参照）。ただし下の Known limitations の、本体が縮退する形と `\_` 区切りの形は例外で、とくに `\_` と語頭 `#` を組み合わせた `env -S '/usr/bin/gh\_-R\_o/x\_#/gh' pr merge 7` は merge を検出するが `repo_flag=None` / `unresolvable=False` のまま現 repo の 旧#7 と読み違える（origin/main と同じ）
  - origin/main が解決していたのに過剰 block になる形（退行）: `-S` の本体と後続引数の両方に `-R` を書く `env -S 'gh -R o/gh' -R o/r pr merge 7`（origin/main は `repo_flag="o/r"` に解決。人間承認 2026-09-11）と、その派生として `--hostname` の値の basename が `gh` になる `env -S 'gh --hostname x/gh' pr merge 7` / `env -S 'gh --hostname=x/gh' pr merge 7` / `env -S 'gh --hostname' x/gh pr merge 7` / `env -S '/usr/bin/gh -R o/r --hostname h/gh' pr merge 7`（origin/main は `pr_number="7"` に解決。実 gh は `pr merge` に `--hostname` を許さず失敗する形なので、運用上の過剰 block にはならない）
- 1 つの simple command に `env -S` を n 個並べた形は、区切りなしで並べると各 argv が後続の split-string を抱えて再展開され、個数に対して指数的に伸びる（Fixed の最後の項目）。1 層で展開する個数に上限 8 を設けたため、n=20 / n=60 の区切りなし・`&&` 区切り・`eval` 混在の形は、上限を超える入力として解析せず block する経路で既存の perf 予算内に収まる（該当する既存 perf テスト 4 本の assert の期待値は変えていない）。上限内に残る語数比例の伸びは下の項目で開示する。余裕はテスト環境での実測値にとどまる（timeout を超えると hook は無出力で allow になる。`[0.41.11]` の開示と同じ）
- 本 PR で塞いでいない origin/main からの既存 fail-open 3 件は別タスクで扱う: トップレベルの引用符付きの演算子による PR 番号・repo 指定の読み落とし（例 `gh pr merge -t ';' 8` → `pr_number=None`）/ `env -u gh GH_REPO=o/r gh pr merge 7` の `GH_REPO=` の見落とし（`env_repo_conflict=False`。`_has_env_repo_prefix` が basename が `gh` の最初の token で止まる。`-S` の本体の中 `env -S '-u gh GH_REPO=o/r /usr/bin/gh' pr merge 7` でも同じ）/ ANSI-C クォート `$'…'` を shlex が解さないため `gh` を見失う形（例 `$'gh' pr merge 7`。`env -S` の有無に関わらずトップ層でも起きる、tokenizer 全体の既存の穴。impl-gate Task 5 Round 2 で発見。origin/main と同じ判定で退行ではない）
- 本体が shlex で割れない（縮退する）形で、後続引数で merge が完成する形は検出しない（例 `env -S 'gh pr "' merge 7` → `is_merge=False`。hook 不発火 = fail-open）。縮退した本体には後続引数を付けないため `merge` を見ない。origin/main と同じ判定で、人間が歯止め「同じクラスタの新しい fail-open は受容しない」の例外として開示のうえ受容した（人間承認 2026-09-11T13:36:09+09:00）。本体に `\c` を含む形（例 `env -S 'gh pr \c"' merge 7`）は、縮退の判定より前に `\c` の有無を見るようになったため、この限界の対象外で `is_merge=True` / `unresolvable=True` になる（Fixed 参照。impl-gate Task 5 Round 2 で発見・訂正）
- env の option 区間にリダイレクトがある形（`env 2>/dev/null -S 'gh pr merge 7'` / `env -S >/dev/null 'gh pr merge 7'` 等）は、option 走査がリダイレクトを operand と読んで打ち切り、`-S` を見落とす（`is_merge=False`。fail-open）。origin/main と同じ判定で、上と同じく歯止めの例外として受容した（人間承認 2026-09-11T13:36:09+09:00）
- `-S` の本体で env 固有の区切り `\_` を使う形は、parser の分割が `\_` を区切りとして再現しないため、次の 2 通りに読み違える（fail-open）。どちらも origin/main と同じ判定で、上と同じく歯止めの例外として受容した（人間承認 2026-09-11T13:36:09+09:00 / 2026-09-11T14:14:53+09:00）
  - hook の不発火: `env -S 'gh\_pr\_merge\_7'` → `is_merge=False`
  - 本体を 1 つの token に見せて repo を読み違える: 本体 `/usr/bin/gh\_-R\_o/x\_#/gh` + 後続引数 `pr merge 7`（`env -S '/usr/bin/gh\_-R\_o/x\_#/gh' pr merge 7`）→ `is_merge=True` / `pr_number="7"` / `repo_flag=None`。現 repo の 旧#7 と読むが、実 env は `\_` で割って `#` 以降を捨て、o/x の 旧#7 を merge する。Fixed の末尾条件の対象外（同じ形で `#` の代わりに `\c` を使うと、本体に `\c` を含む形として位置を問わず block 側に倒れる）
- split-string の個数が上限 8 以内でも、同じ simple command に語を多数並べると、解析時間が語数に比例して伸びる（例 `env -Sx ` × 8 + 語 40000 個 + `gh pr merge 7`）。`timeout: 10` を超えると hook は無出力で allow になる（fail-open）。10 秒に届く長さは負荷に依存し、通常の負荷では 100 KB 前後（測定値は約 90 KB）、高負荷下（load average 60〜73）では 20 KB 前後まで下がる。origin/main は同じ入力を 1 秒未満で merge と判定するので、**この入力に限れば origin/main より悪い**。ただし同じ長さの `eval` の並びは origin/main でも既に素通りし（`eval` 単独なら 513 byte で 10 秒に届く）、hook の時間制限を使う素通りの手段が新しく増えるわけではない。閉じるには長さの予算（展開した argv の語数の合計の上限）という別の仕組みが要る。人間が歯止めの例外として開示のうえ受容した（人間承認 2026-09-11T14:14:53+09:00）
- 上限の裏返しの過剰 block（fail-closed）: 1 つの層に、split-string を持つ `env` を 9 個以上並べたコマンド（1 つの `env` につき最初の `-S` だけを数える。同じ `env` に `-S` を複数書いても 1 個と数える）、または本体に `\c` を 1 つでも含むコマンドは、`gh pr merge` を含まなくても解析せず `is_merge=True` / `unresolvable=True` になる（payload に `merge` を含み、かつ active な GDD repo か root を解決できない場所で実行すると block される）
- `env` が simple command 内の実行位置以外（他コマンドの単なる引数）にあっても、tokens 全体から basename 一致で `env` を探すため `-S` の本体を実行内容として再解析し、過剰 block になる（fail-closed）。例: `rg env -S 'gh pr merge 7'` / `echo env -S 'gh pr merge 7'` は検索・表示コマンドであり merge を実行しないが `is_merge=True` になる（PR 旧#67 のインラインレビュー指摘で発見）。この過剰検出は、`rg gh pr merge 7` / `echo gh pr merge 7`（`env` を介さない形）が同じ理由で既に `is_merge=True` になる既存・受容済みの過剰 block クラスと同型であり、`gh` 本体側を直さずに `env -S` 側だけを直すと、`sudo` / `nohup` / `timeout` / サブシェル `(...)` / コマンド置換 `$(...)` / `if …; then …; fi` 等の wrapper・制御構文経由で実行される形が検出対象から外れ、新たな fail-open を生む（実測・独立レビューで発見。「fail-open は受容しない」歯止めに反するため見送った）。`bash` / `eval` を含め、この過剰検出クラス全体をどう閉じるかは別 steering で扱う

### [0.42.0] - 2026-09-09

#### Summary

`[0.41.10]` は done guard Check 2 の判定を「未完了検出は無条件・列位置非依存 / 完了受理は canonical schema」という 2 つの不変条件へ還元した。その後、この 2 不変条件を土台にした独立レビューが 9 ラウンド走り、high 34 件を検出・修正したが収束しなかった。根本原因は判定規則の実装品質ではなく**仕様側の欠落**だった。`skills/gdd-ac-verification/SKILL.md` は Verification 行のフィールド（method / status / evidence / notes）だけを規定し、行のシリアライズ形式を規定していなかった一方、`references/self-contained-contract.md` は閉じた文法を暗黙に宣言し、実装は歴史的な実データに合わせて 8 通りの行形を受理していた。**未定義の形式に正しいパーサは書けない**。本 entry は `## Verification` 節が受理する行の文法を「空行 / `- なし` / canonical header / canonical separator / 4 列 canonical data 行（3 形）」の閉じた列挙 1 本に統一し、contract / SKILL / `done_guard.py` を同一文法へ揃える。詳細な設計判断は後継 ADR（`docs/adr/2026-09-08-verification-closed-grammar.md`）を参照。

#### Breaking Contract Changes

- `## Verification` 節の受理文法を閉じた行種の列挙に統一した。列挙外の行（list 行 / 引用行 / インデント行 / 装飾 status / 注記付き status / ラベル形 / 日本語 header 語 / 外側パイプ省略 / 全角パイプ / 凡例 list / 5 列 ROW-ID 表など）はすべて schema 違反として block されるようになった
- 節に重なる fenced code block（記入例 fence を含む）は schema 違反になった（AC-7）。記入例・散文は `## Verification Notes` 節へ移すこと
- **唯一の block→done 方向の挙動変化**: `notes_only_status_word_is_detected`。旧実装の `_has_unfinished_status` は全セルを**列位置非依存**で走査していたため、status 列以外のセル（notes / evidence）に書かれたリテラル `pending` / `fail` も未完了として block していた。新文法は status 列を**固定 2 列目**としてのみ判定するため、この行は通るようになった。これは旧 ADR（`docs/adr/2026-09-06-done-guard-verification-header.md`）の不変条件 (1)「未完了の検出は無条件・列位置非依存」に直接触れる変更であり、後継 ADR で明示的に上書きしている。実コーパス実測では該当件数 0 件（下記 Migration Cost）
- `done_guard.py` から列位置推定・補助表判定・凡例除外・注記位置規則・header 境界規則・コードスパン保護に関わる 18 個の推論（AC-8 の 16 シンボル + `_CODE_SPAN` / `_mask_code_spans`）を削除した。`done_guard.py` は origin/main（`c421a9b`）比で 650 行 → 289 行（154 insertions / 515 deletions。2026-09-10 の AC-9 第 5 形の追補を含む。`done_guard.py` は `c421a9b` から origin/main `64e33e0` まで変更なし）
- **AC 検証行（`method=ac:`）が 1 件も無い `## Verification` 節は「検証行がありません」で block される**（AC-9 第 5 形 / 2026-09-10 追補）。`security_evidence` 行・`refactor-checkpoint` 行だけの表は AC の検証の代わりにならない。第 5 形に未完了/失敗行があれば、「検証行がありません」と未完了/失敗の件数を併記する
- **LF / CR / CRLF 以外の行区切り文字（`\x0b` `\x0c` `\x1c`〜`\x1e` `\x85` U+2028 U+2029）を含む tasklist は block される**（2026-09-11 独立レビュー R23 / PR 旧#65 レビュー対応）。`str.splitlines()` がこれらの文字でも行を分けるため、行の途中の `U+2028## X` で `## Verification` 節が切れ、後ろの `fail` 行が節の外に出て done が通っていた（変更前からの fail-open）。block 理由は文字そのものではなく `U+XXXX` 表記と原文行番号を示す。検査は tasklist 全体への入口検査で、Check 1（Current / Pending / Completed）が同じ文字で節を読み違える形も併せて閉じる

#### User Action Required

1. **`## Verification` 節を canonical schema へ書き直す**。canonical 形は次の 3 行（header + separator + data 行）:

   ```
   | method | status | evidence | notes |
   |---|---|---|---|
   | method=ac:AC-1 | pending | - | - |
   ```

   この 3 行は行頭に空白を付けずに書くこと（閉じた文法では字下げ行は schema 違反になる）。

   block メッセージが canonical 3 行を回復案内として提示し、違反行ごとにラベルを付けるので、agent は block を 1 回受けた時点でその指示に従って自分で書き直せる。書き直しが必要なのは検証行（`method=` / AC ID / `security_evidence` / `refactor-checkpoint` を含む行、または `pending` / `pass` / `fail` / `n/a` / `unsupported` の status トークンを含む行）のみで、それ以外の**散文・凡例・補助表・検証コマンド一覧は消さずに `## Verification Notes` 節へ移す**こと（`## Verification` の直後に置くのが推奨形）
   - `## Verification` の**初期枠**（節を新設する時点でまだ検証行が無い状態）は、空のままにせず **canonical header + separator の 2 行だけを置く**こと。この 2 行だけの表は空節・`- なし` だけの節と同様に「検証行がありません」で fail-closed に block される（done までに検証行を最低 1 行足す必要がある点は変わらない）。**初期枠を canonical で作る利点は、後から検証行を足すときに schema 違反の形で書き始める余地が無くなること**であり、文法違反による初回 block を減らす導線として推奨する
2. **外部 verifier（Snyk のスキャン結果を書く verifier plugin）の row writer を canonical 表行形式へ更新する必要がある**。現状の writer は `- SECURITY-CODE | security_evidence:code | pending | - | 初期値` のような 5 列 list 行を書く実装を持つ。これは新文法では schema 違反になる。writer 修正の 2 点: (a) `method=` prefix を付与する、(b) 4 列表形式（`| method=security_evidence:code | pending | - | 初期値 |`）へ変更する。**この writer 修正は verifier plugin 側（本 repo 外）の作業であり、本 PR の対応範囲外**。writer が legacy 形式で書いた行が block された場合、block メッセージが再生成される旨・writer 修正 2 点・verifier plugin の local 設定ファイル（project の `.claude/` か global の `~/.claude/`）の `enabled: false` による暫定回避（副作用: 設定を置いただけでは block は解除されない / Snyk の Stop ゲートとスキャン状態追跡も止まり `~/.claude/` 側は全プロジェクトに効く / writer 修正後は設定を戻し verifier を再実行してから done にすること）を専用の分岐で案内する。2026-09-10 の AC-20 改訂により、この暫定回避は**人間が判断して行う操作**で agent は設定しない。status が `fail` / `pending` の legacy 行は削除も移動もせず、原因を解消して verifier を再実行する。残るのが legacy 形式の行だけなら、writer 修正までは agent は `<gdd-stop reason="blocked">` で停止して人間へ報告する
   - **writer が canonical 化された後の smoke assert 反転手順**: `scripts/external-verifier-smoke.sh` の契約テストは、現状 writer が legacy list 行を upsert した後も `_scan_verification` の `line` 種別違反が残ることを assert している（下記 Known Limitations 参照）。snyk plugin 側の writer が canonical 4 列形へ修正されたら、この assert を「violations 0 件 + `method=security_evidence:code` 行が `_classify_verification_line` で data と分類される（`verification_data_rows` は AC 行だけを数えるので rows では数えない）」へ反転すること
3. **完了済み（done 済み）セッションは影響を受けない**。done guard の Stop hook は完了済みセッションに対して再実行されないため、過去に done へ遷移したセッションの tasklist.md が新文法に適合していなくても遡って block されることはない。影響を受けるのは、今後 `done` へ遷移しようとする進行中セッションのみ
4. **`## Verification` には `method=ac:` 行を 1 件以上置く**（2026-09-10 追補）。external verifier が書く `security_evidence` 行だけ、または `refactor-checkpoint` 行だけの節では done できない。block されたら、各 AC の検証結果を `method=ac:<AC_ID>` 行として追加する
5. **tasklist に LF / CR 以外の行区切り文字を置かない**（2026-09-11 追補）。block 理由に示された行の見えない文字を削除する（半角空白への置き換えは、行頭のタスク行を字下げにして Check 1 から見えなくすることがあるので勧めない）。通常の改行（LF）への置き換えは、後ろの行が別の節に移って検証行が `## Verification` の外に出ることがあるので勧めない。手元の tasklist 469 件のうち該当は 1 件だった

#### Migration Cost

実コーパス実測（時点依存のスナップショットとして扱う。断定形では読まない）。

- 導出コマンド: `python3 plugins/gate-driven-development/scripts/measure-done-guard-drift.py`
- measured_at: 2026-09-09T05:59:52+09:00
- integration_ref: origin/main
- population: 459 tasklist.md
- done→block: **131 件**
  - done→block[grammar]（文法由来）: **130 件**
  - done→block[fence]（fence 由来）: **0 件**
  - done→block[both]（両方）: **1 件**
  - done→block[n/a]: **0 件**
- block→done: **0 件**（唯一のクラス `notes_only_status_word_is_detected` の実データ該当数）
- 再実測（AC-9 第 5 形の追加後 / 2026-09-10 追補）: measured_at: 2026-09-10T17:13:48+09:00 / integration_ref: origin/main / population: 455 / done→block: 129（grammar 128 / fence 0 / 両方 1 / n/a 0）/ block→done: 0。第 5 形による増分は 0 件（新実装単独で done を返すファイルが 0 件のため。コーパスが新文法へ移行していない時点のスナップショット性質で、恒久的な性質ではない）。母集団と件数の減少（459 → 455 / 131 → 129）はローカル実データの入れ替わりによる

#### Known Limitations

- **AC-13 条項 (b)（`external-verifier-smoke.sh` が exit 0 で終了すること）は unsupported**。`--snyk-plugin-root` を指定しても verifier plugin 側の writer が `pass` ではなく `fail` を書き、smoke スクリプト `:123` の assert で失敗する。**base commit `c421a9b` でも 2 つの起動形（`--snyk-plugin-root` 指定あり / なし）の両方で同一に失敗する**ため、この不成立は本 PR が持ち込んだ退行ではない。条項 (a)（smoke が書く節そのものの文法適合）は環境非依存の代替テスト（`_scan_verification` へ初期節を直接掛ける契約テスト）で検証済み。なお smoke の初期節は AC 行を持たないので、writer の canonical 化後は第 5 形（AC 検証行 0 件）で block される。
- **done guard は AC カバレッジを検査しない**。Check 2 が見るのは `## Verification` 節の行の形と、AC 検証行が 1 件以上あることだけである（スコープ判断）。`scripts/lint-ac.py` は AC 参照が tasklist 全体から消えた場合（削除の一部）を警告で出すが block せず、他節への移動は検出しない。後続対応は PR 本文を参照（Issue は未起票）
- `method=security_evidence:*` 行の手書き禁止は機械強制ではなく、block メッセージと contract の文言のみで抑制する
- 外部 writer（legacy 行）について、`fail` / `pending` の行を削除しないこと、`enabled: false` を agent が置かないことも、block メッセージの文言だけで抑制しており機械強制ではない（2026-09-10 AC-20 改訂）
- 行区切り文字の封鎖は tasklist が対象で、state.md の `Route In Progress`（Check 3）には効かない。同じ文字で `none` に偽装できる形と、`## Pending Tasks` 見出しの前の空白・タブ・BOM で未完了タスクがCheck 1 から見えなくなる形（いずれも変更前から）は、Check 1 / Check 3 を変更しない本 entry の範囲外として次の PR で扱う

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/done_guard.py`（Check 2 を閉じた文法パーサへ置換、AC-8 の 16 シンボル + `_CODE_SPAN` / `_mask_code_spans` を削除）
- `plugins/gate-driven-development/hooks/scripts/lib/tasklist_parse.py`（`strip_fenced_lines_marked()` 追加、AC-7 の fence 位置受け渡し）
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`（`_verification_errors` / `_build_recovery_hints` / `_build_why_explanations` を新文法・fence 違反 2 種へ追従）
- `plugins/gate-driven-development/hooks/scripts/lib/done_block_message.py`（新規。block reason のメッセージ生成（`_build_recovery_hints` / `_build_why_explanations`）を `gdd_stop_hook.py` から分離。code-health の 1 ファイル 1500 行目安対応。振る舞いは移設時点では同一（その後 AC-9 第 5 形の分岐、Notes ヒント、外部 writer 分岐の文言（AC-20 改訂）を変更））
- `plugins/gate-driven-development/references/self-contained-contract.md` / `plugins/gate-driven-development/references/faq.md` / `plugins/gate-driven-development/references/phase-progression.md` / `plugins/gate-driven-development/references/skill-responsibility-matrix.md`（Verification 行の記述を新文法へ）
- `plugins/gate-driven-development/skills/gdd-ac-verification/SKILL.md` / `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`（§ Verification Schema に同一文法ブロック）
- `plugins/gate-driven-development/scripts/external-verifier-smoke.sh`（初期節を canonical 表へ、凡例 2 行を除去）
- `plugins/gate-driven-development/scripts/measure-done-guard-drift.py`（新旧 API 両対応の drift 計測）
- `plugins/gate-driven-development/tests/`（149 case の契約テスト新設、共有 fixture の canonical 化、fence 契約反転、文法ブロック一致テスト新設ほか）
- `docs/adr/2026-09-08-verification-closed-grammar.md`（新規。後継 ADR）
- `docs/adr/2026-09-06-done-guard-verification-header.md`（`Superseded by` 追記）
- `docs/VERSIONING.md` / `.claude-plugin/plugin.json` / `.codex-plugin/plugin.json` / `.cursor-plugin/plugin.json`（版数 0.42.0）
- （2026-09-10 追補 / AC-9 第 5 形）`hooks/scripts/lib/done_guard.py`（`verification_data_rows` を AC 行に限定）/ `hooks/scripts/gdd_stop_hook.py`（`_unfinished_message` への集約と第 5 形の併記）/ `hooks/scripts/lib/done_block_message.py`（第 5 形 + 未完了で Notes 導線を出さず AC 検証行の追加を案内）/ `references/self-contained-contract.md` / `skills/gdd-ac-verification/SKILL.md`（AC 検証行 1 件以上の要求）/ `tests/test_verification_ac_row_required_contract.py`（新規）ほか既存テスト 3 ファイル / `docs/adr/2026-09-08-verification-closed-grammar.md`（Consequences 追記）
- （2026-09-10 独立レビュー R20 / AC-20 改訂）`hooks/scripts/gdd_stop_hook.py`（違反行ラベル: 判定語に AC ID / `n/a` / `unsupported`、既定ラベルを条件付きの文言へ、外部 writer の legacy 行に専用ラベル）/ `hooks/scripts/lib/done_block_message.py`（外部 writer 分岐の案内を人間の操作・削除も移動もしない・停止して人間へ報告へ、Notes ヒントの検証行の例、legacy 行があるときは「唯一の回復手順」を出さない）/ `tests/test_verification_block_message_contract.py` / `tests/test_verification_ac_row_required_contract.py` / `tests/test_t8_final_verification_contract.py` / `tests/test_verification_closed_grammar_release_notes_contract.py`
- （2026-09-11 PR 旧#65 レビュー対応）`hooks/scripts/lib/done_block_message.py`（schema 違反と AC 検証行 0 件の回復ヒントを `_verification_shape_hints` へ切り出し、AC 検証行 0 件では未完了の有無にかかわらず `method=ac:<AC_ID>` 行の追加を案内する。「唯一の回復手順」は schema 違反のときだけ出す。AC 検証行 0 件の判定は hook 自身の見出し行への行頭一致にし、block 理由に載る行本文の文言で案内が切り替わらないようにする）/ `tests/test_verification_ac_row_required_contract.py` / `tests/test_stop_hook_done_guard_regression_contract.py`（header のみの節で旧挙動を pin していた assert を反転）
- （2026-09-11 独立レビュー R23 の修正）`hooks/scripts/lib/done_guard.py`（`_line_break_char_error`: LF / CR 以外の行区切り文字を含む tasklist の block 理由）/ `hooks/scripts/gdd_stop_hook.py`（tasklist を 1 回だけ読み、入口で行区切り文字を検査。schema 違反メッセージに legacy 行の件数行を追加）/ `hooks/scripts/lib/done_block_message.py`（legacy 行を違反行全件で数える `_legacy_writer_headline`、行区切り文字の回復ヒント）/ `references/self-contained-contract.md` / `skills/gdd-ac-verification/SKILL.md`（改行は LF / CR / CRLF だけの規定）/ `tests/test_done_guard_line_break_chars_contract.py`（新規）/ `tests/test_verification_block_message_contract.py`
- （2026-09-11 origin/main `19b5ebc`（PR 旧#66 / `### [0.41.12]` X-35 AC 閉包チェック）の merge conflict 解消）`docs/VERSIONING.md`（現行バージョンは v0.42.0 を維持し、統合先の消費済み版数を main が実際に出荷した v0.41.12 に更新）/ `CHANGELOG.md`（`### [0.42.0]` と `### [0.41.12]` の両エントリを新しい順のまま保持）/ `.claude-plugin/plugin.json` / `.codex-plugin/plugin.json` / `.cursor-plugin/plugin.json`（version は競合せず v0.42.0 のまま）。実装ファイルの競合は無し（PR 旧#65 と PR 旧#66 は重ならないファイルを変更していた）

#### Validation / Eval Impact

**以下の数値は測定時点のスナップショットであり、以後も成り立ち続ける不変条件ではない**。どこかにテストを 1 本足せば偽になる。したがって、この節の数値を「生きた全体スイート実測」に束縛する検査は置かず、記載値どうしの内部整合だけを `tests/test_t8_final_verification_contract.py` が検査する。

- measured_at: 2026-09-11T14:22:03+09:00
- 測定環境: 本 PR の GDD worktree（`.steering/20260908-verification-closed-grammar/` が存在する）。`.steering/*/` は `.gitignore` 対象で repo にコミットされないため、**クリーンチェックアウトでは dogfooding 3 本が skip する**（下のクリーンチェックアウト行）。origin/main（`64e33e0`）を取り込んだ後のツリーで、PR 旧#65 のレビュー対応（AC 検証行 0 件の回復案内）を加えた後に測定した
- `python3 -m pytest plugins/gate-driven-development/tests -q`: **2443 passed, 1 skipped, 14656 subtests passed**, exit 0（1052.07s / 0:17:32）。failure 0
- baseline `2413 passed, 1 skipped, 14636 subtests passed`（**導出値**: 上の全体回帰から、2026-09-10 追補と 2026-09-11 の PR 旧#65 レビュー対応で新設した契約テスト 2 ファイルの実測分を除いた値。同じ追補で既存テスト 1 本を削除し、origin/main の取り込みで main 側のテストも加わっているため、過去の単一時点の実測を baseline にすると増分内訳が負の項を含んでしまう。回帰が無いことの証跡は全体回帰の failure 0 で示す）
- 増分の内訳（2026-09-10 追補と 2026-09-11 の PR 旧#65 レビュー対応が新設した契約テスト 2 ファイル）: `test_verification_ac_row_required_contract.py` **23 passed / 7 subtests**、`test_done_guard_line_break_chars_contract.py` **7 passed / 13 subtests**、合計 **30 passed / 20 subtests**
- 本 entry の既存契約テスト（参考。増分には含めない）: `test_verification_closed_grammar_release_notes_contract.py` 14 passed / 14 subtests、`test_t8_final_verification_contract.py` 7 passed / 0 subtests
- クリーンチェックアウト（`.steering/*/` 不在）での同一コマンド: **2440 passed, 4 skipped, 14656 subtests passed**（dogfooding 3 本が passed から skipped へ移るだけで、failure は増えない）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0（`version-not-consumed: OK (shipping v0.42.0; integration target consumed v0.41.12)`）
- 再測定（origin/main `19b5ebc`（v0.41.12 / PR 旧#66 X-35 AC 閉包チェック）を取り込む merge conflict 解消後 / 2026-09-11 追記）: measured_at: 2026-09-11T17:50:04+09:00 / `python3 -m pytest plugins/gate-driven-development/tests -q`: **2457 passed, 1 skipped, 14690 subtests passed**, exit 0（834.31s / 0:13:54）。failure 0。増分（origin/main が追加した `test_planning_reviewer_ac_closure_contract.py` 分）: **14 passed / 34 subtests**。`bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0（`version-not-consumed: OK (shipping v0.42.0; integration target consumed v0.41.12)`）

### [0.41.12] - 2026-09-11

#### Summary

`gdd-planning-reviewer` に「AC 閉包チェック（AC Closure Check）」節を追加した。全称・網羅・同値・不変・否定を表す発火語を含む AC に、有限の入力集合（列挙）か、実行できる計測コマンドと合否基準を添えさせる。閉じられない述語は AC から外して `Honest Limitations` に開示させる。ただし安全境界・ユーザーが明示した完了条件・不可逆操作の述語は、この退避を使わず既存の gate 規則に従わせる。2026-09-10 に GDD 自身の修正 3 本（X-28 / X-34 / Verification 文法）のレビューループが収束しなかった原因は、完了条件が曖昧なことではなく「開いている」こと（例: X-28 AC-18「任意の shell コマンド文字列から chdir の意図を検出する」）だった。本変更はその入口側の対策（X-35）。

#### Added

- `agents/gdd-planning-reviewer.md`: `## Additional Design-Quality Checks` に `### AC 閉包チェック（AC Closure Check）` 節を追加。発火語の確定リスト（日本語 18 語 + 英語 8 語）/ 閉じ方 (a) 列挙・(b) 計測コマンドと合否基準 / 閉じた列挙を包む開いた見出しの扱い / `Honest Limitations` への退避（安全境界・ユーザーが明示した完了条件・不可逆操作の述語は退避の対象外とし、既存の gate 規則に従わせる） / 重大度の表 / 悪い例→閉じた例 2 件（X-28 AC-18、X-34 AC-3 の見出し）
- `agents/gdd-planning-reviewer.md`: `## Phase Context` の Requirements phase と Design phase の両方から同節を参照する文を追加
- `tests/test_planning_reviewer_ac_closure_contract.py`: 契約テスト。節の中に閉じ込めた逐語 needle 17 件（免除 2 行・安全境界等の除外を含む）/ 見出しの一意性と配置（`## Additional Design-Quality Checks` の配下）/ 新節と Design phase 節に advisory が戻らないこと / 除外文が名指しする参照先 2 つ（Fail-closed Check の見出しと、完了条件の「非スコープか Open Questions に理由付き」）が実在すること / 実害の出た 4 文言の発火語（「任意の」「同一」「増やさない」「残っていない」）がリストに残っていること / 変異テスト M1〜M7（節の削除・各 phase の参照文の削除・発火語 1 語の削除・表の行や完結した文の後ろへの語の追加で赤になること）

#### Changed

- planning reviewer が、閉じ方も開示も無い開いた述語を `Open Predicate in AC` として報告するようになる。requirements phase では **Medium**（blocking）、design phase では **Low**（design phase の AC は承認済みで閉じ直すには amendment が要り、`gdd-design-gating` は high と medium の全解消を approved 条件にしていて advisory を区別しないため）
- PR 旧#64 のレビュー（P1）を受けて、安全境界の述語を丸ごと退避させない例外と専用の finding（`Unapproved Safety Predicate Removal` High）を検討したが、マージ前の独立レビュー 4 回で、例外と既存 gate 規則（Fail-closed Check・再入レビュー規則・完了条件の非スコープ規則）の交差から隣の穴が続いたため採らなかった（どのリリースにも出荷していない）。代わりに (v) の退避の対象から安全境界・明示された完了条件・不可逆操作の述語を除く 1 文だけを置いた

#### Known limitations

- 発火語リストに無い言い回し（例:「壊れない」「問題なく動く」）で書かれた開いた述語は、この節の発火条件に乗らない。拾えるかどうかは reviewer の読解次第になる
- 契約テストは reviewer 本文に契約文があることを固定するだけで、reviewer（LLM）が実際にこの指摘を出すかは検証しない。レビューの巡回数が減るかどうかも本変更では測れない。効果は、マージ後に requirements-gating を通るタスクで観測する
- `quick (express)` と `trivial` は requirements-gating を通らないため、この節は走らない。`references/requirements-template.md` 側への規則追加は、references の行数予算のため行っていない
- 「その列挙が述語を具体化できているか」の判定は reviewer の判断に残る。この節は判定の型を与えるだけで、判定そのものは機械化しない
- どの述語が安全境界・ユーザーが明示した完了条件・不可逆操作に当たるかの判定も reviewer の読解に残る
- 契約テストが検知する変異は次の集合に限る: 節・参照文の削除 / needle 内の語の削除・変更 / 表の行と完結した文の後ろへの語の追加 / 文中の needle の述部の後ろへの語の追加（意味の反転）/ 発火語 1 語の削除 / 節の `## Additional Design-Quality Checks` の外への移動 / 新節と Design phase 節への advisory の復帰。これ以外（例: needle の手前への語の追加、needle どうしの間への文の差し込み、反転した写しの追加、箇条書きの行末への後続文）は検知しない。「どんな変異でも検知する」という開いた目標にせず、PR 旧#64 のレビューで求められた集合で閉じた
- **安全境界の述語について、この節には既知の穴がある（マージ前の独立レビュー 5 回目 旧#1 High・旧#2 Medium。開示して受容）**。(1) 閉じ方 (a)（列挙）や見出しの縮小で安全境界の述語を狭め、残りを `Honest Limitations` にも承認ポイントにも書かない AC を、この節は拾わない（表 1 行目で対象外になる）。X-35 は AC を閉じる方向の圧力を持つため、安全境界の AC を黙って狭める圧力にもなりうる。(2) (v) の除外文（安全境界等の述語はこの退避を使わない）に反して `Honest Limitations` へ移した AC を拾う指摘も無い。委譲先の Fail-closed Check が扱うのは未設定時のデフォルト・untrusted input の区切り・injection のトリガー文字列の 3 項目だけで、Mission の blocking 接地条件は指摘を生む規則ではない。移した述語は HITL の Honest Limitations には表示される。安全境界の述語と X-35 の閉じ方の相互作用は、`skills/gdd-requirements-gating/SKILL.md`・`references/` 側と一緒に後続タスクで設計する
- 「レビューの対象を AC の閉じた集合に限定する」「完了条件を『high 0』から『閉じた集合で high 0 + 範囲外の発見に処遇を記録』に置き換える」の 2 点は範囲外（`independent-review.md` / `reviewer-common.md` を触るため、W-29 マージ後に別タスクで扱う）

#### Affected Files

- `agents/gdd-planning-reviewer.md` / `tests/test_planning_reviewer_ac_closure_contract.py` / `CHANGELOG.md` / `docs/VERSIONING.md` / 3 manifest

#### Breaking Contract Changes

- なし（reviewer set・gate 順序・state field は変えない）。ただし planning reviewer の指摘観点が増えるため、requirements-gating 中のタスクでは、開いた述語を含む AC に新しい blocking 指摘（Medium）が出うる。design phase では開いた述語は Low で gate を止めない

#### User Action Required

- インストール済みプラグインが main チェックアウトへの symlink の場合、pull した時点で稼働中のすべての GDD セッションの planning reviewer にこの観点が加わる。requirements-gating / design-gating 中のタスクがあるなら、pull の時期を調整する
- AC を書くときは、発火語を含む述語に列挙か計測コマンドを添えるか、閉じられないものを `Honest Limitations` へ移す

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`: `2273 passed, 1 failed, 1 skipped, 14464 subtests passed in 401.39s`（tip `e68bd3c`）。failed の 1 件は `hooks/` の時間閾値テスト `test_merge_gate_followup_findings.py::MergePrefilterScopeTests::test_large_payload_stays_far_below_the_hook_timeout` で、並列負荷下の flaky（この回は機械が高負荷で所要が通常の約 3.5 倍。同じテストを単独で直列実行すると 2 回とも pass。本 PR の差分は `hooks/` に 0 行）。直前の `0ac4c95` では同じコマンドで `2274 passed, 1 skipped`・failed 0。PR 旧#64 のレビュー指摘 2 回分・マージ前の独立レビュー 5 回分・実装レビューの advisory を反映し、安全境界の専用の finding は採らなかった最終コード
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0。`version-not-consumed: OK (shipping v0.41.12; integration target consumed v0.41.11)` を含む全 BLOCK が OK/PASS/SKIP
- `bash plugins/gate-driven-development/scripts/measure-budgets.sh`: headroom は references 20 行 / express 15 tokens / standard 132 tokens で変更前と同値（agents・tests は計数対象外）
- 実ファイルへの変異で赤になることを確認: （tip `0ac4c95` で測定）新節の削除 → 25 failed / 免除 2 行の削除 → 2 failed / 新節を `## Phase Context` の後ろへ移動 → 1 failed / 安全境界等の除外の文を削除 → 2 failed / Design phase の参照文を advisory に戻す → 3 failed / 除外の括弧書きから「秘匿」を削除 → 1 failed（いずれも復元後に GREEN）
- 意味の反転を検知することを確認（in-memory 変異）: 除外の文の後ろに後続文 → `v-safety-carveout` 赤（M7）/ 閉じ方 (a) に「必要はない」→ `ii-enumeration` 赤 / 表の行の後ろに「（blocking）」→ `vi-severity` 赤 / Design phase の参照文の後ろに後続文 → `phase-ref-design` 赤（PR 旧#64 レビュー指摘。M5・M6 としてテストに固定）/ 行末で終わる完結文 3 本の後ろに後続文 → 各 label 赤（impl-gate F-14。M7 としてテストに固定）
- `evals/evals.json` / `scripts/grade_evals.py` への影響なし

### [0.41.11] - 2026-09-08

#### Summary

`run-merge-gate-hook.sh` の repo root 解決を、hook プロセス cwd 単独から「hook プロセス cwd → payload cwd → コマンド先頭の単一 `cd <絶対パス>`」の 3 候補へ拡張した。GDD worktree 運用でセッションを repo 外のディレクトリから起動すると `gh pr merge` が `repo-root-unresolvable` で恒久 block される問題（2026-09-06〜07 の実測 4 件: PR 旧#37 ×2 / 旧#52 / 旧#57）を、fail-closed を緩めずに解消する。

#### Added

- `hooks/scripts/lib/gh_command_parse.py`: `parse_gh_pr_merge()` の戻り値に `cd_target`（cwd 変更 token の受理条件を満たす `cd` の引数、または None）を追加
- `hooks/scripts/lib/gh_command_parse.py`: 戻り値に `cd_intent`（走査範囲に cwd 変更 token `cd` / `pushd` / `popd` / `env -C` / `env --chdir` が 1 つでもあれば true）を追加。`cd_target=None` の理由が「chdir の語彙が無い」か「語彙はあるが AC-4 で不採用にした」かを hook が区別するための signal（impl-gate T-8/T-9 F-1、人間承認済み案 (a)(1)）
- `hooks/scripts/run-merge-gate-hook.sh`: 新 reason code `untrusted-root-unverified`。untrusted 由来 root（payload cwd / `cd_target`）で gate 起動根拠が無い経路を block へ倒す（AC-13/AC-14）

#### Changed

- **AC-18 を (a‴) の原則で拡張**: 走査範囲に chdir intent があるのに AC-4 の受理条件で `cd_target` を不採用にした形（`cd /A && cd /B`、`builtin cd /B`、`cd -- /B` / `cd -P /B`、`pushd /B`、`env --chdir=/B`、走査範囲に `$` / `` ` `` / `env` を含む形、入れ子 `bash -c` / `eval` / subshell 内の `cd`、語中 `#` で 2 つ目の `cd` を隠す形）は、実行先の signal が無いのではなく「解決できない実行先」なので、解決不能な payload cwd / `cd_target` と同じく `pr-target-unresolvable` で block する（impl-gate T-8/T-9 F-1、人間承認 2026-09-08T08:32:20+09:00 案 (a)(1)）。従来はプロセス cwd 由来 root の証跡で判定されて allow に抜けていた（origin/main も同じ）
- `gh_command_parse._tokenize` のコメント処理を bash 準拠にした: **語頭**（行頭 / 空白の直後 / `;` `&` `|` `<` `>` `(` `)` の直後）の `#` だけをコメント開始とし、語中の `#`（`x#y`、`$#`、`${#a}`）とクォート内の `#` は token に残す。従来（origin/main）は shlex 既定の `commenters='#'` により語中の `#` もコメントになり、`echo x#y && gh pr merge 7` が `is_merge=false` で gate ごと素通り（fail-open）していた

- root 候補は `[プロセス cwd, payload cwd, cd_target]` を順に解決し、`.claude/gdd-dev.local.md` を持つ最初の候補を採用する（単純な候補順の早さではなく marker 優先。AC-2）。payload cwd と `cd_target` は同一の untrusted 信頼クラスとして扱い、marker を持つ候補が 1 つも無い場合だけプロセス cwd（trusted）の解決結果へ fallback する（AC-11）
- `repo-root-unresolvable` の block 文言を「repo 内のディレクトリで実行するか、GDD 管理下の repo なら `cd <repo> && gh pr merge` の形で実行してください」へ訂正（旧文言「リポジトリ内で実行してください」は `cd` を足しても効かない誤誘導だった。AC-7）
- root ≠ `gh` の実行先（`cd_target` または payload cwd のどちらの signal でも）を既存 `pr-target-unresolvable` へ倒す（AC-18）
- `parse-error` の block 文言に、本 PR が足した原因クラス（tokenizer の縮退＝クォートが閉じていない）の復旧手順を先頭へ加えた（PR review M-1）。旧文言「python3 が実行できるか、hook へ渡る入力が壊れていないかを確認」は、縮退で発火したときにどちらの確認も空振りし、真の出口（クォートを直す）を案内しなかった
- `pr-target-unresolvable` の block 文言も訂正した（advisory-1）。1 文目を「root の repo 内のディレクトリで実行するか、実在する repo を `cd` に指定する」へ差し替え、旧文言の「URL か `-R owner/repo <番号>` で対象を明示する」は括弧書きへ移した。**この code は本 PR 以前からある経路（`gh pr merge <ブランチ名>` のように対象 PR を決められない形）でも発火する**ため、その経路の 1 文目も入れ替わる（実測: root 内・全証跡ありの repo で `gh pr merge my-feature-branch` → main は「URL か -R …で対象を明示してください」、本 PR は「root の repo 内のディレクトリで実行するか…（URL か -R …での明示も可）」）。当該経路の利用者は既に root 内にいるため、実際に効く手順が括弧内へ降格する面が残る（completion-check Round 4 M4-1。文言の再訂正は本 PR では行わず開示に留める）

#### Fixed

- 語中 `#` による gate 素通り（`echo x#y && gh pr merge 7` / `echo x#y ; gh pr merge 7` / `bash -c 'echo a#b && gh pr merge 7'` が origin/main では `is_merge=false` で無検査 ALLOW）を塞いだ（completion-check Round 2 H-1 / T-8）。修正の途中版（`commenters=""` のみ）は行末コメント付きの正当な merge（`gh pr merge 7 # squash after CI` 等 4 形）を `pr-target-unresolvable` で誤 block していたが、語頭 `#` をコメントとして落とす形に直し、origin/main と同じ allow に戻した（impl-gate T-8/T-9 F-2。リリース版には含まれない途中版の不具合）
- `cd_intent` の `env` 走査が `-u NAME` / `-P path` のように引数を別 token で取る option の引数を「起動するコマンド名」と誤認して打ち切り、`env -u X -C /B gh pr merge 7` / `env -u X --chdir=/B …` / `/usr/bin/env -u X -C /B …` で intent が落ちて allow に抜けていた（`env -C /B` 単独は block。同一 guard 内の非対称）のを、最初の `env` 以降の token 全体から `-C` / `--chdir` を探す形に直した（impl-gate T-8/T-9 Round 2 G-1。リリース版には含まれない途中版の不具合。BSD env / GNU env とも `-u` と `-C` を実装する実行可能な形だった）

#### Known limitations

- AC-18 の chdir intent 判定は **可視の chdir 語彙**（`cd` / `pushd` / `popd` / `env` の `-C` / `--chdir`）にのみ効く。`env` の `-C` は短オプション束（`env -iC /B`）・値密着（`env -iC/B`）・両者の併用まで拾い、`--chdir` は `--chdir=/B` / `--chdir /B` に加えて GNU coreutils env が受理する一意な省略形（`--ch` / `--chd` / `--c`。`env` の長オプションで `c` 始まりは `--chdir` だけ）も拾う（`env` の chdir 綴りはこの 2 つだけなので綴りの列挙はここで閉じる）。語彙が展開でしか現れない形（`CD=cd && $CD /B && gh pr merge 7` のように literal `cd` token が無い形）は intent が立たず、プロセス cwd 由来 root で従来どおり判定される（origin/main と同じ挙動。この形は「忘れは止まるが偽りは止まらない」強度モデルの範囲内）。逆に、chdir 語彙と一致する単独 token を引数に持つ形（`gh pr merge 7 -t cd`）や、`env` より後ろに `C` を含む短オプション束 / `--chdir` の接頭になる 3 文字以上の長オプション token を持つ形（`env x -C /B …` のように `env` 自身の option でなくても）は intent と誤認して block 側に倒れる
- 縮退のせいで merge 判定が付かないまま root も解決できない場合は、**管轄外として通す**（block しない）。解析そのものが完走しなかった場合（python3 不在 / import 失敗 / 不正 JSON）は「merge ではない」と断定できない family なので、この緩和には含めず従来どおり block する。GDD セッションかどうかを決められない状態で block すると、非 git ディレクトリで実行した merge でもないコマンドを「repo 内で実行してください」という無関係な理由で止めてしまうため。merge と判定できている場合は従来どおり `repo-root-unresolvable` で block する。
- **`env -S '-C /B gh pr merge 7'`（`-S` の文字列分割）は上記 guard の手前で落ちる**。BSD env は文字列を分割して chdir + merge を実際に実行するが（実測: `cd ~ && env -S '-C /private/tmp pwd'` → `/private/tmp`）、hook の merge 検出（`_scan_tokens`）から見ると `gh pr merge` は 1 つのクォート済み token の内側にあり `is_merge=false` になるため、**hook 自体が発火せず gate を完全に素通りする**（実測: origin/main / 本 PR とも `is_merge=false` / `cd_intent=true`）。AC-18 の chdir intent 判定を広げても届かない面で、merge 検出側の課題として本 PR のスコープ外。**残置項目の中でこれだけが実害が成立し、かつ有限で閉じる**（`-S` は綴りが 1 つなので `_scan_tokens` が `-S` の引数を再走査すれば閉じる）ため、**別 steering の第一候補として閉じる予定**（findings.md § 別 steering 候補）
- **chdir option を持つ `env` 以外の wrapper（`sudo -D <dir>` / `sudo --chdir=<dir>` / `chroot <dir>`）は AC-18 の検出対象外**。`gh pr merge` は検出されるが chdir intent は立たず、プロセス cwd 由来 root で判定される（実測: origin/main / 本 PR とも `is_merge=true` / `cd_intent=false`）。agent が非対話で通す経路としての到達性は低い（`sudo -D` はパスワード要求、`chroot` は root 権限が要る）ため開示に留める
- `source` / `.` で読み込んだスクリプト内の chdir は上記とは別の形で残る。`cd /A && source /s && gh pr merge 7` は `cd_target` が `/A` として非空のまま採用されるため AC-18 は発火せず、`/s` が実際に chdir した先とは無関係に `/A` 由来の判定が行われる（design.md Round 4 security M-3。allow 側に残る面であり、本 PR で塞いでいない）
- B-1 の allowlist（`$` / `` ` `` / `env` の 3 条件）は shell の chdir 手段を網羅列挙したものではない。閉じ方が denylist から allowlist へ変わったことが根拠であり、未列挙の形の到達性は個別に評価が要る
- signal は届いたが toplevel へ解決できない untrusted 実行先（不在 dir / 非 git dir を `tool_input.cwd` や `cd` に載せた形）は allow ではなく `pr-target-unresolvable` で block する（impl-gate Round 4 IG-13、人間承認済み案 (a‴) の帰結。root == 実行先を保証する意味ではない）
- `cd <repo> && pwd` 形の root 解決は、実行環境に `CDPATH` が設定されているとシェル組み込みの `cd` の挙動が変わりうる前提の上に成り立つ。hook 側は先頭（`SCRIPT_DIR` 解決と lib の `source` より前）で `unset CDPATH` して対処済みだが、これは hook 内部の `cd` を守るものであり、ユーザー側シェルの `CDPATH` 設定そのものを変更しない
- **`tool_input.cwd` / `tool_input.workdir` は現行の Claude Code では載らない（実測）**。Bash tool のパラメータ schema に `cwd` / `workdir` は存在せず、公式ドキュメントの PreToolUse payload 例も `tool_input` は `{"command": ...}` のみ。`cwd` はトップレベルにだけ入り、hook プロセスの cwd と同じ値になる。したがって payload cwd を読む候補は**現行版では死にコード**で、A-1 で決めた untrusted 扱い（marker 必須 / AC-13 の block 対象）は将来 schema が変わった場合の予防に相当する。これに依存する 2 つの限界（相対パスの `tool_input.cwd`、`CDPATH` を export した環境）も現行版では発火しない
- AC-13 の marker 不在分岐（4 面目）は、untrusted 候補が採用条件（marker 必須）を満たした直後に marker が消える TOCTOU を除いて構造的に到達不能であり、fixture 対象外（D-1）。実装は防御的に書くが「テストで守られていない分岐」であることを明記する
- **主目的形は達成されている（実測で確認）**。completion-check Round 2 M-4 は「`tool_input.cwd` に非 git なセッション起動ディレクトリが載る環境では主目的形が依然 block される」と開示していたが、上記のとおり `tool_input.cwd` は現行版では載らないため**この環境は実在しない**。主目的形（非 git な process cwd から `cd <marker 付き repo> && gh pr merge 7`）は、origin/main では `repo-root-unresolvable` で恒久 block だったのが本 PR では `approval-missing`（= 通常の証跡判定）まで到達することを A/B で実測済み。将来 harness が `tool_input.cwd` に非 git dir を載せるようになった場合は、raw signal 非空・解決不能として `pr-target-unresolvable` に倒れ、復旧文が実際の回避策を示せない状態になる（その時点で再設計が要る）
- **timeout による無出力素通り**（本 PR が増幅、実測）: `eval` を n 段重ねた入力で解析時間が伸びる。`hooks.json` の `timeout: 10` を超えると hook は無出力で終了し allow になる。同一入力・同一マシンで n=60 が origin/main 1.174s / 本 PR 1.375s、n=100 が 8.085s / 9.489s（約 17% 増）で、timeout に触れる n がその分だけ手前へ寄る。入れ子展開を 2 回走らせる構造は本 PR が持ち込んだもので、走査予算の上限化（超過を `unresolvable` として block へ倒す）は別 PR の課題として残す。
- **heredoc を含む形の縮退は検出しない**（上記の判定範囲の帰結）。`bash <<'EOF' … gh pr merge 7 … EOF` の本文にアポストロフィがある形や、引用符の内側で heredoc introducer に一致する形は、縮退したまま解析されて素通りしうる（origin/main と同じ挙動で、本 PR で悪化はしていない。実測で両者とも `is_merge=false`）。
- **引用符の内側にある heredoc 開始語で merge を飲み込む形は検出できない**。`_strip_heredoc_bodies` は行ごとに正規表現で開始語を探し、引用状態を持たない。そのため `echo "x <<EOF` のように引用符の内側で開始語に一致すると、終了語までの行がデータとして捨てられ、その中にある `gh pr merge` が解析対象から消える（実測: origin/main / 本 PR とも `is_merge=false`。実 bash は merge を実行する）。**この形と、コミットメッセージの heredoc という正当形は、切り落とし後の縮退という同じ signature を出すため区別できない**（実測で両者とも `stripped_degraded=true`）。安全側に倒すと日常操作の誤 block になるので、本 PR では塞がず開示する。塞ぐには開始語の探索に引用状態の判定を持たせる必要があり、`_strip_heredoc_bodies` は merge gate 以外の hook からも使われるため別 steering として扱う。
- **heredoc の後ろに続くコマンドは従来どおり検出できない**。`_strip_heredoc_bodies` は本体だけでなく heredoc 以降を切り落とすため、`bash -c 'true <<MSG ... MSG' ;gh pr merge 7` の末尾は解析対象から消える（origin/main と同じ挙動。実測で両者とも `is_merge=false`）。本 PR では塞がない。
- `pr-target-unresolvable` は **2 つの family で使い回されている**（gate 故障系 = root と実行先が一致しない / 解決できない、policy 違反系 = `state.md` の PR URL 欠落を含む全件列挙）。gate 故障系の instance だけが kill-switch の出口を案内し、policy 違反系は共通復旧要素を案内する。code 単位の family 表では分類できないため、前者は専用の契約テストで固定している。
- `_mg_log_suppressed` が kill-switch 迂回の記録に使う `repo:` ハッシュの基準が、origin/main の「正規化した payload cwd」から本 PR の「プロセス cwd」へ変わる。ログの当該列はバージョン境界をまたいで比較できない。

#### Affected Files

- `hooks/scripts/run-merge-gate-hook.sh` / `hooks/scripts/lib/gh_command_parse.py` / `tests/test_merge_gate_hook_gate_activation.py` / `tests/test_merge_gate_hook_command_parse.py` / `tests/test_merge_gate_hook_block_reason_quality.py` / `tests/test_hook_block_reason_recovery_contract.py` / `tests/_merge_gate_support.py` / `CHANGELOG.md` / `docs/VERSIONING.md` / 3 manifest

#### Breaking Contract Changes

- **block 条件が増える**。従来 allow だった次の形が block になる（impl-gate の A/B 実測で 4 形が新規 block、2 形が reason code 変更）。
  - untrusted 由来 root（payload cwd / `cd_target`）で gate 起動根拠が無い経路 → 新 reason code `untrusted-root-unverified`
  - untrusted な実行先が root と一致しない、または toplevel へ解決できない形（不在 dir / 非 git dir を `tool_input.cwd` や `cd` に載せた形を含む） → `pr-target-unresolvable`
  - root が marker 優先で untrusted 候補（payload cwd / `cd_target`）へ移ったことで、既存の証跡系 reason code が新規発火する経路（新 reason code の追加ではない）。実測: プロセス cwd が git repo だが marker を持たず（trusted 候補が非採用）、`cd <marker + steering を保持する repo> && gh pr merge <番号>` を実行すると、main では `ALLOW(exit0-silent)` だった経路が、root が untrusted 候補へ移った結果 `approval-missing` 等の既存 reason code で block される（`untrusted-root-unverified` にも `pr-target-unresolvable` にも該当しない）
  - **走査範囲に chdir intent があるのに AC-4 で `cd_target` を不採用にした形** → `pr-target-unresolvable`（impl-gate T-8/T-9 F-1、人間承認済み案 (a)(1)）。root = 全証跡を持つ repo A で実測した 12 形（`builtin cd <B>` / `cd <A> && cd <B>` / `cd <A> && echo x#y ; cd <B>` + 改行 / `cd -- <B>` / `cd -P <B>` / `cd <A> && CD=cd && $CD <B>` / `cd <A> && env --chdir=<B>` / `env --chdir=<B>` / `pushd <B>` / `cd <A> && bash -c 'cd <B> && …'` / `eval 'cd <B> && …'` / `(cd <B> && …)`、いずれも末尾 `gh pr merge 7`）は origin/main で `ALLOW(exit0-silent)`（実 bash + `gh` stub の実行先は B）だったのが block になる。**正当形にも当たる**: `cd <root> && cd sub && gh pr merge 7`（`cd` 2 回）や `cd <root> && gh pr merge 7 -t "$T"`（走査範囲に `$`）は root 内で完結していても block される
  - 語中 `#` を含むコマンド（`echo x#y && gh pr merge 7` 等）が gate の検査対象になる。origin/main では `is_merge=false` で無検査 ALLOW だったため、証跡が無ければ `approval-missing` 等で新規に block される（fail-open の解消）
  - 同じ語中 `#` の扱いにより、**fragment 付きの PR URL（`gh pr merge https://github.com/<owner>/<repo>/pull/7#issuecomment-1`）は証跡が揃っていても `pr-target-unresolvable` で block される**。origin/main は `#` 以降をコメントとして落とすため URL が解決でき `ALLOW(exit0-silent)` だった。`gh` 本体は fragment を分離してこの URL を受理するので、gate だけが止める過検出になる（実測: root = 全証跡 repo・対象 PR 一致でも block。completion-check Round 4 M4-2）。回避策は fragment を外して URL を渡すか、`-R owner/repo <番号>` で指定する
- これに伴い AC-17（payload cwd の解決失敗は root 決定に影響しない）と AC-18（解決できない場合は従来どおり）の意味を変更した。**gate の管轄内（root に marker がある）では allow を block へ倒す方向のみ**で、証跡を検査する経路が allow へ倒れる変更は含まない。
- ただし **管轄外へ倒れる形が 1 つある**（独立レビュー実測）: プロセス cwd が marker を持たない git repo で、`tool_input.cwd` に実在する非 git ディレクトリが載る場合、origin/main は payload cwd を root にしようとして `repo-root-unresolvable` で block していたが、本 PR は候補ループが trusted な toplevel へ倒れ、marker 不在により非 GDD セッションとして `exit 0` になる。marker が無い = gate の管轄外で検査すべき証跡も存在しないため gate bypass ではないが、`gh pr merge` が block されなくなる形として開示する。
- **shlex がクォート解析に失敗して縮退した入力は `parse-error` で block する**。`$'...'`（ANSI-C quoting）のように bash では valid でも `shlex` が `ValueError` を投げる形では、`text.split()` へ縮退した token 列が演算子と密着した token を割らないため、`;gh` が token `gh` にならず merge 検出が落ち、`;cd` も chdir 語彙として数えられない。「merge ではない」と断定できないので、解析未完走と同じ family へ倒す。巻き込みの範囲は step 1 の粗いフィルタ（**payload 全体**に `merge` の部分文字列があるか）が決める。`merge` を含まないコマンドでも、`cwd` / `transcript_path` に `merge` を含む環境（`…/20260907-merge-gate-…` のような worktree）では縮退入力が `parse-error` で block される（実測: marker 付き repo で `echo it's fine` が origin/main の ALLOW から BLOCK へ転換）。ただし縮退するのは bash 自身も解釈できない未閉クォートの形に限られる（`echo $'\t'` / `echo "don't"` / `sed -i '' "s/a/b/" f.txt` / `jq -r '.a' f.json` は実測で縮退しない）。通常のクォート内アポストロフィ（`-t "it's done"`）では縮退しない。判定はトップレベルの tokenize だけを見て、**heredoc を含まないコマンドに限る**。入れ子本体まで含めると `bash -c "echo don't"` のように bash として valid な形（アポストロフィが二重引用符の内側）まで縮退扱いになり、日常操作が block される。入れ子本体だけが縮退した形は、`parse-error` へは倒さず AC-18 の chdir intent 側で処置する（target は採用せず intent だけ立てて block 方向へ倒す）。先頭の `cd` を「唯一の cwd 変更」として誤採用すると、実シェルが別の場所へ chdir しているのに実行先の照合が通ってしまうため。heredoc があると、切り落とし後を基準にすれば引用符の内側で introducer に一致して閉じ引用符が落ちる形が、元コマンドを基準にすれば実行されない本文のアポストロフィ（`Don't merge yet`）が、それぞれ block 方向の誤検知になる。どちらも正当な操作を止めるので、heredoc を含む形では signal を立てず origin/main と同じ扱いにする。

#### User Action Required

- worktree 運用でセッションを repo 外から起動している場合、`cd <repo> && gh pr merge` の形が使えるようになる（`<repo>` に `.claude/gdd-dev.local.md` が必要）
- 上記 Breaking Contract Changes により、`gh pr merge` が新たに block される場合がある。`untrusted-root-unverified` は「セッションを repo 内で起動する」か「証跡を記録する」で解消する。`pr-target-unresolvable` は root の repo 内のディレクトリで実行するか、実在する repo を `cd` に指定する
- 3 つ目のカテゴリ（root が untrusted 候補へ移ったことで既存の証跡系 reason code が新規発火する経路）は、そのセッションで実際に承認・記録済みの証跡（PR URL 記録等）を用意することで解消する。`.claude/gdd-dev.local.md` を持つ trusted なディレクトリ（プロセス cwd）からセッションを起動した場合、root は marker 優先の候補順によりそのプロセス cwd に**固定される**ので、そこから `cd <別の repo> && gh pr merge` を使うと `cd` 先が root と一致せず AC-18 の `pr-target-unresolvable` で block される（実測: プロセス cwd=A(marker あり) + `cd B`(marker あり) → `pr-target-unresolvable`。root は A のまま B へは移らない。impl-gate T-8/T-9 F-4 で因果の記述を訂正）。`cd` を使わずそのディレクトリで直接 `gh pr merge` を実行するか、`cd` 先を root 自身（またはその配下）にすれば block は避けられる
- 4 つ目のカテゴリの過検出は、CHANGELOG が先に挙げた `cd <root> && cd sub` / `$` を含む形以外にも及ぶ（独立レビュー実測）。**`gh pr merge 7 && cd /tmp`**（`cd` が `gh` より後ろで、merge は root で走る形）と **`cd sub && gh pr merge 7`**（root 内の単一の相対 `cd`）も block される。判定は走査範囲に chdir 語彙があるかだけを見ており、`gh` との前後関係も相対パスの解決も行わないため。どちらも block 方向で、下記の復旧手順が効く。
- 4 つ目のカテゴリ（chdir intent があるのに `cd_target` を不採用にした形）は、コマンド先頭に **単一の `cd <絶対パス>`** だけを置き、走査範囲（入れ子 `bash -c` / `eval` を含む）に 2 つ目の `cd` / `pushd` / `popd` / `env` / `$` / `` ` `` を含めない形へ書き直すか、root の repo 内のディレクトリで `cd` を使わずに実行することで解消する。block 文言の 1 文目（root の repo 内のディレクトリで実行するか、実在する repo を `cd` に指定する形で実行する）はこのカテゴリにも同じ復旧手順として効く

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q`（AC-1〜AC-19 の新規契約テストを含む）: `2256 passed, 1 skipped, 14397 subtests passed in 713.76s (0:11:53)`、failed 0
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0。`version-not-consumed: OK (shipping v0.41.11; integration target consumed v0.41.10)` を含む全 BLOCK が OK/PASS/SKIP

### [0.41.10] - 2026-09-07

#### Summary

`[0.41.9]` が入れた done guard Check 2 の fail-open を塞ぐ。あわせて判定の設計を作り直す。どちらもマージ直前の独立レビューで検出したが、修正が push 前だったため `[0.41.9]` のマージには含まれなかった。**現行の main では注記を 1 つ付けるだけで done guard を通過できる**ため、優先して塞ぐ。

#### Changed（設計の見直し）

`[0.41.9]` までの判定は、列位置・セル数・語数といった**代理指標**を積み重ねる形になっていた。指標を 1 つ足すたびに別の迂回路か誤検出が開き、独立レビュー 19 ラウンドで high 38 件を出した。原因は個々の指標ではなく、**「未完了の検出」と「完了の受理」が同じ判定経路に混ざっていた**ことだった。本 entry で判定を次の 2 つの不変条件に還元する。

1. **未完了の検出は無条件・列位置非依存**。`pending` / `fail` と完全一致するセルを持つ行は、形（表 / list / 散文）・インデント・引用・凡例・補助表を問わず必ず未完了として報告する。これを抑止する規則を置かない
2. **完了の受理は canonical schema に一致する行だけ**。status 列を **1 つに確定**できた行の値が許容値のときだけ検証済みと認め、確定できない検証行は「status 判別不能」で block する

R9〜R15 の独立レビューが挙げた fail-open は**すべて「検出の前段に置かれた絞り込み」**が原因だった（受理ゲート / 凡例除外 / 補助表除外 / インデント除外 / 列候補の探索順）。検出を無条件にすると、逆側の「計上」をどれだけ緩めても fail-open にならない。

以下は上記から導かれる規則。

- **列の役割を先に確定し、行の判定は method 列と status 列だけで行う**。表ブロックの先頭行を header として読み、`method` / `status`（日本語の `検証方法` / `ステータス` / `状態` / `判定` を含む）から列位置を解決する。**method も status も特定できない行は header ではない**（語彙外の見出しで表全体が guard から外れるのを避ける）。header が無い表は canonical の 0 列目を method、2 列目 / 3 列目を status 候補とし、0 列目が ROW-ID（`V-01` / `ROW-3` / 連番）か status のときだけ method を 1 つ右にずらす
- **補助行（method 列が検証対象を名指していない行）の除外は行単位で行う**。表ブロック単位で「補助表」と決めつけると、`結果` / `検証項目` のような語彙外の見出しが 1 つ混ざるだけで表全体が guard から外れ、後続の表や list まで巻き込む（実測）
- **識別子の照合は語境界で行い、語数やセル数の閾値を使わない**。`| 検証 対象 は ac:AC-1 |` のように語を前置されても検出し、`spec の AC-4 行からだけ削除` のような散文は（そもそも method 列に来ないので）拾わない
- **AC 検証行の判定も method 列だけで行う**。行全体を見ると、evidence / notes に `AC-3 は対象外` と書いた External Security Evidence 行まで AC 行と誤判定し、contract 上正しい `N/A` が解除不能な block になる
- **コードスパン（`` `…` ``）内のパイプを列区切りにしない**。割ると `` - AC-13: `rg X | sort` が 0 件 `` のような散文 1 行が 3 セルの表行に化け、検証行として誤って block される
- **正規化を 1 箇所に集約する**。セル生成の時点で list marker（`- ` / `+ ` / 番号）と小文字化を済ませ、識別子側と status 側が同じセル値を見るようにする。片方だけ剥がしていると `- pending | ac:AC-2 | log` の status が読めず素通りした
- **形の判定は「計上するか」だけに使う**。`_verification_line_shape()` は表 / list / 外側パイプ省略の別だけを返し、status や識別子の有無で行を落とさない。**この段は検出に関与しない**ので、狭くても fail-open にならない
- **status 列は候補集合ではなく 1 つに確定する**。「最初に解決できた列」を採ると canonical 表の evidence 欄の `pass` / `N/A` を status として読み、`| method=ac:AC-1 | 未実施 | pass | … |` が verified 扱いになる
- **header 行に出会うたび列束縛を貼り替える**。表ブロックの先頭 1 行しか読まないと、空行なしで列順の違う表を続けたとき前の表の status 列束縛が持ち越され、後続表の notes 欄を status として読む
- **正規化は 1 箇所に集約する**。引用記号（`> `）・全角パイプ（`｜`）・list marker・コードスパン・装飾・zero-width をセル生成の時点で吸収し、下流の判定がそれぞれ別に剥がすのをやめる
- **インデント行の除外は計上側だけに残す**。検出にも掛けていたため、`  - Status: fail` と入れ子 list で書いた**実在の未完了 tasklist 2 件が丸ごと不可視**だった。記入例よけは code fence（走査前に除外済み）が本来の手段
- **status 先頭列（`| pending（明日） | ac:AC-1 | log |`）は status を 0 列目から読む**。2 列目から読むと evidence 欄の `pass` で verified に化け、逆に全 pass の節は「判別不能」で解除不能な block になっていた
- **括弧注記の未完了（`pending（未実施）` / `fail(3 件)`）は列位置を問わず検出する**。識別子を持たない行が検証行判定に落ちて、注記付き未完了ごと消えていた。コロン注記（`fail: 0`）は notes の集計と区別できないので従来どおり status 列限定
- **見出し行（`### `）でも表ブロックの列束縛をリセットする**。空行が無いだけで前の表の status 列を後続の表へ持ち越していた
- **header と認めるのは表ブロックの先頭行か、GFM どおり直後に separator が続く行だけ**。どの行でも header 語との一致で貼り替えると、`| 検証 | 2026-09-01 | 状態 |` のような data 行が header に化けて消え、以降の行の status 列までずれる
- **status ラベルの剥がし方を header 語彙と揃える**（`ステータス` / `状態` / `判定`、全角コロン含む）。header 判定では認めている語をセル正規化が剥がしておらず、ラベルを日本語にするだけで `pending` が検出を抜けていた
- **AC 検証行の判定を識別子照合と同じ語境界にする**。`^` 固定だったため `| [AC-1] | n/a | 未実施 |` のように 1 語前置するだけで AC 行と認識されず、未検証 AC が `N/A` 1 語で verified に化けていた（同じセルを見る `_VERIFICATION_ID` は語境界照合で、段の間で判断が食い違っていた）
- **括弧注記の未完了は「status 列を確定できない行」だけで拾う**。確定した status 列が完了値なら、他セルの `pending（前回）を解消` は経緯の記述であって未完了ではない
- **先頭セルが ID（`V-01` / 連番）の行は header と認めない**。header の先頭は列名であって行番号ではない。認めると `| V-01 | 検証 | 未実施 |` が表ブロックの先頭に置くだけで header に化けて消える
- **ID 列形は正準形（`ID | method | status | …`）と短縮形（`ID | status | …`）を読み分ける**。1 列目が許容 status 値なら短縮形と読む。読み分けないと `| AC-1 | pass | log |` が解除不能な block になる
- **インデントされた表も計上する**（表以外のインデント行は従来どおり計上しない）。除外していたため、list 項目の下に入れ子で置いた検証表が丸ごと不可視になり、親の散文 list 1 行だけで done が通っていた
- **`\|`（エスケープしたパイプ）は検出時のみ区切りとして見る**。列位置をずらさずに `method=ac:AC-1 \| pending` と結合して未完了を隠せていた
- **行全体をコードスパンで包んだ形（`` - `| ac:AC-1 | pending | log |` ``）は中身を展開してから割る**。包んだままだと全セルが 1 つに潰れ、`pending` 明記の行が検出も判別不能判定も抜けたうえ data 行として計上されていた
- **`method=` ラベル付きセルは識別子を含まなくても検証行として扱う**。`_identifier_cell()` がラベルを剥がすため、剥がした後だけを見ると `method=受入確認` のような行が「検証行ではない」と判定されて消えていた
- **単セルの list 行は受理側に入れない**。0 列目を status 列と確定してしまい、`- pending: 0 件` のような 0 件宣言の集計行を未完了として報告していた
- **行が検証行かどうかを見るときの ROW-ID は前方一致にする**（列位置を決める判定は全一致のまま）。全一致を流用していたため、`| V-01 手動確認 | 未実施 | - |` のように語尾が 1 語付くだけで検証行と認識されず、status が許容値でない行が計上も報告もされずに消えていた
- **表 header の列束縛は、空行を挟まず続く list 行へ波及させない**。表の status 列位置を list 行に当てて evidence 欄を status として読み、canonical な list 行が判別不能になっていた
- **凡例行の除外は検出より後段に置く**。前段に置くと `- 各行の形式: 手動確認 | pending | log` のように語を 1 つ前置するだけで未完了行を消せる。その結果、`|` 区切りで許容値を列挙した凡例（`- 許容 status: pending | pass | fail`）は **意図的に block する**（凡例と迂回を構造で区別できないため fail-closed へ倒す）
- **0 列目が status のときは method 列を 1 つ右へずらす**（ROW-ID 形と同じ扱い）。header 無しで列順が `status | method | evidence` の表を見失わないため
- 表・list・外側パイプ省略の 3 形を**同じ分類関数**に通す。`pending` / `fail` の検出、注記付き status の受理、判別不能の扱いが形ごとにずれていた非対称を解消する

#### Fixed

- 注記付き status（`pending(再実行待ち)` / `fail: 3 件残`）が 1 件も計上されず done が通っていた（`[0.41.9]` の CHANGELOG はこの挙動を「block される」と記載しており、記述と実装が逆だった）
- method 列が status 列に隣接しない header で、AC 行の `N/A` 禁止と「status 判別不能」の両方が外れて未検証 AC が通っていた
- 数値だけの ROW-ID セル（`| 1 | 手動確認 | 未実施 |`）は `[0.41.9]` でも block していたが、設計見直しの過程で表ブロック先頭に置いたときだけ header 扱いで不可視になった。header 判定を「method も status も特定できない行は header ではない」に直して塞いだ
- 引用ブロック（`> | method=ac:AC-1 | pending | … |`）に包んだ検証行が走査対象外で、同じ節に `pass` 行が 1 行あると done が通っていた。引用記号を剥がしてから形を判定するよう改めた
- 凡例語（`各行の形式: ` / `許容 status: `）を前置した list 行の `pending` / `fail` が、凡例除外に飲まれて 1 件も計上されなかった
- header の無い表・list で evidence 欄の `pass` / `N/A` が status として読まれ、status セルが `未実施` の未検証行が done を通していた
- 空行を挟まずに列順の違う表を続けると、前の表の status 列束縛が持ち越されて後続表の notes 欄が status として読まれていた
- 外側パイプを省いた 2 セル行（`ac:AC-2 | pending`）と全角パイプ（`｜`）の行が受理前に落ち、`pending` 明記の行が不可視だった
- **インデントされた検証行の `pending` / `fail` が検出対象外だった**。入れ子 list（`- \`AC1\`` / `  - Status: fail`）で書いた**実在の未完了 tasklist が実コーパス 455 件中 2 件、done を通過できる状態**だった
- status 先頭列の行で、目視で `pending（再実行待ち）` と書いてあるのに evidence 欄の `pass` を status として読み、verified 扱いにしていた
- 識別子を持たない行（`| 手動確認 | 2026-09-01 | pending（未実施） |`）が計上も報告もされず消えていた。`pending` に注記を 1 つ足すだけで block から不可視へ反転していた
- `### ` 見出しを挟むと前の表の status 列束縛が持ち越され、後続の header 無し表の notes 欄を status として読んでいた
- `| 検証 | 2026-09-01 | 状態 |` のような data 行が header と誤認され、行ごと消えたうえ以降の canonical 行の status 列をずらしていた
- 日本語の status ラベル（`- ステータス: pending` / `- 状態: pending`）が素通りしていた
- AC-ID の前に 1 語（`[` / `・` / `手動 `）を置くだけで AC 行の判定を外れ、未検証 AC の `N/A` / `unsupported` が検証済みとして受理されていた
- list 項目の下に入れ子で置いた検証表（`  | ac:AC-1 | 未実施 | - |`）が走査対象外で、節全体が親の散文 list 1 行だけで done を通していた
- `| V-01 | 検証 | 未実施 |` を表ブロックの先頭に置くと header 扱いで消え、「status 判別不能」の報告を回避できた
- `\|` でセルを結合して `pending` を隠せた

**実測件数（時点依存。断定形では読まない）**:

- 導出コマンド: `python3 plugins/gate-driven-development/scripts/measure-done-guard-drift.py`（統合先 = 現 `origin/main` = `[0.41.9]` との差分）
- measured_at: 2026-09-08T14:24:30+09:00
- population: 455 tasklist.md
- done→block: **3 件** / block→done: **0 件**
- done→block の 3 件のうち **2 件は正しい是正**（入れ子 list で `Status: fail` / `status: pending` と記録された未完了セッションが、インデント除外により done を通過できていた）。残る **1 件は上記 Known limitations の補助表**（インデントされた補助表を検証行と誤読する既知の誤検出。fail-open との引き換えで受け入れ、節の外か code fence へ移せば解除できる）
- ただし **実データの件数は「母集団に該当形が有ったか」しか示さず、規則クラスの網羅性の証拠にはならない**。合成ケースの反転は上記 § Changed / § Fixed に主なものを挙げているが、網羅ではない

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/done_guard.py`（Check 2 の判定）
- `plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py`（契約テスト 66 形追加 / 反転 3 形）
- `plugins/gate-driven-development/references/self-contained-contract.md`（補助表の扱いを実装に合わせて訂正）
- `docs/adr/2026-09-06-done-guard-verification-header.md`（判定を 2 つの不変条件へ還元、§ 論点 2c 規則 2 の改訂を記録）
- `plugins/gate-driven-development/tests/test_stop_hook_bind_resolution_contract.py`（インデント行の pin を「計上のみ除外」へ改訂）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.41.10、統合先消費済み版数 v0.41.9）

#### User Action Required

- `## Verification` の status セルに理由を併記していたセッション（`| method=ac:AC-1 | pending(再実行待ち) | … |`）は新たに block される。`[0.41.9]` の CHANGELOG が既に案内しているとおり、理由は notes 列へ移して status セルは許容値だけにすること
- `## Verification` の list 行で AC を名指しながら status を書いていない行（`- AC-2: 実装済み | 手動確認で確認`）も「status 判別不能」で block される。canonical schema の status セル（`pending` / `pass` / `fail`）を足すこと。コードスパンだけで区切られた散文（`` - AC-13: `rg X | sort` が 0 件 ``）は対象外
- **インデントして書いた `pending` / `fail` も block されるようになった**。`- \`AC1\`` / `  - Status: fail` のような入れ子 list 形式で記録しているセッションは、従来 done を通過できていたが今後は止まる（これが本 entry の主目的の 1 つ）。記入例としてインデントしている場合は code fence に入れること
- `|` 区切りで許容 status 値を列挙した凡例行（`- 許容 status: pending | pass | fail`）は block される。区切りを `/` にするか code fence に入れること

#### Known limitations

いずれも「未完了の検出を無条件にした」ことの裏返しで、**escapable な誤検出**（利用者が書き方を直せば解除できる）である。fail-open と引き換えに受け入れている。

- **連番・ROW-ID を先頭列に持つ補助表は block される**: `| 1 | high | 誤字 | 修正済 |` のような指摘一覧は、canonical な ROW-ID 形の検証行（`| 1 | 手動確認 | 未実施 |`）と構造的に区別できない。**インデントして list 項目の下に置いた補助表も同じく block される**（インデントされた表を除外すると、入れ子の検証表が丸ごと不可視になる fail-open と引き換えになるため。実コーパス 455 件中 1 件が該当）。補助表は `## Verification` の外か code fence へ移すこと（`references/self-contained-contract.md` の指示どおり）
- **`|` 区切りで許容 status 値を列挙した凡例行は block される**（`- 許容 status: pending | pass | fail`）。凡例と迂回（`- 各行の形式: 手動確認 | pending | log`）を構造で区別できないため。区切りを `/` にするか code fence に入れれば解除できる
- **AC-ID を含みパイプが 2 個以上ある散文注記は「status 判別不能」で block される**（`- AC-1 の証跡は build.log | test.log | coverage.log にある`）。`| 各行の形式 AC-2 | 未実施 | |` のような未検証行と構造で区別できないため。注記を `## Verification` の外へ出すか code fence に入れれば解除できる
- **fence の外に置いたインデントの記入例に `pending` / `fail` があると block される**。記入例は code fence に入れること（fence 内は走査対象外）
- **散文の list 行に書いた `pending` / `fail` は検出できない**（fail-open 側に残る既知形）。`- AC-1: 実装済み。ユニットテストは pending` のように区切りを持たない行は、セル完全一致にも括弧注記にも当たらない。散文中の語を部分一致で拾うと `pending を解消済み` まで未完了と読むため塞いでいない。**あわせて、検証行を 1 行も持たない節でも散文の list が 1 行あれば「検証行がありません」を回避できる**（散文 list を data 行に数えるのをやめると、実コーパス 455 件中 **49 件**が誤って block される / 実測）。`## Verification` は canonical schema（`method | status | evidence | notes`）で書くこと
- **header が status 列を名指していても、method セルに識別子が無い行は計上されない**（`| method | status | evidence |` header の下の `| 手動確認 | 未実施 | AC-2 |` が消える）。`origin/main` と同挙動の既存 fail-open
- **ID 列形の 3 列レイアウトで evidence 欄の注記付き `pass` が status として読まれる**（`| AC-1 | 未実施 | pass（2026-09-08） |` が verified 扱い）。`origin/main` と同挙動の既存 fail-open
- 上記 2 件は **status 列の推定と識別子判定の段間不整合**に由来し、個別パッチでは別の迂回路が開く（本 entry の作業中に実測で確認）。`## Verification` の文法を閉じる後続作業で構造的に解消する
- **コードスパン内のパイプを列区切りにしない副作用**: `- 手動確認 | 未実施 | `cmd | pass` | notes` のように識別子を持たない行では、`origin/main` が偶然 block していたものが通るようになる（main 側の block はパイプを割ってしまう main 自身の欠陥の副産物で、同じ行からコードスパンを外すと main / 本版とも通る）。コードスパン退避は実コーパス 455 件中 **15 件**の Verification 行が該当する誤検出を防いでおり、その利得を取って据え置く
- **header の取れない表・list 行で canonical 位置に `pass` が入る形は verified 扱い**

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests -q`: **2169 passed, 1 skipped, 12792 subtests passed**, exit 0
- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_*.py plugins/gate-driven-development/tests/test_hook_injection_security_contract.py -q`: **309 passed, 172 subtests passed**, exit 0
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0（`version-not-consumed: OK (shipping v0.41.10; integration target consumed v0.41.9)`）
- `python3 scripts/gdd-codebase-health.py --mode changed --base-ref origin/main --fail-on high`（cwd = `plugins/gate-driven-development`）: **high 0 件 / medium 0 件**
- Superpowers Benchmark Summary: not_applicable（no changed GDD primitive; Stop hook 内部ロジックのみ）


### [0.41.9] - 2026-09-07

#### Summary

done guard（Stop hook Check 2）の表形式 `## Verification` 判定が、header を `stripped.startswith("| method")` / `startswith("| ROW")` という prefix で見分けていたため、canonical な data 行 `| method=ac:AC-1 | pending | … |` も同じ prefix に巻き込まれて丸ごと不可視になり、`pending` / `fail` を残したまま done が通る fail-open が実在した。表形式のみの節は別の fail-closed 分岐（「検証行がありません」）が受け止めていたが、**list 形式の行が 1 本でも混在すると data 行が非空になってその分岐も発火せず、done が通っていた**（修正前の実装で再現確認済み）。判定を「装飾・空白・不可視文字を除去したセルが許容 status 値（`pending`/`pass`/`fail`/`N/A`/`unsupported`）と完全一致するか」で見る status セル分類へ反転させ、header prefix 判定を廃止した。さらに PR 旧#56 の独立レビューを受けて、**判別不能な status セルを「不可視」ではなく「未検証」へ倒し**（fail-closed）、**list 行にも表行と同じセル正規化を適用**した。さらに `|` 区切りセルを 3 個以上持つ list 行（= 表を list へ書き換えた形）にも status セルを要求し、表で block された内容を list へ書き換えて迂回する経路を塞いだ。header は表ブロック先頭行に限り、行の全セルが header 語彙に収まる場合だけ header と判定する。

#### Added

- `tests/test_stop_hook_done_guard_regression_contract.py`: `TableVerificationRowClassificationTests`（block 方向: header 3 形 / separator 2 形 / padding・装飾 4 形 / セル数不足行 / 混在 / list 回帰 pin / list の padding・装飾・無 padding 3 形 / 不可視文字・取り消し線 2 形 / 判別不能 status セル 2 形 / 非 schema 表と list 全 pass の同居）、`TableVerificationRowClassificationAllowPathTests`（allow 方向: 全 pass 3 形 / `N/A` のみ / `unsupported` のみ / canonical header + 整列 separator / status セルを持たない散文 list）、`VerificationNoRowsMessageTests`（「検証行がありません」の本文と回復ヒントの文言）を追加

#### Changed

**規則クラス（必須・時点非依存）**:

- 表の `pending` / `fail` を検出するようになった（従来は header prefix に巻き込まれて不可視だった）
- status 列を持たない非 schema 表（`| AC | 検証方法 | … | 実測 |` 等）の行は「status 判別不能」として**未検証扱いで block**されるようになった。節に list の `pass` 行が同居していても素通りしない
- OLD で header prefix に巻き込まれて不可視だった表 data 行が `pass` / `N/A` / `unsupported` として計上され、節が通るようになった（block→done 方向。規則上は canonical 全 pass 表の false positive 解消・`N/A` のみ・`unsupported` のみの節が該当する）
- `N/A` / `unsupported` は contract の早見表どおり **AC 検証行（method セルが `ac:` / `method=ac:` / `AC-n` 形）では不可**とする。判定は method セル（status 列の 1 つ左、header が無ければ 0 列目）で行い、marker と `method=` / `method: ` ラベルを剥がしてから比較する。AC でも security evidence でもない行（gate / checkpoint の記録）は早見表の 2 軸に載らないため対象外にする。**AC 検証行では検証済みと認めない**（未検証の AC を 1 語書き換えて done を通す経路を塞ぐ。実測での追加 block は 0 件）
- `- ` / `* ` / `+ ` の箇条書きと番号付き list（`1. ` / `1) `）を data 行として受理する（marker を変えるだけで判定を迂回できた）。外側パイプを省いた GFM 表行（`method=ac:AC-1 | pending | |`）は **status セルを判別できる行に限り**受理する（パイプの本数だけで受理すると `grep a | sort` のような散文の注記行まで data 行になり、全 pass の節が誤って block される）
- header の見出し語に日本語（`ステータス` / `状態` / `判定` / `検証方法`）を加え、header の取れない表でも 2 列目と 3 列目の両方を status 候補にする（`| V-01 | ac:AC-1 | pass | … |` のような ROW-ID 表が誤って block されていた）。status 列があると分かる header は、語彙外の列名（`#` / `date` / `検証観点`）が混ざっていても header と認める
- `status=pass` / `status: pass` のようにフィールド名を付けた表記を受理する（`method=ac:AC-1` と同じ書き方の派生で実データに多く、剥がさないと検証済みの行が「判別不能」で誤って block された）。剥がす正規化は pending 検出と検証済み判定の**両方**を通るので `status=pending` が pass 扱いへ反転することはない
- 行が検証行かどうかを、セル数や記法ではなく**method セルが検証行の識別子（`method=` / `ac:` / `AC-1` / `V-01` / `security_evidence`）であるか**で判定する。`## Verification` 節に置かれた補助表（指摘一覧・変異表・対応表）は検証対象を名指さないため検証行として扱わない。ただし**この除外は `pending` / `fail` の検出より先に効かせない**（列順が違うだけの検証行が丸ごと不可視になるため）（セル数だけで判定すると、コードスパンや区切りを含む散文や補助表まで data 行になり、全 AC が pass の節が誤って block された）
- 許容 status 値に**括弧・コロンで始まる注記**が続く形（`pass（2026-08-30 …）` / `N/A（no-action + 理由）`）を、**status 列を特定できる場合に限り**受理する。記録は済んでいるのに注記を理由に解除できない block になっていたため。列位置を問わない `pending` / `fail` の検出は従来どおり完全一致だけで、notes 欄の `fail: 0` / `pending: なし` を未完了として拾うことはない
- 散文ラベル（`- 補足: 手順は A | B | C`）は list の status セル要求から外す（`method=ac:AC-1` のような識別子のコロンは空白を伴わないので衝突しない）
- 2 つ目以降の `## Verification` 節も走査する（従来は最初の 1 節で走査を打ち切っていたため、節を分けるだけで判定を回避できた）
- 整列指定付き separator（`|:---|:---|`）が素通りしていた既存の fail-open を塞いだ。`|  pending  |` のような padding 差・大文字小文字差・装飾差（`` ` `` / `*` / `_` / `~~`）・不可視文字（zero-width / 制御文字）は、**表行と list 行の両方**で正規化して検出する

**実測件数（時点依存。CHANGELOG 執筆時に corpus drift 再計測スクリプトを再実行した値。断定形では読まない）**:

- 導出コマンド: `python3 plugins/gate-driven-development/scripts/measure-done-guard-drift.py`（本 PR で追加。**本ブロックが実測値の唯一の正本**で、ADR とコードコメントはここを参照する）
- measured_at: 2026-09-07T22:25:00+09:00
- population: 456 tasklist.md
- done→block: 6 件（**全件が妥当な block であることを 1 件ずつ確認済み**。内訳: `pending` / `fail` を実際に残していた 4 件 / AC 行に canonical な status を記録していない表 2 件）
- block→done: 0 件
- 母集団は進行中セッションが書き換え続けるローカルデータのため、件数は計測時点のスナップショットである

#### Fixed

- `hooks/scripts/lib/done_guard.py`: `_is_verification_data_row()` から header prefix skip を削除し、1 行の判定を `_classify_verification_row()`（`(data 行か, pending 理由)` を返す）へ集約した。セル正規化 `_verification_cells()` は装飾（`` ` `` / `*` / `_` / `~`）・前後空白（半角 / タブ / 全角空白）に加えて Unicode カテゴリ `Cc` / `Cf`（制御文字・zero-width）を除去する。「行が検証済みか」は `_verification_status_cell()` が列位置で判定し、列は `_verification_header_status_col()` が表ブロック先頭行の header から解決する（header の status 列は日本語別名 `ステータス` / `状態` / `判定` でも解決する。header に status 語が無い / header が無い表は 2 列目と 3 列目を候補にし、notes 欄まで広げない。fallback では method セルの位置も確定しないため、候補列の直前と先頭セルの両方を AC 判定に使う）。`pending` / `fail` の検出は `_verification_table_row_statuses()` が列位置を問わず行う。list 行は header を持たず正準形が 2 通りある（`- method=… | status | …` / `- V-01 | method | status | …`）ため、`|` 区切りセルが 3 個以上ある行について 2 列目と 3 列目の両方を status 候補として見る
- `hooks/scripts/gdd_stop_hook.py`: 「検証行がありません」の本文とヒントを、行を足しても解除されない旨へ改め、例示を canonical schema の表形式にした（旧ヒントは list 行 1 行の追加で非 schema 表を直さずに ALLOW へ誘導していた）。「status 判別不能」用の回復ヒント（理由は notes 列へ移し status セルは許容値だけにする）を追加し、件数側にも「うち status 判別不能 N 件」を出すようにした（不可視文字を含む行が `safe_for_output()` で置換されるとマーカーが消えるため）

#### Breaking Contract Changes

- 挙動変化（両方向）: 上記 § Changed の実測件数を参照。表形式 Verification に `pending`/`fail` を残したセッション、および status 列を持たない非 schema 表を使ったセッションは新たに block される。回復手順は「Verification 行を canonical schema（`method`/`status`/`evidence`/`notes`）に直す」こと。**list 形式への書き換えは回避策にならない**（`|` 区切り 3 セル以上の list 行にも同じ status セル要求がかかる）
- **判別不能な status セルの扱いを反転した**: 注記・絵文字付きの status（`pending(再実行待ち)` / `pending ⏳`）や非 status 語（`未実施`）、`N/A（理由）` のような理由併記は許容 status 値と完全一致しないため、**未検証として block** される（従来は不可視で素通りしていた）。回復は「理由を notes 列へ移し、status セルは許容値だけにする」。この挙動は `TableVerificationRowClassificationTests` の `decorated_pending_emoji_with_pass_row_blocks` / `non_status_word_with_pass_row_blocks` で pin してある
- **本変更で塞いでいない Check 2 の同型 fail-open**（非スコープ。変更前後とも挙動不変で、後続 follow-up の対象）:
  - インデント行を一括除外するため、非インデントの `pass` 行が 1 行でもあるとインデントされた `pending` 行は不可視になる
  - trailing `|` の無い list 行（`- method=ac:AC-1 | pending`）は、セル分割で最終セルが `pending` になるため検出される。一方 `- method=ac:AC-1 pending`（区切りが無い形）は検出されない
  - 全角パイプ（`｜`）で書かれた表は、表行としても list 行としても扱われない
- **`pending` / `fail` の検出は列位置を問わない（fail-closed 方向の誤検出）**: notes 欄などが単独で `pending` / `fail` という値だけの場合、status セルが `pass` でも block される。`pending を解消済み` のように語を含むだけの文は誤検出しない（いずれも実測確認済み）。done を止める方向なので安全側だが、遭遇したら notes の書き方で回避すること。一方**「行が検証済みか」の判定は列位置で行う**（header があればその列、無ければ canonical の 2 列目のみ）。列位置を問わずに探すと evidence / notes 欄の `N/A` を根拠に未検証行が verified 扱いになる fail-open が出る（独立レビュー R2 で実測・是正済み）
- **「検証行がありません」の射程**: この fail-closed は **すべての `## Verification` 節の data 行の合算**で判定するため、list 行が 1 行でもあれば発火しない（節を分けて 2 節目の検証行を書き忘れても、1 節目に data 行があれば発火しない）。非 schema **表**の行、および `|` 区切り 3 セル以上の list 行は「status 判別不能」として未検証に計上されるため、表を list へ書き換えても迂回できない。**散文 list だけは対象外**で、data 行として計上されるが判別不能は付かない。散文 list は「区切りセル 3 個未満（`- AC-1 は未検証`）」または「先頭セルが検証行の識別子（`method=` / `ac:` / `AC-1` / `V-01` / `security_evidence`）でなく、行内に許容 status 値も無い（`- 補足 A | B | C`）」で判定する。全 list 行へ広げたときの過剰 block を避けるための意図的な除外で、根拠は ADR § 却下した代替案 の実測
- **status 列の残余**: header が取れない表と list 行では 2 列目と 3 列目の両方を status 候補として見るため、`- method=ac:AC-1 | 未実施 | pass | 後で` のように 3 列目へ許容値が入る形は verified 扱いになる（実測）。`N/A` / `unsupported` は method セルの security evidence 判定が入るので 3 列目でも通らない。canonical schema の表（header 付き）で書けば列が確定するので起きない

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/done_guard.py`（Check 2 の表行判定）
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`（block メッセージ・回復ヒント文言）
- `plugins/gate-driven-development/tests/test_stop_hook_done_guard_regression_contract.py`（契約テスト 3 クラス追加 + module docstring 更新）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.41.9、統合先消費済み版数 v0.41.8）
- `docs/adr/2026-09-06-done-guard-verification-header.md`（repo-root。判定規則を反転させた意思決定と、却下した代替案・受容した挙動変化の蒸留）
- `scripts/measure-done-guard-drift.py`（新規。§ Changed の実測値の導出コマンド。hook 本体と同じ可視性判定を通すため `tests/test_fence_policy_single_source_contract.py` の 2 値 API allow-list に理由付きで追加した）
- `CHANGELOG.md`（本 entry の追記のみ。904 → 978 行。archive 回転は統合先が `### [0.40.3]` 〜 `[0.38.0]` を `CHANGELOG-archive-3.md` へ移す形で実施済みで、本 PR では行っていない）

#### User Action Required

- 表形式 `## Verification` に `pending`/`fail` を残したまま done しようとしていたセッションは新たに block される。回復は「該当行を pass にする」か「done を保留する」
- status 列を持たない自作の `## Verification` 表（例: `| AC | 検証方法 | … | 実測 |`）や、`N/A（理由）` のように status セルへ理由を併記した行は「status 判別不能」で block される。**`## Verification` 節に置いた補助表（変異表・指摘一覧など）も同じ理由で block される**ので、節の外へ移すか canonical schema へ揃えること。canonical schema（`| method | status | evidence | notes |`）へ書き直し、理由は notes 列へ移すこと（list 形式への書き換えは回避策にならない）。実測では 456 tasklist 中 6 件が該当し、いずれも未検証項目が残っているか status を canonical schema で記録していないセッションだった

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_*.py plugins/gate-driven-development/tests/test_hook_injection_security_contract.py -q`: **309 passed, 146 subtests passed**, exit 0
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0（`version-not-consumed: OK (shipping v0.41.9; integration target consumed v0.41.8)`）
- `python3 scripts/gdd-codebase-health.py --mode changed --base-ref origin/main --fail-on high`（cwd = `plugins/gate-driven-development`。上 2 コマンドは repo root 起点なので起点が異なる）: **high 0 件 / medium 1 件**（medium は `gdd_stop_hook.py` の関数数 47 > warn 閾値 40 で、本変更前から継続。`--fail-on high` の対象外。v0.40.14 の stop hook 分割で pre-existing の high 7 件が解消済み）
- Superpowers Benchmark Summary: not_applicable（no changed GDD primitive; Stop hook 内部ロジックのみ）

### [0.41.8] - 2026-09-07

#### Summary

root-branch guard の gate 1 `_segment_creates_branch`（`git branch` 経路）が持っていた最後の fail-open（curated set のどちらにも無い未知 flag を黙って非作成側に倒す）を fail-closed へ反転した。PR 旧#41（`[0.40.3]`）の 1 パス cursor walk を骨格として維持し、(1) 未知 flag の早期 `return False` 撤去、(2) 非作成テーブルの実測ベース拡張と unconditional/conditional の 2 区分化、(3) 短 option cluster 判定の letter 単位走査化、の 3 点だけを変更する最小 diff。`switch`/`checkout`/gate 2/`worktree add` は不変。

#### Fixed

- `git branch -v`/`-i`/`-vv`/`-vi`/`-iv`/`--verbose`/`--ignore-case`/`--omit-empty`/`--quiet`/`--no-column`/`--no-abbrev` + GDD 名 positional が allow だった（未知 flag の fail-open）
- `git branch -tdirect <name>`（`--track=direct` の letter 結合形）が全英字のため `d` を delete letter と誤読し allow だった
- `--no-*` 否定形 19 形と `--copy`/`-c`/`-C` × list-scope の long/分離形 8 形が未知 flag として site 収集から漏れていた（変更 1/2 で自動的に閉じる）
- `--cop -a <name>`（unambiguous abbreviation として `--copy` に解決され実際に ref を作る）が conditional veto の条件不足で allow だった
- 独立実装レビュー指摘: list-scope mode flag（`-a`/`-r`/`--all`/`--remotes`）は `--copy`/`-c`/`-C` と同時指定されると実 git は copy/rename 処理を list-scope チェックより先に評価し branch を作成するが、旧実装は list-scope を無条件 mode veto にしており fail-open だった（`-ca`/`-ac`/`-Cr`/`--copy --all` 等）

#### Breaking Contract Changes

- **narrowing（allow → deny）**: (1) 未知 flag + positional（上記 Fixed 全形）、(2) list-scope letter（`a`/`r`）が未知 letter（short/long 問わず、attached/分離いずれの形でも）と組み合わされた positional 付き形（`-a -l <pattern>` / `-al <pattern>` / `--all --omit-empty <pattern>` 等）。creating letter（`c`/`C`/`f`/`q`/`t`）との組み合わせは**分離形のみ新規**（`-a -c <名前>` 等。base は各 token を個別に未知判定するため `-a` 単独が既に fail-open だった）で、attached 形（`-ac <名前>` 等）は base の部分文字列一致で既に deny だったため変化なし。list-scope letter 同士・neutral letter（`v`/`i`）・unconditional veto letter（`d`/`D`/`m`/`M`）・残余なしの `u` とのみ組み合わされた場合は allow のまま（実測: `-a` と結合して allow を維持する letter は `a d i m r u v D M` の 9 個のみ。widening クラス（下記）に該当する場合を除く）、(3) attached-value 短 cluster（`-umain`/`-tdirect`/`-tv`）、(4) gate 2 fallback 経由の start-point 形（`git branch -v feature-x codex/…-seed`）
- **据え置き（不変）**: `git branch -- <name>` は allow のまま（既知 gap）。`-m`/`-M`/`--move` は rename 経由で allow のまま（実測 94 形。scope 外）
- **widening（deny → allow）**（completion-check の全数列挙で検出。base では `_short_cluster_has` の部分文字列一致により捕捉されていたが、letter 単位走査への置換で見逃すようになった）: **必要十分条件（3点すべてを満たす短 cluster）** — (i) cluster に `d`/`D`/`m`/`M` を含まない、(ii) 残余のある（cluster 末尾ではない）`u` が cluster 中で最初に現れる位置より前の部分文字列が、すべて `a`/`r`/`v`/`i`、または残余のない `u` のいずれかで構成され、かつ `a`/`r` を 1 つ以上含む、(iii) その（最初に現れる残余ありの）`u` の残余（`u` 以降の全文字列）に creating letter（`c`/`C`/`f`/`q`/`t`）を 1 つ以上含む。代表形（cluster 長 3）: `-auc`/`-auC`/`-auf`/`-auq`/`-aut`/`-ruc`/`-ruC`/`-ruf`/`-ruq`/`-rut`（+ GDD 名 positional）の 10 形。cluster 長は開放集合のため全量列挙はせず、上記 3 条件を正本とする（既知 14 文字 `arucCfqtvidDmM` について長さ ≤5 の全数列挙で必要十分性を実測確認済み: miss 0 / false positive 0。`-dauc`/`-aduc`（`d`/`D`/`m`/`M` を含む）と `-acuc`/`-aZuc`（`u` より前に creating/未知 letter がある）は base・head とも allow/deny が一致し widening ではない）。原因: `u` が残余ありの value-taking letter として即時 return するため、後続の creating letter が走査されず `saw_creating` が立たない。実測確認済み: git 2.50.1（該当形はいずれも rc=128・新規 ref 0 件で fail-open ではない。guard を弱めてはいない）

#### Affected Files

- `hooks/scripts/validate-worktree-command.py`（`_segment_creates_branch`、`_classify_branch_short_cluster` / `_branch_long_flag_dispatch` 新設、`_token_is_branch_*` 削除。copy × list-scope の是正は関数新設ではなく `_BRANCH_CONDITIONAL_NON_CREATING_LONG_FLAGS` / `_BRANCH_CONDITIONAL_NON_CREATING_SHORT_LETTERS` の conditional veto で実現）
- `tests/test_root_branch_name_candidates.py` / `tests/test_root_branch_guard_real_git.py` / `tests/test_root_branch_guard_contract.py`（テスト追加・コメント更新）
- `docs/design/2026-09-03-validate-worktree-git-global-flag-adr.md`（ADR-6 Superseded 追記）
- `docs/adr/2026-09-06-branch-guard-unknown-flag.md`（新規）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（版数 0.41.8）
- `docs/VERSIONING.md`

#### User Action Required

- `git branch <未知 flag> <name>` 系のコマンドが新たに deny されうる。回避策は dedicated worktree / `git worktree add -b`
- `git branch -l '<pattern>'` は長形式 `--list` を使う

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`: `2164 passed, 1 skipped, 12701 subtests passed`（exit 0、fail 0。origin/main合流分の追加テスト込み）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: 全 BLOCK pass（exit 0、`version-not-consumed: OK (shipping v0.41.8; integration target consumed v0.41.7)` 含む）
- `python3 plugins/gate-driven-development/scripts/gdd-codebase-health.py --mode changed --base-ref origin/main`: `high=1, medium=2`（exit 0。`--fail-on`既定`none`。scan対象11ファイル＝本PRの差分と一致）。本PRの実質的な寄与はmedium 2件のみで、high 1件はorigin/main自身の別コミット由来かつ本PRの差分が触れていない事前存在: `_peel_one_noop_suffix_end`のcomplexity 18（`git diff origin/main -- hooks/scripts/validate-worktree-command.py`に同関数への変更0件で確認）。本PR由来のmedium 2件: (a) `hooks/scripts/validate-worktree-command.py`の`python_function_count` 44 > warn 40 — origin/main（44）と同値で本PRからの純増0、(b) `tests/test_root_branch_name_candidates.py`の`python_function_count` 45 > warn 40 — 本PRのテスト追加で27→45と新規に閾値超過。(b)はテストファイルであり code-health の行数・関数数ガイドラインの対象外、かつ non-blocking のため advisory として受容する

### [0.41.7] - 2026-09-07

#### Summary

`hooks/scripts/run-pre-push-gate-hook.sh:145`（escape hatch のログ記録失敗を block へ倒す唯一の分岐）が、`HOME` 未設定環境では `gdd_sr_log_event`（`lib/self-review-evidence.sh:486`）の未ガード `${HOME}` 展開で `set -u` 即死し、block を出せずに無記録で push が通っていた欠陥を修正した（v0.41.4 の Known Limitations で予告済み）。

修正は 2 段。(1) `gdd_sr_log_event` の記録先解決を `GDD_HOOK_STATE_DIR` → `${HOME}`（あれば）→ 未解決（空）の 3 分岐にし、未解決を既存の「書き込み失敗」経路（`optout` は block、他 event は best-effort）へ合流させた。(2) `run-pre-push-gate-hook.sh` の optout 記録呼び出し（修正前 145 行 / 修正後 151 行）を `if ( gdd_sr_log_event ... ) 2>/dev/null; then` にし、helper 内で将来別の即死要因が増えても block へ倒れる構造的保険を重ねた。

#### Fixed

- `HOME` と `GDD_HOOK_STATE_DIR` の双方が未設定の環境で escape hatch 付きの push を行うと `set -u` でシェルごと死んでいたものを、fail-closed の block（`optout-log-write-failed`）を正しく出すように修正した
- 同条件で `gdd_sr_log_event` を非 `optout` event（`hook-error` / `session-mismatch` / `unresolved-steering`）で呼ぶ経路も、即死せず既存の best-effort 契約（戻り値 0）どおりに動くようになった
- `tests/test_session_start_hook_compact_resume.py` の post-merge seed 系 3 テストが、実行環境の状態を読み書きしていた問題を修正した。(1) `GDD_STEERING_DIR` を外すだけで `cwd` を固定していなかったため、`gdd_detect_active_steering` が cwd 起点の `git rev-parse` で **実行環境の `.steering/` を発見**し、active な GDD worktree 内でスイートを回すと結果が変わっていた。さらに `mkdir "${_steering_dir}/.gdd_is_running"` が live な steering にロックを作り、消えるのは pre-compact hook のときだけだった。(2) `GDD_HOOK_STATE_DIR` を渡していなかったため、hook が `${HOME}/.claude/.gdd-hook-state/last-turn-failure.json` を解決し、成功経路の `_gdd_consume_last_failure_record` が **開発者の実ファイルを `rm -f` していた**。テスト側で cwd を git 管理外の一時ディレクトリに固定し、`GDD_HOOK_STATE_DIR` を per-test の一時ディレクトリへ向けた（テストのみの変更）

#### Affected Files

- `hooks/scripts/lib/self-review-evidence.sh`（`gdd_sr_log_event` の記録先解決を 3 分岐化 + 書き込み条件に `[[ -n "$_state_dir" ]] &&` を追加）
- `hooks/scripts/run-pre-push-gate-hook.sh`（optout 記録呼び出し（修正前 145 行）を `if ( ... ) 2>/dev/null; then` に変更 + 意図コメント追加。以降の行が 6 行ずれる）
- `tests/test_pre_push_gate_contract.py`（`_run_hook` に `drop_env` 追加 + 回帰テスト 6 本追加）
- `tests/test_session_start_hook_compact_resume.py`（post-merge seed 系 3 テストを共有ヘルパーへ集約し cwd と `GDD_HOOK_STATE_DIR` を隔離、`_run()` と直呼び 2 箇所にも state dir を注入、`isolated_cwd` に repo 境界を張って `TMPDIR` が git repo 配下でも隔離が崩れないようにした + 回帰テスト 3 本追加 + 既存 2 テストの assertion 強化）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.41.7）
- `CHANGELOG-archive-3.md`（新規。§ Archive の 1200 行トリガに従い `### [0.40.3]` 〜 `[0.38.0]` を移動。本文は変更していない）
- `README.md` / `CONTRIBUTING.md`（構成の記載に `CHANGELOG-archive-3.md` を追加）
- `CHANGELOG.md` § Archive（回転トリガ「1200 行に達したら新しい連番 archive へ移して 800 行台まで戻す」を `### [0.40.7]` の § User Action Required から昇格。同節が archive へ移ると運用規約が CHANGELOG から消えるため）
- `docs/learned-patterns.md`（repo root。判定経路の形を規約に追記）

#### User Action Required

- **`HOME` 未設定環境でこの escape hatch を使っていた場合**: 本修正後は記録できないため push が block されるようになる。復旧するには、**hook プロセス自身の環境変数**として記録先を与える。具体的には Claude Code のセッションを起動する前に `export GDD_HOOK_STATE_DIR=<書き込み可能な絶対パス>`（または `export HOME=<書き込み可能な絶対パス>`）しておく。**`GDD_HOOK_STATE_DIR=... git push ...` のようにコマンド文字列の先頭に置いても効かない**（実測: block のまま）—— hook が command 文字列から解釈するのは `GDD_SKIP_PRE_PUSH_GATE` だけで、記録先はプロセス env からしか読まないため。kill switch（`~/.claude/gdd-hooks-disabled`）と block reason が案内する escape hatch は、この環境ではどちらも効かない（kill switch は `HOME` 依存、escape hatch は今回 block された当のものと同一で循環する）
- それ以外の利用者（`HOME` が設定された通常環境）は挙動変更なし

#### Validation / Eval Impact

- `tests/test_pre_push_gate_contract.py` に 6 本追加（AC-1 / AC-2 ×2 / AC-3 / AC-4 / AC-8）。うち 4 本は修正前 RED、2 本（AC-3 / AC-8）は非回帰の基準線
- 変異注入 4 通りをすべて実測し `worklog.md` に記録した（下記 Known Limitations 参照）
- 最終回帰: `pytest plugins/gate-driven-development/tests/ -q -n auto` = **2146 passed, 1 skipped, 12613 subtests passed**（baseline 2113 + 追加 13 本。うち 6 本が pre-push gate の回帰、7 本が hermetic 化の回帰）。hermetic 化により **active な GDD worktree の中でも** failed 0 になる（従来は clean な detached worktree でのみ成立と記録していた）
- hermetic 化の 4 ガードはそれぞれ独立に load-bearing であることを変異注入で実測した: (A) `_run_post_merge_seed` の cwd 固定を外す → hermetic テスト 3 ケースが RED / (B) 同ヘルパーの `GDD_HOOK_STATE_DIR` を外す → 1 本 RED / (C) `_run()` の `GDD_HOOK_STATE_DIR` を外す → 1 本 RED / (D) `isolated_cwd` の repo 境界を外す（`TMPDIR` を git repo 配下に置いた条件下）→ 7 本 RED
- `evals/evals.json` への影響なし

#### Known Limitations

- **2 段ガードの相互冗長性（実測）**: 変異 (a)（helper ガード除去）は AC-2 ×2 / AC-4 を RED にする一方 AC-1 は GREEN のまま残し、変異 (b)（呼び出し側 subshell 除去）も AC-1 を GREEN のまま残した。すなわち呼び出し側 subshell は現時点では load-bearing ではない。AC-1 の判別力は変異 (d)（両ガード同時除去 → AC-1 / AC-2 ×2 / AC-4 すべて RED）で担保している。Approved Direction に従い、subshell は helper 内の未知の即死要因への保険として残す
- **スコープ外の同種欠陥が 5 箇所残存**: `run-merge-gate-hook.sh:166` / `run-session-start-hook.sh:280,367,643,655` に未ガードの `${HOME}` が残っている（`run-stop-failure-hook.sh:113` は当初 6 箇所としていたが実測で既にガード済みと判明し除外）。別 PR で対応する
- **block reason 文言は変更していない**: `HOME` 未設定環境で block されたとき、reason 文言自体には `GDD_HOOK_STATE_DIR` での復旧手順が案内されない（requirements の非スコープ「block reason 文言の変更」に該当するため）。復旧手順は本 entry の User Action Required にのみ記載する
- **同種の hook state 汚染が他のテストファイルに残る**: `tests/` 配下で `run-session-start-hook.sh` を起動するのは **22 ファイル**（`.py` 20 + `checks/*.sh` 2）。うち `GDD_HOOK_STATE_DIR` を設定しているのは本 PR 適用後で 2 ファイル（本 PR で直した `test_session_start_hook_compact_resume.py` と、元から設定していた `test_session_start_last_turn_failure_contract.py`）で、**残り 20 ファイルは未設定のまま**。本 PR は FAIL を出した 1 ファイルのみを対象とし、残りは別 PR に送る
- **`test_merge_gate_followup_findings.py::test_large_payload_stays_far_below_the_hook_timeout` は負荷依存**: 壁時計で `elapsed < 2.5s` を assert しており、`-n auto` でマシンが飽和すると 3.2s 程度まで伸びて落ちることがある（実測: 2 回中 1 回。単独実行では 0.73s）。本 PR の差分とは無関係で、閾値の見直しは別 PR
- CI（Linux）上での挙動は未検証（macOS / bash 3.2 系で実測）

### [0.41.6] - 2026-09-07

#### Summary

GDD を使う別の repo の PR（レビュー bot の round-9 指摘。3 巡連続で「前回指摘・未対応」）: `gdd-codebase-health-baseline.json` の `current_lines` / `current_count` / `current_complexity` は、PR の繰り返し rebase 後のワーキングツリーから採取した値をそのまま信頼していたため、PR 自身がその場で加えた増分を「既存 debt」として黙って baseline に取り込めてしまっていた（当該 PR の baseline エントリの `reason` 欄自身が rebase 由来であることを認めていた）。gate script 自身が base branch との merge-base を「pre-PR ref」として解決し、baseline の記録値がその ref 時点の実測値を超えていないかを検証するチェックを 3 セクション全てに追加した。

#### Fixed

- `scripts/gdd-codebase-health.py`: `resolve_pre_pr_ref(repo, base_ref)` を追加し、既存の `resolve_changed_base` で解決した base branch と `HEAD` の `git merge-base` を「PR 前の状態」として求める。`--mode changed` のときのみ解決する（`survey` は PR 文脈が無いため対象外）
- 同上: `read_text_at_ref` / `measure_lines_at_ref` / `measure_python_function_count_at_ref` / `measure_python_complexity_at_ref` を追加し、`git show <ref>:<path>` で任意の ref 時点のファイル内容を実測する。対象ファイルがその ref に存在しない場合（新規追加ファイル）は `None` を返し、比較対象が無いケースを誤検出しない
- 同上: `validate_large_file_baseline` / `validate_python_function_count_baseline` / `validate_python_complexity_baseline` に検証を追加。baseline の記録値が pre-PR ref 時点の実測値を超えている場合、High severity の `codebase_health_baseline` finding を報告する

#### Affected Files

- `scripts/gdd-codebase-health.py`
- `tests/test_engineering_baseline_architecture_contract.py`（`TestCodebaseHealthPrePrRefMeasurement` を追加。3 セクションそれぞれの inflation 検出・pre-PR ref 一致時の非検出・新規ファイルでのスキップ・`resolve_pre_pr_ref` 単体の 3 系統、計 8 test）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（version bump）
- `docs/VERSIONING.md`（現行バージョン更新）

#### User Action Required

- なし。既存 baseline の記録値が pre-PR ref 時点の実測値以下であれば挙動は変わらない。記録値が実測を上回っている場合のみ、新たに High finding が出る（その場合は baseline を pre-PR ref の実測値まで下げること）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`: `2135 passed, 1 skipped, 12608 subtests passed`（本 PR 反映後の HEAD で実測）
- `bash tests/validate-plugin.sh`: exit 0
- 修正前のコードに一時的に戻して新規 8 test が red（5 件失敗: 3 件は finding 不在、2 件は `resolve_pre_pr_ref` 未定義の `AttributeError`）になることを確認した上で修正を戻し、green を再確認（TDD 手順）
- Superpowers Benchmark Summary: not_applicable（changed GDD primitive なし。state machine field / reviewer set / hook 契約 / `Resume From` 等の変更を含まない、gate script 内部の計測ロジック修正）

### [0.41.5] - 2026-09-07

#### Summary

PR 旧#57（v0.41.3）マージ直後の独立レビュー（merge 差分・diff-only）で見つかった high 1 件を、W-29 の方針「high 0 でマージし、残りは follow-up PR で閉じる」に従い単独 PR で修正した。あわせて PR 旧#57 の帳簿系 3 件（case 番号・移植コメント・箇所数）と、`SELF_REVIEW_PARSE_TIMEOUT` 予算の複数 target 前提の未整合を Known limitations に記録した。

#### Fixed

- `hooks/scripts/lib/steering_size.py`: `MultiEdit` の `edits` に非 dict 要素、または `replace_all: true` の edit を 1 つ混ぜると、`_compute_post_write_size` がファイル全体の算出を諦めて None（= 非 deny）を返し、上限超過の edit が素通りしていた（実測 rc=0 → 2。PR 旧#52 の R3 旧#3 が review-detection branch へ委譲した項目で、v0.41.3 は未処理のまま出荷）。原因は R4 旧#1 と同型の「算出不能なら小さい方・諦める方へ倒れる」設計で、原因単位で直した: 非 dict / old・new 欠落の要素は増分を持たないので無視して残りの総和で判定を続け、`replace_all` は既存内容の出現回数 × 1 回分の delta で計上する（既存内容が読めなければ 1 回分を下限。case 52 に 3 fixture）
- 同上: 旧 case 7「`replace_all` の Edit は算出不能なので deny しない」は fail-open だった（`a`×19,990 に `a` → `b`×1000 を replace_all すると post size 約 20MB を通していた）。契約を「出現回数で算出し超過なら deny」に更新し、上限内 allow の case 7b を追加した
- 同上: 上記の初版（`per_hit × hits`）が別形の迂回を 2 つ開けていた（PR 旧#58 の独立レビュー blocking 2 件。実測 rc=0）。(1) 縮小 edit（負の delta）に元の内容の出現回数を掛けるため、MultiEdit の逐次適用で実際には起きない縮小が増分を相殺できた（old の別名 `oldText` で縮小だけを水増しする形も同根）。(2) `old_string: ""` の `replace_all` は `str.replace` の仕様で文字数 + 1 箇所へ挿入されるのに 1 回分に丸めていた。設計原則を**「size 判定は正確な合成シミュレーションではなく deny 寄りの上界推定」**に固定して閉じた: 縮小は計上しない / old が非 str・欠落は 0 バイト扱い（純増）・`edits` が dict なら 1 要素として扱う（受理集合の対称性、medium 旧#1）/ `replace_all` は出現回数倍で空 old は文字数 + 1 倍 / 既存内容が読めない・old が無いときは 1 回分を下限（medium 旧#4）。case 53 に 7 fixture（AC-5 の出口「縮小のみの replace_all は上限超過中でも allow」の回帰 pin を含む）
- 同上（2 巡目の独立レビュー blocking 2 件）: (1) `replace_all` の出現回数を**元の内容だけ**で数えていたため、MultiEdit の逐次適用で先行 edit が後続 `replace_all` の対象を増やす形（`HEADER` → `Q`×500 の後に `Q` → `Q`+`y`×100 を replace_all）が hits=0 → 1 回分に丸められ、実サイズ 69,491B（上限の 3.5 倍）が allow に倒れた。haystack を「元の内容 + 全 edit の new 文字列」にして逐次適用で作られうる出現箇所の上界を採る（case 54）。(2) `hooks/scripts/validate-steering-write.py` の `extract_content_chunks` が `edits` の dict を落としており、size 側だけ dict を受理した結果、secret / email / path の全 detector を型ゆらぎ 1 つで素通りできる非対称が顕在化した（既存欠陥）。size 側と同じ正規化に揃えた（case 54b）。1MB 境界の 2 経路（読まない → 1 回分下限 / ちょうど 1MB は読む）も case 54c / 54d で固定

#### Known limitations

- `hooks/scripts/validate-steering-write.py`: `SELF_REVIEW_PARSE_TIMEOUT` の予算注釈「3s×2 + advisory lint 2s = 8s < 10s」は単一 target 前提（PR 旧#52 R4 旧#3）で、v0.41.3 が契約化した複数 target payload では advisory lint が target ごとに起動し、最悪 `3s×2 + 2s×N` で `hooks.json` の 10 秒に到達しうる（lint が上限まで粘る必要があり latent。取り込み後の独立レビュー medium 旧#2）。1 invocation 共有 deadline か lint 起動本数の上限で閉じる。後続で対応
- 既存内容の読み取りは `replace_all` を含む `Edit` / `MultiEdit` のときだけ行い、1MB を超えるファイルでは読まずに 1 回分を下限に計上する（PR 旧#58 medium 旧#3）。読み取りで `MemoryError` が出る経路は `(OSError, ValueError)` で捕捉されず `validate-steering-write.py` の top-level guard（fail-closed）に委ねる
- `tests/`: `GDD_HOOK_STATE_DIR` を tmp に向けた環境でフル pytest を回すと hook state を前提にする既存テスト 17 件が偽 RED になる（2 巡目 medium A。既存欠陥で本 PR の範囲外）。`conftest.py` の autouse fixture で環境から落とすか各 `_run_hook` で上書きする。**後続で対応**
- 上界推定の近似 2 点（PR 旧#58 medium 旧#2）: (1) `replace_all` の出現回数は「元の内容 + 全 edit の new 文字列」を haystack に数える上界であり、逐次適用の厳密な合成ではない（2 巡目 BL-1 で「元の内容だけ」の版が実測で迂回されたため上界側へ寄せた。上界なので過剰 deny はありうるが迂回は残っていない、を case 54 で固定）。(2) 縮小を計上しないため、上限超過中に「縮小と追加を同じ MultiEdit で行う」write は実態が縮小でも deny されうる。縮小を先に単独の write で行えば通る（fail-closed 側の誤 block として受容）

#### Affected Files

- `hooks/scripts/lib/steering_size.py` / `hooks/scripts/validate-steering-write.py`（注釈のみ）/ `tests/test_steering_size_deny_contract.py` / `CHANGELOG.md`（v0.41.3 の case 番号訂正・Known limitations 追記）/ `docs/VERSIONING.md` / 3 manifest

#### Validation

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`: `2128 passed, 1 skipped, 12609 subtests passed in 99.63s (0:01:39)`（2 巡目対応・旧#55 取り込み後の HEAD で実測）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0（`version-not-consumed: OK (shipping v0.41.5; integration target consumed v0.41.4)`）
- Case 52 / Case 7 / Case 53 の再現: 非 dict 要素・`replace_all` decoy・`replace_all` 単独（約 20MB）・縮小による相殺（逐次適用 / 別名）・空 old・`edits` dict・非 str old の 7 形で修正前 rc=0 → 修正後 rc=2。縮小のみの `replace_all`（上限超過中）は rc=0 のまま。2 巡目: 先行 edit による増幅（実サイズ 69,491B）と `edits` dict の secret 素通りも修正前 rc=0 → 修正後 rc=2

### [0.41.4] - 2026-09-07

#### Summary

merge gate hook（`run-merge-gate-hook.sh`）に残っていた最後の無防備な `_mg_log_suppressed` 呼び出し（`legacy-evidence-no-blocking-field`）を、v0.41.0 の `unowned-active-marker-demoted`（adr.md ADR-1）と同じ subshell ガードへ揃えた。記録失敗でシェルごと即死し、**gate が無出力で素通りする** fail-open を塞ぐ。

`_mg_log_suppressed` は `set -euo pipefail` 下で 2 通りに即死しうる。`HOME` 未設定（`set -u`）と、`shasum` / `sha1sum` の**両方**が無い・失敗する（`_repo_id="$(... | shasum ...)"` が `pipefail` で非 0）。即死すると hook は何も出力せずに終わり、PreToolUse の契約上「block を返さなかった」= 素通りになる。

呼び出し 5 箇所（event 名では 4 種。`unresolved-steering-on-merge` が 2 箇所）のうち、ガードが要るのは**記録後も処理を続ける** 2 箇所だけで、`unowned-active-marker-demoted` は v0.41.0 で既に隔離済みだった。残る `legacy-evidence-no-blocking-field`（旧書式の証跡を寛容側の既定で通したことの監査記録）は未対応のまま残っており、ここで即死すると**独立レビューの sha / high / blocking 検査に到達せず、証跡が不十分なまま `gh pr merge` が通る**（fail-closed gate の保護面の消失）。残る 3 箇所（`kill-switch-bypass` 1 箇所 / `unresolved-steering-on-merge` 2 箇所）は直後が `exit 0` なので結果が変わらない。この hook が block を表明する手段は stdout の `{"decision": "block"}`（`block()` を呼んで `exit 0`）であり、即死時の rc=1・stdout 空はどちらの経路でも block にならないが、これら 3 箇所はそもそも通過が確定している位置にある。

なお `|| true` だけでは不十分である。bash は `||` の左辺の関数呼び出しの中では errexit を抑止するため `pipefail` 由来の死は捕まえられるが、`set -u` の未定義変数エラーは抑止しない。subshell が load-bearing なのはこの 1 面。

#### Fixed

- 旧書式（`blocking` key 欠落）の証跡経路で、suppression ログの記録が失敗しても merge gate の block 判定が出力されるようになった（記録は従来どおり best-effort で、成否は gate 判定を変えない）

#### Affected Files

- `hooks/scripts/run-merge-gate-hook.sh`（`legacy-evidence-no-blocking-field` の呼び出しを subshell で隔離）
- `tests/test_merge_gate_hook_evidence_gate.py`（`LegacyEvidenceLogFailureContainmentTests` を追加。`shasum` 失敗経路と `HOME` 未設定経路の 2 面）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`、`docs/VERSIONING.md`（版数 0.41.4。origin/main が分岐後に v0.40.15 / v0.41.0 / v0.41.1 / v0.41.2 / v0.41.3 と版数を消費したため採番し直した）
- `CHANGELOG.md` / `CHANGELOG-archive.md`（本 entry の追加で `CHANGELOG.md` が行数上限 1500 を超えた（1581 行）ため、§ Archive の運用どおり `### [0.37.4]` 〜 `[0.37.0]` の 5 節を archive へ移した。**本文は移動時に変更していない**。1581 → 1412 行）

#### User Action Required

- なし（hook 内部の best-effort 記録の隔離のみ。gate の判定条件・block reason は変更していない）

#### Validation / Eval Impact

- 回帰テスト `LegacyEvidenceLogFailureContainmentTests` を 2 件追加。いずれも旧書式 × `high: 1`（本来 block）の証跡で hook を起動し、`independent-review-missing` の block が出ることを検査する
  - `test_shasum_failure_still_reaches_evidence_gate`: `shasum` / `sha1sum` が必ず失敗する stub を PATH 先頭に挿す。修正前は stdout が空（無出力素通り）で RED
  - `test_unset_home_still_reaches_evidence_gate`: `HOME` / `GDD_HOOK_STATE_DIR` を落とす（v0.41.0 が `_run_hook` に足した `drop_env`）。subshell を `|| true` へ弱める mutation はこちらでのみ落ちる
- `evals/evals.json` への影響なし

#### Known Limitations

- **本 entry の「最後の無防備な呼び出し」は `_mg_log_suppressed` に限った話であり、GDD hook 全体で同種の欠陥が解消したという意味ではない**。独立レビューが実測で、同じクラスの silent fail-open が `hooks/scripts/run-pre-push-gate-hook.sh:145` に**現存する**ことを確認した。`gdd_sr_log_event`（`lib/self-review-evidence.sh:486`）も未ガードの `${HOME}` を持ち、`HOME` を落として hook を起動すると rc=1 / stdout 空・stderr に `HOME: unbound variable`。当該分岐は「記録できないなら push を止める」と**明示的に fail-closed に設計された**位置なので、記録して継続するだけの merge gate 側より意図の破壊が大きい。既存の `tests/test_pre_push_gate_contract.py` は `_run_hook` が `os.environ.copy()` で必ず `HOME` を持つため、この面を踏めない。**別 PR で対応する（v0.41.7 で解消）**
- 修正は呼び出し側ガードで、`_mg_log_suppressed` 本体（`${HOME}` / `shasum` パイプ）は素のまま。6 箇所目が「記録後も継続する」位置に追加されれば無言で再発しうるが、この判断は v0.41.0 の adr.md ADR-1 が確定させた設計方針に揃えたもの。規約を強制する lint / contract test は未整備

### [0.41.3] - 2026-09-07

#### Summary

reviewer recall の実測（PR 旧#37 の diff に対し、後段レビューで確定した欠陥 11 件を各 reviewer 構成へ headless で当てた）を受けて、レビュー機能の検出力を上げる 4 点を入れた。

実測の要点は 3 つ。(1) 単体 recall は最大 3/11 で、5 構成の和集合でも 8/11 にしかならない。(2) Pre-Push の 3 レーン自己周回は **0/11 で `approved`** を出した（拾った 7 件はすべて CHANGELOG 文言・行番号・日付といった帳簿系）。(3) High 3 件のうち、既存 escape hatch による deny 迂回は唯一拾った構成が medium、別名キーによる無言 allow は low と判定された。

そこで、これまで「たまたま踏んだ reviewer だけが拾っていた」型を検査項目として固定し（推論型 4 / 照合型 4）、実害クラスの severity を下げられなくし、検出責務を自己周回から独立レビューへ移した。

#### Fixed

- `hooks/scripts/lib/steering_size.py`: 同一ファイルを `file_path` と `path` 等で二重指定した payload が target 2 件扱いになり size 判定を迂回できた（実測 rc=0 → 2）。重複を畳んでから single-target 判定（case 47。新 独立レビュー契約の観点 (h) が発見）
- `hooks/scripts/lib/steering_size.py`: 上記の畳み込みが**生文字列の完全一致**だったため、`t/state.md` と `t/./state.md` のように綴りを変えるだけで target 2 件に戻り、同じ迂回が残っていた。dedupe を `Path(t).resolve()` 済みの実体で行うように変え、バックスラッシュ→スラッシュの読み替え（POSIX ではバックスラッシュもファイル名の一部で、別ファイルを stat しうる）を dedupe key からも stat 対象からも外した（case 47 に綴り違い fixture を追加）
- `hooks/scripts/lib/steering_size.py`: それでも `resolve()` は case-fold しないため、case-insensitive FS（Darwin 既定。同一 inode を実測）で `…/state.md` + `…/State.MD` は resolved 2 件のまま dedupe を抜け、single-target 条件が外れて size 判定ごとスキップされていた（実測 rc=0）。**dedupe による single-target 前提そのものを撤廃**し、`_steering_size_targets()` が target を列挙して 1 件でも size deny が成立すれば deny する契約に変えた（独立レビュー R2 旧#1。case 47 に case 変種 fixture、case 24 / 24c / 24d / 24e に複数 target の deny / allow fixture）。既存 case 24「複数 target = 非 deny」は新契約へ更新した
- `hooks/scripts/run-pre-push-gate-hook.sh`: step 13b が `Independent Review` の `high` しか見ておらず、merge gate（`high == 0 && blocking == 0`）と受理集合が非対称だった。`high: 0 | blocking: 2` が push gate だけ素通りしていたため、pre-push も `blocking` を見るようにした（reason code は `independent-review-high` のまま）
- `hooks/scripts/run-pre-pr-gate-hook.sh` / `references/post-completion-pr-flow.md`: `dry-not-reached` の block 文言と post-completion フローの正本が旧定義（「2 連続クリーンまで繰り返す」「独立レビューは未到達時の代替」）のまま残り、gate が operator に撤廃済みの手順を指示していた。新定義（内部整合レーン 1 周で新規 high / blocking ゼロ ＋ standard は独立レビュー 1 回 high 0 が**必須で代替ではない**）へ同期した
- `hooks/scripts/run-pre-pr-gate-hook.sh`: 上記の `dry-not-reached` 文言が独立レビューを要求する一方、pre-PR gate 自体は `Independent Review` を一切読んでおらず、機械強制できる述語を自己申告のまま残していた。pre-push step 13b と同じ parser / 述語（HEAD sha 一致・`high: 0` かつ `blocking: 0`）で検査するようにした（reason code `independent-review-missing` / `independent-review-stale` / `independent-review-high`。独立レビュー R2 旧#5）
- `references/independent-review.md` / `references/self-review-lanes.md`: 受理述語が `high: 0` のみと書かれており、実装（pre-push / merge gate とも `high == 0 && blocking == 0`）と非対称だった。両文書を `high: 0` かつ `blocking: 0` に統一した（独立レビュー R2 旧#2）
- `references/self-review-lanes.md`: 「merge gate が必須とするレビュー入力は独立レビューのほう」という断定が実装と不一致だった（`Bot Review Received: received: yes` の経路では merge gate は `Independent Review` を読まない）。「`received: yes` は bot レビューのみで通る / `received: no` の経路でだけ独立レビューが待機免除の条件」に訂正した（独立レビュー R2 旧#3）
- `hooks/scripts/lib/self-review-evidence.sh` / `references/self-review-lanes.md`: `standard` は接地・敵対を独立レビューへ委譲するのに schema が `adversarial` に uint を強制していたため、回していないレーンに 0 を書く証跡になっていた。`not_applicable` 理由 token に `independent-review` を追加し、`grounding` / `adversarial` の委譲記録形として受理する（`internal` と他 token は従来どおり不可。独立レビュー R2 旧#4）
- `hooks/scripts/lib/steering_size.py`: 上記の複数 target 全件判定は 2 件形しか閉じておらず、`…/.steering/x/State.MD` を**単独 target** で渡すと `limits` 照合が大小文字を区別するため target 0 件になり、case-insensitive FS 上で同一 inode の `state.md` へ上限超過 Write が通っていた（実測 rc=0 → 2）。`.STEERING/` も同様。`limits` は小文字 key で引き（`_limit_for`）、`.steering` 判定も大小無視（`_is_under_steering`）にして、既存 `is_steering_path` と同じ規律に揃えた（独立レビュー R3 旧#1。case 51（PR 旧#52 取り込み時に case 48 から改番）に単独 target の casing 変種 3 fixture を追加）
- `hooks/scripts/run-pre-push-gate-hook.sh` / `run-pre-pr-gate-hook.sh` / `hooks/scripts/lib/merge-gate-evidence.sh`: `independent-review-*` の block reason が復旧要素 2（必要 key の全列挙）に self-review 側の key 一覧（`sha,rounds,consecutive_clean,dry,lanes`）を出していたため、operator は `Independent Review` 行の書式を hook ソースからしか復元できなかった。`GDD_IR_RECOVERY_CORE`（`sha,reviewer,context,high,medium,blocking,at`・正本 `references/independent-review.md`）を lib に置き、3 code はそちらを使う。key 列挙が parser の必須集合と一致することは `tests/test_independent_review_recovery_contract.py` が key を 1 つずつ落として機械検査する（独立レビュー R3 旧#7）
- `hooks/scripts/lib/self-review-evidence.sh`: `adversarial=not_applicable(independent-review)` が Task Size を見ずに受理され、独立レビューを要求する gate が無い `quick (standard)` / `quick (express)` でも委譲を記録できた。パーサが Task Size（第 3 引数）を受け取り `standard` でのみ受理するようにした（独立レビュー R3 旧#10）
- `hooks/scripts/validate-steering-write.py`: write 時の証跡バリデータだけが `gdd_parse_self_review_field` を **Task Size 無し**で呼んでいたため、`quick (standard)` / `quick (express)` で委譲記録形が「write は通るが pre-push / pre-PR gate は invalid にする」非対称になっていた（同 module が T-19 Attempt 1 M-1 として明示的に防いだ形の再発）。書き込み対象 `state.md` の既存内容 + chunk から `Task Size` を読み、`normalize_task_size()` で正規化してから第 3 引数へ渡す（独立レビュー R4 旧#1）
- `hooks/scripts/lib/self-review-evidence.sh`: `grounding=not_applicable(independent-review)` は Task Size を見ずに受理されており、R3 旧#10 で `adversarial` 側に閉じた穴が `grounding` 側に残っていた。`GDD_SR_ADVERSARIAL_DELEGATION_SIZES` を `GDD_SR_DELEGATION_SIZES` へ一般化し、判定を `_gdd_sr_delegation_size_ok()` 1 本に集約して両レーンへ同じ受理集合を適用する（他の理由 token は従来どおり size 非依存。独立レビュー R4 旧#3）
- `hooks/scripts/run-pre-pr-gate-hook.sh`: 未知の Task Size を pre-push gate は `standard` へ正規化して渡すのに pre-PR は生値のまま渡しており、未知値の `state.md` では pre-PR だけが独立レビューを要求しつつ委譲記録形を invalid にする自己矛盾になっていた。pre-push step 9 と同じ規則（既知 4 値以外は `standard`）へ揃えた（独立レビュー R4 旧#7）
- `CONTRIBUTING.md` / `skills/gdd-pr-review/SKILL.md`: 証跡の**書き手側** 4 箇所が受理述語を `high: 0` のみと記述しており、実装（3 gate とも `high == 0 && blocking == 0`）と非対称だった。`high: 0` かつ `blocking: 0` に統一した（独立レビュー R3 旧#3）
- `skills/gdd-pr-review/SKILL.md`: Pre-Push Self Review の schema と手順に、`standard` で接地・敵対を独立レビューへ委譲した場合の記録形 `grounding=not_applicable(independent-review),adversarial=not_applicable(independent-review)` を明記した（skill どおりに書くと「回していないレーンに 0」へ戻る片側更新だった。独立レビュー R3 旧#4）
- `references/self-review-lanes.md`: § followup 周回時のレーン要求（自己周回は内部整合のみ）と push 前の新定義（内部整合 1 周 ＋ 独立レビュー 1 回）が矛盾していた。**独立レビューは自己周回の免除対象ではない**（`standard` は followup 再 push でも要求する。「push 前 1 回」は push 1 回あたり 1 回の意味）ことを明記して両段落を一致させた（独立レビュー R3 旧#6）
- `references/reviewer-common.md` ほか参照側: 新節名「常時 High の実害クラス」が予約 alias **実害クラス**（= `is_blocking` の 4 category）と衝突し `blocking` の数え方が二義になっていた。節名を「常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）」に改め、両者が別概念であること（重なるのは `fail-open` のみ。`blocking` の導出は § finding category が単独正本）を明示した（独立レビュー R3 旧#5）
- `references/fixed-models.md` / `references/independent-review.md`: モデル指定の唯一の正本の外で `Opus 5 + effort max` を定義していた。`independent_review` tier（Claude Code: `Opus 5` + `effort=max`、Cursor / Codex は `general_heavy_risk` と同じ写像）を追加し、`independent-review.md` は tier を pointer 参照するだけにした（独立レビュー R3 旧#8）
- `hooks/scripts/validate-steering-write.py`: R4 旧#1 で新設した `Task Size` の読み取りが `OSError` しか捕捉しておらず、target path に lone surrogate / NUL が含まれると `ValueError`（`UnicodeEncodeError` を含む）が `main()` まで抜けて hook が rc=1 で落ち、secrets / placeholder / peer-turn / origin-session の既存 deny が 1 件も走らずに fail-open していた。同 module の `read_text` 全 7 箇所を `except (OSError, ValueError)` へ揃え、併せて同じ path で落ちる `_state_key()` の `encode`（`errors="surrogatepass"`）と advisory lint の `Path(...).resolve()`（例外時は当該 target のみ skip）も閉じた（PR 旧#52 と同じ規約。独立レビュー R5 旧#1）
- `hooks/scripts/validate-steering-write.py`: `Task Size` を `existing_text + chunk_text` の連結から引いていたが、`state_field_value()` は**最初の値付き出現**を返すため既存値が常に勝ち、「同じ書き込みで更新する場合に chunk 側の新値を使う」というコメントの主張と逆になっていた。`state_field_value(chunk_text, ...) or state_field_value(existing_text, ...)` の chunk 優先へ変え、同一 write で `standard` → `quick (standard)` へ変える fixture で委譲 token が invalid になることを固定した（独立レビュー R5 旧#2）
- `references/state-field-tiers.md` / `references/fixed-models.md`: `Independent Review` の作り方の正本が 2 つに割れており、Tier 表側は実装文脈（steering artifacts）を読むのが job の `gdd-completion-reviewer` を否定命令付きで dispatch するよう案内していて、新契約の条件 1「実装文脈を渡さない」に違反していた。両文書とも「実装文脈を渡さない独立実行（手順の正本は `references/independent-review.md`）」に訂正し、`gdd-completion-reviewer` の dispatch は independent review ではないことを `independent_review` tier の記述に明記した（独立レビュー R5 旧#3）
- `references/self-review-lanes.md`: 空洞化率の定義「`lanes` が全て 0」が `standard` の委譲記録形（`grounding`/`adversarial=not_applicable(independent-review)`）では原理的に成立せず、対象 size で指標が死んでいた。「`lanes` の数値が全て 0 かつ委譲 token でも無い」へ更新し、委譲記録形は「回した」側に数える（逐語 pin も同時更新。独立レビュー R5 旧#4）
- `references/self-review-lanes.md`: § followup 周回時のレーン要求 の「接地・敵対は初回 push 時に自己周回で再適用」が、同ファイルの発火表・新定義（`standard` は自己周回では回さない）と矛盾していた。当該文を `quick (standard)` へスコープ限定した（R3 旧#6 の「両段落を一致させた」は片側のみだった。独立レビュー R5 旧#5）
- `hooks/scripts/lib/self-review-evidence.sh`: 証跡書式の header コメントが `adversarial=<n>` のままで、委譲記録形に更新した skill 側テンプレートと片側更新だった。`adversarial=<n|not_applicable(<reason-token>)>` へ同期した（独立レビュー R5 旧#6）
- `hooks/scripts/lib/steering_size.py`: `_steering_size_decision()` の上限引きが `_limit_for(...) or 0` で、将来 artifact 以外の path で呼ばれると「上限 0 = 全 write deny」へ無音で倒れる形だった（現状は `_steering_size_targets` が保証しているため latent）。`None` は `or 0` で潰さず size 非対象として早期 return する（独立レビュー R5 旧#7）

#### Known limitations

- `hooks/scripts/lib/steering_size.py`: `content` に lone surrogate が 1 つ含まれると `encode("utf-8")` の `UnicodeEncodeError` が捕捉されず hook が非 block で落ち、既存 deny が 1 件も走らない（独立レビュー R3 旧#2。origin/main にも存在する既存欠陥で本 branch の regression ではない）。**PR 旧#52（v0.41.2）で修正済み**。本 branch は 旧#52 マージ後の origin/main を取り込み（`steering_size.py` / `validate-steering-write.py` / 契約テスト / CHANGELOG の conflict を解消、本 branch の Case 48 は Case 51 に改番）、閉じた
- `references/fixed-models.md` に追加した `independent_review` tier が、全 tier を列挙する3 つの写像表（`skills/gdd-model-routing/SKILL.md` / `references/cursor.md` / `references/codex.md`）と `tests/test_model_routing_contract.py` の tier リストに未反映（独立レビュー R4 旧#2）。**後続で対応**
- pre-push / pre-PR gate が旧書式（`blocking` key 欠落）の `Independent Review` を寛容側で通すとき、`references/self-review-lanes.md` が対で要求する `_mg_log_suppressed "legacy-evidence-no-blocking-field"` を出さず寛容化が無記録になる（記録しているのは merge gate のみ。独立レビュー R4 旧#5）。**後続で対応**
- `GDD_IR_RECOVERY_CORE` の注釈は `independent-review-missing` / `-stale` / `-high` の復旧要素 2 と宣言しているが、同 code を出す 3 hook のうち merge gate は従来どおり `GDD_MG_RECOVERY_CORE` を使い続けている（独立レビュー R4 旧#6）。**後続で対応**
- `hooks/scripts/validate-steering-write.py`: `SELF_REVIEW_PARSE_TIMEOUT` の予算注釈「3s×2 + advisory lint 2s = 8s < 10s」は単一 target 前提（PR 旧#52 R4 旧#3）で、本 branch が契約化した複数 target payload（Case 24 / 47）では advisory lint が target ごとに起動し、最悪 `3s×2 + 2s×N` で `hooks.json` の 10 秒に到達しうる（成立には lint が上限まで粘る必要があり latent。取り込み後の独立レビュー medium 旧#2）。1 invocation 共有 deadline か lint 起動本数の上限で閉じる。**後続で対応**
- `skills/gdd-pr-review/SKILL.md` の 3f（敵対レーンの入口・常時）と standard の「接地・敵対は自己周回で回さない」の整合（独立レビュー R6 旧#1）／merge gate 証跡の Ownership 記述に「`Independent Review` は初回 push 時に `gdd-pr-review` の手順で書く」を追記する件（R6 旧#3）／write hook（`state_field_value`）と gate（`gdd_extract_doc_field`）で Task Size の抽出器が異なる件（R6 旧#4。どちらも未知値は `standard` へ畳むため fail-closed）／効果測定の「レーン別検出数」に `Independent Review` の high / medium / blocking を含める件（R6 旧#6）／advisory 側の `single` 述語が生の `len(steering_targets)==1` のままで deny 側の全 target 判定と非対称な件（R6 旧#7。advisory のみ）。**後続で対応**

#### Changed

- `references/inline-review-checklists.md`: implementation-reviewer checklist に **推論型 4 項目**（既存機構との分岐相互作用 / 受理集合の対称性 / 例外で guard 全体が落ちる経路 / 正規化と判定の順序）と **照合型 4 項目**（記録 vs 統合先実態 / 注釈・ADR の主張 vs 実装 / テストマトリクスの欠けセル / 契約 vs 契約の優先順位）を追加した。各項目に対応分類と由来実例を 1 行添える既存書式に合わせている。severity guideline に「常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）」の参照 1 行を置いた
- `references/reviewer-common.md`: **deny 迂回 / guard bypass / fail-open / 例外で guard が落ちる** を「常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）」として節に切り出し、false positive 実績による severity 1 段階降格の適用対象外にした（この節が正本。checklist / self-contained-contract / implementation-gating SKILL は参照側）。節名は予約 alias「実害クラス」（= `is_blocking` の 4 category）との衝突を避けて命名しており、両者が別概念であること（`blocking` の数え方は § finding category が単独正本）を同節に明示した
- `references/self-review-lanes.md`: 発火表の `standard` 行で接地・敵対を「独立レビューが担う」に変え、`dry` 要求を「内部整合 1 周で新規 high / blocking ゼロ ＋ `Independent Review` 行（push 対象 tip の sha、high 0 かつ blocking 0）」に改めた。3 レーン定義表では接地・敵対の両方に「`standard` は独立レビューが担う」を書く（片側だけ更新しない。独立レビュー R2 旧#7）。**`dry` の 2 連続要件は撤廃**（2026-09-06 PR 旧#44 の定義を上書き）。§ merge gate 証跡 の `Bot Review Received` 説明にも「`Independent Review` が HEAD で high 0 / blocking 0 なら bot 待機は不要」を明記した（`received: yes` の経路では merge gate は `Independent Review` を読まず bot レビューのみで通る。独立レビューは `received: no` の経路でだけ待機免除の条件になる）
- `references/independent-review.md`（新規）: 独立レビューの契約（実装文脈を渡さない headless / subagent、read-only、diff-only、モデルは `references/fixed-models.md` の `independent_review` tier）、観点レーン (a)〜(f) に **(g) 例外で guard 全体が落ちる経路** と **(h) 受理集合の対称性** を加えた 8 レーン、出力フォーマット、証跡書式を定義した
- `hooks/scripts/run-pre-push-gate-hook.sh`: step 13b を追加し、`standard` で `Independent Review` 行の sha が push 対象 tip と一致し `high: 0` かつ `blocking: 0` であることを検査する（reason code `independent-review-missing` / `independent-review-stale` / `independent-review-high`）。`quick (standard)` / `quick (express)` / `trivial` は従来どおり免除。step 13 は `consecutive_clean == 0` も明示して落とす
- `hooks/scripts/lib/self-review-evidence.sh`: `dry: yes` の自己矛盾判定の閾値を `consecutive_clean < 2` から `== 0` へ緩めた（2 連続要件の撤廃に対応）
- `skills/gdd-pr-review/SKILL.md`: Pre-Push Self Review の手順を「内部整合レーン 1 周 ＋ 独立レビュー 1 回」に同期した（起動方法の正本は `references/independent-review.md` を 1 行で参照）
- `skills/gdd-pr-review-followup/SKILL.md`: § State / Worklog Contract の merge gate 証跡 段に `references/independent-review.md` への参照 1 行を足した（`independent-review.md` の `参照元` が本 skill を宣言しているのに片側リンクだった。独立レビュー R2 旧#6）
- `CONTRIBUTING.md`: 必須チェックに「独立レビュー 1 回（push 前・standard のみ）」を追加し、レビュー観点の表に 1 行足した
- `hooks/scripts/run-merge-gate-hook.sh`: merge gate の bot レビュー待機（`Bot Review Received: received: no`）を、`Independent Review` が HEAD sha で `high: 0` / `blocking: 0` のときは免除するようにした。bot レビューが恒久的に来ない repo で push のたびに 40 分の空待ちが発生していた（待機経過後に要求されるのも同じ独立レビュー）。独立レビューが無い / sha 不一致 / `high > 0` の場合は従来どおり `review-wait-not-elapsed` で block する

#### Affected Files

- `references/inline-review-checklists.md` / `references/reviewer-common.md` / `references/self-review-lanes.md` / `references/self-contained-contract.md` / `references/post-completion-pr-flow.md`
- `references/independent-review.md`（新規）
- `hooks/scripts/run-pre-push-gate-hook.sh` / `hooks/scripts/run-pre-pr-gate-hook.sh` / `hooks/scripts/run-merge-gate-hook.sh` / `hooks/scripts/lib/self-review-evidence.sh` / `hooks/scripts/lib/steering_size.py`
- `skills/gdd-pr-review/SKILL.md` / `skills/gdd-implementation-gating/SKILL.md` / `skills/gdd-pr-review-followup/SKILL.md`
- `CONTRIBUTING.md` / `docs/VERSIONING.md` / 3 manifest
- `tests/test_pre_push_gate_contract.py` / `tests/test_pre_push_independent_review_contract.py`（新規）/ `tests/test_self_review_lanes_contract.py` / `tests/test_self_review_evidence.sh` / `tests/checks/skill-body-budget.sh`
- `tests/test_steering_size_deny_contract.py` / `tests/test_pre_pr_gate_contract.py` / `tests/test_merge_gate_hook_evidence_gate.py` / `tests/test_merge_gate_hook_block_reason_quality.py` / `tests/test_merge_gate_followup_findings.py`
- `references/fixed-models.md` / `hooks/scripts/lib/merge-gate-evidence.sh` / `tests/test_independent_review_recovery_contract.py`（新規）/ `tests/_block_reason_support.py`
- `hooks/scripts/validate-steering-write.py` / `tests/test_validate_steering_write.py`（独立レビュー R4 旧#1）

#### User Action Required

- **`standard` の task で `git push` する前に、`state.md` の `## Gate Status` 節へ `Independent Review` 行を書く**。書式は merge gate と同一で、`sha` は push 対象 ref の tip、`context` は `diff-only`、`high` と `blocking` はともに 0 であること。欠落・sha 不一致・`high > 0` / `blocking > 0` は pre-push gate が block する。**`gh pr create` の pre-PR gate も同じ述語で block する**（そちらの sha は HEAD 基準）
- 3 レーンの自己周回は `standard` では不要になった。接地・敵対の観点は独立レビューが担う。証跡には `grounding=not_applicable(independent-review)` / `adversarial=not_applicable(independent-review)` と書く（回していないレーンに 0 を書かない）。この委譲記録形は `standard` 限定で、`quick (standard)` / `quick (express)` では invalid になる（それらの size は従来どおり件数を書く）
- `dry: yes` に `consecutive_clean: 2` は不要になった（1 で足りる）。既存の `consecutive_clean: 2` の証跡はそのまま有効

#### Validation

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/test_self_review_evidence.sh`
- `tests/checks/skill-body-budget.sh` / `tests/checks/self-review-lane-tokens.sh` / `tests/checks/version-not-consumed.sh`
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`: `2111 passed, 1 skipped, 12582 subtests passed`（PR 旧#52 取り込み後に再実測。R4 是正後は 2089 passed）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`: exit 0（`version-not-consumed: OK (shipping v0.41.3; integration target consumed v0.41.2)`）
- `tests/checks/skill-body-budget.sh`: exit 0（`gdd-pr-review-followup/SKILL.md` への参照 1 行追加後も維持）
- `scripts/measure-budgets.sh`: `references/*.md` は 11922 行上限に対し 11899 行（headroom 23）。express / standard の runtime token profile は不変（30068 / 45249）
- `scripts/gdd-codebase-health.py --mode changed --base-ref origin/main --fail-on high`: high 0 / medium 7 / exit 0。`tests/test_pre_push_gate_contract.py` の large_file / python_function_count は origin/main 時点（1883 行）から続く medium で、step 13b の test は新規 module へ切り出して増分を +50 行に抑えた（1933 行）。`tests/test_pre_pr_gate_contract.py` の python_function_count（71 > warn 40）は独立レビュー R2 旧#5 の fixture 追加で、`hooks/scripts/validate-steering-write.py` の python_function_count（49 > warn 40）は R4 旧#1 の `normalize_task_size()` 追加で warn 側へ入った。いずれも warn であり、分割 task で解消する
- 独立レビュー R2 旧#1 の再現: `state.md` + `State.MD` の二重指定で 30,000B Write を `validate-steering-write.py` に流し、修正後は `rc=2`（`state.md would become 30000 bytes, exceeding the 20000 byte limit`）を実測

### [0.41.2] - 2026-09-06

#### Summary

`validate-steering-write.py` が lone surrogate（JSON の `\udXXX` 単独）を含む入力や内部例外で exit 1 終了し、hook が PreToolUse の**非 block**（既存 deny category（email / secret 等）が 1 件も走らない fail-open）になっていた欠陥を修正。閉じたのは **content 経路・path 経路の lone surrogate、および `main()` の内部例外全般**の 3 つ。content 経路の size 判定は「算出不能に落とす」のではなく `encode("utf-8", "surrogatepass")` で**算出を継続**し（surrogate は 3 バイトとして数える）、末尾に 1 文字足すだけで AC-5 の size deny を無効化できた fail-open も塞ぐ。path 経路と `main()` の内部例外は fail-closed（deny / exit 2）。**独立レビュー Round 3 を受けて、fail-closed の正本を Python 側 guard から shell wrapper（`run-steering-write-hook.sh`）の rc guard へ移した**（module import 段階の例外は `main()` の guard では捕まらないため）。実測: content 側 surrogate `contact: <非 example email> \ud800` / 超過 content + 末尾 surrogate / path 側 surrogate（`file_path` の directory segment・2 つ目の target key `path`・ApplyPatch の `*** Update File:` header）がいずれも rc=1（traceback）→ 修正後 rc=2（それぞれ本来の email deny / size deny）。

#### Fixed

- `hooks/scripts/lib/steering_size.py`（独立レビュー R2 旧#1）: `_compute_post_write_size` / `_edit_delta` / `_oversize_warning` の `encode("utf-8")` を `errors="surrogatepass"` にし、lone surrogate を含む content でも size 算出を継続して deny を維持する。`_evaluate_size_decision` の `except ValueError` は当初「想定外入力の最後の網」として残したが、到達不能であることが判明したため削除した〔訂正: 下の独立レビュー R3 旧#5 参照〕
- `hooks/scripts/validate-steering-write.py`（独立レビュー H-2）: `main()` の未捕捉例外を deny（exit 2）へ倒す top-level guard を追加。deny 本文は固定文 + 例外の**型名のみ**（メッセージ・traceback・path・content は出さない）。無効化は既存 kill switch `~/.claude/gdd-hooks-disabled`（wrapper が Python 起動前に判定）で行い、新 env は追加しない
- `hooks/scripts/validate-steering-write.py`（独立レビュー H-1）: `_state_key` の `encode("utf-8")` を `errors="surrogatepass"` にし、path 由来文字列を OS へ渡す `read_text` 7 箇所の `except OSError` を `except (OSError, ValueError)` へ拡張。path 側 surrogate でも既存 deny が最後まで走る
- `hooks/scripts/lib/steering_size.py`（独立レビュー M-1）: `_oversize_warning` は on-disk サイズ（`existing`）由来の W-27 肥大 advisory を必ず維持する（別名 key に surrogate を 1 文字入れて advisory を黙らせられる穴を塞ぐ）。当初は chunk 単位の `except UnicodeEncodeError` で実現したが、`surrogatepass` の encode は任意の str で成功するため到達不能と判明し削除した〔訂正: 下の独立レビュー R3 旧#5 参照〕
- `hooks/scripts/validate-steering-write.py`（独立レビュー R2 旧#2）: `parse_self_review_line` の tempfile を `errors="surrogatepass"` で開き、`tmp_path` を write の前に確保して `finally` で必ず削除。`except` に `ValueError` を足し、証跡行の surrogate が guard の固定文 deny に化けないようにする
- `hooks/scripts/validate-steering-write.py`（独立レビュー R2 旧#5）: 非 str の `transcript_path` を「未指定」扱いにする `_payload_is_peer_turn` を切り出す（型ゆらぎ 1 つで全 `.steering` write が恒久 deny になり、自動 escape hatch が無い経路を塞ぐ）
- `hooks/scripts/validate-steering-write.py`（独立レビュー L-1）: `run_advisory_lints` の `Path(path).resolve()` を `_steering_size_target` と同じ `except (OSError, ValueError, RuntimeError)` で保護し、失敗した target のみ skip する
- `hooks/scripts/run-steering-write-hook.sh`（独立レビュー R3 旧#1）: **fail-closed の正本を wrapper 側に置いた**。`exec python3 …` をやめ、python の rc を受けて **0 / 2 以外（1 = 未捕捉例外・import 失敗、124 = timeout、126 / 127 = 起動失敗）を固定文 deny + exit 2 に倒す**。Python 側の top-level guard は `main()` の中でしか効かず、module import 段階の例外（`lib/steering_size.py` の欠落・部分更新・`sys.modules["lib"]` 衝突）は exit 1 = PreToolUse の**非 block**のまま既存 deny が 1 件も走らなかった。実測: `lib/steering_size.py` を退避して email 入り payload を流すと修正前 **rc=1**（traceback）→ 修正後 **rc=2**（固定文・traceback なし）。python の stderr は一旦退避し、固定文 deny に差し替えるときは捨てる（traceback に path / content の生値が載りうるため）。kill switch（`gdd_kill_switch_active`）は従来どおり Python 起動前に判定し、Python 不在時の既存 exit 2 経路と本文だけ分けて統合。Python 側の top-level guard は二重防御として残す
- `hooks/scripts/validate-steering-write.py`（独立レビュー R3 旧#2）: `_payload_is_peer_turn` の `last_user_turn_is_peer(Path(raw))` を `try/except (OSError, ValueError)` で包み、例外時は **`is_peer_turn = True`（fail-closed: peer turn 扱いで state core field の write を deny 側に倒す）**。`transcript_path` の**値**に lone surrogate / NUL が入ると filename の encode が `UnicodeEncodeError`（= `ValueError`）を投げ、`lib/transcript.py` の `except OSError` では拾えず guard 固定文 deny に落ちて同一 session の全 `.steering` write が自動回復なしで恒久 deny になっていた（R2 旧#5 は型軸だけを塞いでいた）。`lib/transcript.py` は触っていない（他 hook と共有のため。R2 旧#1 の「`read_text` 7 箇所」は **`validate-steering-write.py` 内の 7 箇所**を指す）
- `hooks/scripts/lib/steering_size.py`（独立レビュー R3 旧#3）: `_compute_post_write_size` の `Write` 分岐が `("content", "contents")` という別リテラルを持っており、受理集合の正本宣言（`NEW_STRING_KEYS`、ADR-4）と食い違っていた。`_first_str(tool_input, NEW_STRING_KEYS)` に統一し、`newText` / `new_string` / `replacement` で書いた超過 `Write` も size deny が成立する。**同 finding のうち target key 2 個のケースと `edits` の非 dict 要素は本 PR の対象外**（複数 target の全件判定は review-detection branch で扱う）
- `hooks/scripts/validate-steering-write.py`（独立レビュー R3 旧#4）: `load_deny_count` の例外集合を広げ、counter state file が「妥当な JSON だが非 dict」「`count` / `ts` が非数値」「不正バイト」のいずれでも counter 0 扱い（既存の JSON 不正時と同じ）にする。従来は `AttributeError` / `TypeError` / `UnicodeDecodeError` が top-level guard に届き、TTL は読めた後にしか効かないため当該 (path, category) が kill switch 以外で解けない恒久 deny で固まっていた（guard 追加前は静かな fail-open だった挙動が反転していた）
- `hooks/scripts/lib/steering_size.py`（独立レビュー R3 旧#5）: 到達不能な `except` を 2 箇所削除した（`_oversize_warning` の `UnicodeEncodeError`、`_evaluate_size_decision` の `ValueError`）。`str.encode("utf-8", "surrogatepass")` は任意の Python str で成功し、surrogate / NUL 入り path は `_steering_size_target` が先に None にするため、どちらの分岐もテストで通せない（通していない防御が循環的複雑度だけ増やす）。到達不能である旨をコメントで残した
- `hooks/scripts/validate-steering-write.py`（独立レビュー R3 旧#6）: `SELF_REVIEW_PARSE_TIMEOUT` を **10 → 5 秒**。hook 全体の timeout（`hooks/hooks.json` の 10 秒）と同値だと内部 timeout が先に効かず、parser が遅れたときに harness が hook ごと kill して `self_review_evidence` だけでなく同一 payload の email / secret deny まで消える
- `hooks/scripts/validate-steering-write.py`（独立レビュー R3 旧#7）: `run_advisory_lints` の呼び出しを `try/except Exception` で包み、例外時は warnings 空にする。advisory 層の例外が top-level guard 経由で deny に昇格すると「advisory は deny に昇格しない（修正路径を奪わないため）」という明文の設計と矛盾する（例: `.steering` 祖先が EACCES で `p.is_file()` が `PermissionError`）
- `hooks/scripts/lib/steering_size.py`（独立レビュー R4 旧#1）: R3 旧#3 の是正で `Write` 分岐が `_first_str`（**最初に一致した別名だけ**）になり、`content` に実サイズを載せた write へ `"new_string": "y"` のような decoy 別名を同居させると算出が小さい方へ倒れて上限超過 write が非 deny で素通っていた（`origin/main` は `("content","contents")` を直接見ていたので本 PR が新たに開けた穴）。`_first_str` を `_str_byte_sizes`（str 値を持つ**全** key の UTF-8 バイト長）へ置き換え、`Write` は最大値を post-write size にする。`_edit_delta`（`Edit` / `MultiEdit`）も **new 側の最大 − old 側の最小 = 最大 delta** を採り、片側だけ decoy で縮められないようにする。実測: `{"content": "x"*30000, "new_string": "y"}` の `Write` が修正前 **rc=0** → 修正後 **rc=2**
- `hooks/scripts/run-steering-write-hook.sh`（独立レビュー R4 旧#2 / 旧#4）: `set -e` を外し（`set -uo pipefail` のみ）、rc 変換を自前で行う構造にした。`set -e` 下では stderr 中継（`cat`）や `rm` の失敗が **rc 2 を持ったまま別 rc で途中終了 = PreToolUse の非 block** になり、fail-closed の正本そのものが fail-open していた。中継は `|| true` を付けて失敗を無視し、deny 経路は必ず `exit 2` で終える。`mktemp` 失敗時（TMPDIR が書き込み不可等）は退避先を `/dev/null` に倒すのをやめ、**stderr をそのまま通して rc 変換だけ行う**（従来は rc 2 の deny 本文まで捨てて「理由なし block」になっていた。異常終了時に traceback が見える縮退は許容する）。さらに `trap 'rm -f "$ERR_FILE"' EXIT` を追加し、harness の 10 秒 timeout / Ctrl-C で kill されても path / content の生値を含みうる退避ファイルを TMPDIR に残さない
- `hooks/scripts/validate-steering-write.py`（独立レビュー R4 旧#3）: `SELF_REVIEW_PARSE_TIMEOUT` を **5 → 3 秒**。この値は **1 呼び出しあたり**で `SELF_REVIEW_FIELDS` は 2 本あるため、両方に触れた chunk では 5s × 2 = 10s と hook timeout（`hooks/hooks.json` の 10 秒）に到達し、R3 旧#6 で塞いだはずの「harness が hook ごと kill して email / secret deny まで消える」経路が 1 field のときしか閉じていなかった。**1 invocation の総和の根拠**: parser 3s × 2 本 + advisory lint（`_run_lint_script` の既定 2s。単一 target の write では `lint-approved-direction` か `lint-ac` のどちらか 1 本）= **8s < 10s**
- `tests/test_steering_write_wrapper_fail_closed.py`（新規 / 独立レビュー R3 旧#1、R4 旧#2 で追補）: `hooks/scripts` を写した壊せる plugin root を作り、`lib/steering_size.py` を消して wrapper 経由で email 入り payload を流す → **rc=2・固定文・`Traceback` / `ModuleNotFoundError` / email 非出力**。健全な root では本来の email deny（rc=2）と clean write の allow（rc=0）がそのまま通ること、kill switch が Python 起動前に効くことも同時に固定する。R4 旧#2 で **TMPDIR を書き込み不可にした縮退経路**（`mktemp` 失敗）でも rc=2 かつ本来の email deny 本文が出ることを追加で固定した。新規 hook script は追加していないため `test_hooks_wiring_new_events_contract.py::test_every_script_on_disk_is_wired` / `test_hooks_kill_switch.py::ALL_HOOKS` に影響はない
- `tests/test_steering_size_deny_contract.py`: case 45（content 側 surrogate + email → rc=2、traceback なし / 超過 + 末尾 surrogate → rc=2 / 上限内 + surrogate → rc=0）、case 45b / 45c / 45d（path 側 surrogate の 3 変種 → rc=2 かつ本来の email deny）、case 45e（別名 key への surrogate 混入でも on-disk 由来の `[artifact size]` advisory が残る）、case 45f（証跡行の surrogate でも guard 固定文でなく本来の `self_review_evidence` deny）、case 48（内部例外の fail-closed。固定文・型名のみ・traceback なし）、case 48b（非 str `transcript_path` は「未指定」扱いで allow）、case 48c / 48d（`transcript_path` の値に surrogate → guard 固定文ではなく peer 扱いの本来の判定。core field write は deny / 無関係な write は allow）、case 49（`Write` の別名 content key 4 種で超過 → rc=2）、case 49b / 49c（decoy 別名を同居させても `Write` / `Edit` / `MultiEdit` の算出が小さい方に倒れない）、case 50（counter state file の 3 破損形でも guard 固定文にならず本来の email deny が出る）、case 46（tasklist.md の deny 経路と縮小 Write の allow。reviewer recall 実験で impl / completion reviewer が指摘した契約テストの欠落）

#### Affected Files

- `hooks/scripts/run-steering-write-hook.sh` / `hooks/scripts/validate-steering-write.py` / `hooks/scripts/lib/steering_size.py`
- `tests/test_steering_size_deny_contract.py` / `tests/test_steering_write_wrapper_fail_closed.py`（新規）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md`（版数 0.41.2）

#### User Action Required

- なし

#### Validation / Eval Impact

- 発見経路: reviewer recall 実験（`gdd-security-reviewer` を headless で PR 旧#37 head に当てた際の finding。impl-gate Round 1〜2・completion reviewer・Copilot・独立レビュー 2 回はいずれも見逃していた）

### [0.41.1] - 2026-09-06

#### Summary

`[0.40.14]`（stop hook の健全性リファクタ）のマージ後に走った独立レビューが出した low 3 件に対応する。**production コードの挙動変更はない**（記述の是正とコメントの追随のみ）。

#### Affected Files

- `CHANGELOG.md`（`[0.40.14]` entry の 2 箇所を訂正し、各行に `〔訂正: [0.41.1] 参照〕` を付記）
- `hooks/scripts/lib/merge-gate-evidence.sh` / `tests/test_merge_gate_hook_evidence_parsing.py` / `tests/test_peer_turn_write_boundary_contract.py` / `tests/test_stop_hook_unit.py`（移設に伴うコメントの参照先を更新）
- `references/state-schema.json` / `tests/test_state_field_value_less_line_contract.py`（`Next Action=` 部分文字列 reader の参照先を `lib/handoff_summary.py:_is_terminal_tasklist` へ更新）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`、`docs/VERSIONING.md`（版数。統合先の消費済み版数を v0.40.15 → v0.41.0 へ是正）

#### Fixed

- **`[0.40.14]` の行数リテラルが実測と 1 行ずれていた**: `1595 → 1423 行` と記載していたが、`wc -l` と `gdd-codebase-health.py:count_lines` の両方で実測 **1422**（main 側の 1595 は両方式で一致）。同一 entry 内で片方の数値だけがずれると、後から「どの指標で数えたか」を復元できない
- **`[0.40.14]` の「移設した 4 関数が main 版と同一であることは機械照合済み」が字義どおりには成立しなかった**: 新規 lib 3 本の 16 関数を `origin/main` の hook と AST 比較すると、同名・同 AST の関数は **0 件**（すべて新規名の抽出・再構成）。実際に照合したのは「移設対象 4 関数の AST が `origin/main` と旧ブランチの分岐元とで一致すること」＝「旧ブランチの古いコードを持ち込んでいない」ことの担保であり、挙動等価の根拠は差分テストと「全体 pytest が `origin/main` と同一件数で通ること」であって AST 一致ではない。何を何と照合したかを（4 関数名・旧ブランチ ref・照合コマンドまで）明示する形へ書き換えた
- **移設に伴うコメントの陳腐化 7 箇所**: `MANUAL_MERGE_RE` / `PR_URL_RE` が `lib/post_merge_continuation.py` へ、`Next Action=` 部分文字列 reader が `lib/handoff_summary.py:_is_terminal_tasklist` へ移ったのに、6 ファイル 7 箇所のコメント・台帳が `gdd_stop_hook.py` を指したままだった。機能影響はないが、次に同経路を追う人の grep 導線が切れる。`references/state-schema.json` は「同型 reader の台帳」として機械可読形式で保持されている参照文書なので、台帳としての正確性も落ちる

#### User Action Required

不要。

#### Validation / Eval Impact

- **production コードの差分なし**（`git diff origin/main -- 'hooks/scripts/*.py' 'hooks/scripts/lib/*.py' 'scripts/*.py'` が 0 行。`.sh` の差分はコメント 1 行のみ、test 3 本は文字列定数以外の AST が完全一致）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q`: **2067 passed, 1 skipped, 12497 subtests passed** / exit 0（`origin/main` の baseline と同一件数。独立レビュアーが両側を隔離コピーで実測）
- `bash tests/validate-plugin.sh`: exit 0
- `gdd-codebase-health.py --mode changed --base-ref origin/main --fail-on high`: high=0 / exit 0

#### Notes

`[0.40.14]` は「CHANGELOG に実在しない変更を書いた」medium をマージ前に 1 件直したが、**同じクラスの誤りが 2 件残っていた**（行数リテラルと照合内容の記述）。実測値を書くときは、書いた後に実測と突き合わせる手順を挟むこと。


### [0.41.0] - 2026-09-06

#### Summary

merge gate が「他セッションが残した active marker」による session_id 不一致を block（`session-mismatch`）として扱っていた箇所を、他 gate（9 箇所 / 8 hook）と同じ「管轄外（marker 由来の起動をやめる = 降格）」へ揃えた。block reason の復旧手順（「セッションを開き直して再実行してください」）は原理的に実行不能だったため、この block 面を削除し、fail-closed を弱めない形で誤 block を解消した。

#### Changed

- `hooks/scripts/run-merge-gate-hook.sh`: `IS_ACTIVE_MARKER` を `IS_OWNED_ACTIVE_MARKER` へ改名し、意味を「marker が `active: true` と書いてある」から「自セッションが所有する active GDD run がある」へ揃えた。所有を確認できない marker（別セッション所有 / `session_id` 空・欠落）が `active: true` の repo でも、以後は gate 対象から「起動根拠を除去（降格）」する形にし、対応する `unowned-active-marker-demoted` suppression log を記録する
- `hooks/scripts/run-merge-gate-hook.sh`: PR URL 一致経路（旧 `:420`）の session continuity 検査を撤去した。この経路の管轄根拠は steering artifact（PR URL の記録）であり、以降の証跡検査（承認 sha 一致 / 再 fetch 鮮度 / bot review / independent review）はすべて session 非依存のため、session 検査を残す理由がなかった

#### Fixed

- merge gate の `session-mismatch` block の復旧手順（「セッションを開き直して再実行してください」）が原理的に実行不能だった欠陥を解消。再ログインしても `CLAUDE_CODE_SESSION_ID` は新しい値になり、残置 marker の `session_id` と一致することは無かった。実測では、9 日前の別セッションが残した `active: true` marker のせいで、現行セッションが自分で作成した PR の merge が block されていた

#### Breaking Contract Changes

- **(a) block 面の削除**: merge gate の reason code から `session-mismatch` を削除した（`_mg_action` のカタログ行を含む）。理由: この block は「他セッションが残した marker」だけでなく「`session_id` が空・欠落」（自セッションの marker 書き込み不全でも起きる）でも発火しており、いずれのケースも復旧手順が実行不能だった。他 gate（9 箇所 / 8 hook）はこの種の不一致を全て `exit 0`（管轄外）として扱っており、merge gate だけが block に倒す非対称の正当な理由は見つからなかった（`hooks/scripts/lib/detect-steering.sh` の `gdd_session_continuity_ok "..." || exit 0` という関数契約からも、block は契約からの逸脱だったと確認できる）
- **(b) fail-open を導入していない根拠**: 単純に `exit 0` へ倒すと、残置 marker 1 個で merge gate 全体（承認証跡・再 fetch 証跡・bot review・independent review の検査）が無効化される既知の fail-open を再導入する。今回の変更はそれを避けるため、marker 由来の起動根拠だけを外す「降格」を採用した。降格後の通過集合は `active: false` marker と同値（同一入力に対して同じ block 有無・reason code）であり、かつ marker 不在時（無条件 `exit 0`）の通過集合の真部分集合にとどまる。PR URL 一致経路（証跡検査そのもの）は session 検査を外しても検査項目は減らない——引き続き承認 sha 一致・鮮度・bot review・independent review を要求する。**縮小する保護面は 3 面**（うち (1)(2) が marker 由来、(3) は走査コスト由来）: (1) 他人の `active: true` marker がある repo で、その steering が対象 PR を記録していない merge——降格後は素通り、(2) done steering が複数あり対象 PR をどれも記録していない場合——降格後は `steering-ambiguous` block から素通り（`unresolved-steering-on-merge` ログ）へ変わる。(1)(2) はいずれも「対応する証跡が無く実行可能な復旧手順も持たない、他人／所有不明の marker だけを根拠にした強制」という同一クラス。(3) は性質が異なる: 降格したケースは marker 由来の即時 block が無くなる分だけ `.steering/` の全走査へ必ず進むため、**steering が約 295〜300 件以上ある repo では hook が 10 秒 timeout に達して無出力のまま素通りする**（実測: 0 件 0.40 秒 / 50 件 1.91 秒 / 300 件 9.70〜10.10 秒 / 400 件 timeout）。走査コスト自体は所有済み marker でも同じ（300 件 9.88 秒）で本変更が作ったものではないが、(3) =「所有を確認できない marker + steering 約 300 件以上 + 対象 PR を記録した steering あり + 証跡不足」の入力だけは、今日の `session-mismatch` block から timeout 素通りへ変わりうる。縮小するのはこの 3 面で、それ以外は縮小しない
- **Migration**: `active: false` marker + 別セッションでの merge も影響を受ける。PR URL 一致経路の session 検査撤去により、従来 `session-mismatch` で block していた「単一 steering・PR URL 一致・証跡不足」の入力は、`active` の値によらず `approval-missing` 等の actionable code で block されるようになった（block 自体は継続するが reason code が変わる）。また、承認証跡の provenance が session に紐づかなくなる: セッション X が記録した `Merge Approval` をセッション Y の `gh pr merge` が消費しうる。窓は「承認・再 fetch 直後で HEAD が動いていない間」（承認 120 分鮮度 / 再 fetch 10 分鮮度 / head sha 一致 / PR 番号一致で縛られる）に限られ、`active: false` marker では従来から同じ前提だったため許容する。なお同一 head sha を持つ PR が複数ある場合、sha 一致だけでは対象を識別できない。`gh pr merge <番号>` や PR URL のように対象を明示した実行では、`Merge Approval` が承認宛 PR 番号と実行対象 PR 番号の二重一致を要求するため別 PR の承認は流用されないが、引数省略の `gh pr merge` では実行対象が state.md の `PR URL` から導出されるため、この二重一致は単一一致に縮む
- **(c) 再導入条件**: 将来「session 越境の merge」を再度 block したくなった場合は、同名の reason code をそのまま復活させない。復活させる block は、削除前の `session-mismatch` が欠いていた「実行可能な復旧手順」を持つことを条件にする（例: marker の所有者を特定して削除を案内する、または marker に TTL を持たせて自動失効させる等）

#### Known Limitations

- `commands/gdd-dev.md` の setup フォールバック手順は `session_id:` を空のまま state を作る形を案内しており、降格の恒常的な発生源になっている。本 PR では非スコープ（follow-up 候補）
- `merge-gate-suppressed.log` は rotation を持たない append-only ログで、降格が起きる repo では `gh pr merge` 1 回につき最大 2 行増える。頻度が低いため許容する
- `.steering/` の done 候補が約 295〜300 件を超える repo では、降格ケースが hook の 10 秒 timeout に達して無出力のまま素通りしうる（§ Breaking Contract Changes (b) の保護面 (3)）。走査コストは所有済み marker でも同じで本変更が作ったものではないが、降格ケースが新たにこの経路へ入る。現実の repo で 300 件超は観測していないため許容し、是正（走査の早期打ち切り / timeout 値見直し）は follow-up

#### Affected Files

- `hooks/scripts/run-merge-gate-hook.sh`
- `tests/test_merge_gate_hook_gate_activation.py`
- `tests/test_merge_gate_hook_block_reason_quality.py`
- `tests/test_hook_block_reason_recovery_contract.py`
- `tests/_merge_gate_support.py`
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json`（v0.41.0 へ bump。bump 起点は分岐点ではなく統合先の消費済み版数で、その実値は `docs/VERSIONING.md` § 現状 が正本）
- `docs/VERSIONING.md`
- `docs/adr/2026-09-06-merge-gate-session-jurisdiction.md`（repo-root。新規 / 蒸留した判断）
- `docs/learned-patterns.md`（repo-root）

#### User Action Required

- 対応不要。他人の残置 marker で誤 block されていた正当な merge は今後 block されなくなる。対象 PR を記録した steering が承認証跡を欠く場合は、引き続き `approval-missing` 等で block される

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto` → `2064 passed, 1 skipped, 12477 subtests passed in 100.50s`（origin/main v0.40.13 / `4d97d0a` を merge した HEAD で実測）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh` → exit 0（`version-not-consumed: OK (shipping v0.41.0; integration target consumed v0.40.13)`）
- `gdd-codebase-health.py --mode changed --base-ref origin/main --fail-on high` → high 0
