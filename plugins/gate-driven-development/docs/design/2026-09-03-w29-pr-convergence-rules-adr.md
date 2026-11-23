# ADR アーカイブ: W10 / W-29 — finding category taxonomy と merge-gate 判定の刷新

> **出典**: `.steering/20260903-w29-pr-convergence-rules/adr.md`（design-gating、2026-09-04 確定）を逐語アーカイブしたもの。
> `.steering/*/` は branch-only artifact でリリースに含まれないため、意思決定の記録として本ファイルへ移す。
> 個々の判断の本文・数値・実測はすべて本ファイルが正本。

> 2026-10-16 追記: pre-push gate・pre-PR gate・merge gate は、今はコマンドを止めずに実行後に通知する（docs/adr/2026-10-15-merge-gate-notice-only.md・docs/adr/2026-10-16-push-pr-gate-notice-only.md）。本文の「止める」「block」は当時の挙動である。

design-gating（2026-09-04）で確定した意思決定と、却下した代替案の記録。`design.md` は「現在の正しい設計」、本ファイルは「なぜそう決めたか / 何を却下したか」を持つ。

## ADR-1: category 語彙の単一正本を named alias で実現する

- **Context**: AC-1 は `category` 語彙 9 値を `references/reviewer-common.md` の 1 箇所だけに定義し、他は参照のみとする。一方 AC-7 / AC-8 の requirements 本文はバッククォート付きの category リテラルを列挙しており、文面どおり実装すると AC-1 に違反する。
- **Decision**: 参照側（`references/state-machine.md` / `references/state-field-tiers.md` / `skills/gdd-implementation-gating/SKILL.md`）はリテラルを再掲せず、named alias（**実害クラス** = `blocking: yes` の 4 値 / **Round 非消費 category** = `Round 消費: no` の 3 値）と正本 pointer だけを書く。
- **Why**: リテラルを再掲すると X-15（語彙の正本分散）を新規に作る。alias 方式なら AC-7 / AC-8 の規則の意味は変わらず、AC-1 の契約テストも同時に満たせる。
- **Consequences**: 読者は alias から正本へ 1 ホップ必要になる。契約テストが正本ファイルを 1 本に固定するため、W-28 が別ファイルに語彙を書いた瞬間にテストが赤くなる（統合時の検出点として機能するが、他ブランチを落とす副作用でもある）。

## ADR-2: AC-1 契約テストはバッククォート付きトークン形だけを走査し、`agents/` を除外する

- **Context**: `product` / `style` / `fail-open` は一般語であり、素の文字列走査では誤爆する。実測で `fail-open` は `references/` / `skills/` の 15 ファイルに散文語として存在する。一方バッククォート付き 9 トークンは `references/` / `skills/` / `agents/` に 0 件。
- **Decision**: 走査は `` `<token>` `` の形に限定し、走査範囲は `references/**/*.md` + `skills/**/*.md` とする。`agents/` は走査しない。
- **Why**: バッククォート形は語彙宣言の形であり散文語と構造的に区別できる。`agents/` を含めると、reviewer 出力契約（producer）を所有する W-28 と正面衝突する。requirements § 非スコープの producer/consumer 境界をテストの走査範囲として機械化する。
- **Consequences**: producer 側の語彙再掲は本 PR のテストでは検出されない。`product` / `style` は将来 style guide 等の文脈でバッククォート付き使用が起きうるため、他 2 トークンより誤爆確率が高い。

## ADR-3: 旧書式（`blocking` 欠落）の既定は `requirements.md` の (c) 定義を採る【確定】

- **Context**: `state.md` § Approved Direction は「(c) 段階移行（blocking 欠落は warning+**旧判定**、W-28 着地後に昇格）」、`requirements.md` HCQ2 の (c) は「warning 記録のうえ **(b) の判定**（`high != 0` のみ）を使う」。同じ Approved Direction 行が「全項目、無回答時デフォルト=AI 推奨をそのまま採用」とも書いており、HCQ3 では (a) を記録しているのに requirements の AI 推奨は (b) という自己矛盾もあった。
- **Decision【2026-09-04 human check で確定。暫定解釈を正式決定に昇格】**:
  1. HCQ2 の「旧判定」= `requirements.md` の (c) 定義。すなわち **`blocking` 欠落は 0 とみなし、判定は `high != 0` のみ**。欠落の事実は `_mg_log_suppressed "legacy-evidence-no-blocking-field"` に warning として記録する
  2. HCQ3 は **(a) 等価交換のみ**で確定。X-18（budget 上限引き上げ）は本 PR に含めない
  3. Approved Direction 末尾の「全項目、無回答時デフォルト=AI 推奨をそのまま採用」という記載は**誤りとして無視する**（個別選択の記録が優先）
- **Why**: 「旧判定」は (a) fail-closed とも読めるが、(a) は requirements が明示的に「目的未達」として退けた選択肢であり承認意図と矛盾する。planning-reviewer も requirements 優先の解釈を妥当と判定していた。ユーザーがこの解釈をそのまま確定回答として採用した。
- **Consequences**: W-28 着地までの移行期間、実害クラスの検出は効かず、緩和分の説明責任は `Medium Disposition`（AC-4）の機械強制だけが担う。ただしその強制は `Bot Review Received: received: no` 経路にしか到達しない（design.md § ロールバック / fail-closed）。**訂正（completion-check Round 3、2026-09-06、独立レビュー指摘）**: 「穴を閉じる操作は定数 `GDD_MG_REQUIRE_BLOCKING_FIELD` の 1 箇所反転で完了する」という記述は、この定数を実際に読んで判定を分岐させる消費側コードが（`grep` で確認した限り）まだ存在しないため誤り。反転が意味を持つには、W-28 側の producer 契約着地に加え、この flag を読む分岐の実装が別途必要。

## ADR-4: requirements の参照先ずれ 3 件を design 側で訂正した

- **Context**: 実測により、requirements の AC 本文が指す参照先が 3 件ずれていた。
- **Decision**:
  1. AC-7 の検証先を `references/gate-checklists.md` から、実際の Round カウント site（`skills/gdd-implementation-gating/SKILL.md` の `Gate Rounds` +1 箇所 と `references/state-field-tiers.md` の field 定義）へ訂正
  2. AC-7 / AC-8 の語彙列挙を named alias へ置換（ADR-1）
  3. AC-11 の対象に `references/human-check-template.md` を追加（`scripts/lint-hitl-stage-plan.py` が読むのは human-check draft の `段階実装案` テーブルであり `requirements.md` ではない）
- **Why**: いずれも AC の受入条件そのもの（何が満たされれば pass か）を変えず、参照先の事実誤認を正すだけ。
- **Consequences**: AC-11 の変更ファイル数が 1 増える。`references/human-check-template.md` は standard runtime profile 外なので runtime token budget には影響しないが、`references/*.md` 行数 budget には効く。

## ADR-5: Round 2 は `human_recheck_required` で escalate し、A〜D の確定をもって Round 3 で approved にした【確定】

- **Context**: Round 2 レビューで High 6 件 / unresolved Medium 11 件を検出した。うち 2 件は `design_detail_only` の範囲を超える。
  - budget が 1 本ではなく 3 本 headroom ≒ 0（gate 側で実測再現）。承認ポイント 3 の判断材料として提示した「limit 11922 / actual 11922 / headroom 0」という単一 budget の framing が事実として不完全だった
  - `state.md` § Approved Direction が HCQ3 で (a) を記録する一方、同じ行が「無回答時デフォルト=AI 推奨」と書き、requirements の AI 推奨は (b)（X-18 を含める）だった
- **Decision**: Round 2 では `references/rollback-patterns.md` § `human_recheck_required` に従い差し戻し、A（budget 方針）/ B（承認記録の食い違い）/ C（スコープ境界 = item 旧#2）/ D（独立案 B の採否）を人間判断に返した。**2026-09-04 にユーザーが 4 論点すべてを確定回答**（A=案1 等価交換のみ、B=ADR-3 の解釈で確定、C=案1 Stage 1 に含める、D=不採用）。Round 3 でこれを design.md / adr.md に反映し、残る High / Medium もすべて design 内に処置を書き切ったうえで `Design Review Status=approved` とする。
- **Why**: Approved Direction の「人間に戻す条件」に **「budget 上限値そのものの引き上げ（X-18）採否」** と **「AC の追加・削除」** が明記されており、Round 2 の 2 件はいずれにも直接該当した。承認の前提となった数値が不完全なまま design 側で方針を拡張する（等価交換を 3 本へ広げる / S1 を落とす）のは silent change にあたる。逆に、確定回答が出たあとに同じ論点で再度 human check へ戻すのは承認往復の空転であり、Round 3 は `design_detail_only` の範囲で閉じるのが正しい。
- **Consequences**: design gate を 1 往復追加した。一方、実装に入ってから `validate-plugin.sh` が落ちて planning_rework になる経路（AC-13 が確定で fail する）を回避し、budget 3 本の削減対象を実測値つきで確定できた。C の承認により producer 契約領域（`references/reviewer-common.md` § Output Format、`skills/gdd-pr-review-followup/SKILL.md`）に踏み込むため、W-28 との conflict 面は広がる。

## ADR-6: budget 3 本すべてを等価交換で吸収し、削除ではなく `docs/` へ移送する【確定】

- **Context**: A の確定回答は「3 本すべてを等価交換のみで吸収する（X-18 は含めない）」。一方 Round 2 M-13 は、当初の donor（旧 `references/` 配下の `team-onboarding.md` の quick サンプル 2 本。現在は `docs/references-archive/team-onboarding.md`）が `references/` 配下で**唯一の記入済み worked example** であり、単純削除は requirements § リスクの「削除は『参照へ置換』に限定し、削除した本文の移送先を明記する」に反すると指摘した。
- **Decision**: donor を**削除ではなく移送**に変更する。旧 `references/` 配下の `team-onboarding.md` L97-163（67 行）と `references/task-sizing.md` L69-83（`### Direct Intent スコアの計算例`、15 行 / 918 chars）を `docs/references-archive/worked-examples.md` へ移し、元の位置には pointer だけを残す。加えて `references/task-sizing.md` L224-232（`## Auto-Confirm Decline` の例ブロック、9 行 / 294 chars）は直前の template ブロックが正本なので削除して pointer に置換する。budget 2（SKILL body total、headroom 0）は**追加を 0 行に設計する**ことで donor 不要にする（既存行への節追加のみ）。
- **Why**: `docs/` はどの budget の計測対象にも入らない（budget 1 = `references/*.md`、budget 2 = `skills/*/SKILL.md`、budget 3 = runtime profile 12 ファイル）。`docs/references-archive/worked-examples.md` は既存の worked example 置き場で `tests/checks/skill-body-budget.sh` の `required_files` にも登録済みという先例がある。移送なら内容が 1 行も失われず、M-13 の指摘と A の確定回答を同時に満たせる。
- **Consequences**: worked example への到達に 1 ホップ増える（`references/` から `docs/` への pointer 経由）。`docs/` は runtime に読まれないため、実行時に例を参照する導線は失われる。budget 2 の headroom は 0 のまま維持されるので、実装中に skills 側へ 1 行でも足すと即 fail する。

## ADR-7: `Medium Disposition` に sha / count を持たせて恒久バイパスを閉じる【確定】

- **Context**: Round 2 H-2（security H-1 / dialectic F4）は、当初設計の `Medium Disposition`（sha なし・件数と無関係）では緩和分の唯一の統制が空洞化すると指摘した。(a) 一度書けば以後の全 push で再利用可能、(b) 節を見ずに field を拾うためテンプレ引用でも成立、(c) `recorded: accepted | <理由>` が medium 12 件を 1 行で allow にできる。
- **Decision**: 書式を `- Medium Disposition: <sha> | count: <uint> | recorded: <URL | accepted> | note: <1 行> | at: <ISO 8601>` とし、(1) `<sha>` を **HEAD 一致検査の対象に含める**（検査対象は 4 field → 5 field）、(2) `count` が `Independent Review` の `medium` と一致することを要求、(3) `recorded` / `note` がプレースホルダ（`<...>`）または空なら invalid、とする。
- **Why**: (1) が (a) を、(2) が (c) を閉じる。(b) は既存 6 field すべてが共有する `gdd_extract_doc_field` の弱点で、W-29 が新規に作るものではないため本 PR では埋めず既知の限界として明記する。**当初設計が掲げていた「HEAD 一致検査の 4 field は増やさない」方針はここで撤回する** — 検査 field を 1 本増やすコストより、緩和分の統制が 1 行で恒久バイパスされるリスクのほうが大きい。
- **Consequences**: `references/self-review-lanes.md` の「sha を持つのは 5 field」「HEAD 一致まで検査するのは 4 field」を 6 / 5 に更新する必要がある。push のたびに `Medium Disposition` の書き直しが要るため、followup ループの手順が 1 ステップ増える。

## ADR-8: category 未付与 finding の consumer 側既定を `product` 相当（fail-closed）にする【確定】

- **Context**: Round 2 H-5 は、merge gate 側は AC-5 で既定を持つのに impl-gate 側（AC-6 / AC-7）に category 未付与の既定が無い、と指摘した。W-28 未着地の期間、reviewer が category を出さない可能性がある。
- **Decision**: category 未付与の finding は **`product` 相当（Round 消費・非 blocking）** として扱う。この既定を `references/reviewer-common.md` § finding category の正本表直後に 1 行で書く。
- **Why**: 「未付与 = advisory」に倒すと W-28 未着地の全期間が fail-open になる。「未付与 = 実害クラス」に倒すと既存の全 medium が block され AC-3 の緩和が消える。`product` 相当は **impl-gate 側で旧挙動（severity で判断し Round を消費する）と厳密に一致する**唯一の既定であり、移行期間の挙動を現状維持にできる。
- **Consequences**: AC-7 の安全網の発火ケースから「W-28 未着地で category を付けない出力が来たとき」が消える（未付与も Round を消費するため）。

## 却下した代替案

| 代替案 | 却下理由 |
|---|---|
| severity ラベル自体の再定義（medium 廃止、high/blocking の 2 値化） | reviewer 出力契約の全面改訂になり W-28 と正面衝突する。severity は記録用に残し block 判定だけ category に移す方が変更面が小さい |
| merge gate ではなく skill 散文だけで規則を書く | `.steering/` 不在レーンでは 0 効果。レーン非依存にするには hook 側に置く必要がある |
| hook 側で category 一覧から `blocking` を再計算する | hook は state.md の散文を parse するだけで finding 本文を持たない。証跡に数値として書く方が帳簿 markdown の parse 誤爆を増やさない |
| AC-7 の条件を「blocking ゼロなら approved」に広げる | 未解消の `product` finding まで通ることになり AC の意味が変わる |
| AC-4 に移行猶予（grace period）を設ける | 旧書式に対して新ルールは旧ルールの厳密な緩和であり、猶予条件は分岐を 1 本増やすだけで利得が無い |
| counter の独立案 B（disposition ledger: `unresolved` カウンタ + `fixed/deferred/accepted` の算術検算） | **2026-09-04 の human check（論点 D）で不採用が確定**。AC-1 / AC-6 / AC-7 / AC-8 が category 語彙の値域と単一正本を受入条件として固定しており、採用には AC 再承認（承認往復の追加）が必要 |
| item 旧#2（reviewer 出力書式への `category:` 行追加）を Stage 1 から落とす | **2026-09-04 の human check（論点 C）で「Stage 1 に含める」が確定**。producer 契約（W-28 所有）への越境をユーザーが承認した |
| budget 上限の引き上げ（X-18、`references/*.md` limit を 12160 程度へ） | **2026-09-04 の human check（論点 A）で不採用が確定**。3 本すべてを等価交換のみで吸収する |
| AC-7 の評価入力を state に永続化する新 field（round ごとの category 記録） | 新 field を足すと `references/state-field-tiers.md` の field lifecycle と証跡書式の両方を広げ、budget 3 本すべてに効く |

## 補遺: Pre-PR Blocker 解消（2026-09-05〜06、completion-check Round 22）

上記 ADR-1〜8 の確定後、実装・impl-gate・completion-check を経て `origin/main`（34 commit 先行）へ統合する段階で、以下の運用判断を追加で行った（設計上の ADR には昇格しない、統合作業の記録）。

- **統合方法**: `git rebase` は auto mode classifier に拒否されたため、ユーザー選択で `git merge origin/main --no-edit` を採用（履歴改変を避ける）
- **`test_merge_gate_hook.py` の分割コンフリクト解消**: `origin/main` が同ファイルを 7 ファイルへ分割済みだったため、本 PR の追加分をクラス単位で対応する分割後ファイルへ手動再配置し、独立レビュー（`gdd-completion-reviewer`）が行の多重集合照合で正確性を確認した
- **`gdd-codebase-health-baseline.json` の閾値引き上げ**: CHANGELOG.md 行数 ratchet を統合後の実測値へ再計算する必要があり、具体的な数値をユーザーへ提示して明示的な承認を得た（ADR-7 が要求する「緩和には代償とセットの承認」という設計思想を、この PR 自身の統合作業にも一貫して適用した）
