---
lane: L1
pr: 427
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | bc626cab | 0 | 2 | 0 | 2026-10-10 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 072dbe93 | 0 | 1 | 0 | 2026-10-10 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 1d395700 | 0 | 0 | 0 | 2026-10-10 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 53005f79 | 0 | 0 | 0 | 2026-10-10 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 相談の手順が、main が subagent の human check を表示する規定（gdd-dev 9.2、subagent-dispatch の Post-Return Routing・background・HITL Pending Invariant）に入っていない。4 か所に main が `相談役の推奨:` を埋める例外を書いた。commit: 1d395700 |
| I1-2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 一次表示の正本の compact に行の置き場が無く、依頼の「最初から載せる」が表示に届かない。compact の判断ポイントに欄を足した。commit: 072dbe93 |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | `gdd-opus-advisor` を起動する場面の列挙（agent の description、fixed-models.md、autonomy.md の参照元）に原則 7 が無い |
| I1-4 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 変更断片の type が patch。minor にした。commit: 072dbe93 |
| I1-5 | 独立-1 | low | no | self-inflicted | product | fixed | Codex で委譲の許可が無いと、最初の human check の推奨が unavailable になる。PR 本文の限界に書いた。commit: なし（PR 本文） |
| I1-6 | 独立-1 | low | no | self-inflicted | bookkeeping | next-pr | 代わりの経路で起動したときの model・effort の記録先が無い |
| I1-7 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 済ませた相談の再利用で Fable の推奨が Opus の推奨として出うる。Opus 以外だけなら Opus にも相談し、Fable の推奨は model 名つきで添える。commit: 53005f79 |
| I1-8 | 独立-1 | low | no | self-inflicted | product | fixed | 判断ポイントごとの推奨を 1 回の起動で受け取る手順が無い。判断ポイント（番号と選択肢）と main の案を渡し、番号ごとに受け取ると書いた。commit: 072dbe93 |
| I1-9 | 独立-1 | low | no | self-inflicted | product | next-pr | 足す行が Stop hook の HITL の行数の検査に数えられる |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | Handoff で行を足す指示が「いまの結論」の項にある。「次に決めてほしいこと」の `おすすめ` の後に移した。commit: 072dbe93 |
| I1-11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が抜粋に見えない。PR 本文に書いた。commit: なし（PR 本文） |
| I1-12 | 独立-1 | advisory | no | self-inflicted | product | accepted | 依頼の (a) の行き先 旧#424 をリポジトリから確かめられない。旧#424 は root CLAUDE.md の安全策 1 を変えている |
| I1-13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 目的の数値を数えたコマンドと、期間中に human check を表示した件数が無い |
| I1-14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 18 件に Fable を求めた分も入っている。守られたかは行の有無で数えられる |
| I2-1 | 独立-2 | medium | no | self-inflicted | wiring | fixed | gdd-dev 9.2 に `相談役の推奨:` の例外が入っておらず、subagent-dispatch の「main が埋める」と食い違う（I1-1 の残り）。commit: 1d395700 |
| I2-2 | 独立-2 | low | no | self-inflicted | product | next-pr | 原則 7 は判断ポイントごと、compact の欄は選択肢が 2 つ以上の行だけ |
| I2-3 | 独立-2 | low | no | self-inflicted | product | next-pr | compact の欄が、埋め方を定めた原則 7 を指していない |
| I2-4 | 独立-2 | low | no | self-inflicted | product | next-pr | 相談役の出力に番号ごとの推奨の形が無く、流用した推奨が番号ごとに読めないことがある |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の欄名が古い。commit: 1d395700 |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | `gdd-opus-advisor` の起動場面の列挙に原則 7 が無い（I1-3 と同じ） |
| I2-7 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | 目的の数値を数えたコマンドが PR 本文に無い |
| I2-8 | 独立-2 | advisory | no | self-inflicted | product | accepted | 18 件に Fable を求めた分も入っていて、Opus と分けて数えないと効果を小さく見積もる |
| I3-1 | 独立-3 | low | no | self-inflicted | request-drift | fixed | Fable を選んだ経路では Opus の推奨が無いまま表示される。済ませた相談が Opus 以外だけなら Opus にも相談するようにした。commit: 53005f79 |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | compact の欄が原則 7 の書式（区切り・model 名）に追いついていない |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | 原則 7 は判断ポイントごと、compact は選択肢 2 つ以上だけ（I2-2 と同じ） |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | gdd-dev 9 で「同じ assistant turn 内に」を削り、express の例外の文の中身が薄くなった |
| I3-5 | 独立-3 | low | no | self-inflicted | style | next-pr | gdd-dev.md で main の書き方（空白の有無・メイン）が混在する |
| I3-6 | 独立-3 | advisory | no | self-inflicted | style | fixed | 変更断片の余分な空白。commit: 53005f79 |
| I3-7 | 独立-3 | advisory | no | self-inflicted | style | accepted | 9.2 の参照の書き方がほかと違う |
| I4-1 | 独立-4 | low | no | self-inflicted | product | next-pr | model 名の付け方が「済ませた相談」に限られ、Codex・Cursor の代わりの経路の推奨が model 名の無い行に入りうる |
| I4-2 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | autonomy.md の「Opus は呼ばない」がどの場面の話か書かれていない |
| I4-3 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 「その推奨」が何を指すか読み違えやすい。PR 本文を「済ませた相談の推奨は」にした。commit: なし（PR 本文） |
| I4-4 | 独立-4 | low | no | inherited | doc-claim | re-reported | `gdd-opus-advisor` の起動場面の列挙に原則 7 が無い（I1-3 と同じ） |
| I4-5 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | Opus と Fable の両方に相談を済ませていたとき、Fable の推奨を載せるかが決まっていない |
| I4-6 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 「起動し直さない」と言い切った直後に例外を書いている |
