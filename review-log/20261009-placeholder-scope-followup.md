---
lane: L1
pr: 420
follow_up_of: 411
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承, CLAUDE.md・memory 入り | cdfb3e2a | 0 | 0 | 0 | 2026-10-09 |
| 独立-2 | general-purpose, 差分, model: opus, effort 継承, CLAUDE.md・memory 入り | 70bbe17e | 0 | 0 | 0 | 2026-10-09 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 独立-1 | low | no | self-inflicted | request | fixed | 対象外を「語そのものを扱うコード例」に狭めたので、requirements.md・design.md の通常のコード例の `TODO` まで禁止の対象に広がった（依頼は tasklist の `Actual code` だけを問題にしている）。対象外をコード例全般に戻し、tasklist の `Actual code` に書く実装だけを対象にした。commit: 6b5c09e8 |
| P2 | 独立-1 | low | no | inherited | doc-claim | accepted | `skills/gdd-task-breakdown/SKILL.md` § No Placeholders ポリシー（:97）は TBD・TODO を対象外なしで並べ、正本の対象外を指していない |
| P3 | 独立-1 | low | no | inherited | doc-claim | accepted | `CONTRIBUTING.md` § レビュー観点の表（:234）の「プレースホルダー混入」の行が、対象外と見る範囲を書いていない |
| P4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片は SKILL.md の Plan Self-Review Contract 2 が正本を指すと書くが、実際は Task Self-Review 6 を経由した間接の参照 |
| P5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | `Actual code` の中で `TODO` を検出・入力として扱う箇所が、対象か対象外かどちらとも読める |
| P6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 正本は「`Actual code` に書く実装の `// TODO`」、`task-breakdown-steps.md:378` は「`Actual code` の `// TODO`」で、RED step のテストのコードの `// TODO` の判定が文書によって割れる |
| P7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「`// TODO` だけは対象」が、`# TODO`・`/* FIXME */`・`TBD` など、ほかの書き方と語を対象外と読ませうる |
