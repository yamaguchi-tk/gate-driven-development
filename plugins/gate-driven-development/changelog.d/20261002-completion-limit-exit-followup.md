---
type: patch
---

#### Summary

`gdd-completion-check` の Round 上限超過で示す方式転換の 4 つ目「限界として開示して人に渡す」が、実際に出口として働くようにした。これまでは、この案を選んだ人の返答が通常の承認として処理され、`Human Check Status=approved` になって元のループに戻りえた。あわせて、案を置ける条件と、選ばれた後の扱いの抜けを埋めた。

#### Fixed

- `commands/gdd-dev.md` #10 STEP 1 に、Round 上限のメニューへの返答のうち、4 つ目を選ぶものと案を名指ししないもの（「OK」「おすすめで」など）の分類を足した。STEP 2 と共通の承認後処理に通さない。案を名指ししない返答には、おすすめの案を名前で復唱して確かめ、1〜3 つ目なら名指しの返答を待つ。4 つ目を選んだ後に届く承認に見える返答には、マージ後に cancelled にする案内を繰り返す。メニューの返答例には案の名前を入れる
- 各案に書く見込みを 2 点にした。completion-check を差し戻し無しで通れるか（`Completion Rounds` は戻らない）と、その後の pre-PR gate の条件（`Pre-PR Self Review` の dry、`Independent Review` の high 0・blocking 0）を満たせるか
- 案を置ける条件を、残る high・blocking が 1 件以上あり、すべてが人の承認の記録（承認時点の `requirements.md` § Honest Limitations、Correction Log、human check への人の返答）を持つときに絞った。`adr.md` や ADR の記載は、これらの出典を併記したものだけを数える。メニューに限界ごとの承認の出典を書く
- 選ばれた後の扱いを足した。草案は `handoff/completion_check.md` の末尾に決まった見出しで追記する。草案の先頭の節は「直していない high・実害クラス」にする。草案と差分に秘密情報の確認をかける。走っていない pre-PR gate の検査と、steering の終え方（マージ後に cancelled にする）を草案に書く。`GDD_SKIP_PRE_PUSH_GATE=1` も使わず案内しない
- `references/gate-checklists.md` の Round 上限の手順に残っていた「方式転換 3 択」を、`references/rollback-patterns.md` への参照に替えた

#### Affected Files

- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/gate-checklists.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`

#### User Action Required

- 4 つ目の案を選んだら、`git push`・`gh pr create`・PR 後のレビュー対応の push を自分の端末で行う。PR のマージ後に、その steering を `references/self-review-lanes.md` § 使わないステアリングの終え方 で cancelled にする

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
