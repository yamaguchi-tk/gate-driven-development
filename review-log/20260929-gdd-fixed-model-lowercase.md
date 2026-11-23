---
lane: L1
pr: 239
follow_up_of: 187
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4fb9af787c640596030d16b837803565ffb695a1 | 0 | 0 | 0 | 2026-09-29T20:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片が gdd-model-routing の変更箇所を「Claude Code のモデル使い分けと既定の節」と書くが、§ 初稿とレビューの 2 行（155・160 行目）も変えている |
| L2 | 独立-1 | low | no | inherited | doc-claim | accepted | `references/fixed-models.md:39` の general_heavy の所属の列挙に `gdd-requesting-code-review` が無い |
| L3 | 独立-1 | low | no | inherited | doc-claim | accepted | `skills/gdd-model-routing/SKILL.md:76` と `README.md:228` の Claude Code で `opus` を使う skill の列挙に `gdd-requesting-code-review` が無い |
| L4 | 独立-1 | advisory | no | inherited | test-power | accepted | skill の `## Fixed Model` の Claude Code 行を resolver の tier と突き合わせるテストが無く、`Sonnet` + medium に戻しても落ちない |
| L5 | 独立-1 | advisory | no | inherited | doc-claim | fixed | PR 本文の限界の節が、残したコードスパンでない散文を `subagent-dispatch.md` だけ挙げていた。種類で書き直した。commit: なし（PR 本文） |
| L6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が「なし」と行動を同じ行に書く。Claude Code では skill の中からモデルを切り替えられない |
| L7 | 独立-1 | advisory | no | inherited | test-power | accepted | `tests/checks/hooks.sh:848` の "Sonnet" の文言検査が gdd-model-routing:73 の散文 1 か所だけで通っている |
| L8 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence の有無を抜粋から確かめられない。PR 本文に対象外の理由を書いた。commit: なし（PR 本文） |
