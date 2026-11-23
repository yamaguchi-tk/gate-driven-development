---
name: gdd-test-failure-debug-pack
version: 0.1.0
description: "Use when GDD tests or verification fail and need debug evidence before systematic debugging."
---

# Test Failure Debug Pack

実際の failing test を、修正前に読み返せる debug artifact に変換する。routing の正本は `gdd-systematic-debugging` に残し、この skill は test failure の状況整理に集中する。

Debug entry order:

- red test / executable verification failure: this skill first
- confidence low after pack: `root-cause-investigation` Phase 1〜3
- route decision after evidence: `gdd-systematic-debugging`

## Goal

- failing test を再現できる形で固定する
- `Expected` と `Actual` を分けて書く
- root cause を evidence 付きで狭める
- workaround と最小 fix plan を出す
- `worklog.md` を更新すべきかを判断する
- `Next Action` の最終決定は `gdd-systematic-debugging` に委譲する

## Fixed Model

- `Claude Code`: `sonnet` + `effort=medium`
- `Cursor`: `Grok 4.5` + `reasoning.effort=medium` / `Codex`: `gpt-5.6-terra` + `reasoning.effort=medium`（light tier）
- failure の構造化までは軽いモデルを使い、root cause の最終 route 判断は `gdd-systematic-debugging` に委譲する

## When To Use

- `gdd-test-driven-development` または `gdd-subagent-driven-implementation` で real failing test / executable verification failure が出たとき
- same `Current Task` で失敗が続き、修正前に原因整理を残したいとき
- user が「tests are failing」「RED が崩れた」などとだけ言い、修正より先に failure を整理する必要があるとき

使わない:

- review finding だけで実際の test failure が無いとき
- required security scan evidence や external prerequisite 不足だけが blocker のとき
- `Next Action` や `Resume From` の state 更新だけを決めたいとき
- **silent failure（無反応）**: サービス / bot が一切応答しない、テストが毎回 timeout で fail しており PASS が一度もない → インフラ層の問題の可能性が高い。`gdd-systematic-debugging` に直行する。**timeout でも PASS/FAIL が混在する場合は flaky suspicion として本 skill を使う**
- **expected side effect missing**: テストが PASS に見えたが PR open など期待する副作用が起きていない → 副作用の実態を先に確認する
- 症状の種別が不明な場合は `references/debug-triage.md` で分類してから入口を決める

## Steps

1. active worktree 側 `tasklist.md` の `Current Task` と failing command を確認する。
2. failing command / test name / input / env 差分を最小再現として固定する。再現に前提がある場合は省略せず書く。
2b. **Regression チェック**: このテストは以前 PASS していたか？
    - PASS していた場合: `git log --oneline -10` で直近の変更を確認し、failing test / 関連ファイルに触れたコミットを特定する。特定できた場合はそのコミットを Evidence の最有力候補として Step 5 に書く
    - 初回実装で最初から RED の場合: このステップはスキップ
3. `Expected` と `Actual` を分ける。assertion text, stack trace, exit code のどれが主要証跡かも明記する。
4. `Failure Surface` を切り分ける。
   - test bug
   - implementation bug
   - test data / fixture bug
   - env / timing / flaky suspicion → **Handoff 前にテストを 3 回再実行して再現率を記録する**:
     - 3/3 再現: flaky ではない → 通常の Handoff
     - 1-2/3 再現: Evidence に「再現率 N/3」を記載し、`Confidence: low` + `Open Doubts` に「flaky 疑い」を明記して Handoff
     - 0/3 再現: 一時的環境問題の可能性。再現手順を見直してから再度実行する
   - planning issue suspicion
5. strongest evidence だけを 1-3 点書く。推測だけで root cause を断定しない。
6. `Root Cause Hypothesis` を 1 つに絞り、`Confidence` を `high|medium|low` で添える。競合仮説が残るなら `Open Doubts` に短く残す。
   - `high`: 証拠から断定できる（stack trace / commit が直接指している）
   - `medium`: 有力仮説が 1 つに絞れているが確認が必要
   - `low`: 複数の仮説が残存し証拠だけでは断定できない → 「Confidence: low の場合の調査拡張」を実行する
7. `Workaround` は暫定策だけを書く。恒久修正と混ぜない。
8. `Fix Plan` は最小差分で書く。**競合仮説が複数ある場合は優先順位を付け、試す順序を明記する。複数の変更を同時に加えない（何が効いたか判別できなくなるため）。**
   - 例: 「① import パス修正を試す → PASS しなければ ② 初期化順序を変える」
   - requirements / design を変える案が必要でも、route 変更はまだ行わない。
9. `Worklog Decision` を `yes|no + reason` で書く。
   - `yes`: same `Current Task` で再発、non-obvious root cause、route escalation 可能性、operator risk がある
   - `no`: first local failure で原因と fix plan が単純
10. 最後に `Handoff to gdd-systematic-debugging` を 1-3 行で書く。`Next Action` はこの skill 自身では更新しない。

## Confidence: low の場合の調査拡張

`Confidence: low` のまま Handoff すると `gdd-systematic-debugging` が根拠不足で routing を誤るリスクがある。Handoff 前に **`root-cause-investigation` skill の Phase 1〜3 を回して** Confidence を上げる:

1. **Phase 1（事実収集）の補完**: エラー精読 / 再現条件 / 直近変更 / 境界証跡 / data flow source 追跡を、pack で抜けている観点だけ追加で実施する
2. **Phase 2（pattern 比較）**: 動いている類似実装を探し、差分を全部列挙する
3. **Phase 3（仮説検証）**: 仮説を 1 個に絞り、最小変更で検証する
   - 検証で root cause が確定: Hypothesis を更新して Confidence を `medium` 以上に上げてから Handoff
   - 確定できない: `Open Doubts` に残して `Confidence: low` のまま Handoff（routing の判断は `gdd-systematic-debugging` に委譲）

`root-cause-investigation` の output template をそのまま pack の `Evidence` / `Root Cause Hypothesis` に転記してもよい。類似例が見つからない場合や差分が絞れない場合は、無理に Confidence を上げず `low` のまま Handoff し、`Open Doubts` に「類似例なし」「差分が複数残存」と明記する。

## Output Template

次の構造で返す。後続 skill が素早く読めるよう、見出し名は変えない。

### Test Failure Debug Pack

- `Current Task`:
- `Failure Command`:
- `Reproduction`:
- `Expected`:
- `Actual`:
- `Failure Surface`:
- `Evidence`:
- `Root Cause Hypothesis`:
- `Confidence`:
- `Open Doubts`:
- `Workaround`:
- `Fix Plan`:
- `Worklog Decision`: `yes|no + reason`
- `Handoff to gdd-systematic-debugging`:

## Guardrails

- failing test を再実行せずに pack を捏造しない
- `Expected` と `Actual` を混ぜない
- stack trace 全文をそのまま貼るより、判断に効く部分を短く抜く
- root cause を証拠なしで確定しない
- workaround と恒久修正を混ぜない
- この skill だけで `Next Action` / `Resume From` を更新しない
- planning / human check への差し戻し判断は `gdd-systematic-debugging` に委譲する
