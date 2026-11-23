---
lane: L1
pr: 614
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 759ce4e1 | 0 | 3 | 0 | 2026-10-30T10:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | fixed-models.md の相談役の段落の後半に「人に表示する前の相談だけは Opus high と Fable medium を並べる」と、変更前の組を指す「並行の 2 本は…金額は未測」が残り、書き換えた前半と食い違う（fixed-models.md:66） |
| r1-2 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 依頼の 3 項目のうち Sonnet 化と README の費用の節を、確かめずに次の PR に回した。別の agent 定義と計測・README に広がるので (c) としてユーザーに確かめ、ユーザーが分けると決めた（2026-10-30） |
| r1-3 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | autonomy.md § 限界から `並行` を外したので、Codex・Cursor で委任先 `並行` が人間に止まらなくなった。挙動の変化が PR 本文と断片に無く、別コンテキストを 2 つ起動するかも書いていない（autonomy.md:12, 23） |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docs/claude-md-rationale.md の規則の引用（158、216-218）が、書き換えた・消した CLAUDE.md の文のまま |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | test_stop_hook_autonomy_pushback.py:182 の docstring が `並行` を「Opus と Fable に並行で相談」と説明している |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 項目 7 の「片方の相談を済ませていれば、もう片方だけ」と `Opus unavailable` が、2 本の Opus と委任先 fable の相談の組み合わせで決まらない（human-check-template.md:54、CLAUDE.md:152） |
| r1-7 | 独立-1 | low | no | self-inflicted | product | accepted | 信号 ① が、2 本のうち 1 本だけ main と違うとき・2 本が割れたときに発火するかが読めない（CLAUDE.md:208, 212） |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の Fable の起動条件に、description に残る「利用する repo の規則が名指ししたとき」が無い（断片:7） |
| r1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「費用は半分以下」の比べ先は 10-14 時点の定義の組で、断片の Summary に但し書きが無い（断片:7、fixed-models.md:66） |
| r1-10 | 独立-1 | advisory | no | self-inflicted | product | accepted | 当て直しは「後で正しかった側」で採点しており、Fable の役（ユーザーの選択との一致）は測っていない。PR 本文の限界に書くとよい |
