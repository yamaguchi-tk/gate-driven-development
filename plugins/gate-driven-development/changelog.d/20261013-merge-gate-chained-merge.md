---
type: patch
---

#### Summary

merge gate は、1 回の Bash に `gh pr merge` が 2 つ以上あるとき（`gh pr merge 6 && gh pr merge 7`、入れ子の `bash -c`、改行で区切った形を含む）、読めた番号・URL を全部 GDD の PR 台帳と照合するようにした。marker の無い checkout（root checkout など）から打った連結した merge が台帳の PR を含むと、今までは照合する番号が無く通っていたが、止めて GDD の worktree での実行へ誘導する。台帳の PR を含まない連結した merge は今までどおり通る。

- 演算子でつないだ merge は、merge ごとの `-R` の値と番号を組にして照合する。先頭の `cd` は全部の merge の実行先として、その origin で組む。merge の間・後ろに `cd` があるとき、`-R` の無い番号は番号だけで照合する
- 改行で区切った merge（1 本の merge の位置引数 2 つ以上として読まれる）は、番号と `-R` の対応を決められないので、番号だけで照合する
- slash の無い未展開の `-R`（`-R "$REPO"`）の番号は、1 本の merge でも番号だけで照合する（今までは照合から落ちていた）
- 0918 の断片（`20260918-merge-gate-non-gdd-merge.md`）が書く「連結した merge は台帳の PR でも通る」限界は、この変更でなくなる

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`

#### User Action Required

- なし

#### Validation / Eval Impact

- `plugins/gate-driven-development/tests/test_merge_gate_chained_merge_ledger.py` を足し、`test_merge_gate_hook_non_gdd_merge.py` の、台帳の PR を含む連結した merge を通すとしていた期待を、止める側に改めた
