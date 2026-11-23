# Benchmark Scenarios（superpowers との比較ベンチマーク）

GDD primitive と superpowers 同等品の **直接比較ベンチマーク用シナリオ集**。`empirical-prompt-tuning` skill を回す際に、GDD primitive の standalone 質を superpowers 同等品と比較するために使う。

## 目的

- 「GDD primitive は standalone でも superpowers 同等品と等速 or 上回る」を release-criteria として測定可能にする
- 改修時の hold-out gate（`empirical-prompt-tuning` の Hold-out Regression Gate）の入力にする
- 「superpowers でいい」と判定されない raw quality を継続維持する

## 評価軸

各シナリオで両 skill を実行し、以下を測る:

| 軸 | 取り方 | 合格基準 |
|---|---|---|
| 精度 | 要件チェックリストの達成率 % | GDD ≥ superpowers - 5pt |
| steps | Task tool usage の `tool_uses` | GDD ≤ superpowers × 1.5 |
| duration | Task tool usage の `duration_ms` | GDD ≤ superpowers × 1.5 |
| retries | subagent 自己申告 | 両者とも 0 |
| state machine 連動有無 | GDD のみ追加軸 | GDD は State Machine Integration block を出力（root-cause-investigation 等） |

GDD が steps / duration で 1.5 倍を超える場合、`empirical-prompt-tuning` を回して raw quality を改善する。

## Release Gate

changed GDD primitive（`gdd-brainstorming` / `gdd-test-driven-development` / `gdd-subagent-driven-implementation` / `root-cause-investigation` など superpowers 同等品がある primitive）を変更した場合、該当 Pair の benchmark scenario を release evidence として扱う。

- `SUPERPOWERS_BENCHMARK_REQUIRED=true`: validate 時に benchmark evidence の提示を要求する
- `SUPERPOWERS_BENCHMARK_EVIDENCE=<path-or-summary>`: `.steering/<task>/findings.md` など、GDD 版 / superpowers 版の比較結果を指す
- evidence には対象 primitive、実行した scenario、GDD / superpowers の checklist 達成率、steps / duration / retries、GDD 固有軸（state machine 連動）が含まれていること
- benchmark を実行しない場合は、`SUPERPOWERS_BENCHMARK_REQUIRED` を立てず、PR / release note に「primitive 変更なし」と書く

この gate は「すべての validate で常に benchmark を走らせる」ものではない。changed GDD primitive の raw quality drift を release 前に検出するための opt-in release gate である。

## シナリオ集

### Pair 1: root-cause-investigation vs superpowers:systematic-debugging

#### Scenario A: 単一 commit regression（軽量）

```
症状: pytest tests/test_pagination.py::test_cursor_pagination が AttributeError で失敗。
コンテキスト: 直近 3 commit のうち 1 つで `paginate` メソッドを別名にリネームしている。
期待: git log -S paginate で commit 特定 → Phase 4 で fix 提案。
要件チェックリスト:
1. [critical] 主因 commit を一意に特定する
2. [critical] failing test を Phase 4 で明示する
3. fix 対象ファイル / 行を 1 つに絞る
4. Early Exit を判定して Phase 2/3 を skip する（commit 一意特定済みのため）
5. （GDD のみ）State Machine Integration block を出力する
```

#### Scenario B: multi-layer secret 伝播

```
症状: signing step が "IDENTITY not set" エラー。
コンテキスト: GitHub Actions workflow → build script → security tool の 3 layer で secret 伝播。
期待: 各 layer に probe を入れて欠落 layer を特定 → Phase 4 で fix。
要件チェックリスト:
1. [critical] 各 layer で probe を実行し欠落 layer を特定する
2. [critical] root cause が「どの layer の env 設定漏れか」で確定する
3. multi-layer-probing.md を参照する
4. fix を当てる layer を 1 つに絞る
5. （GDD のみ）ADR 起票判定で「環境依存・再調査防止」として true を出力
```

#### Scenario C: flaky test

```
症状: tests/test_async.py::test_event_order が CI で 30% の頻度で失敗。local では再現しない。
コンテキスト: 非同期処理 / sleep 依存 / event loop の serialization order。
期待: deterministic 再現が取れないため root cause 未確定 → Phase 4 で追加データ収集提案。
要件チェックリスト:
1. [critical] 再現性が intermittent と認識される
2. [critical] root cause 未確定で Phase 4 を出力（fix 提案しない）
3. 追加データ収集の具体内容（instrumentation / 観測強化）を提案する
4. Iron Law（NO FIX WITHOUT ROOT CAUSE）を遵守する
```

### Pair 2: gdd-test-driven-development vs superpowers:test-driven-development

#### Scenario D: AC ID 付き RED 作成

```
要件: requirements.md に AC-1（cursor pagination 対応）と AC-2（next_cursor の null 判定）が定義されている。
期待: 両 AC をカバーする RED Evidence を作成し、各 AC ID を `AC:` 行に記載。
要件チェックリスト:
1. [critical] RED Evidence が 2 件作成される（AC-1 / AC-2 それぞれ）
2. [critical] 各 RED Evidence に `AC: AC-X` 行がある
3. テストフレームワーク失敗 output が記録される
4. Contract Surface Coverage で success path / validation path が applicable と判定される
5. （GDD のみ）AC ID 未紐付け時に fail-closed する仕組みが文書化されている
```

#### Scenario E: テストフレームワーク無し / executable verification

```
要件: shell script のみのリポジトリで AC-1（特定 env var が export されること）を担保する RED を作成。
期待: 形式 2（executable verification）で `env | grep VAR` などの検証手順を記録。
要件チェックリスト:
1. [critical] executable verification 形式で RED を作成する
2. [critical] AC ID が `AC:` 行に記載される
3. expected / current の差分が明示される
4. テストフレームワーク無しの理由が記録される
```

### Pair 3: gdd-brainstorming vs superpowers:brainstorming

#### Scenario F: 新規機能の要件整理

```
入力: 「API レスポンスにキャッシュ層を追加したい。Redis を使う想定。」
期待: requirements.md / lightweight design.md skeleton を生成し、human check 承認ポイントを提示。
要件チェックリスト:
1. [critical] requirements.md に AC が 3 件以上ある
2. [critical] Summary Brief の 4 層（一言 / 判断材料 / 承認ポイント / Honest Limitations）が揃う
3. design.md skeleton に Cache strategy / TTL / fallback の 3 見出しがある
4. Options Exploration で 2-3 案（やらない案含む）が比較される
5. （GDD のみ）Entry Intent: new が state.md に記録される
```

#### Scenario G: amendment（既存機能の修正依頼）

```
入力: 「PR review の Copilot benchmark 評価を拡充したい。」（active steering=20260510-pr168-feed-rdf-strictness）
期待: entry intent=amendment と判定し、gdd-requirements-amendment に委譲。
要件チェックリスト:
1. [critical] entry intent=amendment と判定される
2. [critical] anchor=<既存 feature 名> が判定理由に含まれる
3. gdd-requirements-amendment への委譲が提案される
4. （GDD のみ）Entry Intent セクションが state.md に永続化される
```

## 運用方法

1. **Skill 改修時**: 改修した GDD primitive について、対応シナリオで `empirical-prompt-tuning` を実行
2. **subagent 並列起動**: GDD 版 / superpowers 版それぞれの subagent を並列で起動し、評価軸を測る
3. **Hold-out Regression Gate**: 上記合格基準を満たさない場合、`empirical-prompt-tuning` の Hold-out Regression Gate § quick-gate 例外（5件未満許可）で記録し、release を保留
4. **記録**: 結果は `.steering/<task>/findings.md` に benchmark 結果を残し、必要なら `docs/learned-patterns.md` に固定化

## シナリオ追加ガイド

新しいシナリオを追加するとき:

- **中央値 + edge**: 中央値 1 件 + edge 1-2 件のセット
- **要件チェックリスト**: 3-7 項目、`[critical]` 最低 1 つ
- **GDD 固有軸**: state machine 連動を測る項目を 1 つは含める（GDD primitive 評価の必須軸）
- **superpowers 同等品が無いシナリオは追加しない**: 比較ベンチマークなので必ず両者を走らせられる

## 関連

- `references/superpowers-overlap.md`: GDD と superpowers の overlap map（このベンチマークの上位ドキュメント）
- `empirical-prompt-tuning` skill: ベンチマーク実行方法（subagent 並列・両面評価・Hold-out Regression Gate）
- `references/skill-responsibility-matrix.md`: GDD 内 skill 間の責務分担
