---
type: patch
---

#### Summary

- 上限で止まる提示の選択肢を広げた。前は Round 上限の一括提示が accept as known risk / 修正 / 差し戻しの 3 つに決まっていて、原因を変える案が並ばなかった。今は、残った指摘と依頼の未達を生んだ設計の決定・前提を名指しして変える案を加え、すべての選択肢を、依頼を満たすか・原因が消えるかで比べる。推奨は依頼を満たし原因を消す案を優先する。変える案が無いときは、無い理由を書く
- 元の 3 つは残すので、これまでの案は名指しで選べる
- ほかの上限（修正の回数など）で止まるときも同じにする。方式転換の選択肢では案の数を増やさず、再設計の案で同じ決定・前提を名指しする
- 一括提示への返答の扱いを、`references/requirements-gating-steps.md` § 一括提示への返答 の 1 か所にまとめた。一括提示は承認の確認ではないので、案名の無い「OK」は承認にせず、推奨の案を名前で復唱して確かめる
- 一括提示で修正や原因の決定を変える案を選ぶと、AC・依頼の読み方・前提・範囲を変えるものと迷うものは `gdd-brainstorming` に戻す。それ以外は変更を反映し、止まった gate をもう一度回す（前は修正を直して再提示していた）
- 委任で採った案も同じ表で進む。時間超過の一括提示も同じ表で受ける。委任中は「レビュー無しで承認」を相談役が選べず、人に戻す

#### Affected Files

- `references/requirements-gating-steps.md`
- `references/human-check-template.md`
- `agents/gdd-formal-gate-runner.md`
- `agents/gdd-light-task-runner.md`
- `references/subagent-dispatch.md`
- `references/rollback-patterns.md`
- `references/state-machine.md`
- `commands/gdd-dev.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh` と、変更したファイルの名前を参照するテスト
- 判定を変えるコードは無いので、eval の更新は無い
