---
lane: L1+
pr: 349
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) + user（待機の監視の 2 本目。旧#334 の方針メモでユーザーが 4 本の分割と、対象を reviewer・gate-runner に絞ることを選び、旧#340 のマージの後に「次に進んで」と指示した。実測 2026-09-26〜10-03: background の reviewer 42 件・gate-runner 39 件で期限 timer 0 件、gate-runner は最長 81 分で上限の規定が無い、planning reviewer が 215 分後に failed。Opus は部品が要るとし、実装前の穴を 2 つ挙げた〔連続 block のカウンタが保存されず上限が効かない、主のいない dispatch に期限切れの block が出続ける〕。ほかに、background の判定を起動応答で行う、timer は期限の後に満了する形だけを認める〔短い timer で再設置の block が続くため〕、人間に渡す停止には当てない、判定の例外は記録して何もしない、transcript は ParsedTranscript を広げて 1 回だけ読む、を推した。main の案〔N ≤ 上限の timer を認める、transcript をもう 1 回読む〕と食い違い、Opus の案を採った。主のいない dispatch は、TaskStop を一度呼んだら結果を問わず対象から外す形にした。background の sleep が Bash の timeout〔600 秒〕で打ち切られるかは、このセッションで sleep 700 を起動して確かめた〔17:35 に起動し約 703 秒で exit 0・status completed の通知、<tool-use-id> つき。600 秒では打ち切られない〕。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T17:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 050a1d6158accfc4cff6afb9f5fa42804606c6a8 | 5 | 2 | 5 | 2026-10-03T18:05+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（独立-1 の 閉じ方: 列挙 の high 3 件〔H2・H3・H4〕。実測: 直近 30 日の main transcript の background Bash 1,756 件のうち、is_error で起動応答の無いもの 9〔hook の deny・auto mode の拒否・merge gate の block〕、正常 1,747 はすべて起動応答あり。H2 は agent が事故で作る形なので (a) で、起動応答を確かめた timer だけを認める許可リストにした〔正常 1,747 件に誤 block 0〕。H3・H4 は host の不具合か敵対的な形〔未測〕だが、self-inflicted で accepted にすると安全策 4 の数えに残るので、Opus は (a) に準じて閉じる案を推した〔timer の形を ASCII・6 桁に絞る、時刻の例外を捕まえる、読めない起動時刻は期限切れに倒す〕。H1・H5 の案には、count の計算を 1 つにする、保存に失敗したら block しない、免除の集合を定数から導く、を足した。state.md 側の human-check 待ちは見ず、限界にした。main の案と一致〔H4 だけ、main の案は未武装の判定に倒すもので、Opus の止める側の案を採った〕） | - | 0 | 0 | 0 | 2026-10-03T18:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3e1c7b7e34e71e7b89864b67be5dd5eb6913316e | 1 | 0 | 1 | 2026-10-03T18:25+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable (general-purpose, model: fable)（安全策 4 の発火: fail-open のクラスタの high を含む巡が 2 回〔独立-1・独立-2〕。独立-2 の high は 閉じ方: 列挙。実測 直近 30 日の main transcript: marker を含む tool result は Bash 777・Read 600 超・Grep 30 超・Agent 約 200。Opus は (r)〔人間に渡す停止を本文の marker だけで見分ける。R1 は accepted にして限界に書く〕を推した。(a)〔Agent・Task の返り値だけを読む〕は引用した marker の形が列挙で閉じず残るため。Fable〔信号 ②〕も (r) を推し、block の文に「止めた後は受け取った marker を本文に書く」を足すこと、_check_stop_markers との非対称は意図として書くこと、(r) の誤 block の件数を測ることを足した。(r) で block になりうる停止点〔直前の tool result に人間に渡す marker があり、本文に marker が無く、background の対象 dispatch が実行中〕は 30 日で 20 件〔9 本〕。案内の 1 行で 1 回の block で抜けられ、連続 block の上限で止まる。main の案と一致。memory の 2026-09-28 の決定に従い、ユーザーへの HITL は内部の相談で代えた〔root CLAUDE.md 安全策 4 の「続行を決めるのはユーザーだけ」と食い違うので、報告で明示する〕） | - | 0 | 1 | 0 | 2026-10-03T18:50+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | cd7bf336ef1eb7bb3b0b60a326c41345ccce3868 | 0 | 0 | 0 | 2026-10-03T19:06+09:00 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | d082e6cf468b35474ea3438f76f935e06600614b | 0 | 0 | 0 | 2026-10-03T19:38+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨〔連続 block のカウンタの保存、主のいない dispatch の除外、起動応答での background の判定、期限の後に満了する timer だけを認める、人間に渡す停止には当てない、例外は記録して何もしない、ParsedTranscript を広げる〕を採用） |
| H1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 連続 block の上限を超えると watchdog が exit 0 し、done guard を飛ばして停止を通す。上限を超えるときは block せず後段に任せ、frontmatter を変えない（テストを先に書いて失敗を確かめた） commit: 4487383b |
| H2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 拒否・失敗で起動しなかった timer も武装とみなし、終わりを tool-use-id だけで判定する。起動応答を確かめた timer だけを認め、shell の id と TaskStop でも終わりを判定する（テストを先に書いて失敗を確かめた） commit: 4487383b |
| H3 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 桁の多い sleep・範囲外の年の時刻で例外になり、その Stop の判定が全部外れる。timer の形を ASCII・6 桁に絞り、時刻の例外を捕まえる（テストを先に書いて失敗を確かめた） commit: 4487383b |
| H4 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 起動時刻が読めない dispatch は期限切れにならず、上限が効かない。期限切れとして TaskStop させる（テストを先に書いて失敗を確かめた） commit: 4487383b |
| H5 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | done 以外の marker を全部免除し、自走する pause も免除する。免除を人間に渡す停止の集合にする（テストを先に書いて失敗を確かめた） commit: 4487383b |
| R1 | 独立-1 | medium | no | self-inflicted | product | fixed | 人間に渡す停止の marker を本文だけから読み、tool result の marker を見ない。_check_stop_markers と同じく両方を読む commit: 4487383b |
| R2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | subagent-dispatch.md の時間上限と Template（同期の gate-runner）が食い違う。Template を使うと対象外になることを書いた commit: 903ac31a |
| R3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 移した docstring と stderr の文が事実と合わない。watchdog が enforce_consecutive_block_ceiling を呼ばなくなり、事実に戻った commit: 4487383b |
| R4 | 独立-1 | low | no | self-inflicted | product | fixed | 正規表現の \s・\d が Unicode に当たる。ASCII にした commit: 4487383b |
| R5 | 独立-1 | low | no | self-inflicted | product | fixed | peer の turn でも block する。peer なら block しない commit: 4487383b |
| R6 | 独立-1 | low | no | self-inflicted | test-power | fixed | 起動応答の無い dispatch の除外、例外のときの stdout、上限と done guard のテストが無い commit: b74c4ba6 |
| R7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 20261002-reviewer-input-time-budget.md の ScheduleWakeup の記述と食い違う。リリースの dry-run で版の節を直す |
| R8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 規定した長さ（1260〜3660 秒）の sleep は実測していない。PR 本文の限界に書く |
| R9 | 独立-1 | advisory | no | self-inflicted | style | fixed | テスト名が確かめている内容と合わない commit: b74c4ba6 |
| R10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 目的の事例のうち、この差分が届く件数が無い。PR 本文に書く |
| M2 | 方針メモ-1 | advisory | no | inherited | none | accepted | 要約: なし（Opus の推奨を採用） |
| S1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 人間に渡す停止の免除を、tool の種類を問わない最後の tool result の marker からも読むので、Read・Grep・Bash の出力の marker で watchdog が外れる。本文の marker だけで見分け、止めた後は marker を本文に書くよう案内する（テストを先に書いて失敗を確かめた） commit: 264a8cc7 |
| S2 | 独立-2 | medium | no | inherited | fail-open | next-pr | _check_stop_markers（Fallback 1）が tool の種類を問わず最後の tool result の marker で停止を通す（既存の形で、watchdog の後段） |
| S3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の文が、timer を TaskStop したときの扱いと食い違う commit: なし（PR 本文） |
| S4 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 上限を超えたときに state を変えないこと、8 回目の Stop の扱いをテストが確かめていない |
| S5 | 独立-2 | low | no | self-inflicted | test-power | next-pr | is_error の起動応答と、TaskStop 単独での timer の終わりのテストが無い |
| S6 | 独立-2 | low | no | self-inflicted | product | next-pr | HANDOFF_STOP_REASONS を差で導くので、ALLOWED_STOP_REASONS に足した reason が黙って免除に入る。明示の集合にして突き合わせのテストを置く |
| S7 | 独立-2 | low | no | self-inflicted | product | next-pr | 起動時刻が少し未来（時計のずれ）でも期限切れになる。許容の幅を決める |
| S8 | 独立-2 | low | no | self-inflicted | style | next-pr | background_shell_ids のコメントが、入る値（起動応答を確かめた shell だけ）を書いていない |
| S9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | peer の turn と、連続 block の上限の後は watchdog が当たらない。PR 本文の限界に書く |
| S10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | Template は gate-runner を同期で起動するので、この差分だけでは watchdog が当たらない。次の PR（C）で background にする |
| M3 | 方針メモ-2 | medium | no | self-inflicted | product | accepted | R1 を戻した: 同期の subagent が返した人間に渡す marker を、main が本文に書かずに止まると、background の対象 dispatch が実行中なら block する（30 日で 20 件の停止点）。止める側に倒れ、案内の 1 行と連続 block の上限で抜ける。PR 本文の限界に書く |
| T1 | 独立-3 | medium | no | self-inflicted | test-power | next-pr | watchdog を _check_stop_markers より前に呼ぶ順序を、tool result だけに人間に渡す marker がある入口からのテストが固定していない |
| T2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | stop-hook-structured-markers.md と state-machine.md の停止判定の順序に、本文だけを読む watchdog の段が無い |
| T3 | 独立-3 | low | no | self-inflicted | product | next-pr | marker を本文に書く案内の行が、TaskStop の無い未武装の block にも付き、本文の marker で外れることを知らせる |
| T4 | 独立-3 | low | no | self-inflicted | product | next-pr | 案内の行のプレースホルダ `<gdd-stop reason="...">` が STOP_PATTERN に一致し、本文に引用すると後ろの本物の marker を取りこぼす（止める側） |
| T5 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が、timer を置いて期限内の dispatch でも block するように読める commit: なし（PR 本文） |
| T6 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 断片の User Action Required に、人間に渡す marker を本文に書くことが無い。PR 本文に書く |
| T7 | 独立-3 | low | no | inherited | doc-claim | next-pr | stop-hook-structured-markers.md の許可 reason が 5 件で、ALLOWED_STOP_REASONS（8 件）と食い違う（差分の外。実データに該当あり） |
| U1 | 独立-4 | medium | no | self-inflicted | product | next-pr | gate-runner の上限 60 分が、内側の reviewer の最悪経路（30 分 + 再実行 30 分 + gate の作業）より短く、gate-runner の超過の扱いが subagent-dispatch.md に無い |
| U2 | 独立-4 | medium | no | self-inflicted | product | next-pr | block の後に timer か TaskStop を呼ぶと、同期 subagent が tool result で返した停止の marker が後段から見えなくなり、blocked・cancelled の停止処理が飛ぶ（state を保ったままの pause） |
| U3 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 規定と PR 本文が、watchdog が /gdd-dev の自走中（local state が active で session が一致）だけ効くことを書いていない。PR 本文の限界に足した（規定は次の PR） commit: なし（PR 本文） |
| U4 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | PR 本文の gdd_stop_hook の行数（1,498）が、取り込んだ後の base（1,490）と合わない。時点を書いた commit: なし（PR 本文） |
| U5 | 独立-4 | low | no | self-inflicted | style | next-pr | gdd_stop_hook の未使用の import time と、参照されない re-export の noqa の説明 |
| U6 | 独立-4 | low | no | self-inflicted | test-power | next-pr | sleep の秒数の部分一致、600 秒の slack の境界、上限を超えたときの assert、write_state 失敗と peer 判定の例外の分岐のテストが無い |
| U7 | 独立-4 | low | no | self-inflicted | test-power | next-pr | test_limits_table が実装の値を写しているだけで、規定と突き合わせていない |
| U8 | 独立-4 | low | no | self-inflicted | product | re-reported | 人間に渡す停止理由を引き算で決めている（S6 と同じ） |
| U9 | 独立-4 | advisory | no | self-inflicted | product | accepted | 拒否・失敗した TaskStop でも、その dispatch は以後の期限の対象から外れる。PR 本文の限界に書く |
