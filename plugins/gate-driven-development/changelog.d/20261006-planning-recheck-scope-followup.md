---
type: patch
---

#### Summary

planning reviewer の再入レビューの定義と読む範囲を、design-gating でも同じに効くように直した。再入は「前回 Round が `changes_requested` で、その blocking を処置してから起動する Round」とし、回数を問わない（design の Round 3 以降も含む。build から戻ったときの最初の Round は含めない）。読む範囲には、変えた節の AC ID を引く節（影響節）も入れる。design の再入の 1 枚にも、前回 Round の blocking の一覧を載せる。design-gating の処置（`design_detail_only`）でも、再入の前に反映するのは blocking だけにし、advisory は high・medium とも最後の Round の後に反映する。

`reviews.md` の Round の見出しに、所要時間とツール呼び出しの回数の欄を置いた。計れない経路では `不明` と書く。前の変更で入った、`tasklist.md` の Attempts への呼び出しの回数の記録と、agent 定義の読む範囲も、この版から効く。

#### Changed

- `references/requirements-gating-steps.md` § レビューループの契約 3: 再入の定義を原因で決め、読む範囲に影響節を入れた。`reviews.md` の形式に所要時間と呼び出しの回数の欄
- `references/subagent-dispatch.md` § Reviewer Input and Time Budget: 再入の 1 枚の中身を requirements・design 共通にした。計れないときは `不明`
- `agents/gdd-planning-reviewer.md`: 再入の定義・影響節・一覧が無いときは Round 1 と同じ範囲
- `skills/gdd-design-gating/SKILL.md` 手順 12・14: 再入の前の反映は blocking だけ

#### Affected Files

- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py --run`）
- Skill RED-GREEN Evidence: 再入の範囲の判断を問う短い場面を、変更前と変更後の reviewer 定義で比べた（PR 本文）
