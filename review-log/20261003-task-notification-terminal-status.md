---
lane: L1+
pr: 334
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user（待機の監視を A〔終わりの通知の判定〕→ B〔Stop hook の期限 watchdog〕→ C〔reviewer・gate-runner の background 強制〕→ D〔待機スクリプト〕の 4 PR に分けた最初の PR。実測 2026-09-26〜10-03: background の reviewer・gate-runner 81 件で期限 timer 0 件、planning reviewer が 215 分後に failed。通知の status は 10 日分で completed 7,623・failed 214・killed 128・stopped 56。Opus は、completed だけを終わりとする判定が B のループの原因になり、既存でも継続を抑止し続けると指摘した。main の案と食い違いは無い。ユーザーは分割の順序と、B の対象を reviewer・gate-runner に絞ることを選んだ） | - | 0 | 0 | 0 | 2026-10-03T01:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5defeebde939df47ff53d54dc09bb6aec785ec02 | 1 | 1 | 1 | 2026-10-03T01:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 4490588124150cccfb32e02b49c245043c71cc39 | 1 | 0 | 1 | 2026-10-03T02:10+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus) + Fable (general-purpose, model: fable)（安全策 4 の発火: fail-open〔1 行の中身で parse_transcript が例外で抜ける〕の high が独立-1・独立-2 の 2 巡。実測: 直近 30 日の transcript 9,264 ファイル・2,500,224 行で、文字列でない id・name・tool_use_id、再帰の上限を超える行、読めない行は 0 件。Opus・Fable とも、フィールドごとの isinstance〔列挙〕をやめ、行の処理を 1 か所の except Exception で囲む〔構造〕案を推した。止める案は、accepted の常時 High が次の PR〔同じ transcript.py と Stop hook を触る期限 watchdog〕で安全策 4 を再発火させるので推さない。呼び出し側で block に倒す案は stop_hook_active のループ防止を迂回するので不可。main の案〔reviewer の修正案どおり列挙で直し、medium も直す〕と食い違い、Opus の案を採った。last_user_turn_is_peer は呼び出し側が例外を受けているので触らない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T02:16+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 16b78c8c95d165146afb90a9199d46691d1115ab | 1 | 0 | 1 | 2026-10-03T02:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の再発火: fail-open の high が独立-1〜3 の 3 巡。独立-3 の high は、方針メモ-1 で parse_transcript が行を読み飛ばすようにした結果、同じ行で例外を出す last_user_turn_is_peer に届き、呼び出し側が例外を peer でないと扱う経路。Opus は、呼び出し側 2 か所で例外を止める側に倒す案〔B〕だけを推した。last_user_turn_is_peer を読み飛ばしにする案〔A〕は validate-steering-write の fail-closed を緩めるので入れない。main の案と一致。止める案は accepted の常時 High が次の PR で再発火させるので推さない。Fable はこの PR で使用済み。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T02:35+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | d3d86e61f6a168db140903b5c1909f9c00ec61db | 1 | 0 | 1 | 2026-10-03T02:55+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の 3 回目の発火。独立-4 の high は、user の record の text block の後に文字列でない tool_use_id があると parse_transcript が行ごと捨て、last_user_turn_is_peer はその text を読むので、古い継続意図で block が出る形。reviewer の閉じ方は列挙で、text が文字列でない形・書きかけの行は残る。作り手は host の不具合だけで peer は作れず、実データ 30 日 2,500,224 行で 0 件。Opus は止める案を推した〔開いた入力・脅威モデルの外・確かめの差分巡は残り 1 回〕。main の案と一致。block 単位の捕捉は次の PR〔期限 watchdog〕の最初の commit で入れる。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T03:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨: 終わりの集合を completed・failed・killed・stopped と TaskStop の成功結果にそろえる。そのまま採用） |
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | TaskStop の id・tool_result の tool_use_id が文字列でないと TypeError、深い JSON で RecursionError になり parse_transcript ごと Stop hook が落ちる。文字列のときだけ扱い、RecursionError も捕まえる（テストを先に書いて失敗を確かめた） commit: 367428a7 |
| F2 | 独立-1 | medium | no | self-inflicted | product | fixed | 終わりの status を許可リストで列挙し、host の新しい status で同じ取りこぼしが起きる。<status> があれば終わりとし、in_progress・running・pending だけを除く commit: 367428a7 |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | is_error の除外を固定するテストが無い。task_id を持つ JSON で is_error のケースを足した commit: 367428a7 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | M2 のテストの docstring が「completed 以外は解除しない」のまま commit: 367428a7 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | subagent_in_flight_from_parsed の docstring に TaskStop の解除が無い commit: 367428a7 |
| F6 | 独立-1 | low | no | self-inflicted | style | fixed | 変数名 notification_a_killed が中身（in_progress）と合わない commit: 367428a7 |
| F7 | 独立-1 | low | no | self-inflicted | product | fixed | id と status をブロックの本文全体から拾い、<result> に引用された別の id で終わりにする。<summary>・<result>・<event> より前のヘッダからだけ拾う（テストを先に書いて失敗を確かめた） commit: 367428a7 |
| A1 | 独立-1 | advisory | no | self-inflicted | style | accepted | 孤児の集計 id の除外は判定に効かず、テストも無い（PR 本文に書く） |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | TaskStop の結果・孤児の通知の形と実測件数が repo から確かめられない（PR 本文に at <sha> つきで書く） |
| A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に tool-use-id の拾い方・開始タグでの区切り・deep json のテストが無い commit: なし（PR 本文） |
| A4 | 独立-1 | advisory | no | self-inflicted | test-power | fixed | 閉じていないブロックを開始タグで区切る挙動のテストが無い。テストを足した commit: 367428a7 |
| A5 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 正規表現のコメントが、実際に当たる範囲より狭い commit: 367428a7 |
| G1 | 独立-2 | high | yes | inherited | fail-open | fixed | 文字列でない tool_result の tool_use_id・tool_use の id/name、桁の多い整数・再帰の上限を超える行で parse_transcript が例外で抜け、stop_hook_active の Stop で hook が落ちて done guard が走らない。行の処理を関数に切り出し、1 行の例外はその行だけを読み飛ばす（テストを先に書いて失敗を確かめた） commit: f5f4095d |
| G2 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | 境界のテスト 2 本が、status をヘッダの最初の status で決めるようにしたため、境界の正規表現を外しても通る。2 件目が解除されることを assert する |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | parse_transcript の docstring が「completed・failed・killed・stopped」「閉じタグの境界」のまま |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 本文に通知のブロックを丸ごと引用すると、その id は終わり扱いになる。断片とコメントの「本文に引用された id では終わりにしない」が広い |
| G5 | 独立-2 | low | no | self-inflicted | style | next-pr | M2 のテスト名 test_non_completed_task_notification_does_not_resolve_in_flight が挙動と逆の意味 |
| G6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 通知のヘッダの順序（status と id が <summary> より前）に依存する（PR 本文に書く） |
| G7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | in_progress・running・pending 以外の status（空・大文字の違いを含む）を終わりとする（PR 本文に書く） |
| G8 | 独立-2 | advisory | no | inherited | product | accepted | 通知の text block の後ろに別の text block が付くと、通知を読まない（PR 本文に書く） |
| M2 | 方針メモ-1 | advisory | no | inherited | none | accepted | 要約: なし（Opus・Fable の推奨は行単位の読み飛ばしで一致。そのまま採用。reviewer は repo 全体の Grep で review-log の行を表示したが、判断に使っていないと報告した） |
| H1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | parse_transcript が読めない行を読み飛ばすようになり、同じ行で例外を出す last_user_turn_is_peer に届く。呼び出し側は例外を peer でないと扱い、peer の後でも古い継続意図・merge 報告で block を出す。例外のときは止める側に倒す（テストを先に書いて失敗を確かめた） commit: b0fa0b6e |
| H2 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 再帰の上限を超える入れ子の行のテストが無く、except を狭めても通る。json.loads が実際に RecursionError を出す前提も assert する |
| H3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 「文字列でない id・name の行は読み飛ばす」は list・dict だけで、数値の id は読み飛ばさない。例外の前に処理した block の結果は残る |
| H4 | 独立-3 | low | no | self-inflicted | product | next-pr | 行を読み飛ばした例外を何も記録しない。全行が失敗しても hook-errors に出ない |
| H5 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 入口のテストの assertIn("decision") が部分一致で、継続の block であることを固定していない |
| H6 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 断片の Summary に、読めない行を読み飛ばす変化が無い |
| H7 | 独立-3 | low | no | inherited | product | next-pr | 終わりの通知を、record の最後の text block（candidate）だけから拾う |
| H8 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文のテストの列挙に、読めない行の E2E と桁の多い整数の unit が無い commit: なし（PR 本文） |
| H9 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | commit の件名に巡の ID が入っている（以後の件名には書かない。履歴は書き換えない） |
| M3 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨は B だけ。そのまま採用。既存の peer の E2E テスト〔test_peer_turn_after_gdd_dev_does_not_revive_stale_continuation〕の assertNotIn の文字列が実際の出力と合わず常に通る点は、次の PR で直す） |
| J1 | 独立-4 | high | yes | self-inflicted | fail-open | accepted | user の record で text block の後に文字列でない tool_use_id の block があると、parse_transcript は行ごと捨て、last_user_turn_is_peer はその text を読む。last_user_text が古い継続意図のまま残り、継続・post-merge の block が出る（PR の前は hook が落ちて停止が通っていた）。実データ 0 件、host の不具合でしか作れない。PR 本文の限界の先頭に書き、次の PR の最初の commit で block 単位の捕捉にして閉じる |
| J2 | 独立-4 | low | no | self-inflicted | product | next-pr | peer の判定の例外で止まったときも stderr に peer の文が出て、例外が hook-errors に残らない |
| J3 | 独立-4 | low | no | self-inflicted | test-power | next-pr | 新しい 2 本のテストが int の桁数の上限（CPython 3.11 以上）に頼り、前提を assert していない |
| J4 | 独立-4 | low | no | self-inflicted | test-power | next-pr | post-merge のテストが rc を見ておらず、例外で落ちる形を検出しない |
| J5 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 断片に、行ごとの読み飛ばしと peer の判定の例外を止める側に倒す変更・gdd_stop_hook.py と新しいテストが無い |
| J6 | 独立-4 | advisory | no | inherited | product | accepted | validate-steering-write は peer の判定の RecursionError を最上位の guard で deny にし、Stop hook と意味がずれる（PR 本文に書く） |
| J7 | 独立-4 | advisory | no | self-inflicted | test-power | accepted | 新しい E2E が、peer の guard で止まったこと（stderr）を固定していない（PR 本文に書く） |
| J8 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | peer が無くても、最後の人間のターンの後に読めない行が 1 行あれば次の人間の発話まで継続しない（PR 本文の限界に書く） |
| M4 | 方針メモ-3 | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨は止める。そのまま採用） |
