# Rollback Patterns

> **所有**: planning / design / build phase からの差し戻し時の Gate Status 更新パターン
> **上位正本**: `self-contained-contract.md`（差し戻し route 定義）、`state-machine.md`（遷移表）
> **参照元**: `gdd-design-gating`、`gdd-test-driven-development`、`gdd-subagent-driven-implementation`、`gdd-systematic-debugging`
> **Why**: 4 skill で同一パターンを繰り返していた差し戻し status 更新を 1 箇所に集約し、DRY を改善する

## 保存場所

差し戻し時の永続化先は `references/state-machine.md` の保存場所定義に従う。

- `Gate Status` / `Resume From`: active worktree 側 `state.md`
- `Next Action`: active worktree 側 `tasklist.md`

## planning_rework_required

前提や計画の組み直しが必要なとき。

| Field                      | Value                                                                                              |
| -------------------------- | -------------------------------------------------------------------------------------------------- |
| Requirements Review Status | `pending \| evidence: <planning-reopen-id> \| updated_by: <skill-name> \| updated_at: <timestamp>` |
| Design Review Status       | `pending \| evidence: <planning-reopen-id> \| updated_by: <skill-name> \| updated_at: <timestamp>` |
| Human Check Status         | `pending \| evidence: none \| updated_by: <skill-name> \| updated_at: <timestamp>`                 |
| Resume From                | `gdd-brainstorming`                                                                                |
| Route In Progress          | `planning_rework_required`                                                                         |
| Next Action                | `gdd-brainstorming`（`tasklist.md` が既にある場合）                                                |

古い `waiver_reason` を残さない。

## human_recheck_required

承認済みの要件・実装方針の狭い変更に人間判断が必要なとき。

| Field                      | Value                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------- |
| Requirements Review Status | `approved \| evidence: <requirements-review-id> \| updated_by: <skill-name> \| updated_at: <timestamp>` |
| Design Review Status       | `pending \| evidence: <human-recheck-id> \| updated_by: <skill-name> \| updated_at: <timestamp>`        |
| Human Check Status         | `pending \| evidence: none \| updated_by: <skill-name> \| updated_at: <timestamp>`                      |
| Resume From                | `human-check-waiting`                                                                                   |
| Route In Progress          | `human_recheck_required`                                                                                |
| Next Action                | `human-check-waiting`（`tasklist.md` が既にある場合）                                                   |

`Origin Session` 有時の起動元通知は `references/phase-progression.md` § Cross-Session Messaging に従う。

古い `waiver_reason` を残さない。

### Downstream Human Recheck Handoff

`Route In Progress=human_recheck_required` だけでは不十分であり、build / debug / completion の途中で人間判断へ戻す場合は、以下を人間向けの日本語で出力してから `<gdd-stop reason="human-check-waiting">` で停止し、マーカーの後に `## 👤 次にすること`（`references/output-format.md` § 停止時の「次にすること」マップ）を置く。次の判定は main が行う（subagent はこの判定をせず、`事前回答の適用:` の行も書かずに、Handoff を出力して止まる。main は受け取った後に `references/subagent-dispatch.md` § HITL Pending Hard Invariant のとおり扱う）。`Approved Direction` の `判断の委任` の欄が委任の値か、`worklog.md` に対象を含む `事前回答:` 行があれば、出力の前に `references/human-check-template.md` § 事前回答 2・3 で扱う（適用は出力の代わりになる）。

- **前置き 3 行**: `**依頼**:`・`**なぜやるか**:`・`**現在地**:`（`references/human-check-template.md` § 判断の書き方 2）
- **いまの結論**: どこまで進み、なぜここで人間判断が必要か
- **ここまで出来ていること**: 実装済み内容、通ったテスト、再実行で確認したこと
- **まだ確認できていないこと**: 未確認 evidence、評価用サンプル、人間確認待ち、本番に近い条件での検証など（項目ごとに先頭に種類。`references/common-guardrails.md` § Honest Limitations）
- **次に決めてほしいこと**: 書き方は `references/human-check-template.md` § 判断の書き方。`案A` / `案B` の選択肢（判断ポイントごとに、`おすすめ` の案について `- 依頼との差: なし` を 1 行。`おすすめ` を依頼より狭くせず、狭める案は採用しない案に変わる AC を書いて並べる〔`あり: <その項目>` の点がある確認は、表示の時点で出し直しになる〕。マーカーの直前の `<gdd-hitl-fields ...>` タグに、点の順に `none`/`differs` を並べた `request-diff` を置く）、`おすすめ`、`迷う場合` の返答導線。`おすすめ` の後に、main が `references/human-check-template.md` 一次表示の原則 7 のとおり `相談役の推奨:` の行を足す（相談役の返りを待たずに表示する。返った後に全文を出し直すかは同 一次表示の原則 7 と § 止まり直さないもの 2）（Handoff を出す subagent は書かない）
- **返答例**: ユーザーがそのまま返せる短い文

内部用語をそのまま並べない。`holdout` は「評価用に取り分けたサンプル」、`human-confirm` は「人が内容を確認済みにする」、`executable` は「自動テストやコマンドで実行できる状態」、`no-post` は「外部投稿しない」、`prod_equivalent` は「本番に近い条件で検証する」、`production model env` は「本番相当のモデル設定」として先に言い換える。

**gdd-completion-check の Round 上限超過**（`Pre-PR Fix Attempts` の上限と、`references/independent-review.md` の (3-f) の取り直しでも high・blocking が残ったときも、この 4 択を使う。(3-f) から着いたときも、次の差し戻しは昇格処理の手順 1〜3 のとおり新値で決まる〔3 以上ならこの 4 択。取り直しは使用済み〕）: `Next Action` は本表と異なり `gdd-systematic-debugging` を使う（`Next Action` 許容値表を変えないための、Round 上限超過のときだけの例外）。`Resume From` / `Human Check Status` / `Route In Progress` は本表どおり。この 1 点の逸脱は `references/state-machine.md` § Resume 時の state 整合性検証 の検証項目 1 で明示的に許容されており、再開時に state 不整合として fail-closed しない。方式転換 4 択（task 撤回 / 再設計 / 依頼の範囲を変えるかを人に問う / 限界として開示して人に渡す）を Downstream Human Recheck Handoff の出力手順に従って提示する。再設計の案で、残った指摘と依頼の未達を生んだ設計の決定・前提を名指しする（案の数は増やさない）。推奨は再設計を先に比べ、閉じる再設計が無いときに、依頼の範囲を変えるかを人に問う案か、限界の開示を推す（`references/common-guardrails.md` § 選ぶときの基準 2）。各案には、その案を選んだ後に PR を作れる見込みを 2 点書く。(1) completion-check を差し戻し無しで通れるか（`Completion Rounds` は `human_recheck_required` では戻らないので、次の Round で blocker が 1 件出ればまたこの確認に戻る）。(2) その後の pre-PR gate の条件（`Pre-PR Self Review` の `dry: yes`、`Independent Review` の high 0 かつ blocking 0。後者の正本は `references/independent-review.md`）を満たせるか。「限界として開示して人に渡す」は、残る high・blocking が 1 件以上あり、そのすべてが人が承認した限界に当たるときだけ選択肢に置く。人が承認した限界とは、`Human Check Status=approved` 時点の `requirements.md` § Honest Limitations、Correction Log（人の修正指示から書く記録）、または human check への人の返答に記録があるものをいう。`adr.md` や PR に入る ADR の記載は、これらの出典を併記したものだけを数える（agent が人の承認なしに書けるため）。依頼の原文から外れた限界（`Request Drift`）は、この出典があっても、`agents/gdd-completion-reviewer.md` の 9 が承認の記録に数えるものだけを数える。実害クラスも、人が承認していれば含めてよい（`skills/gdd-pr-review-followup/SKILL.md` の既知の限界と違い、この案は件数を変えずに人に渡して止まるため）。メニューには、限界ごとに種類（`references/common-guardrails.md` § Honest Limitations）と承認の出典を書き、返答例には案の名前を入れる。このメニューへの返答のうち、4 つ目を選ぶものと案を名指ししないもの（「OK」「おすすめで」など）は、`commands/gdd-dev.md` #10 STEP 1 が STEP 2 と `references/human-check-template.md` の共通の承認後処理に通さずに分ける。案を名指ししない返答には、おすすめの案を名前で復唱して確かめ、4 つ目なら下の手順に進み、1〜3 つ目なら名指しの返答を待つ。4 つ目を選んだ後（`worklog.md` にその行があるとき）に届く承認に見える返答も STEP 2 に通さず、マージ後に cancelled にする案内を繰り返す。選ばれたら、`Independent Review` 行は実際の件数のまま残し（0 に書き換えない）、`state.md` の値も Round 上限超過で書いたまま変えない。`handoff/completion_check.md` の末尾に見出し `## PR 本文の草案（限界として開示して人に渡す）` を追記し（既存の節を上書きしない）、その下に PR 本文の草案を書く。草案の先頭には「直していない high・実害クラス」の節（常時 High を先頭に、1 件ずつ内容・直していない理由・影響・承認の出典）を置く。草案と `git diff origin/<default-branch>...HEAD` に `skills/gdd-pr-review/SKILL.md` の 3d（秘密情報）の確認をかけ、結果を草案に書く。草案の限界には次を書く：pre-PR gate の検査（completion-check の通過、`Pre-PR Self Review`、ADR の蒸留、Codebase Health、PR 本文の機密チェック）は走っていない。この steering では PR 後の followup と post-merge QA を GDD で行わない（agent の再 push にも pre-push gate が同じ述語を要求するため）。steering は待ち状態のまま残り、再開すると同じメニューが出るので、PR のマージ後に `references/self-review-lanes.md` § 使わないステアリングの終え方 で cancelled にする。`worklog.md` に選ばれた案と人の返答を 1 行書き、`git push` と `gh pr create` は人が自分の端末で行うよう案内して止まる。agent は push も PR 作成もせず、kill-switch（全 hook が止まる）も `GDD_SKIP_PRE_PUSH_GATE=1`（pre-push gate の通知の文が案内する）も使わず、案内もしない。`Pre-PR Fix Attempts` の上限（`references/post-completion-pr-flow.md` の昇格処理の順序 3）で止めたときも、このメニューを同じ手順で使う。そのときの (1) の注記は「`Pre-PR Fix Attempts` も戻らないので、次の差し戻しでまたこの確認に戻る」と読み（(3-f) の取り直しの上限から着いたときは「次の差し戻しは新値で決まり、3 以上ならまたこの確認に戻る」と読む）、4 つ目の草案の限界の括弧からは「completion-check の通過」を除き（completion-check は通っている）、「Round 上限超過で書いたまま」は「`Pre-PR Fix Attempts` の上限（または (3-f) の取り直しの上限）で止めたときに書いたまま」と読む。この 4 択で止まる遷移（上の state の組）を書く側（completion-check を走らせる gate runner、`references/post-completion-pr-flow.md` の昇格処理の順序 3 を行う側。inline なら main。worker 経由なら結果を統合する main で、worker は書かない）は、同じ手順で `references/human-check-template.md` § 事前回答 3 の `上限到達:` 行を書く（語は、Round 上限なら `completion-round-limit`、`Pre-PR Fix Attempts` と (3-f) の取り直しの上限なら `pre-pr-fix-limit`。形と、表示し直しでは書かないことは同節が正本）。

### Cumulative Diff Base の再計測（新 Approved Direction 承認時）

`human_recheck_required` で Approved Direction が変わると、旧 base（旧 N での事前スキャンファイル数）は新 scope に対して stale となる。旧 base を残したまま impl-gate「前回の 2 倍以上」判定を行うと silent pass（例: 旧 N=50・base=150 → 新 Approved N=10 承認後、45 変更が base=150 下で silent pass）が発生する。

- 新 Approved Direction が human-check で再承認された時点で、`Cumulative Diff Base` を **再計測して `state.md` に追記**する（上書きせず履歴として追記し、最新行を最新基準とする）
- 保存先は `state.md` の `Cumulative Diff Base` field（schema は `state-machine.md` の該当セクション参照）
- 追記行の理由 field に `recalibrated_after_human_recheck: <旧 recorded_at ISO> -> <新 recorded_at ISO>` を付記し、監査時に旧 base が stale 化した契機を特定可能にする
- `Why:` human_recheck で Approved Direction が狭まった後に旧 base が残り silent pass 化する経路を塞ぐ

### Refactor Gate の追加リセット（drift 経由で発火した場合）

`Scope Drift Guard` / `E2E Discovery Loop` 経由で `human_recheck_required` が発火したときは、Approved Direction の範囲が変わるため Refactor Gate の既存判定も無効化する。以下を併せて実行する:

- `Refactor Gate Status`（`tasklist.md` の `Review Status` 節）は、再承認の後の task-breakdown の作り直しで消える（`absent`）。別にリセットしない。reset 理由だけを worklog に `Refactor Gate Reset: approved-direction-widened` で記録
- 既存 Refactor Task（`R-1` 等）も、同じ作り直しで tasklist から除去する（`Completed Tasks` にあって `Reviewed by:` があるなら、先に `Pending Tasks` へ移す書き込みを挟む。`references/task-breakdown-steps.md` 手順 2）。worklog.md に reset 記録を残す（監査用）

**Why**: Refactor Gate は「Approved Direction 範囲内での重複排除・命名統一」を前提に走査する。human_recheck で Approved Direction が広がると、以前の Refactor 計画は前提を失う。作り直しで `Refactor Gate Status` が `absent` になり、build 完了後に `gdd-implementation-gating` の absent の分岐が `gdd-refactor-planning` へ進めるので、新 scope に対する再評価が保証される。

## design_detail_only

要件は変わらないが detailed design の修正が必要なとき。

| Field                      | Value                                                                                                      |
| -------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Requirements Review Status | `approved \| evidence: <requirements-review-id> \| updated_by: <skill-name> \| updated_at: <timestamp>`    |
| Design Review Status       | `changes_requested \| evidence: <design-reopen-id> \| updated_by: <skill-name> \| updated_at: <timestamp>` |
| Human Check Status         | `approved \| evidence: <元の evidence> \| updated_by: <skill-name> \| updated_at: <timestamp>`               |
| Resume From                | `gdd-design-gating`                                                                                        |
| Route In Progress          | `design_detail_only`                                                                                       |
| Next Action                | `gdd-design-gating`（`tasklist.md` が既にある場合）                                                        |

- final output owner / delivery path / prompt-output contract / masking enforcement / rollout order が human 承認済み policy から変わる場合は、この route を選ばない。
- E2E Discovery Loop 自走中は、`Approved Direction` の自走範囲内であれば human check に戻さずこの route で閉じてよい（自走条件の詳細は `references/phase-progression.md` の「E2E Discovery Loop」を参照）。
- **記録要件（必須）**（`references/adr-vs-design.md` の書き分けルールに従う）: この route を通過して `Design Review Status=approved` に戻す前に、以下を同じ diff 内で必ず更新する:
  - `design.md`: 変更の該当セクション本文を**現在の正しい設計に上書き更新**する（差分は git で見る）
  - `adr.md`: `Context` / `Decision` / `Why` / `Consequences` を追記
  - 記録が欠けている場合、`gdd-design-gating` は `approved` にしない。反映忘れは completion-check / pr-review の Spec Drift Check で遅れて検出されるが、手戻りが大きくなるため route 通過時点で記録する
- **AC 影響時の escalation**: 以下のいずれかに該当する場合は自走範囲外として `human_recheck_required` に昇格する:
  - AC の根本追加 / 削除 / 意味変更（境界値・許容値の変更を含む）
  - `Approved Direction` の方向性自体が変わる
  - final output owner / delivery path / prompt-output contract / masking enforcement / rollout order の変更
  - **方向性 metadata 変更**: storage engine（例: S3 → DynamoDB）、query engine（例: Athena → Redshift）、framework / runtime / protocol 等のコア技術選定が変わる method-only 変更は、ファイル差分が少なくても `design_detail_only` に含めず `human_recheck_required` に昇格する
  - AC の表現揺れ（言い回しの整理、用語統一）だけなら `design_detail_only` のまま続行可能

- **method 変更時の adr.md 義務化**: method（実装手段 / 選択技術）が変わる場合は `design_detail_only` route 内であっても `adr.md` に Before / After を必ず追記する（記録要件の一部。欠落時は `approved` に戻さない）

- **Counter マトリクス**（Scope Drift Counter の +1 判定。詳細な counter 定義は `state-machine.md` 参照）:
  | 変更分類 | Counter | route |
  |---------|---------|-------|
  | naming / comment only（振る舞い不変） | +0 | `design_detail_only` |
  | method-only（方向性 metadata 外の実装手段変更） | +1 | `design_detail_only` |
  | 方向性 metadata 変更（storage / query engine / framework 等） | Counter 対象外 | `human_recheck_required` に昇格 |

- **Approved Direction glob 粒度 guard**（自動 lint 化済み）:
  - **自動 lint script**: `scripts/lint-approved-direction.py` が以下を機械的に検査する。`gdd-systematic-debugging` が `design_detail_only` 判定前の Step 3c で呼び出す
    - 単一ファイル固定 glob を検出 → **exit=1**（ERROR、route を進めない）
    - 全域 glob × security-sensitive marker の交差を検出 → **exit=0** + WARN（`human_recheck_required` 昇格を検討）。`WARN: human-evidence`（`references/post-merge-qa.md` § 入口と手順 2 の形を自走上限と evidence が満たさない理由。`references/human-check-template.md` § 事前回答 2）は route 判定に使わない
    - script 引数: state.md パスを渡すと Approved Direction block から glob を抽出（正本の見出しの形では `含むディレクトリ / モジュール glob:` の欄と続きの箇条だけを読み、自由文の欄は読まない。欄に glob の形〔`/` を含み `*` などを含む語か、`src/foo.ts` のような単一ファイル〕でない語〔`S-1/S-2`、`**` の無い `src/foo` など〕か、`!`・`-` で始まる否定の語〔`!src/legacy/**`〕が 1 つでもあれば欄を読まず、`WARN: glob field not read` を出す。colon の形では `自走範囲` の値・欄名の無い続きの行・glob の欄のうち、語がすべて glob の形でパスと glob の記号だけの行に glob が無いとき〔`戻し条件` などの glob、`リポジトリ全体、src/legacy/** は除く`・`** except src/legacy/**` のように自由文と並べた glob、`!` の否定、欄名つきの続きの行〔`明示的に除外する範囲:` など。glob の欄を除く〕の下の箇条の glob は lint するが数えない〕も含め、欄が無いときと読まないときは `INFO: no Approved Direction patterns found` で exit=0 になるが、glob を検査していないので合格に数えず、自走範囲を手で照らす） / `--pattern <glob>` で個別検査可
  - **単一ファイル固定 glob の禁止**: `src/foo.ts` のような単一ファイル固定 pattern を Approved Direction に書かない。最低限「ディレクトリ単位」の glob（例: `src/foo/**`）で記述する
    - `Why:` 単一ファイル固定だと rename / split で Approved Direction 外判定になり、実質的な振る舞い不変の編集でも silent に過剰発動する
  - **全域 glob × security-sensitive path の交差昇格**: `**/*.ts` のような全域 glob が Approved Direction に含まれる場合、security-sensitive path list と交差する変更は `design_detail_only` から除外して `human_recheck_required` に昇格する
    - security-sensitive path list の参照先: `references/reviewer-selection.md` の `gdd-security-reviewer` 起動条件（auth / authz / secrets / PII / untrusted input / webhook payload / installation token 等）に該当する path。既存の reviewer selection 条件をそのまま path 判定に流用する
    - 例示（reviewer-selection.md に定義が無い環境でのフォールバック）: `**/auth/**`, `**/secret*/**`, `**/webhook*/**`, `**/payload*/**`, 認証トークン / 署名検証 / PII を扱う module path
    - `Why:` 全域 glob を許すと security-sensitive な method 変更も `design_detail_only` に吸収され silent merge される経路が開く

## implementation_fix_only

build 内で閉じられるとき。`Resume From` は変更しない。

| Field             | Value                                                  |
| ----------------- | ------------------------------------------------------ |
| Route In Progress | `implementation_fix_only`                              |
| Next Action       | `gdd-subagent-driven-implementation`（実装修正の場合） |
| Next Action       | `gdd-implementation-gating`（修正後の再審査の場合）    |

- `Gate Status` / `Resume From` は変更しない。active worktree 側 `tasklist.md` の `Next Action` だけを戻り先に更新する。
- `Route In Progress` は `state.md` に記録する。route の修正が完了し impl-gate を通過した時点で `none` にクリアする。**RED 再現テスト必須化（実害クラス / High）**: 対象 finding の category が実害クラス（値域の正本は `references/reviewer-common.md` § finding category）、または severity が `High` の場合（文言・帳簿の指摘は対象外）、`implementation_fix_only` の復帰シーケンスは次の順序に固定する: 1. 指摘が再現する RED テストを書き、失敗することを確認する（テストが無ければ追加する。既存テストで再現できても、`gdd-implementation-gating` Step 1d は差分にも未 commit の分にも無い `test:` のファイルを差し戻すので、再現テストは差分に入る形〔新しいテスト、または既存テストへの追加・変更〕で書く）→ 2. 実装を修正する（テストは変更しない）→ 3. テストが通ることを確認してから `gdd-implementation-gating` へ進む。再現テストは remediation 完了後も suite に残す。後続の簡素化・リファクタでこの修正が消えた場合に、再現テストが機械的に RED へ戻ることで回帰を検出する。対象外の finding（文言・帳簿の指摘、および実害クラスでも `High` でもない finding）は、上の固定の順序を当てずに「§ 直し方 → 実装修正 → impl-gate」で進めてよい。どちらの finding でも、実装を修正する前から `references/self-review-lanes.md` § 直し方 に従う（1・2 を当てない修正は同節の冒頭のとおり）。実害クラス・`High` では、§ 直し方 2 が求めるテスト（境界・fail-open・欠陥の種類ごと）もすべて 1. の段で書き、2. ではテストを変えない（2. で修正の分岐が変わったら 1. に戻ってテストを足し、落ちることを確かめる。修正の前から通るテストは RED に数えない）。**修正の commit 規律**: 実装修正の commit には、指摘への対応以外（簡素化・スコープ縮小・無関係な変更）を混ぜない。同じ commit に混ぜると、次の独立レビュー / completion-check の差分スコープ（`references/gate-checklists.md` § Checklist E、`references/independent-review.md` の 2 回目以降の起動範囲）が指摘への対応以外まで巻き込み、レビュー範囲が不必要に広がる。**Why**: 実害クラス・`High` の finding は復旧コストが最も高い。修正が「効いているように見えるが実は再現条件を外している」誤りを防ぐには、修正前に失敗する再現テストが要る。RED を経ない修正は、reviewer が次周回で同じ finding を再検出するまで気付けない。

## Route In Progress のクリア

route の修正が完了し次の phase に正常遷移した時点で、`state.md` の `Route In Progress` を `none` にクリアする。クリアの責務は遷移先の skill が持つ:

| Route                      | クリアする skill            | タイミング                                                                                           |
| -------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------- |
| `design_detail_only`       | `gdd-design-gating`         | design gate 通過後、`gdd-task-breakdown` に handoff する直前                                         |
| `implementation_fix_only`  | `gdd-implementation-gating` | impl gate 通過後                                                                                     |
| `human_recheck_required`   | `commands/gdd-dev.md` STEP 2 | human check 承認時（`references/human-check-template.md` § 共通の承認後処理の無条件クリアと同時。`gdd-design-gating` は既にクリア済みの値を再確認するだけで、二重にはクリアしない） |
| `planning_rework_required` | `gdd-requirements-gating`   | requirements gate 通過後                                                                             |

requirements・design の Round 上限の一括提示で止まるときも `none` にする（`references/requirements-gating-steps.md` § 一括提示への返答 で選ばれた案が route を書き直す）。

## ターミナル状態でのクリア

`Next Action` が `done` または `cancelled` に遷移するとき、`Route In Progress` が `none` 以外で残っていれば `none` にクリアする。ターミナル状態では route の文脈は不要であり、残すと次回の steering 解決で stale metadata が候補判定を汚染する。

| 契機        | クリアする skill       | 対象                     |
| ----------- | ---------------------- | ------------------------ |
| `done`      | `gdd-completion-check` | `Route In Progress=none` |
| `cancelled` | `gdd-completion-check` | `Route In Progress=none` |

**Why:** reroute 中にキャンセルされた場合や、外部前提不足で `gdd-completion-check` を繰り返した後に `done` に達した場合、`Route In Progress` が孤立するのを防ぐ。

## Reviewer Loop Escape Hatch

同じ `Current Task` に対して `changes_requested` が 5 回連続（`implementation_fix_only` と `design_detail_only` の合計。Gate Batch では finding の対象になった task ごとに数える。`state-machine.md` § Remediation Loop Safety）で返された場合、route 判定を無視して **route recalibration checkpoint** を強制適用する。

- 判定正本: `tasklist.md` の `Fix Attempts` + `worklog.md` の Error Log（両者が食い違う場合は大きい方）。planning 差し戻し後の tasklist の作り直しをまたぐと数えは途切れる（`state-machine.md` § planning 差し戻し後の tasklist.md リセット）
- procedural / evidence only（例: `Reviewed by:` 欠落、verification wording 不整合、reviewer evidence 整形ミス）なら **`human_recheck_required` を使わず**、`gdd-systematic-debugging` が failing gate の再実行条件を整える。必要なら `blocked` で具体的な修正手順を返す
- policy / scope / ownership / security boundary / prompt-output contract の変更が必要なら、上記 `human_recheck_required` パターンを適用する
- `human_recheck_required` を選んだ場合だけ、`Human Check Questions` に「5 回連続 `changes_requested` により自動エスカレーション」の旨と、解消できなかった findings の要約を記載する

**Why:** `implementation_fix_only` の 3 回制限は `design_detail_only` への昇格で回避される。`design_detail_only` 後にさらに `changes_requested` が繰り返される場合、AI だけでは構造的問題を解決できない兆候ではあるが、それが直ちに人間再承認を意味するわけではない。方向性の変更が無い procedural / evidence blocker まで `human_recheck_required` に倒すと、human check が過剰に増える。

## 使い方

各 skill は差し戻しが必要なとき、このファイルの該当パターンに従って Gate Status を永続化する。`<skill-name>` は呼び出し元の skill 名（例: `gdd-design-gating`）に置き換える。
