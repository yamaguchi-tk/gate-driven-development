---
lane: L1
follow_up_of: 494
pr: 旧#498
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2e217d7ce1b5cdc4c64af3809592ece0d02c931b | 0 | 0 | 0 | 2026-10-14T20:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の変異注入の項は、実装中に回したテストの結果の断定で、差分が変える挙動ではない |
| r1-2 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | pre-push gate の順序のテストが subTest の間で pre-push-optout.log を消さず、cwd 側が壊れると workdir の subTest も落ちて、どちらが壊れたか分からない（誤って通る向きの穴は無い） |
| r1-3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 足したコメントが、実測されていない「Codex は tool_input.workdir」を事実として書く（既存の 5 か所と同じ文言） |
| r1-4 | 独立-1 | advisory | no | inherited | test-power | accepted | pre-PR gate の、tool_input の値と最上位の cwd の読む順序のテストが、どちらの key でも無い |
| r1-5 | 独立-1 | advisory | no | inherited | doc-claim | accepted | test_merge_gate_hook_gate_activation.py:1278 の docstring が「harness は常に tool_input.cwd を送る」と書き、最上位の cwd の実測と食い違う |
