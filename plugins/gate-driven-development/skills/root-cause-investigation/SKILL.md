---
name: root-cause-investigation
description: "Use for root-cause investigation of bugs, failures, regressions, or unexpected behavior before proposing fixes."
version: 0.1.0
---

# Root Cause Investigation

「直す前に、本当の原因を突き止める」ための汎用 methodology。GDD などの workflow に依存せず、どんな debug 場面でも使える。

## Fixed Model

- `Claude Code`: `opus` + `effort=high`
- `Cursor`: `Grok 4.6` + `reasoning.effort=low` / `Codex`: `gpt-5.6-sol` + `reasoning.effort=low`（general_heavy tier）
- 根本原因の誤特定は後続実装全体の手戻りに直結するため、重いモデルで固定する

## GDD Debug Entry

This skill is the standalone debug entry for GDD-adjacent work. For bugs, test failures, silent failures, unexpected behavior, or 「原因を調べたい」 outside an active `/gdd-dev` state, prefer root-cause-investigation over superpowers:systematic-debugging when the user is asking in a GDD/plugin context.

It is artifact-free until GDD state is explicit: do not create `.steering/`, do not resume `.claude/gdd-dev.local.md`, and do not update `Next Action` unless `/gdd-dev` or active GDD state is explicit.

If GDD state exists and root cause is confirmed, hand off to `gdd-systematic-debugging`; otherwise stay standalone.

### Goal-Driven Root Cause Loop

root cause investigation は「1 回調べて終わり」ではない。Goal が「確度の高い原因を見つけ、必要なら修正へ進む」ことで、原因がまだ確定していない場合は `gdd-goal-driven-execution` の Goal-Driven Execution として扱う。

Loop owner の正本は `references/state-machine.md` § Goal-Driven Loop Ownership。`root-cause-investigation` は root cause inner loop を所有し、outer loop / Goal Contract の owner にはならない。

Inner loop handoff: return root cause status to the outer loop with evidence and confidence. This skill does not change Goal Contract; Goal / Done When / Not Changing Without Human の変更が必要なら、修正実装へ進まず `gdd-goal-driven-execution` か `gdd-systematic-debugging` に human recheck route を返す。

- confidence labels: `confirmed / likely / no_root_cause_yet / insufficient_evidence`
- `confirmed`: root cause の因果関係を言葉で説明でき、反証条件を満たしていない。原因が複数なら共同主因セット・寄与要因・検出/回復の欠落を分離して説明できる。Phase 4 と `gdd-systematic-debugging` に handoff 可能
- `likely`: 最有力だが反証が残る。fix allowed: no。追加 probe を Working Hypothesis として次サイクルへ
- `no_root_cause_yet`: 再現はあるが仮説検証が不足。fix allowed: no。仮説を更新して次サイクルへ
- `insufficient_evidence`: 再現条件・log・fixture・環境情報が不足。fix allowed: no。追加証跡を集めるか人間に戻す

### Confirmed Gate: 症状・検出地点・根本原因を分ける

観測されたエラー、アラート、例外、失敗したテスト、最終状態は、まず**症状または検出地点**として扱う。単独では root cause とみなさない。根本原因は「その症状を発生させ、再発を防ぐにはどこを変えるべきか」を説明する上流の条件・変更・設計上の欠落である。

root cause は必ずしも 1 個ではない。独立した複数要因が同時に必要な場合、原因を無理に単一化しない。以下を分けて扱う:

- **共同主因（最小十分原因セット）**: その組合せがそろうと症状を生む最小の条件集合。AND 条件の各要因は、単独で症状を生まなくても共同主因として並べる
- **寄与要因**: 共同主因セットの外にあり、発生確率・頻度・影響範囲を増やしたが、今回の症状に必要ではなかった条件
- **検出/回復の欠落**: 発生自体の原因ではないが、早期検知・隔離・復旧を妨げて利用者影響へ至らせた条件

同じ症状に複数の最小十分原因セットがある場合は、セットごとに並記する。原因のラベルは重要度順ではなく反事実で決める: ある要因を除くとセットが成立しないなら共同主因、除いてもセットが成立するが影響が小さくなるなら寄与要因である。

これらは因果グラフとして表す。直列だけでなく、AND 条件・分岐・複数経路を許容する。

`confirmed` に格上げする前に、必ず次の因果鎖を証拠で埋める:

```text
入力・変更・前提条件群
→ 最初の異常な状態または契約違反（複数可）
→ 症状が利用者影響まで伝播した経路（分岐・増幅・回復失敗を含む）
→ 観測されたエラー / 最終状態
```

- **必須**: 症状の直前に起きた最後の成功・最初の異常・状態遷移を確認する。複数 component、親子処理、retry、fallback、非同期 job がある場合は、それぞれの開始・完了・結果受領を同じ timeline に置く。
- **必須**: 少なくとも 1 つ、同じ症状を生む別の上流仮説を立てて棄却する。棄却できない場合は `likely` 以下とし、fix allowed: no。
- **必須**: 原因が複数ある可能性を確認し、共同主因セット・寄与要因・検出/回復の欠落の各分類に該当なし／候補／確認済みを記録する。
- **必須**: 修正対象が症状の発生地点ではなく、因果グラフで特定した異常またはそれを許した境界・契約であることを説明する。
- **例外**: 観測地点そのものを変えた commit を戻すと症状が消えても、それだけでは一次原因にしない。観測変更が latent defect を露出しただけではなく、最初の異常状態を生成した証拠がある場合だけ、共同主因セットの一部として扱ってよい。

`confirmed` の最低条件は、(a) 最初の異常または最小十分原因セット、(b) 症状まで伝播した因果、(c) 共同主因・寄与要因・検出/回復の欠落の分類、(d) 同じ失敗を防ぐ最小の修正単位、を別々に説明できること。いずれかが欠ける報告は `likely` または `no_root_cause_yet` とする。

**例（終端症状の場合）**: timeout、exit code、HTTP 5xx、OOM、retry exhausted、circuit open、queue full は「どこで止まったか」を示すことがある。これらを一次原因と結論するには、上記の因果鎖に加え、その設定・制限・終端処理自体が最初の異常である証拠が必要。

Current State → Working Hypothesis → probe → confidence 更新を、各 probe が因果グラフを前進させる間は回してよい。probe が新しい証跡・因果関係・棄却を生まない状態が 3 回続いたら、盲目的に続けず `No Root Cause Decision` を出す。時間・費用・利用者影響の調査予算が先に尽きる場合も同様に停止し、`gdd-goal-driven-execution` または `gdd-systematic-debugging` に停止理由と次に必要な証跡を渡す。

出力には以下を含める:

```markdown
Root Cause Confidence:
- status: confirmed | likely | no_root_cause_yet | insufficient_evidence
- cycle: <1/3 | 2/3 | 3/3>
- disproving evidence checked:
- next evidence to collect:
- fix allowed: yes | no
```

## なぜこの skill が要るか

症状に対して最初に思いついた fix を当てる「guess-and-check」は、平均すると systematic な root cause 分析より遅い。理由は以下のいずれかで時間が溶けるから:

- 同じバグの別の症状が後で再発する（root cause が直っていない）
- fix が別の場所を壊す（影響範囲を理解せずに変更したため）
- 3 件目以降の fix は、shared state / coupling / leaky abstraction が原因で、もう individual bug ではない
- 「明らか」に見える原因の 3 割は症状で、真因は別にある

このコストを回避するため、fix を当てる前に **常に root cause を特定する** ことを iron law にする。

## Iron Law

> **NO FIX WITHOUT ROOT CAUSE.**

Phase 1〜3 のいずれかを完了せずに Phase 4（実装）に進まない。これを守らなかった瞬間にこの skill を使う意味がない。

## 適用範囲

使うべき場面:

- test failure（unit / integration / e2e いずれも） / silent failure（無反応 / timeout / 副作用が起きない） / production bug（observed misbehavior） / 想定外の挙動（spec と現実がずれている）
- build / CI failure / integration の境界で壊れている疑い / performance 異常

特に **使わなければいけない**:

- 急いでいるとき（焦りは guess を呼ぶ） / 「一発で直りそう」と思ったとき（その直感の 3 割は外れる）
- すでに 1 回以上 fix を試して失敗しているとき / 完全には理解していないとき

「単純すぎて process いらない」も言い訳。単純な bug にも root cause はある。

## 4 Phases

各 phase を順に進める。前 phase の output が次 phase の input になる。

### Phase 1: Root Cause Investigation（事実を集める）

fix を提案する前に、以下を全部やる。

**早期切り上げ条件（Early Exit Criteria）**: 以下を**すべて**満たす場合は Step 4（境界証跡）以降を skip し、**Phase 2 / Phase 3 を簡略化または skip して Phase 4 へ直行**してよい。**過剰な外部リソース調査（CloudWatch / Terraform / 監査ログ等）でコストを浪費しないため**:

1. Step 1〜3（エラーメッセージ + 再現条件 + 直近変更）だけで **最初の異常を導入した candidate commit が一意に特定**できた（`git log -S <symbol>` の結果が **1 件** に絞れる、または candidate 2 件以下 + 直近変更で 1 件に確定できる）
2. `git log -S <symbol>` / `git show <commit>` で **regression の入った commit と回復方法**が両方確定した
3. 再現性が **deterministic** に確認できた（intermittent / flaky でない）
4. system が single-component（単一プロセス / 単一サービス）で multi-layer の secret 伝播・boundary 問題が原因として考えにくい

該当する典型例: 「commit X で削除された変数 / 関数 / attribute が原因の regression」「特定 commit 以降 test が落ちる」など、git history 上で symbol level の出現/削除が決定的な場合。**Early Exit 時の Phase 2 / Phase 3 の扱い**:

- **Phase 2（Pattern Analysis）**: candidate commit が一意なら類似 working code との比較は不要。**完全に skip してよい**。ただし「副次的に他の場所でも同じ pattern が発生していないか」の念のため確認として軽く触れるのは可
- **Phase 3（Hypothesis & Testing）**: `Confirmed Gate` に必要な因果・共同条件・対立仮説の証拠が Step 1〜3 でそろう場合のみ、**完全に skip してよい**。それ以外は不足した因果関係だけを簡略検証する
- **Phase 4（Implementation Handoff）**: **必ず実行**（test を書かずに fix を作らないルールは変わらない）。出力テンプレートの構造もすべて埋める

Early Exit は比較・仮説検証の工数を省くためのものであり、`Confirmed Gate` を迂回しない。`confirmed` とする前に、commit が作った最初の異常、必要なら共同主因セット、症状への伝播、少なくとも1つの対立仮説の棄却を簡潔に記録する。これを満たせない場合は Early Exit でも `likely` 以下とする。

省略可: Phase 2 / Phase 3 を skip / 簡略化した場合は、出力テンプレートの該当セクションに「**Early Exit のため省略**」と 1 行だけ明記して、なぜ skip したかの根拠（一意特定の証拠）を Phase 1 セクションに残す。

**通常 path（早期切り上げに該当しない場合）**: 以下を全部やる:

1. **エラーメッセージを最後まで読む** — stack trace は省略せず読む / 行番号・ファイルパス・エラーコードを記録する
   - warning も無視しない（root cause の手がかりがそこにあることが多い）

2. **再現条件を固定する**
   - 必ず再現できるか？ / 再現手順は何ステップか？ / 毎回起きるのか、たまに起きるのか？
   - 再現できないなら、まずデータ収集（再現データを集める）に戻る。再現できない状態で fix を提案しない

3. **直近の変更を確認する**
   - `git log --oneline -20` / `git diff` で関連箇所の最近の変更を見る / 新しい依存追加、config 変更、env 変数の追加・削除 / 環境差分（local では動くが CI で落ちる、など）
   - 過去 6 か月で同一 symbol の出現回数が変化した commit（`git log -S` の pickaxe 検索結果）のうち fix / 修正相当のものが 3 件以上ないか `git log --since="6 months ago" -S"<symbol>" --oneline` で確認する（`<symbol>` はプレースホルダ。クォートしないとシェルにリダイレクトとして解釈されるため必ずクォートする。Architecture Check の履歴パターン発火条件）

4. **境界ごとに証跡を集める（multi-component の場合）**

   システムが複数 component（CI → build → sign / API → service → DB / workflow → Lambda → handler 等）にまたがる場合、**どの境界で壊れているか** を特定する前に fix を提案しない。

   各 component 境界で: 入ってくる値をログに出す / 出ていく値をログに出す / 環境変数・config の伝播を確認する / 各層の state を確認する。1 回流して証跡を集める → どの層で壊れているかを特定する → その層を深掘りする、の順序を守る。

   **非同期・複数実行主体の追加必須証跡**: 親 job、子 task / lane、retry、fallback、queue を含む場合、最後に観測されたエラーだけで止めない。少なくとも `開始時刻 / 最初の異常 / 後続の状態遷移 / 結果受領 / 終端または利用者影響` を列にした timeline または happens-before 図を作る。時計ずれ・欠損ログで全順序が作れない場合は、correlation ID、親子関係、request ID 等で確認できる部分順序を示す。各関係について「次に誰が何をしたか」を 1 文で説明し、説明不能な空白は未確認として残す。

   例（multi-layer の secret 伝播）:
   ```bash
   # Layer 1: Workflow
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Build script
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Signing
   security find-identity -v
   ```
   → どの層で `IDENTITY` が失われているかが特定できる。layer 構成ごとの具体テンプレート（CI/CD / Lambda / Web stack / Container / データパイプライン）は **`./references/multi-layer-probing.md`** を参照。複数 env 変数の伝播を 1 コマンドで検証するには **`scripts/verify-env-propagation.sh`** を各 layer で `LAYER_NAME=<layer> ./verify-env-propagation.sh VAR1 VAR2 ...` の形で実行する（masking 付き、SET / SET_EMPTY / UNSET の 3 状態を返す）。

5. **データフローを source まで遡る**

   error が call stack の深いところで出ている場合、「悪い値はどこで生まれたか」を遡る: その悪い値を渡したのは誰か / そいつにその値を渡したのは誰か / source まで辿り、source で直す。症状の場所で fix すると、別の経路から同じ悪い値が来たときに再発する。

   call stack が深く、手動で遡るのが困難な場合は **`./references/call-stack-tracing.md`** を参照。各言語（JS / TS / Python / Go / Shell）の stack trace instrumentation コード、各 hop で記録すべき情報、fix を当てる場所の判定（source / 中間 / defense-in-depth）、アンチパターン（観測点で握りつぶす / try-catch で握りつぶす）が網羅されている。

### Phase 2: Pattern Analysis（似ているものと比べる）

事実が集まったら、似た working code を探して差分を取る:

**典型的な failure pattern を素早く照合する場合は `./references/common-failure-patterns.md` を参照**。env 伝播ロス / token 期限切れ / timing 依存 / quota / DNS / serialization / permission / cache / version mismatch / silent swallowed error / feature flag / timezone / storage / 型不一致 / concurrent modification の 15 パターンに、典型的 root cause と proving probe をまとめている。同じ shape の症状を見つけたら、それを Phase 3 の仮説候補にする。該当パターンが無ければ通常通り codebase 内比較を進める。

1. **動いている類似実装を探す** — 同じ codebase 内で似たことをしている箇所はないか / 動いている版と壊れている版の差分が root cause の候補
2. **参照実装があれば全文を読む** — 「だいたい同じ」では bug が混入する。差分を全部列挙する / 「これは関係ないはず」という直感は保留する（その直感が外れて 1 時間溶ける）
3. **差分を全部書き出す** — small differences こそ root cause になる / 順序、option の有無、default 値、timing、env
4. **依存関係を理解する** — 何の component / config / env が前提か / その前提が今満たされているか

### Phase 3: Hypothesis & Testing（仮説を 1 個ずつ検証する）

集めた事実と差分から、仮説を立てて検証する:

1. **検証対象の仮説は 1 つに絞り、文章で書く** — 原因候補は複数持ってよいが、1 回の probe では 1 つの因果関係だけを検証する。「X は共同主因（または寄与要因）だと考える。理由は Y」 / 曖昧な仮説は曖昧な検証しかできない
2. **最小の変更で検証する** — 1 度に 1 変数だけ動かす / 複数同時に変えると、何が効いたか分からなくなる
3. **検証結果で因果グラフを更新する** — 仮説どおりなら、その因果関係をグラフへ追加する。共同主因セット・別経路・検出/回復の欠落に未検証の必須候補が残る間は Phase 4 へ進まない。外れた場合は新しい仮説を立てる。fix を積まない
   - 「分からない」も valid な結論。分からないことを「分かったふり」しない
4. **手詰まりなら止まる** — 「分からない X がある」と明示する / 追加情報を取りに行くか、人間に聞く
5. **並列調査の検討（hypothesis が 2-4 件、各検証が重い場合）** — hypothesis が 2-4 件残っており、各々が**独立に検証可能**で sequential には時間がかかりすぎる場合、**failure-domain 並列調査**を検討する。並列にして良い: 環境 / コード / データ / 外部依存 / テスト / タイミング のような **異なる failure-domain** に分けられる仮説
   - 詳細手順・発火条件・anti-pattern・loop safety は `references/parallel-failure-investigation.md`
   - 並列にしない: hypothesis A の結果で hypothesis B の検証内容が変わる依存関係がある場合、検証コストが軽い場合、root cause が既に絞れている場合

### Phase 4: Implementation Handoff（root cause が確定したら）

root cause を特定したら、fix の実装に移る。ただし以下を守る:

1. **failing test を先に書く**
   - root cause を assert する最小の failing test を作る / 自動化できないなら手動再現手順を残す / test が無い fix は「直ったつもり」になりやすい
2. **因果要因と是正制御を分ける** — root cause は因果要因、入力検証・circuit breaker・監視などは escape point または是正制御として記録する。是正制御を root cause と呼ばない。
3. **fix は 1 作業単位に絞る** — 単一原因なら 1 つの fix、複数原因なら因果グラフで必要と確認した最小の整合した fix セットだけを入れる。「ついでにここも直す」「リファクタも入れる」をやらない（何が効いたか分からなくなる）
4. **verify する** — failing test が pass するか / 他の test が壊れていないか / 元の症状が消えているか
5. **fix が効かなかったら止まる** — 試行回数を数える
   - 3 回未満なら Phase 1 に戻り、新しい情報込みで再分析
   - 3 回以上失敗 → 次の Architecture Check に進む

#### 出力構造のルール

調査結果を呼び出し側に報告するとき、以下の構造で出力する。**root cause が確定したか / 未確定か** によって最優先アクションの中身が変わる:

1. **最優先アクション top 1（必須）**: 「**最優先**: 〇〇」の形で**1 つだけ**明示。複数の改善余地があっても、即着手すべきものを 1 つに絞る。**root cause 確定時**: 最優先 = **fix 実装**（failing test を先に書く / fix 対象を明示）
   - **root cause 未確定時**（flaky / 探索的調査 / 情報不足）: 最優先 = **追加データ収集**（再現手順の確立 / instrumentation / 観測強化）。fix 対象は「未定（root cause 確定後）」と明記し、**fix を提案しない**（Iron Law: NO FIX WITHOUT ROOT CAUSE）
   - **Architecture Check 発火時**: 最優先 = **人間への相談**。この項目内に「発火条件: in-session 3 回失敗 / 履歴パターン一致（該当 commit 一覧）」を明記し、fix は提案しない。深掘り調査やリファクタ計画の作成が必要と判断される場合は、別途 dedicated な調査（人間主導、または別 agent への委任）を推奨する 1 行を添えるに留め、この skill 自身は実行しない
2. **副次アクション 0-3 件（任意）**: 「副次的に対応すべき項目」として優先度の低い項目を列挙。本論と分離して、判断負荷を最優先に集中させる
3. **副次的発見（Side Observations、任意）**: 調査中に**本論とは別に気付いた**項目。bot 文言の不正確性、IaC drift、文書の食い違い、関連 incident の兆候など。**本論と混ぜずに分離して記録**することで、後続タスクに引き継げる
4. **意思決定の question（必須）**: 「**修正に着手しますか?** それとも調査メモのみで止めますか?」のような**明示的な question**で締める。ユーザーが next step を即決できる形にする
   - **root cause 未確定時**は question を「**追加データ収集に着手しますか?** それとも flaky として retry / monitor 等の運用回避に倒しますか?」のように、データ収集 vs 運用回避の選択肢を提示する形にする

混在を避ける理由: top 1 と副次を並列に列挙すると判断負荷が上がる。superpowers の `systematic-debugging` の意思決定促しと、GDD の多層原因分離を両立する。

**root cause 未確定時の Phase 4 一次原因欄の書き方**: 「**一次原因（仮説、未確定）**: 〇〇が最有力」と**未確定であることを明示** / 「**一次原因が確定するまで fix を当てない**」と Iron Law の遵守を明示 / 増悪要因や副次的発見は通常通り記録（観測強化に役立つため）

#### State Machine Integration（GDD workflow 内で呼ばれた場合）

GDD workflow 経由で呼ばれた場合（`gdd-systematic-debugging` / `gdd-test-failure-debug-pack` からの handoff、または `.steering/<task>/state.md` が存在する状態で呼ばれた場合）、root cause 確定後に以下を判断し、結果を Phase 4 出力に含めて呼び出し元へ渡す。standalone（GDD 外）で呼ばれた場合はこのセクションを省略してよい。

1. **ADR 起票判定（`.steering/<task>/adr.md` への記録）**: 確定した root cause が以下のいずれかに該当するなら ADR 起票を**必須**として handoff する — 既存設計の前提（API 契約・データ形状・layer 境界・env 伝播ルール）が誤っていた / 「もう一度同じ調査が走るのを防ぎたい」種類の知見（環境依存・timing 依存・外部サービス quirk） / Architecture Check に該当（3 回失敗パターン / 履歴パターン一致） / common-failure-patterns.md の 15 パターンに該当（次回同症状の検出速度を上げるため）
2. **Reviewer Lineage 影響判定**: root cause が以下に該当するなら、`tasklist.md` の `Implementation Reviewer Selection` に reviewer 種別追加を提案する — security boundary（auth / secrets / trust 境界）に触れる → `gdd-security-reviewer` を Lineage に追加 / 既存 reviewer 観点で見逃された原因 → 該当 reviewer 種別を Lineage 拡張記録
3. **Routing 提案（呼び出し元の `Next Action` 設定）**: fix を当てる前に、AC / scope / contract への影響を判定し以下のいずれかを提案 — `gdd-subagent-driven-implementation`: AC 不変の pure implementation fix（自走可）
   - `human-check-waiting`（`human_recheck_required`）: AC / scope / security boundary / prompt-output contract が変わる
   - `gdd-design-gating`（`design_detail_only`）: 要件不変だが detailed design が変わる
   - `gdd-brainstorming`（`planning_rework_required`）: 要件の前提が崩れた
4. **出力への明示**: 上記 1〜3 の判定結果を Phase 4 出力末尾に「**State Machine Integration**」見出しで記録し、呼び出し元（`gdd-systematic-debugging`）が state.md に反映できる形にする。standalone 呼び出しではこの見出しごと省略する。

**Why**: superpowers の `systematic-debugging` は単発で root cause を出すまでが責務だが、GDD は確定した root cause を artifact / Reviewer Lineage / Next Action に波及させて次 phase へ自走させる。この接続点を明文化することで「primitive 単体の質」ではなく「state machine 一体型 debug」として差別化する。

## Investigation Hygiene（認知バイアス対策・6 原則）

4 Phases の中で繰り返し陥る認知バイアスを防ぐための**横断ガードレール**。Phase 1〜4 のどこでも常時適用する。**重要**: これは **model 性能では防げない種類のミス**で、上位モデル（Opus 等）でも同じ罠にかかる。skill 側の強制力で初めて回避できる（Opus がこの 6 原則をいずれも踏まずに誤った root cause を確定した実例は `./references/investigation-hygiene.md` § 失敗実例を参照）。

1. **Scope Expansion Before Narrowing（早期スコープ固定の防止）**: ユーザーが指した対象だけでなく、同じコンテキスト（時間帯・環境・親リソース・同 deploy・同 session）で同時に動いていた他のエンティティを最初に列挙してから絞る。証跡フィルタを初手にしない
2. **Configuration / Rule の意味的評価**: 設定や rule を取得しただけで結論材料に使わず、「実際に何にマッチ / 許可 / 拒否するか」を 1 文で言語化してから推論に進む
3. **Multiple Working Hypotheses（対立仮説 3+ 生成）**: 未知の観測には最低 3 つの競合仮説を並べ、各仮説を棄却するまで結論しない。「これは X だろう」で 1 仮説に飛ばない
4. **非対称性は仮説棄却の Primary Signal**: 「同一条件で異なる結果」が観測されたとき、仕様起因 / プロトコル起因仮説は原則不成立。差分を先に潰す（規模差・設定値の微差等の補強仮説で塗りつぶさない）
5. **一次出典の直接読み取り（Source Bias 対策）**: 検索結果のサマリーや AI 要約だけで結論を出さない。判定格上げ（suspected → confirmed）の前に一次出典を直接取得して context 込みで引用する
6. **反証ステップの明示（Confirmation Bias 対策）**: 仮説形成後、必ず「この仮説が誤りなら何が観測されるはず？」を書き出し、その観測を能動的に探す

各原則の適用ドメイン別チェックリスト・禁則・チェックテンプレ・過去の違反実例（ある通知ノイズの調査）は **`./references/investigation-hygiene.md`** を参照。

## Architecture Check（3 回失敗、または過去パターン一致のとき）

以下のいずれかで発火する。もはや individual bug ではなくアーキテクチャ問題の兆候。盲目的に次の fix を試さず立ち止まる:

- **in-session 3 回失敗**（既存条件）: 同一調査セッション内で fix が 3 回失敗した
- **履歴パターン一致**（session をまたぐ再発）: Phase 1 step 3 の `git log --since="6 months ago" -S"<symbol>" --oneline`（pickaxe 検索）で、同一 symbol の出現回数が変化した commit のうち fix / 修正相当のものが過去 6 か月で 3 件以上見つかった。in-session の失敗回数が 0 でもこの条件単独で発火する

兆候（いずれの発火条件でも典型的に見られるもの）:
- 各 fix が別の場所で新たな問題を露出させる（症状が移動する） / fix のたびに mock / workaround / 条件分岐を積み上げないと動かない / 同一 root cause が形を変えて再発している
- 「massive refactor が必要」が口癖になる

これは「失敗した仮説」ではなく「**間違ったアーキテクチャ**」。盲目的に次の fix を当てるのではなく、

- このパターン自体が正しいか
- 慣性で続けているだけではないか / 続けるより architecture を直すほうが速くないか

を人間と相談する。発火時の出力形式は Phase 4「出力構造のルール」item 1（最優先アクション）の **Architecture Check 発火時** を参照。**深掘り調査やリファクタ計画の作成はこの skill の責務外**であり、この skill 自身は実行しない。

## Red Flags（出てきたら一旦止まる）

以下のいずれかが頭をよぎったら、Phase 1 に戻る:

- 「一旦これで直しておいて、原因はあとで調べる」 / 「とりあえず X 変えてみる」 / 「複数まとめて直してテスト回す」
- 「test 飛ばして手で確認すればいい」 / 「たぶん X が原因、直しちゃおう」 / 「完全には分からないけど、これで動くかも」
- 「reference を全部読むのは面倒、適当に真似する」
- 「もう 1 回だけ試す」（すでに 2 回以上失敗） / 「fix のたびに別の場所で問題が出る」

## 合理化との対決

| 出てくる言い訳 | 現実 |
|---|---|
| 「単純な issue だから process いらない」 | 単純な bug にも root cause はある。systematic は単純な bug ほど速い |
| 「緊急だから process やってる暇ない」 | guess-and-check のほうが遅い。data ベースでそう |
| 「先に試して、ダメなら調べる」 | 最初の fix がパターンを決める。最初から正しく |
| 「test は fix が動いたら書く」 | 「動いたつもり」の untested fix は粘らない |
| 「複数まとめて直すほうが速い」 | 何が効いたか分からない。新規 bug を生む |
| 「reference 長いから part だけ読む」 | 部分理解は bug を保証する |
| 「症状見えてるから直せる」 | 症状 ≠ root cause |
| 「もう 1 回だけ fix」（2+ 失敗後） | 3 回失敗はアーキテクチャ問題。fix ではなく構造を疑う |

## 「root cause が無い」と結論するとき

systematic な調査の結果、本当に環境依存 / timing 依存 / 外部要因だった場合: (1) ここまで調べた内容を記録する (2) 再発時に活きる handling を入れる（retry / timeout / 明確な error message / monitoring） (3) 「分からない」を「分からない」と書く

ただし、「root cause 無し」と結論されるケースの 95% は **調査不足**。一度 Phase 1〜3 をきちんと回したか自問する。

### When Process Reveals No Root Cause

Phase 1〜3 を回しても root cause が確定しない場合、fix を発明しない。これは「直せない」ではなく、観測・再現・証跡の不足を正直に切り分ける状態。Output must include No Root Cause Decision, including No Root Cause Decision with fix allowed: no.

`No Root Cause Decision` は以下を満たす場合だけ出せる:

- エラー / 症状 / 再現条件 / 直近変更 / 境界証跡を収集した
- 少なくとも 2 つの plausible hypothesis を検証し、結果を True / False / inconclusive で記録した
- 類似の正常例または既存実装との差分を確認した
- 追加で必要な証跡が何かを具体的に書ける

status selection guide:

- `non_reproducible`: 具体的な failure は観測済みだが、制御した再実行で再現できない
- `insufficient_evidence`: failure の詳細、log、環境、入力、再現手順が不足し、仮説検証に入れない
- `no_root_cause_yet`: 再現はできるが、仮説検証が未完了または棄却しきれていない

出力テンプレート:

```markdown
## No Root Cause Decision
- status: no_root_cause_yet | non_reproducible | insufficient_evidence
- final route hint: root-cause-investigation | design_detail_only | human_recheck_required
- evidence collected: <収集済み証跡>
- hypotheses rejected: <棄却した仮説>
- next data to collect: <次に必要な log / fixture / reproduction / reviewer input>
- safe operational fallback: <monitoring / retry / clearer error / rollback 等。なければ none>
- fix allowed: no
```

この状態で許可されるのは、追加証跡の収集、再現条件の固定、監視・診断メッセージなどの観測強化だけ。原因未確定のまま behavior-changing fix を入れない。GDD workflow 内では、この block を `gdd-systematic-debugging` の `No Root Cause Routing` に渡す。

## Quick Reference

| Phase | 何をする | 完了の判定 |
|---|---|---|
| 1. Root Cause | エラー精読 / 再現固定 / 直近変更 / 境界証跡 / source 追跡 | WHAT と WHY が言葉で書ける |
| 2. Pattern | 動いている類似と比較 / 差分列挙 | 差分が全部書き出せる |
| 3. Hypothesis | 因果関係を1つずつ最小検証し、因果グラフを更新 | 必要な共同主因セット・伝播経路・検出/回復の欠落を説明でき、未検証候補が結論を変えない |
| 4. Implementation | failing test → 1 つの fix → verify | test pass + 症状消失 + 他壊れない |

## Supporting References

この skill ディレクトリに同梱の補助ファイル:

- **`./references/multi-layer-probing.md`** — CI/CD / Lambda / Web stack / Container / データパイプラインの 5 構成について、各層で証跡を出すためのコマンド・log 出力テンプレート集。Phase 1 step 4 で参照
- **`./references/common-failure-patterns.md`** — env 伝播ロス / token 期限切れ / timing / quota / DNS / serialization / permission / cache / version mismatch / silent error / feature flag / timezone / storage / 型不一致 / concurrent modification の 15 パターン。各パターンに「典型的 root cause」「proving probe」「fix の方向」を併記。Phase 2 で参照
- **`./references/call-stack-tracing.md`** — 深い call stack で悪い値が観測されたとき、source まで遡るためのテクニック集。各言語の instrumentation、各 hop で記録すべき情報、fix を当てる場所の判定（source / 中間 / defense-in-depth）、アンチパターン。Phase 1 step 5 の深掘りで参照
- **`./references/condition-based-waiting.md`** — flaky test / timing 依存バグ対策。固定時間 sleep の anti-pattern と、観測条件で待つ recipe（subprocess / file / WaitGroup / DOM / DB 伝播）。flaky / sporadic failure を Phase 1〜3 で扱うときに参照
- **`./references/defense-in-depth.md`** — 同じ root cause が形を変えて再発するケースの多層 validation 設計。Boundary / Sanitization / Business rule / Defensive output / Audit の 5 層モデルと anti-pattern。Phase 4 で fix を当てる層を選ぶときに参照
- **`scripts/verify-env-propagation.sh`** — 環境変数の伝播を masking 付きで各 layer から検証する shell script。`LAYER_NAME=<layer> ./verify-env-propagation.sh VAR1 VAR2 ...` で実行。SET / SET_EMPTY / UNSET を返し、missing があれば exit code 2
- **`scripts/find-polluter.sh`** — テスト汚染源（test pollution）の特定 helper。「単体 PASS / suite FAIL」パターンに対し binary search で polluter を 1 件特定。`./find-polluter.sh <suspect-test-id>` で起動。`POLLUTER_TEST_LIST_CMD` / `POLLUTER_TEST_RUN_CMD` 環境変数で test runner を切り替え可能（既定: pytest）
- **`./references/superpowers-relationship.md`** — `superpowers:systematic-debugging` との使い分け目安（状況別の優先 skill 一覧）。「他 skill との関係」節で参照
- **`./references/investigation-hygiene.md`** — Investigation Hygiene 6 原則の適用ドメイン別チェックリスト・禁則・チェックテンプレ・過去の違反実例。Investigation Hygiene セクションで参照

これらは fix を書く前の **証跡収集と仮説生成** を加速するためのもの。skill 本体（4 Phases）の代替ではなく補助として使う。

## 他 skill との関係

この skill は workflow に依存しない汎用 methodology。以下と組み合わせて使う:

- **`gdd-systematic-debugging`** — GDD workflow 内で、この skill で root cause を確定させた後、どの GDD phase に差し戻すかを決める router。GDD 利用時はこの skill → `gdd-systematic-debugging` の順で呼ぶ
- **`gdd-test-failure-debug-pack`** — GDD workflow 内で test RED の Expected / Actual / Evidence pack を整理する skill。pack 内で root cause を狭めきれない場合、この skill の Phase 1〜3 を回してから `gdd-systematic-debugging` に handoff する
- **`superpowers:test-driven-development`** — standalone では Phase 4 で failing test を書くときに参照可。GDD workflow 内では `gdd-test-driven-development` を workflow として使い、superpowers は補助 reference に限定する
- **`superpowers:systematic-debugging`** — 同等の汎用 methodology（4 phases / Iron Law / architecture check の構造は同じ）。GDD workflow 外の standalone debug では利用可。GDD workflow 内では `root-cause-investigation` → `gdd-systematic-debugging` を primary route とし、superpowers は補助 reference に限定する

`root-cause-investigation` と `superpowers:systematic-debugging` の使い分け目安は **`./references/superpowers-relationship.md`** を参照。両方を同じ debug セッションで呼ばない（重複して時間が溶ける）。最初に 1 つ選んでそれで進める。

## 出力形式（任意）

呼び出し側が record したい場合のテンプレート:

```markdown
## Root Cause Investigation

### 症状
<1 行で >

### Phase 1: 集めた事実
- エラー: <message / line>
- 再現条件: <steps>
- 直近変更: <commit / file>
- 境界証跡: <どの層で値が壊れているか>
- データ source: <悪い値が生まれた場所>

### Phase 2: 比較した working code と差分
- 類似実装: <path>
- 差分: <list>

### Phase 3: 仮説と検証
- 仮説: <X が root cause、理由 Y>
- 検証方法: <minimal change>
- 結果: <True / False / 追加調査必要>

### Phase 4: 確定した root cause
<1〜2 行で。**未確定の場合は「未確定（探索継続中）」と明記**>

**原因の内訳**:
- 共同主因セット: <1 セット以上。未確定なら「共同主因セット（仮説、未確定）: {A, B}」>
- 寄与要因: <なければ「なし」>
- 検出/回復の欠落: <なければ「なし」>

**因果関係**:
<どの要因の組み合わせ・順序で症状に至ったか。AND 条件・分岐があれば明示>

### 最優先アクション

[root cause 確定時]
**最優先**: <共同主因セットまたは必要最小の原因セットに対する 1 作業単位の fix 方針>
- failing test: <path>
- fix 対象: <files / lines>

[root cause 未確定時]
**最優先**: 追加データ収集（**fix を当てない** — Iron Law: NO FIX WITHOUT ROOT CAUSE）
- 収集対象: <再現手順の確立 / instrumentation / 観測強化の具体内容>
- failing test: 未定（root cause 確定後）
- fix 対象: 未定（root cause 確定後）

### 副次アクション（任意、0-3 件）

- <優先度の低い対応項目 1>
- <優先度の低い対応項目 2>

### 副次的発見（Side Observations、任意）

本論とは別に調査中に気付いた点。後続タスクの material:

- <bot 文言の不正確性 / IaC drift / 文書の食い違い等>

### 意思決定

[root cause 確定時]
**修正に着手しますか?** それとも調査メモのみで止めますか?

[root cause 未確定時]
**追加データ収集に着手しますか?** それとも flaky として retry / monitor 等の運用回避に倒しますか?

### State Machine Integration（GDD workflow 内で呼ばれた場合のみ記入。standalone なら省略）

- **ADR 起票**: 要 / 不要（理由: 該当トリガーのみ列挙。複数該当なら slash 区切り。例: `再調査防止 / failure pattern 該当`。トリガー候補は `既存設計前提の誤り` / `再調査防止` / `Architecture Check 該当` / `failure pattern 該当`）
- **Reviewer Lineage 追加提案**: なし / `gdd-security-reviewer` / <他 reviewer 種別>（**Routing 提案とは独立軸**。Reviewer Lineage 拡張 + Routing 自走可（implementation）の組み合わせは矛盾しない）
- **Routing 提案**: `gdd-subagent-driven-implementation` / `human-check-waiting` / `gdd-design-gating` / `gdd-brainstorming`
- **判断根拠**: <AC / scope / contract への影響 1-2 行>
```

GDD workflow 内ではこの output を `worklog.md` の Error Log や `gdd-systematic-debugging` の入力として渡す。副次的発見は別 task として `docs/learned-patterns.md` に追記候補にすることもある。

---

## 中間報告・調査サイクル・状態永続化

### 中間報告ルール（10ツール呼び出しごと）

10ツール呼び出しごとに、以下の形式で中間サマリーをユーザーに向けてテキスト出力する:

> **調査中間報告**（ツール呼び出し N 回目）
> - 確認済みの事実: <箇条書き>
> - 現在の仮説: <1-2行>
> - 次に検証すること: <1-2行>
> - 残り不明な点: <箇条書き>

### 仮説→検証→結論サイクルの遵守

調査は以下のサイクルで進める。サイクルを飛ばして深掘りしない:

1. **仮説を立てる**: 証拠から因果関係の候補を 1-3 個選び、因果グラフ上の位置と分類（共同主因 / 寄与要因 / 検出・回復の欠落）を明示する
2. **検証する**: 仮説を確認/反証できる最小のツール呼び出しを行う
3. **結論を更新する**: 証拠が仮説を支持するか判断し、因果グラフと分類を更新する
4. **収束判定**: 必要な共同主因セット、症状への伝播経路、寄与要因・検出/回復の欠落の該当有無が証拠で説明でき、未検証候補が結論を変えないと判断できたら調査完了

### 調査完了後の遷移案内

調査が完了したら、停止出力を次の順序で構成する: **①本文** → **②`<gdd-stop reason="done">` タグ** → **③`## 👤 次にすること` ブロック**。`## 👤 次にすること` に含める内容:

- 根本原因のサマリー（1-3行） / 修正が必要な場合: 「修正を進めるには『修正して』と指示してください」 / GDD フローで進める場合: 「`/gdd-dev` で修正フェーズを開始できます」

### 調査発見事項の記録

GDD workflow 内では、重要な発見（根本原因の特定・確認証拠・除外した仮説）を都度、以下のファイルに記録する。standalone 調査では artifact-free 方針を優先し、ユーザーが記録を求めた場合または既存 `.gdd/` state がある場合だけ記録する:

ファイル: `.gdd/rci-findings.md`（なければ作成）

```markdown
# Root Cause Investigation Findings

## <タスク名> (<日付>)
- **確認済み**: <発見事項>
- **除外**: <除外した仮説と理由>
- **現在の仮説**: <最新の仮説>
```

このファイルはコンテキストが切れても残るため、再開時に Read することで調査状態を復元できる。
長時間調査（ツール呼び出し 20 回超）では必ず記録すること。
