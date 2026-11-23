---
lane: L1
pr: 旧#173
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承（agent 定義が入る前から動いているセッションのため fallback 経路。read-only は散文だけの規定） | 7059343a5ace394293d81010f76495944e692b89 | 0 | 0 | 0 | 2026-09-22T11:05+09:00 |
| PR後-1 | user（Cursor / Grok 4.6 のレビューを PR に投稿） | 5758582423aef590789383445a7ce0c8f742322a | 0 | 1 | 0 | 2026-09-23T17:52+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | read-check-self-proving | next-pr | 読み込みの照合が自己証明になっている。テンプレートが各ファイルの行数を `（<n> 行）` で渡すので、reviewer は読まずに同じ数字を書けば `wc -l` の照合を通る。候補と PR 本文は「読んだ行数／ファイルの行数」の対になっていない。近道の 1 巡のため `next-pr`。次の PR で、末尾行の引用と `tail -1` の突合に変える |
| F2 | 独立-1 | medium | no | self-inflicted | material-not-bound-to-range | next-pr | 材料ファイルの中身が `base..tip` に結びついていない。前の巡の古い差分・別 worktree の差分・相対パス・0 行のファイルのいずれも fail-closed の列挙に当たらず、照合も通る。近道の 1 巡のため `next-pr`。次の PR で、ファイル名に `<base>..<tip>` の短縮 sha を含める・絶対パスに限る・0 行を弾く・先頭の `diff --git` 行を突き合わせる |
| F3 | 独立-1 | medium | no | self-inflicted | host-route-reachability | next-pr | 非 Claude Code 経路（`cursor.md`・`codex.md` の read-only sandbox / readonly Task）が、リポジトリ外の絶対パス（scratchpad）を読めるかが未確認。読めなければその runtime では独立レビューが成立しない（fail-closed なので誤った merge-ready にはならない）。PR 本文の限界に書いた。次の PR で置き場を worktree 内の gitignore 済みの場所に規定する |
| F4 | 独立-1 | low | no | self-inflicted | line-count-off-by-one | next-pr | 末尾に改行が無いファイルでは `wc -l` が Read の行数より 1 小さく、正しく読んだ巡が無効になる。次の PR で「材料ファイルは末尾を改行で終える」を足す |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「最後まで読める」の根拠が reviewer の自己申告だけなのに、限界の節では「申告は確かめられない」と書いていた。PR 本文の表現を「自己申告では最後まで読めた（実読み込みは未検証）」に直した（PR 本文だけの修正） |
| F6 | 独立-1 | low | no | self-inflicted | ci-red | fixed | `review-log/` の表が空のままで `review-log-present.sh` が block し、CI が赤になる。この巡の行を追記して解消した（`review-log/` だけを変える commit） |
| P1 | PR後-1 | medium | no | self-inflicted | skill-red-green-evidence | fixed | reviewer の守ること・テンプレート・出力の冒頭行を変えたのに、CONTRIBUTING 1c の Skill RED-GREEN Evidence が PR 本文に無い。fail-closed の pressure scenario（差分ファイルが無いパス）を fallback 経路（general-purpose, model: opus, 新しい定義の本文）で 1 本走らせ、`blocking: diff 未到達` の 1 件だけが返ることを確かめた。3 欄を PR 本文に足した（PR 本文だけの修正） |
| P2 | PR後-1 | low | no | self-inflicted | output-order-conflict | next-pr | 守ることの「出力の冒頭に `読み込み:`」と、出力節の「結論を先に書く」が食い違う。`読み込み` を 1 行目、結論を 2 行目と書く。agent 定義（規則の文書）の修正で巡が無効になるため、F1〜F4 と同じ次の PR で直す |
| P3 | PR後-1 | low | no | self-inflicted | stale-after-design-change | next-pr | 守ることの箇条書きが「テンプレートの『呼び出し元の候補』は … 一覧である」のままで、正本が候補ファイルに変わったことに追随していない（3f の E）。「候補ファイルの中身は、機械的に grep しただけの一覧」に直す。P2 と同じ理由で次の PR で直す |
| P4 | PR後-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文に `merge-ready:` の行があり、手順 7（PR 本文に merge-ready と書かない）に反する。見出しを「終了条件の照合」に変えた（PR 本文だけの修正） |
