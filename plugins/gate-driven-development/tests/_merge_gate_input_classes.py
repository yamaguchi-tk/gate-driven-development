"""merge gate hook に渡る入力が同じ行を 1 組にまとめ、hook の起動を組ごとに 1 回にする。

`run-merge-gate-hook.sh` が payload から読むのは、次の 2 つだけである。

- payload 全体に `merge` の語があるか（先頭の粗い絞り込み）
- 埋め込みの python（`gh_command_parse.parse_gh_pr_merge` を呼ぶ部分）が bash に渡す行（`tool_input` の cwd を含む）

2 つが同じ行は、同じ repo の状態では hook の判定も同じになる。埋め込みの python は、hook の
ファイルから取り出して、そのままプロセスの中で走らせる（写しを持たない）。
"""
from __future__ import annotations

import io
import json
import re
import sys

from _paths import PLUGIN_ROOT

HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "run-merge-gate-hook.sh"
LIB_DIR = PLUGIN_ROOT / "hooks" / "scripts" / "lib"

_EMBEDDED = re.compile(
    r"""done < <\(printf '%s' "\$PAYLOAD" \| python3 -c '\n(.*?)\n' "\$SCRIPT_DIR/lib" "\$PROCESS_CWD\"""",
    re.S,
)


def _embedded_parser_source() -> str:
    match = _EMBEDDED.search(HOOK_SCRIPT.read_text(encoding="utf-8"))
    if match is None:
        raise AssertionError("run-merge-gate-hook.sh の埋め込みの python が見つからない")
    return match.group(1)


_SOURCE = _embedded_parser_source()


class _Stdout:
    def __init__(self):
        self.buffer = io.BytesIO()


def hook_input_class(payload: dict, process_cwd) -> tuple:
    """hook が payload から読む 2 つを、比べられる形で返す。"""
    text = json.dumps(payload)
    out = _Stdout()
    saved = sys.argv, sys.stdin, sys.stdout
    sys.argv = ["-c", str(LIB_DIR), str(process_cwd)]
    sys.stdin = io.StringIO(text)
    sys.stdout = out
    try:
        exec(compile(_SOURCE, str(HOOK_SCRIPT), "exec"), {"__name__": "__main__"})
    finally:
        sys.argv, sys.stdin, sys.stdout = saved
    return "merge" in text, out.buffer.getvalue()


def once_per_input_class(run, process_cwd):
    """`run(payload)` を、hook の入力の組ごとに 1 回だけ呼ぶ形に包む。

    包んだ関数は、同じ組の 2 回目からは 1 回目の結果を返す。repo の状態を変えたら、包み直す。
    """
    results: dict[tuple, object] = {}

    def call(payload: dict):
        key = hook_input_class(payload, process_cwd)
        if key not in results:
            results[key] = run(payload)
        return results[key]

    return call
