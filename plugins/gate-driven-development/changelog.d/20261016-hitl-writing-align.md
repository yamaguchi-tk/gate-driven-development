---
type: patch
---

#### Summary

- human check の長さを優先していた規定を、`references/human-check-template.md` § 判断の書き方 に揃えた。行数の目安を超えたときは、判断に効かない段落を外し、内部用語を説明する。判断の筋書き（いまの状態 → 分かったこと → 何が起こりうるか → 選択肢 → おすすめ）は削らない。必須ルール 12 の「3-5 行程度」、§ Compact First の「line budget に収める」、gdd-requirements-gating の「圧縮・言い換え」、self-contained-contract・faq の「短い自然文」を、§ 判断の書き方 を指す文に替えた
- full の human check テンプレートでは、`### 判断ポイント` を `### 30秒判断` の直後（`### やること`・`### 承認サマリ` の前）に移した。30秒判断のカードでも、判断ポイントを整理した要件の直後に置く。`承認サマリ` は判断ポイントの後に置く
- build・debug・completion の途中で人に戻すときの停止本文（`references/rollback-patterns.md`）の「次に決めてほしいこと」も、§ 判断の書き方 に従う

#### Affected Files

- `references/human-check-template.md`（§ GDD Complexity Budget、§ Compact First、出力テンプレート、必須ルール 12・13、§ HITL の役割）
- `skills/gdd-requirements-gating/SKILL.md`（§ GDD Complexity Budget）
- `references/self-contained-contract.md`、`references/faq.md`、`references/rollback-patterns.md`

#### User Action Required

なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
