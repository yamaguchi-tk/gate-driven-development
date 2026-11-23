---
lane: L1+
pr: 235
follow_up_of: 233
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) | 6f7416a00f715aef72cf98233a48d6eeb398baa6 | 0 | 0 | 0 | 2026-09-29T18:00+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) | 1605cd7ff61ef63c2216b0c6ab2ff35ea7d72e93 | 2 | 0 | 2 | 2026-09-29T19:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 913e99ad7f5c06a2527003fed236753b52c5b312 | 2 | 0 | 2 | 2026-09-29T21:00+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 88d45e802030f5381c7d8b11699ed7c0049414f9 | 2 | 0 | 2 | 2026-09-29T22:10+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) | 88d45e802030f5381c7d8b11699ed7c0049414f9 | 1 | 0 | 1 | 2026-09-29T22:40+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | b2bfbc9a9964c657911205db56138f140c58096c | 1 | 1 | 1 | 2026-09-30T00:10+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus) | b2bfbc9a9964c657911205db56138f140c58096c | 0 | 0 | 0 | 2026-09-30T00:40+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | ab6bdd8582292b85bbffaee210d6c548c69b7fe1 | 0 | 0 | 0 | 2026-09-30T01:30+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 5f9ccd714d5f1717a8a46b7435ecba44c69d6df6 | 2 | 0 | 2 | 2026-09-30T03:10+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus) | 5f9ccd714d5f1717a8a46b7435ecba44c69d6df6 | 0 | 0 | 0 | 2026-09-30T03:25+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（旧#233 の T1・T2・T3・T4 を直す。Opus の推奨は、T1 は block 文からパスを外す狭い側〔merge gate の block 理由に入る値はほかに定数か検証済みの値だけ〕、T3 は Resume From の cancelled・done を peer turn の guard に足す広い側〔done の正規の書き手は 0 件〕。.steering/ の外の binding 先・Bash の書き込み・ApplyPatch の move と削除・edits が dict・stale な brainstorming・読めない transcript を peer turn でないとみなすことは限界に書く。ユーザーの確認は memory の決定〔HITL は機能の見込みが無いときだけ〕により省いた） |
| N1 | 方針メモ-1 | high | yes | inherited | peer-turn-reader-asymmetry | fixed | 独立レビュー（全差分、1605cd7f）の指摘。その巡は PR 本文の読み込み行数が合わず（報告 21 / wc 20）無効にしたが、指摘は実コードで再現したので直す。guard の値の比較（state_field_value）は区切りの前の空白・\v を含む行も読み、gate の reader（gdd_extract_doc_field）は読まないので、囮の行を足してから本物の値を置換する 2 回の Edit で 4 つの記録すべてを素通りできた。Opus の推奨どおり reader で読んだ値でも比べ、Write・dict の edits も比べ、reader を起動できなければ止める（6eb0bf37、d9a9130f） |
| N2 | 方針メモ-1 | high | yes | inherited | bound-terminal-fail-open | fixed | 同じ巡の指摘。stale な brainstorming の binding 先は数え直しから外れるが guard は止めない。Opus の推奨（旧#233 の A と同じ考え方）どおり、数え直しでは stale な brainstorming の binding 先も候補に残す。実データで該当する binding は 0 件（6eb0bf37、fb1845cf、fec2e049） |
| N3 | 方針メモ-1 | low | no | self-inflicted | doc-claim | fixed | 同じ巡の指摘。記録の数（3 つ）が 4 つに追いつかず、コメントが guard の範囲を書いていない（cfa757bf） |
| N4 | 方針メモ-1 | low | no | self-inflicted | test-power | fixed | 同じ巡の指摘。NUL の transcript のテストが止まった理由を区別しない（c1866051） |
| N5 | 方針メモ-1 | low | no | self-inflicted | doc-claim | fixed | 同じ巡の指摘。行の正規表現が state.md 以外にも効くことが変更断片・PR 本文に無い（cfa757bf） |
| F1 | 独立-1 | high | yes | inherited | patch-line-split | fixed | peer turn の ApplyPatch で `-\v Resume From: cancelled` のように行区切り文字の後ろに記録を置くと、hook の splitlines() が行を割って追加行から落とし、gate の reader は 1 行として cancelled と読む。承認・マージ承認・Next Action: cancelled も同じ。.steering/ 宛ての patch に LF・CRLF 以外の行区切り文字があれば止める（2edfebc0、764409d8） |
| F8 | 独立-1 | high | yes | inherited | patch-line-split | fixed | 同じ形で Origin Session の write-once も ApplyPatch で外せた（偽の header で別ファイルの行に見せる形も）。F1 と同じ修正で閉じる（2edfebc0、764409d8） |
| F2 | 独立-1 | low | no | self-inflicted | reader-failure | fixed | reader の field ごとの失敗が無視されて空の値として比べられ、孤立サロゲートは一時ファイルのバイトが実ファイルと違いうる。どちらも None（止める）にする（2edfebc0、38709207） |
| F5 | 独立-1 | low | no | self-inflicted | block-message | fixed | stale な brainstorming で止めた文が、使わないステアリングの終え方を示さない。pre-push・merge・pre-PR の 3 つの文に固定の案内を足した（2edfebc0、64359b96） |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | collect_peer_turn_state_write_violations の docstring が Write・reader の比較・ApplyPatch は 1 層目だけであることを反映していない（b21bf340） |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | phase-progression.md の権限境界の列挙に完了（Resume From: done）が無い（b21bf340） |
| F3 | 独立-1 | advisory | no | self-inflicted | dual-impl | accepted | reader_heads が gdd_value_head を Python で書き直している（止める側に広く、今は害なし）。PR 本文に列挙する |
| F4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋の「reader を呼ぶとき」が実装と違う。抜粋を直した |
| G1 | 独立-2 | high | yes | inherited | patch-line-split | fixed | hook は既存の state.md を read_text() で読み、単独の CR を LF に変えてから python の規則と reader の一時ファイルで比べる。gate の reader は LF だけで割るので、CR の後ろに置いた囮の行で、peer turn の値だけの Edit（Resume From: cancelled・done、承認、Next Action: cancelled）が通る。old_string に CR を含む Edit は射影で空振りして「変化なし」に見える。Opus の推奨どおり、tool_input の文字列すべての行区切り文字を止め、old_string が見つからない Edit を peer turn の記録で止める（f0720829、a602d3fe） |
| G2 | 独立-2 | high | yes | inherited | patch-line-split | fixed | 同じ射影を使う Origin Session の write-once も、old_string に CR を含む Edit で書き換えられる（ターンを問わない。ツールが CR を生のバイトで照合するとき）。old_string が見つからない Edit を Origin Session のある state.md で止める（f0720829、a602d3fe） |
| G3 | 独立-2 | low | no | self-inflicted | test-power | accepted | TestReaderFieldValuesFailClosed が unittest.main() の後にあり、直接実行では走らない（pytest では集まる。follow_up_of のある PR の 2 巡目の low なので直さず PR 本文に書く） |
| G4 | 独立-2 | low | no | self-inflicted | test-power | fixed | ApplyPatch の行区切り文字のテストが returncode だけを見て、guard の内部エラーと区別しない。G1・G2 のテストを足す際に理由文も見るようにした（f0720829） |
| G5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の「ターンを問わず止める」に .steering/ を触る patch だけという限定が無い。G1・G2 で書き直す節に含めて直した（a602d3fe） |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | NON_DEMOTABLE の patch_line_break のコメントの「上の 2 つ」「承認・中止」が指す先と数が合わない。category の名前を変える際に関数名と 4 つの記録で書き直した（a602d3fe） |
| O1 | 方針メモ-2 | high | yes | inherited | patch-line-split | fixed | 安全策 4 の発火（patch-line-split の high が独立-1・独立-2 の 2 巡）で Opus に相談した。Opus は、Edit の new_string に `- Origin Session:\v BBB` を足す形が非 peer turn で allow になり、gate の reader は BBB と読むことを再現した（python の規則が \v で行を割り、値が無い行に見える）。推奨: 行区切り文字の拒否を tool_input の文字列すべてに広げ、old_string が見つからない Edit を止める（既存ファイルの生バイトでの拒否は Bash・人手の既知の限界に含まれるので入れない）。model が読む Origin Session の見た目の似た行（字下げ・ゼロ幅・太字）は別クラスタの inherited な限界として PR 本文に書く。実データ 450 件で誤って止める件数は 0。ユーザーの確認は memory の決定（HITL は機能の見込みが無いときだけ）により省いた（f0720829、a602d3fe） |
| H1 | 独立-3 | high | yes | inherited | edit-projection-mismatch | fixed | Claude Code の Edit は new_string が空で old_string が改行で終わらず、ファイルに old_string＋改行があると改行ごと消す（このセッションの Edit で実測: `pending-q1\napproved` が `approved` になった）。guard の射影は改行を残すので、1 回目で `pending-q1\napproved` を置き、2 回目で `pending-q1` を空にする 2 回の Edit で、peer turn の approved・Resume From の cancelled と done・Next Action の cancelled、全ターンの Origin Session の書き換えが通る（0641ac44、eb14a7a2） |
| H2 | 独立-3 | medium | no | self-inflicted | block-message | fixed | peer turn で old_string が見つからない Edit が「承認・中止の記録には使えません」の文で止まり、old_string を合わせ直せば通ることが伝わらない。H1 の修正で射影できない Edit の deny が増えるので、peer turn と Origin Session に専用の文を足した（0641ac44、eb14a7a2） |
| H3 | 独立-3 | low | no | self-inflicted | test-power | fixed | edit_misses_old_string の MultiEdit の分岐（逐次適用）を通すテストが無い。H1 の RED に 2 手目で条件に当たる MultiEdit を入れた（0641ac44） |
| H4 | 独立-3 | low | no | self-inflicted | block-message | accepted | done guard が「見えない文字を削除して」と案内する Edit を、old_string も見る行区切り文字の検査が止める。出口（文字を含まない全文の Write）をどちらの文も案内しない。follow_up_of のある PR の 3 巡目の low なので直さず、出口（文字を含まない全文の Write）を変更断片の User Action と PR 本文の限界に書いた |
| H5 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | 変更断片 19 行目の「peer turn の記録」が、peer turn の state.md・tasklist.md への Edit すべてを止める実装より狭く読める。H1 で書き直す節に含めて直した（eb14a7a2） |
| H6 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | project_edited_text の docstring の「読めなければ chunk 判定に委ねる」が、peer turn の呼び出し元では先に止める実装と合わない。H1 で docstring を書き直す際に直した（eb14a7a2） |
| H7 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「450 件で 0 件」に数え方が無い。PR 本文の抜粋に数えた場所・日付・方法を書き足した |
| P1 | 方針メモ-3 | advisory | no | inherited | edit-projection-mismatch | accepted | 安全策 4 の再発火（high を含む巡が独立-1〜3 の 3 回）で Opus に相談した。Opus はこのセッションの Edit ツールで適用規則を実測し、完全一致があるのに素の置換と食い違うのは空の new_string の規則（replace_all でも同じ）だけで、引用符・desanitize は完全一致が無いときだけ効くので old_string の空振りで止まることを確かめた。推奨は edit_misses_old_string に条件を 1 つ足す広い側（2 通りの射影は同じ入力空間の狭い側）と、止める文の書き直し。誤って止めうる Edit は transcript 上で state.md 8,906 件中 2 件・tasklist.md 11,295 件中 0 件。ほかの harness の規則・Claude Code の版の変化は限界に書く。ユーザーの確認は memory の決定（HITL は機能の見込みが無いときだけ）により省いた |
| J1 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | edit_misses_old_string の名前と、呼び出し側・e2e テストの docstring が「見つからないとき」のまま（空の new_string で行がつながる条件が増えた）。follow_up_of のある PR の low なので直さず、次の PR で名前と docstring を揃える |
| J2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | edit_misses_old_string の docstring の「どれにも当たらなければ、素の置換とツールの結果は一致する」が、Claude Code の単発の Edit で測った範囲を超えて断定している（MultiEdit の正規化の基準は未測）。PR 本文の限界に書いた |
| J3 | 独立-4 | low | no | self-inflicted | test-power | accepted | 射影できない Edit のテストが state.md だけで、tasklist.md の経路（Next Action）と、直後に空行がある行の削除が通ることのテストが無い。次の PR で足す |
| J4 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | references/state-field-tiers.md:91 と phase-progression.md:31 の Origin Session の write-once の記述に、射影できない Edit も止めることが無い。次の PR で足す |
| J5 | 独立-4 | low | no | self-inflicted | style | accepted | validate-steering-write.py が 1,734 行で、この PR は差し引き +196 行足した（base は 1,538 行で目安の 1,500 行を超過済み）。射影の部品を lib へ移す分割は次の PR で行う。CI と validate-plugin.sh は行数を検査しない |
| J6 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 止める文の案内が、行末の一部だけを消す Edit（new_string を空にせず前後の文字を含めて置き換える形）を覆わない。出口の全文 Write は書いてある |
| J7 | 独立-4 | advisory | no | self-inflicted | product | accepted | edit_misses_old_string は食い違う型を列挙して止める作りで、今回で 2 型目。次の PR の候補: 守る field の値を素の置換と改行ごと消す置換の 2 つの射影で比べる、または PostToolUse で実ファイルの記録値を前後で比べる |
| K1 | 独立-5 | high | yes | inherited | pr-url-target-match | accepted | main を取り込んだ差分（ab6bdd85..5f9ccd71。ほぼ全部が main 側の 旧#232 の変更）の巡の指摘。merge gate の対象 PR の照合が、URL の形の merge では文字列全体の一致だけを見るので、正準形でない PR URL（`<url>`・`url` に縦棒と注記を付けた形・リンクの形・`/files`・先頭 0）を記録した steering を、終端の steering だけが残る checkout で照合できず、承認の証跡を見ずに通る。この PR の実際の差分（origin/main 基準）は run-merge-gate-hook.sh の block 文言 2 か所だけで、照合のコードは main と同一。旧#232 の review-log の I3-1・H1・J1（方針メモ-5 で修正を撤回し、後続 PR「対象の読み取り」で直すと決めたもの）と同じ欠陥。この PR のマージで悪化も新規発生もしない。直さず PR 本文の限界の先頭に書く |
| K2 | 独立-5 | high | yes | inherited | pr-url-target-match | accepted | K1 と同じ照合を使う found・multiple の経路（run-merge-gate-hook.sh:846-849・:887）でも、同じ形の URL の merge が承認の証跡なしに通る。main と同一（旧#232 の I3-1・H1・J1 と同じ）。直さず PR 本文の限界の先頭に書く |
| K3 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | この PR の変更断片と main 側の断片（20260929-compact-docs-followups.md）が、peer turn の Resume From: cancelled の deny を二重に説明する。follow_up_of のある PR の low なので直さず、リリースの dry-run でまとめる |
| K4 | 独立-5 | low | no | inherited | doc-claim | out-of-diff | main 側（旧#232）の phase-gate-prechecks.md・README.md の Last Handoff Summary・PreCompact の記述が実装の例外と食い違う。この PR は変えていない。旧#232 の後続 PR で扱う |
| K5 | 独立-5 | low | no | inherited | doc-claim | out-of-diff | main 側（旧#232）の detect-steering.sh のヘッダーコメントが、数え直さない呼び出し元でも Next Action: cancelled で終端になることを載せていない。この PR は変えていない。旧#232 の後続 PR で扱う |
| K6 | 独立-5 | low | no | inherited | test-power | out-of-diff | main 側（旧#232）のテストが、正準形でない PR URL の 5 形のうち 1 形しか使わず、repo の比較を判別できない。この PR は変えていない。旧#232 の後続 PR で扱う |
| K7 | 独立-5 | advisory | no | inherited | doc-claim | accepted | main 側（旧#232）の新しい経路は .steering/ の直下しか列挙せず、.steering/ の外の binding 先が cancelled で外れると対象 PR を記録していても照合されない（main と同じ挙動）。PR 本文に列挙する |
| P6 | 方針メモ-4 | advisory | no | inherited | pr-url-target-match | accepted | 安全策 4 の再発火（high を含む巡が 独立-1・2・3・5 の 4 回）。Opus は、K1・K2 はこの PR の欠陥ではなく、マージしても悪化しない（この PR の detect-steering.sh の変更は、素通りする集合を狭める向きだけ）と確かめ、この PR では直さず accepted にして限界の先頭に書く案（b）を推奨した。旧#232 が同じ領域の修正を試みて fail-open を 7 形生んで撤回した開いた入力で、直しかけは危険。旧#235 から新しい次の PR を作らず、旧#232 の後続 PR で直す。マージの可否は、規則（3 巡の後に high が残ったら merge-ready とは書かずユーザーへ渡す）に従い、ユーザーが判断する。ユーザーの確認は memory の決定（HITL は機能の見込みが無いときだけ）により省いた |
