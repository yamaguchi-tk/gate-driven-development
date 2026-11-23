# Parallel Failure Investigation

> **所有**: root cause が未確定で hypothesis が複数残っているときの「並列調査 dispatch」パターン
> **上位正本**: なし（補助 reference）
> **参照元**: `root-cause-investigation`、`gdd-systematic-debugging`

`root-cause-investigation` の通常 path（hypothesis を 1 つずつ検証）では時間がかかりすぎる、または hypothesis 同士が**独立**で並列に検証できるときに使う補助パターン。

`gdd-subagent-driven-implementation` の Execution Plan = parallel（承認済み tasklist 内の並列実行）とは別物。こちらは **planning / debugging 段階での hypothesis 並列**を扱う。

## Independent Failure Domain Dispatch

superpowers `dispatching-parallel-agents` から取り込む中核ルールは **one agent per independent problem domain**。速くするための並列化ではなく、独立した failure-domain を分離して原因候補を潰すための並列化である。

- Use only when each hypothesis has no shared state, no order dependency, no overlapping files, and no shared external resource.
- Do not use for related failures。たとえば同一 root cause から派生した related failures、同じ API 契約の両端、同じ state.md / tasklist.md field、同じ migration / fixture を触る hypothesis は 1 domain として sequential に扱う。
- 各 subagent には focused かつ self-contained な prompt を渡し、親 session の暗黙 context に依存させない。
- result merge は controller が行う。subagent の報告を足し合わせて結論にせず、evidence を読んで root cause / symptom / inconclusive に再分類する。
- 全 subagent 完了後は conflict check と full suite を実行してから route を決める。

## 発火条件（すべて満たすときに検討）

1. **root cause が未確定**で、`root-cause-investigation` 内で hypothesis が **2-4 件**残っている
2. 各 hypothesis が **独立に検証可能**（共有 state や順序依存がない）
3. hypothesis ごとの検証コストが**それぞれ 5+ ターン相当**で sequential には重い
4. hypothesis のいずれかが「裏」と判明すると routing が大きく変わる（=早期に絞り込み価値が高い）
5. agents が shared state（同一 file、同一 state.md / tasklist.md field、同一 external resource、同一 long-running process）を同時に編集・操作しない

1 件でも満たさなければ通常の sequential 検証に倒す。

## Anti-Pattern（並列にしてはいけないケース）

- hypothesis A の結果で hypothesis B の検証内容が変わる（**依存**）
- 検証コストがすべて軽い（1-2 ターン）→ オーバーヘッドが上回る
- root cause がすでに 1 つに絞られている → 並列にする意味がない
- 共有ファイルや shared lock を全 hypothesis が触る → race condition
- shared state の所有者が曖昧なまま dispatch する → result merge で evidence や修正が上書きされる

## 並列 dispatch の手順

### 1. Failure-Domain Decomposition

root cause hypothesis を以下の軸で「failure-domain」に分割する:

| Domain | 例 |
|---|---|
| **環境 / 設定** | env var 不一致、IAM 権限不足、Terraform drift |
| **コード** | ロジックバグ、契約違反、型不整合 |
| **データ / 状態** | DB schema drift、stale cache、orphan record |
| **外部依存** | API 仕様変更、rate limit、外部サービス障害 |
| **テスト / CI** | flaky test、test fixture drift、CI 環境差分 |
| **タイミング / race** | 並行性バグ、deadlock、初期化順序 |

各 hypothesis を 1 つの domain に紐付け、domain が重複しないようにする（同じ domain なら 1 subagent にまとめる）。

### 2. Subagent Dispatch Template

各 hypothesis に対して `Explore` または `general-purpose` agent を**1 メッセージで並列起動**する。各 subagent への prompt は以下のフォーマット:

```
## 調査対象 hypothesis

<1 文で hypothesis を書く>

## Failure Domain

<上記表の domain 名>

## 入力 / 既知の事実

- <観測された症状>
- <関連 file path / log path>
- <試した範囲、除外できた可能性>

## 検証手順

1. <具体的な確認コマンド・ファイル読み・grep>
2. <次に確認する箇所>
3. <hypothesis を裏付ける / 否定する evidence の判定基準>

## 期待する報告フォーマット（300 語以内）

- **判定**: `confirmed` / `refuted` / `inconclusive`
- **Evidence**: 上記判定の根拠 3 行以内
- **次の hypothesis 候補**: refuted / inconclusive の場合のみ、新たに浮上した可能性 1-2 件
- **副次的発見**: 主 hypothesis 以外で気付いた点
```

## 3. Result Merge

全 subagent の報告を受けたら以下を順に処理する:

1. **`confirmed` が 1 件**: それを root cause として `Routing Decision Tree` に通す。他は副次的発見として `worklog.md` に記録
2. **`confirmed` が 2+ 件**: 真の root cause が複数併存している。各 confirmed を独立 task として扱うか、最も上流の 1 件を root cause、他を symptom として再分類する（再分類は 1-2 ターンの追加調査で決める）
3. **全て `refuted`**: 新たな hypothesis 候補（各 subagent が報告した次候補）から 2-4 件を選び、再度並列 dispatch（最大 2 ラウンドまで）
4. **全て `inconclusive`**: hypothesis 自体の質が低い。並列を打ち切り、`root-cause-investigation` の sequential 詳細調査に戻す

## Loop Safety

- 並列 dispatch は **最大 2 ラウンド**まで。これを超えても root cause が確定しない場合は `human_recheck_required` route に escalate
- 同一 hypothesis を 2 ラウンド連続で並列調査しない（前ラウンドで `inconclusive` だった hypothesis は sequential で深掘り）
- ラウンドごとの結果は `worklog.md` の `## Parallel Investigation Rounds` セクションに追記する

## Express パスでの制約

`Task Size: quick (express)` では並列 dispatch を**使わない**。express は単純なバグ修正想定で、hypothesis 複数並列が必要な複雑な root cause 探索は sizing 不一致を示唆する。Express で並列調査が必要になった時点で sizing 昇格（`quick (standard)` 以上）を提案する。

## State 記録

並列調査を実行したら `state.md` に以下を追記する:

```
Parallel Investigation Rounds:
- Round 1: <ISO8601> | hypotheses=3 | confirmed=0 | refuted=2 | inconclusive=1
- Round 2: <ISO8601> | hypotheses=2 | confirmed=1 | refuted=1 | inconclusive=0
```

確定した root cause は `Routing Decision Tree` で通常 path に戻る。

## superpowers との対応

このパターンは superpowers の `dispatching-parallel-agents` skill から「failure-domain 並列化」要素を抽出して GDD の `root-cause-investigation` / `gdd-systematic-debugging` に統合したもの。superpowers では skill 化されているが、GDD では reference として既存 skill から参照する形を採用（skill 数の肥大を避ける）。
