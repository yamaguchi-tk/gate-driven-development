---
lane: L1+
pr: 610
follow_up_of: 576
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + Fable 設計レビュー (gate-driven-development:gdd-fable-advisor, model: fable) | a52a36a2 | 0 | 0 | 0 | 2026-10-29 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 86f100cf | 0 | 6 | 0 | 2026-10-29 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | 飛ばす条件 | accepted | 方針: 骨格は草案（段 1 で下書き・hash に tasklist・飛ばすときは TDD へ）。Step 8 の Next Action は state.md（両方）、tasklist が無ければ KEEP（両方）、Tasklist Basis（Opus）、質チェックを requirements-gating の design の観点へ（Opus）、手順の正本は task-breakdown-steps.md（Opus）。確認は返事を待たずに推奨で進める |
| I1-1 | 独立-1 | medium | no | self-inflicted | 依頼の範囲 | accepted | design-gating を通る経路（Broad・timeout・Quick Standard Design Gate Optional・light・差し戻し・Step 4 の後の変更）では task-breakdown が残り、依頼の「段 1 に寄せる」より狭い。2026-10-29 にユーザーが推奨どおり（この形）と決めた |
| I1-2 | 独立-1 | medium | no | self-inflicted | Next Action | accepted | 16e が Step 11 を含むので、承認前の下書きに Next Action=gdd-test-driven-development が入り、resume の候補判定で build と planning の両方に当たりうる |
| I1-3 | 独立-1 | medium | no | self-inflicted | 質チェック | accepted | gdd-planning-reviewer.md:362 が、requirements-gating の design の観点では tasklist が無いので質チェックは対象外、と書いたまま |
| I1-4 | 独立-1 | medium | no | self-inflicted | 段 1 の手順 | accepted | 16e が task-breakdown SKILL.md の Plan Execution Fields・Subsystem Boundary Check・Migration の検証 task・Judgment Change・Gate Batch を含まない。Judgment Change の no は task-breakdown だけが書ける |
| I1-5 | 独立-1 | medium | no | self-inflicted | Basis の時点 | accepted | 列挙: basis を刻んだ後も Step 17・lint の修正・節見出しの追加・行数削減・amendment で文書が変わり、取り直しの規定が無い。どれかに当たると飛ばす経路が働かない（fail-closed） |
| I1-6 | 独立-1 | medium | no | self-inflicted | advisory の反映 | accepted | 列挙: 質チェックの指摘は advisory になり、承認の後に回るので、飛ばす経路では tasklist に届かない |
| I1-7 | 独立-1 | low | no | self-inflicted | Next Action | accepted | state-machine.md:469・:473・:592 の draft の Next Action の記述が、Step 8 と 16e と食い違う |
| I1-8 | 独立-1 | low | no | self-inflicted | 質チェック | accepted | subagent-dispatch.md:60 の `参照: tasklist.md` が worktree からの相対パスの形でない |
| I1-9 | 独立-1 | low | no | self-inflicted | 段 1 の手順 | accepted | 16e の条件が、design の観点の組を起動する条件（reviewer-selection.md:151）より広い |
| I1-10 | 独立-1 | low | no | self-inflicted | 参照先 | accepted | 16e の参照先の節（§ tasklist.md の canonical state）に routing source の規定が無い |
| I1-11 | 独立-1 | low | no | self-inflicted | 参照先 | accepted | brainstorming SKILL.md:97 が「この skill では作成しない」の下にあり、:299 が 16e と逆に読める |
| I1-12 | 独立-1 | low | no | self-inflicted | 参照先 | accepted | state-machine.md:503 とテストの docstring に、飛ばす経路の行き先が task-breakdown のまま残る |
| I1-13 | 独立-1 | low | no | self-inflicted | Basis の時点 | accepted | 飛ばす経路では Basis の行が canonical の tasklist に残り、task-breakdown-steps.md:10 の下書きの定義と重なる |
| I1-14 | 独立-1 | low | no | self-inflicted | 参照先 | accepted | 列挙: gdd-dev.md:220・:233、subagent-dispatch.md:189-198、brainstorming-steps.md:131-134、requirements-gating-steps.md:50、reviewer-selection.md:151、state-machine.md:748-778、evals.json:379 が古い流れのまま |
| I1-15 | 独立-1 | low | no | self-inflicted | 質チェック | accepted | design-gating の配線表整合チェックが、段 1 の下書きを対応する task に数えうる |
| I1-16 | 独立-1 | low | no | self-inflicted | 断片 | accepted | 変更断片の「前の版では」が、未リリースの 旧#607 の断片を指す |
| I1-17 | 独立-1 | low | no | self-inflicted | 件数 | accepted | route に足した Tasklist Basis の分岐について、PR 本文に「未測」と記録に無い入力が書かれていない |
| I1-18 | 独立-1 | low | no | self-inflicted | 段 1 の手順 | accepted | Iterative Refinement が 3 回で収束しないと 16e を経ず、下書きが無いので design-gating に進む |
| I1-19 | 独立-1 | advisory | no | self-inflicted | 参照先 | accepted | route の 1 行目が gdd-task-breakdown のまま、次の phase は TDD |
| I1-20 | 独立-1 | advisory | no | self-inflicted | 断片 | accepted | 1 枚に `参照: tasklist.md` を足したことと basis の終了コードが、PR 本文の変更内容に無い |
