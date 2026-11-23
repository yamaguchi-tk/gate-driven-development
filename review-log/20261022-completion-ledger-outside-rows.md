---
lane: L1+
pr: 564
follow_up_of: 563
amends: 20261021-completion-mechanical-ac-coverage.md, 20261021-completion-ledger-ac-glyph.md, 20261022-completion-ledger-doc-drift.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | d8d14059 | 0 | 0 | 0 | 2026-10-22 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 20dcebb1 | 2 | 0 | 2 | 2026-10-22 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 20dcebb1 | 0 | 0 | 0 | 2026-10-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | dba48f09 | 1 | 1 | 1 | 2026-10-22 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | dba48f09 | 0 | 0 | 0 | 2026-10-22 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 635a909e | 0 | 1 | 0 | 2026-10-22 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | 113785ea | 0 | 0 | 0 | 2026-10-22 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 8819907c | 1 | 1 | 1 | 2026-10-22 |
| 方針メモ-4 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | 8819907c | 0 | 0 | 0 | 2026-10-22 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 70176f5b | 0 | 0 | 0 | 2026-10-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | low | no | self-inflicted | fail-open | accepted | 設計: 変える（Ledger の行を節の位置だけで決める）。Opus・Fable とも、節の外で AC を含む表の行を許可リスト（Ledger でない見出しの表の、欄の数が合う行だけ見ない）で閉じ、両方のファイルを読む案を推した（A+B だけでは Notes の表の続きに足した行が残る）。336 ファイルで測り、該当は 1 ファイル（もともと ac-source）、誤って gate に回る行は 0。割れた点（文書の置き場所）は両方を採った（節の中に足す・退避は worklog の節に置く）。ユーザーへの確認は PR 本文の問いで行い、推奨で進める |
| H-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（Ledger を ac-ledger.md に移し、ファイル全体を許可リストで読む。方針メモ-3）。元の判断は 設計: 変えない。方針メモ-1 で (b)。Ledger と同じ欄の数の Ledger でない表（Notes の表など）の続きに足した failed の行は、欄の数が合うので見ず、前の verified で ok。入力者: steering の最終形 336 ファイルで 0 件、transcript は未測 commit: ff40c8f2 |
| H-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（Ledger を ac-ledger.md に移し、ファイル全体を許可リストで読む。方針メモ-3）。元の判断は 設計: 変えない。方針メモ-1 で (b)。節の後ろに足した次の形を見ず ok: 次の行が区切りの failed の行、AC を含む AC ID 見出しの表、引用の中の表、全角・小文字の AC。入力者: steering の最終形で 0 件、transcript は未測 commit: ff40c8f2 |
| L-1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 文書と断片の「節の外で見ない AC の行は…だけ」が、区切りが続く行と 縦棒で始まらない行を見ない実装より広い |
| L-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ac-trace-ledger.md の「節の中にこれ以外の行があると」の「これ」が、差し込んだ節の外の文を指すとも読める |
| L-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「見出しに AC Trace Ledger を含めない」が、節として読まれる「AC Trace Ledger で始まる見出し」と合わない |
| L-4 | 独立-1 | low | no | self-inflicted | product | accepted | size 上限の通知（SIZE_DENY_SUFFIX・state-field-tiers.md）が Ledger の行の退避先を言わず、退避すると以後 ac-source になる |
| L-5 | 独立-1 | low | no | self-inflicted | product | accepted | worklog.md の Ledger の節も AC ごとに最後の行で判定され、古い行だけを移すと unverified で終わる AC が出ることが文書に無い |
| L-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 限界の「Ledger でない AC の表は 4 欄」が、AC を含まない表の欄の数を示していない |
| L-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | 節の外の行を worklog.md 側に置くテストが無く、走査を tasklist.md だけに縮めても落ちない |
| A-1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 挙動の変化に、ac-ledger の invalid も ac-source になることが無い |
| A-2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | completion_trace.py 先頭の説明に、節の外の判定も印をつけた本文を読むことが無い |
| pm-2 | 方針メモ-1 | low | no | self-inflicted | fail-open | accepted | H-1・H-2 の閉じ方: Opus・Fable とも (b)（事故の形は steering の最終形で 0 件、transcript は未測。形の列挙を足すのは同じ形の修正の繰り返しになる）。実装は残す。位置で閉じる案（F: Ledger を最後の節にする）は ok 2 件のうち 1 件を gate に回すので採らない。Fable の F'（tasklist.md の最後の Ledger の節の後ろの縦棒で始まる行を形によらず ac-source）は、測ると ok の 2 件で 0 行（費用 0）。F' を推奨としてユーザーへの問いにし、返事を待つ間は (b) のまま進める |
| H-3 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 設計: 変える（Ledger を ac-ledger.md に移し、ファイル全体を許可リストで読む。方針メモ-3）。元の判断は 設計: 変えない。方針メモ-2 で (b)・安全策 4 の 1 回目の発火で止める。F' の外（worklog.md、節の無い tasklist.md、最初の節より前・節と節の間）では、Ledger でない見出しの 6 欄の表の続きに足した行と、AC を含む AC ID 見出しの表の行を読まず ok。入力者: 336 ファイルで 0 件、transcript は未測 commit: ff40c8f2 |
| M-1 | 独立-2 | medium | no | self-inflicted | test-power | accepted | 形の判定で gate に返す既存の 5 本が tasklist.md の節の後ろに入力を置くので F' の経路で返り、形の判定の分岐（Ledger の見出しの表・欄の数の食い違い）を壊しても落ちない |
| L-8 | 独立-2 | low | no | self-inflicted | product | accepted | tasklist.md の Ledger の節の位置が文書に無く、後ろに表の節（Verification History など）があると毎回 ac-source になる |
| L-9 | 独立-2 | low | no | self-inflicted | test-power | accepted | テスト名の「AC を含む AC ID の見出し」の形を入力に持っていない（AC ID の欄が無い） |
| L-10 | 独立-2 | low | no | self-inflicted | test-power | accepted | texts の先頭を tasklist.md に固定した変更を確かめるテストが無い（tasklist.md が空のとき worklog.md が先頭になる戻しで落ちない） |
| L-11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片の User Action Required が「なし」だが、Ledger Notes の表を散文に直す手順が要る |
| A-3 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | F' が当たる件数（節の後ろに表の行がある tasklist.md の数）が PR 本文に無い |
| A-4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | ac-trace-ledger.md の括弧書きが tasklist.md の後ろの範囲を除いておらず、形によらずに閉じた fence の中が入らないことも書いていない |
| pm-3 | 方針メモ-2 | low | no | self-inflicted | fail-open | accepted | 安全策 4 の 1 回目の発火（fail-open の high を含む巡が独立-1・独立-2 の 2 回）。Opus・Fable とも「止める」を推し、推奨で止めた。Opus は限界に引用の中の表（どこでも見ない）・全角と小文字の AC・区切りが続く行（F' の外）を足すことを推し、採った。worklog.md へ F' を広げる案はユーザーへの問いにする（Ledger の節がある worklog.md は 102 件中 1 件で節の後ろに 23 行、その steering はもともと ac-source で、ok が gate に回る件数は 0）。独立-2 の読み込みの PR 本文は 21 行（最終行に改行が無く wc -l は 20）で中身は一致 |
| pm-4 | 方針メモ-2 | low | no | self-inflicted | fail-open | accepted | ユーザーの返事: 「worklog.md にも F’ を広げる」（続行）。推奨（止めたまま）と違う案。worklog.md の最後の Ledger の節より後ろの縦棒で始まる行も形によらず ac-source にする。以後の巡では安全策 4 をまた数える |
| M-2 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | worklog.md は追記型で、Ledger の節の後に Error Log などの表の節ができると以後毎回 ac-source になる（止まる側）ことが限界に無い。PR 本文の限界に書いた |
| L-12 | 独立-3 | low | no | self-inflicted | test-power | accepted | tasklist.md 側の「AC を含む AC ID の見出し」のテストが名前どおりの入力を持たない（L-9 と同じ） |
| A-5 | 独立-3 | advisory | no | self-inflicted | style | accepted | worklog.md の節の後ろのテスト 3 本が、最後の節より後ろの区切りのコメントの下に入っていない |
| A-6 | 独立-3 | advisory | no | self-inflicted | product | accepted | 節の後ろの縦棒の行が 1 行ずつ ac-source の行になり件数の上限が無い（止まる側） |
| A-7 | 独立-3 | advisory | no | self-inflicted | style | accepted | PR 本文の抜粋の「と」の後に余計な空白 |
| pm-5 | 方針メモ-3 | low | no | self-inflicted | fail-open | accepted | ユーザーの問い「設計に戻って直す選択肢は？」に、Opus・Fable とも案 A（Ledger を専用ファイル ac-ledger.md に移し、ファイル全体を許可リストで読む。tasklist.md・worklog.md に残った Ledger の見出しは ac-source）を推した。割れたのは 旧#564 の扱い（Opus は 旧#564 の中で作り直す、Fable はマージしてから別 PR）。ユーザーは「案 A を 旧#564 の中で作り直して」。8 点は notes.md の方針メモ-3 |
| H-4 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（旧来の見出しの検出の受理集合を、変更前の読み手の式 `^#{2,3}\s+AC Trace Ledger` をそのまま含む上位集合として定義する。方針メモ-4）。旧来の見出しの検出が、`##` の後ろが全角スペース・NBSP の見出しと、`##` だけの行の次の行が AC Trace Ledger で始まる形を拾わず、ac-ledger.md が verified なら ok になっていた。commit: 321dc803 |
| M-3 | 独立-4 | medium | no | self-inflicted | doc-claim | accepted | done guard の block 文（done_block_message.py:98）・gdd-ac-verification/SKILL.md:97・self-contained-contract.md:277 が `## AC Trace Ledger` を tasklist.md の正規の節として案内し続け、従うと以後 ac-source になる（止まる側） |
| L-13 | 独立-4 | low | no | self-inflicted | product | accepted | _QUOTE の `[ ]?` と次の `[ ]{0,3}` が空白を取り合い、引用の印が多数並ぶ行で照合が指数時間になりうる（止まる側。推論） |
| L-14 | 独立-4 | low | no | self-inflicted | product | accepted | Ledger の行を見出し無しで tasklist.md・worklog.md や別の名前のファイルに書くと読まない（PR 本文の限界に開示済み） |
| L-15 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | test_check_completion_mechanical.py の Ledger のテストの名前・コメントが、撤去した「節」の読みを前提にしたまま |
| L-16 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | docs/learned-patterns.md:7 の「AC ごとに最新 1 行だけ残し、過去の行は worklog.md へ移す」が append-only の ac-ledger.md と合わない |
| A-8 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文・断片の「setext 形式によりません」が 1 行の setext だけを拾う実装より広く、旧来の見出しが ac-ledger.md の missing・error より先に判定される順序が無い |
| A-9 | 独立-4 | advisory | no | self-inflicted | product | accepted | 依頼の原文の「修正の手順を書く skill には触らない」に対し、実装の skill 2 つに 1 行ずつ触っている（案 A に要る変更） |
| A-10 | 独立-4 | advisory | no | self-inflicted | style | accepted | テストのコメントにレビューの巡の ID が入っている（test_check_completion_mechanical.py:796） |
| A-11 | 独立-4 | advisory | no | self-inflicted | product | accepted | telemetry の guardrail_detection_entries は語の出現を数えるので、題の無い ac-ledger.md は件数に入らない |
| A-12 | 独立-4 | advisory | no | self-inflicted | product | accepted | 旧来の見出しの検出が、Ledger でない見出し（AC Trace Ledger Gate の結果など）や、リストの次の --- も拾う（止まる側） |
| pm-6 | 方針メモ-4 | low | no | self-inflicted | fail-open | accepted | 安全策 4 の 2 回目の発火（fail-open の high を含む巡が独立-1・独立-2・独立-4）。規則どおり止める扱いで H-4 を accepted にし、PR 本文の限界の先頭に書いた。Opus・Fable とも部品は要り、ユーザーへの推奨は続行（変更前の読み手の式 `^#{2,3}\s+AC Trace Ledger` を名前つきでそのまま含める 1 行。受理集合が変更前を含み、凍結した有限集合で閉じる）。撤去と、見出しによらず語を含む行をすべて拾う案は推さない。実データ 341 ファイルで該当 0 件、transcript は未測 |
| pm-7 | 方針メモ-4 | low | no | self-inflicted | fail-open | accepted | ユーザーの返事: 「PR 本文を投稿して、続行して（変更前の式を含める 1 行と再現テスト、差分レビュー 1 回）」。推奨（続行）と同じ。以後の巡では安全策 4 をまた数える |
| L-17 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文が、変更前の読み手の式で拾う形（`##`・`###` の後ろの全角スペース・NBSP・改行）と、空の `##` の行の後の段落も拾うこと（止まる側）を書いていない。commit: なし（PR 本文） |
| A-13 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | ac-trace-ledger.md:48・gdd-completion-check/SKILL.md:54 の「見出し」が、変更前の読み手の形（空の `##` の行の後の段落）を含むことを書いていない（止まる側） |
| A-14 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の Validation の行が `###` の形を書かず、Summary が変更前の読み手の形を含むことを書いていない |
| A-15 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の実データの件数を tip の式で測ったかが読めない（tip で測り直して 4 件。本文に書いた）。commit: なし（PR 本文） |
| L-18 | 独立-5 | low | no | inherited | product | re-reported | done guard の block 文などが `## AC Trace Ledger` を tasklist.md の正規の節として案内したまま（M-3 の再報告） |
| A-16 | 独立-5 | advisory | no | inherited | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の目的の節に、レビューで穴が繰り返し見つかったという経緯の文がある。PR 本文の更新で除いた |
