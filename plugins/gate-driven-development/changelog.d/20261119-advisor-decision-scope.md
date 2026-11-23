---
type: minor
---

#### Summary

- 判断の相談役（`gdd-opus-advisor`・`gdd-opus-advisor-max`・`gdd-fable-advisor`）は、出力の `そもそもどうあるべきか:` の先頭に、依頼の原文の目的（材料にある、ユーザーが前に述べた目的の発言を含む）を引用で書き、それに照らして考える
- 相談役は、書かれた文（ユーザーの決定・ADR・規則の文書・要件・前の確認の記録）を理由に案を退ける・狭めるとき、その文の原文を `file:line` つきで引き、その文が何について決めたか（対象）を書く。退ける案が対象の外にあれば、その文では退けない。出力に `引いた決定:` の欄が増え、なし以外のときは「2 本が一致していても、引いた行を読み直してから使う」という呼び出し側への 1 行が付く
- main は、相談役の推奨が書かれた文を理由に案を退けていたら、2 本が一致していても引かれた行を読み直してから推奨として出す（`references/common-guardrails.md` § 選ぶときの基準 の基準 0）

#### Affected Files

- `agents/gdd-opus-advisor.md`・`agents/gdd-opus-advisor-max.md`・`agents/gdd-fable-advisor.md`・`references/common-guardrails.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
