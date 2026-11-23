#!/usr/bin/env python3
"""Deterministic task binding registry for GDD status/resume.

The registry is the machine-readable source for "which GDD task belongs to
this worktree". Natural-language status/resume prompts are entry signals only;
they do not decide task identity.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL = {"done", "cancelled"}
REGISTRY_DIR = ".gdd/tasks"


def _norm(path: Path | str) -> str:
    return str(Path(path).expanduser().resolve(strict=False))


# fence 追跡の正本は hooks/scripts/lib/tasklist_parse.strip_fenced_blocks。
# **top-level module として**読む。`hooks/scripts` を載せて `from lib.X import`
# すると `sys.modules["lib"]` が hooks 側に固定され、同一プロセスの
# `scripts/lib`（`lint_base` 等）が解決できなくなる（実測: ModuleNotFoundError）。
_LIB_DIR = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from tasklist_parse import strip_fenced_blocks  # noqa: E402
    from regular_file import read_regular_text  # noqa: E402
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)


def _field(text: str, name: str) -> str:
    # fenced code block の中は書式の記入例であって現在値ではない。
    for raw in strip_fenced_blocks(text).splitlines():
        # canonical field 行は行頭から始まる。インデント行は入れ子 bullet の
        # 履歴メモ / コードブロック内の記入例なので field として読まない
        # （tests/test_canonical_field_line_anchoring_contract.py が正本）。
        if raw[:1] in (" ", "\t"):
            continue
        line = re.sub(r"^-[ \t]+", "", raw.strip())
        for sep in ("=", ":"):
            if line.startswith(name + sep):
                # バッククォート除去は値側だけに適用する。行全体に適用すると
                # `- Worktree: `~/...`` で値の先頭のバッククォートが残り、
                # expanduser() が効かず相対パス扱いになる（silent failure）。
                value = line.split(sep, 1)[1].strip().strip("`").strip()
                # 区切り文字の後ろが空の行は現在値ではない。書きかけの
                # `- Resume From:` が先頭にあるだけで後続の値付き行が見えなくなり、
                # done 済み task を非終端として bind 候補に残していた（R-1）。
                if value:
                    return value
                break  # この行はこの sep で確定。値が空なら次の行へ進む
    return ""


def _approved_direction(text: str) -> str:
    in_section = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## Approved Direction"):
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section:
            normalized = stripped.lstrip("- ").strip()
            for prefix in ("承認内容:", "Approved Direction:", "Scope:"):
                if normalized.startswith(prefix):
                    return normalized.split(":", 1)[1].strip()
            if normalized:
                return normalized
    return ""


def _is_terminal_state(text: str) -> bool:
    return _field(text, "Resume From") in TERMINAL or _field(text, "Next Action") in TERMINAL


def registry_root(repo_root: Path) -> Path:
    return repo_root / REGISTRY_DIR


def binding_path(repo_root: Path, task_id: str) -> Path:
    return registry_root(repo_root) / task_id / "binding.json"


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".binding.", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def upsert_binding_from_state(repo_root: Path, state_path: Path) -> dict[str, Any]:
    """Create/update a registry binding from a steering state.md file."""

    repo_root = Path(repo_root).resolve(strict=False)
    state_path = Path(state_path).resolve(strict=False)
    # `errors="replace"` で開く。state.md は他セッション・他エージェントが書く
    # untrusted 入力で、不正バイトが 1 つあると `UnicodeDecodeError`（ValueError 系）
    # になる。呼び出し元の `except OSError` では捕捉できず、hook が exit 1
    # （non-blocking error）で落ちて **検査そのものが無効化**される。不正バイトは
    # 注記部分に混ざる想定で、field の構造は保たれるため置換文字化しても判定に
    # 影響しない（先例: detect-steering.sh:gdd_extract_route_in_progress）。
    text = state_path.read_text(encoding="utf-8", errors="replace")
    task_id = _field(text, "Task ID") or state_path.parent.name
    steering_path = state_path.parent
    worktree_path = _field(text, "Worktree") or _field(text, "Active Worktree Path") or str(steering_path.parent.parent)
    branch = _field(text, "Branch") or _field(text, "Active Branch")

    data: dict[str, Any] = {
        "binding_version": 1,
        "task_id": task_id,
        "repo_root": _norm(repo_root),
        "steering_path": _norm(steering_path),
        "state_path": _norm(state_path),
        "worktree_path": _norm(worktree_path),
        "branch": branch,
        "canonical_goal": _approved_direction(text),
        "runtime_session_id": "",
        "source_context": {
            "kind": "state",
            "summary": "",
        },
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    _atomic_write_json(binding_path(repo_root, task_id), data)
    return data


def load_bindings(repo_root: Path) -> list[dict[str, Any]]:
    root = registry_root(Path(repo_root))
    if not root.is_dir():
        return []
    bindings: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/binding.json")):
        try:
            # 通常のファイルだけを読む（FIFO で止まると、hook が timeout して素通りになる）。
            data = json.loads(read_regular_text(path) or "")
        except Exception:
            # 1 件の binding.json で解決全体を落とさない（深い入れ子は RecursionError を投げる）。
            # merge gate の binding lookup（hooks/scripts/lib/merge-gate-binding.sh）も 1 件ずつ飛ばす。
            continue
        if isinstance(data, dict):
            bindings.append(data)
    return bindings


def _frontmatter(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}
    # 独立レビュー round 9/10（`hooks/scripts/lib/state_io.py::parse_state()`・
    # `scripts/resolve-gdd-model.py::extract_frontmatter_value()`）と同じ入口の
    # fail-open: 部分文字列一致 `text.split("---\n", 2)` は値がちょうど `"---"` に
    # なる行を終端と誤認し、それより後ろの key（`active`・`session_id` 等）を
    # 丸ごと読み落とす。line-exact（内容が厳密に `---` である行）で終端を判定する。
    lines = text.split("\n")
    try:
        end_index = lines.index("---", 1)
    except ValueError:
        return {}
    result: dict[str, str] = {}
    for raw in lines[1:end_index]:
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def _safe_norm(value: Any) -> str:
    """空でない文字列なら `_norm` した値、そうでなければ空文字。

    binding.json は任意の JSON になりうる。文字列でない値は `Path()` が TypeError を、
    NUL・孤立サロゲートを含む値は `realpath` の lstat が ValueError / UnicodeEncodeError を投げ、
    1 件で `resolve_task()` 全体が落ちる（done guard は conflict の warn に下がる）。
    """
    if not isinstance(value, str) or not value:
        return ""
    try:
        return _norm(value)
    except Exception:
        return ""


def _absolute_worktree_path(item: dict[str, Any]) -> str:
    """`worktree_path` が絶対パスの文字列なら `_norm` した値、そうでなければ空文字。

    空・相対の値を `_norm` に通すと、プロセスの cwd を基準に解決されて今の worktree に
    一致してしまう（`worktree_path` の無い旧書式の binding を commit した repo で実測）。
    `~` 始まりも受けない（done guard の `_validate_binding` と merge gate の binding lookup が
    受けるのも `/` 始まりだけ。書き手は `_norm` した絶対パスを書く）。
    """
    value = item.get("worktree_path", "")
    if not isinstance(value, str) or not value.startswith("/"):
        return ""
    return _safe_norm(value)


def _invalid_bindings(bindings: list[dict[str, Any]]) -> list[dict[str, str]]:
    invalid: list[dict[str, str]] = []
    for item in bindings:
        worktree_path = _absolute_worktree_path(item)
        if not worktree_path:
            continue
        try:
            # Python 3.12 以前の `Path.exists()` は EACCES などを投げ直す。
            exists = Path(worktree_path).exists()
        except OSError:
            exists = False
        if not exists:
            invalid.append(
                {
                    "task_id": str(item.get("task_id", "")),
                    "reason": "missing_worktree_path",
                    "worktree_path": worktree_path,
                }
            )
    return invalid


def _legacy_root_candidates(repo_root: Path, known_steering_paths: set[str]) -> list[str]:
    root = Path(repo_root) / ".steering"
    if not root.is_dir():
        return []
    candidates: list[str] = []
    for state_path in sorted(root.glob("*/state.md")):
        steering = str(state_path.parent)
        if _norm(state_path.parent) in known_steering_paths:
            continue
        # FIFO・デバイスは開くと待ち続け、hook の timeout で gate が通る。通常ファイルだけ読む。
        # 種類の確認も try の中で行う（Python 3.12 の is_file は権限エラーを投げる）。
        try:
            if not state_path.is_file():
                continue
            text = state_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not _is_terminal_state(text):
            candidates.append(steering)
    return candidates


def _select_worktree_matches(
    bindings: list[dict[str, Any]],
    *,
    cwd_norm: str,
    current_branch: str,
    explicit_task_id: str,
    warnings: list[str],
) -> list[dict[str, Any]]:
    """current worktree（+ branch）に一致する binding だけを残す。

    `warnings` は呼び出し側と共有する list を **in-place** で伸ばす（branch 不一致は
    候補ごとに 1 回積まれるが、返却時の `sorted(set(...))` で畳まれる既存挙動）。
    """
    matches: list[dict[str, Any]] = []
    for item in bindings:
        if explicit_task_id and item.get("task_id") != explicit_task_id:
            continue
        worktree_path = _absolute_worktree_path(item)
        if not worktree_path or worktree_path != cwd_norm:
            continue
        item_branch = item.get("branch", "")
        if current_branch and item_branch and item_branch != current_branch:
            warnings.append("branch_mismatch_candidate_ignored")
            continue
        matches.append(item)
    return matches


def _local_state_mismatches(local: dict[str, str], selected: dict[str, Any]) -> list[str]:
    """`.claude/gdd-dev.local.md` の soft signal が binding と食い違う件数分の warning。

    local state は soft signal であり registry の hard match を上書きしない
    （`commands/gdd-dev.md` Instruction 2.0）。食い違いは警告として残すだけ。
    """
    pairs = (
        (local.get("task_id") or local.get("task_slug"), selected.get("task_id")),
        (local.get("branch"), selected.get("branch")),
    )
    warnings = ["local_state_mismatch_ignored" for value, expected in pairs if value and value != expected]
    local_worktree = local.get("worktree")
    if local_worktree and _safe_norm(local_worktree) != _absolute_worktree_path(selected):
        warnings.append("local_state_mismatch_ignored")
    return warnings


def resolve_task(
    *,
    repo_root: Path,
    cwd: Path,
    current_branch: str = "",
    local_state_path: Path | None = None,
    latest_user_text: str = "",
    explicit_task_id: str = "",
) -> dict[str, Any]:
    """Resolve current GDD task without relying on natural-language similarity."""

    display_repo_root = Path(repo_root)
    repo_root = Path(repo_root).resolve(strict=False)
    cwd_norm = _norm(cwd)
    bindings = load_bindings(repo_root)
    known_steering_paths = {_safe_norm(item.get("steering_path", "")) for item in bindings} - {""}
    warnings: list[str] = []
    local = _frontmatter(local_state_path) if local_state_path else {}
    invalid_bindings = _invalid_bindings(bindings)
    if invalid_bindings:
        warnings.append("stale_binding_missing_worktree")
    if local.get("active") == "true" and not local.get("session_id", ""):
        warnings.append("invalid_empty_local_session_id")
    diagnostic_candidates = _legacy_root_candidates(display_repo_root, known_steering_paths)
    if diagnostic_candidates:
        warnings.append("legacy_root_steering_ignored")

    matches = _select_worktree_matches(
        bindings,
        cwd_norm=cwd_norm,
        current_branch=current_branch,
        explicit_task_id=explicit_task_id,
        warnings=warnings,
    )

    if len(matches) != 1:
        if not matches:
            warnings.append("no_current_worktree_binding")
        else:
            warnings.append("multiple_current_worktree_bindings")
        return {
            "status": "conflict",
            "task_id": "",
            "reason": "no unique current worktree binding",
            "warnings": sorted(set(warnings)),
            "diagnostic_candidates": diagnostic_candidates,
            "candidates": [item.get("task_id", "") for item in bindings],
            "invalid_bindings": invalid_bindings,
            "latest_user_text": latest_user_text,
        }

    selected = matches[0]
    warnings.extend(_local_state_mismatches(local, selected))

    return {
        "status": "resolved",
        "task_id": selected.get("task_id", ""),
        "binding": selected,
        "warnings": sorted(set(warnings)),
        "diagnostic_candidates": diagnostic_candidates,
        "invalid_bindings": invalid_bindings,
        "latest_user_text": latest_user_text,
    }


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="GDD task binding registry")
    sub = parser.add_subparsers(dest="command", required=True)

    write_p = sub.add_parser("upsert-from-state")
    write_p.add_argument("--repo-root", required=True)
    write_p.add_argument("--state", required=True)

    resolve_p = sub.add_parser("resolve")
    resolve_p.add_argument("--repo-root", required=True)
    resolve_p.add_argument("--cwd", required=True)
    resolve_p.add_argument("--current-branch", default="")
    resolve_p.add_argument("--local-state-path", default="")
    resolve_p.add_argument("--latest-user-text", default="")
    resolve_p.add_argument("--explicit-task-id", default="")

    args = parser.parse_args(argv)
    if args.command == "upsert-from-state":
        print(json.dumps(upsert_binding_from_state(Path(args.repo_root), Path(args.state)), ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "resolve":
        local_state = Path(args.local_state_path) if args.local_state_path else None
        print(
            json.dumps(
                resolve_task(
                    repo_root=Path(args.repo_root),
                    cwd=Path(args.cwd),
                    current_branch=args.current_branch,
                    local_state_path=local_state,
                    latest_user_text=args.latest_user_text,
                    explicit_task_id=args.explicit_task_id,
                ),
                # 孤立サロゲートを含む値も `\udXXX` に escape して出す（strict な UTF-8 の stdout で
                # print が落ちると、呼び出し側の shell は空出力として fallback に進む）。
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
