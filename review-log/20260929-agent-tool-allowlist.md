---
lane: L1
pr: 旧#247
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| codex-1 | Codex adversarial-review（codex-cli 0.154.0）, 全差分 | 02c4f080 | 1 | 0 | 1 | 2026-09-29T21:55+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1b6ef2a5e2e3aa7c8ce22dd41073c3fcba71c180 | 0 | 2 | 0 | 2026-09-29T22:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 268d481ba02144c83c25442dd2bcc13d3e5af67b | 0 | 1 | 0 | 2026-09-29T23:20+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 68205d54d5053df6aad20703f40792f0d790b01b | 0 | 0 | 0 | 2026-09-30T00:05+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | codex-1 | high | no | self-inflicted | wiring | fixed | MCP の URL を一時ファイルにする書く側が `/gdd-dev` に無かった。instruction 7 に手順を足し、Template の手順 0 に読む側を足した。commit: 1b6ef2a5 |
| F2 | 独立-1 | medium | no | self-inflicted | wiring | fixed | completion-check の runner が実行する `gdd-pr-review` の手順 1 が Skill tool を求めていた。Skill が使えないときも同梱の `pr-review.md` を読む。commit: 268d481b |
| F3 | 独立-1 | medium | no | self-inflicted | fail-closed | fixed | main が URL を渡し損ねたときに runner が止まる手順が無かった。本文が取れない URL で `clarification-needed` で止まる。commit: 268d481b |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | § Typed Agent Resolution の起動し直しの条件に、`tools:` の名前が解決できないときを足した。commit: 268d481b |
| F5 | 独立-1 | low | no | self-inflicted | wiring | fixed | URL と一時ファイルの対応が無かった。`<URL> → <絶対パス>` の対にし、定義を instruction 7 に 1 か所にした。commit: 268d481b |
| F6 | 独立-1 | low | no | self-inflicted | security | fixed | 一時ファイルの置き場所と後片付けが無かった。scratchpad か repo の外、runner が戻ったら消す。commit: 268d481b |
| F7 | 独立-1 | low | no | self-inflicted | test-power | next-pr | runner が実行する契約が許可リストの外のツールを名指ししても落ちるテストが無い（Skill は固定した）。契約からツール名を拾うテストは次の PR |
| F8 | 独立-1 | advisory | no | self-inflicted | doc-claim | next-pr | Review Pending Loop が runner の持たない ScheduleWakeup を名指ししている。main が arm し直すので実害は小さい |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | CONTRIBUTING の「約 2 倍」を、比べた条件と日付つきにした。commit: 268d481b |
| F10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Cursor に配った agent 定義の `tools:` の扱いは未確認。PR 本文の限界に書く |
| F11 | 独立-1 | advisory | no | inherited | doc-claim | out-of-diff | completion-check の SKILL.md が起動を旧名の「Task tool」で書いている |
| F12 | 独立-2 | medium | no | self-inflicted | wiring | fixed | 手順 0 の「呼び出し側が起動し直す」を読む側が無かった。呼び出し側の実際（Intake Brief を表示して止まる）に文言を合わせた。commit: 68205d54 |
| F13 | 独立-2 | low | no | self-inflicted | test-power | fixed | Template の対の書き方と、`gdd-pr-review` の行き先をテストで固定した。commit: 68205d54 |
| F14 | 独立-2 | low | no | self-inflicted | fail-closed | fixed | 対の一時ファイルが読めない・空のときも止まる。commit: 68205d54 |
| F15 | 独立-2 | advisory | no | self-inflicted | doc-claim | next-pr | reviewer が社内 URL を WebFetch したときに「推測しない」規定が無い。reviewer-common.md に 1 文足す |
| F16 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 一時ファイルの後片付けは runner が戻った経路だけ。中断時は scratchpad の寿命に任せる |
| F17 | 独立-3 | medium | no | self-inflicted | wiring | next-pr | 手順 0 が案内する「本文を貼る」出口を受け取る箇所が無い（MCP の無い環境で貼っても runner が同じ URL を WebFetch して止まる）。instruction 7 で貼られた本文も一時ファイルにする |
| F18 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 復帰の 2 案が runner の出力に書かれる保証がない。「次に決めること」に書かせる |
| F19 | 独立-3 | low | no | self-inflicted | fail-closed | next-pr | MCP の読み取りが失敗したときの扱いが instruction 7 に無い（エラー文を保存すると素通りする） |
| F20 | 独立-3 | low | no | inherited | doc-claim | next-pr | § Post-Return Routing（brainstorming）が clarification-needed の戻りを扱っていない（9.0 が先に効く） |
| F21 | 独立-3 | low | no | self-inflicted | test-power | next-pr | 否定の固定が活用形 1 つ、手順 0 の「まだ曖昧」、置き場所の scratchpad の句が固定されていない |
| F22 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 変更断片が「対の一時ファイルが読めない・空で止まる」と、止まった後に利用者がすることを書いていない（リリースで直す） |
| F23 | 独立-3 | low | no | inherited | doc-claim | out-of-diff | brainstorming SKILL.md の Intake Brief の欄名が「未確定」と「まだ曖昧」の 2 通り |
