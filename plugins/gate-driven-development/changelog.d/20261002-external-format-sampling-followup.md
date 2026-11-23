---
type: patch
---

#### Summary

外部形式の実測（brainstorming § 8a）と規則の実値検算（design-gating Step 5d）の書き方を直した。テストで使う fixture はテストの fixture 置き場に置く。5d の「未測」で抜けられるのは、fixture も実データも無いときだけになる。planning reviewer が 5d の記録の有無を Design phase で見る。

#### Changed

- `references/brainstorming-steps.md` § 8a
  - テストで使う fixture は、テストの fixture 置き場に置く（`.steering/` は PR に入らず、steering write guard が 12 桁の数字などを deny して値の形を崩させるため）
  - secret の名前・置き場所は値を返さない操作（`describe-secret` など）で得て、値のキー構造が要るときはマスク済みの sample をユーザーに求める
  - 記録先の欄名は、express の雛形では `外部依存`
- `skills/gdd-design-gating/SKILL.md` Step 5d: 「未測」と書けるのは、fixture も実データも無いとき（「どちらのデータも無ければ」）。fixture で値の形が足りないときに当てる実データは「§ 8a と同じ扱い」（worktree の外・値を書かない）
- `agents/gdd-planning-reviewer.md` Design phase: 外部の形式から値を取る規則が design.md にあるのに Step 5d の記録が無ければ Medium として報告する
- `skills/gdd-test-driven-development/SKILL.md`: § 8a の fixture は、テストの fixture 置き場に置いて使う。Contract Surface Coverage の external API response variants も、§ 8a の fixture を元にする
- `references/requirements-gating-steps.md` § Spec Self-Review Checklist: 外部形式の範囲に Webhook と「など」を足し、§ 8a の判定とそろえた
- `skills/gdd-brainstorming/SKILL.md` の 8a: 文を短くした（内容は変えていない）

#### Affected Files

- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `validate-plugin.sh`（`external-format-sampling-tokens`・`skill-body-budget` を含む）と、変更したファイルを参照する `tests/test_*.py`
