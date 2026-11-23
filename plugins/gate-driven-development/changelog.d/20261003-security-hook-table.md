---
type: patch
---

#### Summary

- `docs/SECURITY.md` § 4 の hook の表に、PreToolUse の EnterPlanMode・EnterWorktree・Skill・Agent・Bash の hook（pre-PR gate・pre-push gate・merge gate・root-branch guard と、PR 後の push の案内）を足した
- 同じ節の「hook は外部通信しない」に、PR 後の push の案内が `gh pr view` で PR の有無を読む例外を書いた

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
