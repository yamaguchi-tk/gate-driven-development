---
type: patch
---

#### Summary

規定（判定・手順・用語・参照先）を変えるタスクで、同じ規定を書いた別の箇所の直し漏れを、design と completion で拾うようにした。

- `gdd-design-gating` の Step 5「影響範囲」: 規定を変えるなら、変える前の語と正本の名前で `git grep` した語と、変える箇所の外の記述ごとに直すか直さない理由を書く
- `gdd-planning-reviewer`: 規定を変える design.md に、この grep の記録が無ければ Medium として報告する
- `gdd-completion-reviewer` の Review Focus に 10 を足した。最終の diff が変えた規定について同じ grep をやり直し、diff の外に残って変えた後の規定と食い違う記述を `Same-Rule Drift` として指摘する。agent・bot が実行時に読む文書なら High、人が読む文書なら Medium。対になる箇所の片方だけに入った変更も同じ扱い。Coverage には、grep した語と、grep で見つかった箇所を 1 行ずつ（`file:line` と、diff で直した／食い違いなし／design で直さないとした（理由）／指摘した）書く

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-design-gating/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/agents/gdd-completion-reviewer.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
