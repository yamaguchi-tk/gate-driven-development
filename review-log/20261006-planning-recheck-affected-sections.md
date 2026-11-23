---
lane: L1
pr: 391
follow_up_of: 390
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3c6d8e51 | 0 | 1 | 0 | 2026-10-06T22:52+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 97c12b98 | 0 | 1 | 0 | 2026-10-06T23:06+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | fixed | 引用を変えずに節の中身だけを直す処置では影響節が 0 件になり、同じ AC を引くほかの節が前の定義より範囲から外れる（ユーザーの指示で直した） commit: 97c12b98 |
| F2 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | grep の照合規則が無く、AC-1 で AC-10 などにも当たる。lint-ac.py の AC_ID_RE と切り出し方が違う |
| F3 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | 範囲で書いた引用（AC-1〜AC-5）は中の ID で grep しても当たらない |
| F4 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | 本文を変えた AC・引用を外した AC を決める前の版を、gate がどこから取るかが無い |
| F5 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | 影響節が 0 件のときの行が無く、列挙の抜けと 0 件を reviewer が見分けられない |
| F6 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | 参照: 行は影響節以外にも使うので、再入で計画 doc の参照: 行を並べると範囲が Round 1 に戻る |
| F7 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | 超過時の再実行は参照: 行を消すので、影響節も消える |
| F8 | 独立-1 | low | no | self-inflicted | 文言 | accepted | 「Round 1 で当て済み」「初回」など、再入でない Round の言い換えが残る |
| F9 | 独立-1 | advisory | no | self-inflicted | 計測 | accepted | 全差分巡の base が merge-base と違う（積み重ねた PR なので base は前の PR のブランチ） |
| F10 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 前の未リリースの断片に置き換えた定義が残る。リリースの dry-run でまとめる |
| F11 | 独立-1 | advisory | no | self-inflicted | 範囲の定義 | accepted | grep の対象に tasklist.md の AC 欄が入らない |
| G1 | 独立-2 | medium | no | self-inflicted | 範囲の定義 | accepted | 「変えた行が引く AC」では外した引用の AC と消した行の AC が入るか読めない。agent 定義に括弧が無く references と食い違う |
| G2 | 独立-2 | low | no | self-inflicted | 範囲の定義 | accepted | 直した AC の行がほかの AC を引くとき、主節と「ほかの AC を引く節は入れない」の括弧が食い違う |
| G3 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 2 つの括弧の主語（AC と節）がそろわず、断片と言い方が違う |
| G4 | 独立-2 | low | no | self-inflicted | 範囲の定義 | accepted | 直した行に AC ID が無いと影響節が出ない（見出しでだけ AC を引く書き方） |
| G5 | 独立-2 | low | no | self-inflicted | 文言 | accepted | RED-GREEN の場面が、この修正で足した挙動（引用を変えない直し・引用を外す直し）を通っていない |
| G6 | 独立-2 | low | no | self-inflicted | 範囲の定義 | re-reported | grep の照合規則（AC-3 が AC-30 にも当たる）。F2 と同じ |
| G7 | 独立-2 | low | no | self-inflicted | 範囲の定義 | re-reported | 前の版の出どころが無く、変えた行を確かめられない。F4 と同じ |
| G8 | 独立-2 | advisory | no | inherited | 文言 | re-reported | 前の断片に節単位の古い定義が残る。F10 と同じ |
