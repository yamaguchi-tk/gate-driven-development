---
type: minor
---

#### Summary

`gdd-completion-check` の Round 上限を超えたときに示す方式転換に、4 つ目の案「限界として開示して人に渡す」を足した。これまでの 3 案（task 撤回 / 再設計 / スコープ縮小）は、どれを選んでも pre-PR gate の受理述語（`Independent Review` の high 0 かつ blocking 0）を満たせるとは限らなかった。人が限界を受け入れても、その後の巡で PR を作れず、同じ種類の確認に何度も戻ることがあった。各案には、選んだ後にこの述語を満たせる見込みがあるかを書く。

#### Added

- 方式転換の 4 つ目の案「限界として開示して人に渡す」。残る high・blocking がすべて、人が承認した限界（`requirements.md` の Correction Log、`adr.md`、PR に入る ADR）に当たるときだけ選択肢に置く。選ばれたら、`Independent Review` 行は実際の件数のまま残す。PR 本文の草案（先頭に「直していない常時 High・実害クラス」の節）を `handoff/completion_check.md` に書く。push と PR 作成は人が自分の端末で行うよう案内して止まる

#### Changed

- 方式転換の各案に、選んだ後に pre-PR gate の受理述語を満たせる見込みを書く
- `references/autonomy.md` の止まる案「Round 上限で残った blocking を accept as known risk にする」に、この 4 つ目の案が入ることを明記した。自律モードでも、この案は自動では選ばない

#### Affected Files

- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/references/autonomy.md`

#### User Action Required

- なし。4 つ目の案を選んだ steering では、PR 後の followup と post-merge QA を GDD で行わない（agent の再 push にも pre-push gate が同じ述語を要求するため）。PR 作成後のレビュー対応は、人が push する

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- 判定のコード（gate の受理述語、`references/independent-review.md` の計上規則、`Next Action` の許容値）は変えていない
