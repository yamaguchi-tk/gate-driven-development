---
lane: L1
pr: 675
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5c3d8eba9210bf711bfc841ac1a42c50cfa9f5d5 | 0 | 1 | 0 | 2026-11-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 31473c05e682f3909f866af83b23c60b54ee16b5 | 0 | 1 | 1 | 2026-11-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 48243bdc91f176a38b7ef12c07b452b597650dc4 | 0 | 1 | 0 | 2026-11-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の 7 件のうち I1-4 を、差分でも PR 本文でも扱っていない。元の指摘に含まれると照らした結論を PR 本文の「やっていないこと」に書いた。commit: なし（PR 本文） |
| I1-2 | 独立-1 | low | no | self-inflicted | request-scope | fixed | completion reviewer の承認の記録が § ズレ確認 に出した行を含まず、I1-5 の直しが閉じていない。commit: 0430a0f9 |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「止まらない」が、委任で承認した経路を含めて言い過ぎ。本人の OK のときに限った。commit: 0430a0f9 |
| I1-4 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 記録の場所の無い規則を依頼の側に倒す仮決定が、一次表示に出ない |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | compact の § ズレ確認 の文が full とそろっていない。commit: 0430a0f9 |
| I1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 検査側が記録の場所の「種類」だけを指し、「着手前の commit」も定義されていない |
| I1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未収束の後に「human check に回さない」行が一次表示に出ることの区別が文から読めない |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの 20261113-lockin-revisit-before-hitl の断片が、一次表示に載せないとだけ書く |
| I1-9 | 独立-1 | advisory | no | inherited | doc-claim | accepted | reason の列挙が stop-hook-structured-markers.md・gdd-brainstorming・subagent-dispatch.md に残る |
| I2-1 | 独立-2 | medium | yes | self-inflicted | approval-path | fixed | 設計: 変えない（列挙の範囲が広かったのが原因で、範囲を名指しすれば閉じる）。承認の記録の「§ ズレ確認 に出した行」が、質問や仮決定の無い行まで OK で承認に入る。書く側と読む側を規則・方針の側の仮決定の行に絞った。commit: 7c42ae0f |
| I2-2 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 依頼の I1-5 が、事前回答の委任の経路で閉じていない。規則・方針の側の仮決定があれば委任でも human check を表示する条件を足した。commit: 7c42ae0f |
| I2-3 | 独立-2 | low | no | self-inflicted | request-scope | fixed | I1-4 を変えていないとした根拠が repo の記録から確かめられない。PR 671 の独立レビューの元の出力の句を notes に引いた。commit: なし（PR 本文） |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | compact の語が「ユーザーの決めた規則・方針」から「既存の規則」に変わった |
| I2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「完了条件の変換」の行という呼び名に § ズレ確認 の行を含めている |
| I2-6 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋に、別の PR の指摘 ID と根拠の句）。次の巡の抜粋から除いた |
| I3-1 | 独立-3 | medium | no | self-inflicted | request-scope | fixed | 依頼の I1-4 を変えていない理由が PR 本文から読めない。照らした結果と照合の場所を PR 本文に書いた。commit: なし（PR 本文） |
| I3-2 | 独立-3 | low | no | self-inflicted | approval-path | accepted | 事前回答 3 の新しい条件が、本人が承認した後の human check でも当たる（止まる側） |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | request.md に写す行の一覧から、本人が答えた § ズレ確認 の質問の行が落ちた（前半の一般規定で拾える読み方もある） |
| I3-4 | 独立-3 | advisory | no | inherited | doc-claim | accepted | risk-low の承認での、規則・方針の側の仮決定の行の扱いが書かれていない |
