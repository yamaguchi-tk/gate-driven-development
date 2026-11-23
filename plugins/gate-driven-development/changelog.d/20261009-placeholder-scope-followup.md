---
type: patch
---

#### Summary

プレースホルダー禁止（`references/common-guardrails.md`）の対象外を、scan の手順からも読めるようにした。対象外は、語に触れるだけの記録（`Stub grep: TODO なし` など）と、コード例（`TODO` を検出する正規表現・テストの入力など）と、`#### Attempts` で、tasklist の `Actual code` に書く実装の `// TODO` だけは対象になる。task-breakdown の Plan Placeholder Failure Gate・Task Self-Review 6・SKILL.md の Plan Self-Review Contract 2 は、この正本を指す。あわせて、プレースホルダーを見るのが task-breakdown の Self-Review（tasklist の Steps）と brainstorming の Self-Review（`requirements.md`・`design.md`）だけであることと、省略記法禁止の除外に `reviews.md` だけへの書き込みがあること（hook の既存の挙動）を書いた。

#### Affected Files

- `plugins/gate-driven-development/references/common-guardrails.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
