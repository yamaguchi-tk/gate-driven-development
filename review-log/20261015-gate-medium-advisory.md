---
lane: L1+
pr: 523
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | - | 0 | 0 | 0 | 2026-10-15 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f673416f | 2 | 5 | 2 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e0e202cb | 1 | 5 | 1 | 2026-10-15 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | e0e202cb | 0 | 0 | 0 | 2026-10-15 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | bf108fc2 | 0 | 1 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | product | fixed | Opus は規則を外し、impl-gating・completion-check で差し戻すのを High と実害クラスだけにする（express も同じ述語）、Stage A の差し戻しは残す、Gate Rounds は changes_requested のたびに +1、consumes_round と Round 消費の列は撤去、差し戻さない medium・low は記録して approved（同じ loop で直さない）、category 未付与の medium は止める側、design-gating は外す、を推した。main の案（design も含める、同じ loop で直してよい、express と同じ述語）と食い違ったので Fable に相談し、design-gating は外さず requirements-gating と同じ blocking の述語（AC の意味・スコープ・承認ポイント・安全境界）を当てる、ほかは Opus どおり、を採った commit: なし（方針） |
| I1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | completion-check 手順 13 の括弧が、impl-gate で advisory にした finding を completion reviewer が実害クラスと付け直しても数えから外す。括弧を消した commit: e0e202cb |
| I1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | category が 9 値の外の medium が未付与にも is_blocking にも当たらず advisory で通る。既定を 9 値の外にも広げた commit: e0e202cb |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | systematic-debugging・subagent-driven-implementation・impl-gating の Remediation Priority が、Step 9 に当たらない medium も同じ loop で直す。差し戻しの理由になった finding だけに絞った commit: e0e202cb |
| I1-4 | 独立-1 | medium | no | self-inflicted | product | fixed | completion-check の差し戻さない medium・low に記録先と PR 本文への搬送が無い。Advisory Findings に記録させ、state-field-tiers の書き手に足した commit: e0e202cb |
| I1-5 | 独立-1 | medium | no | self-inflicted | product | fixed | category 未付与の既定の反転で、gate 自身が出す Medium（scope 外・dead code・E2E 未実施・stub）が差し戻され blocking に数えられる。gate 自身の medium は実害クラスでない medium と定めた commit: e0e202cb |
| I1-6 | 独立-1 | medium | no | self-inflicted | product | fixed | testing gap の AC の検証が弱いと assert の判別力が重なり、括弧が category で advisory に寄せる。AC の Verification の evidence が AC を示せていないものと定め、括弧を外した commit: e0e202cb |
| I1-7 | 独立-1 | medium | no | self-inflicted | product | fixed | 見出しの改名で、進行中の task の旧見出しの記録が PR 本文に運ばれない。読み出しで旧見出しも読むようにし、断片の User Action Required を直した commit: e0e202cb |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | reviewer の出力の approved の条件（High と実害クラスが無い）が、gate の差し戻しの条件（Stage A・Spec Drift・evidence の不足）より狭い |
| I1-9 | 独立-1 | low | no | inherited | doc-claim | accepted | subagent-dispatch の gdd-security-reviewer の finding は blocking のまま扱うが、Step 9 と読み分けられない |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ops-blocking medium の定義の正本を state-machine.md とする参照（phase-progression・self-contained-contract・gdd-dev）が宙に浮く |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の design-gating の reviewer は category を出さないが出力形式と合わない commit: なし（PR 本文） |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の Pre-PR の独立レビューで拾い直す前提が express と quick には当たらない commit: なし（PR 本文） |
| I1-13 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の今までは差し戻さない product と同じ扱いの既定だったが差分前の挙動と合わない commit: e0e202cb |
| I1-14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | AC-7 の安全網の削除が断片に無く、Stage A・Spec Drift の今までどおりとも合わない commit: e0e202cb |
| I1-15 | 独立-1 | low | no | self-inflicted | test-power | accepted | evals id 27・28・30 は expected_output だけが替わり、採点する expectations は旧い規則の答えも通す |
| I1-16 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | README の High/Medium issue は自律 remediation loop で PR 前に解消が古い |
| I1-17 | 独立-1 | low | no | self-inflicted | product | accepted | design gate では High も 4 つの述語に当たるときだけ blocking になった（依頼が扱うのは medium の規則） |
| I1-18 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | independent-review (3-f) の design gate では blocking の述語に当たるときだけ直すが design-gating 手順 14 と食い違う |
| I1-19 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | repo ADR の ADR-8（category 未付与の既定は product 相当）が差し替えの記録無しに残る |
| I1-20 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 4 本に外した Round 消費の挙動が残る（リリースのときに版の節で直す） |
| I2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | reviewer-common.md:108 に足した gate 自身が出す finding の medium を実害クラスでない medium とする例外が、など で閉じず、inline review で gate が走査した checklist の finding も含むと読める。例外の文を消し、既定の主語を gate が扱う finding すべてにして、gate 自身の検査の 4 行に category を書いた commit: bf108fc2 |
| I2-2 | 独立-2 | medium | no | self-inflicted | product | accepted | Step 1 の scope 外の低リスクな Medium（advisory）と Stage A の approved scope を超えている（差し戻し）のどちらが勝つか書かれていない |
| I2-3 | 独立-2 | medium | no | self-inflicted | product | accepted | testing gap を category によらず blocking にしたので、independent-review (3-f) の finding が completion-check で blocking になる（(3-f) の除外が落ちた） |
| I2-4 | 独立-2 | medium | no | self-inflicted | product | accepted | Express の impl-gate（最後の safety net）で stub の意図確認と E2E 一貫性の未実施が advisory になり、testing gap の規則も Express に無い |
| I2-5 | 独立-2 | medium | no | self-inflicted | product | accepted | subagent-driven-implementation と systematic-debugging の 差し戻しの理由になった finding が Step 9 だけを指し、completion-check 手順 13 の理由が抜ける |
| I2-6 | 独立-2 | medium | no | self-inflicted | product | accepted | Advisory Findings に記録する時機が approved にする際 と 検出した時 で割れ、差し戻しの Round の advisory が記録から落ちうる |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の blocking に数える が independent-review (3-b)(3-c) の計上と合わない |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | evals id 28 の expected_output が古い testing gap の定義のまま |
| I2-9 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | state-field-tiers の行の形が completion-check の行を決めていない、唯一の搬送元 の語、post-completion-pr-flow の impl-gate 由来 |
| I2-10 | 独立-2 | advisory | no | self-inflicted | product | accepted | 確認待ち: 依頼は Round 消費の medium の規則を外すだけなのに、Stage A・Spec Drift を category によらず差し戻す締め付けを入れた。推奨（Opus・Fable とも）は残す案で進め、PR 本文で問う。testing gap は差分前から category によらず blocking だった（定義を狭めただけ） |
| M2 | 方針メモ-1 | advisory | no | self-inflicted | fail-open | fixed | 安全策 4 の 1 回目の発火（fail-open の high を含む巡が独立-1・独立-2 の 2 回）。Opus と Fable はどちらも A（続行。例外を消して category を宣言する）と X（Stage A・Spec Drift・testing gap を残す）を推した。割れた点は 2 つ：Opus は既定の主語を gate が扱う finding すべてにする形、Fable は inline の finding を reviewer の finding と書き足す形（より広く閉じる Opus の形を採った）。Opus は 3 巡目に (3-f) の除外を戻す案も含めたが、Fable は F1 だけに絞る案で、2 巡目の medium は accepted の規定なので Fable の側を採った。返事を待たずに推奨で進め、PR 本文で問う commit: bf108fc2 |
| I3-1 | 独立-3 | medium | no | self-inflicted | product | accepted | completion-check 4c-3 の codebase-health の Medium（category 欄が large_file など 9 値の外）が、新しい既定では字義どおり差し戻しになり、4c-3 の Verification に扱いを残す規定とぶつかる |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | design-gating の 5b・5d の Medium に category が無く、新しい既定と手順 9 の文の述語のどちらで決まるか定まらない |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | e2e-verification-catalog の Pattern 1 が、同じ規定を category なしで書いたまま |
| I3-4 | 独立-3 | low | no | inherited | product | accepted | Step 1 の scope 外 Medium（product）と Stage A の承認範囲を超えたら差し戻すがぶつかる |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | reviewer-common.md:87 の 9 値をリテラルで再掲しない と、:108 の category は検査の行に書く がぶつかる |
| I3-6 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | category は検査の行に書く を満たさない High と severity 未指定の自己検査の行が残る |
