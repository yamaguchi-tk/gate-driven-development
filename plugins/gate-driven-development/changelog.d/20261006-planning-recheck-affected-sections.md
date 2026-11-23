---
type: patch
---

#### Summary

planning reviewer の再入レビューで読む影響節を、AC を単位にして gate が列挙するようにした。影響節は、前回 Round から本文を変えた AC と、変えた節の中で変えた行（引用を足した・外した行を含む）が引く AC の ID を引く節である。受入条件の節を 1 行直しても、ほかの AC を引く節は入らない。節の中身だけを直して引用を変えないときも、直した行が引く AC を引くほかの節は入る。gate は `requirements.md`・`design.md` をその AC ID で grep し、当たった節を再入の 1 枚に `参照:` 行で並べる。reviewer はその `参照:` 行の節を読む。

再入の定義に「同じ gate・同じエピソード（直近の human check より後）」を戻し、human check をまたいだ Round は、見出しの番号を数え直したかを問わず再入に含めない。reviewer の定義にも同じ除外を書き、観点レーンを順に当てるのは「再入でない Round」とした。

#### Changed

- `references/requirements-gating-steps.md` § レビューループの契約 3: 影響節の定義（AC 単位）と、gate による列挙。再入の定義に同じ gate・同じエピソード
- `references/subagent-dispatch.md` § Reviewer Input and Time Budget: 再入の 1 枚に影響節の `参照:` 行
- `agents/gdd-planning-reviewer.md`: 再入の定義の除外、影響節は `参照:` 行の節、観点レーンは再入でない Round に当てる

#### Affected Files

- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`

#### User Action Required

- 動いているセッションは、開き直した後から新しい reviewer の定義で動く（agent 定義はセッションの開始時にだけ読み込まれる）

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py --run`）
- Skill RED-GREEN Evidence: 受入条件の 1 行を直した再入の場面を、変更前と変更後の reviewer 定義で比べた（PR 本文）
