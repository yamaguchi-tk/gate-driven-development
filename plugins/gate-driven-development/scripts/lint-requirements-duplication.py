#!/usr/bin/env python3
"""AC の欄名の列挙を、AC 以外の節と design.md に書き直している箇所を出す（warn-only）。

正本: `references/requirements-template.md` § 事実は AC に 1 回だけ書く。
AC（`requirements.md` の `- AC-N:` 行）を単一の正本にし、Summary Brief・
Human Check Questions・Implementation Sequence Plan・Route / Ownership Matrix・
design.md は事実を書き直さず `AC-N 参照` と書く。

背景: GDD を使う別の repo のタスク（2026-10-02）で、許可欄名を 3 つから 2 つに
減らしたのに AC-6 と Route / Ownership Matrix に古い欄名が残り、requirements
レビュー 2 回目の blocking がすべてこの書き換え漏れだった。

検査するのは backtick で囲んだ語だけで、自由文は解析しない:
  - AC の語の集合: AC 定義行（lint-ac.py と同じ文法）と、同じ節でその下に続く行の backtick 語
  - AC 以外の行（AC 定義を含まない節の行、design.md の行。見出し行は除く）が、
    1 つの AC の語を 2 つ以上含んでいたら WARN にする
  - `EXCLUDED_SECTIONS` の節は、その下の小見出しも含めて、同じか上の階層の次の見出しまで見ない
    （スコープの原文と Express Minimal Trace は AC への写しの照合元、Planned Follow-up Stage Lane の
    値は継続の hook が読む）。見出しは完全一致で比べ、閉じたコードフェンスの中の `#` 行は見出しにしない
  - WARN は先頭の `MAX_WARNINGS` 件と、残りの件数だけを出す
数値の重複は見ない（言い回しが自由で誤検知が多いため。限界）。

Exit code:
  0: WARN の有無によらず（warn-only。WARN は stdout に出す）
  1: 例外（lint-ac.py が読めないなど）
  2: usage error

Usage:
  lint-requirements-duplication.py --steering-dir <.steering/<task>/>
  lint-requirements-duplication.py <requirements.md> [<design.md>]
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

BACKTICK_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^(#{1,6})\s")
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
MIN_SHARED_TOKENS = 2
MAX_WARNINGS = 5
EXCLUDED_SECTIONS = {"スコープ", "Express Minimal Trace", "Planned Follow-up Stage Lane"}


def _load_ac_def_re() -> re.Pattern[str]:
    """AC 定義行の文法は lint-ac.py と同じものを使う（受理集合をずらさない）。"""
    path = Path(__file__).resolve().parent / "lint-ac.py"
    spec = importlib.util.spec_from_file_location("gdd_lint_ac", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.AC_DEF_RE


AC_DEF_RE = _load_ac_def_re()


def _heading_levels(lines: list[str]) -> list[int | None]:
    """行ごとの見出しの階層（`#` の数）。見出しでない行と、閉じたコードフェンスの中の行は None。

    フェンスは、開きと同じ文字で長さが同じか長く、info string の無い行で閉じる（CommonMark）。
    文末まで閉じないフェンスは、開きの行から後の `#` 行を見出しとして数える。
    """
    fenced: set[int] = set()
    fence: str | None = None
    open_at = 0
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if fence is None:
            # backtick のフェンスの info string に backtick を含む行は開きにしない（lib/tasklist_parse.py と同じ）
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence, open_at = m.group(1), i
        elif m and m.group(1).startswith(fence) and not m.group(2).strip():
            fenced.update(range(open_at, i + 1))
            fence = None
    levels: list[int | None] = []
    for i, line in enumerate(lines):
        h = None if i in fenced else HEADING_RE.match(line)
        levels.append(len(h.group(1)) if h else None)
    return levels


def _excluded_lines(lines: list[str], levels: list[int | None]) -> set[int]:
    """`EXCLUDED_SECTIONS` の見出しから、同じか上の階層の次の見出しまでの行。"""
    excluded: set[int] = set()
    excluded_level: int | None = None
    for i, level in enumerate(levels):
        if level is not None:
            if excluded_level is not None and level <= excluded_level:
                excluded_level = None
            if excluded_level is None and lines[i].lstrip("#").strip() in EXCLUDED_SECTIONS:
                excluded_level = level
        if excluded_level is not None:
            excluded.add(i)
    return excluded


def _sections(levels: list[int | None]) -> list[list[int]]:
    """見出しで区切った節ごとに、行番号（0 始まり）のリストを返す。"""
    sections: list[list[int]] = [[]]
    for i, level in enumerate(levels):
        if level is not None:
            sections.append([])
        sections[-1].append(i)
    return sections


def split_ac_and_other(lines: list[str]) -> tuple[dict[str, set[str]], list[int]]:
    """AC ごとの backtick 語の集合と、AC 以外の行番号を返す。"""
    ac_tokens: dict[str, set[str]] = {}
    other: list[int] = []
    levels = _heading_levels(lines)
    excluded = _excluded_lines(lines, levels)
    for section in _sections(levels):
        section = [i for i in section if i not in excluded]
        if not any(AC_DEF_RE.match(lines[i]) for i in section):
            other.extend(i for i in section if levels[i] is None)
            continue
        current: str | None = None
        for i in section:
            m = AC_DEF_RE.match(lines[i])
            if m:
                current = m.group(2)
            if current is not None:
                ac_tokens.setdefault(current, set()).update(BACKTICK_RE.findall(lines[i]))
    return ac_tokens, other


def find_duplicates(
    ac_tokens: dict[str, set[str]], lines: list[str], line_numbers: list[int], label: str
) -> list[str]:
    warnings: list[str] = []
    for i in line_numbers:
        tokens = set(BACKTICK_RE.findall(lines[i]))
        if len(tokens) < MIN_SHARED_TOKENS:
            continue
        hits = [
            (ac_id, sorted(tokens & ac_set))
            for ac_id, ac_set in ac_tokens.items()
            if len(tokens & ac_set) >= MIN_SHARED_TOKENS
        ]
        if not hits:
            continue
        detail = "; ".join(
            f"{ac_id} の " + ", ".join(f"`{t}`" for t in shared) for ac_id, shared in hits
        )
        refs = " / ".join(f"{ac_id} 参照" for ac_id, _ in hits)
        warnings.append(
            f"WARN: {label}:{i + 1}（write 前の内容）が AC の欄名の列挙を書き直しています（{detail}）。"
            f"事実は AC に 1 回だけ書き、ここは「{refs}」にしてください（照合元と Lane の値は除く）"
            "（references/requirements-template.md § 事実は AC に 1 回だけ書く）"
        )
    return warnings


def lint(req_path: Path, design_path: Path | None) -> list[str]:
    req_lines = req_path.read_text(encoding="utf-8", errors="replace").splitlines()
    ac_tokens, other = split_ac_and_other(req_lines)
    if not ac_tokens:
        return []
    warnings = find_duplicates(ac_tokens, req_lines, other, req_path.name)
    if design_path is not None and design_path.is_file():
        design_lines = design_path.read_text(encoding="utf-8", errors="replace").splitlines()
        targets = [i for i, level in enumerate(_heading_levels(design_lines)) if level is None]
        warnings += find_duplicates(ac_tokens, design_lines, targets, design_path.name)
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements_md", nargs="?")
    parser.add_argument("design_md", nargs="?")
    parser.add_argument("--steering-dir")
    args = parser.parse_args()

    if args.steering_dir:
        d = Path(args.steering_dir)
        req_path, design_path = d / "requirements.md", d / "design.md"
    elif args.requirements_md:
        req_path = Path(args.requirements_md)
        design_path = Path(args.design_md) if args.design_md else None
    else:
        print("usage: lint-requirements-duplication.py --steering-dir <dir>", file=sys.stderr)
        return 2

    if not req_path.is_file():
        return 0
    warnings = lint(req_path, design_path)
    for warning in warnings[:MAX_WARNINGS]:
        print(warning)
    if len(warnings) > MAX_WARNINGS:
        print(f"（ほか {len(warnings) - MAX_WARNINGS} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
