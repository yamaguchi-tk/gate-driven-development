---
lane: L1
pr: 463
follow_up_of: 446
amends: 20261013-review-convergence-rules.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1d4b6b55 | 0 | 5 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d8b21cb4 | 1 | 2 | 1 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 12d96efb | 0 | 2 | 0 | 2026-10-13 |
| 独立-4 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | f497735b | 0 | 3 | 1 | 2026-10-13 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | bfc06dd3 | 0 | 1 | 0 | 2026-10-13 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 6ec3e3aa | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | product | accepted | 依頼の 12（前の断片の全量に戻る条件）を限界に回した。通常の PR では version-not-consumed.sh の層 B が他の PR の断片の書き換えを止める。旧#455 の amends: は main の取り込みの後に使えるので、取り込みの指示を受けたらこの PR で直す |
| A2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 昇格処理の手順 3 と rollback-patterns が、次の差し戻しの行き先を逆に言い切っていた。どちらも「新値で決まる」にそろえた。commit: a4914c66 |
| A3 | 独立-1 | medium | no | self-inflicted | product | fixed | PR 作成後に (3-f) で人に戻す先が無かった。PR 作成前は順序 3、作成後は gdd-pr-review-followup の方式転換と書いた。commit: a4914c66 |
| A4 | 独立-1 | medium | no | self-inflicted | product | fixed | state-machine.md の例外一覧と gdd-completion-check が (3-f) の経路を数えていなかった。足した。commit: a4914c66 |
| A5 | 独立-1 | medium | no | self-inflicted | product | fixed | 実装 gate に (3-f) の P 型を受け入れる経路が無かった。P 型と承認済み Decision の列挙の形は Round を消費しないとし、実装 gate の手順 9・13 を合わせた。commit: a4914c66 |
| A6 | 独立-1 | low | no | self-inflicted | product | fixed | (3-a) の「両方 0 の場合だけ」が (3-f) の例外を指していなかった。commit: a4914c66 |
| A7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 新しい断片の全差分の条件と昇格処理の書き方が差分と合わなかった。commit: a4914c66 |
| A8 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | Decision Retake の行が state-field-tiers.md に無く、書式に値域と箇条の記号が無かった。commit: a4914c66 |
| A9 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | Medium Disposition の recorded に task の参照を書かせていた。申し送りの正本を Issue にし、recorded は Issue 参照にした。commit: a4914c66 |
| A10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | pr-review-followup の人に戻す条件が high だけで、取り直しの記録の置き場が無かった。commit: a4914c66 |
| A11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋が差分より狭かった。commit: なし（PR 本文） |
| A12 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が抜粋に無い。PR 本文の末尾の節に書く |
| A13 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の type を minor にした。commit: a4914c66 |
| A14 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | agent の「個々の finding も」で列挙の形の category が (3-f) の外に読めた。commit: a4914c66 |
| A15 | 独立-1 | advisory | no | self-inflicted | style | accepted | (3-f) の 2 行に規定を詰めている。references の行予算の余裕が 0 なので分けない |
| B1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | Round を消費しない Decision の finding が severity で限られず、文字どおりに読むと違反を許す high と実害クラスの medium が実装 gate で advisory として通った。medium 以下・実害クラスでないものに限った。commit: 81281ad2 |
| B2 | 独立-2 | medium | no | self-inflicted | product | fixed | 「どの gate でも Round を消費しない」が実装 gate 以外で実装されていなかった。B1 と同じ文で、実装 gate の Round の計上に絞り、design gate では直すと書いた。commit: 81281ad2 |
| B3 | 独立-2 | medium | no | self-inflicted | product | fixed | rollback-patterns の 4 択の読み替えが (3-f) から着いたときに揃っていなかった（依頼の原文の行）。commit: 81281ad2 |
| B4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | (3-a) の主文に (3-f) の例外を括弧で継ぎ足し、全量に戻る条件 1 と食い違う（読み手は全量に倒れ、fail-closed 側） |
| B5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | phase-progression・human-check-template・autonomy の語彙が、順序 3 の発火条件に (3-f) を名指していない |
| B6 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | pr-review-followup の証跡のテンプレートに取り直しを書く欄が無く、常に使用済みに倒れる（fail-closed 側） |
| B7 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | Decision Retake の行に PR の識別が無く、PR を作り直すと前の行が残って使用済みに見える（fail-closed 側） |
| B8 | 独立-2 | low | no | self-inflicted | product | fixed | 申し送りの Issue を読む経路が、task が無いときに無かった（依頼の原文の行）。実装の着手時に main が読むと書いた。commit: 81281ad2 |
| B9 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 前の PR の変更断片が削除済みのテストを検証コマンドとして指す。A1 と同じく、main の取り込みの後に amends: で直す |
| C1 | 独立-3 | medium | no | self-inflicted | product | accepted | Issue を読む規定が、将来のセッションからたどれない（依頼の原文の行。3 巡目の後のため限界に書き、依頼から外れたままと明記する）。案は ADR の Consequences に Issue 参照を書くこと |
| C2 | 独立-3 | medium | no | self-inflicted | product | accepted | Round を消費しない範囲を実装 gate に絞ったので、completion-check では P 型の medium が blocker に戻り Completion Rounds を消費する |
| C3 | 独立-3 | low | no | inherited | product | accepted | 実装 gate の 8a・123 行と state-field-tiers の Gate Rounds の定義が (3-f) の除外を持たない（判定は手順 9 が正しく除外する） |
| C4 | 独立-3 | low | no | inherited | doc-claim | accepted | rollback-patterns の見出しの括弧が PR 作成前に限っていない |
| C5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片に Issue を読む経路が書かれていない |
| C6 | 独立-3 | advisory | no | self-inflicted | product | accepted | design gate の「直す」が P 型で何を直すかを書いていない |
| C7 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | rollback-patterns の真ん中の読み替えに (3-f) が名指しされていない |
| D1 | 独立-4 | medium | no | self-inflicted | product | accepted | 申し送りの Issue を読む経路に入口が無い（C1 と同じ。依頼の原文の行で、3 巡目の後のため限界に書き、依頼から外れたままと明記する） |
| D2 | 独立-4 | medium | no | self-inflicted | product | accepted | (3-f) が列挙の形への finding の category を決めておらず、実害クラスが付くと承認済みの Decision が差し戻される |
| D3 | 独立-4 | medium | yes | inherited | approval-path | fixed | gdd-dev.md STEP 1 の方式転換 4 択への返答の振り分けが (3-f) の上限から着いた入口を挙げず、選んでいない案の承認が記録されうる。メニューの名前で振り分け、(3-f) の入口を含めた。commit: cefef453 |
| D4 | 独立-4 | low | no | inherited | doc-claim | accepted | phase-progression の順序 3 の条件の写しが (3-f) を含まない |
| D5 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | Gate Rounds を足すほかの箇所（8a など）に (3-f) の除外が無い（C3 と同じ） |
| D6 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | pr-review-followup の証跡の書式に取り直しの欄が無い（B6 と同じ） |
| D7 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | rollback-patterns の見出しが PR 作成後にも 4 択を当てる（C4 と同じ） |
| D8 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | gdd-pr-review-followup の checkpoint の trigger の語彙に (3-f) の戻しが無い |
| D9 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 削除したテストを、ほかの未リリースの断片（3 本）がまだ説明している |
| D10 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 軽いレーンで (3-f) の基準が当たるかが root CLAUDE.md 手順 6 に書かれていない |
| D11 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | (3-a) の主節にだけ例外を足し、箇条には書いていない（B4 と同じ） |
| D12 | 独立-4 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が抜粋に無い。PR 本文の末尾の節にある |
| E1 | 独立-5 | medium | no | self-inflicted | product | fixed | 足した括弧で runtime profile の推定 token が予算を 36 超えた（実測 30161 > 30125、45516 > 45480）。行を短くして予算内（rc=0）にした。commit: 22ac9c48 |
| E2 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に commands/gdd-dev.md が無い。commit: なし（PR 本文） |
| E3 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 変更断片に commands/gdd-dev.md が無い。commit: 22ac9c48 |
| E4 | 独立-5 | low | no | inherited | product | accepted | PR 作成後の (3-f) の戻し先（followup の 3 択）への案名の無い返答は STEP 1 で振り分けられない（同じ PR での 2 回目の (1) にも前からある穴） |
| E5 | 独立-5 | advisory | no | inherited | doc-claim | accepted | human-check-template の事前回答の上限の列挙に (3-f) が無い（効く経路は無い） |
| G1 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | runtime の token 予算に収めるため、commands/gdd-dev.md の振り分けの行から (3-f) と 4 択の指し先（ファイル名・節）を外した。振り分けの結果は変わらない |
