## Goal-Driven Execution

この作業は `gdd-goal-driven-execution` を workflow owner にします。`superpowers:executing-plans` は advisory reference として扱い、GDD artifact へ戻します。superpowers を workflow owner にしない。

### Goal Contract

- Goal: 確度の高い原因または改善方針を見つけ、Goal 達成まで必要な修正と検証を回す
- Done When: contract test / scenario eval / PR CI の証跡が揃い、未解決 blocker が残らない
- Not Changing Without Human: scope / safety / merge / deploy / release boundary

原則は **Goal は維持し、Plan は更新する**。

### Current State

- Done: 直近の state.md / tasklist.md / PR / CI を確認済み
- Missing: root cause confidence が confirmed か、または次の証跡が必要
- Evidence: GDD artifact、Git / PR / CI / test
- Uncertainty: 現時点の原因仮説はまだ likely

### Working Hypothesis

- If: 現在の failure は reviewer loop contract の証跡不足が原因
- Then: 不足する contract test と skill guidance を追加すると scenario eval が pass する
- Disprove By: 追加後も同じ critical check が落ちる
- Verification: focused pytest と scenario eval

### Next Action

- Execute and Verify: 最小の contract test を追加し、fixture で scenario eval を回す

### Loop Result

- Executed: contract と scenario artifact を更新
- Observed: confidence != confirmed の場合は fix allowed: no のまま追加証跡を取る
- Decision: progress
- Plan Update: `implementation_fix_only に route しない`。root cause が confirmed になるまで Working Hypothesis を更新して続ける
