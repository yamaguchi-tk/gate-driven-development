---
lane: L1+
pr: 422
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 1e5850c3 | 0 | 0 | 0 | 2026-10-09 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d449b1a8 | 0 | 6 | 0 | 2026-10-10 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | d449b1a8 | 0 | 0 | 0 | 2026-10-10 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b411836d | 0 | 0 | 0 | 2026-10-10 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | low | no | inherited | design | fixed | 終わっていない shell・Agent の判定を 1 つの述語にまとめ、宣言のある側（`merge_wait_reason` の owner・peer の判定の後）にだけ当てる案を推奨。約束の文の側は、background が動いていた 18 回のうち 13 回で押し返しの後に宣言を書いていたので変えない。例外は「動いていない」（押し返す側）に倒す。Monitor の待機は数えない（限界）。実測: 宣言のある側の押し返し 35 回のうち 28 回で background が動いており（Bash 25・Agent 3）、28 回すべてで後に完了通知が届いた。ユーザーへの確認は、内部相談で進めてよいというユーザーの発言（2026-10-08）に従い、内部相談で代えた。commit: なし（方針の記録） |
| I1 | 独立-1 | medium | no | self-inflicted | request | fixed | 依頼は不要な押し返しの原因を約束の文の側（自由文の解析）に置くのに、差分は宣言のある側だけを変え、約束の文の側を限界に回した。ユーザーに確かめ、約束の文の側は変えないとの回答を `.request.md` に足した（方針メモ-1）。commit: なし（依頼の原文） |
| I2 | 独立-1 | medium | no | self-inflicted | request | fixed | 依頼が指す item 4 の merge gate の複合コマンドの件に行き先が無い。ユーザーに確かめ、別の PR（次の PR）にするとの回答を `.request.md` に足した。commit: なし（依頼の原文） |
| I3 | 独立-1 | medium | no | self-inflicted | request | fixed | 依頼の Issue 旧#246 に行き先が無い。ユーザーに確かめ、merge gate の PR の後の別の PR にするとの回答を `.request.md` に足した。commit: なし（依頼の原文） |
| I4 | 独立-1 | medium | no | self-inflicted | design | fixed | 押し返しを止める background に期限が無く、終わらない処理・resume 後の通知の届かない shell で押し返しが止まり続ける。起動が直近 7,800 秒（wait-until.py の上限 7,200 秒＋600 秒）のものだけを数え、時刻を読めない・未来のものは数えない。宣言の後に起動したものに限る案は、実測で background のある 47 回のうち 23 回が宣言より前の起動だったので採らない。commit: 4363ef77 |
| I5 | 独立-1 | medium | no | self-inflicted | perf | fixed | 3 秒の締め切りの中に transcript 全体の parse を足し、所要を測っていない。実測（本番の transcript で最大 60MB）で parse は最大 0.41 秒。PR 本文に書く。commit: なし（PR 本文） |
| I6 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 打ち切り後も CPU を使う parse と done guard の関係を見るテストが無い。約 30MB の transcript で done guard が 8 秒以内に判定を出すテストを足した。commit: 4363ef77 |
| I7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | モジュールの docstring の「判定できないときは押し返さない」と、background の判定の倒し方（押し返す側）が逆。docstring に例外として書いた。commit: 4363ef77 |
| I8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「transcript を読めないときは押し返す」が入口では成り立たず、読めない transcript のテストは新しい分岐を通らない。PR 本文を実際の挙動に合わせ、そのテストを除いた。commit: 4363ef77 |
| I9 | 独立-1 | low | no | self-inflicted | test-power | fixed | 終わった・止めた background の Agent で押し返すことのテストが無い。完了通知・TaskStop の 2 つを足した。commit: 4363ef77 |
| I10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | hooks.json の description に新しい押し返さない条件が無い。足した。commit: 4363ef77 |
| I11 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 測ったコマンドが PR 本文に無い。目的の節に書く。commit: なし（PR 本文） |
| I12 | 独立-1 | advisory | no | self-inflicted | style | fixed | 終わった id の集合の式が transcript.py と wait_watchdog.py に 2 つある。`finished_task_ids` にまとめた。commit: 4363ef77 |
| I13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 変更断片に内部の整理の文がある。除いた。commit: 4363ef77 |
| I14 | 独立-1 | advisory | no | self-inflicted | product | accepted | background の判定のエラーだけ、記録先が `top` で、ほかの押し返しのエラー（`root`）と分かれる |
| M2 | 方針メモ-1 | low | no | inherited | design | fixed | 独立-1 の I1〜I3（依頼とのずれ）について、ユーザーが「Opus の意見を聞きたい」と答えたので Opus に相談した。推奨: 約束の文の側は変えない（background が動いていた 18 回のうち 13 回は押し返しの後に宣言を書いており、同じ条件を当てると効いていた分だけが消える）。merge gate の件と 旧#246 は別の PR に分け、merge gate を先にする。ユーザーは両方とも Opus の推奨を選んだ。commit: なし（依頼の原文） |
| J1 | 独立-2 | low | no | self-inflicted | symmetry | next-pr | `transcript._launch_epoch` は時差の無い時刻を数えず ValueError だけを捕まえ、同じ `ToolLaunch.timestamp` を読む `wait_watchdog._epoch` はローカル時刻として受ける（`post_merge_continuation._epoch` とも写し）。1 つの関数に寄せる |
| J2 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 部分テスト「時差の無い時刻」の値が窓の外なので、時差の判定を外しても通る。窓の中のローカル時刻にする |
| J3 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 大きな transcript のテストは Agent を使うので block を出すのが state_clear_guard で、締め切りで打ち切られても通る。Bash に替え、background が無いときに宣言の押し返しが出ることも assert する |
| J4 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 開けない transcript で押し返さない（入口の挙動）を固定するテストが無い |
| J5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | テストの docstring 3 か所（7・467・542 行）が、窓と background の判定の倒し方を書いていない |
| J6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の「押し返しが止まり続けない」が、Stop が来ないと窓が効かないことより広く読める |
| J7 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | PR 本文に数えたコマンドが無い。数え方の手順を PR 本文に書いた。窓は、この PR のレビューの指摘を直すために足した押し返し（block）の側の条件で、新しい発火条件の規定の除外に当たる。commit: なし（PR 本文） |
| J8 | 独立-2 | advisory | no | self-inflicted | product | accepted | 宣言と関係の無い background の処理でも、窓の中なら押し返しを止める（PR 本文の限界に書いた） |
