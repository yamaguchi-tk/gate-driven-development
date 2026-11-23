---
lane: L1
pr: 646
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5ba4acbd9abd5e3c4ab73d3fa9648ad4ed70f6cf | 0 | 5 | 0 | 2026-11-09 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6bdfc2fc2f27e4d288fa447e7e2381adb65ffc59 | 0 | 4 | 0 | 2026-11-09 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | f14e0cfec9adad940e53f354ffa64275090ab4fb | 0 | 1 | 0 | 2026-11-09 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 8148eac749cbe9a5ea3ccbd9d274961d606083c8 | 0 | 2 | 0 | 2026-11-09 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 4bea2152dc9fda94efa1f6f164899ab6e8215583 | 0 | 0 | 0 | 2026-11-09 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | input-scope | fixed | 発言を前のタスクの終わりで切っていた。依頼の「ユーザーの発言だけ」に合わせ、session の全部を渡す。commit: 59068a4e |
| I1-2 | 独立-1 | medium | no | self-inflicted | input-scope | accepted | 再開で発言がコマンドだけのとき、読み手が依頼を見ずに差なしと答える。残る形は開いている |
| I1-3 | 独立-1 | medium | no | self-inflicted | trigger | accepted | マーカーの引用だけでも起動する。提示でない Stop には起動しないとした PR 本文の文は直した |
| I1-4 | 独立-1 | medium | no | self-inflicted | doc | accepted | SECURITY.md の通信境界・state dir の列挙の文が新しい hook と合わない |
| I1-5 | 独立-1 | medium | no | self-inflicted | trial | accepted | 撤去の線はユーザーが推奨の案に決めた（request.md）。余計の記録先と判定の時機が残らない。PR 本文に問いを書く |
| I1-6 | 独立-1 | low | no | self-inflicted | display-form | fixed | 1 行だけの依頼が件数に上限のない 1 行ずつになっていた。先頭の項目と件数の 1 行にする。commit: 59068a4e |
| I1-7 | 独立-1 | low | no | self-inflicted | display-form | fixed | 依頼に無い未実施の行を見せていた。理由は記録だけに残す。commit: 59068a4e |
| I1-8 | 独立-1 | low | no | self-inflicted | display-form | accepted | 原文として出す引用を照合していない。照合を足して測ると、過去の表示 15 件で言い換えは 0 件、当たった 1 件は太字の記号の違いだったので、足さない |
| I1-9 | 独立-1 | low | no | self-inflicted | trigger | accepted | Stop hook が認める tool result 側と state.md の経路の human check では動かない |
| I1-10 | 独立-1 | low | no | self-inflicted | trigger | accepted | 押し返しで人に渡らない停止でも起動する |
| I1-11 | 独立-1 | low | no | self-inflicted | failure | accepted | 記録に書けないと判定の結果を捨てる |
| I1-12 | 独立-1 | low | no | self-inflicted | failure | accepted | 起動前に落ちると記録も残らない |
| I1-13 | 独立-1 | low | no | self-inflicted | test-power | accepted | MCP の遮断の引数を消しても落ちるテストが無い |
| I1-14 | 独立-1 | low | no | self-inflicted | test-power | accepted | 記録の _redact を消しても落ちるテストが無い |
| I1-15 | 独立-1 | low | no | self-inflicted | test-power | accepted | 未実施の理由と session の区別を固定していない |
| I1-16 | 独立-1 | low | no | self-inflicted | test-power | accepted | claude が無い case が開発機では本物を起動しうる |
| I1-17 | 独立-1 | low | no | self-inflicted | doc | accepted | README の /gdd-dev なしで動く表と hooks.json の description に載っていない |
| I1-18 | 独立-1 | low | no | self-inflicted | doc | accepted | fixed-models.md にこの起動のモデルが無い |
| I1-19 | 独立-1 | low | no | self-inflicted | doc | accepted | 断片の Affected Files と Validation が Policy と合わない |
| I1-20 | 独立-1 | low | no | self-inflicted | doc | fixed | PR 本文の読んでいない件数が表示の件数と合わない。同じ入力の再生の数に直した。commit: なし（PR 本文） |
| I1-21 | 独立-1 | advisory | no | self-inflicted | doc | accepted | 実際の CLI で動かした確認が PR 本文に無い。確認したことに書く |
| I1-22 | 独立-1 | advisory | no | self-inflicted | doc | accepted | 発火条件の数が目的の節に無い。目的の節に移す |
| I1-23 | 独立-1 | advisory | no | self-inflicted | input-scope | accepted | origin を書かない版の transcript は読まない |
| I1-24 | 独立-1 | advisory | no | self-inflicted | process | accepted | テンプレート外の記述あり（PR 本文の抜粋の確認したこと）。次の巡の前に除く |
| I2-1 | 独立-2 | medium | no | self-inflicted | trial | accepted | 撤去の条件はユーザーが推奨の案に決めた（request.md）。余計の記録先と読み方も無い。PR 本文に問いと読み方を書く |
| I2-2 | 独立-2 | medium | no | self-inflicted | display-form | fixed | 引用の照合が忠実な引用にも不一致と出し、件数も測っていない。測って表示を外した。commit: d38b7423 |
| I2-3 | 独立-2 | medium | no | self-inflicted | test-power | accepted | main の except に入るテストが無い |
| I2-4 | 独立-2 | medium | no | self-inflicted | display-form | fixed | verbatim の判定をテストが固定していない。判定を外した。commit: d38b7423 |
| I2-5 | 独立-2 | low | no | self-inflicted | failure | accepted | 記録に書けないと差があっても表示が消える |
| I2-6 | 独立-2 | low | no | self-inflicted | input-scope | accepted | 前のタスクの発言も依頼の下に入る。PR 本文の限界に書く |
| I2-7 | 独立-2 | low | no | self-inflicted | input-scope | accepted | 40,000 字を超えると発言の途中を省く。PR 本文の限界に書く |
| I2-8 | 独立-2 | low | no | self-inflicted | failure | accepted | transcript が読めないときと例外は記録も残らない |
| I2-9 | 独立-2 | low | no | self-inflicted | display-form | accepted | 空の引用が先頭だと後ろの項目を隠す |
| I2-10 | 独立-2 | low | no | self-inflicted | display-form | fixed | ラベルの有無が記録に残らない。ラベルを外した。commit: d38b7423 |
| I2-11 | 独立-2 | low | no | self-inflicted | doc | accepted | hook の入口のコメントが 1 行ずつのまま |
| I2-12 | 独立-2 | low | no | self-inflicted | doc | accepted | 新しい表記が README と断片に無い（件数の表記だけ残る） |
| I2-13 | 独立-2 | low | no | self-inflicted | doc | accepted | 断片の Affected Files に SECURITY.md が無い |
| I2-14 | 独立-2 | low | no | self-inflicted | test-power | accepted | not_run のテストが理由の中身を見ない |
| I2-15 | 独立-2 | advisory | no | self-inflicted | display-form | accepted | 依頼の形に無い（ほか N 件）を足している。問いと一緒に示す |
| I2-16 | 独立-2 | advisory | no | self-inflicted | failure | accepted | 何も出ないとき差なしか未実施か見分けられない。PR 本文の限界に書く |
| I2-17 | 独立-2 | advisory | no | self-inflicted | display-form | accepted | 見せる 1 件は読み手が最初に挙げた項目 |
| I2-18 | 独立-2 | advisory | no | self-inflicted | doc | accepted | 費用の書き方が PR 本文と文書で違う |
| I2-19 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | テスト名の never_blocks に対応する assert が無い |
| I3-1 | 独立-3 | medium | no | self-inflicted | display-form | accepted | ユーザーが照合しない案に決めた（request.md）。表示の引用は読み手の写しで原文と照合しない。依頼の形の <依頼の原文> を厳密に読むかは 2 通りに読める。過去の 15 件で言い換えは 0 件。PR 本文に問いを書く |
| I3-2 | 独立-3 | low | no | self-inflicted | doc | accepted | 引用を照合していないことを文書に書いていない。PR 本文の限界に書く |
| I3-3 | 独立-3 | low | no | self-inflicted | test-power | accepted | 発言に無い引用をどう出すかを固定するテストが無い |
| I3-4 | 独立-3 | low | no | inherited | display-form | accepted | 空の引用だけの答えで中身の無い行が出る |
| I3-5 | 独立-3 | low | no | inherited | doc | accepted | hook の入口のコメントが 1 行ずつのまま |
| I3-6 | 独立-3 | advisory | no | inherited | doc | accepted | 費用の書き方が PR 本文と文書で違う |
| I3-7 | 独立-3 | advisory | no | inherited | trial | accepted | 撤去の条件が未決のままマージすると依頼から外れる。ユーザーが推奨の案に決めた（request.md） |
| I4-1 | 独立-4 | medium | no | self-inflicted | failure | accepted | 読めない項目が表示からも記録からも跡なく消える。過去の答え 61 項目では 0 件 |
| I4-2 | 独立-4 | medium | no | self-inflicted | doc | accepted | 読み手の文が測った文と同じだと照合できない。sha256 を notes に並べて書いた |
| I4-3 | 独立-4 | low | no | self-inflicted | display-form | fixed | 行の形が依頼で指した案と違っていた。案の形に合わせた。commit: 8d954e5a |
| I4-4 | 独立-4 | low | no | self-inflicted | trial | accepted | ユーザーが行で数える案に決めた（request.md）。2 行になったので、撤去の線の表示の単位が 1 通りに決まらなかった |
| I4-5 | 独立-4 | low | no | self-inflicted | doc | fixed | docstring の 1 行目が古い。commit: 8d954e5a |
| I4-6 | 独立-4 | low | no | self-inflicted | doc | accepted | 断片に読めないときと SECURITY.md が無い |
| I4-7 | 独立-4 | low | no | inherited | test-power | accepted | 記録の伏せ字を固定するテストが無い |
| I4-8 | 独立-4 | low | no | inherited | display-form | accepted | ユーザーが照合しない案に決めた（request.md）。引用を発言と照合しない。空の引用も出る |
| I4-9 | 独立-4 | advisory | no | inherited | process | accepted | テンプレート外の記述あり（PR 本文の抜粋の経緯の文）。次の巡の前に除く |
| I4-10 | 独立-4 | advisory | no | inherited | process | fixed | 未決の行に問いと推奨と戻す範囲が無い。commit: なし（PR 本文） |
| I4-11 | 独立-4 | advisory | no | self-inflicted | display-form | accepted | 同じ差が 2 種類で重なって 2 行になりうる。試行の記録で見る |
| I4-12 | 独立-4 | advisory | no | inherited | trial | accepted | 撤去の読みを促す仕組みが配布物に無い。マージの後に Issue にする |
| I5-1 | 独立-5 | low | no | self-inflicted | test-power | accepted | 満たせないの行の件数と別の案をテストが固定していない |
| I5-2 | 独立-5 | low | no | self-inflicted | test-power | accepted | 見せる順が読み手の返す順と区別されない |
| I5-3 | 独立-5 | low | no | self-inflicted | doc | accepted | 別の案の値の書き方が文書ごとに違う。PR 本文は両方の値で書く |
| I5-4 | 独立-5 | advisory | no | self-inflicted | display-form | accepted | 行の見出しの表記が案の文字どおりではない。見せる情報と順は同じ |
| I5-5 | 独立-5 | advisory | no | self-inflicted | failure | accepted | 表示に使わない欄が読めなくても項目を捨てる |
| I5-6 | 独立-5 | advisory | no | inherited | doc | accepted | 断片の Affected Files に SECURITY.md が無い |
