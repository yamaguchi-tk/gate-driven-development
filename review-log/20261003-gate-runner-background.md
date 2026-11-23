---
lane: L1+
pr: 359
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + Fable (general-purpose, model: fable)（待機の監視の 3 本目。旧#334 の方針メモでユーザーが 4 本の分割を選び、旧#349 のマージの後に「次に進んで」と指示した。実測 2026-09-03〜10-03 の main transcript 83 本: main からの起動は同期 993・background 319〔gate-runner 328/64、implementation reviewer 448/107、planning 63/41、security 74/98、completion 80/9〕。30 分を超えた同期の待ち 76 件のうち gate-runner 72・implementation reviewer 4。background の gate-runner の完了通知 79 件の result は最大 9,105 字・中央値 894 字で、human-check の本文を含むもの 5 件。PreToolUse の payload は subagent の中の呼び出しだけに agent_id・agent_type が入り、main には入らない〔headless claude で実測〕。草案の既定は LIMITS の 5 種の deny〔広い側〕。Opus は gate-runner だけの deny を推した〔main からの reviewer の同期起動 665 件は inline gate・gdd-requesting-code-review などが turn 内で集約する前提で、Template を直さない経路の誤 block になる。30 分超の待ちの 72/76 は gate-runner〕。例外・読めない payload は allow して記録、値が読めたら bool の true 以外は deny、新しい script を hooks.json の matcher Agent に 2 本目として足す、を推した。main の案と食い違ったので Fable〔信号 ①〕に相談し、Fable も gate-runner だけを推し、Template に timer を Agent の後に置く・gate-runner 自身の完了通知でだけ Post-Return Routing に進む・先に返ったら timer を TaskStop する、を足した。両方を採った。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T21:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fbfda4b1edf14382cb611d6c4ddfe0ecff42ea12 | 1 | 1 | 1 | 2026-10-03T22:08+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（独立-1 の 閉じ方: 列挙 の high〔F1〕。入力者の実測: 直近 30 日の main transcript で、本文に marker があり tool_use の無い最終発話を、background の dispatch〔起動応答あり・完了通知なし〕の実行中に数えると、対象 type の実行中は blocked 40〔4 本〕・human-check-waiting 22・external-review-waiting 8・done 2・auth-waiting 1、任意の type の実行中は blocked 150・human-check-waiting 63・external-review-waiting 25・done 12・許可外の reason 23。agent が事故で打つ形なので (a)。Opus は、in-flight の間に受理する停止を許可リストで閉じる案〔state を残す 4 つの停止理由、目印の無い停止、全部を TaskStop した後の停止〕と、待つ停止は目印を書かないという文書の修正の組み合わせを推した。type は限らない〔広い側〕。誤 block は最大 185 件で、どれも TaskStop 1 回か目印を外せば抜ける。待ちと本当の停止の内訳は未測。Opus は判定の例外を止める側に倒す案だったが、watchdog の例外の扱い〔記録して通す〕と揃え、限界に書く。main の案と一致） | - | 0 | 0 | 0 | 2026-10-04T18:56+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | f612032b86657ceb867ead1447ce3bb7f6ba34b4 | 1 | 2 | 1 | 2026-10-04T19:40+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus)（L1+ 安全策 4 の発火: fail-open の high が独立-1・独立-2 の 2 巡続いた。対象は Stop hook〔block gate〕で、入力の作り手は main の agent〔本文の marker、Read した reference の tool result、PR review のポーリング回数〕。references/ の literal の marker は 10 ファイル 32 か所。2026-10-03 21:20 開始で 2 巡。main の案は、押し返しを loop state を消す 2 か所〔done 以外の停止の消去は昇格の後、done は post-merge の seed の前〕に callback で移し、watchdog の当てない停止を 旧#349 の集合に戻すもの。Opus も同じ形を推し、Fallback 1 で押し返されたときの案内〔marker を含まない tool を 1 回呼んでから待つ〕と、seed の前で判定することを足した。採った。連続 block の上限・peer・判定の例外で通すのは watchdog と同じ限界。Fable は方針メモで使用済み。memory の 2026-09-28 の決定〔設計変更は内部相談、HITL は機能の見込みが無いときだけ〕に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-04T19:55+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 370d29da50adc55c76b1c8818eb9b51e1b13370c | 0 | 0 | 0 | 2026-10-04T20:30+09:00 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | abab2bda93cac615844b3971c699451899c880b7 | 0 | 0 | 0 | 2026-10-04T22:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus と Fable の推奨〔gate-runner だけを deny、例外は allow して記録、Template の待ち方〕を採用） |
| F1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 待ちの停止の形が決まっておらず、main が既存の継続契約どおり blocked で止まると loop state が消え、watchdog・done guard・この deny・pre-push / pre-PR / merge gate が外れる。background の dispatch の実行中は state を残す停止と目印の無い停止だけを受理し、待つ停止は目印を書かないと規定した（方針メモ-1。テストを先に書いて失敗を確かめた） commit: 55dbe088 |
| F2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 継続契約（setup-gdd-loop.sh・state-machine.md・gdd-dev.md・subagent-dispatch.md の Build Loop）の「ONE assistant turn」「turn を閉じない」が、background で待つ手順と食い違う。待ちは停止ではないと各所に書いた commit: 55dbe088 |
| F3 | 独立-1 | low | no | self-inflicted | product | accepted | background を使えない・挙動が違う host（Cursor の manifest 経由の hook、background の無効化、background の subagent の権限）では deny の出口が kill switch しかない。未測で、入力が開いているので限界に書く |
| F4 | 独立-1 | low | no | self-inflicted | product | fixed | background の返りは tool result ではないので、Stop hook の Fallback 1 が拾えない。返った marker を全部本文に書く手順にし、docstring に書いた commit: 55dbe088 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | README の hook 一覧が 12 本・Agent matcher は block しないのまま commit: 55dbe088 |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「読めない payload は記録する」が型違いの payload に当たらない。「JSON として読めない」に直した commit: 55dbe088 |
| F7 | 独立-1 | low | no | self-inflicted | test-power | fixed | Template のテストが、名前の書き方が変わると空で通り、引数の順序で落ちる commit: b5d7ff20 |
| F8 | 独立-1 | low | no | self-inflicted | test-power | fixed | 新しい deny で kill switch が効くことを固定していない commit: b5d7ff20 |
| F9 | 独立-1 | low | no | self-inflicted | product | fixed | subagent_type の正規化が watchdog と食い違う。limit_kind にまとめた commit: 55dbe088 |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | deny の理由文と docstring が手順の無い節を指し、待ち方・timer の後始末・marker の扱いが抜けている commit: 55dbe088 |
| F11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files に変えたテスト 2 本が無い（利用者から見える変更ではないので書かない） |
| F12 | 独立-1 | advisory | no | self-inflicted | product | accepted | UTF-8 として読めない stdin で、例外の repr に payload が入りうる。PR 本文に書く |
| F13 | 独立-1 | advisory | no | self-inflicted | product | accepted | matcher が Agent だけで Task には当たらない（既存の model gate と同じ）。PR 本文に書く |
| M2 | 方針メモ-1 | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨〔許可リストの停止と文書の修正、type を限らない〕を採用。判定の例外は記録して通し、限界に書く） |
| F14 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 押し返しが止まる理由を本文の marker だけで決めるので、tool result の marker（Fallback 1）とポーリング上限での blocked への昇格の経路では、dispatch が動いたまま loop state が消える。state を消す 2 か所の直前で、昇格の後の実効 reason に当てるようにした（方針メモ-2。テストを先に書いて失敗を確かめた） commit: 33a17c27 |
| F15 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | subagent-dispatch.md の時間上限の節が、watchdog を当てない停止を縮める前の集合のまま。押し返しを state を消す直前に移して集合を元に戻し、別の押し返しがあることを書いた commit: 33a17c27 |
| F16 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 変更断片が Stop hook の挙動の変更（押し返し、待ちは目印なし）と、変えたファイル・テストを書いていない commit: 33a17c27 |
| F17 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | README の Stop 行が「`<gdd-stop>` 以外の停止を block」のままで、目印なしの待ちと state を消す直前の押し返しを書いていない |
| F18 | 独立-2 | low | no | self-inflicted | test-power | next-pr | overdue_reason の type の正規化（空白の除去）を固定するテストが無い |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | wrapper のコメントが「読めない payload は通して記録する」のままで、型を読めない payload は記録しない |
| F20 | 独立-2 | low | no | self-inflicted | style | next-pr | test_background_dispatch_gate.py の docstring の正本の節が古い |
| F21 | 独立-2 | low | no | self-inflicted | product | fixed | cancelled で止まろうとすると、TaskStop と timer の設置を同時に案内する。watchdog の当てない停止を元の集合に戻したので出なくなった commit: 33a17c27 |
| F22 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋のテストの列挙に test_wait_watchdog.py の追加分が無い commit: なし（PR 本文） |
| M3 | 方針メモ-2 | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨〔state を消す直前の押し返し、集合を戻す、Fallback 1 の案内、seed の前で判定〕を採用） |
| F23 | 独立-3 | medium | no | self-inflicted | test-power | next-pr | state を残す停止（clarification-needed・auth-waiting・上限未満の external-review-waiting・human-check-waiting）を、dispatch の実行中に押し返さないことを入口から固定するテストが無い |
| F24 | 独立-3 | low | no | self-inflicted | product | next-pr | blocked・done などは押し返しより先に「次にすること」見出しの要求に当たるので、待つつもりの本文では最初の block が見出しの要求になる（state は残る） |
| F25 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | stop-hook-structured-markers.md（Stop hook の停止判定の所有文書）に、dispatch の実行中の押し返しと期限 watchdog が書かれていない |
| F26 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | subagent-dispatch.md・state-machine.md が、例外（連続 block の上限・peer・判定の例外など）を書かずに押し返すと断定している。PR 本文に書く |
| F27 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 通す条件の列挙（断片・PR 本文）に、state に数を書けないときが無い。PR 本文に書く |
| F28 | 独立-3 | advisory | no | self-inflicted | product | accepted | type を問わないので、利用者が頼んだ無関係な background agent が動いていても押し返し、TaskStop に誘導する。PR 本文に書く |
| F29 | 独立-3 | advisory | no | self-inflicted | style | accepted | ポーリング上限で昇格したときの文面が reason=blocked だけで、昇格を説明しない。PR 本文に書く |
| F30 | 独立-3 | advisory | no | self-inflicted | product | accepted | 「marker を含まない tool を 1 回呼ぶ」案内は、結果が空の tool では最後の tool result を更新しないので効かない（未確認）。PR 本文に書く |
| F31 | 独立-4 | low | no | self-inflicted | test-power | next-pr | state を残す停止（clarification-needed・auth-waiting）を dispatch の実行中に押し返さないことを、入口から固定するテストが無い |
| F32 | 独立-4 | low | no | self-inflicted | test-power | next-pr | 新しい hook の、toplevel が改行で終わるときに active として扱う分岐を通るテストが無い（test_hooks_toplevel_trailing_newline.py の HOOKS に無い） |
| F33 | 独立-4 | low | no | self-inflicted | product | next-pr | 起動応答の判定が本文のどこかの文言で決まるので、同期の subagent の回答がそれを引用すると background とみなし、TaskStop するまで押し返す。run_in_background も条件に入れ、overdue_reason とそろえる |
| F34 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | stop-hook-structured-markers.md・state-machine.md の判定順序・README の Stop 行に、state を消す直前の押し返しと、background の返りに Fallback 1 が効かないことが無い |
| F35 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | setup-gdd-loop.sh の継続契約の CRITICAL（ONE assistant turn）に、gdd-dev.md と同じ待ちの但し書きが無い |
| F36 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | state-machine.md の「dispatch が動いている間、Stop hook は継続を求めない」が、期限 timer の無いときの watchdog の block に触れていない |
| F37 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「期限 watchdog の判定は変えていない」が、type の正規化（前後の空白の除去）の変化を書いていない commit: なし（PR 本文） |
| F38 | 独立-4 | low | no | self-inflicted | bookkeeping | next-pr | 変更断片の Affected Files に test_hooks_kill_switch.py・test_pre_push_gate_contract.py が無い |
| F39 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | Template を general-purpose で起動し直すときに、background の手順を引き継ぐかが書かれていない |
| F40 | 独立-4 | advisory | no | self-inflicted | product | accepted | main か subagent かを agent_id のキーの有無で決めるので、host が null や空文字を入れるようになると deny が外れる。PR 本文に書く |
| F41 | 独立-4 | advisory | no | self-inflicted | product | accepted | ポーリング上限で昇格したときの文面が reason=blocked だけ。PR 本文に書く |
| F42 | 独立-4 | advisory | no | inherited | bookkeeping | accepted | append_hook_error が hook の名前を gdd_stop_hook に固定するので、deny gate の記録も Stop hook の記録になる（差分の外）。PR 本文に書く |
| F43 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | test_background_dispatch_gate.py の docstring の正本の節が本体と食い違う。PR 本文に書く |
