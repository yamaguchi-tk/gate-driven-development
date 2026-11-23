"""transcript の行が人の発言かを決める許可リスト（依存なし。import しても sys.path を変えない）。

依頼の写し（`request_capture.py`）、Stop の検査（`request_diff.py`）、承認の書き込みの検査（`request_diff_approval.py`）が
同じ判定を読む。許可するのは `origin.kind == "human"` の user の行と queued_command の行と、origin がキー無し・null・人の dict の
打ったコマンドの行（isMeta でない `<command-name>`）・`toolUseResult.answers`（AskUserQuestion の答え）。形の崩れた行は人の発言にしない。

- `human_entry`: 写しの見出しと本文（AskUserQuestion は質問と答えを並べる）
- `human_said`: 補正の引用に照らす、人が打った・選んだ部分だけ（host が足す `<system-reminder>` と、main が書いた
  質問文は外す。空なら None）
"""
from __future__ import annotations

import re

REMINDER = re.compile(r"<system-reminder>[\s\S]*?</system-reminder>")
COMMAND = re.compile(r"\A\s*(?:<command-message>[^<]*</command-message>\s*)?<command-name>([^<]*)</command-name>")
COMMAND_ARGS = re.compile(r"<command-args>([\s\S]*?)</command-args>")


def user_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _classify(record: dict) -> tuple[str, str, str] | None:
    """(見出し, 写しの本文, 人が打った・選んだ部分)。人の発言でなければ None。"""
    origin = record.get("origin")
    human = isinstance(origin, dict) and origin.get("kind") == "human"
    if record.get("type") == "attachment":
        attachment = record.get("attachment")
        if not isinstance(attachment, dict):
            return None
        a_origin = attachment.get("origin")
        if attachment.get("type") == "queued_command" and isinstance(a_origin, dict) and a_origin.get("kind") == "human":
            text = user_text(attachment.get("prompt"))
            return "ユーザー（作業中に打った発言）", text, text
        return None
    if record.get("type") != "user" or record.get("isMeta") or record.get("isCompactSummary"):
        return None
    if origin is not None and not human:
        return None
    result = record.get("toolUseResult")
    answers = result.get("answers") if isinstance(result, dict) else None
    if isinstance(answers, dict) and answers:
        shown = "\n".join(f"質問: {q}\n選んだ答え: {a}" for q, a in answers.items())
        return "AskUserQuestion の答え", shown, "\n".join(str(a) for a in answers.values())
    message = record.get("message")
    text = user_text(message.get("content") if isinstance(message, dict) else None)
    command = COMMAND.match(text)
    if command:
        args = COMMAND_ARGS.search(text)
        typed = f"{command.group(1)} {args.group(1) if args else ''}".strip()
        return "ユーザー（打ったコマンド）", typed, typed
    if human:
        text = REMINDER.sub("", text)
        return "ユーザー", text, text
    return None


def human_entry(record: dict) -> tuple[str, str] | None:
    """許可リストに当たる行なら (見出し, 本文) を返す。"""
    found = _classify(record)
    return (found[0], found[1]) if found else None


def human_said(record: dict) -> str | None:
    """人が打った・選んだ部分。reminder を外して空なら None。"""
    found = _classify(record)
    said = REMINDER.sub("", found[2]).strip() if found else ""
    return said or None
