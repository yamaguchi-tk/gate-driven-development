---
type: patch
---

#### Summary

マージ待ちの宣言（`.claude/gdd-merge-intent.json`）を書いた後に、同じ PR の `gh pr merge` が拒否されて止まったとき、Stop hook が押し返さないようにした（`hooks/scripts/lib/autonomy_pushback.py`）。宣言を書いた後の最後の試行の結果が、コマンドが走る前に止められたもの（merge gate・ほかの PreToolUse hook・auto mode classifier の拒否など、`Exit code` で始まらない is_error の結果）なら拒否とみなす。`Exit code` で始まる失敗（コマンドが走って失敗したもの）は数えず、今までどおり押し返す。番号・URL で PR を特定できない `gh pr merge`（引数なし・branch 名・1 つのコマンドに複数のマージなど）は、対象の PR への試行とみなす。これまでは、merge gate がマージを止めた後に人へ戻して止まると、Stop hook が「CI が success ならマージする」と、拒否された操作の再試行を求めていた。押し返しの文にも、拒否されたなら再試行せずに明言して止まる、という選択肢を足した。

宣言を探す場所は、これまでどおり Stop hook の cwd の toplevel（通常はセッションを起動した worktree）の 1 か所だけである。GDD の worktree で作業していても、宣言はこちらに書く。押し返しの文は「worktree の toplevel」と書く代わりに、hook が読む絶対パスを示すようにした（パスが制御文字・surrogate を含むときは `.claude/gdd-merge-intent.json` と相対で出す）。押し返しの文を UTF-8 に encode できないときは押し返さない。`references/post-merge-qa.md` の手順 2 の説明も同じ内容にそろえた。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_pushback.py`
- `plugins/gate-driven-development/references/post-merge-qa.md`・`references/state-machine.md`
- `plugins/gate-driven-development/hooks/hooks.json`（description）

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_autonomy_pushback.py -q`
