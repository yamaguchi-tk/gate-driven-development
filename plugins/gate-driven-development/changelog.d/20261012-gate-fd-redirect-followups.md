---
type: patch
---

#### Summary

pre-PR gate は、`gh pr create`・`gh pr new`・`gh api` の pulls への POST を、merge gate と同じ探し方（`lib/gh_command_parse.py` の `_find_sub_command`）で探すようになった。gh と同じく、sub-command の前後のリダイレクトと flag を読み飛ばすので、`gh 2>/dev/null pr create`・`gh pr -R o/r create` も PR 作成として検査する。前は gh の直後の `-R`・`--repo`・`--hostname`・`--help`・`--version` しか読み飛ばさず、これらを通していた。引数からリダイレクトとそのオペランドを除いて読むので、`--body 2>/dev/null "…"` の本文にも検査が届く。

pre-PR gate は、`lib/gh_command_parse.py` を読めない・解析が例外で終わるとき、active GDD の中なら create・new・pulls を含む Bash の呼び出し（コマンド・cwd・説明などのどれか）を止める（merge gate と同じ向き）。前は hook が exit 1 で終わり、PR 作成を検査せずに通していた。active GDD かは、tool_input の cwd・workdir と最上位の cwd で決める（`cd` 先は解析できないので見ない）。

fd 番号の除去は、両方の gate で引用符の外の 1〜10 桁の数字にそろえた（11 桁以上は bash でも zsh でも語として残る）。`20261010-pre-pr-gate-shared-lexer.md` の、pre-PR gate は 1 桁だけ・merge gate は桁数を問わず消すという記述は、この記述で置き換わる。merge gate は、2〜10 桁の数字がリダイレクトに密着する形（`gh pr merge 12>/tmp/x`）があると、merge の対象を決められないものとする。bash はこの数字を fd 番号に、zsh は語（PR 番号）に読むので、どちらに決めても一方の shell で別の PR を merge させる。active GDD の中では止める。marker の無い checkout では、読めた番号・URL で GDD の PR 台帳と照合する。bash の読みで番号・URL が無いとき（`gh pr merge 12>/tmp/x`）は、最上位のコマンドに限り、2〜10 桁の数字を語として読む zsh の読みの番号・URL で照合する（前は番号が無く、照合せずに通していた）。入れ子の `bash -c` の本体にも同じ判定をかける。

merge gate は、shell interpreter の `-c` の前にあるリダイレクト（`bash 2>/dev/null -c '…'`）と `+` の option（`bash +e -c '…'`・`bash +o pipefail -c '…'`）を読み飛ばし、後ろの script の `gh pr merge` を検査する。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_shared_lexer.py`
- `plugins/gate-driven-development/tests/test_push_command_parse_push_detection.py`
- `plugins/gate-driven-development/tests/test_merge_gate_target_grammar.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`（pre-PR gate・merge gate を入口から流すテストを含む）
- 追加: `tests/test_pre_pr_gate_shared_lexer.py`（リダイレクト・flag の後ろの PR 作成、`--body` の後ろのリダイレクト、2〜10 桁の fd 番号、shell の `-c` の前のリダイレクトと `+` の option、lib が壊れたときの block と payload の cwd）
- 追加: `tests/test_merge_gate_target_grammar.py`（台帳の経路で 2〜10 桁の fd 番号の merge を止める、GDD の中の unresolvable・shell の `-c` の前のリダイレクトと `+` の option）
