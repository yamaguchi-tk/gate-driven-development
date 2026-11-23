---
type: patch
---

#### Summary

`docs/SECURITY.md` の制限事項の、merge gate が止めない形の項を書き直した。cwd が marker の無い git repo のとき、binding を引くのは、parser が対象を決めきれ、cd が無いか cd 先を採れた merge だけで、引用符の無い `$(…)`・`$pr` などで parser が対象を決めきれない形、`-R` の値に `$` を含む形、`$`・相対パスなどで cd 先を採らない cd を含む形は、binding も cd 先の証跡も読まず、台帳で当たらなければ通す（台帳を読めないとき・対象 PR を特定できないときも通す）。cd 先を採る条件の正本（`_select_cd_target`）、URL・`-R` で明示した merge の扱い、実データの件数と内訳、直さない根拠と開き直す条件を書いた。merge gate の `repo-root-unresolvable`・`pr-target-unresolvable` の案内に、絶対パスの cd をコマンドの先頭に 1 つだけ書き、コマンド全体に `$`・バッククォート・`env` を含めないことを足した。判定は変えない。

#### Affected Files

- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`（案内の文とコメントだけ）
- `plugins/gate-driven-development/changelog.d/20261013-merge-gate-relative-cd-limit.md`（`amends:`。Summary に、cd 先を採る条件（cd 先に marker があることを含む）と、台帳を読めないとき・対象 PR を特定できないときも通ることを足した）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_hook_gate_activation.py`・`tests/test_merge_gate_binding_steering.py`・`tests/test_merge_gate_hook_block_reason_quality.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
