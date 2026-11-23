---
# SYNC: bundle 版 `skills/gdd-pr-review/references/pr-review.md` も pr-review plugin 更新時に同期すること。
name: gdd-pr-review
version: 0.4.0
description: "Use for GDD-aware final diff review before PR creation, PR update, merge readiness, or final verification."
---

# Workflow PR Review

`gate-driven-development` の generic PR review 入口。`pr-review` skill の全手順を実行した上で、GDD 固有のチェックを追加する。

## Fixed Model

- `Claude Code`: `opus` + `effort=high`
- `Cursor`: `Grok 4.6` + `reasoning.effort=high` / `Codex`: `gpt-5.6-sol` + `reasoning.effort=high`（general_heavy_risk tier）
- 2026-08-25 に light_task から昇格。根拠は 2026-08-22 の調査 — gate 通過後に残った実害級の欠陥を検出したのは、当時の Opus + effort=high の最終レビューだけだった。詳細は `references/fixed-models.md`
- PR review 判断の品質確保のため mini は使わない。実際の diff レビューは Opus reviewer agent に dispatch する
- Claude Code では実行中モデルを skill 内から切り替えられない。現在のセッションモデルが `sonnet` 以下の場合は、続行前に乖離と影響（検出力低下）を明示して 1 回だけユーザー確認を取る（`gdd-model-routing` § 判断の優先順位 1 と同じ規約）

## When to use this skill (vs `gdd-implementation-gating`)

PR 作成直前 / マージ前の最終 review 専用。**実装直後の formal gate には使わない**（その場合は `gdd-implementation-gating`）。

| 状況 | 使う |
|---|---|
| 「PRレビューして」「差分チェックして」「マージ前に確認して」「PR作る前に見て」「この差分を見て」 | この skill |
| `gdd-completion-check` の Post-Completion PR Flow からの自動呼び出し | この skill |
| 「実装レビューして」「formal gate 通して」（実装直後の文脈） | `gdd-implementation-gating` |
| `Next Action=gdd-implementation-gating` の auto-route | `gdd-implementation-gating` |
| 「コードレビューして」（曖昧） | tasklist の `Next Action` が impl-gating なら impl-gating、それ以外で PR 作成直前なら本 skill |
| 追加で security / final companion review を別レーンで入れたい | `gdd-requesting-code-review` |

判断に迷う場合は `references/skill-responsibility-matrix.md` § Pair 1 を参照。

## When to use (実行契機の補足)

- 文章・コード・Terraform を含む通常の PR review
- PR を作る前に review / fix のサイクルを回したいとき
- `gdd-completion-check` の Post-Completion PR Flow から自動的に呼ばれる（セルフレビューとして機能する）
- ただし、ユーザーが明示的に `gdd-requesting-code-review` を指定した場合はそちらを優先する

## 手順

1. **pr-review skill を実行する** — Skill tool で `pr-review` を呼び出す。Skill tool が使えない（formal-gate-runner の中など、`tools:` に Skill が無い場合を含む）か、インストールされていない場合は `skills/gdd-pr-review/references/pr-review.md` を Read して内容に従う。PR 分類 → model routing → review → Pre-PR loop → PR 作成前チェックリスト Steps 1-4 を実行する。
   - **停止条件の上書き**: GDD では、bundled か上流 plugin かを問わず `pr-review` の loop 終了条件と PR 作成前チェックリストの停止条件を **High finding も実害クラスの finding も 0** と読み替える（正本: `references/post-completion-pr-flow.md` 手順 3・4。bundled `skills/gdd-pr-review/references/pr-review.md` 側は上流 `pr-review` plugin との SYNC 対象なので書き換えない）
2. **GDD 固有のチェックを追加する** — `pr-review` の PR 作成前チェックリスト Steps 1-4 が全て完了したら、引き続き以下の追加チェック（2a, 2b, 3a, 3b, 3c, 3d, 3d-2, 3e, 3f, 3g, 5, 6）を実施する

PR Body の WHY / Issue 参照 / Boundary・Follow-up / Confidentiality / マージで起動する workflow / 自律判断 / Advisory Findings の 7 チェックは `references/post-completion-pr-flow.md` § PR 作成手順（PR Body WHY Check / Issue Reference Check / PR Body Boundary / Follow-up Check / PR Body Confidentiality Check / PR Body Merge-Triggered Workflows Check / Autonomy Decisions Check / Advisory Findings Check）が正本。本 skill から `gh pr create` する場合も同チェックを適用し、欠落は High finding として PR 作成を止める。PR 本文など人間向けの文章を書くときは `references/japanese-writing-norm.md` に従う。

**直す順序**: 本 skill で指摘を直すとき（Pre-PR loop と、手順 2 の追加チェック〔3a・3b でその場で直す分を含む〕）は、bundled か上流 plugin かを問わず `references/self-review-lanes.md` § 直し方 に従う（4・5 の記録先は同節）。

## GDD 固有チェック（pr-review の Steps 1-4 に続けて実施）

### 2a. Evidence Before PR Claims

PR 作成直前の発言にも `gdd-completion-check` と同じ evidence discipline を適用する。`PR 作成可` / `review clean` / `問題なし` / `High なし` と言う前に、少なくとも以下を fresh に確認する。

- diff scope: `git diff <default-branch>...HEAD` の対象と steering scope の対応
- findings: High / unresolved Medium / advisory の分類
- secret scan: AWS アカウント ID、秘密鍵、`.env`、API key、access token、Secrets Manager / SSM 実値
- test / build / lint / verifier: 今回の PR で必要な fresh evidence
- external evidence: required security evidence / rendering evidence / CI log など、該当タスクで要求されたもの

証拠なしに成功表現を使わない。確認できていない項目は `未確認` / `unsupported` / `N/A` を区別して報告し、`問題なし` に丸めない。

### 2b. Self Review 証跡の記録（`git push` / `gh pr create` の前・常時）

出荷 hook（pre-push gate・pre-PR gate）は止めずに通し、不足を **実行後に通知して would-block を記録する**ので、レビューが収束したら証跡を `<steering-dir>/state.md` に書いてから push / PR 作成へ進む。書式・key の正本は `references/self-review-lanes.md`。

```
Pre-Push Self Review: <sha> | rounds: <N> | consecutive_clean: <0|1|2> | dry: <yes|no> | lanes: internal=<n>,grounding=<n|not_applicable(<reason-token>)>,adversarial=<n|not_applicable(independent-review)> | at: <ISO 8601>
Pre-PR Self Review: 同型
```

- **`Pre-Push Self Review` は初回 push から要る**。PR がまだ無い段階でも pre-push gate は発火するため、`gdd-pr-review-followup`（PR 作成後のレーン）を待たない
- `sha` は **push 対象 ref の tip** と一致させる（短縮 sha 可）。tip が進んだら証跡も更新する
- `Pre-PR Self Review` は `gh pr create` の前に書く。standard は **`dry: yes` 到達が必須**（dry = その周回で新規 high / blocking ゼロ。**2 連続要件は 2026-09-06 に撤廃**。正本 `references/self-review-lanes.md`）
- Task Size 別: `trivial` は両方とも不要 / `quick (express)` / `quick (standard)` は記録するが `dry: yes` は要求されない（pre-push gate が複数の steering から push 対象 tip の証跡で 1 件を選んだときは、Task Size によらず standard として検査する）
- `dry: yes` かつ `consecutive_clean` が 0 は自己矛盾として invalid になる
- **standard の push 前は「内部整合レーン 1 周 ＋ 独立レビュー 1 回」**。3 レーン自己周回は回さない（接地・敵対の観点は独立レビューが担う）。手順は次の 3 つだけ:
  1. 内部整合レーンを 1 周回し、新規 high / blocking ゼロを確認して `Pre-Push Self Review`（`consecutive_clean` は 1 以上）を書く
  2. 独立レビューを 1 回起動し、`Independent Review` 行（sha = push 対象 tip、`high: 0` かつ `blocking: 0`）を `state.md` § Gate Status に書く。**起動方法・観点レーン・出力フォーマットの正本は `references/independent-review.md`**。default branch を取り込むだけの merge commit では、取り直さずに `references/self-review-lanes.md` § Independent Review の引き継ぎに従ってよい
  3. `Pre-Push Self Review` の接地・敵対レーンは独立レビューへ委譲したと記録する（`grounding=not_applicable(independent-review),adversarial=not_applicable(independent-review)`）。回していないレーンに `0` を書かない。この委譲記録形は **`standard` でのみ valid**（`quick (standard)` / `quick (express)` では invalid になる）
- 独立レビューの `Independent Review` 行は standard の pre-push gate（push 対象 tip と比べる）と pre-PR gate（HEAD と比べる）が機械検査する（欠落 `independent-review-missing` / sha 不一致（`references/self-review-lanes.md` § Independent Review の引き継ぎで引き継げるときを除く）`independent-review-stale` / `high > 0` または `blocking > 0` `independent-review-high` を実行後に通知し、would-block を記録する。止めはしない）。`quick (standard)` / `quick (express)` / `trivial` は免除（pre-push gate が複数の steering から push 対象 tip の証跡で 1 件を選んだときは、Task Size によらず検査する。`references/self-review-lanes.md` § blocked steering の扱い）

**Why**: この 2 つの gate は per-command の逃げ道を持たない（pre-push のみ `GDD_SKIP_PRE_PUSH_GATE=1`、pre-PR は kill-switch のみ）。証跡を書く手順が本 skill に無いと、レビューを最後まで回したのに push / PR 作成のたびに不足の通知が出る。

### 3a. Spec Drift Check（AC / design / ADR 整合確認）

`gdd-completion-check` の AC Drift Check と同等の**実装 → artifact 逆方向整合**を PR 作成直前に再実行し、依頼の原文（`request.md`）とも突き合わせる。completion-check 通過後に E2E や hotfix で追加した変更の反映漏れを最後に捕まえる safety net。

- `git diff <default-branch>...HEAD` の全差分を読み、**外部観測可能な挙動**（新規エンドポイント / 新規 field / 新規 CLI オプション / 新規環境変数 / 新規 UI 要素 / 新規エラーメッセージ / 境界値変更 / 新規ログ形式等）をリストアップする
- 各挙動が `requirements.md`（AC）・`design.md`・`adr.md` のいずれかに対応記載があるかを照合する。steering に `request.md`（依頼の原文。trivial には無い）があれば最後まで読み、依頼の語ごとに差分が届けるものと突き合わせる。探す型・承認の記録の扱い（無ければ未承認）と、先頭が `<!-- gdd-request-capture:not-copied -->` の request.md の扱いは `agents/gdd-completion-reviewer.md` の 9 と同じで、どれも High finding にして PR 作成を止める。このずれは下の AC・ADR の追記では閉じず（依頼より広げた分の revert は、依頼に合わせて直すに当たる）、依頼に合わせて実装を直すか、`human_recheck_required` に戻してユーザーに確かめ、その発言を `request.md` に足して解消する
- 記載のない挙動がある場合は **High finding** として PR 作成を止め、以下のいずれかで解消してから再実行する:
  - AC に追記（scope 内の軽微な追加）→ `requirements.md` 更新
  - 対応 ADR を追記（設計判断として残す）→ `adr.md` 更新
  - scope 外として revert（無関係な変更）→ 該当 commit を revert
  - AC の根本追加/削除を伴う場合 → `human_recheck_required` に戻す（PR を作らず planning に戻る）
- artifact の言語規約と記載言語の一貫性も合わせて確認する（英語 AC に対して日本語 ADR を混在させない等）

**Why**: completion-check の AC Drift Check を通過した後でも、PR 作成直前の追加 commit（typo fix / lint fix と思っていたら挙動に影響していた等）で drift が再発することがある。PR 公開前の最後の検出点として残す。依頼の原文との突き合わせは、AC 自体が依頼からずれたもの（AC の照合では見えない）を捕まえる。

### 3b. Migration / Conversion Content-Diff Check（該当タスクのみ・最後のセーフティネット）

`requirements.md` に `タスク種別: migration/conversion` が記載されている、または AC に `AC-F1` / `AC-F2` / `AC-F3` / `AC-F4` が含まれている場合のみ実施する。該当しない PR ではこの追加チェックを実行しない。

1. **変換元ファイルの特定**: `git diff --name-only <default-branch>...HEAD` で削除または大幅変更されたファイル（旧フォーマット）と新規追加されたファイル（新フォーマット）をペアにする
2. **原文キーワード抽出**: 削除された各旧ファイルから以下を抽出する:
   - URL（`https?://` で始まる行）
   - 注釈記号 + 本文（`※1` / `※2` / `(※...)` 等）
   - Slack チャンネル（`#foo`）、GitHub user / team（`@user`、`@team`）
   - 手順リンク（社内 wiki / Notion / Confluence / スプレッドシート ID 等）
   - 例示（`例:` / `（例）` で始まる行、具体値を伴うサンプル行）
3. **新ファイルへの存在確認**: 抽出したキーワードごとに、対応する新ファイル（または新フォーマット全体）に `grep` で存在するかを確認する。**完全一致でなくても、description / options / placeholder / value のいずれかのフィールドで参照可能なら OK**
4. **欠落した項目は High finding**: 1 件でも抽出キーワードが新ファイル群で見つからなければ High finding として報告し、PR 作成を止める
5. **変換先ネイティブ機能の活用確認**: 新ファイルが変換先フォーマットのネイティブ機能を使っているか確認する:
   - 単一値に対して `type: input` / `<input>` 相当が使われているか
   - 列挙に対して `type: dropdown` / `checkboxes` / `<select>` 相当が使われているか
   - 表 markup を `type: textarea` の `value:` に丸ごと埋め込んでいないか
   - 不備があれば Medium 以上で報告する
6. **レンダリング確認 evidence の有無**: `Verification` に AC-F4 の evidence（スクリーンショット / 実環境ログ / ブラウザ確認結果）があるか確認する。無い場合は Medium finding として PR 本文に「レンダリング未検証」を明示するよう指摘する
7. **無限ループ防止（escape hatch）**: `references/bounce-log-schema.md` の共通仕様に従う。bounce log 名 `PR Review Bounce Log` / identifier-key `file_path + missing_keyword` / 閾値 `>= 2` / escalate 先 `gdd-systematic-debugging`（schema の既存実装一覧参照）。2 回目の検知時は schema の「発動時の出力テンプレート」を使い、`Reason` に「変換ロジック自体の見直しが必要。個別修正では閉じないため root cause を調査」を書く

**Why:** migration/conversion タスクは、review 観点が「構造変換」「原文保全」「ネイティブ機能活用」「レンダリング」の 4 レイヤーに分かれ、それぞれで失敗モードが独立している。completion-check の AC Drift Check は外部観測挙動との drift を見るが、「原文から落ちた情報」は検出できない（新ファイルだけ見ても分からない）。PR 作成直前に削除側の diff からキーワードを抽出して逆照合することで、最後の検出点を確保する。同じ finding を何度も修正 → re-review で繰り返すと無限ループになるため、2 回目の再発を検知したら systematic-debugging に escalate する（escape hatch の仕様詳細は `references/bounce-log-schema.md`）。

### 3c. Dialectic Review Check（該当タスクのみ）

`requirements.md` / `design.md` / diff のいずれかが `references/dialectic-review.md` の Trigger に該当する場合だけ実施する。該当しない PR では dialectic の実行を省略し、`dialectic: not_applicable` と reason を `Review metadata` に残す。

1. `design.md` または `worklog.md` に `Dialectic Review Summary` があるか確認する
2. summary がある場合、`Final Decision` が PR diff / docs / skill 文面に反映されているか確認する
3. summary が無く、かつ PR が prompt / skill / review policy / 人間向け出力 / severity calibration を変更している場合は、PR review 内で `references/dialectic-review.md` の Short Form を実行し、PR review の `Review metadata` に `dialectic: selected` と最終判断を 1 行で残す
4. dialectic の結果、AC / scope / security boundary / prompt-output contract が変わる場合は PR 作成を止め、GDD の `human_recheck_required` / `planning_rework_required` に戻す
5. 表示形式・章立て・finding 圧縮・採否理由の改善だけで閉じる場合は PR review finding ではなく `要件突合` / `Review metadata` に反映する
6. Trigger に該当しない場合は `dialectic: not_applicable` と reason を `Review metadata` に 1 行で残す。`skipped` は使わない

**Why:** review prompt や人間向け出力の改善は、正しさだけでなく「読み手が 5 秒で判断できるか」「false positive を増やしていないか」が品質の中心になる。single reviewer の主観だけで決めると表示形式や severity が揺れるため、PR 公開前に独立評価と最終統合の evidence を残す。

### 3d. Secret / Confidential Diff Check（常時）

PR 作成前に `git diff <default-branch>...HEAD` と staged / untracked 候補を確認し、機密情報を含む変更が混入していないか明示的に確認する。

- 12 桁の AWS アカウント ID
- private key marker を含む秘密鍵・プライベートキー
- `.env`、パスワード、API キー、アクセストークン
- Secrets Manager / SSM パラメータの実値
- Dockerfile / container build に bake-in された secret、token、credential

検出した場合は **High finding** として PR 作成を止める。マスク・削除・履歴上の扱いを確認し、ユーザーへ即報告する。誤検知と判断する場合も、根拠を `Review metadata` に残す。

### 3d-2. Worktree Provenance Gate（常時・fail-closed）

PR 作成または final diff verification の前に、`task slug / branch / PR / steering / scope` が同じ作業を指していることを機械的に確認する。ここが一致しない場合は **fail-closed** とし、PR 作成・push・cleanup を止める。

必須確認:

- `git rev-parse --show-toplevel` で現在の checkout root を確認し、GDD が期待する active worktree と一致することを確認する
- `git branch --show-current` で current branch を確認し、task slug と branch slug が対応していることを確認する
- `git diff --name-only <default-branch>...HEAD` で変更ファイル一覧を取得し、別 task の `.steering/` や scope 外ファイルが混入していないことを確認する
- PR が既にある場合は `gh pr view --json headRefName,baseRefName,url,title` で PR の head branch と current branch を照合する。PR が無い場合は「PR 未作成」として記録し、PR 作成直前に再確認する
- active steering `.steering/<task-slug>/state.md` / `requirements.md` / `tasklist.md` の task slug と branch / PR / diff scope を照合する
- root checkout 側に同一 slug の `.steering/<task-slug>/` が残っていないか確認する。legacy migration source でない duplicate は **root bleed** として扱い、PR 作成前に正本を解決する
- ラベルを分ける: **root bleed** は root checkout に同一 slug の duplicate steering が残る状態、**別 task steering 混入** は diff / PR scope に現在 slug 以外の `.steering/<other-slug>/` が含まれる状態。どちらも停止理由だが、観測値には別ラベルで記録する

停止条件:

- task slug と branch が対応しない
- active steering が見つからない、または複数候補で一意に決まらない
- current branch と `gh pr view` の head branch が一致しない
- diff に別 task の steering / scope 外 file / root bleed がある
- worktree root が GDD の active worktree と異なる

停止時は High finding として、現在の root / branch / PR / steering / scope の観測値を列挙し、`gdd-status` または `/gdd-dev resume <target>` で正しい候補を選ぶよう返す。曖昧な状態を「たぶんこの PR」として進めない。

### 3e. Superpowers Benchmark Summary（changed GDD primitive のみ）

PR diff が changed GDD primitive（`gdd-brainstorming` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `root-cause-investigation` など superpowers 同等品がある primitive）を含む場合、PR 作成前に `Superpowers Benchmark Summary` を確認する。

- 比較資料がある場合: その対象 primitive、scenario、GDD / superpowers の checklist 達成率、steps / duration / retries、GDD 固有軸（state machine 連動）を PR metadata に要約する
- 比較資料が無い場合: PR metadata に `Superpowers Benchmark Summary: missing` を記録し、changed GDD primitive なのに benchmark を省いた理由を明示する
- primitive 変更が無い場合: `Superpowers Benchmark Summary: not_applicable (no changed GDD primitive)` とする

### 3f. External Reviewer Anticipation Check（常時）

分類の正本は `references/self-review-lanes.md`（10 分類・3 レーン・A〜E 対応表）。この 3f は敵対レーン + 内部整合レーンの入口であり、**D 型（検証・ガードの緩さ / fail-open）を最優先で確認する**。「常に成功する検証は検証していないのと同じ」に該当する箇所がないかを A〜C・E より先に見る。

<!-- self-review-lane-provenance:start -->
分類根拠: 分類3（A型）/ 分類4（B型）/ 分類5（C型）/ 分類6（D型）/ 分類8（E型）。件数・型名の正本は直前の段落が示す参照先とする。この範囲には分類 ID・レーン名・定義済み型名以外の固有名詞を書かない。
<!-- self-review-lane-provenance:end -->

外部 AI レビュアー（Copilot 等）が実際に指摘する型を PR 作成前に自分で潰し、レビュー往復を減らす。対象は**今回の diff で変更したコメント・説明文・判定式**に絞ってよい。ただし散文（ADR / requirements / PR 本文）だけを見て終わらせず、**コード内の docstring / テストの assertion / 検証スクリプトの pin** も同じ対象に含める（3f を導入した後の PR でも、見落とした指摘はすべてコード側だった）。

- **A. 数値・列挙の自己不整合**（出典: PR 旧#201 / 旧#202。コード PR でも docstring「8 並列」対 実装 `= 4` 等が発生）— コメントや本文に書いた件数 / 集計 / 列挙が、同じ変更で更新した実体（配列要素数・関数数・トークン数・表の行数）と一致するか。列挙の接続（`.` の後に `plus` が続く等）が壊れていないか。PR 説明が参照する番号・ファイル名が実物と合っているか
- **B. コマンド・式の引数省略**（出典: PR 旧#203）— `git merge-base --is-ancestor` のように**引数で意味が決まるコマンド**を引数なしで書いていないか。判定式・比較式から「何と何を比べるか」が読み取れるか
- **C. 断定の過剰一般化**（出典: コード PR の ADR「breaker が落ちたら以降 `put_item` は呼ばれない」/ spec「二重起票経路は発生しない」が実装の保証より広かった例）— 「〜なら必ず〜」「いずれも〜」「〜は発生しない」の全称表現が、同じ文書内または参照先の例外条項・実装の実際の保証範囲と矛盾していないか
- **D. 検証・ガードの緩さ**（出典: PR 旧#204 = doc-check の pin token が先頭のバッククォートを欠き、対象文字列を削っても部分一致で通った / PR 旧#206 = temp の後片付けが成功経路にしかなく、`set -e` の失敗時に残った）— 今回**追加・変更したガードや検証**が、意図した対象より広く通ってしまわないか。①pin / assert の文字列が区切り（引用符・バッククォート・行頭行末）まで含んでいるか ②既定値や `None` / 空が素通りしないか ③後片付け・解放・ロールバックが成功経路にしか無くないか ④**その検証は本当に対象を見ているか**（環境変数の差し替えが実際に効いているか / 比較・集計の対象が実物か / 失敗するはずの条件で本当に落ちるか。**常に成功する検証は検証していないのと同じ**。出典: v0.23.0 = `mktemp -t` が `TMPDIR` を無視するため空のディレクトリを数えていた / 同 = 2 つのレビュー結果を実在確認せずに比較して結論を出した）

- **E. 設計変更の追随漏れ**（出典: PR 旧#210 = budget 制約で置き場所を 2 回変えた際、CHANGELOG と doc-check のコメントが初版の記述のまま残った）— 実装中に**置き場所・方式・対象を変更**した場合、先に書いた説明文がすべて追随しているか。A が数え直しで見るのに対し、E は**差分との突き合わせ**で見る。①CHANGELOG / ADR / PR 本文 / コードコメントが**名指ししているファイル・節・skill を実際の変更ファイル一覧と突き合わせる**（`git diff --name-only <default-branch>...HEAD`）②「新設した」「追加した」と書いた対象が実際に差分にあるか③採用しなかった初版の案を説明したままの文が残っていないか
**検出時の扱い**: **High finding にせず**、その場で修正して Pre-PR loop を続行する（PR 作成は止めない）。`Pre-PR Fix Attempts` は増やさない（3a〜3e の High 差し戻し契約と混同させない）。判断に迷うものは修正せず PR 本文に残し、外部レビューに委ねる。

**パターン追加の運用**: 指標は PR 単位の外部レビュー指摘件数と A / B / C / D / E 内訳（分類できないものは「新型」として計上）。記録先は次タスクの `findings.md` または CHANGELOG。**3 PR 連続で 3f の検出が 0 件**かつ同型の外部指摘が発生した場合は 3f を再設計する。新しい型を追加するときは本節に追記し、出典 PR を添える。

### 3g. 配線レビュー（別系統モデル、Wiring Cross-Model Review）

3a〜3f は同一系統（Claude Code 上の Claude モデル）のレビューであり、同一モデル特有の見落としパターンを共有しうる。PR がこの diff で新設要素（関数・state field・trigger・閾値・マーカー）を導入している場合、PR 作成前に別系統モデル（Claude Code では Codex、codex plugin）で配線観点のレビューを 1 回行う。

観点は次の2点に絞る:
- 新設要素ごとに書く側・読む側・到達経路を実コードで追う（`gdd-planning-reviewer` の配線表整合チェックと同じ観点を、別モデルで再確認する）
- 同じ入力を読む別実装との受理集合の一致（独立レビュー観点 (h) と同じ視点）

**手順**: `codex-rescue` agent（または host の codex plugin 相当）に実装文脈を渡さず、diff と配線表だけを渡して上記2点を確認させる。指摘は、人に見せる前・直す前に次のとおりまとめる。
- 依頼文: `references/reviewer-common.md` § finding category の表の値、§ 常時 High の 4 型と適用範囲、severity の尺度（high / medium / low / advisory）を書き写し、指摘ごとに `file:line`（repo からの相対パスと開始行）・category・severity を 1 つずつ添えさせる。category が無い・表の外の指摘は、§ finding category の未付与の既定に代えて blocking、severity が無い・尺度の外の指摘は high として扱う
- 突き合わせる相手: Codex に渡した diff の tip と同じ sha で走った独立レビューの指摘。独立レビューが無いとき、または `file:line` の無い指摘は、突き合わせずに別の 1 件として数える。比べる前に、両方の `file:line` を repo からの相対パスと開始行にそろえる
- 数え方: 同じ `file:line` に独立レビューの指摘があれば、Codex の指摘は別に数えず、そのうち 1 件（`file:line` と要約）に本文を書き添える。行が違うものはまとめない
- 重さ: 受け側の独立レビューの指摘と、書き添えたすべての Codex の指摘のうち、最も重い severity と blocking（category から `is_blocking` で導く）を取り、その重さで扱う。§ 常時 High の 4 型に当たり、同節の適用範囲に当たる指摘は、Codex が付けた severity によらず high にする。4 型に当たるかを判定できない指摘と、確かめた後に戻すときの扱い（どの部品か・戻す条件・上限）は、`gdd-pr-review-followup` の手順 2 Classify と同じにする。ただし、戻し先は上の依頼文の規定で分けた severity（Codex が付けた値。無い・尺度の外なら high のまま。読み替えはしない）とし、確かめた根拠は PR コメントの代わりに PR 本文または worklog に残す。high 相当・blocking の指摘は PR 作成前に修正する（直す順序は上の「直す順序」の段落のとおり § 直し方）。advisory は、blocking でなければ PR 本文に後続課題として記録してよい
- 閉じる条件: 書き添えたすべての本文が直ったことを確かめてから閉じる。Codex の指摘をまとめたことを理由に `Independent Review` 行の件数を足し引きしない。`references/independent-review.md` の (3-c) の未解消分は、独立レビューの指摘の本体が直ったかで判定する

**Why**: 内部 gate は全て同一系統のレビューであり、ADR≥2 トリガーの書き込み側が無い、新設 wrapper の呼び出し元が無い、のような配線欠陥は、内部 gate を全て通過した後の別系統レビュー（Codex・Copilot・レビュー bot・人間）で初めて見つかっていた。PR 前に別系統モデルを 1 回挟むことで、この種の指摘を PR 作成前に前倒しする。

**使えない host での扱い**: 使えない host では skip の理由を記録する（PR 本文または worklog に `Wiring Cross-Model Review: skipped (<理由>)` として残す。skip 自体は PR 作成を止めない）。

### 5. steering scope と PR scope の一致確認

- active steering ディレクトリ（`.steering/YYYYMMDD-short-title/`）が、この PR のブランチと対応しているか確認する
  - `git log --oneline <default-branch>..HEAD` で今回の変更コミットを確認し、steering の `requirements.md` の scope と一致しているかを照合する
  - 別のタスクの steering が参照されていた場合、または steering が参照されていない場合は High finding として報告し、PR 作成を止める
- PR の diff に含まれる `.steering/` ディレクトリのファイルが、今回のタスクの steering のみであることを確認する（別タスクの steering が混入していないか）

### 6. docs / steering / PR metadata の言語一致確認

- PR タイトル・本文・コミットメッセージの言語と、steering artifact（`requirements.md` / `design.md`）の記述言語が一致しているか確認する
- プロジェクト規約で言語が指定されている場合（日本語等）、PR タイトル・本文・docs 変更がその規約に従っているか確認する
- docs 変更を含む場合、変更したドキュメントの本文言語が PR 本文の言語と一致しているか確認する
- 不一致がある場合は Medium finding として報告する（High にはしないが、PR 本文はマージ前に揃えることを推奨する）
