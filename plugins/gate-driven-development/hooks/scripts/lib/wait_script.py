"""理由文に載せる待機スクリプト（scripts/wait-until.py）のパスと書き方。Stop hook と wait-loop-gate が共有する。"""
from __future__ import annotations

import shlex
from pathlib import Path

from lib.task_binding_resolve import _has_unsafe_char

# Bash では ${CLAUDE_PLUGIN_ROOT} が未定義なので、絶対パスで示す
WAIT_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "wait-until.py"
# パスを載せられないときの書き方。`<plugin>` は shell に貼るとリダイレクトになるので使わない
PLACEHOLDER = "…/scripts/wait-until.py"


def shown_wait_script(script: Path) -> str:
    """理由文に載せるパス。制御文字・surrogate を含むなら、クォートしない placeholder にする。"""
    path = str(script)
    return PLACEHOLDER if _has_unsafe_char(path) else shlex.quote(path)
