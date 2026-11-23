---
type: minor
---

#### Summary

人が先に答えた human check の回答（事前回答。例：「S-1〜S-3 は自走上限をマージまで、merge ごとの確認は不要、判断は Fable に相談、ゴール未達のときだけ人に戻して」）を正規の形にした。記録の書式、承認ポイントの判断を相談役に任せたときの記録先、任せても人に戻す条件、後続 Stage の着手の合図（「次に進んで」）を事前回答で代えるときの書式を、`references/human-check-template.md` § 事前回答 に置いた。あわせて、`human:` の evidence に事前回答の補足を付けると自走のマージ（`references/post-merge-qa.md` 手順 2 の完全一致）に入れなくなる点を、steering の書き込み hook の advisory で知らせるようにした。

#### Added

- `references/human-check-template.md` § 事前回答：`worklog.md` の `事前回答:` 行（対象・自走上限・委任先・人に戻す条件・本人の発話の原文。main が本人のターンで書く）、適用できるのは原文が会話の本人の発話にあり、各欄がその原文から読めると確かめた行だけであること（後続 Stage に写した行も同じ。確かめられなければ表示し、後続 Stage にも着手しない）、適用のたびの `事前回答の適用:` 行、承認の evidence は `human:<自走上限の値>` のまま補足を付けないこと、人に戻す条件（scope・AC・policy・ownership・security boundary・prompt-output contract の変更、自走上限の外、AC を弱めるなどの止まる案、AC の曖昧さ、Codex の subagent 委譲の判断点、適用中の本人の新しい入力、事前回答の対象外、相談役を起動できない、どれに当たるか判定できないなど）、後続 Stage の着手の手順（新しい steering への `事前回答:` 行の写し）
- `段階実装案` の `このOKで承認する範囲` に 4 つ目の値 `事前回答で後続PRも実施許可` を足した。事前回答の対象に入っている `follow-up-pr`・`post-merge-verification` の Stage だけで使い、独立した承認ポイントとして出す。`scripts/lint-hitl-stage-plan.py` はこの値を後続 Stage で受け、`current-pr` では拒む
- `scripts/lint-approved-direction.py` は、`Human Check Status` の `human:<値>` と `Approved Direction` の `自走上限` が一致しないとき、または `マージまで`・`マージ・デプロイ・QA まで` に補足が付いているときに WARN を出す。steering の書き込み hook の advisory で届き、書き込みは止めない。hook は書き込み前の state.md を lint するので、警告は次の state.md の書き込みで出て、直した直後の書き込みでももう 1 回出る。glob pattern が無い state.md でも、この WARN を出したときは exit 0 になる（WARN が無ければ今までどおり exit 2）。`gdd-systematic-debugging` Step 3c はこの WARN を route 判定に使わない

#### Changed

- `references/post-merge-qa.md`・`references/gate-status-schema.md`：事前回答を適用した承認も `human:<自走上限の値>` で本人の承認として扱うと明記した
- `references/autonomy.md`：事前回答は `GDD Autonomy: internal` とは別の仕組みで宣言が要らないこと、両方に当たる human check は事前回答で扱うことを書いた
- `references/state-machine.md`・`references/requirements-gating-steps.md`・`references/post-completion-pr-flow.md`・`references/task-breakdown-steps.md`・`skills/gdd-next-plan/SKILL.md`：`事前回答で後続PRも実施許可` の Stage は、事前回答が後続 Stage の着手の明示入力に当たるとした（Lane の書き方は § 事前回答 の 4 に置き、`Human Recheck=not required + 事前回答`）
- `commands/gdd-dev.md` #9、`references/subagent-dispatch.md` § HITL Pending Hard Invariant、Planning Interrupt Decision Menu（`human-check-template.md`・`requirements-gating-steps.md`）：事前回答がある human check は表示の代わりに § 事前回答 2 で扱う例外を足した。`commands/gdd-dev.md` 9.2 の括弧（下の 2 つの項目と同じ内容）は消した
- 後続 Stage を human check の OK だけで実装まで進める書き方を 2 つに絞った。事前回答の対象の Stage の `事前回答で後続PRも実施許可` と、`Continuation Mode=auto-after-clean`・`auto-stacked` を独立承認ポイントで選んだ Stage である。template の `このOKで後続も自走許可` という語（lint が受けない値だった）と、`follow-up-pr` を実施許可に昇格してよいとする一般の文は外した

#### Affected Files

- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/gate-status-schema.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/skills/gdd-next-plan/SKILL.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/scripts/lint-hitl-stage-plan.py`
- `plugins/gate-driven-development/scripts/lint-approved-direction.py`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`（references の行予算を 12076 から 12080 に上げた）
- `plugins/gate-driven-development/tests/test_pre_answer_contract.py`（新規）

#### User Action Required

- 事前回答で進めている steering の `Human Check Status` の evidence と `Approved Direction` の `自走上限` に補足（括弧の注記など）があると、自走のマージの条件を満たさず、マージは 1 問で問われる（止まる側）。自走でマージしたいときは、利用者本人が値だけに直し、補足を `worklog.md` の `事前回答:` 行（§ 事前回答 1 の形）に移す。エージェントは本人のターンの外で `human:` の evidence を書き換えない

#### Validation / Eval Impact

- 新規 contract test `tests/test_pre_answer_contract.py`：後続 Stage の承認範囲の値の受理と拒否、template の承認範囲の語彙と lint の集合の一致、手作りの記録（`human:マージまで（…事前回答…）`）で WARN が出ること・正規の記録では出ないこと・`autonomy:` の evidence は見ないこと、両方に同じ補足を写した記録で補足の WARN が出ること、lint が完全一致を求める値が template の自走上限の置換値にあること、steering の書き込み hook の入口から systemMessage に WARN が届くこと
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
