---
lane: L1
pr: 399
follow_up_of: 392
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | bf85fd31 | 0 | 2 | 0 | 2026-10-07T00:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| N1 | 独立-1 | medium | no | self-inflicted | 取り直しの経路 | accepted | 差し戻しの後は実装が入っているので、取り直しは Pre-existing Implementation Without RED の隔離（既定 route は design_detail_only）か、Covers AC・Planned RED の無い task では task-breakdown への差し戻しに入る。これが書かれていない |
| N2 | 独立-1 | medium | no | self-inflicted | 取り直しの経路 | accepted | 取り直した RED で数えなかった節を置き換えるかが無く、古い節が残ると 1d が古い節を読んで差し戻し、TDD は新しい節で記録済みに数えて飛ばす |
| N3 | 独立-1 | low | no | self-inflicted | 受理集合 | accepted | Resume Check が数えない節と 1d が差し戻す節の集合が一致しない（形式 3 の verification: のパス、base の default branch、コマンド失敗の扱い） |
| N4 | 独立-1 | low | no | self-inflicted | 断片 | accepted | 断片が「TDD が隔離する」を成り立たないと書くが、TDD は既に差分のある task を隔離すると定めている |
| N5 | 独立-1 | low | no | self-inflicted | AC の紐付け | accepted | finding が AC を指さないときの扱いが無く、推定で書くと lint-ac が ERROR、AC の紐付けは task-breakdown の責務ともずれる |
| N6 | 独立-1 | low | no | inherited | 取り直しの経路 | accepted | rollback-patterns.md:137 は既存テストをそのまま RED 再現テストに使うことを許すが、その RED は 1d を通る形で記録できない |
| N7 | 独立-1 | low | no | self-inflicted | 文言 | accepted | TDD の Guardrails の Context Compaction Resilience（:293）が「RED Evidence の有無」で決める読み方のまま |
| N8 | 独立-1 | low | no | inherited | 文言 | accepted | 書き換えた行の「Step 9（実装 handoff）」は誤りで、実装 handoff は Step 10 |
