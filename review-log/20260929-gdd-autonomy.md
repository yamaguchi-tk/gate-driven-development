---
lane: L1
pr: 231
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2ee14fd1419d180e97e9825fe255d7a940fa4aab | 1 | 6 | 3 | 2026-09-29T01:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | f3caf37fa52e04e588d3133e9850a684612b3334 | 0 | 1 | 1 | 2026-09-29T02:05+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 504730459bb6f36ea8a1fa53f34918f5a4a38701 | 1 | 2 | 1 | 2026-09-29T03:00+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 39a64a08f792a61de94c2965194007d4c6932c00 | 2 | 0 | 2 | 2026-09-29T03:40+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 5e95f25ba71be15e0a01c3a75d58b0115565503f | 1 | 0 | 1 | 2026-09-29T04:10+09:00 |
| 独立-6 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | dff21cdf24d361d5de401858236c6ec2446517b4 | 0 | 2 | 2 | 2026-09-29T14:30+09:00 |
| 独立-7 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | b4f05f1187c3a3c79abd40d13a9a1f30ffb3c240 | 0 | 0 | 0 | 2026-09-29T15:10+09:00 |
| 独立-8 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | b2a5aeac3373986e2e09d8b7164802df253b747b | 0 | 0 | 0 | 2026-09-29T16:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | planning_rework_required の除外が human-check-waiting の時点で真にならず、やり直し後の human check が Opus に回っていた。自律で決めてよい停止を閉じた一覧にし、planning_rework_required の route を書く時点で止め、やり直し後の human check を一覧から外した commit: f3caf37f |
| A2 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 止まる条件が閉じた 3 つで、AC の曖昧さ・task 撤回・中止が Opus に回っていた。閉じた一覧に反転し、止まる案と止まる場面を足した commit: f3caf37f |
| A3 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 判断役を起動できないときの規定が無く、Codex では委譲の同意まで main が決められた。起動できないときと Codex の委譲の判断点は止まると書いた commit: f3caf37f |
| A4 | 独立-1 | medium | no | self-inflicted | product | fixed | 宣言を root の CLAUDE.md から読むと self-contained-contract.md の最上位契約と衝突した。宣言を作業ツリー直下の .gdd-config.md に移した commit: f3caf37f |
| A5 | 独立-1 | medium | no | self-inflicted | bookkeeping | fixed | 自律の承認が state.md で人間の承認と区別できなかった。evidence を autonomy:<箇所> にすると書いた commit: f3caf37f |
| A6 | 独立-1 | medium | no | self-inflicted | product | fixed | PR 本文の「自律で判断した箇所」を書く側が配線されていなかった。post-completion-pr-flow.md に Autonomy Decisions Check を足した commit: f3caf37f |
| A7 | 独立-1 | medium | no | self-inflicted | product | fixed | 上限が上限として働かなくなっていた。同じ steering で同じ種類の上限に 2 回目に当たったら止まると書いた commit: f3caf37f |
| A8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 復帰経路・継続の契約にポインタが無く、断片の範囲が配線より広かった。限界に復帰経路と継続の契約を書き、断片を閉じた一覧に合わせた commit: f3caf37f |
| A9 | 独立-1 | low | no | self-inflicted | product | fixed | 宣言の受理集合が読み方で決まっていなかった。.gdd-config.md を Read し、コードフェンス・引用の外の行だけを数え、context に見える行は数えないと書いた commit: f3caf37f |
| A10 | 独立-1 | low | no | self-inflicted | product | fixed | ユーザー本人の返答・割り込みの場面まで Opus に回っていた。止まる場面に足した commit: f3caf37f |
| A11 | 独立-1 | low | no | self-inflicted | product | fixed | 判断役に書き込みの制限が無かった。Plan（Edit・Write を持たない）で起動し、記録は main が行うと書いた commit: f3caf37f |
| A12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「止まるのは〜だけ」が規定と合わず、Codex・Cursor の扱いが書かれていなかった。断片を書き直した commit: f3caf37f |
| A13 | 独立-1 | low | no | self-inflicted | test-power | fixed | 検証が止まる条件を通していなかった。planning_rework と needs_clarification の場面を Skill RED-GREEN Evidence に足した commit: なし（PR 本文） |
| A14 | 独立-1 | low | no | self-inflicted | style | fixed | 行予算のコメントに経緯の数字を積み増していた。コメントを上限と承認の事実だけにし、経緯は断片に寄せた commit: f3caf37f |
| A15 | 独立-1 | low | no | inherited | doc-claim | fixed | rollback-patterns.md の Handoff が存在しない human-check-template.md の節を読ませていた。参照を消した commit: f3caf37f |
| A16 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の抜粋に「ユーザー承認済み」の経緯の記述があった。次の巡の抜粋から除いた commit: なし（PR 本文） |
| A17 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | model: fable を受け付けるかが未検証で、呼べないときの記録値が無かった。Fable: 呼べない を足し、限界に書いた commit: f3caf37f |
| A18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | README の human check の説明が自律モードに触れない。PR 本文に列挙する |
| A19 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 検証と承認の主張は材料から確かめられない。PR 本文に Evidence を書く |
| A20 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | human check の停止を変える規定なので L1+ の安全策が効く種類の変更。hook・gate のコードを触らないので L1 のまま進め、PR 本文に書く |
| B1 | 独立-2 | medium | yes | self-inflicted | approval-path | fixed | 一覧 1 の除外と上限の 2 回目に判別材料・閉じた語彙・優先順位・判定できないときの既定が無く、文脈が切れると自律側に倒れた。一覧 1 を state.md に Approved Direction が無い初回の承認に限り、箇所を閉じた語彙にし、止まる条件の優先と判定できないときは止まることを書いた commit: 50473045 |
| B2 | 独立-2 | medium | no | self-inflicted | product | next-pr | autonomy.md への入口が gdd-dev.md #9 だけで、一覧 2・3 と planning_rework_required の停止に届かない（止まる側に倒れる） |
| B3 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | references の行予算の上限と「余裕は 0」が実測と合わない |
| B4 | 独立-2 | low | no | self-inflicted | product | next-pr | gdd-pr-review から PR を作る経路の PR 本文チェックの列挙に Autonomy Decisions Check が無い |
| B5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | evidence の autonomy:<箇所> が gate-status-schema.md に登録されておらず、design-gating の再記録で上書きされうる |
| B6 | 独立-2 | low | no | self-inflicted | product | next-pr | 宣言の受理を数えない場所の列挙で決めていて、HTML コメント・インデントコードの中の行も数える |
| B7 | 独立-2 | low | no | inherited | product | next-pr | Fable への相談の結果が決定にも記録にも入らない |
| B8 | 独立-2 | advisory | no | self-inflicted | product | accepted | 判断役の read-only は散文だけで、Fable に subagent_type の指定が無い。PR 本文に列挙する |
| B9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片に経緯の文がある。PR 本文に列挙する |
| B10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | Skill RED-GREEN Evidence を材料から確かめられない。PR 本文に書く |
| B11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 一覧 2 に AC の追加・security の新規発生などが入ることが PR 本文と断片から読めない。PR 本文に書く |
| B12 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 「Opus に判断させ」と「design の human check」の書き方が実態と合わない。PR 本文に列挙する |
| B13 | 独立-2 | advisory | no | self-inflicted | product | accepted | 「作業ツリー直下」が root checkout と task の worktree のどちらかが決まっていない。PR 本文に列挙する |
| C1 | 独立-3 | high | yes | self-inflicted | approval-path | fixed | 一覧 1 を state.md に Approved Direction が無いもので決めたため、最初の human check を人間が差し戻した後の 2 回目も一覧 1 に入り、Opus が承認できた。一覧 1 を worklog.md に自律判断: human-check の行が無いものにし、一覧に着いたときは止まるときも行を書くようにした commit: 39a64a08 |
| C2 | 独立-3 | medium | no | self-inflicted | approval-path | fixed | Codex では委譲の許可が承認より前に Approved Direction に書かれ、一覧 1 が発火しなかった。一覧 1 を worklog.md の行で判定するようにした commit: 39a64a08 |
| C3 | 独立-3 | medium | no | self-inflicted | product | re-reported | human_recheck_required と上限到達の停止を定める箇所が autonomy.md を指さず、入口は gdd-dev.md #9 だけ（B2 の再掲） |
| C4 | 独立-3 | medium | no | self-inflicted | approval-path | fixed | 同じ上限の 2 回目を自律で進めた行だけで数え、1 回目を人間が処理すると数え損ねた。一覧に着いたときは止まるときも行を書くようにした commit: 39a64a08 |
| C5 | 独立-3 | low | no | self-inflicted | approval-path | next-pr | 要件ゲートの Round 上限で人間に一括提示する human check も一覧 1 に入る |
| C6 | 独立-3 | low | no | self-inflicted | bookkeeping | re-reported | 予算検査のコメント「余裕は 0」が実測と合わない（B3 の再掲） |
| C7 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 上限の 2 回目の数え方が PR 本文の抜粋に無い。PR 本文に書く |
| C8 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 断片の検証記録を抜粋から確かめられない。PR 本文に Skill RED-GREEN Evidence を書く |
| D1 | 独立-4 | high | yes | self-inflicted | approval-path | fixed | 一覧 1 を worklog.md の行だけで決めたため、宣言より前に人間が承認した steering で、やり直し後の human check を初めてと数えて Opus が承認しえた。止まる場面・判定できないときに行を書かない穴もあった。一覧 1 に Approved Direction が無いことを足し、一覧に着いた後は理由を問わず止まるときも行を書くようにし、宣言より前の差し戻しは限界と User Action Required に書いた commit: 5e95f25b |
| D2 | 独立-4 | high | yes | inherited | approval-path | fixed | 一覧 3 の 2 回目も宣言より前の上限を数えず、宣言の後の 2 回目を 1 回目と数えた。Approved Direction があるのに自律判断: human-check の行が無い steering では一覧 3 でも止まるようにした commit: 5e95f25b |
| D3 | 独立-4 | medium | no | self-inflicted | product | next-pr | 最初の human check の時点で worklog.md が無いとき、読めないとみなして毎回止まる読み方ができる。無いときは行が無いものとして扱うと書く |
| D4 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 人間に止めた行も PR 本文の「自律で判断した箇所」に並ぶ |
| D5 | 独立-4 | low | no | self-inflicted | bookkeeping | next-pr | 判断役を起動できずに止まった行の判断役の推奨・model の欄の値が決まっていない |
| D6 | 独立-4 | low | no | inherited | product | next-pr | Round 上限で残った blocking を accept as known risk にする案が止まる案に入るか書かれていない（C5 と同じ場面） |
| D7 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 断片の検証がこの変更の後のものか確かめられない。PR 本文の Skill RED-GREEN Evidence に、差し戻し後の human check の場面を足す |
| E1 | 独立-5 | high | yes | inherited | approval-path | fixed | 旧#9 以外の経路（中断からの復帰での再生成、Auto-Confirm の戻し）で出た最初の human check は autonomy.md を通らず行が書かれないので、人間が差し戻した後の human check を初めてと数えて Opus が承認しうる。ユーザーの指示でこの PR で直した。人間の返答でも、表示の経路を問わず行を書くようにした commit: dff21cdf |
| E2 | 独立-5 | medium | no | self-inflicted | product | next-pr | Codex では委譲の許可が承認より前に Approved Direction に書かれるので、一覧 1 がどの構成でも自律にならない（止まる側）。判定を `- 方向性:` の行にする |
| E3 | 独立-5 | low | no | self-inflicted | doc-claim | next-pr | 「一覧 1〜3 に着いた後」の「着いた」が、到達か条件を満たしたことか 2 通りに読める |
| E4 | 独立-5 | low | no | inherited | doc-claim | next-pr | Auto-Confirm の steering は Approved Direction を書かないので、途中で宣言を書くと宣言より前の上限を数えられない |
| E5 | 独立-5 | low | no | self-inflicted | doc-claim | next-pr | 断片の Summary と User Action Required が、一覧 3 に足した除外と、途中で宣言を書いたときに一覧 1・3 が使えないことを書いていない |
| E6 | 独立-5 | low | no | self-inflicted | doc-claim | next-pr | 一覧 3 の括弧書き「宣言より前に human check を経たもの」が、条件に当たる範囲（Codex の委譲、Express 昇格の追記、中断）を言い尽くしていない |
| E7 | 独立-5 | low | no | self-inflicted | bookkeeping | re-reported | 判断役を起動せずに止まった行の判断役の推奨・model の値が決まっていない（D5 の再掲） |
| E8 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | Approved Direction の有無の判定方法（見出し・行・追記）が決まっていない。PR 本文に列挙する |
| E9 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | RED-GREEN の場面が Approved Direction の条件・一覧 3 の句・Codex の委譲・旧#9 以外の経路を含むか確かめられない。PR 本文に書く |
| E10 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋が、初めての human check と上限の回数を行だけで決めるように読める。Approved Direction の有無でも決めると書いた commit: なし（PR 本文） |
| G1 | 独立-6 | medium | yes | self-inflicted | approval-path | fixed | 人間の返答の行を 旧#10 のすべての返答で書くため、途中で宣言した steering で一覧 3 の除外条件（Approved Direction があるのに行が無い）が外れた。Approved Direction がまだ無いときだけ書くようにした commit: b4f05f11 |
| G2 | 独立-6 | medium | yes | self-inflicted | security-boundary | fixed | 行を書く時点が provenance 先行判定より前で、cross-session のメッセージが人間の返答として記録された。provenance 先行判定の後、ユーザー本人の入力だけにした commit: b4f05f11 |
| G3 | 独立-6 | low | no | self-inflicted | doc-claim | re-reported | 人間の返答の行が PR 本文の「自律で判断した箇所」に並ぶ（D4 の再掲） |
| G4 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 人間の返答の行の「ほかの欄は なし」が Fable の語彙の外にある。書式を全部書き、Fable: 使わない にした commit: b4f05f11 |
| G5 | 独立-6 | low | no | self-inflicted | approval-path | fixed | human check の表示中の入力を Planning Interrupt Decision Menu で扱う経路は 旧#10 を通らず、行が書かれない（E1 の残りの経路）。入力を扱う先を問わないと書き、HITL Pending Hard Invariant にも参照を置いた commit: b4f05f11 |
| G6 | 独立-6 | low | no | self-inflicted | doc-claim | next-pr | 返答分類の正本 human-check-template.md § 返答分類の判定基準に、行の書き込みが無い |
| G7 | 独立-6 | advisory | no | self-inflicted | doc-claim | fixed | gdd-dev.md のトークン予算に収まるか未確認。validate-plugin.sh で確かめた（express 29827/30083、standard 45150/45405） commit: なし（PR 本文） |
| G8 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | 新しい挙動の Skill RED-GREEN Evidence が材料から確かめられない。PR 本文に書く |
| G9 | 独立-6 | advisory | no | inherited | bookkeeping | accepted | review-log だけを変える commit の件名から、前の独立レビューがあったことが届いた。判断には使われていない |
| H1 | 独立-7 | low | no | self-inflicted | doc-claim | next-pr | autonomy.md の参照元の欄に、手順 5 を参照する gdd-dev.md #10 と subagent-dispatch.md § HITL Pending Hard Invariant が載っていない |
| H2 | 独立-7 | low | no | inherited | product | next-pr | human check の表示中の入力を扱う gdd-using-skills の Workflow Lock に手順 5 への参照が無く、文脈を失うと人間の返答の行が書かれずに後の human check を初めてと数えうる。PR 本文の限界にも書く |
| H3 | 独立-7 | low | no | inherited | bookkeeping | re-reported | 人間の返答・人間に止めた行も PR 本文の「自律で判断した箇所」に並ぶ（D4 の再掲） |
| H4 | 独立-7 | advisory | no | self-inflicted | product | fixed | gdd-dev.md のトークン予算が未実測。validate-plugin.sh で確かめた（express 29827/30083、standard 45150/45405） commit: なし（PR 本文） |
| H5 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | 「手順 5 に従う」だけでは、人間の返答の行の条件（Approved Direction がまだ無いとき）が括弧の奥にある。PR 本文に列挙する |
| I1 | 独立-8 | advisory | no | self-inflicted | style | accepted | 段落をまとめて、止まる案の定義の終わりが行内のラベルだけになった。止まる側に倒れる。PR 本文に列挙する |
| I2 | 独立-8 | low | no | inherited | doc-claim | next-pr | autonomy.md のラベル「ほかに止まるもの」と、手順 5・断片・PR 本文の語「止まる場面」が違う |
| I3 | 独立-8 | low | no | inherited | doc-claim | next-pr | 変更断片の止まるものの列挙から、割り込みと Codex の subagent 委譲の判断点が抜けている |
| I4 | 独立-8 | low | no | inherited | doc-claim | next-pr | 変更断片が、一覧 3 のもう 1 つの除外（宣言より前に human check を経た steering）を書いていない |
