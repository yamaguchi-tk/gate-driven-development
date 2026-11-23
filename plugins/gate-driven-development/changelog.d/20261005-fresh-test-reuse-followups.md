---
type: patch
---

#### Summary

同じ起動の中のテストの結果を使ってよい条件（`references/verification-before-completion.md` § Fresh の粒度）を、次のように締めた。

- 使ってよいのは、テストを回した worktree（`<wt>`）についての主張だけ
- テストを始める直前の確認は、テストと同じ Bash 呼び出しの中で、テストより前に出す。出していなければ回し直す
- `.steering/<task>/` の requirements.md・design.md は、2 回の確認で `shasum` を比べる。テストが `.steering/` を読むかは、テストのコードを grep して確かめる。確かめていなければ回し直す

同じ規定を書いていた箇所（同じ reference の Iron Law・Common Failures の表、`gdd-completion-check` の RUN と Fresh Verification、`gdd-ac-verification` の Guardrails）を、この条件に揃えた。

#### Affected Files

- `plugins/gate-driven-development/references/verification-before-completion.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-ac-verification/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- Skill RED-GREEN Evidence（gate runner・worker・main の場面を、変更前と変更後の規定で比べた）
- `bash tests/validate-plugin.sh`
