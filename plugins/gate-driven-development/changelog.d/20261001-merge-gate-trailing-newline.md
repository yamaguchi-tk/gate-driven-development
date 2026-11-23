---
type: patch
---

#### Summary

merge gate は、プロセス cwd などの toplevel から root を決め、payload の `cwd` / `workdir` と `cd` 先の toplevel・git の共通ディレクトリを root と照合している。名前が改行で終わる別 repo を実行先にすると、この照合を通っていた。プロセス cwd が改行で終わるときは、改行を落とした同名のディレクトリを root にしていた。シェルの `$()` が末尾の改行を落とし、別のパスが同じ文字列になっていたためである。

今後は、末尾の改行を保ったまま値を取る。toplevel が改行で終わると分かった実行先（プロセス cwd、payload の `cwd` / `workdir`、解決できた `cd` 先）があれば、merge と merge かを判定できないコマンドを、root の marker の有無を問わず `pr-target-unresolvable` で止める。root に marker がある GDD のセッションでは、`cd` 先が制御文字（改行・タブなど）を含む merge も、実行先を解決できないものとして止める。途中に改行を含むパスの扱いは変えていない。

#### Fixed

- `hooks/scripts/run-merge-gate-hook.sh` は、プロセス cwd・payload の `cwd` / `workdir`・その絶対化（`pwd`）・候補ごとの `git rev-parse` の出力を、末尾の改行を落とさずに読む
  - toplevel が改行で終わる実行先があれば、merge と、merge かを判定できないコマンドを止める
  - 共通ディレクトリが改行で終わる実行先は、同じ repo の別 worktree として通す条件に当たらない
- `hooks/scripts/lib/gh_command_parse.py` は、制御文字を含む `cd` 先を採らない。hook への出力は改行・タブを空白に置き換えるので、照合するパスと実際に移る先が別になっていた。採らない `cd` 先は、root に marker があれば実行先を解決できないものとして止まり、marker の無い root では PR 台帳の照合に回る

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/tests/test_merge_gate_trailing_newline.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_trailing_newline.py` を足した。hook の入口から次を確かめる
  - 名前が root の名前＋改行の別 repo を指すと止まる。指し方は次のとおり
    - payload の `cwd`（値そのもの・サブディレクトリ・`/`・`/.`・`/..` で終わる形）
    - symlink を経由した `cd`
    - プロセス cwd
    - 共通ディレクトリが改行で終わる worktree への `cd` と payload の `cwd`
  - marker の無い root checkout から、名前が改行で終わる GDD の worktree を指すと止まる（改行を落とした同名の worktree がある形・無い形、解析が縮退するコマンド）
  - root に marker があるセッションで、改行・タブ・語の途中の行継続を含む `cd` 先は止まる
  - 文字列でない `cwd`、toplevel を取れない git・末尾の改行を出さない git では止まる
  - 途中に改行を含むパスの判定（`approval-missing` などで止まる形）と、改行を含まない root を指す形の allow は変わらない
