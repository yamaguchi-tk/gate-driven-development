#!/usr/bin/env python3
"""done guard Check 2 の判定を統合先と手元実装で並走させ、両方向の差分を数える。

`CHANGELOG.md` の `#### Changed` に載せる `measured_at` / `population` /
`done→block` / `block→done` の導出コマンド。判定規則を変えたら必ず再実行する。

使い方（worktree root から）:

    python3 plugins/gate-driven-development/scripts/measure-done-guard-drift.py

母集団は `~/.gdd/worktrees`（`--corpus-root` で足せる）配下の
`**/.steering/*/tasklist.md`（進行中セッションが書き換え続けるローカル実データ）。
件数は不変の事実ではなく `measured_at` 付きのスナップショットとして扱う。
比較対象は `GDD_INTEGRATION_REF`（既定 `origin/main`）の実装。

新旧 signature 両対応（AC-14）: `--integration-ref` 側（既定 `origin/main`）は
本 PR 前の旧 API（`_scan_verification(structural_lines) -> 3-tuple`、
`strip_fenced_lines_marked` 無し）のことがあり、worktree 側は新 API
（`_scan_verification(structural_lines, *, fence_before=, fenced_heading_lines=)
-> 4-tuple`）。`inspect.signature` / `len(result)` / `hasattr(hook,
"strip_fenced_lines_marked")` で分岐し、どちらでも実行できるようにする
（design.md § 4 / tasklist.md T-6 Step 3）。

done→block の内訳は排他 3 分類（design.md § 6 AC-16）: `grammar`（`line`
違反のみ）/ `fence`（`section_fence` / `fenced_heading` 違反のみ）/ `both`
（両方）。新側が旧 API で実行された場合は violations 種別を持たないため
`n/a` に落ちる（tasklist.md T-6 Step 3）。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import inspect
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_REL = "plugins/gate-driven-development/hooks/scripts"

_CATEGORIES = ("grammar", "fence", "both", "n/a")


def _load(root: str):
    for name in [k for k in list(sys.modules) if k == "lib" or k.startswith("lib.") or k == "gdd_stop_hook"]:
        del sys.modules[name]
    sys.path.insert(0, root)
    try:
        import gdd_stop_hook as hook  # noqa: PLC0415
        import lib.done_guard as guard  # noqa: PLC0415
    finally:
        # import が失敗しても差し込んだ path を残さない（`sys.path` 汚染の防止）
        if root in sys.path:
            sys.path.remove(root)
    return hook, guard


def _scan(hook, guard, text: str):
    """`(found, rows, violations, unfinished)` を新旧どちらの API でも返す。

    `violations` は新 API のときだけ埋まる（旧 API 実行時は `None`）。
    hook 本体と**同じ**可視性判定を通す。`strip_fenced_blocks` に替えると
    閉じ忘れ fence の扱いが変わり、実測値が hook の実挙動とずれる（実測で差が出た）。
    2 値 / 4 値 API の allow-list に本スクリプトを載せているのはこの忠実性のため。
    """
    if hasattr(hook, "strip_fenced_lines_marked"):
        structural_lines, _unclosed, fence_before, fenced_heading_lines = (
            hook.strip_fenced_lines_marked(text)
        )
    else:
        structural_lines, _unclosed = hook.strip_fenced_lines(text)
        fence_before = None
        fenced_heading_lines = None

    scan_params = inspect.signature(guard._scan_verification).parameters
    if "fence_before" in scan_params and "fenced_heading_lines" in scan_params:
        result = guard._scan_verification(
            structural_lines,
            fence_before=fence_before,
            fenced_heading_lines=fenced_heading_lines,
        )
    else:
        result = guard._scan_verification(structural_lines)

    if len(result) == 4:
        found, rows, violations, unfinished = result
    else:
        found, rows, unfinished = result
        violations = None
    return found, rows, violations, unfinished


def _category(violations) -> str:
    """design.md § 6（AC-16）の排他分類。violations が無ければ `n/a`。

    fence 違反（`section_fence` / `fenced_heading`）を 1 件でも持てば "fence"、
    `line` 違反も同時に持てば "both" に寄せる。優先順位を固定しないと二重計上・
    単一計上のどちらでも実装でき、CHANGELOG の実測値が再現しない（design.md § 6）。
    """
    if violations is None:
        return "n/a"
    kinds = {kind for kind, _payload in violations}
    has_fence = bool(kinds & {"section_fence", "fenced_heading"})
    has_line = "line" in kinds
    if has_fence and has_line:
        return "both"
    if has_fence:
        return "fence"
    if has_line:
        return "grammar"
    return "n/a"


def _verdict(hook, guard, text: str) -> tuple[str, list]:
    found, rows, violations, unfinished = _scan(hook, guard, text)
    if violations is None:
        errors = hook._verification_errors(found, rows, unfinished)
    else:
        errors = hook._verification_errors(found, rows, violations, unfinished)
    return ("block" if errors else "done"), violations


def _tasklists(roots: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for root in roots:
        for dirpath, _dirnames, filenames in os.walk(root):
            if os.path.basename(os.path.dirname(dirpath)) == ".steering" and "tasklist.md" in filenames:
                found.add(Path(dirpath) / "tasklist.md")
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration-ref", default=os.environ.get("GDD_INTEGRATION_REF", "origin/main"))
    parser.add_argument("--corpus-root", action="append", default=None)
    args = parser.parse_args()

    roots = [Path(p).expanduser() for p in (args.corpus_root or [
        "~/.gdd/worktrees",
    ])]

    with tempfile.TemporaryDirectory() as tmp:
        archive = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "archive", args.integration_ref, PLUGIN_REL],
            capture_output=True, check=True,
        ).stdout
        subprocess.run(["tar", "-x", "-C", tmp], input=archive, check=True)
        old_hook, old_guard = _load(str(Path(tmp) / PLUGIN_REL))
        new_hook, new_guard = _load(str(REPO_ROOT / PLUGIN_REL))

        done_to_block: list[Path] = []
        block_to_done: list[Path] = []
        category_counts: dict[str, int] = dict.fromkeys(_CATEGORIES, 0)
        population = 0
        for path in _tasklists(roots):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            population += 1
            before, _before_violations = _verdict(old_hook, old_guard, text)
            after, after_violations = _verdict(new_hook, new_guard, text)
            if before == "done" and after == "block":
                done_to_block.append(path)
                category_counts[_category(after_violations)] += 1
            elif before == "block" and after == "done":
                block_to_done.append(path)

    print(f"measured_at: {_dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
    print(f"integration_ref: {args.integration_ref}")
    print(f"population: {population}")
    print(f"done->block: {len(done_to_block)}")
    for category in _CATEGORIES:
        print(f"  done->block[{category}]: {category_counts[category]}")
    print(f"block->done: {len(block_to_done)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
