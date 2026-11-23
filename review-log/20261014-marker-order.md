---
lane: L1
pr: 489
follow_up_of: 485
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8ae9b35a | 0 | 2 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 162450dd | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | 依頼の型の文が commands/gdd-dev.md:156（旧#9 の 0、Clarification Loop の main の表示）に残っていた commit: 0adf8206 |
| I1-2 | 独立-1 | medium | no | self-inflicted | product | fixed | 依頼の型の文が skills/gdd-completion-check/SKILL.md:138（done の停止）に残り、限界の分類も取りこぼしていた commit: 0adf8206 |
| I1-3 | 独立-1 | low | no | inherited | product | accepted | subagent-dispatch.md の手順 0・0.5 など「〜で終了」「表示後 … で停止」型の文は見出しに触れない（位置を決めない文として変えていない） |
| I1-4 | 独立-1 | low | no | self-inflicted | product | accepted | main の「マーカーが無ければ見出しの前に追加」が、マーカーも見出しも無い出力・見出しだけが無い出力を決めていない |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary が「書いていた 9 か所」を全部のように書いていた commit: 0adf8206 |
| I1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片が差し戻しを「あった」と断定し、PR 本文の「起きうる」と食い違っていた commit: 0adf8206 |
| I1-7 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 旧#485 が直す § 必須ルール 1 にも「出力末尾に」の語が残る（同じ項に見出しの文はある） |
| I1-8 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が見当たらない。PR 本文に書いた commit: なし（PR 本文） |
| I1-9 | 独立-1 | advisory | no | inherited | doc-claim | accepted | docs/TROUBLESHOOTING.md:130 の確かめ方が、マーカーを「末尾」で探す |
| I2-1 | 独立-2 | low | no | self-inflicted | product | accepted | human-check-template.md:414 の「出力末尾に」と compact テンプレートを 旧#485 に任せたことを、ユーザーが確かめていない。gh pr diff 485 では、compact に見出しが入り、414 に見出しの文が足されるが「出力末尾に」の語は残る。2026-10-14 にユーザーが 旧#485 で直すと決めた（.request.md に追記） |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | gdd-completion-check の手順 7 の同じ文で、blocked の停止（と手順 6）が見出しに触れていない |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | subagent-dispatch.md の Template の手順 0・0.5 が「marker で終了」のままで、手順 4 と食い違う。「〜後 marker で停止」型の文はほかにも 12 か所ある |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「次の 11 か所」が、Affected Files からは数え直せない |
| I2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の「Skill RED-GREEN Evidence（PR 本文）」と、token の予算に収まることを抜粋からは確かめられない（validate-plugin.sh はローカルで通過） |
| I2-6 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 旧#9 の 0 を字面どおりに読むと、subagent の text のマーカー・見出しに加えて main がもう 1 組出し、2 つずつになりうる |
| I2-7 | 独立-2 | advisory | no | inherited | doc-claim | out-of-diff | subagent-dispatch.md:60 の formal_gate の待ちの手順 4 も、マーカーを書くとだけあり見出しに触れない |
