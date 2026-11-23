---
lane: L1+
pr: 664
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 82922a952e3ea2972cdba1c9a133937fc033dd2b | 1 | 4 | 1 | 2026-11-13 |
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | 5b430c88 | 0 | 0 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 5b430c883695d1903e0687e49abb3ff2af25aa8b | 1 | 2 | 1 | 2026-11-13 |
| 方針メモ-1 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | d54a1480 | 0 | 0 | 0 | 2026-11-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | d54a14807e0490ad1af2e1d607b3152dba9b3bb1 | 1 | 0 | 1 | 2026-11-13 |
| 方針メモ-2 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | cbdd5331 | 0 | 0 | 0 | 2026-11-13 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 1053e7b5 | 1 | 2 | 1 | 2026-11-13 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分, model: fable | b205ffee | 1 | 0 | 1 | 2026-11-13 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | d5a1beb0 | 2 | 0 | 2 | 2026-11-13 |
| 独立-7 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 697d263b | 1 | 0 | 1 | 2026-11-13 |
| 方針メモ-3 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 0fb7a41c | 0 | 0 | 0 | 2026-11-13 |
| 独立-8 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 0fb7a41c | 1 | 3 | 1 | 2026-11-13 |
| 独立-9 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 1a2af457 | 1 | 2 | 1 | 2026-11-13 |
| 独立-10 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 767d8f01 | 1 | 1 | 1 | 2026-11-13 |
| 独立-11 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 70effbe0 | 1 | 0 | 1 | 2026-11-13 |
| 独立-12 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | dc257732 | 0 | 1 | 0 | 2026-11-13 |
| 独立-13 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | c1d008ae9b7d98cc1ce0ea3b58d6aa6b6873a5dd | 0 | 1 | 0 | 2026-11-13 |
| 独立-14 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | aa94cc64744e56b23cfebd0ed7c2e5b8e59b2e95 | 1 | 1 | 1 | 2026-11-13 |
| 独立-15 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | d7835b94 | 1 | 0 | 1 | 2026-11-13 |
| 方針メモ-4 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | e85daab8 | 0 | 0 | 0 | 2026-11-13 |
| 独立-16 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | d92fca3400594388570bbbfa9262a5ac16c2d2df | 2 | 2 | 2 | 2026-11-13 |
| 独立-17 | light-lane-independent-reviewer-xhigh, 差分, model: fable | b25a5237 | 1 | 1 | 1 | 2026-11-13 |
| 独立-18 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | d004f3555a4f489a39f6112c4c02e453e358a0b5 | 1 | 2 | 1 | 2026-11-13 |
| 独立-19 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 10146b85462901b09da5caf51c3de17192c37419 | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | yes | self-inflicted | point-count-decl | fixed | 設計: 変える（宣言を本文全体の部分一致で拾う）。前置きの依頼の引用にある「承認ポイント数: N」が宣言として先に拾われ、件数の照合が外れる。行頭の宣言だけを読み、2 行以上は止める。commit: e9e4eee3 |
| I1-2 | 独立-1 | medium | no | self-inflicted | primary-surface-sync | fixed | gdd-requirements-gating の SKILL が一次表示を判断ポイントと OK の範囲だけと書いたまま（依頼から外れる）。commit: 5b430c88 |
| I1-3 | 独立-1 | medium | no | self-inflicted | primary-surface-sync | fixed | 必須ルールの前文と 7 が前置きと現在地の扱いで食い違う（依頼から外れる）。commit: 5b430c88 |
| I1-4 | 独立-1 | medium | no | self-inflicted | advisor-append | fixed | 相談役の推奨の追記が前の番号と案の名前だけに頼る形（依頼から外れる）。commit: 5b430c88 |
| I1-5 | 独立-1 | medium | no | self-inflicted | restate-self-contained | fixed | Clarification Loop の「回答待ち」だけの停止が残る（依頼から外れる）。commit: 5b430c88 |
| I1-6 | 独立-1 | low | no | self-inflicted | restate-self-contained | accepted | Downstream Human Recheck Handoff に前置きの置き場所が無い |
| I1-7 | 独立-1 | low | no | self-inflicted | restate-self-contained | accepted | 再提示の「変えていない点は 1 行」がそれだけで読めることを求めていない |
| I1-8 | 独立-1 | low | no | self-inflicted | request-quote | accepted | request.md が無い・not-copied のときの依頼の行の書き方が無い |
| I1-9 | 独立-1 | low | no | self-inflicted | request-quote | accepted | 言い換えない引用が内部記号の規定・依頼との差の語・用語の lint とぶつかる |
| I1-10 | 独立-1 | low | no | self-inflicted | template-consistency | accepted | 現在地の「次に始まること」と OK後 の行が重なる |
| I1-11 | 独立-1 | low | no | self-inflicted | template-consistency | accepted | 詳細の行が指すものが上位正本・compact・テストで 3 通り |
| I1-12 | 独立-1 | low | no | self-inflicted | template-consistency | accepted | テストの docstring とコメントが前置きを足す前のまま |
| I1-13 | 独立-1 | low | no | self-inflicted | test-power | accepted | 一次表示のテストの本文が手書きで、前置きを消しても緑のまま |
| I1-14 | 独立-1 | low | no | self-inflicted | hitl-length | fixed | 指摘の列挙の扱いが依頼の案（場所を指す 1 行）より広い（依頼から外れる）。commit: 5b430c88 |
| I1-15 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の Validation 欄に検証の種類を書いていない |
| I1-16 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | PR 本文に読む時期と撤去する条件が無い。commit: なし（PR 本文） |
| I1-17 | 独立-1 | low | no | inherited | primary-surface-sync | accepted | GDD Complexity Budget の 30秒判断の列挙が 11-12 の変更から古い |
| I1-A1 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 前置きを機械で見ていない |
| I1-A2 | 独立-1 | advisory | no | self-inflicted | restate-self-contained | accepted | 前置きを毎回書く場面の列挙が箇所ごとに違う |
| I1-A3 | 独立-1 | advisory | no | self-inflicted | primary-surface-sync | accepted | full の出力テンプレートに前置きの欄が無い |
| I1-A4 | 独立-1 | advisory | no | inherited | primary-surface-sync | accepted | NON_ENGINEER_HITL_GUIDE の 30秒判断が前置きに触れていない |
| I1-A5 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文の「前置きは毎回出た」は 1〜2 回の再生からの言い過ぎ |
| I1-A6 | 独立-1 | advisory | no | self-inflicted | hitl-length | accepted | 削らない前置きの分、60 行の警告が増える |
| M-1 | 方針メモ | low | no | self-inflicted | point-count-decl | fixed | 相談役 2 本の推奨で、見出しの行の宣言も数え、行頭にあるのに読めない宣言（埋め忘れ・数でない・5 桁以上）も止める形にした。過去の提示 259 件はすべて宣言 1 つとして読め、誤って止まるものは 0。commit: e9e4eee3 |
| I2-1 | 独立-2 | high | yes | self-inflicted | point-count-decl | fixed | 列挙: 再設計: 宣言を行頭と見出しに限ったので、`>`・番号・太字の疑似見出しの宣言が宣言なしになり、件数の照合が飛ぶ。commit: d54a1480 |
| I2-2 | 独立-2 | medium | no | inherited | advisor-append | accepted | 相談役の推奨の追記がマーカーつきの直前の提示になり、欄が無いと承認の記録が止まる |
| I2-3 | 独立-2 | medium | no | self-inflicted | restate-self-contained | accepted | Clarification Loop の太字の見出しが「再掲しない」のままで本文と逆 |
| I2-4 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 変更断片が見出しの宣言・読めない宣言・deny の文の変更を書いていない |
| I2-5 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 「lint の判定は変えていない」が記録だけの lint の結果の変化を含まない |
| I2-6 | 独立-2 | low | no | self-inflicted | restate-self-contained | fixed | 停止の出力テンプレート（停止しました）に前置きが無い（依頼から外れる）。commit: 260170cb |
| I2-7 | 独立-2 | low | no | self-inflicted | primary-surface-sync | accepted | eval 74 の expected_output と full のテンプレートの現在地の表が前の規定のまま |
| I2-8 | 独立-2 | low | no | self-inflicted | request-quote | accepted | 「行頭の承認ポイント数や依頼との差の語」が 2 通りに読める |
| I2-9 | 独立-2 | low | no | self-inflicted | point-count-decl | accepted | 宣言の問題でも deny の文の先頭が依頼との差と要件の変更の経路を案内する |
| I2-10 | 独立-2 | low | no | self-inflicted | request-quote | accepted | Clarification Loop には request.md が無く、依頼の行の引用元が決まらない |
| I2-11 | 独立-2 | low | no | self-inflicted | test-power | accepted | 足したテストのうち 2 本は挙動を戻しても落ちない・理由を見ていない |
| I2-12 | 独立-2 | low | no | inherited | point-count-decl | accepted | hook と lint で宣言として読む形が違う |
| I2-13 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 未測の deny の分岐（前置きの引用が語を含むと止まる）を残すかは、ユーザーが選んだ案（2026-11-13 11:20。外すのは実測 0 件の分岐だけ）で、残すと決まった |
| I2-14 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 259 件の数は材料から確かめられない |
| M2-1 | 方針メモ-1 | low | no | self-inflicted | point-count-decl | fixed | 再設計: 前提: ずれる（宣言を行の位置で 1 つ選ぶ）。承認ポイント数を依頼との差と同じ予約語として全部の出現で読み、2 つ以上・読めない値は止める。相談役 2 本とも R1。割れた点（同じ値の 2 つ以上を通すか）は、過去の提示 2097 件で 2 つ以上の出現が 0 件なので止める側を採った。commit: d54a1480 |
| I3-1 | 独立-3 | high | yes | inherited | point-count-decl | accepted | 列挙: `承認ポイント数` の後に `:` が無い形が宣言なしとして通り、照合が飛ぶ。語の予約で閉じた（cbdd5331）が、当たる件数が 0 件の分岐だったので、ユーザーの決定（2026-11-13 11:20）で外した。次の PR でタグを読む形に作り直して閉じる |
| M3-1 | 方針メモ-2 | low | no | self-inflicted | point-count-decl | fixed | 再設計: 前提: ずれる（`:` を宣言の引き金にする）。2 本が割れた点（宣言を必須にするか）は、必須にすると欄のある提示 35 件のうち 7 件が止まるので、語の予約だけを採った。必須化はユーザーに確かめる。commit: cbdd5331 |
| I3-2 | 独立-3 | low | no | self-inflicted | scope | fixed | 依頼の「すべての停止」を「人に頼むときだけ」に狭めていた。停止テンプレートと会話の契約を、停止の種類によらず前置きを書く形にし、blocked の例にも足した。commit: 1053e7b5 |
| I3-3 | 独立-3 | low | no | self-inflicted | scope | fixed | 前置きを必ず置くことに検出が無く、読む指標にも無かった。読む時期の指標に「前置き 3 行がある確認の割合」を足した。commit: なし（PR 本文） |
| I3-4 | 独立-3 | low | no | self-inflicted | test-power | accepted | 同じ入力・同じ assert のテストが 2 本あり、名前が前の設計のまま |
| I3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation が、field_problem を呼ぶ lint とログの値の変化を書いていない |
| I3-6 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 停止テンプレートの blocked の例に前置きが無い。I3-2 と同じ規定の箇所なので一緒に直した。commit: 1053e7b5 |
| I3-7 | 独立-3 | low | no | inherited | doc-claim | accepted | compact の `**依頼**:` の placeholder に「…」で切る規定が無い |
| I3-8 | 独立-3 | low | no | inherited | product | accepted | 宣言の問題で止めたときも、deny の文の冒頭が要件の変更の経路を案内する |
| I3-9 | 独立-3 | low | no | inherited | doc-claim | accepted | docstring・hooks.json の止める理由の一覧に宣言の問題が無い |
| I3-10 | 独立-3 | low | no | self-inflicted | bookkeeping | re-reported | 未測の deny の分岐（前置きの引用が語を含むと止まる）を残すかは、ユーザーが選んだ案（2026-11-13 11:20。外すのは実測 0 件の分岐だけ）で、残すと決まった |
| I3-11 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | 2097 件で 0 件の測り方が材料に無い |
| I4-1 | 独立-4 | high | yes | inherited | point-count-decl | accepted | 列挙: 語を書き換えた宣言（`判断ポイント数: 3` など）と数の後ろの補足は、宣言なし・2 として照合を抜ける。ユーザーが PR を分けると決めた（2026-11-13 11:20）。次の PR で件数と欄の値を `<gdd-hitl-fields>` のタグに移し、guard がタグだけを読む形に作り直す |
| I4-2 | 独立-4 | medium | no | self-inflicted | scope | fixed | 依頼の「すべての停止」が、human check の具体例と Downstream Human Recheck Handoff に届いていなかった。両方に前置きを足し、返事を待たない停止の現在地の書き方を足した。commit: b205ffee |
| I4-3 | 独立-4 | medium | no | self-inflicted | point-count-decl | fixed | 実測 0 件の deny の分岐（語の直後が `:` と数でない出現）を、ユーザーの決定（2026-11-13 11:20）で外した。commit: 32cb2586 |
| I4-4 | 独立-4 | low | no | self-inflicted | product | accepted | 宣言の問題で止めたとき、deny の文が語を含む行を示さない |
| I4-5 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 「lint の判定は変えていない」が、field_problem を呼ぶ記録だけの lint とログの値の変化と合わない |
| I4-6 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 変更断片が停止の規定の変更を書いておらず、`:` の無い形という言い方が例と合わない |
| I4-7 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 書き手が読む規定（requirements-gating-steps.md:151 など）に、承認ポイント数を宣言の行のほかに書かない決まりが無い |
| I4-8 | 独立-4 | advisory | no | inherited | point-count-decl | accepted | guard と lint で宣言として読む形が違う |
| I4-9 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文の件数が材料から確かめられない |
| I4-10 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | テストのクラスの説明と guard の docstring が今の規定に追随していない |
| I5-1 | 独立-5 | high | yes | self-inflicted | point-count-decl | accepted | 列挙: 前置きで依頼を複数行で引用し、その中に欄の形の行があると、欠けた本物の欄の代わりに数えられる。ユーザーが PR を分けると決めた（2026-11-13 11:20）。この PR では引用を 1 行に収める規定を足し（commit: c4bf348b）、guard は次の PR でタグを読む形に作り直す |
| I5-2 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 返事を待たない停止がどの reason かが決まらず、done・cancelled の現在地の書き方が無い |
| I5-3 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | human check の具体例が compact の形（前置きの直後に判断ポイント）になっていない |
| I5-4 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 変更断片に rollback-patterns.md と、停止・Handoff の前置きが無かった。断片の確定で直した。commit: acb6c2d6 |
| I5-5 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | Handoff の出力項目で、進み具合を 3 か所に書くことになる |
| I5-6 | 独立-5 | advisory | no | inherited | doc-claim | accepted | gdd-next-plan の `**現在地**:` が別の中身で使われている |
| I5-7 | 独立-5 | advisory | no | self-inflicted | test-power | accepted | Handoff と返事を待たない停止の文言では出力を書かせていない |
| I6-1 | 独立-6 | high | yes | self-inflicted | point-count-decl | accepted | 列挙: 実測 0 件の分岐を外したので、`:` が直後に無い宣言はまた宣言なしとして照合を抜ける。ユーザーが選んだ案（2026-11-13 11:20）の帰結で、次の PR でタグを読む形に作り直して閉じる |
| I6-2 | 独立-6 | high | yes | inherited | point-count-decl | accepted | 列挙: 引用を 1 行に収める規定を guard は強制せず、複数行の引用の中の欄の形の行が本物の欄の代わりに数えられる。ユーザーが選んだ案（2026-11-13 11:20）で、次の PR でタグを読む形に作り直して閉じる |
| I6-3 | 独立-6 | low | no | self-inflicted | test-power | accepted | 語を `:` なしで含む引用で止まらないことを固定するテストが無い |
| I6-4 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | コメントとテストの docstring が、変更後の保証より広い |
| I6-5 | 独立-6 | low | no | self-inflicted | product | accepted | compact の `**依頼**:` の欄に 1 行に収める規定が無い |
| I6-6 | 独立-6 | low | no | self-inflicted | style | accepted | deny の文から読める宣言の形（`: <4 桁までの数>`）が消えた |
| I6-7 | 独立-6 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の限界の節に、受け入れた指摘の記録（直していない常時 High）があった。次の巡の前に抜粋から除く |
| I6-8 | 独立-6 | advisory | no | inherited | point-count-decl | accepted | guard と lint で宣言の受理の形が違う |
| I6-9 | 独立-6 | advisory | no | inherited | doc-claim | accepted | request_diff_approval.py の docstring が止める理由を全部挙げていない |
| I7-1 | 独立-7 | high | yes | inherited | point-count-decl | accepted | 列挙: `承認ポイント数` の後に `:` が無い宣言を読まず、件数の照合が飛ぶ。ユーザーが選んだ案（2026-11-13 11:20）で外した分岐が止めていた形で、次の PR でタグを読む形に作り直して閉じる |
| I7-2 | 独立-7 | low | no | self-inflicted | product | accepted | fail-closed の停止を定める別のファイル（contract-overview.md など）に前置きが無い |
| I7-3 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | full テンプレートと具体例が、必須ルール 7 と前置きの規定に合わない |
| I7-4 | 独立-7 | low | no | self-inflicted | product | accepted | compact の `**依頼**:` に切り方と 1 行の規定が無い |
| I7-5 | 独立-7 | low | no | self-inflicted | product | accepted | 宣言の問題で止めたとき、deny の文の先頭が誤った原因と経路を示す |
| I7-6 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | docstring と hooks.json の止める理由の一覧に宣言の問題が無い |
| I7-7 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | 変更断片が、前置き経由の素通りを過去の出来事として書いている |
| I7-8 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | Clarification Loop の見出しと本文が逆のことを言う |
| I7-9 | 独立-7 | low | no | self-inflicted | product | accepted | `**依頼**:` の引用元（request.md）が無いときの扱いが無い |
| I7-10 | 独立-7 | low | no | self-inflicted | test-power | accepted | 例外を確かめるテストに assert が無い |
| I7-11 | 独立-7 | advisory | no | self-inflicted | test-power | accepted | 同じ入力のテストが 2 本ある |
| I7-12 | 独立-7 | low | no | inherited | doc-claim | accepted | output-format.md の human check の具体例に宣言と欄が無い |
| I7-13 | 独立-7 | advisory | no | inherited | point-count-decl | accepted | lint と guard で宣言の受理の形が違う |
| I7-14 | 独立-7 | advisory | no | inherited | doc-claim | accepted | eval の採点ラベルが必須ルール 7 と食い違う |
| I7-15 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | 軽いレーンで request.md が何を指すかが CLAUDE.md に無い |
| I7-16 | 独立-7 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の限界の文に経緯が混ざっていた。次の巡の前に抜粋から除く |
| M4-1 | 方針メモ-3 | low | no | self-inflicted | point-count-decl | fixed | 設計: 変える（件数と各点の値を提示の自由文から読む）。ユーザーの「highを潰して」で、件数と値をマーカー直前のタグの request-diff に移し、本文の欄は止める向きだけにした。2 本とも同じ設計を推し、割れた点（本文の読めない行も止めるか）は止める側の広い案を採った。過去の欄のある提示 46 件でマーカー直前にタグがあるのは 1 件で、移る間は承認の前に一度止まる。commit: 0fb7a41c |
| I8-1 | 独立-8 | high | yes | self-inflicted | point-count-decl | fixed | 設計: 変える（本文の欄の数をタグと照合する）。引用の欄の形の行が欠けた本物の欄の代わりに数えられ、件数が合って通る。件数の照合と「欄が無い」を外し、通すかと件数はタグだけで決める形にした。commit: 1a2af457 |
| I8-2 | 独立-8 | medium | no | self-inflicted | scope | fixed | 選ばれた案の形（タグだけを読む）と差分の形が違う。I8-1 と同じ修正でタグだけで決める形にした。引用を「…」で切る規定は、本文の読めない行で止める分として残る。commit: 1a2af457 |
| I8-3 | 独立-8 | medium | no | self-inflicted | product | accepted | タグの隣接の実績は 46 件中 1 件で、読む時期に deny の数が入っていない |
| I8-4 | 独立-8 | medium | no | self-inflicted | test-power | fixed | 例外のケースのテストがタグの読み取りに届いていない。欄を置いてタグの読み取りまで通し、返り値を固定した（L1+ 安全策 2 の例外のケース）。commit: f887621b |
| I8-5 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 相談役の推奨の出し直しの規定が hook の説明を古いまま持つ。I8-1 で止める理由が変わったので一緒に直した。commit: 1a2af457 |
| I8-6 | 独立-8 | low | no | self-inflicted | doc-claim | accepted | compact の Required Words がタグの値を none/filled の一方とだけ書いている |
| I8-7 | 独立-8 | low | no | self-inflicted | doc-claim | accepted | request-diff に方向性の点を数えるかが書かれていない |
| I8-8 | 独立-8 | low | no | self-inflicted | product | accepted | 件数をタグの値の数と無回答時のデフォルトの数で突き合わせる記録が無い |
| I8-9 | 独立-8 | advisory | no | self-inflicted | doc-claim | fixed | タグの行の正規表現が lint と違うのにコメントが同じ契約と書いている。コメントを直した。commit: 1a2af457 |
| I8-10 | 独立-8 | advisory | no | inherited | product | out-of-diff | lone surrogate を含む提示で _sha が例外を投げる（wrapper が deny に倒す） |
| I8-11 | 独立-8 | advisory | no | self-inflicted | style | accepted | 記録だけの lint の文言が「欄: タグが無い」になる |
| I9-1 | 独立-9 | high | yes | inherited | regex-redos | fixed | `依頼との差` を含む長い行で FIELD_RE が二乗時間になり、空白 3 万字で 2.5 秒・10 万字で 28 秒（実測）。hook の上限 10 秒を超えると guard 全体が走らない。main にもある部品。無効化後の差分巡の 2 回目の後で、再設計も 2 回使い切ったので、直すかをユーザーに確かめ、「この PR で直す」の返事（13:31）で直した。設計: 変える（欄の行を後戻りする正規表現で読む）。先頭から順に読む線形の処理に置き換えた。commit: 70effbe0 |
| I9-2 | 独立-9 | medium | no | self-inflicted | product | accepted | 本文に欄が 1 行も無い提示でも、タグが none なら承認を記録する |
| I9-3 | 独立-9 | medium | no | self-inflicted | test-power | accepted | 本文に欄が無い形で止める側のテストが無い |
| I9-4 | 独立-9 | low | no | self-inflicted | product | accepted | hook の作り直しをこの PR に入れた理由と、引用の切り方の規定が残ることが PR 本文に無い |
| I9-5 | 独立-9 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界に、消えた件数の不一致の止め方が残っている。commit: なし（PR 本文） |
| I9-6 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | 「タグだけで決める」「件数もタグで取る」が実装より広い |
| I9-7 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | テストの冒頭と deny の文に、欄の欠けで止めると読める説明が残る |
| I9-8 | 独立-9 | advisory | no | inherited | product | out-of-diff | lone surrogate を含む提示で _sha が例外を投げる（deny に倒れる） |
| I9-9 | 独立-9 | advisory | no | inherited | doc-claim | accepted | 断片の User Action Required が「なし」のまま |
| I10-1 | 独立-10 | high | yes | self-inflicted | regex-redos | fixed | 設計: 変える（長さの上限で正規表現の照合を飛ばす）。1,000 字以下の遅い行を並べると合計で時間切れに届く（実測 1 行 2.8 ms、10 秒には約 3.5 MB）。照合を先頭から順に読む線形の処理に置き換え、上限を外した。旧の正規表現と受理が同じことを 30 万件の入力で確かめた。commit: 70effbe0 |
| I10-2 | 独立-10 | medium | no | self-inflicted | test-power | fixed | 時間の assert が照合しない行しか測っていない。上限を外し、照合する長い行と 1,000 字の行を 3,000 本並べた提示の時間を測るテストにした。commit: 250644e6 |
| I10-3 | 独立-10 | low | no | self-inflicted | test-power | accepted | 長い行で入口（validate-steering-write.py）から通すテストが無い |
| I10-4 | 独立-10 | low | no | self-inflicted | product | accepted | 読めなかった行を deny の文に載せる長さに上限が無い |
| I10-5 | 独立-10 | low | no | self-inflicted | doc-claim | fixed | 止める条件の文書に長さの条件が無い。I10-1 で長さの上限を外したので当たらなくなった。commit: 70effbe0 |
| I10-6 | 独立-10 | low | no | self-inflicted | doc-claim | fixed | 変更断片にこの差分の挙動が無い。断片の Summary に、欄の行を順に読んで時間切れの穴を塞いだことを足した。commit: 70effbe0 |
| I10-7 | 独立-10 | advisory | no | self-inflicted | style | fixed | テストのメソッド内の import を先頭に移した。commit: 250644e6 |
| I10-8 | 独立-10 | advisory | no | inherited | product | out-of-diff | lone surrogate を含む提示で _sha が例外を投げる（deny に倒れる） |
| I11-1 | 独立-11 | high | yes | self-inflicted | regex-redos | fixed | 設計: 変える（引用の記号を 1 個ずつ外して残りを複写する）。`>` が長く続く行で二乗の時間になる（実測 30 万字で 11.2 秒）。記号と空白を 1 回で外す形にした。旧の正規表現と受理が同じことを 30 万件の入力で確かめた。commit: 2aeb2a16 |
| I11-2 | 独立-11 | high | no | inherited | regex-redos | out-of-diff | 実測で当たらない: NFKC の正規化が結合文字の長い並びで二乗の時間になるという推定。実測で結合文字 20 万字の正規化は 0.01 秒で、当たらない（Python 3.14 だけの実測。3.9.6・3.12.11 では 17 秒台で再現した。I15-1 で guard に時限を入れて閉じた） |
| I11-3 | 独立-11 | low | no | self-inflicted | test-power | accepted | 時間の assert が壁時計だけで、結果を固定していないケースがある |
| I11-4 | 独立-11 | low | no | self-inflicted | doc-claim | accepted | 「提示の長さに比例する時間」の断定が実装の保証より広い |
| I11-5 | 独立-11 | low | no | inherited | scope | accepted | 「highを潰して」が作り直しをこの PR に入れることまで含むかが依頼の記録から確かめられない |
| I11-6 | 独立-11 | advisory | no | self-inflicted | style | accepted | subTest のラベルが重なる |
| I11-7 | 独立-11 | advisory | no | inherited | doc-claim | accepted | テストファイル冒頭の docstring が古い |
| I11-8 | 独立-11 | advisory | no | inherited | product | accepted | 読めない長い行がそのまま deny の文に入る |
| I12-1 | 独立-12 | medium | no | self-inflicted | scope | accepted | hook の作り直しをこの PR に入れたことと、本文の欄を止める向きに残して引用の切り方の規定を置いたことが、11:20 に選ばれた案（次の PR でタグだけを読む）と違う。「highを潰して」がここまで含むかを PR 本文で確かめ、推奨の今の形で進める。2026-11-13 21:59 のユーザーの「推奨の形でよい」で、この形に決まった |
| I12-2 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | 必須ルール 7 の書き換えが、写像の表・具体例・full の冒頭・compact の OK後・eval 74 に届いていない |
| I12-3 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | タグの値の説明が none/filled の一方のままで、compact の依頼の引用に切り方の規定が無い |
| I12-4 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | Clarification Loop の行が再掲しないと出し直すの両方を書いている |
| I12-5 | 独立-12 | low | no | self-inflicted | product | accepted | request.md が無い場面で前置きの依頼に何を引くかが決まっていない |
| I12-6 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | 「タグだけで決める」「件数はタグで」が実装より広い |
| I12-7 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | タグの行の受理の形が guard と lint で違い、コメントの「guard のほうが厳しい」も当たらない |
| I12-8 | 独立-12 | low | no | self-inflicted | test-power | accepted | 入口からのテストが、引用の件数と欄の数が同じで旧い実装でも通る |
| I12-9 | 独立-12 | low | no | self-inflicted | test-power | accepted | テンプレートの request-diff の値の書き方と guard の受理を突き合わせるテストが無い |
| I12-10 | 独立-12 | low | no | self-inflicted | product | accepted | request-diff.log に判定の根拠のタグの値が残らない |
| I12-11 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | 変更断片の type と User Action Required が hook の契約の変化を表していない |
| I12-12 | 独立-12 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の Validation に検証の種類が無い |
| I12-13 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | PR 本文に guard の変更の読む時期・撤去の条件と、止めたい損失の件数が無い |
| I12-14 | 独立-12 | advisory | no | self-inflicted | test-power | accepted | 時間のテストが、退行すると落ちずに長く止まる |
| I12-15 | 独立-12 | advisory | no | self-inflicted | doc-claim | accepted | 「マーカー直前にタグがあるのは 1 件」は、46 件とも止まると書いたほうが正確 |
| I12-16 | 独立-12 | advisory | no | self-inflicted | doc-claim | accepted | 入口の文と docstring が依頼との差だけを照らすと読める |
| I12-17 | 独立-12 | advisory | no | inherited | product | accepted | deny の後に出し直した提示で、返事を待たずに承認を書けば通る |
| I13-1 | 独立-13 | medium | no | self-inflicted | scope | re-reported | 作り直し（タグの判定）をこの PR に入れたことが、11:20 に選ばれた案（次の PR で作り直す）と違う（I12-1 の再掲） |
| I13-2 | 独立-13 | medium | no | self-inflicted | scope | re-reported | 本文の欄も読み続け、引用の切り方の規定が残っていて、選ばれた案（タグだけを読む）と違う（I12-1 の再掲） |
| I13-3 | 独立-13 | medium | no | self-inflicted | scope | accepted | 選ばれた案は件数と欄の値をタグに移すだったが、タグには値の並びだけで件数が無く、判断ポイントがタグから漏れても通る。I12-1 と同じ問いに足して PR 本文で確かめ、推奨の今の形で進める。2026-11-13 21:59 のユーザーの「推奨の形でよい」で、この形に決まった |
| I13-4 | 独立-13 | low | no | self-inflicted | doc-claim | re-reported | 「通すかどうかと件数はタグだけで決める」が実装より広い（I12-6 の再掲） |
| I13-5 | 独立-13 | low | no | self-inflicted | doc-claim | accepted | タグの値を none/filled の一方とする 2 か所が、request-diff の none/differs の並びと食い違う |
| I13-6 | 独立-13 | low | no | self-inflicted | doc-claim | accepted | 必須ルール 7 の現在地と、出力テンプレート・写像の表・具体例・compact の OK後 の 4 か所が食い違う |
| I13-7 | 独立-13 | low | no | self-inflicted | doc-claim | accepted | full の出力テンプレート・具体例・再質問テンプレが前置き 3 行を持たない |
| I13-8 | 独立-13 | low | no | self-inflicted | product | accepted | request.md が無い・not-copied のときの **依頼**: の書き方が無い |
| I13-9 | 独立-13 | low | no | self-inflicted | doc-claim | accepted | brainstorming の見出し「前回と同一内容の質問を再掲しない」と本文の出し直しが逆を言う |
| I13-10 | 独立-13 | low | no | self-inflicted | bookkeeping | accepted | 断片の type が patch で、guard の止める理由の追加と出力契約の変更に合わない |
| I13-11 | 独立-13 | low | no | self-inflicted | test-power | accepted | 属性名の前とタグ名の後の境界を固定するテストが無い |
| I13-12 | 独立-13 | low | no | self-inflicted | test-power | accepted | テンプレートの request-diff の語彙と TAG_VALUE_RE の食い違いを捕まえるテストが無い |
| I13-13 | 独立-13 | low | no | self-inflicted | doc-claim | accepted | eval 74 の expected_output が、現在地から state.md に移した 2 項目を求めたまま |
| I13-14 | 独立-13 | low | no | self-inflicted | doc-claim | accepted | output-format の human check の具体例に依頼との差・タグ・マーカーが無い |
| I13-15 | 独立-13 | advisory | no | self-inflicted | doc-claim | accepted | 断片の検証の節に、request-diff-approval.log の deny の理由の値が変わることが無い |
| I13-16 | 独立-13 | advisory | no | self-inflicted | product | accepted | **現在地**: の説明に「この確認で何が決まるか」が無い |
| I13-17 | 独立-13 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文に、直したい損失の実データの件数が無い |
| I13-18 | 独立-13 | advisory | no | self-inflicted | doc-claim | accepted | 一次表示のテストの docstring と標本のタグが古い |
| I13-19 | 独立-13 | advisory | no | self-inflicted | approval-path | re-reported | deny の後に同じターンで出し直して承認を書く経路（I12-17 の再掲） |
| I14-1 | 独立-14 | high | yes | self-inflicted | fail-open | fixed | 設計: 変えない（測ると遅さが無く、直す設計が無い）。NFKC の正規化が結合文字の逆順の長い連なりで二乗の時間になり、hook の上限を超えて guard が走らない、という未計測の指摘。`a`＋U+0301×10 万＋U+0316×10 万の行で `field_problem` は 0.01 秒で、再現しなかった。後の退行に備えて、線形時間のテストにこの形を足した。commit: d7835b94（Python 3.14 だけの実測。3.9.6・3.12.11 では 17 秒台で再現した。I15-1 で guard に時限を入れて閉じた） |
| I14-2 | 独立-14 | medium | no | self-inflicted | scope | re-reported | タグによる作り直しをこの PR に入れたことが 11:20 の案と違う（I12-1 の再掲） |
| I14-3 | 独立-14 | medium | no | self-inflicted | scope | re-reported | 本文の欄も読み、引用の切り方の規定が残る（I12-1 の再掲） |
| I14-4 | 独立-14 | medium | no | self-inflicted | test-power | accepted | マーカーごとにタグを要るテストが、末尾のマーカーだけを見る退行を捕まえない |
| I14-5 | 独立-14 | low | no | self-inflicted | doc-claim | accepted | docstring・deny の文・lint のエラー文が、照合の対象を本文の欄として書いたまま |
| I14-6 | 独立-14 | low | no | self-inflicted | doc-claim | re-reported | タグの値を none/filled の一方とする 2 か所の食い違い（I13-5 の再掲） |
| I14-7 | 独立-14 | low | no | self-inflicted | doc-claim | re-reported | brainstorming の見出しと本文が逆（I13-9 の再掲） |
| I14-8 | 独立-14 | low | no | self-inflicted | doc-claim | accepted | 判断ポイントが無い確認で request-diff に何を書くかが無く、空は止まる |
| I14-9 | 独立-14 | low | no | self-inflicted | doc-claim | accepted | compact の **依頼**: の記入欄に、1 行に収める・… で切る規定が無い |
| I14-10 | 独立-14 | low | no | self-inflicted | doc-claim | re-reported | eval 74 の expected_output が古い（I13-13 の再掲） |
| I14-11 | 独立-14 | low | no | self-inflicted | doc-claim | accepted | 必須ルール 7 の表示の契約を外したことが、挙動の変化と断片に無い |
| I14-12 | 独立-14 | low | no | self-inflicted | bookkeeping | re-reported | 断片の type が patch（I13-10 の再掲） |
| I14-13 | 独立-14 | low | no | self-inflicted | test-power | re-reported | テンプレートの語彙と TAG_VALUE_RE の照合が無い（I13-12 の再掲） |
| I14-14 | 独立-14 | low | no | self-inflicted | doc-claim | re-reported | output-format の具体例にタグ・マーカーが無い（I13-14 の再掲） |
| I14-15 | 独立-14 | low | no | self-inflicted | bookkeeping | re-reported | hook の変更の読む時期・撤去の条件と、止めたい損失の件数が無い（I12-13 の再掲） |
| I14-16 | 独立-14 | advisory | no | self-inflicted | doc-claim | re-reported | request.md が無いときの **依頼**: の書き方が無い（I13-8 の再掲） |
| I14-17 | 独立-14 | advisory | no | self-inflicted | doc-claim | accepted | guard のコメントの「行の形は guard のほうが厳しく」は、lint と受理集合が包含関係でないので不正確 |
| I14-18 | 独立-14 | advisory | no | self-inflicted | doc-claim | re-reported | 一次表示のテストの docstring が古い（I13-18 の再掲） |
| I15-1 | 独立-15 | high | yes | self-inflicted | fail-open | fixed | 再設計: 前提: ずれる（遅い形を 1 つずつ線形に直せば guard は上限内に終わる）。設計: 変える（guard 全体に、既定の動作の SIGALRM で 8 秒の時限を掛け、超えたら wrapper が deny に倒す）。Python 3.9.6・3.12.11 の NFKC は結合文字の逆順の連なり 20 万字で 17 秒台かかり、hook の上限 10 秒を超えて guard が走らずに通る。再現テストを先に書いて失敗を確かめた（f388f993）。3.9 の実測で rc 142・9 秒。commit: e85daab8 |
| M5-1 | 方針メモ-4 | low | no | self-inflicted | fail-open | fixed | 再設計: 前提: ずれる（遅い形を 1 つずつ直す）。Opus 2 本とも、遅い形の列挙（結合文字の連続長の上限）と自前の正規化を採らず、guard の入口に SIG_DFL の SIGALRM の時限を置く案を推した。割れた点は時限の秒数（8 と 8.5）だけで、3.9 の実測（起動を含め 9 秒）から余裕を取って 8 にした。commit: e85daab8 |
| I15-2 | 独立-15 | low | no | self-inflicted | test-power | fixed | 足した結合文字の 2 ケースが時間だけを assert する。版で結果が変わるので線形時間のテストから外し、時限のテストに置き換えた。commit: e85daab8 |
| I15-3 | 独立-15 | low | no | self-inflicted | product | accepted | compact の Required Words から前置き 3 行の行を外した（7 行目・Template・上位正本には残る） |
| I15-4 | 独立-15 | low | no | self-inflicted | style | accepted | output-format の停止テンプレートと具体例で、前置きと本文の間の空行を詰めた |
| I15-5 | 独立-15 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files に phase-gate-prechecks.md が無い。commit: e85daab8 |
| I16-1 | 独立-16 | high | yes | self-inflicted | fail-open | fixed | 設計: 変える（時限の外に残る起動の時間を、hook の上限の側で取る）。guard の時限 8 秒と hook の上限 10 秒の間が 2 秒で、起動と import が 2 秒を超えると時限より先に harness が kill して通る。ユーザーの「推奨で進める」で、上限を 30 秒に上げた。上限が時限＋10 秒以上であることを求めるテストを先に書いて失敗を確かめた（333e2016）。commit: b25a5237 |
| I16-2 | 独立-16 | high | yes | self-inflicted | fail-open | accepted | signal.setitimer の無い Windows の Python では時限が張れず、遅い入力で通るまま。ユーザーの「推奨で進める」で、限界として受け入れ PR 本文に書く |
| I16-3 | 独立-16 | medium | no | self-inflicted | test-power | accepted | 時限と hooks.json の timeout の大小をテストで結んでいない |
| I16-4 | 独立-16 | medium | no | self-inflicted | test-power | accepted | wrapper と本物の script を通して時限から deny までを見るテストが無い |
| I16-5 | 独立-16 | low | no | self-inflicted | product | accepted | 時限で止まったときの deny の文が時間切れと分からない |
| I16-6 | 独立-16 | low | no | self-inflicted | doc-claim | accepted | テストのコメントの理由づけ（handler は C の途中で動かない）が、正規表現の driver には当たらない |
| I16-7 | 独立-16 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md と README に時限とその限界が無い |
| I16-8 | 独立-16 | low | no | self-inflicted | product | accepted | 既定の動作の kill は finally を通らず、一時ファイルが残ることがある |
| I16-9 | 独立-16 | low | no | self-inflicted | test-power | accepted | 2 本目のテストが HOME を分けず、3.11 以上の API を使う |
| I16-10 | 独立-16 | low | no | self-inflicted | doc-claim | accepted | 17 秒台の数値に入力の長さが無い |
| I16-11 | 独立-16 | advisory | no | self-inflicted | bookkeeping | fixed | テンプレート外の記述あり（依頼の原文ファイルの「続行」の前置きに巡の ID と経緯）。前置きを何への返事かだけに直した。commit: なし（review-log） |
| I16-12 | 独立-16 | advisory | no | self-inflicted | product | accepted | ほかの block hook は時限を持たない |
| I16-13 | 独立-16 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Validation に足したテストの名前が無い |
| I16-14 | 独立-16 | advisory | no | self-inflicted | test-power | accepted | 1 本目のテストは約 8 秒かかる |
| I16-15 | 独立-16 | advisory | no | self-inflicted | product | accepted | SIGALRM が親から block されたまま渡る場合を戻していない |
| I17-1 | 独立-17 | high | yes | self-inflicted | fail-open | accepted | bash・Python の起動と import は時限の外で、30 − 8 = 22 秒を超えると今までどおり guard が走らずに通る（上限のある hook である限り中からは閉じない）。ユーザーの「限界で受け入れる」で、PR 本文と断片の限界に書く |
| I17-2 | 独立-17 | medium | no | self-inflicted | test-power | accepted | 遅い guard のテストが、起動と import を 1 秒以内に求める（並列の負荷で偽の失敗を出しうる） |
| I17-3 | 独立-17 | low | no | self-inflicted | doc-claim | accepted | guard のコメントが hook の上限を 10 秒と書いたまま |
| I17-4 | 独立-17 | low | no | self-inflicted | doc-claim | fixed | テストの docstring が古い上限のまま。commit: 4b1fa039 |
| I17-5 | 独立-17 | low | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files に hooks/hooks.json が 2 回ある。commit: 4b1fa039 |
| I17-6 | 独立-17 | low | no | self-inflicted | style | fixed | テストが hooks.json を encoding なしで読む。encoding を付けた（helper への置き換えは件数の確認が変わるので見送った）。commit: 4b1fa039 |
| I18-1 | 独立-18 | high | yes | self-inflicted | fail-open | accepted | 起動と import に 22 秒を超えてかかるときと、setitimer の無い Windows では、時限が効かず guard が走らずに通る（I16-2・I17-1 と同じ残り）。ユーザーの「推奨で進める」（19:10、Windows）と「限界で受け入れる」（19:40、22 秒超）で限界として受け入れ済み。reviewer は wrapper が python を background で起動して 25 秒で kill する案（閉じ方: 列挙。bash の起動と Git Bash の kill は残る）も挙げた |
| I18-2 | 独立-18 | medium | no | self-inflicted | primary-surface-sync | fixed | 依頼から外れる（main が確かめた）: 正本 human-check-template.md の full の出力テンプレートと具体例に前置き 3 行が無く、4 行の `### 現在地` 表が残っていた。前置きを入れ、表を `今やること:`・`OK後:` の 1 行に替え、写像表を前置きに向けた。output-format のブロックの言い回しの例には、前置きを省いて示すと注記した。commit: 10146b85 |
| I18-3 | 独立-18 | medium | no | self-inflicted | doc-claim | accepted | 変更断片の User Action Required が「なし」のまま（タグの無い提示の承認が一度止まる、8 秒を超える書き込みが止まる） |
| I18-4 | 独立-18 | low | no | self-inflicted | doc-claim | accepted | 未リリースの断片 20261110-request-diff-field.md が、欄が無い・件数が合わないで止めると書いたまま |
| I18-5 | 独立-18 | low | no | self-inflicted | doc-claim | accepted | § 止まり直さないもの 1 が、hook は欄が無い確認を拒否すると書いたまま |
| I18-6 | 独立-18 | low | no | self-inflicted | doc-claim | accepted | 一部の点だけ答えた返答の出し直しと compact のタグの値の説明が、request-diff に触れていない |
| I18-7 | 独立-18 | low | no | self-inflicted | doc-claim | accepted | guard と lib とテストのコメントが hook の上限を 10 秒と書いたまま（I17-3 と同じ型） |
| I18-8 | 独立-18 | low | no | self-inflicted | product | accepted | guard の中の subprocess の持ち時間の予算が時限 8 秒と組み合っておらず、時限で止めた件数が記録に残らない |
| I18-9 | 独立-18 | low | no | self-inflicted | doc-claim | accepted | brainstorming の見出しと本文が逆（I13-9 と同じ型） |
| I18-10 | 独立-18 | low | no | self-inflicted | test-power | accepted | 前置きの lint のテストの `詳細:` の行が `なぜやるか` を含み、前置きを消しても通る |
| I18-11 | 独立-18 | low | no | self-inflicted | product | accepted | request.md が無い停止で `**依頼**:` に何を書くかが無い |
| I18-12 | 独立-18 | low | no | self-inflicted | product | accepted | 読む時期の比較が件数あたりでなく、タグ化と時限の読む時期・撤去の条件が無い |
| I18-13 | 独立-18 | low | no | self-inflicted | doc-claim | accepted | 変更断片の時限の記述の重複・測った版の一般化・タグだけで決めるという言い過ぎ |
| I18-14 | 独立-18 | advisory | no | self-inflicted | test-power | accepted | 時限のテストが 8 秒以上かかり、enterContext が 3.11 以上を要る |
| I18-15 | 独立-18 | advisory | no | self-inflicted | doc-claim | accepted | NFKC の実測値の裏づけが差分に無い |
| I18-16 | 独立-18 | advisory | no | self-inflicted | product | accepted | 引用がマーカーやタグの文字列を含むと止まり、deny の文が原因を案内しない |
| I19-1 | 独立-19 | low | no | self-inflicted | doc-claim | accepted | 30秒判断の中身を列挙する § GDD Complexity Budget が、なぜやるかを 30秒判断の先頭に残すと書いたまま |
| I19-2 | 独立-19 | low | no | self-inflicted | doc-claim | accepted | `OK後:` の placeholder が残タスクを出すと書き、必須ルール 7 と写像表は残タスクを state.md に書くとする |
| I19-3 | 独立-19 | low | no | self-inflicted | product | accepted | タスクが決まる前の停止（/gdd-dev 単独など）で前置きに何を書くかが無い（I18-11 と同じ型） |
| I19-4 | 独立-19 | low | no | self-inflicted | test-power | accepted | eval 74 と grade_evals の採点が、外した現在地の 4 行の表の語を求めたまま |
| I19-5 | 独立-19 | low | no | self-inflicted | doc-claim | accepted | full の現在地の表を 1 行にしたことが PR 本文と断片に無い。PR 本文には足した |
| I19-6 | 独立-19 | low | no | self-inflicted | doc-claim | accepted | lint のコメントが full は `人間が今やること` と書いたまま |
| I19-7 | 独立-19 | low | no | self-inflicted | doc-claim | accepted | TEAM_ROLLOUT.md が先頭は 30秒判断と案内したまま |
| I19-8 | 独立-19 | advisory | no | self-inflicted | doc-claim | accepted | full の `**依頼**:` の placeholder に 1 行に収める規定への指しが無い |
| I19-9 | 独立-19 | advisory | no | self-inflicted | doc-claim | accepted | full の冒頭に、決めることの数と OK の中身を閉じる文の placeholder が無い |
