---
lane: L1
pr: 402
follow_up_of: 399
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e0f5df88 | 0 | 4 | 0 | 2026-10-07T00:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | d5b12d88 | 0 | 2 | 0 | 2026-10-08T00:00+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 6addf4cc | 0 | 3 | 0 | 2026-10-08T00:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| T1 | 独立-1 | medium | no | self-inflicted | 取り直しの経路 | fixed | 新しい取り直しの経路は節がある task にだけ書かれ、節の無い task は差し戻しの後も隔離の既定 route（design_detail_only）に入る（ユーザーの指示で直した。commit: d5b12d88） |
| T2 | 独立-1 | medium | no | self-inflicted | 受理集合 | fixed | default branch の決め方の指し先（gdd-using-git-worktrees）は local の main を使い、gate runner の origin/HEAD の解決と食い違う（ユーザーの指示で直した。commit: d5b12d88） |
| T3 | 独立-1 | medium | no | self-inflicted | 取り直しの経路 | fixed | 隔離の 2・3 だけを指し、無効化した実装を戻す 4 が抜けていて、無効化したまま handoff へ進みうる（ユーザーの指示で直した。commit: d5b12d88） |
| T4 | 独立-1 | medium | no | self-inflicted | AC の紐付け | fixed | AC: 行の無い節を作る規定が、TDD の AC ID Binding（必須・reject）と食い違う（ユーザーの指示で直した。commit: d5b12d88） |
| T5 | 独立-1 | low | no | self-inflicted | 取り直しの経路 | accepted | 古い節と新しい節が並ぶ task の扱いが、Step 1（節単位）と Guardrails（task 単位）で読み分かれる |
| T6 | 独立-1 | low | no | self-inflicted | 文言 | accepted | rollback-patterns の「差分に入る形で書く」が、書き写さない task にまで掛かり理由より広い |
| T7 | 独立-1 | low | no | self-inflicted | 取り直しの経路 | accepted | Express で使えない design_detail_only を戻し先に挙げている |
| T8 | 独立-1 | low | no | self-inflicted | 取り直しの経路 | accepted | 取れたときに隔離の記録と quarantine handoff を出すかが書かれていない |
| T9 | 独立-1 | low | no | self-inflicted | 文言 | accepted | Covers AC が無いときの戻し先は Step 2 ではなく § AC ID Binding にある |
| T10 | 独立-1 | low | no | inherited | 受理集合 | accepted | Step 1d 側で形式 3 の分け方・test: のパスの正規化・見出しの変種が未定義のまま、TDD が「同じ」と指す |
| T11 | 独立-1 | low | no | inherited | 取り直しの経路 | accepted | Covers AC・Planned RED の無い remediation task を受ける task-breakdown の手順が無い |
| T12 | 独立-1 | advisory | no | self-inflicted | 断片 | accepted | 未リリースの 20261007-red-evidence-followups の断片が、差し替える前の AC の規定を書いている |
| T13 | 独立-1 | advisory | no | self-inflicted | 帳簿 | accepted | CONTRIBUTING 1b の Superpowers Benchmark Summary が材料に無い |
| U1 | 独立-2 | medium | no | self-inflicted | 取り直しの経路 | fixed | 「差し戻しの後」を判定する欄が無く、2 本目以降の task（逐次・Gate Batch）でも production の差分があるので characterization の経路に入り、実装を戻す確認を満たせず design_detail_only に戻されうる（ユーザーの指示で直した。commit: 6addf4cc） |
| U2 | 独立-2 | medium | no | self-inflicted | 取り直しの経路 | fixed | 「別の worktree で確かめる」が TDD runner の Worktree Binding Precheck（Bash は ## Worktree で実行）と食い違う（ユーザーの指示で直した。commit: 6addf4cc） |
| U3 | 独立-2 | low | no | self-inflicted | 取り直しの経路 | accepted | Quarantine Output Contract は今も無条件に quarantine handoff・既定 design_detail_only を求め、Step 1 の出口と食い違う |
| U4 | 独立-2 | low | no | self-inflicted | 取り直しの経路 | accepted | 実装を戻して pass しなかったときの行き先が無い |
| U5 | 独立-2 | low | no | self-inflicted | 取り直しの経路 | accepted | 一時 commit の方式で戻す操作が「未 commit の差分を捨てる操作は使わない」と字面で衝突し、一時 commit を外す手順・.steering/ を入れないことが無い |
| U6 | 独立-2 | low | no | self-inflicted | AC の紐付け | accepted | 例外の節と書き忘れの節を、節の中身から見分けられない |
| U7 | 独立-2 | low | no | self-inflicted | AC の紐付け | accepted | README:95・TDD SKILL.md:128・:291 の AC 必須の記述に例外への指し先が無い |
| U8 | 独立-2 | advisory | no | self-inflicted | AC の紐付け | accepted | lint-ac の WARN 文言が、例外の節にも AC: 行を足すよう指示する |
| U9 | 独立-2 | low | no | self-inflicted | 受理集合 | accepted | impl-gating Step 1・1c と手順 17 は default branch の決め方を gdd-using-git-worktrees に任せたままで、TDD の origin/HEAD の決め方と書き分かれる |
| U10 | 独立-2 | low | no | self-inflicted | 文言 | re-reported | Covers AC が無いときの戻し先は Step 2 ではなく § AC ID Binding（T9 の再掲） |
| U11 | 独立-2 | low | no | self-inflicted | 文言 | fixed | PR 本文の抜粋で主語の #### RED Evidence が抜けていた（commit: なし（PR 本文）） |
| U12 | 独立-2 | low | no | self-inflicted | AC の紐付け | fixed | AC: の無い節は AC Drift / Spec Drift で追えないことが PR 本文の限界に無い（commit: なし（PR 本文）） |
| V1 | 独立-3 | medium | no | self-inflicted | 取り直しの経路 | accepted | 一時 commit ができなかったとき（nothing to commit・hook の失敗）も git reset --soft HEAD~1 を実行し、直前の本物の commit を branch から外しうる |
| V2 | 独立-3 | medium | no | self-inflicted | 取り直しの経路 | accepted | 「base の内容」が未定義で、default branch と読むと前の task の変更も外れて wrong failure を RED と取り、一時 commit の親と読むと何も外れない。Create: のファイルの外し方も無い |
| V3 | 独立-3 | medium | no | self-inflicted | 取り直しの経路 | accepted | Files: が無い task（Express・completion-check の remediation task）では、新しい条件を判定できない |
| V4 | 独立-3 | low | no | self-inflicted | 取り直しの経路 | accepted | 一時 commit から reset までの間に中断すると、再開時に戻す手立てが無く実装が迷子の一時 commit に残る |
| V5 | 独立-3 | low | no | self-inflicted | 取り直しの経路 | accepted | § Pre-existing の発火条件（:46）が task を区別せず、Gate Rounds 0 を通常の Step 2〜4 にする Step 1 と逆を指す |
| V6 | 独立-3 | low | no | inherited | 取り直しの経路 | accepted | 記録が無効と判定された節は、実装が無くても characterization RED に回り、pass の確認が成り立たない |
| V7 | 独立-3 | low | no | self-inflicted | 文言 | fixed | PR 本文で Step 1d の項目の後ろの「同：」が Step 1d を指してしまう（commit: なし（PR 本文）） |
| V8 | 独立-3 | advisory | no | self-inflicted | 文言 | accepted | category の明記が Step 1d の 2 つ目の High にしか付いていない |
| V9 | 独立-3 | advisory | no | inherited | 文言 | accepted | TDD の dispatch の 対象の差分: なし と、SKILL が求める git 操作の関係が曖昧 |
