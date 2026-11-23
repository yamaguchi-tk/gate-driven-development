---
lane: L1+
pr: 516
follow_up_of: 510
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | c912cf9c | 0 | 0 | 0 | 2026-10-15 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2251ab74 | 0 | 3 | 2 | 2026-10-15 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 50284bbb | 1 | 1 | 1 | 2026-10-15 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 51d21700 | 0 | 1 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | design | fixed | 草案の AC「委任先: 並行 の行で押し返す」は今のコードでも通り、何も確かめない。委任先を宣言した集合で読み、外れた値では押し返さない形にした（Fable）。commit: 6e4ed55d |
| M2 | 方針メモ | advisory | no | self-inflicted | design | fixed | 上限での方式転換を委任先に寄せると、同じ種類の上限に 2 回目に当たったら止まる歯止めが事前回答の側に無い。適用の行の 1 欄目に上限の語を足し、2 回目で人に戻す条件を足した（Opus・Fable）。commit: 39e9116d |
| M3 | 方針メモ | advisory | no | self-inflicted | design | fixed | autonomy.md を消すと比較の軸の正本と相談役・予算の一覧の参照が切れる。手順・宣言の行の読み方・比較の軸の正本として残した（Opus・Fable）。commit: 39e9116d |
| M4 | 方針メモ | advisory | no | self-inflicted | design | fixed | 表示した human check で選んだ委任を事前回答の行にするなら、定義と原文の照合（選択肢の文と返事を組で引用）を直す必要がある（Opus）。commit: 39e9116d |
| M5 | 方針メモ | advisory | no | self-inflicted | design | fixed | 名指しの無い選択肢を `並行` に当てるか（Opus は名指しだけ、Fable は名指しが無いときだけ並行）。ユーザーが Fable の案を承認した。commit: 39e9116d |
| A1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 表示した human check で選んだ委任の照合が、組で引用する原文に合わせて直っていなかった。組の前半・後半と各欄の読み方を § 事前回答 2 に書いた。commit: 22696e50 |
| A2 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 修正と委任を同じ返事で受けると、本人がまだ承認していない human check を委任先が承認しうる。委任の行は承認の時点で書き、表示中の human check には適用しないとした。commit: 22696e50 |
| A3 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 上限の 2 回目の数え方に、旧文の「数えられなければ止まる」が写っていなかった。行より前に同じ上限に着いていないと確かめられなければ止まる、を足した。commit: 22696e50 |
| A4 | 独立-1 | low | no | self-inflicted | product | accepted | 旧#10 に、判断の委任を含む返事（「OK、Opus に任せる」など）の分類が無い |
| A5 | 独立-1 | low | no | self-inflicted | product | accepted | compact の Required Words に判断の委任の行が無く、圧縮時に落ちうる |
| A6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 選択肢の `人に止める` と記録の値 `なし` の対応が、2 か所の読み合わせに頼っている |
| A7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | autonomy.md の宣言の行の読み方の「Read で読み」が、post-merge-qa の既定ブランチだけを読む規定と食い違う |
| A8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 事前回答 2 の「判断の手順 4 と同じ」が指し返しの循環になり、autonomy.md の参照元に項目 7 が無い |
| A9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | steering 書き込み hook の WARN が、無くなった「判断役の承認」を例に挙げる（autonomy_value.py:118） |
| A10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界の一覧 1 の書き方が広すぎ、種類も決め直しが要る |
| A11 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | PR 本文の数に、数を出したコマンドと、押し返しを狭めた分の件数が無い |
| A12 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 変更断片が type: minor のまま（利用者の宣言を読まなくなる） |
| A13 | 独立-1 | low | no | self-inflicted | test-power | accepted | 押し返しのテストに、前が無効・最後が有効のケースと opus 単体のケースが無い |
| A14 | 独立-1 | low | no | self-inflicted | style | accepted | テストの空行が PEP 8 に合わない |
| A15 | 独立-1 | advisory | no | self-inflicted | product | accepted | hook と main で、4 値の外の委任先の扱いがそろっていない（hook は止まる側） |
| A16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | マージの問い方への効き目（委任の承認も human: で記録する）が PR 本文に無い |
| A17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「どこまで自走するか」を列挙する別の箇所（手引き・項目 6）に判断の委任が無い |
| A18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | hooks.json の説明に、狭めた押し返しの条件が無い |
| A19 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | hook が今も `自律判断:` を判定行として読む（止まる側） |
| A20 | 独立-1 | advisory | no | self-inflicted | product | accepted | compact の行に内部の指し先が入り、委任の選び方の案内が無い |
| B1 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | 上限の 2 回目の「4 択の跡」が、3 択で提示する 2 種の上限（Remediation Loop Safety、PR 後の 2 回目の設計し直し）に当たらず、2 回目でも委任先が判断する。上限に着くたびに書く `上限到達:` の行で数える形に変えた。commit: 4ec9fa22 |
| B2 | 独立-2 | medium | no | self-inflicted | product | accepted | 自走上限を後で引き上げると、組の原文の行の自走上限が Approved Direction と一致せず、委任が効かなくなる（止まる側） |
| B3 | 独立-2 | low | no | self-inflicted | product | accepted | 組の形以外の、表示中の human check への返事に含まれた事前回答は、今も受けたターンに書くので、§ 2 と 旧#9 の読み手が保留中の human check に当てうる |
| B4 | 独立-2 | low | no | self-inflicted | product | accepted | 1 回目の返事で委任を選び 2 回目が OK だけのとき、「OK だけなら人に止める」と「前の返事の値も承認時に書く」が食い違う |
| B5 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 組の形の行に書く `人に戻す条件` の値が決まっていない |
| B6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文に、行を書く時機・上限の 2 回目・組の照合の挙動が無い |
| B7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 変更断片の上限の 2 回目の文が、両方そろったときに止まるとも読める。上限到達の行で数える文に書き換えた。commit: 4ec9fa22 |
| B8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | § 共通の承認後処理に、委任の行を書く手順が無い |
| B9 | 独立-2 | advisory | no | self-inflicted | product | accepted | gdd-dev.md に足した 1 行で runtime の予算に当たりうる（validate-plugin.sh は通った） |
| C1 | 独立-3 | medium | no | self-inflicted | product | accepted | `上限到達:` 行を書く主体と時機が 4 か所で食い違う。subagent が 4 択を出す経路では、委任した 1 回目で止まる（二重に書く）か、行が書かれず 2 回目を数え落とす |
| C2 | 独立-3 | low | no | self-inflicted | product | accepted | この版より前に同じ上限に着いた steering は `上限到達:` 行を持たず、その 1 回目を数え落とす |
| C3 | 独立-3 | low | no | self-inflicted | product | accepted | compaction・resume で同じ到達を再入すると行が 2 本になり、1 回目で止まる（止まる側） |
| C4 | 独立-3 | low | no | self-inflicted | product | accepted | state-machine の「この節のどのトリガー」に Completion の Round 上限と 5/5 が入りうる |
| C5 | 独立-3 | low | no | self-inflicted | product | accepted | PR 作成後の (3-f) 取り直しでも残ったときに、`上限到達:` を書く指示が無い |
| C6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の抜粋に、新しい `上限到達:` 行が書かれていない（PR 本文で直す） |
| C7 | 独立-3 | advisory | no | self-inflicted | style | accepted | 括弧の前に読点が残っている（human-check-template.md:713） |
