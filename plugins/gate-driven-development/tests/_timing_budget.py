"""Shared timing measurement helper for performance regression tests.

Measures both CPU time and wall-clock time for a code block using the
same API, so subprocess-based tests (#1/#2/#3) and in-process tests
(#4/#5) can share one measurement mechanism instead of each copying
its own formula.

Semantics and caveats (do not change without re-reading
requirements.md Honest Limitations and design.md Detailed Design):
  - cpu_seconds = this process's `time.process_time()` delta
    + `resource.getrusage(RUSAGE_CHILDREN)` (ru_utime + ru_stime)
    delta. This captures CPU used by waited child AND grandchild
    processes (e.g. bash -> python3), confirmed by measurement.
  - RUSAGE_CHILDREN is process-wide, not scoped to one child: if a
    *different* child process is wait()-ed inside the measured
    block, its CPU mixes into the delta too. No `tests/*.py`
    currently does this inside a measured block.
  - pytest-xdist workers are separate OS processes, so
    RUSAGE_CHILDREN values from one worker never leak into another.
  - `resource` is Unix-only. On a non-Unix platform this module
    fails to import, and every test file that imports it fails at
    collection time (fail-loud, not a silent skip).
"""
from __future__ import annotations

import json
import resource
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from _paths import PLUGIN_ROOT


def _children_cpu_seconds() -> float:
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def _require_exited(value: float | None, field: str) -> float:
    if value is None:
        raise RuntimeError(
            f"timing_budget() の with ブロック退出前に {field} が読み出された"
        )
    return value


@dataclass
class TimingBudget:
    """Holds the CPU/wall elapsed time for one measured block.

    Both properties raise until the `with timing_budget()` block has
    exited, so a caller who mistakenly reads them *inside* the
    `with` block gets an exception instead of a bogus
    zero-vs-threshold comparison that would always pass.
    """

    _cpu: float | None = None
    _wall: float | None = None

    @property
    def cpu_seconds(self) -> float:
        return _require_exited(self._cpu, "cpu_seconds")

    @property
    def wall_seconds(self) -> float:
        return _require_exited(self._wall, "wall_seconds")


@contextmanager
def timing_budget() -> Iterator[TimingBudget]:
    budget = TimingBudget()
    start_wall = time.monotonic()
    start_cpu = time.process_time()
    start_children_cpu = _children_cpu_seconds()
    try:
        yield budget
    finally:
        budget._cpu = (time.process_time() - start_cpu) + (
            _children_cpu_seconds() - start_children_cpu
        )
        budget._wall = time.monotonic() - start_wall


def _iter_hook_entries(data: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """hooks.json の event -> group -> hook の入れ子を 1 本の列に均す。"""
    for event_groups in data.get("hooks", {}).values():
        for group in event_groups:
            yield from group.get("hooks", [])


def hook_timeout_seconds(script_basename: str) -> float:
    """Return the `timeout` (seconds) hooks.json declares for a hook.

    Scans every event/group/hook entry whose `command` contains
    `script_basename`. Raises LookupError (fail-loud, no default
    fallback) if:
      - zero hooks match, or
      - two-or-more matches disagree on `timeout`, or
      - `timeout` is missing / not an int or float / <= 0.
    """
    hooks_path = PLUGIN_ROOT / "hooks" / "hooks.json"
    data = json.loads(hooks_path.read_text(encoding="utf-8"))
    matched_timeouts: set[float] = set()
    for hook in _iter_hook_entries(data):
        if script_basename not in hook.get("command", ""):
            continue
        timeout = hook.get("timeout")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or timeout <= 0
        ):
            raise LookupError(
                f"hooks.json の {script_basename} 用 hook に "
                f"有効な timeout が無い: {timeout!r}"
            )
        matched_timeouts.add(float(timeout))
    if not matched_timeouts:
        raise LookupError(
            f"hooks.json に command が {script_basename!r} を含む "
            "hook が見つからない"
        )
    if len(matched_timeouts) > 1:
        raise LookupError(
            f"hooks.json の {script_basename} 用 hook で timeout が "
            f"一致しない: {sorted(matched_timeouts)}"
        )
    return matched_timeouts.pop()


def hang_guard_seconds(script_basename: str) -> float:
    """hook を起動するテストの壁時計の打ち切り（hooks.json の timeout の 6 倍）。

    止まったときの保険だけにする。hook 1 回の CPU 時間は timeout より十分小さいが、壁時計は
    ほぼプロセス起動の待ちで、並列の全量テストと外部の負荷の下では timeout に届く
    （2026-10-26 に、load average が高い中で merge gate 1 回が timeout の近くまで延びた。2026-10-27 には、
    さらに高い load average の中で pre-PR gate の FIFO のテスト 1 本〔hook の起動 2 回〕が timeout の近くまで延びた）。
    """
    return hook_timeout_seconds(script_basename) * 6
