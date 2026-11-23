---
lane: L1
pr: 668
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f8c72da0deb130c19a8912a0db437d908849c7e0 | 0 | 11 | 1 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | d67e2e1e8a8f491ee3a7cee6ed82c47480508082 | 1 | 3 | 1 | 2026-11-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 4a3a7e40d7f41f602492421558ee51a818efb225 | 0 | 5 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | reply-routing | fixed | 設計: 変える（表を上の行から当てる順序）。blocking ごとに違う返事をすると、上の許す行（文面の採用）が先に当たり、差し戻した blocking を残したまま approved に進む。blocking ごとに当て、最も止める側に進むようにした。commit: d67e2e1e |
| I1-2 | 独立-1 | medium | no | self-inflicted | ai-close-verify | fixed | 依頼の原文から外れた（名指しの確かめ）。express・quick (standard) の implementation-gating は reviewer subagent をほぼ起動せず、1 枚に載せても誰も確かめない。必ず回る inline checklist の AC の項に置いた。commit: d67e2e1e |
| I1-3 | 独立-1 | medium | no | self-inflicted | ai-close-verify | fixed | 依頼の原文から外れた（写し間違いの照合）。照合の項目 0 は表示した文面と反映先の字句を突き合わせない。項目 0 に (d) を足した。commit: d67e2e1e |
| I1-4 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の原文から外れた（design-gating の範囲）。ユーザーが変えてよいとしたのは計測の締め直しだけで、正本は任された具体化も design-gating に当てていた。任された具体化を requirements-gating だけにした。commit: d67e2e1e |
| I1-5 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の原文から外れた（任された具体化の見分け方）。固定行の `具体化` には AI が自分で仮決定した行も入る。人が任せた行を `具体化（任された）` と書かせ、その行だけにした。commit: d67e2e1e |
| I1-6 | 独立-1 | medium | no | self-inflicted | ai-close-verify | fixed | 依頼が求めた名指しの確かめが届かない。reviewer の定義に `AI が閉じた計測:` の行の扱いが無い。2 つの reviewer 定義に足した。commit: d67e2e1e |
| I1-7 | 独立-1 | medium | no | self-inflicted | ai-close-verify | fixed | 依頼が求めた名指しの確かめが届かない。design-gating で閉じたとき次の gate が自分自身になる。次の gate を閉じた gate で決めるようにした。commit: d67e2e1e |
| I1-8 | 独立-1 | medium | no | self-inflicted | ai-close-scope | fixed | 依頼の範囲（上限に当たって残った指摘）に時間の目安が入るのに、Step 4b が「処置もせず人に見せる」のままで、AI が閉じる経路が動かない。Step 4b を直した。commit: d67e2e1e |
| I1-9 | 独立-1 | medium | no | self-inflicted | ai-close-scope | fixed | amendment の skill が上限の後の処置を断り、design-gating から呼ぶと requirements-gating に戻す。依頼の経路が動かないので、AI が閉じる処置と文面の採用をこの lane に入れた。commit: d67e2e1e |
| I1-10 | 独立-1 | medium | no | self-inflicted | measurement | fixed | 撤去の条件を数える記録が無い。文面の採用で進んだときに worklog に `表示した文面を採用:` の行を書くようにした。commit: d67e2e1e |
| I1-11 | 独立-1 | medium | no | self-inflicted | measurement | accepted | AI が閉じる型の件数は、接地条件の欄が過去の記録に無く数えられない。未測のまま入れることをユーザーが選んだ（2026-11-13 17:04、request.md）。読む時期と撤去の条件で後から測る |
| I1-12 | 独立-1 | low | no | self-inflicted | reply-routing | accepted | 名指しの無い「推奨で」も、推奨が文面つきの 1 案のときは復唱せずに名指しとして扱う。このままとすることをユーザーが選んだ（2026-11-13 17:04、request.md） |
| I1-13 | 独立-1 | low | no | self-inflicted | reply-routing | accepted | 「おすすめで」が 1 行目と案名の無い承認の行に分かれて載る |
| I1-14 | 独立-1 | low | no | self-inflicted | ai-close-scope | fixed | § レビューループの契約 1 と SKILL の 16 行目が、AI が閉じるものを除かずに「残る blocking を一括提示」のまま。依頼の経路が動かないので直した。commit: d67e2e1e |
| I1-15 | 独立-1 | low | no | self-inflicted | ai-close-scope | fixed | Step 8 で HITL を出さない例外が accept だけで、文面の採用の後に HITL を出し直す。依頼（再確認を挟まない）から外れるので直した。commit: d67e2e1e |
| I1-16 | 独立-1 | low | no | self-inflicted | ai-close-scope | fixed | design-gating の手順 11 が human_recheck の永続化を先に書き、例外を後に書く。順を入れ替えた。commit: d67e2e1e |
| I1-17 | 独立-1 | low | no | self-inflicted | measurement | accepted | Round に数えない照合の表のファイル名が決まらない |
| I1-18 | 独立-1 | low | no | self-inflicted | ai-close-scope | accepted | 全部を AI が閉じた上限到達では `上限到達:` の行が残らず、2 回目の上限で人に戻す規定が効かない |
| I1-19 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 返事の分け方の順序が PR 本文の挙動の変化に無い。commit: なし（PR 本文） |
| I1-20 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文が、採った文面の誤りも次の gate に名指しで渡すと書くが、差分は AI が閉じた AC だけを名指ししていた。I1-10 の行も名指しの対象にした。commit: d67e2e1e |
| I1-21 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の原文から外れた（「確かめ方を厳しくするだけ」）。計測に「確かめる対象を足す」を含め、AC の意味を実質的に広げうる。足す対象を AC の本文が述べる挙動に限り、本文の語の引用を求めた。commit: d67e2e1e |
| I2-1 | 独立-2 | high | yes | self-inflicted | ai-close-verify | fixed | 設計: 変える（照合は止めない・unavailable でも進む、という Step 4a の既定を、写し間違いの唯一の止めにも継いだこと）。文面の採用は、照合が返らない・引用が無いときも承認に進んだ。採用と AI が閉じる経路の両方で、照合の ok を進む条件にし、それ以外は人に見せる側に倒した。commit: 4a3a7e40 |
| I2-2 | 独立-2 | medium | no | self-inflicted | ai-close-verify | fixed | 依頼の原文から外れた（表示した文面と突き合わせる）。照合が比べる元が処置の引用で、表示した文面そのものではなかった。返答とともに request.md に引用した表示の文面を照合に渡して比べるようにした。commit: 4a3a7e40 |
| I2-3 | 独立-2 | medium | no | self-inflicted | ai-close-verify | fixed | 依頼が求めた名指しの確かめが届かない。Judgment Change: no の task では inline checklist が回らない。名指しの AC を実装する task は yes にした。commit: 4a3a7e40 |
| I2-4 | 独立-2 | medium | no | self-inflicted | ai-close-verify | fixed | 依頼が求めた名指しの確かめが届かない。implementation-gating で計測のテストが落ちなくても gate が止まらない。High の finding にして差し戻すようにした。commit: 4a3a7e40 |
| I2-5 | 独立-2 | low | no | self-inflicted | ai-close-verify | accepted | inline checklist の退行注入に、戻す手順（TDD の変異の手順）への指し先が無い |
| I2-6 | 独立-2 | low | no | self-inflicted | reply-routing | fixed | 返事が分かれたとき、採用した文面の反映に記録と照合が含まれるか決まっていない。I2-1 で、承認に進む条件を採用した blocking ごとの照合の ok にしたので閉じた。commit: 4a3a7e40 |
| I2-7 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 固定行の形の正本（human-check-template.md）に `具体化（任された）` の書き方が無い。印が読めなければ人に出る側に倒れる |
| I2-8 | 独立-2 | low | no | self-inflicted | ai-close-scope | accepted | Step 4b の「新しい起動もせず」と、閉じ方の照合の起動が食い違う |
| I2-9 | 独立-2 | low | no | self-inflicted | ai-close-scope | accepted | amendment の lane の説明（pre-HITL の再入）と、design-gating から呼ぶ規定が食い違う |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | requirements-gating の SKILL の手順 6 から、閉じる節への指し先が消えた（express の予算で詰めた） |
| I2-11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 1 枚の行名 `AI が閉じた計測:` が採った AC にも使われ、AC でない文面は名指しされない。PR 本文は「採った文面が AC なら」に直す |
| I2-12 | 独立-2 | low | no | self-inflicted | ai-close-verify | accepted | implementation-gating の名指しの確かめに、対象の task と済みの記録が無い |
| I2-13 | 独立-2 | low | no | self-inflicted | ai-close-scope | accepted | design-gating の手順 11 と閉じ方の最後の行で、残りの出し方（human_recheck と一括提示）が違う |
| I2-14 | 独立-2 | advisory | no | self-inflicted | request-scope | accepted | 進行中の steering には印が無く、任された具体化の経路が当たらない（人に出る側に倒れる） |
| I3-1 | 独立-3 | medium | no | self-inflicted | ai-close-verify | accepted | 照合の出力は項目ごとに主な ok だけでよく、blocking ごとの (d) の ok を保証しない。行が無い blocking は待つ行になり、進める場面で人に戻る（止める側に倒れる） |
| I3-2 | 独立-3 | medium | no | self-inflicted | ai-close-verify | accepted | (d) が最新 Round の処置すべてに当たり、同じ Round で AI が閉じた処置にも引用無しの ng を出す。採用の経路が待つ行になる（止める側に倒れる） |
| I3-3 | 独立-3 | medium | no | self-inflicted | ai-close-verify | accepted | 照合の ng を直した後に、照合を回し直して進むのか待つのかが段落の中で 2 通りに読める |
| I3-4 | 独立-3 | medium | no | self-inflicted | ai-close-verify | accepted | 名指しの AC の task を yes にする規定が task-breakdown の宣言 1 か所だけに頼り、implementation-gating Step 1e と completion-reviewer の観点 11 に受け皿が無い |
| I3-5 | 独立-3 | medium | no | self-inflicted | ai-close-verify | accepted | express・quick では、足した High の finding が差し戻しではなく standard への昇格になる |
| I3-6 | 独立-3 | low | no | self-inflicted | ai-close-scope | accepted | Step 4b の除外が処置にだけ掛かり、時間超過のときに照合を起動できない字面になる（止める側に倒れる） |
| I3-7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Affected Files に references/task-breakdown-steps.md が無い |
| I3-8 | 独立-3 | low | no | self-inflicted | ai-close-verify | accepted | High の finding の括弧「AC の意味」が implementation 段階の category の値ではない |
| I3-9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | brainstorming-steps.md 9 の (1) の「だけを引用」に、一括提示で採用した文面が入っていない |
| I3-10 | 独立-3 | low | no | self-inflicted | ai-close-verify | accepted | (d) が比べるのは、どちらも main が返答の後に書いた引用どうしで、表示から request.md への写しの誤りは拾えない |
| I3-11 | 独立-3 | low | no | self-inflicted | reply-routing | accepted | 照合が起動できず待つ行に倒した後の出口が書かれていない |
| I3-12 | 独立-3 | low | no | self-inflicted | ai-close-verify | accepted | AI が閉じる経路で照合が通らなかったとき、書き換え済みの計測と処置の扱いが書かれていない |
| I3-13 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | Skill RED-GREEN Evidence が照合の ok を進む条件にした後の規則に追随しているかは、reviewer からは未確認 |
