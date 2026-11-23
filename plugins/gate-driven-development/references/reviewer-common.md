# Reviewer Common

> **所有**: 全 reviewer agent 共通の severity フレームワーク、route hints、出力フォーマット、evidence discipline
> **上位正本**: `self-contained-contract.md`
> **参照元**: 全 reviewer agent（`agents/gdd-*-reviewer.md`）と、節を名指しして参照する skill・reference（§ 常時 High を Classify に使う `gdd-pr-review-followup` など）

各 reviewer agent で繰り返される共通ルールを集約する。個々の agent は `references/reviewer-common.md を参照` と書き、固有の review focus と severity 例だけを自身に書く。

## Severity Framework

すべての reviewer は High / Medium / Low の 3 段階を使う。

- **High**: 実運用で重大な障害・セキュリティ事故・データ損失・ワークフロー破壊を引き起こす可能性が高い
- **Medium**: 実務上意味のある品質・運用・保守性のギャップ。放置すると後工程で問題化する
- **Low**: defense-in-depth、nice-to-have の改善のみ

Implementation gate の reviewer（quality / spec / nfr / feasibility / security）は Medium と High のみ報告する。

**Why:** Low は volume が多く、重要な High/Medium を埋没させる。requirements/design 段階では Low も方向修正に使えるため報告する。

### 常時 High（deny 迂回・guard bypass・fail-open・例外で guard が落ちる）（severity 調整の適用対象外。正本）

下記の適用範囲に当たる **deny 迂回 / guard bypass / fail-open / 例外で guard が落ちる** の finding は、reviewer / 段階を問わず **High** に固定する（後続で実装する guard・contract test の要件を定める Decision への finding は、`references/independent-review.md` の (3-f) が本節より先に当たる）。`self-contained-contract.md` § Stage 2 の「false positive 実績のある項目は severity を 1 段階下げる」は、これには**適用しない**（`dry` 判定への非適用と同じ趣旨）。

**適用範囲**: 本節は、次の部品自身の欠陥を除くすべてに適用する。(1) warn-only / advisory の lint と hook（block しないもの。出力が `systemMessage` か `additionalContext` かを問わない）、(2) 開発者が実行する検査スクリプト（`tests/checks/*`、`validate-plugin.sh`）。agent の操作を止める部品（PreToolUse の deny、done guard、steering write guard など。merge gate・pre-push gate・pre-PR gate は止めずに実行後の通知を出すので (1) に入る）と、利用者の製品コードの判定部品（認証・認可・入力検証など）は適用範囲内の例である。適用範囲外の部品で本節の 4 型に当たる欠陥は、severity を **medium を上限**にし、category には **4 型に当たることを理由には実害クラスを付けない**。付けてよい実害クラスは `data-loss` と `security-boundary` だけで（`fail-open` と `approval-path` は付けない）、どちらにも当たらなければ、判別力の欠陥は `test-power`、それ以外は `product` にする。`data-loss` / `security-boundary` を付けた finding には medium の上限を掛けない（独立レビューでは `references/independent-review.md` の (3-d) が同趣旨で降格を禁じる）。4 型に当たらない欠陥は従来どおり判定する。適用範囲外の finding は Stage 2 の severity 調整の対象に戻る。ただし、`data-loss` / `security-boundary` を付けた finding は戻らない。ただし、適用範囲外の部品への変更が **block gate と共有する部品**（shell 解析のヘルパーなど）を壊し、block gate の判定が変わった場合は、**block gate 側の欠陥**として適用範囲内（High）にする。どの部品の欠陥かは、変更の意図ではなく、欠陥が block / allow の判定に届くかで決める。判定できないときは適用範囲内として扱う。block しない hook でも、次に届く欠陥は、block / allow の判定に届かなくても適用範囲内とする。(a) 再開に使う `state.md` の canonical field（`Resume From` / `Next Action` / `Route In Progress` / `Human Check Status`）の書き込み・削除、(b) Safe Resume Candidate Mode の発火判定（`session_id` の照合を含む）と、compaction の直後の SessionStart が案内を出さない判定。hook の (a)(b) に届く欠陥は、種類（書き損じ・消し損じ・誤削除・発火しない・誤発火など）を問わず、本節の fail-open として扱う。発火後に注入する案内文の内容・JSON の sanitize・warn の文言は、適用範囲外のままとする。

**予約 alias との関係**: 適用範囲に当たる本節の 4 型は **severity（常に High）を固定する集合**であり、§ finding category の named alias **実害クラス**（= `is_blocking` の 4 category。`security-boundary` / `approval-path` / `fail-open` / `data-loss`）とは**別概念**である。重なるのは `fail-open` だけで、本節は `data-loss` を含まず、category 語彙の外にある型（deny 迂回 / guard bypass / 例外で guard が落ちる）を含む。requirements / design 段階を除く `blocking` カウンタの数え方は **§ finding category の `is_blocking` が単独正本**であり（requirements / design 段階の blocking は category で決めない。正本は `requirements-gating-steps.md` § 精度の第一原則）、本節は `is_blocking` の定義を変えない（本節に該当する finding も、category が `product` なら `blocking` には数えない）。適用範囲外の部品の欠陥に付ける category は、上記の適用範囲に従う。

**Why:** 2026-09-06 に reviewer の検出力（recall）を測ったところ、既存 escape hatch による deny 迂回を medium、別名キーによる無言 allow を low と判定した構成があった。severity を下げる余地を残すと、最も高い finding だけが選択的に埋没する。適用範囲は 2026-09-18 に設けた。旧#92 の high の大半は warn-only の HITL lint 自身の欠陥で（そのうち Stop hook の block に届くものは適用範囲内）、旧#93 の high の多くは開発者が手元で走らせる検査スクリプトの fail-open・例外だった。agent の操作を止めない部品が往復を長引かせていた。一方 旧#88 の指摘のうち、nudge hook の修正が共有の shell 解析を壊して root-branch guard と pre-push gate を deny から allow に退行させたものは、block gate 側の欠陥として High のまま扱う。2026-09-18（Issue 旧#123）に、block しない hook のうち再開経路に届く欠陥を適用範囲に戻した。PreCompact hook が `Status: paused` を書き損ねると compact 後の自動復帰が発火せず、SessionStart hook の Safe Resume Candidate Mode がすり抜けると古いタスク文脈が注入される。「resume に関わるもの全部」ではなく効果で列挙したのは、案内文や sanitize まで戻すと、適用範囲を設けて縮めた往復が戻るためである。2026-09-28 に compact 自動復帰を廃した（compaction の hook は main と subagent の compaction を見分けられず、自動復帰の文が subagent に届いていた）。(a) から hook だけが書いていた `Status`・`CompactSource` を外し、(b) を Safe Resume と compaction の直後の沈黙の判定にした。沈黙の判定が外れると、自律実行の途中の main に「再開するな」が入る。

## Route Hints

reviewer が指摘の修正方向を示すために使う。gate skill が最終判断する。

| Route Hint | 意味 |
|------------|------|
| `implementation_fix_only` | コード・テストの修正だけで解決。承認済み policy の範囲内 |
| `design_detail_only` | 設計の具体化で解決。承認済み policy の範囲内 |
| `human_recheck_required` | 狭い要件・実装方針変更で人間判断が必要 |
| `planning_rework_required` | 前提や計画の組み直しが必要 |

Requirements 段階の reviewer は route hints を使わない（まだ human check 前のため）。

## Output Format

### Requirements / Design 段階

```
- Findings ordered High -> Medium -> Low
- For each finding:
  - summary
  - evidence
  - impact（blocking なら failure scenario: 具体的な入力・状態 → 誤った結果。正本: `subagent-dispatch.md` § Reviewer Input and Time Budget）
  - blocking: yes（<当たる接地条件: AC の意味 | スコープ | 承認ポイント | 安全境界>）| no（severity と category では決めない。正本: `requirements-gating-steps.md` § 精度の第一原則）
  - origin: this-diff | pre-existing (差分をレビューする段階のみ)
  - category: <finding category値。正本: 本ファイル § finding category>。同じ行に続けて `観点: <この finding を見つけた、reviewer の定義の観点・チェック項目の見出し名。どれにも当たらなければ 観点外>`（観点ごとの効きを後から数えるための欄で、gate は読まない）
  - concrete fix（`閉じ方:` を添える。正本: § Fix の影響範囲）
  - fix blast radius: この修正で挙動が変わる既存経路。無ければ none、未分析なら unanalyzed
  - route hint (design 段階のみ)
- Coverage: 依頼の重点確認リスト外で走査した範囲と、走査していない範囲
- Residual risks or gaps
- Handoff summary (5-10 lines。1 行目は `設計の閉じ方:`。正本: § Fix の影響範囲)
```

### Implementation 段階

Requirements / Design 段階の欄から evidence・blocking・Residual risks・Handoff summary を除き、次だけを替える。

```
- Start with what you reviewed and `設計の閉じ方:`（正本: § Fix の影響範囲）. Report issues in High then Medium.
- 各 issue の先頭に `n: <1 から始まる通し番号>`。summary の代わりに affected file と problem summary、impact の後に `ops impact: yes/no`。origin は必須、route hint は常に書く
- High と実害クラス（§ finding category の `is_blocking`）の finding が無ければ、"approved" と書く。
- 最後の行に `findings: <issue の数>` を書く（0 件でも書く。gate が番号とともに `review-findings.md` に写す。正本: `references/finding-dispositions.md`）
```

`ops impact` は、その issue が実運用のユーザー行動・resume/gate 正確性・オペレーター安全性・必須 evidence に影響するかを示す。

### finding category（語彙の唯一正本）

すべての reviewer は severity に加えて `category` を 1 つ付与する。値域は次の 9 値で、この表が唯一の正本である。他の reference / skill はこの 9 値をバッククォート付きリテラルで再掲せず、named alias（**実害クラス**）と本節への pointer だけを書く。

| category | 意味 | 例（既存 ops-blocking medium の写像先） | `blocking` |
|---|---|---|---|
| `security-boundary` | 認証・認可・信頼境界の欠陥 | 検証なしの権限昇格経路 | yes |
| `approval-path` | 承認・HITL 経路の迂回 | 承認証跡なしで gate を通す | yes |
| `fail-open` | 検証失敗時に通してしまう経路 | parse 失敗を allow に倒す、resume / gate の correctness に影響（範囲は § 常時 High の適用範囲に従う）、rollback 手順が機能しなくなる変更 | yes |
| `data-loss` | データ・証跡の不可逆な喪失 | required verification evidence が取れなくなる変更、証跡の上書き消失 | yes |
| `product` | 実運用の挙動・性能・可観測性の欠陥 | N+1、blue-green / canary の atomicity 破壊、API schema 非互換、metric 消失・改名、500 のみでログなし | no |
| `test-power` | テストの判別力不足 | 等価変異が生存する assert、全パス未テスト | no |
| `bookkeeping` | 帳簿・証跡書式の不整合（判定結果を変えないもの） | field 欠落、書式ゆれ | no |
| `doc-claim` | 文書の記述と実態の不一致 | 散文と実装の食い違い、コメント文言の改善 | no |
| `style` | 命名・整形・未使用 import | 変数名・関数名の一貫性、コードスタイル統一、ログメッセージ文言 | no |

導出述語（reviewer が別途判断しない）:

- `is_blocking(category)` = 上表 `blocking: yes` の 4 値（**実害クラス**）
- `ops impact: yes` = 実害クラス ∪ `product`。既存の `ops impact` field はこの表からの導出であり、reviewer が 2 つを別々に判断しない

**降格の防止**: resume / gate の correctness に影響する欠陥（範囲は § 常時 High の適用範囲に従う）と、「required verification evidence が取れなくなる変更」は、素朴に読むと `bookkeeping` に落ちうるため、上表で `fail-open` / `data-loss` の例に明示する。`bookkeeping` の意味は「判定結果を変えないもの」に限定する。逆に、§ 常時 High の適用範囲外の欠陥のうち同節の 4 型に当たるものには、4 型に当たることを理由には実害クラスを付けない（付けてよいのは `data-loss` と `security-boundary` だけ。付け方は同節の適用範囲に従う）。後続で実装する guard・contract test の要件を定める Decision への finding の category は、`references/independent-review.md` の (3-f) に従う。

**category 未付与 finding の既定（fail-closed）**: gate が扱う finding（reviewer subagent の出力・inline checklist の走査・gate 自身の検査を問わない）のうち、category が付いていない、または上表の 9 値のどれでもないものは、medium 以上なら**実害クラス相当**として差し戻す（止める側に倒す）。low は advisory にする。gate 自身の検査が出す finding の category は、その検査の行に書く。merge gate 側（`blocking` key 欠落）の既定は `references/self-review-lanes.md` が別途規定する。requirements / design 段階の gate は blocking を category で決めないので、この既定を当てない（`blocking:` 欄が無いときの扱いは `requirements-gating-steps.md` § 精度の第一原則）。

## Premise Discipline

依頼プロンプトに書かれた実装の説明（「この経路は X なので Y は起きない」「対応済み」「A と B は対称」等）は、**未検証の主張**として扱う。指摘の成否を左右する主張は、実コードで確認してから議論を進める。確認せずに前提として使った主張は、その旨を出力に明記する。

**Why:** 依頼者は自分が正しいと思っている箇所を背景として書く。誤りが混ざるのはまさにそこであり、前提として受け入れると検査対象から外れて見逃しになる。実際に、依頼文の「この経路は呼び出し側が値を明示するため上書きされない」という記述を前提にしたことで、その記述が誤っていた箇所をまとめて見逃した事例がある。

## Finding の由来と scope

差分をレビューする段階（implementation / security / completion）に適用する。各 finding に `origin` を付ける。

- `this-diff`: この差分が導入した、または差分によって顕在化した
- `pre-existing`: 差分以前から存在し、差分がそれを悪化させていない

`pre-existing` は既定で「別 PR / 別タスクへ切り出す」を推奨し、この差分での修正を求めない。差分が悪化させている場合だけ `this-diff` として扱う。

**Why:** 既存の不具合を通常の指摘に混ぜると PR のスコープが本題から離れて膨らむ。修正がさらに二次不具合を生み、レビューが収束しなくなる。

## Fix の影響範囲

`concrete fix` を出すときは、その修正で挙動が変わる既存経路を列挙する（`fix blast radius`）。列挙対象は (1) 変更する部品の既存の呼び出し元、(2) 同じ入力を読む別の実装（`references/independent-review.md` の観点 (h) と同じ着眼点）とする。列挙できない場合は `unanalyzed` と明記し、依頼者に検証を促す。**実害クラス（`security-boundary` / `approval-path` / `fail-open` / `data-loss`。正本: § finding category）と `High` の finding（文言・帳簿の指摘は除く）では `unanalyzed` を禁止する**。判明している範囲を列挙したうえで未確認部分を明記し、それでも列挙が不可能なら `concrete fix` を出さず、対応方針を「影響範囲の調査」に留める。`concrete fix` には `閉じ方: 有限集合 | 構造 | 列挙` を添える。修正案が同じ種類の入力・場面を全部止めるかを書く。`有限集合` は取りうる入力・場面を全部挙げて確かめられるもの、`構造` は許可リスト・既定の反転・仕組みを外すなど形を問わず閉じるもの、`列挙` は既知の悪い形・語・場合を足していくもので、開いた入力（shell 構文・パス・自由文）や、規定に条件・例外・範囲の定義を足して新しい境界ができるものに残りが出る。書く前に、修正案を当てた後でも残る入力・場面を 1 つ以上探し、見つかったか迷ったら `列挙` にして `修正後に残る形:` を 1 行添える。この `列挙` は修正案が閉じないことを指し、`agents/gdd-planning-reviewer.md` の閉じ方 (a)・`列挙に縮める` とは別の意味である。Implementation 段階の出力形式では冒頭に、Requirements / Design 段階の出力形式では末尾の Handoff summary の 1 行目に `設計の閉じ方: 閉じている | 開いている` を書く。`列挙` の finding が、この差分（requirements / design 段階では、この計画）が新しく足す仕組み（定義・条件・判定）そのものに当たるなら `開いている` とし、「直す前に、この仕組みが要るか・機械で閉じる設計（許可リスト・script での計算・上限）に変えるか・限界として開示するかを決める」と添える。

**Why:** reviewer の提案をそのまま実装した結果、別レーンで復旧不能な状態を作り、その解消に何ラウンドも要した事例がある。修正案は指摘と同じ精度で検証する必要がある。閉じ方は、2026-10-07 に後続 PR の系列を調べた結果による。親から長く続いた系列の多くが、閉じない修正を次の PR で足し続け、撤去・巻き戻しで終わるか同じ型の指摘を出し続けていた。同じ差分を何度かレビューし直すと、新しく足した仕組みへの指摘には毎回 `列挙` が付いた一方、周辺の配線の指摘にも付くことがあったので、finding ごとの直す・直さないではなく、設計を問い直す合図に使う。実害クラス・`High` は復旧コストが最も高い finding であり、`unanalyzed` を許すとそこだけ検証されないまま実装される。**`references/self-review-lanes.md` § 規律A（横展開検索）との役割分担**: 本節は reviewer が finding を出す時点での fix blast radius 列挙を扱い、規律A は実装者が指摘を直した後の同型パターン横展開を扱う。フェーズと主体が異なるため重複しない。

## 重点確認リストへの非依存

依頼プロンプトに「重点確認」「特に見てほしい点」が書かれていても、それとは独立に差分全体を走査するパスを必ず 1 本持つ。出力の `Coverage` に、リスト外で走査した範囲と走査していない範囲を書く。

**Why:** 重点確認リストは依頼者の仮説であり、依頼者の盲点はそこに現れない。リストに予算を吸われると、差分のど真ん中にある単純な不具合を複数ラウンド見逃す。

## Evidence Discipline

Implementation 段階の reviewer に適用する。

正確性・安全性・運用性が diff・テスト・workflow artifact から示せない場合は、「後で人間が見るだろう」と楽観せず、少なくとも Medium として報告する。

**Why:** human check 後の workflow は autonomous に completion まで進む可能性がある。evidence gap を見逃すと、人間のスポットチェック無しに completion が成立してしまう。

## Uncertainty Rule

判断に迷ったら、楽観的な assumption より blocking finding を優先する。requirements / design 段階の `blocking:` 欄は `requirements-gating-steps.md` § 精度の第一原則 で決め、迷ったときの扱いも同節に書いてある（安全境界で迷うものだけをこの規則のとおり yes にする）。
