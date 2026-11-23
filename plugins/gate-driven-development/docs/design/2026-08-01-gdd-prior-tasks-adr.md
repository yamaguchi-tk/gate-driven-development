# ADR アーカイブ: 先行 GDD タスク 4 件

`.steering/` は git 追跡外で worktree 削除とともに失われるため、いずれもマージ済みタスクの steering から
**逐語でアーカイブした**（再要約による転記誤りを避けるため意図的にコピーのみ）。
本文中の `design.md` / `requirements.md` / `tasklist.md` への参照はアーカイブ対象外のため解決しない。

**逐語からの改変は 1 箇所のみ**: `20260628` の ADR-1 にあったプレースホルダのファイル名（`references/` 配下の架空の `.md`）を `references/<名前>.md` に置換した。`docs/**` を走査する `test_reference_integrity_contract.py` が、この例示を実在しない参照とみなして fail するため。元の名前も架空のプレースホルダなので意味は変わらない。

| タスク | ADR 数 | 主題 |
| --- | --- | --- |
| `gdd-self-healing-resume-gaps` | 5 | `auth-waiting` reason の追加と自己修復 resume |
| `20260628-gdd-investigation-rigor-improvements` | 2 | 調査・検証規律の構造的改善 |
| `20260712-hitl-decision-packet-e5-f3` | 4 | HITL Decision Packet（E-5 / F-3） |
| `20260724-f2-express-impl-gate-advisory` | 1 | express の impl-gate advisory 化（gate status の表現方式） |

---

## タスク: `gdd-self-healing-resume-gaps`


design-gating（2026-06-21）で確定した重要判断を蒸留する。承認済み Approved Direction（Option B / `auth-waiting` / reviewer unreachable は代替提案 pause）は変えず、機械強制の design 詳細を確定したもの。

### ADR-1: `auth-waiting` は output-format.md の 2 テーブルへも登録する（H1）

- **Context**: `gdd_stop_hook.py:558` の OT-F10 next-action 検査（`has_next_action_block` + `EXEMPT_REASONS=frozenset({"cancelled"})`）は、line 575 の非終端保持分岐より**前**に全 reason（`cancelled` 除く）へ走る。`auth-waiting` は exempt ではない。さらに `references/output-format.md` の `<gdd-stop reason>` 許容値テーブル（reason は「6 つのみ」と明記）と「👤 次にすること」マップに `auth-waiting` 行が無い。
- **Decision**: S-1 で output-format.md の両テーブルに `auth-waiting` 行を追加する。`<gdd-stop reason="auth-waiting">` は必ず `## 👤 次にすること` ブロックを伴う。AC-1 に両テーブル登録を、AC-2b に line 558 guard 通過 contract test を追加。
- **Why**: 行が無いと (i) marker 自体が未認識で autonomous continuation が走る、(ii) skill が next-action ブロックを付け忘れ初回 auth pause が `block` され「自走再開」の逆になる。許容値「6 つのみ」が正本記述なので明示更新が必要。
- **Consequences**: reason 総数 6→7。output-format.md が S-1 の影響範囲に追加される。次フェーズ task-breakdown は AC-1/AC-2b を S-1 タスクに含める。

### ADR-2: (3-b) は既存 `_find_tasklist_in_steering` を再利用する（M2 / DRY）

- **Context**: done-guard 経路の `_find_tasklist_in_steering`（gdd_stop_hook.py:487）は traversal-safe な hint_slug 優先 + reverse-sort fallback + terminal-skip を OT-F2 で既に硬化済み。progress 経路 `_find_tasklist_text_for_progress`（805-832）は tasklist の **text** を返す並行実装で、hint_slug 未適用・reverse-sort のみ。
- **Decision**: progress 経路を別実装で再パッチせず、`_find_tasklist_in_steering`（または `_find_active_tasklist` 相当）の返す Path を `.read_text()` する形で再利用する。S-3 design-gating でこの再利用を第一候補とし、採らない場合は理由を残す。
- **Why**: hint_slug/traversal guard（`".." in hint_slug` 等）/terminal-skip を二重実装すると 2 経路がドリフトし guard 取りこぼしのリスク。これは Architecture Option Matrix で reject 済みの「全 reverse-sort 一括共通関数化」とは別物（1 sibling helper の再利用で狭く低リスク）。
- **Consequences**: S-3（後続 PR）の実装方針。本 PR=S-1 では未着手。

### ADR-3: CT-5 を機械強制する（security M-1）

- **Context**: CT-5「認証情報を扱わない」は positive 構造（reason 集合・marker）しか test しておらず、秘匿値が pause 出力・`👤 次にすること`・`state.md` に混入しない negative 保証が無い。auth 失効の検知シグナル自体の安全性も未定義。
- **Decision**: (a) 検知シグナルは秘匿値を含まない（session/exit マーカー等、auth サーバ生応答本文ではない）と設計で固定。(b) token 形の偽文字列を含む fixture を与え、その値が auth-waiting 停止出力・next-action テキスト・永続 state.md のいずれにも現れないことを assert する negative contract test を AC-3 に追加。
- **Why**: CT-5 は本機能の中心 security 制約。目視 code-diff だけでは fail-closed を担保できない。「散文ルールでは AC 充足としない」原則と整合させる。
- **Consequences**: S-1 の AC-3 に negative test を含める。検知シグナルの実装は token-free に制約される。

### ADR-4: `auth-waiting` に wake 上限を設ける（security M-2）

- **Context**: `auth-waiting` は非終端で再ログイン待ち中に `ScheduleWakeup` を再 arm する。人間が永久に再ログインしないと無限再 arm になり availability/resource 懸念（「暴れる」失敗クラスの裏返し）。`external-review-waiting` には poll-cap があるが auth-waiting には無い。
- **Decision**: `auth-waiting` に bounded な max-wake / backoff（named/overridable 定数）を持たせ、上限到達時は silently 再 arm せず `blocked`（または 1 アクション提示）へ遷移。AC-3(d) で test-bind。
- **Why**: 非終端 pause の安全網。fail-closed を保ったまま無限ループを塞ぐ。
- **Consequences**: S-1 で定数 1 個追加と上限遷移 test。

### ADR-5: AC-7 の slug-source 確定と worktree-topology fixture は S-3 で行う（M1 deferral）

- **Context**: `_resolve_active_slug(cwd)` は `cwd/.claude/gdd-dev.local.md` を読むが、progress 経路は git worktree path を反復する。`proj_root` 直再利用だと空 slug → fallback 化しうる（AC-7 が対象とする症状の再現）。
- **Decision**: slug 取得元と worktree 反復の関係の確定、および「実 worktree topology を再現した fixture」は **S-3 follow-up PR の design-gating** で行う。本 PR=S-1 では対象外。
- **Why**: S-3 は方針のみ承認の後続 PR。本 PR の scope に引き込まない。Approved Direction（Option B）の範囲内。
- **Consequences**: 本 PR は S-1（AC-1/2/2b/3）に閉じる。AC-6/7/7b/8 は S-3 で具体化。

---

## タスク: `20260628-gdd-investigation-rigor-improvements`


### ADR-1: 改善 3（structural mismatch early-exit）の正本配置を phase-progression.md に置く

### Context
session 56b3bfd1 で「前提が崩れた eval を回数閾値まで反復した」問題が観測された。検証ループは `gdd-pr-review-followup`（PR 後 review ループ）と `references/phase-progression.md`（E2E Discovery Loop / Escalation Decision Table）の両方に存在し、structural mismatch early-exit 規律をどちらに置くかが承認ポイント 2 の論点だった。

### Decision
正本は `phase-progression.md` の Escalation Decision Table（既存に `planning_rework_required` 行あり）に「初回試行で前提崩壊（structural mismatch）を検知したら回数を待たず planning_rework_required」を追加し、`gdd-pr-review-followup/SKILL.md` の Escape Hatches（既存「same finding repeats >= 3」L183）からそれを参照する。followup 側には structural mismatch を attempt 1 で中断するオーバーライド節を追加し、既存の回数ベース規律は refinement 用として残す。

### Why
検証ループ規律を 2 箇所に重複記載すると DRY 違反になり、片方だけ更新される drift リスクがある。正本を phase-progression に 1 つ置き followup から参照する非対称構成が DRY と整合する。reference-integrity test は `references/<名前>.md` 形式のファイル解決のみ検証し `§ セクション名` アンカーは検証しないため、followup→phase-progression 参照の正しさは AC-3 の grep（`structural mismatch` を両ファイルで）で別途担保する。

### Consequences
- 良い影響: 規律が 1 正本に集約され、refinement（回数ベース継続）と structural mismatch（即時中断）の区別が明文化される。
- 制約: followup→phase-progression のアンカー参照は機械検証されないため、grep ベースの content-diff（AC-3）が検証の最終防衛線になる。

### ADR-2: Serena/LSP は今回不採用（評価記録のみ）

### Context
USC-6「Serena（LSP）で構造的に解決できるものがあれば導入を検討。runtime 文脈での利用価値を先に確認」。Serena MCP は本環境の deferred tools に存在（find_symbol / find_referencing_symbols 等、利用可能）。ただし観測事例で eval ハーネスが `--strict-mcp-config {}` で MCP を強制無効化する制約がある。GDD plugin 内の Serena 参照は現状 0 件。

### Why
- (a) GDD plugin 自体は markdown 中心で LSP 対象シンボルが薄く、Serena の価値は「GDD が支援する対象プロジェクト側」の調査に限られる。
- (b) eval 実行フェーズでは MCP が無効化されるため Serena は eval 文脈で利用不可。planning フェーズ（eval 前）なら使える可能性は残るが runtime 価値が未確証。
- 改善 1 の調査網羅性向上は、IDE 非依存で確実に効くプロンプト規律（既存 grep/Read の網羅性を上げる）で達成する方が確実。

### Decision
今回は Serena を採用せず、既存 grep/Read を維持する。評価結論（不採用 + 理由）を design.md § Serena 評価結論に記録する（AC-5 を満たす）。MCP 設定変更・GDD plugin への Serena 導入指示はしない。

### Consequences
- 良い影響: IDE（Claude Code / Cursor / Codex）非依存の静的プロンプトとして全 host で確実に機能する。
- 制約 / 再検討条件: Serena が実は有効だった場合の機会損失が残るが、AC-5 で評価を明文化して回避する。Serena が eval 文脈で有効と確認された場合は別 task で導入を再検討する（requirements.md § Adopted Technology Stack Trace の Recheck trigger）。

### 却下した代替案
- Serena 即導入: eval-MCP 無効化制約で runtime 価値が未確証のため却下。
- 改善 3 を followup skill 側に独立記載: DRY 違反のため却下。

---

## タスク: `20260712-hitl-decision-packet-e5-f3`


### ADR-1: escalation閾値の統一（2回）と Planning Loop Safety 既存文言の書き換え

- **Context**: human check（2026-07-12）で escalation 閾値をユーザー原文の「目安3回」からAI提案の「2回」（`gdd-completion-check` 既存閾値 `>=2` と整合）に変更することが承認された（Approved Direction 決定事項1）。設計具体化の過程で、`state-machine.md` の `Planning Loop Safety` 節（`gdd-brainstorming`/`gdd-requirements-gating`/`gdd-design-gating`/`gdd-task-breakdown` を対象）に既存の「同じ planning blocker が3回の review/edit cycle を超えて残る」という文言が既にあり、design.md 論点4 が「追記」としていた同一root causeカテゴリ検出ウィンドウと数値が矛盾する状態だった（gdd-planning-reviewer 指摘）。
- **Decision**: `Planning Loop Safety` 節の既存「3回」を「2回」に**書き換える**（追記ではなく置換）。同一root causeカテゴリの検出ウィンドウも「直近2回」に統一する。`gdd-implementation-gating` が参照する `Remediation Loop Safety` 節の「3回目のblind `implementation_fix_only`は許可しない」ルール（`Fix Attempts` カウンタが正本）は別節・別対象gate・別カウンタであり、変更しない。
- **Why**: 同一節に矛盾する2つの数値（3と2）を併存させると読み手が誤って適用範囲を混同するリスクがある。`Planning Loop Safety` の対象gateは決定事項1が指す4gateのうち3gate（design/requirements/task-breakdown、+brainstorming）と一致するため、節そのものを新基準に更新するのが最小差分かつ一貫性が高い。`Remediation Loop Safety` は対象gate・カウンタ主体（`Fix Attempts`）が異なるため、決定事項2（implementation-gatingの既存経路維持）により触らない。
- **Consequences**: `state-machine.md` 編集時に `Planning Loop Safety` 節と `Remediation Loop Safety` 節を混同しないよう、tasklist.md のタスク粒度で編集対象行を明示する必要がある。将来 escalation 閾値を再変更する場合、影響範囲が2節に分かれていることをタスク分解時に確認すること。

### ADR-2: gdd-implementation-gating への bounce-log-schema 配線は既存の Fix Attempts カウンタと独立させる

- **Context**: 決定事項2（案A・非対称escalation）により `gdd-implementation-gating` は新規escalation経路を持たず既存の `gdd-systematic-debugging` 経路を維持する方針だったが、design.md の影響範囲表・主要フローは「`gdd-completion-check/SKILL.md:179` と同型のbounce-log-schema配線を追加する」とのみ記述しており、この配線が `Remediation Loop Safety`（`Fix Attempts` 3回ルール）とどう関係するか未記載だった（gdd-planning-reviewer 指摘: 閾値`>=2`が3回ルールを実質的に前倒しで上書きしうるように読める）。
- **Decision**: `gdd-implementation-gating` に追加する bounce-log-schema 配線は、`task-id + reviewer指摘カテゴリ` を identifier-key とする**独立した**bounce log（`gdd-completion-check/SKILL.md:179` の `task-id + 欠落項目` と同型だが対象イベントが異なる）とし、`Remediation Loop Safety` の `Fix Attempts` カウンタとは別軸として扱う。閾値 `>=2` 到達時の遷移先は既存の `gdd-systematic-debugging`（新規destinationは作らない）。両者は最終的に同じ `gdd-systematic-debugging` に合流するが、それぞれ独立したtrigger条件として扱う。
- **Why**: 「reviewer が同じ指摘を繰り返す」（レビューループ）と「同じ修正を試みて失敗する」（デバッグループ）は異なる事象であり、同一カウンタで扱うと片方の閾値がもう片方の安全域を意図せず狭める。決定事項2の「新規escalation経路は追加しない」は destination（送り先）の話であり、trigger（引き金）を追加すること自体は許容範囲内だが、trigger同士の独立性を明記しないと `Fix Attempts` の3回猶予が実質2回に短縮されたように誤読される。
- **Consequences**: task-breakdown / 実装時に、`gdd-implementation-gating` の bounce log と `tasklist.md` の `Fix Attempts` を別々のフィールド・別々のリセット規則で管理すること（`bounce-log-schema.md` のライフサイクル表に準拠）。将来この2軸のどちらかを変更する際は、もう一方に波及しないことを設計段階で明示的に確認する。

### ADR-3: scenario eval fixture の追加先を `evals/gdd-scenario-fixtures.json` に統一

- **Context**: design.md 初版は新規fixtureの追加先を `tests/fixtures/` としていたが、requirements.md の Engineering Baseline / Completion Testability Matrix は `scripts/run-gdd-scenario-evals.py` + `evals/gdd-scenario-fixtures.json` を正本の実行harnessとして指定しており、`references/gdd-scenario-evals.md` の実測（fixture定義は `evals/gdd-scenario-fixtures.json`）とも一致しない矛盾があった（gdd-planning-reviewer 指摘）。
- **Decision**: 新規fixture（AC-1〜AC-8対応）はすべて `evals/gdd-scenario-fixtures.json` に追加する。`tests/fixtures/` 配下の既存 e2e-replay 等の別harnessとは混同しない。
- **Why**: 単一の release-gating harness を正本として一貫させることで、実装フェーズでのfixture配置の迷いとCI laneの二重管理を防ぐ（YAGNI: 新規harness/fixture置き場を増やさない）。
- **Consequences**: tasklist.md でCI lane（`--require-release-pass` / `--require-critical-pass`）の確定と、`evals/gdd-scenario-fixtures.json` への具体的な追加項目をタスク単位で明示する。

### ADR-4: AC-8の検証方式をLLM behavior判定から静的grep判定へ変更

- **Context**: AC-8（Broad Requirementでの段階的対話）はLLM behavior判定（fresh subagentをdispatchしbrainstorming手順を実際にロールプレイさせる）として計画したが、2026-07-13〜14に5回連続でdiscriminatingなRED fixtureの確立に失敗した（3種の構造的に異なる失敗機構: Step2a/Pre-option Scope Narrowingへの収束、Step7 trivial判定によるStep9到達阻止、bullet-3到達後の出力フォーマット未定義）。
- **Decision**: ユーザー明示承認により、AC-8の検証をAC-1/AC-2/AC-3と同型の静的テキスト存在確認（`brainstorming-steps.md`にF-3相当の指示文言が追加されたことを直接grepで確認するcontract level検証）に変更する。CI laneも`--require-release-pass`から`--require-critical-pass`（AC-1/2/3/6と同じ静的grepレーン）に変更する。
- **Why**: 5回の実測が一貫して示したのは、fixture設計の不備ではなく「baselineがbulk Options Exploration dumpという不具合を持つ」という前提自体を、brainstorming-steps.mdの現行構造下でLLM behaviorとして再現できないという構造的知見。これ以上のLLM挙動ベース試行はコストに対して収益が見込めないため、AC-1/2/3と同じ検証水準（false-pass risk低、ただし「文言追加」までしか検証しない）に揃える。
- **Consequences**: AC-8はF-3実装が実際にLLMの対話挙動を変えるかまでは検証しない（Honest Limitationsとして明示）。tasklist.md T-3のfixture・requirements.md Verification Sanity Check / Completion Testability Matrixを本ADRに合わせて更新済み。

---

## タスク: `20260724-f2-express-impl-gate-advisory`


### 2026-07-24: impl-gate advisory 化の gate status 表現方式を修正（impl-gate remediation F1/F2/F3）

- **Context**: 実装完了後の impl-gate（Opus subagent, `gdd-implementation-reviewer`）レビューで `changes_requested` を受けた。指摘は 4 件（F1〜F4）。
  - F1: `skills/gdd-implementation-gating/SKILL.md` の express carve-out バレットに埋め込んだ自己参照行番号（`L90` / `L76` / `L309` / `L106-116, L190` / `L111-113` / `reviewer-common.md L67-81`）が、同バレット挿入自体で後続行がシフトしたためズレていた。
  - F2: 通過状態として使う `approved(advisory)` という文字列が `references/gate-status-schema.md`（Gate Status の正本）に登録されていない pseudo-status だった。
  - F3: `state.md に記録する` という設計時点の文言が、state.md 内のどの named section / field かを指定しておらず、書き手（impl-gate）と読み手（`post-completion-pr-flow.md` の PR 本文 assembly）が同じ場所を指せる保証がなかった。
  - F4: `docs/VERSIONING.md` の out-of-glob 更新（Task 4 remediation）は reviewer が revert 不要と判断済み（対応不要）。
- **Decision**:
  - F1: `SKILL.md` の自己参照を全て `L##` 形式から section 見出し参照（`## Goal` / `## Guardrails` / `## Remediation Priority` / `quick（inline checklist only）` バレット / `reviewer-common.md「### ops-blocking medium の判定例」`）に置換した。以後この行番号がズレても記述は破綻しない。
  - F2: `references/gate-status-schema.md` には手を加えず、impl-gate（express）の `Review Status` は既存の `approved` のまま維持する。advisory findings の有無は state.md の新設セクション `## Advisory Findings (Express Impl-Gate)` への記録の有無で表現する。`approved(advisory)` という文字列は「新設しない」ことの説明としてのみ SKILL.md に残る（新 status 値としては使わない）。
  - F3: `references/state-field-tiers.md` の Tier 3 表に `## Advisory Findings (Express Impl-Gate)`（見出しセクション）を追加登録し、書き込み条件・クリア条件・行フォーマット（`- \`<task-id>\`: <finding 要約> | severity: medium|low | evidence: <impl-gate review run id> | recorded_at: <ISO 8601 timestamp>`）を明記した。既存の「advisory review lane」（`gdd-requesting-code-review` companion review の用語）とは無関係の別概念であることも明記した。
- **Why**:
  - F1: 行番号の自己参照は挿入・編集のたびにズレる。section 見出しは編集に対して安定な参照点。
  - F2: 新しい status 値を canonical schema に追加すると、SessionStart hook / `gdd-status` / 他 skill の status パーサ全てが影響範囲になり、express 専用の 1 ケースのために共有 schema の複雑度を上げてしまう（KISS / YAGNI）。既存の `approved` + advisory 専用フィールドの組み合わせで、同じ利用者体験（advisory findings が記録され PR 本文に列挙される・fail-closed 集合は非退行）を schema 変更なしで実現できる。
  - F3: 書き手・読み手が同じ named section を参照することで、silent drop（advisory findings が記録されたのに PR 本文に反映されない）を防ぐ。
- **Consequences**:
  - `design.md` の HOW / Behavior Change Summary / doc-check 記述を本 ADR に合わせて上書き更新した。
  - AC / scope / fail-closed 挙動・PR 本文への列挙義務には影響しない（design detail のみの訂正であり、human_recheck 昇格は不要と判断）。
  - `references/state-field-tiers.md` に Tier 3 field を 1 件追加した（既存 field への破壊的変更なし）。
  - local plugin（`~/.claude/plugins/local/gate-driven-development/`）と worktree（本 repo）の両方に同一内容を適用し、diff 一致を確認済み。

---

