# R9-2 pilot 前の原本（main 2026-07-17 時点、旧#162/#166/#167 反映済み）。過去セッション事例の一次記録はこちら。

# Brainstorming: Steps

> **所有**: `gdd-brainstorming` の詳細手順
> **参照元**: `skills/gdd-brainstorming/SKILL.md`

## Steps

1. plugin 内 `references/self-contained-contract.md` を読み、entry intent、active steering の決定規則、fail-closed 条件を確認する。`references/state-machine.md`（詳細な遷移表）は entry intent が `ambiguous` と判定された場合、または fail-closed 判定の根拠が必要な場合にのみ読む。通常の `new` / `resume` 判定では読まない。
   - same-name ambient asset が別実体で plugin 側 asset を deterministic に解決できない場合は unsupported configuration として fail-closed で停止する。
2. `references/entry-intent.md` の判定ルールに従って、今回の `/gdd-dev` 明示実行が `new` / `resume` / `ambiguous` のどれかを判断する。
   - 判定は明示 cue のみで行い、implicit な推測はしない。
   - `ambiguous` で止める場合も、`進めない` だけで終わらせず、`参照した正本` / `停止理由` / `次の1アクション` を返す。
   2a. **Clarification Loop（artifact 作成前の要件固め）**: `new` と判定した直後、worktree 作成・`.steering/` 作成・requirements 初稿作成の前に、ユーザー入力だけで scope を固めると誤決定になりやすいかを確認する。誤決定になりやすい場合は、requirements を作らず、会話で要件を固める loop に入る。
   - **発火条件**（いずれか 2 つ以上、または 1 つでも影響が大きい場合）:
     - 対象が未指定: 「通知を改善」「レビュー体験を良くする」「運用を楽にする」等で、どの画面 / コマンド / skill / workflow / 出力を変えるか不明
     - 成功条件が未指定: 「良い」「使いやすい」「固めたい」等で、pass/fail 可能な AC に落とせない
     - 非スコープが未指定: 似た対象が複数あり、今回やらない範囲を AI が推測で決めることになる
     - 優先順位が未指定: 速度 / 厳密さ / UX / 安全性 / コスト削減など、重みで設計が変わる
     - ユーザーが「相談したい」「改善したい」「整理したい」「固めたい」と表現しており、実装指示より方向性相談に近い
   - **発火しない条件**:
     - 変更対象ファイル / 関数 / コマンドが明示され、AC が 1〜3 個に自然に落ちる
     - ユーザーが `--yes` / `--auto-confirm` / 「仮案で進めて」等、AI に scope 仮決定を明示委任している
     - `resume` / `amendment` / active follow-up で、既存 artifact の承認済み方向性を参照できる
   - **ready criteria（全て満たすまで loop 継続）**:
     - 目的: なぜやるか / 誰が困っているかを 1-2 文で説明できる
     - scope: 今回やる対象と、今回はやらない対象が区別できる
     - success: pass/fail 可能な受入条件に落とせる
     - priority: 速度 / 厳密さ / UX / 安全性 / コスト削減など、設計判断で優先する軸が分かる
     - ownership boundary: 判断が必要な人間責任の scope 選択が残っていない
   - **出力ルール**:
     - まず `Intake Brief` を出し、`確定済み` / `判断材料（今回わかっていること）` / `まだ曖昧` / `次に決めること` / `回答後にどう進むか` を更新する。質問は少なくしてよいが、判断材料は省略しない
     - `判断材料（今回わかっていること）` は、ユーザーが「どの選択肢を選ぶと何が変わるか」を判断できる最低限の材料を 3-5 行で示す。候補が複数ある場合は、`候補` / `何が良くなるか` / `向いている範囲` / `後でテストできる形` を短く書く
     - 外部調査、公開事例、論文、既存コード調査、類似実装比較、選択肢比較を行った場合、source link や候補名だけで止めない。`調査から分かったこと` と `選択肢の違い` を `判断材料（今回わかっていること）` に要約してから質問する
     - 質問は「今 requirements 化すると誤りそうな点」に絞る。未確定が多い場合でも、readiness 全軸を一度に埋めようとしない。scope / success / priority / non-scope / ownership boundary のうち、最も誤決定リスクが高い 1〜2 軸だけを次の質問にし、複数往復で固める
     - 各質問には、何を決める質問か（scope / success / priority / non-scope / ownership boundary）、なぜ今決める必要があるか、回答が requirements.md の AC / Non-Goal / Deferred / Implementation Approach / technology stack のどこへ反映されるかを 1 行で添える
     - 推奨デフォルトを出せる場合は添えるが、推奨だけで scope を確定しない。推奨を出す場合は、採用すると何を requirements 化し、何を後回しにするかを明記する
     - 回答形式を簡単にする。例: `A/B/C で回答、補足があれば追記`
     - `回答後にどう進むか` には、回答後に再 clarification するのか、requirements / design を作って human-check へ進むのかを明記する
     - 実装方式（ライブラリ、ファイル分割、細かなテスト方法）は聞かない。正式 workflow の design-gating に送る
     - 末尾に `<gdd-stop reason="clarification-needed">` を付ける
   - **禁止**:
     - Clarification Loop 中に `.steering/...`、`requirements.md`、`design.md`、`state.md` を作らない
     - 曖昧なまま 2-3 案を requirements に書いて human-check へ進まない（ユーザーが求める「往復で固める」体験を壊す）
     - `Human Check Questions` の代替として artifact 作成後に質問停止しない。artifact 作成後は通常の human-check-waiting でまとめて承認を取る
   - **ユーザー回答後**:
     - 回答を元の `$ARGUMENTS` に追記した確定情報として扱い、ready criteria を再評価する
     - ready criteria が未充足なら、`Intake Brief` を更新して Clarification Loop を継続する。人工的な往復回数上限は置かない
     - ready criteria を満たしたら、回答済みの内容を `$ARGUMENTS` に含めて Step 1 から再開し、Step 3 以降の formal workflow に入る
   - **Why:** 広い依頼を AI が一発で requirements 化すると、scope / 成功条件 / 非スコープが既成事実化し、人間は差分修正でしか戻せなくなる。artifact 作成前に requirements readiness を満たすまで会話で方向を締めることで、GDD の「後工程を自走する」強みを保ったまま、要件整理だけは人間と往復できる。
3. `resume` の場合だけ、git worktree の列挙を正本として active steering candidate を 1 つに絞る。
   - build candidate と planning candidate が同じ worktree で競合した場合は fail-closed で停止する。
   - 同一優先順位に candidate が複数ある場合は fail-closed で停止し、どの steering を再開するか明示指定を要求する。このとき `候補一覧` と選び方を返し、新しい steering を作って曖昧さを吸収しない。
   - `resume` なのに worktree candidate が 0 件なら、legacy root steering の migration 候補を調べる。migration 候補も 0 件なら fail-closed で停止し、再開対象の指定か新規開始のどちらを求めるかを明示する。
4. worktree 解決は `gdd-using-git-worktrees` の helper 契約に従う。
   - `new`:
     - task slug を決める
     - default branch から task 専用 branch / worktree を作る
   - `resume`:
     - active worktree を再利用する
   - legacy migration:
     - worktree candidate が無く、legacy root steering が 1 つだけ解決できる場合に限り、task 用 branch / worktree を作るか再利用し、root 側 `.steering/...` を worktree 側へ 1 回だけコピーする
   - git/worktree や migration 前提が足りず停止するときは、current な phase 判断を変えずに復旧手順を返す
     4a. **Worktree Guard（必須チェック）**: Step 4 の worktree 解決が完了したら、以降の Step に進む前に以下を確認する:
   - `git worktree list --porcelain` を実行して worktree パス一覧を取得する
   - Step 4 で作成・特定した worktree の **絶対パス**（以下 `$WORKTREE_ABS_PATH`）を確定し、記録する。例: `/Users/foo/.gdd/worktrees/my-repo/20260503-my-task`
   - **`$WORKTREE_ABS_PATH` がプロジェクト root（`git rev-parse --show-toplevel` の値）と一致する場合は fail-closed**：root は main branch の作業ディレクトリであり、タスク専用 worktree ではない。worktree 作成が未完了のため停止し、原因と復旧手順を返す
   - worktree が確定していない状態で Step 5 以降に進まない（fail-closed）
   - worktree 作成に失敗した場合は、失敗理由と復旧手順を返して停止する。root directory で代替作業しない
   - **Why:** worktree guard が宣言だけで強制されないと、CWD が root のまま Step 5 で `.steering/` が root 直下に作られ、他の worktree との状態分離が壊れる。`$WORKTREE_ABS_PATH` を明示的に確定させることで、以降の artifact 書き込みが必ず worktree 内に向く
   - **pre-artifact 機械チェック**: `.steering/`、`requirements.md`、`design.md`、`state.md` のいずれかを作る前に、`scripts/assert-worktree-ready.py --repo-root <repo-root> --worktree-path "$WORKTREE_ABS_PATH" --steering-slug <slug>` を実行する。これは root に `.steering/` を作る前に失敗させるための pre-artifact guard であり、subagent 復帰後の検知で代替してはならない
5. `$WORKTREE_ABS_PATH/.steering/YYYYMMDD-short-title/` を決める（**必ず絶対パスで指定**。root の `.steering/` への Write は禁止）。
   - `new` なら新規作成する
   - `resume` なら既存 artifact を更新する
   - **同一 slug の root 側 `.steering/<slug>/` が残っていないかを確認する**。legacy migration で明示的に移す場面を除き、root 側 copy が見つかったら root bleed / 置き去り artifact として fail-closed。root と worktree の両方を更新したまま先へ進まない
   - current task の `.steering/<slug>/` は managed artifact なので、以後の PR / cleanup で「untracked だから任意」と扱わない
6. 運用レベルを解決する。優先順位: ユーザー明示（`--level`） > リポジトリ設定（`.gdd-config.md` の `Operation Level`） > デフォルト（`standard`）。運用レベルの詳細は `references/operation-levels.md` を参照。解決した運用レベルを `state.md` の `Operation Level` フィールドに記録する（監査証跡。タスク完了まで変更しない）。
7. タスク規模を `trivial` / `quick (express)` / `quick (standard)` / `standard` で判定する。判定基準は `references/task-sizing.md` を参照。`scripts/suggest-task-size.sh` を実行するとキーワード・diff ベースの自動提案を得られる（`bash scripts/suggest-task-size.sh "タスクの説明"`）。自動提案はあくまでヒントであり、最終判定はユーザーの明示指定を優先する。運用レベルに応じて gate / reviewer の適用範囲が変わる（`references/operation-levels.md`）。
   - `trivial` の場合は artifact-less trivial として `.steering/` を作らず、直接変更を実施して完了する（step 9 以降は skip）。作業履歴は commit message と通常の会話ログに残し、root `.steering` へ最小 state を作る fallback は禁止
   - `quick (express)` の場合は step 7b で Direct Intent スコアを計算し、step 7a（Express Path）に進む。Direct Intent 該当（3 点以上）なら Express Path 内の Refinement も 1 回に制限される（Express + Direct Intent = 最速パス）
   - `quick (standard)` の場合も step 7b で Direct Intent スコアを計算する。3 点以上なら Options Exploration skip + Refinement 1 回制限が適用される
   - `standard` の場合は step 8 以降の通常フローに進む（Direct Intent は standard に適用されない）
   - Step 7 の sizing は**暫定判定**。最終決定は requirements 初稿の後（Step 11a）で行う
   - ユーザーが明示した場合はそれに従う。`--express` 引数は express を強制する
   - 判定が微妙な場合はユーザーに確認する
   - `requirements.md` の冒頭に `Task Size: quick (express)` / `Task Size: quick` / `Task Size: standard` を記録する
   - `quick (standard)` の場合、`requirements.md` と `design.md` は最小構成で進める（`references/task-sizing.md` の表を参照）
   - どのパスでも human check、AC 明示、fail-closed 条件は省略しない
     7t. **Artifact-less Trivial**: `trivial` 判定の場合、trivial は `.steering/` を作成しない。`requirements.md` / `design.md` / `tasklist.md` / `state.md` は作らず、直接変更して commit message に `[trivial] <変更理由>` を残す。trivial が作業中に quick 以上へ昇格した場合は、Step 4 に戻って worktree を作成し、`scripts/assert-worktree-ready.py` を通してから通常フローの artifact を新規作成する。
   7s. **Quick Standard State Bootstrap**: `quick (standard)` 判定の場合、worktree 内の `.steering/YYYYMMDD-short-title/` に最小 `state.md` を即座に作成する:

   ```
   Task ID: <YYYYMMDD-short-title>
   Task Size: quick (standard)
   Requirements Review Status=pending
   Human Check Status=pending
   Design Review Status=pending
   Resume From=gdd-brainstorming
   ```

   Step 13 でこの `state.md` を上書きするが、brainstorming 途中で中断してもセッション復帰時にフックが状態を表示できるようにする。quick (standard) は requirements.md を作成する前にフローが中断することがあるため、state.md だけは先に作る。
   7b. **Direct Intent 判定**: ユーザー入力が十分に具体的な場合、Options Exploration（Step 10）と Iterative Refinement Loop（Step 16）を skip して brainstorming を高速化する。
   - **判定条件**（スコアリング方式。3 点以上で direct intent）:
     | 条件 | 点数 | 例 |
     |------|------|-----|
     | 変更対象ファイルが明示されている | +2 | 「`src/api/users.ts` の…」 |
     | 関数名・コンポーネント名が明示されている | +1 | 「`validateInput` に…」 |
     | アクションが動詞 1 語で完結 | +1 | 「追加」「修正」「削除」「更新」 |
     | 疑問文・相談形でない | +1 | ×「〜した方がいい？」「〜どうすれば？」 |
     | AC が 2 個以下に収まる | +1 | 単一の変更目的 |
     | standard タスクである | -3 | standard は Options Exploration 必須 |
   - **3 点以上 → direct intent**:
     - Step 9（Problem Discovery）は通常通り実施する（変更対象の現状把握は省略しない）
     - Step 10（Options Exploration）を skip する
     - Step 16（Iterative Refinement Loop）を 1 回に制限する（Gap Scan で重大な gap があれば通常ループに戻る）
     - `requirements.md` に `<!-- Direct Intent: score=N, skip options exploration -->` を付記する
   - **2 点以下 → 通常フロー**:
     - Options Exploration と Iterative Refinement Loop を通常通り実施する
   - **広い要件の強制通常フロー**: 入力が「改善したい」「整理したい」「楽にしたい」「品質を上げたい」「使いやすくしたい」「運用しやすくしたい」のように目的語はあるが scope / 成功条件 / 対象ユーザー / 非スコープが複数に分かれる場合、スコアが 3 点以上でも direct intent にしない。`Broad Requirement: true` と記録し、Step 10 の Options Exploration を必須にする
   - **Why:** ユーザーが「src/api/users.ts にバリデーション追加して」と具体的に指示しているのに、「やらない案」を含む 2-3 案の比較や 5 回の Refinement Loop は不要。スコアリング方式にすることで、判定基準が再現可能になり、境界ケースでも一貫した判定ができる
     7a. **Express Path**（`quick (express)` のみ）: 軽量フローで brainstorming → human check → build を最短で通る。Direct Intent（Step 7b で 3 点以上）の場合、Problem Discovery 後すぐに requirements を作成できる。
   1. Problem Discovery（Step 9 と同じ）: 変更対象のコードを読み、問題を理解する
   2. Express テンプレート（`references/requirements-template.md` § Express requirements.md テンプレート）で `requirements.md` を作成する。design.md は作成しない。Direct Intent の場合は `<!-- Direct Intent: score=N, express fast-path -->` を付記する
   3. `state.md` を以下に設定する:
      - `Requirements Review Status=approved`（reviewer skip）
      - `Design Review Status=approved`（design.md 不要）
      - `Human Check Status=pending`
      - `Resume From=human-check-waiting`
   4. Express 昇格条件（`references/task-sizing.md` § Express 昇格条件）をチェックし、該当すれば quick (standard) に昇格して step 8 に戻る
   5. タスクサイズ判定結果は human-check テンプレート（`references/human-check-template.md`）の「タスクサイズ」「フロー」行で明示する。Express の「フロー」値: `要件整理 → 人間確認 → TDD → 実装 → 品質レビュー → 完了（AI reviewer・設計・タスク分割・完了チェックはスキップ）`
      5e. **Express 最小 tasklist.md 作成**: `gdd-task-breakdown` をスキップするため、human check 承認後（`Human Check Status=approved` 確認後）、TDD 開始前に必ず tasklist.md を作成する。**`### Task: T-N` 形式は Express でも必須**（セッション復帰フックが `### Task:` ヘッダーを数えるため、`- [x]` チェックボックスや他の形式を使うと進捗が検出できない）。

   ```
   ## Current Task
   ### Task: T-1 <実装内容1行>
   - AC: AC-1
   - Covers AC: AC-1

   ## Pending Tasks
   - なし

   ## Completed Tasks
   - なし
   ```

   タスクが複数ある場合は T-2, T-3 と連番を付けて `## Pending Tasks` に並べる。完了したら `## Completed Tasks` に移す。6. `<gdd-stop reason="human-check-waiting">` で停止する（通常フローの Step 18 と同じタイミング）

8. ユーザーの入力に具体的な技術名（framework / library / cloud service / AI service 等）が明示されている場合のみ、その技術が version-sensitive または fast-moving かを判断し、最新の公式ドキュメント / release notes / migration guide を確認する。利用可能なら `tech-docs-searcher` を優先し、無ければ host の web/doc search で補う。技術名が明示されていない場合はスキップし、不明点は `Open Questions` に記録する。
   また、ユーザーが外部 API 連携・認証フロー・AI サービス連携など実装アプローチが技術的に非自明なものを明示した場合は、`similar-case-researcher` または `tech-docs-searcher` で類似事例を調査し `findings.md` に記録する。内部コードの変更のみの場合はこの調査を省略してよい。
   8a. **外部 API 統合チェック（External API Integration Check）**: 外部 API 連携が要件に含まれる場合、以下を brainstorming 中に確認し `requirements.md` の `External Dependencies` または `Open Questions` に記録する:
   - API ドキュメントでレスポンスのサンプル JSON を入手したか（表示に必要なフィールドがレスポンスに直接含まれるか、間接解決（別エンドポイント呼び出し）が必要か）
   - 認証方式（PAT, OAuth, API Key）と取得元（SecretsManager 等）を明記したか
   - レートリミット / ページネーション仕様を確認したか
   - **Why:** ある外部 API は組織の表示名をレスポンスに含まず、別エンドポイントでの事前取得が必要だった。レスポンス構造の事前確認を怠ると実装中に設計変更が発生し、コンテナデプロイの往復が増える
     8b. **Runtime 環境変数の依存（Runtime Environment Variable Dependencies）**: 新しいスキルや機能が Runtime 環境変数を必要とする場合、以下を `requirements.md` に明記する:
   - 必要な環境変数名、用途、値の取得元（SecretsManager / SSM Parameter Store / 固定値）
   - IaC（Terraform `agent_runtime_env` 等）への反映先
   - IAM ポリシーへの追加が必要な権限（`secretsmanager:GetSecretValue` / `ssm:GetParameter` 等）
   - **Why:** ある一覧の投稿機能では環境変数 4 つ + IaC 変更 + 権限ポリシー変更が必要だったが、要件段階で網羅できていれば実装フェーズの手戻りが減る
     8c. **Migration / Conversion タスク判定（Format Conversion Check）**: 既存ファイルを別フォーマットへ変換する種類のタスク（例: `.md` → `.yml`、JSON → YAML、framework A → B、table markup → form field）を検知した場合、以下の AC を `requirements.md` の `受入条件` に必須で含める:
   - **AC-F1（原文保全）**: 変換元ファイルに含まれる全要素（本文・URL・注釈番号・手順リンク・例示・備考）が変換後ファイルのいずれかのフィールド（description / options / placeholder / value 等）で参照可能な形で保持されている
   - **AC-F2（変換先ネイティブ機能の活用）**: 変換先フォーマットが提供するネイティブ機能（YAML Forms の `type: input` / `dropdown` / `checkboxes`、UI framework の component、API の structured field 等）を単一値・列挙・キーバリューに対して適切にマッピングしている（全部 `textarea` + raw markup の丸ごと埋め込みで逃げない）
   - **AC-F3（content-diff の検証手段）**: 変換前後の内容差分を機械的に検証できる（元ファイルに出現する URL・記号付きキーワード・人名・手順リンクが変換後にも存在することを grep / script で確認できる）
   - **AC-F4（レンダリング / 実動作の目視確認）**: 変換後の成果物を **実際のレンダリング環境** で 1 件以上目視確認し、evidence（スクリーンショット URL・確認ログ・レンダリング結果の要約）が `Verification` に残っている。YAML Forms → GitHub の Issue 作成画面、Markdown → 実レンダリング、UI framework 変更 → 実ブラウザ、API → 実リクエスト。YAML として parse できる / JSON schema が通る等の静的チェックだけで AC-F4 を pass 扱いしない。Honest Limitations で「merge 後に目視確認」と逃がすことは不可（目視までが verification の一部）
   - **検知ヒント**: 対象動詞 =「移行」「変換」「置き換え」「YAML 化」「Forms 化」「フォーマット変更」「マイグレーション」、または 動詞 + 「既存の ... を」のパターン
   - **記録先**: `requirements.md` の冒頭「Summary Brief / 判断材料」に `タスク種別: migration/conversion` と明示し、`受入条件` に AC-F1 / AC-F2 / AC-F3 / AC-F4 を連番（AC-1 / AC-2 / AC-3 と独立させず、既存 AC の末尾に繋げる）で追加する
   - **Why:** 複数の Issue template を `.md` → `.yml` に変換したタスクでは、構造変換の AC だけ書き、原文保全の AC が無かったため、複数の content-loss（手順 URL、問い合わせ先、注釈記号等）が PR 作成後のレビューで初めて検出された。追加で「表を textarea に丸埋め」してしまい YAML Forms のネイティブ機能が活かせていないこと、さらに「実際に GitHub の Issue 作成画面でどう見えるか」を誰も確認していなかったために merge 後に初めて UI の違和感が露呈した。変換系タスクは「変換できる」「原文を落とさない」「変換先機能を活かす」「実環境で期待通り見える」の 4 レイヤーを AC として独立させないと gate で検知できない
     8d. **IDE 互換性チェック（IDE Compatibility Check）**: skill / hook / plugin / slash command / `settings.json` / `.claude/` 配下の設定ファイルの新規作成または変更を含む場合、以下を `requirements.md` の `受入条件` に明示する:
   - Codex / Cursor / Claude Code で動作するか（特に: 対話/非対話の分岐、subagent 呼び出し時の挙動差異）
   - `CLAUDE_CODE_SESSION_ID` / `GDD_RUNTIME` 等の Claude Code 固有環境変数を参照している場合、Cursor での代替手段または fallback を設けるか・設けないかを明示する
   - hook スクリプトが Claude Code の stop hook として実装されている場合、Codex / Cursor では同等の動作を `AGENTS.md` / `CLAUDE.md` 等の静的指示で代替できるか確認する
   - **検知ヒント**: タスクの変更対象に `~/.claude/skills/`・`~/.claude/plugins/`・`hooks/scripts/`・`settings.json`・`SKILL.md`・`CLAUDE.md` のいずれかが含まれる場合に適用する。変更対象ファイルがプロジェクトの worktree 外（例: `~/.claude/` 配下のグローバルディレクトリ）にある場合も、IDE 設定系ファイルへの変更であれば適用する
   - **Why:** skill / hook 変更で Claude Code 向けの実装が完了した後に「Cursor でも動くようにして」という後追い修正が複数セッション（20260419、20260423、20260427、20260501）で繰り返し発生していた。IDE 互換性を AC として実装前に確定していれば、同一タスク内で複数ホストの動作を一度に設計・実装できる。
     8e. **Command Interface Design Check（コマンドI/F設計の事前固定）**: Slack コマンド / slash command / CLI コマンドの**新規追加**を含む場合、以下を requirements.md に明記してから human check に出す。human check でコマンド名・引数構造・関連コマンドが変更されると「修正版」の再提示が複数回必要になるため、設計を事前に固める。
   - **コマンド名**: 候補を 1 案に絞り、既存コマンドとの命名重複・紛らわしさを確認する（`explicit-route-inventory.md` または CLAUDE.md の許可コマンド一覧を参照）。**絞り切れない場合は**候補・推奨案・判断軸を `Human Check Questions` に列挙して 1 回の human check で確定する
   - **引数設計**: 引数あり単一コマンド（`/cmd action`）か、引数なし複数コマンド（`/cmd-start` + `/cmd-stop`）かを明示する。**決まらない場合は**両案のメリット・デメリットと推奨案を `Human Check Questions` に列挙する
   - **関連ユーティリティコマンド**: ヘルプ / 一覧 / 状態確認コマンドが必要か、本タスクに含めるか別タスクとするかを明示する。**決まらない場合は** `Human Check Questions` に列挙する
   - **Why:** コマンド名・引数構造・関連コマンドが未確定のまま human check に出ると、修正版の再提示が複数回（4回）発生した。設計インターフェースを requirements 段階で固めることで往復を削減する
     8f. **Execution / Evaluation Reality Check（実行実体・評価実体の確認）**: 実行環境、評価環境、AI/agent/model、CI、自動化、benchmark、prompt/skill/plugin/hook/command のいずれかが品質や成否に影響するタスクでは、requirements.md を書く前に「実際に何がどこで動き、何を根拠に pass/fail するか」を確認する。これは特定ランタイムの例外処理ではなく、実行者と評価者がズレる全タスクに適用する汎用チェックである。
   - **適用トリガー**:
     - AI review / agent / model / prompt / benchmark / eval / score / ranking / 自動判定 / 品質ゲートを扱う
     - skill / plugin / hook / slash command / CLI / CI job / background job / scheduled task / production runtime の新規作成または変更を含む
     - local IDE での確認結果を production / CI / bot / runtime の品質根拠に使おうとしている
     - Codex / Cursor / Claude Code の複数ホストで同じ成果物を使う
   - **調査内容**:
     - Execution Reality: 実際に動く host / runtime / entrypoint / command / agent / model / provider / 権限 / 認証 / 非対話実行条件 / input-output boundary を確認する
     - Evaluation Reality: benchmark / eval / test / human review / CI のうち、どれが release gate でどれが exploratory かを分ける。release gate とするには production 相当性の根拠を明記する
     - Host Compatibility Matrix: Codex / Cursor / Claude Code での role（主実行・補助検証・非対応）、制約、代替手段、release gate として扱えるかを表で整理する
     - Evidence Boundary: local pass、prompt dry-run、別モデルでの成功、別 IDE での成功を本番合格扱いにしない。parity が証明できない場合は `探索結果` として扱い、`Human Check Questions` に残す
   - **記録先**:
     - `requirements.md` の `Execution / Evaluation Reality`、`制約・前提・依存関係`、`検証ヒント`、`Human Check Questions`
     - 調査ログ・根拠 URL・コマンド結果・類似事例は `findings.md`
   - **Why:** GDD は要件段階で「何を作るか」だけを整理すると、実際に評価する host / model / runtime / CI とズレたまま human check を通してしまう。AIレビュー改善、prompt tuning、skill/plugin 変更、自動化タスクでは、このズレが「ローカルでは良いが本番では効かない」「Codex では通るが Claude Code/Cursor では使えない」という手戻りになる。実行実体と評価実体を汎用的に固定してから AC を作ることで、コーナーケースの積み増しではなく再利用可能な品質ゲートになる
     8g. **Technology Stack Fit Check（技術スタック適合確認）**: 外部サービス、SDK、CLI、MCP、API、framework、runtime、IaC provider、DB、AI model/eval 基盤を新規採用または変更する場合、requirements.md を書く前に採用方式の候補を比較する。
   - **適用トリガー**:
     - 外部サービスや vendor integration を使う
     - `MCP / CLI / SDK / API` のように複数の access method が自然に存在する
     - credential backend（Secrets Manager / SSM / env / OAuth 等）、multi-tenant、account/service/env 切替が設計に影響する
     - repo に既存の同種パターンがあり、新規採用方式がそれと違う
   - **調査内容**:
     - 公式統合: vendor official MCP / SDK / managed integration / CLI / API があるか、GA / preview / deprecated / unavailable のどれか
     - 既存標準: repo の既存 dependency、runtime helper、Terraform module、project skill、運用手順に合うか
     - access method: MCP / CLI / SDK / API / wrapper / managed integration の候補比較
     - credential / tenant: multi-tenant 切替、credential backend、IAM scope、secret 実値をどこにも出さない境界
     - testability: unit / contract / E2E / external evidence のどこで検証できるか
   - **記録先**:
     - `requirements.md` の `Technology Stack Fit Matrix`
     - 採用案は `Adopted Technology Stack Trace`
     - 後戻りが高い採用技術は Summary Brief の `技術スタック確認` と `Human Check Questions`
     - 公式統合や最新情報の根拠は `Latest Tech Context` / `findings.md`
   - **判断ルール**:
     - 公式統合がある場合はまずそれを第一候補にする。別方式を採るなら理由を明記する
     - 候補が 1 つしかないように見えても、`Existing repo standard` と `Official integration` は必ず確認する
     - multi-tenant / credential backend / access method が未確定なら、AI が仮決定したまま silent に実装へ進まず HITL に出す
   - **Why:** Datadog 連携で direct API helper を先に設計し、後から「公式 MCP が GA」「複数テナントなので account ごとの切替が必要」と判明して技術スタックがズレた。要件段階で Technology Stack Fit Matrix を作れば、`何を作るか` だけでなく `何で作るか` の後戻りを HITL で止められる。
     8h. **Verification Sanity Check（検証手段の妥当性確認）**: 検証を実行する前に、その検証セットアップで目的の改善が実際に計測できるかを確認する。これはどの検証タイプにも適用する汎用チェックである:
   - false pass の防止: 壊れた実装が検証を通過してしまわない設計になっているか（検証が本当に壊れた状態を検出できるか）
   - 改善前後で観測値が動く構造か（不変量を計測していないか）
   - 検証環境 / ハーネス / ツールの制約（eval ハーネスの MCP 無効化等）を確認済みか
   - 検証結果がどう解釈されるかを設計前に明示する（OK条件 / NG条件）
   - 確認先: `requirements.md` の `Verification Sanity Check` / `Completion Testability Matrix` の `Planned RED / E2E`
9. **Problem Discovery（問題の掘り下げ）**: requirements.md を書き始める前に、まず問題を理解する。
   - **Early Resolution Check（早期解決確認）**: ユーザー入力に GitHub PR URL（`https://github.com/.*/pull/\d+`）または Issue URL が含まれる場合、Problem Discovery の他のステップより先に以下を確認する。bot による自動修正が走るワークフロー（drift 修正、Renovate 等）では、GDD 起動時点でタスクが既に完了している場合がある。
     1. `gh pr view <N> --repo <owner/repo> --json state,mergedAt,commits` で PR 状態を確認
     2. **PR が MERGED の場合**:
        - PR 本文・コメントから参照 Issue 番号を特定し `gh issue view <M> --repo <owner/repo> --json state` で確認
        - PR がマージ済み かつ Issue が CLOSED の場合:
          - 最新の PR コミット内容がユーザーの求める修正と同等かを確認（`gh pr view <N> --json commits` + `git show <sha> --stat`）
          - **同等の修正が含まれている**: `trivial` 相当として minimal state.md を作成し `Resume From: done` / `Next Action: done` で即 `<gdd-stop reason="done">` に進む。ユーザーに「PR は <commit> でマージ済み、Issue #M は CLOSED。タスクは完了しています」を報告する
          - **修正が不十分 / 別件**: 通常フロー継続
     3. **PR が OPEN かつ直近 10 分以内に別ユーザー / bot がコミットを追加している場合**:
        - `Human Check Questions` に「他のエージェントが同一修正を進行中の可能性があります」を追記して通常フロー継続
     4. それ以外: 通常フロー継続
     - **Why**: ドリフト修正や依存更新 PR のように bot が自動修正するワークフローでは、人間が GDD を起動した時点で bot がすでに同一修正をマージ済みであることがある。確認なしに進むと、同一変更の重複コミットがブランチに残り後始末が必要になる（本事例: 自動修正 bot が GDD 起動後 4 分でマージ済みだったが発見が遅れ、不要な push が発生した）
   - **Knowledge Transfer Check（過去セッション棚卸し）**: 関連する過去 steering の `findings.md` / `worklog.md` / `SKILL.md` に実験結果・技術的制約・失敗アプローチが記録されている場合は、Problem Discovery の冒頭で引き継ぎ漏れを確認する。記録を確認せずに同じ設計方針を繰り返し採用しない。確認先: `.steering/<slug>/findings.md` / `worklog.md` / 関連 skill の Attempts セクション。
   - **Runner Structure Check（ランナー内部構造確認）**: テストランナー / eval ハーネス / 起動スクリプトの内部構造（実行時設定・MCP 有効化/無効化フラグ・強制無効化の経路）を設計前に確認する。特に eval ハーネスが MCP を `--strict-mcp-config {}` 等で強制無効化する場合、その制約を `Engineering Baseline Survey` の `runner / eval harness structure` 行に記録し、設計方針に反映する。
   - **Current State Verification Check（現状確認）**: 要件を組み立てる前に、対象コードパスが既存 PR・既存実装で対応済みでないかを `git log` / `gh pr list` / `grep` で確認する（session 63bfd3d1: 既存 PR で対応済みの前提を確認せずに要件を組み立て、実装直前で `planning_rework_required` になった再発防止）。加えて、タスクが触れうる可能性のある全実行経路（MCP ラッパー / Bash / subagent / SDK 等）を列挙してから調査範囲を確定する（session 9154bd71: MCP ラッパー経路のみ調査し、Bash / subagent 経由の経路を最初から対象外にしていた再発防止）。
   - **過去の判断の参照**: `.steering/learned-patterns.md` があれば読む。類似の設計判断や却下済み代替案があれば、Options Exploration を短縮できる（`references/cross-task-learning.md` 参照）
   - **ユーザー提供の参考情報の確認**: ユーザーが URL、記事、ドキュメント、既存コードのパスなどを参考として渡した場合、requirements を書く前にその内容を読み、設計の前提・制約・実装パターンを把握する。参考情報を無視して独自に方針を決めない。取得した内容は `findings.md` に残す
   - **現状の把握**: 変更対象のコード・設定・画面を読み、今どうなっているかを具体的に理解する。ファイルを読むだけでなく、**変更が関係するシナリオが現在どう処理されるかを動作の視点で確認する**。呼び出し元・エントリポイントから変更対象まで辿り、既存の条件分岐・前処理・状態チェックを把握してから要件化する。**Why:** 変更対象ファイル単体を読んで要件を書くと、周辺のコードが既に行っている処理（重複排除・状態確認・ガード等）と衝突する設計が生まれ、実装後またはレビュー後にのみ発覚する手戻りが生じる。
   - **Existing Code Reading Evidence（既存コード読解証跡）**: 既存コード変更・既存 workflow 変更・既存 skill/plugin/hook 変更では、requirements.md の `Existing Code Reading Evidence` に次の列を埋める。`changed_code_refs`（変更対象・関連実装の file:line / symbol）、`caller_entrypoint_refs`（呼び出し元・entrypoint・adapter・hook）、`consumer_refs`（下流 consumer・side effect・外部出力 reader）、`existing_test_refs`（既存 test / fixture / eval / smoke）、`runtime_config_refs`（runtime / config / env / manifest / hook / route 定義など、実行時に効く設定）、`existing_capability_refs`（すでに使える既存機能 / DSL / config / helper / module / guard / workflow の file:line。無い場合は検索語・探索範囲・未発見理由）、`similar_implementation_refs`（同じ責務・似た実装・style source）、`pattern_or_invariant`（既存コードから分かった責務・正本・guard・命名・error/log pattern）、`source_to_sink_path`（entrypoint -> changed code -> consumer / output の入口から下流までの経路）、`counter_evidence_or_gap`（反証・未読領域・確認不能点）、`impact_on_approach`（gap や証跡が AC / 技術スタック / 実装方針 / HITL にどう影響するか）。target file only is shallow。変更対象ファイルだけ、または読んだファイル名だけでは evidence 不足として扱う。責務・正本・consumer・runtime / config・既存機能・類似実装が曖昧な場合は AI が仮決定して HITL へ進まず、gap と検索範囲を記録し、Step-by-Step Clarification / Human Check Questions に「何を決める質問か」「どの AC / Non-Goal / 作り方に反映するか」を明示して段階確認する。
   - **Existing Capability / Reuse Check（既存機能・再利用確認）**: 要件が既存 workflow / scheduled task / notification / guard / DSL / config / routing / command / hook の変更に見える場合、requirements.md 作成前にユーザー語彙とコード語彙の両方で検索する。例: ユーザー語彙が「成功時通知 / 失敗時通知」なら `success`, `failure`, `notification`, `channel`, `schedule`, `report_channel`, `report_mode`, `slack_schedules`, `github_schedules` のように既存 DSL・設定名候補も探す。既存機能が見つかった場合は新設案を既成事実にせず、`Implementation Approach Trace` に「既存機能を再利用する / 新設する」の判断を出す。既存機能を再利用しないなら理由を HITL の `既存コード読解` または `作り方の重要判断` に出す。見つからない場合も「未発見」とだけ書かず、検索語・探索範囲・未発見理由を残す。
   - **Why の言語化**: なぜこの変更が必要なのか、誰が困っているのか、何が起きているのかを 1-2 文で書き出す。ユーザーが「ページネーションを追加したい」と言った場合、「ユーザー一覧が全件取得で、1000 件超えるとレスポンスが 5 秒以上かかる」のように具体化する
   - **変更対象パスの存在確認**: `Glob` または `ls` で変更対象ディレクトリ・ファイルが実在するかを確認する。「存在するはず」の前提で requirements を書かない。存在しない場合の対処: 新規作成タスクなら「新規作成」と明示して続行する。存在するはずなのに見つからない場合は `Human Check Questions` に集約してターンを継続する（ユーザーへの質問でターンを終了しない）。
   - **影響範囲の事前スキャン**: 変更が影響しそうなファイル・モジュール・API を事前に特定する（`grep` / `glob` で調査）
   - **外部依存コンポーネントの実動作調査**: 要件に「X のログから情報を参照」「Y の出力を記録」「Z のフィールドを使う」「A と突合できる情報を取得」等が含まれる場合、そのコンポーネントのコードを実際に読んで動作を確認する。
     - **調査内容**:
       - 対象コンポーネントが実際に何を出力・ログするかをコードで確認する（ログ関数・レスポンス構造・イベントスキーマ等）
       - 非同期・バックグラウンド処理の有無を確認する（`async_mode` / callback / thread / queue 等）。非同期の場合、要件の「記録タイミング」で情報が揃わないことがある
       - 成功時・失敗時で出力が異なる場合、両方のケースを確認する
       - 要件で想定しているフィールドが実際に存在するか確認する
     - **調査強度（重め）**: 対象コンポーネントのファイル構造が不明・複数ファイルにまたがる場合は `Explore` subagent を spawn して包括的に調査する。調査結果は `findings.md` に記録する
     - **判定と対処**:
       - 想定フィールドが存在する → 要件に「確認済み（ファイル名:行番号）」として明記する
       - 想定フィールドが存在しない、または非同期で取得不可 → 要件の前提を修正する。外部コンポーネントの変更が必要な場合はスコープ判断として `Human Check Questions` に追加する。「取得不可なら代替手段（session_id 経由の突合等）に切り替える」選択肢も提示する
     - **Why:** 「記録できるはず」の前提で要件を書くと、実装フェーズで「実は取得できない」が判明し rework になる。今回の事例: `async_mode=True` で worker Lambda は ACK のみ受け取り、Claude の出力内容は取得不可だったが、調査なしに `output_preview` を要件に含めて rework が発生した。コードを読む 5〜10 分が、設計・実装・human check の手戻り数時間を防ぐ
   - **Scope Reduction Check（要件縮小の 1 回検討）**: Problem Discovery の終盤で「要件全体が本当に必要か、部分だけで済まないか」を 1 回だけ AI が内部検討する。ユーザーに質問で止まらない。
     - 「今すぐ必要な部分」と「後回しにできる部分」に内部で分ける
     - 代替手段（既存の機能・ユニットテスト・手動運用）で十分な部分があれば、以下のいずれかに **縮小案** を記録する:
       - Options Exploration を実施する場合（standard かつ非 Direct Intent）: Approach C として「フル構築せず CICD だけ構築」などを候補に並べる
       - Options Exploration を skip する場合（quick / Express / Direct Intent）: `requirements.md` の `Human Check Questions` に「scope 縮小」カテゴリの承認ポイントを 1 件追加し、`採用案: 縮小版` / `代替案: フル版` を対比させる
     - 単独で縮小判断を確定しない。縮小は必ず human check の承認ポイント経由でユーザーに判断させる
     - 採用された場合は `やらないこと` に明示、却下された場合は通常の scope に戻す
     - 縮小候補が無い場合はこの Check を skip し、artifact に痕跡を残さない（過剰な承認ポイントを増やさない）
     - **Why:** スコープは「拡大しない」だけでなく「縮小できないか」も検討対象。AI が先回りして縮小案を提示することで、過剰なスコープのまま設計に入って後で「これ要らなかった」に気付く手戻りを防ぐ。自律継続の原則に従い、縮小の確定判断は必ず human check に委ねる。Options Exploration を skip する経路でも縮小提案が失われないよう、承認ポイント直接追加という代替経路を用意する
   - **Why:** requirements.md の「目的」と「影響範囲」の品質を上げるために、書き始める前に問題を具体的に理解する。曖昧な理解のまま要件を書くと、human check で「そもそもなぜ？」に戻る手戻りが起きる。過去の判断を先に参照することで、同じ議論の繰り返しを防ぐ
     9a. **Broad Requirement Check（広い要件の選択肢化）**: Problem Discovery 後、要件が広いままかを判定する。
   - **広い要件の判定条件**（いずれかに該当）:
     - 目的は分かるが、実装 scope が 2 案以上に自然に分かれる
     - 成功条件が「良い」「改善」「楽」「整理」など定性的で、測定可能な AC に直せていない
     - 対象ユーザー / 対象イベント / 対象データ / 対象環境のどれかが未確定で、実装範囲が変わる
     - やることより「やらないこと」の方が重要で、非スコープを人間が選ぶ必要がある
   - **該当時の必須処理**:
     1. `requirements.md` に `Broad Requirement: true` を記録する
     2. **Pre-option Scope Narrowing** を先に実行し、明らかに後回しにできる scope を落とす
     3. 絞り込んだ後も複数の合理的 scope が残る場合だけ、Step 10 の Options Exploration を **quick / Direct Intent でも必須**にする（trivial は除く）
     4. 2-3 案を作る。最低 1 つは縮小案または「やらない / 後回し」案にする
     5. AI 推奨案を 1 つ選ぶが、採用 scope は human check の承認ポイントで人間に選ばせる
     6. 選択されなかった案は `やらないこと` または `後回し` に明示する
   - **Pre-option Scope Narrowing（選択肢化の前に scope を削る）**:
     - 目的: 「広いから A/B/C を全部考える」のではなく、まず YAGNI で実装不要・後回しにできる範囲を落とす
     - 制限時間: 5 分相当の軽い判断に留める。深い調査・詳細設計・実装方式比較はしない
     - 削ってよいもの:
       - ユーザーが今回明示していない利用者 / イベント / 出力先 / 環境
       - 既存 AC の達成に不要な便利機能・将来拡張・nice-to-have
       - 検証や rollout を不必要に広げる追加対象
       - 「後で同じ仕組みを横展開できる」が今回の価値に直結しないもの
     - 削ってはいけないもの:
       - ユーザーが明示した必須対象
       - security / privacy / ownership / rollback など、削ると事故る boundary
       - 既存挙動の互換性や regression 防止に必要な範囲
     - 記録フォーマット:

       ```markdown
       Scope Narrowing:

       - keep: <今回の最小 scope>
       - defer: <後回しにする scope>
       - reason: <なぜ keep だけで今回の価値を満たすか>
       - reopen trigger: <どの条件なら defer を別 task 化するか>
       ```

     - **keep の決め方**:
       - ユーザーが明示した対象があれば、それを keep にする
       - 明示対象が複数ある場合は、依存関係が少なく単独で検証できる最小対象を keep にする
       - 明示対象が複数あり、どれが最小対象かを既存コード・設定から機械的に決められない場合、AI が好みで片方を選ばない。keep は `<要人間選択: 明示対象 A / 明示対象 B / ...>` とし、対象選択だけを human check に出す
       - 明示対象が無い場合、AI が「代表」「利用頻度が高そう」などを推測して 1 つに決めない。keep は `<要人間選択: 対象候補 A/B/C>` とし、human check の承認ポイントで選ばせる
       - 既存コードから機械的に 1 つに絞れる根拠（設定で default と明記、単一 entrypoint しかない等）がある場合だけ、AI が keep を仮決定してよい
     - Narrowing 後に最小 scope が 1 つに絞れた場合、Options Exploration は省略してよい。ただし human check には `Scope Narrowing` を承認ポイントとして出し、「defer でよいか」を人間が覆せる形にする
     - 明示対象が無く keep が `<要人間選択: ...>` の場合、Options Exploration ではなく **対象選択の承認ポイント** として扱う。詳細実装案や A/B/C の設計比較に進まない

   - **探索上限**:
     - 広い要件では、ここで実装方式・ライブラリ・ファイル単位の変更計画を深掘りしない
     - 調査は「既存コードの現状把握」「scope 選択に必要な制約確認」「実現不能案の除外」に限定する
     - 技術調査 / 類似事例調査 / 実装方式比較は、ユーザーが scope を選んだ後の design-gating に送る
     - 各案は `何をやるか / やらないこと / 利点 / リスク / 後で決める実装論点` までに留める
   - **禁止**: 「AI 推奨案を採用」とだけ書いて human check に出し、他の合理的 scope を隠したまま先に進むこと
   - **禁止**: 広い要件の段階で、AI が時間を使って詳細実装案を作り込み、その作り込んだ案を理由に scope を既成事実化すること
   - **Why:** 広い要件は技術的不明点ではなく責任分界の不明点であることが多い。AI が勝手に scope を狭めると、実装後に「そこまで求めていなかった / そこも含めたかった」が発生する。選択肢を human check に出すことで、人間は方向性を選ぶだけで済み、実装前に scope を締められる

10. **Options Exploration（選択肢の提示）**: standard タスクでは、要件を書く前に 2-3 の選択肢を比較する。quick タスクでは省略してよい。
    - **F-3 段階的対話（Broad Requirement 限定）**: `Broad Requirement: true` で未確定の前提が多い場合、Options Exploration は一括提示せず、以下の2点を守る。(a) 1問ずつ深掘りする: 質問を1問ずつ提示し、回答を得てから次の質問に進む。複数の論点を1ターンにまとめて質問しない。(b) 骨子を塊ごとに提示する: requirements 骨子がまとまった単位ごとに提示し、合意を取ってから次を書く。骨子全体を一度に出さない。Direct Intent（`Broad Requirement: false`）の場合は本節をそのまま skip し、既存の一括 Options Exploration を使う。
    - **「やらない」案または「縮小」案を含める**: 変更しない場合のリスク・コストを明示する。Scope Reduction Check（Step 9）で縮小候補が出ている場合は、その縮小案を Approach C として並べる。これが小さいなら本当に必要かを再考する
    - **軽い案と重い案を対比**: 最小限の変更（例: 設定値だけ変える）と本格的な変更（例: アーキテクチャを変える）を並べる
    - **アプローチ比較の必須フォーマット**: standard タスクで Options Exploration を行う場合、以下の構造で `Design Policy Discussion` に記録する。これは省略可能な提案ではなく、standard タスクでは **必須フォーマット**:

      ```markdown
      ### Approach A: <短い名前>

      <1-2 行の説明>

      - メリット: <箇条書き>
      - デメリット: <箇条書き>

      ### Approach B: <短い名前>

      <1-2 行の説明>

      - メリット: <箇条書き>
      - デメリット: <箇条書き>

      ### Approach C: <短い名前、または「やらない」案 / 「縮小」案>

      <1-2 行の説明>

      - メリット: <箇条書き>
      - デメリット: <箇条書き>

      ### 推奨: Approach X

      **理由**: <なぜこれを推奨するか、1-2 文>
      ```

      - 候補が 2 つしか無い場合は A / B + 「やらない」案の C で 3 案に揃える
      - 推奨案は必ず 1 つに絞る。「場合による」「どちらでも良い」は AI の判断放棄とみなす
      - 推奨理由はメリット/デメリットの要約ではなく、**この文脈で最も効く理由** を 1-2 文で書く

    - **実装方式の候補出し**: 方向性が決まったら、「どの技術方式で実装するか」を具体的に洗い出す。`Broad Requirement: true` の場合は方向性がまだ人間未承認なので、この小節を実行しない。人間が採用 scope を選んだ後、design-gating で実装方式を比較する。1 つしか方式がない場合は省略してよいが、複数の合理的な方式がある場合は以下の手順で比較表を `Design Policy Discussion` に記録する:
      1. **候補の列挙**: 各方式の名前・概要を 1 行で
      2. **実装例の調査**: 各候補について実装例・コードスニペット・既知のハマりポイントを調べる。実際に動いている事例の有無は方式の実現可能性の判断材料になる。調査手段は環境で利用可能なものを使う（例: `similar-case-researcher`、`tech-docs-searcher`、WebSearch、公式ドキュメント、リポジトリ内の既存実装）。調査結果は `findings.md` に残す（Step 15 の Findings 永続化ルールに従う）
      3. **比較表の作成**: 比較観点（複雑さ / 信頼性 / 運用コスト / 制約）ごとに優劣を整理。実装例の調査で判明した具体的な制約やハマりポイントも反映する
      4. **推奨の提示**: AI が推奨方式を選び、理由を添える
      - 例: 「CI 待機方式: (A) polling + sleep → シンプルだが agent 生存が必要 / (B) webhook → 即応だが受信エンドポイントが必要 / (C) 外部 wait サービス → agent 不要だが依存増」
    - **判断材料を先に出す**: 比較結果を `Design Policy Discussion` に記録し、AI が推奨案を選んで理由を添える。人間は human check で「OK / 別案希望」を判断する
    - **広い要件の場合**: `Broad Requirement: true` なら quick でも省略不可。human check の承認ポイントに「採用 scope」を必ず入れ、選択肢 A/B/C のうちどれで進むかを人間が明示できる形にする。この時点の比較は scope 比較であり、詳細な実装方式比較ではない
    - **Why:** 最初に選択肢を見せることで、人間が方向性を早く決められる。AI が 1 案だけ提示すると、人間は「他に方法はないのか」と不安になる。さらに、方向性だけ決めて実装方式を design-gating に先送りすると、design フェーズで方式が定まらず実装がぶれる。human check の時点で「何を」だけでなく「どうやって」も承認を取ることで、後工程の手戻りを防ぐ。推奨案を 1 つに絞ることで、人間は「AI の提案を受け入れるか / 別案を指示するか」の 2 択に単純化でき、判断時間が短くなる（superpowers 観察パターン）

    - **Visual Companion（UI/UX 変更を含む場合の視覚化サブステップ）**: 以下のキーワード / 兆候が含まれる場合は、Options Exploration の各 Approach に **視覚的叩き台** を 1 つ添える。textual な比較表だけで human check に進まない。

      - **発火条件**（いずれか）:
        - UI / 画面 / 画面遷移 / レイアウト / コンポーネント / ボタン / モーダル / ダイアログ / 表示順 の言及
        - Slack message / wiki の記事 / GitHub Issue body / メール / 通知 / レポート の出力フォーマット変更
        - JSON / Markdown / YAML 等の機械可読フォーマットで「人間が読む箇所」の構造変更
        - 「見やすく」「並べ替え」「強調」「フォーマット」「整形」等のキーワード
      - **採用する視覚化形式**（task の性質に応じて 1 つ以上を選ぶ）:
        1. **ASCII mockup**: 画面・通知の構造を ASCII 罫線で表現（フレームと配置だけが分かれば十分）
        2. **Markdown table**: フィールド一覧と表示順を表で示す
        3. **Before/After block**: 出力サンプルを `before` / `after` で並べる（最も推奨。差分が一目で分かる）
        4. **Browser preview suggestion**: HTML / React 等の本格 UI 変更時は、`mockup.html` を `/tmp/` に作って `open` する手順だけ提示し、ユーザーに承認後の確認をオプション提案する（自動で起動しない）
      - **配置**: 各 Approach の説明直下に `<details>` ブロックまたは inline code fence で添付。比較表が長くなる場合は `mockup.md` を `.steering/<task>/` に作って参照する
      - **human check への昇格**: mockup の採用案を human check の「承認ポイント」に明示追加する。例:

        ```markdown
        ### 承認ポイント
        - Approach A の Before/After サンプル（上記）の **after** で進めて良いか
        ```

      - **skip 条件**: 内部 API / 内部ロジック / リファクタ / 設定値変更だけで、ユーザー / レビュアーが目視する出力が変わらない場合は不要
      - **Why:** UI/UX 変更や出力フォーマット変更は textual 説明だけでは解釈差が残る。「思っていたのと違う」を human check で発見すると implementation 後の手戻りになる。ASCII / before-after は 1-2 分で作れる軽量視覚化で、解釈差を planning 段階で潰せる。superpowers `brainstorming` の Visual Companion パターンを GDD 向けに具体化したもの

11. `requirements.md` のセクション定義は `references/requirements-template.md` に従う（`quick` パスでは Summary Brief + 目的 + スコープ + AC + 実装方針の最小構成でよい）。
   - **罠7（実測義務）**: requirements.md の AC・Critical Trace に登場する対象ファイル数・行番号・シンボル・分岐は、requirements-gating に提出する前に実コードを実測して確定する。仮の値・推測値（未確認パスや概算のみの記述）を AC・Critical Trace に含めない。実測できない場合は「未測」+ その理由を明示する。
   11a. **Completion / Approach Trace（HITL ズレ防止）**: requirements 初稿を書くとき、ユーザー入力から承認対象への変換履歴を必ず残す。
   - `User-Stated Completion Conditions`: ユーザーが最初に言った完了条件、既存実装状態、仮置き、手動設定済み状態を原文に近く保存する
   - `Completion Condition Trace`: 各初期完了条件を `kept` / `refined` / `split` / `deferred` / `dropped` / `added` / `unresolved` に分類し、`AC / Non-Goal / Deferred / Honest Limitations / Open Question` のどれかへ写像する
     - `Status` は変換種別、`Maps to` は置き場所として分ける。別承認・別タスク・後工程に送るものは `deferred -> Deferred`、安全性や目的不一致で今回採用しないものは `dropped -> Non-Goal` を基本にする
     - 方針は仮決定できるが現物値・外部事実・権限が未確認の場合は、方針と未確認事実を分けて記録する。混ぜる場合は Reason に「方針は仮決定、現物未確認」と書く
     - 既存実装済み・途中実装・手動設定済みなどの初期状態は、守るべき条件なら `AC`、今回触らない境界なら `Non-Goal`、確認できない制約なら `Honest Limitations` へ写像する
   - `Completion Testability Matrix`: accepted AC ごとに `Testable claim` / `Test level` / `Planned RED / E2E` / `Evidence required` / `Status` を書く。ユーザー入力時点では完了条件が曖昧でもよいが、HITL 前には Yes/No で観測できる claim へ寄せる
     - claim にできない条件は `needs-clarification` とし、Open Question または HITL の `テスト化確認` に出す。AI がテストを書いて解釈を固定しない
     - 現スコープでテスト不能な条件は `non-testable-deferred` とし、accepted AC ではなく Deferred / Non-Goal / Honest Limitations に写像する
     - E2E が必要な条件は `e2e-required` とし、E2E に残す境界と先に unit / contract / integration RED で固定する境界を分けて `Planned RED / E2E` に書く
     - 外部証跡が必要な条件は `external-evidence-required` とし、必要な plan / describe / CI / screenshot / log 等を `Evidence required` に書く
   - `Technology Stack Fit Matrix`: 外部サービス / SDK / CLI / MCP / API / framework / runtime / IaC / DB 等の採用判断について、候補、既存 repo 標準、公式統合、運用制約、multi-tenant / credential boundary、testability、fit を書く。公式統合があるのに別方式を採る場合は必ず理由を残す
   - `Adopted Technology Stack Trace`: 採用する技術スタック、採用理由、却下案、HITL に出す risk、後続で `human_recheck_required` になる trigger を書く
   - `Implementation Approach Trace`: repo 分割、既存仕組み再利用 vs 新設、import vs recreate、public vs private、CI/CD 方針など、作り方がズレると後戻りが大きい論点だけを記録する。ファイル単位の計画は書き込みすぎず design-gating に送る
   - `Summary Brief` の `ズレ確認` には、上記 trace のうち `kept` 以外で意味・scope・安全境界・作り方が変わる完了条件変換、テスト化できない完了条件 / E2E必須 / 外部証跡必須 / 解釈差が大きい条件、技術スタック / access method / credential backend / tenant 境界の高リスク判断、後戻りが高い作り方の重要判断だけを短く載せる。ログ粒度や全 unit test 一覧、全 dependency 一覧など、requirements.md に残れば十分な細部は原則出さない。HITL は全文レビューの場ではないため、全 AC や全 trace を貼らない
   - ユーザーが「手順 1-5 を実装済み」「callback は仮」「コンソールで設定済み」等の完了状態を示した場合、それは完了条件そのものと同じ重要度で trace に残す
12. lightweight `design.md` skeleton のセクション定義も `references/requirements-template.md` に従う（`quick` パスでは Summary Brief + 変更点 + テスト方針の最小構成でよい）。
   - **design.md skeleton は HOW（実装方針）と WHERE（変更予定ファイルの実パス・行番号）を、後続の human check Decision Packet にそのまま出せる粒度まで this step で書く。詳細を design-gating に先送りする形で WHERE を空欄・仮パスのまま残さない。**

- planning 中に重要な意思決定や却下した代替案が固まった場合は、任意で active worktree 側 `.steering/.../adr.md` を作成または更新し、`Context` / `Decision` / `Why` / `Consequences` を追記してよい
  12a. **Complexity Evaluation（複雑さ評価）**: requirements.md の初稿が書けたら、`references/task-sizing.md` § 正式判定: Complexity Evaluation に従って 5 次元（Scope Breadth / AC Complexity / Integration Depth / Safety Surface / Uncertainty）を評価する。
- 各次元を低/中/高の 3 段階で判定し、判定ルールに従って推奨 sizing を算出する
- Step 7 の暫定 sizing と比較する:
  - **一致**: そのまま進む
  - **推奨が重い方向**: 昇格を提案し理由を表示。ユーザーが承認すれば昇格して artifact 構成を追加する
  - **推奨が軽い方向**: 降格は提案しない（既に重い方の構成で作業しているため）
- 評価結果を `requirements.md` の `Task Size` 行の直後にコメントとして記録する:

  ```markdown
  Task Size: quick (standard)

  <!-- Complexity: Scope低 / AC中 / Integration低 / Safety低 / Uncertainty低 -->
  ```

- Express Path（Step 7a）を既に通過している場合はこの Step をスキップする（express の Complexity Evaluation は Step 7a-4 で完了済み）
- ユーザーが明示指定した sizing は Complexity Evaluation より優先する

### 要件変更時の再評価 trigger

human-check の往復で要件が追加・拡張されたとき、初期 sizing をそのまま維持しない。修正反映後に以下のいずれかが該当した場合、再提示の前に Complexity Evaluation を再実行する：

- **(a) AC 数が +2 以上 または +50% 以上 増加した**（同一の事象を複数フォーマット・方法で検出する variant は sub-condition として 1 AC にまとめる；別の事象を対象にする条件は独立 AC）
- **(b) 独立した検出パターン・条件カテゴリ・分岐ルールが +1 以上 増加した**（同一カテゴリ内の値追加は除く）
- **(c) 新規の外部依存・他コンポーネント影響・Python/IaC 変更が判明した**
- **(d) AI が「却下した代替案」を 2 件以上書く必要が生じた**（≒ 設計判断が選択肢相当）

特に重要なのは `quick (express) → quick (standard)` の昇格判断。Express は Options Exploration と Iterative Refinement Loop を skip するため、要件が複雑化したまま Express で進めるとエッジケース探索が抜け落ち、レビュー段階での手戻りが発生する。

**Why:** 初期 sizing は「最初の要件の輪郭」に対して下した暫定判断。要件が変われば sizing も動かないと、本来 Options Exploration で炙り出されるべきエッジケース（false-positive 検出範囲、bot 制約の対称性、互換シナリオ等）が requirements を抜け出す。今回の事例（20260508-alert-noop-improvements）: 3パターンで `quick (express)` 判定 → human-check 中に STG 環境要件追加で 4パターン+5AC に膨張 → sizing 維持のまま進めて Options Exploration skip → STG 検出範囲が広すぎる問題（review H-1）と bot 制約欠落（review M-2）がレビューで発覚。

13. `state.md` の `Gate Status` は初期値として次を入れる。

- `Requirements Review Status=pending`
- `Design Review Status=pending`
- `Human Check Status=pending`
- `Resume From=gdd-brainstorming`

14. planning の差し戻しで requirements を更新した場合は、requirements reviewer と human check に戻す前に lightweight `design.md` skeleton の trace / 主要フロー / 影響範囲 / `Latest Tech Context` と、`Summary Brief` / `Behavior Change Summary` / `Route / Ownership Matrix` / `Sensitive Data / Masking Policy` / `Design Policy Discussion` / `Human Check Questions` を追従更新し、`Summary Brief` の `外部依存の確認結果` も最新情報に合わせて取り直す。対象技術や version 前提が変わった場合は最新情報を取り直す。
15. planning 中に調査した案、試して捨てた選択肢、外部情報の検索過程など、artifact に残すほどではないが session 跨ぎで失われると困る知見は `.steering/.../worklog.md` に追記してよい。`adr.md` は「決まったこと」、`worklog.md` は「過程」として棲み分ける。`worklog.md` は canonical state / routing source / gate 条件にはしない。
    - 技術調査の結果、比較検証の結果、pre-workflow-brainstorming の brainstorm で得た発見は `.steering/.../findings.md` に構造化して残してよい。`findings.md` は `Sources` / `Synthesized Findings` / `Comparisons` のセクションで整理する。gate 条件・routing source にはしない。
    - **Findings 永続化ルール**: 調査操作（web 検索、ドキュメント読み込み、コード探索）を **2 回** 行ったら、得られた知見を `findings.md` に書き出す。コンテキストウィンドウは揮発性の RAM であり、ファイルシステムは永続的なディスクである。長い調査で発見が失われるのを構造的に防ぐ。永続化のタイミングを逃しても gate 違反にはならないが、Iterative Refinement Loop（Step 16）で未永続化の調査結果に依存した判断があれば Self-Review で検出される。
    - `findings.md` のテンプレート:

      ```markdown
      # Findings

      ## Sources

      - [ソース名](URL or パス)

      ## Synthesized Findings

      ### カテゴリ名

      - 発見 1
      - 発見 2

      ## Comparisons (任意)

      | 観点 | 選択肢 A | 選択肢 B |
      | ---- | -------- | -------- |
      | ...  | ...      | ...      |
      ```

16. **Iterative Refinement Loop（自律解決）**: artifact の初稿が書けたら、Self-Review（Step 17）に進む前に以下のループで未解決事項を **AI が自律的に解決** する。ユーザーに質問して止まらない。ループは最大 3 回まで（3 回で収束しない場合は残りを `Open Questions` に明示して Self-Review に進む）。

    **16a. Gap Scan** — 次の観点で未解決事項を洗い出す:
    1. `未確定事項` に項目が残っている
    2. `Open Questions` に項目が残っている
    3. `受入条件` に曖昧な表現がある（「適切に」「必要に応じて」等、判定基準が不明なもの）
    4. `Design Policy Discussion` の採用案に根拠が弱いもの、または非採用案との比較が不足しているもの
    5. `Human Check Questions` が未作成、または 3 件未満。ただし `Broad Requirement: true` で `Scope Narrowing` の妥当性だけを確認する場合は、承認ポイントを 1-2 件に絞ってよい（数合わせで広い scope を増やさない）
    6. `Behavior Change Summary` / `Route / Ownership Matrix` / `Sensitive Data / Masking Policy` が空または N/A 根拠なし

    **16b. Self-Resolve** — Gap Scan で見つかった未解決事項を、ユーザーに質問せず AI が自律的に解決する:
    - 利用可能なコンテキスト（既存コード、設定ファイル、ドキュメント）から判断材料を集める
    - `tech-docs-searcher` 等のツールで不足情報を補う
    - 十分な根拠があれば AI が判断を確定し、判断根拠を artifact に記録する
    - AI だけでは判断できない policy-level の事項（ビジネス判断、承認権限、組織方針）は `Human Check Questions` の承認ポイントに残す
    - 技術的に複数の合理的選択肢がある場合は、最もシンプルな案を採用し `Design Policy Discussion` に判断根拠と非採用案を記録する
    - **ユーザーに質問して assistant turn を終了してはならない**。質問が必要な事項は承認ポイントとして HITL に集約する

    **16c. Update** — Self-Resolve の結果を `requirements.md` と `design.md` に反映する:
    - 確定した事項は `未確定事項` から `確定事項` に移し、判断根拠を添える
    - 解決した質問は `Open Questions` から削除し、本文の該当セクションに反映する
    - 設計判断が固まったら `Design Policy Discussion` の採用案/非採用案を更新する
    - AI 判断で新たに判明した未確定事項があれば `未確定事項` / `Open Questions` に追加する

    **16d. Re-scan** — 16a に戻る。Gap Scan で未解決事項が 0 件（`Human Check Questions` に残した承認ポイントは除く）になったら Step 17 に進む。

17. `requirements.md` と lightweight `design.md` が固まったら、以下の 3 点だけを素早くチェックする（Iterative Refinement Loop で内容の整合性・曖昧さは既に解消済みのため、ここでは再確認しない）:
    1. **Placeholder scan**（正本: `common-guardrails.md` § プレースホルダー禁止）: 禁止表現や未完成セクションがないか
    2. **Human Check Questions の品質**: 各承認ポイントが番号付きで、人間が artifact を開かずに判断できる粒度になっているか
    3. **Open Questions の残存レベル**: スコープ・方針レベルの未解決事項が残っている場合は Self-Review fail。実装詳細レベルは残してよい
       問題を見つけたらその場で修正する。再レビューは不要。
18. Self-Review を通過したら `Resume From=gdd-requirements-gating` に更新する。タスクサイズ判定結果は human-check テンプレート（`references/human-check-template.md`）の「タスクサイズ」「フロー」行で明示する。

    **フロー表示の値**:
    - `quick (express)`: 要件整理 → 人間確認 → TDD → 実装 → 品質レビュー → 完了（AI reviewer・設計・タスク分割・完了チェックはスキップ）
    - `quick (standard)`: 要件整理 → 要件レビュー → 人間確認 → 設計 → 実装 → 品質レビュー → 完了（専門レビューアはスキップ）
    - `standard`: 要件整理 → 要件レビュー → 人間確認 → 設計 → 設計レビュー → タスク分割 → TDD → 実装レビュー（専門レビューア含む） → 完了チェック

19. 選択肢が多く、かつユーザーが明示的に比較過程の保存を求めたときだけ `.cursor/plans/*.plan.md` を使う。
20. `gdd-requirements-gating` 通過後は `Resume From=human-check-waiting` で human check へ進む。出力テンプレートと停止ルールは SKILL.md § Output Guidance を参照。
