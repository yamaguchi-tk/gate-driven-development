---
lane: L1
pr: 477
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 682a3121 | 0 | 3 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8b4cbcd5 | 0 | 3 | 0 | 2026-10-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | bc71bcbe | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | 固定行に変換表の具体化の行数が無く、依頼の B1(a)（決まらない行数と具体化の行数を突き合わせる）から外れていた。質問の上限も無かった。（変換表の具体化 <m> 行）を足し、質問は 2 個の上限に数えるとした commit: 83d57b40 |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | express からの昇格経路では human check を開き直さず、固定行も質問も届かない。固定行を worklog.md にも書き、昇格経路では worklog.md にだけ残ると書いた commit: 83d57b40 |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 質問にした行は # しかユーザーに見えない。質問の文を # つきで固定行の下に載せると書いた commit: 83d57b40 |
| I1-4 | 独立-1 | low | no | self-inflicted | product | fixed | # ごとの行き先が steering に残らず、human check を作り直す側が再現できない。worklog.md にも書くとした commit: 83d57b40 |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界「表示文を機械で検査する仕組みは無い」が、Stop hook に配線された lint-hitl-display-integrity と食い違う commit: なし（PR 本文） |
| I1-6 | 独立-1 | low | no | self-inflicted | product | accepted | 突き合わせが unavailable のときの固定行の値が決まっていない |
| I1-7 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | <n> の数え方が節の行の数で、# の数と食い違いうる。要件の表の判定の行の数にした commit: 83d57b40 |
| I1-8 | 独立-1 | low | no | self-inflicted | product | accepted | 固定行の行き先が変換表の扱いの 5 値（未解決を含む）と対応していない |
| I1-9 | 独立-1 | low | no | self-inflicted | product | accepted | compact に固定行の形が無く、request-crosscheck.md の名前も消えた（runtime の推定 token の予算のため） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | product | fixed | PR 本文に B1(a) の名前と C-1・B3 の行き先が無い commit: なし（PR 本文） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が PR 本文の抜粋に無い commit: なし（PR 本文） |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | accepted | express からの昇格経路で決まらない行が worklog.md にだけ残り、ユーザーに届くのは実装の後。依頼の原文から外れた指摘なので、Fable に相談してユーザーに確かめ、「(b) で決める」を request.md に足した。開き直す条件は足さず PR 本文の限界に書く。昇格経路の文面は判断役の承認を経ないと止まる形に直した commit: 43642f9e |
| I2-2 | 独立-2 | medium | no | self-inflicted | product | accepted | 上限を超えた質問を具体化か延期にする扱いが、上限の正本（requirements-template.md:25 の超えたら理由を 1 行）と食い違う |
| I2-3 | 独立-2 | medium | no | self-inflicted | product | fixed | <m> が変換表の具体化の行を全部数え、スコープ由来の行が混ざると落ちた行を見つけられない（依頼の B1(a) の突き合わせの中心）。決まらない行から作る具体化の行の初期条件に # を付け、それだけを数えるとした commit: 43642f9e |
| I2-4 | 独立-2 | low | no | self-inflicted | product | accepted | 質問にした行をズレ確認に出す規定が、承認ポイントを二重に出さないという human-check-template.md:545 と食い違う |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文に上限を超えた分の扱いが無い |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片に上限を超えた分の扱いと昇格経路の扱いが無い |
| I2-7 | 独立-2 | low | no | inherited | product | accepted | 突き合わせが unavailable のときの固定行が決まっていない（I1-6 と同じ） |
| I2-8 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | <n> の「要件の表」がどのファイルの表か書いていない。request-crosscheck.md の要件の表と書いた commit: 43642f9e |
| I3-1 | 独立-3 | low | no | self-inflicted | product | accepted | <m> の数え方が、括弧（1 行に 2 つ載せたら 2）とラベル・断片・brainstorming（行の数）で食い違う。誤った合図の側に倒れる |
| I3-2 | 独立-3 | low | no | self-inflicted | product | accepted | <m> が数える「初期条件の先頭に # がある行」が crosscheck の # に限られず、Issue 番号で始まる完了条件も数えうる |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | brainstorming-steps.md の昇格経路の括弧が、委任の承認の機会があるように読める。延期・削除の行にも触れていない |
| I3-4 | 独立-3 | low | no | self-inflicted | product | accepted | 変換表のひな形（human-check-template.md:264）に #k <原文の語> の形が無い。誤った合図の側に倒れる |
| I3-5 | 独立-3 | advisory | no | self-inflicted | product | accepted | completion-reviewer の (2) は語で、human check は # で同じ変換表の行を照合する |
| I3-6 | 独立-3 | low | no | inherited | bookkeeping | accepted | unavailable のときの固定行が決まっていない（I1-6 と同じ） |
| I3-7 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が PR 本文の抜粋に無い（PR 本文の別の節に書く） |
