---
lane: L1
pr: 451
follow_up_of: 447
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fa56ca2b | 0 | 1 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | a3dfa134 | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | path の綴りのテストが検査を外しても通る commit: a3dfa134 |
| I1-2 | 独立-1 | low | no | self-inflicted | product | fixed | tasklist_parse の import が ImportError 以外の例外で落ちる commit: a3dfa134 |
| I1-3 | 独立-1 | low | no | self-inflicted | test-power | fixed | フェンスの一致のテストに長い閉じ・info つきの閉じが無い commit: a3dfa134 |
| I1-4 | 独立-1 | low | no | self-inflicted | test-power | fixed | block の一覧のテストが前方一致で、番号の順を確かめない commit: a3dfa134 |
| I1-5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 節の後ろの D-n のテストがほかの ### と区別しない commit: a3dfa134 |
| I1-6 | 独立-1 | low | no | self-inflicted | test-power | fixed | import の失敗のテストがほかの理由でも通る commit: a3dfa134 |
| I1-7 | 独立-1 | low | no | self-inflicted | product | accepted | 列挙: NFC・NFD の違う path が同じファイルに届く。閉じ方: 列挙（常時 High の適用範囲外の開いた入力のため、限界として受け入れた） |
| I1-8 | 独立-1 | low | no | self-inflicted | product | accepted | 列挙: 節の後ろの D-n の検査を、前方一致の --until・節の前の D-n・題つきの見出しの形で抜けられる。閉じ方: 列挙（同上） |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 節の後ろの D-n が確定文面でないときの案内が無い commit: a3dfa134 |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が変わらない挙動を Changed に書いている commit: a3dfa134 |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の改行の書き方が不正確 commit: なし（PR 本文） |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | path の規則の文言が / を全部禁じるように読める commit: a3dfa134 |
| I1-13 | 独立-1 | advisory | no | self-inflicted | product | accepted | --repo が repo の top-level でなくても動く |
| I1-14 | 独立-1 | advisory | no | self-inflicted | product | accepted | 大文字小文字だけが違うファイルを持つ repo の扱い |
| I1-15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 再確認の手順 3・4 で section_end の扱いが書かれていない |
| I1-16 | 独立-1 | advisory | no | self-inflicted | product | accepted | #### D-n の下のフェンスの扱い |
| I2-1 | 独立-2 | low | no | self-inflicted | test-power | accepted | 番号の順のテストが文書の順と区別できない |
| I2-2 | 独立-2 | low | no | inherited | test-power | accepted | verify の block の一覧のテストが部分一致のまま |
| I2-3 | 独立-2 | low | no | inherited | test-power | accepted | 節の後ろの D-n の検査のフェンスの外の条件をテストが固めていない |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | path の綴りのテストのコメントが 6 形の全部には当てはまらない |
| I2-5 | 独立-2 | low | no | inherited | doc-claim | accepted | 断片の Changed が 旧#447 にあった宣言の機能を変更として書いている |
| I2-6 | 独立-2 | advisory | no | self-inflicted | product | accepted | 宣言すると後ろの D-n の検査が外れ、文言が宣言を出口として勧めている |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Changed の説明が確定文面でない D-n の場合に追いついていない |
| I2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation の変わらないが照合できず、足したテストの列挙に漏れ |
