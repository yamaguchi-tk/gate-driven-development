# gate-driven-development

AI エージェントによる開発を「正しく完了させる」ための steering-first workflow plugin。

## 何を解決するか

AI コーディングエージェントは強力だが、放任すると**要件の取り違え・設計のスキップ・テスト不足・レビュー漏れ**が起きやすい。手戻りに気づくのは PR レビューや本番障害のタイミングになりがちで、修正コストが高い。

gate-driven-development（GDD）は、開発の各工程に**自動ゲート**を設け、問題を早期に検出・停止させる。人間が確認すべきポイントは最小限に絞りつつ、AI が自律的に品質を担保する。

## 誰のためのツールか

| 対象             | GDD でできること                                                      |
| ---------------- | --------------------------------------------------------------------- |
| **開発者**       | `/gdd-dev <タスク>` で要件整理から実装・レビュー・PR 作成まで一気通貫 |
| **レビュワー**   | AI reviewer が先にチェック済み。人間は判断が必要な点だけ確認          |
| **テックリード** | チーム全体の開発プロセスを標準化。運用レベルで厳密さを調整可能        |
| **PM**           | 人間確認ポイントで要件の承認・却下ができる。工程の可視化              |

## 向いているケース / 向いていないケース

| 向いている                                        | 向いていない                            |
| ------------------------------------------------- | --------------------------------------- |
| 要件整理から実装まで一貫して進めたい              | 探索的なプロトタイピング                |
| チームで開発プロセスを標準化したい                | 1行の typo 修正（trivial パスで対応可） |
| 中断・再開が頻繁に起きる                          | AI を使わない手作業の開発               |
| レビューの品質を底上げしたい                      |                                         |
| Claude Code / Cursor / Codex どれでも同じ工程で進めたい |                                         |

## インストールすると変わること

GDD の hook の多くは、`/gdd-dev` で作業を始めたセッションでだけ動く。ただし次のものは、`/gdd-dev` を使っていないセッションでも動く。hook ごとの役割は [§ Hooks](#hooks) を参照。

| 効果 | いつ | 何が起きるか |
| --- | --- | --- |
| 止める | background の Bash で待ちのループ（`until`・`while`・`for` と `sleep`、`--watch`、`gh run watch`）を動かすとき（subagent の中も含む） | 実行を止め、上限つきで待つ `scripts/wait-until.py` を使うよう案内する。`sleep N` だけの待ちは通す |
| 止める | GDD の作業用の名前（`gdd/`・`claude/`・`codex/`・`cursor/` の後に `20YYYYMM` で始まる名前）のブランチを、worktree の外で作るとき、または worktree を HEAD・main などから作るとき | 実行を止め、worktree で作業するよう案内する |
| 止める | `.steering/` 配下にファイルを書くとき | メールアドレス・秘密情報・ローカルの絶対パスなどを検査し、当たれば止める |
| 止める | Python 3 が無い、または検査が異常終了したときの Write・Edit | 書き込みを止める（判定できないときは止める側に倒す） |
| 止める（1 回だけ） | 最後の発言が「CI が通ったらマージする」の形で終わって止まろうとしたとき | 止まるのを 1 回押し返し、待ってからマージするよう促す |
| 文脈を足す | セッションを始めたとき | GDD が使えることと `/gdd-dev` の案内を足す |
| 文脈を足す | Skill ツールで `gdd-implementation-gating` か `gdd-completion-check` を呼んだとき | main セッションで回さず、`gdd-formal-gate-runner` に任せるよう案内を足す |
| 文脈を足す | PR がある branch に `git push` するとき | `gh pr view` で PR を確かめ（ネットワークに出る）、`pr-review-followup` skill を案内する |
| 記録だけ | Claude の Bash の中で `git push` するとき | 環境変数で git の pre-push hook を足し、push がレビュー済みの tip かを `~/.claude/.gdd-hook-state/push-review.log` に書く。push は止めない。`~/.gitconfig` や `.git/hooks/` は書き換えない |
| OS の通知 | 入力待ち・許可待ちになったとき、API エラーでターンが終わったとき | OS の通知を出す。API エラーは記録し、次のセッションの始めに 1 回だけ報告する |

全部の hook を止めるには `~/.claude/gdd-hooks-disabled` というファイルを置く（中身は空でよい）。消せば元に戻る。

## 他のワークフローとの比較

### GDD が解決する問題

AI コーディングエージェントで開発を進めると、以下の問題が繰り返し起きる。GDD はこれらを構造的に解決する。

| よくある問題                                                          | 既存ツールの対応                                         | GDD の解決方法                                                                                                        |
| --------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **要件の取り違え** — AI が勝手に解釈して実装が方向違い                | Plan mode: 計画は立てるが実行時の逸脱を検出できない      | 要件 gate + human check で方向性を承認。承認範囲を `Approved Direction` に記録し、逸脱を Scope Drift Guard で自動検出 |
| **中断後に再開できない** — session が切れると「今どこ？」が分からない | Superpowers: 4フェーズの流れはあるが、再開制御は弱め     | state.md に gate status を永続化。Stop hook が Context Handoff Summary を自動保存し、SessionStart hook で即座に復元   |
| **レビュー漏れ** — 実装が終わってから PR で初めて問題が見つかる       | workflow-gate: tool blocking で制御するが運用が重い      | 実装直後に inline review gate を自動実行。High/Medium issue は自律 remediation loop で PR 前に解消                    |
| **テスト不足** — 実装を先に書いてテストが後回し                       | claude-code-workflows: recipe 型で手順はあるが強制力なし | TDD を state machine で強制（RED → GREEN → REFACTOR）。テスト作成前に実装に進めない                                   |
| **過剰なセレモニー** — 小さな修正にもフル工程を要求される             | AI-DLC: 非機能レビュー充実だが gate 数が多い             | タスクサイズ自動判定（trivial/quick/standard）で ceremony を適応。1行修正は gate なし、軽量変更は Express Path        |

### ポジショニング

```
軽い ◀━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶ 重い
Plan mode → Superpowers → GDD → workflow-gate / AI-DLC
(計画だけ)   (4フェーズ)   (自動ゲート)   (厳密統制)
```

GDD は **Plan mode だけでは不安だが、AI-DLC ほどの厳密さは不要** な領域を狙う。方向性を決めたら AI が自律的に完走し、問題があれば自動ゲートで止まる。

### GDD の差別化ポイント

- **State Machine**: 全工程の状態遷移を formal に管理。中断・再開・差し戻しを正確にルーティング
- **Fail-Closed**: 曖昧な状態では先に進まず停止。理由と次のアクションを必ず返す
- **Worktree-First**: 専用 worktree で作業を分離。main を汚さない
- **Claude Code / Cursor / Codex 対応**: 同じ契約・同じゲートを各 host で再現
- **運用レベル選択**: strict / standard / light から選べる（`references/operation-levels.md`）
- **Express Path**: 1-2 ファイルの軽量変更は最短経路で（`references/task-sizing.md`）
- **Complexity Evaluation**: 要件の複雑さを 5 次元で評価し ceremony を自動選択（`references/task-sizing.md` § 正式判定）
- **Context Budget（Hook-enforced）**: phase ごとに必要な情報を管理。hook が Handoff Summary の出力漏れを自動検出し、品質を構造的に保証（`references/context-budget.md`）
- **Smart Session Recovery**: phase 遷移時の決定事項を `state.md` に自動永続化。session 再開時に前セッションの最終判断を即座に復元
- **Parallel Execution**: 依存関係のないタスクを subagent で並列実行。standard タスクの実装時間を短縮（`references/task-breakdown-steps.md`）
- **Implementation Guidance**: 実装前にプロジェクト規約・既存コードパターン・過去の学習を参照し、一貫したスタイルで実装を行う
- **Direct Intent Shortcut**: 具体的な指示（「この関数にバリデーション追加」等）では brainstorming の代替案検討を skip し、高速に実装開始
- **Cross-Task Learning**: 完了タスクから設計パターン・却下案・コード規約を蓄積し、次のタスクで参照（`references/cross-task-learning.md`）
- **Reviewer Calibration + Reviewer Learning Loop**: レビュー差し戻しの正当性を記録し、次回 review で false positive パターンの severity を自動調整
- **Progress Visibility**: 自律実行中に Stop hook がフェーズ名・タスク進捗を自動通知
- **CI / Issue 連携**: PR 作成前に CI status を自動確認。`requirements.md` に Issue 番号があれば `Closes #N` を PR 本文に提案
- **Workflow Metrics**: `gdd-metrics` で gate 通過率・差し戻し率・Reviewer Learning Loop の効果を定量的に可視化（steering データ蓄積後に有効）

### なぜ Plan mode や Superpowers だけでは足りないのか

各 runtime の built-in 機能（Plan mode、TodoWrite、Agent tool、Worktree、Memory）は強力だが、**提案はしても強制しない**。GDD が加える価値は「enforcement（強制）」にある。

| 観点           | Built-in だけ                                          | GDD を加えると                                                                            |
| -------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| **要件の承認** | Plan mode で計画を立てるが、実装時の逸脱を検出できない | gate で承認するまで実装に進めない。`Approved Direction` で逸脱を検出                      |
| **中断・再開** | session が切れると「今どこ？」が不明                   | `state.md` に gate status を永続化。hook で自動復元                                       |
| **レビュー**   | 人間が PR で初めてチェック                             | 実装直後に AI reviewer が自動チェック。PR 前に解消                                        |
| **TDD**        | 任意。テストを書かなくても実装できる                   | state machine で RED → GREEN → REFACTOR を強制                                            |
| **監査証跡**   | git log のみ                                           | Reviewer Selection・Approved Direction・Verification を `state.md` / `tasklist.md` に記録 |

**一言で言うと**: Plan mode は「計画を立てる」、GDD は「計画通りに完了させる」。

### Superpowers と併用するときの使い分け

superpowers plugin（`superpowers:brainstorming` / `superpowers:test-driven-development` / `superpowers:systematic-debugging` 等）は GDD と独立に install / activation 可能。両者は重複領域があるが、**設計思想が異なる**ため使い分けが意味を持つ。

| 観点                | superpowers primitives          | GDD primitives（state machine 一体型）                                              |
| ------------------- | ------------------------------- | ----------------------------------------------------------------------------------- |
| **設計思想**        | standalone / artifact-less      | state machine 統合（`.steering/<task>/` / `Resume From` / Reviewer Lineage と連動） |
| **TDD**             | RED→GREEN→REFACTOR の純粋手順   | + AC ID Binding 必須 / `requirements.md` の AC と一体                               |
| **brainstorming**   | 要件の壁打ち                    | + Entry Intent / Approved Direction を state.md に永続化                            |
| **debug**           | root cause 特定までで完結       | + Phase 4 SMI block で ADR / Reviewer Lineage / Routing に波及                      |
| **implementation** | 純粋実装                        | + Spec Change Detection で adr / requirements / design を sync                      |

**使い分けの目安**:

- **standalone な探索** / artifact 不要な作業 → superpowers が軽くて速い
- **要件 → 実装 → review → PR の一貫した workflow** → GDD（state machine が連鎖を保証）
- **両方 install していてどちらでもいい場面** → `references/superpowers-overlap.md` の overlap map を参照
- **実例で挙動の差を見たい場合** → `docs/references-archive/worked-examples.md`（regression / security 変更 / flaky / amendment の 4 シナリオで superpowers / GDD を並記）

**同じ debug / brainstorm セッション内で両方を並行使用しない**（重複して時間が溶ける）。最初に 1 つ選ぶ。

---

## 所要時間の目安

所要時間は **検証・レビュー・差し戻し回数で大きく変わる**。以下は「既存コード調査が浅くない」「依存関係の取得で詰まらない」「レビュー指摘が追加設計を要求しない」場合の目安。表の値は **各工程が素直に進んだ場合** であり、要件整理・テスト失敗調査・PR レビュー修正まで常に含む保証時間ではない。

| タスクサイズ         | 例                             | AI 所要時間   | 人間の作業           |
| -------------------- | ------------------------------ | ------------- | -------------------- |
| **trivial**          | typo 修正、コメント追加        | **〜1 分**    | なし（ゲートなし）   |
| **quick (express)**  | 1 ファイルのバグ修正           | **15〜45 分**（要件レビューを含む） | 承認 1 回 |
| **quick (standard)** | 小規模な機能追加               | **15〜40 分** | 承認 1 回 |
| **standard**         | 複数ファイルにまたがる機能開発 | **45 分〜数時間**（段階 PR 化を推奨） | 承認 1 回 + 必要時だけ追加確認 |

タスクサイズは自動判定される。小さいタスクには小さいセレモニーしかかからない。

---

## 費用の目安

Claude Code では、GDD の reviewer・gate・Opus の相談役・難しい task の実装 worker は、Opus に固定している。Sonnet で動くのは、`Complexity: standard` の task の実装 worker と簡素化パスなど一部だけである（一覧の正本は `references/fixed-models.md`。Cursor・Codex は同じファイルの各 host の列のモデルで動く）。main セッションのモデルを Sonnet にしても、固定した agent は Opus で動く。

作者の環境で、正式 GDD を通ったタスクの 1 本あたりの費用（1 つの repo の 28 本、2026-10 前半、中央値、丸めた値）:

| タスク | 本数 | 1 タスク | うち gate（reviewer と gate runner） | うち main セッション |
| --- | --- | --- | --- | --- |
| 小（差分 1,200 行以下） | 16 | 約 $200 | 約 $110（1 本ごとの割合の中央値で約 6 割） | 約 $60 |
| 大（差分 1,200 行超） | 12 | 約 $600 | 約 $260（同じく約 4 割） | 約 $180 |

- 金額は、usage（subagent の advisor の分を含む）に API の公称単価（Opus 相当）を当てた換算で、請求とは照合していない。Sonnet で動いた分も Opus の単価で数えているので、実際より少し高く出る
- 測ったのは、費用を下げる変更（agent が advisor ツールを呼ばない、一部の reviewer の effort を下げる、簡素化パスを Sonnet にする、並行の相談を Opus 2 本にする、など）が入る前の構成である。今の構成では下がる見込みだが、測っていない
- 表は差分の行数で分けていて、タスクサイズ（quick / standard）では分けていない
- gate の費用は差分の行数にほぼ比例しない。31 本の両対数の傾きでは、行数が 10 倍でも gate の費用は約 2.8 倍だった。小さいタスクほど、1 行あたりは高くつく
- trivial は gate を通らないので、この表の外である
- Pro・Team などのサブスクリプションでは、金額を払うのではなく利用枠を消費する。上の金額は、タスクごとの消費の大きさを比べる目安として使う。Opus の比重が高いので、Sonnet だけで作業するより枠の減りは速い
  - 公式の資料（2026-10-30 に確かめた）では、Pro・Team でも Claude Code の既定のモデルは Opus（その時点の最新の版）で、利用枠（5 時間ごとと週ごと）は Claude と Claude Code で共有する。Claude Code v2.1.280 より前は、一部のプランの既定は Sonnet だった。枠の大きさはプランと seat で違う。数値は [Claude Code のモデルの設定](https://code.claude.com/docs/en/model-config)・[Pro・Max での使い方](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan)・[Team・Enterprise での使い方](https://support.claude.com/en/articles/11845131-use-claude-code-with-your-team-or-enterprise-plan) を見る
  - 作者の環境での例：利用枠の大きいプランでは、1 タスクを最後まで回せた。利用枠の小さいプランでは、2026-10 中旬ごろに、最初の human check の前に枠を使い切った。その後に入った費用を下げる変更の後に、枠の小さいプランで収まるかは確かめていない
  - 初めは小さいタスクを 1 本回し、`/status`（Pro・Max の公式の記事が、残りの枠を見るコマンドとして挙げている）で枠の減り方を見てから大きいタスクに進む。途中で枠が尽きたら、枠が戻った後に `/gdd-dev resume` で続ける
  - 組織の設定などで Opus を使えないとき、Opus に固定した agent がどう動くか（止まるか、別のモデルで動くか）は確かめていない。GDD の側では、相談役を起動できなければ人に止まり、別のモデルに替えない（`references/autonomy.md`）。軽いモデルへ自動で下げることもしない（`references/fixed-models.md`）。ほかの agent が Opus を使えずに起動に失敗したときの扱いは決めていない

最初の human check の承認の後の判断は、既定で Fable の相談役が決める（human check の「判断の委任」の既定が `Fable に任せる`。人に戻るのは、承認した要件を満たせない・満たさない方向に変えるときと、要件が決まらない・判定できないときと、自走上限などの許可の境界に当たるとき）。人に止めたいときは、最初の human check で `人に止める` を選ぶか、承認の後に会話で「人に止めて」と言う。ほかに Fable の相談役を起動するのは、利用者か利用する repo の規則が Fable を名指ししたとき（会話で Fable の意見を求める、など）である。Fable を起動できない環境では、そのときは相談せずに人に止まる。Fable の相談 1 本の費用は、作者の環境で約 $3.6 だった（2026-11-13、4 件の試し）。

advisor ツール（Claude Code の `/advisor`）は、GDD の agent からは呼ばないよう agent の定義に書いている（散文の指示で、仕組みでは止めていない）。main セッションの advisor は利用者の設定のままである。Anthropic の公式の資料（2026-10 時点の [Optimizing for cost and intelligence](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence)）では、Opus（high）に Fable の advisor を付けた構成は、Anthropic 社内の agentic coding のベンチマークで単独より 1.7 点（回ごとのぶれの境目）上がり、費用は約 2.1 倍だった。作者の環境では、advisor が難しい task の実装 worker の費用の約 36% を占めていた。費用を抑えたいときは `/advisor off` で切れる（[advisor の資料](https://code.claude.com/docs/en/advisor)）。

---

## クイックスタート

### Step 1: まず 1 回動かす（3分）

```
/gdd-dev ユーザー一覧画面にページネーションを追加したい
```

これだけで以下が自動的に進む:

1. **要件整理** — AI が質問を自己解決し、人間に聞くべき点だけまとめる
2. **AI レビュー** — 要件の完全性・AC 品質を自動チェック
3. **人間確認** — ここで初めて止まる。各承認ポイントの **背景** と **変更前→変更後** を見て OK / 別案希望 を答えるだけ。**方向性承認** で AI の自走範囲も合意
4. **設計 → TDD → 実装 → レビュー → PR** — 承認後は完了まで自動。E2E で発見された問題は方向性の範囲内なら AI が自律判断（E2E Discovery Loop）

タスクの大きさ（trivial / quick / standard）は自動判定される。

**初回の成功条件**: 人間確認（human check）まで辿れること。承認後の自動フローは 2 回目以降で慣れればよい。

### Step 2: 使い分けを覚える（翌日〜）

| やりたいこと         | コマンド                                    | 所要時間の目安               |
| -------------------- | ------------------------------------------- | ---------------------------- |
| typo 修正            | `/gdd-dev README の typo を修正`            | 1 分（trivial: ゲートなし）  |
| 1 ファイルのバグ修正 | `/gdd-dev --express リダイレクトバグを修正` | 15-45 分（express: 要件レビューを含む） |
| 小〜中規模の機能追加 | `/gdd-dev 通知設定の API を追加したい`      | 15-40 分（quick/standard）   |
| 中断した task を再開 | `/gdd-dev resume` または `/gdd-dev 再開`    | 候補から選択                 |
| まず相談したい       | そのまま会話する                            | 制限なし（artifact なし）    |
| 現在地の確認         | `gdd-status`                                | 即時                         |

### Step 3: チームに広げる（1 週間〜）

1. チーム外展開キットを読む — `docs/TEAM_ROLLOUT.md` で導入判断・HITL・worktree / resume・superpowers 共存・成功指標を確認
2. 運用レベルを選ぶ — `references/operation-levels.md` で strict / standard / light を比較
3. チーム導入ガイドを読む — `docs/references-archive/team-onboarding.md`
4. 実績データを確認する — `gdd-metrics` で gate 通過率・差し戻し率を可視化

---

## メンタルモデル

GDD が管理する4つのファイルと、その役割:

```
.steering/<task-name>/
├── requirements.md   ... 何を作るか（要件・受入条件）    ← 人間が承認する正本
├── design.md         ... どう作るか（設計・技術選定）    ← AI が具体化
├── tasklist.md       ... いつ何をするか（タスク・進捗）  ← build の routing source
└── state.md          ... 今どこか（gate status・再開先） ← planning の routing source
```

`state.md` は最小限の routing / context だけを持つ。詳細な履歴は worklog.md / adr.md / findings.md に分ける。保存先の考え方は `references/state-field-tiers.md`、どの文書が何の正本かは `references/source-of-truth-map.md` を参照。

**用語集**:
| 用語 | 意味 |
|------|------|
| gate | 次の工程に進む前の自動チェックポイント |
| human check | 人間の承認が必要な唯一の停止点 |
| fail-closed | 曖昧なら止まる。勝手に進まない |
| steering | `.steering/` 配下の正本ファイル群 |
| workflow artifact | steering 内の requirements.md / design.md / tasklist.md / state.md |
| worktree | git worktree による作業分離 |

### 工程フロー

```
相談・壁打ち（成果物なし）
    |  /gdd-dev
    v
要件整理 → AI レビュー → 人間確認 → 設計 → 設計レビュー
    |                                          |
    v                                          v
タスク分割 → テスト作成(RED) → 実装(GREEN) → 実装レビュー
    |                                          | 差し戻し
    v                                          v
完了チェック → PR 作成 → done          デバッグ → 再実装
```

---

## 導入

### 前提

| 必要なもの | 用途 | 無いとき |
| --- | --- | --- |
| bash | hook の起動 script | hook が動かない |
| git | worktree での作業の分離、push・merge の確認 | GDD の工程を進められない |
| Python 3 | hook と `scripts/` の判定 | hook の多くが判定できない |
| GitHub CLI（`gh`。ログイン済み） | PR の作成・PR の有無の確認・CI の確認 | PR まわりの確認ができない。PR の有無を確かめられないときは「判定できない」として扱い、PR が無いとは読まない |

- PR の工程は GitHub を前提にしている。ほかのホスティングでは PR まわりの確認が働かない
- 動作を確かめているのは macOS と Linux だけで、Windows では確かめていない

確かめている版と、版で変わること:

| もの | 確かめている版 | 版で変わること |
| --- | --- | --- |
| Python | 3.14（CI） | 3.11 より古いと、hook が起動する子の python が、利用者の repo の module（`json.py` など）を先に読むことがある（`PYTHONSAFEPATH` が効かない）。3.14 より古い版で動くかは確かめていない |
| git | 2.54（作者の環境）。worktree の検査は 2.50.1 でも確かめた | 設定で足す hook（`hook.<name>.*`）に対応しない git では、push の記録（[§ インストールすると変わること](#インストールすると変わること) の「記録だけ」）が何もしない。既存の pre-push hook（`.git/hooks`・husky）とは並んで動く（2.54 で確かめた）。必要な最低版は確かめていない |
| GitHub CLI | 2.93・2.95（作者の環境） | ほかの版は確かめていない。`gh pr merge` などの flag の解釈は 2.93 の `--help` に合わせている |

### 環境別セットアップ

| 環境                      | コマンド                                    | hooks                       | 備考                                   |
| ------------------------- | ------------------------------------------- | --------------------------- | -------------------------------------- |
| **Claude Code** (marketplace) | `/plugin marketplace add yamaguchi-tk/gate-driven-development` → `/plugin install gate-driven-development@gate-driven-development` | 自動有効 | 推奨 |
| **Claude Code** (plugin)  | `claude --plugin-dir <path>`                | 自動有効                    | 推奨                                   |
| **Claude Code** (symlink) | `bash scripts/install-claude-code-links.sh` | 自動有効                    | 解除: `uninstall-claude-code-links.sh` |
| **Cursor** (symlink)      | `bash scripts/install-cursor-links.sh`      | manifest 経由で有効化が必要 | 詳細: `references/cursor-guide.md`     |
| **Cursor** (hooks なし)   | 同上                                        | 手動で phase 間を指示       | Autonomous Continuation 不可           |
| **Codex** (plugin)        | `.codex-plugin/plugin.json`                 | hooks.json を manifest で公開 | 詳細: `references/codex.md`            |

- dry-run: 各 install script に `--dry-run` を付ける
- 検証: `bash tests/validate-plugin.sh`

### モデル選択

Claude Code では、main のセッションを Opus にして使う。main が Sonnet・Haiku だと、GDD の始まり（`/gdd-dev`・`/gdd-resume` の Skill の呼び出し、`setup-gdd-loop.sh` の実行、手動の手順で、active でない `.claude/gdd-dev.local.md` に書く Write・Edit）を止める（セッションの開始か、相談の段の返事の後に、セッションにつき 1 回知らせる）。2026-10-19〜10-30 の実測で、人が確認で作り直しを求めた率が main が Sonnet で 6/13、Opus で 2/56 だったため。Opus を使えないときは、`settings.json` の `env` に `GDD_ALLOW_NON_OPUS_MAIN=1` を設定すると外せる（`setup-gdd-loop.sh` は settings のファイルの env だけを読むので、シェルで export した値やコマンドの前に付けた値では外れない）。モデルは、Skill を呼んだ返事・`setup-gdd-loop.sh` を実行した返事の行を transcript から読む（`setup-gdd-loop.sh` は script の中で判定するので、どう包んで実行しても判定し、読むだけでは判定しない）。transcript は遅れて書かれることがあり、今の返事の行が読めないときは前の返事のモデルで判定する。このときに止めたら、止める文が、画面でモデルを切り替えた直後なら一言送ってからやり直すよう案内する。モデルを判定できないときは止めない。

どの工程・agent がどのモデルと effort で動くかの正本は `references/fixed-models.md`（Claude Code・Cursor・Codex の列）。agent ごとの値は `agents/*.md` の frontmatter（`model`・`effort`）にある。選び方の手順は `skills/gdd-model-routing/SKILL.md`。Opus と Sonnet の配分の要約は [§ 費用の目安](#費用の目安) に書き、agent ごとの一覧は写さない。

### 初回の目標

**人間確認（human check）まで辿れること**。承認後の自動フローは初回以降で慣れればよい。

```
/gdd-dev 通知設定の CRUD API を追加したい
```

→ AI が要件を整理 → AI レビュー → **ここで止まる** → OK と答えれば先に進む

---

## 役割別ガイド

### 開発者

1. `/gdd-dev <やりたいこと>` で開始
2. 人間確認で要件を承認
3. 実装は AI が自動で進める。差し戻しがあれば通知される
4. `done` で PR が作成される

ユーザーが覚える入口は 3 つだけ:

- `/gdd-dev <タスク>` — formal workflow 開始
- `gdd-status` — 現在地の確認
- `gdd-pr-review` — PR / 差分レビュー

補足:
- `/gdd-dev 再開` / `/gdd-dev resume` — 中断したタスクの候補を出して選ぶ
- `/gdd-dev`（空プロンプト） — 新規/再開を決められないため fail-closed し、resume 候補を提示
- 壁打ちしたい → そのまま会話。formal workflow に入る時だけ `/gdd-dev <タスク>` に切り替える
- 1 つのセッションで進めるタスクは 1 つにする（推奨。強制はしない）。ここでいうタスクは、`/gdd-dev <タスク>` で始める別の依頼を指す。同じ計画の後続 Stage（「次に進んで」）は、今までどおり同じチャットで続ける。別のタスクは、どのタスクも使っていない checkout（新しく作った worktree など）で開いた別のセッションで `/gdd-dev <タスク>` から始める。Claude Code では、同じ checkout だと、前のセッションの `/gdd-dev` が終わる（done・cancelled など）まで、新しい `/gdd-dev` が `gdd loop is already active in another session.` で止まる（解除の仕方は `docs/TROUBLESHOOTING.md`）。セッション ID を渡さない runtime（Cursor など）では止まらず、前のセッションの `.claude/gdd-dev.local.md` を上書きする。同じセッションで複数のタスクを並行しても順に進めても、前のタスクの文脈が残って大きくなり、呼び出しごとの費用と compaction の回数が増える

### 再開候補を探すタイミング

GDD は worktree-first なので、別 worktree の途中タスクを通常チャットへ自動で混ぜない。

resume 候補を列挙するのは次の 2 パターンだけ:

1. `/gdd-dev resume ...` / `/gdd-dev 再開 ...` のように、ユーザーが再開を明示したとき
2. `/gdd-dev` を空プロンプトで実行し、新規開始か再開かを人間に確認する必要があるとき

通常チャット開始時や `/gdd-dev <具体的な新規タスク>` では、別 worktree の途中 task は探さない。現在 worktree に active GDD がある場合だけ、その worktree の state を復元する。

binding / state / worktree の 3 層は内部実装として扱う。ユーザーは通常それを理解する必要はない。resume が不整合で止まった場合は、まず `gdd-status` で候補と次の1アクションを確認し、必要なら `/gdd-dev resume <候補>` または `/gdd-resume <continuation-id>` を使う。

### レビュワー

- AI reviewer が先にチェック済みの状態で PR が来る
- `gdd-pr-review` で差分チェックを依頼できる
- reviewer agent の指摘は `state.md` / `tasklist.md` に記録されている

### テックリード

- 運用レベル（strict / standard / light）をリポジトリ単位で設定可能
- `references/operation-levels.md` で詳細を確認
- `evals/evals.json` でトリガー精度を評価できる

### PM

- 人間確認ポイント（human check）で要件の承認・却下ができる
- `requirements.md` の `承認ポイント` が判断すべき内容
- 工程の進捗は `gdd-status` で確認可能
- 初回は `docs/NON_ENGINEER_APPROVER_HANDOUT.md` を先に読み、必要な場合だけ `docs/NON_ENGINEER_HITL_GUIDE.md` で詳しい読み方を確認する

---

## タスクサイズの自動判定

| サイズ               | 例                                        | 工程                                                          |
| -------------------- | ----------------------------------------- | ------------------------------------------------------------- |
| **trivial**          | typo 修正、コメント修正                   | そのまま修正 → commit（ゲートなし）                           |
| **quick (express)**  | 1-2ファイルのバグ修正、方針が明白な変更   | 要件整理 → AI レビュー → 人間確認 → TDD → 実装 → レビュー → done（最短） |
| **quick (standard)** | 3-5ファイルの機能追加、設定値変更         | 要件 → AI レビュー → 人間確認 → 設計 → 実装 → レビュー → done |
| **standard**         | 大規模変更、外部API接続、セキュリティ変更 | フル工程 + specialist reviewer                                |

Express は `--express` で明示指定もできる: `/gdd-dev --express リダイレクトバグを修正`

### パスの分岐フロー

```
ユーザー入力
    │
    ├─ behavior change なし？ ──→ trivial（ゲートなし → commit）
    │
    ├─ 1-2 ファイル & AC 1-3 個？ ──→ quick (express)
    │       │
    │       ├─ Direct Intent 3点以上？ ──→ Express + Direct Intent（最速パス）
    │       │       要件作成 → AI review → human check → TDD → 実装 → impl review → done
    │       │
    │       └─ Direct Intent 2点以下 ──→ Express（通常）
    │               要件作成 → AI review → human check → TDD → 実装 → impl review → done
    │
    ├─ 3-5 ファイル？ ──→ quick (standard)
    │       要件 → AI review → human check → 設計 → TDD → 実装 → impl review → done
    │
    └─ 6+ ファイル or security 変更？ ──→ standard
            要件 → AI review → human check → 設計 → タスク分割 → TDD → 実装 → impl review → completion → done
```

### Direct Intent スコアの計算例

| 条件                           | 点数 |
| ------------------------------ | ---- |
| 変更対象ファイルが明示         | +2   |
| 関数名・コンポーネント名が明示 | +1   |
| アクションが動詞 1 語で完結    | +1   |
| 疑問文・相談形でない           | +1   |
| AC が 2 個以下                 | +1   |
| standard タスク                | -3   |

**例 1**: `/gdd-dev src/api/users.ts の validateInput にメール形式チェックを追加`
→ ファイル明示(+2) + 関数名明示(+1) + 動詞「追加」(+1) + 疑問文でない(+1) + AC 1個(+1) = **6点** → Direct Intent

**例 2**: `/gdd-dev ログイン画面にパスワードリセット機能を追加したい`
→ ファイル不明(0) + コンポーネント不明(0) + 動詞「追加」(+1) + 疑問文でない(+1) + AC不明(0) = **2点** → 通常フロー

**例 3**: `/gdd-dev 認証周りのリファクタリングってどう進めるのがいいかな？`
→ ファイル不明(0) + 関数不明(0) + 動詞不明(0) + 疑問文(-0) + AC不明(0) = **0点** → 通常フロー（相談形なので `gdd-pre-workflow-brainstorming` が適切）

詳細: `references/task-sizing.md`

---

## Skill Catalog

### User Entry Points（覚える入口は 3 つ）

| 入口 | 役割 | 起動方法 |
| ---- | ---- | -------- |
| `/gdd-dev` | 要件整理から PR までの formal workflow | `/gdd-dev <タスク>` / `/gdd-dev resume` |
| `gdd-status` | 現在地、停止理由、resume 候補の確認 | 「今どこ？」「status」 |
| `gdd-pr-review` | PR / 差分レビュー | 「PR レビュー」「差分チェック」 |

その他の skill は、原則として GDD state machine または上記入口から自動で呼ばれる。ユーザーが個別 skill 名を覚える必要はない。

### Specialized Entry / Advanced

| Skill                            | 役割                            | 起動方法                               |
| -------------------------------- | ------------------------------- | -------------------------------------- |
| `gdd-brainstorming`              | formal workflow の起点          | `/gdd-dev <task>`                      |
| `gdd-pre-workflow-brainstorming` | 相談専用レーン（artifact なし） | 「壁打ちしたい」「要件から整理したい」 |
| `gdd-pr-review`                  | PR レビュー                     | 「PR レビュー」「差分チェック」        |
| `gdd-test-failure-debug-pack`    | test failure の structured pack | 「テストが落ちた」                     |
| `gdd-status`                     | 現在 phase の確認               | 「今どこ？」「status」                 |
| `gdd-metrics`                    | ワークフロー実績の可視化        | 「metrics」「実績」「gate通過率」      |
| `gdd-refactor-planning`          | completion 後のリファクタ計画   | 「リファクタしたい」「整理したい」     |

### Internal Routing（state machine が自動遷移）

| Skill                                | 役割                                     |
| ------------------------------------ | ---------------------------------------- |
| `gdd-requirements-gating`            | requirements reviewer gate → human check |
| `gdd-design-gating`                  | detailed design gate                     |
| `gdd-task-breakdown`                 | 承認済み設計からタスク分解               |
| `gdd-test-driven-development`        | RED（failing test）の準備                |
| `gdd-subagent-driven-implementation` | 実装（GREEN + REFACTOR）                 |
| `gdd-implementation-gating`          | 実装レビュー gate                        |
| `gdd-systematic-debugging`           | failure の根本原因切り分け               |
| `gdd-completion-check`               | 最終 gate（AC 検証 + 包括レビュー）      |

### Helper

| Skill                        | 役割                                             |
| ---------------------------- | ------------------------------------------------ |
| `gdd-using-git-worktrees`    | worktree helper（preparation / guard / cleanup） |
| `gdd-requesting-code-review` | companion review の明示起動                      |
| `gdd-receiving-code-review`  | companion review 指摘の検証                      |
| `gdd-model-routing`          | モデル選択ルール                                 |

---

## Reviewer Agents

gate で起動する reviewer は次のとおり。ほかの agent（phase の runner・実装の worker・独立レビュー・判断の相談役など）は `agents/` にあり、役割と起動元は各定義の `description` に書いてある。

| Agent                         | 役割                                               | 起動条件                                 |
| ----------------------------- | -------------------------------------------------- | ---------------------------------------- |
| `gdd-planning-reviewer`       | 要件の完全性・AC 品質・設計の一貫性・実現可能性    | requirements/design gate で常時          |
| `gdd-implementation-reviewer` | バグ・保守性・AC 準拠・契約遵守・信頼性・性能      | implementation gate で常時               |
| `gdd-security-reviewer`       | セキュリティ・secrets・trust boundary              | 条件起動（auth/secrets/untrusted input） |
| `gdd-completion-reviewer`     | 最終横断レビュー・コード品質・cross-cutting リスク | completion check（standard のみ）        |

---

## Contract Sources（正本）

| 正本                                     | 内容                                                          |
| ---------------------------------------- | ------------------------------------------------------------- |
| `references/contract-overview.md`        | 自己完結条件の概要                                            |
| `references/source-of-truth-map.md`      | どの文書が何を決めるかの正本マップ                            |
| `references/self-contained-contract.md`  | 自己完結条件の詳細ルール                                      |
| `references/state-machine-overview.md`   | state field と phase flow の概要                              |
| `references/state-machine.md`            | 詳細な遷移表、active steering 決定規則                        |
| `references/state-field-tiers.md`        | state.md は最小限、詳細な履歴は worklog.md / adr.md に分ける保存先ルール |
| `references/operation-levels.md`         | 運用レベル（strict / standard / light）                       |
| `references/reviewer-selection.md`       | reviewer 選定ルール                                           |
| `references/entry-intent.md`             | entry intent 解決ルール                                       |
| `references/phase-progression.md`        | phase 進行ルール                                              |
| `references/context-budget.md`           | Phase Context Manifest、Handoff Summary、Context Health Check |
| `references/output-format.md`            | phase 遷移ヘッダー、進捗バー、Context Handoff Summary         |
| `references/task-sizing.md`              | trivial / quick / standard の判定基準                         |
| `references/rollback-patterns.md`        | 差し戻し時の Gate Status 更新パターン                         |
| `references/inline-review-checklists.md` | implementation-gating のインラインレビュー用チェックリスト    |
| `references/cursor-guide.md`             | Cursor 環境の差分・制約・導入手順                             |
| `references/onboarding.md`               | 初回利用の最短シナリオ                                        |
| `references/faq.md`                      | よくある詰まりどころと解決方法                                |
| `docs/references-archive/team-onboarding.md`          | チーム導入ガイド                                              |

---

## Plugin Structure

```
gate-driven-development/
├── .claude-plugin/plugin.json    # Claude Code manifest
├── .cursor-plugin/plugin.json    # Cursor manifest
├── .codex-plugin/plugin.json     # Codex manifest
├── commands/gdd-dev.md         # canonical entrypoint
├── hooks/
│   ├── hooks.json                # hook 定義（UserPromptSubmit / UserPromptExpansion / SessionStart /
│                                 #   PreCompact / Stop / StopFailure / Notification / PreToolUse）
│   └── scripts/                  # hook scripts
├── skills/                       # phase skill 群
├── agents/                       # reviewer agent 群、phase runner（gdd-formal-gate-runner / gdd-light-task-runner）、実装 worker（gdd-implementation-worker / -heavy / gdd-remediation-worker）、マージ後の QA（gdd-qa-runner）、判断の相談役（gdd-opus-advisor / gdd-opus-advisor-max / gdd-fable-advisor）、着手前の突き合わせ（gdd-request-code-crosscheck）、指摘の検証役（gdd-finding-verifier）
├── references/                   # 正本文書群
├── scripts/                      # ユーティリティ
├── evals/evals.json              # trigger 評価ケース
├── tests/validate-plugin.sh      # 自己検証スクリプト
├── CHANGELOG.md                  # 最近の release（古い節は archive へ）
├── CHANGELOG-archive.md          # 過去の release 節
├── CHANGELOG-archive-2.md        # さらに古い release 節
├── CHANGELOG-archive-3.md        # 0.40.3 〜 0.38.0 の release 節
├── CHANGELOG-archive-4.md        # 0.40.15 〜 0.40.4 の release 節
├── changelog.d/                  # PR ごとの変更断片（リリースで CHANGELOG.md に集める）
└── README.md
```

## Hooks

`hooks/hooks.json` で以下の 8 種類の hook を定義。Stop hook は `.claude/gdd-dev.local.md` と連携して Autonomous Continuation を実現する。**この表と `hooks.json` の event 集合の一致は `tests/test_hooks_wiring_new_events_contract.py` が機械検査する**（手書きの一覧は黙ってずれるため）:

| hook                 | 役割                                                                 |
| -------------------- | -------------------------------------------------------------------- |
| **UserPromptSubmit** | ユーザー入力時に AC 詳細を補助注入 |
| **UserPromptExpansion** | `superpowers` 側の `writing-plans` / `executing-plans` / `brainstorming` の直接起動を **block** する（active GDD skill があるとき）。直接打った `/gdd-dev`・`/gdd-resume` は、ここでは判定しない（main-model-gate は返事の中の Skill の呼び出しと、`setup-gdd-loop.sh` の中で判定する） |
| **SessionStart**     | main が Sonnet・Haiku と分かれば（payload の model だけ。env と settings の既定と、再開時の transcript は、Desktop で実際のモデルと食い違うので使わない）、Opus への切り替えを知らせる（Stop と合わせてセッションにつき 1 回）。現在 worktree の active steering だけ Quick Reboot 情報を注入（compaction の直後は何も出さない）。**前回ターンが API エラー等で異常終了していれば、`StopFailure` が残した記録を 1 度だけ報告して消費する**（記録は project 一致時のみ注入し、解釈できない記録は fail-closed で削除）。**PR がある branch への push が、レビューの済んだ tip かを git の pre-push hook でログに書く**（`$CLAUDE_ENV_FILE` で差し込む。log-only で push は止めない） |
| **PreCompact**       | context 圧縮の直前に、GDD の状態（state.md の場所と、Resume From・Next Action。build 中の Next Action は tasklist.md が先）を要約器へ渡す。local state の session が現在の session と違うときは渡さない（local state が無いときと、session id が取れない runtime では照合しない）。state.md には書かない |
| **Stop**             | `<gdd-stop>` 以外の停止を block し、Autonomous Continuation を実現（background の dispatch を待つ間は目印なしで turn を終えてよい。background の返りは tool result ではないので、その marker は本文に書く。その間に loop state を消す停止と、期限 timer の無い・期限切れの reviewer・gate-runner の待ちは block） |
| **Stop（依頼との差）** | human check の提示のときだけ、ユーザーの発言と提示の本文を `claude -p`（Opus・ツールなし・hook なし）に渡し、推奨どおりに進めたときに発言がどうなるかを照らし、外れるか届かなければ `依頼との差（変わる）: <発言> → <推奨>` と `依頼との差（満たせない）: <発言>（別の案: あり）` を、種類ごとに 1 行、最大 2 行で `systemMessage` に出す（残りは件数を添える）。差の表示は止めず、main に書き直させない。動かなければ何も出さない。その前に、判断ポイントの `依頼との差:` の欄とマーカー直前のタグを、承認の書き込みの検査と同じ判定（欄が読めない・タグが無い・タグが読めない・なし以外の点がある）で見て、当たれば `claude -p` を起動せずに block し、ユーザーが答える前に確認の全文を出し直させる（同じ人の発言のターンで 3 回まで。なし以外のときは、狭める案を採用しない案として並べさせる。その後は止めずに、そのまま答えてよいこと・狭める点は名指しで答えることと、hook が見た行を人に知らせる。人の返事の後は、確認を出し直さず、欄とタグだけを直し返事を `decided` に引いた補正〔`<gdd-hitl-fields correction ...>`〕で承認を書く）。理由を含む結果は `~/.claude/.gdd-hook-state/request-diff.log` に残す。`GDD_SKIP_REQUEST_DIFF=1` で `claude -p` の照合だけを切れる（欄の検査は切れない）。1 回あたり約 $0.03（過去の 70 件） |
| **Stop（main のモデル）** | main が Sonnet・Haiku なら、返事の後に Opus への切り替えをセッションにつき 1 回知らせる（止めない） |
| **StopFailure**      | API エラーでターンが終了したとき、永続ファイルに記録し次回 SessionStart で報告する（`Stop` は API エラー時に発火しないため別イベント）。block しない |
| **Notification**     | idle / permission 待ちの入力待ち通知。block しない（decision control を使わない） |
| **PreToolUse**       | 7 matcher / 17 hook。Write/Edit 前に Goal + AC を注入するほか、**block するゲート** —— `.steering/` への書き込み / plan mode / worktree 進入 / Skill 起動 / `Bash`（worktree command guard）。**この plugin が plan mode を止めているのはこのイベント**。`Bash` の pre-PR gate・pre-push gate・merge gate は止めずに、不足を実行後に通知する（`Agent` matcher には additionalContext のみで block しない agent-dispatch-model-gate と、main からの gate-runner の同期起動を deny する background-dispatch-gate、`Bash` matcher にはこの他、block しない review-followup-nudge-hook と、GDD active を問わず background の待ちのループ（until・while・for と sleep、`--watch`、`gh run watch`）を deny して `scripts/wait-until.py` で待たせる wait-loop-gate、`Skill` matcher にはこの他、block しない gate-skill-dispatch-nudge-hook がある。`Skill|Write|Edit|MultiEdit` matcher には、返事をしている main が Sonnet・Haiku のときに gdd-dev・gdd-resume の Skill と、手動の手順で run を始める `.claude/gdd-dev.local.md` への書き込み（ディスクのファイルが active でないときの書き込み。書く内容は見ない）を毎回 deny する main-model-gate がある（`setup-gdd-loop.sh` も、同じ判定を script の中で行い、止めるときは 1 で終わる。どの段でモデルを決めたかを state dir の `main-model-gate.log` に書く）。`Agent` matcher にはさらに、依頼と既存コードの突き合わせ agent の起動のときに、まだ無い `request.md` を main の transcript のユーザーの発言で作る request-capture-hook がある。block しない） |

SessionStart hook は別 worktree の途中 task を自動検出・自動再開しない。別 worktree の resume 候補探索は `/gdd-dev resume ...` または空プロンプト `/gdd-dev` の明示実行時だけ `setup-gdd-loop.sh` が行う。現在 task の identity は `.gdd/tasks/<task_id>/binding.json` と current worktree / branch の一致で解決し、自然文や session id だけでは決めない。

## 主要コンセプト

### Planning

- `Summary Brief`: 要件の一言要約。`<対象>に対して<目的>を実施する` の形式で、`確定事項` / `未確定事項` / `やらないこと` / `外部依存の確認結果` を判断材料として添える
- `Problem Discovery` + `Options Exploration`: 既存コード・環境の具体的事実を確認し、候補案を比較してから承認ポイントに落とす
- `Design Policy Discussion`: 設計方針の候補整理。採用案と非採用案を比較記録する
- `Approved Direction`: human check 承認後に方向性と自走範囲を `state.md` に記録。E2E 発見の問題は自走範囲内なら AI が自律判断
- lightweight `design.md` skeleton: human check 前に用意する設計の骨格。detailed design は design gate 後に AI が具体化する
- `Latest Tech Context`: version-sensitive な利用技術の最新情報。`tech-docs-searcher` 等で確認し、design.md に残す

### Build

- `Implementation Reviewer Selection`: task 単位の reviewer 選定記録。`tasklist.md` に保存
- `ops-blocking medium`: 運用に影響する medium 以上の指摘。blind loop 防止に使用

### Remediation

- `E2E Discovery Loop`: `Approved Direction` の自走範囲内かつ AC を壊さない変更は、human check に戻さず AI が自律判断。`Scope Drift Guard` で累積変更を監視（詳細は `references/phase-progression.md`）

### Completion & Routing

- 停止時の構造化出力: `参照した正本` / `停止理由` / `次の1アクション` と、`<gdd-stop>` の後の `## 👤 次にすること`（`cancelled` を除く）を必ず返す
- `Plan mode` との関係: Plan mode は「計画を立てる」までは得意だが、実行・中断再開・停止条件・レビューゲートは持たない。GDD はそこを補完する。Plan mode の計画をそのまま使いたい場合は `.cursor/plans/*.plan.md` を optional artifact として参照できるが、GDD の state machine が正本

### Resume

- `legacy migration`: worktree 移行前の root steering を worktree 側にコピーする仕組み
- `Task Binding Registry`: `.gdd/tasks/<task_id>/binding.json` に worktree / branch / steering path を保存し、自然文 resume / status の混線を防ぐ仕組み。root 側 `.steering` は diagnostic / migration source のみで current task にはしない

## Scripts

| Script                         | 用途                                             |
| ------------------------------ | ------------------------------------------------ |
| `scripts/gdd_task_binding.py`  | Task Binding Registry の作成・解決               |
| `scripts/resolve-gdd-model.py` | runtime / phase / text からモデルを自動選択      |
| `scripts/run-with-plugin.sh`   | plugin 付きで Claude Code を起動                 |
| `scripts/suggest-task-size.sh` | キーワード・diff ベースのタスクサイズ自動提案    |
| `scripts/setup-gdd-loop.sh`    | Stop hook 用の `.claude/gdd-dev.local.md` を生成 |
| `scripts/wait-until.py`       | 処理待ち（CI・デプロイなど）を上限つきで待つ。条件の終了コードは 0 = 成立 / 1 = まだ / それ以外 = 壊れている（exit 2）、期限切れは exit 124。引数の誤りも exit 2、シグナルで止められたら 128 + 番号 |

## 検証

- `tests/validate-plugin.sh`: 必須ファイル・manifest・frontmatter・最小契約トークンの確認。`grading-summary.json` の schema 検証も含む
- `evals/evals.json`: trigger 精度や handoff の評価ケース

## 他チーム導入向けドキュメント（`docs/`）

plugin 内部の正本（`references/`）とは別に、他チーム展開時の読み物を `docs/` に集約している。

| ドキュメント                         | 目的                                                                |
| ------------------------------------ | ------------------------------------------------------------------- |
| `docs/ONBOARDING.md`                 | 30 分で `/gdd-dev` 1 サイクルを完走できる導入シナリオ               |
| `docs/CI_GUARDS.md`                  | 導入先 repo の CI で raw task `.steering/<task>/` 混入を止める設定例 |
| `docs/DISTRIBUTION_READINESS.md`     | 広めの配布前に見る PR 分割・除外・検証 evidence のチェックリスト     |
| `docs/NON_ENGINEER_APPROVER_HANDOUT.md` | PM / PO / 業務担当へそのまま共有する承認者向け 1 ページ配布文       |
| `docs/NON_ENGINEER_HITL_GUIDE.md`    | 非エンジニア承認者が HITL で見る欄・返答例・差し戻し条件            |
| `docs/TROUBLESHOOTING.md`            | 停止パターン別の原因と復帰手順。復帰コマンド早見表付き              |
| `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` | 導入プロジェクトの運用設定雛形（必須項目 + 推奨フルセット）         |
| `docs/SECURITY.md`                   | skill / reviewer / subagent / hook の権限境界、脅威モデル、監査証跡 |
| `docs/VERSIONING.md`                 | v0.x → v1.0 昇格基準、Breaking Change 分類、SemVer 適用ルール       |
| `docs/SUPERPOWERS_COEXISTENCE.md`    | superpowers との役割分担・衝突回避・使い分けガイド                  |
| `docs/METRICS_BASELINE.md`           | `gdd-metrics` の KPI しきい値と赤信号指標                           |

plugin 内部開発者向け: `CONTRIBUTING.md`

## 変更履歴

`CHANGELOG.md` を参照。古い release 節は `CHANGELOG-archive.md` / `CHANGELOG-archive-2.md` / `CHANGELOG-archive-3.md` / `CHANGELOG-archive-4.md` にある（同ファイル `## Archive` の案内から辿れる）。
