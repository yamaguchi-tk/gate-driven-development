---
lane: L1
pr: 667
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d2108541cd0663d2c2942e751c9322a942afb081 | 1 | 2 | 1 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | c79691e9786aa7ebf7848f86598a1a87ffd3d479 | 0 | 2 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | yes | self-inflicted | qa-scope-source | fixed | 設計: 変える（範囲の値の出どころを決めていなかった）。事前回答・後続 Stage・再開の経路で、本人が見ないまま main が QA の範囲を書けた。値は本人の発話から読めるものだけにし、読めなければ不明にして 1 問で問う。commit: c79691e9 |
| I1-2 | 独立-1 | medium | no | self-inflicted | stale-declaration | accepted | autonomy_value.py:103 の WARN の文面に、廃止した宣言での当てはめが残る |
| I1-3 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | global CLAUDE.md の例外が廃止した宣言を名指ししていた。ユーザーの指示（「書き換えて」）で、例外の文を human check で承認した QA の範囲に書き換えた（repo の外のファイル） |
| I1-4 | 独立-1 | low | no | self-inflicted | deploy-workflow-match | accepted | デプロイ系かを main が読んで決め、判定できないときの倒し方が無い |
| I1-5 | 独立-1 | low | no | self-inflicted | merge-intent | accepted | GitHub に断られたときに gdd-merge-intent.json を消す手順が無い |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | CODEOWNERS だけではマージは止まらない（必須レビューの設定が要る）のに、止める側に数えている |
| I1-7 | 独立-1 | low | no | inherited | doc-claim | accepted | 「このときだけ Merge Approval を問わない」が直前の別の場面にかかって読める |
| I1-8 | 独立-1 | low | no | self-inflicted | qa-scope-format | accepted | QA の範囲: デプロイ に なし の形が無い |
| I1-9 | 独立-1 | low | no | self-inflicted | qa-scope-format | accepted | 範囲の書き直しと、同じ種類の行が 2 行以上なら範囲が無いがぶつかる（止まる側に倒れる） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | request-scope | accepted | QA の範囲にもとづくマージ条件を残した読み方を、ユーザーに確かめていない |
| I1-11 | 独立-1 | advisory | no | self-inflicted | security-boundary | accepted | 保護の無い repo で、権限・hook の設定を変える PR も自走でマージされる（PR 本文で開示） |
| I1-12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 引き上げのときに 1 問で問うことを PR 本文の挙動の変化に足す。commit: なし（PR 本文） |
| I2-1 | 独立-2 | medium | no | self-inflicted | qa-scope-source | accepted | 表示した human check に OK と返したときに、並べた値と返事を組で読むことが書かれていない |
| I2-2 | 独立-2 | medium | no | self-inflicted | qa-scope-source | accepted | 不明を問う時機が手順 2 のままで、手順 1 の QA 計画を不明のまま書くことになる |
| I2-3 | 独立-2 | low | no | self-inflicted | qa-scope-source | accepted | 値の出どころの発話を記録する欄が無い |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | main が判定できない値は不明、が正本から消えて参照元にだけ残った |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 再開で 3 行をいつ書くかが定まっていない（止まる側に倒れる） |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 変更断片に、値が不明になる条件が書かれていない |
| I2-7 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 事前回答・後続 Stage で範囲を言っていないとき、マージ前に 1 問で止める。ユーザーが「止めてよい」と決めた |
