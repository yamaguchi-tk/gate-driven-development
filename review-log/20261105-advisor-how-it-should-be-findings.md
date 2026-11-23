---
lane: L1
pr: 637
amends: 20261104-advisor-how-it-should-be.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 67b5c2b50b69d22b908e2fb7a7206e75eef935e7 | 0 | 0 | 0 | 2026-11-05 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 325fe1de575d42631e49c892da5f6ed2b7790043 | 0 | 0 | 0 | 2026-11-05 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 210c8446c2c4238208e7415706cfb58381548fd9 | 0 | 1 | 0 | 2026-11-05 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 依頼の 2 (a) は問いを番号付きの項目にする案だったが、番号の無い段落と箇条のまま置き、テストの抽出を前置きの段落より後の全行に広げた。番号を付けると依頼の 1 が「基準 0」と呼ぶユーザーの決定が 1 にずれ、ほかの 3 ファイルの「基準 1・2」もずれる。今の形で進めると示し、問い 2 の返事（「案 C で直す」）まで異論は無かった。決定: 番号を変えない |
| I1-2 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の 1 は基準 0 と食い違うときの文を相談役の「守ること」に足す案だったが、選ぶときの基準の写しにだけあった。守ることにも同じ扱いを書いた。commit: 325fe1de575d42631e49c892da5f6ed2b7790043 |
| I1-3 | 独立-1 | low | no | self-inflicted | rule-copy | accepted | root CLAUDE.md の安全策 1 の起点を差し替えて、要否・閉じ方・止めるかの問いが消え、定義なしで起動する経路では落ちる |
| I1-4 | 独立-1 | low | no | self-inflicted | wiring | accepted | 相談役が書く `範囲を広げる提案:` を、人への確認に載せる手順（human-check-template 項目 7・CLAUDE.md の確認の前の相談）が無い |
| I1-5 | 独立-1 | low | no | self-inflicted | criteria-order | accepted | 基準 0 と食い違えば人に戻す文と、基準 7 の「取り消しにくい操作以外は進める」のどちらが先かが書かれていない |
| I1-6 | 独立-1 | low | no | self-inflicted | trigger-measure | fixed | 人に戻す新しい発火条件の、当たる件数と残らない入力が PR 本文の限界に書かれていない。限界に書いた。commit: なし（PR 本文） |
| I1-7 | 独立-1 | low | no | self-inflicted | test-rule | fixed | テストが正本に語があることを assert しており、§ テストが書かないとする形だった。番号の基準の前に写す行があるかを見る形にした。commit: 325fe1de575d42631e49c892da5f6ed2b7790043 |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変えたテストのコメントが「同じ番号付きの文を写す」のまま |
| I1-9 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の I1-10 は週次の分析で割れた回数を数える案だったが、PR 本文の限界は「測っていない」だけだった。いつ何を数えるかを書いた。commit: なし（PR 本文） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の「問いを冒頭に移し」は、正本では前から同じ位置で、移したのは相談役の側 |
| I1-11 | 独立-1 | advisory | no | self-inflicted | style | accepted | 正本の前置きの括弧の中が指示の文になっている |
| I2-1 | 独立-2 | low | no | self-inflicted | criteria-order | re-reported | I1-5 の再掲。守ることに足した「人に戻す」が基準 7 と食い違う |
| I2-2 | 独立-2 | low | no | self-inflicted | rule-copy | accepted | 守ることの範囲の文に、基準の節にある「（別の機能・別のファイル群）」が無く、守ることの側は正本と突き合わされない |
| I2-3 | 独立-2 | low | no | self-inflicted | wiring | re-reported | I1-4 の再掲。`範囲を広げる提案:` を読む側・人に見せる規定が無い |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 当て直しの数が、守ることへの追加の前の本文で測ったものかが記録に無かった。notes に測った版を書き、PR 本文の限界に守ることへの追加は当て直していないと書いた。commit: なし（PR 本文） |
| I2-5 | 独立-2 | low | no | self-inflicted | request-scope | re-reported | I1-1 の再掲。依頼の 2 (a) の手段を、抽出を広げる手段で代えた |
| I2-6 | 独立-2 | advisory | no | self-inflicted | trigger-measure | accepted | 当たった件数 0/19 の止まる条件を、当て直しの後の確認なしに足した。ユーザーに確かめ、「案 C で直す」の返事で人に戻す句を外した |
| I3-1 | 独立-3 | medium | no | self-inflicted | request-scope | fixed | 依頼の 1 は「同じ 19 件で当て直してから入れる」だったが、入る最終の本文（守ることへの追加・基準 0 の直し・人に戻す句を外した後）は当て直していなかった。tip の本文で 19 件を当て直し、notes と PR 本文に結果を書いた。commit: なし（PR 本文） |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の未測の列挙から、選ぶときの基準の箇条から人に戻す句を外したことが漏れていた。当て直しの結果で置き換えた。commit: なし（PR 本文） |
| I3-3 | 独立-3 | low | no | self-inflicted | wiring | accepted | 人に戻す句を外したので「食い違いと理由を書く」の書き先の欄が決まっていない |
| I3-4 | 独立-3 | advisory | no | self-inflicted | criteria-order | accepted | 基準 0 が覆す理由に使わないと名指すのは上の問いと 1〜3 だけで、4〜7 は挙がっていない |
| I3-5 | 独立-3 | advisory | no | self-inflicted | rule-copy | re-reported | I2-2 の再掲。守ることの行が選ぶときの基準の箇条と同じ規定を別の言い回しで書いている |
