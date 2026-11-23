---
type: patch
---

#### Summary

簡易版 human check テンプレートの判断ポイントの `判断軸:` で、軸の名前を相談役の欄とそろえ（「信頼境界」を「信頼境界・fail-closed」に）、「この 2 つは必ず」を書く条件に言い切った。`判断軸:` には決め手の軸と一言を書き、推奨案が要件の充足度か信頼境界・fail-closed で ○ でなければ、その軸も書く。相談役（`gdd-opus-advisor`・`gdd-opus-advisor-max`・`gdd-fable-advisor`）の `比較の軸:` では、要件の充足度に「範囲の広さを含む」を、確かめやすさに「未測のまま決めていないか」を足した。軸は、相談役の欄には名前と定義を、テンプレートには名前だけを書く。軸を変えるときにそろえる先は、`references/autonomy.md` § 比較の軸 を含めて 5 か所である。

#### Affected Files

- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor.md`
- `plugins/gate-driven-development/agents/gdd-opus-advisor-max.md`
- `plugins/gate-driven-development/agents/gdd-fable-advisor.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`・`tests/checks/lint-scripts-functional.sh`（runtime profile の推定 token の上限を、standard は 45443 から 45454 に、express は 30088 から 30099 に上げた）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
