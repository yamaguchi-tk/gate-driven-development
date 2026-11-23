---
lane: L1
pr: 旧#188
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b66158d63b127a027009d715973d05e05f32e368 | 0 | 0 | 0 | 2026-09-28T12:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | test-power | next-pr | `test_agents_md_lists_the_materials_step_6_sends` は `AGENTS.md` 全体に「呼び出し元の候補」「PR 本文の抜粋（PR 作成前は草案）」の語があるかだけを見る。「依頼なしに行ってよいのは」の列挙から外して、同じ行の後ろに「1 操作ごとに依頼を取る」側へ書いても通る。列挙の句ごと固定する。近道の規定で次の PR |
| F2 | 独立-1 | low | no | self-inflicted | excerpt-field-not-synced | next-pr | 経路: 差分の `CLAUDE.md:53`（限界の節から受け入れた指摘の記録を除く句を追加）→ 同じ抜粋の定義を持つテンプレートの欄 `.claude/agents/light-lane-independent-reviewer.md:67`。欄には明示の除外が無い（「前の巡の指摘とその対応は書かない」で意味の上では拾える）。欄とテストに同じ句を足す。近道の規定で次の PR |
| F3 | 独立-1 | low | no | self-inflicted | limit-overstated | fixed | PR 本文の限界の「その指摘は main が再掲として分ける」が全称で、§ 常時 High・実害クラスや `origin: this-diff` の指摘は再掲にできず巡の high・blocking に数えられることを落としている。PR 本文の文言を直した（ファイルは変えない） |
| F4 | 独立-1 | low | no | self-inflicted | fragment-direction | fixed | 断片の Summary が、変わったのは手順 7 の側なのに、抜粋の側を変えたように書いている。向きを直した。マージ後の断片は通常の PR で直せない（version-not-consumed の layer B）ので、次の PR に回さずこの PR で直した |
| F5 | 独立-1 | advisory | no | inherited | step7-body-only-scope | next-pr | 経路: 差分の `CLAUDE.md:96`（手順 7 の PR 本文の節の列挙）→ 同じく PR 本文に書くものを定める `CLAUDE.md:88`（終了条件の「巡の sha と結果だけを書き」）。「だけ」の掛かる範囲を巡の記録に限る。PR 本文の advisory に載せ、次の PR |
