# Context Budget

> **所有**: phase ごとの必要情報定義、context 圧縮対策、Handoff Summary ルール
> **上位正本**: なし（context 管理の独立正本）
> **参照元**: 全 phase skill、hooks

AI エージェントのコンテキストウィンドウは有限であり、長い workflow では圧縮によって重要な情報（AC、設計判断、reviewer feedback）が失われる。このファイルは phase ごとに「何が必要で何が不要か」を定義し、context 圧縮後の品質低下を構造的に防ぐ。

## なぜ Context Budget が必要か

GDD の standard タスクは 8+ phase を経る。各 phase で新しい artifact が生まれ、前 phase の議論が context に残り続ける。典型的な問題:

- brainstorming の候補案比較が build phase まで残り、AC を押し出す
- 解消済みの reviewer feedback が context を圧迫する
- session 再開時に「何が決まったか」の要約がなく、artifact 全文を再読する

Context Budget は 3 つの仕組みでこれに対処する:
1. **Phase Context Manifest**: phase ごとに必要な情報を定義する
2. **Context Handoff Summary**: phase 遷移時に前 phase の要約を引き継ぐ
3. **Context Health Check**: hook で重要情報の存在を定期検証する

## Phase Context Manifest

各 phase が正しく動作するために必要な情報のレベル分け。skill が artifact を参照する際の指針として使う。

| Phase | 必須（常に参照） | 推奨（あれば有用） | 不要（前 phase で完了） |
|-------|----------------|-------------------|----------------------|
| brainstorming | codebase scan, user request | - | - |
| requirements-gating | requirements.md (全体), state.md | design.md skeleton | - |
| human-check | requirements.md (承認ポイント中心), design.md (骨格) | - | reviewer feedback (解消済み) |
| design-gating | design.md (全体), requirements.md (AC + 実装方針) | tech context, findings.md | brainstorming 議論詳細 |
| task-breakdown | design.md (変更点 + フロー), requirements.md (AC) | - | gate feedback (解消済み), Options Exploration |
| TDD (RED) | tasklist.md (current task + AC), design.md (該当セクション) | test patterns | 他 task の詳細, requirements 全文 |
| implementation (GREEN) | tasklist.md (current task + AC), test files, design.md (該当セクション) | findings.md | requirements.md 全文, 他 task の完了詳細 |
| implementation-gating | tasklist.md (current task), diff, design.md (該当セクション) | - | 他 task の試行記録 |
| completion-check | tasklist.md (Verification + 全 AC), requirements.md (AC) | design.md, adr.md | 個別 task の試行記録, brainstorming 議論 |

### 使い方

- **必須** 列の artifact は phase 開始時に必ず読む。context に無ければ明示的に Read する
- **推奨** 列は判断に迷ったとき・追加情報が欲しいときに参照する
- **不要** 列は前 phase で役目を終えた情報。context にあっても参照せず、新たに Read しない
- **唯一の例外**: 「他 task の完了詳細」「他 task の詳細」のうち `tasklist.md` の `Carry Forward:` 欄だけは
  直近 1〜2 task 分を参照してよい。subagent 境界で破棄される実測値のうち、次段が知らないと
  **ブロックされる**ものだけを残す枠。判定基準・保存先・分量の正本は
  `references/task-breakdown-steps.md` § Carry Forward

## Skill Runtime Read Limits

GDD の skill は、開始時に関係しそうな reference を無制限に読むのではなく、phase と判断に必要な artifact だけを読む。長い reference は onboarding / troubleshooting 用であり、実行時 context に常時入れるものではない。

### Runtime Budget と Source Budget

GDD の「軽量」は **Runtime Budget** で測る。Runtime Budget は、express / standard の各パスで実際に読む SKILL 本文、テンプレート、reference、HITL primary surface の量であり、実行時の重さ、利用者が待つ時間・読む量・context 圧迫に直結する。

**Source Budget** は、repository 内に存在する reference / docs / tests のソース総量を測る補助指標。CI の references line budget は source sprawl を抑える backstop だが、**references line budget is not the runtime budget**。テスト用 reference や導入ドキュメントが増えても、実行時に読まなければ利用者体験は重くならない。

HITL primary surface は Runtime Budget の一部として扱う。アーキテクチャ選択 / PR 分割の選択肢 / 詳細比較は、条件があるときだけ、判断に効く分を一次表示し、表の詳細は requirements.md / design.md に置く。

`scripts/lint-runtime-budget.py` は HITL 以外の runtime surface を測る機械ゲート。**SKILL body line budget**、**Runtime template budget**、**express runtime profile**、**standard runtime profile**、**estimated runtime tokens** を出力し、`tests/validate-plugin.sh` から実行する。行数は即時に増加を止める backstop、estimated runtime tokens は tokenizer 依存なしで CI に載せるための安定 proxy として扱う。

**実行時の上限**:
- phase skill が最初に読む reference は原則 3 ファイルまで
- SKILL.md 本文は `lint-runtime-budget.py` の per-skill / total cap を超えない
- express / standard の runtime template は `lint-runtime-budget.py` の path 別 cap を超えない
- active GDD routing では `state.md` / `tasklist.md` / `requirements.md` を優先し、共存ガイドや長い比較表は必要時だけ読む
- SessionStart hook は one-line routing decision を注入し、重複 skill 対応表を注入しない
- 読むべきか迷う大きな reference は「なぜ必要か」を 1 行で説明してから読む

**例外**:
- root cause investigation、scenario evaluation、prompt refactor、release review のように「文書全体の整合性」が目的の場合
- ユーザーが明示的に「全体を確認」「総チェック」「深く調査」と依頼した場合

**Why**: GDD は artifact を正本にして再開性を保つ。毎回多量の reference を読み込むと、AC / tasklist / state の重要情報が押し出され、HITL が読める風だが判断できない出力になりやすい。

## Context Handoff Summary

phase 遷移時に、次の phase に引き継ぐべき情報を 10 行以下に圧縮したブロック。各 phase skill の Handoff 出力に含める。

### フォーマット

フォーマットの正本は `references/output-format.md` § Context Handoff Summary を参照。以下は概要:

```markdown
<!-- Context Handoff: <from-phase> → <to-phase> -->
## Handoff Summary
- 決定事項: <この phase で確定した主要な判断 1-3 件>
- 主要変更ファイル: <影響するファイルパス>
- 残りの注意点: <次 phase で気をつけるべき点>
- 未解決: <次 phase に持ち越す open item があれば>
```

### phase 別の Handoff 内容

| From → To | Handoff に含める内容 |
|-----------|---------------------|
| brainstorming → req-gate / human-check | Summary Brief の一言, AC 一覧, 主要な設計判断, express 判定結果 |
| req-gate → human-check | reviewer 結果（pass/差し戻し）, 解消した指摘の要約 |
| human-check → design-gate / TDD | 承認された方向性, 自走範囲, 人間が付けた条件・修正 |
| design-gate → task-breakdown | 設計の主要判断, 変更ファイル一覧, reviewer feedback の要約 |
| task-breakdown → TDD | タスク構成の概要, 依存関係, 最初の task の AC |
| TDD → implementation | test ファイルパス, 期待する failure, 実装のヒント |
| implementation → impl-gate | 変更した箇所の要約, 自信がない点, refactor で行った変更 |
| impl-gate → next task / completion | pass/差し戻しの結果, 解消した指摘, 残りの task 数 |

### ルール

- Handoff Summary は phase 遷移ヘッダー（`references/output-format.md`）の直後に出力する
- 10 行以下に収める。詳細は artifact ファイルを参照すればよい
- 前 phase の議論の「結論」だけを書く。経緯は書かない
- Express Path でも Handoff Summary は出力する（省略しない）

## Context Health Check

既存の hook（UserPromptSubmit, PreToolUse）が注入する context の品質を補強する仕組み。

### 現在の hook による保護

| Hook | 注入内容 | 保護対象 |
|------|---------|---------|
| SessionStart | Quick Reboot（Goal, Phase, Gates, Progress） | session 再開時の方向感 |
| UserPromptSubmit | Goal + Current Task + AC + Next Action + Route In Progress | 毎メッセージの方向維持 |
| PreToolUse (plan-reread) | Goal + Current Task + AC + Past Attempts + Key Findings | Write/Edit 前の AC 見失い防止 |

### 追加の保護: Build Phase 後半の AC 強化注入

build phase の後半（implementation, impl-gate）では context 圧縮が起きやすい。`UserPromptSubmit` hook の注入を以下で強化する:

- `Current Task` の AC を 1 行要約ではなく **全文** で注入する（既存の hook が行っている）
- `Past Attempts` がある場合（= 差し戻し後の再実装）は、直近の差し戻し理由も追加注入する
- `findings.md` の最新エントリ（3件まで）を Key Findings として注入する（既存の hook が行っている）

これらは既に `run-pre-tool-use-plan-reread-hook.sh` と `run-user-prompt-submit-hook.sh` で実装済み。Context Budget は hook の既存動作を正当化し、将来の拡張方針を明示する役割。

### 実装済みの hook 拡張

1. **Smart Session Recovery（Handoff Summary の永続化と注入）**:
   - Stop hook が phase 遷移時に assistant 出力から `<!-- Context Handoff -->` ブロックを抽出し、`state.md` の `Last Handoff Summary` に書き込む
   - SessionStart hook が `Last Handoff Summary` を Quick Reboot context に含めて注入する
   - session 再開時に「前セッションで何が決まったか」を即座に復元できる
2. **Handoff Summary 出力検証（Hook-enforced Context Budget）**:
   - Stop hook が phase 遷移（`<gdd-phase>` マーカー）を検出したとき、Handoff Summary が出力に含まれていなければ `systemMessage` で警告を注入する
   - skill の自主判断ではなく hook レベルで Handoff Summary の出力漏れを検出する
3. **AC miss 検出（UserPromptSubmit AC Coverage Health）**:
   - UserPromptSubmit hook が `requirements.md` と `tasklist.md` Current Task 内の AC ID 数を比較し、`AC Coverage Health: requirements expected N; current task injected M` を注入する
   - `Covers AC:` / `Planned RED / E2E` / `- AC:` のいずれに AC ID があっても Current Task の AC ID set として拾い、context compact 後に AC が削れて見えるのを防ぐ
   - `M < N` は必ずしも失敗ではない（複数 task のうち現在 task が一部 AC だけを担当する場合がある）。completion / done 前に `M` が 0、または Current Task の `Covers AC` と注入 AC が食い違う場合は、TDD / task-breakdown に戻して AC binding を補完する

### 未実装の hook 拡張候補

将来的に context 保護をさらに強化する場合の候補:

1. **phase 検出**: `state.md` の `Resume From` / `tasklist.md` の `Next Action` から現在 phase を推定し、Phase Context Manifest の「必須」列だけを注入する

これらは Phase Context Manifest の定義が安定した後に段階的に実装する。

## Context Degradation Tiers（コンテキスト劣化段階）

長い workflow では context window の使用率が上がるにつれて応答品質が劣化する。以下の 4 段階で状態を識別し、段階に応じた対処を取る。

| Tier | 状態 | 目安 | 対処方針 |
|------|------|------|---------|
| **PEAK** | 完全に正確 | context 使用率 < 50% | 通常通り進める |
| **GOOD** | 省略が起きる可能性 | 50–70% | Handoff Summary を丁寧に出力する |
| **DEGRADING** | 重要情報の見落としリスクあり | 70–85% | artifact を必ず Read してから判断する。記憶に頼らない |
| **POOR** | 深刻な情報欠落・ループリスク | 85% 以上 | `/clear` を推奨。または subagent に委譲する |

### 劣化の Warning Signs

以下の兆候が 1 つでも見えたら DEGRADING 以上の可能性がある:

- **Silent partial completion**: step を飛ばしているが飛ばしたことを言わない
- **Increasing vagueness**: artifact を引用せず、曖昧な要約で回答する
- **Skipped guardrails**: 通常は行う確認（worktree チェック・AC 照合）を省略する
- **AC の見失い**: 別の AC に対応するコードを書いている・AC を誤記する
- **Loop**: 同じ修正を繰り返す。前回の修正を記憶していない

### 対処プロトコル

1. **DEGRADING 検出時**: artifact（`tasklist.md` / `requirements.md` / `design.md`）を明示的に Read してからアクションを取る。「context から覚えている」情報だけで判断しない
2. **POOR 検出時**: `/clear` を提案し、Quick Reboot で最小情報から再開する
3. **Subagent 委譲**: DEGRADING 以上で残タスクが多い場合、各タスクを独立した subagent に委譲する。subagent は isolated context で動作するため、劣化の影響を受けない

## Codex Remote Compact Failure（host-level interruption）

Codex では、context compaction の実行自体が host 側で失敗し（`Error running remote compact task: unexpected status 503 Service Unavailable ...`、url は `chatgpt.com/backend-api/codex/responses/compact`）、assistant turn が中断されることがある。これは **GDD の gate failure / AC failure / review failure ではない**。upstream 503 による host-level interruption として扱う。

### Recovery Contract

- compact 503 を見たら、loop state を消す停止（`done` / `cancelled` / `blocked` など）に進めない。既存の `Resume From` / `Next Action` を維持する
- 復帰時は memory continuation ではなく disk reboot を行う。active worktree の `state.md` / `tasklist.md` を読み、planning 中は `Resume From`、build 中は `Next Action` を正本にする
- `Last Handoff Summary` は context 復元の補助であり、routing source にしない
- interruption が `human-check-waiting` 到達後かつ human-check text の表示前に起きた場合、`state.md` の `Resume From=human-check-waiting` と `requirements.md` / `design.md` から human-check テンプレートを再生成して停止する。要件を再解釈し直さない
- interruption が non-terminal phase 中に起きた場合、既存 artifact を再利用して同じ phase を再実行する。新しい worktree や重複 steering を作らない
- interruption 直後の最初の応答では、観測事実として `Codex compact 503` を記録し、`参照した正本` / `現在 phase` / `次の1アクション` を短く返す
- 会話履歴が欠落した場合でも `state.md / tasklist.md / worklog.md / ac-ledger.md`（AC Trace Ledger）を復帰正本として読み直す。AC Trace Ledger が無い、または `status=unverified` / `status=failed` が残る場合は done 判定を信用せず、`gdd-completion-check` で再検証する

### Checkpoint Discipline

GDD は compact API の失敗を捕捉できないため、壊れない設計は **事前永続化** で作る。

- phase 遷移前に `state.md` / `tasklist.md` の routing field を先に永続化し、read-back してから長い subagent / gate / test 実行に入る
- 長い phase の区切りでは `worklog.md` に `Compact Recovery Checkpoint: <phase> / <next-action> / <artifact paths>` を追記してよい。これは補助情報であり、routing source にはしない
- retry は host 障害に対する retry だけに限定する。AC failure や review finding を compact 503 と混同して再実行しない

## stub.md の扱い（Root Stub サイズ制御）

`phase-progression.md` § X-4 で定義される root stub（archive された root feature steering の local 残置物）は、多段 hotfix 連鎖と `Abandoned Hotfix Attempts` の蓄積で際限なく肥大化するリスクがある。以下のサイズ制御ルールを適用する:

- **chain depth 5 到達を契機に分離**: `Parent Hotfix` chain depth が 5 に到達した時点で、stub.md 本体から **古い Abandoned Hotfix Attempts エントリおよび古い Active hotfix chains エントリ** を同ディレクトリの `stub-archive.md` に切り出す
- **stub.md 本体の保持範囲**: 直近 5 hotfix 分の抄録（Abandoned / merged を問わず最新 5 件）＋ 現在 active な chain のみ
- **stub-archive.md**: append-only。過去のエントリを時系列で保持し、audit 遡行時のみ参照する
- **切り出し時の記録**: 切り出し実施時に worklog.md に `## Stub Archival (ISO8601) / Moved to: stub-archive.md / Entries: <N件>` を記録

### VH merge tie-breaker（同一 timestamp 時の secondary sort）

stub.md § VH merge manifest で複数 chain の `Verification History` を time-sort で結合する際、同一 ISO 8601 timestamp が複数 chain から同時に出現するケースの決定的順序を定める:

- **primary sort**: ISO 8601 timestamp 昇順
- **secondary sort**: `chain-path-sha1-prefix`（chain の steering path を SHA-1 ハッシュし、先頭 **8 hex** を取った文字列）の **辞書順昇順**
- tie-breaker 未定義時は **fail-closed**（merge を実施せず `<gdd-stop reason="blocked">` で停止）。stub 管理者が path を明示リネームするか、timestamp 精度を上げて再試行する

**Why**: 同一 timestamp で順序が非決定だと VH merge manifest が再実行のたびに異なる canonical 順序を生み、audit 比較が不能になる。sha1 prefix は chain-path の identity から deterministic に派生するため安定した tie-breaker となる。
