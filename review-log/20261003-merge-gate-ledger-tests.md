---
lane: L1
pr: 335
follow_up_of: 268
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 5a073166831ffc76dac733c8a04cd9f986bc10bb | 0 | 0 | 0 | 2026-10-03T13:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | ba93a5dd054888cd799fd3890a3e2611a98ffd37 | 0 | 0 | 0 | 2026-10-03T14:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 独立-1 | low | no | self-inflicted | test-power | fixed | 倒し方を固定しているのが素通りの出口 1 つ（steering 無し）だけ。steering の 3 つの形（無い・別の PR を 1 件・複数件）で miss・unknown・unreadable を回した commit: 2235ed3f |
| P2 | 独立-1 | low | no | inherited | test-power | fixed | merge gate の他のテストが手元の GDD_HOOK_STATE_DIR を継承し、台帳の場所が変わる。`_merge_gate_support._run_hook` で継承から落とし、個別の drop_env を外した commit: 2235ed3f |
| P3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | hook の注記「root checkout で直接打ったときと同じく」が倒し方まで同じと読める。root 未解決の経路と同じく miss だけ通すと書いた commit: ba93a5dd |
| P4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「miss 以外」の括弧から hit が抜け、unreadable の範囲が狭い。hit・unknown・unreadable と書き直した commit: 2235ed3f |
| P5 | 独立-1 | advisory | no | inherited | doc-claim | accepted | test_merge_gate_ledger_fail_closed.py:14 の倒し方の列挙が 2 経路のまま（当時の修正範囲の注記で、書いた 2 経路は正しい）。PR 本文に列挙 |
| P6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文が 3 ファイル全部に「miss だけ通す」と書いたように読める。分けて書いた commit: なし（PR 本文） |
| P7 | 独立-1 | advisory | no | self-inflicted | style | fixed | 書き換えた注記の行だけ折り返しが長い。前後と同じ幅で折り返した commit: ba93a5dd |
| Q1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「unreadable（台帳や台帳に載った root を読めない）」に対し、共通ディレクトリの経路のテストが作るのは台帳がディレクトリの形だけ。root 側の unreadable は別の経路のテストで固定している。PR 本文の限界に書く |
| Q2 | 独立-2 | low | no | self-inflicted | test-power | accepted | `_merge_gate_support._run_hook` で GDD_HOOK_STATE_DIR を落としたことを固定するテストが無い（CI は設定しないので、戻しても手元でだけ結果が変わる）。PR 本文の限界に書く |
| Q3 | 独立-2 | low | no | inherited | test-power | accepted | test_merge_gate_followup_findings の独自の hook 起動が GDD_HOOK_STATE_DIR を継承したまま（今のテストは台帳の経路に入らない）。PR 本文の限界に書く |
| Q4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | test_merge_gate_same_repo_worktree.py:135 のコメント「root checkout で直接打ったときと同じく」は hit に限れば正しい。PR 本文に列挙 |
| Q5 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 未リリースの断片 20260918-merge-gate-non-gdd-merge.md が台帳の読み手を 2 経路と書く（当時は正しい）。リリース時に版の節で直す。PR 本文に列挙 |
| Q6 | 独立-2 | advisory | no | inherited | doc-claim | re-reported | test_merge_gate_ledger_fail_closed.py:14 の倒し方の列挙が 2 経路のまま（P5 の再掲） |
| Q7 | 独立-2 | advisory | no | self-inflicted | style | accepted | test_merge_gate_ledger_fail_closed.py・test_merge_gate_target_grammar.py の drop_env=("GDD_HOOK_STATE_DIR",) が冗長になった（extra_env も落とす点で完全には同じでない）。PR 本文に列挙 |
| Q8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary がテストの説明になっている（§ Policy は「利用者から見える変更なし」と書いてよいとする）。PR 本文に列挙 |
| Q9 | 独立-2 | advisory | no | self-inflicted | style | accepted | hook の注記に長い行が 2 本あり、「miss のときだけ通す」を塊の中で 2 回書いている。PR 本文に列挙 |
