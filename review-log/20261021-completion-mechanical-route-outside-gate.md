---
lane: L1+
pr: 552
follow_up_of: 551
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable 設計レビュー (gdd-fable-advisor, model: fable) | 2297eca8 | 0 | 4 | 0 | 2026-10-21 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 777cefa3 | 0 | 6 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| pm-1 | 方針メモ | medium | no | self-inflicted | routing-order | accepted | 草案の順序（2a → 3 → 4c-3）が Step 4・5 を飛ばす。順序を 2a → 3 → 4 → 4c-3 → 5 にし、スクリプトの行順をこの順にそろえてテストで固定する（Opus・Fable） |
| pm-2 | 方針メモ | medium | no | self-inflicted | loop-bound | accepted | 草案では main の差し戻しを Completion Rounds に数えず、Bounce Log の閾値の昇格も main が行うので、上限が外れる。Codebase Health の High は systematic-debugging に固定して main も Completion Rounds を +1 する（Fable）。reviewed-by の Bounce Log が閾値に達したら main は差し戻さず gate を dispatch する（Opus） |
| pm-3 | 方針メモ | medium | no | self-inflicted | fail-open | accepted | 道具の故障（例外・base を解決できない・JSON を読めない・lint-ac の exit 2）が invalid と同じ値で、main が行で差し戻すと誤送する。状態 `error` を分け、main も gate も差し戻さずに外部前提不足で止める（Fable。Opus は route 行の action=dispatch で同じ点を閉じる案） |
| pm-4 | 方針メモ | medium | no | self-inflicted | request-drift | accepted | 回答済み（推奨のまま）: 順序と差し戻し先を、文書の表 1 か所で決めるか（Fable）、スクリプトの route 行で決めるか（Opus）。推奨（表。行順はテストで固定し、route 行は足さない。Bounce Log と Round の判断が main に残り、route 行は表引きしか代えないため）で進め、PR 本文に問いを書く |
| F1 | 独立-1 | medium | no | self-inflicted | product | accepted | (2) の戻し先の impl-gate に、完了済み task を再 gate する入口が無い（Template が渡すのは Current Task だけ）。impl-gate が approved で返ると Bounce Log 2 → gate の昇格 → Round 上限まで回る |
| F2 | 独立-1 | medium | no | self-inflicted | same-rule-drift | accepted | Implementation Gate Bounce Log の key を、main は行の詳細、gate は自分で組み立てる。一致しないと昇格しない |
| F3 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 2 行以上が fail したときの順序が subagent-dispatch.md の 3 か所（:365・:370・:398）で食い違う（依頼は 1 か所に置く）。推奨（:370 の行の順に寄せる）で進め、PR 本文に問いを書いた。ユーザーの回答（推奨のまま）を受けて :365・:398 を :370 の順に従わせた。commit: a22dc123 |
| F4 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | Step 4c-3 の「invalid（base を解決できない・実行できない）なら High」が、新しい error（止める）と食い違う |
| F5 | 独立-1 | medium | no | self-inflicted | loop-bound | accepted | (5) で Round 上限を超えたとき、「次の phase へ進む」が人に戻す手順より先に読める |
| F6 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 回答済み（推奨のまま）: route-in-progress を main で差し戻さない（依頼より狭い）。推奨（gate に任せる。Checklist E の判断が gate にある）で進め、PR 本文に問いを書いた |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の目的が、gate を起動する場合（(2) の閾値・(4)）を含めていない。commit: なし（PR 本文） |
| F8 | 独立-1 | low | no | self-inflicted | routing-order | accepted | 「最初の ok 以外の行」と「(1) どれかの行が error」のどちらを先に見るかが書かれていない |
| F9 | 独立-1 | low | no | self-inflicted | test-power | accepted | NOT_OK が使われず、assert_fails が error を見ない |
| F10 | 独立-1 | low | no | self-inflicted | test-power | accepted | Codebase Health の JSON を読めない分岐にテストが無い |
| F11 | 独立-1 | low | no | self-inflicted | same-rule-drift | accepted | Completion Rounds の書き手・数えない経路・Bounce Log の書き手を定める別の箇所（state-field-tiers.md・state-machine.md:530-531・bounce-log-schema.md など）が更新されていない |
| F12 | 独立-1 | low | no | self-inflicted | measurement | accepted | main の差し戻しが worklog.md に残らず、後から測れない |
| F13 | 独立-1 | low | no | self-inflicted | product | accepted | main が blocked で止めても Blocked Since を書かない |
| F14 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片と docstring の「lint-ac.py の exit 2」がコード（0・1 以外）と合わない |
| F15 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 回答済み（推奨のまま）: 受け皿の Step 0 の判定（道具の故障を差し戻さず止める）まで変えた。推奨（今の形）で進め、PR 本文に問いを書いた |
| F16 | 独立-1 | advisory | no | self-inflicted | style | accepted | 「下の表」が無い。遷移表の行が番号で指す |
| F17 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 新しい分岐の件数を測ったコマンドが PR 本文に無い |
| F18 | 独立-1 | advisory | no | inherited | product | accepted | gate の Step 0 の exit 2 の再実行に、main と同じ引数の縛りが無い |
| F19 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 4c-3 の直後の「不備がある場合:」が 4c-3 にも掛かって読める |
