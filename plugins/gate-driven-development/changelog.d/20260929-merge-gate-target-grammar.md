---
type: patch
---

#### Summary

- merge gate は、`gh pr merge` の対象 PR を gh と同じ規則で読むようにした。短い flag の束ね（`-st 7`）、密着した値（`-t7`・`-Racme/x`・`-t=x`）、`--` の後の位置引数、リダイレクトを挟んだ flag の値を読む。sub-command（`pr`・`merge`）は gh（cobra）の探し方で見つけ、間に置かれた flag（`gh pr -R acme/x merge 7`・`gh pr -s -- merge 7`・`gh -s -t pr merge 7`・`gh pr -st - merge 7`）でも merge を見失わない。これまでは `-` で始まる token を一律に 1 つ飛ばしていたので、`gh pr merge -st 7 <branch>` の 7（件名）を対象の PR と読み、`gh pr merge 7 -st 8` の 8（件名）で対象を上書きし、`pr` と `merge` の間に flag がある merge を merge と判定していなかった
- 対象を決められない merge（gh の表に無い flag・値の無い flag・位置引数 2 つ以上・branch 名）は、読めた番号が記録の PR と違っても、本体の経路で止める。steering が 1 件に決まる経路（found）は `pr-target-unresolvable`、複数の経路と、候補 0 件で PR URL を記録した steering がある経路は `steering-ambiguous` で止まる（候補 0 件で PR URL の記録が無いときは、対象を省いた merge と同じ扱い）（これまでは、番号が違えば別の PR の merge として通していた。改行で続く別のコマンドの引数を位置引数に読んだ形も、この止め方に入る）
- 番号は gh が読む形（先頭の `#`・`+`・先頭の 0）も番号にする。URL は gh と同じく `http://`・大小文字違いの host・`/pull/7/files`・`?…#…` 付きも番号 7 の URL として読み、記録した PR URL との照合は番号で行う（正準形でない記録〔`<…>`・`| 注記`・リンクの形・`/files`・先頭の 0〕も照合できる）。全角の `７` などは branch 名として止める。別の repo の同じ番号の URL は、`-R <owner>/<repo> 7` と同じく `pr-target-unresolvable` で止める
- 台帳の経路（marker の無い checkout から GDD の PR を merge する経路）は、対象を決められない merge でも、読めた URL と番号のどれかが台帳の PR に当たれば止める。当たらなければ今どおり通す
- パーサの中での短い flag の束ね（`-sss…`）と `env` の短い option の束（`env -vvv…`）の読み取りを線形にし、`gh` の token が並ぶコマンド（`gh -s gh -s … ; gh pr merge 7`）の sub-command の探索も 2 乗にならないようにした（tokenize が 1 つの長い token に対して長さの 2 乗になる点は変わらない）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/tests/test_merge_gate_target_grammar.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_gate_regressions.py`

#### User Action Required

- GDD の worktree から、別の repo の同じ番号の PR を URL で merge する形は `pr-target-unresolvable` で止まる。その repo の checkout（root の repo 内のディレクトリ）から実行する
- GDD の worktree で PR を記録した steering があるとき、1 回の呼び出しに、対象を決められない merge（知らない flag・余分な位置引数・改行で続く別のコマンドの引数）が入ると止まることがある。merge は 1 回の呼び出しに 1 つずつ、対象を番号か URL で 1 つ指定して実行する

#### Validation / Eval Impact

- `tests/test_merge_gate_target_grammar.py`
  - パーサの単体テスト：gh の flag の表と pflag の規則での読み、sub-command の探し方（`-`・空の token・`-=` を含む）、番号と URL の受理、長い束ね・gh の token の並び・`env` の束の解析時間
  - hook の入口から固定したもの：対象を決められない merge の停止（found・multiple の経路）、sub-command の探し方の形、URL の形の番号での照合（found・multiple・終端の steering だけの 3 経路 × 正準形でない 5 種の記録）、台帳の経路の照合
- `tests/test_merge_gate_hook_gate_regressions.py`：別の repo の同じ番号を URL の形で merge するとき、番号の形（`-R`）と同じく止めることを固定した（これまでは通すことを固定していた）
