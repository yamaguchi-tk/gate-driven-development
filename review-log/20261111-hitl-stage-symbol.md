---
lane: L1
pr: 656
follow_up_of: 651
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 85d55ccacb203e8617ab2bce78954c1b64eb0a28 | 0 | 1 | 0 | 2026-11-11 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 107d19eeff8f495f3844240abd4883a5f258d197 | 0 | 0 | 0 | 2026-11-11 |
| 独立-3 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | a87d0080351b4ab0e931830404291648beab6ab0 | 0 | 0 | 0 | 2026-11-11 |
| 独立-4 | general-purpose, 差分（確かめ）, model: opus, effort 継承, CLAUDE.md・memory 入り | 65af296b928ac95ccc8898a295cd62f9b2a758d7 | 0 | 0 | 0 | 2026-11-11 |
| 独立-5 | general-purpose, 差分（確かめ）, model: opus, effort 継承, CLAUDE.md・memory 入り | 060fcb6b27576a1d903f0aca0b55de3591fe0327 | 0 | 0 | 0 | 2026-11-11 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | human-check-template.md:511 の express の Stage Continuity Brief を完全省略しない規定が、必須ルール 19（段階が 1 つなら書かない）と食い違う commit: 107d19eef |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | brainstorming-steps.md:65 の (4) が既存とぶつかるをそのまま載せるのままで、# を外す規定と合わない commit: 107d19eef |
| I1-3 | 独立-1 | low | no | self-inflicted | test-power | fixed | stage=none のとき段階以外の必須語も外す変異をテストが検出しない commit: 107d19eef |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | hitl_lint_gate.py:17-22 の docstring が段階実装の語を無条件に見ると書く commit: 107d19eef |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | DISTRIBUTION_READINESS.md:144・:195 が必須フレーズ 6 語を無条件に書く commit: 107d19eef |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | task-breakdown-steps.md:87 が単一段階でも Brief の欄が出る前提の文のまま commit: 107d19eef |
| I1-7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 変更断片の Validation に変えたテスト 2 本が無い commit: 107d19eef |
| I1-8 | 独立-1 | advisory | no | self-inflicted | style | fixed | テストのコメントが警告だけの lint を block 対象と呼び、消えた _hitl_check_points を参照する commit: 107d19eef |
| I1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | human-check-template.md:46 の 8 項目の 8 番目が条件付きになったことが冒頭に無い commit: 107d19eef |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | DISTRIBUTION_READINESS.md:195 の 後者 が 6 語のどれか読めない commit: a87d00803 |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | gdd-resume.md:75 の段階実装サマリーの条件が正本より狭い commit: a87d00803 |
| I2-3 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | stop marker が複数のときの条件を単数で書いている commit: a87d00803 |
| I2-4 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 新しいテストが確かめる段階以外の必須語が 1 語だけ |
| I2-5 | 独立-2 | advisory | no | self-inflicted | style | fixed | hitl_lint_gate.py の docstring の 1 行が折り返し幅を超える commit: a87d00803 |
| I3-1 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | human-check-template.md:7 の段階実装サマリーの条件が複数段階のときのままで、再承認の回が抜ける commit: 65af296b9 |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 規則 19 と lint 3 本の注釈が stage=none を見る条件を単数の marker で書く commit: 65af296b9 |
| I3-3 | 独立-3 | advisory | no | self-inflicted | style | fixed | hitl_lint_gate.py の docstring の折り返しが 1 行だけ長い commit: 65af296b9 |
| I4-1 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | lint-hitl-required-fields.py の docstring だけ、stage=none を見る条件が「すべての marker」になっていない commit: 657ce7d24 |
| I4-2 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | marker が 0 個のとき「すべて」が空真と読める。実装は文書末尾を 1 点として読み、表示・言語の lint は marker を求めるので実害なし |
| I4-3 | 独立-4 | advisory | no | inherited | bookkeeping | accepted | reviewer の環境に Grep・Glob が無く、Bash の read-only コマンドで代えた |
| I5-1 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋が stage=none の条件を単数の marker で書く commit: なし（PR 本文） |
| I5-2 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | marker が 0 個のときの扱い（文書末尾直前のタグ）が規定の文から読めない。実装は外さない側に倒れる（I4-2 と同じ） |
