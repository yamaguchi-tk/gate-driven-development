---
name: gdd-writing-skills
description: "Use when creating, editing, splitting, or validating skills inside the GDD plugin."
version: 0.2.0
---

# GDD Writing Skills

GDD plugin に新規 skill を追加するとき、または既存 skill の構造をリファクタするときの **規約 + テンプレート集**。superpowers の `writing-skills` が「skill 作成に TDD を適用する」discipline を扱うのに対し、こちらは GDD 固有の **state machine / 4 種別 / Phase Gate / Rationalization Check** 規約を埋めるためのガイド。

両者は補完関係。skill 全般の書き方は superpowers 側、GDD 固有の規約はここを参照する。

## Process Documentation TDD

superpowers `writing-skills` の pressure scenario discipline を GDD skill 改修へ吸収する。skill / prompt / HITL 文面を変更する場合、可能な限り **RED-GREEN-REFACTOR** を process documentation に適用する。

1. **pressure scenario**: その文面が無いと agent が失敗する具体シナリオを 1 つ以上書く。例: 「HITL が長すぎて制限事項を見落とす」「review finding を検証せず受け入れる」。
2. **baseline failure**: 既存文書で agent がどう誤るか、または contract test が何を検出できないかを記録する。
3. **minimal skill change**: 失敗を閉じる最小の SKILL.md / reference / hook / test 変更を入れる。
4. **agent complies / contract passes**: 変更後に pressure scenario が pass することを、contract test・eval・review scenario のいずれかで確認する。
5. **loophole close**: agent が別の言い訳で抜けられる場合は Rationalization Check / Guardrails / test を追加する。

機械的に検証できるなら contract test を優先する。判断型の文面改善なら、`worklog.md` または CHANGELOG に pressure scenario / baseline failure / 採用した loophole close を短く残す。

## Skill Type Testing Matrix

Provides Process Documentation TDD for every skill type without moving trigger details back into the frontmatter description.

superpowers `writing-skills` の「skill の種類ごとにテスト方法を変える」考え方を、GDD の 4 種別と reference 文書に対応させる。すべての skill 改修に同じ grep test を当てない。

| 対象 | 主な failure mode | 推奨テスト |
|---|---|---|
| Discipline-enforcing section | agent が言い訳して規律を迂回する | pressure scenario / rationalization phrase / mandatory heading の contract test |
| Phase Gate skill | state 遷移、`Next Action`、必須 artifact 更新が壊れる | transition contract test / required field test / fail-closed scenario |
| Methodology skill | root cause 未確定なのに fix する、phase を飛ばす | scenario eval / phase order test / no-fix-before-root-cause test |
| Specialized Helper skill | formal gate と advisory lane を混ぜる、handoff が曖昧 | trigger routing test / output handoff schema test / source-specific scenario |
| Lookup / Reference skill | read-only のはずが artifact を変更する、回答の正本がずれる | read-only behavior test / source precedence test / referenced path existence test |
| Reference-only document | 参照切れ、古い template、本文との drift | docs-links-valid / dependent skill grep / template snapshot test |

最低限の採用基準:

- 新しい見出しを追加したら、その見出しが存在するだけでなく、失敗を防ぐ **判断語**（例: `fail-closed`, `human_recheck_required`, `pre-existing failure`, `fix allowed: no`）も test に入れる。
- HITL / prompt 文面の変更は、非エンジニアが誤解しやすい pressure scenario を 1 件以上 test 名または CHANGELOG に残す。
- state machine に接続する skill は、文面追加だけでも `Next Action` / `Resume From` の互換を壊していないことを検証する。
- Reference-only 変更では、本文 skill がその reference を読む契約を持っているかを確認する。孤立 reference を増やさない。

## なぜこの skill が要るか

GDD plugin は現時点で 22 skill ある。各 skill には以下のような暗黙の規約が共有されている:

- description の書き出しが種別ごとに違う（`Internal: auto-routed when ...` / `Use when ...` / `Use for ...`）
- `Rationalization Check` 表は 3 列で、Why ラベルは `references/rationalization-root-causes.md` を参照
- state.md / tasklist.md / worklog.md の正本性が phase ごとに違う
- supporting reference は skill 内 `references/`、plugin 共通 reference は `/references` 直下

これらは「前の skill を真似する」ことで伝承されているが、別の AI / 人間が skill を追加すると **構造が崩れる**。一度書面化し、新規 skill 追加時のチェックリストとして使えるようにする。

## Iron Law

> **NEW SKILL MUST FIT INTO ONE OF THE 4 TYPES.**

種別が決まらないなら、それは skill ではなく既存 skill の section 追加か、`references/` 配下の補助ファイル。種別不明のまま skill 化しない。

## Skill RED-GREEN Evidence

skill 本文、prompt、reviewer policy、HITL 出力契約を変更する場合は、文書だけを直して完了にしない。superpowers `writing-skills` と同じく、pressure scenario で RED → GREEN を確認する。

必須記録:

- `baseline_without_skill`: 変更前または該当ルール無しで、agent がどの pressure scenario にどう失敗したか
- `with_skill`: 変更後に同じ pressure scenario がどう改善したか
- `pressure scenario`: agent が合理化しやすい短い入力、期待される違反、期待される合格条件

この evidence は `.steering/<task>/findings.md`、PR 本文、または `SUPERPOWERS_BENCHMARK_EVIDENCE` が指す比較資料に残す。単純な typo 修正やリンク修正は対象外だが、判断・routing・HITL 表示・reviewer severity が変わる場合は対象にする。

## When to Use

- **GDD plugin に新規 skill を追加する直前**: ファイル作成前にこれを読む
- **既存 skill の責務分離 / 統合をする前**: 4 種別のどれに該当するか再判定
- **skill を作るかどうか迷っている**: 「skill にすべきか / reference / inline section で十分か」の判断
- **複数 skill のスタイル統一が崩れていると感じたとき**: 規約を再確認

使わない場面:

- 単発の section 編集（description 1 行直すだけ等）
- `references/` 直下の補助ファイル追加（skill 化を伴わない）
- 既存 skill のロジック修正（書き方ではなく中身の話）

## Skill 種別フレームワーク

新規 skill を作るとき、まずどの種別かを決める。各種別で description の書き方・標準セクション・state 接続が異なる。

### 種別 1: Phase Gate skill（state machine 接続あり）

**例**: `gdd-requirements-gating` / `gdd-design-gating` / `gdd-task-breakdown` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `gdd-implementation-gating` / `gdd-completion-check` / `gdd-systematic-debugging`

**特徴**:
- `Next Action=gdd-XXX` で state machine から auto-route される
- ユーザーが直接呼ばない（呼ばせない）
- 入力: `state.md` / `tasklist.md` / 前 phase の artifact
- 出力: 次 phase への handoff（`Next Action` 更新）

**description 書き出し**:
```
Internal: auto-routed when `Next Action=gdd-XXX`. Do not invoke directly — the state machine routes here. Responsibilities: ...
```

**標準セクション順**:
1. Goal
2. Fixed Model
3. Phase Gate Pre-check（前提条件）
4. Steps
5. Output Guidance（次 phase への handoff 形式）
6. Rationalization Check（3 列）
7. Guardrails

### 種別 2: Methodology skill（GDD 非依存）

**例**: `root-cause-investigation`

**特徴**:
- state.md / tasklist.md を前提にしない
- GDD 外でも単体起動可能
- 入力: 症状や問題の記述
- 出力: methodology に沿った結論（root cause / 仮説 / 次のアクション）

**description 書き出し**:
```
Use when [具体的な triggering condition]. Provides [methodology の核] for [purpose]. Independent of any workflow.
```

**標準セクション順**:
1. なぜこの skill が要るか
2. Iron Law
3. 適用範囲（When to Use / 使わない場面）
4. Phases or Steps
5. Red Flags
6. 合理化との対決（superpowers 風の Rationalization 表）
7. Quick Reference
8. 他 skill との関係

**命名**: `gdd-` prefix を **付けない**（汎用なので）

### 種別 3: Specialized Helper skill（特定状況の補助）

**例**: `gdd-test-failure-debug-pack` / `gdd-pr-review` / `gdd-receiving-code-review` / `gdd-requesting-code-review` / `gdd-refactor-planning` / `gdd-requirements-amendment` / `gdd-pre-workflow-brainstorming`

**特徴**:
- state machine から auto-route されない（手動 trigger）
- 特定の状況・トリガーで人間または他 skill から呼ばれる
- 既存 phase に組み込みづらい局所的な仕事を持つ

**description 書き出し**:
```
Use when [特定状況]. Triggers: 「特定の日本語フレーズ」.
```

**標準セクション順**:
1. Goal
2. Fixed Model
3. When To Use / 使わない場面
4. Steps
5. Output Template（後続 skill が読みやすい形式）
6. Rationalization Check（3 列）
7. Guardrails

### 種別 4: Lookup / Reference skill（read-only）

**例**: `gdd-status` / `gdd-metrics` / `gdd-model-routing` / `gdd-using-skills`

**特徴**:
- artifact を変更しない（または最小限）
- 「今どこ？」「どのモデル？」「どの skill を使う？」のような問い合わせに答える
- 入力: 現在の state
- 出力: 情報・指針

**description 書き出し**:
```
Use when the user asks 「...」「...」「...」, or [状況].
```

**標準セクション順**:
1. Goal
2. Steps（情報取得手順）
3. Output Template
4. Rationalization Check（3 列、`Rationalization Check ルール` § 表に従う）
5. Guardrails（read-only であることの保証）

### Operational Helper exception

`gdd-using-git-worktrees` は問い合わせにも使われるが、`git worktree add/remove` や cleanup 判断を含むため read-only Lookup ではない。分類は Specialized Helper として扱い、破壊的操作・branch削除・worktree cleanup は Operational Safety と明示確認ルールに従う。

## 命名規約

- **GDD state machine に組み込まれる**: `gdd-` prefix 必須
- **GDD 非依存の汎用 methodology**: `gdd-` 外す（例: `root-cause-investigation`）
- **kebab-case**: snake_case や camelCase は使わない
- **3 語以内が望ましい**: `gdd-implementation-gating`（OK）/ `gdd-subagent-driven-implementation`（既存だが境界事例）
- **動詞 or 名詞句**: `gdd-systematic-debugging`（名詞句、推奨）/ `gdd-do-debugging`（動詞、避ける）
- **既存 skill 名と衝突しない**: glob で確認（`ls skills/`）

## SKILL.md frontmatter ルール

```yaml
---
# (skill SKILL.md の YAML frontmatter)
name: <kebab-case-name>     # ディレクトリ名と一致
version: 0.1.0              # 新規時は 0.1.0、変更は SemVer（下記表参照）
description: "..."           # 1024 字以内推奨、種別ごとの書き出しを守る
---
```

- `name` は必須・ディレクトリ名と完全一致
- `description` は **trigger phrase + responsibilities** を含める
  - ユーザー直接呼び出し可能なら **日本語の trigger phrase** を「」で複数列挙
  - Phase Gate なら `Responsibilities: ... + ... + ...` の連結で全責務を列挙
  - **NEVER 行末を `description: ...` で省略**: フル長で書ききる

### Description Discovery Discipline（CSO）

superpowers `writing-skills` の Claude Search Optimization を GDD 向けに吸収する。description は「本文の代替」ではなく、**読むべき skill を見つけるための trigger contract** として書く。

**原則**:

- description は `when to read this skill` を示す。詳細手順・判定順・loop・review 順序を要約しすぎない。
- workflow summary shortcut を作らない。実行者が description だけを読んで本文を飛ばせる書き方は禁止。
- 手動起動 skill は trigger phrase / 症状 / 状況を中心に書く。`Provides ...` は 1 行の能力タグに留め、手順を列挙しない。
- Phase Gate skill は例外として `Internal: auto-routed when Next Action=...` と `Responsibilities:` を残してよい。ただし `Responsibilities:` は責務タグであり、詳細な実行順序や閾値は本文に置く。
- description を変更したら、`empirical-prompt-tuning` の Iteration 0 と同じく description/body alignment を確認する。trigger にある状況が本文で扱われていない、または本文の重要責務が discovery 不能なら修正する。
- trigger phrase 変更時は、同種 skill との collision scan を行う。例: `rg -n "コードレビューして|実装レビューして|route判定" skills/ references/`。

**悪い例**:

```yaml
description: "Use when executing implementation plans. Dispatch subagents, review after each task, then run spec compliance and code quality review."
```

これは実行順を要約しており、本文の Two-Stage Review Order や state machine route を読まずにショートカットされる危険がある。

**良い例**:

```yaml
description: "Use when executing approved GDD Current Task implementation from `tasklist.md`, or when `Next Action=gdd-subagent-driven-implementation`."
```

こちらは発火条件を示し、詳細手順は本文に残している。

## Skill Slimming Discipline

GDD skill は頻繁に読まれるため、本文を太らせすぎると実行者が必要な contract を読み落とす。superpowers `writing-skills` の token efficiency を GDD の SSOT 方針に合わせて使う。

- frequently-loaded skill（`gdd-using-skills` / phase gate / `gdd-brainstorming` / `gdd-completion-check`）は、本文に最小 contract と route 判断だけを置き、長い例・schema・catalog は `references/` に逃がす。
- 1 skill 内で同じ手順を 2 回以上説明しない。複数 skill で共有する手順は reference 化する。
- code / command の exhaustive help を SKILL.md に貼らない。必要なら script の `--help` または dedicated reference に誘導する。
- ただし fail-closed 条件、state field 名、Next Action / Resume From、HITL で人間が判断する制限事項は本文に残す。slimming を理由に安全境界を reference に埋めない。
- 大きな section を reference 化したら、参照元 skill の近くに 1 行 summary と正本 path を置き、`tests/validate-plugin.sh` の docs-links-valid / skill-reference-drift で参照切れを検出できるようにする。

### SemVer Bump 判定基準

skill / plugin の version bump は SemVer に従う。判定に迷うときは保守的に倒す（破壊的判定を選ぶ）。

| Bump | skill version | plugin version | 該当する変更 |
|---|---|---|---|
| **patch** | 0.1.0 → 0.1.1 | 0.3.24 → 0.3.25 | typo / 表現改善 / Why 説明追加 / 既存ルールの言語化 / supporting reference の小修正 |
| **minor** | 0.1.0 → 0.2.0 | 0.3.24 → 0.4.0 | 新規 skill 追加 / 新規 reference 追加 / 既存 skill に新セクション追加 / Rationalization Check に新規行追加 / Steps に新規 step 挿入 |
| **major** | 0.1.0 → 1.0.0 | 0.3.24 → 1.0.0 | skill の rename / 削除 / description の trigger phrase 互換破壊 / SKILL.md 種別変更（Phase Gate → Methodology 等）/ state machine 接続の変更 / 既存 reference 削除 |

### 依存波及の確認手順

skill 変更が他 skill に影響する場合、波及範囲を確認してから bump:

1. **description / name 変更**: `grep -r "<旧 skill 名>" skills/ references/` で参照箇所を全数確認
2. **Phase Gate skill の state 接続変更**: `references/state-machine.md` / 前 phase / 次 phase の handoff 文言も同時更新
3. **共通 reference 変更**: `grep -r "references/<reference 名>" skills/` で参照する全 skill を確認
4. **template / Why ラベル変更**: `gdd-writing-skills` のテンプレートと `rationalization-root-causes.md` を最新に保つ（drift 防止）

### bump 時の同時更新項目

| 変更内容 | 同時に更新するもの |
|---|---|
| 新規 skill 追加 | `plugin.json` minor bump / `CHANGELOG.md` / `skill-responsibility-matrix.md`（責務重複が有り得れば Pair 追加） |
| 既存 skill 大幅改訂 | skill 自身の version bump / `CHANGELOG.md` / 参照する他 skill の handoff 文言 |
| reference 追加 | `plugin.json` minor bump（minor 扱い）/ 参照元 skill の `## 関連 references` セクション |
| description の trigger phrase 変更 | `plugin.json`（互換破壊なら major）/ 同一 trigger を持つ可能性のある他 skill の description |

### 判断に迷うときの保守ルール

- patch / minor で迷ったら **minor**（小修正の連打で patch が積み重なるより、まとまった単位で minor のほうが履歴が読みやすい）
- minor / major で迷ったら **major**（trigger phrase や接続を変えるなら破壊的と扱う）
- patch / major は通常迷わない。迷ったら設計を見直す

## Rationalization Check ルール

GDD skill の Rationalization Check は **種別ごとに列数が違う**。これは意図的な使い分け。

### 種別ごとのフォーマット

| 種別 | section 見出し | 列数 | フォーマット |
|---|---|---|---|
| **Phase Gate** | `Rationalization Check（この skill 固有）` | **3 列** | 合理化 / 現実 / Why |
| **Specialized Helper** | `Rationalization Check（この skill 固有）` | **3 列** | 合理化 / 現実 / Why |
| **Lookup / Reference** | `Rationalization Check（この skill 固有）` | **3 列** | 合理化 / 現実 / Why |
| **Methodology**（GDD 非依存） | `合理化との対決` | **2 列** | 出てくる言い訳 / 現実 |

**Why この使い分け**:

- Phase Gate / Specialized Helper / Lookup は **GDD plugin 内専用** の skill。`references/rationalization-root-causes.md` の Why ラベルカタログを共有して全体の一貫性を保つ
- Methodology は **GDD 非依存** で単独起動も可能（例: `root-cause-investigation`）。superpowers `systematic-debugging` の「合理化との対決」スタイル（2 列）と互換にし、Why ラベルカタログへの依存を弱める。GDD plugin 外で使われる前提で書く

### GDD 専用 skill（Phase Gate / Specialized Helper / Lookup）の 3 列フォーマット

```markdown
## Rationalization Check（この skill 固有）

[description 1 行]。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「...」 | ... | [Bias Label] 1-2 行の補足 |
```

- **Why 列のラベル**は `references/rationalization-root-causes.md` から選ぶ（`[Curse of Knowledge]` 等）
- 既存のラベルに当てはまるものがあれば再利用、無理な場合のみカタログ追加
- カタログ追加時は「GDD の skill / phase でいつ出るか」を明示
- 各行は 1 つの合理化に集中（複合的な言い訳は分解する）

### Methodology skill の 2 列フォーマット

```markdown
## 合理化との対決

| 出てくる言い訳 | 現実 |
|---|---|
| 「...」 | ... |
```

- 列数を 2 に絞る（GDD 非依存のため Why カタログを引かない）
- 認知バイアスラベルを付けたければ「現実」列の冒頭に `[Bias]` を入れてもよい（任意）
- 「現実」列は 1-2 行で簡潔に。長文の説明は別 section に書く

## Supporting References / Scripts の配置ルール

3 階層あり、どこに置くかで意味が変わる:

| 階層 | パス | 用途 |
|---|---|---|
| **plugin 全体共通** | `/references/*.md` | 複数 skill から参照される共通規約・テーブル（state-machine.md / rollback-patterns.md / rationalization-root-causes.md など） |
| **skill 専用 reference** | `skills/<skill-name>/references/*.md` | その skill のみが詳細展開のため使う補助ファイル（root-cause-investigation の multi-layer-probing.md など） |
| **skill 専用 script** | `skills/<skill-name>/scripts/*.sh` | 該当 skill から実行される shell / Python ツール |

**判定ルール**:

- **複数 skill から参照されるか?** → Yes なら plugin 全体共通、No なら skill 専用
- **SKILL.md が 500 行を超えそう?** → references に分割
- **実行可能な検証 / ツールか?** → scripts/

**Security 規則**:
- secret を扱う script は **必ず masking 実装** を入れる（length + prefix のみ出す等）
- script は chmod +x して動作確認してからコミット
- script の冒頭にヘッダーコメント（用途、Usage、exit codes）を書く

## State Machine への接続ルール

Phase Gate skill のみ該当。Methodology / Specialized Helper / Lookup は state を変更しない。

| 状態 | 正本ファイル | 更新する skill |
|---|---|---|
| `Next Action` | `tasklist.md` | 各 phase の完了時に次 phase が更新 |
| `Resume From` | `state.md` | planning 差し戻し時のみ更新 |
| `Route In Progress` | `state.md` | 差し戻し route の進行中だけ非 none、route 完了時に遷移先 skill が none に戻す |
| `Gate Status` | `state.md` | 各 phase の通過判定 |
| `Fix Attempts` | `tasklist.md` | `implementation_fix_only` 選択時に +1 |

新規 Phase Gate skill を作るときは:

1. `references/state-machine.md` に新 phase の遷移を追記
2. 前 phase / 次 phase の skill にも `Next Action=...` の handoff 先として記載
3. `references/rollback-patterns.md` に差し戻し時の永続化先を追加

## 新規 Phase Gate skill テンプレート

```markdown
---
# (Phase Gate skill 用 frontmatter テンプレート)
name: gdd-<name>
version: 0.1.0
description: "Internal: auto-routed when `Next Action=gdd-<name>`. Do not invoke directly — the state machine routes here. Responsibilities: <責務 1> + <責務 2> + <責務 3>."
---

# <Title>

<1-2 行で skill の役割>

## Goal

- <ゴール 1>
- <ゴール 2>

## Fixed Model

- `Claude Code`: `Sonnet` + `effort=medium`
- `Cursor`: `GPT-5.4` + `reasoning.effort=medium`（light_task tier）
- skill/agent 執筆の品質確保のため mini は使わない

## Phase Gate Pre-check

開始前に確認する gate 状態:

- `state.md` の `Gate Status: <前 phase>=approved` を確認
- `tasklist.md` の `Next Action=gdd-<name>` を確認
- <他の前提条件>

満たさない場合は fail-closed で停止し、`参照した正本` / `不足条件` / `次の1アクション` を返す。

## Steps

1. <step 1>
2. <step 2>
...

## Output Guidance

phase 完了時の handoff 形式:

```markdown
## <Phase 名> 完了

### 確定事項
- ...

### 次のアクション
- → `Next Action=gdd-<次 phase>` に更新
```

## Rationalization Check（この skill 固有）

<1 行説明>。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「...」 | ... | [Bias Label] ... |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照。以下はこの skill 固有のルール。

- <固有ルール 1>
- <固有ルール 2>
- **Context Compaction Resilience**: <re-read すべきファイル>
```

## 新規 Methodology skill テンプレート

```markdown
---
# (Methodology skill 用 frontmatter テンプレート)
name: <name>  # gdd- prefix なし
version: 0.1.0
description: "Use when <trigger condition>. Provides <methodology の核> for <purpose>. Independent of any workflow — can be invoked standalone, from <GDD skill>, or by any agent."
---

# <Title>

<役割を 2-3 行で>

## なぜこの skill が要るか

<methodology を持たないとどうなるか、コスト構造>

## Iron Law

> **<太字の不可侵ルール>**

<違反すると何が起きるか>

## 適用範囲

使うべき場面:
- ...

使わない場面:
- ...

## <N> Phases / Steps

### Phase 1: <name>
...

### Phase 2: <name>
...

## Red Flags

以下のいずれかが頭をよぎったら止まる:
- 「...」
- 「...」

## 合理化との対決

> Methodology は **2 列**（superpowers 風 `出てくる言い訳 / 現実`）を採用する。GDD 専用 skill（Phase Gate / Specialized Helper / Lookup）の `Rationalization Check（この skill 固有）` § **3 列** とは別形式。詳細は本 skill の `Rationalization Check ルール` セクションを参照。

| 出てくる言い訳 | 現実 |
|---|---|
| 「...」 | ... |

## Quick Reference

| Phase | 何をする | 完了の判定 |
|---|---|---|
| ... | ... | ... |

## 他 skill との関係

- **`<related skill>`** — <関係の説明>
```

## 新規 skill 追加チェックリスト

ファイル作成 → 試運転 → commit の前に全部チェック:

### 設計
- [ ] 4 種別のどれに該当するか決まっている
- [ ] 既存 21 skill との責務重複が無いことを確認した
- [ ] description の trigger phrase が他 skill と衝突しない（特に同種別の他 skill）
- [ ] state machine に組み込むなら `references/state-machine.md` 更新計画がある

### ファイル構成
- [ ] ディレクトリ名と `name` frontmatter が一致
- [ ] `version: 0.1.0` で frontmatter に入っている
- [ ] SKILL.md は 500 行以下、超えるなら references に分割
- [ ] supporting references は適切な階層（plugin 共通 / skill 専用）に置いた
- [ ] script があれば chmod +x して動作確認した
- [ ] secret を扱う script は masking 実装済み

### 内容
- [ ] 種別ごとの標準セクション順を守っている
- [ ] Rationalization Check は 3 列（合理化 / 現実 / Why）
- [ ] Why 列のラベルは `references/rationalization-root-causes.md` から選んだ（or 新規追加した）
- [ ] Guardrails の冒頭で `references/common-guardrails.md` を参照している（共通ルール重複を避ける）
- [ ] Phase Gate skill なら Context Compaction Resilience が Guardrails にある

### 統合
- [ ] `plugin.json` の version を bump（patch / minor 判定）
- [ ] 前 phase / 次 phase の skill description に handoff 言及を追加（Phase Gate のみ）
- [ ] `references/reviewer-selection.md` 更新（reviewer 起動が必要なら）
- [ ] `references/state-machine.md` 更新（新 phase なら）
- [ ] CHANGELOG.md にエントリ追加

### 検証
- [ ] skill が `available_skills` リストに表示されるか確認
- [ ] description の trigger phrase で別 skill が誤起動しないか確認
- [ ] 既存 skill から参照する場合、参照側の SKILL.md も更新済み

## Rationalization Check（この skill 固有）

skill 作成を雑に進めたくなる思考パターン。`Why` 列の認知バイアスラベルは `references/rationalization-root-causes.md` を参照。

| 合理化 | 現実 | Why |
| --- | --- | --- |
| 「種別不明だが skill 化はしておく」 | 種別不明 = 責務曖昧 = 後で他 skill と重複・衝突する。種別不明なら reference か既存 skill の section 追加で済ます | [Bias for Action] 着手したい欲求が、責務設計の検証を後回しにする |
| 「既存 skill の規約は知ってるから、テンプレートを読まなくていい」 | 22 skill の暗黙規約は人間でも全部覚えていない。テンプレートを毎回参照する方が安く正確 | [Curse of Knowledge] 自分が規約を覚えていると錯覚する |
| 「Rationalization Check はあとで書く」 | Rationalization Check は使われ始めると編集タイミングが無くなる。skill 完成時に書ききる | [Premature Closure] 早く skill を完成と言いたい欲求が、品質要素の後回しを正当化する |
| 「state machine 接続は後で追加できる」 | Phase Gate skill の state machine 接続は、後付けすると既存 skill の handoff も全部見直しになる。最初から含める | [Planning Fallacy] 後付けコストを過小評価する |
| 「skill 1 個追加だけだから version は patch」 | 新 skill 追加は機能追加 = minor bump。patch は内容更新のみ | [Premature Closure] bump 判定を雑に済ませたい |
| 「他の skill も同じ書き方だから問題ない」 | 「他の skill」自身が古い規約のままかもしれない。テンプレートを正本とする | [Recency Bias] 直近見た skill を「標準」と一般化する |
| 「supporting reference は 1 個だから plugin 共通 references に置く」 | 1 skill しか使わないなら skill 専用 references に置く。plugin 共通は複数 skill で参照されるもの限定 | [Locus of Control Drift] 置き場所判断を雑にすると、後で「どの skill のため？」が分からなくなる |

## Guardrails

共通ルールは `references/common-guardrails.md` を参照（自律継続、fail-closed 応答）。以下はこの skill 固有のルール。

- 種別不明のまま skill 化しない（reference / 既存 skill section 追加で済むなら skill 化しない）
- 既存 22 skill との重複チェックを省かない
- Rationalization Check を空欄のままコミットしない（少なくとも 3 行は書く）
- state machine への接続を後付けにしない（Phase Gate skill 限定ルール）
- script に secret 出力を masking なしで書かない
- 規約変更（テンプレートや checklist の更新）は CHANGELOG.md に明記する

## 他 skill との関係

- **`superpowers:writing-skills`** — skill 作成全般の TDD 規律（pressure scenario / RED-GREEN-REFACTOR）。GDD 固有の規約ではなく skill 作成の方法論を扱う。両方併用が望ましい
- **`plugin-dev:skill-development`** — Claude Code plugin の skill 開発全般。frontmatter 形式や YAML 規約など Claude Code 共通のルールを扱う
- **`references/rationalization-root-causes.md`** — Why 列ラベルの正本
- **`references/state-machine.md`** — Phase Gate skill の state machine 遷移定義
- **`references/common-guardrails.md`** — 全 skill 共通の guardrails
- **`references/rollback-patterns.md`** — 差し戻し時の永続化先定義

## Quick Reference

| 状況 | 何をする |
|---|---|
| 新規 skill 追加 | 4 種別判定 → テンプレートコピー → checklist 全通過 → plugin.json bump |
| 既存 skill 責務分離 | 分離先が 4 種別のどれか判定 → 元 skill の SKILL.md から該当箇所抽出 → 元 skill から参照リンク追加 |
| 規約違反を発見 | テンプレート参照 → 該当 skill 修正 → CHANGELOG.md 追記 |
| 種別判定に迷う | 「state を変更するか」「workflow 依存か」「呼び出し主体は誰か」の 3 軸で分類 |
