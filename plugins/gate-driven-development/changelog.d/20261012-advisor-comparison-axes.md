---
type: patch
---

#### Summary

相談役（`gdd-opus-advisor`・`gdd-opus-advisor-max`・`gdd-fable-advisor`）の出力に `比較の軸:` の欄を足した。案ごとに、6 つの軸（要件の充足度、信頼境界・fail-closed、確かめやすさ、堅牢性、保守性、費用）で ○/△/× と一言の理由を書く。要件の充足度と信頼境界は `対象外` にしない。案が 1 つだけの相談でも、その案を軸ごとに評価する。簡易版 human check テンプレートの判断ポイントの `判断軸:` には、決め手の軸と一言を書き、既定の軸の名前を欄に示した。軸の名前と定義は読み手（agent の定義とテンプレート）に直接書き、`references/autonomy.md` § 比較の軸 には、4 か所をそろえることと、軸の選び方の根拠を置いた。lint・gate では検査しない。

#### Affected Files

- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`・`tests/checks/lint-scripts-functional.sh`（runtime profile の推定 token の上限を、standard は 45430 から 45443 に、express は 30083 から 30088 に上げた）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
