---
lane: L1
pr: 旧#206
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 42e9e66e055491fe5ec651dacba37f3e48ea7939 | 0 | 3 | 0 | 2026-09-28T18:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 00049f7c846167c15b592abc7a7ec0377a0420b1 | 0 | 0 | 0 | 2026-09-28T19:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| N1 | 独立-1 | medium | no | self-inflicted | guidance-scope | fixed | PR URL の無い cancelled の steering が残ると merge gate の pr-url-unrecorded を抜けられない。節・断片に影響と出口を書いた（00049f7c）。gate 側の数え方は次の PR |
| N2 | 独立-1 | medium | no | self-inflicted | guidance-scope | fixed | PR が open の steering しか外せないときの手順が無く、除外の理由も誤り。節に手順と理由を書いた（00049f7c） |
| N3 | 独立-1 | medium | no | self-inflicted | guidance-scope | fixed | cancel をユーザーに確かめずに行うよう読め、abandon-and-pause の規定と食い違う。案内 3 か所と節に確認を足した（5376facf、00049f7c） |
| N4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | done guard を移動しない理由に挙げていたが cancelled でも検査は戻らない（00049f7c） |
| N5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | どの検出も候補から外す・tasklist は読まれないは言い過ぎ（handoff の読み手）。範囲を絞り、handoff は限界に書いた（00049f7c） |
| N6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | TROUBLESHOOTING の早見表が tasklist の Next Action=cancelled のまま（00049f7c） |
| N7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | TROUBLESHOOTING の同じ節の stale steering の片付けが移動・削除を案内したまま（00049f7c） |
| N8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | pre-PR hook のコメントが移す手順のまま（00049f7c） |
| N9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 正本の節が Route In Progress のクリアを書いていない（5376facf、00049f7c） |
| N10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の telemetry の説明が実装と違う（PR 本文で直した） |
| N11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 未リリースの断片 2 本が移す案内のまま。通常の PR では書き換えられないので、次のリリースで直す一覧に足し PR 本文に書いた |
| N12 | 独立-1 | advisory | no | inherited | product | accepted | gdd_task_binding.py の _field は注記つきの cancelled を非終端と見る（診断の出力だけ） |
| P1 | 独立-2 | low | no | self-inflicted | test-power | next-pr | Route In Progress の assert が語の有無だけで、none にする指示を pin していない |
| P2 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | .steering/ の外へ移すと git の管理外に落ちるは向きが逆（ignore と raw steering 検査から外れて git に見える） |
| P3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | gdd-using-git-worktrees の stale 片付けと find-stale-steerings.sh の提案が archive・discard のまま |
| P4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | abandon-and-pause の pre-PR は tasklist を読むの主語が pre-PR 全体に読める（done 判定は tasklist 先） |
| P5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Changed が参照先を示すのは pre-push だけと読める |
