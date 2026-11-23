#!/usr/bin/env python3
"""PreToolUse の payload の最上位の `cwd` を、hook が作業ディレクトリとして使えるかを決める。

Claude Code の Bash の PreToolUse payload は、セッションの cwd を `tool_input` ではなく
最上位の `cwd` に持つ。hook のプロセスの cwd はセッションの cwd と違うことがある
（desktop の worktree のセッションでは root checkout になる）。pre-push・pre-PR・merge gate
と push 後の nudge は、この値が使えるときはプロセスの cwd をここへ移してから判定する。

受けるのは、空でない絶対パスの文字列で、存在して中に入れる（実行権のある）ディレクトリのときだけ。`~` は展開しない
（harness が入れる絶対パスだけを受ける）。タブ・改行・CR を含む値は受けない（hook は
`<key>\\t<value>` の行で bash に値を返すので、そこで別のパスに化ける）。受け入れの条件は
`validate-worktree-command.py` の `extract_cwd` の最上位の cwd の分岐と同じにする。
"""
from __future__ import annotations

import os

_LINE_BREAKERS = ("\t", "\n", "\r")


def toplevel_cwd(payload: object) -> str:
    """使える最上位の `cwd` を返す。使えなければ空文字列。

    `os.path.isdir` は OSError・ValueError（NUL など）を False にするので、例外は出さない。
    """
    if not isinstance(payload, dict):
        return ""
    top = payload.get("cwd")
    if not isinstance(top, str) or not top or not os.path.isabs(top):
        return ""
    if any(ch in top for ch in _LINE_BREAKERS):
        return ""
    if not os.path.isdir(top) or not os.access(top, os.X_OK):
        return ""
    return top
