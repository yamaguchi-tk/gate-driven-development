---
lane: L1
pr: 589
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | aa47c78f065c40aee1879388b1b1e95c5b3f201c | 1 | 3 | 0 | 2026-10-27T17:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | aff13c84c38f07edd0707760786eaa58efae6691 | 0 | 1 | 0 | 2026-10-27T18:30+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 4aa3a6b1ae31aac1211bf1cc15cb68a2580038d1 | 0 | 2 | 0 | 2026-10-28T10:30+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 140d11df1d991564bb6708d60ebf6df2539735f3 | 0 | 0 | 0 | 2026-10-28T11:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | high | no | self-inflicted | changelog-fragment | fixed | 設計: 変えない（断片の必須節の書き漏れで、設計の決定から来た穴ではない）。変更断片に `#### User Action Required` が無い。commit: 9439a82b |
| r1-2 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 【3】の範囲を、accepted を直す PR の申し出に狭めた（「次の PR」から作る段・計画の分割の連鎖は止めない） |
| r1-3 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 【3】の次の手の候補（3 本目で止めて問う・最初の PR で直す）を、申し出をしない規定に代えた |
| r1-4 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 申し出をしない対象が accepted 全体（high・実害クラスを含む）に広がっていた。① の blocking でない medium・low と advisory に限った。commit: 9439a82b |
| r1-5 | 独立-1 | low | no | self-inflicted | same-rule-elsewhere | accepted | gdd-next-plan の手順 4 の補完候補（:74）と Medium Disposition の follow-up PR URL が、PR レビューで直さなかった medium を後続に結ぶ形を残す |
| r1-6 | 独立-1 | low | no | self-inflicted | same-rule-elsewhere | accepted | (3-f) の申し送り（Decision Handoff）の finding も「後続PRに送ること」から外れる |
| r1-7 | 独立-1 | low | no | self-inflicted | condition-narrow | accepted | 作る条件が「PR 番号を挙げて頼んだとき」で、番号なしで頼まれたときの扱いが決まっていない |
| r1-8 | 独立-1 | low | no | self-inflicted | condition-narrow | accepted | 「連鎖の残り」が follow_up_of の無い回収 PR（旧#574・旧#575 型）で決まらない |
| r1-9 | 独立-1 | low | no | self-inflicted | unmeasured | accepted | 別の repo の後続 6 本が申し出から始まったかを測っていない |
| r1-10 | 独立-1 | low | no | inherited | doc-claim | accepted | docs/claude-md-rationale.md:195 が消した句「既定で後続 PR に回す」を今の規則として引き、新しい規定の根拠の項も無い |
| r1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「7 本」に対して件数が 5 つしかない。commit: なし（PR 本文） |
| r1-12 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 軽いレーンの CLAUDE.md の文で申し出が消えるかを、変更の前後で回していない |
| r1-13 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | gdd-next-plan の Scenario Fixture に、新しく禁じた振る舞いの fixture が無い |
| r2-1 | 独立-2 | medium | no | self-inflicted | request-drift | re-reported | r1-2 の再掲（【3】の範囲を accepted を直す連鎖に狭めた） |
| r2-2 | 独立-2 | medium | no | self-inflicted | same-rule-elsewhere | accepted | gdd-next-plan の申し出をしない文が Phase Continuity Packet の項目にあり、後続 Stage の無いマージの出力（:70、post-completion-pr-flow.md:305）には書かれていない |
| r2-3 | 独立-2 | low | no | self-inflicted | changelog-fragment | accepted | 断片の User Action Required が、skill の規定の範囲より広く「マージの後」全体について書いている |
| r2-4 | 独立-2 | low | no | self-inflicted | condition-narrow | accepted | 対象を ① の blocking でない medium・low に狭めたので、:75 の列挙で閉じない high の accepted が対象の外に出た |
| r2-5 | 独立-2 | low | no | self-inflicted | condition-narrow | accepted | 「残りを 1 本にまとめる」の「残り」が、挙げた PR の分か全部かで決まらない |
| r2-6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「前の PR の欠陥を直す後続 PR は変えていない」が、① の accepted の欠陥を含むと読める。commit: なし（PR 本文） |
| r2-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 限界に、頼まれない限り残した指摘が直されないという不利益が無い。commit: なし（PR 本文） |
| r2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「軽いレーンの」を外したので、L0 にも手順 6 の ①〜③ が掛かると読める |
| r2-9 | 独立-2 | advisory | no | self-inflicted | changelog-fragment | accepted | 断片の User Action Required が「なし」と書いた後に頼み方を書いている |
| r2-10 | 独立-2 | advisory | no | inherited | same-rule-elsewhere | accepted | gdd-pr-review-followup:83 の根拠例「後続 PR で対応予定 (#xxx)」が、assistant から後続 PR を約束する形のまま |
| r2-11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 新しい規則の根拠が docs/claude-md-rationale.md に無い |
| r3-1 | 独立-3 | medium | no | self-inflicted | chain-question | accepted | 3 本目の問いは 1 回だけで、まとめた 4 本目が「次の PR」を出すと 5 本目以降は問わずに作られる |
| r3-2 | 独立-3 | medium | no | self-inflicted | chain-question | accepted | 「まとめない」と答えた後の残りの「次の PR」の行き先と、連鎖の終わりの行き先の列挙が決まっていない |
| r3-3 | 独立-3 | low | no | self-inflicted | chain-question | accepted | 3 本目の問いが返事を待つかが書かれておらず、全レーン共通の確認の規定で推奨どおりに進む |
| r3-4 | 独立-3 | low | no | self-inflicted | request-drift | fixed | 依頼の「1 本にまとめるか問う」を「まとめるか止めるか」に替えていた。依頼の文のとおりにした。commit: 8a61a7b8 |
| r3-5 | 独立-3 | low | no | self-inflicted | request-drift | accepted | 確認済み（10-28、今のまま）: 依頼の「『次の PR』の連鎖も」を、accepted を直す連鎖にも 3 本目の問いを掛けると読める。follow_up_of の無い accepted の直しの PR は数えない |
| r3-6 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「計画を分けた連鎖も対象にする」を、follow_up_of のある PR の連鎖に直す。commit: なし（PR 本文） |
| r3-7 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「② の扱いも変えていない」が、② の連鎖に 3 本目の問いが入ることと食い違う。commit: なし（PR 本文） |
| r3-8 | 独立-3 | low | no | self-inflicted | chain-question | accepted | 「3 本目」の数え方（根を含めるか・枝分かれ・Issue が根のとき）が決まっていない |
| r3-9 | 独立-3 | low | no | self-inflicted | chain-question | accepted | 4 本目を 3 本目のマージより前に作ると問いが出ない |
| r3-10 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「（② の次の PR を含む）」を消し、棚卸しと ② の「直後に」のどちらが先かが読みにくくなった |
| r3-11 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 発火条件の数を「なぜ変えるか」に書く。commit: なし（PR 本文） |
| r3-12 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 「行き先が別の PR・Issue だけなら、示して閉じてよい」を消し、明示が無くなった |
| r3-13 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 新しい規定の根拠と、消した括弧の根拠が docs/claude-md-rationale.md に無い |
| r3-14 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 同じ箇条で、語の定義が使った後に来て、「も」「同じように」の指す先がずれた |
| r3-15 | 独立-3 | advisory | no | inherited | doc-claim | accepted | docs/claude-md-rationale.md:223 の引用が規定の文と合っていない（差分より前から） |
| r4-1 | 独立-4 | low | no | self-inflicted | chain-question | accepted | 連鎖の「3 本目」が、follow_up_of: を持たない最初の PR を 1 本目に数えるかを決めていない |
| r4-2 | 独立-4 | advisory | no | self-inflicted | chain-question | re-reported | 3 本目の問いが返事を待たず、推奨の案で 4 本目に進む（r3-3 と同じ） |
