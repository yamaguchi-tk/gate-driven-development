"""human check の判断ポイントの `依頼との差:` を見て、依頼から外れる点を承認として記録させない。

`Human Check Status` を approved にする Write・Edit（`validate-steering-write.py`）で、直前の提示（transcript の
最後の、HITL のマーカーを含む assistant の発言）を読み、次のどれかなら止める。

- 欄かタグに問題がある（`lib/request_diff_field.py` の `field_problem`。欄の形が読めない〔値が `なし` と
  `あり: <項目>` のどちらでもない〕・`なし` 以外の点がある・マーカーの直前にタグが無い・タグの `request-diff` が読めない）

ただし、提示の後に人の返事があり、その後の main の補正（`lib/request_diff_field.py` の `correction_problem`）が
使えるなら通す（Stop の hook が動かなかった・記録を書けなかったときに、人に同じ判断を答え直させない）。
前の提示と点の数は比べない（変えた点だけの再提示で外れた点が消えると通る。限界）。通した承認は、読む時期に数えるため
`request-diff-approval.log` に `allow`（補正で通したものは `allow-corrected`）として残す。値は書き手の自己申告で、正しさは見ない。マーカーのある提示が無ければ通す。transcript を読めなければ止める。
`transcript_path` の無い payload（他の runtime）は通す。Bash で承認を書くコマンドは、
`run-request-diff-approval-gate-hook.sh` が提示を読まずに Write・Edit へ付け替える。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# 呼び出し側が hooks/scripts を path に入れて `lib.request_diff_approval` として読む。validate-steering-write.py は
# 起動時に読んだ後で path を外すので、実行時に読む import は置かない。
from lib.hitl_lint_gate import HITL_MARKER  # noqa: E402
from lib.human_reply import human_said  # noqa: E402
from lib.request_diff_field import DECIDED_RE, _adjacent_tag, correction_problem, field_problem, unreadable_lines  # noqa: E402

CATEGORY = "request_diff_approval"
APPROVED_HEAD_RE = re.compile(r"approved(?![A-Za-z0-9_-])")
APPROVED_LINE_RE = re.compile(r"^(?:-\s+)?Human Check Status\s*[:=]\s*approved", re.MULTILINE)

DENY_MESSAGE = (
    "直前の human check の提示で、判断ポイントの `依頼との差` が `なし` でないか、欄かタグが読めません（{problem}）。"
    "ユーザーがこの確認に返事をした後なら、確認を出し直さず、欄とタグだけを直した補正を書いてから承認を書き直します。"
    "補正はマーカーを付けない発言で、最後の行に `<gdd-hitl-fields correction request-diff=\"none,none\">` "
    "（判断ポイントの順に、値はすべて `none`）を置き、同じタグに、提示の後のユーザーの返事の文を `decided=\"…\"` で引きます"
    "（1 行で、`\"` とこの欄の名前を含まない部分をそのまま引く）。補正の文にも、この欄の名前は欄の行だけに使います。"
    "依頼を狭める点（`あり:`・`differs`・読めない欄）は、返事がその点を名指しで選んだときだけ `none` にします。"
    "名指ししていなければ、確認全体ではなく、その点を受け入れるかだけを問います。"
    "ユーザーが名指しで選んでいない、依頼から外れる点は承認として記録せず、要件の変更の経路（`gdd-requirements-amendment`。"
    "計画の途中なら `planning_rework_required`）に送ってください。欄とタグの書き忘れなら、提示を出し直してください。"
    "マーカーの直前の行に `<gdd-hitl-fields ... request-diff=\"none,none\">` のように、判断ポイントの順に "
    "`none` か `differs` をカンマで並べ、本文には判断ポイントごとに 1 行の `- 依頼との差: なし` を置きます。"
    "推奨は依頼より狭くせず、依頼を狭める案は `採用しない案:` に、変わる AC を書いて並べます"
    "（`あり:` の点がある確認は、出した Stop で出し直しになります）。提示のほかの文（出し直しの理由の説明を含む）にはこの語を使わず、"
    "依頼の引用などが含んで止まったら、その部分を「…」で切ってください。確認の追記や回答にはマーカーを付けません。"
    "ユーザーが自分で狭めると決めた点は、その発言を `根拠` の行に引き、欄は `なし` にします。"
    "ユーザーの返事の前なら、同じ提示のまま承認の書き込みを繰り返さず、確認の全文を出し直してユーザーの返事を待ってください。"
)
UNREADABLE_TRANSCRIPT = "transcript を読めない"


class TranscriptUnreadable(Exception):
    """transcript を読めない（止める側に倒す）。"""


def _assistant_text(record: dict) -> str:
    message = record.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(b.get("text", "")) for b in content if isinstance(b, dict) and b.get("type") == "text"
    )


def last_marker_presentation(transcript_path: str) -> tuple[str, str, list[str], str] | None:
    """transcript の最後の、マーカーを含む assistant の発言の (uuid, 本文, その後の人の返事, 最後の補正の候補)。

    補正の候補は、提示の後に人の返事が 1 つ以上あってから書かれた、マーカーの無い assistant の発言のうち最後のもの
    （中身の判定は `correction_problem`）。読めなければ TranscriptUnreadable。"""
    found = None
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(record, dict) or record.get("isSidechain"):
                    continue
                if record.get("type") != "assistant":
                    reply = human_said(record) if found else None
                    if reply:
                        found[2].append(reply)
                    continue
                text = _assistant_text(record)
                if HITL_MARKER in text:
                    uuid = record.get("uuid")
                    found = [uuid if isinstance(uuid, str) else "", text, [], ""]
                elif found and found[2] and text.strip():
                    found[3] = text
    except (OSError, ValueError) as exc:
        raise TranscriptUnreadable(str(exc)) from exc
    return tuple(found) if found else None


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _log_path() -> Path:
    base = os.environ.get("GDD_HOOK_STATE_DIR") or str(Path.home() / ".claude" / ".gdd-hook-state")
    return Path(base) / "request-diff-approval.log"


def _append(record: dict) -> None:
    """記録を 1 行足す。書けなくても止めない。"""
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NONBLOCK", 0), 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (OSError, ValueError):
        pass


def _steering_key(path: str) -> str:
    try:
        return os.path.realpath(path)
    except (OSError, ValueError):
        return path


def _last_presentation(payload: dict) -> tuple[str, str, list[str], str] | None:
    raw = payload.get("transcript_path")
    if not isinstance(raw, str) or not raw:
        return None
    return last_marker_presentation(raw)


def approval_problem(payload: dict) -> tuple[str, str, str] | None:
    """承認の書き込みを止めるなら (理由, 提示の sha, deny の文)。通すなら None。"""
    try:
        found = _last_presentation(payload)
    except TranscriptUnreadable:
        return UNREADABLE_TRANSCRIPT, "", DENY_MESSAGE.format(problem=UNREADABLE_TRANSCRIPT)
    if found is None:
        return None
    _, presentation, replies, correction = found
    problem = field_problem(presentation)
    unusable = correction_problem(presentation, correction, replies) if replies else None
    if not problem or (replies and not unusable):
        return None
    message = DENY_MESSAGE.format(problem=problem)
    if correction:
        message += f"補正を使えない理由: {unusable}。"
    if problem == "欄の形が読めない":
        message += "読めなかった行: " + " / ".join(unreadable_lines(presentation))
    return problem, _sha(presentation), message


def record_deny(payload: dict, entry: str, problem: str, sha: str) -> None:
    """deny を 1 行残す（読む時期に、deny の件数と、その後に案が変わったかを数える）。"""
    _append({"session_id": str(payload.get("session_id", "")), "entry": entry, "problem": problem, "sha": sha})


def record_allow(payload: dict, steering: str) -> None:
    """guard が承認の書き込みを通したことを残す（読む時期に、通した承認と提示を数える）。提示が無い・読めなければ残さない。"""
    try:
        found = _last_presentation(payload)
    except TranscriptUnreadable:
        return
    if found:
        record = {"session_id": str(payload.get("session_id", "")), "entry": "allow",
                  "steering": _steering_key(steering), "uuid": found[0], "sha": _sha(found[1])}
        if field_problem(found[1]):  # 補正で通した（読む時期に、引用の短さで「OK」だけの引用を数える。人の発言は残さない）
            decided = DECIDED_RE.findall(_adjacent_tag(found[3]) or "")
            record.update(entry="allow-corrected", decided_chars=len(decided[0]) if decided else 0)
        _append(record)


def chunks_add_approval(chunks: list[str]) -> bool:
    """追加文字列に `Human Check Status: approved` の行があるか（書き込み後のテキストを作れないときに使う）。"""
    return bool(APPROVED_LINE_RE.search("\n".join(chunks).replace("`", "")))


def value_turns_approved(before: str | None, after: str | None) -> bool:
    return bool(APPROVED_HEAD_RE.match((after or "").strip())) and not APPROVED_HEAD_RE.match((before or "").strip())


def collect_violations(approvals: list[str], payload: dict) -> list[tuple[str, str]]:
    """`approvals` は、`Human Check Status` を approved に変える state.md のパス。呼び出し側
    （validate-steering-write.py）が、peer turn の検査と同じ道具（Edit の当て外れ・gate の reader）で作る。
    通したときの記録（`record_allow`）は、書き込み全体を通すと決めた呼び出し側が行う。
    """
    if approvals:
        found = approval_problem(payload)
        if found:
            problem, sha, message = found
            record_deny(payload, "steering-write", problem, sha)
            return [(CATEGORY, message)]
    return []
