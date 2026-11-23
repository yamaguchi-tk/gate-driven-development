---
lane: L1
pr: 369
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c35e9d315044bb748aa569783d85a3d73933e157 | 0 | 3 | 0 | 2026-10-05T00:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | ed7448beab05b66c6b9c8b760124735351a25e6e | 1 | 3 | 1 | 2026-10-05T01:20+09:00 |
| 方針メモ-1 | Opus 設計レビュー (general-purpose, model: opus, effort 継承) | ed7448beab05b66c6b9c8b760124735351a25e6e | 0 | 0 | 0 | 2026-10-05T01:30+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | fcb791e2e1dce61c08ed3041e25cee845384caff | 1 | 0 | 1 | 2026-10-05T10:40+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 7e18ad32224b2968b473feb4db81f1285c8065a4 | 0 | 0 | 0 | 2026-10-05T11:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | product | fixed | 「同じテストを回し直さず」が禁止の形で、同じ入力で繰り返して比べる手順（E2E の一貫性確認、flaky の再現率）とぶつかる。許可の形にし、その手順を対象外にした（近道では next-pr だが、ユーザーの指示でこの PR で直した） commit: 70dfc8ce |
| F2 | 独立-1 | medium | no | self-inflicted | product | fixed | 条件が「自分が変えていなければ」で、ユーザーのターンや compaction をはさんだ古い結果も通す。ユーザーの発言と compaction をはさまない起動に限り、誰が変えたかを問わず git status と git diff HEAD で確かめる形にした（ユーザーの指示でこの PR で直した） commit: 70dfc8ce |
| F3 | 独立-1 | medium | no | self-inflicted | product | fixed | reference の Iron Law・Gate Function・Common Failures、completion-check、ac-verification が「前の実行は使わない」のまま食い違う。置き換えで例外に揃えた（ユーザーの指示でこの PR で直した） commit: 70dfc8ce |
| F4 | 独立-1 | low | no | self-inflicted | product | fixed | gate は Step の間に .steering/ を書くので「1 つも変えていなければ」が成り立たない。.steering/ 以外のファイルに限った commit: 70dfc8ce |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | Skill RED-GREEN Evidence が sonnet だけで、回し直すべき場面が無い。opus で 5 場面を取り直し、PR 本文に書く commit: なし（PR 本文） |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Summary が、runner の行が SKILL.md の Step より優先することを書いていない commit: 70dfc8ce |
| F7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文に Superpowers Benchmark Summary の行が無い。PR 本文に書く |
| G1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 同じ起動の中の結果の確かめ方（git status と git diff HEAD の出力の一致）が条件より狭く、commit で HEAD が動く・untracked の編集・実行中の変更・subdir の cwd で、変わっても一致する。方針メモ-1 で (a) 許可リスト: テストの直前と使う前の 2 回とも HEAD が同じで、.steering/ 以外の作業ツリーが clean のときだけ使う形にした commit: fcb791e2 |
| G2 | 独立-2 | medium | no | self-inflicted | product | fixed | ac-verification と reference の RUN が使い回しをテスト以外（状態確認・E2E・lint）に広げている。テストの結果だけに限った commit: fcb791e2 |
| G3 | 独立-2 | medium | no | self-inflicted | product | fixed | completion-check の禁止から前のターンの結果が外れた。同じ起動の外の結果（前のターン、compaction の前）に揃えた commit: fcb791e2 |
| G4 | 独立-2 | medium | no | self-inflicted | product | fixed | .steering/ を丸ごと除くと requirements.md・design.md の変更が見えない。それらが変わったら回し直すとした commit: fcb791e2 |
| G5 | 独立-2 | low | no | self-inflicted | product | fixed | 長い git diff の出力を目で比べさせている。clean（出力が空）の判定に変えたので消えた commit: fcb791e2 |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | Iron Law の「以前のターン」が、main の起動を 1 ターンとする定義と合わせて 2 つの意味に読める |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | completion-check:78 の RUN（このセッションで fresh に実行）が、reference の RUN の例外と揃っていない |
| G8 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | レーンが L1。文書（散文の規定）の変更で、block / allow を決めるコードは変えないため L1 とした。PR 本文に書く |
| G9 | 独立-2 | advisory | no | inherited | bookkeeping | accepted | 変更断片の type: patch。既存の許可を条件付きで広げる文書の変更で、利用者の手順は変わらないため patch とした。PR 本文に書く |
| G10 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | RED-GREEN に、worker の commit・untracked の編集の場面が無い。PR 本文に書く |
| M1 | 方針メモ-1 | advisory | no | self-inflicted | fail-open | accepted | G1 の閉じ方を (a) 許可リストに決めた。入力者は通常の流れ（worker の commit の後に gate が回す。worker → gate の組は実データで 7〜13 ペア）。残る形（submodule.ignore を設定したとき、skip-worktree・assume-unchanged、ignore されたファイル、環境の変化）は限界として PR 本文に書く。誤 block はなく、効かない場面（commit 前の作業中）は回し直す側に倒れる。Opus の推奨と main の案に食い違いは無い |
| H1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 同じ起動の中の結果を確かめる git のコマンドが、打った cwd の repo を見る。subagent の cwd は呼び出し元のままなので、別の checkout を確かめて条件を満たせる。確かめる先をテストを回した worktree の root（<wt>）に固定して git -C で指し、テストの cwd を <wt> に限り、コマンドの exit code 0 を条件に足した commit: 7e18ad32 |
| H2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | reference の Common Failures の表（:56）と :31 の括弧書きが、HEAD が同じ・clean を 2 回の条件と requirements.md・design.md の例外に揃っていない |
| H3 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | ac-verification の Guardrails（:311）が、例外をテストの結果に限っていない |
| H4 | 独立-3 | low | no | self-inflicted | product | next-pr | テストを始める直前の確認を、テストを回す側（RUN・agent 定義）で先に取っておく手順が書かれていない |
| H5 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | requirements.md・design.md の変更と、テストが .steering/ を読むかに、確かめ方と「確かめられないときは回し直す」が無い |
| H6 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | completion-check（:337）の「§ Fresh の粒度」にファイル名が無く、このファイルに無い節を指す |
| H7 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | completion-check（:337）の「前のターン」が、subagent では定義に当てはまらない。回し直す側に倒れる。PR 本文に書く |
| I1 | 独立-4 | low | no | self-inflicted | product | next-pr | 使い回した結果を使う先（主張の対象）が <wt> に縛られておらず、main が 1 ターンの中で worktree を移ると、別の worktree の主張に使える読み方が残る |
| I2 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | cwd が <wt> の root と一致しないテスト（サブディレクトリで回すもの）は使い回せないことが、PR 本文の限界の節に無い。限界の節に足した commit: なし（PR 本文） |
| I3 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片の書き写しで、<wt> の root と main の決め方が落ちている（正本は reference）。PR 本文に書く |
| I4 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation の RED-GREEN 比較が、最終の文言で取ったものかを材料から確かめられない。PR 本文に取った sha を書く |
| I5 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | prompt に ## Worktree を受け取らない subagent では <wt> が決まらない（確かめられないとして回し直す側に倒れる）。PR 本文に書く |
