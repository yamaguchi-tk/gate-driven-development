---
lane: L1+
pr: 376
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（実測: 30 日の transcript 3,211 本で、終わりの通知が enqueue+remove だけ 4,472、attachment だけ 159、enqueue だけ 140〔うち Agent 2〕。main の草案は queue-operation を operation を問わず読む案だった。Opus は、enqueue だけは配達待ちで、ここで state を消して止まると通知が state の無いセッションに届く〔state_clear_reason の目的に反する〕として remove だけを読む案を推奨した。main はこれを採り、ユーザーが承認した。食い違いは残らないので max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-05T12:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 16a5a4b9 | 1 | 1 | 1 | 2026-10-05T13:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus)（独立-1 の N1 が high・blocking で閉じ方: 列挙。入力者の実測: queued_command の attachment の origin.kind は、本文が agent-message 885・cross-session-message 14 ですべて peer、人間の文は human 414、通知は task-notification 551 かキー無し 1,930、ci-monitor-event はキー無し 139。queued の peer の文が type:user に出ずに queued でだけ届いたものが cross-session で 7。Opus は、本文の先頭で判定する reviewer 案〔人間の途中発話の後の state.md の write 39 件を deny する〕ではなく、宣言フィールド attachment.origin.kind の許可リスト〔human・task-notification・auto-continuation と origin 無し〕で閉じ、steering write guard だけに入れる (a) を推奨した。main の草案は origin を最上位のキーだけで探して「無い」としていた誤りがあり、Opus の案を採った。食い違いは残らないので max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-05T14:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9dd48ddb | 1 | 2 | 1 | 2026-10-05T15:00+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（安全策 4 の発火: peer 境界のクラスタの high が独立-1・独立-2 で 2 回。対象は exit 2 の block gate の steering write guard、入力者は host。実測: origin の無い queued_command 2,072 行に peer の本文 0 件。queued の peer の後・次の人間の発話より前の .steering への write 23 件に、承認・完了・中止・Origin Session は 0 件。Opus・main とも「止める」。ユーザーの指示で Fable〔gdd-fable-advisor〕にも聞き、推奨は「止める」で同じ。ユーザーは「止める」を選んだ。以後この PR では安全策 4 を発火させない） | - | 0 | 0 | 0 | 2026-10-05T16:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| N1 | 独立-1 | high | yes | inherited | peer 境界 | fixed | 列挙: queued で届いた peer の文を last_user_turn_is_peer が読まず、steering write guard の peer 境界が効かない。方針メモ-2 の (a) で、attachment.origin.kind の許可リストを steering write guard だけに入れた。commit: 2f797685 |
| N2 | 独立-1 | medium | no | self-inflicted | 受理集合の対称性 | fixed | queued の本文が list だと読まず、type:user の行と受理する型がずれる。commit: 49cf0482 |
| N3 | 独立-1 | low | no | self-inflicted | テストの検出力 | fixed | 「判定できないときは通さない」のテストの docstring が、期限 timer の向きまで含めて断定している。commit: 49cf0482 |
| N4 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 変更断片が、新しく出る block（継続の block、期限 timer が無い）を書いていない。commit: 49cf0482 |
| N5 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 完了通知の届き方を type:user の text と書く 3 か所が更新されていない。commit: 49cf0482 |
| N6 | 独立-1 | low | no | self-inflicted | テストの検出力 | fixed | overdue の経路のテストが文言の不在しか見ていない。commit: 49cf0482 |
| N7 | 独立-1 | advisory | no | self-inflicted | 文言 | fixed | PR 本文の enqueue だけ 140 件の内訳（残り 40 件）が書かれていない。commit: なし（PR 本文） |
| M2 | 方針メモ-2 | - | - | - | - | - | なし |
| P1 | 独立-2 | high | yes | self-inflicted | peer 境界 | accepted | 列挙: origin キーの無い queued_command の行を、本文を問わず peer でないとして通す（origin が null・{} なら peer に倒すのと非対称） |
| P2 | 独立-2 | medium | no | self-inflicted | peer 境界 | accepted | subagent の hand-back が queued で届いた後も承認・完了・中止の write を止め、Stop hook 側の継続と食い違う。changelog・PR 本文が steering write guard 側の新しい deny を書いていない |
| P3 | 独立-2 | medium | no | self-inflicted | 文言 | accepted | phase-progression.md:31 の peer の識別基準が queued の経路を書いていない |
| P4 | 独立-2 | low | no | self-inflicted | 文言 | accepted | queued の本文が list のとき tool_result block も読むが、記述は text だけ |
| P5 | 独立-2 | low | no | self-inflicted | 文言 | accepted | last_user_turn_is_peer の docstring の 2 か所が食い違い、_payload_is_peer_turn の docstring が queued に触れていない |
| P6 | 独立-2 | low | no | self-inflicted | テストの検出力 | accepted | Stop hook 側が queued の peer を読まないことを入口から固定するテストが無い |
| P7 | 独立-2 | advisory | no | self-inflicted | 文言 | accepted | remove を配達済みとして読む根拠の実測が残っていない（PR 本文に実測を書いた） |
| M3 | 方針メモ-3 | - | - | - | - | - | なし |
