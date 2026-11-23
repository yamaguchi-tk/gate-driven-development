---
lane: L1
pr: 288
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4123ad8b38e810580f42550509bd350502f9e33a | 0 | 2 | 1 | 2026-10-02T10:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 6eaee75457c71cdad9d7d882d52e1e0b15036910 | 0 | 3 | 2 | 2026-10-02T11:20+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 188c6a475b93c5f67bf72ecf4b06f92556c29bdc | 0 | 1 | 1 | 2026-10-02T11:25+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 5da517d1 | 0 | 1 | 0 | 2026-10-02T12:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | entry-pointer | fixed | § 事前回答 2 の「表示せずに進む」に対応する例外が、入口（gdd-dev 旧#9・HITL Pending Hard Invariant・Planning Interrupt Decision Menu）に無かった。旧#9・subagent-dispatch・メニューの 2 写しに足した（gdd-using-skills・gdd-requirements-gating は runtime profile の予算のため足さず、メニューの正本を指す既存の文で届く） commit: 6eaee754 |
| F2 | 独立-1 | medium | no | self-inflicted | return-conditions | fixed | 人に戻す条件の列挙から、AC の曖昧さ・Codex の subagent 委譲の判断点・本人の割り込みが落ち、委任先 なし で委譲を AI が承認しうる。閉じた一覧にして 3 つを足した commit: 6eaee754 |
| F3 | 独立-1 | low | no | self-inflicted | lint-timing | fixed | hook は書き込み前の state.md を lint するので WARN が 1 回遅れて届くことが書かれていない。§ 事前回答 2 と断片に書いた（hook は block gate なので配線は変えない） commit: 6eaee754 |
| F4 | 独立-1 | low | no | self-inflicted | test-power | fixed | 補足を検出するループを消してもテストが通る。両方に同じ補足を写した記録のテストを足した（ループを無効にすると 2 件落ちることを確認） commit: 6eaee754 |
| F5 | 独立-1 | low | no | self-inflicted | lint-output-contract | fixed | 新しい WARN と exit code の変化が、Step 3c と rollback-patterns の出力の読み方に入っていない。route 判定に使わないと書き、docstring の exit code を直した commit: 6eaee754 |
| F6 | 独立-1 | low | no | self-inflicted | approval-vocabulary | fixed | 規則 18 の例外と 3 値の定義が、auto-after-clean・auto-stacked の Stage を外していた。例外に戻し、方針のみ承認 の着手条件に Stage Continuation を書き、断片に外した語を書いた commit: 6eaee754 |
| F7 | 独立-1 | low | no | self-inflicted | approval-vocabulary | fixed | tasklist の Approval Scope・Lane の Human Recheck に新しい値の書き方が無い。task-breakdown-steps と § 事前回答 4 に足した（compact は runtime profile の予算のため足さない） commit: 6eaee754 |
| F8 | 独立-1 | low | no | self-inflicted | post-merge-stop | fixed | post-completion-pr-flow の後続 Stage を開始しない規定と post-merge-qa の対象の文に、事前回答の例外が無い。足した commit: 6eaee754 |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `### 次の計画` を求める hook の指し先が、手動マージのときだけ動く post_merge_continuation.py だった。gdd_stop_hook.py の done の検査を足した commit: 6eaee754 |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | § 事前回答 2 の承認に #10 STEP 2（Route In Progress のクリアと Resume From の更新）への指し先が無い。足した commit: 6eaee754 |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋に、委任先 なし の経路・lint の exit code・外した語が無い。PR 本文に足した commit: なし（PR 本文） |
| F12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 限界の節の lint の見る範囲が実装と違い、フェンス内・2 行以上・全角コロンを WARN しない。PR 本文の限界を実装に合わせた |
| F13 | 独立-1 | low | no | inherited | lint-noise | next-pr | 正本の見出しの形の state.md では glob pattern が 0 件になり、毎回 INFO と usage で advisory の雑音が出て、新しい WARN が埋もれる |
| F14 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 行予算のコメントの「PR でユーザーの承認を求める」は、承認・却下の後に古くなる。承認されたら書き換える |
| F15 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の User Action Required が、誰が evidence を直すかを書かず、エージェントが本人のターンの外で human: を書き換えうる。利用者本人が行うと書いた commit: 6eaee754 |
| F16 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence の有無を抜粋からは確かめられない（PR 本文に載せる） |
| G1 | 独立-2 | medium | no | self-inflicted | pre-answer-provenance | fixed | 事前回答の行の出どころ（本人の発話か）を確かめずに HITL の表示を飛ばせ、peer turn の検査はこの行を見ない。行に原文を書かせ、原文を会話の本人の発話と突き合わせた行とその写しだけを適用し、確かめられなければ表示するようにした（hook 側の対策は判定のコードの変更なので入れない） commit: 188c6a47 |
| G2 | 独立-2 | medium | no | self-inflicted | return-conditions | fixed | 人に戻す条件の閉じた一覧が、どれに当たるか判定できないときに進む。判定できないときも止まる項目を足し、閉じた一覧の文を列挙の最後に移した commit: 188c6a47 |
| G3 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 変更断片が、tip に無い変更（requirements-template・compact・旧#10・2 つの skill）を書いていた。断片は差分と合わせる必要があるので、blocking の修正で断片を書き直すのに合わせて影響ファイルと記述を差分に合わせた commit: 188c6a47 |
| G4 | 独立-2 | medium | no | self-inflicted | lint-delivery | next-pr | WARN は systemMessage で利用者の端末にだけ出て、モデルには届かない。§ 事前回答 2 と断片に受け手が書かれていない |
| G5 | 独立-2 | medium | no | self-inflicted | post-merge-stop | next-pr | phase-progression.md:503 の「Stage Continuation を除き後続 Stage を開始しない」に事前回答の例外が無い |
| G6 | 独立-2 | medium | no | self-inflicted | entry-pointer | next-pr | Planning Interrupt Decision Menu の項目 3 の例外と、項目 1（自走上限が変わるなら HITL を再生成）・締めの文のどちらが優先するか書かれていない |
| G7 | 独立-2 | low | no | self-inflicted | entry-pointer | next-pr | gdd-dev.md #9 の事前回答の文が述語を欠き、GDD Autonomy の条件の箇条の中にあるので、宣言の下にあるように読める |
| G8 | 独立-2 | low | no | self-inflicted | lint-output-contract | next-pr | glob の無い state.md で human-evidence の WARN の有無により exit 2 と 0 が入れ替わる。rollback-patterns と docstring の説明が補足の WARN を書いていない |
| G9 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | Codex の委譲を「本人の明示の依頼でだけ開く」と書いたが、codex.md の明示委譲ソースは project policy と /gdd-dev 引数も含む |
| G10 | 独立-2 | low | no | self-inflicted | approval-vocabulary | next-pr | gdd-requirements-gating/SKILL.md:146 と template:153 に、後続 Stage を実装まで進める一般の文が残り、事前回答の対象に限る条件が無い |
| G11 | 独立-2 | low | no | self-inflicted | entry-pointer | next-pr | subagent-dispatch.md:128 の Post-Return Routing が無条件の表示を指示し、例外は :132 にしかない |
| G12 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | § 事前回答 4 の方針のみ承認の着手の経路が 2 つで、state-machine.md:158 の 3 経路（Manual Merge Continuation 後の新 steering seed）と合わない |
| H1 | 独立-3 | medium | yes | self-inflicted | pre-answer-provenance | fixed | 写しの例外（写し元の行と照合した写しを適用する）があり、§ 4 の着手と写しに元の行を確かめる手順が無いので、確かめていない行が写しを通じて後続 Stage の human check を飛ばし自走のマージに入る。写しの例外を外し、写しも原文と各欄を確かめた行だけを適用し、着手の前にも元の行を確かめて確かめられなければ着手しないようにした commit: 5da517d1 |
| H2 | 独立-3 | low | no | self-inflicted | pre-answer-provenance | fixed | 写し元は cleanup で消え、絶対パスは書き込み hook が拒むので、写し元との照合は標準の流れで行えない。H1 の修正で写し元を読む必要がなくなった commit: 5da517d1 |
| H3 | 独立-3 | low | no | self-inflicted | pre-answer-provenance | fixed | 確かめが原文の有無だけで、行の各欄が原文から読めるかを見ない。H1 の修正文に各欄が原文から読めることを入れた commit: 5da517d1 |
| H4 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 人に戻す条件の一覧の由来の断定（autonomy.md から 2 つを除いたもの）が、事前回答に固有の条件を含む一覧の実態と合わない |
| H5 | 独立-3 | low | no | self-inflicted | bookkeeping | next-pr | 原文を確かめられず表示するときの worklog.md の記録と、本人への説明（言い直せば記録し直す）が決まっていない |
| H6 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | post-merge-qa.md:34 が事前回答の適用を「事前回答: の行がある」と書いたまま |
| H7 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 断片の User Action Required が、利用者が事前回答: 行に補足を移せば効くと読める（原文が今の会話に無いので § 2 の確認を通らない） |
| H8 | 独立-3 | low | no | inherited | doc-claim | next-pr | gdd-next-plan/SKILL.md:28 が人に戻す条件を § 事前回答 4 と指すが、条件は 3 にある |
| H9 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 断片の「gdd-dev.md 9.2 の括弧を消した」は利用者から見える変更ではない |
| H10 | 独立-3 | low | no | inherited | doc-claim | next-pr | gdd-requirements-gating/SKILL.md:45 に事前回答の例外が無く、計画中の事前回答で表示して止まる（止まる側） |
| H11 | 独立-3 | low | no | inherited | doc-claim | next-pr | gdd-using-skills/SKILL.md:88 の follow-up の振り分けに事前回答を記録する経路が無い（止まる側） |
| H12 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | compaction の後や別セッションで human check を表示する挙動が、PR 本文の限界の節に無い。限界の節に足した |
| I1 | 独立-4 | medium | no | self-inflicted | approval-vocabulary | next-pr | post-completion-pr-flow.md:307 が後続 Stage に「待たずに着手し、止まらない」と無条件に書き、§ 事前回答 4 の元の行を確かめてから着手する条件と食い違う（新しい steering の human check は § 2 が受けるので承認は閉じたまま） |
| I2 | 独立-4 | medium | no | self-inflicted | doc-claim | fixed | compaction の後の扱いが、規則（発話が見えないとき）と PR 本文の限界（無条件）で食い違う。PR 本文の限界を「本人の発話が見えないときは」に合わせた commit: なし（PR 本文） |
| I3 | 独立-4 | low | no | self-inflicted | approval-vocabulary | next-pr | gdd-next-plan/SKILL.md:28 が確かめの条件なしに「待たずに着手し」と書く |
| I4 | 独立-4 | low | no | self-inflicted | approval-vocabulary | next-pr | state-machine.md:158 が、確かめたかを問わず事前回答を着手の明示入力に数える |
| I5 | 独立-4 | low | no | self-inflicted | pre-answer-provenance | next-pr | 原文が触れていない欄（委任先・人に戻す条件）が「原文から読める」かが決まっておらず、確かめられないときの列挙に「欄が原文から読めない」が無い |
| I6 | 独立-4 | low | no | self-inflicted | bookkeeping | next-pr | § 4 の「確かめられずに着手しない」経路で worklog.md に記録が残らない |
| I7 | 独立-4 | advisory | no | inherited | doc-claim | accepted | post-merge-qa.md:34 の括弧が、事前回答の適用を行があるかどうかで言い表している（H6 と同じ箇所） |
| I8 | 独立-4 | advisory | no | self-inflicted | product | accepted | GDD Autonomy: internal の repo で、確かめられない事前回答の行があると autonomy.md の判定を通らずに表示に倒れる（止まる側）。意図した側が書かれていない |
