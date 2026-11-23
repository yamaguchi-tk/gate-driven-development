---
type: patch
---

#### Summary

planning reviewer の再入レビューで読む範囲から、影響節（変えた節の AC を引くほかの節）を外した。再入で読むのは、前回 Round の blocking ごとの処置箇所、変えた節、それらが名指しする実コードだけになる。gate が AC ID で grep して影響節を `参照:` 行で並べる手順も無くした。変えた節が引く AC を参照するほかの節への波及は、再入では見ない（限界）。範囲を広げる変更は、同じ入力で呼び出しの回数・時間・判定・advisory を比べてから入れる。

再入の定義（同じ gate・同じエピソードで、前回 Round が `changes_requested` で、その blocking を処置してから起動する Round）は変えない。

#### Changed

- `references/requirements-gating-steps.md` § レビューループの契約 3: 差分スコープと再入で読む範囲から影響節を外し、波及を見ないことを限界として書いた
- `references/subagent-dispatch.md` § Reviewer Input and Time Budget: 再入の 1 枚から影響節の `参照:` 行を外した
- `agents/gdd-planning-reviewer.md`: 再入で読む範囲から影響節を外した

#### Affected Files

- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`

#### User Action Required

- 動いているセッションは、開き直した後から新しい reviewer の定義で動く（agent 定義はセッションの開始時にだけ読み込まれる）

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py --run`）
