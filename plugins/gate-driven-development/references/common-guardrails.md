# Common Guardrails

> **所有**: 複数 skill で共有される guardrails と、その背景理由
> **上位正本**: `self-contained-contract.md`
> **参照元**: 全 phase skill

各 skill の Guardrails セクションで繰り返されるルールを集約する。個々の skill は `## Guardrails` 冒頭で `references/common-guardrails.md` を参照し、skill 固有のルールだけを自身に書く。

> **スキル選択の判定基準**: どのスキルをいつ呼ぶかは `gdd-using-skills` skill を参照（1% ルール・ユーザー依頼マッピング・rationalization 禁止パターン）。

---

## GDD Truth Source Priority

長い作業、compaction 後、次 stage への継続、または別チャット復旧では、情報源の優先順位を固定する。

| 情報源 | 扱い |
|---|---|
| 会話履歴 → 参考情報 | 壁打ちの文脈や補足として読む。会話履歴だけで次計画を確定しない |
| GDD artifact → 正本 | `requirements.md` / `design.md` / `state.md` / `tasklist.md` を workflow の正本として扱う |
| Git / PR / CI / test → 事実 | merge 済み、CI 結果、test pass/fail、diff は観測事実として扱う |
| Continuation ID → 復旧用の受け渡しキー | 次チャットへ渡す識別子。長文プロンプトの代替であり、正本そのものではない |

通常は同じチャットで「次に進んで」と言えば、GDD artifact と Git / PR / CI / test を re-read して次 stage に進む。別チャットへ移る場合だけ Continuation ID を使う。compaction で会話履歴が短くなっても、artifact と事実を読み直してから判断する。

### Codex Goal Continuation と reboot task の衝突

Codex の `<codex_internal_context source="goal">` は、ユーザーが明示した継続目的を host が再投入したものとして扱う。ただし、それ自体を正本にはしない。goal は **候補検索キー** であり、最終判断は GDD artifact と Git / PR / CI / test の事実で行う。

SessionStart の `[gdd:reboot] Task` と Codex goal continuation の目的が食い違う場合:

1. `[gdd:reboot] Task` を自動採用しない
2. goal の語彙、PR 番号、branch、worktree、state Task ID、Task Binding Registry を使って候補を解決する
3. 一致候補が 1 件だけなら、その `state.md / tasklist.md / worklog.md` を read-back してから進む
4. 複数候補または不一致なら、計画・実装・superpowers workflow を開始せず、候補と次の 1 アクションだけを出す

repo-local Project Skill（例: `example-prod-eval`）は検証手段または実行手段であり、GDD の workflow owner ではない。Project Skill の結果は、必ず GDD artifact / GDD route / worklog に戻す。

禁止表現:

- `superpowers の指示に従い`
- `gdd-dev 相当`

これらは workflow owner を曖昧にするため、active GDD / GDD continuation では使わない。

---

## 合理化防止テーブル（Rationalization Prevention）

GDD のルールを省略・簡略化したくなったとき、以下の思考パターンに気づいたら立ち止まる。

| 合理化 | 現実 |
|--------|------|
| 「このタスクは簡単だから /gdd-dev は不要」 | trivial / express で自動調整される。手動判断より sizing のほうが正確 |
| 「レビューは不要、コードは正しい」 | 自信 ≠ 証拠。reviewer が見つけるバグは実装者が見落としたもの |
| 「human check をスキップしたい、方向性は明白」 | 「明白」に見える要件ほど暗黙の前提が多い。承認は 3 分で済む |
| 「state.md の更新は後でいい」 | 後で = セッション切れで消える。phase 遷移時に即更新しないと中断復帰が壊れる |
| 「Verification は形式的、テスト通ってるから」 | テスト通過 ≠ AC 充足。Verification は AC との対応を証明する記録 |
| 「.steering/ の artifact は面倒」 | artifact が計画の先送りを防ぐ。TBD を書けない = 考えが足りていない |
| 「差し戻しは時間の無駄」 | 差し戻しが見つけた問題は本番で見つかる問題。早期発見 = 低コスト修正 |
| 「この修正は小さいから AC 変更不要」 | AC を変えずに実装を変える = テストが追従しない。scope は明示的に管理 |
| 「Plan mode のほうが考えやすい」 | GDD の task sizing で対応する。二重管理は state の不整合を招く |
| 「context が長いから Handoff Summary は省略」 | context が長いからこそ Handoff が必要。圧縮で失われる情報を守る唯一の手段 |
| 「1 回だけ例外」 | 例外は前例になる。ルールの価値は一貫して守ることで生まれる |
| 「急いでいるからプロセスを飛ばす」 | プロセスを飛ばした手戻りのほうが遅い。systematic は guess-and-check より速い |

### Gate Rationalization Red Flags

以下が頭に浮かんだら、その phase の gate を通す前に一度止まる。これは superpowers の rationalization 対抗を GDD の gate に寄せた最小セットである。

| Red Flag | 取るべき行動 |
|---|---|
| express 判定を甘くする | `task-sizing.md` の正式判定に戻す。safety / integration / uncertainty が高なら standard |
| AC を pass にしたい | fresh verification evidence を再確認する。推測・CI summary だけで pass にしない |
| review 指摘を流したい | `gdd-receiving-code-review` の READ -> UNDERSTAND -> VERIFY を通す |
| human check を短くしたい | 情報を削るのではなく、詳細を artifact に逃がし判断点だけを残す |
| 旧 worktree で続けたい | post-merge follow-up は new worktree。旧 worktree は cleanup 候補 |

---

## 自律継続（Autonomous Continuation）

**`/gdd-dev` の explicit run では `human-check-waiting` に到達するまで assistant turn を終了しない。** Stop hook が非 terminal な stop を block するため、hook レベルで継続が強制される。

- Iterative Refinement Loop 中にユーザーに質問して turn を終えない。未解決事項は AI が自律判断するか `Human Check Questions` に集約
- gating skill は reviewer 起動 → 結果処理 → status 更新 → Handoff 出力 → `<gdd-stop>` を一連で完了
- reviewer 差し戻し（`changes_requested`）は自律修正して再 gate
- **例外**: 下記「Operational Safety」該当操作は自律継続の対象外

**Why:** 途中停止はコンテキスト切れと手戻りを招く。未確定事項は `Human Check Questions` に集約して HITL で一括確認する設計。

## Operational Safety（インフラ操作の安全）

**自律継続・auto mode に関係なく、以下の操作は 1 操作ごとにユーザーの明示的な確認を取る。** 包括的指示を受けても各操作を個別に plan 提示して確認する。

### 確認必須の操作

| カテゴリ | 具体例 |
|---------|------|
| **Terraform write** | `terraform apply` / `destroy` / `import` / `state rm` |
| **AWS CLI write** | `create-*` / `delete-*` / `update-*` / `put-*` / `modify-*` / `terminate-*` / `deregister-*` / `revoke-*` / `stop-*` / `start-*` |
| **破壊的ファイル操作** | `rm -rf` / `rm -r`（ワーキングツリー外や `.steering/` 全体） |
| **Docker push** | `docker push`、ECR への push |
| **DB 破壊操作** | `DROP` / `DELETE` / `TRUNCATE` / `ALTER`（本番/共有 DB） |

### 禁止事項

- **`-auto-approve` 禁止**: `terraform apply -auto-approve` は使わない。`!` コマンドか対話的確認を通す
- **包括的承認の連鎖禁止**: 「デプロイして」「apply して」は **その時点の 1 操作** への承認。次の操作には再度 plan を提示
- **deny 後の再試行禁止**: classifier / hook に deny された操作をパラメータ変更で再試行しない
- **MCP 参照エラーの再試行を繰り返さない**: tool not found / server unavailable は **1 回だけ再試行**し、解決しなければ停止して人間に報告する。**Honest Limitations**: これは機械強制ではない。担保できるのは文言が配布物に存在することまで（`non-testable-deferred` / 固定は `tests/checks/mcp-retry-token.sh`）

### 確認手順

1. `terraform plan` / `aws * describe-*` 等 read-only で変更内容を確認
2. 対象・影響範囲・ロールバック手順を明示
3. `!` コマンドでの直接実行を案内、または明示的承認を得る（`-auto-approve` 不可）
4. 1 操作完了後、次が必要なら手順 1 に戻る

### AWS CLI の read-only 操作（確認不要）

`describe-*` / `get-*` / `list-*` / `lookup-*` / `sts get-caller-identity` / `logs filter-log-events` / `logs get-log-events` / `cloudtrail lookup-events`

**Why:** 自律継続はコード作業の効率化であり、共有インフラ変更の権限委譲ではない。`terraform apply -auto-approve` の auto mode 連鎖で意図しない変更が発生した事例がある。

## Context Compaction Resilience（コンテキスト圧縮耐性）

**長時間 phase（task-breakdown、TDD RED、systematic-debugging 等）では、判断ポイントでディスクから正本を re-read する。**

- phase 内の判断ポイント（route 決定、task 遷移、gating 開始）
- 長い作業の区切り（task 完了、テストスイート実行後、debug cycle 完了）
- re-read は最小限（例: route 判断なら `state.md` + `tasklist.md`、AC 確認なら該当 AC のみ）

**Why:** context compaction で初期 artifact が要約/消失する。ディスク正本は変化しないため re-read で情報劣化を防ぐ。

Codex の remote compact 503 は host 側の中断で、gate の失敗ではない。扱い（loop state を消す停止〔done / cancelled / blocked など〕に進めず、正本から再開する）は `references/context-budget.md` § Codex Remote Compact Failure。

## Context Budget（コンテキスト予算）

**phase 遷移ヘッダー直後に Handoff Summary を 1-3 行で出力する。** 詳細は `references/context-budget.md`。

- 前 phase の「結論」だけ。経緯は書かない
- Express Path でも省略しない
- **Hook-enforced**: Stop hook が phase 遷移時に Handoff Summary 欠落を検出して `systemMessage` で警告
- **Smart Session Recovery**: Stop hook が `state.md` の `Last Handoff Summary` に永続化し、SessionStart hook が session 再開時に Quick Reboot context に注入

**Why:** 長い workflow では context 圧縮で重要情報（AC、設計判断）が失われる。hook 強制で「ルール」から「構造的保証」に昇格。

## 承認見出しルール

**`Human Check Questions`（該当時は `Route / Ownership Matrix` / `Sensitive Data / Masking Policy`）は独立見出しとして維持する。**

- generic な `実装方針` / `リスク` に埋め込まない
- `Route / Ownership Matrix` / `Sensitive Data / Masking Policy` は条件付き節: 該当するときだけ置き、非該当時は見出しごと省略してよい（正本: `references/requirements-template.md` § requirements.md セクション一覧）。置いた見出しを generic セクションへ吸収しない
- `Human Check Questions` には内部状態名や略語だけでなく `条件` / `見る入力` / `出力または次アクション` / `不足時の扱い` が読めるよう書く

**Why:** generic セクションに埋めると route/ownership/masking の変更を reviewer と人間が見落とす。

## Honest Limitations（率直な自己制限の明示）

**standard の `requirements.md` は `## Summary Brief` 内 `### 承認ポイント` 直後に `### Honest Limitations` を置き、この設計で確認できないこと / 担保できない部分を率直に列挙する。** quick では任意。詳細フォーマットは `references/requirements-template.md`。

- 列挙対象: ユニットテストで担保できない部分、デプロイしないと分からない部分、AI が判断できない部分、本番同等環境でないと再現しない挙動
- 「多分できる」は `未確定事項` に回す。Honest Limitations は「できない」と断定できるものだけ
- 人間が scope reduction / 後工程 E2E 計画を判断できる粒度で書く。限界ごとに、先頭に種類を 1 つ書く: `依頼より狭い`（依頼の原文や承認した範囲から縮めた分。選んでもらう判断ポイントの番号か、ユーザーが狭めると決めた記録の場所を添える）/ `リスクが低い`（起きる見込み・害が小さい。件数か未測）/ `費用に見合わない`（費用と効果を数で）/ `その他`（理由を添える）。人が、縮めた要件と気にしなくてよい限界を見分けて決められるようにするため。HITL の `まだ確認できないこと`、Handoff の「限界として開示して人に渡す」の限界、相談役の `残る限界:` も同じ種類を書く

**Why:** 「できること」だけを提示すると、人間は「できないこと」に気付けず過剰 scope で承認してしまう。

## プレースホルダー禁止

**`.steering/` 内の artifact にプレースホルダー表現を書かない。** hook（`validate-steering-write.py`）は検出しない。task-breakdown の Self-Review が tasklist の Steps を、brainstorming の Self-Review が `requirements.md`・`design.md` を見る（ほかは見ない）。

- 禁止表現: `TBD` / `TODO` / `TBA` / `FIXME` / `PLACEHOLDER` / `後で決める` / `後で確認` / `後で追加` / `要検討` / `適宜` / `適切に対応` / `必要に応じて対応`
- 対象外: 語に触れるだけの記録（自己レビューの証跡の `TODO なし`・`Stub grep: TODO なし` など）、コード例（`TODO` を検出する正規表現・テストの入力など）、`#### Attempts` セクション（試行記録用途）。ただし tasklist の `Actual code` に書く実装の `// TODO` は対象

**代替表現の例:**
- `TBD` → `N/A: スコープ外（理由: ...）` または `Open Questions` に明示
- `適切に対応` → 具体内容を書く（例: `400 Bad Request を返す`）
- `必要に応じて` → 判定条件を明記（例: `リクエスト数が 1000/min を超えた場合`）

**Why:** プレースホルダーは先送り。具体値が決まらない場合は `N/A` + 根拠 1 行、または `Open Questions` に残す。

## 省略記法禁止（migration / conversion 対策）

**原文を `.steering/` に転記する際、省略記号で中身を落とさない。** フック（`validate-steering-write.py`）が自動検出・deny する。

- 禁止表現: `...省略` / `…省略` / `（略）` / `(略)` / `省略...` / `省略…` / `（中略）` / `(中略)`
- コードブロック内も対象（migration/conversion タスクでは YAML / コード例の省略がそのまま実装に流れる）
- 除外: `#### Attempts` / `#### 試行記録` セクション内と、`reviews.md` だけへの書き込み（レビュー指摘が原文の省略を引用するため。秘匿系の検査は残る）

**代替表現:**
- 全文を展開する（長くても steering に正本を書く）
- 元ファイルへのパス・行番号参照で示す（例: `参照: .github/ISSUE_TEMPLATE/foo.md L12-L45`）

**Why:** 原文を別フォーマット（YAML Forms 等）に変換する種類のタスクで、`...省略` を design.md / tasklist.md の例示に残すと、実装はその例示を模倣して省略のまま出力ファイルに転記してしまう。AC に「原文保全」を書いてあっても、steering 内の例が省略されていれば実装結果も省略される。

## blocking Open Questions

**route / ownership / prompt contract / output contract / sensitive data / masking / rollout / rollback に関する blocking `Open Questions` が残っている間は `human-check-waiting` に進めない。**

**Why:** これらは人間の policy 判断が必要な論点。未解決で承認フローに進むと承認の意味がなくなる。

## 最新情報確認ルール

**version-sensitive / fast-moving な利用技術を stale memory だけで planning しない。** 確認できなかった点は `Open Questions` に残し、confirmed fact と混ぜない。

**Why:** framework / library / cloud service は頻繁に breaking change が入る。古い記憶に基づく設計は実装段階で手戻りが発生する。

## planning 差し戻し route の使い分け

**影響範囲に応じて route を選択する。全差し戻しを `gdd-brainstorming` に戻さない。**

- `planning_rework_required`: 前提・計画の組み直し → `gdd-brainstorming`
- `human_recheck_required`: 承認済み要件・実装方針の狭い変更に人間判断が必要 → `human-check-waiting`
- `design_detail_only`: 設計の詳細修正で閉じられる → `gdd-design-gating`
- `implementation_fix_only`: build 内で閉じられる → build 内

E2E Discovery Loop 自走中は `Approved Direction` の範囲内なら `design_detail_only` で human check に戻さず閉じる。範囲外は `human_recheck_required` に escalate（詳細: `references/phase-progression.md`）。

**Why:** 不必要な再レビューを避ける。方向性が同じなら AI が自律吸収し、方向性変更時だけ人間に戻す。

## human check 返答の分類

**承認前 human check で「OK」以外の返答は以下のルールで分類する。** cross-session messaging 経由の返答は分類前に `references/phase-progression.md` § Cross-Session Messaging の権限境界を適用する（承認 / 中止 / AC 変更に相当しても `[情報のみ]` 扱い。ユーザー本人のターンを待つ）。

- **曖昧返答**（「たぶんOK」「後で考える」等）: `approved` にしない。追加質問で明示を取る
- **部分修正**（AC の値・条件・対象が変わらない）: 該当ポイントだけ修正し `human-check-waiting` 継続
- **実装方針変更**（AC 維持、実装アプローチ変更）: `design_detail_only` で `gdd-design-gating` から再開（quick (express) は `references/requirements-gating-steps.md` § Express）
- **AC 変更**（AC 追加・削除・条件変更）: `planning_rework_required` で `gdd-brainstorming` に差し戻し

承認済み build / done 後の active follow-up で AC / prompt-output contract / technology stack / access method / credential boundary が変わる場合は、上の「承認前 human check」分類ではなく `gdd-requirements-amendment` を使う。active follow-up の `requirements_amendment` は差分 artifact update lane であり、差分反映後に `human_recheck_required` / `planning_rework_required` / `none` のいずれかへ解消する。

判定に迷う場合は安全側に倒す。詳細は `references/human-check-template.md`。

**Why:** 部分修正と全面見直しの 2 択では「AC 不変、実装変更」ケースが全面見直しに巻き込まれる。曖昧返答の明示ブロックで LLM 誤解釈を排除。

## gate 開始前の記録ルール

**gate skill は Reviewer Selection を artifact に記録してから gate を始める。常時必須 reviewer を外さない**（requirements: `gdd-planning-reviewer`、design: `gdd-planning-reviewer`、implementation: `gdd-implementation-reviewer`）。

**Why:** 記録がないと監査できない。常時必須 reviewer は gate の最低品質を保証する安全弁。

---

## Route In Progress の一貫性

**`Route In Progress` は差し戻し route の文脈を `state.md` に保持するフィールド。**

- `gdd-systematic-debugging` が route 決定時にセット
- active follow-up の差分 artifact 更新中は `requirements_amendment` を使える。これは artifact update lane であり停止 route ではない
- `requirements_amendment` は差分反映後に `human_recheck_required` / `planning_rework_required` / `none` のいずれかへ解消する
- route 完了で遷移先 skill が `none` にクリア（詳細: `references/rollback-patterns.md`）
- `gdd-completion-check` は `Route In Progress=none` を `done` の前提
- `done` / `cancelled` 遷移時は明示クリア
- Hook（UserPromptSubmit / SessionStart）が session 再開時に注入
- session 再開時に `Next Action` との整合性を検証（詳細: `references/state-machine.md`）

**Why:** session 中断後の再開時に「なぜこの phase に戻ったか」を明示。クラッシュ時の state 不整合を整合性検証が安全に検出する。

## adr.md の扱い

**`adr.md` は任意の decision log。routing source / gate 条件 / completion 判定には使わない。**

- デフォルト生成しない
- 無いことだけを理由に止まらない
- 存在しても `Resume From` / `Next Action` の routing source は `state.md` / `tasklist.md` のまま

**Why:** routing / gate を `design.md` / `tasklist.md` に一本化することで state 解決の determinism を保つ。

## Plan mode との分離

**`/gdd-dev` の開始・再開対象では、複雑さだけを理由に host 側 Plan mode へ切り替えない。**

- `.cursor/plans/*.plan.md` をデフォルト生成しない
- Plan ファイルを mandatory にしない

**Why:** Plan mode は host 固有機能で GDD state machine と二重管理になる。
**How to apply:** ユーザーが明示的に比較案や壁打ちログの保存を求めたときだけ使う。

## .steering artifact の正本性

**formal workflow の canonical artifact は active worktree 側 `.steering/...` のみ。**

- tracked な root 側 `.steering` を canonical state として更新しない
- legacy root steering は migration source / diagnostic source としてだけ扱う
- root 側 `.steering` を current task として自動採用しない

**Why:** worktree-first に一本化することで、どの環境でも同じ `.steering/...` を参照すれば state が確定する。あわせて `state.md` / `tasklist.md` / `design.md` には size 上限がある。上限を超えて増える write は止めずに通知する（`hooks/scripts/validate-steering-write.py`・`lib/steering_size.py`）。通知を受けたら、超過分を `worklog.md` / `adr.md` へ退避する。

## Task Binding Registry

**再開・status の task identity は `.gdd/tasks/<task_id>/binding.json` を正本にする。**

- task identity tuple は `worktree path slug` / `state Task ID` / `branch slug` の一致で確認する
- `scripts/gdd_task_binding.py upsert-from-state` で active worktree 側 `state.md` から binding を作成・更新する
- `scripts/gdd_task_binding.py resolve` で current worktree / branch / registry を照合して task を一意に決める
- `.claude/gdd-dev.local.md`、`session_id`、自然文の「続き」「今どこ？」は soft signal / 補助 signal であり、registry と current worktree の一致を上書きしない
- resolver が `conflict` / `not_found` を返す場合は、古い task の詳細を current として出さず、候補と次の1アクションだけを返す

**Why:** compact / resume / platform 差分で session や自然文が混線しても、ディスク上の task binding を照合すれば「古い task を自信ありで提示する」事故を避けられる。

## pre-workflow lane との境界

**`gdd-pre-workflow-brainstorming` は相談専用レーン。formal workflow / state machine の外側。**

- `.steering/...`、state field、artifact を作らない
- 実装、テスト、レビュー、worktree 作成を始めない（相談レーン＝root。判断根拠は `references/workspace-policy.md` § 相談レーンの分類）

**Why:** 相談段階で artifact を作るとユーザーが Go を出す前に formal workflow に入ってしまう。

## scope の勝手な拡大・縮小

**scope を勝手に増やさない。** 承認見出しは generic セクションへ吸収しない（上記「承認見出しルール」参照。条件付き節の省略可否は `references/requirements-template.md` が正本）。

**scope を黙って縮めない。** main が案・既定・推奨を作るとき、次の 4 つは黙って決めない: 依頼や承認した範囲の一部を対象外にする / 狭い側を既定・推奨にする / 合格条件・指標を替える / 後回し（後続 PR・延期）にする。当たるときは、狭い案を出す前に、依頼のままでは届かない理由を、前提か要件の問題として挙げる（前提が誤っている・要件が曖昧すぎる・要件どうしが食い違う・今の方式を前提にしている、など）。依頼より狭くなるのは、前提か要件のどこかがおかしい合図として扱う。そのうえで、前提を変えて依頼を満たす案を推奨にするか、どの前提・要件を確かめたいかを問いとして出す。狭める案は選択肢の 1 つとして並べてよいが、推奨・既定にしない（ユーザーが狭めることを決めたときは除く）。`依頼より狭い` と書けば狭い案を推奨にしてよい、という扱いはしない。迷うときは `gdd-opus-advisor` 2 本に同じ材料を渡して並行に相談する。狭める案を選択肢に並べたら、次に人に示す出力（human check・Handoff・PR 本文・完了報告）の限界の先頭に `依頼より狭い` と理由を書く。その限界には、狭めを選んでもらう判断ポイントの番号か、ユーザーが狭めると決めた記録の場所を添える。どちらも無ければ、その狭めはしない（限界の欄にだけ書いて進めない）

**Why:** 依頼より狭いと書いた推奨にユーザーが OK を返したのは、それしか選択肢が出なかったためだった（2026-11-06。ユーザーは、あまりに狭いものにはやり直しを命じている）。scope を黙って広げると human check で承認した範囲を超える。縮める側は、2026-10 のセッションで依頼から縮めた・止めたずれを調べると、その多くが、人にも相談役にも確認を出す前の main の判断だった（対象外にする・狭い側を推す・合格条件を替える・後回しにする）。GDD の規定の選択肢から出たものはわずかだった

## 選ぶときの基準

案を推すとき・既定を選ぶときは、次の順で照らす。main も相談役も当てる（main が自分で案を推すときも、下の問いを、依頼の原文の目的から自分に問う）。相談役 3 本（`agents/gdd-opus-advisor.md` など）の § 選ぶときの基準 に、この段落より後を同じ文で写す（利用する repo で動く相談役は、plugin の references を読めないため）。一致は `tests/test_advisor_agents.py` が固定し、食い違えばこの節が正本である

並んだ案を見る前に、まず「そもそもどうあるべきか、どうするのがいいのか」を問う。問いがそれを聞いていなくても問う

- そもそもどうあるべきか：依頼の原文の目的（材料にある、ユーザーが前に述べた目的の発言も含む。たとえば「それだけ配ればいい状態にしたい」）を先に書き出し、それと repo の規則・要件から、並んだ案をいったん忘れて、どういう状態になっているのがよいかを考える。目標・指標・手法・方式そのものも、問い直す対象に入れる
- どうするのがいいのか：そのあるべき形に届く、一番よい進め方を考える。症状を塞ぐより先に、その問題を生んだ原因（設計の決定・前提・工程）ごと直す方法を探す
- そのうえで、並んだ案があるべき形に届くかを比べる。どの案も届かないなら、あるべき形に向かう案を推奨にする。問いの前提や案の並びに合わせて、推奨を狭めない
- あるべき形が、下の 0 のユーザーがすでに決めたことと食い違うときは、その決定を覆す案を推奨にしない。食い違いと理由を書く
- あるべき形の一部が依頼の範囲の外（別の機能・別のファイル群）にあるときは、範囲の中で一番近づく案を推奨にし、範囲の外の分は、範囲を広げる提案として分けて書く（相談役は `範囲を広げる提案:`）

0. ユーザーがすでに決めたことを先に見る。依頼の後にユーザーが決めた規則・方針や、すでに受け入れた形（承認・合意・前の確認での選択）があれば、依頼の原文より優先する。上の問いと 1〜3 を、それを覆す理由に使わない。書かれた文（ユーザーの決定・ADR・規則の文書・要件・前の確認の記録）を理由に案を退ける・狭めるときは、その文の原文を場所（`file:line`）つきで引き、その文が何について決めたか（対象）を書く。退ける案がその対象の外にあれば、その文では退けない（決定の文を、書かれた対象より広く読まない）。相談役の推奨が書かれた文（ユーザーの決定・ADR・規則の文書・要件・前の確認の記録）を理由に案を退けていたら、main は 2 本が一致していても、引かれた行を自分で読み直してから推奨として出す
1. 依頼を縮めない。依頼の原文やユーザーが承認した範囲・条件より狭い案は、推奨・既定にしない（ユーザーが狭めると決めたときは除く）。依頼のままでは届かないときは、届かない理由を前提か要件の問題（前提が誤っている・要件が曖昧すぎる・要件どうしが食い違う・今の方式を前提にしている、など）として挙げ、前提を変えて依頼を満たす案を推すか、どの前提・要件を確かめたいかを問いとして返す。依頼より狭くなるのは、前提か要件のどこかがおかしい合図として扱う。`依頼より狭い` と書けば狭い案を推してよい、という扱いはしない。狭める案の数値（実装の費用、誤 block の実測件数、ほかへの波及）は、選択肢の説明として書く。「別の判断が混ざる」「巡が増える」「判断が増える」は、狭める理由にしない
2. 設計変更で完全に閉じるなら、それを先に推す。止めるべきなのは同じ形の修正（列挙を足す・述語を狭める）を続けることで、完全に閉じることではない。入力を構造で閉じる変更（許可リスト・宣言した欄・置き場所の変更・既定の反転など）があれば、限界より先に比べる。限界として開示して止めるのは、閉じる設計変更が見つからないときである
3. 同じ入力空間を閉じる範囲で、広い側と狭い側があれば、広い側が既定。別の機能・別のファイル群へ広げることは既定にしない。選択肢に無い案を推すのは、どの選択肢も依頼を縮めるとき、上の問いのあるべき形にどの選択肢も届かないとき、または 2 の閉じる設計変更・4 の撤去が並んでいないときだけにする
4. 部品を直し続ける前に、その部品が要るかを問う。効果（使った後に何が変わったか・実データの件数）を測る前の部品を、直し続ける側に推さない。要らなければ撤去が既定
5. GDD 自身の hook・gate（agent の操作を止める部品）は事故から守る。agent が手順どおりに動いて踏む形は閉じる。敵対的に作らないと出ない形は限界でよい。利用者の製品の信頼境界（認証・認可・入力検証、外部入力で動く agent の guard）には当てず、敵対的な入力も守る範囲に入れる
6. YAGNI・KISS は、依頼に無いものを足さないための基準である。依頼にあるものを削る理由には使わない
7. 人が決めるのは、ユーザーが任せた範囲（自走の上限・事前回答など）の外にある、取り消しにくい操作（マージ・release・本番・Issue の close）だけである。それ以外は、推奨と理由を示して進める側に倒す
8. 人が手で入れる値の形（secret の登録の形・フォームの入力など）とコードの読み方が食い違うときは、人が普通の手順（管理画面の既定など）で作る形をコードが読む案を推す。人に入れ直させる案は推さない（事例では、管理画面の既定で JSON として入った secret を「プレーンテキストで入れ直して」と頼み続け、人が 3 回押し返した）。コードの読み方をその形に決める直しは、利用者の規則が禁じるフォールバックに当たらない。読み方を repo の外が決めている、ほかの読み手が今の形で読んでいるなど、コードを直せないときは、その読み手と理由を添えて入れ直しを推してよい

## fail-closed の応答

**fail-closed で止めるときも、少なくとも `参照した正本` / `停止理由` / `次の1アクション` を返し、`<gdd-stop>` の後に `## 👤 次にすること` を付ける。** 表現は `references/output-format.md` のブロック時ガイドラインに従う。

**Why:** 停止理由と復旧手順を常に返すことで人間が即座にアクションを取れる。
