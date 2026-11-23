# SUPERPOWERS 共存ガイド

> **対象**: `gate-driven-development` と `superpowers` の両 plugin を有効化しているチーム
> **目的**: skill 名衝突・auto-trigger 重複・役割重複を整理し、使い分けルールを明文化する
> **上位正本**: `skills/gdd-using-skills/SKILL.md`（1% ルール・スキル呼び出し優先順位）
> **この文書の位置付け**: 「どちらを使えばいいか迷う」瞬間に迷わないための判断表

---

## なぜ両方有効なのか

- **GDD**: 要件整理 → 設計 → TDD → 実装 → レビュー → PR を gate 付きで一気通貫する **formal workflow orchestrator**
- **superpowers**: brainstorming / debugging / TDD / plan 等を個別に提供する **個別 skill 集合**

GDD は superpowers の知見（v5.0.7 の testing-anti-patterns、verification-before-completion、subagent-driven-development 等）を取り込みつつ、formal workflow としてまとめている。**両方残っているのは、単発タスクには superpowers の軽量さが適するケースがあるため**。

---

## 基本原則

1. **formal workflow は `/gdd-dev` で入る**（GDD）
2. **単発・experimental・探索は superpowers を使う**
3. **skill 名衝突時は GDD 優先**（`gdd-*` prefix の有無で判別）
4. **自動判定は `gdd-using-skills` が行う**（セッション開始時）
5. **SessionStart hook が superpowers 共存を検出した場合、GDD は auto-trigger を抑制**（conflict 回避のため）
6. **active GDD 中は GDD primary**。superpowers は `superpowers advisory only` として補助 reference / 比較材料に限定する
7. **GDD Workflow Lock**: active GDD 中は GDD remains the state owner。`state.md / tasklist.md / worklog.md` を正本にし、No direct superpowers workflow handoff を守る

---

## 重複する skill 対応表

superpowers の skill は prefix なし、GDD は `gdd-` prefix。名前衝突はないが、**役割重複**がある。

| superpowers skill | GDD skill | 使い分け |
|-------------------|-----------|---------|
| `brainstorming` | `gdd-brainstorming` / `gdd-pre-workflow-brainstorming` | formal workflow や GDD 文脈の壁打ちは GDD。GDD 文脈なしの壁打ちだけなら superpowers でも可 |
| `test-driven-development` | `gdd-test-driven-development` | formal workflow の一部なら GDD、単発 TDD なら superpowers |
| `systematic-debugging` | `gdd-systematic-debugging` | gate で findings が出たら GDD、単発バグ調査なら superpowers |
| `subagent-driven-development` | `gdd-subagent-driven-implementation` | formal workflow なら GDD。superpowers は単発 implementation |
| `verification-before-completion` | （GDD は `references/verification-before-completion.md` として吸収） | GDD 内部では参照、superpowers は独立 skill |
| `using-git-worktrees` | `gdd-using-git-worktrees` | GDD の cleanup / cancel 手順は GDD 側で統合済み。worktree 操作の単独利用は superpowers でも可 |
| `requesting-code-review` | `gdd-requesting-code-review` | companion review は GDD を使う（reviewer との契約が明確） |
| `receiving-code-review` | `gdd-receiving-code-review` | 同上 |
| `finishing-a-development-branch` | `gdd-completion-check`（Post-Completion 4 Options Flow） | GDD に取り込み済み。superpowers は単発利用 |
| `writing-plans` / `executing-plans` | （GDD は `/gdd-dev` 経由、Plan mode は hook で deny） | GDD フロー中は Plan mode 不可。単発タスクだけ superpowers |
| `dispatching-parallel-agents` | `gdd-subagent-driven-implementation` の Multi-task Parallel Execution | GDD は standard タスクで並列化、superpowers は単発の並列タスク |
| `using-superpowers` | `gdd-using-skills` | セッション開始時の skill 選択規律。**GDD active 時は `gdd-using-skills` を優先** |
| `writing-skills` | （GDD 側には対応 skill なし） | plugin 開発時に superpowers を使う |

---

## 「どちらを使うか」判定フロー

```
タスクの種類は？
├─ 「/gdd-dev <task>」と打った
│    → GDD（formal workflow に入る）
│
├─ 「壁打ちしたい」「相談だけ」
│    → gdd-pre-workflow-brainstorming（GDD）
│      ※ GDD完了後・GDD結果ベースの壁打ちは post-completion GDD-adjacent として GDD primary
│      ※ GDD 文脈がなく、artifacts を作らず会話だけで済ませたい standalone 相談なら superpowers:brainstorming も可
│
├─ 単発の PR レビュー
│    → gdd-pr-review（GDD）
│
├─ 単発のバグ修正（要件整理不要、1-2 ファイルで済む）
│    → express mode: /gdd-dev --express <task>（GDD）
│      または superpowers の個別 skill（TDD / debugging）を直接使う
│
├─ 実装中に findings が出た
│    → gdd-systematic-debugging（GDD）
│
├─ formal workflow を使わない実験・prototype
│    → superpowers を自由に使う
│
└─ plugin 開発（skill 新規作成等）
     → superpowers:writing-skills + plugin-dev:*
```

---

## auto-trigger 衝突の扱い

### Codex での auto-trigger 抑制と active GDD

Codex では superpowers が有効な session で、system message に `GDD will not auto-trigger to avoid conflicts` が出ることがある。これは **新規タスクを勝手に GDD として開始しない** ための抑制であり、すでに `.steering/<task>/state.md` や `<gdd-stop>` 由来の承認待ちがある active GDD を superpowers に譲る意味ではない。

active GDD 中は GDD primary とする。ユーザーの自然文 follow-up（例: 「その実装に切り替えて」「デプロイして検証したい」「失敗したので原因を見て」）は、次のように GDD route へ戻す:

| 自然文 follow-up | 扱い |
|---|---|
| AC / scope / architecture / 技術スタックが変わる | `gdd-requirements-amendment` または `human_recheck_required` |
| 既承認 AC 内の実装方針だけを変える | `gdd-systematic-debugging` で `design_detail_only` / `implementation_fix_only` 判定 |
| RED / TDD を要求する | `gdd-test-driven-development` |
| 失敗・デバッグ・検証差分 | `root-cause-investigation` → `gdd-systematic-debugging` |

superpowers は superpowers advisory only として、考え方や補助 reference を参照してよい。ただし `state.md` / `tasklist.md` / `worklog.md` に反映せず、`superpowers:*` を workflow として直接完結させない。

### Codex goal continuation との衝突

Codex Desktop の自動継続では `<codex_internal_context source="goal">` が入り、前ターンからの objective が再投入されることがある。この goal と SessionStart の `[gdd:reboot] Task` が食い違う場合、reboot task をそのまま採用しない。

正しい扱い:

- `GDD primary / superpowers advisory only` と宣言する
- `state.md / tasklist.md / worklog.md` が workflow owner であることを明示する
- Task Binding / PR / branch / worktree / state Task ID で goal に一致する steering を解決する
- repo-local Project Skill（例: `example-prod-eval`）は検証手段であり、workflow owner ではない

禁止する言い方:

- `superpowers の指示に従い`
- `gdd-dev 相当`

この 2 つは active GDD の state machine を曖昧にし、superpowers や Project Skill が workflow owner に見えるため、GDD 継続中の出力では使わない。

### SessionStart hook の挙動

`hooks/scripts/run-session-start-hook.sh` は以下で superpowers を検出する:

- `~/.claude/settings.json` に `"superpowers"` を含む
- `.claude/settings.json` / `.claude/settings.local.json` に `"superpowers"` を含む
- `~/.claude/skills/using-superpowers` が存在
- `~/.claude/plugins/*/skills/using-superpowers` が存在

**検出した場合**: SessionStart の systemMessage で `Routing reason` を出し、「formal GDD auto-trigger is disabled」と明示する。formal workflow の自動開始・古い task の自動再開は抑止する。一方で、GDD natural-language planning intent（例: `GDDで計画して` / `GDDで進めたい` / active GDD follow-up / GDD の requirements・design 相談）は GDD primary とし、`gdd-pre-workflow-brainstorming` を優先する。superpowers advisory only。

**理由**: superpowers の `using-superpowers` skill が「1% の可能性でも skill を呼ぶ」というルールを持つため、formal GDD workflow まで同じタイミングで auto-trigger すると両者が衝突する。ただし、GDD の planning / requirements / design 相談レーンまで止めると、ユーザーが「GDDで計画して」と明示しない限り `superpowers:writing-plans` / `superpowers:brainstorming` に吸われる。抑止対象は formal workflow の開始・再開であり、GDD 文脈の自然文 routing ではない。

### 一時 workspace / detached worktree の扱い

Codex の approval review、eval、focused regression などでは、作業場所が `/private/tmp/...` の一時 workspace になり、現在の checkout に `.steering/` が無いことがある。SessionStart hook は、同一 repo の別 worktree や `~/.gdd/worktrees/<repo>/...` の steering の `state.md` を読まず、案内もしない（以前の `[gdd:shadow-marker]` は撤去した）。案内の文面を選ぶために、各 worktree に `.steering/` があるかだけを見る。

他 workspace の artifact を import / resume しない。ユーザー入力が GDD 文脈（GDD planning / active follow-up / requirements / design / debugging）なら GDD primary / superpowers advisory only とし、`superpowers:writing-plans` / `superpowers:executing-plans` を workflow owner にしない。別 worktree の task を進めるときは、ユーザーが `/gdd-dev resume <target>` で対象を明示する。

### Post-Completion GDD Affinity

GDD の state が `done` / `cancelled` になった後でも、直近 task、artifact、task slug、PR、AC、HITL、または「GDD完了後」「さっきのGDD」「このGDD」「GDD改善」に紐づく相談は `post-completion GDD-adjacent` として扱う。

`post-completion GDD-adjacent` の壁打ち・改善相談・次回タスク相談は `gdd-pre-workflow-brainstorming` を primary にする。完了済み・マージ済み機能の仕様変更、不具合修正、追加要件へ戻すなら `gdd-requirements-amendment` を使う。superpowers は `superpowers advisory only` で、`superpowers:brainstorming` を primary owner にしない。

`done 後` は経過時間だけで判定しない。現在の会話、直近の task id / slug、PR、HITL、artifact 参照によって GDD との関係が読めるなら GDD-adjacent と扱う。

「superpowers が起動する / 呼ばれる」という表現は primary owner と advisory reference を分けて判定する。GDD が意思決定 owner のまま、手法や checklist の参照として superpowers を読むだけなら `superpowers advisory only`。route owner / primary skill として `superpowers:brainstorming` を選ぶなら GDD 文脈では不適切。

GDD と無関係な standalone creative work で、ユーザーが GDD 文脈を出していない場合だけ `superpowers:brainstorming` を primary にしてよい。

### Routing Contract Table

GDD / superpowers の競合時の正本は `skills/gdd-using-skills/SKILL.md` の `Routing Contract Table`。Active GDD 中は `GDD Workflow Lock` を有効にし、意思決定・AC・タスク状態・完了証跡は GDD artifact に戻す。

### Escape Hatch

`Escape Hatch` は、ユーザーが GDD task とは別件の `explicit standalone superpowers request` を明示し、GDD artifact を更新しない場合だけ許可する。active GDD の AC / TDD / debug / PR follow-up / completion を superpowers workflow へ直接 handoff しない。

`post-completion GDD-adjacent` と `Escape Hatch` の両方に見える場合は、Escape Hatch の条件をすべて満たす明示があるときだけ standalone superpowers を許可する。条件が欠ける場合は GDD affinity を優先し、GDD primary / superpowers advisory only とする。

### SessionStart 注入の表示原則

SessionStart はユーザーの本文ではなく systemMessage なので、ここに長い対応表や詳細な比較を入れると、後続の判断で本来の要件より routing 文言が強く効いてしまう。注入するのは **one-line routing decision** に近い短い文に限定する。

- 入れる: `Routing reason`, `GDD primary`, `superpowers advisory only`, `gdd-status` / `/gdd-dev resume <target>` の次アクション
- 入れない: 重複 skill 対応表、superpowers との差分説明、過去 incident の詳細、長い escape hatch
- 詳細が必要な場合: この文書または `skills/gdd-using-skills/SKILL.md` を明示参照する

**Why**: SessionStart injection should be concise. 共存ルールの全文は onboarding / troubleshooting 用であり、毎回の会話開始時に読む判断材料ではない。

### EnterPlanMode の扱い

- GDD session 中（`.claude/gdd-dev.local.md` がある）の `EnterPlanMode` は **GDD の `run-block-plan-mode-hook.sh` が deny**
- superpowers の `writing-plans` / `executing-plans` は GDD session 外で使う
- `superpowers:executing-plans` は汎用的な standalone written-plan executor であり、GDD が完全代替するものではない。active GDD 中の active task progression だけは `state.md` の `Next Action` と `tasklist.md` の `Current Task` / `Pending Tasks` が担うため、`gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `gdd-implementation-gating` / `gdd-completion-check` へ dispatch する
- **Goal-Driven Execution**: fixed plan の実行ではなく、Goal が明確で plan が不確実な作業は `gdd-goal-driven-execution` が owner。Goal は維持し、Plan は更新する。root cause / PR follow-up / scenario eval / CI failure で evidence に応じて plan を変えながら進める場合、`superpowers:executing-plans` を workflow owner にしない
- GDD session を終わらせたい場合は `/gdd-dev` を完了させてから別 session で superpowers を使う

---

## 設定パターン別の推奨

### A. GDD 中心・superpowers は experimental のみ

```
CLAUDE.md:
- formal workflow は必ず /gdd-dev で入る
- superpowers は experimental / 単発タスクのみ
- skill 名衝突時は GDD を優先
```

**適するチーム**: production code に近い、品質担保を重視するチーム

### B. 個別 skill 中心・GDD は大規模案件のみ

```
CLAUDE.md:
- 日常の小タスクは superpowers を使う
- standard サイズのタスクのみ /gdd-dev で入る
- 両方有効時は利用者が明示選択
```

**適するチーム**: prototype・研究開発・小規模改修が中心のチーム

### C. どちらか片方のみ有効化

```
推奨: 両 plugin の auto-trigger 衝突を避けたいなら片方を無効化
実現方法:
- ~/.claude/settings.json で plugin を disable
- または chat でセッションごとに enabled plugin を切り替え
```

---

## チーム運用での推奨事項

### 1. CLAUDE.md で優先度を宣言する

`docs/PROJECT_CLAUDE_MD_TEMPLATE.md` § D の雛形を使う:

```markdown
## Plugin 優先度

- formal workflow は `/gdd-dev` で入る（GDD）
- superpowers は単発タスク・experimental 実行でのみ使う
- `gdd-using-skills` skill がセッション開始時の skill 選択ルールを持つ
- 両 plugin の skill が同名で競合した場合、GDD 側を優先する
```

### 2. オンボーディング時の説明

新メンバーに伝えるポイント:
- **GDD と superpowers は重複機能がある**（両方使うと混乱する）
- **日常フローは `/gdd-dev` で統一**
- superpowers の brainstorming / TDD 等は **`gdd-` prefix のない単発利用時**だけ

### 3. trouble shooting の指針

| 症状 | 確認点 |
|------|-------|
| 両 plugin の skill が同時に反応する | CLAUDE.md に優先度宣言があるか |
| auto-trigger が発動しない | `gdd-using-skills` の「強制適用ポイント」を確認 |
| `EnterPlanMode` が deny される | GDD session 中。`/gdd-dev` を完了させてから別 session で試す |
| superpowers の skill が GDD session 内で動かない | GDD は formal workflow の境界を保つため一部 skill を制限。`docs/TROUBLESHOOTING.md` 参照 |

---

## Breaking Change 時の相互影響

- GDD が `references/*` を superpowers の knowledge（testing-anti-patterns 等）から取り込んだ場合、**superpowers 側の更新に追従するタイミング**を `CHANGELOG.md` で明示する
- superpowers v5.0.7 の skill と GDD v0.2.0 の統合状況は `gdd-using-skills` と `references/` の参照マップで確認できる
- 両 plugin の version 組み合わせで非互換が発生した場合、CHANGELOG の **Breaking Contract Changes** に明記

---

## 参考

- セッション開始時の skill 選択: `skills/gdd-using-skills/SKILL.md`
- auto-trigger 判定ロジック: `hooks/scripts/run-session-start-hook.sh`
- CLAUDE.md 雛形: `docs/PROJECT_CLAUDE_MD_TEMPLATE.md` § D. superpowers / 他 plugin との共存
- トラブルシューティング: `docs/TROUBLESHOOTING.md` § superpowers / 他 plugin との競合
