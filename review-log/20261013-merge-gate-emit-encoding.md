---
lane: L1+
pr: 458
follow_up_of: 449
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 5e9d84ec | 0 | 0 | 0 | 2026-10-13T13:40+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3bb660b195f712d38d4c1e8898244afabf45824d | 2 | 1 | 2 | 2026-10-13T14:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 3bb660b195f712d38d4c1e8898244afabf45824d | 0 | 0 | 0 | 2026-10-13T15:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c5bfc92ef077f650b3db780c46443fef7eb00a87 | 1 | 1 | 1 | 2026-10-13T16:10+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | c5bfc92ef077f650b3db780c46443fef7eb00a87 | 0 | 0 | 0 | 2026-10-13T16:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ-1 | advisory | no | self-inflicted | design | fixed | Opus は emit を pre-push gate と同じ形（surrogateescape、だめなら backslashreplace、stdout.buffer）にし、payload の cwd を書く print も同じ形にするよう推した。依頼の行の手段（backslashreplace だけ）と違うので確かめ、ユーザーは Fable の意見（同じ推奨）を聞いて「pre-push gate にそろえる」を選んだ。cwd の print は、実行すると直す前は止まり直した後は通る（解決できない cwd は marker の無い経路で通る既存の挙動）と分かったので、変えずにテストで固定した。transcript の Bash 563,559 件に書けない文字は 0 件。commit: なし（方針） |
| I1 | 独立-1 | high | yes | inherited | ledger-match | fixed | 列挙: 解決できない payload の cwd を持つ merge は、marker の無い経路で番号が照合から落ちて通る。cwd 欄つきの merge は transcript 564,392 件中 0 件で、方針メモ-2 の既定は (b) だったが、ユーザーが「617 行も変え、穴も直す」を選んだ。実行先を決められない -R 無しの番号は、理由を問わず番号だけで照合する。commit: 66487974 |
| I2 | 独立-1 | high | yes | inherited | fail-open | accepted | 列挙: pre-PR gate の本文の機密検査が、本文に high surrogate があると print の例外で空の本文を見て通る（run-pre-pr-gate-hook.sh:531 ほか）。別の hook の既存の穴。書けない文字を含むコマンドは transcript 563,559 件中 0 件。方針メモ-2 で (b)。限界の節の先頭に書く |
| I3 | 独立-1 | medium | no | self-inflicted | product | fixed | 依頼とのずれ: 選んだ案の説明の「617 行の print も同じ形にする」を外していた。ユーザーに確かめ、617 行を同じ形にし、I1 も直した。commit: 66487974 |
| I4 | 独立-1 | low | no | self-inflicted | test-power | fixed | \udc80 と PYTHONIOENCODING=utf-8:strict の組は、hook の python が -I で起動するので届かず、判別力が無い。組を外し、コメントを直した。commit: da2ce56b |
| I5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | byte で書く根拠を PYTHONUTF8 にしていた（-I で読まれない。UTF-8 mode は -X utf8 で、emit は自分で surrogateescape する）。テストの docstring と PR 本文を直した。commit: da2ce56b |
| I6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「書けない文字だけ backslashreplace」は実際は行全体。断片と PR 本文を直した。commit: da2ce56b |
| I7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | marker のある経路で parse-error から通常の判定に変わることが書かれていない。断片と PR 本文に足した。commit: da2ce56b |
| I8 | 独立-1 | low | no | inherited | product | next-pr | review-followup の nudge hook の emit が以前の形のまま（block しない hook） |
| I9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 0 件の根拠のコマンドが再現できない。PR 本文に数え方を書いた。commit: なし（PR 本文） |
| P2 | 方針メモ-2 | advisory | no | self-inflicted | design | fixed | I1・I2（閉じ方: 列挙）と I3。Opus は I1・I2 を (b)、I3 は「617 行は変えない」を推してユーザーに確かめるよう推した。main の案と同じ。ユーザーは「617 行も変え、穴も直す」を選び、I1 は直した。commit: 66487974 |
| J1 | 独立-2 | high | yes | self-inflicted | ledger-match | accepted | marker の無い git cwd で、origin 以外の remote に gh-resolved がある fork の clone、origin の gh-resolved が別 repo を指す clone、origin の無い clone から gh pr merge <番号> を打つと、台帳の PR でも通る（_exec は決まるが repo が決まらない else 枝）。main から同じ挙動で、20260918 の断片 :80 で受け入れ済み。台帳の root 7 件と手元の repo に該当 0 件。安全策 4 で止めたので直さず、限界の節の先頭に書く |
| J2 | 独立-2 | medium | no | self-inflicted | test-power | accepted | 新しいテストは payload の cwd の書き出し（616 行）を元に戻しても落ちない。止めたので直さず、限界に書く |
| J3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の 10-11 行が、書けない文字を含む payload の cwd の前後の挙動と合っていない。止めたので直さず、限界に書く |
| J4 | 独立-2 | advisory | no | self-inflicted | product | accepted | 選択肢の説明の「書けない文字だけ」と、実装の「行全体を backslashreplace」が違う（判定は変わらない） |
| J5 | 独立-2 | advisory | no | inherited | product | accepted | pre-PR gate は payload の cwd を古い形の print で読み、merge gate と扱いがそろっていない |
| J6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 497 行と _mg_exec_root のコメントが、_exec が空になる条件を全部は書いていない |
| P3 | 方針メモ-3 | advisory | no | self-inflicted | design | accepted | 安全策 4 の発火（ledger-match の high が独立-1・独立-2）。main の案「止める」に Opus も同意した。J1 は依頼の外で、直すと止める範囲を広げるのでユーザーの確認が要るが、止めるのは受け入れ済みの限界を変えないので内部の相談で決めた（2026-10-08 のユーザー決定）。J1〜J6 は直さず PR 本文に書き、merge-ready とは書かない |
