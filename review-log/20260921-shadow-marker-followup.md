---
lane: L1
pr: 旧#167
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e78b9ce7806e0bbedcb84043e3f1069892b99139 | 0 | 0 | 0 | 2026-09-21T22:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c9cd7c74fdf08d9d0bd1c85667b9aa1dae33e263 | 0 | 0 | 0 | 2026-09-21T22:35+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | low | no | inherited | requires-status-check-redundant | fixed | `requires_status_or_resume` が `primary == gdd` しか見ておらず、`expected.primary` と同じことしか検査していなかった（status 側の値が消えて別名になった）。route が `gate-driven-development:gdd-status` を含むことを求める形にし、status 以外の route を落とすテストを先に書いて RED を確認した（6c8812ae） |
| A2 | 独立-1 | low | no | self-inflicted | fragment-user-action | fixed | 断片の User Action Required が「なし」と書いたうえで、それだけでは直らない手順を指示していた。「なし」だけにした（6c8812ae） |
| A3 | 独立-1 | advisory | no | self-inflicted | fragment-claim-overstated | accepted | 断片の「以前は shadow_marker: true のとき gdd_status_required を返していた」は、旧分岐の条件（active の PR 後対応・superpowers 明示の例外）を省いている。利用者への誤った手順ではない。PR 本文に列挙 |
| B1 | 独立-2 | advisory | no | self-inflicted | requires-status-name | accepted | `requires_status_or_resume` の名前とエラー文は resume も受け付けるように読めるが、このモデルに resume の route は無く、受け付けるのは gdd-status だけ。将来 resume の route を足すと落ちる向き（fail-closed）。PR 本文に列挙 |
| B2 | 独立-2 | advisory | no | self-inflicted | requires-status-overlap | accepted | 既存の fixture 3 箇所では、この field は `route_contains: gdd-status` と同じことを見ている。独立して効くのは新しいテスト 1 本。欠陥ではない。PR 本文に列挙 |
| B3 | 独立-2 | advisory | no | self-inflicted | test-class-placement | accepted | `test_requires_status_or_resume_rejects_non_status_route` が shadow_marker 用の class（`ShadowMarkerInputIgnoredTests`）に入っている。挙動には影響しない。PR 本文に列挙 |
