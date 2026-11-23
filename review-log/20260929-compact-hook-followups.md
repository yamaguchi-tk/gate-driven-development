---
lane: L1
pr: 旧#223
follow_up_of: 208
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus) | - | 0 | 0 | 0 | 2026-09-29T07:30+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 39a1fb071a8f2d4ddc3db7b0ce6013300b9944ac | 0 | 0 | 0 | 2026-09-29T08:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | fabaf1ddf0026bbf80b7ef76a93ec72bf4b01ece | 0 | 0 | 0 | 2026-09-29T08:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 方針メモ | advisory | no | inherited | stdin-read | accepted | 旧#208 の I7-2。macOS の /bin/bash 3.2 は `read -t 1` の timeout で途中の入力を捨てるので、compact の payload を書いたまま stdin が閉じない起動では SessionStart の沈黙が外れる（手元で再現）。Opus の推奨は直さず限界として開示する（B）。10 本の hook が stdin を `$(cat)` で読み、UserPromptSubmit も prompt のたびに止まっていないので、Claude Code は stdin を閉じる。python の select に移す案は、Windows（MSYS の bash 4 以上は今のままで正しい）で悪化する |
| I1-1 | 独立-1 | low | no | self-inflicted | session-continuity | fixed | `GDD_STEERING_DIR` を env で渡したとき・detection が失敗したとき、`GDD_STEERING_WT` が空で、ファイルシステムのルートの `/.claude/gdd-dev.local.md` で session を照合していた。worktree が分かるときだけ照合する（5b54c27e） |
| I1-2 | 独立-1 | low | no | self-inflicted | test-power | fixed | `-X utf8` の検査がコメント行も走査し、`-X utf8=0` を通し、変数で起動する python を見ないのに kill-switch.sh と断片が「起動の形で固定」と広く書いていた。コメント行を除き、`utf8=0` を見分け、主張をリテラルの起動に狭めた（5b54c27e・fabaf1dd） |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary が「ほかの注入と同じ条件」と書き、SessionStart の Safe Resume（local state が無い・session id が取れない・ブランチ）との違いを書いていなかった。`session_id` が空のときも渡さないことが抜けていた（5b54c27e） |
| I1-4 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 今の session id が取れないときも渡し続けることを、PreCompact の入口からのテストで固定していない |
| I1-5 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | テンプレート外の記述あり（commit の件名に巡の名前「方針メモ」が入っていた）。判断には使われていない。今後の件名に巡の名前を書かない |
| I2-1 | 独立-2 | low | no | self-inflicted | test-power | accepted | `-X utf8` の検査は、別の引数を取る option（`-X dev`・`-W ignore`）の後ろと継続行の `-I` を数えず、`-X utf8=1` や直後に引用符が来る形は誤って落とす。今の hook にどちらの形も無い。follow_up_of の PR の 2 巡目の low なので限界として PR 本文に書く |
