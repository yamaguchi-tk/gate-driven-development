---
lane: L1
pr: 487
follow_up_of: 480
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d27f12ac | 0 | 1 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | request-drift | next-pr | 項目 3 の gate の分を確認なしに限界へ回した。根拠の 0 件も取り直しの行を数えただけで、申し送りは機械で読める記録に残らず「未測」に当たる。ユーザーに確かめ、gate は別の L1+ PR で足すと決まった（next-pr 相当。.request.md に回答を写した）。PR 本文の限界は「未測」に直した |
| A2 | 独立-1 | medium | no | self-inflicted | product | accepted | checkpoint の強制発火の条件が「行がある状態で high・blocking が残った」で、(3-f) の「取り直しでも残れば」より広い。PR 本文の限界に書く |
| A3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界が gate の受理を quick (express)・trivial だけと狭く書いていた。理由が「重要判断なし」なら Task Size を問わず通る。commit: なし（PR 本文） |
| A4 | 独立-1 | low | no | inherited | doc-claim | accepted | post-completion-learning.md:13・post-completion-pr-flow.md:50 が蒸留の対象を standard task と書いたまま |
| A5 | 独立-1 | low | no | inherited | doc-claim | accepted | gdd-completion-check の「High finding 残存時は差し戻す」が High だけのまま |
| A6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | phase-progression の「blocked で停止」が正本（差し戻しと human-check-waiting）と合わない |
| A7 | 独立-1 | low | no | self-inflicted | product | accepted | 新しい強制発火を判定する時点が書かれていない |
| A8 | 独立-1 | low | no | self-inflicted | product | accepted | ほかの trigger と同時に発火したときの優先が書かれていない |
| A9 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | `<選択>` の値 `人に戻す` が記録の書式の列挙に無い |
| A10 | 独立-1 | advisory | no | inherited | doc-claim | accepted | (3-f) に、取り直しの後に Decision への high がまた出たときの規定が無い |
| A11 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 前の断片 20261014-completion-check-retake-and-records の写しの記述が High のまま |
| A12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の 1 点目が「読めないときは used」を書いていない |
| A13 | 独立-1 | advisory | no | self-inflicted | style | accepted | 申し送った Decision を指す語が 3 か所で揃っていない |
| A14 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が抜粋に無い。PR 本文の末尾の節に書く |
