---
lane: L1
pr: 428
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 072a71c0 | 0 | 1 | 0 | 2026-10-10 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 5bb28e12 | 0 | 0 | 0 | 2026-10-10 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b2c8141e | 0 | 0 | 0 | 2026-10-10 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 7ec558ee | 0 | 0 | 0 | 2026-10-10 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 1d66550b | 0 | 0 | 0 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| D1-M1 | 独立-1 | medium | no | self-inflicted | product | fixed | 足した合格条件が RED の定義と合わず、ラベルが側を「負例」に固定していた。RED 作成前の Contract Surface Coverage の行に移し、受け入れる側・止める側・境界の 3 行にした。commit: 5bb28e12 |
| D1-L1 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 依頼の「RED の前に確認項目」に対し、RED の合格条件に足していた。RED 作成前の確認の行に移した。commit: 5bb28e12 |
| D1-L2 | 独立-1 | low | no | self-inflicted | product | fixed | 境界を本数で必須にしたことが § テスト判定基準と食い違う。各行のテストを判定基準で選び、満たせない行は not_applicable にした。commit: 5bb28e12 |
| D1-L3 | 独立-1 | low | no | self-inflicted | test-power | next-pr | 実装前から通るテストの検出力を確かめる手順が無い |
| D1-L4 | 独立-1 | low | no | self-inflicted | product | fixed | ラベルを RED Evidence のどこに書くかが決まっていない。Contract Surface Coverage の行に書き、対照は RED Evidence に入れないとした。commit: 5bb28e12 |
| D1-L5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「否定側のテストを求める規定が無かった」は言い過ぎ。分岐の側ごとに分けることを求めていなかった、に直した。commit: なし（PR 本文） |
| D1-L6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | PR 本文に、差し戻しの件数の測り方が無い。PR 本文に書いた。commit: なし（PR 本文） |
| D1-L7 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が無い。PR 本文に書いた。commit: なし（PR 本文） |
| D1-A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の type |
| D1-A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 限界の節の測り方では、否定側の欠落を切り出せない |
| D1-A3 | 独立-1 | advisory | no | self-inflicted | style | accepted | 「否定側」がこの repo で逆の意味でも使われている |
| D2-F1 | 独立-2 | medium | no | self-inflicted | product | next-pr | § テスト判定基準のクラス表に、各行のテストを選べるクラスが無い場合がある |
| D2-F2 | 独立-2 | low | no | self-inflicted | product | next-pr | 移した後の行から境界の値の定義（閾値ちょうど・空・形が 1 箇所だけ違う入力）が消えた |
| D2-F3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 差し戻しの理由の書き方が SKILL と PR 本文でずれる |
| D2-F4 | 独立-2 | low | no | self-inflicted | product | next-pr | Contract Surface Coverage の 3 行は gate・lint のどちらも読まない |
| D2-F5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 同じ節の行の書き方（applicable / not_applicable の 2 値）と例が 3 行の形に追いついていない |
| D2-F6 | 独立-2 | low | no | self-inflicted | request-drift | fixed | 依頼は AC の種類を限らないのに、判定型の AC に絞っていた。条件で挙動が分かれる AC 全体にした。commit: b2c8141e |
| D2-A1 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | `実装前から pass（対照）` は実行の出力を残さない |
| D2-A2 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が抜粋から確かめられない |
| D3-1 | 独立-3 | medium | no | self-inflicted | product | next-pr | 副作用の AC の分割先が validation の行で、同じ節の no-op・side effect の行と置き場が二重になる |
| D3-2 | 独立-3 | medium | no | self-inflicted | product | next-pr | 「起こさない側」の不具合に当たるクラスが § テスト判定基準に無い |
| D3-3 | 独立-3 | medium | no | self-inflicted | product | next-pr | 受け入れる側と境界に当たるクラスも § テスト判定基準に無い |
| D3-4 | 独立-3 | low | no | self-inflicted | product | next-pr | ラベルが「通す＝起こす」を前提にし、止める側で副作用を起こす AC と 3 つ以上に分かれる AC で行が決まらない |
| D3-5 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 3 行の書き方と `実装前から pass（対照）` が同じ節の記録語彙と出力例に無い |
| D3-6 | 独立-3 | low | no | self-inflicted | bookkeeping | next-pr | 広げた対象（副作用の AC）の件数とコマンドが PR 本文に無い |
| D3-7 | 独立-3 | low | no | self-inflicted | request-drift | fixed | 依頼の「否定側のテスト」を「受け入れる側・止める側・境界の 3 行」に読み替えていた。ユーザーが止める側と境界の 2 行に決め、そのとおりにした。commit: 1d66550b |
| D3-8 | 独立-3 | low | no | self-inflicted | request-drift | fixed | 対象の AC の種類が括弧の中の列挙で、依頼より狭い。括弧を例示にした。commit: 7ec558ee |
| D3-9 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | 広げた規則の Skill RED-GREEN Evidence を確かめられない |
| D4-1 | 独立-4 | medium | no | self-inflicted | product | next-pr | 3 行に分ける先が「上の行」（validation）に固定され、retry・状態遷移の AC と合わない。AC ごとの 3 行にする |
| D4-2 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の例に「retry・状態遷移」が無い |
| D4-3 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 同じ節の記入例が 1 行のまま |
| D4-4 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 「3 タスクで計 6 回」の数え方が書かれていない |
| D5-L1 | 独立-5 | low | no | self-inflicted | request-drift | accepted | 境界の例「閾値ちょうど・空」は AC によっては通す側の入力になり、ユーザーが選んだ「否定側の中に収まる境界」から外れうる。無効化後の差分巡の 2 回目のため直さず、PR 本文の限界に書いた |
| D5-L2 | 独立-5 | low | no | inherited | product | re-reported | ラベルが「通さない＝起こさない」を前提にし、止める枝で副作用を起こす AC・3 つ以上に分かれる AC で行が決まらない（D3-4 と同じ） |
| D5-L3 | 独立-5 | low | no | self-inflicted | product | next-pr | 「上の行を分けて」で、validation の通す側を書く場所がこの節から消える。「上の行に加えて 2 行を足す」にする |
| D5-L4 | 独立-5 | low | no | self-inflicted | doc-claim | next-pr | 6 回の内訳を数えた元とコマンドが PR 本文に無い |
| D5-L5 | 独立-5 | low | no | inherited | doc-claim | re-reported | 同じ節の記録語彙と出力例が 2 行の形に追いついていない（D3-5・D4-3 と同じ） |
| D5-A1 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 「この行に」がどの行か読み違えうる |
| D5-A2 | 独立-5 | advisory | no | self-inflicted | product | accepted | 境界の例に § テスト判定基準のクラスが直接当たらない |
