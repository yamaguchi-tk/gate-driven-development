# ADR: done guard Check 2 の表行判定を「header prefix 判定」から「status セル分類」へ反転する

- **日付**: 2026-09-06（決定・PR 作成時に蒸留）
- **状態**: 採用
- **Superseded by**: docs/adr/2026-09-08-verification-closed-grammar.md（2026-09-08。不変条件を閉じた文法1本へ移行）
- **関連**: `plugins/gate-driven-development/CHANGELOG.md` の当該 entry / `plugins/gate-driven-development/hooks/scripts/lib/done_guard.py` / `plugins/gate-driven-development/references/self-contained-contract.md` § Verification status 許容値の早見表

## Context

GDD の Stop hook が `done` 遷移を許すかどうかは `validate_done_preconditions()` の 3 つの Check で決まる。Check 2 は `tasklist.md` の `## Verification` 節に未完了（`pending`）や失敗（`fail`）の行が残っていないかを見る。

この Check 2 が、表形式で書かれた Verification に対して **fail-open** していた。data 行かどうかの判定が `stripped.startswith("| method") or stripped.startswith("| ROW")` という header の prefix 一致で行われていたためである。canonical schema は `| method | status | evidence | notes |` なので、**data 行も `| method=ac:AC-1 | pending | … |` の形で `| method` から始まる**。header を弾くつもりの規則が data 行を丸ごと不可視にし、表に `pending` が残ったまま `done` が通っていた。

pending 検出側も `"| pending |" in line.lower()` という固定パディングの部分一致で、`|pending|` / `|  pending  |` / `| PENDING |` / `` | `pending` | `` のような表記差を取りこぼしていた。整列指定付きの separator（`|:---|:---|`）も data 行として素通りしていた。

header 側を賢くする方向（先頭 2 セルの一致で header を見分ける等）も検討したが、そちらは data 行と原理的に衝突し続ける。

## Decision

**判定を 2 つの不変条件に還元し、以下の規則はすべてそこから導く。**

1. **未完了の検出は無条件・列位置非依存**。`pending` / `fail` と完全一致するセルを持つ行は、
   形（表 / list / 散文）・インデント・引用・凡例・補助表を問わず、必ず未完了として報告する。
   これを抑止する規則を置かない
2. **完了の受理は canonical schema に一致する行だけ**。status 列を **1 つに確定**できた行の値が
   許容値のときだけ検証済みと認め、確定できない検証行は「status 判別不能」で block する

この 2 つを分けたことが本 ADR の主眼である。R9〜R15 の独立レビューが挙げた fail-open は
**すべて「検出の前段に置かれた何らかの絞り込み」が原因**だった（受理ゲート・凡例除外・
補助表除外・インデント除外・列候補の探索順）。検出を無条件にすると、逆側の「計上」を
どれだけ緩めても fail-open にはならない。以後、計上側の緩和は安全な変更として扱ってよい。

規則を 1 つ足すときは、**それが (1) 側か (2) 側かを明示すること**。(1) 側に絞り込みを
足す提案は原則として却下する。

- 許容 status 値は `pending` / `pass` / `fail` / `n/a` / `unsupported`（正本は `references/self-contained-contract.md`。この集合は変更しない）
- セル値は `` ` `` / `*` / `_` / `~` と前後空白（半角・タブ・全角空白）、および Unicode カテゴリ `Cc` / `Cf`（制御文字・zero-width）を除去してから lower で完全一致比較する
- **(2) 「行が検証済みか」は status セルの列位置で判定し、列は 1 つに確定する**。header 行が取れていればその列（見出し語は日本語 `ステータス` / `状態` / `判定` も解決する）、取れない表では canonical の 2 列目、0 列目が ID（`AC-01` / `V-01` / 連番、セル全体一致）なら 3 列目、**0 列目が status 値そのものならその 0 列目**（status 先頭列。ここを 3 列目と読むと目視で `pending` と書いてある行が evidence 欄の `pass` で verified に化け、逆に全 pass の節が解除不能な block になる / R16）。**候補を複数試して「最初に解決できた列」を採ってはならない**（evidence 欄の `pass` / `N/A` が status の代わりに読まれ、`| method=ac:AC-1 | 未実施 | pass | … |` のような未検証行が verified 扱いになる / 独立レビュー R2・R15 で実測）
- **(1) `pending` / `fail` の検出は列位置を問わず、どの除外規則よりも先に行う**。安全側（block 方向）の誤検出しか生まないため。凡例除外・補助表除外・インデント除外・形の判定はすべてこの後段に置く。受理するのは**完全一致**と**括弧注記**（`pending（未実施）`）まで。コロン注記（`fail: 0`）は notes の集計と区別できないので status 列限定にする。散文中の語（`- AC-1: … は pending`）は部分一致になるため対象外（既知の fail-open。§ 受容した挙動変化）
- **`N/A` / `unsupported` は AC 検証行では検証済みと認めない**（contract の早見表どおり。判定は method セルで行い、marker と `method=` / `method: ` ラベルを剥がす）。AC でも security evidence でもない行（gate / checkpoint の記録）は早見表の 2 軸に載らないため対象外にする（独立レビュー R5 / R9）
- **(2) 形の判定は「計上するか」だけに使う**（表 / list / 外側パイプ省略の別）。箇条書きの marker（`- ` / `* ` / `+ `、番号付き list）・引用記号（`> `）・全角パイプ（`｜`）はセル正規化の 1 箇所で吸収し、外側パイプを省いた GFM 表行は区切りの有無だけで受理する。status や識別子の有無を条件にしない。**この段が検出に関与しないことが重要**で、関与させると段が狭いときに `pending` 明記の行が不可視になる（この形の fail-open は 3 度発生した）
- **行が検証行かどうかは method セルの識別子で判定する**（`method=` / `ac:` / `AC-1` / `V-01` / `security_evidence`、または行内に許容 status 値がある）。検証対象を名指さない補助表（指摘一覧・変異表・対応表）は `## Verification` 節にあっても検証行として扱わない。**ただしこの除外を `pending` / `fail` の検出より先に効かせてはならない**（列順が違うだけの検証行が丸ごと不可視になる / 実測）。
- **method セルの位置は header から status 列を解決できたときだけ一意に決まる**。fallback 探索では候補列の直前と先頭セルの両方を AC 判定に使う（片方に固定すると、`| V-01 | ac:AC-1 | N/A | x |` か `| method | 結果 | evidence | notes |` のどちらかで AC 判定が外れる / 実測）。セル数やコロンの有無で散文を除外する方式は、コードスパンを含む注記行を誤って block し、逆に contract 記載の `AC-1: 説明` 形 method セルを素通りさせた（どちらも実測）
- **許容 status 値に括弧・コロンで始まる注記が続く形を受理する**（`pass（2026-08-30 …）`）。ただし**status 列を特定できる経路に限る**。列位置を問わない `pending` / `fail` の検出まで広げると、notes 欄の `fail: 0` で全 pass の節が誤って block される（実測）
- **`status=` / `status: ` のフィールドラベルはセル正規化で剥がす**。pending 検出と検証済み判定の両方が同じ正規化を通ることが条件で、片方だけに入れると `status=pending` が pass 扱いへ反転する
- **security evidence の判定は method セルだけを見る**。列位置を問わずに探すと notes 欄へ `security_evidence` と書くだけで AC 行の `N/A` が通る（実測）
- **インデント行の除外は計上側の、しかも表以外だけに残す**（§ 論点 2c 規則 2 の改訂）。検出にも掛けていたため、`  - Status: fail` と入れ子 list で書いた**実在の未完了 tasklist 2 件が丸ごと不可視**だった（実コーパス 455 件）。さらに表にも掛けていたため、list 項目の下に入れ子で置いた**検証表が丸ごと不可視**になっていた（R17）。記入例よけは fence（走査前に除外済み）が本来の手段。代償として入れ子の補助表が検証行と誤読され block される（同 1 件。節の外か fence へ移せば解除できる）— 表 1 つ分の fail-open と引き換えに受け入れる
- **同じ材料を見る述語は同じ照合方式を使う**。AC 行判定（`_AC_METHOD_CELL`）だけが `^` 固定で、識別子照合（`_VERIFICATION_ID`）は語境界だったため、`| [AC-1] | n/a |` が「検証行ではあるが AC 行ではない」と判断され、未検証 AC が `N/A` 1 語で verified に化けた（R17）。照合方式のずれは、それ自体が fail-open の型である
- **注記付き status の受理は「status 列を確定できない行」に限る**。確定した status 列が完了値なら、他セルの `pending（前回）を解消` は経緯の記述。列位置を問わず括弧注記を拾うと全 pass の節が誤って block される（R17）
- **header の先頭セルは列名であって行番号ではない**。先頭セルが ID（`V-01` / 連番）の行を header と認めると、表ブロックの先頭に置くだけで「判別不能」報告を回避できる（R17）
- **ID 列形は正準形（`ID | method | status | …`）と短縮形（`ID | status | …`）を読み分ける**。1 列目が許容 status 値なら短縮形。読み分けないと `| AC-1 | pass | log |` が解除不能な block になる（R17）
- **2 つ目以降の `## Verification` 節も走査する**（従来は最初の 1 節で打ち切っていた）
- **header と認めるのは表ブロックの先頭行か、GFM どおり直後に separator 行（`|---|---|`）が続く行だけ**。先頭 1 行しか読まないと、空行なしで列順の違う表を続けたとき前の表の status 列束縛が持ち越され、後続表の notes 欄を status として読む（独立レビュー R15）。逆にどの行でも header 語との一致で貼り替えると、`| 検証 | 2026-09-01 | 状態 |` のような data 行が header に化けて行ごと消え、以降の canonical 行の status 列までずらす（R16）。表ブロックの切れ目は空行と見出し行（`### `）の両方で、見出しだけ見落とすと同じ持ち越しが起きる（R16）
- `| method` / `| ROW` の prefix 判定は削除する。**列の役割を先に確定し、行の判定は method 列と status 列だけで行う**: 表ブロックの先頭行を header として読み、method 列（`method` / `検証方法` 等）と status 列（`status` / `ステータス` / `状態` / `判定` 等）を解決する。どちらも特定できない行は header ではない（語彙外の見出しで表全体が guard から外れるのを避ける）。header の無い表は canonical の 0 列目を method、2・3 列目を status 候補とし、0 列目が ROW-ID のときだけ method を 1 つ右へずらす。語のリストはコードの `VERIFICATION_METHOD_HEADER_CELLS` / `VERIFICATION_STATUS_HEADER_CELLS` を正本とし、本 ADR に複製しない
- **補助行の除外は行単位で行う**。表ブロック単位で「補助表」と決めつけると、語彙外の見出しが 1 つ混ざるだけで後続の表や list まで guard から外れる（実測）
- **語数・セル数などの代理指標は使わない**。識別子は語境界で照合する。閾値は 1 つ足すたびに別の迂回路（閾値超え）と誤検出（閾値内の散文）を同時に生んだ
- **status セルを判別できない表行は「不可視」ではなく「未検証」として block する**（PR 旧#56 独立レビュー R1 の H3 / H4。読み飛ばすと非 schema 表が丸ごと消え、同一節に `pass` 行が 1 行あるだけで done が通る）
- 実質の検証行が 0 になる形（header のみ / 列を削った header / separator のみ / 空セル / `| なし |`）は「検証行がありません」で **fail-closed** に block する。header 語を持たないセル数不足行は data 行として計上され、「status 判別不能」で block される（別の block 理由になる）
- **list 行にも表行と同じセル正規化を適用する**（PR 旧#56 独立レビュー R1 の H2。padding / 装飾 / 無 padding 差が list 側だけ素通りする非対称を解消）
- **list 行にも表行と同じ列確定を適用する**（同 R4 の H1。表で block された内容を list へ書き換えて迂回する経路を塞ぐ）。list には header が無いので canonical と同じ確定規則を使う。散文 list は検証行として扱わないが、**data 行としては計上する**（節が list の散文だけで書かれている実データが多く、計上しないと「検証行がありません」で 92 件が誤って block される / 実測）。この緩和が安全なのは不変条件 (1) が別経路だから

実装は `hooks/scripts/lib/done_guard.py` の `_is_verification_data_row()` から header prefix skip を削除し、`VERIFICATION_STATUS_VALUES` と `_verification_table_row_statuses()` を新設して `_scan_verification()` を表 / list で分岐させる。block メッセージ本文と回復ヒントは orchestrator 側の `gdd_stop_hook.py` に残る。

## 却下した代替案

- **header prefix を先頭 2 セル一致に絞り込む（当初案）**: 却下する。header を賢くしても data 行との衝突は消えず、実測で phantom data row を 3 形（`| method |` だけの行、列を削った header、整列指定付き separator）生み、AC-5 の fail-closed を破った。加えて `|  pending  |` のような padding 差で block→done 方向の退行が出た。
- **status セル分類（判別不能→未検証を含む）を list 行にも全面適用して表 / list を完全対称にする**: 却下する。設計時点（measured_at: 2026-09-06 / population 449）の両方向シミュレーションで、list 行へ全面適用すると **112〜113 件**が新たに block されると実測した。**この値は設計判断の根拠として残す履歴で、現行の `scripts/measure-done-guard-drift.py` は採用規則の drift しか出力しないため再導出できない**（再検討する場合は候補規則を切り替えて測り直すこと）。過剰 block は guard の信頼性そのものを落とすため、完全対称より実害の小ささを取り、**判別不能の未検証扱いを広げる範囲を `|` 区切り 3 セル以上の list 行までに絞った**（再計測の実測値は `CHANGELOG.md` の当該 entry § Changed を正本とする。導出は `scripts/measure-done-guard-drift.py`）。
- **装飾除去なしの status セル分類**: 却下する。`` `pending` `` / `**pending**` のように装飾された status を見落とし、レビューで blocking finding になった。セル値から装飾文字と全角空白・タブを除去してから比較する。
- **注記・絵文字付き status（`pending(再実行待ち)` / `pending ⏳`）や非 status 語（`未実施`）を許容 status 値の前方一致で拾う**: 却下する。前方一致は `passed` を `pass` と読むなど別方向の誤検出を生む。代わりに**判別不能なセルを未検証として block する**方式を採り、利用者は理由を notes 列へ移して回復する。当初は accept as known risk として不可視のまま pin していたが、PR 旧#56 の独立レビューで block→done の退行（`pending​` / `~~pending~~` が main では block されていた）が実測されたため反転した。

## 受容した挙動変化

判定規則を反転させたので、既存セッションに対して **両方向**の挙動変化が出る。件数は進行中セッションが書き換え続けるローカル実データを母集団にした計測なので、**不変の事実としてではなく `measured_at` 付きスナップショットとして**扱う。正本は `CHANGELOG.md` の当該 entry `#### Changed`（measured_at 付き）。

規則クラスとしては以下が変わる。

- 表の `pending` / `fail` を検出するようになった（done→block 方向）
- status 列を持たない非 schema 表の行は「status 判別不能」として未検証に計上され block されるようになった（done→block 方向。list の `pass` 行が同居していても素通りしない）
- OLD で header prefix に巻き込まれ不可視だった表 data 行が `pass` / `N/A` / `unsupported` として計上され、節が通るようになった（block→done 方向）
- 整列指定付き separator / padding 差 / 装飾差 / 不可視文字による既存の fail-open も同時に塞がった（padding・装飾・不可視文字は表行と list 行の両方）

回復手順は「Verification 行を canonical schema に直す」こと。**list 形式への書き換えは回避策にならない**（`|` 区切り 3 セル以上の list 行にも同じ status セル要求がかかる）。この回復導線が guard 自身のヒントから読み取れるよう、「検証行がありません」の本文とヒントに、status セルを持つ行が 1 行も無い表もこの block に該当することと、行を足すのではなく canonical schema へ書き直すべきことを追記した。

## 後続で参照すべき制約

- **「検証行がありません」の射程**: この fail-closed は **すべての `## Verification` 節の data 行の合算**で判定するため、list 行が 1 行でもあれば発火しない（節ごとの 0 行は検出しない）。非 schema **表**の行、および `|` 区切り 3 セル以上の list 行は「status 判別不能」で止まるため、表を list へ書き換えて迂回することはできない。対象外は **散文 list（区切りセル 3 個未満、または先頭セルが検証行の識別子（`method=` / `ac:` / `AC-1` / `V-01` / `security_evidence`）でなく行内に許容 status 値も無い行）は対象外** で、これは全 list 行へ広げたときの過剰 block（§ 却下した代替案 の実測）を避けるための意図的な除外である。
- **`pending` / `fail` の検出は列位置を問わない（fail-closed 方向の誤検出）**: notes 欄などが単独で `pending` / `fail` の場合、status セルが `pass` でも block される。done を止める方向なので安全側。一方**「行が検証済みか」の判定は列位置で行う**（header があればその列、無ければ canonical の 2 列目のみ）。列位置非依存にすると evidence / notes の `N/A` を根拠に未検証行が verified 扱いになる（独立レビュー R2 で実測・是正済み）。
- **本変更で塞いでいない Check 2 の同型 fail-open**（非スコープ・変更前後とも挙動不変）: インデント行の一括除外 / 全角パイプ（`｜`）の表 / 区切り記号の無い list 行（`- method=ac:AC-1 pending`）/ 区切りセル 3 個未満の散文 list。将来まとめて扱う場合は 4 件を 1 つの規則として設計し直すこと（`許容 status` 語の行単位 skip は R4 / R5 / R7 で（コロンを伴う注記行だけを落とす形へ縮小）、marker 差と複数 `## Verification` 節は R5 / R6 で本 PR に取り込んで解消した）。
- 判別不能 status セルの block 挙動は `TableVerificationRowClassificationTests` の `decorated_pending_emoji_with_pass_row_blocks` / `non_status_word_with_pass_row_blocks` / `table_pending_zero_width_with_pass_row` / `table_pending_strikethrough_with_pass_row` で pin してある。
- **過剰 block の実測コスト**: 件数・母集団・measured_at は `CHANGELOG.md` の当該 entry § Changed を正本とする（導出は `scripts/measure-done-guard-drift.py`）。ここに数値を複製しない。回復は canonical schema への書き直しで、guard の回復ヒントが手順を提示する。
