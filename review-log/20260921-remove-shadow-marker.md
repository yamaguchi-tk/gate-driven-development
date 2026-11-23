---
lane: L1
pr: 旧#166
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8813fa49f116578a546753f98b637699b2f1892a | 0 | 0 | 0 | 2026-09-21T20:45+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | be20a5520cfb9083026422b5a020c87877e34390 | 0 | 0 | 0 | 2026-09-21T21:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | low | no | self-inflicted | stale-output-point-count | fixed | shadow-marker の出力枝を消して SessionStart の出力点が 6 になったのに、hook のコメント（不変条件・sanitize・消費の説明）と `test_hook_injection_security_contract.py` の docstring が 7 のままだった。hook は 6 と内訳（前 2 経路の 3 箇所＋if/elif/else の 3 枝）に直し、テストの docstring は数を外した（e32f252c） |
| A2 | 独立-1 | low | no | self-inflicted | removal-claim-overstated | fixed | 断片の「走査しない」と doc の「現在の checkout の steering だけを見て」が、else 枝の `has_steering_history`（各 worktree の `.steering/` の有無を見る）より広かった。「state.md を読まず、案内もしない。`.steering/` の有無だけは見る」に狭めた（e32f252c） |
| A3 | 独立-1 | advisory | no | self-inflicted | release-note-add-and-remove | accepted | 未リリースの 20260917-shadow-marker-* の断片 2 本と、この撤去の断片が次の版に並ぶ。断片と review-log の 1 対 1 対応を保つため古い断片は消さない。PR 本文に列挙 |
| B1 | 独立-2 | low | no | self-inflicted | pr-body-claim | fixed | PR 草案の「削除のみ。追加行なし」が、同じファイルのコメントの書き換え（出力点の数と内訳）と食い違っていた。PR 本文を「shadow 関連は削除のみ」と「コメントの出力点の数と内訳を直した」に改めた（PR 本文だけの修正） |
| B2 | 独立-2 | low | no | inherited | sanitize-claim-overstated | next-pr | hook:128「既存 6 出力点と同じ 3 段 sanitize」は、サイクル上限の警告（エスケープ 2 段のみ）と既定の案内（固定文）に当てはまらない。数字は差分で直したが断定は前から。最終の全差分巡の後の差分巡で出た blocking でない low で、直すと hook が変わり巡が無効になるため、次の PR で直す |
| B3 | 独立-2 | low | no | inherited | post-merge-seed-path | out-of-diff | post-merge seed の書き手（`<cwd>/.claude/`）と SessionStart の読み手（`${HOME}/.claude/`）のパスがずれている。差分の外。実データでは取り残された seed ファイルが HOME 側にも repo 側にも無く（2026-09-21 確認）、該当なし |
