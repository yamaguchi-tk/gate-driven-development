# Rationalization Root Causes

GDD workflow を進めるなかで AI / 人間が「省略してよさそう」と感じる瞬間の **認知バイアス** と **コスト構造** を、再利用可能なカタログにする。各 skill の Rationalization Check 表の `Why` 列はここを参照する。

「合理化に対する反論」を毎回 ad-hoc に書くと、説得力が skill ごとにバラつき、新しい skill を作るたびに似た反論を書き直すことになる。共通カタログにして名前を付ければ、`Why: [Sunk Cost Fallacy]` の 1 ラベルで背景を呼び出せる。

## カタログの使い方

skill 内の Rationalization Check 表は 3 列にする:

```markdown
| 合理化 | 現実 | Why |
|---|---|---|
| 「「要件は明らかなのですぐ設計にいく」 | 「明らか」の 4 割は暗黙の前提が含まれる | [Curse of Knowledge] 自分が知っていることを他人も知っていると錠話しがち |
```

`Why` 列には **ラベル + 1-2 行の要約** を書く。詳しい背景はこのファイルに残し、skill 側を肥大化させない。

## バイアスカタログ

### [Sunk Cost Fallacy] 既に投じたコストを惜しんで撤退できない

- **症状**: 「ここまで brainstorming したから、多少違和感あっても進めたい」「3 回 fix したから 4 回目も試したい」
- **構造**: 過去の投資は意思決定に無関係（経済学の意思決定理論）。「既に払ったコスト」を「これから払うコスト」に加算してしまう
- **GDD で出やすい場面**:
  - planning phase で人間 check を得たあとに違和感が見つかったとき
  - debug loop で 2 回失敗したあと
  - design-gating の修正を 2 周回したあと
- **対抗策**: 「もし今ゼロから始めるとして、この選択をするか？」と自問する

### [Curse of Knowledge] 自分が知っていることを他人も知っていると錯覚する

- **症状**: 「これは自明だから AC に書かなくていい」「context は明らかなので任せる」
- **構造**: 説明者の脳内モデルと受信者の脳内モデルが同じだと無意識に仮定する。文書化を省く動機になる
- **GDD で出やすい場面**:
  - requirements.md の AC が暗黙の前提を含む
  - implementer subagent への briefing で前提を省く
  - reviewer への context が薄い
- **対抗策**: 「新規メンバーがこの artifact だけ見て同じ結論に到達できるか？」と自問する

### [Confirmation Bias] 仮説を支持する証拠だけを集める

- **症状**: 「これが root cause に違いない、確認のためにこのログだけ見よう」
- **構造**: 仮説を反証する証拠より支持する証拠を探す傾向。debug で fix を当てたあと「動いた」だけで満足する
- **GDD で出やすい場面**:
  - debug の Phase 3 で仮説検証が甘い
  - reviewer 指摘への反論で「これは false positive」と決めつける
  - completion-check で AC pass の証跡だけ集めて drift を見逃す
- **対抗策**: 「この仮説が間違っているとしたら、どんな証跡が見えるか？」を先に書く

### [Planning Fallacy] 自分のタスク完了時間を過小評価する

- **症状**: 「これは小さい変更なので Express で十分」「subagent 並列化は overkill」
- **構造**: 楽観的な best case を base case と勘違いする。過去の類似タスクの実測値より自分の見積もりを信じる
- **GDD で出やすい場面**:
  - Task Size 選定（quick / standard / express）の誤判定
  - brainstorming の Honest Limitations を省く
  - task-breakdown の Step Granularity が粗い
- **対抗策**: 「同じ scope で過去 3 回の workflow 実績はどうだったか」を Steering metrics で確認する

### [Locus of Control Drift] 責任の主体が曖昧になる

- **症状**: 「brainstorming で AI が方向性を決めてくれ」「AC は reviewer に判断を任せる」
- **構造**: 意思決定の所在が AI / 人間 / reviewer の間で滑る。後で「誰が決めたか」を問えなくなる
- **GDD で出やすい場面**:
  - brainstorming の Design Policy Discussion で AI が代表選定する
  - requirements-gating で AC を人間 check に「丸投げ」する
  - implementation-gating の reviewer 指摘を全部 implementer に転送する
- **対抗策**: 各 phase の責務を「誰が決めるか」で名指しする（AI / 人間 / reviewer）

### [Bias for Action] 動いている方が正しい気がする

- **症状**: 「仮説を立てる前にとりあえず変更してみる」「root cause 不明のまま fix を当てる」
- **構造**: 進捗が見えないと不安になり、思考より行動を優先する。失敗データが蓄積しない
- **GDD で出やすい場面**:
  - debug で root-cause-investigation を飛ばす
  - implementation で TDD の RED を作らずに GREEN に着手
  - completion-check の AC verification を省略
- **対抗策**: 「次の 5 分で動くか動かないか分かる仮説を立ててから手を動かす」を iron law にする

### [Authority Substitution] reviewer / AC を「正解」と扱いすぎる

- **症状**: 「reviewer が High と言ったから盲目的に直す」「AC が pass しているから OK」
- **構造**: 判断を外部の権威に委ね、自分で評価しなくなる。reviewer の false positive や AC の drift を catch できない
- **GDD で出やすい場面**:
  - implementation-gating で reviewer の Medium を全部受け入れる
  - completion-check で AC pass を「実装が正しい」と等価視する
  - PR review で CI green を「全部OK」と読む
- **対抗策**: reviewer 指摘は「妥当性確認 → 修正方針決定 → 修正」の 3 ステップを踏む。AC pass と「実装の正しさ」は別問題と扱う

### [Context Compaction Overconfidence] 圧縮された記憶を正本扱いする

- **症状**: 「state.md を読み返さなくても前回の判断は覚えている」「routing decision tree は前回と同じはず」
- **構造**: context compaction で要約された情報を full fidelity と勘違いする。Fix Attempts カウンタや Route In Progress が劣化していても気付けない
- **GDD で出やすい場面**:
  - 長い debug loop の途中で routing 判断を間違える
  - 再開時に state.md / tasklist.md を re-read しない
  - 過去の reviewer 指摘を「対応済み」と勘違いする
- **対抗策**: route 判定 / Phase Gate 評価の前に必ずディスクから state.md と tasklist.md を re-read する

### [Scope Creep Justification] 「ついでに直す」を自己許可する

- **症状**: 「リファクタも入れちゃおう」「テスト追加もここで」「コメントも整理しちゃう」
- **構造**: 一回のコンテキストで複数変更したくなる衝動。fix の効果が分離できなくなり、reviewer の負荷も増える
- **GDD で出やすい場面**:
  - implementation で REFACTOR checkpoint と関係ない変更が混ざる
  - debug fix に「気になっていた周辺整理」が便乗する
  - PR review で「ついでに dependency 更新」が紛れる
- **対抗策**: 「今の Current Task の AC に書いてあるか？」を Yes/No で判定。No なら別 task / 別 PR

### [Premature Closure] 早く done にしたい欲求

- **症状**: 「これで AC は概ね満たしている」「残りは些細なので completion-check 飛ばす」
- **構造**: 認知的負荷の高い task を早く終わらせたい本能。verification を省いてもバレないと無意識に賭ける
- **GDD で出やすい場面**:
  - completion-check で stub detection を省く
  - Express path で AC verification を「pass のはず」で済ます
  - PR を急いで作って pr-review を省略
- **対抗策**: 「done と claim する前に、reviewer が探す probe を自分で先回り実行したか？」を iron law にする

### [Recency Bias] 直前の経験を一般法則扱いする

- **症状**: 「前回の workflow ではこれで OK だった」「先週の reviewer はこれを High にしなかった」
- **構造**: 最近の事例を全体傾向と混同する。reviewer calibration や AC pattern を過剰一般化する
- **GDD で出やすい場面**:
  - reviewer calibration で 1 件の指摘を learned-pattern に昇格させる
  - 過去 1 回の brainstorming で「これは Express で良い」を default 化する
  - 過去の AC pattern を新規 requirements にコピペ
- **対抗策**: 「直近 N 回の事例で何回これが当てはまったか」を Steering metrics で確認する

### [Tooling Faith] ツールが完璧と信じる

- **症状**: 「test が pass しているから OK」「lint が通るから問題ない」「CI green だから merge していい」
- **構造**: 自動化ツールの coverage を 100% と勘違いする。assertion の質や test surface の完備性を疑わない
- **GDD で出やすい場面**:
  - TDD で RED の質を吟味せず GREEN に進む
  - completion-check で stub detection を CI に丸投げ
  - PR review で linter / CI 通過 = OK と判定
- **対抗策**: 「test が pass する = 実装が正しい」ではなく、「test の網羅性 × 実装の正しさ = 信頼度」と再定義する

## カタログの拡張ルール

新しいバイアスを追加する場合は以下を満たすこと:

1. **GDD で再現可能な症状**: 抽象的な「焦り」ではなく、どの skill / phase で出るかを明示
2. **構造の説明**: なぜそのバイアスが起こるか、認知科学・経済学・意思決定理論の文献で裏付け可能なもの
3. **対抗策**: skill 内で実行できる具体的 action

汎用的すぎる（「楽したい」など）は採択しない。GDD workflow の意思決定点と紐付けられるものに絞る。

### 追加判定チェックリスト

新しいバイアスを追加する前に、以下を全てチェック。1 つでも No なら採択しない（既存ラベルで代用 / 採択見送り）:

- [ ] **既存 12 ラベルで代替不能**: 似た意味のラベル（特に `[Premature Closure]` / `[Bias for Action]` / `[Curse of Knowledge]`）で同じ Rationalization 行を Why 化できないか確認した
- [ ] **症状の具体性**: どの skill / phase で出るかを具体的に書ける（「いつでも」は不可）
- [ ] **頻度根拠**: 過去の workflow セッションログ / `worklog.md` / reviewer 指摘で 2 回以上観測されている、または合理的に頻発が予想される
- [ ] **構造の裏付け**: 認知科学・経済学・意思決定理論で名前が付いているバイアスである（独自命名は避ける）
- [ ] **対抗策の実行可能性**: skill の Steps / Guardrails / Rationalization Check の Why 列に書ける具体的 action がある
- [ ] **既存 skill への適用例**: 追加した瞬間に最低 1 つの既存 skill の Rationalization 行で `[新ラベル]` を使える
- [ ] **重複ラベルが他に無い**: 同じバイアスが既存 12 ラベルのどれかと違う名前で重複していない

採択時の手順:

1. このカタログの末尾に新エントリを追加（症状 / 構造 / GDD で出やすい場面 / 対抗策の 4 要素）
2. 適用例となる既存 skill の Rationalization Check 行を更新し、Why 列に `[新ラベル]` を入れる
3. 変更断片（`changelog.d/`）の `type` を `minor` にする（reference 追加扱い）
4. `gdd-writing-skills` § Rationalization Check ルールに新ラベルが反映されていることを確認（テンプレートに list があれば追記）

### 削除 / リネームの判定

既存ラベルを削除 or リネームするときは以下を確認:

- 使用箇所が 1 件以下 → 統合・削除候補
- 12 ラベル中で最も近い 1-2 個と毎回セット使用されている → 統合候補
- ラベル名が `[Long-Phrase Name]` で長すぎる → リネーム候補

リネーム / 削除は **major bump 級の破壊変更**。実施時は全 skill の Why 列を grep して同時更新する。
