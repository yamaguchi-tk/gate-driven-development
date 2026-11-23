# Changelog Archive

`gate-driven-development` の変更履歴のうち、`### [0.37.4]` 〜 `[0.16.0]` をここへ移した。
記載ルール・Entry Template・Versioning Notes の正本は [`CHANGELOG.md`](CHANGELOG.md)。
本文は移動時に変更していない。

### [0.37.4] - 2026-09-02

#### Summary

往復（remediation loop）発生時の model routing を Fable + effort=high に昇格する `remediation_loop` tier を追加。

#### Changed

- `references/fixed-models.md`（正本）: 同一 `Current Task` で `changes_requested` が累計 2 回目（`tasklist.md` の `Gate Rounds` ≥ 2。route 非依存で `Fix Attempts` では判定せず、`human_recheck_required` の reset を跨いでも維持）になった時点から、(1) route 判断（systematic-debugging subagent）、(2) 再レビュー（impl-gating の gate subagent 自体と escalation 先 reviewer を `Agent(model="fable")` で起動）、(3) remediation 実装（worker subagent の dispatch 必須、inline 修正不可）を `remediation_loop` tier で起動。`gdd-completion-check` は対象外。実適用 model は `worklog.md` に記録
- `tasklist.md` の `Current Task` に `Gate Rounds: N` を新設（`gdd-implementation-gating` が `changes_requested` のたびに +1、task `approved` で削除。`state-field-tiers.md` / `bounce-log-schema.md` に reset 対象外を明記）
- 往復回数による昇格を本 tier に一本化: `general_heavy_risk` の条件と Opus `xhigh` 限定使用の条件から「3 回以上の差し戻し」を除去（`fixed-models.md` / `gdd-model-routing`）
- 開始条件の数値は正本にだけ書き、`gdd-model-routing` / `subagent-dispatch.md` / `gdd-implementation-gating` / `gdd-systematic-debugging` / `gdd-subagent-driven-implementation` / `commands/gdd-dev.md` / `cursor.md` / `codex.md` は tier 名 + pointer
- `scripts/resolve-gdd-model.py` / `scripts/run-gdd-worker.py`: `--complexity remediation_loop` で tier を明示指定できるようにし、Cursor（`opus-5` + high）/ Codex（`gpt-5.6-sol` + high）の worker runner 経路を追加
- 実測根拠: PR-W8 T-2 は Opus 5 で 6 回往復しても収束しなかった（ユーザー判断 2026-09-02）

#### Validation / Eval Impact

- 新規 `tests/test_remediation_loop_model_routing_contract.py`: 正本の tier 定義、`Gate Rounds` 判定、gate subagent 自体の Fable 起動と worker dispatch 必須、`general_heavy_risk` に旧ルールが残らないこと、非正本に数値が再掲されないこと、全 host の tier 表と resolver の切替
- `tests/test_model_routing_contract.py`: 全 host tier リストと resolver の `remediation_loop` 解決を追加

### [0.37.3] - 2026-09-02

#### Summary

W-27: implementation-gating への精度二層化の適用と steering artifact 肥大の抑制（PR-W8 dogfooding 実測に基づく）。

#### Changed

- Remediation Loop Safety（`references/state-machine.md` 正本）: hard cap で人間に戻した後の `Fix Attempts` は既存どおり reset するが、**reset 後の上限を 5/5 → 2/2** に下げる（承認後の再ループ上限）。2/2 到達で**方式転換**（task 撤回・再設計・スコープ縮小）の選択肢を人間へ一括提示。同一箇所に 3 回連続 finding（impl-gating が `file:function` を Error Log に記録して判定）は「方式そのものの問題」として同様に扱う
- implementation-gating: 再入時は前回 `changes_requested` 以降の差分と影響範囲だけをレビュー（差分スコープ）。`requirements.md` § Honest Limitations に**承認時点で既載**の限界（build 中の追記・design.md 側は対象外。新たな攻撃面の発見は含めない）に該当する finding は blocking にしない。reviewer agent 2 本にも同契約を明記
- steering artifact: state.md の Tier 1 routing field は現在値のみ（旧値を残さない。累積追記 field は既存定義どおり）。全 artifact の行数目安（requirements 300 / design 500 / tasklist 600 / adr 300 / state 100）を `requirements-template.md` に集約
- hook `validate-steering-write.py`: state.md 20KB / tasklist.md 80KB / design.md 60KB 超過を advisory で警告（deny しない）
- task-breakdown: task 総数は原則 8 task 以内。超える場合は Stage 分割を提案

#### Validation / Eval Impact

- 新規 `tests/test_impl_gate_precision_tiering_contract.py`（契約 + hook 実挙動）
- 実測根拠: PR-W8 で planning は 27 分・1 ラウンドで収束した一方、T-2 が 10 時間・impl-gate 6 回・Attempt 7・F-1〜F-12 で発散。steering 合計 457KB

### [0.37.2] - 2026-09-01

#### Summary

`validate-steering-write.py` の secret 検出強化。2026-09-01 の実測で
`- token: ghp_...` のような既知接頭辞の token 実値行が `find_secret_marker` /
`find_sensitive_value` のどちらにも拾われず allow されることを確認したため、
`SECRET_MARKER_RE` に既知接頭辞パターンを補強し、あわせて `secret_marker` を
escape hatch の降格対象から外した。

**検出範囲**（接頭辞 allowlist であり網羅ではない）:

- GitHub token: `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_`、`github_pat_`（fine-grained）
- Slack token: `xox[abcdeprs]-`（bot / user / ブラウザセッション等）、`xapp-`（app-level / Socket Mode）
- AWS access key ID: 既存の `AKIA` に一時キー `ASIA` を追加

**前方境界に `\b` を使わない**。Python の `\b` は日本語文字を単語構成文字として
扱うため、分かち書きしない日本語（steering の既定言語）で最も自然な
`トークンはghp_...` を取りこぼす。明示の lookbehind `(?<![A-Za-z0-9])` にした。

**最小長は区切り文字を含まない連続長で見る**。`xoxb-your-token-here` /
`github_pat_YOUR_TOKEN_HERE` のような説明用プレースホルダーは連続長が下限に
届かず誤検知しない。誤検知の実害は下の Changed（非降格化）と噛み合うため、
3 枝それぞれで固定している。

#### Fixed

- `hooks/scripts/validate-steering-write.py`: `SECRET_MARKER_RE` に GitHub / Slack / AWS 一時キーの既知接頭辞検出を追加

#### Changed

- `hooks/scripts/validate-steering-write.py`: `secret_marker` を `NON_DEMOTABLE_CATEGORIES` に追加。3 回連続 deny の escape hatch で warning 付き allow に降格しなくなる。実 token を握っているのは AI 自身なので、表記だけ変えた再試行では値が残ったまま 3 回目に allow へ到達し、平文の credential が git 履歴へ着地する（実測で確認）。値を `<redacted>` に置換すれば必ず解消するため、降格させる必要がない
- `docs/SECURITY.md`: hook の検出範囲を実装に追随。あわせて「接頭辞 allowlist であり網羅ではない」ことと、escape hatch の非降格 category を明記

#### User Action Required

- `.steering/` への token 実値書き込みが新たに deny される。redact 済み表記 `<redacted>` と接頭辞だけの言及（`ghp_ で始まる`）は従来どおり通る
- `secret_marker` の deny は 3 回連続でも allow に降格しなくなった。該当箇所は値を `<redacted>` に置換して解消すること（別表記での再試行では解消しない）

#### Validation / Eval Impact

- `tests/test_distribution_readiness_contract.py` に deny 期待 15 ケース + 誤検知防止 11 ケース + コードブロック / `#### Attempts` 節での発火 2 ケース + 非降格の回帰 1 件を追加
- 非降格テストは 4 回連続書き込みの returncode 全てを観測する（3 回目に降格した直後 counter が clear されるため、終状態だけでは vacuous になる）
- Superpowers Benchmark Summary: not_applicable (no changed GDD primitive)

### [0.37.1] - 2026-09-01

#### Summary

精度二層化（v0.37.0）マージ後の origin/main 実測に合わせて budget 上限を一方向 ratchet down。

#### Changed

- `tests/checks/skill-body-budget.sh` の上限を実測値へ更新:
  references 行数 12,427 → 11,922 / express runtime tokens 33,558 → 30,083 /
  standard runtime tokens 57,189 → 45,381 / total skill body 7,162 → 6,982 /
  standard template lines 815 → 411 / express template lines 188 → 187
  （per-skill 上限 570 は今回の実測対象外のため据え置き）
- 分岐時点ではなく統合先 tip（merge commit 1b7292e）で実測してから下げる運用に従う

#### User Action Required

- 全 6 値が **headroom 0**（上限 = 実測）になった。references/*.md や runtime profile
  対象ファイルに 1 行でも追記すると check が RED になるため、追記する PR では先に
  等価な親テキストを削減・統合すること（一方向 ratchet の契約どおり）

### [0.37.0] - 2026-09-01

#### Summary

精度二層化: 「テストと人間承認点だけ高精度」を planning の第一原則として全面再設計。
実測根拠は PR-W7（planning 11 ラウンド・約 22 時間・実装差分ゼロで凍結。requirements.md
554KB、AC は R7 以降不変のまま 5 ラウンド続行）。出荷物の品質はテストと
implementation-gating が担保し、planning 文書で高精度が要るのは人間の承認判断に使う箇所と
AC の意味だけ、という原則へ寄せた。

#### Changed

- `references/requirements-template.md` を全面再設計（703 → 約 300 行）。standard の
  requirements.md は常設 11 節 + 条件付き節（`Post-PR Completion Scope` /
  `Sensitive Data / Masking Policy` / `Route / Ownership Matrix` /
  `Implementation Sequence Plan` / `Planned Follow-up Stage Lane`）
- **人間が承認した重要判断は AC として書く**。`Critical Trace` をはじめとする trace 群
  6 節を廃止し、AC → テストの経路で承認内容を実装まで運ぶ
- 調査系 9 節（`Existing Implementation Survey` / `Engineering Baseline Survey` /
  `Architecture Recommendation Gate` / `Architecture Option Matrix` /
  `Technology Stack Fit Matrix` 等）を廃止。調査自体は行うが、記録は `findings.md` に残し、
  requirements.md には承認判断に効く結論だけを書く
- レビュー儀式 4 節（`Adversarial Requirements Review` / `Plan Direction LLM Review` /
  `Plan Revision Ledger` / `Workflow Fit Check`）と宣言系 8 節（`fail-closed 方針` /
  `Behavior Change Summary` / `Latest Tech Context` 等）を廃止。ワークフロー適合判定・
  敵対的レビュー（dialectic）は名前を変えて機能として残る
- `Summary Brief` は 3 層構造 + Honest Limitations（「ズレ確認」層は trace 群とともに廃止）
- **レビューループの新契約**（`references/requirements-gating-steps.md` § レビューループの契約）:
  - 再入は 1 回まで。Review Round は `reviews.md` で数え、**記録がなければ上限超過扱い**
    （fail-closed）。上限到達で残る blocking を一覧で人間へ一括提示
  - blocking にできる指摘は「AC の意味・スコープ・承認ポイント・安全境界」に影響する
    ものだけ。それ以外は advisory
  - 再入レビューは amendment の差分と影響節のみ。通過済み未変更節への新規指摘は advisory
  - レビュー記録・処置結果は `reviews.md`（追記専用）へ分離し、requirements.md に積まない。
    gate が読むのは最新ラウンド分だけ
  - requirements.md（standard）は 300 行以内を目安に実測して削る
- `gdd-task-breakdown` の Deferred Trace precheck を撤去（v0.36.0 の O-2 は trace 群廃止に
  伴い役目を終えた）。task の `Covers Critical Trace:` フィールドを廃止し AC カバレッジに一本化
- `gdd-planning-reviewer` に blocking 接地条件と差分スコープレビューを明記

#### Validation / Eval Impact

- 新規: `tests/test_precision_tiering_contract.py`（節構成・廃止節の全文書走査・
  ループ新契約・fail-closed カウンタ）
- 改廃: `test_critical_trace_contract.py` / `test_hitl_trace_contract.py` を削除、
  `test_requirements_tiering_contract.py` は measure-budgets 契約のみ残存、
  `test_requirements_gating_parallel_review_contract.py` /
  `test_engineering_baseline_architecture_contract.py` /
  `test_hitl_lint_marker_sync_contract.py` /
  `test_superpowers_differentiation_contract.py` /
  `test_continuation_registry_contract.py` を新契約・新語彙へ更新
  （Architecture Drift の severity / handling は refactor-planning に一本化、
  HITL 必須ルールは 26 → 24）
- budget 実測（v0.37.0 時点）: references 11,909/12,427 行（+518）、express 30,022/33,558
  tokens（+3,536）、standard 45,203/57,189 tokens（+11,986）。**v0.29.0 以来 pre-existing
  RED だった runtime budget が両プロファイルとも GREEN 化**
- `scripts/grade_evals.py` / `evals/evals.json` は過去セッション replay の採点系のため
  変更していない（歴史データと対の rubric）

#### User Action Required

- 進行中の steering がある場合、旧テンプレートの trace 群は再生成不要（読み手側の gate が
  新契約で動く）。新規タスクから新テンプレートが適用される

### [0.36.0] - 2026-08-31

#### Summary

planning 51 分問題（実測 2026-08-31 / PR-W7）への続編。v0.35.0（reviewer 並行化）に
続き、執筆 19 分の主因である「HITL に表示されない trace 群の HITL 前執筆」を止める。

**O-2: planning 成果物の二層化。** HITL 前に書くのは承認判断に使われるものだけにし、
以下は記入時期を「task-breakdown 入場まで」へ遅延する。埋め残しは
`gdd-task-breakdown` の Phase Gate Pre-check が fail-closed に回収する。

| セクション | HITL 前 | 全量確定 |
|---|---|---|
| `Completion Testability Matrix` | 例外行のみ（needs-clarification / e2e-required / external-evidence-required / non-testable-deferred / 解釈差大） | task-breakdown 入場まで |
| `Critical Trace` | 書かない（承認された判断の記録なので承認前に予測で書かない） | human check 承認直後〜task-breakdown 入場 |
| `Baseline Compliance Check Plan` | 見出しのみ | task-breakdown 入場まで |
| `Verification Sanity Check` | 見出しのみ | task-breakdown 入場まで |

HITL 表示は変わらない: `テスト化確認` に出るのは元々例外行だけ
（`human-check-template.md` 555 行）で、Critical Trace / Baseline Compliance /
Sanity Check は compact 版 HITL に表示されていない。

**O-3: budget 実測の 1 コマンド化。** 新規 `scripts/measure-budgets.sh` が
references 行数 / express・standard runtime tokens の実測と上限・残枠を 1 回で出す。
上限値は `tests/checks/skill-body-budget.sh` の実行引数から読み取り、二重正本を
作らない（判定は従来どおり check 側が担う）。planning 中の同型 Bash 実測
（PR-W7 実測で 49 本）を置き換える。

#### Changed

- `references/requirements-template.md`: Testability Matrix の HITL 前ルールを例外行限定へ変更、遅延 3 セクションに記入時期を明記（**703 行で行数中立**）
- `skills/gdd-task-breakdown/SKILL.md`: Phase Gate Pre-check に Deferred Trace 回収を追加（+2 行）

#### Added

- `scripts/measure-budgets.sh`（budget 対象外の scripts/ 配下）
- `tests/test_requirements_tiering_contract.py`（6 tests）

#### Validation / Eval Impact

- pytest: 1392 passed / 1 skipped
- references 行数: 12,427（上限ちょうど、変化なし）
- runtime tokens: express ±0 / standard は main 比 **+110**（57,254→57,364。記入時期注記の正味コスト）。この指示への投資は実行時の requirements.md 生成を数千トークン規模で削る。上限超過は PR 旧#12 以来の pre-existing RED で、是正は PR-W7 の S-0a
- `version-not-consumed`: v0.36.0 / 消費済み記録 v0.35.0


### [0.35.0] - 2026-08-31

#### Summary

requirements-gating の planning が HITL 提示まで長すぎる問題への即効修正。
実測（2026-08-31 / PR-W7 planning、session ad23dbd7 の subagent transcript）では、
依頼から `human-check-waiting` 到達まで **51 分**かかり、内訳は執筆 19 分 /
**reviewer 直列待ち 9.9 分（メインは完全アイドル）** / **指摘反映 10 分（HITL と直列）**
だった。reviewer 待ちと反映の直列化が体感時間の約 4 割を占める。

gate の順序契約を次のとおり変更する。

1. **reviewer はバックグラウンドで起動**し、完了をアイドルで待たない。待ち時間に
   Adversarial Requirements Review / Plan Direction LLM Review / HITL draft の
   組み立てを先に進める
2. **HITL 提示前に解消必須なのは high と「承認ポイント・AC semantics・scope に
   影響する指摘」だけ**。それ以外の medium（文言・補完・N/A 根拠追記等）は
   HITL 提示後の承認待ち時間中に反映してよい。条件は反映が承認ポイントを
   変えないこと。変える場合は Planning Interrupt Decision Menu の 1（HITL 再生成）で扱う

品質面の担保: Adversarial Requirements Review / Plan Direction LLM Review は
引き続き HITL **前**に確定する（誤承認防止の目的を変えない）。変わるのは
「reviewer 待ちの間それらを先に進めてよい」ことと、「承認内容に影響しない
文書修正を人間の判断待ち時間へ逃がしてよい」ことだけ。

#### Changed

- **`references/requirements-gating-steps.md`** Step 5 / Step 9: 上記 1・2 の順序契約。
  行数は折り返し bullet の結合で相殺し **references 合計 12,427 行（上限ちょうど）を維持**
- **`skills/gdd-requirements-gating/SKILL.md`** Step 4 / Step 5: 概要を同期

#### Validation / Eval Impact

- 新規 `tests/test_requirements_gating_parallel_review_contract.py`（5 tests）:
  バックグラウンド起動・待ち時間の並行作業・非 blocking medium の HITL 後反映・
  SKILL / steps の語彙同期を固定
- `python3 -m pytest plugins/gate-driven-development/tests/`: 1376 passed / 1 skipped
- runtime profile tokens は main 比 **+18**（express 33,590→33,608 / standard
  57,236→57,254）。新しい挙動指示の正味コストで、既存文の重複削減では相殺し切れ
  なかった分。上限（33,558 / 57,189）超過は PR 旧#12 以来の pre-existing RED で、
  是正は PR-W7 の S-0a（上限付け替え）で行う

### [0.34.2] - 2026-08-31

#### Summary

v0.34.1 は canonical field 行の読み取り規約を「行頭 + markdown bullet marker 1 個まで」に
統一したが、**field 名の終端**（名前の直後が区切り文字であること）は
`scripts/setup-gdd-loop.sh` の `parse_field` だけ揃っていなかった。同関数は
`stripped.lower().startswith(name.lower())` で照合したあと、区切り文字を
**行のどこにでもある `=` / `:`** から探していたため、`Task` が `Task Size: standard` に
前方一致して値 `standard` を返していた。

worktree pollution 判定は `state_task_id != task_name` を `state_task_mismatch` と
するため、`Task ID` を明示していない state.md がすべて誤検知される。実害として
`setup-gdd-loop.sh` が

    ⚠ Worktree pollution detected. Auto-resume is disabled until the canonical workspace is selected

を出して auto-resume を無効化し、GDD loop が張れなくなった（2026-08-31 実測）。

他 4 実装（`gdd_extract_doc_field` / `validate-steering-write.py` の
`state_field_pattern` / `gdd_task_binding.py` の `_field` / `collect-gdd-telemetry.py` の
`extract_field`）はいずれも `name + sep` を要求しており、規約から外れていたのは
この 1 実装だけだった。追加した契約テストの RED が `LoopParseFieldAnchoringTests` の
4 subtest のみだったことでこれを機械的に確認している。

#### Fixed

- **`scripts/setup-gdd-loop.sh` `parse_field`**: field 名の直後が `=` / `:` である
  ことを要求する。既存受理形 `Next Action : done`（区切り前の空白）は `lstrip()` で
  維持する。区切り文字の探索を行全体から「field 名の直後」へ限定したため、
  値の中に `:` を含む行を先に割ってしまう経路も同時に閉じる

#### Validation / Eval Impact

- `tests/test_canonical_field_line_anchoring_contract.py` に
  `FIELD_NAME_PREFIX_FORMS` / `FIELD_NAME_EXACT_FORMS` の 2 表と、5 実装ぶんの
  `test_prefix_of_longer_field_is_not_read` / `test_exact_field_is_still_read` を追加。
  拒否と受理を対で固定し、過剰な拒否を防ぐ
- 実データ計測: ローカルの `.steering/*/state.md` 420 件で
  `state_task_mismatch` 判定が **111 件 → 75 件**。判定が変わった 36 件はすべて
  「誤検知 → 正常」で、逆方向（正常 → 誤検知）は **0 件**
- state.md / tasklist.md 999 件 × 5 field = 4,995 回の判定のうち値が変わったのは
  97 回で、すべて `Task ID` 系の誤検出解消。`Resume From` / `Next Action` /
  `Active Branch` / `Status` の値が変わった判定は **0 件**（terminal 判定は不変）
- 97 回のうち 1 件は `- Task Slug: <id>` という別書式を `Task` として拾っていた
  ケースで、修正後は空になるが `or task_name` の fallback が同値を返すため
  判定は変わらない
- `python3 -m pytest plugins/gate-driven-development/tests/`: 1381 passed / 1 skipped


### [0.34.1] - 2026-08-31

#### Summary

canonical field 行の読み取り規約を「**行頭 + markdown bullet marker 1 個まで**」に
統一した。旧実装は先頭の `[[:space:]-]*` を**個数無制限で**除去してから field 名を
照合していたため、入れ子 bullet で書かれた履歴メモが canonical field と区別できなかった。
実害として `gh pr create` が

    ⛔ Next Action=gdd-implementation-gating（T-10 impl-gate Attempt 旧#2 へ再入場）

で block された（`state.md` / `tasklist.md` 先頭とも `Next Action: done` なのに、
tasklist.md 本文 3203 行目の `  - `Next Action=gdd-implementation-gating`（…）` が
最初の一致として返っていた）。バッククォート除去が行全体に効くため、コード表記の
履歴まで一致していた。

同型の prefix 除去は読み手・書き手の 7 実装に散在していたため、片側だけ直すと
「読み手だけ厳格」（G-9）/「書き手だけ厳格」の非対称が残る。7 実装すべてを揃えた。

あわせて `git push origin <branch> 2>&1 | tail -15` が `refspec-ambiguous` で
block される誤検出を修正した。`_lex` は `2>&1` を `2` / `>&` / `1` の 3 token に割るため、
fd 番号と転送先が positional refspec として数えられていた。

#### Fixed

- **`hooks/scripts/lib/detect-steering.sh` `gdd_extract_doc_field`**: 接頭辞除去を
  `^[[:space:]-]*` から `^-[[:space:]]+`（bullet marker 1 個）へ変更。インデント行は
  `index() == 1` に到達しないため field として読まれない
- **`hooks/scripts/validate-steering-write.py` `state_field_pattern`**: 同じ規約へ。
  書き手だけが緩いと「書けたのに gate から見えない」非対称が残る
- **`scripts/gdd_task_binding.py` `_field`** / **`scripts/setup-gdd-loop.sh`
  `normalize_line`** / **`scripts/collect-gdd-telemetry.py` `extract_field`**: 同上
- **`hooks/scripts/run-pre-compact-hook.sh`**（`Status` / `CompactSource` / `PausedAt`）/
  **`hooks/scripts/run-session-start-hook.sh`**（`CompactSource` 削除）: sed の置換・削除
  対象も行頭 + bullet 1 個までに限定。入れ子の履歴メモ（`  - Status: pass`）まで
  `paused` へ書き換える破壊を止めた
- **`hooks/scripts/lib/push_command_parse.py` `classify_refspec`**: shell の
  リダイレクト token（`2>&1` / `> file` / `2> file` / `&> file` / `>>file`）を
  refspec として数えない。リダイレクトは push 対象 ref を変えないため

#### Added

- **`references/state-schema.json` § `canonical_line_form`**: 行形式の正本。
  `allowed_line_prefix` = `["", "- "]`、`indented_lines_are_not_fields` = true、
  履歴メモは入れ子 bullet で書くこと
- **`skills/gdd-completion-check/SKILL.md`**: `Next Action` を行頭に書く規範と、
  履歴メモを入れ子 bullet にする規約を明記

#### Breaking Contract Changes

- **インデントされた field 行は canonical field として読まれなくなる**。
  `  Next Action: ...` / `  - Next Action: ...` は履歴・例示扱いになる。
  実データ 944 件（state.md / tasklist.md）× 5 field = 4,720 回の判定で挙動が
  変わったのは 10 回のみで、すべて「入れ子の per-task `Status: pass` / `Task ID: T-9`」
  「コードブロック内の記入例」= 誤って拾っていたケース。canonical 値を失う file は 0 件

#### User Action Required

- 既存 steering の `state.md` / `tasklist.md` で canonical field をインデントして
  書いている場合は行頭へ移す。実データ計測では該当 0 件のため通常は不要
- 履歴・経緯で過去の `Next Action` に言及するメモは入れ子 bullet（先頭 2 スペース以上）
  で書く

#### Validation / Eval Impact

- 新規 `tests/test_canonical_field_line_anchoring_contract.py`（7 実装の受理形マトリクス +
  `references/state-schema.json` との doc↔実装 突合 + SKILL 規範文 guard）
- `tests/test_state_field_anchoring_contract.py` に `test_indented_lines_are_not_fields` を追加し、
  `  Next Action : ...` を present 側から reject 側へ移した（実データ 0 件を根拠に改訂）
- `tests/test_push_command_parse.py` にリダイレクト 7 形 + fail-open 側 1 形を追加
- 変異注入で検出力を実測: 旧 prefix 除去への復帰（読み手 / 書き手）、SKILL 規範文の
  弱体化、履歴規約の削除、schema の `allowed_line_prefix` へインデント形混入 の 5 形とも KILLED

### [0.34.0] - 2026-08-30


#### ⚠️ 移行注意（利用者向けの挙動変更）

1. **`Route In Progress` の done guard（Check 3）が本版で初めて有効になります。**
   従来の実装は等号形 `Route In Progress=x` の**行内部分一致**しか見ておらず、
   GDD が実際に書く正準形 `- Route In Progress: x`（**コロン**）を素通りしていました
   ＝ **実運用で一度も発火していません**。本版から行頭アンカー付きで両形を読むため、
   **`state.md` に `none` 以外の値を残したまま `done` していた利用者は本版から block されます**。
   解除は `Route In Progress: none` にするだけです。
   fence 内の例と、行頭形でも `Route In Progress` から始まらない散文は拾いません。
2. **bind 不能時の done guard が fail-open から縮小されました。**
   従来は bind 解決不能なら常に通していましたが、本版は「自 worktree の `.steering/` に
   containment 検査を通った候補が**ちょうど 1 つ**」なら検査します
   （**0 個または複数なら従来どおり warn して通す** —— 複数から「どれか」を選ぶのは推測なので行いません）。
3. **fallback で block した場合、block reason に `[gdd:bind-unresolved]` の断りが入ります。**
   「binding.json が無いので推定で対象を選んだ」ことが block 側にも見えるようになります。

#### Summary

GDD の欠陥・計測を是正した（改善計画 §2 の **W-9 / W-10-1 / W-10-3 / W-13**）。
柱は 3 つ。**(1)** Stop hook が別 worktree の steering を掴む誤 bind を、
`.gdd/tasks/<task_id>/binding.json` と worktree / branch の一致で解決する形へ変え、
containment を fail-closed で検証する。**(2)** bounce 計測と done guard が
`### Task <N>: <name>` 形式の見出しを丸ごと取りこぼしていた silent failure を、
**python 側 2 読み手**の受理面を 1 module に集約して塞ぐ（**bash hook 2 本は非スコープ** ——
下記「未確認事項」）。**(3)** API エラーでターンが落ちたとき、
`Stop` は発火しないため利用者が停止に気づけなかった問題に対し、
**`StopFailure` / `Notification` の 2 event を新設**し、次回 `SessionStart` で 1 度だけ報告する。

#### Added

- **`StopFailure` hook**（`hooks/scripts/run-stop-failure-hook.sh` + `lib/stop-failure-record.py`）。
  API エラーでターンが終了したとき、`~/.claude/.gdd-hook-state/last-turn-failure.json` へ記録し
  デスクトップ通知を出す。**block しない**（decision control を使わない）。
  記録に失敗しても通知は出す（通知と記録は独立）
- **`Notification` hook**（`hooks/scripts/run-notification-hook.sh`）。
  idle / permission 待ちを固定文言の対応表で通知する。**本文に自由文を載せない**
- **`SessionStart` での消費**（`hooks/scripts/run-session-start-hook.sh`）。
  記録を読み、**現在の project と一致するときだけ** 1 度だけ報告して削除する。
  使えない記録は原則 fail-closed で削除する（不正 JSON / 非 object / キー過不足 / 非 str 値 /
  **record ファイル自身の** symlink / 空 `project_root`）。「解釈不能 ＝ 無音 no-op」は
  `python3` 不在のような環境要因にだけ許す。
  **分類の正本は実行可能な表**（`tests/test_session_start_last_turn_failure_contract.py` の
  `ReaderClassificationTableTests._TABLE`）で、**ここに規則を書き下さない** ——
  例: **state ディレクトリ自体が symlink の場合は削除しない**（書き手がその経路に書かないため、
  そこにあるファイルは本 hook の産物ではない）。この例外は「散文で列挙すると落ちる」と
  hook 自身のコメントが予告しており、**実際 CHANGELOG 初版で落ちた**
- **bind 解決と containment 検証の module**（`hooks/scripts/lib/task_binding_resolve.py`）。
  `task_id` が正準形（`YYYYMMDD-slug`）でない / `steering_path` が `<repo>/.steering/` の外を指す /
  注入面のある文字（Unicode 一般カテゴリ Cc・Cf・Zl・Zp・Cs）を含む / 絶対パスでない、のいずれかで
  `conflict` に倒す。conflict の候補一覧は **slug と worktree の basename だけ**を出し、
  絶対パスを block message に載せない
- **tasklist 見出しの受理面を 1 module へ集約**（`hooks/scripts/lib/tasklist_parse.py`）。
  従来は `gdd_stop_hook.py` / `collect-gdd-telemetry.py` / bash hook 群が
  それぞれ独自の判定を持ち、正準形しか受理しない読み手が `### Task <N>: <name>` を
  取りこぼしていた（W-9 / CH-6 の silent failure 型）。
  **集約したのは python 側 2 読み手**で、**bash hook 2 本は本 PR の非スコープ**
  （`CH-4`。下記「未確認事項」）
- **静的 BLOCK check 2 本**（`tests/checks/osascript-arg-lint.sh` / `mcp-retry-token.sh`）。
  前者は `osascript` への `-e` 文字列連結と here-doc 区切りの未クォートを止める。
  後者は MCP 再試行 1 回の文言が配布物に存在することを固定する

#### Changed

- **`hooks.json` を 6 -> 8 event へ**（`StopFailure` / `Notification` を追加）。
  `README.md` / `CONTRIBUTING.md` / `docs/VERSIONING.md` の**手書きの event 一覧**は
  `hooks.json` を正本にした機械検査下に置いた
- **`gdd_stop_hook.py` の bind 解決**を `.claude/gdd-dev.local.md` 依存から
  `binding.json` + worktree / branch 一致へ。**bind できないときは block ではなく warn**
- **`collect-gdd-telemetry.py`** を共有受理面へ移行し、`bounce_count` /
  `unparsed_route_sections` を出力に追加。**`completed_tasks` / `pending_tasks` は
  `### Task <N>:` も数えるようになるため既存値より増える方向に変わる**（過小計上の是正）
- **`find-stale-steerings.sh`（W-10-3）**: **git tracked で運用している repo を検出対象外**にし、
  同一 steering ID を dedupe する（出力が変わる）。**受理面の集約とは無関係**
- `references/phase-progression.md` / `bounce-log-schema.md` / `common-guardrails.md` に
  運用規律を追記

#### Removed

- **`gdd_stop_hook.py` の `record_debug_bounce()` と `worklog.md` の
  `## Hook-Detected Debug Bounce Log` 節**（過去の entry で追加を告知した機構。実測 4 -> 0 hit）。
  bounce の計測は telemetry 側へ移した。
  `references/bounce-log-schema.md` も「Stop hook 内の記録機構は PR-W0 で削除済み」へ更新

#### Fixed

- **`find-stale-steerings.sh --help` が実行コード 3 行を漏らしていた**
  （`sed -n '2,19p'` の固定行数指定 -> 先頭コメントブロックの走査へ）

#### 未確認事項（判断に使った情報の限界）

- **実 Claude Code 上での通し確認は 0 回**。`StopFailure` -> 記録 -> `SessionStart` 報告の 3 段は
  hook を実プロセスで起動した end-to-end では確認したが、**実際の API エラーで発火させた確認はしていない**
- **`Notification` は高頻度 hook**。通知量が実運用でどうなるかは未計測
- 測定環境は **task ごとに異なる**（束ねない）。`StopFailure` / `Notification` の fd 破壊 18 形は
  **bash 3.2.57 / macOS**・**5.3.15 / Alpine musl**・**5.2.37 / Debian glibc**、
  `SessionStart` の sanitize / fail-closed 4 形は **3.2.57 / macOS**・**4.4.23 / Alpine musl**・
  **5.2.37 / Debian glibc**。**bash 4 系で測ったのは後者だけ**で、
  `run-notification-hook.sh` のヘッダは「**bash 4 系は 1 形も測っていない**」と明記している。
  Windows / WSL は全 task で未確認
- **`CH-4`: bash hook 2 本に silent failure が現存**。
  `run-session-start-hook.sh` と `run-user-prompt-submit-hook.sh` の awk は
  `^### Task:` だけを見るので `### Task <N>: <name>` を取りこぼす。
  **影響は Current Task 表示と進捗カウントの欠落に限られる**（done guard と bounce 計測は
  python 側で集約済み）。本 PR の非スコープ
- **MCP 再試行 1 回の規律が導線へ届いていない**（`ADV-T23-4`）。文言は
  `references/common-guardrails.md` に置いたが、**参照するのは実測 28 skill 中 12**（gate 系）で、
  `gdd-dev`（ワークフロー入口）/ `gdd-goal-driven-execution` / `gdd-pr-review-followup` は未参照
- **`references/` の行数上限 12,427 に対し残枠 0**（`ADV-T23-1`）。
  次に `references/` へ 1 行足す変更は即 RED になる
- **`osascript-arg-lint` が走査しない形が 6 クラス**残っている（行継続 / 拡張子なし実行ファイル /
  変数経由 / 複数行 argv / 引用符内の区切り文字 / 引用文脈の誤検出）。
  うち fail-open の 4 形は、**全呼び出しがその形へ退行すると空虚化ガードが捕まえる**ことを実測済み

#### User Action Required

- **新規 hook の導入自体は無影響**。`StopFailure` / `Notification` はどちらも block しないため、
  既存の停止・継続の挙動は変わらない。kill switch（`~/.claude/gdd-hooks-disabled`）は新規 2 hook にも効く
- **telemetry を下流で消費している場合は再ベースラインが要る**。
  `completed_tasks` / `pending_tasks` が増える方向に変わり、`bounce_count` /
  `unparsed_route_sections` と summary の `bounce` 節が増える
- **git tracked で steering を運用している repo は `find-stale-steerings.sh` の検出対象外になる**。
  該当運用では stale 検出が黙って消えるので、必要なら別手段を用意すること
- **`.gdd/tasks/<task_id>/binding.json` を持たない進行中セッションでは done guard が弱まる**。
  bind 不能時は **block ではなく warn** へ降格する（AC-2）

#### Validation / Eval Impact

- 差分規模も**ここに書かない**。**導出**: `git diff --numstat $(git merge-base HEAD origin/main) HEAD`

- 全体 suite の実測値は**ここに書かない**（この節を編集するたびに変わる自己参照量）。**導出**: `python3 -m pytest plugins/gate-driven-development/tests/ -q`
- 各 task で**退行注入による判別力の実測**を行った。とくに
  `osascript-arg-lint` は判定窓の誤りで 4 ラウンド連続の是正を要し、
  最終的に負変異 11 / 正の対照 13 の**対**で測っている
- **`validate-plugin.sh` は `origin/main` 由来で exit 1**。fail は **2 件**で、
  `skill-body-budget`（express / standard の runtime token 超過）と
  `lint-scripts-functional`（`lint-runtime-budget.py` の smoke test）。
  本 PR の変更は原因ではなく、一時 worktree で `origin/main` 単体でも同一数値になることを実測した。
  fail-fast のため `skill-body-budget`（6 番目）以降 38 件が走らないので、
  検証は **manifest を読んで 44 件を個別実行**する形で行った（pass 42 / fail 2、fail 2 件とも pre-existing）

### [0.33.0] - 2026-08-25

#### Summary

Cursor / Codex のモデルルーティングを 2026-08 時点の提供状況へ最新化した。
Cursor は GPT-5.4 / GPT-5.5 体系から **Grok + Composer 主体**（heavy: `Grok 4.6`、
light / leaf: `Grok 4.5`、実装: `Composer 2.5`、Dialectic Counter: `Opus 5` は維持）へ、
Codex は **GPT-5.6 系（Sol / Terra / Luna）**（heavy: `gpt-5.6-sol`＝CLI 既定、
light / leaf / 実装: `gpt-5.6-terra`、cheap lane: `gpt-5.6-luna`）へ移行した。
GPT-5.4 は ChatGPT サインイン利用の Codex で 2026-08-31 に廃止予定であり、
GPT-5.5 も GPT-5.6 GA（2026-07-09）で一世代前となったため両方とも routing から除外した。
effort 差別化の考え方（gate=medium / heavy=low / risk=high、light=medium / leaf=low）は変更しない。

#### Changed

- **`scripts/resolve-gdd-model.py` の `TIER_TO_MODEL`** を Cursor: `grok-4.6` / `grok-4.5` /
  `composer-2.5`、Codex: `gpt-5.6-sol` / `gpt-5.6-terra` へ更新
- **`references/cursor.md` / `references/codex.md` を全面改訂**（新モデル体系の正本）。
  `skills/gdd-model-routing/SKILL.md`・`references/fixed-models.md`・
  `skills/gdd-model-routing/references/cursor.md`・`references/cursor-guide.md`・
  `references/subagent-dispatch.md`・`references/dialectic-review.md`・
  `references/onboarding.md`・`references/human-check-template.md`・`README.md`・
  `commands/gdd-dev.md`・各 skill の `## Fixed Model`（24 ファイル）を同期
- **Codex の Dialectic Counter** は別世代 GPT（5.4↔5.5）から**別階層 GPT-5.6
  （Sol↔Terra）+ reviewer prompt role** へ変更
- **mini禁止境界**は cheap lane モデル（`gpt-5.6-luna` / `Grok Code Fast 1` 等）への
  適用として維持
- `scripts/setup-gdd-loop.sh` の heavy model 警告を Grok 4.6 基準へ更新

#### 未確認事項（判断に使った情報の限界）

- `Grok Code Fast 1` の Cursor での提供継続は 2026-08-25 時点で未確認のため、
  cheap lane は `Grok 4.5 + low` を既定にし「使えればそちら」の位置づけとした
- Grok 4.6 の `reasoning.effort=xhigh` は xAI API 仕様上は存在するが Cursor UI での
  露出が未確認のため不使用のまま

#### User Action Required

- Cursor / Codex で GDD を使う場合、モデルピッカー / `config.toml` の既定を
  新モデル（Grok 4.6 / gpt-5.6-sol）に合わせる。Claude Code の割り当てに変更はない

#### Validation / Eval Impact

- `tests/test_model_routing_contract.py` / `tests/test_autonomous_model_worker_contract.py` /
  `tests/checks/hooks.sh`（resolver cases・require/forbid tokens）/
  `scripts/benchmark-model-routing.py` を新モデル体系の期待値へ更新。
  全 1055 テスト green、hooks.sh チェック OK

### [0.32.0] - 2026-08-25

#### Summary

モデルルーティングの「宣言と実行の乖離」を是正した。tier 表は brainstorming /
formal gate = Opus 5 と定めながら、(1) `gdd-pr-review` が light_task（Sonnet）に
割り当てられ、(2) resolver の LIGHT_HINTS に "brainstorming" / "requirements" が
含まれて新規 workflow の入口が light に解決され、(3) 対話セッションでモデル指定が
軽いまま formal gate に入っても乖離がどこにも表面化しなかった。実例:
2026-08-22 の Agent 指示メモリ機能開発では formal 工程一式がセッションモデル
（Sonnet 5）のまま進行し、gate 通過後の実害級欠陥 6 件を検出したのは
Opus + effort=high の最終レビューだけだった。

#### Changed

- **`gdd-pr-review` を `light_task` から `general_heavy_risk` へ昇格**
  （Claude Code: `Opus 5` + `effort=high`、Cursor / Codex: `GPT-5.5` +
  `reasoning.effort=high`）。`scripts/resolve-gdd-model.py` の `PHASE_TO_TIER`、
  `skills/gdd-model-routing/SKILL.md`、`references/fixed-models.md`、
  `references/codex.md`、`skills/gdd-model-routing/references/cursor.md`、
  `skills/gdd-pr-review/SKILL.md`（v0.4.0）を同期
- **resolver の LIGHT_HINTS から "brainstorming" / "gdd-brainstorming" /
  "requirements" を除去**し、phase 未確定の entry でこれらの語を含む場合は
  `formal_gate` に解決する `GATE_ENTRY_HINTS` を追加
- **Phase Gate Pre-check に「Model Tier の照合」（advisory）を追加**
  （`references/phase-gate-prechecks.md` § Common Pre-check 手順 4）。formal gate
  進入時に実行モデルが推奨 tier より軽い場合、乖離を明示して 1 回だけユーザー
  確認を取り、`Last Handoff Summary` に `model-ack:<model>` を残す。
  `gdd-model-routing` § 判断の優先順位 1 にも同じ規約を追記
- **Think モードの effort 段階を 4 段階（low/medium/high/xhigh）に訂正**。
  固定値は `high` を維持し、`xhigh` は限定使用のまま。格上げは gdd-metrics の
  before/after 実測後に判断する

#### User Action Required

- なし（動作既定の変更のみ）。`gdd-pr-review` の実行コストは上がる方向に変わる。
  docs-only PR で軽く済ませたい場合は従来どおり冒頭でモデル推奨が案内される

#### Validation / Eval Impact

- `tests/test_model_routing_contract.py` に 3 テストを追加（pr-review の risk tier
  固定・entry hint の formal_gate 解決・light hint の退行防止）。TDD（RED→GREEN）
  で追加し、既存の routing contract テストは全て green

### [0.31.2] - 2026-08-23

#### Summary

`gdd-codebase-health.py` の `python_cyclomatic_complexity` / `python_function_count`
に、`large_file` と同型の baseline ratchet 機構を追加した。diff が悪化させていない
既存コード（pure-move・コメント修正等）に触れただけで pre-PR gate が恒久的に
ブロックされる問題への対応。

#### Fixed

- **pure-move やコメント修正のみの変更でも、既存の複雑度・関数数が High として
  再検出され `gh pr create` が恒久的にブロックされる問題を修正した**。原因は
  `collect_python_structure_findings` に `large_file` 側にはある baseline 例外
  機構が存在せず、diff に含まれる `.py` ファイルはファイル全体を無条件で
  スキャンしていたこと（`--mode changed` は rename 検出なしの `git diff
  --name-only` ベースのため、pure-move も新規スキャン対象になる）

#### Added

- `gdd-codebase-health-baseline.json` に `python_complexity`（`path` / `function`
  キー）と `python_function_count`（`path` キー）を追加。それぞれ
  `current_*` / `target_*` / `reduce_by` / `expires_on` / `reason` を持ち、
  `large_files` と同じ ratchet 意味論（登録された現在値までは許容し、touch の
  たびに `reduce_by` 分だけ縮小を要求、期限切れは high finding で無効化）で動く

#### User Action Required

- 既存の高複雑度関数・多関数ファイルを pre-PR gate で通したいリポジトリは、
  `gdd-codebase-health-baseline.json` に `python_complexity` / `python_function_count`
  のエントリを追加する。診断で得た `path`（と complexity の場合は `function`）・
  現在値を `current_*` に、縮小目標を `target_*` に設定する
- 既存の `large_files` エントリの書式・意味論に変更はない

#### Validation / Eval Impact

- `tests/test_engineering_baseline_architecture_contract.py` に baseline の
  allow / grow-blocks / reduction-warn / expired の 4 パターンを `python_complexity`
  ・`python_function_count` それぞれに追加（計 9 テスト）。既存 1052 件は全て green

### [0.31.1] - 2026-08-21

#### Fixed

- **`version-not-consumed` の層 B が統合先自身で必ず失敗していたのを直した**
  （`tests/checks/version-not-consumed.sh`）。層 B の 2 つの assert は、作業ツリーが統合先
  （`origin/main`）そのものだと**構造的に必ず失敗する** — (1)「記録された統合先の消費済み版数が
  stale」は、統合先の版数が直前に merge されたブランチの bump 値である以上、「1 つ前に消費した
  版数」を指す記録とは定義上一致しない (2)「その版数は already released」は、統合先では出荷版数
  == released 版数なので恒真。帳簿では解消できず、**任意の PR が merge された直後から `main` の
  `validate-plugin.sh` が恒久的に赤くなっていた**（実測: v0.31.0 が main に入った直後の main で
  FAIL 2 件）。副作用として、**plugin を一切変更しない PR にも版数 bump を要求**し、中身の
  変わらない release を帳簿に書かせていた
- 層 B が守るのは「**ブランチが**統合先の消費済み版数を再利用しないこと」なので、守る対象が無い
  2 条件でスキップするようにした: **HEAD が統合先に含まれる**（ブランチ側の出荷版数が存在しない）/
  **plugin ツリーが統合先と同一**（このブランチは何も出荷しない）。層 A は引き続き無条件で有効
- **測った入力集合**: 3 条件を実測した。統合先自身 = SKIP-B / rc=0、plugin 差分なしのブランチ =
  SKIP-B / rc=0、**陽性対照**（plugin を変更しつつ消費済み版数を出荷）= **FAIL のまま**。
  陽性対照は当初 未コミットの変更で測ってしまい何も検出していなかったため、commit してから
  測り直した（`git diff <ref> HEAD` は commit 同士の比較で、作業ツリーの変更は見ない）

#### Added

- **`.github/copilot-instructions.md` と `.github/instructions/gate-driven-development.instructions.md`
  を追加した**。外部 AI レビュアー向けに、本 repo が主に Markdown（skill / agent 定義）と補助
  スクリプトで構成されること、日本語でレビューすること、YAGNI / KISS / DRY と加算式改修の禁止、
  コード健全性の目安、機密情報の扱い、PR の前提コマンドを伝える

### [0.31.0] - 2026-08-21

#### Summary

配布物に残っていた社内固有の識別子（実メールアドレス・社内 org 名 / repo 名・内部ロール名）を
汎用的な表記へ置き換えた。契約・挙動の変更は無い。

#### Changed

- **plugin manifest 3 本と marketplace.json の `email` を差し替えた**
- **社内 org 名・repo 名・内部ロール名を汎用表記へ置き換えた**（org は `example-org`、repo は
  `example-repo`、内部ロール名は役割が分かる一般名）。対象は CHANGELOG / docs / references-archive /
  evals / test fixtures / 契約テスト
- **残存 4 件を追加で処置した**（セルフレビュー指摘）。社内 repo 名が
  `skills/gdd-using-git-worktrees/SKILL.md` の worktree パス例（**配布される skill 本文**）、
  scenario eval fixture、`CHANGELOG.md` 2 箇所に残っていた。**この節には識別子そのものを書かない** —
  redaction の記録に識別子を列挙すると、記録自体が redaction を打ち消す（実際、初稿でこれを踏んで
  「全て 0 件」と書いた同じ段落が 6 パターンすべてを含む状態になった）。**測った入力集合**は
  `git log` で本 PR の置換前後の差分に現れる旧表記の全パターンであり、確認は
  `git diff <merge-base>...HEAD | grep -E '^-' | grep -oE '<旧表記>'` で再現する

#### Verification

- 置換で**テストの判別力が落ちていない**ことを URL 集合の before/after 比較で確認した。多重度込みで
  1:1 対応し、とくに `other/repo/pull/100` は `example-org/repo/pull/100` と別物のまま残るため
  「別 org・同じ PR 番号」を区別するケースは保たれている

### [0.30.0] - 2026-08-21

#### Summary

`commands/gdd-resume.md` の frontmatter が YAML として parse できず、`allowed-tools` を含む
全フィールドが実行時に黙って捨てられていた。値をクォートして直し、同じ壊れ方を検出する
BLOCK を新設した。

#### Fixed

- **`commands/gdd-resume.md` の frontmatter が parse 不能だったのを直した**。`argument-hint` の値が
  クォートされておらず `例: ` を含んでいたため、YAML がそこをキーの区切りと解釈して frontmatter 全体が
  壊れていた。**`allowed-tools` の宣言も同時に無効化されていた**

#### Added

- **`tests/checks/command-frontmatter-parse.sh` を新設した**（BLOCK）。`commands/*.md` / `skills/*/SKILL.md` /
  `agents/*.md` の frontmatter を走査し、クォートされていないプレーンスカラーのうち **実 YAML parser が
  拒否すると実測した 3 形**（`: ` を含む / 末尾がコロン / `*` で始まる）を弾く。**測った入力集合**: ruby/psych を
  正本にした差分テストで 3 形とも PARSE_ERR を確認し、3 形それぞれの変異注入で rc=1 になることも実測した。
  **担保はこの 3 形だけで、その外側については主張しない** — python 標準ライブラリに YAML parser が無く本物の
  parse ができないため、`` `backtick` `` / `%directive` / `- dash` / `? question` / `, comma` / 未終端クォートは
  同じく壊れるが検出しない（script の docstring に列挙した）

### [0.29.0] - 2026-08-19

#### Summary

`git push` と `gh pr create` を PreToolUse hook で機械ゲート化し、セルフレビューの証跡が無い / 古い / 収束していない状態での push・PR 作成を fail-closed で止める。あわせてセルフレビュー自体を 3 レーン（内部整合・接地・敵対）+ 収束ループ（2 連続クリーンで `dry: yes`）に作り替え、レビュー観点の正本を 1 ファイルに集約した。

#### Added

- **`git push` の pre-push gate を新設した**（`hooks/scripts/run-pre-push-gate-hook.sh`。`hooks/hooks.json` の PreToolUse `Bash` matcher に 3 本目として配線）。active GDD 中の `git push` が block される reason code は次の 6 種類:

  | reason code | 発火条件 | 証跡を直せば通るか |
  |---|---|---|
  | `unresolvable-root` | `git --git-dir=...` / `--work-tree` を伴う push（対象 repo を一意に決められない） | 通らない |
  | `refspec-ambiguous` | `--all` / `--mirror` / `--branches`、または remote 名の後に refspec を 2 個以上置いた push（`git push origin a b`）。push 対象 ref の tip を一意に決められない | 通らない |
  | `optout-log-write-failed` | escape hatch は成立したが、その使用記録の追記に失敗した | 通らない |
  | `missing-evidence` | `state.md` の `Pre-Push Self Review` が無い / 書式不正 | 通る |
  | `sha-mismatch` | 証跡の sha が push 対象 ref の tip と一致しない | 通る |
  | `dry-not-reached` | dry を要求する `Task Size` で `dry: no` | 通る |

  - `Task Size` 別: `trivial` は無条件で通す。`quick (express)` は証跡を要求するが `dry: yes` は要求しない。`quick (standard)` / `standard` は `dry: yes` まで要求する。**`Task Size` が `state.md` に無い / 上記 4 値以外の場合は fail-closed で `standard` と同じ扱いに正規化される**（`gh pr create` の dry gate も同じ向きで、`trivial` / `quick (express)` 以外はすべて `dry: yes` を要求する）
  - escape hatch `GDD_SKIP_PRE_PUSH_GATE=1` の**受理面は 2 つ**（どちらも使用がログに記録される）:
    - **プロセス env**: hook プロセスが `GDD_SKIP_PRE_PUSH_GATE=1` を持っていれば、コマンド文字列に現れなくても受理される（ログの `via: process-env`）
    - **コマンド前置**: `git` の直前に置いた `GDD_SKIP_PRE_PUSH_GATE=1 git push ...`（ログの `via: command-prefix`）。前置は「コマンドの先頭」であればよく、先頭は行頭に限らず `&&` / `||` / `;` / `|` / `&` / `(` / 改行の直後も含む。他の `NAME=VALUE` 代入や `env` token が混ざっていてもよい（`env GDD_SKIP_PRE_PUSH_GATE=1 git push` / `FOO=bar GDD_SKIP_PRE_PUSH_GATE=1 git push` / `cd <repo> && GDD_SKIP_PRE_PUSH_GATE=1 git push` はいずれも受理される）
    - **受理されない形**（いずれも push としては検出されるので block される）: 値が `1` 以外（`=0` / `=true`）、`export GDD_SKIP_PRE_PUSH_GATE=1; git push` のように別コマンドへ分離した形、`bash -c` / `eval` の中に書いた形、`(true) GDD_SKIP_PRE_PUSH_GATE=1 git push` のように `)` の直後に置いた形 — ここまでは `missing-evidence`。`git push origin main GDD_SKIP_PRE_PUSH_GATE=1` のように `git` より後ろへ置いた形は代入が refspec として数えられるため `refspec-ambiguous` になる
  - block メッセージには必ず「書き込み先 `<steering-dir>/state.md`」「必要な key」「復旧導線」の 3 要素が入る
- **セルフレビューの正本 `references/self-review-lanes.md` を新設した**。3 レーン定義、検出漏れ分類 v1（10 分類、各分類はいずれか 1 レーンにのみ配置）、`gdd-pr-review` 3f の A〜E 型との対応表、修正時規律 A（同型パターンの全域 grep）/ B（未消化スレッドを残さない）、Task Size × レーンのリスク比例発火表、followup 周回時のレーン要求、`not_applicable` 理由 token 語彙（`no-external-dep` / `docs-only` / `prompt-only` / `test-only`）、効果測定指標を 1 ファイルにまとめた
- **`tests/validate-plugin.sh` の BLOCK を 4 本増やした**（`self-review-lane-tokens` / `self-review-lane-provenance` / `version-not-consumed` / `bounded-claim-evidence`）。登録は `tests/checks/manifest.tsv` 経由なので **`validate-plugin.sh` 自体に差分は無い**。1 本目はレーン正本の token と順序、2 本目は分類根拠ブロックへの固有名詞混入を allow-list 文法で検査する
- **限定・全称の断定に実測記録を対で要求する BLOCK を新設した**（`tests/checks/bounded-claim-evidence.sh`）。`担保しない` / `測っていない` / `観測範囲の外` / `外側については主張しない` のような限定宣言を書いた出荷文書（`references/` / `skills/` / `docs/`）は、同じ文書に `**測った入力集合**` の宣言を持たなければ FAIL する。マーカー語彙・実測記録の宣言形・走査範囲・走査除外はいずれも `references/self-review-lanes.md` § 分類5 の下位型 の宣言行から機械導出し、検査側 literal との一致を assert する（**両側 pin**。正本だけを書き換えても検査側だけを書き換えても FAIL する）。語彙の導出が空・該当文書が 0 件・正本ファイルが不在のいずれも独立に FAIL する（空洞化アンカー）。非 UTF-8 の `.md` は traceback ではなく FAIL 行で落ちる。**測った入力集合**: 隔離コピー上で出荷 script そのものを実行し、正例 1 形 + 文書側の変異 7 形（実測記録の削除 / 実測記録節の削除で参照だけ残す形 / 限定語彙を空にする / 実測語彙の宣言行を削除 / 語彙を実在しない語へ差し替え / 正本節の削除 / 正本ファイルの削除）に加え、**検査側の変異 2 形**（走査範囲 literal の縮小 / 実測記録の宣言形 literal の骨抜き）と**走査範囲・走査除外の宣言行の変異 2 形**、および非 UTF-8 の `.md` を走査対象へ置いた 1 形を測った。正例 rc=0 / 変異すべて rc=1（SURVIVOR 0 / traceback 0）。さらに本 PR の過去 commit `8df25d0` 時点の `docs/VERSIONING.md`（限定宣言はあるが実測記録が無い実データ）に対して rc=1 を確認した。**測っていない（＝主張しない）**: `.steering/` 側の証跡（出荷されないため対象外）、`CHANGELOG.md`（他文書の断定を引用する release log のため対象外）、日付付きの過去 PR アーカイブ（`docs/design/` / `docs/plans/` / `docs/audits/`。後から追記しない時点記録のため対象外）、および限定宣言マーカー以外の限定語（`のみ` / `だけ` / `すべて` / `必ず` の 4 語。運用不能かつ既存出荷内容が FAIL するため語彙に採らなかった。**却下語彙の hits と走査文書数は本 check の成功時出力が正本**で、ここには件数を書かない — `bash tests/validate-plugin.sh` の `bounded-claim-evidence: OK (…)` 行がそのまま実測値になる）
- **出荷版数が統合先で消費済みでないことを検査する BLOCK を新設した**（`tests/checks/version-not-consumed.sh`）。既存の `grade-evals` / distribution readiness test は version を持つ 4 箇所の**相互一致**しか見ないため、4 箇所すべてが統合先と同じ版数でも通ってしまう。本 check は `docs/VERSIONING.md` に記録した「統合先の消費済み版数」より真に大きいことを常時（git 不要）検査し、統合先 ref が解決できる環境ではその記録が実測と一致することと、出荷版数が統合先 CHANGELOG に released として現れないことも検査する。ref を解決できない環境では `SKIP-B: <理由>` を出力して常時検査だけで判定する。3 つの入力（manifest version / 記録行 / 統合先 ref 側の version）は**欠落・書式不正・型違いを同じく FAIL** として扱う（`v0.28` / `vTBD` のような非 semver の記録や、JSON の `null` / 数値 / 真偽値 / 配列 / オブジェクトを素通りさせると、比較の述語ごと消えて PASS になるため）。**この断定は実測で確定した入力集合の内側に限る**（測った形と結果の一覧は `docs/VERSIONING.md` § 統合先が消費済みの版数を再利用しない の「測った入力集合」。集合の外側については主張しない）。この検査が SKIP-B 環境で何を担保し、何を担保しないか（「記録行が semver として妥当なまま統合先の実態から古い」形は常時検査の観測範囲外で、ref を解決できる環境の検査が塞ぐ）と、運用ルールの正本は `docs/VERSIONING.md` § 統合先が消費済みの版数を再利用しない

#### Changed

- **pre-PR gate が heredoc 本文を command word として token 化していたのを直した**（`hooks/scripts/run-pre-pr-gate-hook.sh`）。heredoc の中身は**データ**であって command word ではないのに token 化されるため、本文に `gh pr create` という語の並びを含むだけの `git commit -F - <<MSG ... MSG` が「PR 作成」と誤判定され block された。二重引用符で括った引用（`echo "gh pr create"`）は shlex が 1 token にまとめるので誤検出しない、という非対称が原因。誤検出された非 PR コマンドは **body を持たない**ため「PR body を検査できません」を満たしようがなく原理的に通せない。**本 PR の commit が実際に 2 回止まり、修正パッチ自身も同じ理由で 2 回止まった**。token 化の前に heredoc 本文を落とすようにし、`<<WORD` / `<<-WORD`（インデント終端）/ 引用符付き終端語の 3 形が block されないことと、本物の PR 作成コマンドが従来どおり block されることを contract test で固定した（修正前の hook に対して 3 形とも FAIL することを差分で確認済み）

- **埋め込み python の制約をコメントに明記した**（同ファイル）。この python は `python3 -c` の**単一引用符付き文字列の中**にあり、単一引用符を 1 つでも含めると文字列がそこで閉じてスクリプトが壊れる（実測で `bash -n` が落ちた）。引用符クラスは `\x27` / `\x22` のエスケープで書く

- **`gdd-pr-review` に § 2b「Self Review 証跡の記録」を新設した**（セルフレビューで検出）。pre-push gate は standard タスクの**全 push** に `Pre-Push Self Review` を、pre-PR gate は `gh pr create` に `Pre-PR Self Review`（`dry: yes` 到達）を要求するが、**その記録を指示する skill が gate より前の導線に無かった**。`Pre-Push Self Review` を指示していたのは `gdd-pr-review-followup`（自身の定義で「PR が既に在る」前提のレーン）だけで、**初回 push は PR 作成より前に起きる**ため間に合わない。`Pre-PR Self Review` 側も、PR 作成直前レーンを名乗る `gdd-pr-review` の言及が 0 だった（実測: 各 SKILL.md の `grep -c` = 0、hook / scripts 側の hit はすべて読み取り・検証で書き込みは無し）。§ 2b に書式・初回 push から要る旨・Task Size 別の分岐・`dry` と `consecutive_clean` の自己矛盾を明記した

- **`tests/test_pr_review_section_enumeration.py` を追加した**。`tests/checks/pr-review-anticipation-tokens.sh` は手順 step 2 の列挙を literal で pin するが、literal の pin は「列挙が消えていない / 旧版に戻っていない」ことしか言えず、**節を足して列挙を更新し忘れると pin を新 literal に直せてしまい不一致のまま通る**（分類 A）。「列挙 == 実在節（順序込み）」を数え直しで固定し、どちらかが空なら FAIL する空洞化アンカーも入れた。判別力は変異注入で実測している（節を 1 本増やして列挙を据え置くと FAIL）

- **pre-PR gate の `gh api` 判定が広すぎたのを直した**（`hooks/scripts/run-pre-pr-gate-hook.sh`）。PR 作成の endpoint は `POST /repos/<owner>/<repo>/pulls` **ちょうど**だが、判定が `"/pulls" in path` の**部分一致**だったため、`/pulls/<n>/requested_reviewers` / `/pulls/<n>/comments` / `/pulls/<n>/reviews` / `/pulls/<n>/merge` への POST まで「PR 作成」に化けて block されていた。これらは body を持たないので「PR body を検査できません」で**原理的に通せない**。`gdd-pr-review-followup` が規定する Copilot レビュー依頼とインライン返信がまさにこの形で、**本 plugin の規定する運用が自分の gate に塞がれていた**（本 PR のドッグフーディングで検出）。query string と末尾スラッシュを落としたうえで**末尾一致**だけを見るようにし、4 つの sub-resource が block されないことと、`POST .../pulls` は従来どおり block されることを contract test で固定した

- **`hooks/scripts/validate-steering-write.py` の 2 関数を分解し、循環的複雑度を上限内へ戻した**（Codebase Health Gate の High 2 件。超過は本 PR より前から存在していた）。`collect_violations` は 7 個の同型ブロックを `DETECTORS` の表（`(category, finder, describe)` の 3 つ組）へ畳み、行の状態遷移を `_advance_section_state()` へ切り出した。`run_advisory_lints` は `_resolve_plugin_root()` / `_find_steering_dir()` / `_lint_warning()` へ分解した。**振る舞いは不変**で、`main` 版と本版に同じ入力を与えて出力が完全一致することを差分テストで確認している（`collect_violations` 15 ケース / `run_advisory_lints` 5 ケース）。検出器の追加は今後この表だけで閉じる。トレードオフとして同ファイルの関数数が 38 → 42 になり warn 上限 40 を超えた（fail 上限は 80 で blocking ではない）

- **`gh pr create` の pre-PR gate に dry gate を追加した**（`hooks/scripts/run-pre-pr-gate-hook.sh` 末尾の独立ブロック）。`Task Size` が `trivial` / `quick (express)` **以外**（`quick (standard)` / `standard`、および未記載・未知値）の場合、`Pre-PR Self Review` が無い・書式不正（`missing-evidence`）または `dry: yes` 未到達（`dry-not-reached`）で `gh pr create` が block される。pre-PR gate 側には per-command の逃げ道を用意していない（`GDD_SKIP_PRE_PUSH_GATE` は `git push` 専用で、`gh pr create` には受理面が無い）
- **`.steering/` への書き込み検証（`hooks/scripts/validate-steering-write.py`）が `Pre-PR Self Review` / `Pre-Push Self Review` の書式を検証するようになった**。書式不正の証跡が `state.md` に書き込まれる時点で止まるため、push / PR 作成まで気付かないケースを減らす
- **`Pre-PR Fix Attempts` のカウント定義を拡張した**（`references/post-completion-pr-flow.md`）。High finding 残存に加え、`dry: yes` 未到達での差し戻し（gate の `missing-evidence` / `dry-not-reached` block を含む）も +1 の対象になる。加算するのは AI であり hook は `state.md` を書かない。`gdd-pr-review` 3f による同一周回内の自己修正は加算しない
- `references/state-field-tiers.md` の Tier 3 に `Pre-PR Self Review` / `Pre-Push Self Review` / `PR Review Follow-up Attempts` を追加した（いずれも上書きされるまで保持。既存 field の補記を含む）
- `gdd-pr-review-followup` の Fix 手順を「直す → 同型を全域 grep → 再 review」の 3 段に固定した。`gdd-pr-review` 3f と `gdd-implementation-gating` は分類の正本として `references/self-review-lanes.md` を参照するようになり、`references/task-sizing.md` は発火条件の重複記載をやめて同 reference に委譲する

#### Affected Files

- `hooks/hooks.json` / `hooks/scripts/run-pre-push-gate-hook.sh`（新規）/ `hooks/scripts/lib/push_command_parse.py`（新規）/ `hooks/scripts/lib/self-review-evidence.sh`（新規）/ `hooks/scripts/run-pre-pr-gate-hook.sh` / `hooks/scripts/validate-steering-write.py`
- `references/self-review-lanes.md`（新規）/ `references/state-field-tiers.md` / `references/post-completion-pr-flow.md` / `references/task-sizing.md`
- `skills/gdd-pr-review/SKILL.md` / `skills/gdd-pr-review-followup/SKILL.md` / `skills/gdd-implementation-gating/SKILL.md`
- `tests/test_pre_push_gate_contract.py`（新規）/ `tests/test_push_command_parse.py`（新規）/ `tests/test_self_review_evidence.sh`（新規）/ `tests/test_self_review_lanes_contract.py`（新規）/ `tests/test_validate_steering_write.py`（新規）/ `tests/test_hook_block_reason_recovery_contract.py`（新規）/ `tests/_block_reason_support.py`（新規）/ `tests/test_pre_pr_gate_contract.py` / `tests/test_validate_plugin_check_inventory.py`
- `tests/checks/self-review-lane-tokens.sh`（新規）/ `tests/checks/self-review-lane-provenance.sh`（新規）/ `tests/checks/version-not-consumed.sh`（新規）/ `tests/checks/bounded-claim-evidence.sh`（新規）/ `tests/checks/manifest.tsv` / `tests/checks/skill-body-budget.sh` / `tests/checks/lint-scripts-functional.sh`
- `CONTRIBUTING.md` / `references/codex.md` / `references/cursor.md` / `references/fixed-models.md`（統合先取り込み後の `references/` 行数バジェットに収めるため、同一ファイル内で重複していた節を統合した）
- `.claude-plugin/plugin.json` / `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` / `docs/VERSIONING.md` / `CHANGELOG.md`

#### User Action Required

- **既定の block 条件が増える**（`docs/VERSIONING.md` § Breaking Change の分類 / 利用者体験レベル）。更新後、active GDD 中の `git push` と `gh pr create` は証跡が無いと止まる。証跡は `state.md` に次の 1 行形式で書く（`Pre-PR Self Review` も同型）:

  ```
  - Pre-Push Self Review: <sha> | rounds: <N> | consecutive_clean: <0|1|2> | dry: <yes|no> | lanes: internal=<n>,grounding=<n|not_applicable(<reason-token>)>,adversarial=<n> | at: <ISO 8601>
  ```

  - `sha` は push 対象 ref の tip（7〜40 桁の hex。短縮形も可）。`dry: yes` は `consecutive_clean` が 2 以上のときだけ有効で、矛盾した組み合わせは書式不正として扱われる
  - レーンの意味・`not_applicable` の理由 token・`dry` の判定基準は `references/self-review-lanes.md` を参照する
- **証跡を直しても通らない停止条件が 3 つある**（いずれも証跡検査より前段で判定するため、`state.md` を書き足しても解除できない）:
  - `unresolvable-root`: `git --git-dir=... push` / `--work-tree` を伴う push。当該 repo へ `cd` してから通常の `git push` に置き換える
  - `refspec-ambiguous`: `git push --all` / `--mirror` / `--branches`、および `git push origin a b` のように refspec を 2 個以上並べた push。ref を 1 つに絞って push を分ける
  - `optout-log-write-failed`: escape hatch の使用記録が書けなかった場合。記録先（`$GDD_HOOK_STATE_DIR/pre-push-optout.log`。既定は `~/.claude/.gdd-hook-state/pre-push-optout.log`）の書き込み権限を直す
  - この 3 つを回避する in-band の手段は無く、escape hatch か kill-switch のみになる
- **誤爆時の一時回避**: `git push` は `GDD_SKIP_PRE_PUSH_GATE=1` を hook プロセスの env に置くか、`git` の直前へ前置する（受理される形・されない形は上記 `#### Added` の escape hatch の項が正本）。`gh pr create` には env による逃げ道が無く、両 gate とも `~/.claude/gdd-hooks-disabled` を置く既存の kill-switch で無効化できる。opt-out の使用は記録されるため、常用は想定していない
- **恒久的に無効化する場合**は `hooks/hooks.json` の PreToolUse `Bash` matcher から `run-pre-push-gate-hook.sh` のエントリを削除する
- `state.md` のフォーマット自体は変更していない（Tier 3 への field 追加のみ）。証跡が無い既存 steering でも、証跡を書き足せばそのまま通る

#### Validation / Eval Impact

- 契約テストを 6 ファイル新設した（`test_pre_push_gate_contract.py` / `test_push_command_parse.py` / `test_self_review_evidence.sh` / `test_self_review_lanes_contract.py` / `test_validate_steering_write.py` / `test_hook_block_reason_recovery_contract.py`）。既存 `test_pre_pr_gate_contract.py` には dry gate 分を追記した
- `tests/validate-plugin.sh` に `self-review-lane-tokens` / `self-review-lane-provenance` / `version-not-consumed` / `bounded-claim-evidence` の 4 BLOCK を `tests/checks/manifest.tsv` 経由で登録した。全 BLOCK 通過
- `--max-standard-estimated-tokens` を統合先取り込み後の実測値へ再設定した（`references/task-sizing.md` の単一正本参照が +36 estimated tokens。統合先は再設定前の上限をちょうど使い切っていた）。`tests/checks/skill-body-budget.sh` と `tests/checks/lint-scripts-functional.sh` の同期は `tests/test_runtime_budget_arg_sync_contract.py` が機械強制する
- 全体テストスイート **1043 passed, 1 skipped, 978 subtests passed**（回帰なし）。内訳の変化は本 release 内で追加した test のみ — pre-PR gate の判定修正 2 件（`/pulls/<n>/` の 4 sub-resource / heredoc 3 形）と列挙照合の test 2 件

### [0.28.0] - 2026-08-18

#### Added

- `scripts/lib/hitl_budget.py` を新設し、HITL 一次表示の行数バジェットの正本を一本化した。lint と marker sync contract が同じ定数を参照する
- `scripts/lint-hitl-decision-quality.py` に any-of 群（`REQUIRED_DECISION_MARKER_GROUPS`）を新設した。compact と full で語彙が違う表示要素を、どちらの正本でも通る形で受ける
- `references/requirements-template.md` に `Workflow Fit Check` を追加した

#### Changed

- **HITL の承認ポイントを 4 要素から 6 要素へ拡張した**（`この案を選ぶと次に何が起きるか` / `無回答時のデフォルト` を追加）。承認者が「何を承認すればよいか分からない」まま OK を求められる状態を減らす
- `Workflow Fit Check` / `Adversarial Requirements Review` / `LLM 方針レビュー` を、`not_applicable` のとき HITL から欄ごと省略してよい形に変更した（判定結果と理由は `requirements.md` に必ず記録する）
- lint のマーカーを装飾なしの content word へ再同期した。`lint-human-check-language` が最終 HITL に要求するフレーズは 6 語になり、`30秒判断` は必須から外れて `判断ポイント` に置き換わった
- `scripts/lint-hitl-complexity.py` の `--max-lines` 既定値を実運用値へ引き下げ、`scripts/lib/hitl_budget.py` の定数を正本にした
- `references/human-check-template-compact.md` に `ズレ確認` を追加した
- 承認者向けドキュメント（`docs/NON_ENGINEER_HITL_GUIDE.md` / `docs/NON_ENGINEER_APPROVER_HANDOUT.md` / `references/team-onboarding.md` / `docs/DISTRIBUTION_READINESS.md`）が案内する欄名を、正本テンプレートに実在する語へ揃えた

#### Fixed

- `references/human-check-template.md` の必須ルール採番の重複（8 / 11 / 12 / 13）を解消し、1〜26 の連番一意にした
- `lint-hitl-decision-quality` が、compact にしか無い語を full にも要求して**正本どおりに書いた HITL を落としていた**誤検知を解消した
- `docs/DISTRIBUTION_READINESS.md` の lint 説明を実挙動へ揃えた。必須から外れた語を「要求する」と書いていた点と、`lint-human-check-language` が実際には検査していない OK 境界を「確認する」と書いていた点の 2 件
- 承認者向け手順書が、正本テンプレートに実在しない見出しを HITL の読みどころとして案内していたのを解消した

#### Affected Files

- `references/human-check-template*.md` / `references/prompt-contract-map.md` / `references/requirements-gating-steps.md` / `references/requirements-template.md` / `references/team-onboarding.md` / `skills/gdd-requirements-gating/` / `scripts/lint-*.py` / `scripts/lib/hitl_budget.py` / `tests/` / `docs/`（承認者向け 3 ファイルと R9-2 監査シート）/ 3 manifest / `docs/VERSIONING.md`
- `skills/gdd-brainstorming/` と `evals/` は本リリースに含まれない

#### User Action Required

- なし。既存の `state.md` / `worklog.md` のフォーマットは変更していない

#### Validation / Eval Impact

- eval scenario の追加は本リリースに含まれない
- `tests/validate-plugin.sh` の既存 check 群に新マーカーが反映される。あわせて `tests/test_r9_2_anchor_verify_contract.py` を削除した（R9-2 照合の配線は後続 PR へ退避。allow list の宣言と監査記録は残す）
- 全体テストスイート 872 passed, 1 skipped, 650 subtests passed（回帰なし）。`tests/validate-plugin.sh` 全 BLOCK 通過

### [0.27.1] - 2026-08-16

#### Fixed

- **`state.md` のフィールド値がバッククォート囲みで書かれていると、値の先頭・末尾に `` ` `` が残ったまま比較・パス解決に流れる silent failure を 3 箇所で修正した**。書き手（skill / エージェント）は `` - Key: `value` `` と `- Key: value` の両方の形で書くが、読み手が片方しか受け付けていなかった。`Resume From` / `Next Action` / `Worktree` / `Branch` のような routing の要になるフィールドで、エラーを出さないまま誤った値が伝播していた
  - **`scripts/gdd_task_binding.py` の `_field()`**（最も影響が大きい）: `line = raw.strip().strip("`")` が**行全体**からバッククォートを落としていた。行は `` - Worktree: `~/.gdd/worktrees/<repo>/<task>` `` の形で先頭が `-` のため末尾の `` ` `` しか除去されず、**値の先頭の `` ` `` が残る**。結果 `_norm()` の `expanduser()` が `~` を認識できず相対パス扱いになり、`upsert-from-state` が `<cwd>/` + `` ` `` + `~/.gdd/...` という壊れた `worktree_path` を `binding.json` に記録していた。この binding は `resolve_task()` の `worktree_path == cwd` 判定に一致しないため、**該当 task が常に `conflict` / `no_current_worktree_binding` に落ちる**
  - **`scripts/setup-gdd-loop.sh` の `parse_field()`**: 行全体が `` ` `` で囲まれた形だけを剥がしており、値側の `` ` `` を落としていなかった。`` `done` `` が terminal 集合に一致せず終了済み steering を候補に拾う、`` `gdd/foo` `` が git branch 比較に一致せず誤って `active_branch_mismatch` / `state_task_mismatch` を報告する経路があった
  - **`scripts/collect-gdd-telemetry.py` の `normalize_field_value()`**: `|` 以降の audit suffix は落とすがバッククォートは落としていなかった。`` `approved` `` / `` `done` `` が集計リテラルに一致せず、gate 一発通過率・完走率が実態より低く出る。`gdd-metrics` の scorecard が参照する値なので、改訂の採否判定を歪めうる
  - **修正方針**: `.steering/` 配下への書き込みは PreToolUse hook (`hooks/scripts/run-steering-write-hook.sh`) がローカル絶対パス（`/Users/...`）を deny するため、`state.md` 側を絶対パスに直す方向は取れない。**読み手側が `~` とバッククォートの両方を許容する**のが正しい直し方であり、3 箇所とも値側にだけ `strip("`")` を適用する形に揃えた
- **`tests/checks/lint-scripts-syntax.sh` の shell 側の対象が `find-stale-steerings.sh` 1 本だけの個別列挙だったのを、`scripts/*.sh` 全数に広げた**。上記の `setup-gdd-loop.sh` 修正中に、`$( ... )` 内の heredoc に backtick を奇数個書いて command substitution のパースを壊す事故を起こしたが、この BLOCK をすり抜けて後段の遅い e2e check (`active-steering-candidate-resolution`) でしか落ちなかった。bash は heredoc 内でも backtick をペアとして数えるため、当該 heredoc では backtick リテラルを使わず `chr(96)` で表現する（理由をコメントで固定した）
- `docs/VERSIONING.md` の「現行バージョン」表記が v0.26.0 のまま stale で、`tests/test_distribution_readiness_contract.py` が失敗していたのを解消した。あわせて `.cursor-plugin/plugin.json` / `.codex-plugin/plugin.json` が v0.26.0 に取り残されていたのを 3 manifest 揃えて bump した

#### User Action Required

- **既存の `.gdd/tasks/*/binding.json` に壊れた `worktree_path` が記録されている場合は再生成が必要**。`worktree_path` に `` ` `` や `~` が含まれていないか確認し、含まれていれば該当 task の `state.md` に対して `python3 scripts/gdd_task_binding.py upsert-from-state --repo-root <repo> --state <path/to/state.md>` を再実行する。修正後のパーサで正しい絶対パスに書き直される
- `state.md` のフォーマット自体は変更していないため、書き手側（skill / エージェント）の対応は不要

#### Validation / Eval Impact

- `tests/test_task_binding_resolver.py` に `TestStateFieldParsing` を追加（5 ケース）。バッククォート囲みチルダ / 裸のチルダ / バッククォート囲み絶対パス / `Branch` のバッククォート除去 / `_field()` の値側限定 strip を固定
- `tests/test_state_field_backtick_parsing_contract.py` を新設（7 ケース）。`setup-gdd-loop.sh` の `parse_field()` と `collect-gdd-telemetry.py` の `extract_field()` について、同型の欠陥が再発しないことを固定する
- 全体テストスイート 862 passed, 1 skipped, 648 subtests passed（回帰なし。v0.27.0 時点で failing だった `test_distribution_readiness_contract` も本リリースで green）
- `tests/validate-plugin.sh` 全 BLOCK 通過。`lint-scripts-syntax` は対象拡大後も全 10 本の `scripts/*.sh` が通ること、および意図的に壊した script で非ゼロ終了することを確認済み

### [0.27.0] - 2026-08-14

#### Added

- **PR followup ループの根本原因調査で確定した 7 件の穴を修正した**（`gdd-pr-review-followup` / `gdd-using-skills` / stop hook）。example-repo の実 PR（旧#822/#823/#899/#900/#910/#915/#922/#924/#927/#928/#840 等）と実セッショントランスクリプトの突合、および Opus による独立レビューで確定
  - **`gdd-using-skills` に GDD PR Follow-up Entry を新設**: Task Binding Registry が `conflict`/`none` を返す、`.claude/gdd-dev.local.md` が無関係な別 task を指す、`.steering/<task>/state.md` が存在しない、のいずれでも `gdd-pr-review-followup` を優先する。GDD Brainstorm Entry / GDD Debug Entry と同型。Task Binding Registry 自体（`scripts/gdd_task_binding.py`）は既に正しく `conflict` を検出できていたが、検出後に PR followup へルーティングする standalone entry が無く、`superpowers:receiving-code-review` や自作の Bash/Monitor ポーリングへフォールバックしていた（example-repo PR 旧#922 / 旧#927 / 旧#928 で確認）
  - **`gdd-pr-review-followup` の Collect ステップに suppressed comments 展開を追加**: Copilot の "no new comments" 表示の裏に埋もれる suppressed comments を個別 finding として展開する。PR 旧#900 実測で 54 件、うち 6 件が実バグだった
  - **同 Collect ステップに `mergeStateStatus: CONFLICTING` 検知を追加**: 他の review finding より優先する actionable finding として扱う。PR 旧#900 / 旧#922 で base への merge conflict が 10 時間以上検知されず放置されていた実測を踏まえる
  - **required checks の判定を個別 check 単位に変更**: 集約表示だけで "CI green" と判定しない。PR 旧#823 で個別 check（`lambroll diff`）の失敗を見落としていた実測を踏まえる
  - **PR スコープ膨張の抑止規律・セルフレビュー打ち切り宣言の禁止を Guardrails に追加**: PR 旧#900 が 34 commits / +3238 行まで膨張し、かつ「セルフレビューはここで打ち切り」と自己免除を宣言した後に一度もセルフレビューを通さず push し続けていた実測を踏まえる
  - **Architecture Check を hook で機械化**（`hooks/scripts/lib/pr_review_followup_polling.py` 新設）: `PR Review Follow-up Attempts` が上限（既定 12、`PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS`）に達したら、transcript が `external-review-waiting` を出力していても stop hook が `blocked` へ強制する。`lib.auth_waiting.next_reason_after_auth_wake` と同型だが、そちらは hook 未配線のまま放置されていたため、今回は `gdd_stop_hook.py` の `try_stop_with_done_guard` に実配線した

#### Fixed

- skill 文言だけで自己申告に依存していたポーリング上限が、エージェントの自己判断（自己免除宣言）で無効化される経路を塞いだ

#### User Action Required

- なし。既存ワークフローへの追加ガードのみで、既存の `state.md` / `worklog.md` フォーマットは変更しない

#### Validation / Eval Impact

- 契約テスト `tests/test_pr_review_followup_contract.py` に 6 ケース追加（suppressed comments / conflict 検知 / CI 個別判定 / PR スコープ抑止 / セルフレビュー打ち切り禁止 / GDD PR Follow-up Entry）
- 契約テスト `tests/test_pr_review_followup_polling_cap_contract.py` を新設（6 ケース）。poll cap の unit 挙動と、stop hook e2e（cap 未到達で pause を維持 / cap 到達で blocked に強制されて state.md がクリアされる）を固定
- 全体テストスイート 850 passed, 1 skipped（回帰なし）
- `tests/validate-plugin.sh` 全 BLOCK 通過（`skill-body-budget` は `gdd-using-skills` の追記分を圧縮して budget 内に収めた）

### [0.26.0] - 2026-08-14

#### Added

- **skill / prompt 改訂の採否を行動メトリクスで判定する scorecard を追加**した（`scripts/gdd-scorecard.py`）。`collect-gdd-telemetry.py --format=json` の snapshot を改訂前後で 2 つ取り、実際に走った task の実績だけで `adopt` / `reject` / `mixed` / `inconclusive` を出す
  - 出典: Microsoft が VS Code のコーディングエージェントの system prompt を改訂した際、主観レビューではなく行動指標（コミット数・編集所要時間・読み取りトークン量）の scorecard で採否を決めていた事例。GDD ではこれまで改訂の効果測定が empirical-prompt-tuning の自己申告と scenario evals に寄っており、「良くなった気がする」を排除する常設の枠がなかった
  - 指標定義は script 内の `METRICS` registry が**単一の正本**。`--list-metrics` で機械的に取り出す（SKILL.md / README に表を複製しない）。初期指標は 8 本（Fix Attempts / Error Log / Workflow Incident / 完走率 / リルート率 / 各 gate の一発通過率）
  - `--fail-on-regress` で regression 時に exit 3 を返すため、CI や cron からも使える

#### Changed

- `gdd-metrics/SKILL.md` に § 改訂の採否をスコアカードで判定する を追加（v0.1.0 → v0.2.0）。description に before/after scorecard の用途を追記して、改訂の効果を問う相談でも発火するようにした

#### Fixed

- scorecard の初版が**実データで偽陽性を出した**ため、リリース前に修正した。`n=3→4` の実 steering データで完走率が 25 ポイント動いたのを `adopt` と判定していたが、これは task 1 件が done になっただけで、相対変化ベースの noise-floor では検出できない
  - 各指標に `unit`（割合指標=100 / 件数指標=1）を持たせ、`unit / 母数` を「task 1 件が動かせる量」として、これを超えない差は `flat` に落とすガードを入れた。同じ実データで `adopt` → `inconclusive` に変わることを確認済み
  - 同一 repo の時系列比較では candidate snapshot が baseline の task を内包して希釈されるため、`steering_id` 一致分を candidate から除外する（除外数は `carried_over_excluded` として出力）

#### User Action Required

- なし。既存のワークフローには介入しない（scorecard は明示的に呼んだときだけ動く読み取り専用スクリプト）

#### Validation / Eval Impact

- 契約テスト `tests/test_gdd_scorecard_contract.py` を新設（24 ケース）。指標 registry の単一正本性・carry-over 除外・gate 通過率の分母・1 task ガード・exit code を固定した
- doc-check `lint-scripts-functional` に scorecard の smoke を追加。`--list-metrics` の疎通に加え、**regression で実際に exit 3 が返ること**まで見る（「crash しない」だけだと常に inconclusive を返す実装でも通ってしまうため）
- negative test: `--fail-on-regress` の分岐を無効化すると smoke が FAIL（exit 1）し、復元すると PASS することを確認した
- SKILL body budget: 7001 → 7042 行（上限 7162、canonical check 数は 37 据え置き）

### [0.25.2] - 2026-08-13

#### Fixed

- `references/gdd-self-development.md` の復旧手順が「repo から再同期する」と書いており、**plugin の正本が local である**という repo 全体の運用（local → repo へ publish する仕組み）と食い違っていた。local には git 履歴が無いこと、rsync で戻すと**未 publish の local 変更が失われる**こと、先に `scripts/check-plugin-drift.py` で差分を確認することを明記した


### [0.25.0] - 2026-08-08

#### Added

- **3f に `E. 設計変更の追随漏れ` を追加**した。実装中に置き場所・方式・対象を変更した場合、先に書いた説明文がすべて追随しているかを見る。**A が数え直しで見るのに対し、E は差分との突き合わせで見る**
  - ①CHANGELOG / ADR / PR 本文 / コードコメントが名指ししているファイル・節・skill を、実際の変更ファイル一覧（`git diff --name-only <default-branch>...HEAD`）と突き合わせる ②「新設した」「追加した」と書いた対象が実際に差分にあるか ③採用しなかった初版の案を説明したままの文が残っていないか
  - 出典: PR 旧#210 = budget 制約で置き場所を 2 回変更（`gdd-writing-skills` → `gdd-using-git-worktrees` の節 → 同 Guardrails の 1 行）した際、CHANGELOG と doc-check のコメントが初版の記述のまま残り、**Copilot に 2 件指摘された**

#### Changed

- パターン追加の運用の内訳表記を `A / B / C / D` → `A / B / C / D / E` に更新

#### Validation / Eval Impact

- 既存 doc-check `pr-review-anticipation-tokens` に E の逐語 pin を 3 本追加（**canonical 37 据え置き**。新規 check は作らない）

### [0.24.0] - 2026-08-08

#### Added

- **GDD 自身を開発するときのルールを明文化**した（`references/gdd-self-development.md`）。GDD で GDD を開発すると動いている道具と作っている成果物が同一になるため、層ごとに開発場所を変える
  - `hooks/scripts/*` は**毎回パス実行**され即座に影響する（`PreToolUse` は Bash 実行のたびに走る）ため、worktree で開発し suite が green になるまで local に入れない
  - `skills/*/SKILL.md` と `references/*.md` は参照時に読まれ、次に呼ぶまで影響が出ないため **local を直接編集してよい**
  - 壊れたときは `touch ~/.claude/gdd-hooks-disabled` で全 hook を no-op にできる（全 12 本の runner 先頭に `gdd_kill_switch_active` があり純 bash で python / git 非依存）
- `gdd-using-git-worktrees/SKILL.md` の § Guardrails に上記 reference への参照を 1 行追加した（**発火点**）。「worktree で開発するか local を直接編集するか」は同 skill の責務であり、置き場所は budget が決めた（`gdd-writing-skills` は allowlist baseline 558 行で 1 行も足せず、`gdd-using-git-worktrees` も独立節では per-skill 上限 350 を超えた）

#### Fixed

- **実体が存在しない `gate-driven-development-b` への同期指示を全削除**した。repo にも `~/.claude/plugins` にも該当ディレクトリが無いにもかかわらず、SYNC ヘッダー等 4 ファイルが同期を指示していた（守りようがない契約）
  - `gdd-pr-review/SKILL.md` の SYNC ヘッダーは、実体のある bundle 版への同期義務を残す形に付け替えた

#### Validation / Eval Impact

- doc-check `gdd-self-development-tokens` を新設（**canonical 36 → 37**、`test_canonical_count_is_36` → `_37`）。発火点である参照行と層別ルールを逐語 pin し、`gate-driven-development-b` の残存を `ban` で検出する

### [0.23.0] - 2026-08-08

#### Added

- **3f のパターン D に ④「その検証は本当に対象を見ているか」を追加**した。①〜③がガードの緩さを見るのに対し、④は**検証そのものが空振りしていないか**を見る（環境変数の差し替えが実際に効いているか / 比較・集計の対象が実物か / 失敗するはずの条件で本当に落ちるか）
  - 出典（いずれも v0.22.1 の作業中に実際に起きた）: `mktemp -t` が `TMPDIR` を無視するため**空のディレクトリを数えており、何をしても「残存 0」になる**検証をしていた / 2 つのレビュー結果を**実在確認せずに比較**して結論を出していた
- 運用上の含意として「negative test は『RED になった』で終わらせず、壊したはずの対象が実際に消えている / 変わっていることを先に確認する」を ADR に記録

#### Validation / Eval Impact

- 既存 doc-check `pr-review-anticipation-tokens` に D④ の逐語 pin を 2 本追加（**canonical 36 据え置き**。新規 check は作らない）
- negative test: ④ を削除すると RED になることを確認（削除後の該当箇所数が 0 であることを先に検算してから実行）

### [0.22.1] - 2026-08-08

#### Fixed

- **doc-check スクリプト 12 本の temp 後片付けを `trap ... EXIT` に統一**した。従来は成功経路の末尾でしか `rm` しておらず、`set -euo pipefail` で assertion が失敗して即終了すると temp ファイル / ディレクトリが残っていた（CI コンテナやローカルの `TMPDIR` に蓄積する）
  - 対象: `clarification-brief-lint` / `codebase-health-smoke` / `existing-code-reading-lint` / `hitl-complexity-lint` / `hitl-display-integrity-lint` / `hitl-outcome-audit-lint` / `human-check-language-lint` / `lint-scripts-functional` / `pr-review-followup-state-lint` / `resume-integrity-lint` / `state-tasklist-continuity-lint` / `worktree-provenance-lint`
  - **trap は最初の mktemp 直後**に登録し、後段で作る temp は `"${VAR:-}"` ガードで未定義でも安全に展開されるようにした（`lint-scripts-functional.sh` は初回と最終の mktemp が 218 行離れており、その間で終了すると漏れていた）
  - trap で完全にカバーされる末尾の `rm` 行は削除した。条件分岐内の `rm` は残している
  - `skill-body-budget` は対象外。temp が関数内の `local` 変数で、トップレベルの trap からは参照できない。同関数は 7 箇所すべての経路で既に片付けているため変更不要

#### Changed

- v0.20.0 の ADR § 測定結果（AC-11）に**既存 gate との重複測定**を追記し、`/code-review` の Pre-PR 統合を**採用しない**と結論した。同じ diff に `gdd-implementation-reviewer` をかけたところ、`/code-review medium` の 8 件中 6 件を検出し、さらに両外部レビューが見逃した最重要欠陥を 1 件見つけた

#### Validation / Eval Impact

- 契約変更なし（patch bump）。canonical 36 据え置き
- 修正前 / 修正後の対比実測: 最初の temp 作成直後で失敗させ、システム temp の差分で **修正前 1 件残存 → 修正後 0 件**

### [0.22.0] - 2026-08-08

#### Added

- **3f に `D. 検証・ガードの緩さ` を追加**した。今回追加・変更したガードや検証が意図した対象より広く通らないかを点検する: ①pin / assert の文字列が区切り（引用符・バッククォート・行頭行末）まで含んでいるか ②既定値や `None` / 空が素通りしないか ③後片付け・解放・ロールバックが成功経路にしか無くないか
  - 出典: PR 旧#204（doc-check の pin token が先頭のバッククォートを欠き部分一致で通った）/ PR 旧#206（temp の後片付けが成功経路にしかなく `set -e` の失敗時に残った）

#### Changed

- **3f の適用対象にコード側を明記**した。散文（ADR / requirements / PR 本文）だけを見て終わらせず、**コード内の docstring / テストの assertion / 検証スクリプトの pin** も対象に含める。3f 導入後 2 PR の実測で、3f が見落とした 3 件はすべてコード側だった（自己検出した 5 件はすべて散文側）
- パターン追加の運用の内訳表記を `A / B / C` → `A / B / C / D` に更新

#### Validation / Eval Impact

- 既存 doc-check `pr-review-anticipation-tokens` を逐語トークンで拡張（D の見出し / 適用対象の拡張 / 内訳表記を別トークンで pin）。**新規 check は作らないため canonical 36 据え置き**（`test_canonical_count_is_36` / `manifest.tsv` / inventory ヘッダーは無改変）
- v0.20.0 の ADR § 測定結果（AC-11）に、コードを含む PR での `/code-review medium` 再測定結果を追記

### [0.21.0] - 2026-08-08

#### Added

- **HITL の「根拠の母集団」を条件付き必須にした**。`scripts/lint-hitl-decision-quality.py` に条件付き判定を 1 本追加し、HITL 出力に `件の実測` / `実測` / `件中` が現れたら `根拠の母集団` の記載を要求する。既存の `PR_BOUNDARY_PHRASES → PR_FOLLOWUP_MARKER` と同じパターン
- `tests/checks/hitl-decision-quality-lint.sh` に negative fixture を追加（件数を根拠に出しながら母集団が無い HITL が reject されることを CI で検証）
- `human-check-template.md` に母集団の仕様（何を書くか / 悪い例 / fail-open の限界）を追加
- doc-check `hitl-population-tokens` を新設。linter の条件判定行と marker 値を逐語 pin し、既存 `REQUIRED_DECISION_MARKERS` 11 件の無改変も `req` で検証する

#### Changed

- `human-check-template.md` の既存 2 欄の記入規則を強化: `OKしても今回は対象外のこと` は**権限の話ではなく scope の話**であること、`完了条件の変換` の `dropped` / `deferred` は**当初目的のどこを取りに行かないか**を書くこと
- `human-check-template-compact.md` の § Template と § Required Words、`requirements-template.md` の § 判断材料 に母集団欄を追加

#### User Action Required

- 件数・実測を根拠に HITL を出す場合、その N をどの集合から取ったかの記載が必須になる。欠けると `lint-hitl-decision-quality.py` が落ちる
- 発火は**条件付き**（該当語が出た場合のみ）。件数を根拠にしない HITL には何も要求されない

#### Validation / Eval Impact

- **canonical 35 → 36**（`test_canonical_count_is_35` → `test_canonical_count_is_36`）。budget 上限は変更していない（実測 express 184/186、standard 806/815 で上限内）

### [0.20.0] - 2026-08-08

#### Added

- **`3f. External Reviewer Anticipation Check`（常時）** を `gdd-pr-review` の § GDD 固有チェックに新設。外部 AI レビュアーが実際に指摘する 3 型（A 数値・列挙の自己不整合 / B コマンド・式の引数省略 / C 断定の過剰一般化）を PR 作成前に自己点検し、レビュー往復を減らす。検出時は **High finding にせず修正して続行**し、`Pre-PR Fix Attempts` は増やさない
- 3f にパターン追加の運用（指標 = PR 単位の指摘件数と A/B/C 内訳 / 記録先 / 3 PR 連続で検出 0 件なら再設計する見直しトリガ）を規定
- doc-check `pr-review-anticipation-tokens` を新設（発火点である実行対象列挙行を逐語 pin し、改訂前の列挙が残っていないことを `ban` で検出）
- `test_validate_plugin_check_inventory.py` に canonical ヘッダーの自己整合テストを追加。算術 `26 + 3 + N = M` を parse し `M == len(CANONICAL_CHECK_NAMES)` と `N == "plus <name> added" の記載数` を検証する（同じ箇所で外部レビュアーに 2 回指摘された集計値ズレを決定論で閉じる）

#### Changed

- **`gdd-pr-review` 手順 step 2 の実行対象列挙を `（3a, 3b, 3c, 3d, 5, 6）` → `（2a, 3a, 3b, 3c, 3d, 3d-2, 3e, 3f, 5, 6）` に修正**。節として存在しながら列挙から漏れていた **2a / 3d-2 / 3e も手順として実行を要求される**ようになる

#### Fixed

- 節を追加しても手順の実行対象列挙に載らなければ実行されない、という発火点の取りこぼしを解消

#### User Action Required

- Pre-PR loop で 2a（Evidence Before PR Claims）/ 3d-2（Worktree Provenance Gate）/ 3e（Superpowers Benchmark Summary）が実行対象として明示される。これまで列挙から漏れていた分、PR 作成前の確認がわずかに増える
- 3f はブロッカーではない（検出 → 修正 → 続行）。既存の High 差し戻し契約（`Pre-PR Fix Attempts`）は無改変

#### Validation / Eval Impact

- **canonical 34 → 35**（`test_canonical_count_is_34` → `test_canonical_count_is_35`）。`references/pr-review.md` は `pr-review` plugin からの同期対象のため無改変。guard / hook は無変更

### [0.19.0] - 2026-08-07

#### Added

- **Stage Continuation の stacked 分岐（⑥'）**: 依存 Stage（`Depends on` あり）を、先行 Stage の branch を base にした stacked worktree で merge 待ちなく先行着手できるようにした（2 段まで）。発火は 6 条件の AND で、`Continuation Mode=auto-stacked` の明示選択と `deleteBranchOnMerge=true` が前提
- `Continuation Mode` に `auto-stacked` を追加（依存 Stage 専用。独立 Stage は従来どおり `auto-after-clean`、既定は `manual`）
- 継続先 steering への `Stacked Base` 記録（先行 Stage ID / head branch / tip SHA / `baseRefName`）と、Lane の `In-flight PR` の記載形式 `<Stage ID>: <PR URL> (<state>)` を規定
- stacked PR は `gh pr create --base <先行 branch>` で作成し、先行 merge 後の base 付け替えは GitHub の自動 retarget に委ねる

#### Changed

- worktree の base 規定に第 3 の許容値（未マージ先行 Stage の branch）を追加し、「task branch を base にしない」の無条件禁止に `auto-stacked` 例外を明記
- `safe cleanup ready` に stacked 依存の確認を追加（stacked 側が main へ rebase 完了するまで先行 worktree を cleanup しない。判定は `merge-base` と `rev-parse` の一致で行い、merge 戦略に依存しない）
- Pre-Flight の main 進行検知と scope 外 file 検出に stacked 分岐を追加（先行未マージ中は fetch 対象と比較対象の両方を先行 branch に切り替え、`origin/<default-branch>` への auto rebase を抑止）
- PR Body Boundary Check の全称文を独立継続 / stacked の場合分けに改訂
- 昇格・HITL 表示規定（`requirements-gating-steps.md` / `gdd-requirements-gating`）を `auto-stacked` にも適用

#### User Action Required

- `auto-stacked` は**依存 Stage 専用**の明示選択値。既定は従来どおり `manual` で、単一 Stage・独立 Stage・`post-merge` / `manual` trigger の挙動は変わらない
- stacked 継続には repo の `deleteBranchOnMerge=true` が必要（false の repo では発火しない）
- 3 段以上の stack は非対応（`Depends on` が未マージ Stage 2 件以上、または先行自身が stacked の場合は継続しない）

#### Validation / Eval Impact

- 既存 doc-check `stage-continuation-tokens` を逐語トークンで拡張（発火点を個別に pin。件数の正本は steering の § 検証ヒント表）。**新規 check は作らないため canonical 34 据え置き**（`test_canonical_count_is_34` 無改変）。guard / hook は無変更

### [0.18.0] - 2026-08-07

#### Added

- **Stage Continuation（独立 Stage の先行着手）**: 段階実装で Stage N の PR が Auto-Arm の収束 clean に到達したら、merge を待たずに独立な次 Stage へ自動着手する（`references/post-completion-pr-flow.md` Option 1 手順 6）。発火は 6 条件すべての AND（Lane に Pending Stage / Auto-Arm 有効 × clean / `Follow-up Trigger=after-current-pr` / `Human Recheck=not required` / `Continuation Mode=auto-after-clean` / 独立判定 pass）
- `Planned Follow-up Stage Lane` に 3 列を追加: `Stage Files`（独立判定の入力）/ `In-flight PR`（着手済み Stage の PR と merge 状態）/ `Continuation Mode`（`auto-after-clean` | `manual`、**既定 `manual`**）
- `Follow-up Trigger=after-current-pr` の意味を定義（従来は語彙のみで未定義）
- doc-check `stage-continuation-tokens` を新設（存在検証 + 改訂前文言の残存検出 + Auto-Arm 発火条件の無改変検証）

#### Changed

- 継続を禁止していた既存契約 6 箇所（`state-machine.md` / `post-completion-pr-flow.md` / `phase-progression.md` / `gdd-completion-check` / `gdd-requirements-gating` / `requirements-gating-steps.md`）を Stage Continuation の発火条件付きに改訂
- clean → done の分岐点（`gdd-pr-review-followup` の state 契約と停止境界、Post-Completion PR Flow の Step 4、`subagent-dispatch` / `gdd-completion-check` / `phase-progression` の done 記述）に継続分岐を追加
- Auto-Arm の収束 clean 到達時に `Next Action=done` の確定とあわせて `Resume From` から `external-review-waiting` を外し、terminal を確定させることを明記（GDD の terminal 判定は両 field を見るため）

#### User Action Required

- 既定は従来挙動: `Continuation Mode` の既定は `manual` で、明示的に `auto-after-clean` を選んだ Stage だけが継続対象。単一 Stage タスク・`post-merge` / `manual` trigger・`Human Recheck=required`・Auto-Arm 無効環境の挙動は変わらない
- `auto-after-clean` を選ぶ場合は HITL の独立承認ポイントに昇格し、圧縮表示経路でも値と選定理由が表示される
- 依存 Stage の stacked 先行着手は本リリースの対象外（後続 Stage S-2 として着手前再承認）

#### Validation / Eval Impact

- 新設 doc-check `stage-continuation-tokens`（`manifest.tsv` / `CANONICAL_CHECK_NAMES` 登録済み、canonical 33→34、`test_canonical_count_is_34`）。既存 `pr-review-auto-arm-tokens` / `pr-review-followup-polling-tokens` は無変更で green


### [0.17.0] - 2026-08-07

#### Added

- **Auto-Arm（PR 作成後の外部 AI レビュー収束の自動化）**: 設定キー `PR Auto Review Convergence: reviewers=<list>` があり、タスク自走上限が「PR 作成 + 外部レビュー収束まで」の場合、PR 作成 + CI pass 後に外部レビュアー（copilot 等）へ自動依頼し、`gdd-pr-review-followup` の Review Pending Loop へ人間キックなしで遷移して clean まで自走する（`skills/gdd-pr-review-followup/SKILL.md` § Auto-Arm Entry / `references/post-completion-pr-flow.md` § Auto-Arm）
- 設定キー仕様を `references/operation-levels.md` に追加（解決順: ① `~/.gdd/config.local.md` ユーザーグローバル優先 ② `.gdd-config.md` チーム共有。優先順位: タスク自走上限 > 設定キー）
- 自走上限の選択肢「PR 作成 + 外部レビュー収束まで」を `references/human-check-template.md` § 承認後の到達点に追加（設定キーがある場合の seed 既定・不在時の「収束までは選択不可」併記義務を含む）
- doc-check `pr-review-auto-arm-tokens` を新設（契約トークンの存在検証 + 旧 done 文言の残存検出）

#### Changed

- done 停止を規定する既存 6 記述（post-completion-pr-flow.md Step 4 ×2 / phase-progression.md CI Wait / subagent-dispatch.md Completion-Check Template / gdd-completion-check SKILL.md ×2）を Auto-Arm 分岐込みに改訂。Express 専用行は従来どおり（Auto-Arm 非適用）

#### User Action Required

- 有効化は opt-in: `~/.gdd/config.local.md` に `PR Auto Review Convergence: reviewers=copilot` を置く。設定キーが無い環境は従来挙動のまま（変更なし）
- merge は引き続き人間が実行する。AC / scope / policy / security boundary に触れる指摘・poll 上限 12 回・依頼コマンド失敗では停止して人間に戻る

#### Validation / Eval Impact

- 新設 doc-check `pr-review-auto-arm-tokens`（`tests/checks/manifest.tsv` / `CANONICAL_CHECK_NAMES` 登録済み、canonical count 32→33）。既存 `pr-review-followup-polling-tokens`（E-2 契約）は無変更で green


### [0.16.4] - 2026-08-04

#### Summary

GDD 改善計画 M-1（差し戻し記録の導線修復）。`gdd-systematic-debugging` への phase 遷移を `gdd_stop_hook.py` が機械的に検出し、各 gate skill の自己申告に依存しない記録経路を追加した。既存 7 種の `Bounce Log`（`references/bounce-log-schema.md`）は指示ベースで実測 0/91 件だったため、hook 発の独立した記録として新設した。

#### Added

- `hooks/scripts/gdd_stop_hook.py` に `record_debug_bounce()` を追加。既存の phase 遷移検出ロジック（`phase_transitioned`）を再利用し、`gdd-systematic-debugging` への遷移を `worklog.md` の `## Hook-Detected Debug Bounce Log` セクションへ append-only で記録する
- 同一タスクで `bounce_count >= 2`（既存 7 種 Bounce Log と同じ閾値）になると `[bounce-escalation]` warning を systemMessage に出す（`decision:block` による強制はしない。fail-open）
- `human_recheck_required` / `planning_rework_required` への遷移検出時に `bounce_count` を 0 にリセットする（`phase_transitioned` に依存しない unconditional 呼び出し。Copilot レビュー指摘対応）
- 重複していた phase marker 候補リストを `GDD_PHASE_MARKERS` 定数へ統合（`main()` 内の heuristic フォールバックと共有）

- `record_debug_bounce()` に早期 return を追加（reset trigger も bounce 対象でもない通常ターンでは `_find_active_tasklist()`（`git worktree list` 実行を含む）を呼ばない。Copilot レビュー指摘対応 — hook は毎ターン実行されるため常時オーバーヘッドを避ける）
- `_append_bounce_log_line()` を、bounce log 見出しが**末尾セクションの場合のみ** true append（`open("a")`）に変更。見出しの後に別セクション（例: `## Error Log`）が追加されていた場合は、新しい行が別セクション内に紛れ込まないよう見出しを再度末尾に追加してから記録する（Copilot レビュー指摘対応。前回の true append 化がセクション構造破損の副作用を持っていた）

#### Changed

- `main()` は 426 → 424 行（`GDD_PHASE_MARKERS` 定数化による重複コード削除と、Copilot レビュー対応の unconditional 呼び出し + エラーログ追加が相殺。行範囲は `def main()` 行から `if __name__` 行の直前まで）
- `_append_bounce_log_line()` を true append 方式に変更（Copilot レビュー指摘対応。以前は毎回 worklog.md 全体を読み書きしていた）

#### Fixed

- CHANGELOG の記述誤り: `[bounce-escalation]` warning は systemMessage のみに出力され、stderr には出力されない（Copilot レビュー指摘対応）
- **`_read_latest_bounce_count()` の task slug 誤帰属バグ**: `"task: <slug>"` の部分文字列一致で判定していたため、あるタスクの slug が別タスクの slug の prefix になっている場合（日付ベースの slug で起こりうる）、無関係な別タスクの `bounce_count` を誤って引き継いでしまう実データ破損バグがあった。回帰テストで実際に `bounce_count: 9`（別タスク）から `10` へ誤加算されることを確認した上で、slug の完全一致（`task: <slug> |`）に修正した（Copilot レビュー指摘対応）
- `_append_bounce_log_line()` の true append が、worklog.md が改行で終わっていない場合に新しい行を直前の行へ連結してしまう問題を修正（Copilot レビュー指摘対応）
- `record_debug_bounce()` の reset trigger 判定に、このファイル内の他箇所と同じ `last_output or ""` 防御パターンを適用（Copilot レビュー指摘対応。現在の呼び出し元では `None` にならないが、既存コードベースの規約に合わせた）

#### Breaking Contract Changes

- なし（`worklog.md` への新規セクション追加のみ。既存 7 種 `Bounce Log` の記録経路・schema は変更していない）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_stop_hook_e2e.py::TestDebugBounceLog` に 8 fixture（初回検出 / escalation warning / counter reset / phase 遷移なしでも reset が発火することの回帰確認 / 別セクションが後続してもセクション構造が壊れないことの回帰確認 / task slug 誤帰属が起きないことの回帰確認 / trailing newline 欠落時に行が連結されないことの回帰確認）
- `pytest`: 814 passed, 620 subtests passed
- `tests/validate-plugin.sh`: exit 0
- **既知の逸脱**: `gdd_stop_hook.py` は 1443 → 1549 行となり、コード健全性方針の目安（1500 行）を 49 行超過。`main()` 自体は増やしていない（426 → 424 行、削減方向。`def main()` 行から `if __name__` 行の直前までで計測）。3 ラウンドの Copilot レビュー対応（correctness / performance / data-integrity 上いずれも妥当な指摘）による正当な増分として、ユーザー承認済みの方針の例外条項（cohesive で分割が可読性を下げる場合の許容）を継続適用。dogfood 3 日観測完了後に `done` とする（正本 作者の手元の分析ノート（非公開） §12 M-1）

### [0.16.3] - 2026-08-03

#### Summary

GDD 改善計画 M-2（replay corpus の拡充）。GDD scenario evals のメインコーパス（`evals/gdd-scenario-fixtures.json`、53 シナリオ）に対する replay 入力（`tests/fixtures/gdd-scenario-eval-inputs/*.assistant.md`）を、実質 1 件から 5 件へ拡充した。R9-2 pilot 設計が要求する「5 件」を満たす。contract 変更は無い。

#### Added

- `root_cause_three_cycle_repair.assistant.md` / `.worklog.md`: root-cause-investigation の 3 cycle 仮説検証ループを検証する replay 入力
- `hitl-decision-packet-ac1-where-full.assistant.md`: human-check-template.md の WHY/WHAT/HOW/WHERE/検証/自律範囲 6 見出しを検証する replay 入力
- `hitl_option_verification_plan.assistant.md`: Option 定義と検証計画（どこで/どう確認/OK条件/失敗時の扱い）を検証する replay 入力（`goal_human_check_decisionable_what_how_verification` は synthetic origin で実 session が無いため、実 session のある本シナリオへ差し替え）
- `brainstorm_to_gdd_pr_completion.assistant.md`: pre-workflow brainstorming から formal GDD Go への遷移で PR 作成までのスコープが保持されることを検証する replay 入力

#### Fixed

- 既存 replay 入力 2 件のうち `branch_only_steering_post_merge_continuation.assistant.md` はメインコーパスではなく別 corpus（`tests/fixtures/gdd-steering-retention-scenarios.json`）専用だったと判明。記録上「2 件」だったメインコーパスの有効な replay 入力は実質 1 件のみだった

#### Validation / Eval Impact

- `scripts/run-gdd-scenario-evals.py --fixture evals/gdd-scenario-fixtures.json --input-dir tests/fixtures/gdd-scenario-eval-inputs` で 5 シナリオとも critical checklist 全 pass（accuracy 100%）を確認
- `pytest`: 807 passed, 620 subtests passed
- `tests/validate-plugin.sh`: exit 0

### [0.16.2] - 2026-08-01

#### Summary

R9-2 Wave 1: GDD ワークフロー実行時に注入される hot references 4 本と skill 4 本を、契約の意味を変えずに蒸留し、削減後の実測値でバジェット 7 値を**減少方向のみ**にラチェットした（引き上げ 0 件）。あわせて、R9-2 の AC-7（バジェット引数の 2 箇所同期）を人手確認ではなく自動テストで守るようにした。

> 本エントリは R9-2 Wave 1（PR 旧#194、version bump なしで `[Unreleased]` のままマージ）と、その completion-check で Medium 指摘だった回帰テスト追加をまとめて 0.16.2 として確定したもの。

#### Added

- `tests/test_runtime_budget_arg_sync_contract.py` を追加した。`scripts/lint-runtime-budget.py` を呼ぶ 2 箇所（`tests/checks/skill-body-budget.sh` / `tests/checks/lint-scripts-functional.sh`）から `--max-*` 6 引数の値を抽出し、片方だけ変更されていれば fail する。R9-2 では `diff <(grep -A7 ...) <(grep -A7 ...)` を人手で実行して同期を確認していたが、自動テストが無く、片方だけ引き下げても CI が通る状態だった。

  生の `grep -A7` の diff は空にならない（`skill-body-budget.sh` 側は `required_files` 配列にも同名パスを持ち、`--quiet` 行の末尾処理も 2 ファイルで異なる）。そのため実行行（`"$PYTHON_BIN" ... lint-runtime-budget.py`）だけを対象に、行末 `\` の継続を連結してから値を抽出して比較している。上限値そのものは固定していない（引き下げ自体は正当な変更で、守る契約は「2 箇所が同時に動くこと」だけ）。

#### Changed

- hot references 4 本と skill 4 本を蒸留した。蒸留前後の実測は次のとおり。

  | 対象 | 前 | 後 | 行削減率 | 推定トークン（前 → 後） | トークン削減率 |
  | --- | --- | --- | --- | --- | --- |
  | `references/state-machine.md` | 841 行 | 792 行 | −5.8% | 18,760 → 17,799 | −5.1% |
  | `references/phase-progression.md` | 697 行 | 677 行 | −2.9% | 12,951 → 12,799 | −1.2% |
  | `references/human-check-template.md` | 773 行 | 773 行 | 0% | 10,641 → 10,641 | 0% |
  | `references/requirements-template.md` | 721 行 | 693 行 | −3.9% | 12,042 → 11,195 | −7.0% |
  | `skills/root-cause-investigation/SKILL.md` | 644 行 | 541 行 | −16.0% | 6,340 → 6,294 | −0.7% |
  | `skills/gdd-writing-skills/SKILL.md` | 590 行 | 558 行 | −5.4% | 5,247 → 5,091 | −3.0% |
  | `skills/gdd-systematic-debugging/SKILL.md` | 484 行 | 463 行 | −4.3% | 6,980 → 6,665 | −4.5% |
  | `skills/gdd-brainstorming/SKILL.md` | 352 行 | 312 行 | −11.4% | 8,731 → 8,021 | −8.1% |
  | **合計** | **5,102 行** | **4,809 行** | **−5.74%** | **81,692 → 78,505** | **−3.90%** |

  > 表の基準: **行数列は body 行**（frontmatter を除く）、**推定トークン列は全文基準**（frontmatter 込みの `ceil(len(text)/4)`）で、2 列の基準は一致していない。監査シートは body 基準で記録しているため、skill 4 本のトークン値は監査シートと 36〜46 トークンずれる。body 基準で揃えた場合の合計は **81,523 → 78,335 = −3.91%** で、結論（削減率は約 −4%）は変わらない。

- バジェット 7 値を蒸留後実測値 × 1.02（承認された余裕率 +2%。`design.md` D-5 Amendment 2）へ引き下げた。

  | 上限 | 現行 | 実測 | 新値 |
  | --- | --- | --- | --- |
  | `--max-skill-body-lines` | 650 | 558 | **570** |
  | `--max-total-skill-body-lines` | 7500 | 7021 | **7162** |
  | `--max-express-template-lines` | 200 | 182 | **186** |
  | `--max-standard-template-lines` | 850 | 799 | **815** |
  | `--max-express-estimated-tokens` | 33600 | 32811 | **33468** |
  | `--max-standard-estimated-tokens` | 57600 | 56011 | **57132** |
  | `references/` 合計行数 | 13128 | 12183 | **12427** |

- `skills/gdd-brainstorming/SKILL.md` が 312 行となり `MAX_SKILL_BODY_LINES=350` を満たしたため、`tests/checks/skill-body-budget.sh` の例外リスト 2 関数（`skill_body_reduction_plan` / `skill_body_baseline_lines`）から削除した。残る 3 件（`root-cause-investigation` 541 / `gdd-writing-skills` 558 / `gdd-systematic-debugging` 463）は baseline を実測値へ引き下げ、未達理由を script のコメントに明記した。**承認時の最終状態は「例外リストが空」だったが、本 Wave はそこに到達していない**（3 件残存）。未達理由は「意味保存を優先した判断」であり到達不能ではない（貪欲 set cover で 177〜180 行への圧縮が構成的に確認済み）。この着地で締めることは人間の再承認を得ている。

#### Fixed

- 検証ツール（AC-1 のアンカー照合器）自体の fail-open を**計 7 件**検出・修正した。いずれも「読み手が 1 つの厳密な形しか認めず、書き手は複数の形で書く」型で、検査は走っているのに実質何も見ていない状態だった。内訳は次のとおり（すべて bash 版に由来する。うち 1 件は 旧#6 の修正自身が持ち込み、Python への構造書き直しで解消した）。

  | # | 内容 |
  | --- | --- |
  | 1 | マッチ 0 件の `grep` が `set -euo pipefail` で集合 (3) の走査を silent に打ち切る |
  | 2 | `[[ "$line" == \#* ]] && continue` が集合 (1) の見出し 39 件を丸ごと未照合にする |
  | 3 | `verify` が anchors ファイル不在でも 0 回ループのまま `ANCHOR_VERIFY_OK` に到達する |
  | 4 | `extract` の非アトミック書き込みで anchors.txt が truncate され、その残骸を 0 件照合が pass させる |
  | 5 | `## SET ` の前方一致がラベル 1〜5 に限定されず内容行と衝突する |
  | 6 | 字下げフェンス・字下げ見出し・小文字 `step` の被覆漏れ |
  | 7 | `--allow-missing` の非対称読み（照合は `#` 行にマッチするがカウントからは除外）。**旧#6 の修正自身が持ち込んだ**同型欠陥で、Python への書き直しで解消 |

  Python 化後にも 3 件（SET 3 の nested quote 取りこぼし / 条件 2 の回帰ケース欠落 / `present()` 大小文字区別の回帰ケース欠落）を検出・修正しているが、これらは **under-extraction と回帰ケース欠落であって fail-open ではない**ため上表には数えていない。

#### Honest Limitations（測定できないこと・分かったこと）

- **設計時の前提「約 5,000 → 約 2,000 行（−60%）」は誤りだった。** 8 対象合計の実績は body 行 5,102 → 4,809 の約 **−5.7%**（想定 −60% の約 1/10）。これらは契約文書であって解説文書ではなく、削れる散文がほとんど存在しなかった。この前提の誤りは承認された余裕率を +5% から +2% へ改定する直接の原因になった（+5% では 7 値中 4 値が現行上限を上回り、ラチェットが成立しなかった）。
- **行数削減とトークン削減は別物。** `skills/root-cause-investigation/SKILL.md` は行数 −16.0% に対し推定トークン −0.7% で、実質的な context 削減はほぼゼロだった。行数だけを成果指標にすると実態を誤認する。**本 Wave の目的は実行時に注入されるトークンの削減なので、成果指標は上表の「トークン削減率」の合計行を見ること**（行数の合計行ではない）。
- `references/human-check-template.md` は削減 0% で着地した。
- **蒸留前後の文面に対する LLM の解釈差は決定論的に測定できない。** 逐語照合 subagent による外部証跡（AC-3）で補っている。
- **アンカー照合の pass は「契約が保全されている」ことの証明ではない。** 照合器の存在判定はファイル全体に対する**部分一致**で、行境界も文脈も見ない。そのため「アンカー文字列は残っているが、それを含む文の規範性が変わっている」型の変化を原理的に検出できない。盲点の実測値は `requirements-template` で 201/559 = **36.0%**、`human-check-template` で 210/585 = **35.9%**（対象により 29〜36%）。実際に本 Wave でも、`gdd-brainstorming` の 2 箇所（判定主体 `reviewer / 人間が` の脱落と `Design Policy Discussion` の総則の格下げ）がこの盲点を通過し、機械照合は pass したまま規範が弱まっていた。**AC-3 の逐語照合（人手・subagent による全削除行の突き合わせ）はこの盲点を埋めるための補完であり、機械照合の重複ではない**。後続 Wave が「`verify` が通ったから意味は変わっていない」と読み替えないこと。
- **AC-1 の「アンカーが 100% 存在する」には承認済みの例外が 2 件ある。** `references/phase-progression.md` で、原本 L556-560 の例に含まれる `Origin Steering:` / `Parent Hotfix:` の 2 行を意図的に削除しており、`--allow-missing` の allow list で宣言している（`verify` の出力は `597 anchors checked, 0 unexpected missing (2 allowed)`）。削除理由は「この例が同じ節で定義される value grammar を満たしておらず規範と矛盾していた」ためで、規範 bullet と上位互換の例は蒸留版に現存する。宣言の正本は `docs/audits/r9-2-phase-progression-allowed-missing-v2.txt`。他の 7 対象の allow list は空。
- 本 Wave が恒久追加した文書量は runtime body の削減量を上回る。runtime body を 293 行削る代わりに、archive 5,122 行 / anchors manifest 約 6,475 行 / 監査シート約 1,838 行 / 照合器 1,081 行 = 約 +14,892 行を `docs/` 配下に追加している。`docs/` は runtime profile 外なので削減主張と矛盾はしないが、Wave を重ねると単調増加するため次 Wave 前に置き場を決めること。
- 原本 8 本は `docs/references-archive/` にコミット保全済みで、ロールバック手順を実証済み（AC-10）。**巻き戻しの手順は復元範囲によって変わる**。原本 1 本だけを復元する場合は引き下げ後の上限に収まるため `git revert` は不要（`references/state-machine.md` の原本 841 行を復元した実測で references 合計 12,232 ≤ 12,427 / `validate-plugin.sh` exit 0）。8 本すべてを復元する場合は skill body 合計が 7,217 > 7,162 となって落ちるため、「原本復元 + バジェット引き下げコミットの `git revert`」の 2 手順セットが必要になる。

#### Affected Files

- `references/state-machine.md`, `references/phase-progression.md`, `references/requirements-template.md`（`references/human-check-template.md` は蒸留対象だったが**本文を 1 バイトも変更していない**ため実際の変更ファイルには含まれない。archive 原本とバイト同一）
- `skills/root-cause-investigation/SKILL.md`, `skills/gdd-writing-skills/SKILL.md`, `skills/gdd-systematic-debugging/SKILL.md`, `skills/gdd-brainstorming/SKILL.md`
- `tests/checks/skill-body-budget.sh`, `tests/checks/lint-scripts-functional.sh`, `tests/test_runtime_budget_arg_sync_contract.py`（新規）
- `docs/references-archive/*-pre-r9-2-wave1-original.md`（原本保全）, `docs/audits/r9-2-*-audit-20260729.md`（監査シート）, `docs/audits/r9-2-anchor-tools.py`（AC-1 のアンカー抽出・照合器）, `docs/audits/r9-2-*-anchors*.txt`（アンカー分母）, `docs/audits/r9-2-phase-progression-allowed-missing*.txt`（承認済み欠落の宣言）

#### User Action Required

- なし（契約の意味は変えていない）。ただし `references/` や `skills/*/SKILL.md` を今後追記する際、上限が 7 値とも引き下げられているため headroom が小さい（例: `--max-express-template-lines` は 4 行）。追記時は等価な親テキストの削除・統合を先に行う。
- **`skills/gdd-brainstorming/SKILL.md` は例外リストから外れたため、351 body 行で `SKILL_BODY_BUDGET_EXCEEDED` にハード fail する**（headroom 38 行）。例外リストに残る 3 件と違って baseline による猶予がないので、追記する場合は同量を削るか references へ移すこと。

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`: exit 0
- `python3 -m pytest tests/ -q`: 807 passed, 615 subtests passed（R9-2 Wave 1 を `main` に取り込んだ後の実測値。Wave 1 単独ブランチでの実測は 790 passed, 607 subtests passed だった）
- `tests/test_runtime_budget_arg_sync_contract.py` は、`lint-scripts-functional.sh` 側の `--max-skill-body-lines` だけを 570 → 580 に変えた状態で実際に fail することを確認済み（確認後に値を戻し、`git diff` が空であることを確認）
- 上限の実効性は **7 値すべて**で実測済み（上限ちょうどは exit 0、+1 単位で exit 1）。`571 > 570` / `7163 > 7162` / `express 187 > 186` / `standard 816 > 815` / `33469 > 33468` / `57133 > 57132` / `REFERENCES_LINE_BUDGET_EXCEEDED: 12428 > 12427`。実測後は全ファイルを復元し `git status` clean を確認
- `docs/audits/r9-2-anchor-tools.py` は 22 ケースの `selftest` を内蔵するが、`tests/` / `scripts/` / `.github/` のいずれからも呼ばれていない（回帰検知の対象外）。後続 Wave で再利用するなら `tests/checks/` から `selftest` を呼ぶこと

### [0.16.1] - 2026-07-30

#### Summary

v0.16.0 に対する Copilot レビュー（PR 旧#191）で指摘された hook の欠陥 3 件を修正する。いずれも「大半のケースでは動くが、特定の入力で静かに間違う」型で、実測で再現を確認してから直した。

#### Fixed

- **write hook の deny が散文で fail-open する**: `validate-steering-write.py:has_state_field` は `f"{field}:" in text` の単純な部分文字列検索だったため、本文の散文に `Next Action:` という文字列が含まれるだけで「field が存在する」と誤判定し、Tier 1 field 欠落の deny が抜けていた
  - 再現: `has_state_field("次のターンでは Next Action: を必ず記録すること。", "Next Action")` → `True`（同ファイルの `state_field_value` は同じ入力で `''` を返す）
  - 同一ファイル内で存在判定と値取得の読み取り規約が割れていたのが原因。行頭アンカー付きパターンを `state_field_pattern()` に切り出し、`has_state_field` / `state_field_value` / `has_started_at` / `state_requires_started_at` の 4 つをすべてそこに揃えた
  - 検査の trigger（`state_requires_started_at`）も同時に揃えている。trigger だけ緩いままだと「散文で trigger され、アンカー済み検査で欠落と判定される」非対称が生まれ、正常な書き込みを誤って deny する
  - 副産物として `Next Action : value`（コロン前に空白）のような表記も認識するようになった。旧実装は取りこぼしていた
  - **値のない field 行は「存在する」と数えない**（PR 旧#193 レビュー指摘）: prefix の有無だけを見ると `Resume From:`（値なし）が present になる。read 側は `[[ -z "${_value// /}" ]]` で空値を missing 扱いするため、write 側が通すと「書けたのに読み取り側で invalid」という同じ構図の非対称が残る。存在判定を値取得そのものに委ねて塞いだ
  - 併せて区切り文字の後を `\s*` から `[ \t]*` に変更した。`\s` は改行も食うため、値のない `Resume From:` の値として**次行の内容**を拾っていた（v0.16.0 以前から存在。値の有無で判定するようにすると、そのまま「空値なのに present」の抜け道になる）
  - **trigger は値の有無を問わない**（PR 旧#193 レビュー指摘）: trigger（`state_requires_started_at`）と充足検査で必要な条件は違う。trigger は「routing field に触ったか」なので、読み取り規約は充足検査と揃えつつ値の有無は問わない。ここまで値必須にすると、routing field を**空値に更新する**書き込みが trigger をすり抜けて Tier 1 検査が走らなくなる。`has_state_field_line`（行の有無）と `has_state_field`（値付き）を別述語に分けた
  - **既知の制約**: 判定対象の「既存ファイル内容 + 書き込み chunk」という連結は書き込み後のファイルではないため、field の削除・空値化を表現できない。既存ファイルに旧値が残っていると、その field を空値に更新する Edit は連結後の文字列に旧値が残るため通る。正確に見るには payload を適用した結果テキストで判定する必要があり、別途の設計変更になる
  - **実データ影響**: `.steering/*/state.md` 126 件で v0.16.0 実装と並走比較し、deny 判定・値取得・canonical tasklist 判定・trigger 判定のいずれも差分 **0 件**。新規 deny は発生しない
- **UserPromptSubmit hook が日本語 field で JSON を壊す**: `run-user-prompt-submit-hook.sh` の `Approved Direction` / `Last Handoff Summary` を `${var:0:512}` で切り詰めていた。bash の substring 展開は locale 依存で、`LC_ALL=C` やロケール未設定では**バイト単位**になり、日本語の UTF-8 シーケンスを途中で切って additionalContext の JSON を壊していた
  - 再現（実測）: `LC_ALL=C` → JSON BROKEN（invalid continuation byte）/ ロケール未設定 → JSON BROKEN / `LC_ALL=ja_JP.UTF-8` → OK
  - どちらも日本語自由記述 field で、512 バイト = 日本語約 170 文字なので超過は現実的。引用符・バックスラッシュのエスケープは既に正しかったので、残る穴は文字境界の切断のみだった
- **SessionStart hook も同じ切り詰めで JSON を壊す**: `run-session-start-hook.sh` の compact 自動復帰プロンプトが同型。`Approved Direction` / `Last Handoff Summary` に加えて `Next Action` も対象で、実データには `human-check-waiting（recall gap 調査を…）` のような全角混じりの値が存在する（128 バイト = 日本語約 42 文字）

#### Changed

- **長さ上限の単位がバイトから文字になる**: `gdd_truncate_chars`（`hooks/scripts/lib/detect-steering.sh`）を追加し、additionalContext / systemMessage へ注入する前の長さ制限をすべてこの helper に統一した。同じ `512` でも日本語の許容量が増えるため、日本語 field の注入量は最大 3 倍（512 バイト → 512 文字 ≒ 1536 バイト）になりうる
  - 実装は python3 で文字単位に切る。python3 が無い環境では multibyte を含む値を切らずに返す（列幅より値の完全性を優先する `scripts/find-stale-steerings.sh` と同じ「壊すより残す」方針）
  - 統一対象は `run-user-prompt-submit-hook.sh` の 2 箇所と `run-session-start-hook.sh` の 7 箇所。同じ sanitize パターンで一部だけ byte 切りが残る状態を避けるため、指摘された field 以外も揃えた

#### User Action Required

- なし。既存の state.md はそのまま動く
- 散文に `Next Action:` 等を書いて deny をすり抜けていた state.md があれば、次の書き込みで正しく deny される（実データ 119 件では該当なし）

#### Validation / Eval Impact

- `tests/test_state_field_anchoring_contract.py`（新規・8 ケース）: 散文の誤判定・実データ表記の網羅・存在判定と値取得の一致・deny の fail-open
- `tests/test_hook_multibyte_truncation_contract.py`（新規・3 ケース / 6 subtests）: 両 hook を `LC_ALL=C` / ロケール未設定 / `ja_JP.UTF-8` の 3 条件で実行し、出力が UTF-8 として妥当な JSON であることと切り詰めが効いていることを検査
- `pytest tests/`: 789 passed → **800 passed**（1 skipped、613 subtests passed）
- `tests/validate-plugin.sh`: exit 0

### [0.16.0] - 2026-07-28

#### Summary

v0.15.0 の改善が「入れたのに効かない」状態だった 2 つの silent failure を修正する。どちらも**読み手が厳格・書き手が緩い**構図で、大半の処理は動くため気付かれずに gate 判定だけが false になっていた。実データ 84 件の `.steering/*/state.md` で修正前後を比較検証した。

#### Fixed

- **PreCompact hook がリスト形式の field を取りこぼす（G-6）**: `sed 's/^Status:.*/Status: paused/'` が行頭限定のため、`- Status: <値>` 形式では置換されず末尾に追記され、同じ field が 2 行並んでいた。SessionStart 側の `gdd_extract_doc_field` は最初の行を読むので自由記述の値が返り、`Status == "paused"` 判定が false になって **compact 自動復帰が発火しなかった**（実データに 10 件）。`Status` / `CompactSource` / `PausedAt` の 3 箇所と、SessionStart 側の `CompactSource` 削除の計 4 箇所を `gdd_extract_doc_field` と同じ正規化に揃え、プレフィックスは capture group で保持して markdown list を壊さないようにした。既に重複している state.md は全行が `paused` に置換されて自動復旧する
  - 再現（他条件を固定し `Status` の書式のみ変えた比較）: 修正前は list 形式で発火せず / 行頭形式で発火。修正後は**両方とも発火**
  - この修正は v0.15.0 の compact 復帰プロンプト改善（context field 注入）が届く前提条件にあたる
- **gate 判定が実データ多数派を取りこぼす（G-9）**: `gdd_check_3field_gate` は `Requirements Review Status=` を grep する **`=` 限定**だったが、汎用の `gdd_extract_doc_field` は `:` と `=` の両方を受け付ける。実データは `:` 形式 35 件 / `=` 形式 21 件で多数派がすり抜け、`GDD_TASKLIST_CANONICAL` が false のままだった。gate 判定を `gdd_extract_doc_field` に統一した
  - 効果（実データ 84 件・修正前後比較）: canonical と判定される task が **14 → 34（+20）**
  - ただし canonical は必要条件であって十分条件ではない。plan-reread hook には task 名の形式依存が別にあり、そちらは下記 G-11 で解消した
- **G-12: 別セッションで再開したときの context 引き継ぎ（G-1 の対称的な穴）**: G-1 は compaction 後の復帰プロンプトに `Approved Direction` / `Last Handoff Summary` を注入するようにしたが、**別セッション（新しいチャット）で再開する経路**に同じ手当が無かった。SessionStart の active steering パスは routing 指示（「state.md を workflow owner として使え」）しか出さず state.md の中身を注入しない。UserPromptSubmit が active steering の context を組み立てる唯一の場所だが、Goal / Current Task / AC / Next Action / Route In Progress までで、「何をしていたか」と「どの方針で承認されたか」が欠けていた
  - UserPromptSubmit に compact 復帰と**同じ 2 field**を同じ扱い（空なら行ごと省略・512 文字 cap・制御文字除去）で追加した。会話履歴が丸ごと無い分、別セッションの方が compaction 復帰より引き継ぎの必要性は高い
  - **注記**: `Last Handoff Summary` は実測 1/77 のため、この注入は現状ほぼ空を読む。配線は 4 つの境界（compaction / subagent / worktree 発見 / 新セッション）すべてで揃ったが、**中身が入るのは G-2 の促しが効き始めてから**

- **R9-4: モデル世代監査の定常運用を明文化**: `docs/VERSIONING.md` に「モデル世代監査」節を追加。メジャーモデル更新をトリガーに R9-2 相当（実行時ロードの実測 → 4 値ルーブリック → replay eval）を回す運用ルールと、比較対象の 2026-07-16 ベースライン（注入が top 8 に約 77% 集中 / Read ゼロ 10/66 / 1 セッション平均約 2,100 行）を記録した
  - この plugin は AI エージェント向けの指示文書であり、旧モデル向けの補正・過剰規定はモデル世代が上がっても自動では消えず堆積する。1 回蒸留して終わりにすると同じ状態に戻るため保守イベントとして定常化する
  - 判断原則として「**静的な参照数を実行時ロードの代理指標にしない**」を明記（10 skill から引用されるのに実行時ロードがほぼゼロだった実測がある）
  - `retrospective-codify` skill は user-level（`~/.claude/skills/`）で plugin 外、かつ「タスク完了時の学びを codify する」という別目的のため**組み込まない**判断とした。運用ルールの正本は `VERSIONING.md` 単独に置く

- **S-2: worktree 横断レジストリ（`find-stale-steerings.sh --registry`）**: 実測で `~/.gdd/worktrees` に 40 worktree、うち origin/main にマージ済みで残存 28 件、未コミット変更あり 20 件。既存の stale 検出は「`Started At` が N 日超 **かつ** `Resume From=gdd-brainstorming`」＝ planning 序盤で放棄されたものしか拾わず、実測の停止分（`gdd-completion-check` / `human-check-waiting` ＝ 完了間際）が検出対象外だった。スコープも current worktree 止まりで、実測は 9 リポジトリに分散していた
  - **走査は `.git` の存在で判定する**。深さ固定の glob（`~/.gdd/worktrees/*/*`）だと branch 名に `/` を含む worktree（実測 4 件が `fix/...`）を取りこぼす
  - 停止検出は `state.md` の **mtime** ベースに変更（`Started At` 基準では完了間際の停止を拾えない）
  - merged 判定は `git merge-base --is-ancestor HEAD origin/main`。`git branch -r --contains` は ref を全列挙するため 40 worktree では実用にならない。実測 **6.4 秒**で全件
  - **list only**。既存モードの archive / `rm -rf` 提案は付けない（停止分は完了間際、20 件が dirty で、削除を勧めてよい状態ではない）。既定モードは非退行
- **S-3: E-5 の効果は既存 artifact から測定不能と判明**（調査のみ・コード変更なし）。`Bounce Log` 0/91、`Review Calibration` 0、telemetry の Fix Attempts 0。`gdd-metrics` の集計自体は動作するが対象データが存在しない。0 の解釈が「差し戻しが起きていない」か「記録されていない」か区別できず、E-5 の効果判定は保留とした。詳細と次の一手は改善計画に記録

- **S-1: subagent 境界で次段に引き継ぐ実測値を定義（`Carry Forward`）**: `P1-4` は「task N の実装詳細は subagent の文脈ごと破棄される」ことを**利点として**明記している。破棄自体は正しいが、破棄しないものが「tasklist 更新 + Handoff Summary」としか定義されておらず、次段が必要とする実測値がどこにも残らなかった。結果、次段が同じ調査をやり直すか誤った前提で実装していた
  - `tasklist.md` の task entry に `Carry Forward:` 欄を追加。**選択基準は「次段がそれを知らないとブロックされる / 誤った前提で進む」もの**だけで、「あると便利」は書かない。種別は 確定した実測値 / 名前・場所 / 実行時に判明した制約 / **未解決の申し送り** の 4 つ
  - **供給 → 記録 → 消費の 3 点を繋いだ**: 供給は subagent の `Expected output`（この報告が唯一の供給源で、出なかった事実は境界の破棄後に復元できない）、記録は Step 12b（`Completed Tasks` へ移す前の**既に必須の手順**）、消費は Subagent Prompt Contract（**直近 1〜2 task 分のみ**渡し、他 task の実装詳細は渡さないので `P1-4` の破棄方針を打ち消さない）
  - **保存先に `findings.md` を使わない**: 実測の存在率 6%、`Last Handoff Summary` は 1.3%。「指示するだけでは書かれない」ことが実測済みのため、既存手順の中で書かれる `tasklist.md` を選んだ
  - 行数上限（1 task 5 行程度）は書きすぎの検知用で、**抑制の根拠にしない**。次段がブロックされる情報は上限を超えても省略しない旨を明記
  - 効果は次の実 GDD run まで観測できない（subagent が受け取る内容の変更のため）

- **F-2 の doc-check を追加**: F-2（express impl-gate の advisory 化）は v0.14.0 で実装済みだが、仕様書が「テスト・手順」で要求していた doc-check が入っていなかった。`post-completion-pr-flow.md` は **silent drop の検出が見出し文字列の厳密一致に依存する**と明記しているのに、同じ見出し `## Advisory Findings (Express Impl-Gate)` が writer（`gdd-implementation-gating/SKILL.md`）・定義（`state-field-tiers.md`）・reader（`post-completion-pr-flow.md`）の 3 ファイルにハードコードされたまま同期を守るテストが無かった。文字列同期、fail-closed 集合（`High` + `ops-blocking medium`）の非退行、`express_promotion_required` 優先、および `approved(advisory)` という新 status 値が**導入されていないこと**を契約テストで固定した
  - 実装は仕様書の当初案（`approved(advisory)` を新設）を採らず、`gate-status-schema.md` の既定許容値のまま advisory の有無をセクション記録で表す方針を選んでいる。古い仕様書の記述から再導入されないよう不在を pin した

- **`Next Action` の欠落を write 側でも塞ぐ（G-8）**: 実データでは `Next Action` が state.md / tasklist.md の両方で欠落しているものが 38% あった。G-9 で read 側は fail-closed するようになったが write 側は無検査のままで、「書けてしまってから止まる」構図が残っていた。canonical tasklist phase（3 gate approved + tasklist.md あり）でだけ必須にする conditional 検査を追加した
  - 保存先は state.md / tasklist.md の**どちらでもよい**（read 側の decoupling と揃えないと、routing source を持っている task を write 側だけが弾く）
  - **既存の `state_core_fields` category に統合**し、新しい deny category は作らない。メッセージが 2 本に割れると 1 回の書き込みで直せず、`MAX_CONSECUTIVE_DENIES` の escape hatch を無駄に消費するため
  - G-7 で `Status` に deny を追加しなかったのと判断が分かれるのは、**`Next Action` は routing source で、欠落すると復帰時に次の行動を決められない**のに対し、`Status` は hook 所有で値が次の compaction に上書きされるため。enforce するのは routing に効く field だけに絞る

- **plan-reread hook が task 名を取れず silent exit する（G-11）**: `## Current Task` 節から `[[ "$line" == "### Task:"* ]]` の厳密一致で task 名を取り、空なら hook 全体が exit していた。正本 `task-breakdown-steps.md` のテンプレートは `### Task: T-1 <name>` なので hook は正本に忠実だったが、**実データの Current Task 節にこの形式は 0 件**で、多数派は `### Task <N>: <name>`（13 件）と `- Task: <name>`（9 件）だった
  - `### Task: X` / `### Task <N>: X` / `#### Task <N>: X` / `- Task: X` を受理する正規表現に変更
  - AC 行も同様に `- Covers AC: AC-2, AC-5` を受理するようにした。`task-breakdown-steps.md` が「既存 artifact に `Covers AC:` が残っている場合は **legacy alias として読んでよい**」と明記しているのに hook が読めていなかった
  - 効果（実データ 69 件の tasklist.md）: Current Task 節に実際の task が書かれている **22 件すべて**で task 名を取れるようになった（修正前 **0 件**）。残る 36 件は `None.` / `（全 Task 完了）` / `1. Human check for ...` など **task が存在しない**ケースで、注入しないのが正しい挙動
  - `task-breakdown-steps.md` に正準形（`### Task: <ID> <name>`。連番は見出しでなく Task ID 側で表現）と、形式が崩れると注入が silent に止まることを明記した

#### Changed

- **`Next Action` を tasklist.md / state.md のどちらからでも受け付ける（G-9 の副作用緩和）**: 設計上の routing source は build phase では tasklist.md だが、実運用では state.md 側に書かれることが多い（実測 48/77）。tasklist.md 限定のままだと、区切り文字の正規化で新たに canonical になった task が routing source を持っているのに fail-closed していた。`state-schema.json` の `routing_source.build` も実態に合わせて fallback を明記
- **`Status` を hook 所有 field として定義（G-7）**: 許容値は `paused` のみ、不在が正常、書き手は PreCompact hook、読み手は SessionStart。skill / LLM は書かない（進捗は `Resume From` / `Next Action` で表現する）。`gate-status-schema.md` に節を追加し、`state-schema.json` § `hook_owned_fields` と `state-field-tiers.md` にも記載。**write hook への新規 deny は追加していない** — G-3 で deny category を 1 つ足したばかりで、free-text `Status` を持つ既存ファイルに 2 つ目を当てると `MAX_CONSECUTIVE_DENIES` の escape hatch が連発してノイズになるため、定義に留めて enforcement は見送った
- `state-schema.json` に `gate_field_delimiter`（書き手は `=`、読み手は両方を受理）を追加し、区切り文字の規約を明文化
- runtime profile のトークン上限を引き上げ（express 33500 → 33600、standard 57450 → 57600。実測 33521 / 57568）。S-1 の `Carry Forward` 追加分。`context-budget.md` は express profile に含まれ予算が厳しいため、carve-out の宣言だけを残し、判定基準・保存先・分量の正本は `task-breakdown-steps.md`（standard 側）に置く構成にした

#### Breaking Changes

- **G-9 により、これまで silent に canonical 判定をすり抜けていた task が gate 検査の対象になる**。実データ 84 件で検証したところ、新たに fail-closed するのは **1 task のみ**（`20260616-investigation-evals-ks-coverage`）。原因は `Next Action` が state.md / tasklist.md のどちらにも無いことで、routing source 欠落のため停止が正しい挙動。hook のエラーメッセージが復旧手順（`Next Action` の書き戻し）を案内する
- **G-8 により、canonical tasklist phase で `Next Action` を欠いた state.md の書き込みが deny される**。実データ 75 件の state.md に対して write hook を実行して検証したところ、新たに deny されるのは **2 task のみ**（`20260616-investigation-evals-ks-coverage` / `20260616-pr-review-fn-reduction`）。どちらも routing source が両ファイルとも無い状態で、deny が正しい挙動
- **G-6 により、free-text の `Status` 値は次の compaction で `paused` に上書きされる**。これは意図した挙動（値の意味論は「compaction で中断された」の 1 点のみで、進捗は `Resume From` / `Next Action` が持つ）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-compact-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/detect-steering.sh`
- `plugins/gate-driven-development/references/gate-status-schema.md`
- `plugins/gate-driven-development/references/state-schema.json`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/tests/test_pre_compact_hook.py`
- `plugins/gate-driven-development/tests/test_status_field_ownership_contract.py`（新規）
- `plugins/gate-driven-development/tests/test_gate_delimiter_normalization_contract.py`（新規）
- `plugins/gate-driven-development/hooks/scripts/run-pre-tool-use-plan-reread-hook.sh`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/tests/test_plan_reread_task_format_contract.py`（新規）
- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`（G-8 の conditional 検査）
- `plugins/gate-driven-development/tests/test_express_advisory_findings_contract.py`（新規・F-2 doc-check）
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`（S-1 schema）
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`（S-1 供給・記録・消費）
- `plugins/gate-driven-development/references/context-budget.md`（S-1 carve-out）
- `plugins/gate-driven-development/references/task-breakdown-steps.md`（S-1 正本）
- `plugins/gate-driven-development/tests/test_carry_forward_contract.py`（新規・S-1）
- `plugins/gate-driven-development/scripts/find-stale-steerings.sh`（S-2 `--registry`）
- `plugins/gate-driven-development/tests/test_worktree_registry_contract.py`（新規・S-2）
- `plugins/gate-driven-development/hooks/scripts/run-user-prompt-submit-hook.sh`（G-12）
- `plugins/gate-driven-development/tests/test_cross_session_handoff_contract.py`（新規・G-12）
- `plugins/gate-driven-development/docs/VERSIONING.md`（R9-4）
- `plugins/gate-driven-development/tests/test_model_generation_audit_contract.py`（新規・R9-4）

#### User Action Required

- `20260616-investigation-evals-ks-coverage` を再開する場合は、`state.md` に `Next Action` を書き戻してから進める
- 既存の state.md に free-text `Status` がある場合、手動修正は不要（次の compaction で自動的に `paused` になる）

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ -q`: **784 passed, 1 skipped, 607 subtests**
- `bash tests/validate-plugin.sh`: exit=0
- 実データ検証: 旧実装のコピーと新実装を 84 件の `.steering/*/state.md` に対して並走させ、canonical 14→34 / 新規 fail-closed 1 件を確認
- 実データ検証（G-8）: 75 件の state.md に write hook を実行し、新たに deny されるのが 2 task のみであることを確認
- 実データ検証（G-11）: 69 件の `tasklist.md` の Current Task 節に対し、task 名の抽出可否を修正前後で比較。実際に task が書かれている 22 件で 0 → 22 件
- **測定上の注意**: `.steering/` の実データは完了済み task が大半で `gdd_detect_active_steering` が `none` を返すため、**hook 本体を実データに対して走らせても注入は発生しない**（active steering でないため正しい挙動）。hook 単体の挙動は fixture ベースの契約テストで、実データに対する効果は形式適合率で評価している
