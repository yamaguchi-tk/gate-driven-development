---
lane: L1
pr: 368
follow_up_of: 367
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f3e37fbbffda7150e1a000a7fee25ae57e565e69 | 0 | 1 | 0 | 2026-10-05T00:52+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | ed6882d86572630890890c3ad339e44e734840a7 | 0 | 0 | 0 | 2026-10-05T01:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | product | fixed | 3g の戻し先を Classify に指したため、尺度の外・欠落の Codex severity が戻すときに読み替え（P2→Medium など）になり、同じ節の依頼文の「尺度の外なら high」と食い違う。ユーザーの指示で、戻し先を依頼文の規定の severity（読み替えなし）にした。commit: ed6882d86572630890890c3ad339e44e734840a7 |
| F2 | 独立-1 | low | no | self-inflicted | product | accepted | Medium の上限が戻す経路にだけ掛かり、最初から適用範囲外と分かる 4 型の指摘は high のまま。経路で重さが分かれる。follow_up_of のため PR 本文の限界に書いた |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の User Action Required が「適用範囲内の部品」の限定を落とし、warn-only の lint などの指摘まで high になると読める。follow_up_of のため PR 本文の限界に書いた |
| F4 | 独立-1 | low | no | inherited | product | next-pr | root CLAUDE.md 手順 5（codex-N）だけが Classify を指さず、判定できない指摘の扱いが無い。次の PR |
| F5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 根拠を worklog に残すと PR 上のレビュアーから見えない。PR 本文に列挙 |
| F6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 3g には受け入れ判定の段が無く、戻す前に確かめる時点が決まらない。PR 本文に列挙 |
| G1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 戻し先の「high のまま」と、Classify に委ねた適用範囲外の部品の medium 上限のどちらが勝つかが文面から決まらない（厳しい側に倒れる）。follow_up_of のため PR 本文の限界に書いた |
| G2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 新しい戻し先は Codex の指摘にしか定義が無く、独立レビューの指摘を判定できないとして high にしたとき「high のまま」と読める。follow_up_of のため PR 本文の限界に書いた |
| G3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Summary「Classify と同じにした」が、戻し先だけ違えた変更より広く言っている。follow_up_of のため PR 本文の限界に書いた |
| G4 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 3g は high から戻した後の medium の扱いも決めていない（PR 本文の限界は low だけを挙げていた）。PR 本文を直した |
| G5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 「読み替えはしない」と読むと、Codex の `Medium` など大文字の表記ゆれも尺度の外になり high に固定される。PR 本文に列挙 |
