---
lane: L1
pr: 627
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0a9dfcbc | 0 | 5 | 0 | 2026-10-31 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e2e055a1 | 0 | 2 | 0 | 2026-10-31 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 4fffb445 | 0 | 2 | 0 | 2026-10-31 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 7a93c792 | 0 | 0 | 0 | 2026-11-01 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | review-log の書式の正本を README に向けたが、README は外の計画書を正本とし、表の書式も持たない。README は review-log の群の PR で直す |
| I1-2 | 独立-1 | medium | no | self-inflicted | intent | fixed | 依頼の ① から外れ: hook の実行時の文に計画の番号と実測の比率が残る。同じファイルのコメントの番号・実測値も外した。commit: b0c879d8 |
| I1-3 | 独立-1 | medium | no | self-inflicted | intent | fixed | 依頼の ②④ から外れ: 外した計画の番号が別の skill 2 本に残る。commit: b0c879d8 |
| I1-4 | 独立-1 | medium | no | self-inflicted | intent | fixed | 依頼の ②④ から外れ: rollback-patterns.md に計画のレビュー指摘番号が残る。commit: b0c879d8 |
| I1-5 | 独立-1 | medium | no | self-inflicted | intent | fixed | 依頼の ①④ から外れ: 触った skill 4 本に実測の値が残る。同じ行の session ID も外した。commit: b0c879d8 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文が「日付は変えていない」と書くが、標本の期間の日付を外した箇所がある。PR 本文を直す。commit: なし（PR 本文） |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 書き直しで、元の計測が示した代償や事例の意味が一般の断定に寄った箇所がある |
| I1-8 | 独立-1 | low | no | self-inflicted | intent | fixed | 依頼の ② から外れ: 過去のタスクの AC 番号が触ったファイルと規則の文書に残る。見出しと参照を揃えて外した。commit: b0c879d8 |
| I1-9 | 独立-1 | low | no | inherited | doc-claim | accepted | context-budget.md の § X-4 の参照が別のファイルを指す（既存） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | session ID が規則の文書に残る。I1-5 で直した行の分は外した |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片に、plugin の配布物でない root の文書の変更を書いている |
| I1-12 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 外した見出しや語を、scripts とテストのコメントが古い形で引く。その群の PR で揃える |
| I1-13 | 独立-1 | advisory | no | self-inflicted | intent | fixed | 依頼の「review-log-present.sh の全行」から外れ: 巡の ID が残る。commit: b0c879d8 |
| I1-14 | 独立-1 | advisory | no | self-inflicted | intent | fixed | 依頼の ② から外れ: 「（Fix X）」のラベルが残る。commit: b0c879d8 |
| I1-15 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence の記録が無い。notes に対象外の理由を書いた。commit: b0c879d8 |
| I2-1 | 独立-2 | medium | no | inherited | intent | fixed | 依頼の ② から外れ: 計画書の項目番号 OT-F3 が skill と reference に残る。commit: 4fffb445 |
| I2-2 | 独立-2 | medium | no | self-inflicted | intent | fixed | review-log-present.sh で指摘番号の説明を外した後も、本文が H2〜H6 のラベルと方針メモ-2 を使い続ける。何をした案かの文に置き換えた。commit: 4fffb445 |
| I2-3 | 独立-2 | low | no | self-inflicted | intent | fixed | state-schema.json の同じ行に巡の番号が残る。commit: 4fffb445 |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文の「外した」が実際と合わない。I2-1〜I2-3 を直して合わせた。commit: 4fffb445 |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | セッション ID を中身の無い汎用の文に置き換えた。brainstorming-steps.md は repo の中の出典から中身を書いた。commit: 4fffb445 |
| I2-6 | 独立-2 | low | no | self-inflicted | intent | accepted | 過去のタスクの AC 番号・レビューの巡や指摘の番号・セッション ID を外すのは、依頼の 3 種類より広いかもしれない。ユーザーが外したままにすると決めた（2026-11-02） |
| I2-7 | 独立-2 | advisory | no | self-inflicted | style | accepted | model gate hook のコメントで同じことを 2 回言っている |
| I2-8 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 過去の steering の slug が、事例の出典として残る |
| I2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 凍結済みの監査アンカーが、名前を変えた見出しを指したまま。docs の群の PR で扱う |
| I3-1 | 独立-3 | medium | no | inherited | intent | fixed | 依頼の ②④ から外れ: reviewer-common.md・subagent-dispatch.md・gdd-model-routing に、レビューの巡や指摘の番号が残る。順 1 の群を同じ型で grep し、残りは語の誤検知だけと確かめた。commit: 5c415148 |
| I3-2 | 独立-3 | medium | no | inherited | intent | fixed | 依頼の ②④ から外れ: brainstorming-steps.md に計画の項目番号 F-3 と過去の steering の slug が残る。commit: 5c415148 |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | review-log-present.sh の書き直しで、再発の時期が「2 つ目の案の直後」になり、時系列が 1 段ずれた |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | version-not-consumed.sh のコメントが、review-log-present.sh から外した H ラベルを名指ししたまま。tests/checks の群の PR で扱う |
| I3-5 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の references の本数が古い。数え直した。commit: 5c415148 |
| I3-6 | 独立-3 | advisory | no | inherited | doc-claim | accepted | 過去のタスク ID らしい記述・日付の列・罠7 のラベルが残る（罠7 は reviewer の出力の接頭辞） |
| I3-7 | 独立-3 | advisory | no | self-inflicted | style | accepted | review-log-present.sh の書き換えた行の折り返し幅が揃っていない |
| I4-1 | 独立-4 | low | no | self-inflicted | intent | accepted | 依頼の 3 種類の外（AC 番号・巡や指摘の番号・セッション ID・steering の slug）まで外した。依頼が 2 通りに読めるのでユーザーに問い、外したままにすると決まった（2026-11-02） |
| I4-2 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | 断片の references の本数が state-machine.md を数えていないおそれ。merge-base からの git diff --name-only で 28 本（state-machine.md・state-schema.json を含む）、skills 13 本と数え、合っていた |
| I4-3 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 外した F-3 のラベルを evals の scenario が名指ししたまま。採点の語は残る。evals の群の PR で扱う |
| I4-4 | 独立-4 | advisory | no | inherited | doc-claim | next-pr | context-budget.md が state-machine.md の § X-4 を指すが、節は phase-progression.md にある |
