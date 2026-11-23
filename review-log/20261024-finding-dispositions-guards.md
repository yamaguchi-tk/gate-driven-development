---
lane: L1+
pr: 575
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | 53a97857ac63e0bc3b0eca20286b78157612fd29 | 0 | 0 | 0 | 2026-10-24T02:00+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 109f3015fa1300631b13baa177e485793c9aafe1 | 0 | 4 | 0 | 2026-10-24T03:20+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) + user | 109f3015fa1300631b13baa177e485793c9aafe1 | 0 | 0 | 0 | 2026-10-24T04:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d61d63b245f757d4295c0de0c0a40c35b770c51e | 0 | 2 | 0 | 2026-10-24T05:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| m1-1 | 方針メモ-1 | low | no | inherited | design | accepted | IG 節に sha を足し CLI に --task を必須で足す案（Opus）と tasklist を読む案（Fable）が割れ、引数の案で進めた。Round の番号は方針メモ-2 で tasklist の Gate Rounds から読むことにした |
| r1-1 | 独立-1 | medium | no | self-inflicted | round-identity | fixed | 設計: 変える（今回の Round を sha だけで見分けた。IG 見出しに round を足し、tasklist の Gate Rounds と最後の節を突き合わせる。ユーザーが方針メモ-2 で推奨を選んだ）同じ HEAD のまま再 gate すると、今回の Round の IG 節を書き落としても前の節で通る（依頼 568 r1-3 の効果が狭まった。check-finding-dispositions.py:100）commit: d61d63b2 |
| r1-2 | 独立-1 | medium | no | self-inflicted | round-identity | fixed | 設計: 変える（分類を HEAD の節に狭めた。どの節もその sha で分類し、解けなければ invalid。祖先は見ない）HEAD でない sha の IG 節の absent@ の行は、sha の実在・祖先を見ずに分類から外れる（依頼 571 r4-3 の残り。:103）commit: d61d63b2 |
| r1-3 | 独立-1 | medium | no | self-inflicted | test-power | accepted | 同じ sha の節すべての引き継ぎを、1 つ前だけに戻す変異で落ちるテストが無い（空の節を 2 つ続けるケースが無い） |
| r1-4 | 独立-1 | medium | no | self-inflicted | task-arg | accepted | 並列実行で `--task <Current Task>` に何を渡すかが Step 8 に書かれず、見出しを複数 task にすると穴が開く |
| r1-5 | 独立-1 | low | no | self-inflicted | test-power | accepted | `--task` に複数の task を渡すテストが無く、any に変える変異で通る |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | CLI の `--task` の説明が「どれかを含む」と読め、コード（すべての task）と食い違う |
| r1-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | refuted の根拠の形のテストに advisory:unverified_file の行き先が無い |
| r1-8 | 独立-1 | low | no | self-inflicted | changelog | accepted | 旧#571 の断片の User Action Required の呼び方が `--task` 無しのまま。この PR の断片も新しい呼び方を書かない |
| r1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文が「14 件を直す」と書くが、挙動を変えるのは 13 件（commit: なし（PR 本文）） |
| r1-10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり（PR 本文の抜粋ファイル内。別の PR の巡の ID と、閉じていたので変えていないという記述）。次の巡の前に抜粋から除く |
| r1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | absent@ の行が無くても、steering が git の外か HEAD が解けないと invalid になることが挙動の変化に無い |
| r1-12 | 独立-1 | advisory | no | self-inflicted | product | accepted | duplicate の参照先の制限が拒否リスト。採った行の行き先の許可リストにできる |
| r1-13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 新しい invalid の分岐の当たる件数を transcript で測った（notes.md）。件数 0 の規則も足すとユーザーが方針メモ-2 で決めた |
| m2-1 | 方針メモ-2 | low | no | self-inflicted | measurement | accepted | transcript の実測で、件数 0 の規則が多く、IG の re-reported の重さの規則は正当な 1 件を止める。ユーザーは件数 0 の規則も足し、重さは IR 節だけにすると決めた |
| r2-1 | 独立-2 | medium | no | self-inflicted | round-identity | accepted | Gate Rounds の reader が、ほかの reader の読む書き方（`**Gate Rounds**:`・バッククォート・`=`・小文字・全角のコロン・task の見出しより前）を「行が無い」と読んで 0 にし、その書き方では同じ HEAD の再 gate が前の節で通る |
| r2-2 | 独立-2 | medium | no | self-inflicted | round-identity | accepted | 前の節の sha が HEAD の祖先かを見ない。ユーザーが方針メモ-2 で、祖先を見ない案を選んだ（request.md に指された案の文を足した） |
| r2-3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の件数（13 件＋1 件）が依頼の ID（14 個、うち 2 つは同じ件）と合わず、閉じた範囲とも対応しない（commit: なし（PR 本文）） |
| r2-4 | 独立-2 | low | no | self-inflicted | round-identity | accepted | rebase と gc の後に前の節の sha が解けなくなると、その節の absent@ の行は invalid のままで、直す手順が文書に無い |
| r2-5 | 独立-2 | low | no | self-inflicted | task-arg | accepted | task の見出しの受理集合がほかの reader と違う（`- T-1 x`、`### Task 3: 名前`）。invalid の詳細に読めた task の名前が出ない |
| r2-6 | 独立-2 | low | no | self-inflicted | test-power | accepted | テストのコメント「名前の一部だけでは照合しない」がコードと違い、assert もそれを固定していない |
| r2-7 | 独立-2 | low | no | self-inflicted | changelog | accepted | 変更断片の User Action Required に、既存の IG 節の見出しに sha・round を足すことが無い |
