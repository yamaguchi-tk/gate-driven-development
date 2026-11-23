---
type: patch
---

#### Summary

- requirements-gating と design-gating の blocking の決め方を、`references/requirements-gating-steps.md` § 精度の第一原則 の 1 か所にまとめた。blocking にするのは、接地条件（AC の意味・スコープ・承認ポイント・安全境界）に当たり、failure scenario を付けられる指摘だけにする。severity・category・reviewer の観点では決めない
- `gdd-security-reviewer` の指摘も、requirements / design 段階ではほかの reviewer と同じ規則で分ける。これまでは「security reviewer の指摘は blocking のまま扱う」の規定で、Low の指摘まで blocking にされることがあった。failure scenario が無くても blocking のまま扱うのは、`reviewer-common.md` § 常時 High の 4 型に当たる指摘だけにする
- requirements / design 段階の reviewer は、指摘ごとに `blocking: yes（<当たる接地条件>）` か `blocking: no` を書く。gate を実行する側は advisory を blocking に上げない。`blocking: yes` を advisory に下げてよいのは、再現できないときと、欄の値が正本に挙げた置き場所の、advisory にすると決めた規則に反するときだけで、指摘ごとに理由を `reviews.md` に書き、常時 High の 4 型は下げない。requirements-gating では、policy-level の指摘（安全境界を含む）を `Human Check Questions` に移して解除してよい。design-gating では移さず、`human_recheck_required` で人に戻す。欄が無い指摘は自分で分ける。reviewer に渡す 1 枚の blocking の定義にも、この節を写す
- `reviewer-common.md` の `is_blocking`（実害クラス）と category 未付与の既定は、requirements / design 段階を除く数え方だと明記した。implementation 段階の blocking の決め方は変えていない
- design-gating の「high・medium のうち」の条件を外した（severity では決めない）
- design-gating（human check の後）では、planning reviewer の `Open Predicate in AC`（承認済みの AC の開いた述語）は blocking にしない（安全境界に当たるものを除く）。今まで Low の severity で design gate を止めないようにしていたものを、規則で書いた
- `reviewer-common.md` § Uncertainty Rule の「迷ったら blocking」は、requirements / design 段階では、AC の意味・スコープ・承認ポイントに当たるかで迷う指摘に当てない。安全境界に当たるかで迷う指摘には今までどおり当てる
- `references/phase-progression.md` の design-gating の行も、正本を指すだけにした

#### Affected Files

- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/reviewer-common.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-requirements-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-security-reviewer.md`
- `plugins/gate-driven-development/references/phase-progression.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
