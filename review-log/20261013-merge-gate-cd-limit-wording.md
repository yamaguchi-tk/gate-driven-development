---
lane: L1
pr: 481
follow_up_of: 468
amends: 20261013-merge-gate-relative-cd-limit.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 00cdc03d | 0 | 3 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c3633cfa | 0 | 0 | 0 | 2026-10-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c9df4c7f | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 冒頭の「止めるのは台帳と binding のときだけ」が、採った cd 先・payload の cwd に marker があればそこを root にすることを落とし、実装と逆になる。root の決め方と、marker 不在の出口に限ることを書いた commit: 7d1501ea |
| I1-2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | `-R` の値に `$` を含む形（binding を引かない）がどちらの形にも数えられていない。binding を引く条件を gdd_mg_binding_lookup・gdd_mg_binding_exec_root を正本に肯定形で書き、件数（0 件）を足した commit: 7d1501ea |
| I1-3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | git でない cwd の文が一般の挙動として書かれ、_mg_outside_gdd_merge で通る形・unresolvable は明示でも止まることと合わない。主語を項の形に限った commit: 7d1501ea |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 新しい断片の Summary が、cd の無い merge を外し、`$` を含む形を広く言い、SECURITY.md と食い違う commit: 7d1501ea |
| I1-5 | 独立-1 | low | no | self-inflicted | product | fixed | 列挙: 案内文と断片が、cd 先を採らない理由からバッククォートを落としている。案内・断片にバッククォートを足した（`cd --`・`..`・`builtin cd` は残る。案内は判定を変えない） commit: 7d1501ea |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | cd 先を採る条件の「コマンド全体」「1 つだけ」が、merge より後ろの cd・env について実装より厳しい。走査範囲 _through_merge_segment を正本に足した commit: 7d1501ea |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 書き直したコメントの「明示した merge を除いて止める」が unresolvable の形に当たらない commit: 7d1501ea |
| I1-8 | 独立-1 | low | no | self-inflicted | product | fixed | ユーザーが選んだ「実データ 2 件」を確かめずに消している。今の測り方で 3 件（43 件の内数）と書いた commit: 7d1501ea |
| I1-9 | 独立-1 | low | no | self-inflicted | product | fixed | 承認の確かめ方が書かれていない。transcript でユーザーの発言を読んだことを書いた commit: 7d1501ea |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「GDD の外の正当な merge（11 件）」に確かめ方が無い。GDD の merge かは確かめていないと弱めた commit: 7d1501ea |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「cd なし…binding を引き」が、binding の受理条件を落として広く言い切っている commit: なし（PR 本文） |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界 2 が、件数の変わった理由として数える形の定義の変更を書いていない commit: なし（PR 本文） |
| I1-13 | 独立-1 | low | no | inherited | product | fixed | repo-root-unresolvable の案内の binding の句が、git の外の cwd では成り立たない。cwd が git repo のときと条件を付けた commit: 7d1501ea |
| I1-14 | 独立-1 | low | no | self-inflicted | product | fixed | 書き換えた 旧#468 の断片に、cd 先に marker があることの条件が無い commit: 7d1501ea |
| I1-15 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 新しい断片の Validation に、案内文の構造を検査する test_merge_gate_hook_block_reason_quality.py が無い。足した commit: 7d1501ea |
| I1-16 | 独立-1 | advisory | no | self-inflicted | style | fixed | pr-target-unresolvable の案内で、cd を先頭に書く形と chdir を分ける形が並んで読み取りにくい。選択肢として書き分けた commit: 7d1501ea |
| I1-17 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 20261012-pr-ledger-limit-followup.md の「止まり続ける」が binding の条件を書いていない（差分と無関係） |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 列挙: binding を引く条件が、gdd_mg_binding_exec_root の「cd 先が cwd と同じ repo」を落とし、番号だけで別 repo へ絶対パスで cd する形が列挙に無い |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 列挙: repo-root-unresolvable の案内の binding の句が、別 repo の worktree への cd と git の外の cwd では成り立たない |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 列挙: cd 先を採る条件の「だけ」に、heredoc 本文の $、pushd などの cwd を変える語、切り出せない形の走査範囲の反例がある |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 旧#468 の断片の env の範囲が「コマンド」で、SECURITY.md の「segment まで」と食い違う |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 列挙: hook のコメントが binding を引かずに通る形を 2 つに限り、-R の値の $・別 repo への cd を挙げていない |
| I2-6 | 独立-2 | low | no | inherited | doc-claim | accepted | SECURITY.md:109 と :274 が、binding を引く条件を別々の集合で書いている |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の目的の主語と、pr-target-unresolvable の chdir の句の変更が差分と合わない commit: なし（PR 本文） |
| I2-8 | 独立-2 | low | no | self-inflicted | product | fixed | 項の主語を、ユーザーが選んだ「parser が対象を決められない形の merge」から「binding を引けない形」に読み替えた。見出しをユーザーの語に戻し、含む形を挙げた commit: 146ac981 |
| I2-9 | 独立-2 | low | no | inherited | doc-claim | accepted | 列挙: pr-target-unresolvable の案内が、AC-18 の本体形（marker のある root から別 repo へ cd）では打ったコマンドの形を返し、止まり続ける |
| I2-10 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 実データの件数・fixture の結果に、測ったコマンドや場所が無く再現できない |
| I3-1 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 見出しの「parser が対象を決められない形（cd 先を採らない形・-R の値の $ を含む）」が、本文の parser の定義（unresolvable）と食い違う |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 見出しの範囲が、本文が書く binding を引かずに通る形（GH_REPO・origin 以外の remote・host つきの -R・別 repo への cd）を含まない |
