---
type: patch
---

#### Summary

- requirements / design 段階で、failure scenario が無くても blocking のまま扱う指摘を、安全境界の全体から `reviewer-common.md` § 常時 High の 4 型だけに狭めた。ほかの安全境界の指摘は、破壊的操作・秘匿・不可逆のどれに当たり、何が壊れる・漏れるかを failure scenario に書く
- gate を実行する側が `blocking: yes` を advisory に下げてよい場合に、欄の値が advisory にすると決めた規則（置き場所は、正本の節、§ レビューループの契約、`subagent-dispatch.md` の blocking の条件、planning・security reviewer の定義）に反するときを足した。下げた指摘は、reviews.md の advisory に `（gate が下げた: <理由か規則の場所>）` を添える
- requirements-gating で `Human Check Questions` に移して blocking を解除する処置を、安全境界に当たる policy-level の指摘にも使えるようにした（下げることとは別の、人の回答で閉じる処置として書いた）。移した項目には元の指摘 ID と当たる接地条件を書く。安全境界に当たる項目を移した human check は、事前回答（判断の委任）があっても人に表示する（`human-check-template.md` § 事前回答 3 に足した）
- design-gating で blocking にしない例外を、承認済みの AC の文言への指摘の全体から、planning reviewer の `Open Predicate in AC` だけに狭めた。承認済みの AC へのほかの指摘は一般の規則で分け、blocking なら `human_recheck_required` で人に戻す。planning reviewer の表の design phase の行も、design-gating（human check の後）だけに当たるようにした
- reviewer が接地条件に当たるかで迷ったときの扱いを正本に書いた。AC の意味・スコープ・承認ポイントなら `blocking: no` にして迷った点を書き、安全境界なら `blocking: yes（安全境界）` にする。`reviewer-common.md` § Uncertainty Rule は正本を指す
- `reviewer-common.md` の `is_blocking` の「単独正本」の文を、requirements / design 段階を除く数え方として書いた
- 再入の差分スコープで、通過済みの節への新しい指摘を blocking にできるのは reviewer だけだと書いた
- design-gating の E2E Discovery Loop の自走中に policy-level の指摘が blocking で出たら、自走条件の外として扱う

#### Affected Files

- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/changelog.d/20261104-planning-blocking-rule.md`（同じ未リリースの断片の記述を、この変更に合わせた）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
