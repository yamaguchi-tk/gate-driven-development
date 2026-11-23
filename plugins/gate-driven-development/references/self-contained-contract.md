# Self-Contained Contract

> **所有**: 自己完結条件、forbidden な root 依存、許可される外部依存、fail-closed 条件、Verification schema、acceptance criteria
> **上位正本**: なし（最上位）
> **概要版**: `contract-overview.md`（ほとんどの skill はそちらだけで十分）
> **運用ルール展開**: `common-guardrails.md`（各 skill が日常的に参照する guardrails 集約）
> **参照元**: `state-machine.md`、全 skill、全 agent、`commands/gdd-dev.md`

`gate-driven-development` を「plugin を配布しただけで同じ workflow 契約を再現できる」状態にするための正本候補。概要だけ必要な場合は `references/contract-overview.md` を参照。

## 目的

- `gate-driven-development` の挙動を root 側 `CLAUDE.md` や ambient な skill / agent / rule に依存させない
- Claude Code / Cursor / Codex のどの host でも、同じ工程遷移・同じ gate・同じ fail-closed 条件を再現できるようにする
- 今後 auto-trigger を許可しても、`/gdd-dev` の明示実行と同じ workflow 契約に収束させる

## この文書における「再現性」

ここでいう再現性は、生成される文章やコードが 1 文字単位で一致することではない。次が一致することを指す。

- 開始 phase
- artifact の保存場所
- state の持ち方
- gate の順序
- 必須レビューと必須検証
- 停止条件と fail-closed 条件

## 非目的

- 生成物の文面やコード断片の完全一致
- 特定の security scan plugin の同梱
- root 側 workflow との長期二重保守
- plugin-managed Cursor symlink alias を除く、ambient に存在する同名 skill / agent / command との共存保証

`scripts/install-cursor-links.sh` が作り、`~/.cursor/plugins/gate-driven-development/cursor-links.tsv` で current plugin asset への alias と確認できる Cursor symlink は plugin-managed Cursor symlink alias とみなし、same-name ambient asset 衝突には含めない。

plugin-managed Cursor symlink alias を除き、同名 ambient asset がある環境は supported configuration に含めない。install / import / 起動時に検知できるなら停止する。

## 正本の境界

`gate-driven-development` の workflow 契約に関する正本は plugin 内だけに置く。

- `commands/`
- `skills/`
- `agents/`
- `references/`
- `scripts/`
- `.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json`
- `.codex-plugin/plugin.json`

root 側 `CLAUDE.md`、root 側 skill / agent、workspace ルールは、plugin が未定義の一般原則だけを補う存在として扱う。workflow の工程判断・gate 判断・artifact 判断の根拠に使わない。

## 対応 host capability

この contract が前提とする host capability は次だけとする。

- command 実行
- Stop hook 実行
- file 読み書き
- subagent 実行
- 最新技術情報の検索（公式ドキュメント / release notes / migration guide）
- git repository の認識
- git worktree の作成と再開

これらの capability が欠ける場合は fallback せず停止する。

## 優先順位

GDD に関する判断の優先順位は次の通りとする。

1. `references/self-contained-contract.md`
2. `references/state-machine.md`
3. `commands/` と `skills/` と `agents/`
4. host 側の一般ルール

host 側ルールと plugin 契約が衝突した場合、`gate-driven-development` の対象範囲では plugin 契約を優先する。

## plugin が内包すべき必須契約

plugin は少なくとも次の契約を自前で持つ。

- 設計原則
  - simplicity first
  - YAGNI / KISS / DRY
  - 過剰な互換レイヤーを増やさない
- steering 契約
  - formal workflow の canonical artifact は active worktree 側 `.steering/.../requirements.md`, `design.md`, `tasklist.md`
  - active worktree 側 `.steering/.../adr.md` は optional な decision log として持てる
  - `requirements.md` は要件・受入条件・実装方針を持つ人間承認の正本とする
  - `requirements.md` は少なくとも 目的、スコープ、非スコープ、Yes/No で判定できる受入条件（`AC-1`, `AC-2`, ... の連番 ID 付き）、制約・前提・依存関係、実装方針、影響範囲、検証ヒント、ロールバック、Open Questions を持つ
  - `requirements.md` の `Summary Brief` には Problem Discovery（既存コード・環境の具体的事実）と Options Exploration（候補案の比較）を経た根拠を反映する
  - 受入条件の AC ID は task breakdown での AC 紐付け、completion での pass/fail 追跡に使う
  - `references/task-sizing.md` が定める size tier（quick / standard）ごとに、必須セクションと独立見出しの省略ルールが適用される。quick では `requirements.md` を最小構成でよい（`design.md` は下の行）
  - `requirements.md` の節構成は `references/requirements-template.md` の常設 11 節 + 条件付き節が正本。`Human Check Questions` は常設で、人間に yes/no で承認ポイントだけを並べる（route / ownership / secret handling / masking / rollout / rollback が scope にある場合は、その承認事項を必ず含める）。`Route / Ownership Matrix` / `Sensitive Data / Masking Policy` は該当時のみ置く
      - 人間がそのまま読んで判断できる自然文（`references/human-check-template.md` § 判断の書き方）にし、内部 field 名や略語だけの箇条書きにしない
  - human check 前の `design.md` は lightweight design skeleton とし、節と粒度は `references/requirements-template.md` § lightweight design.md skeleton セクション一覧 に従う（design-gating を通るタスクは詳細設計の粒度）
  - human check 前の `design.md` skeleton も `Human Check Questions`（該当時は `Route / Ownership Matrix` / `Sensitive Data / Masking Policy`）を requirements と trace できる形で持つ
  - in-scope の version-sensitive / fast-moving な利用技術の確認結果（技術、対象 version、要点、参照元、checked_at）は `findings.md` に残せる
  - 最新情報を確認できなかった点は `Open Questions` に残し、確定事項として扱わない
  - `design.md` は human check 後に AI が具体化する detailed design の正本とする
  - `adr.md` は重要な意思決定、却下した代替案、その理由、影響を残す補助 artifact であり、gate・routing・completion の必須条件にはしない
  - `adr.md` が無いことだけを理由に fail-closed しない
  - `adr.md` がある場合、後続 phase は補助コンテキストとして読んでよいが、canonical state や routing source には使わない
  - tasklist 作成前に実装へ進まない
  - tracked な root 側 `.steering` は新 contract の canonical state に使わない
  - legacy root steering は resume 時の migration source / diagnostic source としてだけ扱い、current task として自動採用しない
  - legacy migration で root 側 `.steering/.../adr.md` があれば worktree 側へ一緒にコピーしてよく、無ければそのまま進める
  - `.gdd/tasks/<task_id>/binding.json` は task identity の正本。自然文 resume / status では current worktree / branch / registry を照合して task を一意に解決する
- pre-workflow 契約
  - `gdd-pre-workflow-brainstorming` は相談専用レーンとして formal workflow / state machine の外側に置く
  - `.steering/...`、`.cursor/plans/*.plan.md`、`Resume From`、`Next Action` を持たない
  - ユーザーが明確に実装 Go を出すまでは artifact を作らない
- Autonomous Continuation 契約
  - 詳細ルール（stop 条件、`<gdd-stop>` マーカー、`blocked` の定義）は `state-machine.md` の「Autonomous Continuation」を正本とする
  - `.claude/gdd-dev.local.md` は routing の正本ではなく、Stop hook が non-terminal phase を継続させるための補助 state に限定する
- mode switch 契約
  - `/gdd-dev` の開始・再開対象では、複雑さだけを理由に host 側の **Plan mode** へ切り替えない
  - `.cursor/plans/*.plan.md` は **Plan mode** とは別物の optional artifact として扱う
- requirements gate 契約
  - `gdd-requirements-gating` は human check 前に `gdd-planning-reviewer` を回す
  - reviewer selection ルールは `references/reviewer-selection.md` を正本とし、`Planning Reviewer Selection` を `state.md` に記録せずに gate を開始しない（design gate も同じ）
  - `gdd-planning-reviewer` は常時必須。design-gating を通るタスク（`Broad Requirement: true` を除く）では、design の観点の組（planning を design phase の文脈で 1 本、条件に当たる security）も同じ Round に並行に起動する（正本: `references/reviewer-selection.md` § Gate Rules）
  - `gdd-requirements-gating` 通過前に human check へ進まない
  - route / ownership / prompt contract / output contract / sensitive data / masking / rollout / rollback に関する blocking な `Open Questions` が残っている間は `human-check-waiting` に進めない
  - human check handoff には要約だけでなく `承認ポイント` を含め、route / ownership / secret handling / masking / rollout / rollback が scope にある場合はその承認事項を必須にする
  - `承認ポイント` は、人間がそのまま読んで判断できる自然文（`references/human-check-template.md` § 判断の書き方）で書き、内部 field 名や略語だけの箇条書きにしない
  - 各 `承認ポイント` には **背景**（なぜこの判断が必要か）と **変更前 → 変更後**（何がどう変わるか）を含め、人間がコンテキストを遡らずに判断できるようにする
  - `承認ポイント` の末尾に **方向性承認** を含め、E2E 発見時の AI 自走範囲を事前に合意する（テンプレートは `requirements-template.md` を参照）
- human check 契約
  - human check は `requirements.md` の要件・受入条件・実装方針を対象に行う
  - human check は通常 1 回を既定とし、`human_recheck_required` のときだけ再実施する
  - human check 承認時に `Approved Direction`（方向性・自走範囲・人間に戻す条件）を `state.md` に記録する
  - `Approved Direction` は routing source にはしない。`gdd-systematic-debugging` が自走範囲の判定に使う補助コンテキスト
  - E2E Discovery Loop: `Approved Direction` の自走範囲内かつ AC を壊さない変更は、human check に戻さず AI が自律判断する（詳細は `phase-progression.md`）
  - Scope Drift Guard: 同一 steering 内で `design_detail_only` が 3 回を超えた場合、方向性との整合を再確認する（詳細は `phase-progression.md`）
  - Route In Progress: `gdd-systematic-debugging` が route を決定したとき `state.md` に記録し、route 完了後にクリアする。セッション中断後の再開時に route 文脈を保持する（詳細は `state-machine.md`）
- design gate 契約
  - human check は `Human Check Questions` と handoff 内 `承認ポイント` に列挙された policy change を yes/no で判断できる状態でなければ始めない
  - lightweight `design.md` skeleton が揃っていることを gate 条件に加える
  - `gdd-design-gating` は approved な `requirements.md` と lightweight `design.md` skeleton をもとに detailed design を具体化する
  - `gdd-design-gating` は detailed design を固める前に対象技術の最新情報を再確認し、設計への影響を `design.md` に残す
  - 最新情報の再確認で requirements / implementation policy の変更が必要だと分かった場合、silent change せず `human_recheck_required` または `planning_rework_required` に戻す
  - `gdd-planning-reviewer` は常時必須とし、`gdd-security-reviewer` は selection ルールに従って必要時だけ起動する
  - approved な requirements / implementation policy を `gdd-design-gating` が勝手に増減させない
- planning loop 契約
  - planning phase は同じ unresolved blocker を blind に繰り返さない
  - 詳細な loop safety ルール（bounce 閾値、escalation 条件、blocking `Open Questions`）は `state-machine.md` の「Planning Loop Safety」を正本とする
- 実装契約
  - formal workflow に入ったら dedicated branch / worktree を準備する
  - TDD を前提に RED -> GREEN -> REFACTOR の順で進める
  - human check と `gdd-design-gating` の両方が承認済みになるまで build へ進まない
- review 契約
  - formal review の selection ルールは `references/reviewer-selection.md` を正本とする
  - implementation gate では `gdd-implementation-reviewer` を常時必須とし、`gdd-security-reviewer` は selection ルールに従って必要時だけ起動する。Terraform ファイルが変更対象に含まれる場合は `gdd-implementation-reviewer` が追加の terraform checklist を走査する
  - `Implementation Reviewer Selection` を `tasklist.md` に記録せずに gate を開始しない
  - non-selected reviewer は `waived` を使ってよいが、理由は `reviewer-selection` に基づく non-applicable と分かる形で残す
  - `gdd-implementation-gating` で `changes_requested` になった場合、build はユーザー確認待ちで止まらず自律 remediation loop に入る
  - remediation の優先順位、`ops-blocking medium` の定義、blind loop 防止ルールは `state-machine.md` の「Remediation Loop Safety」を正本とする
  - completion 前に `gdd-completion-reviewer` を必須とする（standard のみ）
  - `gdd-completion-reviewer` は reviewer selection record の欠落、曖昧な reason、scope と selection の不整合も確認する
  - companion review は明示要求時だけ使う
- security 契約
  - required external security evidence が無いまま `gdd-completion-check` を通さない
  - `.steering/**` への書き込みでは personal email、ローカルユーザー領域の絶対パスを hook で拒否する
  - legacy migration で旧 metadata の `Active Worktree Path:` の欄の行（ラベルと値だけの行）を扱う場合だけ、hook の許可例外を認めてよい
- session recovery 契約
  - Stop hook は phase 遷移時に Context Handoff Summary を `state.md` の `Last Handoff Summary` に永続化する
  - SessionStart hook は `Last Handoff Summary` を Quick Reboot context に注入する
  - `Last Handoff Summary` は routing source にしない（`Resume From` / `Next Action` が正本）
- context budget enforcement 契約
  - Stop hook は phase 遷移を検出した際に Handoff Summary が出力に含まれていなければ `systemMessage` で警告を注入する
  - 警告は advisory であり、workflow を block しない
- parallel execution 契約
  - standard タスクでタスク数 3+ かつ依存グラフから並列バッチが構成できる場合、`gdd-subagent-driven-implementation` はバッチ内の独立タスクを subagent で並列実行してよい
  - 同一バッチ内のタスクの変更ファイルが重なる場合は逐次に降格する
  - quick (express / standard) では並列実行しない
  - 並列実行の可否は `tasklist.md` の `Execution Plan` セクションに記録する
- implementation guidance 契約
  - `gdd-subagent-driven-implementation` はコードを書く前にプロジェクトのコード規約、変更対象の既存コード、`learned-patterns.md` を参照し、既存パターンに合わせて実装する
  - Implementation Guidance は参考情報であり、gate 条件にしない
- direct intent 契約
  - スコアリング方式（`references/brainstorming-steps.md` § 7b が正本。5 条件、うち 4 条件は +1〜+2 点、1 条件〔目的だけで手段未指定〕は -3 点）で判定。3 点以上で direct intent
  - direct intent の場合、Options Exploration skip + Iterative Refinement Loop を 1 回に制限
  - standard タスクでは、上記スコアとは別に direct intent を適用しない（実質無効）
  - Problem Discovery は direct intent でも省略しない
  - Express Path と組み合わせ可能（Express + Direct Intent = 最速パス）
- cross-task learning 契約
  - `gdd-completion-check` が `done` 時に採用パターン・却下案・発見した規約を `docs/learned-patterns.md` に蓄積する
  - `gdd-brainstorming` と `gdd-subagent-driven-implementation` が `learned-patterns.md` を参照する
  - `learned-patterns.md` は routing source にしない
- reviewer calibration 契約（Reviewer Learning Loop）
  - Stage 1（記録）: `gdd-implementation-gating` が差し戻し → 修正 → 再通過のサイクルで Calibration データを `tasklist.md` の Attempts に記録する
  - Stage 2（参照）: `gdd-implementation-gating` が review 開始前に `learned-patterns.md` の false positive 記録を読み、該当 finding の severity を 1 段階下げる（security 項目、および `reviewer-common.md` § 常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる） の適用範囲に当たる finding は除外）
  - Stage 3（改善）: チェックリスト自体の改善はプラグインメンテナが手動で行う
- progress visibility 契約
  - Stop hook が systemMessage に `phase: ... | tasks: N/M done | current: ...` 形式で進捗を注入する
  - `gdd-status` skill も同じ形式で Progress セクションを出力する（表示形式の統一）
  - skill 側での追加作業は不要（hook が自動注入する）
- metrics 契約
  - `gdd-metrics` skill は完了済み・進行中の全 steering から定量データを収集する
  - gate 通過率・差し戻し率・タスクサイズ分布・Reviewer Learning Loop 効果を可視化する
  - state を変更せず、読み取り専用で動作する
  - routing source にしない
- branch / PR 契約
  - plugin が新機能作業や PR 作成時の最低限の運用ルールを内包する
- CI / Issue 連携契約
  - PR 作成前に `gh` CLI で CI status を確認する（optional: `gh` が使えない場合はスキップ）
  - `requirements.md` に Issue 番号が含まれている場合、PR 本文に `Closes #N` を含める提案をする
  - 自動で Issue を close しない（PR 本文への記載提案のみ）
  - CI status 確認は advisory であり、failure でも PR 作成を block しない（ユーザー判断）

## 許可される外部依存

配布単体での再現性を壊さないため、外部依存は最小化する。

- 許可:
  - host が元から持つ基本能力
    - shell
    - file editing
    - subagent
    - git / worktree
- 不許可:
  - root 側 `CLAUDE.md` を読まないと判断できない設計
  - root 側 `~/.claude/skills/*` への依存
  - root 側 `~/.claude/agents/*` への依存
  - workspace ごとの ambient ルールを前提にした phase 分岐
    外部 verifier や hook が security evidence を供給してもよいが、`gate-driven-development` は特定 plugin 名、version、CLI surface を completion 契約に埋め込まない。

### External Security Evidence Contract

gdd-completion-check では、AC 検証と external security evidence の両方を下記「Verification 節の受理文法」が定める schema（`method` / `status` / `evidence` / `notes`）に記録する。**AC 検証行（`method=ac:`）は 1 件以上必要**。下記文法は data 行 0 件の節も行の形としては受理するが、done guard は `method=ac:` 行が 1 件も無い節を「検証行がありません」で block する。`security_evidence` 行・`refactor-checkpoint` 行は AC の検証行の代わりにならない。AC 検証行 1 件以上は形の下限であり、AC カバレッジを保証しない。tasklist の改行は LF / CR / CRLF だけとし、`str.splitlines()` が行を分ける他の文字（`\x0b` `\x0c` `\x1c`〜`\x1e` `\x85` U+2028 U+2029）を含む tasklist は、行・節の境界が崩れて検証行を正しく数えられないため done guard が block する（該当文字を削除する）。

**`method=security_evidence:*` 行は external verifier hook が書く。agent の手書きは契約違反**。

### Verification 節の受理文法

<!-- verification-grammar:begin -->
```
verification_section := heading NEWLINE section_line*
heading              := "## Verification"      ; exact match。rstrip 後の全行一致で
                                               ; 判定し、接頭一致は取らない。したがって
                                               ; `## Verification Notes` /
                                               ; `## Verification History` /
                                               ; `## Verification の例:` はいずれも
                                               ; 別の節であり、この節に飲み込まない
section_line         := blank | empty_marker | header | separator | data_row
blank                := ""                     ; rstrip 後に空
empty_marker         := "- なし"
header               := "|" h_method "|" h_status "|" h_evidence "|" h_notes "|"
separator            := "|" sep_cell "|" sep_cell "|" sep_cell "|" sep_cell "|"
data_row             := ac_row | evidence_row | refactor_row

ac_row       := "|" ws* "method=ac:" AC_ID ws*            "|" ac_status "|" cell "|" cell "|"
evidence_row := "|" ws* "method=security_evidence:" KIND ws* "|" ev_status "|" cell "|" cell "|"
refactor_row := "|" ws* "method=refactor-checkpoint" ws*  "|" ac_status "|" cell "|" cell "|"

h_method   := ws* "method" ws*      ; ASCII 小文字化して比較
h_status   := ws* "status" ws*
h_evidence := ws* "evidence" ws*
h_notes    := ws* "notes" ws*
sep_cell   := ws* ":"? "-"+ ":"? ws*
ac_status  := ws* ("pending" | "pass" | "fail") ws*                            ; ASCII 小文字化後に完全一致
ev_status  := ws* ("pending" | "pass" | "fail" | "n/a" | "unsupported") ws*    ; 同上
cell       := 任意（区切りの `|` は `\|` でエスケープする）

AC_ID  := "AC-" [A-Za-z]? DIGIT+ ("-" (DIGIT+ | [a-z]))? [a-z]?
KIND   := [a-z] [a-z0-9-]*

ws     := " " | TAB                 ; ASCII 半角空白 (U+0020) と水平タブ (U+0009) の 2 種だけ。
                                    ; 全角空白 (U+3000) / NBSP (U+00A0) / U+2028 等の
                                    ; Unicode 空白は ws ではなく、除去もしない。セルの
                                    ; padding に使った行は schema 違反になる
DIGIT  := [0-9]                     ; ASCII 数字だけ。全角数字 (`AC-１`) は DIGIT ではない
```

`## Verification` 節に置けるのは上記が定める行だけ。列挙外の行はすべて schema 違反として block される（`## Verification Notes` へ移す。検証行〔`method=` で始まる行 / AC ID・`security_evidence`・`refactor-checkpoint` を名指す行 / status トークンを含む行〕は `## Verification` 以外のどの節へも移してはならない。ただし `ac-ledger.md` / `## Verification History` が各々の規定に従って持つ正規の記録は対象外）。節に一部でも重なる fenced code block も schema 違反。

**節見出しは exact match**。行を rstrip した結果が `## Verification` と**完全一致**する行だけがこの節の開始であり、接頭一致では判定しない。`## Verification Notes` / `## Verification History` / `## Verification の例:` はいずれも別の節として扱い、この文法の適用対象外とする。fenced code block の中にある `## Verification` 見出し行も同じ exact match で判定する（接頭一致で拾うと、記入例 fence が `## Verification Notes` を 1 行含むだけで回復手順の無い恒久 block になる）。
<!-- verification-grammar:end -->

### Verification row の具体例

**AC 検証の例:**

```
| method | status | evidence | notes |
|--------|--------|----------|-------|
| method=ac:AC-1 | pass | pytest tests/test_pagination.py::test_cursor_pagination — all passed | カーソルベースのページ取得 |
| method=ac:AC-2 | pass | curl 確認 — response に next_cursor field あり | next_cursor がレスポンスに含まれる |
| method=ac:AC-3 | pass | pytest tests/test_pagination.py::test_invalid_cursor — 400 returned | 無効 cursor で 400 エラー |
```

**External security evidence の例:**

```
| method | status | evidence | notes |
|--------|--------|----------|-------|
| method=security_evidence:code | pass | tool=mcp__snyk__snyk_code_scan; scan_id=abc123; 0 issues | |
| method=security_evidence:sca | n/a | | dependencies 変更なし |
| method=security_evidence:iac | unsupported | | Terraform module だが snyk IaC が未対応 |
```

**refactor checkpoint の例:**

```
| method | status | evidence | notes |
|--------|--------|----------|-------|
| method=refactor-checkpoint | pass | src/foo.ts を 80 行 → 50 行に簡略化 | |
```

### 詳細ルール

- AC 検証: `pass` のときは検証 evidence を残す
- external security evidence:
  - `pass` のときは URL、相関 ID、artifact path などの追跡可能な evidence を残す
  - `n/a` はその evidence kind が今回の変更に非該当のときだけ許可する
  - `unsupported` は evidence kind は必要だが current verifier contract では対象外であることを具体的に示せるときだけ許可する

### Required Evidence Kind 判定

変更内容に応じて必要な evidence kind を決定する。この表が「いつ・どの kind が必要か」の正本である。

| 変更内容 | 必要な evidence kind | 判定例 |
|----------|---------------------|--------|
| ソースコード変更（`.ts`, `.py`, `.go`, etc.） | `security_evidence:code` | `.ts` ファイルの追加・変更 |
| 依存パッケージ変更（`package.json`, `Gemfile`, `go.mod`, etc.） | `security_evidence:sca` | `package.json` の dependencies 変更 |
| IaC / インフラ変更（`.tf`, CloudFormation, etc.） | `security_evidence:iac` | Terraform ファイルの変更 |
| コンテナイメージ変更（`Dockerfile`, etc.） | `security_evidence:container` | Dockerfile の変更 |
| 上記に該当しない（ドキュメントのみ、設定値のみ等） | evidence 不要 | `gdd-completion-check` が `N/A` で記録 |

- 1 つの変更が複数カテゴリに該当する場合、該当する全 kind の evidence が必要
- row の作成責任は external verifier hook にある。hook が active worktree 側 `tasklist.md` の Verification に upsert する
- hook が未導入の環境では、`gdd-completion-check` が外部前提不足として fail-closed する
- plugin は特定の verifier 実装（Snyk 等）の名前・version・CLI surface を completion 契約に埋め込まない

## 起動契約

### 明示起動

- `/gdd-dev` は canonical entrypoint とする
- `/gdd-dev` は canonical state 解決の前に entry intent（`new` / `resume` / `ambiguous`）を判定する
  - 判定ルールは `references/entry-intent.md` を正本とする
  - 判定は明示 cue のみで行い、implicit な推測はしない
  - `再開`, `続き`, `続きから`, `resume` などの明示 cue があれば `resume`
  - `新規`, `新規開始`, `別件`, `新しい task`, `新しいタスク` などの明示 cue があり、resume cue と衝突しなければ `new`
  - resume cue を含まない具体的な新規 task 説明なら `new`
  - `$ARGUMENTS` が空、cue が弱い、cue が衝突する場合は `ambiguous` とし、fail-closed で確認する
- 新規開始時は `gdd-brainstorming` から入り、worktree を準備してから artifact を作る
- `gdd-brainstorming` の次は `gdd-requirements-gating` に進み、その後に human check と `gdd-design-gating` を行う
- 継続 task では Task Binding Registry と git worktree の照合を正本として canonical state を解決し、適切な phase に resume する
- worktree candidate が見つからず legacy root steering だけがある場合でも current task としては採用せず、diagnostic / migration candidate として提示して停止する。migration はユーザーが対象を明示した後にだけ試みる
- planning と resume の workflow artifact は `.steering/.../requirements.md`、`design.md`、`tasklist.md` を正本とする

### 相談用 auto-trigger

- `gdd-pre-workflow-brainstorming` は相談専用の pre-workflow lane として auto-trigger されてよい
- この lane は formal workflow / state machine の外側に置く
- `.steering/...`、`.cursor/plans/*.plan.md`、`Resume From`、`Next Action` を読まず書かない
- 実装、review、worktree、completion は開始しない
- ユーザーが明確に実装 Go を出したときだけ `/gdd-dev` に handoff する
- active steering の解決、resume 判断、fail-closed 判定、artifact 作成は `/gdd-dev` と `gdd-brainstorming` に委譲する

### formal auto-trigger

将来 `/gdd-dev` 相当の formal auto-trigger を許可する場合でも、次を満たさなければならない。

- 初回 routing は `/gdd-dev` 明示実行と同じ contract に従う
- `gdd-brainstorming`、`gdd-requirements-gating`、human check、`gdd-design-gating`、`gdd-task-breakdown` を勝手に短絡しない
- artifact と state の保存場所を変えない
- review / completion の必須条件を緩めない

## Artifact 契約

primary artifact は次のみとする。

- `.steering/YYYYMMDD-short-title/requirements.md`
- `.steering/YYYYMMDD-short-title/design.md`
- `.steering/YYYYMMDD-short-title/state.md`
- `.steering/YYYYMMDD-short-title/tasklist.md`

**trivial パスの例外**（`references/task-sizing.md` 参照）:
- primary artifact は不要。commit message に `[trivial]` と変更理由を記載する
- gate / reviewer / human check / security evidence / completion check はすべて省略
- 作業中に trivial 条件を満たさなくなった場合は quick 以上に昇格する

optional artifact は次のみとする。

- `.steering/YYYYMMDD-short-title/reviews.md`
  - requirements-gating のレビュー Round・指摘・処置の記録先（追記専用）
  - Round カウントの正本であり、gate は最新ラウンド分だけを読む（`references/requirements-gating-steps.md` § レビューループの契約）
- `.steering/YYYYMMDD-short-title/adr.md`
  - 重要な意思決定が発生したときだけ作る
  - 追記型の decision log として使う
  - `Context` / `Decision` / `Why` / `Consequences` を最小テンプレとする
  - canonical state、routing source、gate 条件にはしない
- `.steering/YYYYMMDD-short-title/review-findings.md`: impl-gating と独立レビューの、指摘ごとの ID・行き先・検証役の判定（追記専用。正本: `references/finding-dispositions.md`）。routing は読まず、読むのは `scripts/check-finding-dispositions.py` と `scripts/check-gate-ledger.sh` の `findings` 行
- `.steering/YYYYMMDD-short-title/findings.md`
  - brainstorm や調査の過程で得た発見・比較結果・技術検証結果を構造化して残す
  - `pre-workflow-brainstorming` の brainstorm や `brainstorming` の技術調査で蓄積する
  - canonical state、routing source、gate 条件にはしない
  - `gdd-status` が goal / findings の要約に使ってよい
- `.cursor/plans/*.plan.md`
  - ユーザーが明示的に保存を求めたときだけ使う

`gdd-pre-workflow-brainstorming` は primary artifact も optional artifact も作らない。

新 contract の通常フローでは active worktree 側 `.steering/...` を唯一の canonical artifact とし、tracked な root 側 `.steering` を build / planning の正本として使わない。

## State 契約

state の正本は plugin 内 `references/state-machine.md` に置く。resume と phase 遷移はその定義だけに従う。

- task identity: `.gdd/tasks/<task_id>/binding.json`（`task_id`, `worktree_path`, `branch`, `steering_path`, `state_path`）
- tasklist 作成前: active worktree 側 `state.md` の `Resume From`
- tasklist 作成後でも `Requirements Review Status=approved`、`Design Review Status=approved`、`Human Check Status=approved` の 3 つが揃う前: stale tasklist を draft planning artifact として扱い、`tasklist.md` を routing source にせず、active worktree 側 `state.md` の `Resume From` を使う
- tasklist 作成後かつ 3 つの gate が承認済み: active worktree 側 `tasklist.md` の `Next Action`
- `Resume From` / `Next Action` は canonical artifact の値だけを正本とし、自然言語だけで上書きしない
- active worktree 側 `adr.md` は存在しても routing source にしない
- `.claude/gdd-dev.local.md` と session id は soft signal。Task Binding Registry と current worktree の一致を上書きしない
- legacy root steering は migration source / diagnostic source としてだけ扱い、migration 後は worktree 側 state だけを更新する

tracked な root 側 `.steering` を移行期 fallback として build / planning の正本に参照する設計は最終形に含めない。

## Fail-Closed 条件

次の条件では先へ進まず停止する。

- git / worktree が必要 phase なのに使えない
- plugin-managed Cursor symlink alias ではない same-name ambient asset の衝突で plugin 側 asset を deterministic に解決できない
- plugin 契約に必要な file / manifest / reference が欠けている
- worktree candidate が複数あり 1 つに決められない
- 同一 worktree で planning/build candidate が競合する
- legacy root steering はあるが migration に必要な git 情報または copied artifact が欠けている

## Blocked Response Contract

fail-closed は「状態を勝手に進めない」ことを意味し、何も案内せず会話を打ち切ることは意味しない。停止するときは、少なくとも次を返す。

- `参照した正本`
- `停止理由`
- `次の1アクション`
- `<gdd-stop>` の後の `## 👤 次にすること`（`references/output-format.md` § 停止時の「👤 次にすること」マップ）

追加ルール:

- 既に current phase が決まっている場合、external prerequisite 不足・metadata 修復・人間入力待ちだけを理由に別 phase へ reroute しない
- その場合は current phase の `Resume From` / `Next Action` を維持したまま unblock 手順を返し、解消後に同じ phase を再実行できるようにする
- `entry intent=ambiguous`、active steering 候補の競合、plugin-managed Cursor symlink alias ではない same-name ambient asset 衝突のように正本そのものを決められない場合は、state を変えずに停止し、候補一覧や選択方法を返す
- `gdd-completion-check` の required external security evidence が external prerequisite 不足で取得できない場合は、`done` に進めず、`Next Action=gdd-completion-check` のまま不足前提のチェックリストを返す
- actual な AC failure、review blocker、verification evidence 不足だけを `gdd-systematic-debugging` などの差し戻し対象にする

## 命名と衝突回避

- command / skill / agent / plugin manifest 名は、plugin-managed Cursor symlink alias を除く same-name ambient asset と衝突しにくい名前を使う
- install / import 時に plugin-managed Cursor symlink alias ではない同名 asset が見つかった場合は停止する
- `scripts/install-cursor-links.sh` が作り、`~/.cursor/plugins/gate-driven-development/cursor-links.tsv` で current plugin asset への alias と確認できる Cursor symlink は、host が別 path で見せても同一 asset の alias とみなす
- 「たまたま host 側で同名 asset が先に解決された」状態を許容しない

host が plugin 同梱 asset の優先解決を保証しない前提で設計する。したがって、plugin-managed Cursor symlink alias ではない同名 ambient asset が見つかった時点でその環境は unsupported とみなし、成功扱いにしない。

## branch / PR 契約

plugin が内包する branch / PR の最小契約は次とする。

- 新機能作業は default branch から専用 branch を切って進める
- worktree を使う phase では branch と worktree を 1 task に対して対応付ける
- PR 作成時は template があればそれに従う
- PR タイトルと本文は日本語を既定にする
- template 内コメントは削除しない

## 検証契約

plugin は少なくとも次を検証できなければならない。

- 検証レイヤは分けてよい。`tests/validate-plugin.sh` 単体で全部を証明する必要はない
- `tests/validate-plugin.sh`:
  - manifest 同期
  - 必須 asset の存在
  - forbidden な root 依存の不在
  - frontmatter / 最小契約トークン / 軽量 fixture
- `evals/evals.json` と eval ループ:
  - trigger / handoff / routing / fail-closed / review 応答の妥当性
  - remediation 優先順位や loop safety の応答契約
- sample task / review / manual walkthrough:
  - sample task での end-to-end 遷移
  - resume / migration の determinism
  - host capability を含む phase 間の自己完結性

- manifest 同期
- 必須 asset の存在
- forbidden な root 依存の不在
  - root `CLAUDE.md`
  - root skill / agent 参照
  - root fallback 前提の文言
- sample task での end-to-end 遷移
- resume / migration の determinism
- 将来 auto-trigger を有効化するなら、明示起動との差分がないこと

## Acceptance Criteria

この contract が満たされたと言えるのは、次をすべて Yes で判定できるときだけとする。

- clean な Claude Code / Cursor 環境で git / worktree capability が使えるとき、`/gdd-dev` で workflow が開始できる
- formal workflow では planning から active worktree 側 `.steering/...` を正本として使い、tracked な root 側 `.steering` を通常フローの canonical source にしない
- 既存 non-terminal steering があっても、明示 resume cue の無い `/gdd-dev <具体的な新規 task>` は新しい `.steering/...` を作って開始し、既存 steering を勝手に resume しない
- `/gdd-dev` 単独実行や new / resume cue が衝突する入力では fail-closed で `新規開始` か `再開` かを確認する
- `gdd-pre-workflow-brainstorming` が相談レーンとして auto-trigger されても、`.steering/...`、`.cursor/plans/*.plan.md`、state field を作らない
- root 側 `CLAUDE.md`、root skill、root agent が存在しなくても、workflow の phase 判断と gate 判断が成立する
- root 側 `CLAUDE.md`、root skill、root agent が存在しても、それらを workflow 判断根拠として使わない
- `gdd-requirements-gating` が human check 前の reviewer gate として機能し、lightweight `design.md` skeleton が揃うまで先へ進まない
- `requirements.md` と human check 前の `design.md` skeleton には `Human Check Questions`（該当時は `Route / Ownership Matrix` / `Sensitive Data / Masking Policy`）が存在する
- `gdd-requirements-gating` と `gdd-design-gating` は `references/reviewer-selection.md` に従って applicable reviewer だけを起動し、selection evidence を artifact に残す
- route / ownership / prompt contract / output contract / sensitive data / masking / rollout / rollback に関する blocking `Open Questions` が残っている場合、`gdd-requirements-gating` は `human-check-waiting` に進めない
- `human-check-waiting` に入る handoff には `承認ポイント` があり、route / ownership / secret handling / masking / rollout / rollback が scope にある場合はその承認事項が含まれる
- `gdd-brainstorming` と `gdd-design-gating` は、version-sensitive / fast-moving な利用技術について最新の公式ドキュメント / release notes / migration guide を確認し、`findings.md` または `Open Questions` に残す
- `adr.md` は重要な意思決定を任意で残せるが、無くても planning / build / review / completion を止めない
- human check は `requirements.md` の要件・受入条件・実装方針を対象にし、通常 1 回を既定とし、`human_recheck_required` のときだけ再実施する
- `gdd-design-gating` はその承認後に detailed design を具体化する
- `adr.md` が存在しても `Resume From` と `Next Action` の routing source は `design.md` / `tasklist.md` のまま変わらない
- same input state なら `Resume From` と `Next Action` の解決結果が host に依らず一致する
- build / planning candidate が競合した場合は fail-closed で停止する
- `gdd-implementation-gating` が `changes_requested` を返した場合、formal workflow はユーザー確認待ちで止まらず自律 remediation loop に入る
- `gdd-implementation-gating` は current task ごと（Gate Batch では batch ごと）に `Implementation Reviewer Selection` を残し、non-selected reviewer を理由付き `waived` と区別できる
- 自律 remediation loop は `state-machine.md` の「Remediation Loop Safety」に従う（優先順位、blind loop 防止、escalation 条件）
- required external security evidence が必要な変更では、`security_evidence:<kind>` 行と evidence schema が固定されている
- required external security evidence が無い場合、`gdd-completion-check` は `done` に進まない
- external verifier の具体例として、Snyk のスキャン結果を書く verifier pluginのような hook-based verifier は、active worktree 側 `tasklist.md` の `Verification` に `| method=security_evidence:code | pass | ... | |` のような canonical 表行を upsert する。**`method=security_evidence:*` 行は external verifier hook が書く責務であり、agent の手書きは契約違反**。現行の外部 writer は canonical 形ではなく、2 列目に `security_evidence:<kind>` を持つ非 canonical な 5 列 list 行を書くため、その行は schema 違反として block される
- active `tasklist.md` を 1 件に決められない verifier は、誤書き込みより no-op を優先してもよい
- `gdd-completion-check` は reviewer selection record が欠けている、または scope と不整合なまま `done` に進まない
- plugin-managed Cursor symlink alias ではない same-name ambient asset が存在する場合、install / import / 起動のいずれかで成功扱いにせず停止する
- `scripts/install-cursor-links.sh` が作った Cursor symlink alias だけが存在する場合、それを same-name ambient asset conflict と誤判定しない
- `.claude-plugin/plugin.json` と `.cursor-plugin/plugin.json` が同一 contract を表現し、`.codex-plugin/plugin.json` の共通 field（name / version / description / author / keywords）との差分も検証で検出される

## 移行方針

plugin を自己完結化する際は、次の順で進める。

1. この契約に沿って plugin 内に必須ルールを移す
2. `README.md` と `references/state-machine.md` から root canonical 前提を除く
3. skill / agent / command の記述を plugin 契約に合わせる
4. validate script に forbidden dependency check と worktree-first contract check を追加する
5. sample task と review で自己完結性を確認する

## 未解決事項

- auto-trigger をどの粒度で許可するか
- branch / PR 契約を `README.md` に置くか、専用 reference に切り出すか
