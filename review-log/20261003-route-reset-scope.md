---
lane: L1
pr: 346
follow_up_of: 339
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus)（旧#339 の次の PR の F2・F5。main の案は route のクリアを task-breakdown へ移して design_detail_only の部分リセットを届くようにするもので、Opus は部分リセットの規定を削って実際の挙動〔全セクションの初期化〕に合わせる案を推奨した〔main の案は batch_mixed の中の design_detail_only が none に落ちる穴と、書き込みとクリアの間のクラッシュで再分割・Fix Attempts の継承が二重にかかる穴が残る〕。実測: route と Next Action の整合を見る hook は無く、worklog 105 本のうち design_detail_only に触れるのは 1 本。食い違いのため信号 ① で Fable に 1 回相談し、Fable も Opus の案を推奨した〔逆戻り時の扱いも削る、断片に部分リセットが走っていなかったことを書く〕ので採った） | - | 0 | 0 | 0 | 2026-10-03T09:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4a4ccfec | 0 | 4 | 0 | 2026-10-03T10:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 84687019 | 0 | 1 | 0 | 2026-10-03T10:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| F1 | 独立-1 | medium | no | self-inflicted | 文言 | fixed | gdd-systematic-debugging の design_detail_only の復帰シーケンスが「影響タスクのみ再分割」のまま。この PR の目的（規定を実際の挙動にそろえる）が達成されないので、近道でも直した。commit: 84687019 |
| F2 | 独立-1 | medium | no | self-inflicted | 文言 | fixed | task-breakdown-steps.md 手順 2 が route で分けたままで、実際に届く再到達（route が none）に当たる項が無い。F1 と同じ理由で直した。commit: 84687019 |
| F3 | 独立-1 | medium | no | self-inflicted | 文言 | accepted | 並列 batch で 1 タスクだけ design_detail_only を出したとき（phase-progression.md:291）と batch_mixed が残る経路は、全セクションの初期化と食い違う |
| F4 | 独立-1 | medium | no | self-inflicted | 文言 | accepted | 削った Fix Attempts の継続・再分割の継承は、作り直しをまたぐ数え方として部分リセット以外にも目的があった。作り直しで Fix Attempts が 0 に戻る |
| F5 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 「全 revert 対象」の参照先が tasklist の節になっていた。code artifact 扱いの節に直した。commit: 84687019 |
| F6 | 独立-1 | low | no | inherited | 文言 | accepted | state-machine.md:431 の再評価マトリクスに「tasklist を部分保持するため」が残る |
| F7 | 独立-1 | low | no | inherited | 文言 | accepted | 並列 batch の carry-over の例外（phase-progression.md:271）に、task-breakdown 側から届く参照が無い |
| F8 | 独立-1 | low | no | self-inflicted | 文言 | accepted | design_detail_only で残した commit が満たす AC の task を、作り直した tasklist でどう扱うかが決まっていない |
| G1 | 独立-2 | medium | no | self-inflicted | 文言 | accepted | gdd-requirements-amendment/SKILL.md:104 が design_detail_only のとき影響 AC の task の部分再整備を許したまま（同じ規定の別の箇所） |
| G2 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 手順 2 の「route は none に戻っている」は並列 batch の batch_mixed では成り立たない |
| G3 | 独立-2 | low | no | self-inflicted | 文言 | accepted | systematic-debugging:272 の一律の作り直しが、並列 batch の単独発火（phase-progression.md:291）と食い違う（F3 と同じ） |
| G4 | 独立-2 | low | no | self-inflicted | 文言 | accepted | prompt-contract-map.md:25 が、作り直しは Route In Progress が決めると書いたまま |
| G5 | 独立-2 | low | no | self-inflicted | 文言 | fixed | 断片の参照先の段落が、code artifact 扱いへ向けた参照と合わない。commit: eab88507 |
| G6 | 独立-2 | low | no | self-inflicted | 文言 | fixed | 断片の「実際にはいつも」に根拠が無く、限界の記述（batch_mixed）が入っている。commit: eab88507 |
| G7 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 作り直しのたびに、同じ Current Task 単位のループ上限（escape hatch・2/2・root cause 3 連続・remediation ADR）の数えが途切れる（F4 と同じ型） |
| G8 | 独立-2 | advisory | no | self-inflicted | 文言 | accepted | design_detail_only でも Stage Continuity Source を戻すことが PR 本文・断片に無い |
| G9 | 独立-2 | advisory | no | inherited | 文言 | accepted | 並列 batch の human_recheck での Completed Tasks の持ち越しが全初期化と食い違う（F7 と同じ） |
| G10 | 独立-2 | advisory | no | self-inflicted | 文言 | accepted | 作り直しで commit 済みの task が TDD の Quarantine に入り、作り直しを繰り返すおそれ |
| G11 | 独立-2 | advisory | no | self-inflicted | 文言 | accepted | 手順 2 の 2 つ目の項の見出しが親の文と同じで読み分けにくい |
