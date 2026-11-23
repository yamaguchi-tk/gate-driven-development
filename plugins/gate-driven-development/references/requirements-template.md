# Requirements Template

> **所有**: `requirements.md` と lightweight `design.md` skeleton のセクション定義
> **上位正本**: `self-contained-contract.md`
> **参照元**: `gdd-brainstorming`、`gdd-requirements-gating`

## 精度の第一原則

出荷物（コード・テスト・出荷ドキュメント）の品質はテストと implementation-gating が担保する。planning 文書で高精度が要るのは次の 2 つだけ:

1. **人間の承認判断に使う箇所**（承認ポイント・スコープ・安全境界 = 破壊的操作・秘匿・不可逆）
2. **AC の意味**（テストの正本になる受入条件）

それ以外の記述は「実装に着手できる程度」でよい。詳細化はテストと実装が引き受ける。

- **人間が承認した重要判断は受入条件（AC）として書く**。独立した trace 表は作らない。AC はテストに落ちるので、表がなくても実装完了まで運ばれる
- **枠（節見出し）は機械強制・中身は prose**。機械検査（このテンプレートへの contract test と gate の節見出し確認）が見るのは節の存在と決まった欄の有無だけで、中身の網羅性を機械検査で追わない（2026-08-31 の経験による。精度を機械強制すると、レビューが何ラウンドも発散した）
- 実測・件数を根拠に書く場合は母集団（どの集合の N か）を併記する。書けないなら断定しない

## 事実は AC に 1 回だけ書く

- 欄名・数値・PR の分け方などの事実は `受入条件` の AC に 1 回だけ書く（1 PR あたり 8 個以内）。ほかの節と design.md は書き直さず `AC-n 参照` と書く。照合元（`スコープ` の原文、`Express Minimal Trace`）と `Planned Follow-up Stage Lane` の値（hook が読む）はそのまま書く
- `Human Check Questions` は AI が決められないものだけを、方向性承認を除いて 2 個以内にする（昇格必須のものも数え、超えたら理由を 1 行）
- steering write hook が `scripts/lint-requirements-duplication.py` で AC の欄名の列挙（backtick の語 2 つ以上）の書き直しを advisory に出す

## HITL Outcome Audit

Approved Direction と最終成果物を照合し、この承認をきっかけに AI が自走した結果、期待どおりの結果になったかを確認する。結果は `match / mismatch / unverified` で記録する。mismatch / unverified が残る場合は completion を通さず、必要に応じて `human_recheck_required` または planning route に戻す。

## Size-Specific Template Dispatch

このファイルは full requirements template の詳細正本である。express template に無い情報が必要になった場合だけ、この full template に昇格する。

- `quick (express)`: `references/requirements-template-express.md`
- `quick (standard)`: このファイルの最小構成（下記「requirements.md セクション一覧」冒頭）
- `standard`: このファイルの full template

## Summary Brief（3 層構造 + Honest Limitations）

`requirements.md` と `design.md` の両方で冒頭に配置する。

```markdown
## Summary Brief

### 一言
<対象>に対して<目的>を実施する

### 判断材料
- 確定事項: <AC-n 参照>
- 未確定事項: ...
- やらないこと: ...
- 外部依存の確認結果: ...
- 設計方針: ...
- 根拠の母集団: <件数・実測を根拠に出す場合のみ。その N をどの集合から取ったか>

### 承認ポイント
1. **<カテゴリ>**: <判断対象の説明>
   - 背景: <なぜこの判断が必要か — Problem Discovery で得た具体的事実を 1-2 文で> / 根拠: <AC と同じ>
   - 変更前: <現在の挙動・状態>
   - 変更後: <採用案を適用した場合の挙動・状態>
   - 採用案: <AIが選んだ案とその理由>
   - 代替案: <却下した案とその理由>
   - → OK / 別案希望

2. **<カテゴリ>**: <判断対象の説明>
   - 背景: <なぜこの判断が必要か> / 根拠: <同上>
   - 変更前 → 変更後: <1 行で対比できる場合はこの形式でもよい>
   - 内容: <承認してほしい内容>
   - リスク: <承認した場合のリスクと対策>
   - → OK / 修正依頼

### Honest Limitations
<承認ポイントの直後に配置する。standard で必須、quick は任意>
- <種類>: <この設計で確認できないこと / テストで担保できない部分 / デプロイしないと分からない部分>

### ズレ確認
<形は `references/human-check-template.md` § ズレ確認>
```

- 「一言」は 1 行で何をするかを書く。人間が最初にこれだけ読めば話が分かる粒度にする
- 「承認ポイント」は human check で判断してほしい事項を番号付きで書く（数は § 事実は AC に 1 回だけ書く）
  - 各ポイントは **カテゴリ**（scope / 方針 / リスク / 権限 / データ等）を太字で先頭に置く
  - **背景**: なぜこの判断が必要なのかを具体的事実で示す。「ページネーションの方式」ではなく「全件取得は 1000 件超で 5 秒以上かかるので取得方式を変える」のように書く
  - **変更前 → 変更後**: 現状と採用案適用後の対比を示す。人間が「何が変わるか」を一目で把握できるようにする
  - AI が選んだ案・理由・代替案を提示し、人間は「OK / 別案希望 / 修正依頼」で判断する
  - 人間がコンテキストを読み込まなくても、承認ポイントだけ読めば判断できる粒度にする
- 「方向性承認」を承認ポイントの末尾に 1 件追加する（原則必須）:
  ```markdown
N. **方向性**: <この変更の目的を 1 行で>
   - 自走範囲: <この方向性と矛盾しない限り、E2E で発見された問題の修正は AI が自律判断してよい>
   - 自走上限: <今回の承認で AI が進めてよい最大到達点。値は human-check-template § 自走上限の置換値>
   - Post-PR Completion Scope: <none / マージして再学習まで / post-merge verification / relearning まで。ユーザーが明示した場合は PR 作成までに丸めない>
   - Post-PR 操作承認: <manual merge required / merge approved / deploy approval required / Requires explicit operation approval>
   - 人間に戻す条件: <満たせない見込み / AC・scope を削る・弱める / 信頼境界を緩める>
   - → OK / 自走範囲を制限したい
  ```
  - 人間が「OK」と答えた場合、`state.md` に `Approved Direction` として方向性と自走範囲を記録する
- 人間が自走範囲または自走上限を制限した場合、その制限を `Approved Direction` に記録し、制限を超える変更は human check に戻す
  - **Why:** E2E 起因の問題が続くたびに human check に戻すと確認が爆発する。方向性を先に承認すれば、詳細は AI に委ねられる
- 「Honest Limitations（この設計で確認できないこと）」は率直に書く。「多分できる」「たぶん大丈夫」は `未確定事項` に回す
  - Honest Limitations を読んだ人間が **scope reduction**（範囲を狭める）や **後工程の E2E 計画** を判断できる粒度で書く
  - **Why:** AI が「できることだけ」を示すと、人間は「できないこと」に気付けず広すぎるスコープで承認する。手戻りの最大の原因は後で気付いた担保不足なので、最初に明示する

## requirements.md セクション一覧

`quick (standard)` パスでは Summary Brief + 目的 + スコープ + 受入条件 + 実装方針 + `Human Check Questions` + ズレ確認の最小構成でよい（承認ポイントの独立見出しは quick でも省略しない — `references/common-guardrails.md` § 承認見出しルール）。

**常設 11 節**（standard。節見出しの存在を gate が確認する。中身は prose）:

1. Summary Brief（上記 3 層構造 + Honest Limitations + ズレ確認）
2. 目的
3. スコープ
   - **ユーザーが述べた完了条件を原文に近い箇条書きで残す**（3〜5 行程度）。AC への写し（受入条件の記入規則）の照合元で、会話履歴は compaction で欠けるため、この一覧が無いと写しを後から検証できない
4. 非スコープ
5. 受入条件
   - 各条件に `AC-1`, `AC-2`, ... の連番 ID を付け、AC ごとに `根拠:`（前提を読むか測った `file:line`・コマンドと値、`未測（理由）`、`なし（理由）`）と `計測:`（何を・どの母集団で・どの値なら合格か）を箇条の先頭か ` / ` の後に書く（無い・AC か承認ポイントの項目が 0 件なら lint が止める）
   - ID は task breakdown での AC 紐付け、completion での pass/fail 追跡に使う。例: `- AC-1: ユーザーがログインボタンを押すとダッシュボードに遷移する`
   - ユーザーが明示した完了条件は、そのまま AC に写す（勝手に丸めない・落とさない。落とすなら非スコープか Open Questions に理由付きで書く）
   - 観測面が外部にある条件（外部システムへの投稿 / デプロイ後の挙動 / 外部 API の実呼び出し）は、検証水準（E2E 必須 / 外部証跡必須）を AC 本文に明記する（書かない水準は後の照合で守られない）
   - 曖昧な受入条件・境界ケース・失敗時挙動があるときだけ、入力/出力/期待挙動の代表例を条件の下に書いて固定する
   - AC が扱う入力（文字列・コマンド・ファイルパス・外部ペイロード等）が有限集合か開いた集合かを判定し、開いた集合であれば **開いた入力の扱い** を1行で明記する: `構造で閉じる`（設計を変え、範囲を保ったまま入力の形を閉じる。候補があれば既定）／`なし`（実質有限で根拠あり）／`列挙に縮める`（対象パターンを列挙し列挙外の既定挙動を明記）／`限界として開示する`（`Honest Limitations` へ。合格基準のある AC には使わない）のいずれか
6. 実装方針
   - どう作るかの要点。複数の合理的方式がある場合だけ、方式比較（概要 / 複雑さ / 信頼性 / 運用コスト）を表で書き、採用案を承認ポイントに含める
   - 調査（既存実装・依存関係・技術スタック・アーキテクチャ）は実施してよいが、requirements に書くのは**承認判断に効く結論だけ**。調査ログは残さない
7. 影響範囲
8. リスク
   - 不可逆な操作・破壊的操作・本番影響を中心に書く。該当がなければ「なし」と 1 行
9. 制約・前提
10. Open Questions
11. `Human Check Questions`
    - Summary Brief の「承認ポイント」と同じ構造化形式・件数・記入規則を使う（上記「承認ポイント」の定義が正本）
    - route / ownership / secret handling / masking / rollout / rollback が scope にある場合は、その承認事項を必ず含める

**条件付き節**（該当するときだけ置く。非該当時は見出しごと省略してよい）:

- `Post-PR Completion Scope`: ユーザーが `merge` / `マージ` / `再学習` / `relearning` / `post-merge verification` / `release verification` / `apply 後確認` を完了条件として明示した場合に必須。`マージして再学習まで` のような条件を `PR 作成までに丸めない` 方針と、`merge / deploy / apply / AWS write` は `1 操作ごとの明示承認` とする操作承認境界を記録する
- `Sensitive Data / Masking Policy`: 秘匿データを扱う場合。どの値が sensitive か / prompt に入るか / どこで mask / reject / sanitize するか / 最終責任者
- `Route / Ownership Matrix`: rollout / rollback / owner 変更がある場合。before / after / owner / flag / rollback を 1 表で
- `Implementation Sequence Plan`: 複数 Stage / 複数 PR / 後続 PR がある場合。Stage ID / 生成物 / 完了確認（`AC-n`） / `PR Boundary` / `Approval Scope` / **見積もり diff 行数** / 人間に戻す条件を、human-check に `段階実装案` を出せる粒度で書く。単一段階なら節ごと省略
- `Planned Follow-up Stage Lane`: `PR Boundary=follow-up-pr` または `post-merge-verification` の Stage がある場合に必須。計画済み後続 Stage が PR merge 後に消えないよう、後続作業の seed を残す。形式:

  | Pending Stage ID | Origin Steering | Base Branch | Base Commit | Next Planned Stage | Follow-up Trigger | Stage Files | In-flight PR | Continuation Mode | Tracking Destination | Human Recheck |
  |---|---|---|---|---|---|---|---|---|---|---|
  | S-2 | <現在の steering path> | <現在の base branch> | <PR 作成時または merge 後の commit> | <次に着手する Stage ID と目的> | post-merge / after-current-pr / manual | <この Stage が触るファイル / glob> | <`<Stage ID>: <PR URL> (<state>)` 形式。継続のたびに追記> | auto-after-clean / auto-stacked / manual | <new steering seed / backlog / issue / none + 理由> | required before implementation / not required + 理由 |

  - `Follow-up Trigger=after-current-pr` の意味: 現 Stage の PR が**外部レビュー収束（Auto-Arm clean）に到達した後**、merge を待たずに着手してよい
  - `Continuation Mode` の既定は `manual`。`auto-after-clean` は Stage Continuation（`references/post-completion-pr-flow.md` Option 1 手順 6 § Stage Continuation）の必要条件であり、選ぶ場合は HITL の独立承認ポイントに昇格する。`auto-stacked` は**依存 Stage 専用**（`Depends on` あり。先行 branch を base にする stacked 継続）で、独立 Stage には `auto-after-clean` を使う
  - `Stage Files` / `In-flight PR` は独立判定と stacked 判定の入力。`In-flight PR` は `Depends on` の Stage ID から一意に解決できるよう `<Stage ID>: <PR URL> (<state>)` 形式で記載する。未宣言・不明な Stage は依存扱いとして継続しない。`In-flight PR` の正本は継続先 steering にコピーした Lane とする
  - 中が `- [x]` と空行だけなら完了。表の行が残れば未完

### 行数の目安

standard の目安: **requirements.md 300 行** / design.md 500 行 / tasklist.md 600 行 / adr.md 300 行 / state.md 100 行。超えそうなら承認判断・routing に効かない記述から削るか `worklog.md` へ移す。レビュー指摘・処置結果は `reviews.md` へ。hook（`validate-steering-write.py`）が state / tasklist / design のサイズ超過を advisory で警告する。

## Express requirements.md テンプレート

`quick (express)` パスでは `references/requirements-template-express.md` を使う。design.md は作成しない。

Express テンプレートの原則:
- 承認ポイントは方向性承認を必ず 1 件含め、ほかは 2 件以内に絞る
- 条件付き節（Post-PR Completion Scope 等）は該当するときだけ足す
- `state.md` の Gate Status は requirements-gating 通過時に以下を設定（`requirements-gating-steps.md` § Express）:
  - `Requirements Review Status=approved`
  - `Design Review Status=approved`（design.md 不要。同じ evidence）
  - `Human Check Status=pending`
  - `Resume From=human-check-waiting`

## lightweight design.md skeleton セクション一覧

運用レベル light の quick (standard) は Summary Brief + 変更点 + テスト方針だけでよい。ほかは 5〜8・10 と条件付きの節を design-gating Step 5 の粒度で書く（`Broad Requirement: true` は human check で scope を選んだ後に Step 5 で書く）。

1. Summary Brief（requirements と同じ 3 層構造 + Honest Limitations。テンプレートは上記参照）。事実は写さず `AC-n` を引く
2. 変更点の要約
3. `Design Policy Discussion`（human check 前に設計方針の候補、簡略化余地、採用しない案、残る判断点を見える位置に残す）。以下の設計抜けパターンチェックリストを必要に応じて使う:
   - **インターフェース全量カバレッジ**: 既存インターフェースを書き換えるとき、元のインターフェースが扱う全ケース（メッセージ種別・状態・ハンドラ分岐）が新設計に含まれているか
   - **コンポーネント間の対称性ポリシー**: 複数コンポーネントに同じ機能を追加するとき、対称性（または意図的な非対称の理由）が明文化されているか
   - **やらない判断の根拠**: AC または Non-Goal に「やらない」判断の根拠（技術的制約・スコープ外・コスト判断）が記録されているか
4. `Human Check Questions`（requirements の承認事項を番号と `AC-n` で引く。非該当は `N/A` と根拠 1 行）
5. 影響範囲
6. 主要フロー
7. テスト方針
8. ロールバック / fail-closed
9. Open Questions
10. 配線表（新設要素がある場合のみ）: 新設する関数・state field・trigger・閾値・マーカーごとに、書く側（file:関数）／読む側／入口からの到達経路／同じ入力を読む既存実装／検証テスト名を1行で記載する

条件付き（該当するときだけ）: `Route / Ownership Matrix`（enforcement point を具体化）／`Sensitive Data / Masking Policy`（同）／`Implementation Sequence Plan` の参照（写さず Stage ID と `AC-n` で引く。矛盾が出たら requirements 側を直し、必要なら human recheck に戻す）

## state.md セクション一覧

Gate Status と Reviewer Selection を `design.md` から分離した state-only ファイル。

1. Gate Status
   - `Entry Intent`（brainstorming 開始時に記録。下記「Entry Intent テンプレート」参照）
   - `Requirements Review Status`
   - `Planning Reviewer Selection`
   - `Design Review Status`
   - `Human Check Status`
   - `Resume From`
   - `Approved Direction`（human check 承認後に記録。以下のテンプレートで `state.md` に追記する）
   - `Plan Revision`（段階計画の最新 revision。レビュー Round とは別カウンタで、Round の正本は `reviews.md`。routing source にはしない）
   - `Current Stage`（現在実装・再設計・再承認の対象になっている Stage ID。未着手なら `planning`）
   - `Next Stage`（次に進む Stage ID。tasklist 未作成なら `task-breakdown`）
   - `Stage Continuity Source`（段階連続性の正本への参照。例: `requirements.md#Implementation-Sequence-Plan` / `tasklist.md#Execution-Plan`）
   - `Origin Session`（optional、write-once。起動元の cross-session 識別子。`references/phase-progression.md` § Cross-Session Messaging）

`state.md` の routing field（Tier 1 Core: `Resume From` / `Next Action` / `Human Check Status` / `Route In Progress`、および Review Status 群）は**現在値のみ**を持つ（旧値を残さない。`旧 Resume From:` のような履歴行を積まない）。累積追記 field（`Cumulative Diff Base` / `Approved Direction` 追加承認 / Hotfix 系 / `Planning Reviewer Selection` 等）は `references/state-field-tiers.md` の定義どおり履歴を保持する。route 判断の理由は 1 行要約 + `worklog.md` 参照にし、長い reviewer history、Fix Attempts の詳細、scenario eval の全文、HITL で却下された案の長い理由は `worklog.md` / `adr.md` に移す。Core field（`Resume From` / `Next Action` / `Human Check Status` / `Route In Progress`）は省略しない。

### Entry Intent テンプレート（正本）

```markdown
## Entry Intent
- 判定: new | resume | amendment | ambiguous
- 判定理由: <1 行で。例: "明示的な新規依頼 + active steering なし" / "resume cue + 単一 active steering" / "既存機能の amendment、anchor=<feature name>">
- 参照した正本: `references/entry-intent.md`
- 判定日時: <ISO8601 + TZ 付き、例: 2026-05-12T14:30:00+09:00>
```

- **記載位置**: `state.md` ファイル先頭側に **`## Entry Intent`（H2 見出し）** として独立配置する（`## Gate Status` の前または直後。`Gate Status` 配下の H3 ではない）
- **タイムスタンプ形式**: ISO8601 + タイムゾーン明示。JST なら `+09:00`、UTC なら `Z`
- brainstorming Step 2 で entry intent を判定したら、**必ずこの形式で `state.md` に記録する**
- `ambiguous` の場合は fail-closed 停止するため state.md は作成しない（または判定行のみ記録して停止）
- 後続 phase（completion-check / reviewer / pr-review）が「なぜこの phase 構成か」を再現できるよう、判定理由を 1 行で残す
- amendment 判定時は `anchor`（一意に紐付ける既存 feature / artifact 名）を判定理由に必ず含める

### Approved Direction テンプレート（正本）

```markdown
## Approved Direction
- 方向性: <human check で承認された目的の 1 行要約>
- 自走範囲:
  - 含むディレクトリ / モジュール glob: <例: src/auth/**, src/http/**>
  - 含む AC: [AC-1, AC-3]（省略時は全 AC）
  - 明示的に除外する範囲: <例: DB migration, logger 設定。省略時は除外なし>
- 自走上限: <値は human-check-template § 自走上限の置換値>
- 判断の委任: <fable | opus | 並行 | 人に止める>（最初の承認で書く。上げ下げは § 事前回答 5）
- 承認後の到達点: <PR 作成まで / deploy 手前まで / 実装完了まで。terraform apply / AWS write / DB write / Docker push は別途明示承認>
- Post-PR Completion Scope: <none / マージして再学習まで / post-merge verification / relearning まで。ユーザーが明示した場合は PR 作成までに丸めない>
- Post-PR 操作承認: <manual merge required / merge approved / deploy approval required / Requires explicit operation approval>
- 別途明示承認が必要な操作: <terraform apply / AWS write / DB write / Docker push / 本番デプロイ。非該当なら N/A と根拠>
- 人間に戻す条件: <満たせない見込み / AC・scope を削る・弱める / 信頼境界を緩める>
- 事前スキャンファイル数: <N>（Cumulative Changed Files の基準値。brainstorming 時の影響範囲スキャンで取得）
- 事前スキャン対象 glob: <brainstorming 時に実スキャンした glob パターン>
- 承認日: <timestamp>
```

- routing source にはしない（`Resume From` / `Next Action` が正本）
- `gdd-systematic-debugging` が自走範囲の判定に使う補助コンテキスト
- **自走範囲の判定**: `gdd-systematic-debugging` は「含むディレクトリ / モジュール glob」への glob マッチを第一基準とし、glob 外のパスに触れた時点で自走範囲外（`human_recheck_required` 相当）と判定する
- **事前スキャンファイル数**は `Cumulative Diff Base: <sha>` と合わせて `state.md` に記録し、`human_recheck_required` での新 Approved Direction 承認時に現 HEAD で更新する

### Stage Continuity State テンプレート（正本）

```markdown
## Stage Continuity
- Plan Revision: R1
- Current Stage: planning | S-1 | S-2 | ...
- Next Stage: workflow-handoff:task-breakdown | S-1 | S-2 | ...
- Stage Continuity Source: requirements.md#Implementation-Sequence-Plan
```

- `Current Stage` / `Next Stage` は resume / compact / human_recheck_required 後に「複数段階のどこにいるか」を復元するためのアンカーであり、routing source にはしない。routing は引き続き `Resume From` / `Next Action` が正本
- `Next Stage` は Stage ID か、まだ Stage 実行に入っていない場合の `workflow-handoff:<phase>` を使う。例: human-check 前は `workflow-handoff:task-breakdown`、実装中の次 Stage は `S-2`
- `Stage Continuity Source` は、tasklist 作成前は `requirements.md#Implementation-Sequence-Plan`、tasklist 作成後は `tasklist.md#Execution-Plan` を指す（単一段階 express は `N/A - single-stage express`）
