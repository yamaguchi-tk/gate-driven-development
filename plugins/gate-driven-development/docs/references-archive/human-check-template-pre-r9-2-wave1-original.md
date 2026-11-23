# human-check テンプレート（正本）

`human-check-waiting` 停止時に出力するテンプレートの **唯一の正本**。構造・適用ルール・content 品質ルールを全てここに集約する。skill / reference 側から参照する際は「このファイルを Read して従う」と pointer で書き、構造を inline で再掲しない（DRY / SSOT 維持のため）。

## GDD Complexity Budget

HITL を出す前に GDD Complexity Budget を確認する。内部用語数、HITL行数、承認ポイント数、正本重複、似たルールの重複が超過していないかを見る。超過した場合は詳細表を減らす、30秒判断を先頭に寄せる、または内部用語を説明する。30秒判断にはなぜやるか（WHY・根本原因） / 整理した要件 / 実装する方法・内容 / 変更予定ファイル（WHERE） / 検証する方法・内容 / どこまで自走するのか / 判断ポイント / 段階実装サマリーを残す。WHY を先頭に置くことで WHAT と HOW の判断根拠が見えるようにする。

## Codex Subagent Delegation Permission

Codex ではサブエージェント利用を HITL で露出する。無関係なら省略する。出す場合は、このタスクで使う / 使わない / 既に明示許可済み のいずれかを明記し、明示委譲ソースを Approved Direction に残す。

## Compact First

human check の一次表示は `references/human-check-template-compact.md` を先に使う。本文の長い trace / 詳細表 / 返答分類ルールはこのファイルに残すが、最初に人間へ出す承認画面は compact template の line budget に収める。

- quick (express): compact template をそのまま使う
- quick (standard): compact template + 必要なら詳細 artifact へのリンク
- standard: compact template を一次表示にし、詳細は `requirements.md` / `design.md` / `tasklist.md` / `worklog.md` へ逃がす

**Why**: human check は全文レビューではなく「この OK で AI が自走しても想定どおりか」を判断する停止点。長い正本を読ませるほど、読まれずに OK されるリスクが上がる。

参照する skill:
- `skills/gdd-brainstorming/SKILL.md` § Output Guidance
- `skills/gdd-requirements-gating/SKILL.md` § Human Check Handoff
- `references/requirements-gating-steps.md` § Human Check Handoff

## Planning Interrupt Decision Menu

planning / requirements-gating / subagent planning が進行中で、HITL を人間に表示する前にユーザーが追加指示・質問・方針変更を挟んだ場合は、黙って計画に混ぜて build phase へ進まない。次の 4 択を自然文で出し、どれとして扱うかを明示する。

1. **要件追加として取り込んでHITLを再生成**: scope / AC / 技術スタック / security / 自走上限 / 段階実装 / 複数PR戦略が変わる場合。`requirements_amendment` として requirements / design skeleton を更新し、同じ HITL 内で変更後の判断ポイントを再表示する
2. **相談として回答し、計画は一時停止**: 質問への回答だけで artifact を変えない場合。回答後も `human-check-waiting` なら HITL を表示して止める
3. **いまのHITLを承認して次へ進む**: すでに同じ HITL を人間に表示済みで、ユーザーが明示的に OK した場合だけ。未表示の HITL を内部承認扱いにしない
4. **計画を中止/作り直し**: 方向性を変える、または現在の planning を破棄する場合。`planning_rework_required` または cancelled として扱う

このメニューは HITL そのものを長くするためではなく、「途中で指示したらHITLが消える」事故を防ぐための分岐である。ユーザーの割り込みが要件追加なのか相談なのか曖昧な場合は、この 4 択で確認してから進める。

---

## 出力テンプレート

`<...>` を実際の内容で置換して出力する。出力後は必ず `<gdd-stop reason="human-check-waiting">` マーカーを付けて停止する。

### 一次表示の原則

HITL は全文レビューではなく、**この OK で AI が自走しても想定どおりの結果になりそうか**を人間が判断する停止点である。一次表示は、詳細表を開かなくても以下 8 項目が読める形にする。**なぜやるか（WHY）を先頭に置き、WHY が WHAT と HOW の判断根拠になるようにする**。

1. **なぜやるか（WHY・根本原因）**: 解決する問題・根本原因・この変更が必要な理由。WHY が先にあることで WHAT と HOW の判断根拠が見える
2. **整理した要件**: ユーザー入力を AI がどう解釈したか。変換・延期・非スコープ化した完了条件があればここで見えるようにする
3. **実装する方法・内容**: 採用するアーキテクチャ、技術スタック、既存実装の再利用方針（変更対象ファイルは項目 4 の WHERE に記載する）
4. **変更予定ファイル（WHERE）**: 変更予定の実ファイルパスと変更内容の対応。`git grep` / 類似実装調査に基づく実名を記載し、placeholder（例: `src/...`）は禁止。該当なしの場合は「N/A」と根拠を1行添える
5. **検証する方法・内容**: どこで確認するか、どう確認するか、OK条件、失敗時の扱い
6. **どこまで自走するのか**: 実装完了 / PR 作成 / post-merge read-only 検証などの最大到達点と、merge / deploy / apply 等の除外
7. **判断ポイント**: 人間が今決める必要がある 1-3 件。`Option B` / `P1` のような略称は同じ HITL 内で定義する
8. **段階実装サマリー**: 単一段階か複数段階か、この PR でやる範囲、後続 Stage が何を consume するか

一次表示の目安は quick (express) 10 行以内、quick (standard) 20 行以内、standard 30 行以内。standard で 30 行を超える場合は、情報を削るのではなく、詳細を `requirements.md` / `design.md` / `tasklist.md` / `worklog.md` に逃がし、HITL には「判断に必要な差分」だけを残す。

禁止:
- 何を判断すべきか曖昧な旧式見出しを使わない。特に「保護が増える/増えない」という言い方で、実装範囲・検証範囲・未確認事項を説明しない
- `P0` / `P1` / `Option B` / `S-2` を未定義のまま出さない
- 検証計画、自走上限、未確認事項、人間に戻す条件を参考欄や長い trace の末尾に埋めない
- 詳細を短くするために、要件変換・検証境界・危険操作の除外を落とさない

### 承認後の到達点

- 標準: PR 作成まで
- インフラ変更: deploy 手前まで（`terraform apply` / AWS write は別途明示承認が必要）
- 本番相当操作: `terraform apply`、AWS write、DB write、Docker push はこの human check の包括承認に含めない。承認後にアーキテクチャ選択（採用フレームワーク・access method・credential backend 等）を覆す必要が出た場合も同様に、silent に変更せず `gdd-requirements-amendment` 経由で再承認を取る
- ユーザーが「マージして再学習まで」「merge 後に検証まで」「post-merge verification / relearning まで」などを完了条件として明示した場合、その完了条件を **Post-PR Completion Scope** として残し、標準既定の `PR 作成まで` に丸めない。危険操作だけを「別途明示承認が必要な操作」に分離する

```markdown
## 🔍 確認

### 30秒判断（まず見るところ）

**なぜやるか（WHY・根本原因）**: <解決する問題・根本原因・この変更が必要な理由>
**整理した要件**: <ユーザー入力を AI がどう整理したか>
**実装する方法・内容**: <採用する実装方法と変更内容>
**変更予定ファイル（WHERE）**: <実ファイルパス | 変更内容 | 対応ACの行、または該当なしの理由>
**検証する方法・内容**: <どこでどう確認するか>
**どこまで自走するのか**: <実装 / PR 作成 / merge 前まで等>
**判断ポイント**: <人間が今決めること>
**段階実装サマリー**: <単一段階 / 複数段階 / 次PRの扱い>

### やること
<この変更で何を実現するか — 1-2 文>

**タスクサイズ**: <quick (express) | quick (standard) | standard> — <判定理由 1 行>
**フロー**: <このサイズで通るセレモニーを 1 行>
**通過予定 gate 数**: <N gate>（<gate 名を列挙>）
**自走上限**: <今回の承認で AI が進めてよい最大到達点。例: 実装完了まで / PR 作成まで / デプロイ準備まで / デプロイ実行は別承認>
**Post-PR Completion Scope**: <なし / マージして再学習まで / post-merge verification / relearning まで。ユーザーが明示した場合は PR 作成までに丸めない>

### 承認サマリ

非エンジニア向けに、詳細表を読まなくても `OK` の意味が分かる 5 行以内の要約を必ず置く。

- **人間が今だけ判断すること**: <scope / AC / 技術スタック / 自走上限のうち、ズレると後戻りが大きい判断を 1-3 件>
- **What と How の分離**: <何を実現するか（What）と、どう作るか（How）が分かれているか。混ざっている場合は human-check に進めない>
- **OK で許可される最大到達点**: <実装完了まで / PR 作成まで / デプロイ準備まで等。merge / deploy は含めないなら明記>
- **PR 後も完了条件に含むこと**: <Post-PR Completion Scope がある場合だけ 1 行。例: PR が merge された後に read-only で再学習結果を確認する>
- **OK でも許可されないこと**: <merge / deploy / terraform apply / AWS write / DB write / Docker push / actual external posting など>
- **OK 後に AI がまず行うこと**: <design-gating / task-breakdown / RED 作成など、次アクションを 1 行>
- **迷った時の返答**: <例: `2 は変更` / `自走上限は実装完了まで` / `全面見直し`>

### 判断ポイント

非エンジニアでも `OK` の意味が分かるよう、詳細表の前に意思決定カードを必ず置く。ここには仕様のズレ・漏れを防ぐための重要判断だけを書く。

**OKで実装・検証すること**
- <今回の承認で AI が実装すること / 新しく確認すること>

**OKしても今回は対象外のこと**
- <今回 scope 外のため実装しないこと / 今回は検査だけで本番では止めないこと>

**人間に決めてほしいこと**
1. <業務・安全上の判断を自然文で。例: 未知の経路は warn（警告）から始め、今すぐ止めないことでよいか>
2. <実装方針の判断を自然文で。例: Judge は offline（評価用）に限定し、本番では止めないことでよいか>
3. <自走上限または戻し条件>

### HITL読みやすさ確認

表示前に、なぜやるか（WHY・根本原因） / 整理した要件 / 実装する方法・内容 / 検証する方法・内容 / どこまで自走するのか / 判断ポイント / 段階実装サマリーが先に読めるかを確認する。WHY が先頭にあることを確認する。

### 選択肢の説明

`Option B` / `P1` / `S-2` のような短いラベルだけでは承認者が判断できない。選択肢を出す場合は、同じ HITL 内で Option A / B / C の意味、採用案、採用理由、却下理由を必ず自然文で説明する。Option B だけを承認ポイントに出す、未定義の Option ラベルを出す、`Option B とは？` と聞かれる状態のまま human-check に進める、の 3 つは禁止。単一案なら Option ラベルを使わず `選択肢なし（単一案。理由: ...）` と書く。

| 選択肢 | 何をする案か | 良い点 | 弱い点 / やらないこと | AI の仮決定 |
|---|---|---|---|---|
| Option A | <小さく直す / 個別修正だけ等、承認者が分かる言葉で説明> | <早い / 影響が小さい等> | <再発防止や測定が弱い等> | <採用 / 不採用> |
| Option B | <今回の推奨案なら、その中身を 1 行で説明。例: 既存 runner を拡張し、品質を測れる仕組みまで入れる> | <なぜ良いか> | <重くなる点 / 今回やらない点> | <採用 / 不採用> |
| Option C | <大きく作る / release gate 化する等> | <強い保証等> | <重すぎる / 運用変更が必要等> | <採用 / 不採用> |

### Multiple PR Strategy Options

複数PR、後続PR、post-merge verification、または段階実装でPRをまたぐ場合は必須。HITL には段階表だけでなく、PRをどう分けるかの選択肢を出す。単に「複数PRで進める」「このPRではここまで」と書くだけでは、人間が同じチャットで続けるべきか、マージ後に次へ進むべきか、別チャットに渡すべきか判断できない。

| 選択肢 | 何をする案か | 良い点 | 弱い点 / やらないこと | AI の仮決定 |
|---|---|---|---|---|
| 単一PR | <全部を1つのPRで進める案> | <レビューとマージが一度で済む> | <巨大PRになりやすく、戻しづらい> | <採用 / 不採用> |
| 複数PR | <安定した単位でPRを分ける案> | <レビュー・検証・rollback がしやすい> | <段階間の追跡が必要> | <採用 / 不採用> |
| 後続PR着手前に再承認 | <前のPRがmergeされた後、ローカル整理と次段階確認をしてから着手する案> | <混線しにくい。マージ後の状態から始められる> | <都度の確認が必要> | <採用 / 不採用> |

複数PR案を採用する場合は、`段階実装案` に `後続の追跡先`、`同じチャットで続けるか / 別チャットへ渡すか`、`次に進む条件 / 人間に戻す条件`、`後続PR着手前に再承認` か `このOKで後続も自走許可` かを出す。後続 Stage の実装までこの OK で許可する場合は、独立した承認ポイントに昇格する。

### 検証計画

実装することと同じ重さで、検証することを承認者に見せる。`どこで確認するか` / `どう確認するか` / `OK条件` / `失敗時の扱い` が無い検証計画のまま human-check に進めない。

| 検証対象 | どこで確認するか | どう確認するか | OK条件 | 失敗時の扱い |
|---|---|---|---|---|
| <例: artifact ledger> | <repo / worktree / runner / 出力 artifact / 既存 test file> | <unit / contract / integration / E2E / no-post smoke / compare / score> | <何が観測できたら pass か。例: phase ごとの入力・出力・失敗理由が artifact に残る> | <自動修復 / coverage gap 記録 / human_recheck_required / blocked> |
| <例: classified unavailable artifact> | <status artifact / score artifact> | <fixture または no-post smoke で確認> | <未検証を green 扱いせず、不可理由が分類される> | <未分類なら修正して再検証。外部前提不足なら PR ready / 完了とは言わない> |

Web 画面・UI・ブラウザ操作を含む場合は、QA観点と Playwright 確認をここに含める。Playwright が実行できない場合も、`not_run` ではなく、理由・代替確認・人間に戻す条件を明示する。

Playwright fallback minimum:
- Playwright が実行不可なら、最低でも manual reproduction steps、screenshot or DOM evidence、console / network error check、対象 viewport / browser、未確認として残るリスク、人間に戻す条件を `検証計画` に出す
- screenshot or DOM evidence は「画面を見た」だけではなく、対象画面・操作・期待表示・取得時刻またはコマンドを残す
- DOM evidence の例は locator text、accessible name、URL、timestamp を含める
- console / network error check ができない場合は、その理由と代替確認を明記し、UI の完了 claim を弱める
- 主要導線が確認できない場合は PR ready / done と言わず、blocked または human_recheck_required にする

### モデル実行計画

GDD が phase ごとに worker model / effort を使い分ける場合は必須。`requested` と `applied` を混同しない。実行 metadata で確認できない場合は `適用未確認` と表示し、`要求どおり適用済み` と断定しない。

| 工程 | 推奨する品質レベル | 要求する model / effort | 実際の適用状態 | 判断への影響 | 次に選べること |
|---|---|---|---|---|---|
| <例: design-gating> | <設計レビューなので高精度モデル> | <gpt-5.5 / medium> | <適用確認済み / 適用未確認 / 利用不可> | <判断品質に影響あり / 影響軽微> | <このまま進める / 高精度 model で再実行 / 人間が確認して採用> |

表示ルール:
- `要求する model / effort`: GDD が worker 起動時に指定する値
- `実際の適用状態`: `verified` / `unverified` / `unavailable` / `failed` の人間向け表示
- formal gate で `unverified` / `unavailable` / `failed` の場合は、軽量 model へ黙って落とさず、再実行または human acceptance を承認ポイントに出す
- main session の model が裏で切り替わったとは書かない。worker 起動時の要求として説明する

### まず見るところ

- **判断してほしいこと**: <承認ポイントのうち必ず確認してほしい 1-3 件。例: scope / 技術スタック / 自走上限>
- **この OK で進めること**: <OK 後に AI が進める scope・作り方・検証・自走上限を 1-2 行>
- **この OK では許可しないこと**: <merge / deploy / terraform apply / AWS write / DB write / Docker push / actual posting / 未承認の方式変更など、上位 2-3 件>
- **迷ったら確認する欄**: <承認ポイント N / 技術スタック確認 / テスト化確認 / 参考詳細など、判断に必要な欄名>

### Stage Continuity Brief

段階連続性:
- <S-1: 何を生成するか> → <S-2: 何がそれを consume するか> → <S-3: 何を完成させるか>
- 後続が依存する生成物: <schema / API / policy / fixture / integration contract 等>
- 前回からの段階計画の変更: <初回なら `なし`。再承認なら Plan Revision Ledger の変更要約>
- 人間に戻す条件: <Stage の生成物・依存・後続消費物が変わる場合>

### 段階実装案

`Implementation Sequence Plan` が複数 Stage を持つ場合は必須。`Stage Continuity Brief` は「段階間の受け渡し」、この表は「どの順番で何を実装・検証するか」を示す。片方で代替しない。

| Stage | この段階でやること | このPR/後続 | このOKで承認する範囲 | 完了確認 | 次に進む条件 / 人間に戻す条件 | 後続の追跡先 |
|---|---|---|---|---|---|---|
| <S-1> | <目的と生成物を 1 行。例: 既存コード調査と contract test を固定する> | <current-pr / follow-up-pr / post-merge-verification> | <このPRで実施許可 / 後続PRの方針のみ承認 / 後続PR着手前に再承認> | <Covers AC / 検証方法 / RED test> | <次 stage へ進む条件。scope・技術スタック・生成物の意味が変わるなら人間に戻す> | <current-pr なら `なし`。follow-up-pr なら Planned Follow-up Stage Lane の seed / backlog / steering 予定> |
| <S-2> | <実装する主な変更> | <current-pr / follow-up-pr / post-merge-verification> | <このPRで実施許可 / 後続PRの方針のみ承認 / 後続PR着手前に再承認> | <unit / contract / integration / E2E / external evidence> | <継続条件または停止条件> | <後続PRの作成タイミング・追跡先> |

### LLM 方針レビュー

方針を出す前の LLM review:
Selection: Plan Direction LLM Review=<selected / selected(main-session) / not_applicable> — <理由 1 行>

| 観点 | 結果 | HITL で確認してほしい点 |
|---|---|---|
| ユーザー入力との一致 | <AI が整理した要件・方針がユーザー入力とズレていないか。直した点があれば 1 行> | <scope / AC / N/A> |
| 作り方の妥当性 | <アーキテクチャ・技術スタック・変更ファイル・access method が妥当か> | <技術スタック / 実装方針 / N/A> |
| 安全性と制約 | <secret / tenant / 外部送信 / 危険操作 / 本番相当 write の扱いが妥当か> | <制限事項 / 自走上限 / N/A> |
| 検証と自走 | <検証方法と自走範囲が、この承認で任せてよい粒度か> | <検証方法 / 自走上限 / N/A> |
| HITL 表示のわかりやすさ | <未定義の P0/P1 など、承認者が判断できない語を残していないか> | <用語定義 / 承認ポイント / N/A> |

### Adversarial Requirements Review

独立 / 敵対的レビュー:
| 項目 | 内容 | HITL で確認してほしい点 |
|---|---|---|
| 反対仮説 | <この要件・完了条件・作り方が間違っているとしたら何が原因か。非該当なら `not_applicable: <理由>`> | <承認ポイント / 関連欄 / N/A> |
| ズレリスク | <人間が「思ったんと違う」と言いそうな scope / AC / 技術スタック / access method / credential boundary / Stage continuity / self-run limit> | <どこを見れば判断できるか> |
| 採用した修正 | <敵対的レビューから requirements / design skeleton / human-check に反映した修正> | <修正後の承認対象> |
| 残すリスク | <承認後も残る未確認・外部証跡・解釈差。ない場合は `なし`> | <OK してよいか、条件付きにするか> |

### 人間に戻す主な条件

Top 3 Stop Conditions:
- <AC の追加・削除・意味変更、または scope の根本変更が必要になった場合>
- <技術スタック / access method / credential backend / tenant 境界 / official integration adoption が変わる場合>
- <自走上限超過、危険操作・本番相当 write、E2E / 外部証跡不足により検証境界が変わる場合>

### まだ確認できないこと

Not Verified Yet:
| 未確認事項 | 今回の扱い | 確認タイミング / 人間に戻す条件 |
|---|---|---|
| <post-merge 反映 / relearning / prod 相当評価 / actual posting / 外部サービス状態など> | Deferred / external evidence required / blocked if unavailable | <いつ確認するか。不足時に止めるか、次 phase に送るか> |

### この OK で許可すること / 許可しないこと

| 区分 | この OK で許可すること | この OK に含まれないこと | 人間に戻す条件 |
|---|---|---|---|
| scope / AC | <承認対象の要件・完了条件> | <非スコープ / Deferred / Open Question / 未解決条件> | <AC の追加・削除・意味変更が必要になった場合> |
| 実装 | <採用する作り方・技術スタック・access method> | <未承認の方式変更 / credential backend 変更 / tenant 境界変更 / 公式統合からの逸脱> | <技術スタック / access method / credential backend / tenant 境界 / official integration adoption が変わる場合> |
| 自走 | <実装完了まで / PR 作成まで / デプロイ準備まで等、自走上限の範囲内> | <merge / deploy / terraform apply / AWS write / DB write / Docker push / その他の危険操作・本番相当 write> | <自走上限を超える操作、または operational safety 対象の 1 操作ごとの承認が必要な場合> |
| PR 後の完了条件 | <Post-PR Completion Scope がある場合、PR 作成後も done にせず、明示承認済みの post-PR scope の read-only verification / relearning まで追跡する> | <merge / deploy / apply / AWS write の自動実行。これらは 1 操作ごとの明示承認が必要> | <PR 作成後に merge / deploy / apply / AWS write が未承認で必要になった場合は `<gdd-stop reason="blocked">` で停止し、scope は消さない> |
| 検証 | <unit / contract / integration / E2E / external evidence のうち今回実施する証跡> | <今回確認できないこと / 外部証跡なしでは断言できないこと / 非テスト化 Deferred> | <E2E 不可、外部証跡不足、再現不能、検証境界の変更が発生した場合> |

### 現在地

| 項目 | 内容 |
|------|------|
| ここまで出来ていること | <例: 要件整理 / requirements review / lightweight design skeleton / trace 作成まで完了> |
| 人間が今やること | <例: 承認ポイントを確認し、OK / N は変更 / 全面見直し のどれかで返答する> |
| OK 後に残る作業 | <例: design-gating → task-breakdown → TDD → 実装 → implementation-gate → completion-check → PR 作成> |
| 残タスク | <tasklist.md が未作成なら「承認後に task-breakdown で作成」。作成済みなら Pending Tasks の要約。無ければ「なし」> |

### 前提
| 項目 | 内容 |
|------|------|
| 確定 | <箇条書き> |
| 非スコープ | <今回やらないこと> |
| 外部依存 | <なければ「なし」> |
| 設計方針 | <採用方針を 1 行> |
| ベースライン検証 | <pass / fail / not_run。fail なら作業前から壊れていた可能性、not_run なら未計測理由を 1 行> |

### ズレ確認

HITL は全文レビューの場ではない。requirements.md には詳細 trace を残し、この出力ではズレると手戻りが大きい差分だけを露出する。`kept` は原則省略し、件数だけ触れてよい。

**完了条件の変換**
| 初期条件 | 扱い | 変換後 | 承認してほしい点 |
|---|---|---|---|
| <ユーザーが最初に言った完了条件> | refined / split / deferred / dropped / added / unresolved | <AC / Non-Goal / Deferred / Honest Limitations / Open Question への写像> | <ここがズレると何が困るか> |

**テスト化確認**
| 完了条件 | テスト可能な形 | 確認方法 | HITL で確認したい点 |
|---|---|---|---|
| <テスト化できない完了条件 / E2E必須 / 外部証跡必須 / 解釈差が大きい条件> | <Testable claim or unresolved> | unit / contract / integration / E2E / external evidence / Open Question | <何がズレると困るか> |

**既存実装の調査状況**
| 調査対象 | 状況 | 見つけた既存経路 / 再利用判断 | HITL で確認したい点 |
|---|---|---|---|
| <repo 構造 / 関連ファイル / 類似実装 / read-write surface / tests / docs / policy boundary / QA観点 / Playwright 対象> | complete / partial / not_run | <既存 wrapper / adapter / policy / client / command / tests を再利用・拡張するか、新規が必要な理由> | <未調査・部分調査のまま OK すると何がズレ得るか。complete なら `N/A`> |

**Engineering Baseline**
| 観点 | 現状 / 採用案 | 根拠 | HITL で確認したい点 |
|---|---|---|---|
| どこに何を置くか | <architecture / code structure / module boundary> | <既存構造・類似実装・新規なら採用理由> | <この構造で「思った作り方」とズレないか> |
| どうやって同じ環境を再現するか | <dependency manifest / lock file / runtime / install command> | <既存 file / docs / CI / 未整備なら今回整える範囲> | <未整備のまま進めてよいか、今回整えるか> |
| どうやって検証するか | <test command / CI command / baseline command> | <既存 test / runner / CI / 代替確認> | <どの検証を OK 条件にするか> |

**コードベース健全性確認**
| 見つかったこと | 設計・タスク順序への影響 | この OK で扱うこと | HITL で確認したい点 |
|---|---|---|---|
| <巨大ファイル / lockfile なし / test baseline なし / CI baseline なし等。影響する finding だけ> | <設計変更、先に足場タスク、今回は Non-Goal 等> | <実装する / 先に整える / 明示的に対象外にする> | <後戻りが大きい判断だけ> |

**アーキテクチャ提案**
| 採用案 | 何を意味するか | 却下した案 | HITL で確認したい点 |
|---|---|---|---|
| <Follow / Fit + Small Refactor / Reshape / Simple Modular / Layered / Clean-ish / Service / Worker Split> | <承認者が分かる言葉で。例: 既存の置き場所に合わせる / 小さく責務整理する / service を分ける> | <なぜ採用しないか> | <この構造で進めてよいか。後から変えると何が大きく変わるか> |

**依存・実行環境**
| 項目 | 採用 / 現状 | 不足・制約 | HITL で確認したい点 |
|---|---|---|---|
| package manager / dependency manifest / lock file | <例: pnpm + package.json + lock file / pyproject + lock / missing> | <不足があれば明記> | <今回整えるか、後続に回すか> |
| runtime / install command / test command / CI command | <実行環境とコマンド> | <未確認・重い・CIのみ等> | <どこまでを完了条件にするか> |

**Project Reproducibility Gate**
| 再現性チェック | 状態 | 扱い |
|---|---|---|
| dependency manifest | confirmed / missing / needs-human / N/A | <今回作る / 既存利用 / 後続 / 非スコープ> |
| lock file | confirmed / missing / not-used + reason / needs-human / N/A | <同上> |
| install command | confirmed / missing / needs-human / N/A | <同上> |
| test command | confirmed / missing / needs-human / N/A | <同上> |
| CI command | confirmed / missing / needs-human / N/A | <同上> |

**Baseline Compliance Check**
| 完了時に確認すること | 確認方法 | 失敗時の扱い |
|---|---|---|
| approved architecture / file placement に従ったか | <diff / reviewer / path check> | <設計に戻す / 実装修正 / human recheck> |
| dependency manifest / lock file が実装と一致するか | <manifest / lock / import / provider / image check> | <修正して再検証 / 未整備なら blocked> |
| fresh install / fresh test / CI command の証跡があるか | <command / CI / not_run reason> | <pass 扱いしない / blocker / debug route> |

**Architecture Drift / Re-Architecture**
| 兆候 | 今回の扱い | 人間に戻す条件 |
|---|---|---|
| <mixed responsibilities / duplicated validation / dependency direction inversion / runtime-deploy mismatch 等> | <なし / Local Refactor / Boundary Reshape / Runtime / Service Split / 後続> | <承認済み architecture option や runtime boundary が変わる場合> |

**正本と事実の扱い**
| 種別 | 扱い | HITL で確認してほしい点 |
|---|---|---|
| 会話履歴 | 会話履歴は参考情報。compaction / 新チャットで欠落し得るため、単独で正本にしない | 初期意図の読み替えがズレていないか |
| GDD artifact | GDD artifact は正本。requirements.md / design.md / tasklist.md / state.md / worklog.md / continuation.json を承認済み scope と state の基準にする | artifact に残した What / How / 検証境界が妥当か |
| Git / PR / CI / test | Git / PR / CI / test は事実。merge commit、PR state、CI、test result、diff を観測事実として扱う | 事実確認できないものを pass 扱いしていないか |
| Continuation ID | Continuation ID は復旧用の受け渡しキー。通常は同じチャットで「次に進んで」、チャットが壊れた場合だけ `/gdd-resume <id>` で registry を読む | 長文プロンプト貼り付けではなく ID 復元でよいか |

**Workflow Fit Check**
| 判定 | 理由 | HITL で確認したい点 |
|---|---|---|
| GDD formal workflow / standalone route / superpowers sufficient | <state machine・AC ID・Reviewer Lineage が必要か、単発相談や単発 debug で十分か> | <GDD に乗せる重さが妥当か。standalone route に落としてよいか> |

**Baseline Verification Status**
| baseline_command | status | evidence / blocker |
|---|---|---|
| <例: npm test / pytest / bash tests/validate-plugin.sh / not_run> | pass / fail / not_run | <開始時点で壊れているか、未実行ならなぜ未実行か> |

**技術スタック確認**
| 採用する技術スタック | 代替案 | 採用理由 | HITL で確認したい点 |
|---|---|---|---|
| <MCP / CLI / SDK / API / framework / runtime / IaC / DB 等> | <比較した案> | <Existing repo standard / Official integration / Operational constraints / Multi-tenant / credential boundary / Testability への適合> | <access method / credential backend / tenant 境界 / 公式統合とのズレで何が困るか> |

**Architecture Option Matrix**
複数の妥当な選択肢がある architecture / CI / IaC policy / runtime / framework / test tooling / access method / credential backend では必須。AI が勝手に単一案へ丸めない。既存 repo 標準、業界標準 / vendor official、最小の自前実装、現行方式を比べ、DRY / KISS / YAGNI に照らして採用しない理由と人間に確認する点を出す。

`業界標準 / vendor official` は、vendor official があれば vendor official、無い/非該当なら ecosystem standard 寄り候補を意味する。HITL では混同しないよう、例: `OPA/Rego + Conftest（Terraform公式そのものではなく、policy as code の標準寄り候補）` のように一言補足する。

| 選択肢 | 何をする案か | 標準との合い方 | DRY / KISS / YAGNI | 良い点 | 弱い点 / 採用しない理由 | AIの仮決定 |
|---|---|---|---|---|---|---|
| 既存 repo 標準 | <既存CI・既存tooling・既存配置に合わせる> | <既存 repo 標準との一致> | <重複・複雑化を増やさないか> | <良い点> | <不採用なら理由> | <採用 / 不採用 / 人間に確認> |
| 業界標準 / vendor official | <公式・標準ツールに寄せる> | <公式統合・標準方式との一致> | <自前実装を減らせるか> | <良い点> | <不採用なら理由> | <採用 / 不採用 / 人間に確認> |
| 最小の自前実装 | <Python / shell / small script 等で狭く作る> | <標準から外れるか> | <KISSか、長期的に重複が増えるか> | <良い点> | <不採用なら理由> | <採用 / 不採用 / 人間に確認> |

Terraform plan JSON の CI policy では、既存 repo 標準が無い限り `OPA/Rego + Conftest` を第一候補として説明する。既存 repo 標準が Python 等で存在する場合は、既存標準拡張と `OPA/Rego + Conftest` 移行を `needs-human` として並べ、policy が増える見込み、保守できる人、導入コスト、CI 依存追加を判断材料にする。`Python 独自チェック` を採る場合は「なぜ Conftest / OPA ではないか」を判断ポイントに出す。`terraform validate / tflint / Checkov` は補助候補として、何を検出し何を検出しないかを `検証計画` に分ける。

**実装技術スタック**
| 分類 | 採用するもの | 採用理由 | 変更時の影響 |
|---|---|---|---|
| language / runtime | <例: Python 3.11 / Node.js 20 / Go 1.22> | <既存 repo 標準・host 制約・運用制約> | <変えると build / deploy / test に何が波及するか> |
| framework / library | <例: FastAPI / React / Terraform provider / internal helper> | <既存実装再利用・公式統合・保守性> | <変えると API shape / UI / IaC state に何が波及するか> |
| test tooling | <例: pytest / vitest / contract test / E2E smoke> | <Completion Testability Matrix と対応> | <検証境界が変わる場合の影響> |
| access method | <MCP / CLI / SDK / direct API / managed integration> | <公式統合・既存標準・認可境界> | <後から変えると credential / tenant / mock / E2E が変わるか> |
| credential backend | <Secrets Manager / SSM / env / OAuth / none> | <secret handling と tenant 境界> | <変更時の移行・権限・監査影響> |

**作り方の重要判断**
| 論点 | AI の仮決定 | 代替案 | ズレた時の影響 |
|---|---|---|---|
| <repo 分割 / import-recreate / 既存再利用 / public-private / CI/CD 方針など> | <採用案> | <却下案または design-gating 送り> | <後戻りが高い理由> |

**Adversarial Requirements Review**
| 反対仮説 | ズレリスク | 採用した修正 | 残すリスク |
|---|---|---|---|
| <この requirements / completion condition / implementation approach が間違っているとしたら何が原因か> | <誤承認すると後戻りが大きい点> | <HITL 前に直した点> | <人間が OK / 条件付き OK / 修正依頼を判断すべき点> |

### 承認ポイント

返答ガイド:
- **「OK」** → 全承認。上記の自走上限まで進めます
- **「N は〇〇にしてほしい」** → 該当ポイントだけ修正して再提示します
- **「実装方針を〇〇に変えて」** → AC は維持し、設計フェーズから再開します
- **「自走上限は PR 作成まで」** → 実装・検証・PR 作成までは進め、merge / deploy は止めます
- **「自走上限はデプロイ準備まで」** → デプロイ計画・dry-run・PR 準備までは進め、deploy 実行は止めます
- **「全面見直し」** → 要件ごとやり直します

**1. <判断テーマ>**
- **AI の仮決定**: <選んだ案を 1 行>
- **根拠**: <なぜこれを選んだか・根拠となる制約や前提を 1-2 行>
- **却下した代替案**: <検討したが採用しなかった案 + 却下理由を 1 行。単一候補なら「他案なし（理由）」>
- **判断に影響する前提**: <この前提が崩れたら結論が変わる条件を 1 行。なければ「なし」>

**N. 方向性**
- 自走範囲: ...
- 自走上限: ...
- 人間に戻す条件: ...

### 用語の短縮定義（該当時のみ必須）
- `<用語1>`: <1 行定義>
- `<用語2>`: <1 行定義>
- `warn`: 問題の可能性を記録・表示するが、今すぐ止めない扱い
- `offline`: 本番の実行経路ではなく、評価・検査用にだけ使う扱い
- `unknown surface`: Browser / Playwright / HTTP など外部送信になり得る未知の経路

### 参考（任意）
変更範囲 / リスク / 戻し方 / 詳細: <.steering/パス>
```

---

## 必須ルール（contract 違反で `human-check-waiting` に進めない）

### 構造・マーカー

1. 出力末尾に `<gdd-stop reason="human-check-waiting">` マーカーを含める（無いと autonomous continuation が止まらず人間確認がスキップされる）
2. 「requirements.md を確認してください」「次は human check です」だけで止めない（テンプレート省略は contract 違反）
3. Express Path も同じテンプレートを使う（承認ポイントが 1-3 件と少ないだけ）
4. downstream phase からの再承認では「前回からの変更点」を承認ポイントの前に追加する
5. 初回 human check では **自走上限** を必ず明示する。上限が曖昧なまま `OK` 承認させない
6. 初回 human check では、完了条件の変換と作り方の重要判断のうちズレると後戻りが大きい箇所だけを `ズレ確認` に出す。requirements.md の全文や全 AC を貼らない
7. HITL 停止時の状況ブロックとして `現在地` を必ず含め、`ここまで出来ていること` / `人間が今やること` / `OK 後に残る作業` / `残タスク` を表示する。state.md / tasklist.md / requirements.md / design.md を根拠にし、根拠が無い残タスクは推測せず「承認後に task-breakdown で作成」または「未作成」と書く
8. 外部サービス、runtime、framework、test tooling、access method、credential backend のいずれかを採用または変更する場合、`技術スタック確認` とは別に `実装技術スタック` を必ず含める。HITL で「何を作るか」だけでなく「何で実装するか」を承認できる状態にする
8. architecture / CI / IaC policy / runtime / framework / test tooling / access method / credential backend の選定で複数の妥当な選択肢がある場合、`Architecture Option Matrix` を必ず含める。既存 repo 標準 / 業界標準 / vendor official / 最小の自前実装を比較し、AI が勝手に単一案へ丸めない。非標準な自前実装を採る場合は、採用理由と採用しない理由を `人間に確認` する承認ポイントへ昇格する
9. 初回 human check では `この OK で許可すること / 許可しないこと` を必ず含める。`OK` が許可する scope / AC、実装、自走、検証と、`この OK に含まれないこと` を同じ表で明示する。危険操作・本番相当 write はここで明示的に **承認しない** と書く
10. 初回 human check では `まず見るところ` / `人間に戻す主な条件` / `まだ確認できないこと` を `この OK で許可すること / 許可しないこと` より前に置く。制限事項・未検証事項・停止条件を詳細 trace や参考欄に埋めない
11. 初回 human check では `判断ポイント` を必ず含め、`OKで実装・検証すること` / `OKしても今回は対象外のこと` / `人間に決めてほしいこと` を 3-5 行程度で書く。制限事項を詳細表に埋めず、先頭で読む人に見えるようにする
12. 初回 human check では `承認サマリ` を `判断ポイント` より前に置く。非エンジニア向けに `人間が今だけ判断すること` / `OK で許可される最大到達点` / `OK でも許可されないこと` を 5 行以内で出し、詳細表を読まない承認者にも誤承認させない
12. `Baseline Verification Status` を取得済み、または未実行理由が判明している場合は、`前提` の `ベースライン検証` に必ず出す。作業前 failure を隠すと、承認者が「今回壊した / 今回直るはず」を誤認する
13. `ベースライン検証` を承認ポイントに昇格する条件:
   - baseline `fail` / `not_run` が今回の完了条件、検証範囲、または「既存 failure を直すか」に影響する場合は、独立した承認ポイントにする
   - baseline `not_run` だが代表コマンドが存在するかを人間に確認したい場合は、`人間に決めてほしいこと` に 1 行で出す
   - baseline が `pass`、または未計測でも scope / 完了条件に影響しない軽微な作業なら、`前提` の 1 行で足りる。承認ポイントを増やしすぎない
   - `Codebase Health Survey` に設計・タスク順序・検証方法へ影響する finding がある場合は、`コードベース健全性確認` を必ず含める。全 finding を貼らず、巨大ファイル、依存管理、テスト/CI baseline のうち「今回どう扱うか」を人間が判断すべきものだけに絞る。影響なしなら欄は省略可だが、requirements.md の finding は `no-action + 理由` にする
11. standard または複数段階の quick (standard) では `Stage Continuity Brief` を必ず含める。`Implementation Sequence Plan` 全文を貼らず、Stage 間の生成物・consume 関係・前回からの段階計画の変更・人間に戻す条件だけを 3-5 行に圧縮する
12. standard または複数段階の quick (standard) で `Implementation Sequence Plan` が複数 Stage を持つ場合、`Stage Continuity Brief` とは別に `段階実装案` を必ず含める。`段階実装案` には `Stage ID`、この段階でやること、この PR / 後続の区分、この OK で承認する範囲、完了確認、次に進む条件 / 人間に戻す条件、後続の追跡先を出す。`Stage Continuity Brief` だけで済ませない
13. 「段階実装」「複数段階」「この PR ではここまで」「後続で実施」と書く場合、`段階実装案` が無い human check は contract 違反。段階の詳細が多い場合でも、HITL には stage list summary を出し、詳細は requirements.md の `Implementation Sequence Plan` に残す。`follow-up-pr` の Stage は `後続PRの方針のみ承認` または `後続PR着手前に再承認` を明記し、この OK だけで後続実装へ自走しない
14. quick (express) の単一段階では `Stage Continuity Brief` を完全省略しない。single-stage 最小表示として、`段階連続性: single-stage` / `後続が依存する生成物: なし` / `前回からの段階計画の変更: なし` / `人間に戻す条件: AC 追加・修正範囲拡大` だけを出す。`段階実装案` は `N/A - single-stage express` と 1 行でよい。これにより Express Path も同じテンプレートを使いながら、standard 相当の Stage 詳細を増やさない
15. `LLM 方針レビュー` を必ず含める。`requirements.md` の `Plan Direction LLM Review` から、ユーザー入力との一致 / 作り方の妥当性 / 安全性と制約 / 検証と自走 / 表示のわかりやすさの結果だけを短く出す。長い reviewer 本文、思考ログ、model 比較は出さない。`Plan Direction LLM Review=not_applicable` の場合も、理由を 1 行で示し、欄自体は省略しない
16. `Adversarial Requirements Review` を必ず含める。`requirements.md` の `Adversarial Requirements Review` から、反対仮説 / ズレリスク / 採用した修正 / 残すリスクだけを短く出す。`Dialectic Review Lane=not_applicable` の場合も、反対仮説に `not_applicable: <理由>` と書き、欄自体は省略しない
17. 初回 human check では `既存実装の調査状況` を必ず含める。`Existing Implementation Survey` から、repo 構造、関連ファイル、類似実装、read / write / persistence / API / MCP / wrapper / adapter 経路、tests / contracts、docs、policy 境界のうち、再利用判断や未調査だとズレる点だけを圧縮表示する。読み書き・保存・投稿・検索・更新・外部連携を含むタスクでこの欄が無い場合は contract 違反
18. ユーザー入力または `User-Stated Completion Conditions` に `merge` / `マージ` / `再学習` / `relearning` / `post-merge verification` / `release verification` / `apply 後確認` が含まれる場合、`Post-PR Completion Scope` を必ず表示する。標準既定を理由に自走上限を PR 作成までへ自動降格しない。write 操作が未承認なら `別途明示承認が必要な操作` に分離し、完了条件そのものは残す
19. `Option A` / `Option B` / `Option C`、`P0` / `P1` / `P2`、`S-1` / `S-2` のような短いラベルを使う場合は、`選択肢の説明` または `段階実装案` でラベルの意味を同じ HITL 内に定義する。`Option B とは？` と聞かれる状態、未定義の Option ラベル、略称だけの承認ポイントは contract 違反であり、human-check に進めない
20. `OKで実装・検証すること`、`検証`、`no-post`、`score`、`compare`、`runner`、`E2E`、`external evidence` のいずれかを出す場合は、`検証計画` を必ず含める。`検証計画` には検証対象、どこで確認するか、どう確認するか、OK条件、失敗時の扱いを出す。`classified unavailable artifact` や外部前提不足は成功扱いではなく、分類済み未検証として扱い、PR ready / 完了とは言わない

### 承認ポイントの 4 要素（欠落禁止）

各承認ポイントは必ず以下の 4 要素を揃える。1 つでも欠けたら contract 違反:

- **AI の仮決定**: 選んだ案
- **根拠**: なぜそれを選んだか・根拠となる制約
- **却下した代替案**: 検討したが採用しなかった案 + 理由（単一候補なら「他案なし（理由）」）
- **判断に影響する前提**: この前提が崩れたら結論が変わる条件（なければ「なし」）

**Why**: 人間が根拠を追えないと承認判断できず、`/btw` で定義質問が発生して停止点の価値（artifact を開かず判断できる）が崩れる。

### 用語の短縮定義

仮決定や AC に **ユーザーが即座に意味を取れない技術用語**（Webhook event 名・プロトコル名・サービス固有の概念等）が含まれる場合、**同じ human check 出力内で 1 行定義**を付ける。別ドキュメントに誘導しない。

特に `warn` / `offline` / `unknown surface` のように制限事項の誤解につながる語は、非エンジニア向けに「何を止めるか / 止めないか」を自然文で説明する。例: `offline Judge`: 評価用の検査であり、本番では止めない。`unknown surface`: 未知の経路で、warn の場合は今すぐ止めない。

例:
- `synchronize イベント`: PR に新しい commit が push されたときに発火する GitHub Webhook event
- `ready_for_review`: Draft PR が通常の PR に変更されたときに発火するイベント

### 通過予定 gate 数の置換値

sizing ごとの gate 数。`<N gate>（<gate 名を列挙>）` を以下で置換する。

| sizing | gate 数 | gate 名 |
|--------|---------|---------|
| quick (express) | 1 gate | impl-gate |
| quick (standard) | 3 gate | req-gate → design-gate → impl-gate |
| standard | 4 gate | req-gate → design-gate → impl-gate → completion |

**Why**: ユーザーが「承認後にどれだけ AI が自走するか」を事前に把握できる。「standard: 4 gate を通過予定」と見れば覚悟ができるし、過剰に感じれば sizing 変更を依頼できる。

### 自走上限の置換値

`<自走上限>` は、今回の human check で承認された後に AI がどこまで進めてよいかを示す。scope / AC の承認とは別に、以下のいずれかを明示する。

| 上限 | AI が進めてよいこと | 止めること |
|------|--------------------|------------|
| 実装完了まで | 実装、テスト、実装 gate、完了確認用の証跡整理 | commit / push / PR 作成 / merge / deploy |
| PR 作成まで | 実装、テスト、commit、push、PR 作成、PR 本文作成 | merge / deploy |
| デプロイ準備まで | PR 作成、release note、deploy plan、dry-run / plan、必要な手順整理 | deploy 実行、本番 write 操作 |
| デプロイ実行まで | 明示された環境への deploy 実行まで。ただし危険操作は 1 操作ごとの承認を維持 | 未提示の追加 deploy、merge、追加 write 操作 |
| PR マージ後検証 / 再学習まで | PR 作成、レビュー収束、明示承認済みの post-PR scope、post-merge verification / relearning の read-only 確認 | 未承認の merge / deploy / apply / AWS write。これらは 1 操作ごとの明示承認で停止 |

- デフォルト推奨は **PR 作成まで**。リポジトリ規約やユーザー指示で commit / push / PR 作成が禁止される場合は **実装完了まで** に落とす
- ユーザーが「マージして再学習まで」などを完了条件に入れた場合、デフォルト推奨を理由に `PR 作成まで` へ自動降格しない。HITL では `Post-PR Completion Scope` として表示し、PR 作成後も done にしない範囲と、merge / deploy / apply / AWS write のように 1 操作ごとの明示承認が必要な範囲を分ける
- 本番 deploy、Terraform apply、AWS write、DB write、docker push、merge 等の operational safety 対象は、自走上限が「デプロイ実行まで」でも **1 操作ごとの明示承認** を別途必要とする
- 自走上限を変更したい場合は、ユーザーが「自走上限は PR 作成まで」「デプロイは止めて」等と返せるように、承認ポイントにも 1 件として出す
- `この OK で許可すること / 許可しないこと` の表では、`自走上限` の置換値をそのまま人間向けに再掲し、`この OK に含まれないこと` と `人間に戻す条件` を隣に置く。上限名だけで済ませない

**Why**: 「OK」が要件承認なのか、PR 作成までの許可なのか、デプロイまでの許可なのかが曖昧だと、AI が進みすぎるか、逆に途中で止まりすぎる。初回 HITL で最大到達点を分けて確認することで、自走と安全確認の境界が揃う。

---

## content 品質ルール

### HITL の役割

- human check は全文レビューの場ではない。人間に読ませる量を増やすのではなく、ズレると後戻りが大きい判断だけを短く露出する
- HITL 停止時は「承認してください」だけで止めない。冒頭の `まず見るところ` で、何を判断してほしいか、OK が何を許可し何を許可しないか、迷ったらどこを見るかを 30 秒で読めるようにする
- `人間に戻す主な条件` は Top 3 Stop Conditions として表の前に出す。AC / 技術スタック / 自走・検証境界の 3 系統を短い自然文で示し、詳細な `人間に戻す条件` は `この OK で許可すること / 許可しないこと` の表で補足する
- `まだ確認できないこと` は Not Verified Yet として表の前に出す。post-merge 反映、relearning、prod 相当評価、actual posting、外部サービス状態など、今回の HITL では断言できないものを `Deferred` / `external evidence required` / `blocked if unavailable` で扱い分ける
- `Stage Continuity Brief` は段階計画レビューではない。人間に確認してほしいのは、Stage の生成物が後続でどう使われるか、どの境界が変わると再承認が必要かだけに絞る。全 task / 全 Depends on / 全ファイル一覧は tasklist に残し、HITL では表示しない
- quick (express) の `Stage Continuity Brief` は single-stage 最小表示にする。完全省略しない理由は、出力テンプレートの形を保ちつつ「この task は多段階ではない」と人間に明示するため。standard のような Stage 表や `Plan Revision Ledger` の詳細は出さない
- `段階実装案` は表示されていても、空欄、`TBD`、`TODO`、`適切に`、`必要なら`、`実装する`、`テストする` だけのような曖昧なセルがある場合は contract 違反。`scripts/lint-hitl-stage-plan.py` で human-check draft / fixture を検査できる形にし、複数 Stage では Stage ID と requirements.md の `Implementation Sequence Plan` を対応させる
- `このOKで承認する範囲` は、承認者の誤解を防ぐために必須。`current-pr` はこの PR で実施許可、`follow-up-pr` は原則 `後続PRの方針のみ承認` または `後続PR着手前に再承認` と書く。`follow-up-pr` をこの OK で実施許可にする場合は独立した承認ポイントに昇格する
- `後続の追跡先` は、`follow-up-pr` / `post-merge-verification` の Stage で必須。未作成なら `Planned Follow-up Stage Lane seed を completion/post-merge で作成` と書き、後続 Stage が会話終了で消えないようにする
- `Adversarial Requirements Review` は独立 / 敵対的レビューの議論ログではない。HITL では、承認者が誤承認しやすい反対仮説、ズレリスク、採用した修正、残すリスクだけを出し、Primary / Counter の長い評価本文やモデル比較は出さない
- `LLM 方針レビュー` は方針を出す前の quality gate の結果であり、HITL では「この方針で AI が自走してよさそうか」を判断するための短い確認欄にする。レビューで直せるものは HITL 前に直し、残った判断点だけを出す
- `選択肢の説明` は内部メモではなく、承認者の「Option B とは？」を防ぐための欄である。Option A / B / C を使わない場合は `選択肢なし（単一案。理由: ...）` と書いてよいが、Option B だけを承認ポイントに出してはいけない
- `検証計画` は full test list ではない。人間に確認してほしいのは、どの完了条件をどの場所・どの方法で確認し、何を OK条件 とし、失敗した時に自動修復するのか人間に戻すのかである。実装詳細の全テスト名は tasklist / design に残す
- downstream phase からの再承認では、`前回からの段階計画の変更` に `Plan Revision Ledger` の差分を必ず要約する。新 task が元のどの Stage を変えたのか、後続 invalidation があるかを隠さない
- HITL では「できること」だけでなく、`この OK に含まれないこと` を上部に出す。制限事項は説明文に埋めず、scope / AC、実装、自走、検証の 4 区分で `人間に戻す条件` と一緒に表で示す
- `現在地` は state.md / tasklist.md / requirements.md / design.md を根拠に書く。tasklist.md がまだ無い planning 初回停止では、残タスクを捏造せず「承認後に task-breakdown で作成」と明示する
- requirements.md には `User-Stated Completion Conditions` / `Completion Condition Trace` / `Implementation Approach Trace` の詳細を残す
- Human Check Questions は requirements 側の記録名。human-check では `承認ポイント` として表示する。requirements の質問を別セクションとして二重表示せず、ユーザーが yes/no / 修正依頼で答えられる自然文へ圧縮する
- HITL には `Completion Condition Trace` のうち `refined` / `split` / `deferred` / `dropped` / `added` / `unresolved` だけを原則表示する。`kept` は原則省略し、必要なら「N 件 kept」とだけ書く
- `refined` はすべて表示しない。意味・scope・安全境界・作り方が変わるものだけを出し、ログ粒度・テスト観点・文言の具体化など細部の精緻化は requirements.md 側に残す
- `テスト化確認` は full test plan review ではない。`Completion Testability Matrix` のうち、テスト化できない完了条件、`needs-clarification`、`e2e-required`、`external-evidence-required`、`non-testable-deferred`、解釈差が大きく後戻りが高い `Testable claim` だけを表示する
- unit test / contract test の全件一覧は HITL に出さない。人間に承認してほしいのは「どの完了条件をどの観測可能な claim として扱うか」「E2E / 外部証跡に残す境界が妥当か」だけに絞る
- `技術スタック確認` は dependency 一覧や実装詳細レビューではない。`Technology Stack Fit Matrix` / `Adopted Technology Stack Trace` のうち、vendor official integration とのズレ、既存 repo 標準からの逸脱、MCP / CLI / SDK / API 等の access method、credential backend、multi-tenant 境界、後戻りが高い採用技術だけを表示する
- `実装技術スタック` は、人間が「どういう技術スタックで実装するか」を承認するための短い表である。language / runtime、framework / library、test tooling、access method、credential backend を中心に、既存 repo 標準・公式統合・credential / tenant 境界に関わるものだけを出す
- 後戻りが高い技術判断とは、access method / credential backend / tenant boundary / official integration / existing repo standard のいずれかを変える判断、または一度実装すると wide refactor・認証情報移行・運用手順変更・テスト証跡再作成が必要になる判断を指す
- 公式統合があるのに direct API / CLI wrapper / 独自実装を採る場合、または credential backend（Secrets Manager / SSM / env / OAuth 等）や tenant 切替方式が未確定の場合は、必ず `技術スタック確認` または承認ポイントに出す
- `Implementation Approach Trace` は repo 分割、既存仕組み再利用 vs 新設、import vs recreate、public vs private、CI/CD の載せ方など、後戻りが高い作り方の判断だけ表示する。ファイル単位計画や細かな設計は design-gating に送る

### 承認ポイントの粒度

- `Summary Brief` の「承認ポイント」は summary の言い換えではなく、人間に yes/no で決めてほしい policy question だけを書く
- 各承認ポイントには **変更前 → 変更後**（何がどう変わるか）を含め、人間がコンテキストを遡らずに判断できるようにする
- 原則 **1 項 1 判断** で、誰が / 何が変わるか / 何を承認してほしいかが読み取れるようにする
- 承認ポイントは原則 **3〜5 件** に絞る
- 人間がそのまま読んで判断できる短い自然文にする。内部フィールド名や略語だけで済ませず、必要なら括弧で補足する

### 判定ルールの書き方

- `unknown -> needs_input` のような内部遷移だけでは書かない。必ず「どの条件なら」「何の入力を見て」「どの出力・応答にするか」を自然文で書く
- 判定ルールは少なくとも `条件` / `見る入力` / `出力または次アクション` / `不足時の扱い` の 4 点が読めるようにする
- 悪い例: `unknown は needs_input に倒す`
- 良い例: `service metadata の信頼度が unknown、または PRD / non-PRD 判定に必要な証跡が不足している場合は、自動受理せず needs_input を返して人手確認に止める`

### scope 必須項目

以下が scope にある場合は、それぞれの承認事項を「承認ポイント」に**必ず**含める:
- route / ownership
- secret handling / masking
- rollout / rollback
- 自走上限（実装完了 / PR 作成 / デプロイ準備 / デプロイ実行）

上記カテゴリに関する blocking `Open Questions` が残っている場合は `human-check-waiting` に進めない。

### 承認ポイントの位置関係

- `Summary Brief` は `Design Policy Discussion` の前に置き、人間が短い要約だけ先に読めるようにする
- `Summary Brief` の「一言」で対象と目的、「判断材料」で確定/未確定/非スコープ/外部依存/設計方針が読めること
- `Design Policy Discussion` は「承認ポイント」の判断根拠として、人間が設計方針を先に見てから承認判断できる位置に置く
- 「参考」は折りたたみ的な位置づけ。承認ポイントの判断に必要な情報はすべて承認ポイント内に書く

---

## 含めるべき情報の写像

`requirements.md` / `design.md` の各情報をテンプレートのどこに配置するか:

| 情報 | テンプレートの位置 |
|------|-------------------|
| なぜやるか（WHY・根本原因） | **まず見るところ（30秒判断）の先頭**。WHY が WHAT と HOW の判断根拠になるよう最初に配置する |
| 対象 steering / artifact | 参考 > 詳細 |
| 実装内容・変更内容の要約 | やること |
| state.md / tasklist.md / requirements.md / design.md から分かる workflow 状況 | 現在地（ここまで出来ていること / 人間が今やること / OK 後に残る作業 / 残タスク） |
| Summary Brief 4 層構造（一言 / 判断材料 / 承認ポイント / Honest Limitations） | やること + まず見るところ + 前提 + 承認ポイント（Honest Limitations は `まだ確認できないこと` と参考欄にも写す） |
| Honest Limitations / Open Questions / 外部証跡不足 | まだ確認できないこと（Not Verified Yet） + 必要なら前提 > 非スコープ |
| Approved Direction / safety boundary / recheck trigger | 人間に戻す主な条件（Top 3 Stop Conditions） + この OK で許可すること / 許可しないこと |
| Design Policy Discussion / Options Exploration | 選択肢の説明（Option A / B / C の意味、採用案、採用理由、却下理由。未定義の Option ラベルは禁止） |
| User-Stated Completion Conditions / Completion Condition Trace | ズレ確認 > 完了条件の変換（kept は原則省略、変換・延期・削除・追加・未解決だけ） |
| Completion Testability Matrix | ズレ確認 > テスト化確認（テスト化できない完了条件 / E2E必須 / 外部証跡必須 / 解釈差が大きい条件だけ） |
| Verification Plan / Completion Testability Matrix / no-post / score / compare | 検証計画（どこで確認するか / どう確認するか / OK条件 / 失敗時の扱い） |
| Technology Stack Fit Matrix / Adopted Technology Stack Trace | ズレ確認 > 技術スタック確認（採用する技術スタック / 公式統合 / 既存標準 / access method / credential backend / tenant 境界だけ） + 実装技術スタック（language / runtime、framework / library、test tooling、access method、credential backend） |
| Codebase Health Survey | ズレ確認 > コードベース健全性確認（巨大ファイル / 依存管理 / test baseline / CI baseline のうち、設計・タスク順序・検証へ影響するものだけ） |
| Implementation Approach Trace | ズレ確認 > 作り方の重要判断（後戻りが高い論点だけ） |
| Design Policy Discussion | 前提 > 設計方針（採用案を 1 行で） + 承認ポイントの AI の仮決定 / 根拠 / 却下した代替案 |
| 変更範囲と利用者影響 | 参考 > 変更範囲 |
| リスク / 注意点 | 参考 |
| ロールバック方針 | 参考 |
| 検証方針 | 参考 |
| 未解決の質問 / 仮定 | 前提 > 非スコープ or 承認ポイント |
| 何の承認を求めているか | 承認ポイント（全文） |

---

## 具体例

CI Gated PR Open タスク（standard）での出力例:

```markdown
## 🔍 確認

### やること
PR 作成後に CI が通るまで Draft で待機し、成功後にだけ open して reviewer をアサインする仕組みを全 PR 作成ルートに共通で入れます。CI 失敗時は自動修復を最大 2 回試み、上限超過なら Draft のまま返します。

**タスクサイズ**: standard — 5 ルート共通の契約変更・外部 API 呼び出し方式変更を含むため
**フロー**: 要件整理 → 要件レビュー → 人間確認 → 設計 → 設計レビュー → タスク分割 → TDD → 実装レビュー → 完了チェック
**通過予定 gate 数**: 4 gate（req-gate → design-gate → impl-gate → completion）
**自走上限**: PR 作成まで。merge / deploy は別承認

### まず見るところ

- **判断してほしいこと**: CI 成功判定を required checks に限定するか、自動修復の上限を 2 回にするか、自走上限を PR 作成までにするか
- **この OK で進めること**: PR 作成ルート共通の契約文言・runtime prompt・テストを更新し、PR 作成まで自走します
- **この OK では許可しないこと**: merge / deploy / GitHub branch protection 変更 / 本番 write は含めません
- **迷ったら確認する欄**: 承認ポイント 1-3、技術スタック確認、まだ確認できないこと

### 人間に戻す主な条件

Top 3 Stop Conditions:
- CI 成功判定を required checks 以外に広げる必要が出た場合
- GitHub API の access method、credential backend、PR route ownership を変える必要が出た場合
- merge / deploy / branch protection 変更など、自走上限を超える操作が必要になった場合

### まだ確認できないこと

Not Verified Yet:
| 未確認事項 | 今回の扱い | 確認タイミング / 人間に戻す条件 |
|---|---|---|
| 実 PR での CI 待機から ready_for_review までの end-to-end 挙動 | external evidence required | 実装後の E2E smoke で確認。GitHub 側制約で再現不能なら人間に戻す |

### この OK で許可すること / 許可しないこと

| 区分 | この OK で許可すること | この OK に含まれないこと | 人間に戻す条件 |
|---|---|---|---|
| scope / AC | CI green まで Draft 維持し、成功後 ready_for_review する契約追加 | branch protection 変更、レビュー基準変更、CI 高速化 | AC の意味や対象 route を変える場合 |
| 実装 | 既存 GitHub API client と `AGENTCORE_WAIT_FOR_CI` を使う | credential backend 変更、独自 GitHub client 新設 | access method / credential backend / route ownership を変える場合 |
| 自走 | テスト・実装・PR 作成まで | merge / deploy / GitHub 設定変更 / 本番 write | 自走上限を超える操作が必要な場合 |
| 検証 | unit / contract / E2E smoke を実施 | 実運用 PR 全ルートでの長期観測 | E2E smoke 不可、外部証跡不足の場合 |

### 現在地

| 項目 | 内容 |
|------|------|
| ここまで出来ていること | 要件整理と承認ポイントの抽出まで完了 |
| 人間が今やること | 承認ポイント 1-3 を確認し、OK / N は変更 / 全面見直し のどれかで返答する |
| OK 後に残る作業 | design-gating → task-breakdown → TDD → 実装 → implementation-gate → completion-check → PR 作成 |
| 残タスク | 承認後に task-breakdown で作成 |

### 前提
| 項目 | 内容 |
|------|------|
| 確定 | Draft PR → CI 待機 → green で ready_for_review。既存の `AGENTCORE_WAIT_FOR_CI` フラグで制御 |
| 非スコープ | branch protection 変更、CI 自体の高速化、レビュー基準の変更 |
| 外部依存 | GitHub API（`ready_for_review` 切り替え）、既存の `github-api` Lambda |
| 設計方針 | shared reference（`pr-ci-gate.md`）に共通契約を集約し各 skill はそれを参照するだけにする |

### 承認ポイント

**1. 修復ループの上限**
- **AI の仮決定**: 自動修復は最大 2 回、上限超過なら Draft のまま返す
- **根拠**: 1 回だと一時的エラー（flaky test 等）に弱く、3 回以上は Claude API コストと CI 実行時間が増大するため。コスト対回復率のバランス点として 2 回を採用
- **却下した代替案**: 上限 1 回（retry 不足で flaky に弱い）／上限なし（無限ループで料金爆発のリスク）
- **判断に影響する前提**: CI の flakiness が現状同等（5% 未満の一時失敗率）。flakiness が悪化したら上限再検討

**2. CI 成功判定の基準**
- **AI の仮決定**: `required checks` が全て成功した時点で CI 成功と判定し ready 化
- **根拠**: `required checks` は PR マージ可否のゲートとして既に branch protection で定義済み。この定義を流用することで判定基準の二重管理を避ける
- **却下した代替案**: 全 checks 成功（optional な lint 失敗で ready 化が止まるリスク）
- **判断に影響する前提**: 現行の branch protection が維持される。required checks の定義変更があれば再検討

**3. 方向性**
- 自走範囲: 各 skill / command の契約文言更新、runtime の prompt 更新、テスト追加
- 自走上限: PR 作成まで。merge / deploy は別承認
- 人間に戻す条件: 新しいセキュリティ要件の発生、`AGENTCORE_WAIT_FOR_CI` の挙動変更が必要な場合

### 用語の短縮定義
- `ready_for_review`: Draft PR を通常の PR に切り替えて reviewer 割当を開始する GitHub API 操作
- `required checks`: branch protection で必須化された CI check（merge の前提条件）

### 参考（任意）
変更範囲: repo-pr / idc / route53 / cloudflare-drift / route53-drift の各 skill | 詳細: `.steering/<dir>/requirements.md`
```

---

## 返答分類の判定基準（メインセッション向け）

テンプレート出力後のユーザー返答を以下のフローで分類する。

### 曖昧返答の検出

「たぶんOK」「後で考える」「いいかも」「まあいいか」等、明確な承認（OK）でも明確な修正指示でもない返答は **曖昧返答** として扱う。曖昧なまま `approved` にしない。

#### 判定ルール（hedge 語彙 AND 進行指示の弱さ）

曖昧返答の判定は以下 2 条件の **AND**（両方満たしたときに強制再質問）:

1. 返答に以下の **hedge 語彙が 1 つ以上含まれる**
2. 返答の **明示的進行指示が欠落している、または弱い**（「OK」「承認」「進めて」等の明確な承認表現がないか、hedge に打ち消されている）

**hedge 語彙リスト**（日本語圏）:
- たぶん / おそらく
- まあ / まあまあ / まあいいか / まあいいんじゃない
- 一応
- 悪くない
- かも / かもしれない
- いいかも / 良さそう（単独時）
- 後で考える / 後で見る
- とりあえず / ひとまず
- 別にいい / 別に

#### ケース別判定

| 返答例 | hedge 有無 | 進行指示 | 判定 |
|--------|-----------|---------|------|
| 「OK、進めて」 | なし | 強 | approved |
| 「OK で」 | なし | 強 | approved |
| 「一応テストも通ってるし OK、進めて」 | あり（「一応」） | 強（「OK、進めて」） | approved（hedge は状況説明） |
| 「たぶん OK」 | あり | 弱 | 再質問 |
| 「まあいいんじゃない？進めて」 | あり | 中途半端（hedge に打ち消される） | 再質問 |
| 「一応これで良さそう、続けて」 | あり | 弱（「一応」が承認を弱める） | 再質問 |
| 「悪くないけど、気になる点があるかも。でも進めて」 | あり（複数） | 未解消懸念あり | 再質問 |

**AND 条件の意図**: hedge 語彙単独で再質問にすると「一応テストも通ってる」等の状況説明で誤検出する。明示的進行指示（OK / 進めて / 承認）が hedge に打ち消されず強く残っているなら approved として扱う。

#### 再質問テンプレ

```
承認か修正かが判断できませんでした。以下のどちらかで明示的にお答えください:
- 承認して自走を開始: 「OK」とだけお返事
- 修正したい点がある: 具体的に箇所と変更内容を教えてください
```

### 修正指示の 4 分類

ユーザーが修正を指示した場合、以下の順で判定する:

| 判定順 | 条件 | 分類 | アクション |
|--------|------|------|-----------|
| 1 | AC の追加・削除・条件変更がある | **AC 変更（全面見直し）** | `planning_rework_required` で `gdd-brainstorming` に差し戻し |
| 2 | AC は維持、実装アプローチ・技術選定が変わる | **実装方針変更** | `design_detail_only` で `gdd-design-gating` から再開 |
| 3 | AC は維持、`Approved Direction`（自走範囲 / 人間に戻す条件）のみ変更 | **方向性 metadata 修正** | `state.md` の `Approved Direction` を上書きし、差分だけ再提示 → 承認されたら `Route In Progress=none` にクリアして元の `Resume From` から再開 |
| 4 | AC の値・条件・対象が変わらない（文言・非機能・表現のみ） | **部分修正** | 該当ポイントだけ修正 → 変更箇所だけ再提示 → `human-check-waiting` 継続 |

**判定に迷う場合**: 安全側に倒す（4 より 3、3 より 2、2 より 1 を選ぶ）。ユーザーに「AC 自体の変更ですか？ それとも実装方法の変更ですか？ それとも方向性だけの変更ですか？」と確認してもよい。

### 即再承認の短絡形（human_recheck_required 直後）

AI が `human_recheck_required` を提示した直後にユーザーが即再承認する場合、状況に応じて以下の短絡形を使う。

| 状況 | 短絡形 | 理由 |
|------|-------|------|
| ユーザーが却下対象を取り下げて元の計画で再承認 | 再 brainstorming せず **元の `Approved Direction` で `Human Check Status=approved` に遷移**。`Route In Progress=none` クリア | 新情報がないため Problem Discovery をやり直す必然性なし |
| ユーザーが新 AC を具体的に文言まで提示した AC 追加 | `planning_rework_required` の短絡形として **`gdd-requirements-gating` から再開**（brainstorming をスキップ） | AC が具体的に示されており Problem Discovery は不要 |
| ユーザーが `Approved Direction` のみ変更（人間に戻す条件の調整） | 上記「4 分類」の 3 番（方向性 metadata 修正）を適用 | AC / 設計に影響しないため |

**共通の承認後処理**（全ケース）:
1. `Human Check Status=approved` を `state.md` に記録
2. 新 `Approved Direction` を記録（変更がある場合）
3. **`Route In Progress=none` にクリア** — 忘れると次の gate check で不整合扱いされる
4. `Resume From` を次 phase に更新（短絡形のテーブルに従う）
