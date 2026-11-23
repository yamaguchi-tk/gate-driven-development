---
type: patch
---

#### Summary

自走上限が「マージまで」「マージ・デプロイ・QA まで」のとき、完了条件に「マージ」を含めて `Post-PR Completion Scope` が記録されても、マージ後の QA の経路に入るようにした。前は Scope があると従来の止まる経路に戻っていた。入る条件は `references/post-merge-qa.md` § 入口 の 1 か所にまとめた。

#### Changed

- `references/post-merge-qa.md` に § 入口 を足した。条件は、Option 1 で PR を作り、`state.md` の `Approved Direction` の自走上限が上の 2 値で、同じ `Approved Direction` の `Post-PR Completion Scope` が無い（`none`・`なし` を含む）か、その項目がすべて自走上限の中にあることである。中にあるのは、マージ、デプロイの完了確認、QA 計画に入る確認（read-only か、宣言の Environment と Write Targets の中の書き込み）だけである。apply・release・宣言の外への書き込みなどが 1 つでもあれば、従来の Post-PR Scope Continuation に進む
- `references/post-merge-qa.md` § 入口 に、completion-check を main で動かしたとき、および中断した後に再開するときの入り方を足した
- `references/post-completion-pr-flow.md` Option 1（冒頭・手順 7・Step 4）、`references/subagent-dispatch.md` § Completion-Check Post-Return Routing、`skills/gdd-completion-check/SKILL.md` の Re-entry 手順 6 が、§ 入口 を指すようにした
- Completion-Check Post-Return Routing で、subagent が `<gdd-stop reason="blocked">` で戻ったときは、完了サマリーではなく blocker を出して止まるようにした
- `references/post-merge-qa.md` で次を変えた
  - 宣言は human check のときと手順 1 の前の 2 回読み、選んだ値が選べなくなっていたら止まる
  - マージの条件に、QA 計画をレビューした head とマージする head が同じことを足した。Deploy Paths と比べるパスは `git diff --name-only --no-renames origin/<既定ブランチ>...<head>` で出す
  - QA 計画のレビューを Codex・Cursor で行う先と、起動できないときに止まることを足した
- human check の「OK でも許可されないこと」（`references/human-check-template.md`・`references/human-check-template-compact.md`）から、自走上限の値で許す操作を除くようにした。§ 自走上限の置換値に「PR 作成 + 外部レビュー収束まで」の行を足し、`references/human-check-template.md`・`references/requirements-template.md` の値の例の列挙を、この表を指す形にした

#### Affected Files

- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/requirements-template.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/tests/test_agent_dispatch_model_gate_contract.py`

#### User Action Required

- なし。`.gdd-config.md` の宣言の書式は変えていない

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- `tests/test_agent_dispatch_model_gate_contract.py` ほか、変更した文書を参照する pytest（コメントの変更だけで、assert は変えていない）
