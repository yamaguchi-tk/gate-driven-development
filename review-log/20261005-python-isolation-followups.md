---
lane: L1
pr: 380
follow_up_of: 378
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | dd85490337e354303bf581d8f68193b624e757ba | 0 | 1 | 0 | 2026-10-05T19:58+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 77bbe356fb2d28f864d7be0115321494cdb388e1 | 0 | 0 | 0 | 2026-10-05T20:13+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| J1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | SECURITY.md の fail-closed の例外を 2 つに限るが、pre-push・pre-PR・active-gdd-skill とその expansion も読めない payload で通し、worktree-command-guard は python が無いと通す。escape hatch の文も 2 hook に掛かるように読める commit: 77bbe356 |
| J2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | kill-switch.sh とテストの docstring の PYTHONSAFEPATH の理由が、hook に無い bash -c の起動を挙げ、python3 が無いときの python の -c を落とし、子の python の露出の記述も消した commit: 77bbe356 |
| J3 | 独立-1 | low | no | self-inflicted | test-power | fixed | Stop hook の入口のテストの docstring が「cwd の json.py と PYTHONPATH=: でも HITL lint が判定する」と書くが、lint は json を import しないので子の python が -I かを見分けない commit: 77bbe356 |
| J4 | 独立-1 | low | no | inherited | product | next-pr | HITL lint の子 python が -I なしで起動され、PYTHONPATH の空の要素と repo の argparse.py などがそろうと、きれいな HITL を traceback で block する（hitl_lint_gate.py・advisory_lint.py・resolve-gdd-model の起動） |
| J5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 関数を通らない起動の検査が並べた形だけで、引用符つきの絶対パス・名前に python を含まない変数・オプションや行継続を拾わず、断片の主張より狭い commit: 77bbe356 |
| J6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | SECURITY.md の Agent の行に、background-dispatch-gate が読む run_in_background・agent_id と git の toplevel が無い commit: 77bbe356 |
| J7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が PYTHONSAFEPATH のテスト全部の skip を変えたように読める（変えたのは Stop hook のテストだけ） commit: 77bbe356 |
| J8 | 独立-1 | low | no | self-inflicted | product | fixed | subagent に先に出す foreground の案内に、Bash の timeout の既定値（省くと 120 秒）が無い commit: 77bbe356 |
| J9 | 独立-1 | low | no | inherited | product | fixed | subagent への理由文が、background で起動して完了通知を待つという共通の文を先に見せ、foreground を先に案内する意図を打ち消す commit: 77bbe356 |
| J10 | 独立-1 | low | no | inherited | doc-claim | fixed | subagent が通知を受け取れるかを、wait_loop_gate は確かめていないと書き、references/subagent-dispatch.md と background_dispatch_gate の docstring は受けられないと言い切る commit: 77bbe356 |
| J11 | 独立-1 | low | no | inherited | doc-claim | next-pr | SECURITY.md の hook の表が hooks.json の 8 イベントと合わず、UserPromptExpansion の gate と Stop の書き込み先が無い |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | wait_loop_gate の docstring の通す形が、--watch を含む command では成り立たない（PR 本文に列挙） |
| A2 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | PATH に python3 が無いと collection error、HOME の kill switch で clean の側が素通り、decision の比較が区切り文字に依存（PR 本文に列挙） |
| A3 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | ファイルで起動される lib の .py を拾う範囲が、起動の形の検査より狭い（PR 本文に列挙） |
| A4 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの名前 monitor_or_foreground と、foreground を先にする assert の順序が逆（PR 本文に列挙） |
| K1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | subagent への理由文が使い方の参照先にする wait-until.py の docstring は、run_in_background: true で起動して完了通知を待つと無条件に書く |
| K2 | 独立-2 | low | no | self-inflicted | product | accepted | subagent への理由文が --timeout だけを Bash の timeout より短くと案内し、--check-timeout と 10 秒の分を含めない |
| K3 | 独立-2 | low | no | self-inflicted | product | accepted | subagent の分岐にも sleep N だけを起動する案内が残り、foreground か N の上限が書かれていない |
| K4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | test_background_dispatch_gate.py の test の docstring が subagent は通知を受けられないと言い切ったまま |
| K5 | 独立-2 | low | no | inherited | doc-claim | accepted | 未リリースの断片 20261005-wait-loop-deny.md が subagent には Monitor か foreground を示すと書き、この PR の理由文と食い違う（リリースの dry-run で版の節を直す） |
| K6 | 独立-2 | low | no | inherited | doc-claim | accepted | SECURITY.md の Bash の行に、wait-loop-gate が読む payload の agent_id が無い |
| K7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md の新しい箇条の worktree-command-guard と、表の root-branch guard が同じ部品の別名で対応が書かれていない |
| K8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md が pre-push gate を command を解析できないと通すにだけ分類し、steering を解決できない・想定外のエラーで通す経路を書かない |
| K9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 関数を通らない起動の検査が拾わない形の一覧に「など」が無く、/usr/bin/env python3・sudo などが漏れる |
| K10 | 独立-2 | low | no | self-inflicted | test-power | accepted | subagent の理由文の --timeout の assert の境界が 600 で、既定の 120 秒を超える例を通す。コメントは「超える」で assert は「以上」 |
| K11 | 独立-2 | low | no | self-inflicted | style | accepted | test_reason_invocations_are_accepted_by_the_script_and_the_gate の中の import re が不要 |
| K12 | 独立-2 | low | no | inherited | product | accepted | subagent の分岐でも、常駐の処理は利用者に確認するという結びのままで、subagent は利用者にたずねられない |
| A5 | 独立-2 | advisory | no | self-inflicted | product | accepted | Monitor も確かめていない経路なのに、自分が起動した background の処理を待つ唯一の手段として残る（PR 本文に列挙） |
| A6 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり: PR 本文の抜粋の限界の節に、前の PR の断片の古い記述の個別の列挙がある |
