#!/usr/bin/env bash
# ~/.claude/gdd-hooks-disabled が存在すれば呼び出し元 hook を即 no-op で抜けさせる。
# 純 bash。python/git 非依存。HOME を尊重する（テストで override 可能）。
gdd_kill_switch_active() {
  [[ -n "${HOME:-}" ]] && [[ -f "${HOME}/.claude/gdd-hooks-disabled" ]]
}

# hook の中の文字の扱いを、利用者のロケールに依らず UTF-8 にそろえる。Claude Code が渡す payload と
# state.md は UTF-8 で、UTF-8 以外のロケール（EUC-JP など）では python の stdin・stdout・argv・環境変数と
# awk・sed がそれを読めず、block gate が例外で素通りしていた。どの hook も最初にこのファイルを source する。
# C.UTF-8 が無い OS では、bash 自身は受け継いだロケールのままで setlocale の警告を stderr に出し、子の
# awk・sed・grep は C（バイト単位）になる。PYTHONUTF8 はそのときも python を UTF-8 mode にする。
# PYTHONUTF8 は `-I`・`-E` 付きの python には効かないので、そういう起動（下の python3 関数を通るものを含む）
# には `-X utf8` も付ける（tests/test_hook_locale_utf8_contract.py が、リテラルの `python3 -I` などの起動の形で
# 固定する。変数で起動する python は見ない）。
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
# hook の cwd（利用者の repo）の json.py・lib/ などを、標準ライブラリや plugin の module より先に読ませない
# （読むと block gate の import が落ちて素通りする）。hook の中の `python3` は、この関数を通って `-I -X utf8` で
# 起動する（リテラル・変数〔"$PYTHON_BIN"〕・`python3 -` のどれでも）。`-I` は cwd・スクリプトのディレクトリ・
# PYTHONPATH・PYTHONHOME を読まず、Python 3.4 以上で効く。関数を通らない起動もある: `exec python3`、python3 が
# 無いときの `python`（3 系でも）、hook が起動した python・git などがさらに起動する子の python（関数は子の
# プロセスに渡らない）。それらの `-c`・`-` の起動のために PYTHONSAFEPATH=1 も設定する（3.11 以上で cwd を入れない。
# PYTHONPATH の要素は止めないので、子の python は PYTHONPATH の要素を読む）。ファイルで起動する python はもともと
# cwd ではなくスクリプトのディレクトリを入れるので、自分のディレクトリの lib を読むスクリプトは、`-I`・
# PYTHONSAFEPATH のどちらの下でも自分でそのディレクトリを入れる（tests/test_hook_python_safe_path.py）。python3 の
# 実行ファイルが無いときは関数を置かない（置くと `command -v python3` が関数を見つけ、python が無いときに止める
# hook の経路を通らなくなる）。
if command -v python3 >/dev/null 2>&1; then
  python3() { command python3 -I -X utf8 "$@"; }
fi
export PYTHONSAFEPATH=1
