# review-log/

軽いレーン（root `CLAUDE.md`）で進める GDD 改善の指摘記録。正本は
作者の手元の分析ノート（非公開） § X-52。

`plugins/gate-driven-development/changelog.d/<YYYYMMDD>-<slug>.md` と同じ slug で
1 対 1 に対応する `review-log/<同じファイル名>` を、軽いレーンの手順 5（Codex を使ったとき）・6・7
と L1+ 安全策 1・4 で追記する。巡の名前と reviewer 列の書き方は root `CLAUDE.md` の
「review-log の巡の名前」と手順 6 に従う。強制は `plugins/gate-driven-development/tests/checks/review-log-present.sh`
（`validate-plugin.sh` 経由）が行う。

`<slug>.request.md` は、その PR のきっかけになったユーザーの発言の写し（依頼の原文）で、
root `CLAUDE.md` 手順 1 で書き、手順 6 で独立レビューに渡す。検査は読まない。

`## 指摘` の `対応` は `fixed` / `deferred` / `accepted` / `re-reported` / `next-pr` /
`out-of-diff` のどれかにする。後の 3 つは X-52 の後に足した値で、この PR で直さない指摘を
表す（`re-reported` は前の巡で記録した指摘の再掲、`next-pr` は次の PR で直すもの、
`out-of-diff` は差分の外で対応しないもの）。行は残し、`## 巡` の high・medium には数えない
（振り分けは root `CLAUDE.md` 手順 6）。`実害` が `yes` の行には付けられない（検査が落とす）。
`deferred`・`accepted` は今までどおり数える。

front matter は `lane`（`L1` / `L1+`）と `pr`（PR 作成までは空でよい）を必ず書く。前の PR の「次の PR」か、
Issue の「いつ直すか」から作った PR では、`follow_up_of: <PR か Issue の番号>` も書く。① の振り分けは、
このキーの有無で変わらない（巡ごとの扱いは root `CLAUDE.md` 手順 6）。
他の PR の、まだリリースしていない断片（`plugins/gate-driven-development/changelog.d/`）の文を直すときは、
`amends: <断片のファイル名>, ...` も書く。この review-log と対になる断片をこの branch で足し、この review-log が
merge-base に無いときだけ、`tests/checks/version-not-consumed.sh` は宣言した断片の同じパスでの書き換えを通す
（削除・改名・`type:` の変更は通さない）。

plugin ディレクトリの外（repo root 直下）に置く理由: `plugins/gate-driven-development/`
はチームの共有 repo へ同期される配布物であり、開発の
記録を配布物に混ぜないため。

## 遡及しない範囲（cutoff）

この強制（`review-log-present.sh`）は、これを導入した PR（review-log 機能導入）が
`main` に取り込まれた**時点で `changelog.d/` に既に存在した断片には適用されない**。
実装上は「このブランチが統合先との merge-base 以降に足した断片」だけを検査対象に
する（`version-not-consumed.sh` と同じ merge-base 差分方式）ため、以下の断片は
恒久的に review-log 無しのまま残る。遡及的な作成はしない（スコープ外。X-52 参照）。

導入 PR 時点で `changelog.d/` に存在した断片（2026-09-14 時点、7 件）:

- `20260911-x36-parallel-regression-tests.md`
- `20260912-changelog-fragments.md`
- `20260912-regression-guard-and-diff-scoped-review.md`
- `20260912-x37-test-timing-flakiness.md`
- `20260912-x41-compact-suggestion.md`
- `20260913-planning-design-wiring-checks.md`
- `20260913-x33-subagent-dispatch-worktree.md`

この分は X-52 の効果測定（Codex・独立レビュー・PR 後の指摘件数の蓄積）から
恒久的に欠落する。X-45 の総件数比較にも使えない（X-52 の限界として PR 本文に
明記済み）。
