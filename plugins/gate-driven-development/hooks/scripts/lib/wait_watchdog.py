"""Stop hook の期限 watchdog: background の reviewer・gate-runner の待ちに上限を強制する。

main が待ちで idle の間は hook が発火しないので、main を起こすのは期限 timer（`sleep N` の
background Bash）である。この module は Stop のたびに次を確かめ、当たれば block する。

- 期限切れ: 実行中の対象 dispatch が、起動から上限を超えた（起動時刻が読めない・未来なら
  期限を測れないので、これも期限切れとする） → TaskStop で止めさせる
- 未武装: 実行中の対象 dispatch の期限を覆う timer（dispatch より後に起動を確かめられ、まだ
  終わっていない `sleep N`。満了が期限から期限 + TIMER_SLACK_SECONDS の間）が無い → 置かせる

また、background の dispatch（type を問わない）が動いている間は、Stop hook が loop state を消す
停止を、ほかの停止の検査より先に押し返す（state_clear_guard。停止理由は本文・tool result の marker、ポーリング上限での
昇格のどれで決まってもよい）。

正本の規定は references/subagent-dispatch.md § Reviewer Input and Time Budget。
"""
from __future__ import annotations

import json
import math
import re
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from lib.constants import ALLOWED_STOP_REASONS, STOP_PATTERN
from lib.errors import append_hook_error, hook_error_log_path
from lib.regular_file import read_regular_text
from lib.state_io import write_state
from lib.stop_block_ceiling import STOP_HOOK_MAX_CONSECUTIVE_BLOCKS, next_block_count
from lib.transcript import (
    ParsedTranscript,
    ToolLaunch,
    finished_task_ids,
    inflight_dispatch_ids,
    last_user_turn_is_peer,
    running_background_agent,
    running_background_shell,
)

# 起動から返るまでの上限（秒）。subagent_type の `:` より後ろで引く。
LIMITS = {
    "gdd-planning-reviewer": 1800,
    "gdd-security-reviewer": 1800,
    "gdd-completion-reviewer": 1800,
    "gdd-implementation-reviewer": 1200,
    "gdd-formal-gate-runner": 3600,
}
# 人間に渡す停止。watchdog は当てない（自走する pause と done には当てる）。
HANDOFF_STOP_REASONS = ALLOWED_STOP_REASONS - {"done", "external-review-waiting", "auth-waiting"}
# timer の満了は期限の後、この秒数までを認める（それより遅い timer では期限に起きない）。
TIMER_SLACK_SECONDS = 600
# 案内する timer は期限の少し後に満了させ、起きた Stop がそのまま期限切れに当たるようにする。
_TIMER_MARGIN_SECONDS = 60
_TIMER_RE = re.compile(r"[ \t]*sleep[ \t]+([1-9][0-9]{0,5})[ \t]*", re.ASCII)


def limit_kind(subagent_type: str) -> str:
    """LIMITS を引く名前（前後の空白と plugin の prefix を除く）。"""
    return subagent_type.strip().rsplit(":", 1)[-1]


def _epoch(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def _stop_reason(text: str) -> str | None:
    match = STOP_PATTERN.search(text or "")
    return match.group(1) if match and match.group(1) in ALLOWED_STOP_REASONS else None


def _hands_to_human(last_output: str) -> bool:
    # 本文の marker だけを読む。tool result（Read・Bash の出力や subagent の返り値）は、引用した
    # marker を含みうるので読まない（_check_stop_markers より狭く、止める側に倒す）。
    return _stop_reason(last_output) in HANDOFF_STOP_REASONS


def _running_timer_seconds(tv: ParsedTranscript, launch: ToolLaunch, finished: set[str]) -> int | None:
    """起動を確かめられ、まだ終わっていない `sleep N` の timer なら N を返す。"""
    if running_background_shell(tv, launch, finished) is None:
        return None
    m = _TIMER_RE.fullmatch(launch.command)
    return int(m.group(1)) if m else None


def _running_background_agent_ids(tv: ParsedTranscript, inflight: set[str]) -> list[str]:
    """起動応答の agentId があり、完了通知も、host が動いていないと答えた TaskStop の結果もまだの dispatch の agentId（type を問わない）。"""
    return [agent_id for launch in tv.launches if (agent_id := running_background_agent(tv, launch, inflight))]


# TaskStop が待ちから外れない結果で返ったときの出口（期限切れと loop state を消す停止の押し返しで共通）。
# 完全な marker は書かない（書式は references/stop-hook-structured-markers.md にある）。
_TASK_STOP_UNACCEPTED_EXIT = (
    "TaskStop の結果が、本文の JSON の task_id・shell_id が止めた id と同じ成功・No task found・is not running のどれでもなかったら"
    "（拒否など）、繰り返さず、loop state を保つ停止（gdd-stop の reason に clarification-needed を書く。marker の後に要る見出しを含めて、"
    "書式は references/stop-hook-structured-markers.md と references/output-format.md）で人に渡す。"
)


def record_unaccepted_task_stops(tv: ParsedTranscript, project_root: Path) -> None:
    """待ちから外さなかった TaskStop の結果を .gdd/hook-errors.log に、tool_use_id ごとに 1 回だけ書く。

    host が TaskStop の結果の形（エラーの文面・成功の本文）を変えたときに気づくための記録で、判定には使わない。
    log が読めないときは書く側に倒す（記録は gate ではない）。書けないときは何もしない（append_log_record）。
    本文の lone surrogate は置き換えて書く。log の JSON で escape される tool_use_id（host の id は英数字で、実例は無い）は
    照合に当たらず、Stop のたびに書き直す（hook は落ちない）。"""
    if not tv.unaccepted_task_stops:
        return
    try:
        log = read_regular_text(hook_error_log_path(project_root), errors="replace") or ""
    except OSError:
        log = ""
    for tool_use_id, text in tv.unaccepted_task_stops:
        key = f"tool_use_id={tool_use_id} "
        if key in log:
            continue
        text = text.encode("utf-8", "replace").decode("utf-8")
        message = f"{key}TaskStop の結果を待ちから外さなかった: {text}"
        append_hook_error(project_root, "task_stop_unaccepted", message)
        log += message + "\n"


def overdue_reason(tv: ParsedTranscript, last_output: str, now: float) -> str | None:
    """期限切れか未武装の対象 dispatch があれば、block の reason を返す。無ければ None。"""
    if _hands_to_human(last_output):
        return None
    inflight = inflight_dispatch_ids(tv)
    finished = finished_task_ids(tv)
    lines: list[str] = []
    overdue = False
    for index, launch in enumerate(tv.launches):
        kind = limit_kind(launch.subagent_type)
        limit = LIMITS.get(kind)
        agent_id = tv.dispatch_agent_ids.get(launch.tool_use_id)
        if (
            launch.name not in {"Agent", "Task"}
            or limit is None
            or launch.tool_use_id not in inflight  # TaskStop に動いていないと答えた後は inflight に無い
            or agent_id is None  # 起動応答の無いもの（同期の dispatch）は対象外
        ):
            continue
        start = _epoch(launch.timestamp)
        if start is None or start > now or now >= start + limit:
            elapsed = "起動時刻が読めず" if start is None or start > now else f"起動から {int((now - start) // 60)} 分で"
            lines.append(
                f"background の {kind}（agentId {agent_id}）は{elapsed}、上限 {limit // 60} 分を超えた"
                f"ものとして扱う。TaskStop（task_id: {agent_id}）で止め、"
                "references/subagent-dispatch.md § Reviewer Input and Time Budget の超過として扱う。"
            )
            overdue = True
            continue
        deadline = start + limit
        if not any(_covers(tv, timer, finished, deadline) for timer in tv.launches[index + 1:]):
            lines.append(
                f"background の {kind}（agentId {agent_id}）を待つ期限 timer が無い。"
                f"Bash の run_in_background: true で `sleep {math.ceil(deadline - now) + _TIMER_MARGIN_SECONDS}` を"
                "起動してから待つ（コマンドはこの形だけを timer と認める）。"
            )
    if not lines:
        return None
    if overdue:
        lines.append(_TASK_STOP_UNACCEPTED_EXIT)
    lines.append(
        "止めた後に人間へ渡して停止するなら、受け取った `<gdd-stop reason=\"...\">` を本文に書く"
        "（watchdog は本文の marker だけを読む）。"
    )
    return "GDD wait watchdog:\n" + "\n".join(f"- {line}" for line in lines)


def _covers(tv: ParsedTranscript, timer: ToolLaunch, finished: set[str], deadline: float) -> bool:
    seconds = _running_timer_seconds(tv, timer, finished)
    start = _epoch(timer.timestamp)
    if seconds is None or start is None:
        return False
    return deadline <= start + seconds <= deadline + TIMER_SLACK_SECONDS


def state_clear_reason(tv: ParsedTranscript, reason: str) -> str | None:
    """background の dispatch が動いていれば、loop state を消す停止（reason）を押し返す reason を返す。"""
    running = _running_background_agent_ids(tv, inflight_dispatch_ids(tv))
    if not running:
        return None
    return (
        f"GDD wait watchdog:\n- background の dispatch（agentId {', '.join(running)}）が動いている間に、"
        f"loop state を消す停止（reason={reason}）で止まろうとした。完了通知を待つなら、目印を書かずに"
        "turn を終える（gdd-stop を書かない）。本文に目印が無いのに止められたなら、最後の tool result（Read した文書など）の"
        "marker を拾っている。marker を含まない tool を 1 回呼んでから待つ。ここで止めるなら、先にその "
        f"dispatch を TaskStop で止めてから止まる。{_TASK_STOP_UNACCEPTED_EXIT}"
    )


def _block_if(
    compute: Callable[[], str | None],
    hook_input: dict,
    frontmatter: dict[str, str],
    prompt_body: str,
    state_path: Path,
    project_root: Path,
    transcript_path: Path | None,
) -> None:
    """compute が reason を返せば block を出して exit する。それ以外は何もせず戻る。

    判定が例外のとき、直近の実会話ターンが peer のとき（判定が例外のときも）、連続 block の
    上限を超えるとき、state に数を保存できないときは block しない。
    """
    try:
        reason = compute()
        if reason and transcript_path is not None and last_user_turn_is_peer(transcript_path):
            return
    except Exception as exc:
        append_hook_error(project_root, "wait_watchdog", repr(exc))
        return
    if not reason:
        return
    now = int(time.time())
    count = next_block_count(hook_input, frontmatter, now)
    if count > STOP_HOOK_MAX_CONSECUTIVE_BLOCKS:
        return
    updated = {**frontmatter, "consecutive_stop_hook_blocks": str(count),
               "consecutive_stop_hook_blocks_at": "0" if count == 0 else str(now)}
    try:
        write_state(state_path, updated, prompt_body)
    except Exception as exc:
        append_hook_error(project_root, "wait_watchdog", repr(exc))
        return
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    raise SystemExit(0)


def guard(
    hook_input: dict,
    tv: ParsedTranscript,
    last_output: str,
    frontmatter: dict[str, str],
    prompt_body: str,
    state_path: Path,
    project_root: Path,
    transcript_path: Path | None,
) -> None:
    """期限切れ・未武装なら block を出して exit する（frontmatter は変えない）。停止を通すかは後段
    （done guard・継続の判定・連続 block の上限）が決める。"""
    _block_if(lambda: overdue_reason(tv, last_output, time.time()),
              hook_input, frontmatter, prompt_body, state_path, project_root, transcript_path)


def state_clear_guard(
    hook_input: dict,
    tv: ParsedTranscript,
    frontmatter: dict[str, str],
    prompt_body: str,
    state_path: Path,
    project_root: Path,
    transcript_path: Path | None,
) -> Callable[[str], None]:
    """loop state を消す停止で、Stop hook がほかの検査より先に呼ぶ関数を返す（引数は実効の停止理由）。"""
    return lambda reason: _block_if(lambda: state_clear_reason(tv, reason),
                                    hook_input, frontmatter, prompt_body, state_path, project_root, transcript_path)
