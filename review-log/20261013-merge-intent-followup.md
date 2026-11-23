---
lane: L1+
pr: 455
follow_up_of: 448
amends: 20261013-merge-intent-vs-merge-gate.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 4ee07068 | 0 | 0 | 0 | 2026-10-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 55323936 | 0 | 1 | 0 | 2026-10-13 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 1d0a79ae | 0 | 0 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 7ad5ffad | 0 | 0 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | be6b1685 | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | advisory | no | inherited | design | accepted | 採用: 5 項目を方針メモどおりに直し、encode の検査のコメントを U+DC80〜DCFF に限る書き方にし、記録先の陽性対照のテストを足し、置き換えた待機スクリプトのパスを shlex.join の外で組む |
| I1-1 | 独立-1 | medium | no | self-inflicted | test-coverage | fixed | list 形の本文の連結を still_push_back と broken lines で固定していない。commit: 068d0cf1 |
| I1-2 | 独立-1 | low | no | self-inflicted | test-coverage | fixed | 待機スクリプトのパスの置き換えを、理由文を組む入口から確かめていない。commit: 068d0cf1 |
| I1-3 | 独立-1 | low | no | self-inflicted | test-coverage | fixed | 空のリスト・text の無いリスト・content の無い is_error の形がテストに無い。commit: 068d0cf1 |
| I1-4 | 独立-1 | low | no | self-inflicted | test-coverage | fixed | `CODES="${CODES%, }"` を文字列の有無だけで見ていて、wait だけの拒否の実際の文を判定に当てていない。commit: 068d0cf1 |
| I1-5 | 独立-1 | low | no | self-inflicted | docs | fixed | hooks.json の description に `UTF-8,,` の二重カンマ。commit: 4a4b4094 |
| I1-6 | 独立-1 | low | no | self-inflicted | docs | fixed | encode の検査のコメントが本番の起動を PYTHONUTF8=1 と書いている（実際は -X utf8）。commit: 4a4b4094 |
| I1-7 | 独立-1 | low | no | inherited | docs | fixed | encode できない理由文のテストのコメントが本番の仕組みと合わない。commit: 068d0cf1 |
| I1-8 | 独立-1 | low | no | self-inflicted | docs | fixed | state-machine.md と理由文が「拒否」と書き、空本文・encode の条件を書いていない。commit: 4a4b4094 |
| I1-9 | 独立-1 | low | no | self-inflicted | docs | fixed | 新しい断片が変更と前の断片の補足を混ぜ、PR を特定できない形を重複して書いている。commit: 4a4b4094 |
| I1-10 | 独立-1 | low | no | self-inflicted | docs | fixed | PR 本文の限界の、本文が空の is_error の実測の書き方。commit: なし（PR 本文） |
| I1-11 | 独立-1 | low | no | self-inflicted | intent | fixed | 依頼の「変更断片の文言をそろえる」を、前の断片の書き換えでなく新しい断片の補足で代えた。ユーザーが B（検査に例外を足して書き換え）を選び、amends: の宣言で前の断片を直した。commit: e02fa62d |
| I1-12 | 独立-1 | low | no | inherited | wiring | accepted | wait_loop_gate.py の deny の文が待機スクリプトのパスを判定せずに載せ、Stop hook と書き方が分かれている。独立-2 で依頼の範囲の外（wait-loop-gate）と指摘され、変更を戻した（commit: 51b96ca5）。wait-loop-gate の deny の文の置き換えは限界の節に書く |
| I1-13 | 独立-1 | advisory | no | self-inflicted | docs | accepted | PR 本文のテストの項が、締め切りのテストの assert を広げたことを書いていない（PR 本文に書き足す） |
| I1-14 | 独立-1 | advisory | no | self-inflicted | docs | accepted | placeholder `<plugin>` を shell に貼るとリダイレクトになる（PR 本文に列挙） |
| I1-15 | 独立-1 | advisory | no | self-inflicted | design | accepted | 理由文の値の検査のテストが merge gate の文の契約のクラスに置かれている（PR 本文に列挙） |
| M2-1 | 方針メモ-2 | advisory | no | self-inflicted | design | accepted | 採用: ユーザーが B を選んだ。Opus の推奨どおり、version-not-consumed.sh に review-log の amends: の宣言を読む例外を足す（この branch で足した断片と対の review-log・merge-base に無い・HEAD から読む・NAME_RE と merge-base にある名前・type: を変えない）。2026-09-23 の判断（例外を足さずリリース時に直す）を変える |
| I2-1 | 独立-2 | low | no | self-inflicted | product | fixed | wait-loop-gate の deny の文にまで置き換えを広げ、依頼の範囲を広げた。wait_loop_gate.py の変更を戻した。commit: 51b96ca5 |
| I2-2 | 独立-2 | low | no | self-inflicted | product | fixed | hooks.json の description に、宣言のパスを相対で出す場合が無い。commit: 51b96ca5 |
| I2-3 | 独立-2 | low | no | self-inflicted | product | fixed | Stop hook が wait_loop_gate を読み込み時に import する。変更を戻して import が無くなった。commit: 51b96ca5 |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文が、理由文に入っていない条件まで「そろえた」と書いている。commit: なし（PR 本文） |
| I2-5 | 独立-2 | low | no | self-inflicted | test-power | accepted | 読めない宣言のテストの needle が lost の FAIL 文でも満たされ、宣言を黙って無視する変異が通る（PR 本文の限界に書く） |
| I2-6 | 独立-2 | low | no | self-inflicted | test-power | accepted | 壊れた review-log のテストが except BaseException のため常に通る（PR 本文の限界に書く） |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片の読めない宣言の列挙が実装より狭く、「前の版の断片」の語と、リリース後に消える断片のパスを書いている（PR 本文の限界に書く） |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | encode の条件が 2 つの断片に重複している（PR 本文の限界に書く） |
| I2-9 | 独立-2 | low | no | self-inflicted | style | fixed | WAIT_SCRIPT の行を消してコメントが宙に浮いた。変更を戻して元に戻った。commit: 51b96ca5 |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | VERSIONING.md の層 B の表とスクリプト冒頭に、断片の書き換えの禁止と amends の例外が無い（PR 本文の限界に書く） |
| I3-1 | 独立-3 | low | no | inherited | product | accepted | wait-loop-gate の deny の文は待機スクリプトのパスを置き換えず、Stop hook と書き方が分かれる（PR 本文の限界に書く） |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「encode の条件は 2 つの断片に重複」が今の断片と合わない。commit: なし（PR 本文） |
| I3-3 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 「制御文字・surrogate」は Cf・Zl・Zp も含む判定の略し方（PR 本文に列挙） |
