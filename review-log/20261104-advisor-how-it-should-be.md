---
lane: L1
pr: 636
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f10b6596e02579e12e6dd282b5530b79cd38aab3 | 0 | 1 | 0 | 2026-11-04 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c92219de2998f98e91c0b22f204d7def3f48408c | 0 | 0 | 0 | 2026-11-04 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c474a4a398a49080a160b563ebffe51c42186a4f | 0 | 0 | 0 | 2026-11-04 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | criteria-order | accepted | 新しく置いた照らす前の問い（どの案も届かないなら、あるべき形に向かう案を推す）と、同じ節の基準 3（選択肢に無い案を推してよい条件）・基準 0（ユーザーがすでに決めたこと）のどちらが優先するかが書かれていない。基準 3 に条件を足すか、問いを基準に従わせる案 |
| I1-2 | 独立-1 | low | no | self-inflicted | rule-copy | accepted | 正本は「相談役 3 本に同じ文を写し、一致は test が固定」と書くが、足した段落は写されず、test も番号付きの行しか見ない。書き分ける案 |
| I1-3 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼は案 D の本文を正本にも入れることだったが、正本に入ったのは要約で、「問いがそれを聞いていなくても問う」「問いの前提や案の並びに合わせて、推奨を狭めない」が無かった。2 つの文を正本の段落に足した。commit: c92219de2998f98e91c0b22f204d7def3f48408c |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 出力の節の「結論を先に書く」の直後の最初の欄が、結論ではない `そもそもどうあるべきか:` になった。文を書き分ける案 |
| I1-5 | 独立-1 | low | no | self-inflicted | lens-label | accepted | 推奨をあるべき形から導くので、`観点:` がどの相談でも `あるべき形` に寄り、効きを数える値が分かれなくなる。並んだ案に無い案を推したときだけ付ける案 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 消した文（並んだ案に無い案を基準 2・3・4 に結び付けていた文）が、断片と PR 本文に書かれていない |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 効果の数字は Opus で effort を main から継承して測ったもので、Fable・max の新しい本文は未測だと、PR 本文の限界に書いていなかった。PR 本文の限界に足した。commit: なし（PR 本文） |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | root CLAUDE.md:158 の安全策 1 の問いの起点が「この部品は要るか」のままで、相談役の順序と読み違えうる |
| I1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation に、根拠の実測の場所（notes）が書かれていない |
| I1-10 | 独立-1 | advisory | no | self-inflicted | parallel-split | accepted | 2 本が独立に作る新しい案は違う案と判定されやすく、並行の委任で人に戻る回数が増えうる。未測 |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の「この PR の本文で」が PR の説明文と読める。「この PR の相談役の本文で」に直した。commit: なし（PR 本文） |
| I2-1 | 独立-2 | medium | no | self-inflicted | criteria-order | re-reported | I1-1 の再掲。足した「推奨を狭めない」が基準 3 の選択肢に無い案の制限と基準 0 にぶつかる |
| I2-2 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 正本の段落に、案 D の本文の「目標・指標・手法・方式そのものも、問い直す対象に入れる」と「原因（設計の決定・前提・工程）」がまだ入っていなかった。正本の 2 句を本文と同じ語にした。commit: c474a4a398a49080a160b563ebffe51c42186a4f |
| I2-3 | 独立-2 | low | no | self-inflicted | rule-copy | re-reported | I1-2 の再掲。「一致は test が固定」が前置きの段落には当たらない |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 足した「推奨を狭めない」の挙動が、PR 本文の挙動の変化と断片に書かれていない |
| I2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 正本の「問い」が、main が自分で推すときに何を指すか書かれていない |
| I3-1 | 独立-3 | low | no | self-inflicted | criteria-order | re-reported | I1-1 の再掲。照らす前の問いが基準 0 より先にあり、ユーザーが受け入れた指標を置き換える推奨が出うる（閉じ方: 列挙。low で常時 High に当たらない） |
| I3-2 | 独立-3 | low | no | self-inflicted | rule-copy | re-reported | I1-2 の再掲。節の冒頭の「同じ文を写す・一致はテストが固定」が照らす前の問いの段落に当たらない |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片の 7 行目が、正本から外した 2 句（「目標・指標・手法・方式を含む」「原因ごと直す進め方」）のまま |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化が外した 2 句のままだった。正本・本文と同じ語にした。commit: なし（PR 本文） |
| I3-5 | 独立-3 | advisory | no | self-inflicted | style | accepted | 差し替えた括弧書きが名詞への注釈の中で指示の文になっている |
| I3-6 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の測定値の記録の場所が材料から確かめられない。PR 本文の確認したことに notes の場所を書いた |
