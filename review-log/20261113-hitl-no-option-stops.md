---
lane: L1
pr: 669
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1101af91ebb6a97654ccd0cbebbbf8329bb1c908 | 0 | 7 | 1 | 2026-11-13 |
| 方針メモ-1 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 1101af91ebb6a97654ccd0cbebbbf8329bb1c908 | 0 | 0 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | bd10d9dd65f8c29ca825bf43e16bbeb23be3bb96 | 0 | 6 | 1 | 2026-11-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 8d0d1b12e0115ca41b11352fa2bec6f966a61be0 | 0 | 5 | 1 | 2026-11-13 |
| 方針メモ-2 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 8d0d1b12e0115ca41b11352fa2bec6f966a61be0 | 0 | 0 | 0 | 2026-11-13 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 3523466a6463a03006f4330a0366ffbaad0fc44e | 0 | 1 | 1 | 2026-11-13 |
| 方針メモ-3 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 3523466a6463a03006f4330a0366ffbaad0fc44e | 0 | 0 | 0 | 2026-11-13 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | a923661de79bd535728d898c6dac90829b256127 | 0 | 2 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 列挙: 設計: 変える（§ 止まり直さないもの 3 が STEP 1 とは別の進む経路を持った）。§ 止まり直さないもの 3 が「次の工程に進む」と書き、全点と OK の範囲の明確な承認を条件にしていないので、一部の点だけの返事で approved に進む読み方ができる。方針メモ-1 で、§3 から進む経路を外し、gdd-dev.md #10 STEP 1 に「表示した案の名指し」の行を足して受ける形を閉じた。commit: bd10d9dd |
| I1-2 | 独立-1 | medium | no | self-inflicted | rule-conflict | fixed | § 止まり直さないもの 3 と、一部変更で全点を再提示する既存の規定（human-check-template.md:366・789、requirements-gating-steps.md:151、gdd-brainstorming・gdd-requirements-gating の SKILL、gdd-dev.md:190）がぶつかる。I1-1 の再設計で、各所に名指しは変更要求ではないと 1 文ずつ足した。commit: bd10d9dd |
| I1-3 | 独立-1 | medium | no | self-inflicted | rule-conflict | accepted | subagent-dispatch.md:143 の HITL Pending Hard Invariant（human-check-waiting なら次の最終回答で HITL を表示）が § 止まり直さないもの 2・4 とぶつかる |
| I1-4 | 独立-1 | medium | no | self-inflicted | rule-conflict | accepted | 案・承認ポイントを必須にする既存の規定（Broad Requirement の scope 選択、非標準の自前実装、PR の分け方の 3 案、brainstorming-steps.md:79 の 2〜3 案）と § 止まり直さないもの 1 の優先関係が無い |
| I1-5 | 独立-1 | medium | no | self-inflicted | rule-conflict | accepted | Round 上限の一括提示を 1 点にできるとしたが、選択肢の正本（requirements-gating-steps.md 契約 1・Step 7）と「OK」の扱い（:138）が変わっておらず、1 点に OK と答えるともう 1 回止まる |
| I1-6 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 確認待ち: 承認の hook の拒否による出し直し 12 件を、表示前の lint の手順だけにし、止める側の変更を 旧#664 の後の PR に回した。PR 本文の限界の節に問いを書いた |
| I1-7 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | PR 本文に、効果を読む時期と撤去する条件が無い |
| I1-8 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 確認待ち: 判断ポイント 0 件の要件の承認と Round 上限の一括提示を止まるまま残した。PR 本文の限界の節の問い |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 止まり直さないもの の「続ける意図の文を書くと押し返される」はコードと合わない（_stop_on_human_check_loophole は即停止する） |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 一次表示の原則 7 の固定文「確認中（届いたら全文を出し直す）」が、出し直さない場合と食い違う |
| I1-11 | 独立-1 | low | no | self-inflicted | rule-conflict | accepted | human-check-template.md:374 の「単一候補なら他案なし」が :438 と compact にそろっていない |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 表示前に当てる lint-hitl-decision-fields.py は、依頼との差の欄のほかに完了条件の変換なども検査し、compact をそのまま埋めた提示でも落ちる |
| I1-13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | changelog の Affected Files・Summary に brainstorming-steps.md と lint の手順が無く、件数の文が差分と合わない |
| I1-14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の表の「止めた規則」の欄が既存の規定と合わない（聞き直しは全点の再提示の規定、回答への再掲は HITL Pending Hard Invariant）。commit: なし（PR 本文） |
| P1-1 | 方針メモ-1 | low | no | self-inflicted | approval-path | accepted | 2 本は「STEP 1 に名指しの行を足し、§3 は指すだけ」で一致し、割れたのは、承認の語の無い名指しだけの返答を 1 問で止めるか（Opus-2）止めないか（Opus-1）。表示の「OK は…という意味」の案名を入れ替えた承認と読めるので、止めない側を採った。限界: 推奨でない案を名指ししたとき、その案の依頼との差は表示に無いことがある |
| I2-1 | 独立-2 | medium | yes | self-inflicted | approval-path | fixed | 設計: 変える（STEP 1 に新しい分類の行を作った）。名指しの行に「差が なし の点だけ」の限定が無く、推奨が依頼より狭い点に「推奨で」と答えると承認に進む。新しい行を外し、「推奨で」と全点の名指しを既存の「明確な承認」に入れて限定を効かせた。commit: 8d0d1b12 |
| I2-2 | 独立-2 | medium | no | self-inflicted | rule-conflict | fixed | 名指しの行と § 止まり直さないもの 3 で分類が逆になる（AC の意味が変わる名指し・express の Round の条件が §3 にだけある）。I2-1 の設計の変更で条件を STEP 1 の明確な承認の行に移した。commit: 8d0d1b12 |
| I2-3 | 独立-2 | medium | no | self-inflicted | rule-conflict | accepted | 名指しの行が、どの確認への返答かを限っていない（方式転換 4 択の 1〜3 つ目や Handoff の案の名指しが STEP 2 に入りうる） |
| I2-4 | 独立-2 | medium | no | self-inflicted | rule-conflict | fixed | express の追加 Round の条件が既存の 3 項目より 1 つ少ない。明確な承認の行で、範囲・Files・Implementation Policy が変わる名指しを修正指示に送る形にした。commit: 8d0d1b12 |
| I2-5 | 独立-2 | low | no | self-inflicted | rule-conflict | fixed | 「その点だけを出し直す」が全点を載せる規定と合わない。§ 止まり直さないもの 3 に、答えた点を 1 行と依頼との差で残す形だけを書き、STEP 1 からはそこを指した。commit: 8d0d1b12 |
| I2-6 | 独立-2 | medium | no | self-inflicted | rule-conflict | accepted | compact から「案が実質 1 つ」の注記を外したので、原因に挙げた compact の 採用しない案 の必須が残る（express の読み込み量の上限のため） |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | changelog と PR 本文が compact を合わせたと書くが、compact の変更は 0 行。changelog から外した。commit: 8d0d1b12 |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 「名指し」の語が rollback-patterns・requirements-gating-steps の「案名の無い承認」と逆の意味になる。新しい行を外し、「推奨で」は明確な承認に入れた。commit: 8d0d1b12 |
| I2-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | requirements-gating-steps.md:151 の変更指示の例「3 は別案で」と足した注記が食い違い、括弧の句点が崩れている |
| I2-10 | 独立-2 | medium | no | self-inflicted | request-scope | accepted | 確認待ち: 判断ポイント 0 件の要件の承認と Round 上限の一括提示を止まるまま残した（I1-8 より severity が高いので再掲にしない）。PR 本文の限界の節の問い |
| I2-11 | 独立-2 | medium | no | self-inflicted | request-scope | re-reported | I1-6 の再掲（承認の hook の拒否による出し直し 12 件は手順を足しただけ） |
| I2-12 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | changelog の「当たるのは 36 件」が 1 件多い。35 件と 12 件・1 件を分けて書いた。commit: 8d0d1b12 |
| I2-13 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | §3 の「進む経路を持たない」が同じ項の中身と合わない。§3 を書き直した。commit: 8d0d1b12 |
| I2-14 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | express の読み込み量の上限 30208 を実測で確かめていない（validate-plugin.sh で確かめた） |
| I3-1 | 独立-3 | medium | yes | self-inflicted | approval-path | fixed | 列挙: 設計: 変える（名指しを承認に入れる条件を、返答の形でなく「全点に答えた」という読みに任せた）。「B で」「2 で」のような点の番号の無い名指しが、点が 2 つ以上の確認で明確な承認に入りうる。方針メモ-2 で、承認に入る形を「点の番号と案名の組で全点」と「1 点の確認での案名だけ」の許可リストに閉じ、それ以外の名指しは「どの点を何にしますか」の 1 行で聞き返すことにした。入力者は人の返答で、2026-11-09〜13 の返事に「案A」「推奨で」の名指しがある。commit: 4650262 |
| I3-2 | 独立-3 | medium | no | self-inflicted | rule-conflict | fixed | 明確な承認の行が修正指示の行より後ろにあり、順に判定すると「1 は B で」が先に修正指示に当たる。明確な承認の行を修正指示の前に移した。commit: 4650262 |
| I3-3 | 独立-3 | medium | no | self-inflicted | rule-conflict | accepted | 「名指しは変更要求ではない」の写し 5 か所が、明確な承認の例外（推奨でない案で AC などが変わるなら修正指示）と食い違う |
| I3-4 | 独立-3 | medium | no | self-inflicted | request-scope | accepted | 確認待ち: 推奨でない案を全点の名指しで選び AC が変わるときは、今までどおり修正指示で再提示か差し戻しになり、聞き直しの一部が残る。PR 本文の限界の節に問いを書く |
| I3-5 | 独立-3 | medium | no | self-inflicted | rule-conflict | accepted | 「AC の意味が変わる」の境界が決まらず、同じ返答で承認か修正指示かが main ごとに割れうる |
| I3-6 | 独立-3 | medium | no | self-inflicted | request-scope | re-reported | I2-10 の再掲（判断ポイント 0 件の承認と Round 上限の一括提示は止まるまま） |
| I3-7 | 独立-3 | medium | no | self-inflicted | request-scope | re-reported | I1-6 の再掲（承認の hook の拒否による出し直し 12 件は手順を足しただけ） |
| I3-8 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | changelog の「規定を変えたのは 35 件」に、止まるままの Round 上限 4 件と、修正指示に残る名指しが入る |
| I3-9 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界で compact が 旧#664 と重なると書くが、compact は変えていない。commit: なし（PR 本文） |
| I3-10 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 返答ガイド（human-check-template.md:366）に内部の指し先（commands/gdd-dev.md #10 STEP 1）が入り、人への表示に出る |
| I3-11 | 独立-3 | low | no | self-inflicted | approval-path | accepted | 推奨でない案の名指しでは、差が なし の点だけの限定が推奨の案の欄で決まる（PR 本文の限界に開示） |
| P2-1 | 方針メモ-2 | low | no | self-inflicted | approval-path | accepted | 2 本とも判定順の入れ替えで一致。割れたのは、承認に入る名指しを結果の条件（全点の案が 1 つずつに決まる返答。Opus-1）で書くか、形の許可リスト（点の番号と案名の組、1 点なら案名だけ。Opus-2）で書くか。読み違えで承認側に倒れない許可リストを採った。限界: 1 点の確認で案名が数字のとき「1 で」が点の番号とも読める（推奨が同じなら結果は同じ） |
| I4-1 | 独立-4 | medium | yes | self-inflicted | approval-path | fixed | 列挙: 設計: 変える（明確な承認の定義を、返答の中身ではなく判定の順序で守っていた）。明確な承認を修正指示より先に判定したため、名指しや「OK」に変更要求が付いた返答が承認に当たりうる。方針メモ-3 で、明確な承認を「承認の語か全点の名指しだけの返答」の許可リストにし、変更・条件が付けば修正指示、変更でない文なら聞き返すとした。入力者は人の返答で、2026-11-09〜13 の名指しの返答 21 件に変更の語が付いたものは 0 件（正規表現の目安）。commit: 4293b30 |
| I4-2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 「推奨で」だけの返答が、§ 止まり直さないもの 3 を先に読むと 2 点以上で聞き返しに読める |
| I4-3 | 独立-4 | medium | no | self-inflicted | request-scope | re-reported | I2-10 の再掲（判断ポイント 0 件の承認と Round 上限の一括提示は止まるまま） |
| I4-4 | 独立-4 | medium | no | self-inflicted | request-scope | re-reported | I1-6 の再掲（承認の hook の拒否による出し直し 12 件は手順を足しただけ） |
| I4-5 | 独立-4 | low | no | self-inflicted | request-scope | re-reported | I3-4 の再掲（推奨でない案の名指しで AC が変わるときの聞き直し） |
| I4-6 | 独立-4 | low | no | self-inflicted | bookkeeping | accepted | 新しい聞き返しの分岐に、当たる件数の実測が PR 本文に無い。返答 136 件で、2 点以上の確認に点の番号の無い名指しは 2 件（目安）と測り、PR 本文に書いた |
| I4-7 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 一次表示の返答ガイドが、受け付ける名指しの形（点の番号と案名の組）を示していない |
| P3-1 | 方針メモ-3 | low | no | self-inflicted | approval-path | accepted | 2 本とも、明確な承認の行全体を許可リストにし、判定順は承認が先のままで一致。割れたのは、変更でない文が付いた返答を聞き返すか（Opus-2）修正指示にするか（Opus-1）。選んだ案が消えない聞き返しを採った。限界: 返答の分類は main の読みで、hook は返答を見ない |
| I5-1 | 独立-5 | medium | no | self-inflicted | approval-path | accepted | 「ほかに文がある返答は承認に入れない」で、礼や状況説明の付いた OK（「OK、ありがとうございます」）も聞き返しになり、§ 曖昧返答の検出の表（状況説明つきの OK は approved）と食い違う。PR 本文の限界に書いた |
| I5-2 | 独立-5 | medium | no | self-inflicted | rule-conflict | accepted | 決定済みの 1 行と全欄の点が混ざる再提示は、lint-hitl-decision-quality.py の件数の照合で落ちる（表示前に lint を当てる手順と食い違う） |
| I5-3 | 独立-5 | medium | no | self-inflicted | request-scope | re-reported | I2-10・I1-6・I3-4 の再掲（依頼より狭い 3 点を本人の確認なしに推奨で進めている） |
| I5-4 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 「名指しは変更要求ではない」の写し 5 か所が「名指しだけ」に限っていない |
| I5-5 | 独立-5 | low | no | self-inflicted | approval-path | accepted | 「OK。ところで X は？」が STEP 1 のどの行にも当たらず、gdd-dev.md の参照も「ほかの名指し」に限る |
| I5-6 | 独立-5 | low | no | self-inflicted | rule-conflict | accepted | 1 点の確認で名指しした点に条件が付くとき、決定済みの 1 行に残すか判断ポイントにするかが決まらない |
| I5-7 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | PR 本文の聞き返しの見込みに、ほかの文が付いた承認の件数が無い |
| I5-8 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | gdd-dev.md の行が縮んだ後の express の上限の余裕を測り直していない |
