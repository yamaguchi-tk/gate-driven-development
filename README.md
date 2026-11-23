# gate-driven-development

GDD（Gate-Driven Development）は、方向性を決めたら AI が完走する、Claude Code・Codex・Cursor 向けの軽量オーケストレーターです。要件整理 → 人間の確認 → 設計 → TDD → 実装 → レビュー → PR を、工程ごとの gate を付けて一気に進めます。

使い方・導入・費用の目安は [plugins/gate-driven-development/README.md](plugins/gate-driven-development/README.md) にあります。

## 導入（Claude Code）

```text
/plugin marketplace add yamaguchi-tk/gate-driven-development
/plugin install gate-driven-development@gate-driven-development
```

## この repo の履歴

この repo は、作者の private repo から GDD だけを切り出して、1 commit で始めています。文書の中の `#NNN` は、切り出す前の private repo の PR 番号で、この repo の Issue・PR とは別のものです。

この repo 自身の開発ルールは [CLAUDE.md](CLAUDE.md) にあります。

## ライセンス

[MIT](LICENSE)
