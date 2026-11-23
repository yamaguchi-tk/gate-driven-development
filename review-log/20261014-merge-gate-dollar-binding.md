---
lane: L1
pr: 490
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 0f9a5285 | 0 | 0 | 0 | 2026-10-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0be74bfc | 0 | 1 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ-1 | advisory | no | inherited | binding-reach | fixed | 候補案（番号と -R を読めれば $ があっても binding を引く）の要否。実測（main 0f9a5285 の parser、merge 1,404 件）で、marker の無い git cwd からの素通りの形は 37 件。候補案の射程は 4〜6 件で、どの PR の steering にも PR URL の記録が無く、binding は当たらない（広げても当たり 1 件、binding 無し・承認あり）。原因は binding の側（読める state.md 46 件中 PR URL ありは 18 件、PR 1099 は worktree_path が実在せず太字の PR URL を読まない）。Opus は C（文書だけ）、ユーザーは Fable の意見を求め、Fable も C（開き直す条件に直す形を書かない、binding の欠陥は次の PR）。ユーザーが「C＋Fable の補足」を選んだ。hook は直さず、SECURITY.md の項を書き直す commit: なし（方針） |
| I1-1 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 「判定が変わる merge は 0 件」は今の binding・worktree の状態で見た値で、merge の時点の binding（worktree ごと消えたもの）を区別できないのに断定している。近似の注記に binding・worktree の有無と transcript の文字列検索が無い（近道の 1 巡目の blocking でない medium。限界の節に書く） |
| I1-2 | 独立-1 | low | no | self-inflicted | product | accepted | 開き直す条件が、worktree の実在・PR URL を読めることをいつの時点で見るかを書かず、merge 後に worktree を消す流れでは後から測っても当たらない側に偏る。誰がいつ測るかも無い |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 置き換えで「-R の値に $ を含む形は 0 件」が消え、37 件の定義では cd の無い `-R "$R"` の形が数えられず、件数を項から読めない |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 承認を確かめた 5 件の選び方が書かれていない |
| I1-5 | 独立-1 | advisory | no | self-inflicted | product | fixed | 依頼の「E は PR 本文に候補として残す」「binding の側の欠陥は次の PR に並べる」が抜粋に無い。PR 本文の「次の PR」と候補の節に書いた commit: なし（PR 本文） |
| I1-6 | 独立-1 | advisory | no | self-inflicted | product | accepted | 旧条件「正当な merge を止めずに閉じる形が見つかったとき」を消して置き換えている。依頼は条件の中身を指定していない |
| I1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 43 件の日付と 旧#473 の説明が食い違って見える。43 件を数えた main d4fb6e70（2026-10-13）は 旧#473 を含まないことを確かめた（`git merge-base --is-ancestor 8b527358 d4fb6e70` が偽） |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | binding が読める steering の括弧が lookup の条件の一部だけで、正本（gdd_mg_binding_lookup）を名指ししていない |
| I1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 別の直し方（cd 先を採らなかった merge を止める分岐）を採らない根拠の文を消したことが PR 本文に無い。変更内容に書いた commit: なし（PR 本文） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | front matter に follow_up_of が無い。旧#481 の「次の PR」は「なし（穴を直す PR は別の依頼として作る）」で、この PR は後続 PR に当たらない |
