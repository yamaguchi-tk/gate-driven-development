---
type: patch
---

#### Summary

- merge gate のパーサは、`gh pr merge` の URL を gh と同じく host を問わず path の前方一致で読み、正準形の URL（`…/pull/7`）として記録する。host は gh が正規化する（大小文字・Unicode・下位の host・host が空の形）ので、列挙で近似しない。そのうえで、対象を名指しできない形（番号の後が空白・`.`・`-x` などで始まる、host が大小文字を除いて `github.com` と一致しない、port・userinfo・path の `%xx` を含む）は、対象を決められない merge として扱う。marker の無い checkout では、その URL が台帳の PR に当たれば止め、当たらなければ通す。別の host（GHES など）で owner/repo/番号が台帳と一致する merge も止まる
- 語の途中の行継続を挟んだ `…/pull/1\⏎23` のような形は、PR 1 として名指しせず、対象を決められない merge として止める（marker の無い checkout では、読んだ 旧#1 で台帳を照合する）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/hooks/scripts/lib/merge-gate-evidence.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/tests/test_merge_gate_target_grammar.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_target_grammar.py`（番号の後の続き・host・`%xx` の綴りが、パーサで URL と unresolvable になり、台帳の PR なら止まる）。既存の `tests/test_gh_line_continuation_tokens.py` が、行継続を挟んだ URL が対象を決められない merge（`unresolvable`）になる契約を固定している
