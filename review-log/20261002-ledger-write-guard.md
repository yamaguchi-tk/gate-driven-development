---
lane: L1+
pr: 315
follow_up_of: 294
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（main の案は、state.md の gate が読む field と tasklist.md の Reviewed by・Next Action の行が減る書き込みを止め、旧#294 の限界の step 8b の切り出しと戻す規則の向きつき化も同じ PR に入れるものだった。実測: 直近 30 日の steering の state.md・tasklist.md への書き込み約 12,000 件のうち、1 回の呼び出しで gate が読む行が減ったのは 82 件で、大半（task 見出し 61）は移動・再オープンの正当な書き込みだった。Opus は、後ろの gate が fail-closed で拾わない tasklist の Reviewed by だけに絞り、state.md の field と行数の比較をやめること、step 8b の切り出しは block gate の本体を変えるので別 PR にすることを推した。main の案と食い違ったので信号 ① で Fable を呼んだ。Fable は、戻す規則の向きつき化はユーザーが承認済みなので同じ PR に残すこと、step 8b は別 PR に分けること、判定中の例外は止める側に倒すこと、validate-steering-write.py の行数の相殺は共有部品を動かさずコメントの短縮で行うこと、丸ごと消す形の取りこぼしを数で開示することを推した。main は Opus 案に Fable の点を足し、丸ごと消す・見出しが崩れる形も、別の節に無ければ止める側（広い側）に広げて採った。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた。step 8b の切り出しを別 PR に分けたことはユーザーへの報告に書く） | - | 0 | 0 | 0 | 2026-10-02T23:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d6a28c09066b66a96b1549c375143222f5daec36 | 4 | 1 | 4 | 2026-10-02T14:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | a8e4ac05 | 3 | 3 | 3 | 2026-10-02T15:09+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable。ユーザーの指示で 1 PR 1 回の枠を超えて呼んだ) + user（安全策 4 の発火: 独立-1・独立-2 の両方に completed_reviewed_by の fail-open の high。Opus は、guard は後ろの fail-closed の検査より早く気づかせる部品で、F1 は S-0 の形そのものなので直し、F4 は効かない例外を消して閉じ、F2・F3 は開いた入力なので限界に書いて止める (A) を推した。Fable も (A) を推し、F1 は共有の `_record_existing_denies` でなく collector でまとめること、route は task-breakdown の前に none へ戻るので例外は死んだ分岐であることを実コードで確かめた。ユーザーは (A) を選んだ。直した後の差分巡で high が出ても直さず限界に書く。SKILL.md の手順は変えず、deny 文言の案内に任せる） | - | 0 | 0 | 0 | 2026-10-02T15:40+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 92ada784f8765b5f1f477efb2f0b96ec01add466 | 2 | 0 | 2 | 2026-10-02T23:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| E1 | 独立-1 | high | yes | self-inflicted | completed_reviewed_by の fail-open | fixed | 再オープンの免除が Completed 以外の節すべてに効き、`## Archived Tasks` への移動や Completed の見出しの改名で Reviewed by を落とせる commit: a8e4ac05 |
| E2 | 独立-1 | high | yes | self-inflicted | completed_reviewed_by の fail-open | fixed | タスク名（番号を除く）の集合で比べるので、同名タスクが 2 件あると片方の Reviewed by を落としても通る commit: a8e4ac05 |
| E3 | 独立-1 | high | yes | self-inflicted | completed_reviewed_by の fail-open | fixed | Edit の投影が素の置換で、空の new_string が続く改行ごと消すツールの挙動と違い、Reviewed by の行を前の行に繋げる Edit を通す commit: a8e4ac05 |
| E4 | 独立-1 | high | yes | self-inflicted | completed_reviewed_by の fail-open | fixed | content chunk が空で違反の無い書き込みが連続 deny の回数を戻さないので、間に違反の無い書き込みを挟んだ 3 回目の deny が警告に降格する commit: a8e4ac05 |
| E5 | 独立-1 | medium | no | self-inflicted | 既存手順の誤 deny | fixed | gdd-task-breakdown の全セクションの作り直しと gdd-refactor-planning の abort が完了タスクを消す書き込みで止まる commit: a8e4ac05 |
| E6 | 独立-1 | low | no | self-inflicted | 文言 | fixed | WHY の「どの hook も読みません」がこの変更で事実でなくなった commit: a8e4ac05 |
| E7 | 独立-1 | low | no | self-inflicted | 文言 | fixed | tasklist_parse.py の docstring と check-gate-ledger.sh のコメントの「hook は見ない」が事実でなくなった commit: a8e4ac05 |
| E8 | 独立-1 | low | no | self-inflicted | 文言 | fixed | state-field-tiers.md が guard の範囲（Write・Edit・MultiEdit だけ、3 回連続で警告に降格）を書いていない commit: a8e4ac05 |
| E9 | 独立-1 | low | no | self-inflicted | 文言 | fixed | test_check_gate_ledger.py のコメントが古い戻す規則のまま commit: a8e4ac05 |
| E10 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 例外と見出しが見つからない場合の deny 文言が実際の原因を言わない commit: a8e4ac05 |
| E11 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 変更断片の Added が内部の関数を挙げている commit: a8e4ac05 |
| E12 | 独立-1 | advisory | no | self-inflicted | テスト | accepted | ApplyPatch を通すテストは限界の固定で、expectedFailure にする案がある |
| E13 | 独立-1 | advisory | no | self-inflicted | PR 本文 | accepted | PR 本文の誤 deny の見積もりに件数と分類の記録場所が無い |
| E14 | 独立-1 | advisory | no | inherited | 断片 | accepted | 他の未リリース断片に古い戻す規則が残る（リリースの dry-run で直す） |
| F1 | 独立-2 | high | yes | self-inflicted | completed_reviewed_by の fail-open | fixed | 完了タスクごとに reason を出すので、1 回の書き込みで 3 件以上落とすと連続 deny の回数が 3 に届き、初回で警告付きで通る commit: 92ada784 |
| F2 | 独立-2 | high | yes | self-inflicted | completed_reviewed_by の fail-open | accepted | replace_all で空の new_string の Edit の投影が Claude Code（old+改行が 1 か所でもあれば old+改行だけを全置換）と違い、重なる old_string で Reviewed by を落とす書き込みを通す |
| F3 | 独立-2 | high | yes | self-inflicted | completed_reviewed_by の fail-open | accepted | 書き込みの前の tasklist.md で fence が閉じていないと、その先の完了タスクを ok と数えず守らない |
| F4 | 独立-2 | medium | no | self-inflicted | 既存手順の誤 deny | fixed | 作り直しの route は task-breakdown の時点で none に戻っており、route の例外が効かない。route は agent が書く値でもある commit: 92ada784 |
| F5 | 独立-2 | medium | no | self-inflicted | 既存手順の誤 deny | fixed | 同じ書き込みで足した名前だけを再オープンと数えるので、Edit 2 回での再オープンが止まる commit: 4ed08a8e |
| F6 | 独立-2 | medium | no | self-inflicted | 既存手順の誤 deny | accepted | gdd-refactor-planning の abort の手順（Completed から直接消す）が guard とぶつかる |
| F7 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 回数が戻るのは、この category で違反が無い書き込み（別 category の deny・ApplyPatch を含む）で、断片の記述と少し違う |
| F8 | 独立-2 | low | no | self-inflicted | 文言 | accepted | テストの module docstring に「どの hook も読まない」が残る |
| F9 | 独立-2 | low | no | self-inflicted | 文言 | accepted | state-field-tiers.md の正本の注記が guard の文に付いて見える |
| F10 | 独立-2 | low | no | self-inflicted | 既存手順の誤 deny | accepted | UTF-8 で読めない tasklist.md は直す書き込みも止まる |
| K2 | 方針メモ-1 | - | - | - | - | - | なし |
| G1 | 独立-3 | high | yes | self-inflicted | completed_reviewed_by の fail-open | accepted | 書き込みの前から Current・Pending にあるタスクも再オープンと数えるので、同じ名前の別のタスクが Current・Pending にあると、完了タスクの Reviewed by を落とす・消す書き込みが通る（2 回の書き込みでの再オープンを通すための広げ方の代償） |
| G2 | 独立-3 | high | yes | inherited | completed_reviewed_by の fail-open | accepted | 同じ tasklist.md を file_path と path の 2 つの key で指す Write は、target が 2 件になり、1 回目の deny で降格の回数に届いて通る（全 category に共通の `_record_existing_denies` の数え方） |
| G3 | 独立-3 | low | no | self-inflicted | 文言 | accepted | 断片は deny 文言が gdd-task-breakdown の作り直しを案内すると書くが、文言の括弧は refactor の abort だけ |
| G4 | 独立-3 | low | no | self-inflicted | テスト | accepted | 3 件を一度に落とすテストは、3 回目の降格を HUMAN REVIEW REQUIRED で確かめていない |
| G5 | 独立-3 | low | no | self-inflicted | テスト | accepted | テストの `_state` ヘルパが使われなくなった |
| G6 | 独立-3 | low | no | inherited | 既存手順の誤 deny | accepted | gdd-task-breakdown の route ごとのリセットの範囲は、route が先に none へ戻るので届かず、作り直しのたびにこの guard の deny に当たる |
| G7 | 独立-3 | advisory | no | self-inflicted | テスト | accepted | テスト名は 2 回の Edit だが、1 回目は Write |
