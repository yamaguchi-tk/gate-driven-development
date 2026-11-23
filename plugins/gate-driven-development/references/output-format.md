# スキル開始アナウンス

skill が起動したとき、処理を始める前に 1 行でアナウンスする。ユーザーが「今どのスキルが動いているか」を把握できるようにする。

## フォーマット

```
▶ <skill 名>: <このスキルが今回行うこと（15 字以内）>
```

### 例

```
▶ gdd-brainstorming: 新規タスクのブレインストーミング
▶ gdd-systematic-debugging: failure の症状分類と routing 判定
▶ gdd-receiving-code-review: advisory findings のトリアージ
▶ gdd-pr-review: PR 作成前チェックリスト実行
▶ gdd-completion-check: AC 検証と完了宣言の最終判定
```

### ルール

- アナウンスは phase ヘッダー（`<gdd-phase>` マーカー）の **前** に出す
- 1 行に収める。箇条書き・見出しは使わない
- 内部スキル（state machine から自動 route されたもの）でも省略しない

---

## Human-Facing Conversation Contract

人間との会話内容はすべて、内部 state の値ではなく「人間が何を理解し、何を決めればよいか」を先に書く。`Next Action` / `Route In Progress` / `Resume From` / `human_recheck_required` / `blocked` などの内部用語は補足として使ってよいが、本文の主語にしない。

停止本文も同じ契約に従う。停止するとき（human check・経過報告の末尾の問い・確認の出し直し・完了報告を含む、すべての停止）は、1 の前に `references/human-check-template.md` § 判断の書き方 2 の前置き 3 行（`**依頼**:`・`**なぜやるか**:`・`**現在地**:`）を置く。返事を待たない停止の `**現在地**:` には、次に何を待っているかを書く。前の発言を読んだ前提で書かず、`D-1`・`判断 2`・`案 C` のような前の発言の中の呼び名だけで頼まない。人間に返す本文では、次の順序を基本形にする:

1. **いまの結論**: 何が起きたか、どこまで進んだか
2. **ここまで出来ていること**: 実装・検証・確認済みの事実
3. **まだ確認できていないこと**: 未検証・外部前提・不足 evidence
4. **人間にお願いしたいこと**: 選択、確認、準備してほしいもの（判断を求めるときの書き方は `references/human-check-template.md` § 判断の書き方）
5. **次にやること**: OK 後に AI が進める作業、または再開コマンド

内部用語は補足として括弧で出す。例: `本番に近い条件での検証（prod_equivalent）`、`次に実行する工程（Next Action）`。見出しだけで `holdout human-confirm executable` のように並べない。

---

# 作業場所宣言

worktree で作業するか root で作業するかの**判断ルール本文**は `references/workspace-policy.md` を参照。この節では書式のみ規定する。

- **フォーマット**: 応答の最初の行に1行で出力する（スキル開始アナウンス・フェーズ遷移ヘッダーより前）。
- **2 例**:
  - `作業場所: worktree（<worktree の絶対パス>）`
  - `作業場所: root（trivial: <理由>）`

---

# Phase 遷移ヘッダー

> **所有**: phase 遷移時の出力フォーマット（ヘッダー、進捗バー、ブロック時表現）
> **上位正本**: なし（出力形式の独立正本）
> **参照元**: 全 phase skill

各 skill が phase を進めるとき、ユーザーへの出力の冒頭に以下のヘッダーを付ける。

## フォーマット

```
<gdd-phase>現在の skill 名</gdd-phase>
Phase: <現在の phase 名>
Task Size: trivial | quick (express) | quick (standard) | standard | 未定
Route In Progress: <差し戻し route 名>（none 以外のときだけ表示）
正本: <参照すべき artifact パス>
次のアクション: <次に実行する skill 名 または停止理由>
```

- `Route In Progress` は `state.md` の値をそのまま表示する（`design_detail_only` / `implementation_fix_only` / `human_recheck_required` / `planning_rework_required` / `requirements_amendment` / `batch_mixed`）
- `requirements_amendment` は active follow-up の artifact update lane で、差分反映中であることを示す。停止判断としては `human_recheck_required` / `planning_rework_required` / `none` のいずれかへ解消してから扱う
- `none` または未設定の場合はこの行自体を省略する（通常フローでは表示されない）

> `<gdd-phase>` マーカーは Stop hook が phase を正確に検出するために使う。ヘッダーの 1 行目に必ず含める。値は skill 名（例: `gdd-brainstorming`、`gdd-requirements-gating`）。

### 進捗バー

ヘッダーの直後に、以下の進捗バーを 1 行で出力する。現在の phase を `**太字**` にし、完了した phase に `~取消線~` を付ける。

**standard / quick (standard) パス:**

```
~plan~ → ~req-gate~ → ~human-check~ → **design-gate** → task-breakdown → TDD:RED → TDD:GREEN+REFACTOR → impl-gate → completion
```

**quick (express) パス:**

```
~plan~ → ~req-gate~ → ~human-check~ → **TDD:RED** → TDD:GREEN+REFACTOR → impl-gate → done
```

Express では design-gate / task-breakdown / completion を省略する。

phase 名の対応表:

| 表示名             | skill 名                           |
| ------------------ | ---------------------------------- |
| plan               | gdd-brainstorming                  |
| req-gate           | gdd-requirements-gating            |
| human-check        | human-check-waiting                |
| design-gate        | gdd-design-gating                  |
| task-breakdown     | gdd-task-breakdown                 |
| TDD:RED            | gdd-test-driven-development        |
| TDD:GREEN+REFACTOR | gdd-subagent-driven-implementation |
| impl-gate          | gdd-implementation-gating          |
| completion         | gdd-completion-check               |

> **補足**: TDD は RED / GREEN / REFACTOR の 3 段階で構成される。RED（テスト作成）と GREEN+REFACTOR（実装+リファクタ）を別スキルで実行するが、全体として RED-GREEN-REFACTOR サイクルを表す。

## Context Handoff Summary

phase 遷移時に、進捗バーの直後に Context Handoff Summary を出力する。前 phase の決定事項を次 phase に引き継ぐための圧縮ブロック。

### フォーマット

```markdown
<!-- Context Handoff: <from-phase> → <to-phase> -->

**Handoff:** <決定事項 1-3 件を箇条書き> | 変更対象: <ファイルパス> | 注意: <次 phase で気をつける点>
```

- 10 行以下（理想は 1-3 行）
- 前 phase の「結論」だけを書く。経緯は書かない
- Express Path でも出力する
- phase ごとの Handoff 内容は `references/context-budget.md` を参照

### 例

```markdown
<!-- Context Handoff: design-gating → task-breakdown -->

**Handoff:** REST API + カーソルベースページネーション採用、offset 上限 10000 | 変更対象: src/api/users.ts, src/components/UserList.tsx | 注意: offset パラメータの最大値バリデーション
```

## 出力量ガイドライン

phase 遷移やレビュー結果の出力が長すぎるとユーザーの注意が散る。sizing ごとに出力行数の上限目安を定め、重要な情報を先に見せる。

### 行数の目安

| sizing           | phase ヘッダー + Handoff          | findings 出力              | 合計目安      |
| ---------------- | --------------------------------- | -------------------------- | ------------- |
| quick (express)  | 2 行（進捗バー + 次のアクション） | 省略可                     | **10 行以下** |
| quick (standard) | 標準（6 行）                      | High のみ                  | **20 行以下** |
| standard         | 標準（6 行）                      | High + ops-blocking Medium | **30 行以下** |

### Findings 出力の絞り込み

reviewer が返す findings が多い場合、ターミナルへの出力を絞る。findings の全文は `worklog.md` に残す。

- **High**: 常に出力する（件名 + 1 行要約 + 対象ファイル）
- **ops-blocking Medium**（運用に直接影響する Medium）: standard のみ出力する
- **その他 Medium / Low**: ターミナルには「他 N 件は worklog.md を参照」と折りたたむ
- **Advisory**: ターミナルには出力しない

```
## Implementation Review 結果

✅ approved（3 件の指摘あり）

- HIGH-1: 入力値未検証（src/api/handler.ts:42）→ 修正済み
- MEDIUM-2 [ops]: レートリミット未設定（src/api/handler.ts:18）→ 修正済み
- 他 1 件は worklog.md を参照
```

### Express の phase ヘッダー圧縮

Express path では phase 遷移ごとの出力を最小化する。`<gdd-phase>` マーカーと進捗バーは省略せず、ヘッダーの中間行（Phase / Task Size / 正本）を省略して 2 行にする。

```
<gdd-phase>gdd-implementation-gating</gdd-phase>
~plan~ → ~human-check~ → ~TDD:RED~ → ~TDD:GREEN+REFACTOR~ → **impl-gate** → done
次のアクション: done
```

**Why**: Express は 1-2 ファイルの軽量変更であり、Task Size や正本パスは変わらない。毎回の 6 行ヘッダーは冗長で、ユーザーが進捗を追いにくくなる。

## ルール

- `<gdd-phase>` マーカー + 4 行ヘッダー + 進捗バー + Context Handoff Summary をセットで出力する。いずれも省略しない（Express の圧縮ヘッダーを除く）
- 値が不明な場合は `未定` と書く
- `Phase` は skill 名ではなく phase 名（planning / requirements-gating / human-check / design-gating / task-breakdown / build / implementation-gating / completion-check）
- `Task Size` は `requirements.md` 冒頭の `Task Size` に従う
- `正本` は worktree 側 `.steering/.../` の相対パス（例: `.steering/my-task/requirements.md`）
- `次のアクション` は次に進む skill 名、または terminal 状態（`done` / `cancelled` / `human-check-waiting` / `blocked`。この欄に書ける値で、reason の一覧ではない。一覧は § `<gdd-stop reason>` の許容値）
- `planning_rework_required` / `human_recheck_required` / `design_detail_only` / `implementation_fix_only` は **route 名** であり、`gdd-stop` の reason ではない。停止が必要な場合は、human-check テンプレートを出すときだけ `human-check-waiting`、それ以外は `blocked` を使い、route 名は `Route In Progress` または本文で示す
- route 差し戻しで `blocked` 停止する場合、ヘッダーの `次のアクション` には **terminal 状態ではなく実際の復帰先**（例: `gdd-brainstorming`）を書いてよい。terminal 理由の `blocked` は `<gdd-stop>` と停止本文で伝える
- post-return で **to-phase の開始ヘッダー**を出す場合、ヘッダーの `次のアクション` には **これから実行する skill（= to-phase）** を書く。さらに先の phase は、その skill が完了してから次の出力で示す
- rollback / re-entry で復帰先 phase の開始ヘッダーを出す場合、進捗バーは「過去にどこまで進んだか」ではなく **復帰先を現在地とした再開表示** にする。巻き戻された phase より後続の完了表現は残さない
- gate 通過・差し戻し・停止のいずれの場合もヘッダーを出す
- `gdd-stop` タグとヘッダーは併用してよい（ヘッダーが先）

## Progress Visibility（進捗の可視化）

Stop hook が自律継続中に systemMessage へ以下の情報を自動注入する。skill 側での追加作業は不要。

- `phase: <current-phase>` — 現在のフェーズ名
- `tasks: N/M done` — 完了タスク数 / 全タスク数（tasklist.md がある場合）
- `current: <task-name>` — 現在実行中のタスク名（50 文字まで）

これにより、ユーザーは自律実行中も「今どこにいるか」「全体の何割が終わったか」を把握できる。

`gdd-status` skill も同じ `phase: ... | tasks: N/M done | current: ...` 形式で Progress セクションを出力する。自律実行中（Stop hook）と手動確認時（gdd-status）で同じ情報が同じ形式で表示される。

**Why:** human check 後の自律実行は数十分に及ぶことがある。進捗情報がないと「動いているのか止まっているのか分からない」不安が生じる。systemMessage に進捗を含めることで、ユーザーのターミナルに各 iteration のステータスが表示される。表示形式を統一することで、ユーザーが「どこを見ても同じ情報」を得られる。

## ブロック時の出力ガイドライン

fail-closed や mandatory gate で停止するときは、正確さに加えて**初見のユーザーにも次のアクションが分かる**書き方を心がける。

### 原則

- 内部用語（`entry intent=ambiguous`、`active steering candidate`）だけで説明せず、ユーザーが取るべき具体的な操作を自然言語で書く
- 「何が起きたか」→「なぜ止まったか」→「どうすればよいか」の順で書く
- 選択肢がある場合はコマンド例を添える
- 下のパターンは言い回しの例で、前置き 3 行（§ Human-Facing Conversation Contract）を省いて示す。実際の停止では冒頭に置く

### よくあるブロックパターンと推奨表現

**パターン 1: `/gdd-dev` 単独実行（引数なし）**

悪い例:

> 停止理由: `$ARGUMENTS` が空で `ambiguous`

良い例:

> `/gdd-dev` だけだと新規タスクか再開か判断できません。
>
> - 新しいタスクを始める → `/gdd-dev 〇〇を追加したい`
> - 前回の続き → `/gdd-dev 再開`

**パターン 2: resume 候補が複数**

悪い例:

> 同一優先順位に candidate が複数あり fail-closed で停止

良い例:

> 再開できるタスクが複数あります。どれを続けますか？
>
> 1. `20260405-notification` — implementation-gating 待ち
> 2. `20260403-auth-fix` — human-check 待ち
>
> → `/gdd-dev 再開 20260405-notification` のように指定してください

**パターン 3: git / worktree が使えない**

悪い例:

> git / worktree が必要 phase なのに使えない

良い例:

> このディレクトリは git リポジトリではないため、formal workflow を開始できません。
> → git リポジトリ内で `/gdd-dev` を実行してください

**パターン 4: external security evidence 不足**

悪い例:

> required external security evidence が無いため `done` に進めない

良い例:

> セキュリティスキャンの結果がまだ記録されていません。`done` に進むには以下が必要です:
>
> - [ ] `security_evidence:code` — コードスキャン結果
>
> スキャンを実行するか、N/A の理由を明記してください

**パターン 5: same-name ambient asset 衝突**

悪い例:

> same-name ambient asset の衝突で deterministic に解決できない

良い例:

> `gdd-brainstorming` という名前の skill が別のプラグインにも存在するため、どちらを使うか判断できません。
>
> - 原因: 別実体の同名 skill/agent が競合している
> - → 競合する skill を退避・無効化してから `/gdd-dev` を再実行してください

**パターン 6: reviewer で high 指摘が未解消**

悪い例:

> unresolved high findings があるため次 phase に進めない

良い例:

> AI レビューで重要度 High の指摘が残っています。次の工程に進むには解消が必要です:
>
> - HIGH-1: 入力値のバリデーションが不足（`design.md` § API Design）
> - → 指摘に対応して `design.md` を修正してください
> - → 修正後、`/gdd-dev 再開` で続行できます

**パターン 7: remediation loop 上限到達**

悪い例:

> blind loop 防止により停止

良い例:

> 実装の修正を 3 回繰り返しましたが、テストが通りません。同じアプローチでは解決しない可能性があります。
>
> - 直近のエラー: `TypeError: Cannot read properties of undefined`（`src/api/handler.ts:42`）
> - → 設計を見直す場合: `/gdd-dev 再開`（design_detail_only で差し戻し）
> - → 人間が修正する場合: エラー箇所を手動で修正後 `/gdd-dev 再開`

## 停止出力の構造化テンプレート

すべての停止出力は以下の構造に従う。チームでの再現性を高めるため、必ずこの順序で情報を提示する。停止本文も同じ契約に従うため、内部用語だけの「次のアクション」ではなく、先に自然な日本語で人間がすることを書く。

```
## 停止しました

<前置き 3 行（`**依頼**:`・`**なぜやるか**:`・`**現在地**:`。停止の種類によらず毎回。§ Human-Facing Conversation Contract）>
**いまの結論**: <1文で状況を説明>

**ここまで出来ていること**: <確認済みの事実。無ければ「まだありません」>

**まだ確認できていないこと**: <不足している evidence / 外部前提 / 判断>

**人間にお願いしたいこと**:
- → <具体的なコマンド例または操作手順>
- → <代替手段がある場合はそちらも>

**次にやること**: <AI が再開後に実行する工程。必要なら内部名を括弧で補足>

**参照した正本**: <file path>

<gdd-stop reason="<許容値>">

## 👤 次にすること

- <reason に対応する次のアクション（下記マップを参照）>
```

### `<gdd-stop reason>` の許容値（正本）

Stop hook が認識する reason 値は以下 **8 つのみ**。他の値を使うと hook が検出に失敗し autonomous continuation が走る可能性がある。

| reason 値               | 用途                                                                                                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `done`                  | ワークフロー正常完了（PR 作成後の終了など）                                                                                                                |
| `cancelled`             | ユーザー明示中止（「中止」「cancel」「やめる」等）                                                                                                         |
| `human-check-waiting`   | human check 承認ポイント提示後の停止                                                                                                                       |
| `clarification-needed`  | 質問・確認が必要で自律継続できない停止。loop state を消す停止（`done`・`cancelled`・`blocked`・`staging-verification-blocked`）の前に、background の dispatch への `TaskStop` が待ちから外れない結果（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running` のどれでもない結果。拒否など）で返ったときの受け渡しにも使う（`references/state-machine.md` § Autonomous Continuation）                                                                                                                     |
| `blocked`               | fail-closed 全般（external prerequisite 不足、ambiguous routing、contract violation、read-back 失敗、reviewer unresolved high 等すべての mandatory stop）。`fail-closed`/`contract-violation`/`read-back-fail` 等の細分化 reason は hook 未サポートのため marker では `blocked` に集約し、カテゴリは本文の「何が起きたか / なぜ止まったか」で表現する |
| `external-review-waiting` | 外部レビュー収束待ちの pause（`ScheduleWakeup` で自走、state.md 保持）                                                                                    |
| `auth-waiting`          | SSO/auth 失効による非終端 pause（再ログイン後の wake で自走再開、state.md 保持、認証情報は扱わない。max-wake 上限到達で `blocked`）                          |
| `staging-verification-blocked` | staging E2E を実行できない環境での、手動確認の依頼の停止（`references/phase-progression.md`）。loop state を消す |

> **MUST: proactive に書くこと**
> このブロックは stop hook が出力後に検査するが、**hook に頼らず最初から書くこと**（hook に指摘されてから追加するのは reactive 修正であり、不要なコンテキストを消費するため禁止）。subagent をバックグラウンド起動して停止する場面でも必ず書く。

### 停止時の「👤 次にすること」マップ（必須 trailing block）

`<gdd-stop>` を出す停止出力の末尾に reason 対応の `👤 次にすること` ブロックを必ず含める（**`<gdd-stop>` タグの後**に置く。順序: 本文 → `<gdd-stop>` → `## 👤 次にすること`）。Stop hook は `## 👤 次にすること` 等の Markdown 見出し行を fail-closed で検査する（見出しレベルは自由。以下マップは内容の目安—状況に応じた補足を追記してよい）。`cancelled` のみ免除。

| reason | 👤 次にすること |
| --- | --- |
| `human-check-waiting` | 「OK」で承認 / 直したい点を書いて返信 |
| `clarification-needed` | 質問に回答してください |
| `blocked` | `<復帰アクション>`。解消したら「続行して」 |
| `external-review-waiting` | PR: `<url>`。レビュー収束を自動で待っています。今すぐ止めるには「中断」 |
| `auth-waiting` | 再ログインしてください。完了後に自動で再開します（上限到達時は「続行して」） |
| `staging-verification-blocked` | staging で手動確認し、結果を返信してください |
| `done` + PR 作成 | PR: `<url>`。マージしたら「マージした」、次段階は「次に進んで」 |
| `done` + 後続 stage 残 | 次段階に進むには「次に進んで」 |
| `done` + 後続なし | 完了（追加対応なし） |

### Marker 形式

- Stop hook が検出に使う正本は **開始タグ** の `<gdd-stop reason="...">` である
- `</gdd-stop>` の閉じタグは **任意**。付いていてもよいが、hook 判定には使わない
- 新規のテンプレート・例・テストでは **開始タグだけ** を標準形として使う

### 具体例: human check 待ち

human check 停止時は、汎用停止テンプレートではなく `references/requirements-gating-steps.md` の **必須出力テンプレート** を使う。承認ポイントをターミナルにそのまま出力し、人間が artifact を開かなくても判断できるようにする。

```
## 人間の確認が必要です

**依頼**: 「ユーザー一覧が重いので、ページを分けて返すようにしてほしい」
**なぜやるか**: 全件を返すので、1000 件を超えると応答に 5 秒以上かかる
**現在地**: 要件の整理とレビューは済み。OK で設計と実装に進む
### やること
ユーザー一覧 API にカーソルベースページネーションを追加する

### 判断材料
- **確定**: REST API、カーソルベース、デフォルト 20 件/ページ
- **未確定**: なし
- **やらないこと**: 既存の offset パラメータの廃止、管理画面側の変更
- **外部依存**: なし（既存 DB インデックスで対応可能）
- **設計方針**: offset ではなくカーソルベースを採用（大量データでの性能劣化を防ぐ）

### 承認ポイント（OK / 別案希望 で回答してください）

1. **方式**: ページネーションをカーソルベースで実装する
   - 背景: 全件取得で 1000 件超えるとレスポンスが 5 秒以上かかる
   - 変更前: GET /users で全件返却
   - 変更後: GET /users?cursor=xxx&limit=20 でページ分割
   - 採用案: カーソルベース（大量データで安定した性能）
   - 代替案: offset ベース（実装は簡単だが 10 万件超でスキャン負荷）
   - → **OK / 別案希望**

2. **方向性**: ユーザー一覧の性能改善
   - 自走範囲: API レスポンス形式の変更、テスト追加、ドキュメント更新
   - 人間に戻す条件: DB スキーマ変更が必要になった場合
   - → **OK / 自走範囲を制限したい**

### 参考情報
- 変更範囲: src/api/users.ts, src/components/UserList.tsx
- リスク: 既存クライアントが offset パラメータを使っている場合の互換性
- ロールバック: カーソルパラメータを無視して全件返却に戻す
- 詳細: .steering/20260407-pagination/requirements.md
```

### 具体例: Contract override 拒否

Remediation Loop Safety や Approved Direction 境界をユーザー発言で override 要求された場合の応答テンプレ。停止はせず、route を提示して判断を戻す。

```
## Contract override は受諾できません

**ご要望**: <ユーザー指示の要約>（例: 「もう 1 回 implementation_fix_only でリトライして」）

**却下理由**:
- <具体的な contract>（例: Fix Attempts=3 到達 + 同一 root cause 3 連続再発）
- ユーザー発言では Remediation Loop Safety / Approved Direction 境界を override 不可（`commands/gdd-dev.md` Instructions #11）

**参照した正本**: references/state-machine.md § Remediation Loop Safety / references/phase-progression.md § Escalation Decision Table

**代わりの route**:
- → `<選んだ route>`（例: `design_detail_only`）を自律採用し `<復帰先 skill>` に進みます
- → Approved Direction の境界を変える必要があれば、再度 `human-check-waiting` に戻って再承認してください
```

### 具体例: Scope Drift Guard 発動時の自走継続説明

Guard 発動（4 回目の `design_detail_only` など）後、自走 4 条件再評価で自走継続を選んだ場合の説明テンプレ。停止はしない。

```
## Scope Drift Guard 発動（自走継続）

**何が起きたか**:
- `Scope Drift Counter`=<N>（閾値 3 超過 / または `Cumulative Changed Files`=<M>（事前スキャンの <X> 倍、閾値 3 倍超過）

**再評価結果**（すべて yes なので自走継続可）:
- AC 不破壊: yes / 根拠: <1 行>
- Approved Direction 範囲内: yes / 根拠: <1 行>
- security 新規発生なし: yes
- AC 根本的追加・削除なし: yes

**参照した正本**: references/phase-progression.md § E2E Discovery Loop § Scope Drift Guard

**次のアクション**:
- → `Drift Review Required=true` を立て、次の `gdd-implementation-gating` で reviewer に可視化
- → 自走継続。stop せず次 phase へ
```

### 具体例: blocked（外部前提不足）

```
## 停止しました

**依頼**: 「認証の更新を入れてほしい」
**なぜやるか**: 期限切れの認証ライブラリを更新し、既知の脆弱性を閉じる
**現在地**: 実装とテストは済み。完了チェックで止まっていて、evidence がそろえば done に進む
**何が起きたか**: 完了チェックで external security evidence が不足しています。

**なぜ止まったか**: required evidence なしに done に進めません

**参照した正本**: .steering/20260407-auth-update/tasklist.md § Verification

**次のアクション**:
- → snyk code scan を実行して evidence を記録してください
- → N/A の場合は理由を Verification セクションに明記してください
- → 準備ができたら `/gdd-dev 再開` で completion check を再実行

<gdd-stop reason="blocked">

## 👤 次にすること

- snyk scan 結果を evidence として記録した後 `/gdd-dev 再開`
```

---

### スコープ変更通知

セッション中にタスクの対象・範囲が変わった場合（別サブタスクへの移行・問題の切り分け・意図的な絞り込みを含む）、以下を `<gdd-stop>` タグの**直前**（本文末尾）に **必ず** 追加する（`done` の作業完了報告も同様）:

> **スコープ外になった項目**
> - <元のタスクや要求で、今回対応しなかった項目>
> - 理由: <スコープ外にした理由>
> - 対処が必要な場合: <ユーザーが次にすべき操作>

スコープ変更に気づかず省略した場合、ユーザーは「対応済みか未対応か」を判断できない。

**スコープ変更の例**:
- 「Aバグ調査」で始まり「Bバグ修正の PR 作成」で完了した場合 → 「Aバグへの対処は今回スコープ外」を明記
- 「全 env var の SSM 移行」を依頼されて「静的値のみ」を移行した場合 → 「PARAM_NAME / SECRET は今回未対応」を明記
