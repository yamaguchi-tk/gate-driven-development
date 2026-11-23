---
lane: L1
pr: 291
follow_up_of: 282
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d66e310916c076c8efa67950d7c706e170545f4d | 0 | 0 | 0 | 2026-10-02T11:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 06b2740ae20e375e15c6140be41e38dbf2a8cd25 | 1 | 2 | 1 | 2026-10-02T12:15+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | c517d3e536342ba6ee2807b5aa5ad71e398fc4ae | 0 | 0 | 0 | 2026-10-02T12:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | test-power | fixed | hook 経由のテストのコメントが、CLAUDE_PLUGIN_ROOT を明示する理由と食い違う commit: 132b9b6f |
| F2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 上の階層の見出しで外す範囲が終わる・`~~~` のフェンス・design.md のフェンスの中の行を、テストが固定していない commit: 132b9b6f |
| F3 | 独立-1 | low | no | self-inflicted | lint-scope | fixed | フェンスの開閉を交互に切り替えるだけで、info string 付きの行や閉じないフェンスで見出しの判定がずれる。CommonMark の閉じ方にし、閉じなければフェンスを考えない commit: 06b2740a |
| F4 | 独立-1 | low | no | self-inflicted | rule-sync | fixed | 断片・PR 本文が「express の Scope」を検査するとしているが、実際は Task Size を問わず `## Scope` を検査する。記述を直し、英語見出しの standard の照合元も検査されることを限界に書いた commit: 06b2740a |
| F5 | 独立-1 | advisory | no | self-inflicted | rule-sync | accepted | human-check-template の 101 行と 189 行で、同じ件数の基準を「自走上限」と「方向性」で呼び分けている |
| F6 | 独立-1 | advisory | no | inherited | bookkeeping | accepted | 未リリースの 旧#282 の断片に、この PR で変えた件数・除外の節の古い記述が残る（リリース時に直す） |
| F7 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 配布の wrapper 経由では `CLAUDE_PLUGIN_ROOT` が空にならず、空のときの分岐は手で起動したときだけ通る |
| F8 | 独立-1 | advisory | no | self-inflicted | rule-sync | fixed | PR 本文の「Stop hook とそろう」が、見出しの階層によってはそろわない場合まで言い切っている commit: なし（PR 本文） |
| F9 | 独立-1 | advisory | no | inherited | lint-scope | accepted | gdd_stop_hook・hitl_lint_gate の plugin root の求め方が、この PR の hook と違う |
| F10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | `_resolve_plugin_root` が同じパスを 2 回 resolve する |
| F11 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | テストが hook の起動を `_run` と別に書いている |
| G1 | 独立-2 | high | yes | inherited | stop-hook-fence | accepted | Stop hook の Lane の読み取り（`lib/next_plan_check.py` の正規表現）がフェンスを見ず、フェンスの中の `## ` で Lane が切れて後ろの `- [ ]` を見ないので、`### 次の計画` なしの停止が通る。block gate の既存の欠陥で L1+ になるため、限界の先頭に書き、直後の PR で直す |
| G2 | 独立-2 | medium | no | self-inflicted | lint-scope | fixed | 閉じないフェンスが 1 つあると、それより前の閉じたフェンスの中の `#` 行まで見出しになる。閉じたフェンスの範囲を保ち、閉じないフェンスは開きから後だけを素で数える commit: c517d3e5 |
| G3 | 独立-2 | medium | no | self-inflicted | test-power | fixed | info string の閉じ方のテストが、その条件を外しても通る。閉じ損ねでフェンスの中の見出しが露出する入力に替えた commit: 8f19a257 |
| G4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 閉じのフェンスの「同じ文字」「長さが同じか長い」の条件を、テストが固定していない |
| G5 | 独立-2 | low | no | self-inflicted | test-power | accepted | `~~~` のフェンスのテストが returncode を見ていない |
| G6 | 独立-2 | low | no | inherited | test-power | accepted | 既存のテスト 2 本が returncode を見ていない |
| G7 | 独立-2 | low | no | inherited | lint-scope | accepted | フェンスの開きが、info string に `` ` `` を含む行と全角空白の字下げも受け付け、`tasklist_parse.py` の規則より広い |
| G8 | 独立-2 | low | no | self-inflicted | rule-sync | fixed | PR 本文の Stop hook とそろう範囲が、フェンスの中の `## ` と Lane の後の `#` 1 個の見出しの場合を除いていない。条件を絞った commit: なし（PR 本文） |
| G9 | 独立-2 | low | no | self-inflicted | rule-sync | fixed | モジュール docstring の「フェンスの中の `#` 行は見出しにしない」が、閉じないフェンスの扱いと食い違う commit: c517d3e5 |
| G10 | 独立-2 | advisory | no | inherited | bookkeeping | accepted | 未リリースの 旧#282 の断片が、この PR の断片と食い違う（リリース時に直す） |
| G11 | 独立-2 | advisory | no | self-inflicted | style | accepted | `_heading_levels` の制御の流れと、見出しの計算の重複が読みにくい |
| G12 | 独立-2 | advisory | no | inherited | lint-scope | accepted | gdd_stop_hook・hitl_lint_gate の plugin root の求め方が、この PR の hook と違う |
| H1 | 独立-3 | low | no | self-inflicted | test-power | accepted | 閉じた後に開きの状態を戻す処理（`fence = None`）を消しても、どのテストも落ちない |
| H2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | info string のテストの docstring「以後の見出しを失わない」が、検査している内容と合わない |
| H3 | 独立-3 | advisory | no | self-inflicted | lint-scope | accepted | フェンスの走査が `tasklist_parse._scan_fences` の写しで、開きの受理集合が 2 点ずれている |
