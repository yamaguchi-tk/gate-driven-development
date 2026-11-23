"""human check の返事を受けたターンの Stop で、`記録の場所: なし` の行の印（` / 表示: 済み`）の付け忘れを知らせる。

印の規定は `references/human-check-template.md` § ズレ確認。一次表示に出した `記録の場所: なし` の行に本人が返事をしたら、
返事を受けた main が `requirements.md` の同じ行の末尾に印を足す。付け忘れると、その行は完了の報告に余分に載る
（`references/post-completion-pr-flow.md` Step 4）。この hook は止めずに知らせだけを出す（systemMessage）。

- 見るのは、最後の人の発言（`lib/human_reply.py` の許可リスト。cross-session の返事は数えない）の直前のターンの、
  最後のマーカー付きの発言（一次表示）だけ。その発言と人の発言の間に compaction があれば見ない（main が自分の一次表示を
  確かめられないときは足さない規定のため）。人の発言の後のターンで確認を出し直したら見ない（書き直した行は印を外す規定のため）
- 一次表示の `記録の場所: なし` の行を 1 行ずつ、bind された steering（無ければ最新の steering）の `requirements.md` の
  § ズレ確認 の行と突き合わせる（表の区切り・箇条の記号・`#`・空白・印を外して比べる）。一致して印の無い行と、
  一致する行が無い一次表示の行を数え、どちらかが 1 行以上なら知らせる。一次表示に出していない行は数えない
- 後で読むため、見た回ごとに行数だけを hook の state dir の `display-marker.log` に残す（行の本文は残さない）
- 例外・読めない入力では何も出さない（知らせだけの hook なので、止める側には倒さない）
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.hitl_lint_gate import HITL_MARKER  # noqa: E402
from lib.request_capture import _assistant_text, _human_entry  # noqa: E402
from lib.steering_candidate import latest_steering_candidate, usable_candidate  # noqa: E402
from lib.task_binding_resolve import resolve_bind  # noqa: E402

ROW_KEY = "記録の場所: なし"
MARK = "/ 表示: 済み"
SECTION = "### ズレ確認"
NOISE = re.compile(r"[\s|｜#\-*・]")
LOG_NAME = "display-marker.log"


def _records(transcript_path: str) -> list[dict]:
    records = []
    with open(transcript_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and not record.get("isSidechain"):
                records.append(record)
    return records


def _is_compaction(record: dict) -> bool:
    return (record.get("type") == "system" and record.get("subtype") == "compact_boundary") or bool(record.get("isCompactSummary"))


def reply_turn_display(records: list[dict]) -> str | None:
    """最後の人の発言が一次表示への返事で、そのターンが確認を出し直していなければ、その一次表示の文。"""
    humans = [i for i, r in enumerate(records) if _human_entry(r)]
    if not humans:
        return None
    last = humans[-1]
    if any(r.get("type") == "assistant" and HITL_MARKER in _assistant_text(r) for r in records[last + 1:]):
        return None
    start = humans[-2] + 1 if len(humans) > 1 else 0
    display = None
    for record in records[start:last]:
        if record.get("type") == "assistant":
            text = _assistant_text(record)
            if HITL_MARKER in text:
                display = text
        elif display is not None and _is_compaction(record):
            return None
    return display


def section_rows(text: str) -> list[str]:
    """`### ズレ確認` の節の、`記録の場所: なし` を含む行。"""
    rows, inside = [], False
    for line in text.splitlines():
        if line.startswith("#"):
            inside = line.strip() == SECTION
            continue
        if inside and ROW_KEY in line:
            rows.append(line)
    return rows


def row_key(line: str) -> str:
    return NOISE.sub("", line.replace(MARK, ""))


def compare(display: str, rows: list[str]) -> tuple[int, int, int]:
    """(一次表示の行数, 一致して印の無い行数, 一致する行が無い行数)。"""
    by_key = {}
    for row in rows:
        by_key.setdefault(row_key(row), []).append(row)
    shown = [line for line in display.splitlines() if ROW_KEY in line]
    unmarked = missing = 0
    for line in shown:
        found = by_key.get(row_key(line))
        if not found:
            missing += 1
        elif not any(MARK in row for row in found):
            unmarked += 1
    return len(shown), unmarked, missing


def _toplevel(start: Path) -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, check=True,
                             cwd=str(start), timeout=5).stdout
        top = os.fsdecode(out[:-1] if out.endswith(b"\n") else out)
        if top:
            return Path(top)
    except Exception:  # noqa: BLE001 - git が無い・worktree でないときは cwd のまま
        pass
    return start


def requirements_path(cwd: Path) -> Path | None:
    top = _toplevel(cwd)
    bind = resolve_bind(repo_root=top, cwd=top)
    if bind.status == "resolved" and bind.steering_dir is not None:
        found = usable_candidate(bind.steering_dir / "requirements.md", bind.steering_dir)
    else:
        found = latest_steering_candidate(top / ".steering", "requirements.md")
    return found[0] if found and found[1] else None


def _log(payload: dict, shown: int, unmarked: int, missing: int) -> None:
    base = os.environ.get("GDD_HOOK_STATE_DIR") or str(Path.home() / ".claude" / ".gdd-hook-state")
    try:
        path = Path(base) / LOG_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": str(payload.get("session_id", "")),
                "cwd": str(payload.get("cwd", "")),
                "shown": shown,
                "unmarked": unmarked,
                "missing": missing,
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass


def message(path: Path, unmarked: int, missing: int) -> str:
    parts = [f"human check の一次表示に出した `{ROW_KEY}` の行に本人が返事をしました。"]
    if unmarked:
        parts.append(
            f"そのうち {unmarked} 行は、`{path}` の § ズレ確認 の同じ行の末尾に ` {MARK}` がありません。"
            f"一次表示に出した行への本人の返事なら、`references/human-check-template.md` § ズレ確認 のとおり、"
            f"その行の末尾に ` {MARK}` を足してください。一次表示にその行があると確かめられないとき（compaction の後など）は"
            f"足さずに残します（その行は完了の報告に書かれます）。"
        )
    if missing:
        parts.append(f"一次表示の {missing} 行は、`{path}` の § ズレ確認 に同じ行が見つからないので、印を確かめられません。")
    parts.append("この知らせは停止を止めません。")
    return "".join(parts)


def run(payload: dict) -> dict | None:
    if payload.get("stop_hook_active"):
        return None
    transcript, cwd = payload.get("transcript_path"), payload.get("cwd")
    if not transcript or not cwd:
        return None
    try:
        records = _records(str(transcript))
    except OSError:
        return None
    display = reply_turn_display(records)
    if display is None:
        return None
    if ROW_KEY not in display:
        return None
    path = requirements_path(Path(str(cwd)))
    if path is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    shown, unmarked, missing = compare(display, section_rows(text))
    _log(payload, shown, unmarked, missing)
    return {"systemMessage": message(path, unmarked, missing)} if unmarked or missing else None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        output = run(payload)
    except Exception as exc:  # noqa: BLE001 - 知らせだけの hook なので停止を妨げない
        print(f"display-marker: {type(exc).__name__}", file=sys.stderr)
        return 0
    if output:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
