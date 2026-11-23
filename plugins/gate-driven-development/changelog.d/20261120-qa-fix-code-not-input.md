---
type: patch
---

#### Summary

- `references/common-guardrails.md` § 選ぶときの基準 に 8 を足した。人が手で入れる値の形（secret の登録の形・フォームの入力など）とコードの読み方が食い違うときは、人が普通の手順（管理画面の既定など）で作る形をコードが読む案を推し、人に入れ直させる案は推さない。その直しは利用者の規則が禁じるフォールバックに当たらない。コードを直せないとき（読み方を repo の外が決めている、ほかの読み手が今の形で読んでいるなど）は、入れ直しを推してよい。main も相談役も当てる
- マージ後の QA が fail で、原因がこの食い違いのとき、報告の推奨はこの基準に従う

#### Affected Files

- `references/common-guardrails.md`・`references/post-merge-qa.md`・`agents/gdd-opus-advisor.md`・`agents/gdd-opus-advisor-max.md`・`agents/gdd-fable-advisor.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
