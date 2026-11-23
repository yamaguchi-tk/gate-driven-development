from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from lib.constants import (
    _HOOK_INJECTION_PREFIXES,
    _PEER_MESSAGE_TEXT_PREFIX,
    _QUEUED_NON_PEER_ORIGIN_KINDS,
    PR_URL_RE,
)
from lib.errors import append_hook_error

# 起動応答は host が tool result の本文の先頭に書く。途中にある同じ文言は引用（fixture を読んだ
# Bash の出力や、それを引いた同期の subagent の回答）なので、起動応答とみなさない。
_LAUNCH_ACK_AGENT_ID_RE = re.compile(
    r"\A\s*Async agent launched successfully\.[\s\S]*?agentId:\s*(\S+)"
)
# background Bash の起動応答。shell の id は通知の <task-id> と TaskStop の task_id に出る。
_BACKGROUND_SHELL_ACK_RE = re.compile(r"Command running in background with ID: ([A-Za-z0-9_-]+)")
# <task-notification> の 1 ブロック（終わりかどうかは _ended_notifications が status で
# 決める）。閉じタグにも次の開始タグにも越えないので、終わっていないブロックが後ろの
# ブロックの <status> を拾わない。
_TASK_NOTIFICATION_RE = re.compile(
    r"<task-notification>(?P<body>(?:(?!</?task-notification>)[\s\S])*)"
)
# id と status はヘッダ（subagent や Monitor が書く本文より前）からだけ拾う。本文に
# id のタグだけを引用しても、まだ動いている dispatch を終わりにしないため。通知のブロックを
# 開始タグから丸ごと引用したときは、それも 1 つの通知として読む（この形は区別できない）。
_NOTIFICATION_BODY_START_RE = re.compile(r"<(?:summary|result|event)>")
_TASK_ID_RE = re.compile(r"<task-id>([^<]+)</task-id>")
_TOOL_USE_ID_RE = re.compile(r"<tool-use-id>([^<]+)</tool-use-id>")
_STATUS_RE = re.compile(r"<status>([^<]*)</status>")
# <status> を持つ通知は終わりとし、終わっていない status だけを除く（許可リストにすると、
# host が新しい終わりの status を出したときに completed だけを見ていたのと同じ取りこぼしが
# 起きる）。Monitor のイベント通知は <status> を持たず、終わりではない。
_NON_TERMINAL_STATUSES = frozenset({"in_progress", "running", "pending"})
# subagent が自分の background の処理を残したまま返ったときの通知。status は completed だが途中で、
# 同じ task-id で後にもう一度通知が来る。<note> は <summary> の後ろにあるので、ヘッダではなく
# 本文（<result>・<event>）より前の区間で探す。文言には省略記号の形もあるので接頭辞で照合する。
_INTERIM_NOTE_RE = re.compile(r"<note>\s*This agent stopped with background work of its own still running")
_NOTIFICATION_RESULT_START_RE = re.compile(r"<(?:result|event)>")
# 孤児をまとめた通知が id の並びに足す集計用の id。task の id ではない。
_ORPHAN_SUMMARY_TASK_ID_PREFIX = "__orphan_summary__"


def _ended_notifications(text: str) -> list[tuple[str, str | None, str]]:
    """text 中の終わりの <task-notification> から (task_id, tool_use_id, status) を集める。"""
    found: list[tuple[str, str | None, str]] = []
    for block in _TASK_NOTIFICATION_RE.finditer(text):
        header = _NOTIFICATION_BODY_START_RE.split(block.group("body"), maxsplit=1)[0]
        status = _STATUS_RE.search(header)
        if not status or status.group(1).strip() in _NON_TERMINAL_STATUSES:
            continue
        if _INTERIM_NOTE_RE.search(_NOTIFICATION_RESULT_START_RE.split(block.group("body"), maxsplit=1)[0]):
            continue
        tool_use = _TOOL_USE_ID_RE.search(header)
        tool_use_id = tool_use.group(1) if tool_use else None
        for task_id in _TASK_ID_RE.findall(header):
            if not task_id.startswith(_ORPHAN_SUMMARY_TASK_ID_PREFIX):
                found.append((task_id, tool_use_id, status.group(1).strip()))
    return found


def _accumulate_notifications(result: "ParsedTranscript", text: str) -> None:
    for task_id, tool_use_id, status in _ended_notifications(text):
        result.task_notifications.append((task_id, tool_use_id))
        result.resumed_agents.pop(task_id, None)
        if status == "completed":
            result.completed_notifications.append((task_id, tool_use_id))


# TaskStop のエラーのうち、host が「その task は動いていない」と答える決まった文面（許可リスト）。
# No task found は、今のプロセスの task の一覧に無い id（終わった task、前のプロセスで起動した task）に返り、
# is not running は、一覧にあって終わった task に返る。どちらも「今は動いていない」の意味で、場面は問わない。
# id は _not_running_id の比較で、input の task_id・shell_id のどれかと全体が等しいときだけ当てる（前方一致で別の task を外さない）。
# 2 本目の否定先読みは running の後ろにあり、running に英数字・_・- が続く文面（is not runnings など）を外す。
_TASK_STOP_NOT_RUNNING_RES = (
    re.compile(r"\A(?:<tool_use_error>)?No task found with ID: ([A-Za-z0-9_-]+)"),
    re.compile(r"\A(?:<tool_use_error>)?Task ([A-Za-z0-9_-]+) is not running(?![A-Za-z0-9_-])"),
)


def _not_running_id(text: str, targets: tuple[str, ...]) -> str | None:
    """is_error の TaskStop の本文が、targets のどれかは動いていないという host の決まった文面なら、その id を返す。"""
    stripped = text.strip()
    for r in _TASK_STOP_NOT_RUNNING_RES:
        m = r.match(stripped)
        if m is not None and m.group(1) in targets:
            return m.group(1)
    return None


def _stopped_id(texts: list[str], targets: tuple[str, ...]) -> str | None:
    """TaskStop の成功結果の text block（JSON）ごとに task_id・shell_id を読み、targets（input の id）と同じものを返す。
    input と違う id・読めない本文・targets が空なら None（待ちに残す側に倒す）。"""
    for text in texts:
        try:
            payload = json.loads(text)
        except (ValueError, RecursionError):
            continue
        if isinstance(payload, dict):
            for key in ("task_id", "shell_id"):
                if payload.get(key) in targets:
                    return payload[key]
    return None


def _block_text(source: object, key: str = "text") -> str:
    """dict の text 相当フィールドを **文字列に限って**取り出す。

    host によっては text block の `text` が JSON `null` / 数値で届く。素の
    `block.get("text", "")` を `.strip()` / 正規表現に渡すと `AttributeError` /
    `TypeError` になり、transcript を読む hook 全体が落ちる（最上位・`message` の
    malformed 値と同型の防御漏れ。PR #31 レビュー Finding A / L）。非文字列は
    「本文なし」として読み飛ばす。
    """
    if not isinstance(source, dict):
        return ""
    value = source.get(key)
    return value if isinstance(value, str) else ""


@dataclass
class ToolLaunch:
    """assistant が起動した Agent・Task・Bash の tool_use（transcript 上の順）。"""
    tool_use_id: str
    name: str
    subagent_type: str
    command: str
    run_in_background: bool
    timestamp: object  # record の timestamp（読めるかは使う側が確かめる）


@dataclass
class ParsedTranscript:
    last_assistant_text: str = ""
    last_user_text: str = ""
    last_tool_result_text: str = ""
    all_task_agent_ids: set[str] = field(default_factory=set)
    all_tool_result_ids: set[str] = field(default_factory=set)
    dispatch_agent_ids: dict[str, str] = field(default_factory=dict)
    task_notifications: list[tuple[str, str | None]] = field(default_factory=list)
    # task_notifications のうち、status が completed のもの（成功で終わった background の dispatch）
    completed_notifications: list[tuple[str, str | None]] = field(default_factory=list)
    # is_error の tool_result の tool_use_id（all_tool_result_ids にも入る）
    error_tool_result_ids: set[str] = field(default_factory=set)
    launches: list[ToolLaunch] = field(default_factory=list)
    # background で起動できた Bash の tool_use_id → shell の id（is_error の結果は入れない）
    background_shell_ids: dict[str, str] = field(default_factory=dict)
    # TaskStop の tool_use_id → input の task_id と shell_id（host の schema の古い名前）のうち空でない str
    # （結果を読むまで、待ちからは外さない）
    task_stop_inputs: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # _TASK_STOP_NOT_RUNNING_RES のエラーで、host が動いていないと答えた id。成功の結果は、本文の JSON に
    # input の id が書かれていれば task_notifications に入れて外す（_stopped_id）。拒否・未知の文面・結果なしは入れない
    task_stop_targets: set[str] = field(default_factory=set)
    # 止めた相手（input）があるのに待ちから外さなかった TaskStop の結果（tool_use_id, 本文の先頭）。
    # 未知の文面のエラーと、本文の JSON に止めた相手の id が無い成功。host の形の変化に気づくための記録で、判定には使わない
    unaccepted_task_stops: list[tuple[str, str]] = field(default_factory=list)
    # SendMessage で再開した agentId → 再開の結果の record の timestamp。行の順に読み、再開の後に同じ id の
    # 終わりの通知か、host が動いていないと答えた TaskStop の結果が来たら消す
    resumed_agents: dict[str, object] = field(default_factory=dict)
    # 例外で読み飛ばした block・行（parse_transcript が project_root に記録する）
    skipped: list[str] = field(default_factory=list)
    # 人間の発話と record の timestamp。origin.kind が human の type:user 行で置き直し、turn の途中に
    # queued で届いた human の本文を後ろに足す。ほかの行（host の注入など）では変えない。
    # マージの合図の判定だけが読む（last_user_text と継続判定は変えない）
    human_utterances: list[tuple[str, object]] = field(default_factory=list)
    # origin.kind が human の行が 1 行でもあったか（無ければ origin を書かない版として last_user_text を読む）
    human_origin_seen: bool = False
    # assistant の本文に PR の URL が初めて出た record の timestamp
    pr_url_first_seen: dict[str, object] = field(default_factory=dict)


def _str_field(source: object, key: str) -> str:
    value = source.get(key) if isinstance(source, dict) else None
    return value if isinstance(value, str) else ""


def _accumulate_assistant_block(result: ParsedTranscript, block: object, timestamp: object = None) -> None:
    if not isinstance(block, dict):
        return
    if block.get("type") == "text":
        t = _block_text(block)
        if t:
            result.last_assistant_text = t
            for url in PR_URL_RE.findall(t):
                result.pr_url_first_seen.setdefault(url, timestamp)
    elif block.get("type") == "tool_use":
        tid = block.get("id", "")
        name = block.get("name", "")
        if tid and name in {"Task", "Agent"}:
            result.all_task_agent_ids.add(tid)
        elif isinstance(tid, str) and tid and name == "TaskStop":
            inp = block.get("input")
            targets = tuple(t for key in ("task_id", "shell_id") if (t := _str_field(inp, key)))
            if targets:
                result.task_stop_inputs[tid] = targets
        if isinstance(tid, str) and tid and name in {"Task", "Agent", "Bash"}:
            inp = block.get("input")
            result.launches.append(ToolLaunch(
                tool_use_id=tid,
                name=name,
                subagent_type=_str_field(inp, "subagent_type"),
                command=_str_field(inp, "command"),
                run_in_background=isinstance(inp, dict) and inp.get("run_in_background") is True,
                timestamp=timestamp,
            ))


def _accumulate_tool_result(result: ParsedTranscript, block: dict) -> None:
    tid = block.get("tool_use_id", "")
    c = block.get("content", "")
    texts: list[str] = []
    if isinstance(c, str):
        texts = [c]
    elif isinstance(c, list):
        for ci in c:
            if isinstance(ci, dict) and ci.get("type") == "text":
                t = _block_text(ci)
                if t:
                    texts.append(t)
    text = texts[-1] if texts else ""
    targets = result.task_stop_inputs.get(tid) if isinstance(tid, str) else None
    if targets:
        if block.get("is_error") is True:
            stopped_id = _not_running_id(text, targets)
            if stopped_id:
                result.task_stop_targets.add(stopped_id)
        else:
            stopped_id = _stopped_id(texts, targets)
            if stopped_id:
                result.task_notifications.append((stopped_id, None))
        if stopped_id:
            result.resumed_agents.pop(stopped_id, None)
        else:
            result.unaccepted_task_stops.append((tid, text.strip()[:200]))
    if isinstance(tid, str) and tid and block.get("is_error") is not True:
        shell = _BACKGROUND_SHELL_ACK_RE.search(text)
        if shell:
            result.background_shell_ids[tid] = shell.group(1)
    if isinstance(tid, str) and tid and block.get("is_error") is True:
        result.error_tool_result_ids.add(tid)
    if tid:
        m = _LAUNCH_ACK_AGENT_ID_RE.search(text)
        if m:
            result.dispatch_agent_ids[tid] = m.group(1)
        else:
            result.all_tool_result_ids.add(tid)
    if text:
        result.last_tool_result_text = text


def _user_block_text(result: ParsedTranscript, block: object) -> str:
    """user の record の 1 block を result に足し、本文の候補を返す（候補でなければ "")。

    text block は空白だけなら候補にしない。素の文字列は空白だけでも候補にする（空白だけの
    発話で last_user_text を上書きし、その前の継続意図で継続しないため）。
    """
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return ""
    if block.get("type") == "text":
        t = _block_text(block)
        return t if t.strip() else ""
    if block.get("type") == "tool_result":
        _accumulate_tool_result(result, block)
    return ""


def _queued_body(item: dict) -> object:
    """turn の途中に届いて queue から出た入力の本文（content / prompt の値）を返す。queued の行でなければ None。

    host は、main が動いている間に届いた通知を type:user の行ではなく、queue-operation の
    remove の content と attachment（type: queued_command）の prompt にだけ書くことがある。
    enqueue は読まない。queue に入っただけで配達待ちなので、ここで終わりとすると、loop state を
    消した後に通知が届く。この本文は last_user_text に使わない（人間の本文は human_utterances に入れる）。
    """
    if item.get("type") == "queue-operation" and item.get("operation") == "remove":
        return item.get("content")
    attachment = item.get("attachment")
    if item.get("type") == "attachment" and _str_field(attachment, "type") == "queued_command":
        return attachment.get("prompt")
    return None


def _queued_text_blocks(body: object) -> object:
    """queued の本文のうち、素の文字列と text block だけを残す（許可リスト）。

    tool_result などほかの block は読まない。読むと、queued の本文だけで dispatch を終わりにし、
    last_tool_result_text（Stop hook が停止の目印を探す）を書き換える。
    """
    if not isinstance(body, list):
        return body
    return [b for b in body if isinstance(b, str) or (isinstance(b, dict) and b.get("type") == "text")]


def _user_texts(result: ParsedTranscript, content: object) -> list[str]:
    """user の record の content から本文の候補を集める。block ごとに例外を捕まえる。

    queued の本文も、`_queued_text_blocks` で素の文字列と text block に絞ってからここを通す。
    """
    texts: list[str] = []
    if isinstance(content, str):
        texts.append(content)
    elif isinstance(content, list):
        for block in content:
            try:
                texts.append(_user_block_text(result, block))
            except Exception as exc:
                result.skipped.append(repr(exc))
    return [t for t in texts if t]


def _accumulate_resume(result: ParsedTranscript, item: dict) -> None:
    """SendMessage の結果の行の、host が書く宣言フィールド（toolUseResult の success が true で、resumedAgentId が
    空でない str）から再開を記録する。本文（"Resuming agent" など）は読まない。例外は捕まえて、同じ行のほかの
    block は読む。"""
    try:
        tur = item.get("toolUseResult")
        agent_id = tur.get("resumedAgentId") if isinstance(tur, dict) and tur.get("success") is True else None
        if isinstance(agent_id, str) and agent_id:
            result.resumed_agents.pop(agent_id, None)
            result.resumed_agents[agent_id] = item.get("timestamp")
    except Exception as exc:
        result.skipped.append(repr(exc))


def _accumulate_line(result: ParsedTranscript, raw_line: str) -> None:
    """transcript の 1 行を result に足す。読めない行・dict でない行は何もしない。

    content の block は 1 つずつ例外を捕まえる。1 つの block の中身が変（文字列でない
    id・name など）でも、同じ record のほかの block（人間の発話・起動応答・通知）は読む。
    record ごと捨てると、last_user_text が古い継続意図のまま残る。
    """
    if not raw_line.strip():
        return
    try:
        item = json.loads(raw_line)
    except json.JSONDecodeError:
        return
    # 妥当な JSON でも最上位が dict とは限らない（`null` / 配列 / 文字列の行）。
    # `item.get(...)` は AttributeError になり、この parser を呼ぶ hook 全体が
    # 落ちるため、dict 以外の行は decode 失敗と同じく読み飛ばす。
    if not isinstance(item, dict):
        return

    item_type = item.get("type")
    queued = _queued_body(item)
    if queued is not None:
        texts = _user_texts(result, _queued_text_blocks(queued))
        for t in texts:
            _accumulate_notifications(result, t)
        attachment = item.get("attachment")
        origin = attachment.get("origin") if isinstance(attachment, dict) else None
        if texts and _str_field(origin, "kind") == "human":
            if not any(texts[-1].strip().startswith(p) for p in _HOOK_INJECTION_PREFIXES):
                result.human_utterances.append((texts[-1], item.get("timestamp")))
                result.human_origin_seen = True
        return
    message = item.get("message")
    content = message.get("content", []) if isinstance(message, dict) else []

    if item_type == "assistant":
        if isinstance(content, list):
            for block in content:
                try:
                    _accumulate_assistant_block(result, block, item.get("timestamp"))
                except Exception as exc:
                    result.skipped.append(repr(exc))

    elif item_type == "user":
        _accumulate_resume(result, item)
        texts = _user_texts(result, content)
        for t in texts:
            _accumulate_notifications(result, t)
        if texts:
            # last_user_text には最後の本文の候補を使い、peer の印は全 block で探す。
            candidate = texts[-1]
            peer_marker_found = any(t.strip().startswith(_PEER_MESSAGE_TEXT_PREFIX) for t in texts)
            ts = candidate.strip()
            origin = item.get("origin")
            # `isMeta` 単独は peer 信号として使わない（PR #31 レビュー是正、独立
            # レビューで実 transcript を検証: skill 起動時のプリアンブル
            # （`Base directory for this skill: ...`）・`Stop hook feedback:`・
            # `<local-command-caveat>` / `<system-reminder>` 等、host が peer と
            # 無関係に付けたもの（false positive）が、isMeta:true の記録の
            # 大半を占めた。genuine な peer message は origin.kind=="peer" と
            # text prefix を必ず併せ持つ（`PEER_RECORD` fixture 参照）ため、
            # isMeta を外しても検出漏れにならない。
            #
            # peer marker の判定は `peer_marker_found`（record 内の全 text block を
            # 独立に走査した結果）を使う。`candidate`（`last_user_text` に使う最後の
            # 非空 block）だけを見ていたときは、複数 block の record で peer marker が
            # 先頭 block にあり末尾 block が無害な文（例: manual-merge trigger の
            # `merged`）だと、その無害な文が peer 判定を経ずに `last_user_text` へ
            # 採用されてしまった。`gdd_stop_hook.py` は peer guard より前段で
            # `last_user_text` を読む箇所（`maybe_block_incomplete_post_merge_continuation()`
            # 等）があるため、peer が末尾 block に無害語を混ぜるだけで peer guard を
            # 迂回して先行処理を起動できた（Copilot レビュー是正、独立レビュー Finding F-8
            # と同根）。
            is_peer_origin = (isinstance(origin, dict) and origin.get("kind") == "peer") or peer_marker_found
            if not any(ts.startswith(p) for p in _HOOK_INJECTION_PREFIXES) and not is_peer_origin:
                result.last_user_text = candidate
                if _str_field(origin, "kind") == "human":
                    result.human_utterances = [(candidate, item.get("timestamp"))]
                    result.human_origin_seen = True


def parse_transcript(path: Path, project_root: Path | None = None) -> ParsedTranscript:
    """Single-pass transcript parser.

    Accumulates last_assistant_text, last_user_text, last_tool_result_text,
    all_task_agent_ids (every Task/Agent tool_use id ever dispatched, across
    all assistant turns), and all_tool_result_ids (accumulated across all
    user turns, excluding tool_results recognized as a background-agent
    launch acknowledgement). A sync dispatch is in-flight until its id
    appears in all_tool_result_ids, no matter how many text-only turns pass
    in between.

    dispatch_agent_ids maps a dispatch's own tool_use_id to the background
    agentId recorded in its launch-ack tool_result (see
    _LAUNCH_ACK_AGENT_ID_RE), for dispatches that are async rather than
    resolved synchronously. task_notifications collects (task_id,
    tool_use_id) pairs for every background task that has ended: each
    <task-id> of an ended <task-notification> block (defined below), plus
    the input id of a successful TaskStop whose JSON task_id or shell_id
    names it (the killed notification may arrive later). These, and task_stop_targets (the id
    in a fixed host error text of _TASK_STOP_NOT_RUNNING_RES, only when it
    equals the input task_id or shell_id of that TaskStop), are
    matched against dispatch_agent_ids in subagent_in_flight_from_parsed to
    resolve background dispatches via hybrid A (tool_use_id match) or
    hybrid B (agentId/task_id match). A notification has ended when its
    header has a <status> other than in_progress / running / pending (see
    _ended_notifications); every text block of a user record is read, as
    is a notification that left the queue mid-turn (see _queued_body), and
    an orphan summary block lists several ids. A notification block ends at
    the next <task-notification> or </task-notification> tag, so a block that
    has not ended (e.g. a Monitor event without <status>) cannot borrow a
    later sibling block's status.

    A content block or a line that raises is skipped on its own (the other
    blocks of the same record are still read). When project_root is given,
    the count of those skipped by an exception and the first exception are
    logged once to hook-errors (a line that is not JSON or not a dict is
    skipped without counting). The log is written on every call, so a
    transcript that keeps such a block adds one entry per Stop.

    Reads with `errors="replace"` and returns an empty result on `OSError`
    (PR #31 独立レビュー Finding F-5): a strict `encoding="utf-8"` read raises
    `UnicodeDecodeError` on a single malformed byte anywhere in the
    transcript, which is not an `OSError` subclass and was previously
    uncaught here — crashing this hook's process entirely and disabling
    every check downstream of it (peer-turn / write-once / secrets), not
    just the transcript-derived ones. Same sibling fix already applied in
    `hooks/scripts/lib/detect-steering.sh:gdd_extract_route_in_progress`.

    Splits on a literal `"\n"` (JSONL's own record separator), not
    `str.splitlines()` (PR #31 独立レビュー Finding F-5 再検証時の Finding 2):
    `splitlines()` also breaks on U+2028/U+2029/U+0085/U+000B/U+000C/
    U+001C-1E, none of which a JSON encoder is required to escape (Node's
    `JSON.stringify`, which writes Claude Code's JSONL, leaves U+2028/U+2029
    raw). A peer record can embed one of these inside its own text value to
    split itself into two fragments that both fail `json.loads()` and get
    silently skipped, hiding the peer record from detection entirely.
    """
    result = ParsedTranscript()
    try:
        raw_text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return result
    for raw_line in raw_text.split("\n"):
        # 行として読めない（桁の多い整数、再帰の上限を超える入れ子など）ときは、その行だけを
        # 読み飛ばす。block の中身が変なときは _accumulate_line が block 単位で読み飛ばす。
        try:
            _accumulate_line(result, raw_line)
        except Exception as exc:
            result.skipped.append(repr(exc))
    if result.skipped and project_root is not None:
        append_hook_error(
            project_root, "parse_transcript",
            f"{len(result.skipped)} 個の block・行を読み飛ばした（最初: {result.skipped[0]}）",
        )
    return result


def _is_same_session_origin(origin: object) -> bool:
    """同じ session の task が返した行（subagent の hand-back・SendMessage）の origin かを返す。

    host はこの行にも kind "peer" を付けるが、送り手の task を origin.senderTaskId（host が書く
    宣言フィールド）に書く。別セッションの行はこのフィールドを持たないので、空でない str のときだけ
    同じ session とする。本文（peer の prefix など）は読まない。
    """
    if not isinstance(origin, dict) or origin.get("kind") != "peer":
        return False
    sender = origin.get("senderTaskId")
    return isinstance(sender, str) and sender != ""


def _queued_line_is_peer(item: dict) -> bool | None:
    """queued_command の attachment の行が peer 由来かを返す。その行でなければ None。

    attachment.origin.kind（host が書く宣言フィールド）で決め、本文は読まない。origin が無い行と
    _QUEUED_NON_PEER_ORIGIN_KINDS の kind は peer でない。ほかの値（peer・未知の kind・dict でない
    origin・str でない kind）は peer とする（判定できないときは止める側）。同じ session の task が
    返した行（`_is_same_session_origin`）は peer でない。
    """
    attachment = item.get("attachment")
    if item.get("type") != "attachment" or _str_field(attachment, "type") != "queued_command":
        return None
    if "origin" not in attachment:
        return False
    origin = attachment["origin"]
    if _is_same_session_origin(origin):
        return False
    kind = origin.get("kind") if isinstance(origin, dict) else None
    return not (isinstance(kind, str) and kind in _QUEUED_NON_PEER_ORIGIN_KINDS)


def last_user_turn_is_peer(path: Path, include_queued: bool = False) -> bool:
    """直近の *実会話ターン*（tool_result のみの record と
    _HOOK_INJECTION_PREFIXES に一致する record を除いた、直近の
    type:"user" record）が peer 由来（origin.kind=="peer" または
    peer message の text prefix 一致）かどうかを返す。tool 呼び出しを
    何回挟んでも判定は維持され、次に人間本人が実際に発話するまで peer 状態が
    続く。

    `_HOOK_INJECTION_PREFIXES` には `<task-notification>`（バックグラウンド
    Agent の完了通知。host が `type:"user"` の text record として注入する。turn の
    途中に届いた通知は queued の行〔`_queued_body`〕にだけ残り、この関数は既定では読まない）も
    含まれる。含めないと、peer message の直後に無関係な Agent が完了しただけで
    peer 状態が解除され、承認・中止 write の境界を人間の発話なしに迂回できる。

    `isMeta` は単独の peer 信号として**使わない**（PR #31 レビュー是正）。
    独立レビューで実 transcript を検証した結果、Claude Code は
    skill 起動時のプリアンブル（`Base directory for this skill: ...`）・
    `Stop hook feedback:`・`<local-command-caveat>` / `<system-reminder>` 等、
    peer と無関係な host 注入の多くにも `isMeta: true` を付けており、
    isMeta:true の記録の大半がこの false positive だった。genuine な peer message は
    `origin.kind=="peer"` と text prefix を必ず併せ持つ（`PEER_RECORD`
    fixture が実測形状）ため、isMeta を外しても検出漏れにならない。

    `errors="replace"` で読む（PR #31 独立レビュー Finding F-5、`parse_transcript()`
    と同じ理由）: 厳格 `utf-8` decode は不正バイト 1 つで `UnicodeDecodeError`
    になり、`except OSError` では拾えず本 hook プロセスごと落ちる。

    JSONL の record 区切りである文字どおりの `"\n"` で分割する（`splitlines()`
    ではない。`parse_transcript()` と同じ理由 = Finding 2 再是正）:
    `splitlines()` は U+2028 等でも分割し、peer 自身が record 内にこれを
    埋め込むと record が 2 断片に割れて JSON decode に失敗し、peer 判定を
    完全に迂回できる。

    include_queued=True（steering write guard だけが使う）のときは、turn の途中に届いた
    queued_command の attachment の行も読む（判定は `_queued_line_is_peer`）。peer の行なら True、
    peer でない行は読み飛ばす（人間の発話としても数えず、peer 状態を解除しない）。既定の False では
    queued の行を読まない。Stop hook と wait watchdog は peer のとき検査を飛ばすので、ここを広げると
    検査を飛ばす場面が増える。
    """
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return False
    for raw_line in reversed(lines):
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        # parse_transcript と同じ理由で dict 以外の最上位値を読み飛ばす（AttributeError
        # で peer 判定を呼ぶ write hook 全体が落ちるのを防ぐ）。
        if not isinstance(item, dict):
            continue
        if include_queued:
            queued_peer = _queued_line_is_peer(item)
            if queued_peer:
                return True
        if item.get("type") != "user":
            continue
        # 同じ session の task が返した行は、本文に peer の prefix があっても peer にも人間の発話にも
        # 数えず読み飛ばす（peer 状態も解除しない）。
        if _is_same_session_origin(item.get("origin")):
            continue
        message = item.get("message")
        content = message.get("content", []) if isinstance(message, dict) else []
        text = ""
        peer_marker_found = False
        if isinstance(content, str):
            text = content
            peer_marker_found = content.strip().startswith(_PEER_MESSAGE_TEXT_PREFIX)
        elif isinstance(content, list):
            # `text`（injection-prefix skip / 空判定用）は最後の非空 block を採用し
            # `parse_transcript()` の candidate 選定と揃える。だが peer marker の
            # 検出は**全 block を独立に走査**する（`break` しない）。「1 block だけ
            # 選んで peer 判定する」設計は、選ぶ基準を最初にしても最後にしても
            # 「marker が選ばれなかった側の block にある」ケースを見落とす鏡像の
            # 非対称を生む（旧実装は最初の block で `break` しており F-8 として
            # 是正したが、その修正が単に非対称を最後の block 側へ移しただけだった
            # ことが独立レビューの再検証で判明。PR #31 独立レビュー Finding F-8
            # 再是正）。fail-closed 側に倒すため、いずれかの block が marker を
            # 持てば record 全体を peer とみなす。
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = _block_text(block)
                    if t.strip():
                        text = t
                        if t.strip().startswith(_PEER_MESSAGE_TEXT_PREFIX):
                            peer_marker_found = True
                elif isinstance(block, str) and block.strip():
                    # `parse_transcript()` の bare str block 対応と揃える
                    # （独立レビュー再検証: この分岐が無いと、bare str block しか
                    # 持たない record で `text` が空のまま残り、後段の
                    # `if not text.strip(): continue` で読み飛ばされて古い record
                    # まで遡ってしまう）。
                    text = block
                    if block.strip().startswith(_PEER_MESSAGE_TEXT_PREFIX):
                        peer_marker_found = True
        if not text.strip():
            continue
        stripped = text.strip()
        origin = item.get("origin")
        is_peer = (isinstance(origin, dict) and origin.get("kind") == "peer") or peer_marker_found
        if is_peer:
            return True
        if any(stripped.startswith(p) for p in _HOOK_INJECTION_PREFIXES):
            continue
        return False
    return False


def last_assistant_text(path: Path) -> str:
    return parse_transcript(path).last_assistant_text


def last_user_text(path: Path) -> str:
    return parse_transcript(path).last_user_text


def last_tool_result_text(path: Path) -> str:
    return parse_transcript(path).last_tool_result_text


def inflight_dispatch_ids(tv: ParsedTranscript) -> set[str]:
    """完了の信号がまだ無い Task/Agent の dispatch の tool_use_id を返す
    （判定は subagent_in_flight_from_parsed の docstring のとおり）。"""
    residual = tv.all_task_agent_ids - tv.all_tool_result_ids
    if not residual:
        return residual
    notified_tool_use_ids = {tid for _, tid in tv.task_notifications if tid}
    notified_task_ids = {task_id for task_id, _ in tv.task_notifications}
    for tid in list(residual):
        agent_id = tv.dispatch_agent_ids.get(tid)
        if agent_id is None:
            continue
        # TaskStop に host が動いていないと答えた agent は待たない（拒否・未知のエラー・結果なしは待つ）
        if tid in notified_tool_use_ids or agent_id in notified_task_ids or agent_id in tv.task_stop_targets:
            residual.discard(tid)
    return residual


def running_background_shell(tv: ParsedTranscript, launch: ToolLaunch, finished: set[str]) -> str | None:
    """background で起動を確かめられ、完了通知も、host が動いていないと答えた TaskStop の結果もまだの Bash なら shell の id を返す。"""
    shell_id = tv.background_shell_ids.get(launch.tool_use_id)
    if launch.name != "Bash" or not launch.run_in_background or shell_id is None:
        return None
    if launch.tool_use_id in finished or shell_id in finished or shell_id in tv.task_stop_targets:
        return None
    return shell_id


def running_background_agent(tv: ParsedTranscript, launch: ToolLaunch, inflight: set[str]) -> str | None:
    """起動応答の agentId があり、完了通知も、host が動いていないと答えた TaskStop の結果もまだの Agent/Task の dispatch なら agentId を返す。
    完了通知と TaskStop の判定は inflight（inflight_dispatch_ids の結果）が持つ。"""
    agent_id = tv.dispatch_agent_ids.get(launch.tool_use_id)
    if launch.name in {"Agent", "Task"} and launch.tool_use_id in inflight and agent_id is not None:
        return agent_id
    return None


def finished_task_ids(tv: ParsedTranscript) -> set[str]:
    """完了の通知が届いた tool_use_id と task-id。"""
    return {tid for _, tid in tv.task_notifications if tid} | {task_id for task_id, _ in tv.task_notifications}


def _launch_epoch(launch: ToolLaunch) -> float | None:
    return _timestamp_epoch(launch.timestamp)


def _timestamp_epoch(timestamp: object) -> float | None:
    if not isinstance(timestamp, str):
        return None
    try:
        at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return at.timestamp() if at.tzinfo is not None else None


def any_background_running(tv: ParsedTranscript, since: float, until: float) -> bool:
    """起動の時刻が since 以上 until 以下で、まだ終わっていない background の処理（Bash・Agent/Task）が
    1 つでもあるか。起動の時刻を読めないものは数えない。"""
    finished = finished_task_ids(tv)
    inflight = inflight_dispatch_ids(tv)
    return any(
        (at := _launch_epoch(launch)) is not None and since <= at <= until
        and (running_background_shell(tv, launch, finished) or running_background_agent(tv, launch, inflight))
        for launch in tv.launches
    )


def any_resumed_agent_running(tv: ParsedTranscript, since: float, until: float) -> bool:
    """再開の時刻が since 以上 until 以下で、再開の後に終わりの通知も、host が動いていないと答えた TaskStop の結果もまだの agent が 1 つでもあるか。
    再開の時刻を読めないものは数えない。"""
    return any(
        (at := _timestamp_epoch(ts)) is not None and since <= at <= until
        for ts in tv.resumed_agents.values()
    )


# 待ちとして数える background の Bash の形（許可リスト）。期限 timer の単独の `sleep <秒>` と、
# plugin の scripts/wait-until.py の起動（コマンドの先頭か、; & | の直後に、python3 か path つきで
# 書いたもの。前後に通知などのコマンドが付いてもよい）。cat・grep などで触れただけのものは数えない。
_WAIT_COMMAND_RES = (
    re.compile(r"\A\s*sleep\s+\d+\s*\Z"),
    re.compile(r"(?:\A|[;&|])\s*(?:python3?\s+)?[\"']?(?:\S*/)?wait-until\.py[\"']?(?=\s|\Z)"),
)


def any_background_wait_running(tv: ParsedTranscript, since: float, until: float) -> bool:
    """起動の時刻が since 以上 until 以下で、まだ終わっていない待ちの background の Bash
    （_WAIT_COMMAND_RES のどれかに当たるもの）が 1 つでもあるか。起動の時刻を読めないものは数えない。"""
    finished = finished_task_ids(tv)
    return any(
        any(r.search(launch.command) for r in _WAIT_COMMAND_RES)
        and (at := _launch_epoch(launch)) is not None and since <= at <= until
        and running_background_shell(tv, launch, finished)
        for launch in tv.launches
    )


def subagent_in_flight_from_parsed(tv: ParsedTranscript, project_root: Path | None = None) -> bool:
    """Return True if any Task/Agent dispatched anywhere in the transcript still has
    no matching completion signal. Uses a pre-parsed ParsedTranscript to avoid
    re-reading the file. Text-only turns in between (e.g. the model reporting
    "still waiting") do not clear this — only an observed tool_result (sync call),
    a matching ended <task-notification> (background dispatch), or a TaskStop
    result that names its agentId (a success whose JSON task_id or shell_id is the agentId,
    or a fixed host error text such as "No task found" whose id equals the input
    task_id or shell_id; a denial, an unknown error or no result yet keeps it in
    flight; matched by agentId only) does.

    Judgment order: (1) residual = all_task_agent_ids - all_tool_result_ids;
    (2) for each residual id with a recorded launch-ack agentId, check hybrid A
    (task-notification tool-use-id matches the dispatch's own tool_use_id) then
    hybrid B (task-notification task-id or a TaskStop target matches the
    recorded agentId); (3) a
    residual id with no recorded launch-ack agentId is a sync call miscategorized
    as pending — fall back to the plain residual verdict (exclusion rule, AC-E9-4).
    """
    try:
        return bool(inflight_dispatch_ids(tv))
    except SystemExit:
        raise
    except Exception as exc:
        if project_root is not None:
            append_hook_error(project_root, "subagent_in_flight", str(exc))
        return False


def subagent_in_flight(transcript_path: Path, project_root: Path | None = None) -> bool:
    """Return True if any Task/Agent dispatched in the transcript has no matching
    tool_result in any subsequent user block, even if later assistant turns were
    text-only.

    Prevents the continuation nudge from firing while the parent session is
    waiting for a subagent to return. Fail-open: any non-SystemExit exception
    is logged and returns False so the hook does not suppress legitimate nudges.
    """
    try:
        tv = parse_transcript(transcript_path, project_root)
        return subagent_in_flight_from_parsed(tv, project_root)
    except SystemExit:
        raise
    except Exception as exc:
        if project_root is not None:
            append_hook_error(project_root, "subagent_in_flight", str(exc))
        return False
