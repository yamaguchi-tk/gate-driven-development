#!/usr/bin/env python3
"""implementation-gating が steering から読む節を、行番号つきで 1 回に出す。

runner は Steps ごとに tasklist.md・state.md・handoff・worklog.md の別の節を
読み直していた（2026-10-02〜10-16 の実測で、1 回の gate で何度も。tasklist.md は
長く、その多くは Completed Tasks）。この script はその節だけを出す。
判定（approved / changes_requested）はしない。

出すもの:
  tasklist.md: 全節の索引（行の範囲）、冒頭（最初の `## ` より前。Agentic Worker Header）、
    Current Task・Pending Tasks・Implementation Reviewer Selection・Review Status・
    Execution Plan・Refactor Gate Status の各節の全文、Refactor Gate Status を含む行、
    Completed Tasks の task 行と、`was_valid: false` を持つ `[Review Calibration]` の entry
  state.md: Task Size・Route In Progress・Active Worktree Path
  `impl-gate-review: skip <task 名>` か `impl-gate-review: run（<理由>）` の固定行（SKILL.md Step 1e。
    正本: references/task-breakdown-steps.md § Judgment Change）
  worktree 直下の docs/learned-patterns.md（SKILL.md Step 5 の置き場。steering は <worktree>/.steering/<task>/）
  の Rejected Alternatives 節、worklog.md の末尾 20 行
  handoff/: `### State Machine Impact` の block（最も新しいファイル）と、
    implementation_gating.md（前回の gate の出力）の見出しと `判定:` の行

節は done guard と同じく `## <名前>` の前方一致で決め、一致した節は全部出す。
Current Task・Pending Tasks・Implementation Reviewer Selection の節が見つからない、
Current Task・Pending Tasks の task が done guard の数え方（tasklist_parse.open_task_names）
と合わない、tasklist.md が
読めない、fence が閉じていないときは、何も出さずに exit 1 で理由を stderr に書く
（「節が無い」を「task が無い」と読ませない。Pending Tasks を取りこぼすと、
残りの task があるのに completion へ進む）。runner はそのとき従来どおり自分で読む。

fence と task 行の受理は hooks/scripts/lib/tasklist_parse.py を使い、done guard
などと揃える。正本: skills/gdd-implementation-gating/SKILL.md § Steps。

Exit code:
  0: 出した
  1: 必須の節を特定できない（runner は自分で読む）
  2: usage error

Usage:
  impl-gate-context.py --steering-dir <.steering/<task>/>
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# collect-gdd-telemetry.py と同じく、hooks/scripts/lib を top-level module として読み、
# 読んだ直後に path を戻す（`from lib.X import` は scripts/lib の解決を壊す）。
_LIB_DIR = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from state_fields import state_field_value  # noqa: E402
    from tasklist_parse import (  # noqa: E402
        _scan_fences,
        classify_task_line,
        impl_gate_review,
        open_task_names,
        select_route_in_progress,
        task_name,
    )
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)

REQUIRED = ("Current Task", "Pending Tasks", "Implementation Reviewer Selection")
OPTIONAL = ("Review Status", "Execution Plan", "Refactor Gate Status")
WORKLOG_TAIL = 20
_H2_RE = re.compile(r"^## ")
_HEADING_RE = re.compile(r"^#{1,6} ")
_WAS_VALID_FALSE_RE = re.compile(r"was_valid\s*[:=]\s*false", re.IGNORECASE)


class ContextError(Exception):
    pass


def _sections(text: str) -> tuple[list[str], set[int], list[tuple[int, int]]]:
    """(全行, fence の内側の行, fence の外の `## ` 節の [(見出しの index, 終わりの次の index)])。"""
    lines, closed, open_at, _spans = _scan_fences(text)
    if open_at >= 0:
        raise ContextError(f"{open_at + 1} 行目の fence が閉じていない")
    starts = [i for i, line in enumerate(lines) if i not in closed and _H2_RE.match(line)]
    ends = starts[1:] + [len(lines)]
    return lines, closed, list(zip(starts, ends))


def _named(lines: list[str], spans: list[tuple[int, int]], name: str) -> list[tuple[int, int]]:
    # done guard（lib/done_guard.py）と同じく前方一致で節を決める。
    # `## Pending Tasks（再オープン）` も Pending Tasks の節に数える
    return [(start, end) for start, end in spans if lines[start].startswith(f"## {name}")]


def _check_open_tasks(text: str, lines: list[str], closed: set[int], open_spans: list[tuple[int, int]]) -> None:
    """出す Current Task・Pending Tasks の節の task 名が、done guard 側の数え方
    （tasklist_parse.open_task_names）と食い違えば止める。節の見出しの読み方が
    ずれて残りの task を落とす形を、fixture に無い見出しでも捕まえる。"""
    names: Counter[str] = Counter()
    for start, end in open_spans:
        for i in range(start + 1, end):
            line = lines[i]
            if i not in closed and line[:1] not in (" ", "\t") and (name := task_name(line.rstrip())):
                names[name] += 1
    if names != open_task_names(text):
        raise ContextError("Current Task・Pending Tasks の task が done guard の数え方と合わない")


def _numbered(lines: list[str], start: int, end: int) -> list[str]:
    return [f"{i + 1}\t{lines[i]}" for i in range(start, end)]


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _calibration_and_tasks(lines: list[str], start: int, end: int) -> list[str]:
    """task 行と、続きに `was_valid: false` を持つ `[Review Calibration]` の entry。"""
    out: list[str] = []
    i = start + 1
    while i < end:
        line = lines[i]
        if "[Review Calibration]" in line:
            indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < end and lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) > indent:
                j += 1
            if any(_WAS_VALID_FALSE_RE.search(lines[k]) for k in range(i, j)):
                out.extend(_numbered(lines, i, j))
            i = j
            continue
        if classify_task_line(line.strip()) == "task":
            out.append(f"{i + 1}\t{line}")
        i += 1
    return out


def _tasklist(path: Path) -> list[str]:
    text = _read(path)
    if text is None:
        raise ContextError(f"{path} を読めない")
    lines, closed, spans = _sections(text)
    for name in REQUIRED:
        if not _named(lines, spans, name):
            raise ContextError(f"tasklist.md に `## {name}` で始まる節が無い")
    _check_open_tasks(text, lines, closed, _named(lines, spans, "Current Task") + _named(lines, spans, "Pending Tasks"))
    out = [f"# tasklist.md（{len(lines)} 行）", "## 節の索引"]
    out.extend(f"{start + 1}〜{end}\t{lines[start]}" for start, end in spans)
    header_end = spans[0][0] if spans else len(lines)
    out.append(f"## 冒頭（1〜{header_end} 行。Agentic Worker Header など）")
    out.extend(_numbered(lines, 0, header_end))
    for name in REQUIRED + OPTIONAL:
        found = _named(lines, spans, name)
        if not found:
            out.append(f"## {name}: 節が無い")
        for start, end in found:
            out.append(f"{lines[start]}（{start + 1}〜{end} 行）")
            out.extend(_numbered(lines, start + 1, end))
    out.append("## `Refactor Gate Status` を含む行")
    out.extend(f"{i + 1}\t{line}" for i, line in enumerate(lines) if "Refactor Gate Status" in line)
    completed = _named(lines, spans, "Completed Tasks")
    if not completed:
        out.append("## Completed Tasks: 節が無い")
    for start, end in completed:
        out.append(f"{lines[start]}（{start + 1}〜{end} 行）の task 行と、was_valid: false の [Review Calibration]")
        out.extend(_calibration_and_tasks(lines, start, end))
    return out


def _state(path: Path) -> list[str]:
    text = _read(path)
    if text is None:
        return ["# state.md: 読めない"]
    return [
        "# state.md",
        f"- Task Size: {state_field_value(text, 'Task Size') or '（行が無い）'}",
        f"- Route In Progress: {select_route_in_progress(text) or '（行が無い）'}",
        f"- Active Worktree Path: {state_field_value(text, 'Active Worktree Path') or '（行が無い）'}",
    ]


_SHA_RE = re.compile(r"[0-9a-f]{7,40}")


def _git(worktree: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def _gate_diff(steering: Path, state: str | None) -> tuple[str, frozenset[str]] | None:
    """gate 単位の差分（起点の sha, 変更ファイル）。取れなければ None（review を回す側）。

    起点は state.md の `Impl Gate Base`（Step 11 が gate 単位を終えたとき〔Current Task が空になったとき〕に書く）。無ければ default branch（origin/HEAD）との
    merge-base。起点は HEAD の祖先でなければならない。差分には未 commit・untracked のファイルを含め、この steering の
    ディレクトリだけを除く。
    """
    worktree = steering.resolve().parent.parent
    top = _git(worktree, "rev-parse", "--show-toplevel")
    base = (state_field_value(state, "Impl Gate Base") if state is not None else "") or ""
    base = base.strip().strip("`")
    if not base:
        base = (_git(worktree, "merge-base", "origin/HEAD", "HEAD") or "").strip()
    if top is None or not _SHA_RE.fullmatch(base) or _git(worktree, "merge-base", "--is-ancestor", base, "HEAD") is None:
        return None
    try:
        own = steering.resolve().relative_to(Path(top.strip()).resolve()).as_posix() + "/"
    except ValueError:
        return None
    tracked = _git(worktree, "-c", "core.quotepath=off", "diff", "--name-only", "--no-renames", "-z", base, "--")
    untracked = _git(worktree, "-c", "core.quotepath=off", "ls-files", "--others", "--exclude-standard", "-z", "--full-name")
    if tracked is None or untracked is None:
        return None
    names = {name for name in (tracked + untracked).split("\0") if name and not name.startswith(own)}
    return base, frozenset(names)


def _completed_at_start(state: str | None) -> int | None:
    """gate 単位の始まりの Completed Tasks の数（Step 11 が `Impl Gate Base` と同じ時点で `Impl Gate Completed` に書く）。

    起点も欄も無い最初の gate 単位は 0。欄が無い（起点だけある）・数でないときは None（review を回す側）。
    """
    if state is None:
        return None
    value = (state_field_value(state, "Impl Gate Completed") or "").strip().strip("`")
    if re.fullmatch(r"[0-9]+", value):
        return int(value)
    if not value and not (state_field_value(state, "Impl Gate Base") or "").strip():
        return 0
    return None


def _review_line(steering: Path) -> str:
    """review（Step 2〜10）を外すかの固定行（SKILL.md Step 1e が読む。判定は tasklist_parse.impl_gate_review）。"""
    tasklist = _read(steering / "tasklist.md") or ""
    state = _read(steering / "state.md")
    diff = _gate_diff(steering, state)
    task_size = state_field_value(state, "Task Size") if state is not None else ""
    skip, detail = impl_gate_review(tasklist, task_size, diff[1] if diff else None, _completed_at_start(state))
    return f"impl-gate-review: skip {detail}（差分の起点 {diff[0]}）" if skip and diff else f"impl-gate-review: run（{detail}）"


def _learned(path: Path) -> list[str]:
    # SKILL.md Step 5 の Cross-task と同じ置き場（正本: references/cross-task-learning.md）を読む
    text = _read(path)
    if text is None:
        return [f"# learned-patterns.md: ファイルが無い（{path}）"]
    try:
        lines, _closed, spans = _sections(text)
    except ContextError as exc:
        return [f"# learned-patterns.md: {exc}（自分で読む）"]
    out = ["# learned-patterns.md § Rejected Alternatives"]
    for start, end in _named(lines, spans, "Rejected Alternatives"):
        out.extend(_numbered(lines, start + 1, end))
    return out if len(out) > 1 else ["# learned-patterns.md: Rejected Alternatives 節が無い"]


def _worklog(path: Path) -> list[str]:
    text = _read(path)
    if text is None:
        return ["# worklog.md: ファイルが無い"]
    lines = text.splitlines()
    start = max(len(lines) - WORKLOG_TAIL, 0)
    return [f"# worklog.md（{len(lines)} 行。末尾 {WORKLOG_TAIL} 行）", *_numbered(lines, start, len(lines))]


def _handoff(directory: Path) -> list[str]:
    files = sorted(directory.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = ["# handoff/ の State Machine Impact"]
    for path in files:
        lines = (_read(path) or "").splitlines()
        hits = [i for i, line in enumerate(lines) if line.startswith("### State Machine Impact")]
        if hits:
            start = hits[-1]
            end = next((i for i in range(start + 1, len(lines)) if re.match(r"^#{1,3} ", lines[i])), len(lines))
            out.append(f"## handoff/{path.name}（{start + 1}〜{end} 行）")
            out.extend(_numbered(lines, start, end))
            break
    else:
        out.append("（block が無い）")
    previous = directory / "implementation_gating.md"
    lines, closed, _open_at, _spans = _scan_fences(_read(previous) or "")
    out.append(f"# handoff/implementation_gating.md の見出しと判定の行（{len(lines)} 行）")
    out.extend(
        f"{i + 1}\t{line}" for i, line in enumerate(lines)
        if i not in closed and (_HEADING_RE.match(line) or "判定:" in line or "判定：" in line)
    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--steering-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    steering = args.steering_dir
    try:
        out = _tasklist(steering / "tasklist.md")
    except ContextError as exc:
        print(f"impl-gate-context: {exc}。tasklist.md は自分で読む", file=sys.stderr)
        return 1
    out += _state(steering / "state.md")
    out.append(_review_line(steering))
    out += _learned(steering.resolve().parent.parent / "docs" / "learned-patterns.md")
    out += _worklog(steering / "worklog.md")
    out += _handoff(steering / "handoff")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
