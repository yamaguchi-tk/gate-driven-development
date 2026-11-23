---
lane: L1
pr: 576
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a8f39c68 | 0 | 4 | 0 | 2026-10-24 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 4434b618 | 0 | 2 | 0 | 2026-10-24 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | fe2c9c64 | 0 | 0 | 0 | 2026-10-24 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 独立-1 | medium | no | self-inflicted | scope | accepted | ユーザーが推奨どおりと回答（2026-10-24 11:22）: 依頼の「分割を先に相談」の相談の記録なしに、手順 6 を分けてこの PR の範囲を決めた。PR 本文に分割の案と問いを書く |
| M-2 | 独立-1 | medium | no | self-inflicted | scope | accepted | ユーザーが推奨どおりと回答（2026-10-24 11:22）: 段 1 の成果物「要点を 1 枚にまとめる」を「詳細設計を段 1 に寄せる」と読み替えた |
| M-3 | 独立-1 | medium | no | self-inflicted | product | fixed | リスクの段の行を full テンプレートにだけ足し、人に出る compact テンプレートに無いので、表示されない。commit: 4434b618 |
| M-4 | 独立-1 | medium | no | self-inflicted | product | fixed | 列挙: quick (standard) の design.md を最小とする文が task-sizing.md:91・:120・:269 と gdd-brainstorming の SKILL.md:95・:196 に残り、広い要件・light の例外も無い。commit: 4434b618 |
| L-1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | requirements-template.md:167 が express に design.md があるように書き、実際に変わったのは quick (standard) の最小の選択肢が消えたことだと読めない。commit: 4434b618 |
| L-2 | 独立-1 | low | no | self-inflicted | product | fixed | express は request-crosscheck.md が無いので、足した行は express で毎回「高」になる。commit: 4434b618 |
| L-3 | 独立-1 | low | no | self-inflicted | product | fixed | 「design-gating Step 5 の粒度」の場所を示さず、brainstorming の runner の読む範囲から届かない。commit: 4434b618 |
| L-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「Step 5 は確かめて足りない分を足す」が design-gating の SKILL.md に無く、断片と PR 本文の書く変化が手順に無い。commit: 4434b618 |
| L-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「人が詳細設計まで見て承認できる」は、human check が詳細を出さず承認が詳細設計を固定しないことと合わない。commit: 4434b618 |
| A-1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | human-check-template.md の standard の具体例の「やること」に、リスクの段の行が無い |
| A-2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | brainstorming-steps.md:92 と human-check-template.md:542 の「design-gating に送る」の送り先が古い |
| A-3 | 独立-1 | advisory | no | inherited | doc-claim | next-pr | 「やること」の既存の行（タスクサイズ・フロー・通過予定 gate 数）も compact に無く、brainstorming-steps.md:130 の指し先が人に届かない |
| M-5 | 独立-2 | medium | no | self-inflicted | scope | fixed | ユーザーが (i) と回答（2026-10-24 14:36）し、Broad Requirement: true は human check で scope を選んだ後に Step 5 で書くと明記した: requirements-template.md:167 の括弧「広い要件は scope を絞った後」が、広い要件を詳細設計を着手時に寄せる範囲から外すと読め、SKILL.md:152 とも合わせて読みが決まらない。commit: a7554b7a |
| M-6 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 上位正本 self-contained-contract.md:94・:97 に human check 前の design.md を最小・最低限とする文が残る（M-4 の残り）。commit: fe2c9c64 |
| L-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | express の昇格の手順 2（task-sizing.md:269）を詳細設計の粒度にしたが、state-machine.md:385 は design-gating で詳細化するとし、時機が食い違う |
| L-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 最小構成でよい条件に Quick Standard Design Gate Optional が入るかが決まらず、12 の時点で成り立つかも分からない（M-4 の light の例外の残り）。commit: fe2c9c64 |
| L-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | gdd-planning-reviewer.md:327 が requirements phase では配線表が無いとして整合チェックを省く理由が、配線表を着手時に書くと成り立たない |
| L-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | リスクの段の行で「無い」を外し「express は省く」を足したので、express 以外で記録が無いときに行ごと省くと読める余地がある |
| L-10 | 独立-2 | low | no | self-inflicted | style | accepted | gdd-request-code-crosscheck.md:41 の `-compact.md` が実パスとして grep で引けない |
| L-11 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 最小構成の条件を運用レベル light にしたので、light で express から昇格した quick (standard) に requirements-template.md:167 と task-sizing.md の昇格の手順が別の粒度を求める |
| L-12 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | task-sizing.md:120 の「原則として…ただし」が、Optional に当たるタスクを詳細設計の粒度の例外と読ませる |
| L-13 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | self-contained-contract.md:97 がテンプレートの最小構成（Human Check Questions を含まない）を指し、:98 の全骨組みに Human Check Questions を求める文と食い違う |
| L-14 | 独立-3 | low | no | self-inflicted | style | accepted | self-contained-contract.md:94 の「requirements.md を最小構成でよい」の文が崩れ、「下の行」がどの行か分からない |
| A-4 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「optional の節の言い換えの 1 文を消し」が、Optional のときの最小構成の許可を消したことを字数の調整として書いているように読める |
