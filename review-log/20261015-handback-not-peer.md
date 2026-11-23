---
lane: L1+
pr: 526
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | - | 0 | 0 | 0 | 2026-10-15 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4465df3d | 0 | 4 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | fail-open | accepted | Opus と Fable はどちらも、案 B（origin.kind が peer で senderTaskId が空でない str の行を、同じ session の行として読み飛ばす）と案 S1（共有の last_user_turn_is_peer を直し、steering write guard・Stop hook・wait watchdog を揃える）を推した。割れた点は parse_transcript：Opus は変えない、Fable は同じ 3 値の判定を当てる。今の parse_transcript は peer の行を last_user_text に採らずに読み進め、読み飛ばしと同じなので、変えない側を採った。依頼の文は subagent に当てない（主体で外す）だが、hand-back の origin で外す手段に代えた（main での deny 1 件も閉じ、本物の peer の後に subagent が書く形を通さないため）。S1 で Stop hook と watchdog が hand-back の user 行の直後に検査を飛ばさなくなる。PR 本文で問い、ユーザーは「このまま」「変えない」と答えた |
| I1-1 | 独立-1 | medium | no | self-inflicted | product | accepted | 依頼の前半「バイト上限を warn にし」が差分に無い。上限超えは 2026-09-06 以降 0 件で、Opus と Fable の推奨（変えない）で進め、PR 本文で問い、ユーザーは「このまま」「変えない」と答えた |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | accepted | 依頼の「subagent に当てない」（主体で外す）を、行の origin.senderTaskId で外す手段に代えた。方針メモの推奨（B）で進め、PR 本文で問い、ユーザーは「このまま」「変えない」と答えた |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | accepted | 共有の last_user_turn_is_peer を変えたので、Stop hook の post-merge の判定・継続意図の guard・マージ待ちの押し返し・wait watchdog も、同じ session の行の後で動くようになる。方針メモの推奨（S1）で進め、PR 本文で問い、ユーザーは「このまま」「変えない」と答えた |
| I1-4 | 独立-1 | medium | no | self-inflicted | security-boundary | accepted | senderTaskId を同じ transcript の起動応答の agentId と照合していない。実測では別セッションの行 109 本のうち senderTaskId を持つものは 0 本、照合を足すと同じ session の行 4,516 本のうち 121 本（起動応答 2,253 本だけなら約半分）が再び deny になる。当たる件数が 0 の deny の分岐は足さない（全レーン共通・規律 C）ので足さず、限界の節に書く |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文に、deny 11 件が新しい条件に当たることと、各数のコマンドが無い |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の Stop hook 側の変化の書き方が狭い（4 つの判定、SendMessage の行の後も変わる） |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | peer turn のときだけ出ていた Origin Session の初回・射影できない Edit・読めない move の deny も、同じ session の行の後で出なくなることが書かれていない |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | constants.py:173-189 の注釈に同じ session の行の例外が無い |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | last_user_turn_is_peer の docstring の定義に例外が無く、_is_same_session_origin の docstring が host の挙動を言い切っている |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | references/phase-progression.md:31 の識別基準に例外が無い |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | references/autonomy.md:12 の SendMessage を使わない理由が成り立たなくなる |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 未リリースの changelog.d/20261005-queued-task-notification.md:11 と逆のことを書く |
| I1-13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | tests/test_queued_task_notification.py:339-343 の case 名「hand-back」が、senderTaskId の無い行を確かめている |
| I1-14 | 独立-1 | low | no | self-inflicted | test-power | accepted | test_malformed_origin_does_not_crash が戻り値を assert せず、kind == "peer" の条件を外す変異が残る |
| I1-15 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 呼び出しの tip 欄が sha でなかった（材料は最後まで読めた） |
| I1-16 | 独立-1 | advisory | no | self-inflicted | style | accepted | last_user_turn_is_peer の複雑度（ADR で 17）に分岐を 1 つ足した |
| I1-17 | 独立-1 | advisory | no | inherited | product | accepted | queued の分岐と user 行の分岐で、origin.kind を受け付ける範囲が違う（差分は変えていない） |
