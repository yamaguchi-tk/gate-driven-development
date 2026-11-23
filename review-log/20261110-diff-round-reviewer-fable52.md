---
lane: L1
pr: 655
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5e21c5e8dce283fc9a06fa906e2d3d0b8ce550b0 | 0 | 4 | 0 | 2026-11-10T16:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus（セッションの開始時に読んだ定義で走った。transcript は claude-opus-5-5・xhigh） | b7e9d9c74411efa24e61ed4a142c9bf6cceec7b7 | 0 | 1 | 0 | 2026-11-10T16:55+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus（セッションの開始時に読んだ定義で走った） | 744ba0dc89f385fb9999466bd5305bee9d53381f | 0 | 1 | 0 | 2026-11-10T17:15+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の文の「入れる前に、読む時期と撤去する条件を決める」が PR 本文にしか無く、マージ後に読むセッションが読み始める契機が無い。 commit: b7e9d9c7 |
| F2 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の例の「high を付けた件数」「PR の後に見つかった指摘」が読むものから抜け、マージ後の high に狭まった。 commit: b7e9d9c7 |
| F3 | 独立-1 | medium | no | self-inflicted | doc-sync | accepted | AGENTS.md:13 の「merge-ready の条件の model: opus は」が、書き換えた終了条件と合わない |
| F4 | 独立-1 | medium | no | self-inflicted | product | accepted | 終了条件の「上の起動の agent」に fallback（general-purpose, model: opus）が入らず、最後の巡を fallback で回した PR が文字どおりには merge-ready にならない。fallback の差分巡は opus のまま |
| F5 | 独立-1 | low | no | self-inflicted | product | accepted | reviewer 列の model: fable は実際に走った model ID を記録しない |
| F6 | 独立-1 | low | no | self-inflicted | product | accepted | Fable の拒否・起動失敗で差分巡を回し直すときの回し直し先と記録の仕方が無い |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docs/claude-md-rationale.md の根拠の項目が指す規則の文が無くなった。 commit: b7e9d9c7 |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 規則の文が「同じ費用」と言い切り、年の無い日付を使っている。 commit: b7e9d9c7 |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 全差分巡の行が Fable の理由の行の子になっている。 commit: b7e9d9c7 |
| G1 | 独立-2 | medium | no | self-inflicted | request-scope | fixed | 撤去の条件の閾値（費用 1.2 倍・時間が短くならない）が、依頼の前提「同じコスト・時間半分」より緩い。 commit: 744ba0dc |
| G2 | 独立-2 | medium | no | inherited | doc-sync | re-reported | AGENTS.md:13 の model: opus の読み替えが残る（F3 と同じ） |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | rationale:73 の項目が CLAUDE.md から消えた文を指し、56 行と重なる |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | rationale:55 の「下の 2 行」が、間に入れた行を指して読める |
| G5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 撤去の条件（規則）を rationale にだけ書き、CLAUDE.md は指すだけ |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「4 つ目の撤去条件」が PR後-N の条件（5 つ目）を指していない |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「基準の半分（14%）」と 15/56 の半分（約 13.4%）で判定が割れうる |
| G8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 基準の 62 本と 56 巡の違い、時間の定義、数えた場所が無い |
| G9 | 独立-2 | low | no | self-inflicted | product | accepted | 10 本を誰がいつ数えるかが無く、単発の撤去条件も 10 本まで読まれない |
| G10 | 独立-2 | low | no | inherited | doc-claim | accepted | rationale:70 の項目に、差分巡を Fable に替えた後の位置づけが無い |
| G11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 当て直しの「今の本文」の commit が無く再現できない |
| G12 | 独立-2 | advisory | no | self-inflicted | product | accepted | Fable が medium・low にし、後で high・blocking になった指摘を読むものに入れていない |
| H1 | 独立-3 | medium | no | self-inflicted | product | accepted | 費用 1.1 倍・時間 0.6 倍を、対にならない比較（別の期間の中央値）で判定するので、前提が成り立っていても当たりうる。当て直しの 旧#124 は対の比でも 1.15 |
| H2 | 独立-3 | low | no | inherited | doc-claim | re-reported | rationale:3「ここには規則を書かない」と撤去の条件の置き場が食い違う（G5 と同じ） |
| H3 | 独立-3 | low | no | inherited | doc-claim | re-reported | 「基準の半分（14%）」と 15/56 の半分が合わない（G7 と同じ） |
| H4 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「4 つ目の撤去条件」が PR後-N の条件を指していない。commit: なし（PR 本文） |
| H5 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | 1.1 倍・0.6 倍の幅を main が決めたことが書かれていない。commit: なし（PR 本文） |
| H6 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | 「5.2 に解決されるのを確かめた」の確かめ方が無い。commit: なし（PR 本文） |
