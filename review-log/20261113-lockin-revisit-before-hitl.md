---
lane: L1
pr: 660
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 16a5722bc1f1ce1cb84c001d2698b8bdab0d3ce5 | 0 | 3 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 707bf89fadf0c4706e0c7250a37467594cea6f96 | 0 | 2 | 1 | 2026-11-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | c0b54312a26a63f0a1998dda87e6ff36597171ae | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 設計: 変えない（聞いた行の種類を 2 つとも条件と行き先に入れれば閉じる）。見直しの条件を、範囲を決める行から聞いた行の全部に広げ、未収束の後の既存とぶつかるを仮決定にして human check の一次表示から外した。commit: f70a9ef3 |
| I1-2 | 独立-1 | medium | no | self-inflicted | lockin-routing | fixed | 設計: 変えない（I1-1 の行き先に届く分岐が要る）。回答の前の行が未収束なら未収束の後の扱いに進む分岐を足した。commit: f70a9ef3 |
| I1-3 | 独立-1 | medium | no | self-inflicted | lockin-routing | accepted | request-crosscheck.md の上書きで、答えから足した行と、起動し直しが unavailable のときの行が消える |
| I1-4 | 独立-1 | low | no | self-inflicted | lockin-routing | fixed | 未収束でも表示する問いを worklog に写すようにした（I1-1 の文の書き直しに含む）。commit: f70a9ef3 |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 見直しでリスクの段が替わることと、突き合わせの 2 回目の起動が、PR 本文・断片・agent 定義に書かれていない |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | compact の § ズレ確認 の列挙を full 版に合わせた。commit: f70a9ef3 |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 件数（待ちが 3 本に達した steering 0 件）と読む時期・撤去の条件を PR 本文に書いた。commit: なし（PR 本文） |
| I1-8 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 「一つ前」は突き合わせ、見直しは 1 回までで 2 回目は目的を聞き直す（ユーザーの返事で決定） |
| I1-9 | 独立-1 | advisory | no | self-inflicted | lockin-routing | accepted | 突き合わせに見直しであることも止まった行も渡らず、同じ行が返りうる |
| I2-1 | 独立-2 | medium | yes | self-inflicted | zure-display | fixed | 設計: 変える（経路ごとの判定をやめ、行ごとに回答か仮決定を添えたかで決める）。一次表示から外すのを、確認で回答か仮決定を添えた行だけにした。commit: 26fb3aec |
| I2-2 | 独立-2 | medium | no | self-inflicted | zure-display | accepted | 未収束の後の既存とぶつかるの仮決定に、向きの規定と Step 4c の写しが無い |
| I2-3 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 確認待ちの問いに、2 回目の後は AI の仮決定で閉じることを足した。commit: なし（PR 本文） |
| I2-4 | 独立-2 | low | no | self-inflicted | zure-display | fixed | 回答か仮決定を添える書き方を human-check-template に足した（I2-1 の修正に含む）。commit: 26fb3aec |
| I2-5 | 独立-2 | low | no | self-inflicted | lockin-routing | accepted | 任された既存とぶつかるの行き先が書かれていない |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「最後の要件確認行だけで決める」と、回答の前の行も読む括弧が食い違う |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の条件を聞いた行の全部に合わせた。commit: 26fb3aec |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 固定行の書式に回答の欄が無い（既存の規定） |
| I2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 上限に数えない括弧は I2-1 の修正で意味が戻る |
| I3-1 | 独立-3 | medium | no | inherited | zure-display | re-reported | I2-2 の再掲（未収束の後の既存とぶつかるの仮決定に向きの規定が無い） |
| I3-2 | 独立-3 | low | no | self-inflicted | lockin-routing | accepted | 任された既存とぶつかるに回答・仮決定のどちらを添えるかが決まっていない |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 確認を行わなかった経路の例の express からの昇格が、確認の除外条件と揃っていない |
| I3-4 | 独立-3 | low | no | inherited | doc-claim | accepted | 一次表示のズレ確認の列挙に依頼の原文なしの行が無い（既存） |
| I3-5 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 断片に回答を添えて書くことが無い |
