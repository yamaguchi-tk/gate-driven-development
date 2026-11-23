---
type: patch
---

#### Summary

`docs/SECURITY.md` の制限事項に、merge gate が止めない形を 1 つ書き足した。merge gate が cd 先を root にするのは、コマンドの先頭の cd 1 つが絶対パスで、コマンドに `$`・バッククォート・`env` が無く（条件の正本は `_select_cd_target`）、cd 先に marker があるときだけで、相対パスなどの形ではセッションの cwd を root にする。cwd が marker の無い git repo なら、cd 先の証跡を読まず、GDD の PR 台帳に無ければ通す（台帳を読めないとき・対象 PR を特定できないときも通す）。hook の挙動は変えていない。

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
