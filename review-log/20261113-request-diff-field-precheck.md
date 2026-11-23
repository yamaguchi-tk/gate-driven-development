---
lane: L1+
pr: 672
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | 1520fd654f60784cc0ac6098e89ad7aed0fb48ea | 0 | 9 | 0 | 2026-11-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e1475cea751097807ecbbd60d0d0fc7d7d845dca | 0 | 3 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 78e17bc4dafdcd5897aff677d38ed396906bcae9 | 0 | 1 | 0 | 2026-11-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | f01bced307eb6cbd17fd91cfeec33a25acc6a76b | 0 | 1 | 0 | 2026-11-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | medium | no | self-inflicted | field-grammar | fixed | 値の判定を「なし で始まるか」の前方一致にせず、なし と あり: <項目> の 2 形の許可リストで閉じる（2 本とも推奨。ありません。・案 1 ならなし… が前方一致では残る）。欄の形の行は - 依頼との差: なし だけを示す。commit: 7bb58f88 |
| M2 | 方針メモ | medium | no | self-inflicted | stop-precheck | fixed | Stop が読む提示を、承認の検査と同じ「最後のマーカー付きの発言」にし、人の発言でターンを区切る（2 本とも推奨）。commit: 7bb58f88 |
| M3 | 方針メモ | medium | no | self-inflicted | field-grammar | fixed | 形の判定を format_problem に分け、Stop の block と提示の lint はこちらを使う。lint が あり: の点まで落として差を隠す方へ押さない（Opus-1）。commit: 7bb58f88 |
| M4 | 方針メモ | medium | no | self-inflicted | stop-precheck | fixed | block の文で、前置きを書かずに確認の全文だけを出し直させ、読めなかった行を載せる（2 本とも推奨）。commit: 7bb58f88 |
| M5 | 方針メモ | medium | no | self-inflicted | stop-precheck | fixed | block した記録は not_run に理由を入れて読み手の統計と分け、_already_seen に数えない（2 本とも推奨）。commit: 7bb58f88 |
| M6 | 方針メモ | medium | no | self-inflicted | stop-precheck | fixed | 連続の上限を時間やターンで区切る。Opus-2 は stop_hook_active=false で数え直す案だが、完了通知でも false になる（stop_block_ceiling.py の注記）ので、人の発言のターンで数え直す形にした。commit: 7bb58f88 |
| M7 | 方針メモ | medium | no | self-inflicted | measurement | fixed | AC-5 を Stop の選び方での再生に替え、分母を提示の数にし、誤 block の件数も測る（2 本とも推奨）。結果は notes の ## 再生 |
| M8 | 方針メモ | medium | no | self-inflicted | doc-claim | fixed | 「止めない」前提の文書とテスト（README・run-request-diff-hook.sh・human-check-template.md・test_request_diff_hook.py・test_hooks_wiring_new_events_contract.py）を直す（2 本とも推奨）。commit: 7bb58f88 |
| M9 | 方針メモ | medium | no | self-inflicted | approval-target | accepted | 承認の検査が読む提示を「最後の人の発言より前の、最後のマーカー付きの発言」に変える案（Opus-2 の範囲の拡大。同じターンで提示と書き込みをする形を閉じる）。依頼の 4 点の外で、提示の後に人が答えずに書き込むと古い提示で通る形を新しく作るので、この PR では入れない。Fable も入れない側。報告でユーザーに示す |
| M10 | 方針メモ | advisory | no | inherited | measurement | out-of-diff | request-diff.log の読み手が 11-13 05:42 以降ほぼ全件「読み手が失敗した」（Opus-1）。claude -p を同じ引数で起動すると 429（weekly limit）で、コードの不具合ではない |
| I1-1 | 独立-1 | medium | no | self-inflicted | stop-precheck | accepted | GDD を使っていないセッションでも、発言がマーカーの文字列を含むだけで Stop が block する（承認の書き込みが起きえない場面）。PR 本文に書く |
| I1-2 | 独立-1 | medium | no | self-inflicted | stop-precheck | accepted | block の文の最後の 1 文が、追記の型ではマーカーなしの発言を足せば解けると読める（実際は全文をマーカー付きで出し直すまで解けない） |
| I1-3 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | docs/SECURITY.md:130 の「request-diff の hook は止める hook ではない」が古い |
| I1-4 | 独立-1 | low | no | self-inflicted | test-power | accepted | _already_seen が block の記録を数えない変更を、テストが固定していない（2 回目も _field_check が先に返る） |
| I1-5 | 独立-1 | low | no | self-inflicted | test-power | accepted | block しない側のテストが、例外で落ちた場合も通る（読み手の呼び出しと記録を見ていない） |
| I1-6 | 独立-1 | low | no | self-inflicted | stop-precheck | accepted | 上限の後の知らせの経路でも読み手を起動しない。PR 本文に書く |
| I1-7 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の type が patch（新しい block で minor 相当）。User Action Required の「なし。」と後ろの文が食い違う |
| I1-8 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | PR 本文に読む時期と撤去の条件が無い。PR 本文に書く |
| I1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 上限の後の知らせの記録が、読み手の動かなかった行と同じ鍵の形で、_already_seen も見たと数える |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | request_diff.py の docstring の「承認の検査と同じ選び方」が、人の発言で区切る点を書いていない |
| I1-11 | 独立-1 | advisory | no | self-inflicted | style | accepted | test_hooks_wiring_new_events_contract.py の変数名 blocking と説明文が、request-diff の hook の block と合わない |
| I1-12 | 独立-1 | advisory | no | self-inflicted | style | accepted | test_request_diff_approval_gate.py:133 の置き換えが、テンプレートの変更で何もしていない |
| I2-1 | 独立-2 | medium | no | self-inflicted | request-scope | fixed | compact テンプレートに、差がある点の値とタグの書き方・並べて書かないこと・要件の変更の経路へ送ることが無く、`なし`／`あり:` の並べ書きが残っていた（依頼の項目 1 から外れる）。commit: f01bced3 |
| I2-2 | 独立-2 | low | no | self-inflicted | stop-precheck | accepted | phase-progression の報告型の停止（タグの規定が無いマーカー付きの停止）も Stop で 2 回 block される |
| I2-3 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 値を なし と あり: <項目> の 2 形に閉じたこと（裸の項目を読めない形にした）に、ユーザーの決定が .request.md に無かった。ユーザーが 2 形のままでよいと答えた（.request.md の発言 4） |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | docs/SECURITY.md:130 の「request-diff の hook は止める hook ではない」が古い（I1-3 と同じ） |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | _already_seen が block の記録を数えない変更を、テストが固定していない（I1-4 と同じ） |
| I2-6 | 独立-2 | low | no | self-inflicted | stop-precheck | accepted | block の文の「前置きの説明を書かずに」が、テンプレートの前置き 3 行と同じ語で逆の指示に読める |
| I2-7 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の type が patch（新しい block で minor 相当）。User Action Required の「なし。」と後ろの文が食い違う（I1-7 と同じ） |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片に、GDD を使っていないセッションでも Stop の block が働くことが書かれていない |
| I2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | test_hooks_wiring_new_events_contract.py の assert の文が、request-diff の hook の block と合わない（I1-11 と同じ） |
| I2-10 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 抜粋に読む時期と撤去の条件が無い（PR 本文の別の節にある） |
| I2-11 | 独立-2 | advisory | no | self-inflicted | measurement | accepted | request-diff.log の block の行・知らせの行が not_run を持ち、読み手の失敗の数えに混ざる |
| I2-12 | 独立-2 | advisory | no | self-inflicted | style | accepted | test_request_diff_hook.py のクラスの間の空行が 1 行 |
| I3-1 | 独立-3 | medium | no | self-inflicted | measurement | accepted | compact の 1 行で express の読み込み量の上限を超えるかが未確認（reviewer は実行できない）。tip で validate-plugin.sh を回し、上限内を確かめた |
| I3-2 | 独立-3 | low | no | self-inflicted | request-scope | fixed | compact の差がある点の書き方で「承認にはならず」「経路に送る」が落ちていた（依頼の項目 1 から外れる）。commit: a14bc8f0 |
| I3-3 | 独立-3 | low | no | inherited | stop-precheck | accepted | タグの placeholder の request-diff の値に、none と differs を縦棒で並べて書かせる型が残る（PR 664 の記述） |
| I3-4 | 独立-3 | advisory | no | self-inflicted | request-scope | accepted | 同じターンで 3 回目から止めないことと、GDD 外のセッションでも働くことに、ユーザーの発言が依頼の原文に無い |
