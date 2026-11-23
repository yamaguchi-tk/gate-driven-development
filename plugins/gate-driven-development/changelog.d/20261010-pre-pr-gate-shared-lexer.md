---
type: patch
---

#### Summary

pre-PR gate は、PR 作成のコマンドを探す字句解析（heredoc の本文の除去・行継続・コメント・演算子の切り出し・1 桁の fd 番号の除去）を、merge gate と同じ `lib/gh_command_parse.py` から読むようになった。hook の中に持っていた古い写しは消した。これで、語の途中の `#`（`echo fix#12; gh pr create …`）の後ろや、`bash <<EOF` の本文の中の `gh pr create` も PR 作成として検査する。前は、これらをコメントやデータとして捨てて通していた。

`lib/gh_command_parse.py` の字句解析は、fd 番号の除去（`2>&1` の `2`）を引用符の中にかけなくなった。pre-PR gate の本文の読みでは、引用符の外でも 1 桁の数字だけを fd 番号として消すので、`--body "| 123456789012<br> |"` や `--body 123456789012>out.txt` の本文の数字が残る。merge gate は今までどおり、引用符の外の桁数を問わない数字を消す。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_shared_lexer.py`
- `plugins/gate-driven-development/tests/test_gh_line_continuation_tokens.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`（pre-PR gate・merge gate を入口から流すテストを含む）
- 追加: `tests/test_pre_pr_gate_shared_lexer.py`（旧の写しが見落とした形、本文の 12 桁数字、gate ごとの fd 番号の除去）
- `test_gh_line_continuation_tokens.py` の `InlineCopyMatchesLibTests`（写しと lib の一致を見るテスト）は、写しが無くなったので消した
