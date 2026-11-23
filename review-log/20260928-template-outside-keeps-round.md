---
lane: L1
pr: 旧#196
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 9ba56d8dc4a5b15eb136538127b5471b07ae292e | 0 | 0 | 0 | 2026-09-28T14:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| T1 | 独立-1 | medium | no | self-inflicted | contract-override-header-stale | next-pr | `CLAUDE.md:54` は契約 1 を破った巡（`テンプレート外の記述あり` を報告した巡）も有効とするが、手順 6 の冒頭（`:48`）の、軽いレーンが契約から外れる点の列挙には「抜粋の分だけ緩める」しか無い。`independent-review.md:7` の「4 条件すべてを満たすときだけ独立レビューと呼ぶ」から読むと、この巡は独立レビューに数えない読みが残る。`:48` に 1 句足し、テストで固定する。近道の規定で次の PR |
| T2 | 独立-1 | low | no | self-inflicted | test-power | next-pr | 手順 7 の列挙に足した assert は句の有無だけを見るので、`unavailable` の行を括弧の中の「書かない」側へ移しても通る。前後の区切り（`next-pr`・advisory、…の行。CI の結果と…は書かない）まで固定する。近道の規定で次の PR |
| T3 | 独立-1 | advisory | no | self-inflicted | measurement-wording | next-pr | `:54` の「誘導・抑制の文 0 件」は、`20260922-test-git-fixture.md` の A2（`### 検証` 節の実行結果の断定）を「通るはず」型に数えると 1 件になる（reviewer は根拠に採用していない）。数え方を 1 句で固定する。あわせて「56 本」は、測った時点（f0640629）の README を除く本数 55 本の誤り（README を含めて数えていた）。次の PR |
