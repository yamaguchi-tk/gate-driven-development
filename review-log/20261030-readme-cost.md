---
lane: L1
pr: 619
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 092039b7 | 0 | 2 | 0 | 2026-10-30T11:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | ec45311a | 0 | 1 | 0 | 2026-10-30T12:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼は Pro・Team を対象に含めるが、1 タスクが枠に収まるか・Opus を使えないときの動きが分からないまま限界にしていた。相談役 2 本の推奨（聞き直さず、公式の資料で分かる範囲と確かめていない点を書く）どおり、Pro・Team の既定のモデル・利用枠の共有と見方（/status）・資料のリンク・自分で測る手順・Opus を使えないときは未測を足した。commit: ec45311a |
| r1-2 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 費用の表は、effort の引き下げ・advisor の停止・Sonnet 化より前の構成で測った値で、そのことと、1 つの repo の 28 本から出したことを書いていない（README.md:149-156） |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Fable を起動する条件を「判断の委任で Fable に任せるを選んだときだけ」と狭く書いている。名指しで意見を求めたときなども起動する（README.md:161） |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「相談役は Opus に固定」に Fable の相談役も入って読める（README.md:147） |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Opus の固定が Claude Code に限った話だと書いていない。Cursor・Codex は別のモデルに写す（README.md:147） |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「GDD の agent からは advisor を呼ばない」が散文の指示で、仕組みで止めていないことを書いていない（README.md:163） |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 表の割合（110/200 は 55%）と「10 倍で約 3 倍」（表では約 2.4 倍）が表の値と合わず、何の中央値かが書かれていない（README.md:153, 157） |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 公式の資料の出典・ベンチマークの名前・時点が書かれていない（README.md:163） |
| r1-9 | 独立-1 | low | no | inherited | doc-claim | accepted | fixed-models.md:66 に、Opus と Fable を並べていた頃の文が今の規定として残っている |
| r1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しい節が Sonnet で動く agent を挙げ、§ モデル選択の「この README には一覧を写さない」と食い違う（README.md:284） |
| r1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | /advisor off の書き方を確かめた跡が無い（README.md:163） |
| r1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 表を差分の行数で分けていて、すぐ前の所要時間の表のタスクサイズ（trivial / quick / standard）と対応しない（README.md:151-154） |
| r2-1 | 独立-2 | medium | no | self-inflicted | request-drift | accepted | 依頼の「Proも含める　Team Planとかも」は「読者に含める」とも「Pro・Team で使えることを前提に公開する」とも読める。ユーザーに確かめ、Team の Premium では回せた・Standard では 2〜3 週間前に human check の前に枠が尽きた・今は不明、という実測の返事を受けた。README に作者の環境の例として書いた（README.md:161） |
| r2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「GDD の側にも、その場合の扱いは無い」は言い過ぎ。相談役は起動できなければ人に止まる（autonomy.md:12）、軽いモデルへ自動で下げない（fixed-models.md:12）（README.md:162） |
| r2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「Opus 5.5」と版数を書いていて、fixed-models.md § モデル名の書き方（版数を書かない）と食い違う（README.md:160） |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 利用枠を見るコマンド /status が正しいか確かめた跡が無い。公式の Pro・Max の記事は /status で残りの枠を見ると書いている（README.md:161） |
| r2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 公式資料から引いた既定のモデル・枠の共有を reviewer は確かめられない。seat の種類で既定が違う時期があった（README.md:160） |
| r2-6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化に、公式資料から引いた事実・リンク・自分で測る手順が書かれていない。PR 本文を直した。commit: なし（PR 本文） |
| r2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 利用枠が作業の途中で尽きたときの続け方（/gdd-dev resume）が手順に無い（README.md:161） |
