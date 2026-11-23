---
type: minor
---

#### Summary

- requirements-gating で design の観点の reviewer の組も起動したときは、planning reviewer の出力を受け取った直後に Dialectic review も起動する（前の版では design-gating のときだけ起動していた）

#### Changed

- Dialectic review の起動の場所（`references/dialectic-review.md`）

#### Affected Files

- `references/dialectic-review.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
