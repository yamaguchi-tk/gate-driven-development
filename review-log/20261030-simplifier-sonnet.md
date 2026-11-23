---
lane: L1
pr: 616
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5b5f8a53 | 0 | 2 | 0 | 2026-10-30T14:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 依頼の「一部を Sonnet に下げる」を費用 0.09% の 1 agent に狭め、費用の大きい agent を確かめずに対象外にした。依頼が 2 通りに読める（直前の案が挙げた 2 候補か、効く agent まで含むか）ので (b) としてユーザーに確かめ、推奨の「2 候補で閉じ、費用の大きい agent は別に測る」で進め、ユーザーがそれでよいと決めた（2026-10-30） |
| r1-2 | 独立-1 | low | no | self-inflicted | request-drift | accepted | Pro・Team への効き目を API 換算の金額で代えた。r1-1 と同じ問いで確かめ、ユーザーがそれでよいと決めた（2026-10-30） |
| r1-3 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 断片と fixed-models.md の「約 0.7 倍」が、alias が最新の Sonnet に解決される前提を書いていない。1 つ前の版なら約 1.24 倍（断片:7、fixed-models.md:66） |
| r1-4 | 独立-1 | low | no | self-inflicted | product | accepted | opus 必須の工程で simplifier に出る警告が、worker 向けの案内のまま（run-agent-dispatch-model-gate-hook.sh:144-152） |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | sonnet に固定して frontmatter で判定する agent を worker だけと書く箇所が残る（fixed-models.md:12、agent_dispatch_gate.py:65-73） |
| r1-6 | 独立-1 | low | no | self-inflicted | style | accepted | fixed-models.md:66 が同じファイルの「版数を書かない」規定に反して「Sonnet 5.5」と書く |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「テストが赤なら変更を捨てるので、誤りは後段で拾われる」が保証より広い（fixed-models.md:66） |
| r1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | model を明示した simplifier の起動の警告が overrides_fixed から工程の判定に変わったことが、PR 本文と断片に無い（agent_dispatch_gate.py:237） |
| r1-9 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の type: minor が、model・effort を変えた直近の断片の patch と揃っていない |
| r1-10 | 独立-1 | advisory | no | self-inflicted | style | accepted | 新しいテストの前の空行が 2 行で、モジュールの docstring に簡素化パスが無い（test_implementation_worker_agents.py:163-165） |
| r1-11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 依頼の原文に、番号で答えた assistant の問いと「Sonnet 化に進む」が指す問いが無い。.request.md に引用と、この PR が扱う行を足した。commit: なし（review-log） |
