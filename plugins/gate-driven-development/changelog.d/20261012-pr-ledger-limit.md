---
type: patch
---

#### Summary

- PR 台帳（`gdd-pr-roots`）の限界を、`docs/SECURITY.md` の state dir の `gdd-pr-roots` の項と § 制限事項、`hooks/scripts/lib/gdd-pr-roots.sh` の冒頭のコメントに書いた。挙動は変えていない
- `cd <GDD worktree> && … gh pr create` の形で移動先に marker が無いと、pre-PR gate は completion-check などの marker を見る検査をせずに通し、台帳にも書かない。state.md に `PR URL` が無い PR も照合で当たらないので、merge gate の台帳の照合は GDD の PR の多くに効かない

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py`）
