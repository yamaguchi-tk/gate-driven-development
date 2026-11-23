---
type: patch
---

#### Summary

マージの後の次の計画（`gdd-next-plan`）で、直さないと決めた medium・low を直す後続 PR を申し出ない規定が、後続 Stage の無いマージ（次にやることが cleanup だけ・完了のとき）にも掛かるようにした。`collect-gdd-telemetry.py` の `--help` と説明に、消えた worktree を警告して飛ばすことを書いた。

#### Changed

- `skills/gdd-next-plan/SKILL.md`：申し出をしない文を、Phase Continuity Packet の項目から「merge 後」の箇条の本文へ移した。後続 Stage の有無によらず、直さないと決めた medium・low を「後続PRに送ること」にも次にやることにも入れない
- `scripts/collect-gdd-telemetry.py`：module の説明と `--include-worktrees` の help に、ディレクトリが無い worktree を警告して飛ばすこと、`--root` で明示した場所が無いときは終了 1 になることを書いた

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-next-plan/SKILL.md`
- `plugins/gate-driven-development/scripts/collect-gdd-telemetry.py`
- `plugins/gate-driven-development/tests/test_telemetry_missing_worktree.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_telemetry_missing_worktree.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- skill の変更前後で、後続 Stage の無いマージの場面を回した（`review-log/20261028-accepted-findings-589-600.notes.md` § Skill RED-GREEN Evidence）
