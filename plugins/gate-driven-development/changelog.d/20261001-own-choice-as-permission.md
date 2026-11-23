---
type: minor
---

#### Summary

自走上限の `マージまで`・`マージ・デプロイ・QA まで` によるマージと QA の書き込みの許可を、利用者の例外の行（`~/.gdd/config.local.md` の `GDD Post-PR Autonomy Exception: on`）から、本人が human check でその値を選んだことに替えた。`マージまで` は repo の宣言が無くても選択肢に出す。`マージ・デプロイ・QA まで` は今までどおり repo の宣言が要る。

#### Changed

- `references/post-merge-qa.md` § 宣言: 利用者の例外の行を読まなくなった。`GDD Post-PR Autonomy:` の値は `merge-deploy-qa` だけにし、`マージまで` は宣言なしで選べる。`Post-PR Autonomy 判定:` の記録は `マージ・デプロイ・QA まで` のときだけ書く
- `references/post-merge-qa.md` 手順 1・2: `Merge Approval` を問わずにマージする条件と、QA の書き込みを runner に任せる条件を、本人の承認（`state.md` 全体で `Human Check Status` の行が 1 行だけで、値が `approved`、evidence が `human:<自走上限の値>` で、その値が `Approved Direction` の `自走上限` と完全に一致する）にした。形の揺れと、この版より前の承認は満たさず、1 問で問う
- `references/post-merge-qa.md` § 入口: 中断からの再開で、`マージまで` は `マージ前` の行から見る
- `references/post-merge-qa.md` § 限界: `human:` の evidence を main が本人のターン以外で書いても止める hook が無いこと、判断役の再承認で問う側に戻ること、利用者の規則を読まないこと、repo の側から自走のマージを止める宣言が無いことを書いた
- `references/human-check-template.md`・`references/human-check-template-compact.md`: `マージまで` をどの repo でも選択肢に出す。2 値はどちらも既定値・推奨値にせず（承認ポイントの「既定は広い側」も当てない）、ユーザーが選んだ・求めたときだけ値に置く。マージで起動する workflow と環境を判定できなければ `不明` と書く。共通の承認後処理と即再承認の記録に `evidence: human:<自走上限の値>` を足した
- `commands/gdd-dev.md` STEP 2: 本人の承認の記録を `Human Check Status=approved | evidence: human:<自走上限の値>` にした
- `references/gate-status-schema.md`: 本人のターンの承認の evidence を `human:<承認した自走上限の値>` にし、`approved` のまま書き直すときは元の evidence をそのまま写す。`skills/gdd-design-gating/SKILL.md`・`references/task-breakdown-steps.md`・`references/rollback-patterns.md` の書き直しのひな形を `<元の evidence>` にした
- `references/operation-levels.md` § Post-PR Autonomy: 上に合わせた

#### Affected Files

- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/gate-status-schema.md`
- `plugins/gate-driven-development/references/operation-levels.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`

#### User Action Required

- `~/.gdd/config.local.md` の `GDD Post-PR Autonomy Exception: on` の行は要らなくなった（あっても読まない。消してよい）。同じ版の前の変更が案内した、この行を足す手順は不要である
- repo の `.gdd-config.md` の `GDD Post-PR Autonomy: merge` も要らなくなった（あると宣言の形が違うものとして扱い、`マージ・デプロイ・QA まで` を出さない。`merge-deploy-qa` に書き換えるか消す）
- この版より前に `マージまで` などで承認した進行中の steering は、`human:` の evidence が無いので、マージの前に 1 問で問う
- 手順は利用者の規則（グローバルの CLAUDE.md・AGENTS.md）を読まない。自分の規則が 1 操作ごとの確認を求めていると、エージェントがそれに従って問うことや、auto mode classifier がマージを拒否することはある

#### Validation / Eval Impact

- `tests/test_merge_gate_hook_evidence_parsing.py`（`post-merge-qa.md` の `Merge Approval` のひな形を merge gate の parser に通す）
- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
