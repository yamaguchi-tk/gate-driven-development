---
lane: L1
pr: 旧#257
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | bfefa5223c7fbce0edabafbc2ae35282722d0ddd | 0 | 0 | 0 | 2026-09-30T16:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | c908ba742485a377c54ab64b8bb9afe0f621e1c4 | 0 | 0 | 0 | 2026-09-30T17:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | README の PreToolUse の hook 本数と、block しない hook の列挙が 11 本のまま。commit: c908ba74 |
| F2 | 独立-1 | low | no | self-inflicted | product | fixed | SKILL.md の追記文の条件が Skill ツール経由に限られ、slash 展開・Read の経路が抜ける。断片の記述とも範囲がずれる。commit: c908ba74 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | SKILL.md の追記文が Claude Code の語だけで書かれ、同じ skills/ を読む Codex・Cursor を区別しない。commit: c908ba74 |
| F4 | 独立-1 | low | no | self-inflicted | test-power | fixed | hook が指す Template の見出しと dispatch 先が、subagent-dispatch.md に実在するかをテストが見ていない。commit: c908ba74 |
| F5 | 独立-1 | low | no | self-inflicted | test-power | fixed | block しないことを top-level の decision の有無でしか見ておらず、permissionDecision を返す変更が通る。commit: c908ba74 |
| F6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 断片が hook の追加を type: patch・Changed に書いており、VERSIONING と先行例（minor・Added）に合わない。commit: c908ba74 |
| F7 | 独立-1 | advisory | no | self-inflicted | product | accepted | 案内が Template だけを指し、戻った後の Post-Return Routing を指さない |
| F8 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | skill 名のキーの優先順（name→skill_name→skill）をテストが固定していない |
| F9 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | テストの _skill_commands が matcher の * と空を、すべてに当たるものとして扱わない |
| F10 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストが tempfile.mkdtemp() で作った HOME を消していない |
| F11 | 独立-1 | advisory | no | inherited | doc-claim | accepted | test_hooks_kill_switch.py の docstring の本数と efficacy の一覧が古い |
| F12 | 独立-1 | advisory | no | inherited | doc-claim | accepted | run-session-start-hook.sh:362 と lib/done_block_message.py:184 の案内が、gate の skill を Template 抜きで名指ししている |
| F13 | 独立-2 | medium | no | self-inflicted | product | next-pr | skill の文の「Codex・Cursor は § Codex / Cursor Worker Dispatch に従う」の飛び先は、Cursor の worker を未実装とし、Codex の委譲許可が無いときの inline 実行にも触れていない。Cursor では gate のたびに行き詰まるか HITL に落ちる |
| F14 | 独立-2 | low | no | self-inflicted | product | next-pr | skill の文の条件が「この手順を読んでいるとき」まで広がり、参照のために開いた main も runner を dispatch する読み方になる |
| F15 | 独立-2 | low | no | self-inflicted | test-power | next-pr | テストが hookSpecificOutput の中のキーだけを固定し、top-level の continue: false などを足す変更が通る |
| F16 | 独立-2 | low | no | inherited | doc-claim | next-pr | README の PreToolUse の block gate の列挙に、merge gate と steering write guard が抜けている |
| F17 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の Skill RED-GREEN が、どの版の本文で取ったかと、試した経路を書いていない |
| F18 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary と PR 本文の目的が、skill の文が slash・Read も対象にしたことを述べていない |
| F19 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「1 文足した」が、実際に足した文の数と合わない |
| F20 | 独立-2 | advisory | no | inherited | doc-claim | re-reported | F12 の再報告（run-session-start-hook.sh:362・done_block_message.py:184 の案内） |
| F21 | 独立-2 | advisory | no | inherited | doc-claim | re-reported | F11 の再報告（test_hooks_kill_switch.py の docstring） |
| F22 | 独立-2 | advisory | no | inherited | test-power | re-reported | F8 の再報告（キーの優先順をテストが固定していない） |
| F23 | 独立-2 | advisory | no | inherited | style | re-reported | F10 の再報告（mkdtemp の HOME を消していない） |
