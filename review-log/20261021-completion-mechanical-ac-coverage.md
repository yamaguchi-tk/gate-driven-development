---
lane: L1+
pr: 556
follow_up_of: 551
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | b3de0aca | 0 | 3 | 0 | 2026-10-21 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 153fff22 | 7 | 1 | 6 | 2026-10-21 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 153fff22 | 0 | 1 | 0 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2d76a240 | 5 | 2 | 5 | 2026-10-21 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 2d76a240 | 0 | 1 | 0 | 2026-10-21 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 557b711d | 2 | 5 | 2 | 2026-10-21 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) + user | 557b711d | 0 | 1 | 0 | 2026-10-21 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 1544c0cb | 2 | 0 | 2 | 2026-10-21 |
| 方針メモ-4 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 1544c0cb | 0 | 1 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | medium | no | self-inflicted | deadlock | accepted | Ledger は completion-check 自身が Part B で書く（実データ 3 件）。Step 0 と main の実行で missing を止めると行き止まりになる。Ledger は `--ledger` で Part B の後に gate が回す（Opus。Fable は報告だけの行にする案。広い側の Opus 案を採り、PR 本文で確かめる） |
| pm-2 | 方針メモ | medium | no | self-inflicted | routing-order | accepted | 4d が invalid のとき main は止めずに dispatch する（追跡先は gate が補う。state-machine.md の Tracking Destination の行）（Opus。Fable は止める案。repo の規定に合う Opus 案を採る） |
| pm-3 | 方針メモ | medium | no | self-inflicted | same-rule-drift | accepted | 4c は `AC:`（正本）と `Covers AC:`（legacy）の両方を読み、main は `gdd-task-breakdown` を書かずに blocked で止める（Opus・Fable が一致）。Task Size では分けない |
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | 列挙: (b)。実データ 0/0（Ledger のある steering 4 件）。Ledger の欄の数が見出しと違う行・AC ID の欄が素の ID でない行を黙って捨て、前の verified の行が勝つ（completion_trace.py:127-130） |
| F2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: (a)。AC が両方のファイルにあれば両方の最後の行を通す（Opus 案。実データ 1 件・13 AC で誤 block 0）。tasklist.md と worklog.md の両方に同じ AC の Ledger 行があると worklog.md（退避した古い行）が勝つ（completion_trace.py:106-113）。commit: fcf0fbce |
| F3 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | 列挙: (b)。実データ 0（Lane の表 3 件）。Lane の「埋まっている」が空と `<...>` だけを弾く。テンプレートの Human Recheck の文言・`なし`・`-`・`+ 理由` のままが ok（completion_trace.py:94-99） |
| F4 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: (b)。取りこぼす形は実データ 0（Lane のある 4 件）。Lane の済み判定が、字下げした `- [ ]`・表の後ろの `- [ ]` を読み飛ばす（completion_trace.py:74-81）。方針メモ-2 で、Lane のどこかに `- [ ]` があれば invalid にして閉じた。commit: fade2e6c |
| F5 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: (a)。AC を閉じた形で読めないときは ok を出さず ac-source を invalid にし gate に返す（Opus 案。Fable は invalid で止める案。実データで止めると 43 件中 40 件が AC ID を持たない requirements の書式の強制になる）。requirements.md から AC を 1 件も読めないとき、ac-coverage と ac-ledger が ok を返す（check-completion-mechanical.py:116-134）。commit: fcf0fbce |
| F6 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: (a)。被覆を task の範囲（3 つの task の一覧の節と task 見出しの下）に限る。実データで ok → invalid の反転 0。被覆が task の節の外の `AC:` 行（Verification Notes・worklog の自由文）も数える（completion_trace.py:59-63）。commit: fcf0fbce |
| F7 | 独立-1 | high | no | self-inflicted | request-drift | fixed | 確認待ち: Ledger の節が無い（missing）では止めず completion output に書く（Opus 案。Fable は止めたまま Part B に書く手順を足す案）。PR 本文の確認したいことに (A)・(B) を書く。Ledger の節が無い steering（実データ 57/61）を新しく止める。今の gate が止めていなかった挙動の変更で、ユーザーの確認が無い。commit: fcf0fbce。方針メモ-2 で取り消し、missing を不備に戻して出口（Part B の結果から Ledger を追記して回し直す）を書いた（G3）。commit: fade2e6c |
| F8 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | Implementation Sequence Plan で PR Boundary が current-pr でない Stage の AC を除く（Opus・Fable が一致。実データ 2 件とも除けた）。後続 Stage に回した AC で main が dispatch の前に止まる（実データ 2/58）。Implementation Sequence Plan の Stage の AC から除けるのに限界にした。commit: fcf0fbce |
| F9 | 独立-1 | low | no | self-inflicted | product | accepted | tasklist.md が無いと ac-coverage だけ error になり、remaining-tasks の missing より先に外部前提不足で止まる |
| F10 | 独立-1 | low | no | self-inflicted | test-power | accepted | 行区切りのテストが、行区切りのガードを消しても別の理由で通る |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「Ledger は Part B が書く」に根拠が無い（Part B に追記の手順が無い）。commit: fcf0fbce |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docstring の「既存の実装を呼ぶ」が新しい述語と合わない |
| F13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の変更内容に、外から見える挙動（reviewer が指摘しなくなる、error の新しい経路など）が足りない |
| F14 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 実データの件数が 61 と合わず、コマンドと止まる分の件数が無い |
| F15 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の「task の AC: 行」「ok でなければ止める」が実装と合わない。commit: fcf0fbce |
| F16 | 独立-1 | low | no | self-inflicted | product | accepted | blocked・deferred-human を常に invalid にし、ac-trace-ledger.md の「未解消のとき」とずれる |
| F17 | 独立-1 | low | no | self-inflicted | product | accepted | lint-ac.py を import の時点で読み込み、_guarded の隔離の外に出た |
| F18 | 独立-1 | low | no | self-inflicted | product | accepted | Step 4d の invalid で gate が何をするか（欄が空・表でない）が決まっていない |
| F19 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 限界の `リスクが低い` に件数も「未測」も無い |
| F20 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | `--ledger` を回す時点が Steps に無い |
| F21 | 独立-1 | advisory | no | self-inflicted | product | accepted | AC の範囲表記を、書式の正本にも他の読み手にも無い形で受け取り、上限も無い |
| F22 | 独立-1 | advisory | no | self-inflicted | product | accepted | worklog.md を strict な UTF-8 で読み、壊れたバイトで error になる |
| F23 | 独立-1 | advisory | no | self-inflicted | product | accepted | 4d が 5 の前に入り、両方 invalid のとき main の早い停止が消える |
| pm-4 | 方針メモ-1 | medium | no | self-inflicted | fail-open | accepted | 独立-1 の列挙の high 6 件: 部品は残す（Opus・Fable 一致）。F1・F3・F4 は (b)、F2・F5・F6 は (a)。割れた F2 の閉じ方・F5・F7 は Opus 案を採る（F2 は実データで誤 block 0、F5・F7 は依頼に無い書式の強制・挙動の変更を避ける）。F1・F3・F4 が残るので merge-ready と書かずにユーザーへ渡す |
| G1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | PR Boundary が current-pr で始まらなければ、どんな値（this-pr・空・記入例）でも AC を除く（completion_trace.py:96）。commit: fade2e6c |
| G2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | current-pr の行と後続の行の両方にある AC を除く（completion_trace.py:95-98）。commit: fade2e6c |
| G3 | 独立-2 | high | yes | self-inflicted | request-drift | fixed | Ledger の節が無いと止めないことにした。依頼から外れ、ac-trace-ledger.md:52-54・:72 ほか 5 か所と食い違う（SKILL.md:54）。commit: fade2e6c |
| G4 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | Ledger の行が読めない（欄の数・AC ID の欄）と黙って飛ばし前の verified が残る。閉じ方: 構造（既定の反転）（completion_trace.py:197-200）。commit: fade2e6c |
| G5 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | Lane の欄の判定が空と `<...>` だけ。スクリプトの ok を「空でない」に限り中身は gate が読む（閉じ方: 構造）（completion_trace.py:162）。commit: fade2e6c |
| G6 | 独立-2 | medium | no | self-inflicted | product | accepted | AC が両方のファイルにあると、退避した RED の行で止まる |
| G7 | 独立-2 | medium | no | self-inflicted | same-rule-drift | fixed | --ledger の ac-source の扱いが SKILL.md:54 の同じ段落で食い違う。commit: fade2e6c |
| G8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | ok の詳細の件数が後続の AC を除いた後の数と合わない |
| G9 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の行の件数と経緯の文。commit: fade2e6c |
| G10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | --ledger でも後続の AC を除くことがどこにも書かれていない。commit: fade2e6c |
| G11 | 独立-2 | low | no | self-inflicted | test-power | accepted | 受入条件の節が無い場合のテストが無い |
| G12 | 独立-2 | low | no | self-inflicted | style | fixed | test_covers_in_fence_is_not_coverage の def 行が消え、本文が別のテストの中に入った。commit: 13342085 |
| G13 | 独立-2 | low | no | self-inflicted | same-rule-drift | accepted | task の一覧の節の見出しの受理が done guard と違う |
| G14 | 独立-2 | low | no | self-inflicted | product | accepted | task の範囲で LF 以外の行区切りでも行を分ける |
| G15 | 独立-2 | low | no | self-inflicted | product | accepted | deferred_acs が区切り行だけの表で IndexError、範囲の上限が無い |
| G16 | 独立-2 | low | no | self-inflicted | product | accepted | 要求する AC の集合を requirements.md 全体から取り、片向きの照合 |
| G17 | 独立-2 | low | no | self-inflicted | product | accepted | worklog.md の task の見出しの形が違うと、原因と違う報告で止まる |
| G18 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋の限界の 3 項目が受け入れた指摘の記録の形） |
| G19 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | テストの assert を assertLessEqual に緩めた変更が入っている |
| G20 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 抜粋とエラー文が `## Acceptance Criteria` を書いていない |
| pm-5 | 方針メモ-2 | medium | no | self-inflicted | fail-open | accepted | 安全策 4 の 1 回目の発火（fail-open の high を含む巡が独立-1・独立-2 の 2 回）。Opus・Fable とも続行を推奨。推奨（続行）で進め、G1〜G5 と F4 を既定の反転（読めない形は ok にしない）で閉じた。G4 は Opus 案（AC ごと。Fable は Ledger 全体）、G3 は 2 本が一致（missing を不備に戻す）。返事が「止める」なら 2d76a240 まで戻す。PR 本文に問いを書く |
| H1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | SKILL.md:227 の gate の手読みの文が「current-pr でない Stage の AC を除く」のまま。ac-source で返した空・記入例の PR Boundary の AC を gate が除いて通す。ユーザーの続行の返事で、gate の文を実装の語彙に合わせた。commit: 0ca800e2 |
| H2 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 列挙: 読めない Ledger の行の検出が列挙（completion_trace.py:215-234）。別綴りの AC ID・表でない追記の後で前の verified が残る。ユーザーの続行の返事で、Ledger の節で受け付ける行を許可リストで決め、それ以外は ac-source で gate に返した（実データの 4 件のうち、表でない形で書いた Ledger の 1 件が gate に回る）。commit: 0ca800e2 |
| H3 | 独立-3 | medium | no | self-inflicted | same-rule-drift | accepted | `- [ ]` があれば follow-up-stage を invalid にするが、gdd-requirements-gating/SKILL.md:124 は未完の Stage を `- [ ]` で並べる。直さず限界の節に書く（medium・low・advisory） |
| H4 | 独立-3 | medium | no | self-inflicted | product | fixed | 読めない Ledger の行の不備が、後の verified の行でも消えない（append-only に反する）。読めない行は、その AC の最後の行を「読めない」にし、後の読める行で上書きする。commit: 0ca800e2 |
| H5 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | Ledger の節が無いとき gate が Part B の結果から追記して通す（SKILL.md:54）。合格の条件にかかわる。ユーザーの返事は (A)。commit: 0ca800e2 |
| H6 | 独立-3 | medium | no | self-inflicted | same-rule-drift | fixed | gate-checklists.md:123,125・ac-trace-ledger.md:30,61 と SKILL.md:54 が食い違う。Checklist E と ac-trace-ledger.md に例外を書いた。commit: 0ca800e2 |
| H7 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片と抜粋の missing・invalid の出口が SKILL.md:54 の範囲と合わない。変更断片を SKILL.md:54 の範囲に合わせた。commit: 0ca800e2 |
| H8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | ac-source の理由の記述（docstring・(4a)・テストのコメント・断片）が古い。直さず限界の節に書く（medium・low・advisory） |
| H9 | 独立-3 | low | no | self-inflicted | product | accepted | 後続の判定だけが前方一致で、lint-hitl-stage-plan.py の完全一致と非対称。直さず限界の節に書く（medium・low・advisory） |
| H10 | 独立-3 | medium | no | self-inflicted | same-rule-drift | accepted | 済みの Lane の判定が next_plan_check と割れる（字下げの注記・`1. [ ]`・`- []`）。直さず限界の節に書く（medium・low・advisory） |
| H11 | 独立-3 | low | no | self-inflicted | test-power | accepted | 記入例の PR Boundary のテストが語彙の分岐を通らず、詳細も見ない。直さず限界の節に書く（medium・low・advisory） |
| H12 | 独立-3 | low | no | self-inflicted | product | accepted | 区切り行だけの表で IndexError になり error に倒れる。直さず限界の節に書く（medium・low・advisory） |
| H13 | 独立-3 | advisory | no | self-inflicted | style | accepted | テストの空行と `_one_line` の重複。直さず限界の節に書く（medium・low・advisory） |
| pm-6 | 方針メモ-3 | medium | no | self-inflicted | fail-open | accepted | 安全策 4 の 2 回目の発火（fail-open の high を含む巡が独立-1・2・3）。規則どおり止めて PR を作り、返事を待つ。Opus・Fable ともユーザーへの推奨は続行（H1 は文の 1 行、H2 は Ledger の節で受け付ける行の形を許可リストで閉じ、読めない形は gate に返す）。部品は縮めない。H5 の推奨は 2 本とも (A) Part B の結果から追記。ユーザーは続行と (A) を選んだ（request.md に時刻つきで記録） |
| J1 | 独立-4 | high | yes | self-inflicted | fail-open | accepted | 列挙: Ledger の節で区切り行の直前の行を中身を見ずに別の表の見出しとして読み飛ばす（completion_trace.py:244-246）。failed の行の直後に区切り行があると ok。base では invalid（退行）。安全策 4 で止めた。ユーザーの指示で次の PR で直す（Issue にしない） |
| J2 | 独立-4 | high | yes | self-inflicted | fail-open | accepted | 列挙: Ledger の節で `>`・`#` で始まる行を AC ID を含んでも読み飛ばす（completion_trace.py:230-231）。安全策 4 で止めた。ユーザーの指示で次の PR で直す（Issue にしない） |
| J3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | SKILL.md:54 と断片が受け付けない行の例に「表でない追記」を挙げるが、`>`・`#` は受け付ける。安全策 4 で止めた。直さず限界の節に書く |
| J4 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | ac-trace-ledger.md § Completion Gate Rule に追記の例外への言及が無い（止める側）。安全策 4 で止めた。直さず限界の節に書く |
| J5 | 独立-4 | low | no | self-inflicted | test-power | accepted | known_ids と別の表の AC-01 の分岐を変えても落ちるテストが無い。安全策 4 で止めた。直さず限界の節に書く |
| J6 | 独立-4 | low | no | self-inflicted | product | accepted | `### AC Trace Ledger` の節が同じ階層の見出しで終わらず、散文が gate に回る（止める側）。安全策 4 で止めた。直さず限界の節に書く |
| J7 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | SKILL.md:227 と断片が「で始まる値」と書いていない（コードは前方一致）。安全策 4 で止めた。直さず限界の節に書く |
| J8 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 断片と抜粋に Plan の欄の数の不一致が無い。断片の「2 つの行」が 4 つの要求と合わない。安全策 4 で止めた。直さず限界の節に書く |
| J9 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | check-completion-mechanical.py の docstring に、Ledger の受け付けない行で ac-source を出すことが無い。安全策 4 で止めた。直さず限界の節に書く |
| J10 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | request.md が、ユーザーが番号で指した「確認したいこと」の文を引用していない。request.md に引用を足した |
| J11 | 独立-4 | advisory | no | self-inflicted | product | accepted | 追記の例外の条件（Part B で pass した AC だけ）をスクリプトは確かめない。安全策 4 で止めた。直さず限界の節に書く |
| pm-7 | 方針メモ-4 | medium | no | self-inflicted | fail-open | accepted | 安全策 4 の 3 回目の発火（fail-open の high を含む巡が 4 巡続いた）。Opus・Fable とも止めるを推奨（前の確認でユーザーが「また high が出たら止める」を受け入れた）。部品は縮めない。続行なら、AC の字形を含む行は読み飛ばさない不変条件で 1 commit にする。PR 本文に問いを書いて返事を待つ。ユーザーは止めて新しい PR で直すを選んだ（request.md に記録） |
