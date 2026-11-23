---
type: patch
---

#### Summary

- 独立レビューを 2 回目以降で差分に絞ると、範囲外（前回証跡の sha より前）で見つけた fail-open を後続課題に回したまま merge できた。範囲外でも **severity High または実害クラス**の finding は `advisory` にできず、`high` / `blocking` に計上することを契約に入れた。PR 旧#77 のレビューで出た High 指摘への対応
- 計上義務の正本は **独立レビュー 1 か所**（`references/independent-review.md` 契約 3）に置く。`state.md` の `Independent Review` 行の `high` / `blocking` カウンタは、pre-push gate が `REQUIRE_DRY`、pre-PR gate が `PP_REQUIRES_DRY` の条件で読み（`trivial` / `quick (express)` / `quick (standard)` では読まない）、merge gate は `Bot Review Received: no` の経路で読む。契約を計上が起きる場所に畳むと、gate ごとに異なる降格規定との衝突を列挙しなくて済む。impl gate・completion-check・要件 gate の内部規定は変更しない。followup は基準点（`last_head`）と `範囲外 blocker` の強制発火を引き続き自前で持ち、契約 3 からそこへ pointer を張った
- 設計の経緯: 当初は「正本 1 か所＋参照 9 か所へ pointer と述語を inline」で進めたが、独立レビューを 5 回回す間に fail-open 型の high が 3 回連続した（Honest Limitations 既載の例外、Reviewer Calibration による severity 引き下げ、1c Reviewer File Scope Constraint など、finding を小さくする仕組みが gate ごとに別レイヤで存在し、名前でも効果でも列挙し切れなかった）。列挙をやめ、強制点（証跡カウンタ）へ畳む設計に切り替えた

#### Changed

- `references/independent-review.md` 契約 3 を **(3-a) 絞り込みの可否 / (3-b) 範囲の判定 / (3-c) 計上義務 / (3-d) 降格規定の非適用 / (3-e) followup との分担** の 5 項と、(3-a) 配下の fail-closed 箇条に割り、次を定めた（規定を 1 行に継ぎ足し続けた結果、主節と後置の限定句が食い違う退行が 2 周続いたため。契約 3 は分割前 1 行 948 文字、分割後は最長 678 文字。+10 行、`references/*.md` の headroom は 18 → 8）
  - (3-c) 範囲外でも severity High または実害クラスの finding は `advisory` にせず、新しい情報の根拠が無くても `high` に計上する（`blocking` は `is_blocking(category)` に従い、§ finding category が単独正本のまま）
  - (3-c) `high` に計上した finding は `medium` に二重計上しない
  - (3-c) 前回までに解消していない `high`・`blocking` は範囲外のままでも計上を続ける（独立レビュアーは前回の finding 一覧を持たないため、再報告されなかった分は main session が件数に足す）
  - (3-b) 範囲内として扱った finding の計上先は `medium` と書き切った（証跡行のカウンタは `high` / `medium` / `blocking` の 3 つで `low` を持たないため、「severity に従って `medium` に数える」は `low` の finding で自己矛盾していた。過大計上側なので fail-closed だが、読み手が解釈で埋める余地を残さない）
  - (3-b) 「範囲外」は位置ではなく **(3-a) が対象とした差分にも、その影響先にも当たらない箇所**と定義した（位置だけで書くと、(3-a) が意図的に対象へ入れた影響先が定義上つねに範囲外になり、そこで見つけた medium が計上されない）。advisory 既定は (3-c) の計上義務に当たらない finding にだけ適用する。昇格は `blocking` カウンタを直接動かすのではなく**範囲内として扱い、`medium` に数える**形にした（(3-b) の適用集合には `is_blocking` な category が存在しないため、旧文は `blocking` の単独正本と食い違っていた。計上先を書かないと、`medium != 0` で merge gate が要求する `Medium Disposition` の要否が推論頼みになる）。範囲内か範囲外かを判定できない finding は範囲内として扱う（fail-closed）
  - (3-d) **範囲内か範囲外かを問わず、severity High または実害クラスの finding には**、severity を引き下げる規定（`self-contained-contract.md` § plugin が内包すべき必須契約 の reviewer calibration 契約 Stage 2、impl gate 手順 5 の 1 段階降格）と、`advisory` へ落とす規定（Honest Limitations 既載の例外、`origin: pre-existing` の既定、impl gate 1c の Reviewer File Scope Constraint）を、名称を問わず適用しない。適用できるのは **severity が medium 以下で、かつ実害クラスでない** finding に限る
    - 降格の可否を範囲で分岐させると、契約 3 が影響先（同じ入力を読む別の実装）を範囲内に含めるため、観点 (h) で見つかる `origin: pre-existing` の High がそのまま抜け道になる
    - 許可集合を severity だけで書くと、**medium × 実害クラス**（常時 High は `data-loss` を含まないため正当に存在する）が両条件に該当し、`blocking` を 1 → 0 にできてしまう。`blocking` は `is_blocking(category)` で数えるため、これは受理述語の素通りに直結する
  - (3-a) 前回証跡を読んで絞り込みを決めるのは **main session** である（契約 1 は reviewer に前回レビュー結果を渡さない）
  - (3-e) PR 後の周回でも独立レビューの起動範囲の基準点は契約 3 の前回証跡 sha のままで、`gdd-pr-review-followup` § 差分スコープ の `last_head` は PR レビュー finding の対応範囲と `範囲外 blocker` の強制発火にのみ用いる（計上義務の正本は契約 3）
  - (3-a) 冒頭で「本条でいう**対象**は、差分とその影響先（変更したシンボルの呼び出し元・同じ入力を読む別の実装）を指す」と一度だけ定義し、分岐ごとには書かない。分岐ごとに書いていたときは、絞り込み分岐にだけ影響先があり、1 回目の既定と fail-closed 分岐の 2 か所から漏れていた（fail-closed 側のほうが範囲内が狭いという逆転が 3 周続けて起きた）
  - (3-a) の 3 分岐（1 回目の既定・絞り込み・fail-closed の全量）は、いずれも定義語「**対象**」で読解範囲を書く。定義を冒頭へ集約した直後は絞り込み分岐だけが「差分に絞ってレビューする」と定義語を使っておらず、字義上そこにだけ影響先が付かない状態になっていた（影響先で見つかる High がそもそも読まれないため、(3-c) の計上義務が空振りする fail-open）
  - (3-a) 絞り込みを禁じる条件を 1 条件 1 箇条で列挙した（1 文に並べていたときは、下の 2 条件が同時に抜けていた）
    - 前回証跡が両方 0 でない
    - 証跡行が `self-review-lanes.md` § merge gate 証跡 の書式として valid でない、**または `blocking` key を欠く旧書式行（`legacy-no-blocking-field`）である**。後者は gate を通るが `blocking` の件数が不明なため、絞り込みの前提（前回が両方 0）を満たせない
    - 前回証跡の sha が解決できない、**または push 対象 tip の祖先でない**（履歴を書き換えても旧 commit は解決できるため、解決可能性ではなく祖先関係で判定する）
    - 差分が空
  - (3-c) 計上先は分配的に書いた: High は `high` に、実害クラスは `blocking` に（両方に当たるなら両方）。`high` を「High severity の件数」と定義する followup:196 / self-review-lanes:130 との非対称を消すため
  - (3-c) 計上した `high`・`blocking` は当該 push で 0 まで解消する。強制するのは**独立レビューを要求する `standard` の** pre-push / pre-PR gate であり、`trivial` / `quick (express)` / `quick (standard)` は独立レビュー自体を要求しない。merge gate が本行を読むのは `Bot Review Received: received: no` **かつ `Last Review Push At` が valid** な経路のみで、`received: yes` では本行を読まず reason code も積まない（`Pre-Merge Review Recheck` と `Merge Approval` が merge を止める）
- `references/independent-review.md` § 証跡: 範囲外の finding も契約 3 により `advisory` にできないものは件数に数えることを明記した。受理述語（`high: 0` かつ `blocking: 0`）・証跡行の書式・sha 一致検査・絞り込みの前提条件（前回が両方 0 のときだけ）は変えていない

#### Affected Files

- `references/independent-review.md`
- `skills/gdd-pr-review/SKILL.md`（bundled か上流 plugin かを問わず `pr-review` の停止条件を「High も実害クラスも 0」と読み替える上書きを置く。bundled `pr-review.md` は SYNC 対象なので触らない）
- `skills/gdd-pr-review-followup/SKILL.md`・`references/post-completion-pr-flow.md`（(3-d) と同じ「medium 以下かつ実害クラスでない」で割る。pre-PR flow は「残存 finding の集合」を読む述語が 3 つある——手順 3 の差し戻しトリガ、その配下のカウント定義（`Pre-PR Fix Attempts`）、手順 4 の進行条件——ので、3 つとも同じ述語へ揃えた。1 つだけ直すと、medium × 実害クラスが block も記録もされずに PR へ進む／差し戻しても Attempts に載らず `human_recheck_required` へ到達しない、という別々の穴が開く）
- `tests/test_diff_scope_out_of_range_blocking_contract.py`（新規。後に PR 旧#463 で削除）
- `tests/test_independent_review_differential_scope_contract.py`（既存 pin を新構造へ追随）

#### User Action Required

- 独立レビューを起動する側: 範囲外の指摘でも High・実害クラスは advisory に落とさず証跡の件数に入れる。hook と受理述語は変わっていないため、利用するだけの人の対応は不要

#### Validation / Eval Impact

- 追加 test（後に PR 旧#463 で削除）: `tests/test_diff_scope_out_of_range_blocking_contract.py`（AC-1 範囲外 High の計上を完全文で固定 / AC-2 fail-open の 3 ケース（allow への転落・基準点の欠落や解決不能や空差分・判定不能）/ AC-3 契約が独立レビュー 1 か所にしか無いこと / AC-4 証跡の計上と受理述語・sha 一致検査の不変 / 内部 gate の降格規定を変更していないこと / 降格規定の適用を範囲で分岐させる表現と、許可集合を severity だけで書く表現が無いこと / (3-a)〜(3-e) の見出しと順序、1 行 750 字未満（分割前の 948 字を下回る上限にして判別力を持たせる）/ fail-closed の 4 条件がそれぞれ独立した箇条であること——所有箇条の一意性・条件数・弱化語の不在を検査し、改変 3 種（2 条件の畳み込み・箇条末尾への例外句・条件でない地の文の混入）を実際に当てていずれも落ちることを確認した / followup が基準点と強制発火を自前で持ち続けること / 対になる followup・post-completion-pr-flow が severity ∧ category で割られていること / pre-PR flow の 3 述語（トリガ・カウント定義・進行条件）と followup の差分スコープ行が、行全体で pin されていること / 正本ファイルの見出し集合が全階層（`#` 以上すべて）で期待値と一致すること（節を新設して免除を置く改変をここで落とす。`##` だけを見ていたときは `###` 節の新設が素通りした）/ **正本ファイル全体**・対の 5 行に pin されていない**文**が無いこと（契約 3 のブロックだけ→`## 契約` 節だけ、と走査範囲を広げても、そのつど節の外側へ免除を置く改変が素通りしたため、ファイル全体へ広げた）——語彙のブラックリストは語を変えた例外句を素通りさせたため、地の文まで pin し「pin を差し引いた残りが markdown の記号だけ」を要求する形にした。lead 文末尾・見出し行末尾・(3-c) 行末への例外句、対の片方を severity だけへ戻す改変、対の pin 直後への再許容句、(3-f) という新しい免除項の挿入、契約 3 の外側（`4. **モデル**` の直後）への `5. **例外**` の挿入、`## 適用除外` 節の新設、§ 証跡 への免除句の追記（同じ行の末尾／別の行として／pin 行の直前の 3 形）、`### 運用上の緩和` 節の新設、冒頭引用への免除句の挿入、(3-a) の対象定義から影響先を落とす改変を当てて、いずれも落ちることを確認した。残差方式は差し引くだけなので **pin 済みの文を丸ごと削除する改変は素通りしていた**（観点レーン (g) の行を消しても全量スイートが 1 件も落ちなかった）。差し引く前に pin の存在を要求する検査を 3 つの残差ガードへ入れ、同じ削除を当てて落ちることを確認した）/ (3-a) の 3 分岐がいずれも定義語「対象」で読解範囲を書いていること（絞り込み分岐だけが定義語を使わない状態を RED で確定してから直した） / 契約文が**所属する項の中に在る**こと（逐語 pin は位置を見ないため、AC-1 の中核文を (3-c) から `## 出力フォーマット` の直前へ逐語のまま移す改変が全量スイートを素通りした。所属表を持たせて落ちることを確認した） / 対の 5 行が**それぞれの見出しと親項の下に在る**こと（`停止条件の上書き` の箇条を `pr-review` を呼ぶ手順 1 から手順 2 の下へ移す改変が素通りした。移すと実行時に読まれない経路ができる。所属を固定して落ちることを確認した） / 対の各述語が**所有行と完全一致する**こと（PR 旧#85 レビュー指摘。`owners` を「どこかの pin 済み行に在るか」でしか検査していなかったため、述語を本来の所有行から別の paired 行へ移すコピーが素通りしていた。実測: `post-completion-pr-flow.md` の Known limitations 述語を削除し、`gdd-pr-review-followup/SKILL.md` の差分スコープ行へ移したコピーで実行しても 21 passed, 93 subtests passed だった。各述語の所有行を`PAIRED_PREDICATE_OWNER` として明示し、`owners` がその 1 行と完全一致することを検査する形に直し、同じ改変で落ちることを確認した）
- Skill RED-GREEN Evidence: 実装文脈を渡さない実行者に同じ pressure scenario を当てた。RED（main 相当）は「範囲外の fail-open は advisory、`high: 0 / blocking: 0` で push 可」と判定した。GREEN は `high: 1 / blocking: 1`・push 不可と判定した。あわせて起点が解決不能・差分が空・範囲内外が判定不能・`pre-existing` を理由にした降格（範囲内・範囲外の双方で通らない）・High × `product`（`high: 1 / blocking: 0`）も、いずれも契約文から一意に導けることを確認した
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（BLOCK の追加なし）
- `references/*.md` の line budget: 11919 / 11927（headroom 8）。契約 3 の分割で +10 行

#### 受け入れた限界

- (3-b) の「範囲外」は計上の判定語で、`skills/gdd-pr-review-followup/SKILL.md` § 差分スコープ の「対応範囲外」（比較 diff の変更行基準）とは別概念である。同じ語が 1 つのワークフロー内で 2 つの意味を持つ。計上義務の正本は (3-c) なので計上自体は守られる
- `skills/gdd-pr-review/SKILL.md` の上書きは bundled `pr-review.md` の該当行を行番号でも文言でも検査していない。上流 `pr-review` plugin が更新されて当該文が変わっても、テストは無言で通る

- `Independent Review` 行の `blocking` key を書かない旧書式は、`merge-gate-evidence.sh:330` が `legacy-no-blocking-field` として `blocking = 0` で受理する（`GDD_MG_REQUIRE_BLOCKING_FIELD="false"`）。したがって key を省けば `blocking` カウンタは 3 gate すべてで 0 になる（merge gate は `legacy-evidence-no-blocking-field` の監査ログを 1 行残して受理し、pre-push / pre-PR は無音で 0 とみなす）。本 PR の契約は (3-a) でこれを「絞り込みの前提を欠く」として全量レビューへ倒すが、gate の受理集合は変えていない。この互換窓は `self-review-lanes.md:140` が W-28（reviewer category 出力契約）着地後に `true` へ反転すると明記しており、所有者はそちらにある。pre-push / pre-PR だけ先に塞ぐと merge gate との受理集合が非対称になるため、本 PR では実施しない

- 強制されるのは `state.md` の自己申告カウンタ（`high != 0` または `blocking != 0` で block）だけで、「範囲外の High を実際に数えたか」を検査する hook は無い。reviewer が黙って降格した場合は検出できない。機械検査できる形（降格を `demoted:` 行としてのみ許し hook で検査する）は `state.md` の schema と hook の変更を伴うため別タスクとする
- followup と pre-PR flow の「範囲外は advisory」規定は、(3-d) と同じ「medium 以下かつ実害クラスでない」へ揃えた（対の片方だけ直すと medium × 実害クラスが漏れるため）。impl gate・completion-check・要件 gate の内部規定は変えていない。内部 gate は finding を遅らせられるが、merge 前の独立レビューの計上は通過させられない。全 gate の文言を揃えることは今回のスコープから外した
- 「残存 finding の集合を読んで差し戻す／進む」述語は、本 PR で揃えた pre-PR flow の 3 か所と `gdd-pr-review/SKILL.md` の loop 終了条件のほかに、`skills/gdd-completion-check/SKILL.md:350`（「High finding 残存時は `gdd-systematic-debugging` に差し戻す」）と `references/phase-progression.md:491`（「High finding があれば `blocked` で停止」）・`:691`（「PR Flow 中の High finding」）が残る。**`dry` 判定はこれらの補償にならない**——`references/self-review-lanes.md:100` の `dry` は「その周回で**新規** high または blocking ゼロ」で、前巡で受容した**残存** blocking は次周回の `dry: yes` を妨げないため、軸が違う。止まるのは `Independent Review` の受理述語（`high: 0` かつ `blocking: 0`）が効く `standard` の pre-push / pre-PR gate だけである。文言を揃えるのは別タスクとする
- (3-a) の fail-closed は 4 条件の列挙で、条件そのものを判定できない場合の既定を持たない（(3-b) の「判定不能なら範囲内」に相当する規定が (3-a) には無い）。また `hooks/scripts/lib/detect-steering.sh` の `gdd_extract_doc_field` は最初の一致行を返すため、`Independent Review` 行が 2 本ある場合に main session と hook で前回証跡がずれうる
- medium × 実害クラス（`blocking` にだけ計上される finding）を `medium` にも数えるかは (3-c) で未定義。merge gate は `medium != 0` のとき `Medium Disposition` を要求するため、数え方で要求証跡が変わる（どちらに倒しても fail-closed）
- `self-review-lanes.md:130` は merge gate の経路を「`received: no` の経路でだけ」と書いており、(3-c) に足した「かつ `Last Review Push At` が valid」の限定がそちらには無い（block する点は両者とも同じで、fail-open にはならない）
- bundled `skills/gdd-pr-review/references/pr-review.md` の停止条件は High 単独のままである。同ファイルは上流 `pr-review` plugin との SYNC 対象（冒頭の SYNC 注記）なので書き換えず、GDD が所有する `skills/gdd-pr-review/SKILL.md` 手順 1 に上書きを置いた。上書きは「bundled か上流 plugin かを問わず、`pr-review` の loop 終了条件と PR 作成前チェックリストの停止条件を読み替える」という形で、経路にも行番号にも依存しない（SYNC で該当行が動いても効く）。残る非対称は、上書きを読まずに bundled 本文だけを読む実行者には旧述語が見える点である
- `tests/test_diff_scope_out_of_range_blocking_contract.py` の `test_evidence_section_carries_no_escape_hatch`（ファイルごと PR 旧#463 で削除）は、走査対象も pin 集合も `test_canonical_file_carries_no_escape_hatch` の部分集合で、独立した判別力を持たない（節単位でエラーを出すためだけに残していた）
- `references/reviewer-common.md` § Finding の由来と scope の `origin: pre-existing` の既定（「別 PR / 別タスクへ切り出すを推奨し、この差分での修正を求めない」）は無条件のままで、(3-d) への戻り pointer を持たない。独立レビュアーは同ファイルを `origin` の正本として読むため片方向 pointer になる（severity も件数も変わらず disposition の話なので、後続課題）
- (3-c) は `blocking` を `is_blocking(category)` に完全に依存させたため、category 未付与の finding は非 blocking 扱いになる。medium × 実害クラスで category を書き忘れると `blocking: 0` のまま通る（High は `high` に載るので止まる。出力フォーマットが category を必須にしているため到達性は低い）
- 対の 3 ファイル（`references/post-completion-pr-flow.md` / `skills/gdd-pr-review/SKILL.md` / `skills/gdd-pr-review-followup/SKILL.md`）は、pin した 5 行が動いていないかしか検査しない。正本ファイル（`references/independent-review.md`）はファイル全体を残差走査しているのに対し、対の側は pin 行の**隣**に免除句を足す改変を検出できない（実測: 手順 3 配下に `origin: pre-existing` を差し戻し対象から除外する箇条を追加しても、対応する contract test は 1 件も落ちなかった）。全体走査へ揃えるかブロック単位へ広げる作業は別タスクとする（このテストは後に PR 旧#463 で削除。今は対の側も正本ファイルも機械では検査しない）
- (3-b)・(3-d) は `advisory` を severity 相当の値として使うが、`§ 出力フォーマット` の値域宣言は high / medium / low の 3 段階で `advisory` を含まない。`advisory` は disposition（計上しない）であって severity ではないという 1 文を書き足すのが安いが、`references/*.md` の headroom が 8 行しか無く、残差方式の pin 集合へ新しい文を通す作業と合わせて別タスクとする（pin 集合を持つテストは後に PR 旧#463 で削除）
- `agents/gdd-implementation-reviewer.md` と `agents/gdd-security-reviewer.md` の Honest Limitations 例外には、impl gate skill 側にある実害クラス除外が無い。独立レビュアーはこれらの agent ではないため契約 3 の計上には効かないが、非対称は残る（後続課題）
- 降格を封鎖する境界は severity と category（High・実害クラス）であり、範囲ではない。範囲内の medium 以下には既存の降格規定がそのまま効くため、`pre-existing` の medium を別 PR へ切り出す運用は変わらない。ただし「High か実害クラスか」の判定自体は reviewer に委ねられており、境界を severity に寄せたぶん、その判定誤りがそのまま計上漏れになる
- merge gate が `Independent Review` 行を読むのは `Bot Review Received: no` の経路だけである。`received: yes` の経路では `Pre-Merge Review Recheck` の `new_blocking` と `Merge Approval` が merge を止める。最終 push の後に独立レビューを回して範囲外 High を計上しても、その経路では本契約の計上が merge 判定に直接は効かない
