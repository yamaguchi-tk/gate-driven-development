---
type: patch
---

#### Summary

`gdd-implementation-gating` Step 1d が差し戻した task で、`gdd-test-driven-development` が RED を取り直す経路を決めた。

- `gdd-implementation-gating` Step 1d の finding の category を `product`（Round を消費する）と明記した。category の無い finding の既定と同じで、挙動は変わらない。Step 1d で差し戻された task は `Gate Rounds` が 1 以上になる
- 取り直す節の判定を Step 1d と同じにした（形式の分け方・パスの正規化・`<default-branch>` の決め方）。default branch は gate runner と同じく `origin/HEAD` から決め、local の branch 名は使わない。判定の `git diff`/`git status` が失敗した節も記録済みに数えない
- 差し戻しの後は production の差分が既にあり、足したテストはすぐ pass して RED にならない。そこで § Pre-existing Implementation Without RED の 2・3 で characterization RED を取るようにした。取れたら Quarantine Output Contract の既定 route（`design_detail_only`）には回さず、実装 handoff へ進む。`#### RED Evidence` が無いまま gate に回った task も、`gdd-implementation-gating` で差し戻された（`Gate Rounds` が 1 以上の）task で、その task の production ファイルに差分があるときは同じにする。`Gate Rounds` が 0 の task は、前の task の実装で差分があっても通常の手順で RED を取る。実装を無効にするのは `## Worktree` の中の一時 commit で戻せる形に限り（別の worktree・共有の `git stash` は使わない）、記録の前に実装を戻してテストが pass することを確かめる
- 取り直した RED は、数えなかった節を置き換えて記録する（節を足さない）。これまでは古い節が残ると、Step 1d が古い節を読んで差し戻し、TDD は新しい節を見て記録済みに数え、同じ差し戻しが続きえた
- Post-Compaction Resume Check の進み先を Step 10（実装 handoff）に直した（Step 9 は `design_detail_only` で戻る手順）。Guardrails の Context Compaction Resilience も、同じ判定を指すようにした
- `references/rollback-patterns.md` の RED 再現テストは、既存テストで再現できても、差分に入る形（新しいテスト、または既存テストへの追加・変更）で書くようにした。変えていない既存のテストは Step 1d が差し戻す
- `gdd-subagent-driven-implementation` 手順 17 で節を作るとき、`Covers AC:` が無い remediation task では、finding が AC ID を明示しているときだけその ID を書く。推定では書かない。この節は `gdd-test-driven-development` § AC ID Binding の例外として、`AC:` が無くても reject しない（`lint-ac` の WARN で残す）

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/superpowers-overlap.md`
- `plugins/gate-driven-development/references/faq.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
