---
lane: L1
pr: 462
follow_up_of: 452
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1c03ec78 | 0 | 2 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 3996e3ea | 0 | 1 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | f677ecba | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| J1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 一時 commit が作られないと reset が本物の commit を外し、依頼の「安全な戻し方」を満たさない。履歴に触れずに、worktree の外の複製で戻す形に書き換えた（Opus 設計レビューの推奨）。commit: 3996e3ea |
| J1-2 | 独立-1 | medium | no | inherited | product | accepted | reviewer の Focus 3 の退行注入に戻し方の規定が無い。PR 本文の限界に書いた |
| J1-3 | 独立-1 | low | no | self-inflicted | product | accepted | 並列バッチで変異を後に回すと、compaction の後に変異の確認が飛ばされる。PR 本文の限界に書いた |
| J1-4 | 独立-1 | low | no | self-inflicted | product | fixed | 戻した後の確認が抜けている。cmp と対照のテストの pass で確かめる形にした。commit: 3996e3ea |
| J1-5 | 独立-1 | low | no | inherited | product | accepted | Steps 1 の取り直しにも、一時 commit が作られないときに reset が本物の commit を外す穴がある。PR 本文の限界に書いた |
| J1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が「一時 commit の前の」を落としている。戻し方を変えたので、断片を新しい形に書き直した。commit: 3996e3ea |
| J1-7 | 独立-1 | low | no | self-inflicted | product | accepted | 並列実行では、inline の範囲がレビューしている task より広く読める。PR 本文の限界に書いた |
| J1-A1 | 独立-1 | advisory | no | inherited | product | accepted | soft reset の後に変更が staged に移り、name-only の数え直しが取りこぼしうる（Steps 1 の分） |
| J1-A2 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence を抜粋から確かめられない。PR 本文に書いた。commit: なし（PR 本文） |
| J2-1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | 戻す手順がテストの落ちた側にしか無く、落ちなかったときに変異が production に残り、依頼の「安全な戻し方」を満たさない。落ちても落ちなくても次の操作の前に戻す形にした。commit: f677ecba |
| J2-2 | 独立-2 | low | no | self-inflicted | request-drift | fixed | 依頼の行が名指しした一時 commit を複製に替えたことを、ユーザーが確かめた記録が無い。Opus・Fable の推奨（どちらも複製のまま）を示し、ユーザーが A（複製のまま）を選んだ。回答を review-log/20261013-tdd-mutation-revert.request.md に足した。commit: なし（依頼の原文） |
| J2-A1 | 独立-2 | advisory | no | self-inflicted | product | accepted | 複製を置いた一時ディレクトリを片付ける指示が無い |
| J3-1 | 独立-3 | low | no | self-inflicted | style | accepted | 足した入れ子の括弧が全角の（）で、同じ行の〔〕とそろわず、外側の括弧が閉じたように読める。PR 本文の限界に書いた |
| J3-2 | 独立-3 | low | no | inherited | test-power | accepted | 直したテストが変異の無い実装で落ちたとき（対照ではなく RED になったとき）の扱いが無い。PR 本文の限界に書いた |
| J3-3 | 独立-3 | low | no | inherited | test-power | accepted | 変異で「落ちた」の理由（assert か、収集・import・構文の失敗か）を問わない。PR 本文の限界に書いた |
| J3-4 | 独立-3 | medium | no | inherited | product | re-reported | reviewer の Focus 3 の退行注入に同じ戻し方の規定が無い（J1-2 と同じ） |
| J3-A1 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文に、テストを直した後の入れ直しの一句が無い。PR 本文に書いた。commit: なし（PR 本文） |
| J3-A2 | 独立-3 | advisory | no | inherited | product | accepted | repo の外へ複製した側を変異させる強い形（docs/learned-patterns.md）があり、限界の「変異が worktree に残る」を構造で閉じうる |
| J3-A3 | 独立-3 | advisory | no | inherited | product | accepted | 一時ディレクトリの片付けと、複製の場所の記録が無い |
