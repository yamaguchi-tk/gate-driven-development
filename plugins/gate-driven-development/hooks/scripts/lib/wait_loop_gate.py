"""PreToolUse（Bash）: background の待ちのループを deny し、scripts/wait-until.py で待たせる。

main は待ちの間 idle で hook が発火しないので、止めどころは起動の時点しかない。場当たりのループは上限が無いか、
打ち切りも成立も exit 0 で見分けられず、条件が壊れていても待ち続ける（2026-10-05 実測。直近 30 日の
background の Bash では、ループ + sleep と --watch・gh run watch がかなりの割合を占めた）。

対象は run_in_background が bool の true の Bash で、command が次のどれかに当たるもの。GDD active を問わず、
subagent の中も対象にする（subagent が background の完了通知や Monitor のイベントを受け取れるかは確かめていない
ので、subagent には background の起動と完了通知を案内せず、foreground で上限を Bash の timeout より短くして待つ
案内を出し、自分が起動した background の処理だけ Monitor で待たせる）。
  - ループの語（until・while・for）の後ろに sleep がある（python の time.sleep も含む）。語の左が英数字・`.`・
    `/`・`-` のときは語に数えない（wait-until.py・/for-ci/ のようなパスの中の語）
  - `--watch`、`gh run watch`
`sleep N` だけの期限 timer（lib/wait_watchdog.py の _TIMER_RE）と、最初のループの語の後ろに sleep が無い command
（`sleep N; <コマンド>` など）は通す。
型を読めない payload は通す。shell は解析しない（agent が事故で打つ形だけを止める）。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from lib.wait_script import WAIT_SCRIPT, shown_wait_script

_LOOP_WORD = re.compile(r"(?<![\w./-])(?:until|while|for)\b")
_SLEEP = re.compile(r"\bsleep\b")
_WATCH = re.compile(r"--watch\b|\bgh[ \t]+run[ \t]+watch\b")


def is_wait_loop(command: str) -> bool:
    if _WATCH.search(command):
        return True
    word = _LOOP_WORD.search(command)
    return bool(word and _SLEEP.search(command, word.end()))


def deny_reason(payload: object) -> str | None:
    """deny するなら理由を返す。通すなら None（型を読めない payload も通す）。"""
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or tool_input.get("run_in_background") is not True:
        return None
    command = tool_input.get("command")
    if not isinstance(command, str) or not is_wait_loop(command):
        return None
    script = shown_wait_script(WAIT_SCRIPT)
    if "agent_id" in payload:
        # subagent が background の完了通知や Monitor のイベントを受け取れるかは確かめていない
        how = ("subagent の中では、待機スクリプトを foreground（run_in_background を付けない）で、`--timeout` を "
               "Bash の timeout（省くと 120 秒、最大 600 秒）より短くして起動する")
        pr_timeout = timeout = "<秒、Bash の timeout より短く>"
        tail = "自分が起動した background の処理の終わりは Monitor で待つ。"
    else:
        how = "待機スクリプトを Bash の run_in_background: true で起動する"
        pr_timeout, timeout = "3600", "<秒、7200 まで>"
        tail = "自分が起動した background の処理の終わりは、その完了通知を待つ。"
    return (
        "background の待ちを、ループ（until・while・for と sleep）や --watch・gh run watch で書かない"
        "（上限が無い、打ち切りと成立が同じ exit 0、条件が壊れていても待ち続ける）。"
        f"{how}: PR の CI は `python3 {script} --timeout {pr_timeout} "
        "--pr-checks <PR 番号> [-R <owner/name>]`、それ以外は `python3 "
        f"{script} --timeout {timeout} -- bash -c '<条件>'`。条件は、成立なら 0、まだなら 1、"
        "条件の確認が壊れたら 2 以上を返す（例: run の完了は `s=$(gh run view <ID> --json status -q .status) || exit 2; "
        "[ \"$s\" = completed ]`）。終了コードは 0 = 成立、124 = 期限切れ、2 = 条件が壊れている（使い方はスクリプトの "
        "docstring）。決まった時間だけ待つなら `sleep N` だけを起動する。" + tail +
        "待ちでない常駐の処理（`--watch` の dev watcher など）を background で起動したいときは、利用者に確認する。"
    )


def main(log_file: str) -> None:
    try:
        reason = deny_reason(json.loads(sys.stdin.read()))
    except Exception as exc:  # 読めない payload は通し、利用者の state ディレクトリに記録する
        if log_file:
            try:
                path = Path(log_file)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "a", encoding="utf-8") as log:
                    log.write(f"wait_loop_gate: {type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}\n")
            except OSError:
                pass
        return
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}, ensure_ascii=False))
