# Self-Review Lanes

> **所有**: セルフレビューの 3 レーン・検出漏れ分類 v1・修正時規律・リスク比例発火表・効果測定の正本
> **参照元**: `skills/gdd-pr-review/SKILL.md`（3f。本 skill で指摘を直すときに § 直し方）、`skills/gdd-pr-review-followup/SKILL.md`（Fix 手順。規律 A〜C と § 直し方）、`skills/gdd-implementation-gating/SKILL.md`、`skills/pr-review-followup/SKILL.md`（GDD 非依存の Fix 手順。規律 A〜C と § 直し方をそのまま適用し、followup 例外は持たない）、`skills/gdd-subagent-driven-implementation/SKILL.md`（差し戻し時の修正。規律 C と § 直し方）、`skills/gdd-systematic-debugging/SKILL.md`（§ Failure Routing の各 route で指摘を直す段。§ 直し方）、`skills/gdd-receiving-code-review/SKILL.md`（IMPLEMENT。§ 直し方）、`skills/gdd-test-driven-development/SKILL.md`（Step 1 で、指摘を直すために戻った task にテストを足す段。§ 直し方 の冒頭と 1・2）、`references/subagent-dispatch.md`（TDD Template の読むファイル。§ 直し方）、`references/rollback-patterns.md`（§ implementation_fix_only。§ 直し方）
>
> 参照元を上記 8 skill と 2 reference に限る理由（ここに挙げるのは § 修正時規律・§ 直し方 を使うものだけで、本ファイルの書式・表を参照するだけの reference は挙げない）: 実装差分そのものをレビューする lane が `gdd-pr-review`・`gdd-pr-review-followup`・`gdd-implementation-gating`・`pr-review-followup` の 4 つで（このうち `gdd-pr-review`・`gdd-pr-review-followup`・`pr-review-followup` は指摘の修正で § 直し方 も使う）、`gdd-subagent-driven-implementation` は差し戻しの修正で規律 C と § 直し方を、`gdd-systematic-debugging` は各 route で指摘を直す段で、`gdd-receiving-code-review` は IMPLEMENT の修正で、`gdd-test-driven-development` は指摘を直すために戻った task のテストで § 直し方の冒頭と 1・2 だけを使い、`subagent-dispatch.md` の TDD Template と `rollback-patterns.md` § implementation_fix_only は指摘を直すテストと順序で § 直し方を使うため。
> `gdd-completion-check` は evidence 検証、`gdd-requesting-code-review` は companion 依頼の入口であり観点の正本を持たないため。

## 3 レーン定義

| レーン | 見るもの | 必須になる条件 |
|---|---|---|
| 内部整合（internal） | diff 内部の数値・列挙・命名・型の自己整合性 | 常時必須 |
| 接地（grounding） | diff の外（実データ・実環境・配線・外部依存・デプロイ・信頼境界） | 外部依存・デプロイ・信頼境界を触る diff のときのみ必須。`standard` は独立レビューが担う。非該当は `not_applicable(<reason-token>)` |
| 敵対（adversarial） | fail-open 経路・検証の緩さ・バイパス手段 | `quick (standard)` で必須。`standard` は独立レビューが担う。`quick (express)` は内部整合レーンのみ |

## 検出漏れ分類 v1（10 分類、各レーンに一意配置）

| 分類 ID | 内容 | 配置レーン |
|---|---|---|
| 分類1 | 実データ照合なしでのレビュー完了宣言 | 接地 |
| 分類2 | 機械強制できる述語を自己申告のままにする | 敵対 |
| 分類3 | 数値・列挙の自己不整合（3f A 型と対応） | 内部整合 |
| 分類4 | コマンド・式の引数省略（3f B 型と対応） | 内部整合 |
| 分類5 | 断定の過剰一般化（3f C 型と対応） | 内部整合 |
| 分類6 | 検証・ガードの緩さ（3f D 型と対応） | 敵対 |
| 分類7 | 配線の実在（新設要素を実際に消費する側の欠落） | 接地 |
| 分類8 | 設計変更の追随漏れ（3f E 型と対応） | 内部整合 |
| 分類9 | ロールバック手順の欠落・不動作 | 接地 |
| 分類10 | 明示的事実による判定を飛ばした推測ベースの合格判定 | 敵対 |

10 分類はいずれも上記 3 レーンのいずれか 1 つにのみ配置される（同じ分類 ID が複数レーンに現れない）。

## A〜E 型 ↔ 10 分類の対応表

`skills/gdd-pr-review/SKILL.md` 3f の既存 A〜E 型は分類の別名ではなく、10 分類の一部を実データ根拠付きで具体化したサブセットである。

| 3f 型 | 対応する分類 ID |
|---|---|
| A（数値・列挙の自己不整合） | 分類3 |
| B（コマンド・式の引数省略） | 分類4 |
| C（断定の過剰一般化） | 分類5 |
| D（検証・ガードの緩さ） | 分類6 |
| E（設計変更の追随漏れ） | 分類8 |

3f に無い分類1・2・7・9・10 は、内部整合レーンの範囲を超える（接地・敵対レーン）ため、3f 単独では捕捉できない。3f は「敵対レーン + 内部整合レーンの入口」として残し、分類の正本は本ファイルとする。

### inline checklist との責務境界

`references/inline-review-checklists.md` は implementation-gating が走査する**検査項目**の正本、本ファイルは**レーン配置と分類 ID** の正本。両者が同じ欠陥を指す場合も走査は checklist 側で行い、finding に付ける分類 ID とレーンは本ファイルの 10 分類に従う（本節は severity を定めない。finding の severity は checklist 側 severity guideline とその上位正本 `references/reviewer-common.md` に従う。ただし `dry` 判定の severity には § followup 周回時のレーン要求 の例外規定が優先する）。

## 修正時規律

- **規律 A（横展開検索）**: 1 件の指摘を直したら、同型のパターンを `grep -r` / `git grep`（コードは AST 走査も併用）で全域検索し、ヒットしたすべてを一括修正してから再レビューする。走査対象の母集合（ファイル数・抽出条件）と候補件数を記録し、母集合を書かない「他に同型なし」宣言は受け付けない。ヒット件数と修正した型だけを記録し、全件リストを証跡に転記しない（LLM Output Boundary の非決定性対策）。**followup 例外**: `gdd-pr-review-followup` では規律 A のヒットを検出・記録までにとどめ、一括修正は原因クラスタが設計し直しと判定された場合に再設計側で行う（正本: 同 SKILL Step 3〜5 の対応プロトコル）
- **規律 B（スレッド消化）**: 未消化の指摘・未解決スレッドを残したまま次の周回に進まない。各周回の終わりに未消化件数 0 を確認してから `rounds` を加算する
- **規律 C（deny 分岐の入力者実測）**: 修正で guard に deny の分岐（拒否する条件・長さや件数の上限・受理する集合の縮小）を足すときは、実装の前に、新しく deny になる入力を本番で誰が何件出すかを実測する。測る先は、その入力を作る実際の呼び出し元（hook なら transcript・実行ログ、API なら access log など）で、読み取り専用の操作だけを使い、secret を返す操作は使わない。実値（ID・URL・本文・個人情報・secret）は、記録にも PR コメントにも書かない（`references/brainstorming-steps.md` の外部形式の実測 ① と ④ と同じ扱い）。記録する項目は、取得元・範囲・`新しく deny になる件数 / 総件数`・そのうち正当な入力の件数・比べた直し方と採った理由である。記録先は、formal gate の修正では `tasklist.md` の該当 task の `Verification Evidence`（worker は `.steering/` に書けないので controller が書く）、followup では証跡の `Verification:` 行（無いテンプレートでは、その周回の証跡に `Fixed findings` の id とは分けて書く）。design-gating を通る修正では、`skills/gdd-design-gating/SKILL.md` の 5d（規則の実値検算）の記録で代えてよい。正当な入力が 1 件以上当たるなら、その分岐を足す前に、別の直し方（入力の扱いを変える、限界として開示する）を比べる。測れないときは「未測」と理由を記録し、その分岐が正当な入力を止めうることを `requirements.md` § Honest Limitations か PR 本文の限界に書く。実例: 2 乗の計算量で hook が timeout する指摘を、16384 文字を超える入力を拒む上限で直した。その入力を本番で誰が出すかを測らなかったため、正当な heredoc の投稿を止めうるという次の指摘を生んだ

### 直し方

レビューの指摘（出所を問わない。gate の差し戻し・独立レビュー・companion / security review・PR 後の外部レビュー・自分で見つけた指摘など）を直すときは、次の順に進める。本節は直す側の手順で、reviewer 側の点検（`references/independent-review.md` の (h)、`references/inline-review-checklists.md`、`references/reviewer-common.md` § Fix の影響範囲）とは別である。文言・帳簿だけを直す修正（コードの挙動を変えない修正）には 1・2 を当てない。skill・reference・prompt のように文書が挙動を決める変更で、先に何を確かめるかは `references/testing-anti-patterns.md` § テスト判定基準（対象 repo の `docs/testing-standard.md`・`AGENTS.md`・`CLAUDE.md` のテストの節があればそれが正）に従い、skill 本文・prompt・reviewer policy・HITL 出力契約の変更は `skills/gdd-writing-skills/SKILL.md` § Skill RED-GREEN Evidence で確かめる。0・4・5 の記録先は規律 C と同じにする（0 の例外は 0 に書く）。規律 C の記録先に当たらない修正（`gdd-pr-review` の中の修正、`gdd-receiving-code-review` の IMPLEMENT など）では、steering があれば `worklog.md`、無ければ PR 本文に書く。

0. **直す前に設計に戻る**: `High` か実害クラスの finding を直す前に、その種類の穴を生んだ設計の決定を 1 つ挙げ、その種類ごと消す設計の変更があるかを確かめる。あれば、指摘の形だけを塞ぐ修正より先にそれを採る（route を変えるなら `skills/gdd-systematic-debugging/SKILL.md` の routing に従う）。結果は `設計: 変える（<決定>）` か `設計: 変えない（<理由>）` の 1 行で、規律 C と同じ記録先に書く。同じ task が impl-gate で 3 回差し戻された後の route 判断では、`references/state-machine.md` § Remediation Loop Safety の `Approach Rethink` の行に書く。PR 後のレビュー対応の 3 巡目は、`skills/gdd-pr-review-followup/SKILL.md` § Design Review Checkpoint の (a) が同じ見直しを求め、その `checkpoint:` の行が記録になる
1. **再現するテストを先に書く**: 指摘が起きる入力でテストを書き、修正の前に落ちることを確かめる。テストは修正の後も残す（`skills/root-cause-investigation/SKILL.md` § Phase 4 の failing test と同じ順序）。実害クラス・`High` の finding を `implementation_fix_only` で直すときの順序と commit の規律は、`references/rollback-patterns.md` § implementation_fix_only に従う
2. **修正が受け入れる入力の形を先に列挙する**: 修正が足す・変える分岐・正規化・順序ごとに、受け入れる入力の形を書き出し、境界ごとにテストを書く。境界の例は、閉じた後に残る区切り、全角空白・NBSP、行区切り（`\r\n`・`\r`・U+2028 など）、入れ子、深さや長さに比例する費用である。判定（通す・止める・警告する・PASS / FAIL）を出すコードか、その判定に届く部品（判定が使う解析・正規化などの共有部品を含む。届くかは、変更の意図ではなく、その部品の欠陥が上の判定の結果を変えうるかで決める。決め方は `references/reviewer-common.md` § 常時 High の適用範囲と同じ）か、block しない hook の、`references/reviewer-common.md` § 常時 High の適用範囲の (a)(b) に届く部分を変えるときは、fail-open の 3 ケース（止める・警告する・FAIL にすべき入力が通る／例外で guard や検査の全体が落ちる／判定できないときに通る）のテストを必ず書く。(a)(b) に届く部分では、同節が挙げる欠陥の種類ごとのテストも書く。判定を出すコードは agent の操作を止める部品、利用者の製品コードの判定部品（認証・認可・入力検証など）、warn-only の lint・hook、開発者が実行する検査スクリプトを含む。3 つのどれかに当たるか決められないときは含める
3. **使う側と対を列挙してから直す**: 変える部品を使う側・呼び出し元・同じ入力を読む別の実装・同じ規定を書く別の箇所を、直す前に列挙する。対の片方だけを直さない。規律 A（直した後に同じ型を全域で探す）とは時機が違い、両方を行う
4. **拒否リストに足す前に比べる**: 直し方が拒否リストに語・形を足す形になるなら、先に許可リストで閉じる案・既定を反転する案（判定できない入力を止める側に倒す）と比べ、採った案と理由を記録する。比べ方と既定は `references/common-guardrails.md` § 選ぶときの基準 2 に従う。deny の分岐を足すことにしたら、規律 C で入力者を測る
5. **同じ部品の修正が 2 巡続いたら問う**: 前の巡で直した部品（関数・hook・規定の節）を、今の巡でもまた直すことになったら（2 巡続いたら）、今の巡の修正の前に、その部品が要るか・共有の実装に寄せられるかを問い、答えを記録する。要るかの決め方（効果・実データの件数）と撤去が既定であることは、同節の基準 4 に従う。要らない・寄せられるなら、直し続けずにその案を採る。route を変えるときは `skills/gdd-systematic-debugging/SKILL.md` の routing に従う（同 skill § Loop Safety の上限は変えない）

**Why:** 2026-10-20 に、軽いレーンの差分巡で前の巡の修正が作った・関わった high・実害の指摘を機序で分けた。最も多かったのは修正そのものの誤り（足した分岐・正規化・順序の誤り）で、対の取りこぼし、受け入れる入力の範囲が開いているものがそれに続いた（分類は subagent の判定で、検算していない）。3 の列挙が効くのは対の取りこぼしだけで、それは一部にすぎないので、1 と 2 を先に置く。修正そのものの誤りは、shell の解析・正規化のような入力の形が多い部品の修正に寄っていた（そうした部品を直し続けた PR では、この型が大半を占めた）ので、5 を置く。

### 実装差分レビューの検査項目（実測に基づく規律。各項目に対応分類と由来実例を 1 行添える）

規律 A / B は手順の骨格、規律 C は deny の分岐を足す修正の前提であり、以下は内部整合・接地・敵対レーンで実際に見落としが起きた型を検査項目として固定したものである。特に分類3（数値・列挙の自己不整合）・分類6（検証・ガードの緩さ）・分類10（推測ベースの合格判定）に集中する。

1. **mutation は方向（fail-open / 誤爆）× 型（分岐 / 値置換）× 対象レイヤ（コード / 設定・配線）の 3 軸で起こし、KILL 判定には巻き添え検査（FAILED が当該 test のみで他は無反応）を必ず添える**（分類6）— 実例: 対象レイヤの軸が無かったため、設定・配線のみの diff で mutation 集合が空になり判別力ゼロのまま緑化した
2. **変異の適用はアンカーの一意完全一致を assert してから行う**（分類6）— 実例: 文字列置換ベースの変異が実コードにマッチせず、無効パッチを survivor と誤認する事故が複数回発生した
3. **期待値は実装・設定ファイル自身から機械導出し、件数・メンバー名の literal を持たせない。ただし空洞化防止アンカー（独立に導出した対向値との突き合わせ）を併置する**（分類3）— 実例: 期待値をテスト対象自身の定数からそのまま読んだ結果、その値を削除する mutation を検出できなかった
4. **飽和の述語は「追記先の契約テストの既存 test が同一分岐を固定しているか」であり、「suite のどこかで KILL されるか」ではない**（分類10）— 実例: 新規追加予定のテストが既存テストと同一の分岐しか踏んでおらず、追記しても即 GREEN で RED が成立しなかった
5. **Step 0 の写像元は AC 本文と設計文書の 2 つを独立に読む**（分類8）— 実例: AC 本文だけを写像元にした結果、設計文書側が追加で要求していた次元を見落としていた
6. **併記形は単独形へ分解して実測する**（分類3）— 実例: 2 つの条件を同時に満たす併記形のテスト 1 本だけでは、片方の条件を壊す mutation が生存する等価変異になっていた
7. **配線の実在: 新設要素を実際に消費する側が存在するかを end-to-end で追う**（分類7）— 実例: 新設した委譲用の関数を実際に呼ぶ経路が repo 全域で 0 件のまま出荷され、判別力ゼロの死んだ経路が残っていた
8. **終状態のみ assert するのを禁止し、カウンタ・状態機械は遷移列全体を観測する。変異を選ぶときは変異点の粒度（どの式・どの行を何に置換したか）を記録し、追試が再現できる形にする**（分類6）— 実例: 状態が周回ごとに変化する仕組みで最終回だけを assert するテストは、途中の遷移が壊れる mutation に無反応だった
9. **記述の実測裏取り: 安全側の限定（「〜にはならない」「〜方向のみ」等）を書くときは、限定の外側を 1 形以上実際に叩いてから書き、散文だけに置かず現状挙動を固定する regression test と対にする。記述と実態の一致は shipped 成果物と steering 記録の両面で確認する**（分類10）— 実例: 反証実行を伴わずに書いた安全性の断定が、実測すると偽だったと事後に判明した
10. **各テストが固有の変異を KILL することを個別実証する**（分類2）— 実例: 判別力の主張を suite 全体の合格だけで済ませ、どのテストがどの mutation を殺すかを個別に確認していなかったため、重複や無判別力のテストが見過ごされていた

### 分類5 の下位型: 限定・全称の未測定断定

「〜のみ」「唯一の」「残るリスクは」「管轄外」のような限定・全称の断定を、**限定の外側を 1 形も測らずに書く**型。**分類5（断定の過剰一般化）の下位型として扱い、独立分類（11 分類目）は立てない**（独立分類にすると `10 分類` を逐語 pin している検査・契約テスト・参照側 skill へ波及するが、分類5 の定義文が既にこの型を含むため検出力は増えない。波及先の実集合は `grep -rlF '10 分類'` で導出する。件数はここに書かない）。規律の正本は上記検査項目 9。散文の規律だけでは実績として防げなかったため（同型が 1 つの PR の中で何度も再発した）、**出荷文書側は下記マーカーの対で機械検査する**（`tests/checks/bounded-claim-evidence.sh`）。

- **限定宣言マーカー**: `担保しない` / `測っていない` / `観測範囲の外` / `外側については主張しない`
- **実測記録マーカー**: `測った入力集合`
- **実測記録の宣言形**: `**{}**`（プレースホルダに実測記録マーカーを埋めた強調宣言。散文の言及だけでは通さない）
- **走査範囲**: 出荷文書（`references/` / `skills/` / `docs/`）
- **走査除外**: **本ファイル自身と `CHANGELOG.md` は対象外**（本ファイル = `references/self-review-lanes.md`。前者は語彙宣言行が両マーカーを必ず含み実集合が常に非空になって空洞化アンカーが発火しないため、後者は他文書の断定を引用する release log のため）。日付付きの過去 PR アーカイブ `docs/design/` / `docs/plans/` / `docs/audits/` も対象外（決定・計画・監査の時点記録で後から追記しない。新規則の遡及適用は閉じた記録の改変になる）

限定宣言マーカーを 1 つ以上含む出荷文書は、同一文書内に実測記録マーカーを実測記録の宣言形で持たなければならない（参照だけ残して実測記録の中身を消す形を素通りさせるため）。**上の宣言行はすべて検査側が機械導出し、検査側 literal との一致を assert する**。宣言行だけを書き換えても検査側 literal だけを書き換えても FAIL になる（両側 pin）。`.steering/` は走査範囲の外（出荷されず統合先で対象 0 件 = fail-open になる）。退役 reference の置き場は規範本文が生きているため走査対象に残す。

## リスク比例発火表（Task Size × レーン）

| Task Size | 内部整合 | 接地 | 敵対 | dry 要求 |
|---|---|---|---|---|
| `trivial` | — | — | — | 要求しない（`.steering/` を作らないため証跡自体が不要） |
| `quick (express)` | 1 周必須 | 対象外（`not_applicable` 相当） | 対象外 | 要求しない |
| `quick (standard)` | 必須 | 該当 diff のみ必須 | 必須 | 要求しない（レーンは回すが `dry: yes` 到達を要求するのは standard のみ。2026-09-06 緩和） |
| `standard` | 必須 | 独立レビューが担う | 独立レビューが担う | 内部整合 1 周で新規 high / blocking ゼロ ＋ `Independent Review` 行（push 対象 tip〔PR 作成時は HEAD〕の sha か引き継いだもの、high 0 かつ blocking 0） |

## followup 周回時のレーン要求

PR 作成後の followup ループ（`gdd-pr-review-followup`）で再 push する際は **自己周回は内部整合レーン 1 周のみ必須**とする。接地・敵対レーンの自己周回は **`quick (standard)` に限り**、初回 push 時、または信頼境界・外部依存・デプロイ設定を触る修正時にのみ再適用する（`standard` は両レーンを独立レビューへ委譲済みで、followup 周回でも自己周回では回さない）。followup ループは複数巡回りうるため、毎周 3 レーン全周は費用対効果が合わない。

**push・PR の前の検算**: 証跡の行を書いたら、`git push`・`gh pr create` の前に `bash <plugin>/scripts/check-gate-ledger.sh` を走らせ、gate 列にそのコマンドの gate（`git push` は `pre-push` と `independent-review`、`gh pr create` は `pre-PR` と `completion-check` と `independent-review`）を含む行に missing / invalid が無いことを確かめる（`git push` の前は、steering 行の詳細が `pre-push=multiple` なら、gate 列と状態によらずその詳細も読む）。判定の述語は pre-PR gate・pre-push gate と共有し、要求する行（steering の解決・raw steering の除外・`Next Action=done`・`ADR distilled`・Self Review・`Independent Review` の sha と high / blocking）と、completion-check の完了タスクの `Reviewed by:` と、`Independent Review` の指摘の行き先（`findings` 行。`references/finding-dispositions.md`）を一度に一覧する（steering 行の「両 gate の解決がそろうか」と `Reviewed by:` と `findings` 行は、hook が見ない検算だけの行）。pre-push gate は最初に欠けた 1 行だけを実行後に通知し、pre-PR gate の通知は PR を作った後に届くので、通知を受けて直すのを繰り返さない。**独立レビューは自己周回の免除対象ではない**。`standard` は followup の再 push でも `Independent Review` 行（push 対象 tip の sha か引き継いだもの、high 0 かつ blocking 0）を要求する（pre-push gate は Task Size だけで分岐し followup を区別しない。複数の steering から push 対象 tip の証跡で 1 件を選んだときは、Task Size によらず standard として検査する）。「push 前 1 回に絞る」（`references/independent-review.md`）の 1 回は **push 1 回あたり 1 回**の意味であり、PR 全体で 1 回ではない。

`dry` の意味は、followup 周回・初回 push / PR 作成時とも **「その周回で新規 high または blocking ゼロ」**である（内部整合レーン 1 周で数える。**2 連続要件は 2026-09-06 に撤廃**。理由: reviewer の検出力を調べると、3 レーン自己周回は確定した欠陥を 1 件も拾えずに `approved` を出しており、同じ観点を何周積んでも検出力が増えないと確定した。検出は独立レビューへ移す）。medium / low / advisory は記録して次周回に持ち越さず、`consecutive_clean` を 0 に戻さない（「帳簿 finding は非 blocking」という方針の pre-push / pre-PR gate への適用。2026-09-06 改訂: 旧定義「新規指摘ゼロ」は帳簿系 medium が毎周新出して収束せず、standard で周回を重ねても連続クリーン周回が 1 回も出なかったため）。`consecutive_clean` はどちらの場合も同じ意味（連続クリーン周回数）で記録する。

**内部整合 1 周 ＋ 独立レビュー 1 回（2026-09-06 改訂）**: `standard` の push 前は、内部整合レーン 1 周（新規 high / blocking ゼロ）と **独立レビュー 1 回（契約の正本: `references/independent-review.md`）で high: 0 かつ blocking: 0** の両方を満たしたときだけ `dry: yes` と記録する。接地・敵対の観点は独立レビューの観点レーンが担うため自己周回では回さない。独立レビューの根拠は `state.md` § Gate Status の `Independent Review` 行（merge gate と同一書式。sha は push 対象 tip（PR 作成時は HEAD）か、§ Independent Review の引き継ぎで引き継いだもの）に残し、pre-push gate（push 対象 tip と比べる）と pre-PR gate（HEAD と比べる）がこの行を機械検査する。独立レビューで high が出た場合は是正後に内部整合レーン 1 周を回し直し、独立レビューを再実行する（後で実装する guard・contract test の Decision への high は、`references/independent-review.md` の (3-f) の取り直しの上限に従う）。自己周回は **3 周を上限**とし、3 周で内部整合レーンが収束しない場合は push を止めて `gdd-systematic-debugging` に差し戻す。

`dry` の severity 判定は `references/inline-review-checklists.md` の severity guideline を正本とするが、**「false positive 実績のある項目は severity を 1 段階下げる」規定は `dry` 判定には適用しない**。適用すると自分の finding を advisory に落として 1 周で `dry: yes` に到達できてしまうため（dialectic counter 指摘の空洞化経路）。

## `not_applicable` 理由 token 語彙

`grounding` / `adversarial` レーンを `not_applicable` とする場合、括弧内に以下いずれか 1 つの固定語彙を書く（`no-external-dep` / `docs-only` / `prompt-only` / `test-only` は `grounding` 専用、`independent-review` は `standard` の委譲記録として両レーンで使う）。理由なしの `not_applicable` は最も安い選択肢になり接地レーンが常に飛ばされる方向に流れるため、理由 token を必須にする。

- `no-external-dep`: 外部依存・デプロイ・信頼境界のいずれにも触れない diff
- `docs-only`: ドキュメントのみの変更
- `prompt-only`: skill / prompt 文面のみの変更
- `test-only`: テストコードのみの追加・修正
- `independent-review`: `standard` で当該レーンを独立レビューへ委譲した（`grounding` / `adversarial` に共通の記録形）。**`grounding` / `adversarial` の両レーンでこの token を `standard` でのみ受理する**（`quick (standard)` / `quick (express)` は独立レビューを要求する gate が無く、委譲先が存在しないまま「回していないレーン」を非 0 件扱いにできるため。パーサは Task Size を受け取って判定し、write 時の証跡バリデータ・pre-push gate・pre-PR gate の 3 箇所とも同じ正規化規則（未知値・欠落は `standard`）で Task Size を渡す。例外として、pre-push gate が複数の steering から push 対象の tip の証跡で 1 件を選んだときは `standard` を渡すので、quick の steering にこの token を書くと write 時のバリデータが拒む。そのときは数値のレーンで書くか、使わない steering を終える）

## blocked steering の扱い

`Resume From: blocked`・`Next Action: blocked` の steering は「作業継続中に人間判断待ちで止まっている」状態であり、push gate の対象に含める（`gdd_pre_push_resolve_steering` の統一判断）。worktree の binding が終端（done・cancelled・stale な brainstorming。`Next Action` だけが done・cancelled の正規の完了の形も含む。binding 先の `tasklist.md` が在るのに読めない・ファイルでないときも done とみなし、読めるように直すと外れる）の steering を指し、作業中の steering があるときは、binding が無いときと同じ規則で作業中の steering を数え、done・blocked の steering も候補に残す（作業中の steering の Task Size で検査を緩めないため）。`Resume From: cancelled`（完全一致）でなく `Next Action` などだけで終端とみなした binding 先と stale な brainstorming の binding 先は、cancel でも候補に残し、作業中の steering が無ければ binding 先で検査する。候補が 2 件以上のときは、`.steering/` の全 `state.md` のうち、valid な `Pre-Push Self Review` の sha（大文字小文字は区別しない）が push 対象の tip の sha の先頭と一致するものがちょうど 1 件なら、その steering で以降の検査を行う（Task Size は読まず standard で検査する。trivial・quick の steering を選んで検査を緩めないため）。一致が 0 件・2 件以上なら、active・終端を問わず pre-push gate が `steering-multiple` を通知する（pre-PR gate も binding が終端のときは同じ規則で数え直すが、tip の証跡で選ぶ材料が無いので、候補が 2 件以上なら通知する。どちらも止めずに通し、実行後に通知して would-block を記録する）。それより前に、steering の列挙から落ちるもの（symlink・一覧できないディレクトリ・読めない `state.md`）が `.steering/` に 1 つでもあれば、解決の結果によらず `steering-unreadable` を通知する（復帰の手順: `docs/TROUBLESHOOTING.md`）。
## 使わないステアリングの終え方
pre-push の `steering-multiple`、pre-PR と SessionStart の複数 steering の案内が指す手順。どれを終えるかはユーザーに確認する（別 session・別 runtime が作業中の steering かもしれない。`references/abandon-and-pause.md` のとおり、cancel は明示の意思表示なしに行わない）。使わない steering の `state.md` で、`Resume From: cancelled` と `Next Action: cancelled` をどちらも書き、`Route In Progress` が `none` 以外なら `none` にする（`cancelled | superseded-by: <slug>` のように注記してよい）。片方だけでは外れない（pre-push は done・blocked をどちらの field でも候補にする）。PR が open（未マージ）の steering は対象にしない（PR の後の followup がその steering を再開して merge の証跡を書く）。それしか外せないときは、先にその PR を merge してから cancelled にするか、新しいタスクを別の worktree で進める。削除・移動はしない（移すと PR が open の steering は merge gate の PR URL 照合から外れ、`.steering/` の外へ移すと `.steering/` の ignore から外れ、git に見える未追跡ファイルになって全量 commit で PR に混入しうる）。cancelled にしてもディレクトリは残るので、bind できないときの Stop hook の done guard は検査しないままになる。PR URL の無い cancelled の steering が残ると、所有 marker の無い merge で対象 PR を記録した steering が見つからないとき、merge gate は `pr-url-unrecorded` を merge の後に通知する（止めない。次からは対象 PR の worktree から merge する）。終端の steering だけが残るときも、対象 PR を記録した steering は merge gate が検査し、PR を記録した steering がある checkout で対象 PR を省いた merge は `steering-ambiguous` を merge の後に通知する。書き込み guard に止められたら、足りない必須 field（`Human Check Status`・`Started At` など）を同じ編集で足す。
## merge gate 証跡（`gh pr merge` の解除条件。正本）
`skills/gdd-pr-review-followup/SKILL.md` が記録する。`state.md` の `## Gate Status` 節に他の field と同じ `- <Field>: <value>` の bullet 1 段で書く（`gdd_extract_doc_field` が拾わないのは**インデントした行だけ**。行頭 1 桁目から始まる bare 行は bullet と同じく拾われるため、`Merge Approval` の下書きを bare 行で `state.md` に置くと承認証跡として読まれる）。
```
- PR URL: https://github.com/<owner>/<repo>/pull/<number>
- Last Review Push At: <sha> | at: <ISO 8601>
- Pre-Merge Review Recheck: <sha> | new_blocking: <uint> | at: <ISO 8601>
- Bot Review Received: <sha> | received: <yes|no> | at: <ISO 8601>
- Independent Review: <sha> | reviewer: <agent-name> | context: diff-only | high: <uint> | medium: <uint> | blocking: <uint> | at: <ISO 8601>
- Medium Disposition: <sha> | count: <uint> | recorded: <follow-up PR URL / issue 参照 | accepted> | note: <1 行> | at: <ISO 8601>
- Merge Approval: PR #<number> / head <sha> | evidence: <承認発言の要約 | post-pr-autonomy:<自走上限の値>> | approved_at: <ISO 8601>
```
`sha` を持つのは 6 field（`PR URL` は持たない）。いずれも 7〜40 桁 hex を要求する。うち **HEAD 一致まで検査するのは 5 field**（`Merge Approval` / `Pre-Merge Review Recheck` / `Bot Review Received` / `Independent Review` / `Medium Disposition`）で、full sha へ正規化して `git rev-parse HEAD` と比較する。`Independent Review` は、§ Independent Review の引き継ぎの条件を満たせば一致しなくても通す（pre-push gate・pre-PR gate と、merge gate の `received: no` の経路）。**`Last Review Push At` の sha は書式だけを検査し HEAD とは比較しない**。この field を縛るのは時刻側で、`at` が HEAD の committer date 以降であることを要求する（push は commit の後に起きる、という制約）。`at` は ISO 8601（`Z` 接尾または `+HH:MM` 必須、naive は invalid）。パーサは `hooks/scripts/lib/merge-gate-evidence.sh` の `gdd_parse_merge_gate_field()`（self-review 用の `gdd_parse_self_review_field` とは必須 key が異なるため流用しない）。hook 所有ログ（suppression 記録）の repo 識別子は絶対パス全体の sha1 先頭 8 桁で、絶対パスをログに残さないための識別子であり匿名化ではない（候補パス集合が小さければ逆引き可能）。**`Merge Approval` は他 6 field と書式が違い**（先頭 segment が `PR #<n> / head <sha>`、時刻 key が `at` ではなく `approved_at`。`Medium Disposition` 追加後、本節が扱う証跡 field は `PR URL` を含め全 7 種で、`Merge Approval` を除く 6 種と比較する）、**書き手は `skills/gdd-pr-review-followup/SKILL.md` の手順に従う GDD main session だけ**（subagent は書かない）。`evidence` には人間の承認発言の**要約**を書き、原文を丸ごと転記しない（自走のマージの条件〔`references/post-merge-qa.md` 手順 2〕で承認に代えたマージでは `post-pr-autonomy:<自走上限の値>`）。`Bot Review Received` が `received: no` のときは最後の push から待機時間だけ待つが、**`Independent Review` が HEAD sha（または § Independent Review の引き継ぎで HEAD に引き継いだもの）で `high: 0` / `blocking: 0` なら bot 待機は不要**（`received: yes` の経路では bot レビューのみで通り、merge gate は `Independent Review` を読まない。`received: no` の経路でだけ、独立レビュー（HEAD sha か引き継いだもの・high 0・blocking 0）が待機免除の条件になる。待機の目的は bot の着弾待ちであり、経過後に要求されるのも同じ `Independent Review`。bot が恒久的に来ない repo で 40 分の空待ちを避ける）。**`blocking`**（`Independent Review` = 実害クラス category の件数）と**`new_blocking`**（`Pre-Merge Review Recheck` = 前回レビュー以降の新規 blocking finding 数）は別概念であり混同しない。`gdd_extract_doc_field` は section を見ずに文書全体から field を拾うため、`## Gate Status` 節の外に書かれた実値入りの行も証跡として成立するという既知の限界がある（既存 6 field すべてが共有する弱点で本 PR で新規に作るものではない）。

### 旧書式（`blocking` 欠落）の既定挙動

| 証跡の状態 | 判定 | 記録 |
|---|---|---|
| `blocking` key あり（新書式） | `high != 0 \|\| blocking != 0` を不足として通知する（would-block を記録する）。medium ≥ 1 なら `Medium Disposition` 必須 | — |
| `blocking` key 欠落（旧書式） | `blocking` を 0 とみなす（`unparsable` にしない）。判定は `high != 0` のみ。medium ≥ 1 なら `Medium Disposition` 必須 | `_mg_log_suppressed "legacy-evidence-no-blocking-field"` |
| `blocking` key あり・値ドメイン違反 | 既存どおり `evidence-malformed` を不足として通知する | — |

`hooks/scripts/lib/merge-gate-evidence.sh` に定数 `GDD_MG_REQUIRE_BLOCKING_FIELD="false"` を置く。reviewer の category 出力契約が整った後に `true` へ反転する（反転すると旧書式は `unparsable` になる。反転は本 PR では行わない）。

### `Medium Disposition` の valid 述語（正本。実装は `hooks/scripts/lib/merge-gate-evidence.sh`）

`medium != 0` の証跡でのみ要求する（`medium == 0` では不要）。以下すべてを満たさなければ invalid で、不足として通知する。reason code は、行が無い・`<sha>` が HEAD と違う（commit に解決できないときを含む）・`count` が `Independent Review` の `medium` と一致しないときは `medium-disposition-missing`、必須 key（`<sha>`・`count`・`recorded`・`note`・`at`）の欠落は `evidence-unparsable`、値の誤り（hex でない sha、uint でない `count`、プレースホルダか空の `recorded`・`note`、読めない `at`）は `evidence-malformed` になる（`hooks/scripts/run-merge-gate-hook.sh` の `Medium Disposition` の分岐と `hooks/scripts/lib/merge-gate-evidence.sh`）:

1. `<sha>` を持ち、HEAD 一致検査の対象に含める（上記 5 field の 1 つ）
2. `count: <uint>` が `Independent Review` の `medium` と一致する
3. `recorded` と `note` は**プレースホルダ（`<...>` 形式）または空なら invalid**
4. `at` は ISO 8601（`Z` または `+HH:MM` 必須、naive は invalid）

## Independent Review の引き継ぎ（default branch を取り込むだけの merge commit。正本）
レビュー済みの tip に default branch を merge しただけの commit では、独立レビューを取り直さずに旧 sha の `Independent Review` を引き継げる。main session が、`Independent Review` 行（旧 sha のまま）の隣に `- Independent Review Carry: <merge sha> | from: <旧 sha> | verified: diff-equal | at: <ISO 8601>` を書く（sha は 7〜40 桁 hex、`verified` は固定値、`at` は ISO 8601）。読むのは pre-push gate・pre-PR gate・merge gate（`received: no` の経路の待機の免除と独立レビューの要求）・検算（`scripts/check-gate-ledger.sh`）で、`Independent Review` の sha が比較先（push 対象の tip・HEAD）と一致しないときだけ見る（述語は `hooks/scripts/lib/gate-ledger.sh` の `gdd_ir_carry_matches`、判定は `hooks/scripts/lib/ir_merge_carry.py`）。gate は `verified` を信用せず次をすべて git から計算し直し、1 つでも満たさない・git が失敗する・時間内に終わらない（git の待ちと計算を合わせて判定は 5 秒まで。hook では、hook の起動から 8 秒を過ぎる分も使わない）ときは今までどおり不足として実行後に通知する（pre-push gate・pre-PR gate は `independent-review-stale`、merge gate は `review-wait-not-elapsed`・`independent-review-missing`）: (1) `<merge sha>` が比較先に、`from` と `Independent Review` の sha が同じ commit に解決される (2) 比較先の親がちょうど 2 つで、第 1 親が `from`、第 2 親が remote-tracking の default branch（`origin/HEAD`・`origin/main`・`origin/master` の最初に見つかったもの）の祖先、merge-base が 1 つ（criss-cross は不可） (3) 衝突したファイル C を `git merge-tree --write-tree --name-only <第 1 親> <第 2 親>` で求め（git 2.38 以上。衝突マーカーは 2 方向に固定）、C の外のファイルは自動 merge の tree と merge commit の tree で同じ (4)（依頼の (a)）C の外のファイルで、`git diff <merge-base> <第 1 親>`（PR の差分）と `git diff <第 2 親> <merge>` のファイルごとの差分（`-U0`。`index` 行と `@@` 行は比べない）が一致する (5)（依頼の (b)）C のファイルの merge 側に、行頭の 7 文字以上の `<`・`>`・`|` の行が無く（衝突ブロックの位置で両側のどちらでもない行は、7 文字以上の `=` の行も不可）、消えた・NUL を含むファイルも無い（`.gitattributes` の binary 扱いによらず中身を読む） (6) C のファイルごとに、自動 merge の blob を衝突の外の行の塊と衝突ブロック（PR 側・default branch 側）に分け、merge 側の blob で、衝突の外の塊が同じ順序で連続して現れ（先頭と末尾の塊は先頭と末尾に固定）、各ブロックの位置に PR 側と default branch 側の行がそれぞれ順序を保って残る（片側に寄せた解消・衝突の外の行の移動は不可。マーカーの並びが読めない・ブロックの無い衝突も不可） (7)（依頼の (c)「衝突解消の行数」）ブロックの位置にある行のうち、両側のどちらの行にも当たらない行の合計が 5 行以下。high・blocking の検査は変わらない。引き継げるのは 1 回で、merge の後にもう一度 default branch を merge したら（第 1 親が `from` でなくなる）取り直す。`Pre-Push Self Review`・`Pre-PR Self Review`・`Medium Disposition` の sha は引き継がない。引き継ぎが成り立つ merge では、これらの行は sha だけを merge sha に書き換えてよい（判定が、衝突の外が自動 merge のとおりで、衝突の位置に両側の行が残ることを確かめる）。閾値 5 の根拠（2026-10-13）: GDD を使う別の repo の main の履歴にある、main を branch に取り込んだ merge に当てると、多くは引き継げた。衝突ありで (7) まで届いた merge の値はほとんどが 0 で、最大でも 5 を下回った。止まった merge の多くは、merge の中の追加の編集（ADR の番号の振り直しなど。(3) で止まる）と、衝突ファイルの片側に寄せた・書き換えた解消（(6) で止まる）だった。限界: 行が重ならない変更の組み合わせで壊れる意味上の衝突は見ない。衝突ブロックの中で両側の行をどう並べるかと、5 行以内の足した行は、レビューを経ずに通る。ブロックの中でどちらかの側が削った行を、もう片側が残す形は通る（PR 側が消した行も merge で戻る）。時計を張れない環境（Windows）では引き継がない。`conflict-marker-size` を変えた repo・rename を伴う衝突・両側が同じ変更をした merge（`git diff <第 2 親> <merge>` に行が出ない）は取り直しになる。`origin/HEAD` が PR の base と違う branch を指す repo と、積み PR（base が別の feature branch）では引き継げない。
## 効果測定

以下の 3 つを field 名つきで定義する。新 field は追加しない。

| 指標 | 記録先 |
|---|---|
| 外部レビュー round 数 / PR | 既存 field `PR Review Follow-up Attempts`（`hooks/scripts/lib/constants.py` に上限 12 の定義あり。レビュー待ちの wake 数で、checkpoint の巡数は `gdd-pr-review-followup` の `PR Review Rounds` を参照） |
| 内側ループ round 数 | `Pre-PR Self Review` の `rounds` key |
| レーン別検出数 | 同 `lanes` key |

### 空洞化率（dogfood 第一観測指標）

`rounds: 1` かつ `dry: yes` かつ **`lanes` の数値が全て 0 で、かつ委譲 token（`not_applicable(independent-review)`）でも無い**証跡は「レビューせず書式だけ満たした」形と区別できない（`standard` の委譲記録形は「回した」側に数え、空洞化に含めない）。この比率（空洞化率 = 該当証跡数 / 全 dry:yes 証跡数）を dogfood 期間で観測する。新 field は追加せず、既存 key（`rounds`/`dry`/`lanes`）からの導出値として扱う。
