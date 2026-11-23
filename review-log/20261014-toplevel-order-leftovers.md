---
lane: L1
follow_up_of: 498
pr: 旧#499
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f3fe56a487d166dae5cd49088045992cacff17e6 | 0 | 0 | 0 | 2026-10-14T21:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | low | no | self-inflicted | test-power | accepted | 新しい pre-PR の順序テストはプロセスの cwd が tool_input の値と同じ root なので、PROJECT_ROOT がプロセスの cwd に戻るだけでも通る（その退行は test_pre_pr_gate_contract.py:432 が落とす） |
| r1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 書き換えた merge gate の docstring が実行先の key を tool_input.cwd だけに限り、Codex の workdir の経路を書いていない |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「片方の key が壊れるともう片方の subTest も落ちていた」は、先に回る cwd の key が壊れたときだけ成り立つ。commit: なし（PR 本文） |
| r1-4 | 独立-1 | low | no | inherited | doc-claim | accepted | test_merge_gate_hook_gate_activation.py:599-600 のテスト名とコメントが、harness が tool_input.cwd を送る前提を残している |
| r1-5 | 独立-1 | low | no | inherited | doc-claim | accepted | test_gates_toplevel_cwd.py の module docstring が、tool_input の値が先に効くことを書かず、pre-push gate がプロセスの cwd を移すように書いている |
