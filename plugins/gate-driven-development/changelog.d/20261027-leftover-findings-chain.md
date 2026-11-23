---
type: patch
---

#### Summary

マージの後の次の計画（`gdd-next-plan`）で、直さないと決めた medium・low（`## Advisory Findings (Impl-Gate)` の行、PR 本文の `指摘止まり（` の行）を「後続PRに送ること」に入れず、それを直す後続 PR を申し出ないようにした。本人が PR 番号を挙げて頼んだときだけ後続にし、そのときは残りを 1 本にまとめる。

#### Changed

- `skills/gdd-next-plan/SKILL.md`：Phase Continuity Packet の「後続PRに送ること」から、直さないと決めた medium・low を外した。それを直す後続 PR は、本人が PR 番号を挙げて頼んだときだけ作り、残りを 1 本にまとめる

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-next-plan/SKILL.md`

#### User Action Required

- なし。マージの後、残した指摘（Advisory Findings・`指摘止まり（` の行）を直す後続 PR を、assistant は申し出なくなる。直したいときは、本人が PR 番号を挙げて頼む

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- skill の変更前後で、マージの報告に Advisory Findings が 2 件ある場面を回し、後続 PR の申し出が消えることを確かめた（`review-log/20261027-leftover-findings-chain.notes.md` § Skill RED-GREEN Evidence）
