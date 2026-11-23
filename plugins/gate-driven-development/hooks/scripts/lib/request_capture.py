"""突き合わせ agent の起動のときに、main の transcript のユーザーの発言で request.md を作る。

runner が見るのは Template の `${ARGUMENTS}`（`/gdd-dev` の引数）だけで、main が Skill で起動すると、
そこには main が書いた文が入り、ユーザーの発言は runner に届かない（review-log/20261031-request-capture.notes.md）。
そこで Claude Code では、runner は request.md を作らず、引数の写しを request-notes.md に書く。request.md を
読む最初の consumer（`gdd-request-code-crosscheck`）の起動のときに、hook が transcript から request.md を作る。
起動は止めない。

- hook が書くのは、request.md がまだ無いときに新しく作るときだけ。既にある request.md（runner・main・人が
  書いたもの、前に hook が作ったもの）は書き換えない。作るときは、同じディレクトリの一時ファイルを
  link するので、既にあるファイルを上書きせず、途中で落ちても中途半端な request.md を残さない
- 写す範囲は、main の assistant の文で code の外の行頭にある最後の `<gdd-stop reason="done">`
  か `cancelled`（前のタスクの終わり）より後（無ければ session の開始）から、この steering を作った
  `/gdd-dev` の起動（打ったコマンドか、main の Skill）まで。作った起動は、state.md の `Started At`
  以前で最後の起動とする（再開を引数の語で見分けない）。起動の後から突き合わせまでの発言は、
  節の下に時刻つきで写す
- state.md の `Created In Session`（steering を作った runner が書く session の id）が payload の
  session_id と一致するときだけ写す。別の session で作った steering を、この session の別のタスクの
  起動と取り違えないため。写せないとき（transcript が無い、欄が無い・違う、`Started At` が読めない、作った
  起動か起動より前の発言が transcript に無い）は、写していないことと理由の見出しの request.md を作り（起動の
  後の発言があれば下に写す）、systemMessage でも知らせる。読み手はこの形を「依頼の原文なし」として止める側に
  扱う。例外で落ちたときは request.md を作らない（brainstorming の runner が同じ形で作る）
- 既にある request.md は読まない。state.md に `Created In Session` が無いとき（runner が書き漏らして
  request.md を作った形）だけ、systemMessage で知らせる
- 写す行は許可リストで選ぶ: `origin.kind == "human"` の user の行と queued_command の行、
  origin の無い打ったコマンドの行（isMeta でない `<command-name>`）、main の行の
  `toolUseResult.answers`（AskUserQuestion の答え）。各発言の前に、その前の発言の後の main の
  assistant の文を、ユーザーの発言ではないと分かる見出しで添える
- steering の書き込み検査が止める値は、同じ検出器で語に置き換える
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# state_fields は `from tasklist_parse import` を使うので、lib 自身も path に入れる。
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.secret_scanning import (  # noqa: E402
    find_aws_account_id,
    find_ellipsis,
    find_email,
    find_local_path,
    find_secret_marker,
    SENSITIVE_VALUE_RE,
)
from state_fields import state_field_value  # noqa: E402
from lib.human_reply import human_entry as _human_entry  # noqa: E402

BEGIN = "<!-- gdd-request-capture:begin -->"
END = "<!-- gdd-request-capture:end -->"
NOT_COPIED = "<!-- gdd-request-capture:not-copied -->"
CROSSCHECK = "gdd-request-code-crosscheck"
# 定義が見つからないときの代わりの経路（general-purpose に定義の本文を渡す）を見分ける見出し。
_CROSSCHECK_BODY_MARK = "## リスクの段（正本）"
_REQUEST_PATH = re.compile(r"(/[^\s`'\"<>()（）]*?/\.steering/[^/\s`'\"<>()（）]+/request\.md)(?![\w.])")
_DONE_LINE = re.compile(r'^\s*<gdd-stop reason="(?:done|cancelled)">')
# (検出器, 置き換える語)。steering の書き込み検査（validate-steering-write.py の DETECTORS）と同じ 6 種。
_REDACTORS = (
    (lambda line: find_email(line), "（email）"),
    (lambda line: find_local_path(line), "（ローカルパス）"),
    (lambda line: find_ellipsis(line, False), "（省略の記号）"),
    (lambda line: find_aws_account_id(line, False), "（アカウント ID）"),
    (lambda line: find_secret_marker(line), "（secret の目印）"),
    # 検査はキーの語だけを返すが、写すときは値まで伏せる（キーだけ置き換えると値が残る）。
    (lambda line: (m := SENSITIVE_VALUE_RE.search(line)) and m.group(0), "（伏せた値）"),
)


def _redact(text: str) -> str:
    lines = []
    for line in text.split("\n"):
        for _ in range(200):
            hit = next(((value, word) for finder, word in _REDACTORS if (value := finder(line))), None)
            if hit is None:
                break
            line = line.replace(hit[0], hit[1])
        lines.append(line)
    return "\n".join(lines)


def _quote(text: str) -> str:
    return "\n".join("> " + line if line else ">" for line in _redact(text.strip()).split("\n"))


def _assistant_text(record: dict) -> str:
    content = (record.get("message") or {}).get("content")
    if not isinstance(content, list):
        return ""
    return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text").strip()


def _skill_args(record: dict) -> list[str]:
    content = (record.get("message") or {}).get("content")
    out = []
    for block in content if isinstance(content, list) else []:
        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
            tool_input = block.get("input") or {}
            if str(tool_input.get("skill", "")).split(":")[-1] == "gdd-dev":
                out.append(str(tool_input.get("args", "")))
    return out


def _is_done(text: str) -> bool:
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and _DONE_LINE.match(line):
            return True
    return False


def _is_invocation(record: dict) -> bool:
    if record.get("type") == "assistant":
        return bool(_skill_args(record))
    entry = _human_entry(record)
    return bool(entry and entry[0] == "ユーザー（打ったコマンド）" and entry[1].split(" ")[0].lstrip("/").split(":")[-1] == "gdd-dev")


def _time(value: object) -> datetime | None:
    """ISO 8601 の時刻。時差の無いものと読めないものは None。"""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else None


def _render(records: list[dict]) -> list[str]:
    """発言ごとの小節（前の assistant の文を添える）を返す。"""
    parts: list[str] = []
    said: list[str] = []
    for record in records:
        if record.get("type") == "assistant":
            if text := _assistant_text(record):
                said.append(text)
            continue
        entry = _human_entry(record)
        if entry is None or not entry[1].strip():
            continue
        if said:
            parts.append(f"#### 前の発言の後の assistant の文（文脈。要件ではない）\n\n{_quote(chr(10).join(said))}")
            said = []
        stamp = f"（{record['timestamp']}）" if isinstance(record.get("timestamp"), str) else ""
        parts.append(f"#### {entry[0]}{stamp}\n\n{_quote(entry[1])}")
    return parts


def capture(transcript_path: str, started_at: datetime) -> tuple[str, str] | None:
    """transcript から (request.md の節, 起動の後の発言) を作る。作った起動が無ければ None。

    起動より前に写す発言が無ければ、節は空文字（起動の後の発言だけを返す）。"""
    records = []
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                record = json.loads(line)
            except Exception:
                continue
            if isinstance(record, dict) and not record.get("isSidechain"):
                records.append(record)
    start = 0
    for i, record in enumerate(records):
        if record.get("type") == "assistant" and _is_done(_assistant_text(record)):
            start = i + 1
    stop = None
    for i in range(len(records) - 1, start - 1, -1):
        if _is_invocation(records[i]) and (at := _time(records[i].get("timestamp"))) and at <= started_at:
            stop = i + 1
            break
    if stop is None:
        return None
    after = _render(records[stop:])
    below = "\n\n".join(after) + "\n" if any(p.startswith(("#### ユーザー", "#### AskUserQuestion")) for p in after) else ""
    parts = _render(records[start:stop])
    if not any(p.startswith(("#### ユーザー", "#### AskUserQuestion")) for p in parts):
        return "", below
    header = (
        "## ユーザーの発言（hook が transcript から写した。依頼の原文の正本）\n\n"
        "「ユーザー」「AskUserQuestion の答え」の小節が原文である。assistant の文は文脈で、"
        "ユーザーの発言が指したときだけ承認に数える。"
    )
    section = f"{BEGIN}\n{header}\n\n" + "\n\n".join(parts) + f"\n{END}\n"
    return section, below


def _is_crosscheck(tool_input: dict) -> bool:
    subagent_type = str(tool_input.get("subagent_type", "")).strip()
    if subagent_type.split(":")[-1] == CROSSCHECK:
        return True
    return subagent_type == "general-purpose" and _CROSSCHECK_BODY_MARK in str(tool_input.get("prompt", ""))


def _request_path(prompt: str) -> Path | None:
    found = set(_REQUEST_PATH.findall(prompt))
    if len(found) != 1:
        return None
    path = Path(found.pop())
    if path.parent.is_symlink() or not (path.parent / "state.md").is_file():
        return None
    return path


def _create(path: Path, text: str) -> None:
    """path がまだ無いときだけ作る（link は既にある名前に失敗する）。一時ファイルは必ず消す。"""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.link(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def _section(payload: dict, path: Path) -> tuple[str, str | None]:
    """(request.md に書く中身, 写さなかった理由) を返す。写さなかったときの中身は、写していない旨の下に置く行。"""
    transcript = payload.get("transcript_path")
    if not isinstance(transcript, str) or not os.path.isfile(transcript):
        return "", "transcript を読めない"
    state = (path.parent / "state.md").read_text(encoding="utf-8")
    created = state_field_value(state, "Created In Session")
    if not created:
        return "", "state.md に Created In Session が無い（steering を作った runner が書いていない）"
    session = payload.get("session_id")
    if not isinstance(session, str) or not session or created != session:
        return "", "state.md の Created In Session がこの session と違う（別の session で作った steering）"
    started_at = _time(state_field_value(state, "Started At"))
    if started_at is None:
        return "", "state.md の Started At を読めない"
    captured = capture(transcript, started_at)
    if captured is None:
        return "", "steering を作った /gdd-dev の起動が transcript に無い"
    section, below = captured
    if not section:
        return below, "起動より前に写すユーザーの発言が transcript に無い（起動の後の発言は下に写した）"
    return section + ("\n" + below if below else ""), None


def run(payload: dict) -> str | None:
    """突き合わせの起動で、まだ無い request.md を作る。写せなかったときは理由を返す。"""
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name") != "Agent" or not _is_crosscheck(tool_input):
        return None
    path = _request_path(str(tool_input.get("prompt", "")))
    if path is None:
        return None
    if os.path.lexists(path):
        # 読まず書き換えない。runner が Created In Session を書き漏らして request.md を作った形だけを知らせる。
        state = (path.parent / "state.md").read_text(encoding="utf-8")
        if payload.get("session_id") and not state_field_value(state, "Created In Session"):
            return "state.md に Created In Session が無く、request.md は runner が作ったもの（原文の正本ではない）"
        return None
    content, reason = _section(payload, path)
    section = content
    if reason:
        section = (
            f"{NOT_COPIED}\n## hook は依頼の原文を写していない（{reason}）\n\n"
            "初めの依頼の原文は無い。runner の写しは request-notes.md にあり、原文の正本ではない。"
            "この下の時刻つきの行は、hook か main が写したユーザーの発言である（`見直し` で始まる行は assistant の引用）。\n"
        ) + ("\n" + content if content else "")
    try:
        _create(path, section)
    except FileExistsError:
        return None
    return reason


def main() -> int:
    try:
        reason = run(json.loads(sys.stdin.read()))
    except Exception:
        return 0
    if reason:
        message = f"request-capture-hook: 依頼の原文を写していません（{reason}）。"
        print(json.dumps({"systemMessage": message}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
