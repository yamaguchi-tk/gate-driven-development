---
lane: L1
pr: 531
follow_up_of: 529
amends: 20261016-hitl-writing-align.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3c570a84 | 0 | 5 | 0 | 2026-10-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | dc508f72 | 0 | 4 | 0 | 2026-10-16 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c445f74e | 0 | 1 | 0 | 2026-10-16 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 84f85d07 | 0 | 1 | 0 | 2026-10-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | product | fixed | § 具体例に承認サマリが無いまま、成り立たない理由（重複要約の lint）で限界に回していた。commit: e0bf4406 |
| M2 | 独立-1 | medium | no | self-inflicted | product | fixed | 名指しされていない長さの規定を例の 6 つだけ直し、断片は全部揃えたと書いていた。必須ルール 15 の「1 行で」、compact のズレ確認、gdd-brainstorming と pre-workflow の Summary Brief などが残る。commit: e0bf4406 |
| M3 | 独立-1 | medium | no | self-inflicted | product | fixed | compact の Template の選択肢の欄が「1〜3 行」のまま。commit: e0bf4406 |
| M4 | 独立-1 | medium | no | self-inflicted | product | fixed | 具体例の判断ポイントに、必須ルール 12 の 3 欄と相談役の推奨の行が無い。commit: e0bf4406 |
| M5 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 具体例の判断 2 に、いまの状態・分かったこと・2 回の理由が無く、承認ポイント 1 の根拠も失われた。commit: e0bf4406 |
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | test_hitl_lint_marker_sync_contract.py:117 のコメントが、外した「5 行以内」を理由に挙げたまま |
| L2 | 独立-1 | low | no | self-inflicted | product | accepted | lint-hitl-complexity の新しい警告文の処方が、内部用語数・承認ポイント数・詳細表数の超過には効かない |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | TEAM_ROLLOUT の手順 5 が簡易版に合わず、2 つの欄で許可しないこと・戻す条件まで確かめられると言い過ぎる |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd-requirements-gating SKILL.md:20 に、定義の無い「easy summary を先に出し」が残る |
| L5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 具体例が、差分の前から必須ルール 1・6・16・23 と承認ポイントの 8 要素の一部を満たさず、承認ポイント数の宣言も件数と合わない |
| L6 | 独立-1 | low | no | inherited | doc-claim | accepted | § 一次表示の原則の番号つき一覧だけ、判断ポイントが 7 番目（ほかの並びでは 3 番目） |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の行数・トークンの数に、測ったコマンドが無い。PR 本文にコマンドと出力を書いた。commit: なし（PR 本文） |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Affected Files に § Compact First が無く、警告文の引用が実際の文と違う |
| A3 | 独立-1 | advisory | no | self-inflicted | style | accepted | 具体例の判断ポイントと承認ポイントで番号が交差する |
| A4 | 独立-1 | advisory | no | inherited | product | accepted | full の並びの HITL は、lint-hitl-decision-quality が承認ポイント数の宣言を判断ポイントの節に探すため落ちうる（Stop hook にはつながっていない） |
| N1 | 独立-2 | medium | no | self-inflicted | product | fixed | 簡易版の WHY・要件・実装・検証の欄の行数の目安を、確認なしに限界へ回していた（依頼の原文から外れた）。commit: c684b6fa |
| N2 | 独立-2 | medium | no | self-inflicted | product | fixed | 開示していない長さの指示（まず見るところの「1-2 行」「上位 2-3 件」、必須ルール 15 の「前提の 1 行」、brainstorming-steps の「1-2 行」、requirements-gating の「短く」「短い表」）が残り、上書きの一文の範囲が skill に及ぶか読めない（依頼の原文から外れた）。commit: c684b6fa |
| N3 | 独立-2 | medium | no | self-inflicted | product | fixed | Summary Brief を短くする規定が、承認ポイントの位置関係・requirements-gating の合理化表（5 行）・skill-responsibility-matrix に残る（依頼の原文の同じ種類）。commit: c684b6fa |
| N4 | 独立-2 | medium | no | self-inflicted | product | accepted | 具体例の方向性を指す形にしたとき、「新しいセキュリティ要件」「AGENTCORE_WAIT_FOR_CI の挙動変更」の人間に戻す条件が落ちた |
| N5 | 独立-2 | low | no | inherited | doc-claim | accepted | test_hitl_lint_marker_sync_contract.py:117 のコメントが、外した「5 行以内」を前提にしたまま |
| N6 | 独立-2 | low | no | inherited | doc-claim | accepted | DISTRIBUTION_READINESS.md:144 と requirements-gating SKILL.md:20 に、古い処方の「easy summary」が残る |
| N7 | 独立-2 | low | no | self-inflicted | style | accepted | compact の選択肢・PR 分割の欄が、「1〜3 行」を外して条件だけの文になった |
| N8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 具体例の中で、決める数が 2 つか 3 つか（方向性を数えるか）が場所ごとに違う |
| N9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 具体例の判断ポイント 2 の「5% 未満」に根拠の母集団が無く、判断ごとに最悪の場合を分けていない |
| N10 | 独立-2 | low | no | self-inflicted | product | accepted | full テンプレートの欄名「OK でも許可されないこと」（空白あり）が、lint-hitl-display-integrity の綴りと合わない |
| N11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 具体例の承認ポイントに 8 要素のうち 4 つと、完了条件の変換（必須ルール 6）が無い |
| N12 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | § 判断の書き方 2 の「最初に決めてほしいことの数」が、full テンプレートと具体例では WHY の後になる |
| N13 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が PR 本文に無い。PR 本文に書いた。commit: なし（PR 本文） |
| N14 | 独立-2 | advisory | no | self-inflicted | product | accepted | 具体例で自走上限と許可しない操作を 5 か所に書いている（必須ルール 11・13 の設計） |
| N15 | 独立-2 | advisory | no | inherited | bookkeeping | accepted | request.md の「同じセッションからの範囲の連絡」は、ユーザーの発言ではなく前のセッションの注記 |
| P1 | 独立-3 | medium | no | self-inflicted | product | fixed | 選択肢・承認の材料を作る行（brainstorming-steps の概要「1-2 行」、requirements-template の「短い表」「1〜2 行」、gdd-brainstorming の「1 行で」、pre-workflow の「簡潔に」「短い要約」）に長さの指示が残り、§ 判断の書き方 も指していない（依頼の原文から外れた）。commit: ed915450 |
| P2 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 変更断片の Affected Files・Summary に、brainstorming-steps・skill-responsibility-matrix と human-check-template の 2 節が無い。commit: ed915450 |
| P3 | 独立-3 | low | no | self-inflicted | product | accepted | § 判断の書き方 の冒頭の文が出所を括弧で列挙し、この文書のほかの節と agents・commands・lint の文が字どおりには外れる（いまの該当行に実害は無い） |
| Q1 | 独立-4 | medium | no | self-inflicted | product | fixed | 同じ規定を書く brainstorming-steps.md:54 に、採用方式と理由の「1〜2 行」が残る（依頼の原文の同じ種類）。commit: 15f9be1e |
| Q2 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | pre-workflow:125 の相談の締めの選択肢に「短く出す」が残る（依頼の原文の同じ種類）。commit: 15f9be1e |
| Q3 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | pre-workflow の Options の行（:97・:110）だけ § 判断の書き方 を指していない |
| Q4 | 独立-4 | low | no | inherited | doc-claim | accepted | pre-workflow の選択肢の数が :97（2〜3）と :110（2 つまで）で食い違う |
| Q5 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Summary で、human-check-template の項目が別ファイルの変更と読める |
| Q6 | 独立-4 | advisory | no | inherited | doc-claim | accepted | gdd-brainstorming の Intake Brief（:117）とワークフロー適合判定（:174）に「短く」が残る |
| Q7 | 独立-4 | advisory | no | self-inflicted | product | accepted | runtime のトークン予算を超えていないかを tip で確かめていない（validate-plugin.sh の skill-body-budget で確かめる） |
| Q8 | 独立-4 | advisory | no | inherited | doc-claim | accepted | requirements-template.md:112 の完了条件に「（3〜5 行程度）」が残る |
