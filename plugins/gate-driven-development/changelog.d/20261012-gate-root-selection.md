---
type: patch
---

#### Summary

- `docs/SECURITY.md` の PR 台帳の限界で、`cd <GDD worktree> && … gh pr create`・`git push` の形で pre-PR gate・pre-push gate が検査せずに通すことを、直さずに受け入れた限界と書いた。root の選び方を merge gate にそろえる案と、GDD worktree にも marker を書く案は、completion-check を受けずに作られた PR をほとんど止めないと見込まれたので採らなかった

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py`）
