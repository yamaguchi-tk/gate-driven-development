---
lane: L1+
pr: 492
follow_up_of: 487
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 5c78cd05 | 0 | 0 | 0 | 2026-10-14 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 463c0e8d | 0 | 0 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | b87c07c4 | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | self-inflicted | design | fixed | 草案は値を渡し、値が空の行を「無い」と読んでいた。依頼の「行があるか読めないとき」を狭めるので、state.md のパスを渡し、文字列の presence で拒む形に替えた（Fable も同じ推奨。ユーザーが確認で選んだ）。commit: eb1a5d3b |
| A1 | 独立-1 | low | no | self-inflicted | product | accepted | 欄を worklog へ移すと ledger の行が invalid から ok に変わり、サイズ退避の検算の戻す規則に掛からず、not_applicable が通る。PR 本文の限界に書く |
| A2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片が post-completion-learning.md の「gate はこれを検査しない」を直したと書くが、その句は post-completion-pr-flow.md にしか無かった。PR 本文は直した。commit: なし（PR 本文） |
| A3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | post-completion-pr-flow.md:80・post-completion-learning.md:52 が「行で拒む」と書き、実装（語で判定）と (3-f)・state-field-tiers の「語があれば」より狭い |
| A4 | 独立-1 | low | no | self-inflicted | product | accepted | ADR distilled が無いときの案内が、申し送りがあっても not_applicable を勧める（従うと次の gh pr create で handoff の block に当たる） |
| A5 | 独立-1 | low | no | self-inflicted | test-power | accepted | ledger のテストが handoff 専用の行の文言を assert していない（分岐を消しても通る） |
| A6 | 独立-1 | low | no | self-inflicted | test-power | accepted | ledger が読む欄が SIZE_DENY_SUFFIX に載ることを見るテストが、lib の grep で読む Decision Handoff を拾わない |
| A7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 非 UTF-8 の state.md で「行の中身によらず exit 2」は awk の実装による。PR 本文は直した。テストのコメントは残る。commit: なし（PR 本文） |
| A8 | 独立-1 | advisory | no | self-inflicted | product | accepted | 欄名を別の表記（Decision-Handoff・空白 2 つなど）で書くと「無い」として通る |
| A9 | 独立-1 | advisory | no | self-inflicted | style | accepted | state.md を読めないときも「理由が不足」の文言が出る |
| A10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | state-field-tiers.md:18 の gate が読む欄の例に Decision Handoff が無い |
| A11 | 独立-1 | advisory | no | self-inflicted | style | accepted | 足したテストが mkdtemp の一時ディレクトリを消さない |
| B1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「state-field-tiers.md に行を足した」が、Decision Retake の行にまとめた後の表と合わない。PR 本文は直した。commit: なし（PR 本文） |
| B2 | 独立-2 | low | no | self-inflicted | style | accepted | まとめた行の欄の区切りが「・」で、同じ表のほかの行の「 / 」と違う |
| B3 | 独立-2 | advisory | no | inherited | doc-claim | accepted | post-completion-pr-flow.md・post-completion-learning.md が「行で拒む」と書き、表と (3-f) は「語」と書く（A3 と同じ） |
| B4 | 独立-2 | advisory | no | inherited | doc-claim | accepted | SIZE_DENY_SUFFIX の残す欄の例に Decision Retake が無い |
