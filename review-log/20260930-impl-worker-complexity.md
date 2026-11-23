---
lane: L1
pr: 旧#249
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus（この前に tip 3e1705d9 で起動した全差分巡は、読み込みの照合が PR 本文 25/24 行で合わず無効にした。その起動の指摘〔high 0・medium 1・low 10・advisory 9〕は eb74edef までに反映し、この巡の材料にした） | eb74edefe76b846b8d15a552bc6988f7e6da4686 | 0 | 3 | 0 | 2026-09-30T13:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | d956b0bf44c867ae993e7d6634283760067fc8e9 | 0 | 0 | 0 | 2026-09-30T14:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | escalation-ladder | fixed | BLOCKED の再 dispatch を一律に heavy にしていて、remediation worker が格下げされ、heavy は同じ model の retry になっていた。1 段上の worker（standard → heavy → remediation）にし、Gate Rounds 2 以上では remediation worker より下げない。commit: ddb8f835 |
| F2 | 独立-1 | medium | no | self-inflicted | wiring-gap | fixed | Express の最小構成の tasklist に Complexity が無く、Express の worker が常に heavy になっていた。phase-progression と TDD の最小構成に Complexity を足した。commit: ddb8f835 |
| F3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | gdd-model-routing の旧規定（sonnet が既定で risk 時だけ opus）が残り、新規定と既定の向きが逆だった。Complexity と Gate Rounds で選ぶ記述に置き換えた。commit: ddb8f835 |
| F4 | 独立-1 | low | no | self-inflicted | acceptance-set-asymmetry | fixed | sonnet 固定の worker を工程を見ずに免除し、opus 必須の工程で model 省略なら無音、明示なら警告になっていた。固定 model の表を足し、model 省略時は agent 定義の model で工程を判定する。免除は opus 固定だけ。commit: ddb8f835 |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 実装の工程で model 未指定の general-purpose に hook が model="sonnet" を勧めていた。typed worker を model 省略で使うよう案内を変えた。commit: ddb8f835 |
| F6 | 独立-1 | low | no | self-inflicted | wiring-gap | fixed | worker 本文の plugin 相対パスを worker が解決できなかった。手順 2a・3 で ## Plugin Root を渡し、本文の参照を <Plugin Root> から読む。無ければ NEEDS_CONTEXT。commit: ddb8f835 |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | § Fixed Model の Claude Code の行が sonnet + medium のままで既定を表していなかった。worker ごとの model・effort を書いた。commit: ddb8f835 |
| F8 | 独立-1 | low | no | self-inflicted | test-power | fixed | controller が使う worker 名（fixed-models の段落・手順 3）を agent 定義と突き合わせていなかった。文書から worker 名を抜き出して agent 定義と一致を確かめるテストを足した。commit: 3708bb80 |
| F9 | 独立-1 | low | no | inherited | doc-claim | next-pr | gdd-model-routing:112 の「max は使わない」が :153 と矛盾する |
| F10 | 独立-1 | low | no | inherited | doc-claim | next-pr | gdd-implementation-gating:41 の security reviewer の適用条件が Step 3（:152）より狭い |
| F11 | 独立-1 | low | no | inherited | style | next-pr | gdd-task-breakdown の雛形の見出しが `### Task N:` で、task-breakdown-steps の正準形と違う |
| F12 | 独立-1 | low | no | inherited | style | next-pr | task-breakdown-steps § Task Self-Review の番号が 9, 10, 9, 10, 11, 12 と重複している |
| F13 | 独立-1 | advisory | no | self-inflicted | style | accepted | Complexity の語が tasklist の欄・runner の --complexity・task-sizing の評価の 3 つの意味で使われる |
| F14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 既存の tasklist は heavy で動くという説明が Gate Rounds 2 以上の task を除いていなかった（断片と PR 本文は ddb8f835 で書き足した） |
| F15 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 雛形に足した行を、既存の段落の改行を詰めて行予算で相殺している |
| F16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | worker 本文の「scope・AC を変える判断は止めて返す」と、DONE_WITH_CONCERNS で仕様乖離を受ける経路がずれている |
| F17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | gdd-systematic-debugging:153 が remediation worker を agent 定義の名前で書いていない |
| F18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 手順 3 の選び方に「Claude Code では」が付いていなかった（ddb8f835 で手順 3 を書き直したときに付けた） |
| F19 | 独立-1 | advisory | no | self-inflicted | product | accepted | task-breakdown-steps の雛形の括弧書きを値ごと写すと、standard と一致せず heavy に倒れる（費用だけの害） |
| F20 | 独立-2 | medium | no | self-inflicted | doc-claim | next-pr | fixed-models.md:37 の正本が、3 つの worker を model 省略時に免除すると書いたまま（免除は opus 固定だけに変わった） |
| F21 | 独立-2 | medium | no | self-inflicted | doc-claim | next-pr | fixed-models.md:12 の X-61 の段落が、免除の例に sonnet の gdd-implementation-worker を挙げている |
| F22 | 独立-2 | low | no | self-inflicted | wiring-gap | next-pr | hook の実装の工程向けの案内が ## Plugin Root を伝えず、runner や worker 以外の general-purpose にも worker を案内する |
| F23 | 独立-2 | low | no | self-inflicted | product | next-pr | sonnet の worker を opus 必須の工程で起動したときの警告が「model=sonnet が指定されています」で、対処（model=opus の明示）も設計の組み合わせにならない |
| F24 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | heavy・remediation の agent 定義の description と fixed-models.md:41 が、BLOCKED の昇格先としての使い方を含んでいない |
| F25 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 断片と PR 本文が、frontmatter の model で判定する対象を「型付きの agent」と広く書いている（表に無い runner は含まない） |
| F26 | 独立-2 | low | no | self-inflicted | wiring-gap | next-pr | subagent-dispatch.md:343・impl-gating:205・:209 の remediation worker の起動に ## Plugin Root の受け渡しが書かれていない |
| F27 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | test_implementation_worker_agents.py の docstring が「hook が worker を免除する」のまま |
| F28 | 独立-2 | advisory | no | self-inflicted | product | accepted | BLOCKED で昇格しても task に残らず、次の起動で Complexity から選び直して元の worker に戻る |
| F29 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | prefix の有無の比較が、両方とも空文字でも通る |
| F30 | 独立-2 | advisory | no | self-inflicted | style | accepted | 文書の段落を文の書き出しで探していて、語を直すと error で落ちる。prefix の assertIn は語の有無だけを見る |
| F31 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | hook の案内文の worker 名を突き合わせるテストが無く、部分一致の assertIn は heavy にも一致する |
| F32 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の検証の節に、固定 model の表を frontmatter と突き合わせるテストが書かれていない |
