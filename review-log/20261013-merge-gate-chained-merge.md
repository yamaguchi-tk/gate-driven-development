---
lane: L1+
pr: 449
follow_up_of: 438
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 775988f7df05247017ed83a9bd33b7d0fcb6e1cc | 0 | 0 | 0 | 2026-10-13T10:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8b5099e3 | 3 | 1 | 3 | 2026-10-13T12:10+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 8b5099e3 | 0 | 0 | 0 | 2026-10-13T12:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | cbbe48901420b835ba941a31a4078ef1278e2c48 | 4 | 2 | 4 | 2026-10-13T11:55+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | cbbe48901420b835ba941a31a4078ef1278e2c48 | 0 | 0 | 0 | 2026-10-13T12:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ-1 | advisory | no | self-inflicted | design | fixed | 方針は照合案で、ユーザーが Issue の棚卸しの AskUserQuestion で選んだ。Opus は採用を推し、足す 6 点（区切りは展開で切り set -u で落ちない、cd を挟む形は番号だけで照合、zsh の再走査は浅いコピーに頼らない、例外の経路の扱いを書く、組を記録してから値を戻す、契約テストの形）を挙げ、すべて採った。env -S の上限を超える形は、解析が merge を読む前に打ち切るので組が取れず、今までどおり（限界に書く）。commit: なし（方針） |
| F1 | 独立-1 | high | yes | self-inflicted | ledger-match | fixed | 列挙: 改行で区切った連結 merge は 1 本の merge（位置引数 2 つ）になり、最後の番号しか照合しない。方針メモ-2 で (a)。transcript に本物の形が 2 件。位置引数 2 つ以上の merge は読めた番号・URL を全部組に残し、番号は repo を決めない印で番号だけで照合する。hook は分岐をなくして組だけで照合する。誤 block の件数は未測（transcript の時点の台帳を復元できない）。commit: cbbe4890 |
| F2 | 独立-1 | high | yes | self-inflicted | ledger-match | fixed | 長い値で新しいループの展開が 2 乗に効き、root 未解決の経路で timeout で通りうる。emit の前に repo・URL を 512 文字、番号を 19 桁で替え、組を重複なしにした。commit: cbbe4890 |
| F3 | 独立-1 | high | yes | self-inflicted | ledger-match | fixed | slash の無い未展開の -R（-R "$REPO"）は番号が照合から落ちる。owner/repo に解決しない -R は番号だけで照合する。commit: cbbe4890 |
| F4 | 独立-1 | medium | no | self-inflicted | product | fixed | cd を含む連結 merge を cd の位置によらず番号だけで照合していた。$3 をなくし、先頭の cd は cd 先の origin で組み、間・後ろの cd は既存の例外で番号だけにした。commit: cbbe4890 |
| F5 | 独立-1 | low | no | self-inflicted | test-power | fixed | cd を挟むテストが番号だけの照合を確かめていない。origin が別 repo の clone から打つ形にし、先頭の cd のテストも足した。commit: fdbdcc9e |
| F6 | 独立-1 | low | no | self-inflicted | test-power | fixed | zsh の読みの組を足す行を固定するテストが無い。連結した形を足した。commit: fdbdcc9e |
| F7 | 独立-1 | low | no | self-inflicted | test-power | fixed | 区切り文字のテストが置き換えを外しても通る。台帳の番号を区切り文字の値に入れる形を足した。commit: fdbdcc9e |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片・PR 本文が改行の形・cd の範囲を実際と違って書く。断片と PR 本文を直した。commit: cbbe4890 |
| F9 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 件数を測ったコマンドが PR 本文に無い。目的の節に書いた。commit: なし（PR 本文） |
| F10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | env -S の上限超過の節のコメントの「先に読んだ ledger_targets は残す」は、その節では起きない |
| F11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 出口の照合のコメントが連結 merge の組に触れていない |
| F12 | 独立-1 | advisory | no | inherited | doc-claim | fixed | 未リリースの 0918 の断片が連結 merge は台帳の PR でも通ると書いたまま。新しい断片に、その限界がなくなると書いた。commit: cbbe4890 |
| P2 | 方針メモ-2 | advisory | no | self-inflicted | design | fixed | F1〜F4 の扱い。Opus は F1 を (a) で閉じる（案 A を、全番号を番号だけ・hook の分岐をなくす・印は F3 の分岐に乗せる、の 3 点で直す）、F2 は 3 欄すべてに上限、F4 は $3 をなくすと推奨し、main の案と食い違いは無く、すべて採った。規定の「改行は受理しない」より依頼の原文（GDD 以外の連結 merge は止めない）を優先した。commit: cbbe4890 |
| G1 | 独立-2 | high | yes | self-inflicted | ledger-match | accepted | 列挙: 先頭の cd の origin で組む仕組みが、cd の直後の単独の & やパイプを見分けない。`cd /unrelated & gh pr merge 6 && gh pr merge 7` などで、merge は checkout で走るのに cd 先の origin と組んで外れ、通る。cd 先を読めた merge 230 件に該当 0 件。安全策 4 で「止める」を選んだので直さず、限界の節の先頭に書く |
| G2 | 独立-2 | high | yes | self-inflicted | ledger-match | accepted | 台帳の照合を ledger_targets だけにしたので、emit の途中の例外（cd 先の lone surrogate で UnicodeEncodeError）で組が空になり、marker の無い出口で unknown として通る。敵対的な形。直すなら stdout を backslashreplace にする 1 行。止めたので直さず、限界の節の先頭に書く |
| G3 | 独立-2 | high | yes | self-inflicted | ledger-match | accepted | 位置引数が多い merge（数千個）は組の数に上限が無く、組ごとの fork で timeout して通りうる（未測）。敵対的な形。止めたので直さず、限界の節の先頭に書く |
| G4 | 独立-2 | high | yes | inherited | ledger-match | accepted | G1 と同じ原因が 1 本の merge にもある（`cd /unrelated & gh pr merge 7`）。前からある穴。止めたので直さず、限界の節の先頭に書く |
| G5 | 独立-2 | medium | no | self-inflicted | product | accepted | 依頼とのずれ: 番号だけの照合（merge の間・後ろの cd、改行区切り、解決しない -R）で GDD 以外の merge を止めうる。今の台帳での近似は 0 件。ユーザーが方針メモ-3 で「今の形を認める」を選び、.request.md に足した |
| G6 | 独立-2 | medium | no | self-inflicted | product | accepted | 依頼とのずれ: 1 本の merge の挙動も変えた（-R "$R" を番号だけで照合、値の上限、照合を組だけで行う）。ユーザーが方針メモ-3 で「今の形を認める」を選び、.request.md に足した |
| G7 | 独立-2 | low | no | self-inflicted | test-power | accepted | 重複の除去と 19 桁の上限を外しても落ちるテストが無い。止めたので直さず、限界に書く |
| G8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | テストの module docstring が「番号・URL が読めないときに組で照合する」のまま。止めたので直さず、限界に書く |
| G9 | 独立-2 | low | no | self-inflicted | style | accepted | _consume_merge_args の型注記が -> None のまま。止めたので直さず、限界に書く |
| G10 | 独立-2 | low | no | self-inflicted | style | accepted | 上限の 512 が python 側と bash 側の 2 か所で定義されている。止めたので直さず、限界に書く |
| G11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「1 本の merge は 1 組」「目安の行数にある」が実際と違う、0918 の断片の記述が新しい断片と同じ版の節に並ぶ。PR 本文は書き直した。断片は直さない。commit: なし（PR 本文） |
| P3 | 方針メモ-3 | advisory | no | self-inflicted | design | accepted | 安全策 4 の発火（ledger-match の high が独立-1・独立-2 の 2 巡）。Opus は「止める」を推し、main の案（続行して連結の形に絞り直す）と食い違ったので、Fable に信号 ① で相談した。Fable も「止める」と、F5・F6 は「今の形を認める」を推した。ユーザーは「止める」「今の形を認める」を選んだ。G1〜G4 は accepted にして限界の節の先頭に書き、merge-ready とは書かない |
