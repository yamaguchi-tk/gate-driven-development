#!/usr/bin/env python3
"""completion-check の機械検査を 1 回で回す。読むだけで、何も書かない。

使い方:
  python3 scripts/check-completion-mechanical.py --steering <dir> --base <ref> [--root <dir>] [--ledger]
    --steering  検査する steering（.steering/<slug>/）
    --base      Codebase Health の差分の起点（Cumulative Diff Base の最新 hash_prefix。無ければ default branch）
    --root      repo（既定: cwd の git toplevel）
    --ledger    AC Trace Ledger の行（gate 列 `completion-check:ledger`）だけを出す。gate が Part B の後に回す
                （既定の実行には入れない。main は回さない）

出力は 1 行 1 要求で `状態<TAB>要求<TAB>gate<TAB>詳細`（scripts/check-gate-ledger.sh と同じ形）。
状態は ok / missing（行が無い）/ invalid（値が条件を満たさない）/ error（検査の道具が判定できない:
例外・base を解決できない・子の出力を読めない・lint-ac.py の exit 2）。error は記録の不備ではないので、
差し戻さずに外部前提不足で止める。gate 列は completion-check の Step（`completion-check:2a` など）で、
行は Step の順（2a → 3 → 4 → 4c → 4c-3 → 4d → 5）に出す。行の扱い（差し戻し先）は references/subagent-dispatch.md
§ Completion-Check の前の機械検査（main）と、その Step（gate）が決める。
ok 以外が 1 件でもあれば exit 1、引数の誤りは exit 2。最後の行は終わりの行
（`ok<TAB>end<TAB>completion-check:0<TAB>rows=<n>`）で、これが無い出力は途中で落ちたものとして扱う。

行の述語は既存の実装のものを呼ぶ。ここに述語を書き足さない:
  - reviewed-by（Step 2a）: hooks/scripts/lib/tasklist_parse.py reviewed_by_rows（check-gate-ledger.sh と共有）
  - remaining-tasks（Step 3）: hooks/scripts/lib/tasklist_structure.py と done_guard.py _scan_remaining_tasks
    （Stop hook の done guard の Check 1 と同じ組み立て。block 理由の文だけが違う）
  - route-in-progress（Step 4）: hooks/scripts/lib/done_guard.py _route_in_progress_errors（done guard の Check 3）
  - ac-ids（Step 5）: scripts/lint-ac.py
  - ac-coverage（Step 4c）・follow-up-stage（Step 4d）・ac-ledger（AC Trace Ledger Gate）:
    hooks/scripts/lib/completion_trace.py（AC ID は lint-ac.py の文法、Lane の節は next_plan_check.py の範囲）。
    requirements.md の AC か PR Boundary を閉じた形で読めないとき、または --ledger で ac-ledger.md に
    Ledger の表のほかの行があるか、tasklist.md・worklog.md に Ledger の見出しが残っているとき
    （references/ac-trace-ledger.md § Append-Only Rule）は、ac-coverage・ac-ledger の代わりに ac-source の行を
    invalid で出す（AC 集合で ok を出さない。gate が読んで判定する）
  - codebase-health（Step 4c-3）: scripts/gdd-codebase-health.py --mode changed --fail-on high
  - unused-symbols（Step 4c-3）: scripts/lint-unused-new-symbols.py（報告だけ。失敗にしない）
Verification の文法（done guard の Check 2）は見ない。Verification は completion-check の Part B が埋めるので、
gate の前は pending が正しい。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
# hooks/scripts を先頭に置き、`lib` を hooks/scripts/lib に解決させる（scripts/lib と同名）。
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.completion_trace import (  # noqa: E402
    ac_source_errors, deferred_acs, follow_up_stage_errors, ledger_errors, legacy_ledger_headings, uncovered_acs,
)
from lib.done_guard import _route_in_progress_errors, _scan_remaining_tasks  # noqa: E402
from lib.regular_file import read_regular_text  # noqa: E402
from lib.tasklist_parse import reviewed_by_rows  # noqa: E402
from lib.tasklist_structure import tasklist_structure  # noqa: E402

Row = tuple[str, str, str, str]


def _load_lint_ac():
    # AC ID の文法は lint-ac.py を正本にする（scripts/lint-plan-consistency.py と同じ読み込み方）
    spec = importlib.util.spec_from_file_location("gdd_lint_ac", SCRIPTS / "lint-ac.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_lint_ac = _load_lint_ac()


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    # 子の lint も利用者のロケールによらず UTF-8 で書かせ、UTF-8 で読む（文字で落ちた lint を失敗と取り違えない）
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, check=False)


def _tasklist_rows(tasklist: Path) -> list[Row]:
    text = read_regular_text(tasklist)  # 無ければ None。ディレクトリ・FIFO は OSError
    if text is None:
        return [("missing", req, gate, "tasklist.md が無い")
                for req, gate in (("reviewed-by", "completion-check:2a"), ("remaining-tasks", "completion-check:3"))]
    rows: list[Row] = [(s, "reviewed-by", "completion-check:2a", d) for s, d in reviewed_by_rows(text)]
    errors, structural_lines, _fence_before, _fenced = tasklist_structure(text)
    remaining, unexpected = _scan_remaining_tasks(structural_lines)
    errors += [f"未完了タスクが残っている: {line.strip()}" for line in remaining]
    errors += [f"Current Task / Pending Tasks に非標準の内容がある: {line.strip()}" for line in unexpected]
    if errors:
        rows += [("invalid", "remaining-tasks", "completion-check:3", _one_line(e)[:300]) for e in errors]
    else:
        rows.append(("ok", "remaining-tasks", "completion-check:3", "Current Task・Pending Tasks に残りが無い"))
    return rows


def _route_rows(tasklist: Path) -> list[Row]:
    gate = "completion-check:4"
    if not (tasklist.parent / "state.md").exists():
        return [("missing", "route-in-progress", gate, "state.md が無い")]
    errors = _route_in_progress_errors(tasklist)
    if errors:
        return [("invalid", "route-in-progress", gate, _one_line(e)) for e in errors]
    return [("ok", "route-in-progress", gate, "Route In Progress=none")]


def _ac_rows(steering: Path, root: Path) -> list[Row]:
    result = _run([sys.executable, str(SCRIPTS / "lint-ac.py"), "--steering-dir", str(steering)], root)
    detail = _one_line(result.stdout + result.stderr)[:300]
    if result.returncode == 0:
        return [("ok", "ac-ids", "completion-check:5", detail or "AC ID が一致する")]
    if result.returncode != 1:  # 1 だけが AC ID の不整合。2 は usage・requirements.md が無い
        return [("error", "ac-ids", "completion-check:5", f"lint-ac.py exit {result.returncode}: {detail}")]
    return [("invalid", "ac-ids", "completion-check:5", f"lint-ac.py exit {result.returncode}: {detail}")]


def _requirements(steering: Path) -> tuple[str, set[str]] | None:
    text = read_regular_text(steering / "requirements.md")  # 無ければ None。ディレクトリ・FIFO は OSError
    if text is None:
        return None
    return text, _lint_ac.extract_ac_ids_from_requirements(text)[0]


def _target_acs(req: tuple[str, set[str]], gate: str) -> tuple[set[str], list[Row]]:
    # ac-coverage と ac-ledger が共有する、この PR が満たす AC の集合（後続の Stage にだけ置いた AC を除く）。
    # AC か PR Boundary を閉じた形で読めないときは、AC 集合で ok を出さず ac-source の行だけを出す（gate が読む）
    deferred, plan_errors = deferred_acs(req[0], _lint_ac.AC_ID_RE)
    errors = ac_source_errors(req[0], req[1], _lint_ac.AC_ID_RE) + plan_errors
    return req[1] - deferred, [("invalid", "ac-source", gate, e) for e in errors]


def _coverage_rows(steering: Path, tasklist: Path) -> list[Row]:
    gate = "completion-check:4c"
    req = _requirements(steering)
    tasklist_text = read_regular_text(tasklist)
    if req is None or tasklist_text is None:
        return [("error", "ac-coverage", gate, "requirements.md か tasklist.md が無い")]
    target, source = _target_acs(req, gate)
    if source:
        return source
    worklog_text = read_regular_text(steering / "worklog.md") or ""
    missing = uncovered_acs(target, [tasklist_text, worklog_text], _lint_ac.AC_ID_RE)
    if missing:
        return [("invalid", "ac-coverage", gate,
                 f"tasklist.md・worklog.md の task の AC:・Covers AC: に無い AC: {', '.join(missing)}")]
    return [("ok", "ac-coverage", gate,
             f"AC {len(target)} 件がどれも task の AC: にある（後続 Stage にだけ置いた AC {len(req[1] - target)} 件を除く）")]


def _follow_up_rows(steering: Path) -> list[Row]:
    gate = "completion-check:4d"
    req = _requirements(steering)
    if req is None:
        return [("error", "follow-up-stage", gate, "requirements.md が無い")]
    errors = follow_up_stage_errors(req[0])
    if errors:
        return [("invalid", "follow-up-stage", gate, _one_line(e)[:300]) for e in errors]
    return [("ok", "follow-up-stage", gate, "Planned Follow-up Stage Lane が無いか、欄が空でない（中身は gate が読む）")]


def _ledger_rows(steering: Path) -> list[Row]:
    gate = "completion-check:ledger"
    req = _requirements(steering)
    if req is None:
        return [("error", "ac-ledger", gate, "requirements.md が無い")]
    target, source = _target_acs(req, gate)
    if source:
        return source
    # 旧来の置き場所（tasklist.md・worklog.md の節）に Ledger の見出しが残っていれば、ac-ledger.md があっても
    # AC の判定をせず gate が読む（append-only で消せない旧い行を読まずに ok にしない）
    legacy = [f"{name}: {heading}" for name in ("tasklist.md", "worklog.md")
              for heading in legacy_ledger_headings(read_regular_text(steering / name) or "")]
    if legacy:
        return [("invalid", "ac-source", gate, f"ac-ledger.md の外に Ledger の見出しがある: {h}") for h in legacy]
    text = read_regular_text(steering / "ac-ledger.md")  # 無ければ None。ディレクトリ・壊れた symlink は OSError
    if text is None:
        return [("missing", "ac-ledger", gate, "ac-ledger.md が無い")]
    errors, unreadable = ledger_errors(target, text, _lint_ac.AC_ID_RE, re.compile(_lint_ac._AC_ID_CORE), req[1])
    if unreadable:  # どの AC の出来事か決まらない行。AC 集合で ok を出さず gate が読む
        return [("invalid", "ac-source", gate, f"Ledger の行を読めない: {line}") for line in unreadable]
    if errors:
        return [("invalid", "ac-ledger", gate, _one_line(e)[:300]) for e in errors]
    return [("ok", "ac-ledger", gate, f"AC {len(target)} 件の最後の行がどれも verified")]


def _health_rows(root: Path, base: str) -> list[Row]:
    gate = "completion-check:4c-3"
    resolved = _run(["git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"], root)
    if resolved.returncode != 0:
        return [("error", "codebase-health", gate, f"--base {base} を commit に解決できない")]
    result = _run([sys.executable, str(SCRIPTS / "gdd-codebase-health.py"), "--repo-root", str(root),
                   "--mode", "changed", "--base-ref", base, "--format", "json", "--fail-on", "high"], root)
    try:
        findings = json.loads(result.stdout)["findings"]
    except (ValueError, KeyError, TypeError):
        return [("error", "codebase-health", gate,
                 f"gdd-codebase-health.py exit {result.returncode}: {_one_line(result.stderr)[:300]}")]
    high = [f"{f.get('path')}: {f.get('evidence')}" for f in findings if f.get("severity") == "high"]
    medium = sum(1 for f in findings if f.get("severity") == "medium")
    if result.returncode != 0 or high:
        return [("invalid", "codebase-health", gate, _one_line(f"High {len(high)} 件: {'; '.join(high)}")[:400])]
    rows: list[Row] = [("ok", "codebase-health", gate, f"High 0 件（Medium {medium} 件は Step 4c-3 で扱いを残す）")]
    unused = _run([sys.executable, str(SCRIPTS / "lint-unused-new-symbols.py"), "--repo-root", str(root),
                   "--base-ref", base], root)
    rows.append(("ok", "unused-symbols", gate, "報告だけ: " + _one_line(unused.stdout + unused.stderr)[:300]))
    return rows


def _guarded(reqs: tuple[tuple[str, str], ...], fn, *args) -> list[Row]:
    # 部品の例外で全体を落とさず、その部品が判定を受け持つ要求のどれにも error 行を残す（行を消さない・ok にしない）
    try:
        return fn(*args)
    except Exception as exc:  # noqa: BLE001
        detail = f"検査が例外で止まった: {type(exc).__name__}: {_one_line(str(exc))[:200]}"
        return [("error", name, gate, detail) for name, gate in reqs]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="completion-check の機械検査")
    parser.add_argument("--steering", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--root")
    parser.add_argument("--ledger", action="store_true")
    args = parser.parse_args(argv)
    # 行の文字で print が落ちて後ろの行が消えないよう、利用者のロケールによらず UTF-8 で書く
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    steering = Path(args.steering).resolve()
    if not steering.is_dir():
        print(f"steering が無い: {steering}", file=sys.stderr)
        return 2
    if args.root:
        root = Path(args.root).resolve()
    else:
        top = _run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
        if top.returncode != 0:
            print("git の toplevel を解決できない（--root で指定する）", file=sys.stderr)
            return 2
        root = Path(top.stdout.strip())
    tasklist = steering / "tasklist.md"
    if args.ledger:
        rows = _guarded((("ac-ledger", "completion-check:ledger"),), _ledger_rows, steering)
    else:
        rows = (
            _guarded((("reviewed-by", "completion-check:2a"), ("remaining-tasks", "completion-check:3")),
                     _tasklist_rows, tasklist)
            + _guarded((("route-in-progress", "completion-check:4"),), _route_rows, tasklist)
            + _guarded((("ac-coverage", "completion-check:4c"),), _coverage_rows, steering, tasklist)
            + _guarded((("codebase-health", "completion-check:4c-3"),), _health_rows, root, args.base)
            + _guarded((("follow-up-stage", "completion-check:4d"),), _follow_up_rows, steering)
            + _guarded((("ac-ids", "completion-check:5"),), _ac_rows, steering, root)
        )
    # 終わりの行。これが無い出力（途中で落ちた・kill された）は、読む側が判定できないものとして止める
    rows.append(("ok", "end", "completion-check:0", f"rows={len(rows)}"))
    for row in rows:
        print("\t".join(row))
    return 1 if any(row[0] != "ok" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
