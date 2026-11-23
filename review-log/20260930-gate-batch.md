---
lane: L1+
pr: 旧#248
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Fable 設計相談 (general-purpose, model: fable)（ユーザーが 2026-09-30 に自律進行を承認し、確認は内部の相談で代えた。当初の「round 上限と code-simplifier の撤去」を Gate Batch に置き換え、codex-1 の後に判定の単位を batch 全体にする案 D を確かめた） | - | 0 | 0 | 0 | 2026-09-30T00:00+09:00 |
| codex-1 | Codex adversarial-review, 全差分 | e1b80f01 | 3 | 0 | 3 | 2026-09-30T00:15+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 6088df77f01dcabf505718e00f1dfe1e5739ac49 | 0 | 7 | 0 | 2026-09-30T00:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 1613a9dcb3e24126c81f43a309cfd1c289f3f358 | 1 | 2 | 1 | 2026-09-30T01:05+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | d314dc46d113f98852339381b5f4768e59f166ef | 0 | 0 | 0 | 2026-09-30T01:28+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P0 | 方針メモ | advisory | no | self-inflicted | design | fixed | round 上限だけでは gate の本数が減らない（本数は task の数 × task ごとの gate で決まる）。逐次の task を batch にまとめて gate を 1 回にする案に置き換えた。commit: e1b80f01 |
| C1 | codex-1 | high | no | self-inflicted | verdict-unit | fixed | task ごとの混合判定を書いたが、impl-gating の返却と Review Status は gate 全体で 1 つの状態しか持たない。batch を 1 つの gate 単位で判定する。commit: 6088df77 |
| C2 | codex-1 | high | no | self-inflicted | wiring | fixed | 文脈を注入する hook は Current Task の先頭の task を読むが、先頭は実装を終えた task だった。実装中の task を先頭に置き、hook を実際に起動するテストを足した。commit: 6088df77 |
| C3 | codex-1 | high | no | self-inflicted | wiring | fixed | canonical state の「Current Task は 0 または 1 件」が Gate Batch の状態を不正にしていた。件数制約に Gate Batch を足した。commit: 6088df77 |
| F1 | 独立-1 | medium | no | self-inflicted | verdict-unit | fixed | 差し戻しの規定が Step 11 にあり、Round 非消費の finding でも batch 全体が差し戻された。Step 9 に移し、Round 消費 category に限った。commit: 1613a9dc |
| F2 | 独立-1 | medium | no | self-inflicted | wiring | fixed | Fix Attempts の書き手が impl-gating と systematic-debugging の 2 つになった。systematic-debugging だけに戻し、対象の task に足す。commit: 1613a9dc |
| F3 | 独立-1 | medium | no | self-inflicted | verdict-unit | fixed | RED Evidence の照合・security の適用判定が単一の Current Task のままだった。batch の全 task に当てる。commit: 1613a9dc |
| F4 | 独立-1 | medium | no | inherited | doc-claim | fixed | Execution Status: completed の定義が gate 通過後で、gate 前の目印に使えなかった。実装の手順 12b に揃えた。commit: 1613a9dc |
| F5 | 独立-1 | medium | no | self-inflicted | wiring | fixed | 差し戻し後に直す task が決まらなかった（全 task が completed）。対象の task を in_progress に戻して先頭に移す。commit: 1613a9dc |
| F6 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 「hook は先頭の task だけを読む」は task 名だけに当てはまる。主張を狭め、ほかの field の読み方をテストで固定した。commit: 1613a9dc |
| F7 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 文書の語だけを assert するテストが root CLAUDE.md § テストに反していた。消して、Skill RED-GREEN Evidence で代えた。commit: 1613a9dc |
| F8 | 独立-1 | low | no | self-inflicted | wiring | fixed | 手順 17 が次の task を Pending Tasks から外すと書いていなかった。commit: 1613a9dc |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 「current task ごとに selection」などの単一 task の記述が reviewer-selection.md・self-contained-contract.md・phase-progression.md に残る（references の行予算に空きが無い） |
| F10 | 独立-1 | low | no | inherited | product | next-pr | compact の提案が batch の task の数だけ出る（compact_suggestion.py のキーが task 単位） |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の telemetry の記述が実装（最初の Fix Attempts だけを読む）と合わなかった。記述を削った。commit: 1613a9dc |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | Loop Safety の閾値の扱いが限界に書かれていなかった。PR 本文に書いた。commit: 1613a9dc |
| F13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence を PR 本文に残す |
| F14 | 独立-1 | advisory | no | inherited | doc-claim | out-of-diff | task-breakdown SKILL.md の見出しの雛形 `### Task N:` と references の `### Task: T-N` が食い違う |
| F15 | 独立-2 | high | no | self-inflicted | wiring | fixed | ADR の Origin の単位を一部だけ Gate Batch <N> に変え、書き手・読み手・検査が食い違った。変更を取り消し、task ごとに数える（task ごとの gate と同じ）。commit: d314dc46 |
| F16 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 断片と PR 本文の「Loop Safety を batch で共有する」が Fix Attempts の数え方と逆だった。断片から削り、PR 本文の限界を直した。commit: d314dc46 |
| F17 | 独立-2 | medium | no | self-inflicted | wiring | fixed | Gate Batch の差し戻しが Step 9 にしか無く、Step 1・1d・8a の出口に届かなかった。全出口に当て、TDD の対象も揃えた。commit: d314dc46 |
| F18 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | hook の読み方の説明（Last Error は置き換わる、plan reread の AC は最初の task）を実態に合わせた。commit: d314dc46 |
| F19 | 独立-2 | low | no | inherited | wiring | out-of-diff | UserPromptSubmit は `### Task:` の見出しだけを受け付け、雛形の `### Task N:` では task 名を注入しない。PR 本文の限界に書く |
| F20 | 独立-2 | low | no | inherited | product | re-reported | compact の提案が batch の task の数だけ出る（F10 の再報告） |
| F21 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 「skill 本文の変更は RED-GREEN で確かめた」の範囲を、手順 17 と Step 9 の差し戻しに絞った。commit: d314dc46 |
| F22 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | completed の定義を手順 12b の条件（REFACTOR など）まで揃えた。commit: d314dc46 |
| F23 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | 断片に限界の文が入っていた。PR 本文に寄せた。commit: d314dc46 |
| F24 | 独立-2 | advisory | no | inherited | doc-claim | out-of-diff | Execution Status の値の集合が `pending` と `not_started` で違う |
| F25 | 独立-3 | medium | no | self-inflicted | wiring | next-pr | Gate Batch で ADR の Origin に何を書くか（先頭・対象の task）と、8a が finding 無しで発火したときの対象の task が決まっていない。state-machine.md § Remediation Loop Safety に 1 文足す |
| F26 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | Escape Hatch の「同じ Current Task に 5 回連続」を、batch の全 task を changes_requested にする Step 9 と合わせて読むと共有にも読める。対象の task だけで数えると書く |
| F27 | 独立-3 | low | no | self-inflicted | wiring | next-pr | 対象の task を決められない finding（Worktree が解決できない、どの task にも属さない scope 外の変更）の扱いが無い。batch の全 task を対象にする |
| F28 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | task-breakdown-steps.md § Gate Batch の要約が「Round 消費の finding」のままで、Step 9 の「どの出口からも」に追随していない |
| F29 | 独立-3 | low | no | inherited | wiring | next-pr | 実装の手順 1b が Gate Batch の限定なしに in_progress を書く。2b の対象の task だけにする |
| F30 | 独立-3 | low | no | inherited | product | re-reported | compact の提案が batch の task の数だけ出る（F10 の再報告）。PR 本文の「compact の提案は batch で共有する」も直す |
| F31 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | PR 本文の Skill RED-GREEN Evidence に、走らせた本文の版と scenario の範囲を書いた |
| F32 | 独立-3 | advisory | no | self-inflicted | bookkeeping | next-pr | 断片の Validation に件数（pressure scenario 2 本）が入っている。リリースで直す |
| F33 | 独立-3 | advisory | no | inherited | doc-claim | next-pr | 実装中の task を先頭に置く契約の hook の列挙に SessionStart が無い（挙動は正しい） |
| F34 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | テストの docstring は計画の X-94（決定の記録）、PR 本文は X-93 の改善 2（改善の一覧）を指す。どちらも同じ計画ファイルの節 |
