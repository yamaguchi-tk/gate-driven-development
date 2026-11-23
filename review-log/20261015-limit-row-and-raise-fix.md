---
lane: L1
pr: 521
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | bb8550bb | 2 | 1 | 3 | 2026-10-15 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | bb8550bb | 0 | 0 | 0 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6a7e29ec | 1 | 2 | 2 | 2026-10-15 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 5e634964 | 0 | 2 | 0 | 2026-10-15 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 1551aeed | 2 | 0 | 2 | 2026-10-15 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 9def7a74 | 1 | 0 | 1 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | 列挙: remediation-loop-limit の鍵 `<Current Task の id>:<Fix Attempts>` は承認で Fix Attempts が戻るので、同じ task の 2 回目の到達も同じ鍵になり、書き足さずに数え落とす。列挙の (a)〜(c) ではなく、鍵と書き足しの抑止を外し、行を止まる遷移に結びつけて（遷移を書いた側が同じ手順で書く。表示し直しでは書かない）構造で閉じた（方針メモ-1。Opus・Fable とも同じ推奨）。commit: 6a7e29ec |
| A2 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | subagent が 4 択を出す経路で、委任していない到達の `上限到達:` 行を main が書く指示が main の表示経路に無く、1 回目が記録されない。遷移を書いた側（gate runner などの subagent か main）が書く形にし、gate runner の契約にも書いた。委任先に聞く前に 0 本なら止まる（Opus の補足）。commit: 6a7e29ec |
| A3 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | § 事前回答 4 で後続 Stage に写した委任の行が、写した先の Approved Direction（引き下げ前の値）で読まれ、自走のマージに進む。原文が自走上限に触れない行は、写す時点の元の steering の Approved Direction で写す（Fable の案。Opus の「狭い方」は置換値に順序が無い組があるため採らなかった）。commit: 6a7e29ec |
| A4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「狭い側に倒れる」が、引き下げた場合を隠している。PR 本文の限界を直した。commit: なし（PR 本文） |
| A5 | 独立-1 | low | no | self-inflicted | product | accepted | 表示した human check を `人に止める` で承認しても、前の判断の委任の行が効き続ける |
| A6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「4 択を表示するか」が、選択肢が 3 つの 2 種の上限に合わない。「4 択を表示するか」の文を外した。commit: 6a7e29ec |
| A7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「subagent は書かないことも書く」が followup の行には無い。PR 本文の書き方を直した。commit: なし（PR 本文） |
| A8 | 独立-1 | low | no | self-inflicted | product | fixed | 鍵の無い既存の `上限到達:` 行の扱いと、新しく止まる条件が断片に無い。鍵を外したので、鍵の無い行との互換の問題が無くなった。commit: 6a7e29ec |
| A9 | 独立-1 | low | no | self-inflicted | product | fixed | Gate Batch では鍵の `<Current Task の id>` がどの task か決まらない。鍵を外したので、task id を決める必要が無くなった。commit: 6a7e29ec |
| A10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が PR 本文に無い。PR 本文に足した。commit: なし（PR 本文） |
| A11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 足した条件の件数か「未測」と記録に残らない入力が PR 本文に無い。PR 本文の限界に「未測」と記録に残らない入力を書いた。commit: なし（PR 本文） |
| M1 | 方針メモ-1 | advisory | no | self-inflicted | design | accepted | 要約: なし（A1〜A3 の直し方を決めた相談。Opus・Fable とも、鍵をやめて行を止まる遷移に結びつける案を推した。割れたのは A3 の写す値だけで、Fable の案を採った） |
| B1 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | § 事前回答 4 が元の steering で後から引き上げた自走上限を後続 Stage に写し、本人が許していない後続 Stage の PR を自走でマージしうる。行の値と元の今の値が違えば `PR 作成まで` で写す形にした（引き上げは届かず、引き下げは届く）。commit: 5e634964 |
| B2 | 独立-2 | medium | yes | self-inflicted | approval-path | fixed | 「0 本なら止まる」が欠けた行を補わず、2 回目の到達を委任先が判断しうる。0 本なら main が行を書いてから止まる形にした。commit: 5e634964 |
| B3 | 独立-2 | medium | no | self-inflicted | product | fixed | remediation の遷移を書く gdd-systematic-debugging に `上限到達:` 行を書く指示が無く、この経路で委任の 1 回目に止まる（依頼の C1 が残る）ので直した。commit: 5e634964 |
| B4 | 独立-2 | low | no | self-inflicted | product | fixed | rollback-patterns の書く側の列挙に worker 経由の統合する main が無い（止まる側）。直す commit に同じ 1 句を入れた。commit: 5e634964 |
| B5 | 独立-2 | low | no | self-inflicted | product | accepted | § 4 で元の steering の自走上限が読めないときの扱いが無い。B1 の修正（読めなければ PR 作成まで）に含まれた |
| B6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 未リリースの前の断片（autonomy-delegation-choice）の `上限到達:` の書き手の記述が古いまま残る |
| B7 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 「0 本なら止まる」は未測のまま足した発火条件で、ユーザーの確認が依頼の原文に無い。ユーザーが残すことを確かめた（request.md に追記） |
| B8 | 独立-2 | advisory | no | inherited | product | accepted | PR 作成後の (3-f) 取り直し後の残りに `上限到達:` の語が割り当てられていない（止まる側。変更前から） |
| C1 | 独立-3 | medium | no | self-inflicted | product | fixed | state-machine と systematic-debugging の `remediation-loop-limit` を書く条件が 5/5 の hard cap などにも当たり、委任した 1 回目で止まる（依頼の C1 が残る）。方式転換のトリガーを名指しする形にした。commit: 1551aeed |
| C2 | 独立-3 | medium | no | self-inflicted | product | fixed | § 事前回答 4 の写し方で、元の steering の引き上げで後続 Stage が行の値より下がる（依頼の B2 が後続 Stage で残る）。引き下げの行が無ければ行の値で写す形にした。commit: 1551aeed |
| C3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片に `実装完了まで` と読めないときの扱いが抜けていた。C2 の修正で書き直した。commit: 1551aeed |
| C4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「1 回目の書き落としは拾う」が、委任の前に着いた分を拾わないことを書いていない。commit: なし（PR 本文） |
| C5 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容 2 の書く側の列挙に worker 経由の統合する main が無い。commit: なし（PR 本文） |
| C6 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | systematic-debugging の本文と SKILL の本文の合計が、行の予算の上限ちょうどになっている |
| D1 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | § 事前回答 4 で読めないときに `実装完了まで` の例外が外れ、`PR 作成まで` に上がる。どの場合も `実装完了まで` を優先する形にした。commit: 9def7a74 |
| D2 | 独立-4 | high | yes | self-inflicted | approval-path | fixed | 引き下げを `自走上限の引き下げ:` 行だけで見分けるので、行を書かずに下がる経路（§ 4 の写し、human check の再承認）で行の値が戻る。差が引き上げの記録だけで説明できるときだけ行の値にし、それ以外は `PR 作成まで` にする形（既定の反転）にした。commit: 9def7a74 |
| D3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | state-machine の括弧が「Round 上限では `上限到達:` を書かない」とも読める（止まる側） |
| D4 | 独立-4 | low | no | self-inflicted | style | accepted | systematic-debugging の `上限到達:` の文が fail-closed の箇条に同居している |
| D5 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文の記述が規則と合わない。D1・D2 の修正で書き直した。commit: 9def7a74 |
| D6 | 独立-4 | advisory | no | inherited | product | accepted | 自走上限を名指しした事前回答の行は、引き上げた後も行の値で読まれて人に止まる（B2 の「委任」がこの行を含むかは確かめていない） |
| E1 | 独立-5 | high | yes | self-inflicted | approval-path | accepted | § 事前回答 4 の「差が引き上げの記録だけで説明できるか」は最後の引き上げの値しか見ず、記録の無い引き下げや前の Stage の引き下げの後に引き上げると、本人が下げた値より上の行の値が後続 Stage に写る。確かめの差分巡の 2 回目の後なので直さず、PR 本文の限界の先頭に書いてユーザーへ渡す |
| E2 | 独立-5 | low | no | self-inflicted | product | accepted | 行を書かずに human check の再承認で上げたとき、後続 Stage が `PR 作成まで` に下がる（止まる側。依頼の B2 と同じ向き） |
| E3 | 独立-5 | advisory | no | inherited | product | accepted | 同じ § 4 で、元の行を確かめられないときは着手せず止まるのに、元の値が読めないときは `PR 作成まで` で着手する |
