---
lane: L1+
pr: 597
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 96ee7e73 | 0 | 2 | 0 | 2026-10-28 |
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 96ee7e73 | 0 | 0 | 0 | 2026-10-28 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e0bd124a | 0 | 1 | 0 | 2026-10-28 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | 依頼の範囲 | fixed | 依頼の原文から外れた（観点 0）: 依頼が名指しした CRLF の low（F5-2）を、確認なしに限界へ回した。比べる点で改行をそろえて直す。commit: e0bd124a |
| I1-2 | 独立-1 | medium | no | self-inflicted | 依頼の範囲 | accepted | F5-3〜F5-10 を行き先を書かずに外した。依頼は全件とも主な 2 つとも読める。全件の読みで進め、F5-3・F5-4・F5-5・F5-8・F5-9 を直し、F5-6・F5-7・F5-10 は限界に書いた。ユーザーが全件の読みと F5-6・F5-7 を限界のままにすることを選んだ |
| I1-3 | 独立-1 | low | no | self-inflicted | 文書の主張 | fixed | PR 本文の限界の行に種類（依頼より狭い）が無い。commit: なし（PR 本文） |
| I1-4 | 独立-1 | low | no | self-inflicted | テストの検出力 | accepted | 足したテストの assert が、どの層が止めたかを確かめない |
| I1-5 | 独立-1 | low | no | self-inflicted | テストの検出力 | accepted | 多重集合の比較を集合の比較に変える退行は、足したテストでは落ちない |
| I1-6 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | 変更断片が、数の比較への退行で落ちるのは入れ替わる形の 1 件だけであることを書いていない |
| I1-7 | 独立-1 | low | no | self-inflicted | 文書の主張 | accepted | テストの docstring が 2 層と書いたまま |
| M-1 | 方針メモ | advisory | no | self-inflicted | 改行の扱い | accepted | 設計: 変える（書き込み前と後を別の読み方で読む）。Opus は比べる点で両側の改行をそろえる形、Fable は書き込み前を read_regular_text で読む形を推した。Edit ではどちらでも閉じる（全文の Write は既にある risk-low の行も追加分に入り、改行によらず 1 層目が止める）。比べる点 1 か所でそろえれば読み方が増えても再発しないので、前者を採った。範囲は 2 本とも F5-2〜F5-5・F5-8・F5-9 を直し、F5-6・F5-7 を限界にする案で一致した |
| I2-1 | 独立-2 | medium | no | self-inflicted | 依頼の範囲 | accepted | 依頼を全件と読んだのに、F5-6（別名の key）と F5-7（空の old_string・後で置換する形）を確認の問いに入れずに限界へ回した。問いに足し、ユーザーが限界のままにすることを選んだ |
| I2-2 | 独立-2 | low | no | self-inflicted | deny の文面 | accepted | 親に権限が無いなどで止める経路にも UNPROJECTABLE_REASON（old_string が当たらない）の文が出て、原因と直し方を取り違える |
| I2-3 | 独立-2 | low | no | self-inflicted | 文書の主張 | accepted | state_write_projection.py の docstring の「どの検査も、先に edit_misses_old_string で止める」が言い過ぎ（Origin Session と risk_tier は別の形で扱う） |
| I2-4 | 独立-2 | low | no | self-inflicted | テストの検出力 | accepted | move のテストの assert が rc 2 だけで、Origin Session の検査が止めたことを固定しない |
| I2-5 | 独立-2 | advisory | no | self-inflicted | テンプレート外 | accepted | テンプレート外の記述あり: PR 本文の抜粋に前の PR の指摘 ID ごとの中身と対応がある。次の巡の前に抜粋から除く |
| I2-6 | 独立-2 | advisory | no | self-inflicted | 改行の扱い | accepted | 単独の CR を挟んだ risk\r-low は、改行をそろえた後は書き込み後の全文の層で行が割れて通る（read_text の読み手も risk と読むので実害なし） |
| I2-7 | 独立-2 | advisory | no | self-inflicted | 文書の主張 | accepted | 新しく止めるのは ENOENT・ENOTDIR 以外の OSError 全部で、断片と PR 本文の「親に権限が無い」より広い |
| I2-8 | 独立-2 | advisory | no | self-inflicted | テストの検出力 | accepted | CRLF の全文の Write のサブケースは追加分の層で止まり、改行をそろえる処理を通らない |
